"""Agent Firewall based on "Securing Generative AI Agentic Workflows: Risks, Mitigation, and a Proposed Firewall Architecture".

Reference: Agentic workflow security architecture with multiple protection layers.
Features: Input validation, output filtering, tool access control, attack detection.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ThreatLevel(Enum):
    """Threat severity levels."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats."""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    SENSITIVE_DATA = "sensitive_data"
    TOOL_ABUSE = "tool_abuse"
    DENIAL_OF_SERVICE = "dos"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_LEAKAGE = "data_leakage"


@dataclass
class SecurityEvent:
    """A security event or detected threat."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    threat_type: ThreatType = ThreatType.PROMPT_INJECTION
    threat_level: ThreatLevel = ThreatLevel.SAFE
    description: str = ""
    content: str = ""  # The flagged content
    action_taken: str = ""  # What was done
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


@dataclass
class SecurityConfig:
    """Security configuration."""
    # Threat detection sensitivity
    injection_sensitivity: float = 0.7  # 0-1
    jailbreak_sensitivity: float = 0.8

    # What to block
    block_jailbreak: bool = True
    block_prompt_injection: bool = True
    block_sensitive_data: bool = False  # Just warn by default

    # Tool access
    allowed_tools: list[str] = field(default_factory=list)  # Empty = all allowed
    blocked_tools: list[str] = field(default_factory=list)

    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_request: int = 100000

    # Logging
    log_all_events: bool = True
    log_blocked_only: bool = False


class PromptInjectionDetector:
    """Detects prompt injection attacks."""

    # Common injection patterns
    INJECTION_PATTERNS = [
        # Direct instructions
        r"ignore\s+(all\s+)?(previous|prior|above)",
        r"forget\s+(everything|all|your)",
        r"disregard\s+(your|all)",
        r"new\s+instruction[s]?:",
        r"system\s+prompt:",

        # Role playing bypass
        r"you\s+are\s+(now|a)",
        r"pretend\s+to\s+be",
        r"act\s+as\s+(if|a|an)",

        # Hidden instructions
        r"\[INST\]",
        r"\<\|.*?\|>",  # Special tokens
        r"```system",

        # Override attempts
        r"override\s+(your|system)",
        r"bypass\s+(safety|security)",

        # Delimiter attacks
        r"###\s*Instruction",
        r"====\s*User",
    ]

    def __init__(self, sensitivity: float = 0.7) -> None:
        """Initialize detector."""
        self.sensitivity = sensitivity
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def detect(self, text: str) -> tuple[bool, float, list[str]]:
        """Detect prompt injection.

        Returns:
            (is_injection, confidence, matched_patterns)
        """
        matched = []
        for pattern in self._patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)

        # Calculate confidence based on matches
        confidence = min(1.0, len(matched) * 0.3)

        is_injection = confidence >= self.sensitivity
        return is_injection, confidence, matched


class JailbreakDetector:
    """Detects jailbreak attempts."""

    JAILBREAK_PATTERNS = [
        # DAN (Do Anything Now) variants
        r"\bDAN\b",
        r"do\s+anything\s+now",
        r"developer\s+mode",
        r"jailbreak",

        # Role-based bypasses
        r"evil\s+",
        r"roleplay\s+as\s+.*?(evil|harmful)",

        # Hypothetical/Framing
        r"(fictional|hypothetical|imaginary)\s+(scenario|story)",
        r"for\s+(research|educational)\s+purposes?",

        # Character/Persona bypass
        r"character\s+prompt:",
        r"respond\s+as\s+.*?(without|won't)",
    ]

    def __init__(self, sensitivity: float = 0.8) -> None:
        """Initialize detector."""
        self.sensitivity = sensitivity
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]

    def detect(self, text: str) -> tuple[bool, float, list[str]]:
        """Detect jailbreak attempt.

        Returns:
            (is_jailbreak, confidence, matched_patterns)
        """
        matched = []
        for pattern in self._patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)

        confidence = min(1.0, len(matched) * 0.4)

        is_jailbreak = confidence >= self.sensitivity
        return is_jailbreak, confidence, matched


class SensitiveDataDetector:
    """Detects sensitive data exposure."""

    SENSITIVE_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "api_key": r"(api[_-]?key|apikey)\s*[:=]\s*['\"]?\w+",
        "password": r"password\s*[:=]\s*['\"]?\S+",
    }

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect sensitive data.

        Returns:
            Dictionary of detected types and matches
        """
        results = {}
        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[data_type] = matches
        return results


