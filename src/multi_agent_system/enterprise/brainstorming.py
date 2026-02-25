"""Multi-agent brainstorming system.

Reference: "Exploring Design of Multi-Agent LLM Dialogues for Research Ideation"

Enables multiple agents to collaborate and generate creative ideas through structured dialogue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AgentRole(Enum):
    """Roles in brainstorming session."""

    RESEARCHER = "researcher"  # Research expert
    CRITIC = "critic"  # Evaluates ideas
    CREATOR = "creator"  # Generates novel ideas
    SYNTHESIZER = "synthesizer"  # Combines ideas
    EXPANDER = "expander"  # Expands on ideas


@dataclass
class BrainstormAgent:
    """A participant agent in brainstorming."""

    role: AgentRole
    persona: str  # Description of the agent's perspective
    expertise: list[str]  # Areas of expertise
    name: str = ""


@dataclass
class Idea:
    """A single idea generated during brainstorming."""

    id: str
    content: str
    author_role: str
    parent_id: str | None = None
    votes: int = 0
    comments: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class BrainstormSession:
    """A brainstorming session."""

    session_id: str
    topic: str
    agents: list[BrainstormAgent] = field(default_factory=list)
    ideas: list[Idea] = field(default_factory=list)
    rounds: int = 0
    max_rounds: int = 5
    created_at: str = ""
    status: str = "active"  # active, completed, cancelled


class MultiAgentBrainstorming:
    """Multi-agent brainstorming system.

    Coordinates multiple agents with different roles to generate creative ideas.
    """

    # Default agent configurations
    DEFAULT_AGENTS = [
        BrainstormAgent(
            role=AgentRole.RESEARCHER,
            persona="A research expert with deep knowledge in the field",
            expertise=["literature review", "methodology", "state-of-art"],
            name="Researcher",
        ),
        BrainstormAgent(
            role=AgentRole.CRITIC,
            persona="A critical thinker who evaluates ideas rigorously",
            expertise=["problem identification", "weakness analysis", "risk assessment"],
            name="Critic",
        ),
        BrainstormAgent(
            role=AgentRole.CREATOR,
            persona="A creative thinker who generates novel ideas",
            expertise=["ideation", "innovation", "cross-domain connections"],
            name="Creator",
        ),
        BrainstormAgent(
            role=AgentRole.SYNTHESIZER,
            persona="A synthesizer who combines diverse ideas into coherent solutions",
            expertise=["integration", "pattern recognition", "solution design"],
            name="Synthesizer",
        ),
    ]

    def __init__(self) -> None:
        self.sessions: dict[str, BrainstormSession] = {}
        self.output_path = Path("./data/brainstorming")
        self.output_path.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        topic: str,
        custom_agents: list[BrainstormAgent] | None = None,
        max_rounds: int = 5,
    ) -> str:
        """Create a new brainstorming session."""
        import uuid
        from datetime import datetime

        session_id = str(uuid.uuid4())[:12]
        agents = custom_agents or self.DEFAULT_AGENTS

        session = BrainstormSession(
            session_id=session_id,
            topic=topic,
            agents=agents,
            max_rounds=max_rounds,
            created_at=datetime.now().isoformat(),
        )

        self.sessions[session_id] = session
        return session_id

    def generate_ideas(
        self,
        session_id: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Generate ideas through multi-round brainstorming.

        Args:
            session_id: The brainstorming session
            context: Additional context/information

        Returns:
            Generated ideas and session results
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        if session.status != "active":
            return {"error": "Session is not active"}

        results = []

        # Round 1: Each agent generates initial ideas
        for agent in session.agents:
            # In production, this would call actual LLM
            idea = self._generate_agent_idea(agent, session.topic, context, round=1)
            session.ideas.append(idea)
            results.append({
                "role": agent.role.value,
                "idea": idea.content,
            })

        session.rounds = 1

        # Round 2-3: Expansion and critique
        for round_num in range(2, session.max_rounds + 1):
            # Creator expands on ideas
            creator = next((a for a in session.agents if a.role == AgentRole.CREATOR), None)
            if creator:
                expanded = self._generate_agent_idea(
                    creator,
                    session.topic,
                    f"Build on these ideas: {[i.content for i in session.ideas[-3:]]}",
                    round=round_num,
                )
                session.ideas.append(expanded)
                results.append({
                    "role": "creator_expansion",
                    "idea": expanded.content,
                })

            # Critic evaluates
            critic = next((a for a in session.agents if a.role == AgentRole.CRITIC), None)
            if critic:
                critique = self._generate_critique(
                    critic,
                    session.topic,
                    session.ideas[-3:],
                )
                results.append({
                    "role": "critique",
                    "content": critique,
                })

            session.rounds = round_num

        # Final round: Synthesizer combines
        synthesizer = next((a for a in session.agents if a.role == AgentRole.SYNTHESIZER), None)
        if synthesizer:
            final = self._generate_synthesis(
                synthesizer,
                session.topic,
                session.ideas,
            )
            results.append({
                "role": "synthesis",
                "idea": final.content,
            })
            session.ideas.append(final)

        session.status = "completed"

        # Save session
        self._save_session(session)

        return {
            "session_id": session_id,
            "topic": session.topic,
            "rounds": session.rounds,
            "total_ideas": len(session.ideas),
            "results": results,
            "final_ideas": [i.content for i in session.ideas if i.role == AgentRole.SYNTHESIZER.value],
        }

    def _generate_agent_idea(
        self,
        agent: BrainstormAgent,
        topic: str,
        context: str,
        round: int,
    ) -> Idea:
        """Generate an idea as a specific agent (simulated)."""
        import uuid

        # In production, this would call LLM with agent persona
        templates = {
            AgentRole.RESEARCHER: f"Research approach to {topic}: ",
            AgentRole.CREATOR: f"Innovative angle on {topic}: ",
            AgentRole.CRITIC: f"Critical analysis of {topic}: ",
            AgentRole.SYNTHESIZER: f"Integrated solution for {topic}: ",
        }

        content = templates.get(agent.role, f"Idea about {topic}: ") + f"Round {round} contribution"

        return Idea(
            id=str(uuid.uuid4())[:12],
            content=content,
            author_role=agent.role.value,
        )

    def _generate_critique(
        self,
        agent: BrainstormAgent,
        topic: str,
        ideas: list[Idea],
    ) -> str:
        """Generate critique (simulated)."""
        return f"Critique of {len(ideas)} ideas about {topic}: Consider feasibility and scalability"

    def _generate_synthesis(
        self,
        agent: BrainstormAgent,
        topic: str,
        ideas: list[Idea],
    ) -> Idea:
        """Generate final synthesis (simulated)."""
        import uuid

        content = f"Final synthesis for {topic}: Combining {len(ideas)} ideas into a coherent approach"

        return Idea(
            id=str(uuid.uuid4())[:12],
            content=content,
            author_role=agent.role.value,
        )

    def vote_ideas(self, session_id: str, idea_id: str, votes: int = 1) -> bool:
        """Vote for an idea."""
        session = self.sessions.get(session_id)
        if not session:
            return False

        for idea in session.ideas:
            if idea.id == idea_id:
                idea.votes += votes
                return True
        return False

    def get_top_ideas(self, session_id: str, top_k: int = 5) -> list[Idea]:
        """Get top voted ideas."""
        session = self.sessions.get(session_id)
        if not session:
            return []

        sorted_ideas = sorted(session.ideas, key=lambda x: -x.votes)
        return sorted_ideas[:top_k]

    def get_session(self, session_id: str) -> BrainstormSession | None:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def _save_session(self, session: BrainstormSession) -> None:
        """Save session to file."""
        session_file = self.output_path / f"{session.session_id}.json"

        data = {
            "session_id": session.session_id,
            "topic": session.topic,
            "rounds": session.rounds,
            "status": session.status,
            "ideas": [
                {
                    "id": i.id,
                    "content": i.content,
                    "author_role": i.author_role,
                    "votes": i.votes,
                }
                for i in session.ideas
            ],
        }

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)


# Global instance
_brainstorming: MultiAgentBrainstorming | None = None


def get_brainstorming() -> MultiAgentBrainstorming:
    """Get global brainstorming instance."""
    global _brainstorming
    if _brainstorming is None:
        _brainstorming = MultiAgentBrainstorming()
    return _brainstorming
