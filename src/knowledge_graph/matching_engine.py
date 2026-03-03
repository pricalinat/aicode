"""Bidirectional matching engine for user-intent and supply-capability graphs.

This module connects:
- UserIntentGraph (human demand side)
- SupplyCapacityGraph (supply capability side)

Data source: goldset_v0_1 (gold_ecom.jsonl + gold_miniapp.jsonl)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .supply_capacity_graph import SupplyCapacityGraph
from .user_intent_graph import UserIntentGraph


@dataclass
class MatchingEngineConfig:
    topk_candidates: int = 200
    user_supply_weight: float = 0.75
    rule_bonus_weight: float = 0.25
    min_score_threshold: float = -1.0


@dataclass
class MatchResult:
    user_id: Optional[str]
    supply_id: Optional[str]
    score: float
    vector_score: float
    rule_score: float
    reasons: List[str]
    payload: Dict[str, Any]


class BidirectionalMatchingEngine:
    """Two-way matching engine:

    1) user_to_supply: human seeks supply
    2) supply_to_user: supply seeks users
    """

    def __init__(
        self,
        user_graph: Optional[UserIntentGraph] = None,
        supply_graph: Optional[SupplyCapacityGraph] = None,
        config: Optional[MatchingEngineConfig] = None,
    ) -> None:
        self.user_graph = user_graph or UserIntentGraph()
        self.supply_graph = supply_graph or SupplyCapacityGraph()
        self.config = config or MatchingEngineConfig()

        self.records_by_id: Dict[str, Dict[str, Any]] = {}
        self.user_ids: List[str] = []
        self.supply_ids: List[str] = []

    # ---------- Build ----------
    def load_from_goldset(self, goldset_dir: Path | str) -> None:
        root = Path(goldset_dir)
        self.user_graph.load_from_goldset(root)
        self.supply_graph.load_from_goldset(root)

        self.records_by_id = {}
        self.user_ids = []
        self.supply_ids = []

        for name in ("gold_ecom.jsonl", "gold_miniapp.jsonl"):
            file_path = root / name
            if not file_path.exists():
                continue
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    rid = rec["id"]
                    self.records_by_id[rid] = rec
                    self.user_ids.append(rid)
                    self.supply_ids.append(rid)

    # ---------- Public APIs ----------
    def user_to_supply(
        self,
        query: str,
        hint: Optional[Dict[str, Any]] = None,
        topk: int = 20,
    ) -> List[MatchResult]:
        """Match a new user query to supply items/services."""
        user_vec = self.user_graph.encode_query_as_user(query, hint=hint)

        candidates = self._recall_supply_by_vector(user_vec, self.config.topk_candidates)
        results: List[MatchResult] = []

        for supply_id, vector_score in candidates:
            rec = self.records_by_id.get(supply_id)
            if rec is None:
                continue

            rule_score, reasons = self._score_user_to_supply_rules(rec, hint or {}, query=query)
            final_score = self._fuse_score(vector_score, rule_score)
            if final_score < self.config.min_score_threshold:
                continue

            results.append(
                MatchResult(
                    user_id=None,
                    supply_id=supply_id,
                    score=final_score,
                    vector_score=vector_score,
                    rule_score=rule_score,
                    reasons=reasons,
                    payload=rec,
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:topk]

    def supply_to_user(
        self,
        supply_id: Optional[str] = None,
        supply_record: Optional[Dict[str, Any]] = None,
        topk: int = 20,
    ) -> List[MatchResult]:
        """Match one supply item/service to potential users."""
        if supply_id is None and supply_record is None:
            raise ValueError("either supply_id or supply_record must be provided")

        if supply_record is None:
            supply_record = self.records_by_id.get(supply_id or "")
            if supply_record is None:
                return []

        if supply_id is None:
            supply_id = supply_record.get("id")

        supply_vec = self._encode_supply_from_record(supply_record)
        candidates = self._recall_users_by_vector(supply_vec, self.config.topk_candidates)

        results: List[MatchResult] = []
        for user_id, vector_score in candidates:
            rec = self.records_by_id.get(user_id)
            if rec is None:
                continue

            rule_score, reasons = self._score_supply_to_user_rules(supply_record, rec)
            final_score = self._fuse_score(vector_score, rule_score)
            if final_score < self.config.min_score_threshold:
                continue

            results.append(
                MatchResult(
                    user_id=user_id,
                    supply_id=supply_id,
                    score=final_score,
                    vector_score=vector_score,
                    rule_score=rule_score,
                    reasons=reasons,
                    payload=rec,
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:topk]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "records": len(self.records_by_id),
            "users": len(self.user_ids),
            "supplies": len(self.supply_ids),
            "user_graph": self.user_graph.get_statistics(),
            "supply_graph": self.supply_graph.get_statistics(),
        }

    # ---------- Recall ----------
    def _recall_supply_by_vector(self, user_vec: np.ndarray, topk: int) -> List[Tuple[str, float]]:
        scores = []
        for sid in self.supply_ids:
            emb = self.supply_graph.get_supply_embedding(sid)
            score = self._cosine(user_vec, emb)
            scores.append((sid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:topk]

    def _recall_users_by_vector(self, supply_vec: np.ndarray, topk: int) -> List[Tuple[str, float]]:
        scores = []
        for uid in self.user_ids:
            emb = self.user_graph.get_user_embedding(uid)
            score = self._cosine(supply_vec, emb)
            scores.append((uid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:topk]

    # ---------- Rule scoring ----------
    def _score_user_to_supply_rules(
        self,
        supply_rec: Dict[str, Any],
        hint: Dict[str, Any],
        query: str,
    ) -> Tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        label = supply_rec.get("label", {})
        domain = supply_rec.get("domain", "")

        hint_intent = hint.get("intent")
        if hint_intent and hint_intent == label.get("intent"):
            score += 1.0
            reasons.append("intent_match")

        hint_domain = hint.get("domain")
        if hint_domain and hint_domain == domain:
            score += 0.6
            reasons.append("domain_match")

        if domain == "ecommerce":
            product = supply_rec.get("product", {})

            target_category = hint.get("target_category")
            if target_category and (
                target_category == product.get("category_lv2") or target_category == label.get("target_category")
            ):
                score += 1.2
                reasons.append("category_match")

            price_range = hint.get("price_range")
            if price_range:
                p = float(product.get("price", 0.0))
                pmin = float(price_range.get("min", -1e18))
                pmax = float(price_range.get("max", 1e18))
                if pmin <= p <= pmax:
                    score += 1.0
                    reasons.append("price_in_range")
                else:
                    score -= 0.8
                    reasons.append("price_out_of_range")

            attrs = product.get("attributes", {})
            must_have = set(hint.get("must_have", []))
            if must_have:
                matched = 0
                for item in must_have:
                    if item in attrs.values() or item in attrs.keys():
                        matched += 1
                if matched:
                    score += 1.2 * (matched / max(1, len(must_have)))
                    reasons.append("must_have_partial_match")

            exclude = set(hint.get("exclude", []))
            if exclude:
                violated = sum(1 for x in exclude if x in attrs.values() or x in attrs.keys())
                if violated > 0:
                    score -= 1.0 * violated
                    reasons.append("exclude_violated")

        if domain == "miniapp_service":
            service = supply_rec.get("service", {})
            city = hint.get("city")
            if city and city == service.get("city"):
                score += 1.0
                reasons.append("city_match")

            req_slots = set(hint.get("required_slots", []))
            supply_slots = set(label.get("required_slots", []))
            if req_slots:
                overlap = len(req_slots & supply_slots)
                score += 1.0 * (overlap / max(1, len(req_slots)))
                if overlap:
                    reasons.append("slot_overlap")

            pre = set(hint.get("preconditions", []))
            supply_pre = set(label.get("preconditions", []))
            if pre:
                overlap = len(pre & supply_pre)
                score += 0.7 * (overlap / max(1, len(pre)))
                if overlap:
                    reasons.append("precondition_overlap")

            expected_action = hint.get("expected_action")
            if expected_action and expected_action == label.get("expected_action"):
                score += 0.8
                reasons.append("expected_action_match")

        inferred_intent = self.user_graph._infer_intent(query)
        if inferred_intent == label.get("intent"):
            score += 0.3
            reasons.append("query_intent_heuristic_match")

        return score, reasons

    def _score_supply_to_user_rules(
        self,
        supply_rec: Dict[str, Any],
        user_rec: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        s_label = supply_rec.get("label", {})
        u_label = user_rec.get("label", {})

        if s_label.get("intent") == u_label.get("intent"):
            score += 1.2
            reasons.append("intent_match")

        if supply_rec.get("domain") == user_rec.get("domain"):
            score += 0.8
            reasons.append("domain_match")

        if supply_rec.get("domain") == "ecommerce" and user_rec.get("domain") == "ecommerce":
            sp = supply_rec.get("product", {})
            up = user_rec.get("label", {})
            user_cat = up.get("target_category")
            if user_cat and user_cat == sp.get("category_lv2"):
                score += 1.2
                reasons.append("category_match")

            user_price = up.get("price_range")
            if user_price:
                p = float(sp.get("price", 0.0))
                pmin = float(user_price.get("min", -1e18))
                pmax = float(user_price.get("max", 1e18))
                if pmin <= p <= pmax:
                    score += 1.0
                    reasons.append("price_fit")
                else:
                    score -= 0.8
                    reasons.append("price_mismatch")

            attrs = sp.get("attributes", {})
            must = set(up.get("must_have", []))
            if must:
                hit = sum(1 for x in must if x in attrs.values() or x in attrs.keys())
                score += 1.0 * (hit / max(1, len(must)))
                if hit:
                    reasons.append("must_have_fit")

            excl = set(up.get("exclude", []))
            bad = sum(1 for x in excl if x in attrs.values() or x in attrs.keys())
            if bad:
                score -= 1.0 * bad
                reasons.append("exclude_violation")

        if supply_rec.get("domain") == "miniapp_service" and user_rec.get("domain") == "miniapp_service":
            ss = supply_rec.get("service", {})
            us = user_rec.get("service", {})

            if ss.get("city") and ss.get("city") == us.get("city"):
                score += 1.0
                reasons.append("city_match")

            if ss.get("category") and ss.get("category") == us.get("category"):
                score += 1.0
                reasons.append("service_category_match")

            s_slots = set(s_label.get("required_slots", []))
            u_slots = set(u_label.get("required_slots", []))
            if u_slots:
                ov = len(s_slots & u_slots)
                score += 0.8 * (ov / max(1, len(u_slots)))
                if ov:
                    reasons.append("slot_fit")

            s_pre = set(s_label.get("preconditions", []))
            u_pre = set(u_label.get("preconditions", []))
            if u_pre:
                ov = len(s_pre & u_pre)
                score += 0.6 * (ov / max(1, len(u_pre)))
                if ov:
                    reasons.append("precondition_fit")

        return score, reasons

    # ---------- Helpers ----------
    def _encode_supply_from_record(self, record: Dict[str, Any]) -> np.ndarray:
        temp_id = record.get("id")
        if temp_id and temp_id in self.supply_graph.supply_embeddings:
            return self.supply_graph.get_supply_embedding(temp_id)

        # If it's an ad-hoc record not in graph, build a temporary node by reusing graph logic.
        self.supply_graph.add_record(record)
        temp_id = record["id"]
        return self.supply_graph.get_supply_embedding(temp_id)

    def _fuse_score(self, vector_score: float, rule_score: float) -> float:
        w_vec = self.config.user_supply_weight
        w_rule = self.config.rule_bonus_weight
        return w_vec * float(vector_score) + w_rule * float(rule_score)

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return 0.0
        return float(np.dot(a, b) / (na * nb))


__all__ = [
    "MatchingEngineConfig",
    "MatchResult",
    "BidirectionalMatchingEngine",
]
