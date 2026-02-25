"""User Preference Model for personalized agent interactions.

Based on "Agent WARPP: Workflow Adherence via Runtime Parallel Personalization"
and related work on user modeling and personalization.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class PreferenceCategory(Enum):
    """Preference categories."""
    COMMUNICATION = "communication"  # How to communicate (verbose, concise, etc.)
    OUTPUT_FORMAT = "output_format"  # Format preferences (JSON, markdown, etc.)
    WORKFLOW = "workflow"           # Workflow preferences
    INTERACTION = "interaction"     # Interaction style
    PRIVACY = "privacy"             # Privacy settings
    NOTIFICATION = "notification"  # Notification preferences
    CUSTOM = "custom"              # Custom preferences


class PreferenceStrength(Enum):
    """How strong a preference is."""
    WEAK = 1       # Can be easily overridden
    MODERATE = 2  # Default but changeable
    STRONG = 3    # Should be respected
    CRITICAL = 4   # Must be respected


@dataclass
class Preference:
    """A single user preference."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: PreferenceCategory = PreferenceCategory.CUSTOM
    key: str = ""
    value: Any = None
    strength: PreferenceStrength = PreferenceStrength.MODERATE
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: str = "explicit"  # "explicit", "observed", "inferred"

    def update_value(self, new_value: Any) -> None:
        """Update preference value."""
        self.value = new_value
        self.updated_at = datetime.now()


@dataclass
class UserProfile:
    """User profile with preferences and behavior."""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""

    # Basic info
    display_name: str = ""
    email: str = ""
    role: str = ""  # "developer", "researcher", "manager", etc.

    # Preferences
    preferences: dict[str, Preference] = field(default_factory=dict)

    # Behavior patterns
    interaction_count: int = 0
    last_active: datetime | None = None
    average_session_duration_minutes: float = 0.0

    # Learning
    learned_patterns: dict[str, Any] = field(default_factory=dict)
    feedback_history: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)

    def get_preference(self, key: str) -> Preference | None:
        """Get preference by key."""
        return self.preferences.get(key)

    def set_preference(
        self,
        key: str,
        value: Any,
        category: PreferenceCategory = PreferenceCategory.CUSTOM,
        strength: PreferenceStrength = PreferenceStrength.MODERATE,
    ) -> Preference:
        """Set a preference."""
        if key in self.preferences:
            pref = self.preferences[key]
            pref.update_value(value)
        else:
            pref = Preference(
                key=key,
                value=value,
                category=category,
                strength=strength,
            )
            self.preferences[key] = pref

        self.updated_at = datetime.now()
        return pref

    def get_preferences_by_category(self, category: PreferenceCategory) -> list[Preference]:
        """Get all preferences in a category."""
        return [p for p in self.preferences.values() if p.category == category]

    def to_config(self) -> dict[str, Any]:
        """Convert to configuration dict for agent."""
        return {
            pref.key: pref.value
            for pref in self.preferences.values()
            if pref.strength >= PreferenceStrength.STRONG
        }


class PreferenceLearner:
    """Learns user preferences from behavior."""

    def __init__(self, window_days: int = 30) -> None:
        """Initialize preference learner.

        Args:
            window_days: Days to consider for pattern learning
        """
        self.window_days = window_days

    def learn_from_interaction(
        self,
        profile: UserProfile,
        interaction: dict[str, Any],
    ) -> list[Preference]:
        """Learn preferences from user interaction.

        Args:
            profile: User profile
            interaction: Interaction data

        Returns:
            List of learned/inferred preferences
        """
        learned = []

        # Analyze communication style
        if "response_length" in interaction:
            length = interaction["response_length"]
            if length > 500:
                pref = Preference(
                    key="communication.verbose",
                    value=True,
                    category=PreferenceCategory.COMMUNICATION,
                    strength=PreferenceStrength.WEAK,
                    source="inferred",
                    description="User prefers detailed responses",
                )
                learned.append(pref)
            elif length < 100:
                pref = Preference(
                    key="communication.concise",
                    value=True,
                    category=PreferenceCategory.COMMUNICATION,
                    strength=PreferenceStrength.WEAK,
                    source="inferred",
                    description="User prefers concise responses",
                )
                learned.append(pref)

        # Analyze format preferences
        if "format_used" in interaction:
            fmt = interaction["format_used"]
            pref = Preference(
                key=f"output_format.{fmt}",
                value=True,
                category=PreferenceCategory.OUTPUT_FORMAT,
                strength=PreferenceStrength.MODERATE,
                source="observed",
                description=f"User uses {fmt} format",
            )
            learned.append(pref)

        # Analyze workflow preferences
        if "workflow_completed" in interaction:
            workflow = interaction["workflow_completed"]
            if "steps" in workflow:
                pref = Preference(
                    key="workflow.step_by_step",
                    value=True,
                    category=PreferenceCategory.WORKFLOW,
                    strength=PreferenceStrength.MODERATE,
                    source="observed",
                    description="User follows step-by-step workflows",
                )
                learned.append(pref)

        return learned

    def update_profile(self, profile: UserProfile, interaction: dict[str, Any]) -> None:
        """Update profile with learned preferences."""
        learned = self.learn_from_interaction(profile, interaction)

        for pref in learned:
            existing = profile.get_preference(pref.key)
            if existing:
                # Update if observed more frequently
                if pref.source == "observed" and existing.source == "inferred":
                    existing.value = pref.value
                    existing.source = pref.source
                    existing.strength = PreferenceStrength.MODERATE
            else:
                profile.preferences[pref.key] = pref


