"""Neo4j-style knowledge graph built on top of NetworkX.

This module provides:
1) In-memory heterogeneous graph storage via networkx.MultiDiGraph
2) Real entity nodes and typed relations from goldset_v0_1
3) Independent user-subgraph and supply-subgraph modeling
4) Bidirectional matching APIs: user_to_supply / supply_to_user
5) Export APIs: Neo4j Cypher and GraphML
"""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import networkx as nx
import numpy as np
from networkx.algorithms import isomorphism


class GraphAggregator:
    """Numpy-based graph neural aggregation for heterogeneous graphs.

    Design notes:
    - MB-DGT inspiration: supports relation-weighted message passing across layers.
    - GraphSASA inspiration: optional hierarchical aggregation by node-label communities.
    """

    def __init__(
        self,
        graph: nx.MultiDiGraph,
        embedding_dim: int = 64,
        num_layers: int = 2,
        aggregator_type: str = "mean",
        direction: str = "both",
        alpha: float = 0.5,
        hierarchical: bool = True,
        hierarchy_weight: float = 0.2,
        seed: int = 42,
    ) -> None:
        self.graph = graph
        self.embedding_dim = max(4, int(embedding_dim))
        self.num_layers = max(1, int(num_layers))
        self.aggregator_type = aggregator_type.lower()
        self.direction = direction.lower()
        if self.direction not in {"out", "in", "both"}:
            raise ValueError("direction must be one of: out, in, both")
        self.alpha = float(np.clip(alpha, 0.0, 1.0))
        self.hierarchical = hierarchical
        self.hierarchy_weight = float(np.clip(hierarchy_weight, 0.0, 1.0))
        self.seed = seed

    def aggregate_neighbors(
        self,
        node_id: str,
        node_features: Dict[str, np.ndarray],
        method: str = "mean",
    ) -> np.ndarray:
        """Aggregate one-hop neighbors for a node.

        Supported methods:
        - mean: simple mean pooling
        - gcn: degree-normalized convolution
        - graphsage: mean + self fusion
        - gat: attention-weighted sum
        """
        method = method.lower()
        if method not in {"mean", "gcn", "graphsage", "gat"}:
            raise ValueError("method must be one of: mean, gcn, graphsage, gat")

        self_feat = node_features[node_id]
        neighbor_ids, edge_weights = self._collect_neighbors(node_id)
        if not neighbor_ids:
            return self_feat.copy()

        neigh_mat = np.vstack([node_features[nid] for nid in neighbor_ids])
        weights = np.asarray(edge_weights, dtype=np.float64)
        if weights.size == 0:
            weights = np.ones((len(neighbor_ids),), dtype=np.float64)

        if method == "mean":
            norm = np.maximum(weights.sum(), 1e-9)
            return (weights[:, None] * neigh_mat).sum(axis=0) / norm

        if method == "gcn":
            deg_self = max(self._node_degree(node_id), 1)
            norm_messages: List[np.ndarray] = []
            for idx, nid in enumerate(neighbor_ids):
                deg_n = max(self._node_degree(nid), 1)
                coeff = weights[idx] / np.sqrt(float(deg_self * deg_n))
                norm_messages.append(coeff * node_features[nid])
            out = np.sum(norm_messages, axis=0)
            out += (1.0 / float(deg_self)) * self_feat
            return out

        if method == "graphsage":
            neigh_mean = neigh_mat.mean(axis=0)
            # Keep output dimension unchanged with residual-style fusion.
            return 0.5 * self_feat + 0.5 * neigh_mean

        # method == "gat"
        attn_logits = np.array([np.dot(self_feat, node_features[nid]) for nid in neighbor_ids], dtype=np.float64)
        attn_logits = attn_logits / np.sqrt(max(self.embedding_dim, 1))
        attn_logits += np.log(np.maximum(weights, 1e-9))
        attn = self._softmax(attn_logits)
        return (attn[:, None] * neigh_mat).sum(axis=0)

    def propagate(
        self,
        node_features: Dict[str, np.ndarray],
        num_layers: Optional[int] = None,
        method: Optional[str] = None,
    ) -> Dict[str, np.ndarray]:
        """Run multi-layer message passing and return updated node features."""
        method = (method or self.aggregator_type).lower()
        if method not in {"mean", "gcn", "graphsage", "gat"}:
            raise ValueError("method must be one of: mean, gcn, graphsage, gat")
        layers = max(1, int(num_layers or self.num_layers))

        current = {nid: feat.astype(np.float64, copy=True) for nid, feat in node_features.items()}

        for _ in range(layers):
            updated: Dict[str, np.ndarray] = {}
            label_centroids = self._label_centroids(current) if self.hierarchical else {}

            for node_id in self.graph.nodes:
                base_agg = self.aggregate_neighbors(node_id, current, method=method)
                fused = (1.0 - self.alpha) * current[node_id] + self.alpha * base_agg

                if self.hierarchical:
                    h_feat = self._hierarchical_aggregate(node_id, current, label_centroids)
                    fused = (1.0 - self.hierarchy_weight) * fused + self.hierarchy_weight * h_feat

                updated[node_id] = self._l2_normalize(fused)

            current = updated

        return current

    def compute_node_embeddings(
        self,
        initial_features: Optional[Dict[str, np.ndarray]] = None,
        method: Optional[str] = None,
        num_layers: Optional[int] = None,
    ) -> Dict[str, np.ndarray]:
        """Compute node embeddings from attributes + multi-layer propagation."""
        if initial_features is None:
            features = {node_id: self._init_feature(node_id) for node_id in self.graph.nodes}
        else:
            features = {}
            for node_id in self.graph.nodes:
                raw = initial_features.get(node_id)
                if raw is None:
                    features[node_id] = self._init_feature(node_id)
                    continue
                vec = np.asarray(raw, dtype=np.float64).reshape(-1)
                features[node_id] = self._fit_dim(vec)

        return self.propagate(features, num_layers=num_layers, method=method)

    def _collect_neighbors(self, node_id: str) -> Tuple[List[str], List[float]]:
        neighbor_ids: List[str] = []
        edge_weights: List[float] = []

        if self.direction in {"out", "both"}:
            for _, dst, _, data in self.graph.out_edges(node_id, keys=True, data=True):
                neighbor_ids.append(dst)
                edge_weights.append(float(data.get("weight", 1.0)))

        if self.direction in {"in", "both"}:
            for src, _, _, data in self.graph.in_edges(node_id, keys=True, data=True):
                neighbor_ids.append(src)
                edge_weights.append(float(data.get("weight", 1.0)))

        return neighbor_ids, edge_weights

    def _hierarchical_aggregate(
        self,
        node_id: str,
        node_features: Dict[str, np.ndarray],
        label_centroids: Dict[str, np.ndarray],
    ) -> np.ndarray:
        node_label = self.graph.nodes[node_id].get("label", "Entity")
        label_feat = label_centroids.get(node_label, node_features[node_id])
        neigh_ids, _ = self._collect_neighbors(node_id)
        if not neigh_ids:
            return 0.5 * node_features[node_id] + 0.5 * label_feat

        two_hop_feats: List[np.ndarray] = []
        for nid in neigh_ids:
            n2_ids, _ = self._collect_neighbors(nid)
            if not n2_ids:
                continue
            two_hop_feats.append(np.mean([node_features[n2] for n2 in n2_ids], axis=0))

        if two_hop_feats:
            two_hop = np.mean(two_hop_feats, axis=0)
            return (node_features[node_id] + label_feat + two_hop) / 3.0
        return 0.5 * node_features[node_id] + 0.5 * label_feat

    def _label_centroids(self, node_features: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        buckets: Dict[str, List[np.ndarray]] = {}
        for node_id, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", "Entity")
            buckets.setdefault(label, []).append(node_features[node_id])
        return {label: np.mean(vectors, axis=0) for label, vectors in buckets.items()}

    def _node_degree(self, node_id: str) -> int:
        if self.direction == "out":
            return int(self.graph.out_degree(node_id))
        if self.direction == "in":
            return int(self.graph.in_degree(node_id))
        return int(self.graph.degree(node_id))

    def _init_feature(self, node_id: str) -> np.ndarray:
        attrs = self.graph.nodes[node_id]
        text_parts = [str(node_id), str(attrs.get("label", ""))]
        for k in sorted(attrs.keys()):
            if k == "label":
                continue
            v = attrs.get(k)
            if isinstance(v, (dict, list, tuple, set)):
                text_parts.append(f"{k}:{json.dumps(v, ensure_ascii=False, sort_keys=True)}")
            else:
                text_parts.append(f"{k}:{v}")

        seed = (hash("|".join(text_parts)) ^ self.seed) & 0xFFFFFFFF
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.embedding_dim)
        return self._l2_normalize(vec)

    def _fit_dim(self, vec: np.ndarray) -> np.ndarray:
        if vec.shape[0] == self.embedding_dim:
            return self._l2_normalize(vec)
        if vec.shape[0] > self.embedding_dim:
            return self._l2_normalize(vec[: self.embedding_dim])

        out = np.zeros((self.embedding_dim,), dtype=np.float64)
        out[: vec.shape[0]] = vec
        return self._l2_normalize(out)

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        x = x - np.max(x)
        e = np.exp(x)
        return e / np.maximum(e.sum(), 1e-9)

    @staticmethod
    def _l2_normalize(x: np.ndarray) -> np.ndarray:
        denom = np.linalg.norm(x)
        if denom <= 1e-12:
            return x
        return x / denom


