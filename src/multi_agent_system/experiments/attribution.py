from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AttributionModel:
    """Simplified revenue attribution for offline simulation."""

    channel_weights: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.channel_weights is None:
            self.channel_weights = {
                "search": 0.5,
                "mini_program": 0.35,
                "recommendation": 0.15,
            }

    def attribute(self, events: list[dict[str, Any]], order_value_map: dict[str, float]) -> dict[str, Any]:
        by_channel: dict[str, float] = {k: 0.0 for k in self.channel_weights}
        total = 0.0
        for e in events:
            if e.get("event_type") != "order":
                continue
            sid = e.get("supply_id")
            value = order_value_map.get(sid, 0.0)
            channel = e.get("context", {}).get("channel", "search")
            weight = self.channel_weights.get(channel, 0.1)
            attributed = value * weight
            by_channel[channel] = by_channel.get(channel, 0.0) + attributed
            total += attributed
        return {"attributed_revenue": round(total, 4), "by_channel": by_channel}
