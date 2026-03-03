"""Supply capacity graph module inspired by KGAT/KGIN.

This module models product/service capabilities for bidirectional matching.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class SupplyGraphConfig:
    embedding_dim: int = 64
    topk_neighbors: int = 24
    random_seed: int = 20260226


@dataclass
class SupplyNode:
    supply_id: str
    domain: str
    title_or_name: str
    intent: str
    category_lv1: Optional[str]
    category_lv2_or_service: Optional[str]
    brand: Optional[str]
    price: Optional[float]
    attributes: Dict[str, Any]
    city: Optional[str]
    channel: Optional[str]
    required_slots: List[str]
    preconditions: List[str]
    expected_action: Optional[str]


class SupplyCapacityGraph:
    """Supply-side graph for capability representation and retrieval."""

    def __init__(self, config: Optional[SupplyGraphConfig] = None) -> None:
        self.config = config or SupplyGraphConfig()
        self.supply_nodes: Dict[str, SupplyNode] = {}
        self.node_features: Dict[str, np.ndarray] = {}
        self.edges: Dict[str, List[Tuple[str, str, float]]] = {}
        self.relation_attention: Dict[str, float] = {}
        self.intent_factors: Dict[str, np.ndarray] = {}
        self.supply_embeddings: Dict[str, np.ndarray] = {}

    def load_from_goldset(self, goldset_dir: Path | str) -> None:
        root = Path(goldset_dir)
        for name in ("gold_ecom.jsonl", "gold_miniapp.jsonl"):
            file_path = root / name
            if not file_path.exists():
                continue
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    self.add_record(json.loads(line))

        self._build_relation_attention()
        self._build_intent_factors()
        self._build_supply_embeddings()

    def add_record(self, record: Dict[str, Any]) -> None:
        label = record.get("label", {})
        product = record.get("product", {})
        service = record.get("service", {})

        domain = record.get("domain", "unknown")
        is_ecom = domain == "ecommerce"

        node = SupplyNode(
            supply_id=record["id"],
            domain=domain,
            title_or_name=product.get("title") or service.get("name", ""),
            intent=label.get("intent", "未知"),
            category_lv1=product.get("category_lv1") if is_ecom else service.get("category"),
            category_lv2_or_service=product.get("category_lv2") if is_ecom else service.get("name"),
            brand=product.get("brand") if is_ecom else None,
            price=product.get("price") if is_ecom else None,
            attributes=dict(product.get("attributes", {})),
            city=service.get("city"),
            channel=service.get("channel"),
            required_slots=list(label.get("required_slots", [])),
            preconditions=list(label.get("preconditions", [])),
            expected_action=label.get("expected_action"),
        )

        self.supply_nodes[node.supply_id] = node
        self._upsert_node_feature(node.supply_id, self._encode_supply_node(node))
        self._attach_supply_edges(node)

    # ---------- KG structure ----------
    def _upsert_node_feature(self, node_id: str, feature: np.ndarray) -> None:
        self.node_features[node_id] = self._l2norm(feature)
        self.edges.setdefault(node_id, [])

    def _add_edge(self, src: str, dst: str, relation: str, weight: float) -> None:
        self.edges.setdefault(src, []).append((dst, relation, float(weight)))

    def _attach_supply_edges(self, node: SupplyNode) -> None:
        sid = node.supply_id

        intent_key = f"intent::{node.intent}"
        self._upsert_node_feature(intent_key, self._encode_text(intent_key))
        self._add_edge(sid, intent_key, "supports_intent", 1.0)

        if node.category_lv1:
            cat1 = f"category_lv1::{node.category_lv1}"
            self._upsert_node_feature(cat1, self._encode_text(cat1))
            self._add_edge(sid, cat1, "belongs_to_lv1", 0.95)

        if node.category_lv2_or_service:
            cat2 = f"category_lv2::{node.category_lv2_or_service}"
            self._upsert_node_feature(cat2, self._encode_text(cat2))
            self._add_edge(sid, cat2, "belongs_to_lv2", 0.9)

        if node.brand:
            brand = f"brand::{node.brand}"
            self._upsert_node_feature(brand, self._encode_text(brand))
            self._add_edge(sid, brand, "has_brand", 0.8)

        if node.price is not None:
            bucket = self._price_bucket(node.price)
            price = f"price_bucket::{bucket}"
            self._upsert_node_feature(price, self._encode_text(price))
            self._add_edge(sid, price, "in_price_bucket", 0.85)

        for k, v in node.attributes.items():
            attr = f"attr::{k}::{v}"
            self._upsert_node_feature(attr, self._encode_text(attr))
            self._add_edge(sid, attr, "has_attribute", 0.9)

        if node.city:
            city = f"city::{node.city}"
            self._upsert_node_feature(city, self._encode_text(city))
            self._add_edge(sid, city, "operates_in", 0.9)

        if node.channel:
            channel = f"channel::{node.channel}"
            self._upsert_node_feature(channel, self._encode_text(channel))
            self._add_edge(sid, channel, "channels_through", 0.75)

        for slot in node.required_slots:
            s = f"slot::{slot}"
            self._upsert_node_feature(s, self._encode_text(s))
            self._add_edge(sid, s, "requires_slot", 0.85)

        for pre in node.preconditions:
            p = f"pre::{pre}"
            self._upsert_node_feature(p, self._encode_text(p))
            self._add_edge(sid, p, "requires_precondition", 0.75)

        if node.expected_action:
            a = f"action::{node.expected_action}"
            self._upsert_node_feature(a, self._encode_text(a))
            self._add_edge(sid, a, "expects_action", 0.8)

    def _build_relation_attention(self) -> None:
        counts: Dict[str, int] = {}
        total = 0
        for triples in self.edges.values():
            for _, relation, _ in triples:
                counts[relation] = counts.get(relation, 0) + 1
                total += 1
        if total == 0:
            self.relation_attention = {}
            return
        self.relation_attention = {r: c / float(total) for r, c in counts.items()}

    def _build_intent_factors(self) -> None:
        intents = sorted({n.intent for n in self.supply_nodes.values()})
        self.intent_factors = {
            i: self._encode_text(f"supply_intent_factor::{i}") for i in intents
        }

    def _build_supply_embeddings(self) -> None:
        self.supply_embeddings = {}
        for sid, node in self.supply_nodes.items():
            base = self.node_features[sid]
            neigh = self.edges.get(sid, [])[: self.config.topk_neighbors]
            if not neigh:
                self.supply_embeddings[sid] = base
                continue

            factor = self.intent_factors.get(node.intent, np.zeros(self.config.embedding_dim))
            agg = np.zeros(self.config.embedding_dim)
            denom = 1e-8
            for nb_id, relation, edge_w in neigh:
                nb_vec = self.node_features.get(nb_id)
                if nb_vec is None:
                    continue
                rel_att = self.relation_attention.get(relation, 0.0)
                factor_att = self._cosine(nb_vec, factor)
                alpha = max(0.0, rel_att * edge_w * (0.5 + 0.5 * factor_att))
                agg += alpha * nb_vec
                denom += alpha

            self.supply_embeddings[sid] = self._l2norm(0.6 * base + 0.4 * (agg / denom))

    # ---------- Retrieval APIs ----------
    def get_supply_embedding(self, supply_id: str) -> np.ndarray:
        if supply_id in self.supply_embeddings:
            return self.supply_embeddings[supply_id]
        node = self.supply_nodes.get(supply_id)
        if node is None:
            return np.zeros(self.config.embedding_dim)
        return self._encode_supply_node(node)

    def topk_similar_supply(self, supply_vec: np.ndarray, k: int = 20) -> List[Tuple[str, float]]:
        scores = [
            (sid, self._cosine(supply_vec, emb)) for sid, emb in self.supply_embeddings.items()
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def get_statistics(self) -> Dict[str, Any]:
        domain_dist: Dict[str, int] = {}
        for node in self.supply_nodes.values():
            domain_dist[node.domain] = domain_dist.get(node.domain, 0) + 1
        return {
            "supplies": len(self.supply_nodes),
            "graph_nodes": len(self.node_features),
            "graph_edges": sum(len(v) for v in self.edges.values()),
            "domain_distribution": domain_dist,
            "relations": dict(sorted(self.relation_attention.items(), key=lambda x: x[1], reverse=True)),
        }

    # ---------- Feature encoding ----------
    def _encode_supply_node(self, node: SupplyNode) -> np.ndarray:
        pieces = [
            f"domain::{node.domain}",
            f"name::{node.title_or_name}",
            f"intent::{node.intent}",
            f"lv1::{node.category_lv1 or ''}",
            f"lv2::{node.category_lv2_or_service or ''}",
            f"brand::{node.brand or ''}",
            f"city::{node.city or ''}",
            f"channel::{node.channel or ''}",
            f"action::{node.expected_action or ''}",
        ]

        if node.price is not None:
            pieces.append(f"price_bucket::{self._price_bucket(node.price)}")
        pieces.extend(f"attr::{k}::{v}" for k, v in node.attributes.items())
        pieces.extend(f"slot::{x}" for x in node.required_slots)
        pieces.extend(f"pre::{x}" for x in node.preconditions)

        vec = np.zeros(self.config.embedding_dim)
        for token in pieces:
            vec += self._encode_text(token)
        return self._l2norm(vec)

    @staticmethod
    def _price_bucket(price: float) -> str:
        p = float(price)
        if p < 500:
            return "0-500"
        if p < 2000:
            return "500-2000"
        if p < 5000:
            return "2000-5000"
        return "5000+"

    def _encode_text(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(abs(hash((text, self.config.random_seed))) % (2**32))
        return rng.normal(0.0, 1.0, self.config.embedding_dim)

    @staticmethod
    def _l2norm(vec: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(vec)
        if n < 1e-12:
            return vec
        return vec / n

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return 0.0
        return float(np.dot(a, b) / (na * nb))


__all__ = [
    "SupplyGraphConfig",
    "SupplyNode",
    "SupplyCapacityGraph",
]
