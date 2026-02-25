"""Multi-Agent Communication System.

Based on "Towards Effective GenAI Multi-Agent Collaboration" and related work.
Provides structured message passing, protocols, and coordination mechanisms.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class MessageType(Enum):
    """Message types in multi-agent communication."""
    REQUEST = "request"       # Request something from another agent
    RESPONSE = "response"    # Response to a request
    NOTIFICATION = "notification"  # One-way information
    QUERY = "query"          # Ask for information
    ANSWER = "answer"        # Answer to a query
    BROADCAST = "broadcast"  # Message to all agents
    ALERT = "alert"          # Urgent message
    PROPOSE = "propose"      # Proposal for collaboration


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class AgentAddress:
    """Agent address for routing."""
    agent_id: str = ""
    agent_type: str = ""  # "researcher", "planner", "executor", etc.
    capability: str = ""  # What the agent can do
    metadata: dict[str, Any] = field(default_factory=dict)

    def matches(self, agent_type: str | None = None, capability: str | None = None) -> bool:
        """Check if address matches criteria."""
        if agent_type and self.agent_type != agent_type:
            return False
        if capability and self.capability != capability:
            return False
        return True


@dataclass
class Message:
    """Agent message."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING

    # Routing
    sender: AgentAddress = field(default_factory=AgentAddress)
    recipient: AgentAddress | None = None  # None = broadcast
    recipients: list[AgentAddress] = field(default_factory=list)  # Multiple recipients

    # Content
    content: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    # Context
    conversation_id: str = ""  # For threading messages
    parent_message_id: str = ""  # Reply to specific message

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: datetime | None = None
    expires_at: datetime | None = None

    # Results
    response: dict[str, Any] | None = None
    error: str | None = None

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.recipient is None and len(self.recipients) == 0

    def is_reply(self) -> bool:
        """Check if this is a reply to another message."""
        return bool(self.parent_message_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.msg_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "sender": {
                "agent_id": self.sender.agent_id,
                "agent_type": self.sender.agent_type,
                "capability": self.sender.capability,
            },
            "content": self.content,
            "payload": self.payload,
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
        }


class MessageRouter:
    """Routes messages between agents."""

    def __init__(self) -> None:
        """Initialize message router."""
        self._agents: dict[str, AgentAddress] = {}
        self._handlers: dict[MessageType, list[Callable]] = {
            mt: [] for mt in MessageType
        }

    def register_agent(self, address: AgentAddress) -> None:
        """Register an agent."""
        self._agents[address.agent_id] = address

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]

    def find_agents(
        self,
        agent_type: str | None = None,
        capability: str | None = None,
    ) -> list[AgentAddress]:
        """Find agents matching criteria."""
        results = []
        for address in self._agents.values():
            if address.matches(agent_type, capability):
                results.append(address)
        return results

    def register_handler(self, msg_type: MessageType, handler: Callable) -> None:
        """Register message handler."""
        self._handlers[msg_type].append(handler)

    async def dispatch(self, message: Message) -> dict[str, Any]:
        """Dispatch message to appropriate handlers."""
        handlers = self._handlers.get(message.msg_type, [])

        results = []
        for handler in handlers:
            try:
                result = await handler(message)
                results.append({"handler": handler.__name__, "result": result})
            except Exception as e:
                results.append({"handler": handler.__name__, "error": str(e)})

        return {"dispatched": len(results), "results": results}


