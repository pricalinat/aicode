from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FeedbackLoop:
    """Apply offline evaluation feedback to feature weights."""

    positive_boost: float = 0.12
    negative_penalty: float = 0.1

    def apply(
        self,
        feature_map: dict[str, dict[str, Any]],
        evaluation: dict[str, dict[str, float]],
    ) -> dict[str, dict[str, Any]]:
        for sid, feat in feature_map.items():
            metrics = evaluation.get(sid, {})
            reward = metrics.get("reward", 0.0)
            risk_violation = metrics.get("risk_violation", 0.0)
            delta = reward * self.positive_boost - risk_violation * self.negative_penalty
            feat["train_weight"] = round(max(0.1, min(3.0, feat.get("train_weight", 1.0) + delta)), 4)
            feat["reward"] = reward
            feat["risk_violation"] = risk_violation
        return feature_map