class AgentFirewall:
    """Agent Firewall for securing agentic workflows.

    Provides multi-layer security:
    1. Input validation
    2. Threat detection
    3. Tool access control
    4. Output filtering
    5. Rate limiting
    """

    def __init__(self, config: SecurityConfig | None = None) -> None:
        """Initialize Agent Firewall."""
        self.config = config or SecurityConfig()

        # Initialize detectors
        self._injection_detector = PromptInjectionDetector(
            self.config.injection_sensitivity
        )
        self._jailbreak_detector = JailbreakDetector(
            self.config.jailbreak_sensitivity
        )
        self._sensitive_detector = SensitiveDataDetector()

        # Event logging
        self._events: list[SecurityEvent] = []

        # Rate limiting
        self._request_counts: dict[str, list[datetime]] = {}

    def check_input(self, text: str, context: dict[str, Any] | None = None) -> SecurityEvent:
        """Check input for security threats.

        Args:
            text: Input text to check
            context: Additional context

        Returns:
            Security event with findings
        """
        event = SecurityEvent(content=text[:500])  # Store truncated

        # Check prompt injection
        is_injection, inj_conf, inj_patterns = self._injection_detector.detect(text)

        if is_injection:
            event.threat_type = ThreatType.PROMPT_INJECTION
            event.threat_level = ThreatLevel.HIGH
            event.description = f"Prompt injection detected (confidence: {inj_conf:.2f})"
            event.metadata["matched_patterns"] = inj_patterns
            event.blocked = self.config.block_prompt_injection
            event.action_taken = "blocked" if event.blocked else "warned"

        # Check jailbreak
        is_jailbreak, jb_conf, jb_patterns = self._jailbreak_detector.detect(text)

        if is_jailbreak and event.threat_level.value == "safe":
            event.threat_type = ThreatType.JAILBREAK
            event.threat_level = ThreatLevel.CRITICAL
            event.description = f"Jailbreak detected (confidence: {jb_conf:.2f})"
            event.metadata["matched_patterns"] = jb_patterns
            event.blocked = self.config.block_jailbreak
            event.action_taken = "blocked" if event.blocked else "warned"

        # Check sensitive data
        sensitive = self._sensitive_detector.detect(text)
        if sensitive and event.threat_level.value == "safe":
            event.threat_type = ThreatType.SENSITIVE_DATA
            event.threat_level = ThreatLevel.MEDIUM
            event.description = f"Sensitive data detected: {list(sensitive.keys())}"
            event.metadata["detected_data"] = sensitive
            event.blocked = self.config.block_sensitive_data
            event.action_taken = "blocked" if event.blocked else "flagged"

        self._log_event(event)
        return event

    def check_tool_access(self, tool_name: str, user_id: str = "") -> tuple[bool, str]:
        """Check if tool access is allowed.

        Args:
            tool_name: Name of tool to access
            user_id: User requesting access

        Returns:
            (is_allowed, reason)
        """
        # Check blocked tools
        if tool_name in self.config.blocked_tools:
            return False, f"Tool '{tool_name}' is blocked"

        # Check allowed list
        if self.config.allowed_tools and tool_name not in self.config.allowed_tools:
            return False, f"Tool '{tool_name}' is not in allowed list"

        return True, "allowed"

    def check_rate_limit(self, user_id: str = "default") -> tuple[bool, str]:
        """Check if request is within rate limits.

        Args:
            user_id: User identifier

        Returns:
            (is_allowed, reason)
        """
        now = datetime.now()
        minute_ago = now.replace(minute=now.minute - 1)

        # Get request times for user
        if user_id not in self._request_counts:
            self._request_counts[user_id] = []

        # Clean old requests
        self._request_counts[user_id] = [
            t for t in self._request_counts[user_id]
            if t > minute_ago
        ]

        # Check limit
        if len(self._request_counts[user_id]) >= self.config.max_requests_per_minute:
            return False, f"Rate limit exceeded: {self.config.max_requests_per_minute} requests/minute"

        # Record this request
        self._request_counts[user_id].append(now)
        return True, "allowed"

    def filter_output(self, text: str) -> tuple[str, SecurityEvent | None]:
        """Filter output for sensitive data.

        Args:
            text: Output text to filter

        Returns:
            (filtered_text, event_if_any)
        """
        filtered = text
        event = None

        # Detect sensitive data
        sensitive = self._sensitive_detector.detect(text)
        if sensitive:
            # Mask sensitive data
            for data_type, matches in sensitive.items():
                for match in matches:
                    if data_type == "credit_card":
                        masked = "****-****-****-" + match[-4:]
                    elif data_type == "ssn":
                        masked = "***-**-" + match[-4:]
                    else:
                        masked = "***"
                    filtered = filtered.replace(match, masked)

            event = SecurityEvent(
                threat_type=ThreatType.DATA_LEAKAGE,
                threat_level=ThreatLevel.MEDIUM,
                description=f"Output filtered: {list(sensitive.keys())}",
                content=filtered[:500],
                action_taken="filtered",
            )
            self._log_event(event)

        return filtered, event

    def _log_event(self, event: SecurityEvent) -> None:
        """Log security event."""
        if self.config.log_all_events or (self.config.log_blocked_only and event.blocked):
            self._events.append(event)

    def get_events(
        self,
        threat_level: ThreatLevel | None = None,
        blocked_only: bool = False,
    ) -> list[SecurityEvent]:
        """Get security events.

        Args:
            threat_level: Filter by threat level
            blocked_only: Only return blocked events

        Returns:
            List of security events
        """
        events = self._events

        if threat_level:
            events = [e for e in events if e.threat_level == threat_level]

        if blocked_only:
            events = [e for e in events if e.blocked]

        return events

    def get_stats(self) -> dict[str, Any]:
        """Get security statistics."""
        return {
            "total_events": len(self._events),
            "blocked_events": sum(1 for e in self._events if e.blocked),
            "by_threat_type": {
                t.value: sum(1 for e in self._events if e.threat_type == t)
                for t in ThreatType
            },
            "by_threat_level": {
                l.value: sum(1 for e in self._events if e.threat_level == l)
                for l in ThreatLevel
            },
        }


# Global instance
_agent_firewall: AgentFirewall | None = None


def get_agent_firewall(config: SecurityConfig | None = None) -> AgentFirewall:
    """Get global Agent Firewall instance."""
    global _agent_firewall
    if _agent_firewall is None:
        _agent_firewall = AgentFirewall(config)
    return _agent_firewall
