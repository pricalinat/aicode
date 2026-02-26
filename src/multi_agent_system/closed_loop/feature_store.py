from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureStore:
    """Aggregate supply + behavior into lightweight offline training features."""

    features: dict[str, dict[str, Any]] = field(default_factory=dict)

    def build(
        self,
        supplies: list[dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        by_supply: dict[str, Counter[str]] = defaultdict(Counter)
        unique_users: dict[str, set[str]] = defaultdict(set)

        for event in events:
            sid = event["supply_id"]
            by_supply[sid][event["event_type"]] += 1
            unique_users[sid].add(event["user_id"])

        output: dict[str, dict[str, Any]] = {}
        for supply in supplies:
            sid = supply["supply_id"]
            counter = by_supply[sid]
            impressions = counter.get("impression", 0)
            clicks = counter.get("click", 0)
            orders = counter.get("order", 0)
            output[sid] = {
                "supply_id": sid,
                "category": supply.get("category"),
                "quality_score": supply.get("quality_score", 0.5),
                "risk_level": supply.get("risk_level", "medium"),
                "price": supply.get("price", 0.0),
                "impression_cnt": impressions,
                "click_cnt": clicks,
                "favorite_cnt": counter.get("favorite", 0),
                "cart_cnt": counter.get("add_to_cart", 0),
                "order_cnt": orders,
                "consult_cnt": counter.get("consult", 0),
                "ctr": (clicks / impressions) if impressions else 0.0,
                "cvr_proxy": (orders / clicks) if clicks else 0.0,
                "coverage_user_cnt": len(unique_users[sid]),
                "train_weight": 1.0,
            }
        self.features = output
        return output

    def snapshot(self) -> list[dict[str, Any]]:
        return list(self.features.values())
