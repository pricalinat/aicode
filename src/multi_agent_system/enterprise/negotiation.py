"""Multi-Agent Negotiation System.

Provides negotiation, bargaining, and agreement mechanisms for multi-agent systems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NegotiationState(Enum):
    """Negotiation state."""
    PROPOSING = "proposing"
    COUNTERING = "countering"
    ACCEPTING = "accepting"
    REJECTING = "rejecting"
    COMPLETED = "completed"
    FAILED = "failed"


class OfferType(Enum):
    """Types of offers."""
    PROPOSAL = "proposal"
    COUNTER = "counter"
    ACCEPT = "accept"
    REJECT = "reject"
    WITHDRAW = "withdraw"


@dataclass
class Offer:
    """A negotiation offer."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    offer_type: OfferType = OfferType.PROPOSAL

    # Content
    terms: dict[str, Any] = field(default_factory=dict)
    value: float = 0.0
    explanation: str = ""

    # Sender
    agent_id: str = ""
    agent_name: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None


@dataclass
class NegotiationRound:
    """A round in negotiation."""
    round_number: int = 0
    offers: list[Offer] = field(default_factory=list)
    state: NegotiationState = NegotiationState.PROPOSING
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Negotiation:
    """A negotiation session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    description: str = ""

    # Parties
    parties: list[str] = field(default_factory=list)  # Agent IDs

    # Rounds
    rounds: list[NegotiationRound] = field(default_factory=list)
    current_round: int = 0

    # State
    state: NegotiationState = NegotiationState.PROPOSING
    final_offer: Offer | None = None

    # Result
    agreement: dict[str, Any] | None = None
    outcome: str = ""  # "agreement", "impasse", "withdrawal"

    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class NegotiationStrategy:
    """Base negotiation strategy."""

    def make_offer(
        self,
        negotiation: Negotiation,
        agent_id: str,
    ) -> Offer | None:
        """Make an offer."""
        raise NotImplementedError

    def evaluate_offer(
        self,
        offer: Offer,
        agent_id: str,
    ) -> tuple[bool, str]:
        """Evaluate an offer."""
        raise NotImplementedError


class BargainingStrategy(NegotiationStrategy):
    """Bargaining negotiation strategy."""

    def make_offer(
        self,
        negotiation: Negotiation,
        agent_id: str,
    ) -> Offer | None:
        """Make a bargaining offer."""
        round_num = len(negotiation.rounds)

        # Calculate offer value based on round
        base_value = 100.0
        decrement = 10.0 * round_num
        value = max(base_value - decrement, 50.0)

        return Offer(
            offer_type=OfferType.PROPOSAL,
            terms={"price": value},
            value=value,
            explanation=f"Round {round_num + 1} offer",
            agent_id=agent_id,
        )

    def evaluate_offer(
        self,
        offer: Offer,
        agent_id: str,
    ) -> tuple[bool, str]:
        """Evaluate offer."""
        # Accept if within range
        if offer.value >= 60.0:
            return True, "Acceptable offer"
        return False, "Needs improvement"


class NegotiationManager:
    """Manages multi-agent negotiations.

    Features:
    - Create negotiation sessions
    - Multi-party support
    - Strategy selection
    - Agreement tracking
    """

    def __init__(self) -> None:
        """Initialize negotiation manager."""
        self._negotiations: dict[str, Negotiation] = {}
        self._strategies: dict[str, NegotiationStrategy] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default strategies."""
        self._strategies["bargaining"] = BargainingStrategy()

    def create_negotiation(
        self,
        topic: str,
        parties: list[str],
        description: str = "",
    ) -> Negotiation:
        """Create a new negotiation."""
        negotiation = Negotiation(
            topic=topic,
            description=description,
            parties=parties,
        )
        self._negotiations[negotiation.id] = negotiation

        # Create first round
        self._add_round(negotiation.id)

        return negotiation

    def _add_round(self, negotiation_id: str) -> NegotiationRound | None:
        """Add a new round."""
        negotiation = self._negotiations.get(negotiation_id)
        if not negotiation:
            return None

        round_num = len(negotiation.rounds) + 1
        negotiation_round = NegotiationRound(
            round_number=round_num,
            state=NegotiationState.PROPOSING,
        )
        negotiation.rounds.append(negotiation_round)
        negotiation.current_round = round_num

        return negotiation_round

    def submit_offer(
        self,
        negotiation_id: str,
        agent_id: str,
        agent_name: str,
        offer: Offer,
    ) -> bool:
        """Submit an offer."""
        negotiation = self._negotiations.get(negotiation_id)
        if not negotiation:
            return False

        if not negotiation.rounds:
            return False

        offer.agent_id = agent_id
        offer.agent_name = agent_name

        negotiation.rounds[-1].offers.append(offer)
        negotiation.state = NegotiationState.COUNTERING

        return True

    def respond_to_offer(
        self,
        negotiation_id: str,
        agent_id: str,
        accept: bool,
        message: str = "",
    ) -> bool:
        """Respond to current offer."""
        negotiation = self._negotiations.get(negotiation_id)
        if not negotiation or not negotiation.rounds:
            return False

        current_round = negotiation.rounds[-1]
        if not current_round.offers:
            return False

        # Get last offer
        last_offer = current_round.offers[-1]

        if accept:
            # Accept
            last_offer.offer_type = OfferType.ACCEPT
            negotiation.state = NegotiationState.ACCEPTING
            negotiation.agreement = last_offer.terms
            negotiation.final_offer = last_offer
            negotiation.outcome = "agreement"
            negotiation.completed_at = datetime.now()
        else:
            # Reject
            last_offer.offer_type = OfferType.REJECT
            negotiation.state = NegotiationState.REJECTING

            # Check if max rounds reached
            if len(negotiation.rounds) >= 10:
                negotiation.state = NegotiationState.FAILED
                negotiation.outcome = "impasse"
                negotiation.completed_at = datetime.now()
            else:
                # Add new round
                self._add_round(negotiation_id)

        return True

    def get_negotiation(self, negotiation_id: str) -> Negotiation | None:
        """Get negotiation by ID."""
        return self._negotiations.get(negotiation_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get negotiation statistics."""
        total = len(self._negotiations)
        agreements = sum(1 for n in self._negotiations.values() if n.outcome == "agreement")
        impasses = sum(1 for n in self._negotiations.values() if n.outcome == "impasse")

        return {
            "total_negotiations": total,
            "agreements": agreements,
            "impasses": impasses,
            "success_rate": agreements / total if total > 0 else 0,
        }


# Global manager
_negotiation_manager: NegotiationManager | None = None


def get_negotiation_manager() -> NegotiationManager:
    """Get global negotiation manager."""
    global _negotiation_manager
    if _negotiation_manager is None:
        _negotiation_manager = NegotiationManager()
    return _negotiation_manager