@dataclass
class Conversation:
    """Conversation thread between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: list[str] = field(default_factory=list)  # Agent IDs
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add message to conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages(
        self,
        agent_id: str | None = None,
        msg_type: MessageType | None = None,
    ) -> list[Message]:
        """Get messages with optional filters."""
        messages = self.messages

        if agent_id:
            messages = [m for m in messages if m.sender.agent_id == agent_id]

        if msg_type:
            messages = [m for m in messages if m.msg_type == msg_type]

        return messages


class AgentCommunication:
    """Multi-agent communication system.

    Features:
    - Structured message passing
    - Message routing and delivery
    - Conversation threading
    - Delivery guarantees
    """

    def __init__(self) -> None:
        """Initialize communication system."""
        self.router = MessageRouter()
        self._conversations: dict[str, Conversation] = {}
        self._pending_messages: dict[str, Message] = {}
        self._delivery_callbacks: list[Callable] = []

    def register_agent(self, agent_id: str, agent_type: str = "", capability: str = "") -> None:
        """Register an agent."""
        address = AgentAddress(
            agent_id=agent_id,
            agent_type=agent_type,
            capability=capability,
        )
        self.router.register_agent(address)

    def send_message(
        self,
        sender_id: str,
        recipient_id: str | None = None,
        content: str = "",
        msg_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.NORMAL,
        payload: dict[str, Any] | None = None,
        conversation_id: str | None = None,
    ) -> Message:
        """Send a message.

        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID (None for broadcast)
            content: Message content
            msg_type: Message type
            priority: Message priority
            payload: Additional payload
            conversation_id: Conversation thread ID

        Returns:
            Created message
        """
        # Get sender address
        sender_addr = self.router._agents.get(sender_id)
        if not sender_addr:
            raise ValueError(f"Unknown sender: {sender_id}")

        # Create message
        message = Message(
            msg_type=msg_type,
            priority=priority,
            sender=sender_addr,
            content=content,
            payload=payload or {},
            conversation_id=conversation_id or str(uuid.uuid4()),
        )

        # Set recipient if specified
        if recipient_id:
            recipient_addr = self.router._agents.get(recipient_id)
            if recipient_addr:
                message.recipient = recipient_addr
        else:
            # Broadcast - find all other agents
            message.recipients = [
                addr for addr in self.router._agents.values()
                if addr.agent_id != sender_id
            ]

        # Store in pending
        self._pending_messages[message.id] = message

        # Update conversation
        conv_id = message.conversation_id
        if conv_id not in self._conversations:
            self._conversations[conv_id] = Conversation(id=conv_id)
            self._conversations[conv_id].participants = [sender_id]
            if recipient_id:
                self._conversations[conv_id].participants.append(recipient_id)

        self._conversations[conv_id].add_message(message)
        self._conversations[conv_id].participants.extend([
            sender_id,
            recipient_id
        ]) if recipient_id else []

        # Update status
        message.status = MessageStatus.SENT

        return message

    def reply_to(
        self,
        original_message: Message,
        sender_id: str,
        content: str,
        msg_type: MessageType = MessageType.RESPONSE,
        payload: dict[str, Any] | None = None,
    ) -> Message:
        """Reply to a message."""
        return self.send_message(
            sender_id=sender_id,
            recipient_id=original_message.sender.agent_id,
            content=content,
            msg_type=msg_type,
            conversation_id=original_message.conversation_id,
            payload=payload,
        )

    def broadcast(
        self,
        sender_id: str,
        content: str,
        msg_type: MessageType = MessageType.BROADCAST,
        payload: dict[str, Any] | None = None,
    ) -> Message:
        """Broadcast to all agents."""
        return self.send_message(
            sender_id=sender_id,
            recipient_id=None,  # Broadcast
            content=content,
            msg_type=msg_type,
            payload=payload,
        )

    def query_agents(
        self,
        sender_id: str,
        query: str,
        agent_type: str | None = None,
        capability: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[Message]:
        """Query multiple agents."""
        # Find matching agents
        recipients = self.router.find_agents(agent_type, capability)

        messages = []
        for recipient in recipients:
            msg = self.send_message(
                sender_id=sender_id,
                recipient_id=recipient.agent_id,
                content=query,
                msg_type=MessageType.QUERY,
                payload=payload,
            )
            messages.append(msg)

        return messages

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_agent_messages(self, agent_id: str) -> list[Message]:
        """Get all messages for an agent."""
        messages = []
        for conv in self._conversations.values():
            messages.extend(conv.get_messages(agent_id))
        return sorted(messages, key=lambda m: m.created_at)

    def get_statistics(self) -> dict[str, Any]:
        """Get communication statistics."""
        total_messages = len(self._pending_messages)
        by_type = {}
        by_priority = {}

        for msg in self._pending_messages.values():
            t = msg.msg_type.value
            by_type[t] = by_type.get(t, 0) + 1

            p = msg.priority.value
            by_priority[p] = by_priority.get(p, 0) + 1

        return {
            "total_messages": total_messages,
            "active_conversations": len(self._conversations),
            "registered_agents": len(self.router._agents),
            "by_type": by_type,
            "by_priority": by_priority,
        }


# Global communication system
_communication: AgentCommunication | None = None


def get_communication() -> AgentCommunication:
    """Get global communication system."""
    global _communication
    if _communication is None:
        _communication = AgentCommunication()
    return _communication
