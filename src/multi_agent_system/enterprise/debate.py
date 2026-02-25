"""Multi-Agent Debate System.

Based on "The Social Laboratory: A Psychometric Framework for Multi-Agent LLM"
and related work on multi-agent reasoning, debate, and consensus building.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class DebateRole(Enum):
    """Roles in a debate."""
    PROPOSER = "proposer"       # Proposes an idea
    OPPONENT = "opponent"       # Challenges the idea
    MODERATOR = "moderator"     # Guides the debate
    EXPERT = "expert"           # Provides domain expertise
    ANALYST = "analyst"         # Analyzes arguments


class ArgumentType(Enum):
    """Types of arguments."""
    FACT = "fact"               # Factual claim
    OPINION = "opinion"         # Opinion
    EVIDENCE = "evidence"       # Evidence-based
    COUNTER = "counter"        # Counter-argument
    REFUTATION = "refutation"  # Refutation
    QUESTION = "question"       # Question


class DebateStage(Enum):
    """Stages of a debate."""
    OPENING = "opening"         # Opening statements
    ARGUMENT = "argument"       # Main arguments
    REBUTTAL = "rebuttal"       # Rebuttals
    QUESTION = "question"        # Questions
    CLOSING = "closing"         # Closing statements
    JUDGMENT = "judgment"      # Final judgment


@dataclass
class Argument:
    """A single argument in the debate."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    argument_type: ArgumentType = ArgumentType.OPINION
    content: str = ""
    evidence: list[str] = field(default_factory=list)
    source: str = ""  # Agent ID who made the argument

    # Quality metrics
    strength: float = 0.5  # 0-1
    relevance: float = 0.5  # 0-1
    clarity: float = 0.5  # 0-1

    created_at: datetime = field(default_factory=datetime.now)

    def quality_score(self) -> float:
        """Calculate overall quality score."""
        return (self.strength + self.relevance + self.clarity) / 3


@dataclass
class AgentPosition:
    """An agent's position in the debate."""
    agent_id: str = ""
    agent_name: str = ""
    role: DebateRole = DebateRole.PROPOSER
    stance: str = ""  # "support", "oppose", "neutral"

    # Arguments made
    arguments: list[Argument] = field(default_factory=list)

    # Scores
    participation_score: float = 0.0
    persuasion_score: float = 0.0
    quality_score: float = 0.0

    # Metadata
    joined_at: datetime = field(default_factory=datetime.now)

    def add_argument(self, argument: Argument) -> None:
        """Add argument to position."""
        self.arguments.append(argument)
        self.update_scores()

    def update_scores(self) -> None:
        """Update scores based on arguments."""
        if self.arguments:
            # Quality score
            self.quality_score = sum(a.quality_score() for a in self.arguments) / len(self.arguments)

            # Participation score
            self.participation_score = min(1.0, len(self.arguments) / 5)


@dataclass
class DebateRound:
    """A single round of debate."""
    round_number: int = 0
    stage: DebateStage = DebateStage.ARGUMENT
    prompt: str = ""
    positions: list[AgentPosition] = field(default_factory=list)
    arguments: list[Argument] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Debate:
    """A complete debate session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    description: str = ""

    # Participants
    positions: dict[str, AgentPosition] = field(default_factory=dict)  # agent_id -> position

    # Rounds
    rounds: list[DebateRound] = field(default_factory=list)
    current_round: int = 0

    # Configuration
    max_rounds: int = 3
    require_consensus: bool = False

    # Results
    winner: str | None = None  # Agent ID who won
    consensus_reached: bool = False
    final_summary: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def add_agent(
        self,
        agent_id: str,
        agent_name: str,
        role: DebateRole,
        stance: str = "neutral",
    ) -> AgentPosition:
        """Add agent to debate."""
        position = AgentPosition(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            stance=stance,
        )
        self.positions[agent_id] = position
        return position

    def get_position(self, agent_id: str) -> AgentPosition | None:
        """Get agent's position."""
        return self.positions.get(agent_id)

    def add_argument(
        self,
        agent_id: str,
        argument: Argument,
    ) -> bool:
        """Add argument from agent."""
        position = self.positions.get(agent_id)
        if not position:
            return False

        position.add_argument(argument)

        # Add to current round
        if self.rounds:
            self.rounds[-1].arguments.append(argument)

        return True


