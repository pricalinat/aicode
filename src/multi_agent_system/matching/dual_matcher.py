from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import SupplyEntityType


_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass
class DualMatcher:
    """Bidirectional matcher: user->supply and supply->users.

    Scoring combines:
    1) KG retrieval candidates
    2) Feature-based ranking
    3) Strategy/risk constraints
    """

    db: SupplyGraphDatabase
    feature_map: dict[str, dict[str, Any]]

    def match_supply_for_user(self, user_id: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        context = context or {}
        user = self.db.get_entity(user_id)
        if user is None:
            return []

        top_k = int(context.get("top_k", 5))
        risk_tolerance = context.get("risk_tolerance", user.properties.get("risk_tolerance", "medium"))
        preferred_categories = context.get("preferred_categories", user.properties.get("preferred_categories", []))

        candidates = self._kg_supply_candidates(preferred_categories)
        scored = []
        for supply in candidates:
            feat = self.feature_map.get(supply.id, {})
            risk_level = feat.get("risk_level", supply.properties.get("risk_level", "medium"))
            if _RISK_ORDER.get(risk_level, 1) > _RISK_ORDER.get(risk_tolerance, 1):
                continue
            score = self._score_supply_for_user(supply.id, preferred_categories, context)
            scored.append({"supply_id": supply.id, "score": score, "risk_level": risk_level})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def match_users_for_supply(self, supply_id: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        context = context or {}
        supply = self.db.get_entity(supply_id)
        if supply is None:
            return []

        top_k = int(context.get("top_k", 5))
        max_risk_level = context.get("max_risk_level", supply.properties.get("risk_level", "medium"))
        users = self.db.query_by_type(SupplyEntityType.USER)
        scored = []
        for user in users:
            user_tol = user.properties.get("risk_tolerance", "medium")
            # Policy: ensure user's tolerance >= supply required risk
            if _RISK_ORDER.get(user_tol, 1) < _RISK_ORDER.get(max_risk_level, 1):
                continue
            pref = user.properties.get("preferred_categories", [])
            score = self._score_user_for_supply(user.id, supply_id, pref)
            scored.append({"user_id": user.id, "score": score, "risk_tolerance": user_tol})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _kg_supply_candidates(self, preferred_categories: list[str]) -> list[Any]:
        candidates = self.db.query_by_type(SupplyEntityType.PRODUCT)
        if not preferred_categories:
            return candidates
        return [
            c
            for c in candidates
            if c.properties.get("category") in preferred_categories
        ] or candidates

    def _score_supply_for_user(self, supply_id: str, preferred_categories: list[str], context: dict[str, Any]) -> float:
        feat = self.feature_map.get(supply_id, {})
        category = feat.get("category")
        score = 0.0
        score += 0.35 * feat.get("quality_score", 0.5)
        score += 0.25 * feat.get("ctr", 0.0)
        score += 0.2 * feat.get("cvr_proxy", 0.0)
        score += 0.2 * min(1.0, feat.get("train_weight", 1.0) / 2.0)
        if category in preferred_categories:
            score += 0.12
        if context.get("boost_category") == category:
            score += 0.08
        return round(score, 6)

    def _score_user_for_supply(self, user_id: str, supply_id: str, preferred_categories: list[str]) -> float:
        feat = self.feature_map.get(supply_id, {})
        score = 0.4 * feat.get("cvr_proxy", 0.0) + 0.3 * feat.get("ctr", 0.0)
        score += 0.3 * min(1.0, feat.get("quality_score", 0.5))
        if feat.get("category") in preferred_categories:
            score += 0.15
        if user_id.endswith("0"):
            score += 0.01  # deterministic tie-breaker in offline mode
        return round(score, 6)
