"""E-commerce Knowledge Graph - User Profile Graph.

Provides user profile representation, behavior tracking, and preferences
for e-commerce scenarios.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class UserType(Enum):
    """User types."""
    SHOPPER = "shopper"
    VIP = "vip"
    WHOLESALE = "wholesale"
    NEW = "new"


class UserSegment(Enum):
    """User segments."""
    PRICE_SENSITIVE = "price_sensitive"
    QUALITY_ORIENTED = "quality_oriented"
    BRAND_LOYAL = "brand_loyal"
    BARGAIN_HUNTER = "bargain_hunter"
    INDECISIVE = "indecisive"


@dataclass
class UserProfile:
    """User profile entity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: str = ""  # External user ID

    # Basic info
    name: str = ""
    email: str = ""
    phone: str = ""
    age: int = 0
    gender: str = ""  # male, female, other

    # E-commerce
    user_type: UserType = UserType.NEW
    segments: list[UserSegment] = field(default_factory=list)

    # Preferences
    price_sensitivity: float = 0.5  # 0-1
    quality_preference: float = 0.5  # 0-1
    brand_preferences: list[str] = field(default_factory=list)
    category_preferences: list[str] = field(default_factory=list)
    color_preferences: list[str] = field(default_factory=list)

    # Shopping behavior
    avg_order_value: float = 0.0
    order_frequency: float = 0.0  # orders per month
    last_order_date: datetime | None = None

    # Engagement
    total_spent: float = 0.0
    total_orders: int = 0
    return_rate: float = 0.0  # 0-1

    # Tags
    tags: list[str] = field(default_factory=list)

    # Trust score
    trust_score: float = 0.5  # 0-1

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserBehavior:
    """User behavior record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: str = ""

    # Behavior type
    behavior_type: str = ""  # view, search, click, add_to_cart, purchase

    # Target
    target_type: str = ""  # product, category, brand
    target_id: str = ""
    target_name: str = ""

    # Context
    query: str = ""  # Search query if any
    source: str = ""  # source channel
    session_id: str = ""

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: int = 0  # Time spent

    # Outcome
    converted: bool = False


@dataclass
class UserPreference:
    """User preference."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: str = ""

    category: str = ""
    attribute: str = ""
    value: Any = None
    strength: float = 1.0  # 0-1, how strong the preference

    source: str = ""  # explicit, inferred, observed
    created_at: datetime = field(default_factory=datetime.now)


class UserGraph:
    """User profile knowledge graph.

    Features:
    - User profile management
    - Behavior tracking
    - Preference inference
    - Segment classification
    """

    def __init__(self) -> None:
        """Initialize user graph."""
        self._users: dict[str, UserProfile] = {}
        self._behaviors: list[UserBehavior] = []
        self._preferences: dict[str, list[UserPreference]] = {}  # user_id -> prefs
        self._by_segment: dict[UserSegment, set[str]] = {}

    def add_user(self, profile: UserProfile) -> UserProfile:
        """Add user to graph."""
        self._users[profile.id] = profile

        # Index by segment
        for segment in profile.segments:
            if segment not in self._by_segment:
                self._by_segment[segment] = set()
            self._by_segment[segment].add(profile.id)

        return profile

    def get_user(self, user_id: str) -> UserProfile | None:
        """Get user by ID."""
        return self._users.get(user_id)

    def record_behavior(self, behavior: UserBehavior) -> None:
        """Record user behavior."""
        self._behaviors.append(behavior)

        # Update user profile based on behavior
        user = self._users.get(behavior.user_id)
        if user:
            user.updated_at = datetime.now()

            if behavior.behavior_type == "purchase":
                user.total_orders += 1

    def add_preference(
        self,
        user_id: str,
        category: str,
        attribute: str,
        value: Any,
        strength: float = 1.0,
    ) -> UserPreference | None:
        """Add user preference."""
        if user_id not in self._users:
            return None

        pref = UserPreference(
            user_id=user_id,
            category=category,
            attribute=attribute,
            value=value,
            strength=strength,
        )

        if user_id not in self._preferences:
            self._preferences[user_id] = []
        self._preferences[user_id].append(pref)

        return pref

    def get_preferences(self, user_id: str) -> list[UserPreference]:
        """Get user preferences."""
        return self._preferences.get(user_id, [])

    def infer_segments(self, user_id: str) -> list[UserSegment]:
        """Infer user segments based on behavior."""
        user = self._users.get(user_id)
        if not user:
            return []

        segments = []

        # Price sensitive
        if user.price_sensitivity > 0.7:
            segments.append(UserSegment.PRICE_SENSITIVE)

        # Quality oriented
        if user.quality_preference > 0.7:
            segments.append(UserSegment.QUALITY_ORIENTED)

        # Brand loyal
        if len(user.brand_preferences) > 3:
            segments.append(UserSegment.BRAND_LOYAL)

        # Bargain hunter
        if user.avg_order_value < 100 and user.order_frequency > 5:
            segments.append(UserSegment.BARGAIN_HUNTER)

        # Update user
        user.segments = segments
        return segments

    def get_by_segment(self, segment: UserSegment) -> list[UserProfile]:
        """Get users by segment."""
        ids = self._by_segment.get(segment, set())
        return [self._users[i] for i in ids if i in self._users]

    def get_similar_users(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[UserProfile]:
        """Find similar users."""
        user = self._users.get(user_id)
        if not user:
            return []

        # Calculate similarity based on preferences
        similarities = []

        for other_id, other in self._users.items():
            if other_id == user_id:
                continue

            # Simple similarity: shared preferences
            user_prefs = set((p.category, p.attribute) for p in self._preferences.get(user_id, []))
            other_prefs = set((p.category, p.attribute) for p in self._preferences.get(other_id, []))

            if user_prefs & other_prefs:
                score = len(user_prefs & other_prefs) / len(user_prefs | other_prefs)
                similarities.append((other, score))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [u for u, s in similarities[:limit]]

    def recommend_for_user(
        self,
        user_id: str,
        categories: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Generate recommendations for user."""
        user = self._users.get(user_id)
        if not user:
            return {}

        recs = {
            "user_id": user_id,
            "recommended_categories": [],
            "price_range": {},
            "brands": [],
        }

        # Based on category preferences
        if categories:
            recs["recommended_categories"] = categories
        else:
            recs["recommended_categories"] = user.category_preferences[:5]

        # Price range based on avg order value
        recs["price_range"] = {
            "min": user.avg_order_value * 0.7,
            "max": user.avg_order_value * 1.3,
        }

        # Preferred brands
        recs["brands"] = user.brand_preferences[:5]

        return recs

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_users": len(self._users),
            "total_behaviors": len(self._behaviors),
            "by_segment": {
                seg.value: len(ids)
                for seg, ids in self._by_segment.items()
            },
            "avg_order_value": sum(u.avg_order_value for u in self._users.values()) / len(self._users) if self._users else 0,
        }


# Global user graph
_user_graph: UserGraph | None = None


def get_user_graph() -> UserGraph:
    """Get global user graph."""
    global _user_graph
    if _user_graph is None:
        _user_graph = UserGraph()
    return _user_graph