class DebateJudge:
    """Judges debate outcomes.

    Evaluates arguments and determines winner or consensus.
    """

    def __init__(
        self,
        consensus_threshold: float = 0.7,
    ) -> None:
        """Initialize debate judge.

        Args:
            consensus_threshold: Threshold for consensus (0-1)
        """
        self.consensus_threshold = consensus_threshold

    def evaluate_debate(self, debate: Debate) -> dict[str, Any]:
        """Evaluate debate and determine outcome.

        Args:
            debate: Debate to evaluate

        Returns:
            Evaluation results
        """
        if not debate.rounds:
            return {"error": "No rounds in debate"}

        # Calculate scores for each agent
        agent_scores = {}
        for agent_id, position in debate.positions.items():
            agent_scores[agent_id] = {
                "quality_score": position.quality_score,
                "participation_score": position.participation_score,
                "argument_count": len(position.arguments),
            }

        # Determine winner (highest quality score)
        winner = None
        if agent_scores:
            winner = max(agent_scores.items(), key=lambda x: x[1]["quality_score"])[0]

        # Check for consensus
        consensus_reached = False
        if len(agent_scores) >= 2:
            scores = [s["quality_score"] for s in agent_scores.values()]
            avg = sum(scores) / len(scores)
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)
            if variance < (1 - self.consensus_threshold) ** 2:
                consensus_reached = True

        # Generate summary
        summary = self._generate_summary(debate, agent_scores, winner, consensus_reached)

        return {
            "winner": winner,
            "consensus_reached": consensus_reached,
            "agent_scores": agent_scores,
            "summary": summary,
        }

    def _generate_summary(
        self,
        debate: Debate,
        agent_scores: dict,
        winner: str | None,
        consensus: bool,
    ) -> str:
        """Generate debate summary."""
        parts = [f"Debate on: {debate.topic}"]

        if consensus:
            parts.append("Consensus was reached among participants.")
        elif winner:
            position = debate.positions.get(winner)
            if position:
                parts.append(f"Winner: {position.agent_name} (score: {agent_scores[winner]['quality_score']:.2f})")

        parts.append(f"Total rounds: {len(debate.rounds)}")
        parts.append(f"Total arguments: {sum(len(r.arguments) for r in debate.rounds)}")

        return "\n".join(parts)


