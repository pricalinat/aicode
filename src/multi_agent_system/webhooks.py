"""Webhooks for external integrations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class Webhook:
    """A webhook definition."""
    id: str
    url: str
    event_type: str
    secret: str = ""
    enabled: bool = True


@dataclass
class WebhookPayload:
    """A webhook payload."""
    event: str
    data: dict
    timestamp: float
    webhook_id: str


class WebhookManager:
    """Manage webhooks."""
    
    def __init__(self) -> None:
        self._webhooks: Dict[str, Webhook] = {}
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register(
        self,
        url: str,
        event_type: str,
        secret: str = "",
    ) -> str:
        webhook_id = str(uuid.uuid4())
        webhook = Webhook(
            id=webhook_id,
            url=url,
            event_type=event_type,
            secret=secret,
        )
        self._webhooks[webhook_id] = webhook
        return webhook_id
    
    def unregister(self, webhook_id: str) -> bool:
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def trigger(self, event_type: str, data: dict) -> None:
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Webhook handler error: {e}")
    
    def list_webhooks(self, event_type: str | None = None) -> List[Webhook]:
        if event_type:
            return [w for w in self._webhooks.values() if w.event_type == event_type]
        return list(self._webhooks.values())


# Global webhook manager
_webhook_manager: WebhookManager | None = None


def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager
