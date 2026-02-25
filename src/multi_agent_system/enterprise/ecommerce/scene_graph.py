"""E-commerce Knowledge Graph - Scene/Context Graph.

Provides context awareness, scene understanding, and situational matching
for e-commerce scenarios.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class SceneType(Enum):
    """Scene types."""
    SHOPPING = "shopping"
    GIFTING = "gifting"
    BROWSE = "browse"
    COMPARISON = "comparison"
    CHECKOUT = "checkout"
    AFTER_SALE = "after_sale"
    SEARCH = "search"


class TimeContext(Enum):
    """Time context."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    WEEKEND = "weekend"
    WEEKDAY = "weekday"
    HOLIDAY = "holiday"
    BLACK_FRIDAY = "black_friday"
    CHRISTMAS = "christmas"


class LocationContext(Enum):
    """Location context."""
    HOME = "home"
    OFFICE = "office"
    COMMUTE = "commute"
    STORE = "store"
    TRAVEL = "travel"


@dataclass
class SceneContext:
    """Scene context entity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])

    # Scene type
    scene_type: SceneType = SceneType.SHOPPING

    # Time
    time_context: TimeContext | None = None
    is_weekend: bool = False
    is_holiday: bool = False

    # Location
    location: LocationContext | None = None
    device: str = ""  # mobile, desktop, tablet

    # User state
    user_mood: str = ""  # happy, urgent, relaxed, etc.
    user_intent: str = ""  # browse, buy, compare, return

    # Session
    session_id: str = ""
    session_duration_minutes: int = 0

    # Previous interactions
    previous_pages: list[str] = field(default_factory=list)
    previous_searches: list[str] = field(default_factory=list)
    cart_value: float = 0.0

    # External
    weather: str = ""  # sunny, rainy, cold, hot
    season: str = ""  # spring, summer, fall, winter

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScenePattern:
    """Pattern for scene matching."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""

    # Conditions
    scene_types: list[SceneType] = field(default_factory=list)
    time_contexts: list[TimeContext] = field(default_factory=list)
    locations: list[LocationContext] = field(default_factory=list)
    user_moods: list[str] = field(default_factory=list)

    # Tags for matching
    keywords: list[str] = field(default_factory=list)

    # Actions
    recommended_actions: list[str] = field(default_factory=list)
    recommended_products: list[str] = field(default_factory=list)  # product IDs


