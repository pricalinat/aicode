from __future__ import annotations

import math
from typing import Any


class OfflineMetrics:
    @staticmethod
    def recall_at_k(recommended: list[str], relevant: set[str], k: int = 5) -> float:
        if not relevant:
            return 0.0
        top_k = recommended[:k]
        hit = len([x for x in top_k if x in relevant])
        return hit / len(relevant)

    @staticmethod
    def ndcg_at_k(recommended: list[str], relevance_map: dict[str, float], k: int = 5) -> float:
        dcg = 0.0
        for idx, item in enumerate(recommended[:k], start=1):
            rel = relevance_map.get(item, 0.0)
            dcg += (2**rel - 1) / math.log2(idx + 1)

        ideal_items = sorted(relevance_map.items(), key=lambda kv: kv[1], reverse=True)
        idcg = 0.0
        for idx, (_, rel) in enumerate(ideal_items[:k], start=1):
            idcg += (2**rel - 1) / math.log2(idx + 1)
        return 0.0 if idcg == 0 else dcg / idcg

    @staticmethod
    def conversion_proxy(events: list[dict[str, Any]]) -> float:
        click = len([e for e in events if e.get("event_type") == "click"])
        order = len([e for e in events if e.get("event_type") == "order"])
        return order / click if click else 0.0

    @staticmethod
    def coverage(unique_recommended: set[str], total_catalog: int) -> float:
        return 0.0 if total_catalog <= 0 else len(unique_recommended) / total_catalog

    @staticmethod
    def risk_violation_rate(results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        violations = len([r for r in results if r.get("risk_violated")])
        return violations / len(results)
