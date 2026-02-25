"""Proactive layer based on ProAgent paper.

Reference: "ProAgent: Harnessing On-Demand Sensory Contexts for Proactive LLM Agent Systems"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserContext:
    """User context for proactive predictions."""

    user_id: str | None = None
    recent_queries: list[str] = field(default_factory=list)
    session_history: list[dict] = field(default_factory=list)
    explicit_preferences: dict[str, Any] = field(default_factory=dict)
    implicit_preferences: dict[str, Any] = field(default_factory=dict)
    time_context: str = ""  # morning, afternoon, evening, etc.
    device_context: str = ""  # mobile, desktop, etc.


@dataclass
class PredictedNeed:
    """A predicted user need."""

    need_id: str
    description: str
    confidence: float  # 0-1
    suggested_actions: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class ProactiveLayer:
    """Proactive service layer that predicts user needs.

    Based on ProAgent framework - transitions from reactive to proactive paradigm.
    """

    def __init__(self) -> None:
        self.user_contexts: dict[str, UserContext] = {}
        self.prediction_model: Any = None  # Would be ML model in production

    def update_context(self, user_id: str, query: str, context: dict | None = None) -> None:
        """Update user context with new query."""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)

        user_ctx = self.user_contexts[user_id]
        user_ctx.recent_queries.append(query)

        # Keep only recent queries
        if len(user_ctx.recent_queries) > 10:
            user_ctx.recent_queries = user_ctx.recent_queries[-10:]

        if context:
            user_ctx.session_history.append(context)

    def predict_needs(self, user_id: str) -> list[PredictedNeed]:
        """Predict user needs based on context."""
        if user_id not in self.user_contexts:
            return []

        user_ctx = self.user_contexts[user_id]
        predictions = []

        # Pattern 1: Follow-up queries
        if len(user_ctx.recent_queries) >= 2:
            last_query = user_ctx.recent_queries[-1]
            second_last = user_ctx.recent_queries[-2]

            # User asked about X, might want more details
            predictions.append(
                PredictedNeed(
                    need_id="follow_up",
                    description=f"User might want more details about: {last_query}",
                    confidence=0.6,
                    suggested_actions=["provide_more_details", "offer_related_topics"],
                )
            )

        # Pattern 2: Time-based predictions
        if user_ctx.time_context == "morning":
            predictions.append(
                PredictedNeed(
                    need_id="daily_brief",
                    description="User might want a daily summary or briefing",
                    confidence=0.4,
                    suggested_actions=["offer_daily_summary"],
                )
            )

        # Pattern 3: Preference-based
        if user_ctx.explicit_preferences.get("interested_topics"):
            predictions.append(
                PredictedNeed(
                    need_id="personalized_recommendations",
                    description="User might be interested in new content in their topics",
                    confidence=0.7,
                    suggested_actions=["recommend_related_content"],
                )
            )

        return predictions

    def suggest_actions(self, predictions: list[PredictedNeed]) -> list[str]:
        """Get suggested proactive actions."""
        actions = []
        for pred in predictions:
            if pred.confidence > 0.5:
                actions.extend(pred.suggested_actions)
        return list(set(actions))

    def get_proactive_suggestion(self, user_id: str) -> str | None:
        """Get a proactive suggestion for the user."""
        predictions = self.predict_needs(user_id)

        if not predictions:
            return None

        # Return highest confidence prediction
        best = max(predictions, key=lambda p: p.confidence)
        if best.confidence > 0.5:
            return f"Suggestion: {best.description}"

        return None


# Global instance
_proactive_layer: ProactiveLayer | None = None


def get_proactive_layer() -> ProactiveLayer:
    """Get global proactive layer instance."""
    global _proactive_layer
    if _proactive_layer is None:
        _proactive_layer = ProactiveLayer()
    return _proactive_layer
