"""Intent Recognition System.

Provides user intent recognition and classification for agent interactions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IntentType(Enum):
    """Intent types."""
    QUESTION = "question"
    COMMAND = "command"
    REQUEST = "request"
    INFORMATION = "information"
    CONFIRMATION = "confirmation"
    GREETING = "greeting"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Recognized intent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    intent_type: IntentType = IntentType.UNKNOWN

    # Classification
    confidence: float = 0.0  # 0-1
    category: str = ""

    # Entities
    entities: dict[str, Any] = field(default_factory=dict)

    # Context
    context: dict[str, Any] = field(default_factory=dict)

    # Metadata
    raw_input: str = ""
    processed_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntentPattern:
    """Pattern for intent matching."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    intent_type: IntentType = IntentType.UNKNOWN
    category: str = ""

    # Patterns
    keywords: list[str] = field(default_factory=list)
    regex: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)

    # Entities
    entity_extractors: dict[str, str] = field(default_factory=dict)


class IntentRecognizer:
    """Recognizes user intents.

    Features:
    - Pattern-based matching
    - Keyword extraction
    - Entity recognition
    - Confidence scoring
    """

    def __init__(self) -> None:
        """Initialize intent recognizer."""
        self._patterns: list[IntentPattern] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default intent patterns."""
        self._patterns = [
            # Question
            IntentPattern(
                intent_type=IntentType.QUESTION,
                category="query",
                keywords=["what", "how", "why", "when", "where", "who", "which"],
                templates=["{kw} is {entity}?", "{kw} does {entity} work?"],
            ),
            # Command
            IntentPattern(
                intent_type=IntentType.COMMAND,
                category="action",
                keywords=["do", "make", "create", "delete", "update", "run", "execute"],
                templates=["{verb} {object}", "please {verb} {object}"],
            ),
            # Request
            IntentPattern(
                intent_type=IntentType.REQUEST,
                category="ask",
                keywords=["can you", "could you", "please", "would you", "help me"],
                templates=["can you {action}", "help me {action}"],
            ),
            # Information
            IntentPattern(
                intent_type=IntentType.INFORMATION,
                category="share",
                keywords=["here is", "this is", "information", "details"],
            ),
            # Confirmation
            IntentPattern(
                intent_type=IntentType.CONFIRMATION,
                category="verify",
                keywords=["confirm", "verify", "check", "is this correct", "right"],
            ),
            # Greeting
            IntentPattern(
                intent_type=IntentType.GREETING,
                category="social",
                keywords=["hello", "hi", "hey", "good morning", "good evening"],
            ),
        ]

    def add_pattern(self, pattern: IntentPattern) -> None:
        """Add intent pattern."""
        self._patterns.append(pattern)

    def recognize(self, text: str) -> Intent:
        """Recognize intent from text."""
        text_lower = text.lower()

        # Check each pattern
        best_match = None
        best_score = 0.0

        for pattern in self._patterns:
            score = self._match_pattern(text_lower, pattern)

            if score > best_score:
                best_score = score
                best_match = pattern

        # Create intent
        if best_match and best_score > 0.3:
            intent = Intent(
                intent_type=best_match.intent_type,
                confidence=best_score,
                category=best_match.category,
                raw_input=text,
            )

            # Extract entities
            intent.entities = self._extract_entities(text_lower, best_match)

        else:
            intent = Intent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_input=text,
            )

        return intent

    def _match_pattern(self, text: str, pattern: IntentPattern) -> float:
        """Match text against pattern."""
        score = 0.0
        matches = 0

        # Check keywords
        for keyword in pattern.keywords:
            if keyword.lower() in text:
                score += 0.4
                matches += 1

        # Check regex
        import re
        for regex in pattern.regex:
            if re.search(regex, text):
                score += 0.5
                matches += 1

        # Normalize
        if matches > 0:
            return min(1.0, score / (len(pattern.keywords) + len(pattern.regex) + 1))

        return 0.0

    def _extract_entities(
        self,
        text: str,
        pattern: IntentPattern,
    ) -> dict[str, Any]:
        """Extract entities from text."""
        entities = {}

        # Simple entity extraction based on patterns
        import re

        # Extract numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities["numbers"] = numbers

        # Extract quoted text
        quoted = re.findall(r'"([^"]+)"', text)
        if quoted:
            entities["quoted"] = quoted

        # Extract time-related
        time_words = ["today", "tomorrow", "yesterday", "now", "later"]
        for word in time_words:
            if word in text:
                entities["time"] = word

        return entities


# Global recognizer
_intent_recognizer: IntentRecognizer | None = None


def get_intent_recognizer() -> IntentRecognizer:
    """Get global intent recognizer."""
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognizer()
    return _intent_recognizer