class UserPreferenceManager:
    """Manages user preferences and profiles.

    Features:
    - Profile creation and management
    - Preference storage and retrieval
    - Learning from behavior
    - Profile merging
    """

    def __init__(self) -> None:
        """Initialize preference manager."""
        self._profiles: dict[str, UserProfile] = {}
        self._learner = PreferenceLearner()

    def create_profile(
        self,
        user_id: str,
        username: str = "",
        role: str = "",
        **kwargs,
    ) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(
            user_id=user_id,
            username=username,
            role=role,
            **kwargs,
        )
        self._profiles[user_id] = profile

        # Set default preferences
        self._set_defaults(profile)

        return profile

    def _set_defaults(self, profile: UserProfile) -> None:
        """Set default preferences."""
        defaults = [
            ("communication.verbose", False, PreferenceCategory.COMMUNICATION),
            ("output_format.default", "text", PreferenceCategory.OUTPUT_FORMAT),
            ("workflow.auto_save", True, PreferenceCategory.WORKFLOW),
            ("notification.enabled", True, PreferenceCategory.NOTIFICATION),
            ("privacy.share_usage", True, PreferenceCategory.PRIVACY),
        ]

        for key, value, category in defaults:
            profile.set_preference(key, value, category, PreferenceStrength.WEAK)

    def get_profile(self, user_id: str) -> UserProfile | None:
        """Get user profile."""
        return self._profiles.get(user_id)

    def get_or_create_profile(
        self,
        user_id: str,
        username: str = "",
        role: str = "",
    ) -> UserProfile:
        """Get existing profile or create new one."""
        if user_id in self._profiles:
            return self._profiles[user_id]
        return self.create_profile(user_id, username, role)

    def set_preference(
        self,
        user_id: str,
        key: str,
        value: Any,
        category: PreferenceCategory = PreferenceCategory.CUSTOM,
        strength: PreferenceStrength = PreferenceStrength.MODERATE,
    ) -> bool:
        """Set user preference."""
        profile = self.get_profile(user_id)
        if not profile:
            return False

        profile.set_preference(key, value, category, strength)
        return True

    def get_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get user preference value."""
        profile = self.get_profile(user_id)
        if not profile:
            return default

        pref = profile.get_preference(key)
        return pref.value if pref else default

    def record_interaction(self, user_id: str, interaction: dict[str, Any]) -> None:
        """Record user interaction and learn preferences."""
        profile = self.get_profile(user_id)
        if not profile:
            return

        # Update interaction stats
        profile.interaction_count += 1
        profile.last_active = datetime.now()

        # Learn from interaction
        self._learner.update_profile(profile, interaction)

    def merge_profiles(
        self,
        source_user_id: str,
        target_user_id: str,
        strategy: str = "prefer_stronger",
    ) -> UserProfile | None:
        """Merge two user profiles.

        Args:
            source_user_id: Source profile ID
            target_user_id: Target profile ID
            strategy: Merge strategy

        Returns:
            Merged profile
        """
        source = self.get_profile(source_user_id)
        target = self.get_profile(target_user_id)

        if not source or not target:
            return None

        for key, pref in source.preferences.items():
            if key not in target.preferences:
                target.preferences[key] = pref
            elif strategy == "prefer_stronger":
                if pref.strength.value > target.preferences[key].strength.value:
                    target.preferences[key] = pref
            elif strategy == "prefer_explicit":
                if pref.source == "explicit":
                    target.preferences[key] = pref

        target.updated_at = datetime.now()
        return target

    def get_statistics(self) -> dict[str, Any]:
        """Get preference system statistics."""
        total_profiles = len(self._profiles)
        total_preferences = sum(len(p.preferences) for p in self._profiles.values())

        category_counts = {}
        for profile in self._profiles.values():
            for pref in profile.preferences.values():
                cat = pref.category.value
                category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_profiles": total_profiles,
            "total_preferences": total_preferences,
            "preferences_by_category": category_counts,
        }


# Global manager
_preference_manager: UserPreferenceManager | None = None


def get_preference_manager() -> UserPreferenceManager:
    """Get global preference manager."""
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = UserPreferenceManager()
    return _preference_manager