class Neo4jKnowledgeGraph:
    """Heterogeneous knowledge graph compatible with Neo4j export."""

    def __init__(self) -> None:
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph(name="goldset_v0_1_kg")
        self.bridge_rel_types: Set[str] = {"LOOKS_FOR", "CAN_SATISFY"}

    # ---------------------------------------------------------------------
    # Build graph
    # ---------------------------------------------------------------------
    def load_from_goldset(self, goldset_dir: Path | str) -> None:
        root = Path(goldset_dir)
        for filename in ("gold_ecom.jsonl", "gold_miniapp.jsonl"):
            file_path = root / filename
            if not file_path.exists():
                continue
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    self.add_record(json.loads(line))

    def add_record(self, record: Dict[str, Any]) -> None:
        domain = record.get("domain", "unknown")
        if domain == "ecommerce":
            self._add_ecom_record(record)
        elif domain == "miniapp_service":
            self._add_miniapp_record(record)
        else:
            self._add_generic_record(record)

    # ---------------------------------------------------------------------
    # Entity + relation construction
    # ---------------------------------------------------------------------
    def _add_ecom_record(self, record: Dict[str, Any]) -> None:
        rid = record["id"]
        query = record.get("query", "")
        language = record.get("language", "")
        label = record.get("label", {})
        product = record.get("product", {})

        user_id = self._entity_id("User", rid)
        user_need_id = self._entity_id("UserNeed", rid)

        supply_id = self._entity_id("Supply", rid)
        supply_offer_id = self._entity_id("SupplyOffer", rid)
        product_id = self._entity_id("Product", rid)

        # User subgraph
        self._add_node(
            user_id,
            "User",
            {
                "record_id": rid,
                "domain": "ecommerce",
                "query": query,
                "language": language,
                "dataset": record.get("dataset", ""),
                "difficulty": record.get("difficulty", ""),
                "role": "user",
                "subgraph": "user",
            },
        )
        self._add_node(
            user_need_id,
            "UserNeed",
            {
                "record_id": rid,
                "domain": "ecommerce",
                "role": "user_need",
                "subgraph": "user",
            },
        )
        self._add_edge(user_id, user_need_id, "EXPRESSES_NEED", {"domain": "ecommerce", "weight": 1.0})

        # Supply subgraph
        self._add_node(
            supply_id,
            "Supply",
            {
                "record_id": rid,
                "domain": "ecommerce",
                "supply_type": "product",
                "title": product.get("title", ""),
                "price": product.get("price"),
                "role": "supply",
                "subgraph": "supply",
            },
        )
        self._add_node(
            supply_offer_id,
            "SupplyOffer",
            {
                "record_id": rid,
                "domain": "ecommerce",
                "role": "supply_offer",
                "subgraph": "supply",
            },
        )
        self._add_node(
            product_id,
            "Product",
            {
                "record_id": rid,
                "title": product.get("title", ""),
                "price": product.get("price"),
                "domain": "ecommerce",
                "subgraph": "supply",
            },
        )
        self._add_edge(supply_id, supply_offer_id, "HAS_OFFER", {"domain": "ecommerce", "weight": 1.0})
        self._add_edge(supply_offer_id, product_id, "OFFERS_PRODUCT", {"domain": "ecommerce", "weight": 1.0})

        # Bidirectional bridge between demand and supply.
        self._add_edge(user_id, supply_id, "LOOKS_FOR", {"domain": "ecommerce", "weight": 1.0})
        self._add_edge(supply_id, user_id, "CAN_SATISFY", {"domain": "ecommerce", "weight": 1.0})

        query_id = self._entity_id("Query", rid)
        self._add_node(
            query_id,
            "Query",
            {
                "text": query,
                "language": language,
                "domain": "ecommerce",
                "subgraph": "user",
            },
        )
        self._add_edge(user_need_id, query_id, "SEARCHES", {"weight": 1.0})

        intent = label.get("intent")
        if intent:
            intent_id = self._entity_id("Intent", intent)
            self._add_node(intent_id, "Intent", {"name": intent})
            self._add_edge(user_need_id, intent_id, "HAS_INTENT", {"weight": 1.0})
            self._add_edge(supply_offer_id, intent_id, "MATCHES_INTENT", {"weight": 1.0})

        target_category = label.get("target_category")
        if target_category:
            cat_id = self._entity_id("Category", target_category)
            self._add_node(cat_id, "Category", {"name": target_category, "level": "target"})
            self._add_edge(user_need_id, cat_id, "PREFERS_CATEGORY", {"weight": 1.0})

        category_lv1 = product.get("category_lv1")
        if category_lv1:
            cat1_id = self._entity_id("Category", category_lv1)
            self._add_node(cat1_id, "Category", {"name": category_lv1, "level": "lv1"})
            self._add_edge(supply_offer_id, cat1_id, "BELONGS_TO", {"level": "lv1", "weight": 1.0})

        category_lv2 = product.get("category_lv2")
        if category_lv2:
            cat2_id = self._entity_id("Category", category_lv2)
            self._add_node(cat2_id, "Category", {"name": category_lv2, "level": "lv2"})
            self._add_edge(supply_offer_id, cat2_id, "BELONGS_TO", {"level": "lv2", "weight": 1.0})

        brand = product.get("brand")
        if brand:
            brand_id = self._entity_id("Brand", brand)
            self._add_node(brand_id, "Brand", {"name": brand})
            self._add_edge(supply_offer_id, brand_id, "HAS_BRAND", {"weight": 1.0})

        price_range = label.get("price_range")
        if isinstance(price_range, dict):
            pmin = price_range.get("min")
            pmax = price_range.get("max")
            pr_name = f"{pmin}-{pmax}"
            pr_id = self._entity_id("PriceRange", pr_name)
            self._add_node(pr_id, "PriceRange", {"name": pr_name, "min": pmin, "max": pmax})
            self._add_edge(user_need_id, pr_id, "HAS_PRICE_RANGE", {"weight": 1.0})

        attrs = product.get("attributes", {})
        for k, v in attrs.items():
            attr_name = f"{k}:{v}"
            attr_id = self._entity_id("Attribute", attr_name)
            self._add_node(attr_id, "Attribute", {"key": k, "value": v, "name": attr_name})
            self._add_edge(supply_offer_id, attr_id, "HAS_ATTRIBUTE", {"weight": 1.0})

        for val in label.get("must_have", []):
            attr_id = self._entity_id("Attribute", val)
            self._add_node(attr_id, "Attribute", {"name": val})
            self._add_edge(user_need_id, attr_id, "MUST_HAVE", {"weight": 1.0})

        for val in label.get("exclude", []):
            attr_id = self._entity_id("Attribute", val)
            self._add_node(attr_id, "Attribute", {"name": val})
            self._add_edge(user_need_id, attr_id, "EXCLUDES", {"weight": 1.0})

        sort_by = label.get("sort_by")
        if sort_by:
            behavior_id = self._entity_id("Behavior", sort_by)
            self._add_node(behavior_id, "Behavior", {"name": sort_by})
            self._add_edge(user_need_id, behavior_id, "SORTS_BY", {"weight": 0.8})

    def _add_miniapp_record(self, record: Dict[str, Any]) -> None:
        rid = record["id"]
        query = record.get("query", "")
        language = record.get("language", "")
        label = record.get("label", {})
        service = record.get("service", {})

        user_id = self._entity_id("User", rid)
        user_need_id = self._entity_id("UserNeed", rid)

        supply_id = self._entity_id("Supply", rid)
        supply_offer_id = self._entity_id("SupplyOffer", rid)
        service_id = self._entity_id("Service", rid)

        # User subgraph
        self._add_node(
            user_id,
            "User",
            {
                "record_id": rid,
                "domain": "miniapp_service",
                "query": query,
                "language": language,
                "dataset": record.get("dataset", ""),
                "difficulty": record.get("difficulty", ""),
                "role": "user",
                "subgraph": "user",
            },
        )
        self._add_node(
            user_need_id,
            "UserNeed",
            {
                "record_id": rid,
                "domain": "miniapp_service",
                "role": "user_need",
                "subgraph": "user",
            },
        )
        self._add_edge(user_id, user_need_id, "EXPRESSES_NEED", {"domain": "miniapp_service", "weight": 1.0})

        # Supply subgraph
        self._add_node(
            supply_id,
            "Supply",
            {
                "record_id": rid,
                "domain": "miniapp_service",
                "supply_type": "service",
                "name": service.get("name", ""),
                "role": "supply",
                "subgraph": "supply",
            },
        )
        self._add_node(
            supply_offer_id,
            "SupplyOffer",
            {
                "record_id": rid,
                "domain": "miniapp_service",
                "role": "supply_offer",
                "subgraph": "supply",
            },
        )
        self._add_node(
            service_id,
            "Service",
            {
                "record_id": rid,
                "name": service.get("name", ""),
                "domain": "miniapp_service",
                "subgraph": "supply",
            },
        )
        self._add_edge(supply_id, supply_offer_id, "HAS_OFFER", {"domain": "miniapp_service", "weight": 1.0})
        self._add_edge(supply_offer_id, service_id, "OFFERS_SERVICE", {"domain": "miniapp_service", "weight": 1.0})

        # Bidirectional bridge between demand and supply.
        self._add_edge(user_id, supply_id, "LOOKS_FOR", {"domain": "miniapp_service", "weight": 1.0})
        self._add_edge(supply_id, user_id, "CAN_SATISFY", {"domain": "miniapp_service", "weight": 1.0})

        query_id = self._entity_id("Query", rid)
        self._add_node(
            query_id,
            "Query",
            {
                "text": query,
                "language": language,
                "domain": "miniapp_service",
                "subgraph": "user",
            },
        )
        self._add_edge(user_need_id, query_id, "SEARCHES", {"weight": 1.0})

        intent = label.get("intent")
        if intent:
            intent_id = self._entity_id("Intent", intent)
            self._add_node(intent_id, "Intent", {"name": intent})
            self._add_edge(user_need_id, intent_id, "HAS_INTENT", {"weight": 1.0})
            self._add_edge(supply_offer_id, intent_id, "MATCHES_INTENT", {"weight": 1.0})

        service_category = service.get("category")
        if service_category:
            cat_id = self._entity_id("Category", service_category)
            self._add_node(cat_id, "Category", {"name": service_category, "level": "service"})
            self._add_edge(supply_offer_id, cat_id, "PROVIDES", {"weight": 1.0})

        city = service.get("city")
        if city:
            city_id = self._entity_id("City", city)
            self._add_node(city_id, "City", {"name": city})
            self._add_edge(supply_offer_id, city_id, "OPERATES_IN", {"weight": 1.0})
            self._add_edge(user_need_id, city_id, "LOCATED_IN", {"weight": 0.9})

        channel = service.get("channel")
        if channel:
            channel_id = self._entity_id("Channel", channel)
            self._add_node(channel_id, "Channel", {"name": channel})
            self._add_edge(supply_offer_id, channel_id, "CHANNELS_THROUGH", {"weight": 1.0})

        for slot in label.get("required_slots", []):
            slot_id = self._entity_id("Slot", slot)
            self._add_node(slot_id, "Slot", {"name": slot})
            self._add_edge(user_need_id, slot_id, "REQUIRES_SLOT", {"weight": 1.0})
            self._add_edge(supply_offer_id, slot_id, "REQUIRES_SLOT", {"weight": 1.0})

        for pre in label.get("preconditions", []):
            pre_id = self._entity_id("Precondition", pre)
            self._add_node(pre_id, "Precondition", {"name": pre})
            self._add_edge(user_need_id, pre_id, "HAS_PRECONDITION", {"weight": 1.0})
            self._add_edge(supply_offer_id, pre_id, "HAS_PRECONDITION", {"weight": 1.0})

        action = label.get("expected_action")
        if action:
            action_id = self._entity_id("Action", action)
            self._add_node(action_id, "Action", {"name": action})
            self._add_edge(user_need_id, action_id, "EXPECTED_ACTION", {"weight": 1.0})
            self._add_edge(supply_offer_id, action_id, "EXPECTED_ACTION", {"weight": 1.0})

        time_constraint = label.get("time_constraint", {})
        if isinstance(time_constraint, dict):
            before = time_constraint.get("before")
            if before:
                tc_id = self._entity_id("TimeConstraint", str(before))
                self._add_node(tc_id, "TimeConstraint", {"before": before, "name": str(before)})
                self._add_edge(user_need_id, tc_id, "HAS_TIME_CONSTRAINT", {"weight": 1.0})
                self._add_edge(supply_offer_id, tc_id, "HAS_TIME_CONSTRAINT", {"weight": 1.0})

    def _add_generic_record(self, record: Dict[str, Any]) -> None:
        rid = record.get("id", "unknown")

        user_id = self._entity_id("User", rid)
        supply_id = self._entity_id("Supply", rid)

        self._add_node(user_id, "User", {"record_id": rid, "domain": record.get("domain", "unknown"), "role": "user"})
        self._add_node(
            supply_id,
            "Supply",
            {
                "record_id": rid,
                "domain": record.get("domain", "unknown"),
                "supply_type": "generic",
                "role": "supply",
            },
        )

        self._add_edge(user_id, supply_id, "LOOKS_FOR", {"domain": record.get("domain", "unknown"), "weight": 1.0})
        self._add_edge(supply_id, user_id, "CAN_SATISFY", {"domain": record.get("domain", "unknown"), "weight": 1.0})

        intent = (record.get("label") or {}).get("intent")
        if intent:
            intent_id = self._entity_id("Intent", intent)
            self._add_node(intent_id, "Intent", {"name": intent})
            self._add_edge(user_id, intent_id, "HAS_INTENT", {"weight": 1.0})
            self._add_edge(supply_id, intent_id, "MATCHES_INTENT", {"weight": 1.0})

    # ---------------------------------------------------------------------
    # Bidirectional match APIs
    # ---------------------------------------------------------------------
    def user_to_supply(
        self,
        user_id: str,
        topk: int = 20,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Match one user node to supply nodes.

        Score components:
        - direct LOOKS_FOR edge
        - reverse CAN_SATISFY edge
        - feature overlap between user/supply local subgraphs
        """
        if not self.graph.has_node(user_id) or not self._is_user_node(user_id):
            return []

        candidates = self._candidate_supplies(domain=domain)
        user_features = self._collect_feature_nodes(user_id, max_depth=2)

        results: List[Dict[str, Any]] = []
        for supply_id in candidates:
            score = 0.0
            reasons: List[str] = []

            if self._has_relation(user_id, supply_id, "LOOKS_FOR"):
                score += 2.0
                reasons.append("direct_looks_for")
            if self._has_relation(supply_id, user_id, "CAN_SATISFY"):
                score += 2.0
                reasons.append("direct_can_satisfy")

            supply_features = self._collect_feature_nodes(supply_id, max_depth=2)
            overlap = sorted(user_features.intersection(supply_features))
            if overlap:
                overlap_score = min(3.0, 0.35 * len(overlap))
                score += overlap_score
                reasons.append(f"feature_overlap:{len(overlap)}")

            if score <= 0:
                continue

            results.append(
                {
                    "user_id": user_id,
                    "supply_id": supply_id,
                    "score": round(score, 6),
                    "reasons": reasons,
                    "overlap_nodes": overlap,
                    "supply": {
                        "label": self.graph.nodes[supply_id].get("label", "Supply"),
                        "properties": self._safe_props(self.graph.nodes[supply_id]),
                    },
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:topk]

    def supply_to_user(
        self,
        supply_id: str,
        topk: int = 20,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Match one supply node to user nodes."""
        if not self.graph.has_node(supply_id) or not self._is_supply_node(supply_id):
            return []

        candidates = self._candidate_users(domain=domain)
        supply_features = self._collect_feature_nodes(supply_id, max_depth=2)

        results: List[Dict[str, Any]] = []
        for user_id in candidates:
            score = 0.0
            reasons: List[str] = []

            if self._has_relation(user_id, supply_id, "LOOKS_FOR"):
                score += 2.0
                reasons.append("direct_looks_for")
            if self._has_relation(supply_id, user_id, "CAN_SATISFY"):
                score += 2.0
                reasons.append("direct_can_satisfy")

            user_features = self._collect_feature_nodes(user_id, max_depth=2)
            overlap = sorted(user_features.intersection(supply_features))
            if overlap:
                overlap_score = min(3.0, 0.35 * len(overlap))
                score += overlap_score
                reasons.append(f"feature_overlap:{len(overlap)}")

            if score <= 0:
                continue

            results.append(
                {
                    "supply_id": supply_id,
                    "user_id": user_id,
                    "score": round(score, 6),
                    "reasons": reasons,
                    "overlap_nodes": overlap,
                    "user": {
                        "label": self.graph.nodes[user_id].get("label", "User"),
                        "properties": self._safe_props(self.graph.nodes[user_id]),
                    },
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:topk]

    # ---------------------------------------------------------------------
    # Query APIs
    # ---------------------------------------------------------------------
    def traverse_neighbors(
        self,
        start_node: str,
        max_depth: int = 1,
        direction: str = "both",
        relation_types: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Breadth-first neighbor traversal.

        Args:
            start_node: Node id in the graph.
            max_depth: BFS max depth (>=1).
            direction: "out", "in", or "both".
            relation_types: optional relation type filter.

        Returns:
            Dict with visited nodes and traversed edges metadata.
        """
        if start_node not in self.graph:
            return {"nodes": [], "edges": []}
        if max_depth < 1:
            return {"nodes": [start_node], "edges": []}

        direction = direction.lower()
        if direction not in {"out", "in", "both"}:
            raise ValueError("direction must be one of: out, in, both")

        visited: Dict[str, int] = {start_node: 0}
        traversed_edges: List[Dict[str, Any]] = []
        queue: deque[Tuple[str, int]] = deque([(start_node, 0)])

        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for src, dst, edge_data in self._iter_edges(node_id, direction):
                rel_type = edge_data.get("type")
                if relation_types and rel_type not in relation_types:
                    continue

                next_node = dst if src == node_id else src
                next_depth = depth + 1
                if next_node not in visited or next_depth < visited[next_node]:
                    visited[next_node] = next_depth
                    queue.append((next_node, next_depth))

                traversed_edges.append(
                    {
                        "source": src,
                        "target": dst,
                        "type": rel_type,
                        "depth": next_depth,
                        "properties": self._safe_props(edge_data),
                    }
                )

        nodes = [
            {
                "id": nid,
                "depth": depth,
                "label": self.graph.nodes[nid].get("label", "Entity"),
                "properties": self._safe_props(self.graph.nodes[nid]),
            }
            for nid, depth in sorted(visited.items(), key=lambda x: x[1])
        ]
        return {"nodes": nodes, "edges": traversed_edges}

    def find_paths(
        self,
        source: str,
        target: str,
        max_hops: int = 4,
        relation_types: Optional[Set[str]] = None,
        direction: str = "out",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Find simple paths with edge-level relation constraints."""
        if source not in self.graph or target not in self.graph:
            return []
        if max_hops < 1:
            return []

        direction = direction.lower()
        if direction not in {"out", "in", "both"}:
            raise ValueError("direction must be one of: out, in, both")

        paths: List[Dict[str, Any]] = []

        def dfs(curr: str, visited_nodes: Set[str], node_path: List[str], edge_path: List[Dict[str, Any]]) -> None:
            if len(paths) >= limit:
                return
            if len(edge_path) > max_hops:
                return
            if curr == target and edge_path:
                paths.append(
                    {
                        "nodes": list(node_path),
                        "edges": list(edge_path),
                        "length": len(edge_path),
                    }
                )
                return

            for src, dst, edge_data in self._iter_edges(curr, direction):
                rel_type = edge_data.get("type")
                if relation_types and rel_type not in relation_types:
                    continue

                next_node = dst if src == curr else src
                if next_node in visited_nodes:
                    continue

                visited_nodes.add(next_node)
                node_path.append(next_node)
                edge_path.append(
                    {
                        "source": src,
                        "target": dst,
                        "type": rel_type,
                        "properties": self._safe_props(edge_data),
                    }
                )
                dfs(next_node, visited_nodes, node_path, edge_path)
                edge_path.pop()
                node_path.pop()
                visited_nodes.remove(next_node)

        dfs(source, {source}, [source], [])
        paths.sort(key=lambda x: x["length"])
        return paths

    def match_subgraph(self, pattern_graph: nx.DiGraph, limit: int = 20) -> List[Dict[str, str]]:
        """VF2 subgraph matching.

        Pattern graph conventions:
        - Node attrs can contain: label, properties(dict)
        - Edge attrs can contain: type
        """
        if pattern_graph.number_of_nodes() == 0:
            return []

        host = self._to_matchable_digraph()

        def node_match(host_attrs: Dict[str, Any], pattern_attrs: Dict[str, Any]) -> bool:
            label = pattern_attrs.get("label")
            if label and host_attrs.get("label") != label:
                return False

            props = pattern_attrs.get("properties", {})
            if isinstance(props, dict):
                for k, v in props.items():
                    if host_attrs.get(k) != v:
                        return False
            return True

        def edge_match(host_attrs: Dict[str, Any], pattern_attrs: Dict[str, Any]) -> bool:
            ptype = pattern_attrs.get("type")
            if not ptype:
                return True
            host_types = host_attrs.get("types", set())
            return ptype in host_types

        matcher = isomorphism.DiGraphMatcher(
            host,
            pattern_graph,
            node_match=node_match,
            edge_match=edge_match,
        )

        matches: List[Dict[str, str]] = []
        for mapping in matcher.subgraph_isomorphisms_iter():
            inverted = {pattern_node: host_node for host_node, pattern_node in mapping.items()}
            matches.append(inverted)
            if len(matches) >= limit:
                break
        return matches

    # ---------------------------------------------------------------------
    # Export APIs
    # ---------------------------------------------------------------------
    def export_cypher(self, output_path: Path | str) -> None:
        """Export graph to executable Neo4j Cypher script."""
        out = Path(output_path)
        lines: List[str] = [
            "// Auto-generated from Neo4jKnowledgeGraph (NetworkX)",
            "// Recommended: run in an empty DB or with uniqueness constraint on :Entity(id)",
            "",
        ]

        for node_id, attrs in self.graph.nodes(data=True):
            label = self._sanitize_label(attrs.get("label", "Entity"))
            merged = {"id": node_id}
            for k, v in attrs.items():
                if k == "label":
                    continue
                merged[k] = v

            lines.append(
                f"MERGE (n:{label} {{id: {self._cypher_literal(node_id)}}}) "
                f"SET n += {self._cypher_map(merged)};"
            )

        lines.append("")

        for src, dst, _, attrs in self.graph.edges(keys=True, data=True):
            rel_type = self._sanitize_rel_type(attrs.get("type", "RELATED_TO"))
            rel_props = {k: v for k, v in attrs.items() if k != "type"}
            lines.append(
                "MATCH (a {id: "
                + self._cypher_literal(src)
                + "}), (b {id: "
                + self._cypher_literal(dst)
                + "}) "
                + f"MERGE (a)-[r:{rel_type}]->(b) "
                + f"SET r += {self._cypher_map(rel_props)};"
            )

        out.write_text("\n".join(lines), encoding="utf-8")

    def export_graphml(self, output_path: Path | str) -> None:
        """Export graph to GraphML with GraphML-safe scalar attrs."""
        out = Path(output_path)
        graph_for_export = nx.MultiDiGraph(name=self.graph.graph.get("name", "knowledge_graph"))

        for node_id, attrs in self.graph.nodes(data=True):
            graph_for_export.add_node(node_id, **self._graphml_safe_attrs(attrs))

        for src, dst, key, attrs in self.graph.edges(keys=True, data=True):
            graph_for_export.add_edge(src, dst, key=key, **self._graphml_safe_attrs(attrs))

        nx.write_graphml(graph_for_export, out)

    # ---------------------------------------------------------------------
    # Utility APIs
    # ---------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        label_dist: Dict[str, int] = {}
        rel_dist: Dict[str, int] = {}

        for _, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", "Entity")
            label_dist[label] = label_dist.get(label, 0) + 1

        for _, _, attrs in self.graph.edges(data=True):
            rel = attrs.get("type", "RELATED_TO")
            rel_dist[rel] = rel_dist.get(rel, 0) + 1

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_labels": dict(sorted(label_dist.items(), key=lambda x: x[0])),
            "relation_types": dict(sorted(rel_dist.items(), key=lambda x: x[0])),
        }

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _is_user_node(self, node_id: str) -> bool:
        return self.graph.nodes[node_id].get("label") == "User" or str(node_id).startswith("User:")

    def _is_supply_node(self, node_id: str) -> bool:
        return self.graph.nodes[node_id].get("label") == "Supply" or str(node_id).startswith("Supply:")

    def _candidate_users(self, domain: Optional[str]) -> List[str]:
        users = []
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get("label") != "User":
                continue
            if domain and attrs.get("domain") != domain:
                continue
            users.append(node_id)
        return users

    def _candidate_supplies(self, domain: Optional[str]) -> List[str]:
        supplies = []
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get("label") != "Supply":
                continue
            if domain and attrs.get("domain") != domain:
                continue
            supplies.append(node_id)
        return supplies

    def _has_relation(self, source: str, target: str, rel_type: str) -> bool:
        edge_dict = self.graph.get_edge_data(source, target, default={})
        for attrs in edge_dict.values():
            if attrs.get("type") == rel_type:
                return True
        return False

    def _collect_feature_nodes(self, start_node: str, max_depth: int = 2) -> Set[str]:
        feature_nodes: Set[str] = set()
        queue: deque[Tuple[str, int]] = deque([(start_node, 0)])
        seen: Set[str] = {start_node}

        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for _, dst, _, edge_data in self.graph.out_edges(node_id, keys=True, data=True):
                if edge_data.get("type") in self.bridge_rel_types:
                    continue

                if dst not in seen:
                    seen.add(dst)
                    queue.append((dst, depth + 1))

                if dst != start_node:
                    feature_nodes.add(dst)

        return feature_nodes

    def _add_node(self, node_id: str, label: str, properties: Dict[str, Any]) -> None:
        clean_props = {k: v for k, v in properties.items() if v is not None}
        if self.graph.has_node(node_id):
            existing = self.graph.nodes[node_id]
            existing.update(clean_props)
            existing["label"] = existing.get("label", label)
            return

        attrs = {"label": label}
        attrs.update(clean_props)
        self.graph.add_node(node_id, **attrs)

    def _add_edge(self, source: str, target: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        clean_props = {k: v for k, v in (properties or {}).items() if v is not None}
        clean_props["type"] = rel_type
        self.graph.add_edge(source, target, **clean_props)

    def _iter_edges(self, node_id: str, direction: str) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
        if direction in {"out", "both"}:
            for _, dst, _, data in self.graph.out_edges(node_id, keys=True, data=True):
                yield node_id, dst, data
        if direction in {"in", "both"}:
            for src, _, _, data in self.graph.in_edges(node_id, keys=True, data=True):
                yield src, node_id, data

    def _to_matchable_digraph(self) -> nx.DiGraph:
        """Collapse MultiDiGraph to DiGraph while preserving edge type sets."""
        digraph = nx.DiGraph()

        for node_id, attrs in self.graph.nodes(data=True):
            flattened = dict(attrs)
            props = attrs.get("properties")
            if isinstance(props, dict):
                flattened.update(props)
            digraph.add_node(node_id, **flattened)

        for src, dst, attrs in self.graph.edges(data=True):
            rel_type = attrs.get("type")
            if digraph.has_edge(src, dst):
                digraph[src][dst]["types"].add(rel_type)
            else:
                digraph.add_edge(src, dst, types={rel_type})
        return digraph

    @staticmethod
    def _entity_id(entity_label: str, raw_value: Any) -> str:
        return f"{entity_label}:{raw_value}"

    @staticmethod
    def _safe_props(attrs: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        for k, v in attrs.items():
            if isinstance(v, (dict, list, tuple, set)):
                out[k] = json.dumps(v, ensure_ascii=False, sort_keys=True)
            else:
                out[k] = v
        return out

    @staticmethod
    def _graphml_safe_attrs(attrs: Dict[str, Any]) -> Dict[str, Any]:
        safe: Dict[str, Any] = {}
        for k, v in attrs.items():
            if isinstance(v, bool):
                safe[k] = int(v)
            elif isinstance(v, (int, float, str)) or v is None:
                safe[k] = "" if v is None else v
            else:
                safe[k] = json.dumps(v, ensure_ascii=False, sort_keys=True)
        return safe

    @staticmethod
    def _sanitize_label(label: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_]", "_", label or "Entity")
        if not clean:
            clean = "Entity"
        if clean[0].isdigit():
            clean = f"L_{clean}"
        return clean

    @staticmethod
    def _sanitize_rel_type(rel_type: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_]", "_", rel_type or "RELATED_TO").upper()
        if not clean:
            clean = "RELATED_TO"
        if clean[0].isdigit():
            clean = f"R_{clean}"
        return clean

    @staticmethod
    def _cypher_literal(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, tuple, set)):
            inner = ", ".join(Neo4jKnowledgeGraph._cypher_literal(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, dict):
            return Neo4jKnowledgeGraph._cypher_map(value)

        s = str(value).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{s}'"

    @staticmethod
    def _cypher_map(data: Dict[str, Any]) -> str:
        parts = [f"{k}: {Neo4jKnowledgeGraph._cypher_literal(v)}" for k, v in data.items()]
        return "{" + ", ".join(parts) + "}"


def build_neo4j_knowledge_graph(goldset_dir: Path | str) -> Neo4jKnowledgeGraph:
    """Convenience builder for goldset_v0_1."""
    kg = Neo4jKnowledgeGraph()
    kg.load_from_goldset(goldset_dir)
    return kg


def make_pattern_graph(
    nodes: Sequence[Tuple[str, str, Optional[Dict[str, Any]]]],
    edges: Sequence[Tuple[str, str, Optional[str]]],
) -> nx.DiGraph:
    """Build a pattern graph for subgraph matching.

    Args:
        nodes: [(pattern_id, label, properties_dict)]
        edges: [(src_pattern_id, dst_pattern_id, rel_type_or_none)]
    """
    g = nx.DiGraph()
    for node_id, label, props in nodes:
        g.add_node(node_id, label=label, properties=props or {})
    for src, dst, rel_type in edges:
        edge_attrs = {}
        if rel_type:
            edge_attrs["type"] = rel_type
        g.add_edge(src, dst, **edge_attrs)
    return g


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "goldset_v0_1"
    kg = build_neo4j_knowledge_graph(root)

    print("[summary]", json.dumps(kg.summary(), ensure_ascii=False, indent=2))

    demo_start = next(iter(kg.graph.nodes))
    print("[neighbors]", json.dumps(kg.traverse_neighbors(demo_start, max_depth=1), ensure_ascii=False)[:300], "...")

    node_ids = list(kg.graph.nodes)
    if len(node_ids) >= 2:
        paths = kg.find_paths(node_ids[0], node_ids[1], max_hops=3, limit=3)
        print("[paths]", json.dumps(paths, ensure_ascii=False)[:300], "...")

    pattern = make_pattern_graph(
        nodes=[("u", "User", None), ("i", "Intent", None)],
        edges=[("u", "i", "HAS_INTENT")],
    )
    matches = kg.match_subgraph(pattern, limit=5)
    print("[match_count]", len(matches))

    user_nodes = [n for n, a in kg.graph.nodes(data=True) if a.get("label") == "User"]
    supply_nodes = [n for n, a in kg.graph.nodes(data=True) if a.get("label") == "Supply"]

    if user_nodes:
        print("[user_to_supply]", json.dumps(kg.user_to_supply(user_nodes[0], topk=3), ensure_ascii=False)[:300], "...")
    if supply_nodes:
        print("[supply_to_user]", json.dumps(kg.supply_to_user(supply_nodes[0], topk=3), ensure_ascii=False)[:300], "...")

    out_dir = Path(__file__).resolve().parent
    kg.export_cypher(out_dir / "neo4j_graph.cypher")
    kg.export_graphml(out_dir / "neo4j_graph.graphml")
    print("[exported] neo4j_graph.cypher, neo4j_graph.graphml")