class MultiAgentDebate:
    """Multi-agent debate system.

    Features:
    - Structured debate rounds
    - Multiple roles (proposer, opponent, moderator, expert)
    - Argument quality tracking
    - Consensus detection
    - Automated judging
    """

    def __init__(
        self,
        max_rounds: int = 3,
        consensus_threshold: float = 0.7,
    ) -> None:
        """Initialize multi-agent debate.

        Args:
            max_rounds: Maximum debate rounds
            consensus_threshold: Threshold for consensus
        """
        self.max_rounds = max_rounds
        self.judge = DebateJudge(consensus_threshold)

        # Active debates
        self._debates: dict[str, Debate] = {}

        # Callbacks
        self._on_round_start: list[Callable] = []
        self._on_argument: list[Callable] = []
        self._on_round_end: list[Callable] = []

    def create_debate(
        self,
        topic: str,
        description: str = "",
        max_rounds: int | None = None,
    ) -> Debate:
        """Create a new debate.

        Args:
            topic: Debate topic
            description: Detailed description
            max_rounds: Maximum rounds (uses default if None)

        Returns:
            Created debate
        """
        debate = Debate(
            topic=topic,
            description=description,
            max_rounds=max_rounds or self.max_rounds,
        )
        self._debates[debate.id] = debate
        return debate

    def add_participant(
        self,
        debate_id: str,
        agent_id: str,
        agent_name: str,
        role: DebateRole = DebateRole.PROPOSER,
        stance: str = "neutral",
    ) -> bool:
        """Add participant to debate."""
        debate = self._debates.get(debate_id)
        if not debate:
            return False

        debate.add_agent(agent_id, agent_name, role, stance)
        return True

    async def start_debate(self, debate_id: str) -> DebateRound | None:
        """Start the debate."""
        debate = self._debates.get(debate_id)
        if not debate:
            return None

        # Create first round
        round_num = len(debate.rounds) + 1
        debate_round = DebateRound(
            round_number=round_num,
            stage=DebateStage.OPENING,
            prompt=f"Opening statements on: {debate.topic}",
        )
        debate.rounds.append(debate_round)
        debate.current_round = round_num

        # Trigger callback
        for cb in self._on_round_start:
            await cb(debate, debate_round)

        return debate_round

    async def submit_argument(
        self,
        debate_id: str,
        agent_id: str,
        content: str,
        argument_type: ArgumentType = ArgumentType.OPINION,
        evidence: list[str] | None = None,
    ) -> bool:
        """Submit argument in current round."""
        debate = self._debates.get(debate_id)
        if not debate or not debate.rounds:
            return False

        argument = Argument(
            argument_type=argument_type,
            content=content,
            evidence=evidence or [],
            source=agent_id,
        )

        success = debate.add_argument(agent_id, argument)

        if success:
            # Trigger callback
            for cb in self._on_argument:
                await cb(debate, argument)

        return success

    async def next_round(self, debate_id: str) -> DebateRound | None:
        """Advance to next debate round."""
        debate = self._debates.get(debate_id)
        if not debate:
            return None

        if len(debate.rounds) >= debate.max_rounds:
            return None  # Debate complete

        # Determine next stage
        stages = list(DebateStage)
        current_stage_idx = stages.index(debate.rounds[-1].stage)

        if current_stage_idx < len(stages) - 2:  # Not at judgment
            next_stage = stages[current_stage_idx + 1]
        else:
            next_stage = DebateStage.JUDGMENT

        # Create new round
        round_num = len(debate.rounds) + 1
        debate_round = DebateRound(
            round_number=round_num,
            stage=next_stage,
            prompt=f"Round {round_num}: {next_stage.value}",
        )
        debate.rounds.append(debate_round)
        debate.current_round = round_num

        # Trigger callback
        for cb in self._on_round_end:
            await cb(debate, debate.rounds[-2])

        return debate_round

    async def conclude_debate(self, debate_id: str) -> dict[str, Any] | None:
        """Conclude debate and get results."""
        debate = self._debates.get(debate_id)
        if not debate:
            return None

        # Evaluate debate
        results = self.judge.evaluate_debate(debate)

        # Update debate
        debate.winner = results.get("winner")
        debate.consensus_reached = results.get("consensus_reached", False)
        debate.final_summary = results.get("summary", "")
        debate.completed_at = datetime.now()

        return {
            "debate_id": debate.id,
            "topic": debate.topic,
            "winner": debate.winner,
            "consensus_reached": debate.consensus_reached,
            "summary": debate.final_summary,
            "rounds": len(debate.rounds),
            "total_arguments": sum(len(r.arguments) for r in debate.rounds),
            "agent_scores": results.get("agent_scores", {}),
        }

    def on_round_start(self, callback: Callable) -> None:
        """Register round start callback."""
        self._on_round_start.append(callback)

    def on_argument(self, callback: Callable) -> None:
        """Register argument callback."""
        self._on_argument.append(callback)

    def on_round_end(self, callback: Callable) -> None:
        """Register round end callback."""
        self._on_round_end.append(callback)


# Global debate system
_debate_system: MultiAgentDebate | None = None


def get_debate_system() -> MultiAgentDebate:
    """Get global debate system."""
    global _debate_system
    if _debate_system is None:
        _debate_system = MultiAgentDebate()
    return _debate_system
