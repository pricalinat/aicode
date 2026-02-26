from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .attribution import AttributionModel
from .metrics import OfflineMetrics


@dataclass
class OfflineABRunner:
    """Offline A/B simulator for ranking strategies."""

    output_dir: Path

    def run(
        self,
        baseline: dict[str, list[str]],
        treatment: dict[str, list[str]],
        relevance: dict[str, dict[str, float]],
        events: list[dict[str, Any]],
        order_value_map: dict[str, float],
        report_name: str = "ab_report.json",
    ) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        baseline_ndcg = self._avg_ndcg(baseline, relevance)
        treatment_ndcg = self._avg_ndcg(treatment, relevance)

        baseline_recall = self._avg_recall(baseline, relevance)
        treatment_recall = self._avg_recall(treatment, relevance)

        attr = AttributionModel().attribute(events, order_value_map)
        conversion = OfflineMetrics.conversion_proxy(events)

        unique_baseline = {sid for rec in baseline.values() for sid in rec}
        unique_treat = {sid for rec in treatment.values() for sid in rec}
        catalog_size = max(1, len(unique_baseline | unique_treat))

        report = {
            "baseline": {
                "ndcg@5": baseline_ndcg,
                "recall@5": baseline_recall,
                "coverage": OfflineMetrics.coverage(unique_baseline, catalog_size),
            },
            "treatment": {
                "ndcg@5": treatment_ndcg,
                "recall@5": treatment_recall,
                "coverage": OfflineMetrics.coverage(unique_treat, catalog_size),
            },
            "delta": {
                "ndcg@5": treatment_ndcg - baseline_ndcg,
                "recall@5": treatment_recall - baseline_recall,
            },
            "proxy": {
                "conversion": conversion,
                "attribution": attr,
            },
        }

        output = self.output_dir / report_name
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def _avg_ndcg(self, recs: dict[str, list[str]], rel: dict[str, dict[str, float]]) -> float:
        values = [OfflineMetrics.ndcg_at_k(items, rel.get(uid, {}), 5) for uid, items in recs.items()]
        return sum(values) / len(values) if values else 0.0

    def _avg_recall(self, recs: dict[str, list[str]], rel: dict[str, dict[str, float]]) -> float:
        values = []
        for uid, items in recs.items():
            relevant = {sid for sid, score in rel.get(uid, {}).items() if score > 0}
            values.append(OfflineMetrics.recall_at_k(items, relevant, 5))
        return sum(values) / len(values) if values else 0.0
