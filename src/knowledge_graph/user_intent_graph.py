"""User intent graph module inspired by KGAT/KGIN.

This module builds a heterogeneous user-intent graph from goldset_v0_1.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


@dataclass
class IntentGraphConfig:
    embedding_dim: int = 64
    topk_neighbors: int = 20
    random_seed: int = 20260226


@dataclass
class IntentNode:
    user_id: str
    query: str
    intent: str
    domain: str
    target_category: Optional[str]
    price_range: Optional[Dict[str, float]]
    must_have: List[str]
    exclude: List[str]
    required_slots: List[str]
    city: Optional[str]
    preconditions: List[str]
    expected_action: Optional[str]


class UserIntentGraph:
    """User-side graph for intent representation and retrieval."""

    def __init__(self, config: Optional[IntentGraphConfig] = None) -> None:
        self.config = config or IntentGraphConfig()
        self.intent_nodes: Dict[str, IntentNode] = {}
        self.node_features: Dict[str, np.ndarray] = {}
        self.edges: Dict[str, List[Tuple[str, str, float]]] = {}
        self.relation_attention: Dict[str, float] = {}
        self.intent_factors: Dict[str, np.ndarray] = {}
        self.user_embeddings: Dict[str, np.ndarray] = {}

    # ---------- Data loading ----------
    def load_from_goldset(self, goldset_dir: Path | str) -> None:
        """Load both e-commerce and miniapp records as graph seeds."""
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
        self._build_user_embeddings()

    def add_record(self, record: Dict[str, Any]) -> None:
        label = record.get("label", {})
        service = record.get("service", {})

        node = IntentNode(
            user_id=record["id"],
            query=record.get("query", ""),
            intent=label.get("intent", "未知"),
            domain=record.get("domain", "unknown"),
            target_category=label.get("target_category") or service.get("category"),
            price_range=label.get("price_range"),
            must_have=list(label.get("must_have", [])),
            exclude=list(label.get("exclude", [])),
            required_slots=list(label.get("required_slots", [])),
            city=service.get("city"),
            preconditions=list(label.get("preconditions", [])),
            expected_action=label.get("expected_action"),
        )
        self.intent_nodes[node.user_id] = node

        self._upsert_node_feature(node.user_id, self._encode_intent_node(node))
        self._attach_intent_edges(node)

    # ---------- KG structure ----------
    def _upsert_node_feature(self, node_id: str, feature: np.ndarray) -> None:
        self.node_features[node_id] = self._l2norm(feature)
        self.edges.setdefault(node_id, [])

    def _add_edge(self, src: str, dst: str, relation: str, weight: float) -> None:
        self.edges.setdefault(src, []).append((dst, relation, float(weight)))

    def _attach_intent_edges(self, node: IntentNode) -> None:
        uid = node.user_id
        intent_key = f"intent::{node.intent}"
        self._upsert_node_feature(intent_key, self._encode_text(intent_key))
        self._add_edge(uid, intent_key, "has_intent", 1.0)

        if node.target_category:
            cat = f"category::{node.target_category}"
            self._upsert_node_feature(cat, self._encode_text(cat))
            self._add_edge(uid, cat, "prefers_category", 0.9)

        if node.price_range:
            pmin = int(node.price_range.get("min", 0))
            pmax = int(node.price_range.get("max", 0))
            price = f"price::{pmin}-{pmax}"
            self._upsert_node_feature(price, self._encode_text(price))
            span = max(1, pmax - pmin)
            self._add_edge(uid, price, "has_price_constraint", 1.0 / math.log1p(span))

        for attr in node.must_have:
            key = f"attr::{attr}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "must_have", 1.0)

        for attr in node.exclude:
            key = f"attr::{attr}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "exclude", 0.7)

        for slot in node.required_slots:
            key = f"slot::{slot}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "requires_slot", 0.9)

        if node.city:
            key = f"city::{node.city}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "located_in", 0.85)

        for pre in node.preconditions:
            key = f"pre::{pre}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "has_precondition", 0.7)

        if node.expected_action:
            key = f"action::{node.expected_action}"
            self._upsert_node_feature(key, self._encode_text(key))
            self._add_edge(uid, key, "expects_action", 0.8)

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

        # KGAT-like relation-aware attention prior (frequency-normalized).
        self.relation_attention = {
            r: c / float(total) for r, c in counts.items()
        }

    def _build_intent_factors(self) -> None:
        intents = sorted({n.intent for n in self.intent_nodes.values()})
        self.intent_factors = {
            it: self._encode_text(f"intent_factor::{it}") for it in intents
        }

    def _build_user_embeddings(self) -> None:
        """KGIN-like disentangled aggregation over relation-intent factors."""
        self.user_embeddings = {}
        for user_id, node in self.intent_nodes.items():
            base = self.node_features[user_id]
            neigh = self.edges.get(user_id, [])[: self.config.topk_neighbors]
            if not neigh:
                self.user_embeddings[user_id] = base
                continue

            intent_factor = self.intent_factors.get(node.intent, np.zeros(self.config.embedding_dim))
            agg = np.zeros(self.config.embedding_dim)
            denom = 1e-8
            for nb_id, relation, edge_w in neigh:
                nb_vec = self.node_features.get(nb_id)
                if nb_vec is None:
                    continue
                rel_att = self.relation_attention.get(relation, 0.0)
                factor_att = self._cosine(nb_vec, intent_factor)
                alpha = max(0.0, rel_att * edge_w * (0.5 + 0.5 * factor_att))
                agg += alpha * nb_vec
                denom += alpha

            self.user_embeddings[user_id] = self._l2norm(0.6 * base + 0.4 * (agg / denom))

    # ---------- Retrieval APIs ----------
    def get_user_embedding(self, user_id: str) -> np.ndarray:
        if user_id in self.user_embeddings:
            return self.user_embeddings[user_id]
        node = self.intent_nodes.get(user_id)
        if node is None:
            return np.zeros(self.config.embedding_dim)
        return self._encode_intent_node(node)

    def encode_query_as_user(self, query: str, hint: Optional[Dict[str, Any]] = None) -> np.ndarray:
        pseudo = IntentNode(
            user_id="query::temp",
            query=query,
            intent=(hint or {}).get("intent", self._infer_intent(query)),
            domain=(hint or {}).get("domain", "unknown"),
            target_category=(hint or {}).get("target_category"),
            price_range=(hint or {}).get("price_range"),
            must_have=list((hint or {}).get("must_have", [])),
            exclude=list((hint or {}).get("exclude", [])),
            required_slots=list((hint or {}).get("required_slots", [])),
            city=(hint or {}).get("city"),
            preconditions=list((hint or {}).get("preconditions", [])),
            expected_action=(hint or {}).get("expected_action"),
        )
        return self._encode_intent_node(pseudo)

    def topk_similar_users(self, user_vec: np.ndarray, k: int = 20) -> List[Tuple[str, float]]:
        scores = [
            (uid, self._cosine(user_vec, emb)) for uid, emb in self.user_embeddings.items()
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def get_statistics(self) -> Dict[str, Any]:
        intent_dist: Dict[str, int] = {}
        for node in self.intent_nodes.values():
            intent_dist[node.intent] = intent_dist.get(node.intent, 0) + 1
        return {
            "users": len(self.intent_nodes),
            "graph_nodes": len(self.node_features),
            "graph_edges": sum(len(v) for v in self.edges.values()),
            "intent_distribution": intent_dist,
            "relations": dict(sorted(self.relation_attention.items(), key=lambda x: x[1], reverse=True)),
        }

    # ---------- Feature encoding ----------
    def _encode_intent_node(self, node: IntentNode) -> np.ndarray:
        pieces = [
            f"query::{node.query}",
            f"intent::{node.intent}",
            f"domain::{node.domain}",
            f"category::{node.target_category or ''}",
            f"city::{node.city or ''}",
            f"action::{node.expected_action or ''}",
        ]

        if node.price_range:
            pieces.append(f"price::{int(node.price_range.get('min', 0))}-{int(node.price_range.get('max', 0))}")
        pieces.extend(f"must::{x}" for x in node.must_have)
        pieces.extend(f"exclude::{x}" for x in node.exclude)
        pieces.extend(f"slot::{x}" for x in node.required_slots)
        pieces.extend(f"pre::{x}" for x in node.preconditions)

        vec = np.zeros(self.config.embedding_dim)
        for token in pieces:
            vec += self._encode_text(token)
        return self._l2norm(vec)

    def _encode_text(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(abs(hash((text, self.config.random_seed))) % (2**32))
        return rng.normal(0.0, 1.0, self.config.embedding_dim)

    def _infer_intent(self, query: str) -> str:
        mapping = {
            "查": "服务查询",
            "办理": "服务办理",
            "预约": "预约",
            "投诉": "投诉反馈",
            "状态": "状态追踪",
            "推荐": "搭配推荐",
            "对比": "对比决策",
            "预算": "价格约束",
            "价格": "价格约束",
        }
        for key, val in mapping.items():
            if key in query:
                return val
        return "商品检索"

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
    "IntentGraphConfig",
    "IntentNode",
    "UserIntentGraph",
]
