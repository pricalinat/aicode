from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any


@dataclass
class SyntheticSupplyGenerator:
    """Generate deterministic synthetic supply-side entities for offline demos."""

    seed: int = 42

    def generate(
        self,
        num_supplies: int = 20,
        num_users: int = 12,
        categories: list[str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        rng = Random(self.seed)
        cats = categories or ["electronics", "home", "food", "apparel", "services"]
        risk_levels = ["low", "medium", "high"]

        supplies: list[dict[str, Any]] = []
        for i in range(num_supplies):
            category = cats[i % len(cats)]
            risk_level = risk_levels[(i + rng.randint(0, 5)) % len(risk_levels)]
            quality = round(0.55 + (i % 5) * 0.08 + rng.random() * 0.1, 3)
            price = round(19 + i * 3 + rng.random() * 40, 2)
            supplies.append(
                {
                    "supply_id": f"supply_{i:03d}",
                    "name": f"{category.title()} Offer {i}",
                    "category": category,
                    "merchant_id": f"merchant_{i % 6:02d}",
                    "region": ["CN", "US", "EU"][i % 3],
                    "price": price,
                    "quality_score": min(0.99, quality),
                    "risk_level": risk_level,
                    "tags": [category, "demo", "offline"],
                }
            )

        users: list[dict[str, Any]] = []
        for i in range(num_users):
            pref = cats[(i + 1) % len(cats)]
            users.append(
                {
                    "user_id": f"user_{i:03d}",
                    "tier": ["new", "active", "vip"][i % 3],
                    "preferred_categories": [pref, cats[(i + 2) % len(cats)]],
                    "risk_tolerance": ["low", "medium", "high"][i % 3],
                    "region": ["CN", "US", "EU"][i % 3],
                }
            )

        return {"supplies": supplies, "users": users}
