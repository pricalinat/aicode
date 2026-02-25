"""Agent security module for multi-agent systems.

Reference: "Agents Under Siege" - Prompt Attack Prevention
         "An Adversary-Resistant Multi-Agent LLM System"

Provides security monitoring and defense against adversarial inputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ThreatType(Enum):
    """Types of security threats."""

    PROMPT_INJECTION = "prompt_injection"  # Attempt to override system prompt
    JAILBREAK = "jailbreak"  # Attempt to bypass safety measures
    ROLE_PLAYING = "role_playing"  # Attempt to make model pretend to be someone
    DENIAL_OF_SERVICE = "dos"  # Attempt to overload the system
    DATA_EXTRACTION = "data_extraction"  # Attempt to extract sensitive data
    MANIPULATION = "manipulation"  # Attempt to manipulate agent behavior


@dataclass
class SecurityEvent:
    """A detected security event."""

    event_id: str
    threat_type: ThreatType
    severity: float  # 0-1
    description: str
    original_input: str
    sanitized_input: str | None = None
    blocked: bool = False


@dataclass
class SecurityConfig:
    """Security configuration."""

    enable_prompt_injection_detection: bool = True
    enable_jailbreak_detection: bool = True
    enable_content_filtering: bool = True
    severity_threshold: float = 0.7  # Block if severity > threshold
    block_by_default: bool = False


class AgentSecurityMonitor:
    """Security monitoring for multi-agent systems.

    Detects and prevents adversarial attacks on agents.
    """

    # Known prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"forget\s+(everything|all)\s+(you\s+know|you\s+learned)",
        r"new\s+instruction[s]?:",
        r"#system\s*#",
        r"you\s+are\s+now\s+(?:in\s+)?(?:dev|developer|god)\s+mode",
        r"disregard\s+(your\s+)?(safety|system|ethical)",
        r"(system|developer)\s*:\s*",
    ]

    # Known jailbreak patterns
    JAILBREAK_PATTERNS = [
        r" DAN\b",  # Do Anything Now
        r"developer\s+mode",
        r"jailbreak",
        r"bypass\s+(safety|restriction|filter)",
    ]

    # Sensitive data patterns
    SENSITIVE_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",  # Credit card
        r"password\s*[=:]\s*\S+",
        r"api[_-]?key\s*[=:]\s*\S+",
        r"secret\s*[=:]\s*\S+",
    ]

    def __init__(self, config: SecurityConfig | None = None) -> None:
        self.config = config or SecurityConfig()
        self.events: list[SecurityEvent] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns."""
        self._injection_regex = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self._jailbreak_regex = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]
        self._sensitive_regex = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]

    def check_input(self, user_input: str) -> SecurityEvent | None:
        """Check input for security threats.

        Args:
            user_input: The input to check

        Returns:
            SecurityEvent if threat detected, None otherwise
        """
        import uuid

        # Check for prompt injection
        if self.config.enable_prompt_injection_detection:
            for pattern in self._injection_regex:
                if pattern.search(user_input):
                    event = SecurityEvent(
                        event_id=str(uuid.uuid4())[:12],
                        threat_type=ThreatType.PROMPT_INJECTION,
                        severity=0.9,
                        description="Prompt injection detected",
                        original_input=user_input[:100],
                        blocked=self.config.severity_threshold < 0.9,
                    )
                    self.events.append(event)
                    return event

        # Check for jailbreak attempts
        if self.config.enable_jailbreak_detection:
            for pattern in self._jailbreak_regex:
                if pattern.search(user_input):
                    event = SecurityEvent(
                        event_id=str(uuid.uuid4())[:12],
                        threat_type=ThreatType.JAILBREAK,
                        severity=0.95,
                        description="Jailbreak attempt detected",
                        original_input=user_input[:100],
                        blocked=self.config.severity_threshold < 0.95,
                    )
                    self.events.append(event)
                    return event

        # Check for sensitive data extraction attempts
        if self.config.enable_content_filtering:
            for pattern in self._sensitive_regex:
                if pattern.search(user_input):
                    event = SecurityEvent(
                        event_id=str(uuid.uuid4())[:12],
                        threat_type=ThreatType.DATA_EXTRACTION,
                        severity=0.6,
                        description="Sensitive data pattern detected in input",
                        original_input=user_input[:100],
                        blocked=False,
                    )
                    self.events.append(event)
                    return event

        return None

    def sanitize_input(self, user_input: str) -> str:
        """Sanitize input by removing potential threats.

        Args:
            user_input: The input to sanitize

        Returns:
            Sanitized input
        """
        sanitized = user_input

        # Remove known injection patterns
        for pattern in self._injection_regex:
            sanitized = pattern.sub("[FILTERED]", sanitized)

        # Remove jailbreak patterns
        for pattern in self._jailbreak_regex:
            sanitized = pattern.sub("[BLOCKED]", sanitized)

        return sanitized

    def should_block(self, event: SecurityEvent) -> bool:
        """Determine if input should be blocked."""
        if self.config.block_by_default:
            return True
        return event.severity >= self.config.severity_threshold

    def get_statistics(self) -> dict[str, Any]:
        """Get security statistics."""
        if not self.events:
            return {"total_events": 0}

        by_type = {}
        for event in self.events:
            threat = event.threat_type.value
            by_type[threat] = by_type.get(threat, 0) + 1

        return {
            "total_events": len(self.events),
            "by_type": by_type,
            "blocked_count": sum(1 for e in self.events if e.blocked),
        }

    def clear_events(self) -> None:
        """Clear security events."""
        self.events.clear()


# Global instance
_security_monitor: AgentSecurityMonitor | None = None


def get_security_monitor(config: SecurityConfig | None = None) -> AgentSecurityMonitor:
    """Get global security monitor instance."""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = AgentSecurityMonitor(config)
    return _security_monitor
