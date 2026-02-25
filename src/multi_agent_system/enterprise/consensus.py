"""Consensus decision making for multi-agent systems.

Reference: "Silence is Not Consensus" - handles agreement bias in multi-agent systems
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConsensusStrategy(Enum):
    """Consensus building strategies."""

    MAJORITY = "majority"  # Simple majority vote
    WEIGHTED = "weighted"  # Weighted by confidence
    DEBATE = "debate"  # Multiple rounds of debate
    DELAYED = "delayed"  # Delay consensus to gather more evidence
    HIERARCHICAL = "hierarchical"  # Senior agents have more weight


@dataclass
class AgentOpinion:
    """An agent's opinion on a decision."""

    agent_id: str
    agent_type: str
    decision: str
    confidence: float  # 0-1
    reasoning: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class DecisionResult:
    """Result of a consensus decision."""

    decision: str
    confidence: float
    agreed_by: list[str]  # Agent IDs
    disagreed_by: list[str]  # Agent IDs
    strategy_used: ConsensusStrategy
    rounds: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


class ConsensusManager:
    """Manages consensus building among multiple agents.

    Addresses the "Silent Agreement" problem where agents prematurely converge.
    """

    def __init__(self) -> None:
        self.strategy = ConsensusStrategy.WEIGHTED
        self.min_confidence_threshold = 0.6
        self.debate_rounds = 3

    def set_strategy(self, strategy: ConsensusStrategy) -> None:
        """Set consensus strategy."""
        self.strategy = strategy

    def make_decision(self, opinions: list[AgentOpinion]) -> DecisionResult:
        """Make a consensus decision from agent opinions."""
        if not opinions:
            return DecisionResult(
                decision="",
                confidence=0.0,
                agreed_by=[],
                disagreed_by=[],
                strategy_used=self.strategy,
            )

        if self.strategy == ConsensusStrategy.MAJORITY:
            return self._majority_vote(opinions)
        elif self.strategy == ConsensusStrategy.WEIGHTED:
            return self._weighted_vote(opinions)
        elif self.strategy == ConsensusStrategy.DEBATE:
            return self._debate_round(opinions)
        elif self.strategy == ConsensusStrategy.DELAYED:
            return self._delayed_consensus(opinions)
        else:
            return self._majority_vote(opinions)

    def _majority_vote(self, opinions: list[AgentOpinion]) -> DecisionResult:
        """Simple majority vote."""
        # Group by decision
        votes: dict[str, list[AgentOpinion]] = {}
        for opinion in opinions:
            if opinion.decision not in votes:
                votes[opinion.decision] = []
            votes[opinion.decision].append(opinion)

        # Find majority
        best_decision = max(votes.keys(), key=lambda d: len(votes[d]))
        agreed = [o.agent_id for o in votes[best_decision]]

        # Get disagreeing agents
        disagreed = [o.agent_id for o in opinions if o.decision != best_decision]

        return DecisionResult(
            decision=best_decision,
            confidence=len(votes[best_decision]) / len(opinions),
            agreed_by=agreed,
            disagreed_by=disagreed,
            strategy_used=ConsensusStrategy.MAJORITY,
        )

    def _weighted_vote(self, opinions: list[AgentOpinion]) -> DecisionResult:
        """Weighted vote by confidence."""
        # Group by decision with weighted scores
        scores: dict[str, float] = {}
        opinions_by_decision: dict[str, list[AgentOpinion]] = {}

        for opinion in opinions:
            if opinion.decision not in scores:
                scores[opinion.decision] = 0.0
                opinions_by_decision[opinion.decision] = []

            scores[opinion.decision] += opinion.confidence
            opinions_by_decision[opinion.decision].append(opinion)

        # Find best decision
        best_decision = max(scores.keys(), key=lambda d: scores[d])

        agreed = [o.agent_id for o in opinions_by_decision[best_decision]]
        disagreed = [o.agent_id for o in opinions if o.decision != best_decision]

        return DecisionResult(
            decision=best_decision,
            confidence=scores[best_decision] / len(opinions),
            agreed_by=agreed,
            disagreed_by=disagreed,
            strategy_used=ConsensusStrategy.WEIGHTED,
        )

    def _debate_round(self, opinions: list[AgentOpinion]) -> DecisionResult:
        """Multi-round debate (simulated).

        In production, this would loop through multiple rounds.
        """
        # For now, use weighted but track rounds
        result = self._weighted_vote(opinions)
        result.strategy_used = ConsensusStrategy.DEBATE
        result.rounds = self.debate_rounds

        # Add metadata about disagreement
        if result.disagreed_by:
            result.metadata["needs_more_evidence"] = len(result.disagreed_by) / len(opinions) > 0.3

        return result

    def _delayed_consensus(self, opinions: list[AgentOpinion]) -> DecisionResult:
        """Delayed consensus - require more evidence.

        If agreement is too quick, request more evidence.
        """
        result = self._weighted_vote(opinions)
        result.strategy_used = ConsensusStrategy.DELAYED

        # If too quick to agree (>80%), flag for more evidence
        agreement_rate = len(result.agreed_by) / len(opinions) if opinions else 0
        if agreement_rate > 0.8:
            result.metadata["requires_more_evidence"] = True
            result.metadata["reason"] = "Agreement too quick, might be premature consensus"

        return result

    def detect_early_agreement(self, opinions: list[AgentOpinion]) -> bool:
        """Detect if agents are agreeing too quickly (potential early consensus)."""
        if len(opinions) < 3:
            return False

        # Check if all decisions are the same
        decisions = [o.decision for o in opinions]
        if len(set(decisions)) == 1:
            return True

        # Check if confidence variance is low (everyone is equally confident)
        confidences = [o.confidence for o in opinions]
        if max(confidences) - min(confidences) < 0.1:
            return True

        return False

    def suggest_dissent(self, opinions: list[AgentOpinion]) -> str | None:
        """Suggest an agent to present dissenting view."""
        if not opinions:
            return None

        # Find agent with lowest confidence
        lowest = min(opinions, key=lambda o: o.confidence)
        return f"Consider {lowest.agent_type} perspective more carefully - they have lower confidence"


# Global instance
_consensus_manager: ConsensusManager | None = None


def get_consensus_manager() -> ConsensusManager:
    """Get global consensus manager instance."""
    global _consensus_manager
    if _consensus_manager is None:
        _consensus_manager = ConsensusManager()
    return _consensus_manager
