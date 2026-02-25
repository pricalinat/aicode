"""Agent Role and Persona System.

Based on research about LLM agent role-playing, persona management,
and character modeling for multi-agent systems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PersonaType(Enum):
    """Types of personas."""
    EXPERT = "expert"           # Domain expert
    ASSISTANT = "assistant"     # General assistant
    CREATIVE = "creative"       # Creative writer
    ANALYTICAL = "analytical"   # Analyst
    CUSTOM = "custom"           # Custom persona


class CommunicationStyle(Enum):
    """Communication styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    DIRECT = "direct"


@dataclass
class PersonaAttribute:
    """A single persona attribute."""
    name: str = ""
    value: str = ""
    weight: float = 1.0  # Importance 0-1


@dataclass
class Persona:
    """Agent persona with characteristics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    persona_type: PersonaType = PersonaType.CUSTOM

    # Core traits
    description: str = ""
    background: str = ""  # Backstory
    expertise: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)

    # Behavior
    communication_style: CommunicationStyle = CommunicationStyle.CASUAL
    tone: str = "neutral"  # optimistic, pessimistic, neutral, etc.
    verbosity: str = "medium"  # brief, medium, detailed

    # Constraints
    biases: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    guidelines: list[str] = field(default_factory=list)

    # Dynamic traits
    attributes: dict[str, PersonaAttribute] = field(default_factory=dict)
    mood: float = 0.5  # 0-1, affects responses

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    def get_prompt_context(self) -> dict[str, Any]:
        """Get persona context for prompt injection."""
        return {
            "name": self.name,
            "description": self.description,
            "background": self.background,
            "expertise": self.expertise,
            "communication_style": self.communication_style.value,
            "tone": self.tone,
            "verbosity": self.verbosity,
        }

    def to_system_prompt(self) -> str:
        """Generate system prompt from persona."""
        parts = [f"You are {self.name}."]

        if self.description:
            parts.append(self.description)

        if self.background:
            parts.append(f"Background: {self.background}")

        if self.expertise:
            parts.append(f"Your expertise includes: {', '.join(self.expertise)}.")

        if self.communication_style != CommunicationStyle.CASUAL:
            parts.append(f"Communication style: {self.communication_style.value}.")

        if self.tone != "neutral":
            parts.append(f"Tone: {self.tone}.")

        if self.guidelines:
            parts.append("\\nGuidelines:")
            for g in self.guidelines:
                parts.append(f"- {g}")

        if self.limitations:
            parts.append("\\nLimitations:")
            for l in self.limitations:
                parts.append(f"- {l}")

        return "\n".join(parts)


@dataclass
class AgentRole:
    """Agent role definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Role-specific
    responsibilities: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

    # Hierarchy
    reports_to: str = ""  # Role ID this role reports to
    manages: list[str] = field(default_factory=list)  # Role IDs

    # Persona
    persona: Persona | None = None

    # Tools
    allowed_tools: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    def can_access_tool(self, tool_name: str) -> bool:
        """Check if role can access tool."""
        if tool_name in self.allowed_tools:
            return True
        if tool_name in self.required_tools:
            return True
        return len(self.allowed_tools) == 0  # All allowed if empty


