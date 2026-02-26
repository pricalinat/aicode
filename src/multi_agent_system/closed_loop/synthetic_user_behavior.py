from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Any


EVENT_CHAIN = ["impression", "click", "favorite", "add_to_cart", "order", "consult"]


@dataclass
class SyntheticUserBehaviorGenerator:
    """Generate deterministic user event streams for offline training/eval."""

    seed: int = 7

    def generate(
        self,
        users: list[dict[str, Any]],
        supplies: list[dict[str, Any]],
        days: int = 2,
        max_events_per_user_per_day: int = 30,
    ) -> list[dict[str, Any]]:
        rng = Random(self.seed)
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events: list[dict[str, Any]] = []

        for day in range(days):
            day_base = base_time + timedelta(days=day)
            for user in users:
                event_count = rng.randint(max(5, max_events_per_user_per_day // 3), max_events_per_user_per_day)
                for eidx in range(event_count):
                    supply = supplies[rng.randrange(0, len(supplies))]
                    stage_limit = self._stage_limit(user, supply, rng)
                    for stage in range(stage_limit):
                        evt_time = day_base + timedelta(minutes=eidx * 13 + stage)
                        events.append(
                            {
                                "event_id": f"evt_{day}_{user['user_id']}_{eidx}_{stage}",
                                "timestamp": evt_time.isoformat(),
                                "user_id": user["user_id"],
                                "supply_id": supply["supply_id"],
                                "event_type": EVENT_CHAIN[stage],
                                "context": {
                                    "region": user.get("region"),
                                    "channel": "mini_program" if eidx % 2 == 0 else "search",
                                },
                            }
                        )
        return events

    def _stage_limit(self, user: dict[str, Any], supply: dict[str, Any], rng: Random) -> int:
        score = 1
        if supply["category"] in user.get("preferred_categories", []):
            score += 2
        if user.get("region") == supply.get("region"):
            score += 1
        if supply.get("risk_level") == "high" and user.get("risk_tolerance") == "low":
            score -= 1
        score += rng.randint(0, 2)
        return max(1, min(len(EVENT_CHAIN), score))