@dataclass
class SceneTransition:
    """Scene transition record."""
    from_scene: str = ""
    to_scene: str = ""
    trigger: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class SceneGraph:
    """Scene/context knowledge graph.

    Features:
    - Scene context tracking
    - Pattern recognition
    - Scene transitions
    - Context-aware recommendations
    """

    def __init__(self) -> None:
        """Initialize scene graph."""
        self._scenes: dict[str, SceneContext] = {}
        self._patterns: list[ScenePattern] = []
        self._transitions: list[SceneTransition] = []
        self._active_scene: SceneContext | None = None
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default scene patterns."""
        self._patterns = [
            # Gift buying
            ScenePattern(
                name="Gift Shopping",
                scene_types=[SceneType.SHOPPING, SceneType.GIFTING],
                keywords=["gift", "present", "birthday", "anniversary"],
                recommended_actions=["show_gift_options", "add_wrapping"],
            ),
            # Morning browsing
            ScenePattern(
                name="Morning Browse",
                time_contexts=[TimeContext.MORNING],
                user_moods=["relaxed", "casual"],
                recommended_actions=["show_new_arrivals", "show_trending"],
            ),
            # Weekend shopping
            ScenePattern(
                name="Weekend Shopping",
                time_contexts=[TimeContext.WEEKEND],
                recommended_actions=["show_deals", "allow_comparison"],
            ),
            # Holiday shopping
            ScenePattern(
                name="Holiday Shopping",
                time_contexts=[TimeContext.BLACK_FRIDAY, TimeContext.CHRISTMAS],
                recommended_actions=["show_discounts", "show_bundles"],
            ),
        ]

    def start_scene(
        self,
        scene_type: SceneType,
        session_id: str = "",
    ) -> SceneContext:
        """Start a new scene."""
        scene = SceneContext(
            scene_type=scene_type,
            session_id=session_id,
            timestamp=datetime.now(),
        )

        self._scenes[scene.id] = scene
        self._active_scene = scene
        return scene

    def update_scene(self, scene_id: str, **kwargs) -> SceneContext | None:
        """Update scene context."""
        scene = self._scenes.get(scene_id)
        if not scene:
            return None

        for key, value in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, value)

        return scene

    def end_scene(self, scene_id: str) -> None:
        """End a scene."""
        if scene_id in self._scenes:
            del self._scenes[scene_id]
        if self._active_scene and self._active_scene.id == scene_id:
            self._active_scene = None

    def record_transition(
        self,
        from_scene: str,
        to_scene: str,
        trigger: str,
    ) -> None:
        """Record scene transition."""
        transition = SceneTransition(
            from_scene=from_scene,
            to_scene=to_scene,
            trigger=trigger,
        )
        self._transitions.append(transition)

    def get_current_scene(self) -> SceneContext | None:
        """Get current active scene."""
        return self._active_scene

    def match_pattern(self, scene: SceneContext | None = None) -> list[ScenePattern]:
        """Match scene to patterns."""
        scene = scene or self._active_scene
        if not scene:
            return []

        matched = []

        for pattern in self._patterns:
            score = 0

            # Check scene type
            if scene.scene_type in pattern.scene_types:
                score += 2

            # Check time context
            if scene.time_context and scene.time_context in pattern.time_contexts:
                score += 1

            # Check location
            if scene.location and scene.location in pattern.locations:
                score += 1

            # Check mood
            if scene.user_mood and scene.user_mood in pattern.user_moods:
                score += 1

            if score > 0:
                matched.append((pattern, score))

        matched.sort(key=lambda x: x[1], reverse=True)
        return [p for p, s in matched]

    def get_recommendations(self) -> dict[str, Any]:
        """Get context-aware recommendations."""
        scene = self._active_scene
        if not scene:
            return {}

        # Match patterns
        patterns = self.match_pattern()

        recs = {
            "scene_type": scene.scene_type.value,
            "recommended_actions": [],
            "personalized_message": "",
        }

        # Collect recommendations from patterns
        for pattern in patterns:
            recs["recommended_actions"].extend(pattern.recommended_actions)

        # Generate personalized message based on context
        if scene.scene_type == SceneType.GIFTING:
            recs["personalized_message"] = "找到完美的礼物了吗？我们提供礼品包装服务"
        elif scene.time_context == TimeContext.EVENING:
            recs["personalized_message"] = "晚间购物愉快！明早下单可享快速配送"
        elif scene.is_holiday:
            recs["personalized_message"] = "节日特惠！限时折扣中"
        elif scene.cart_value > 500:
            recs["personalized_message"] = "您已选购商品满500元，可享受会员优惠"
        else:
            recs["personalized_message"] = "根据您的浏览记录，为您推荐"

        return recs

    def detect_intent_from_context(self) -> str:
        """Detect user intent from context."""
        scene = self._active_scene
        if not scene:
            return "unknown"

        # Rule-based intent detection
        if scene.previous_searches:
            return "search"

        if scene.cart_value > 0 and scene.scene_type == SceneType.CHECKOUT:
            return "purchase"

        if len(scene.previous_pages) > 5:
            return "browse"

        if scene.scene_type == SceneType.COMPARISON:
            return "compare"

        return "browse"

    def get_scene_statistics(self) -> dict[str, Any]:
        """Get scene statistics."""
        if not self._scenes:
            return {}

        scene_types = {}
        for scene in self._scenes.values():
            t = scene.scene_type.value
            scene_types[t] = scene_types.get(t, 0) + 1

        return {
            "total_scenes": len(self._scenes),
            "scene_types": scene_types,
            "total_transitions": len(self._transitions),
        }


# Global scene graph
_scene_graph: SceneGraph | None = None


def get_scene_graph() -> SceneGraph:
    """Get global scene graph."""
    global _scene_graph
    if _scene_graph is None:
        _scene_graph = SceneGraph()
    return _scene_graph