class RoleRegistry:
    """Registry for managing agent roles and personas."""

    def __init__(self) -> None:
        """Initialize role registry."""
        self._roles: dict[str, AgentRole] = {}
        self._personas: dict[str, Persona] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default roles and personas."""
        # Default personas
        personas = [
            Persona(
                name="Research Assistant",
                persona_type=PersonaType.EXPERT,
                description="A thorough research assistant with expertise in information gathering.",
                communication_style=CommunicationStyle.FORMAL,
                expertise=["research", "analysis", "information retrieval"],
            ),
            Persona(
                name="Code Expert",
                persona_type=PersonaType.EXPERT,
                description="A skilled software developer focused on clean, efficient code.",
                communication_style=CommunicationStyle.TECHNICAL,
                expertise=["programming", "software design", "debugging"],
            ),
            Persona(
                name="Creative Writer",
                persona_type=PersonaType.CREATIVE,
                description="An imaginative writer who crafts engaging content.",
                communication_style=CommunicationStyle.FRIENDLY,
                interests=["storytelling", "creative writing", "poetry"],
            ),
        ]

        for p in personas:
            self._personas[p.id] = p

        # Default roles
        roles = [
            AgentRole(
                name="Researcher",
                description="Conducts research and gathers information",
                capabilities=["search", "analyze", "summarize"],
                persona=personas[0],
            ),
            AgentRole(
                name="Developer",
                description="Writes and reviews code",
                capabilities=["code", "debug", "test"],
                persona=personas[1],
            ),
            AgentRole(
                name="Writer",
                description="Creates content and documentation",
                capabilities=["write", "edit", "format"],
                persona=personas[2],
            ),
        ]

        for r in roles:
            self._roles[r.id] = r

    def register_role(self, role: AgentRole) -> AgentRole:
        """Register a role."""
        self._roles[role.id] = role
        return role

    def register_persona(self, persona: Persona) -> Persona:
        """Register a persona."""
        persona.updated_at = datetime.now()
        self._personas[persona.id] = persona
        return persona

    def get_role(self, role_id: str) -> AgentRole | None:
        """Get role by ID."""
        return self._roles.get(role_id)

    def get_persona(self, persona_id: str) -> Persona | None:
        """Get persona by ID."""
        return self._personas.get(persona_id)

    def list_roles(self) -> list[AgentRole]:
        """List all roles."""
        return list(self._roles.values())

    def list_personas(self) -> list[Persona]:
        """List all personas."""
        return list(self._personas.values())

    def assign_persona_to_role(self, role_id: str, persona_id: str) -> bool:
        """Assign persona to role."""
        role = self.get_role(role_id)
        persona = self.get_persona(persona_id)

        if role and persona:
            role.persona = persona
            return True
        return False


class PersonaManager:
    """Manages dynamic persona behavior and adaptation."""

    def __init__(self) -> None:
        """Initialize persona manager."""
        self._active_personas: dict[str, Persona] = {}

    def create_persona(
        self,
        name: str,
        description: str = "",
        persona_type: PersonaType = PersonaType.CUSTOM,
        **kwargs,
    ) -> Persona:
        """Create a new persona."""
        persona = Persona(
            name=name,
            description=description,
            persona_type=persona_type,
            **kwargs,
        )
        self._active_personas[persona.id] = persona
        return persona

    def activate_persona(self, agent_id: str, persona: Persona) -> None:
        """Activate persona for an agent."""
        self._active_personas[agent_id] = persona

    def deactivate_persona(self, agent_id: str) -> None:
        """Deactivate persona for an agent."""
        if agent_id in self._active_personas:
            del self._active_personas[agent_id]

    def get_active_persona(self, agent_id: str) -> Persona | None:
        """Get active persona for agent."""
        return self._active_personas.get(agent_id)

    def update_mood(self, agent_id: str, mood_delta: float) -> None:
        """Update agent mood."""
        persona = self._active_personas.get(agent_id)
        if persona:
            persona.mood = max(0.0, min(1.0, persona.mood + mood_delta))

    def adapt_persona(
        self,
        agent_id: str,
        feedback: dict[str, Any],
    ) -> Persona | None:
        """Adapt persona based on feedback."""
        persona = self._active_personas.get(agent_id)
        if not persona:
            return None

        # Adjust based on feedback
        if feedback.get("too_verbose"):
            if persona.verbosity == "detailed":
                persona.verbosity = "medium"
            elif persona.verbosity == "medium":
                persona.verbosity = "brief"

        if feedback.get("too_brief"):
            if persona.verbosity == "brief":
                persona.verbosity = "medium"
            elif persona.verbosity == "medium":
                persona.verbosity = "detailed"

        if feedback.get("tone"):
            persona.tone = feedback["tone"]

        persona.updated_at = datetime.now()
        return persona


# Global instances
_role_registry: RoleRegistry | None = None
_persona_manager: PersonaManager | None = None


def get_role_registry() -> RoleRegistry:
    """Get global role registry."""
    global _role_registry
    if _role_registry is None:
        _role_registry = RoleRegistry()
    return _role_registry


def get_persona_manager() -> PersonaManager:
    """Get global persona manager."""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager
