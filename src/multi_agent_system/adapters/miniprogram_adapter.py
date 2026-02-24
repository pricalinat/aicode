"""Mini-program adapters for WeChat and Alipay."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class MiniProgramRequest:
    """A mini-program request."""
    platform: str  # "wechat" or "alipay"
    action: str
    parameters: dict[str, Any]
    user_id: str | None = None
    session_id: str | None = None


@dataclass
class MiniProgramResponse:
    """A mini-program response."""
    success: bool
    data: Any = None
    error: str | None = None
    platform: str = ""


class MiniProgramAdapter(ABC):
    """Abstract adapter for mini-program platforms."""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform name."""
        pass
    
    @abstractmethod
    def process_request(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Process a mini-program request."""
        pass
    
    @abstractmethod
    def format_for_platform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format data for platform-specific display."""
        pass
    
    def validate_request(self, request: MiniProgramRequest) -> bool:
        """Validate request parameters."""
        return bool(request.action)


class WeChatAdapter(MiniProgramAdapter):
    """Adapter for WeChat mini-program."""
    
    @property
    def platform_name(self) -> str:
        return "wechat"
    
    def process_request(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Process WeChat mini-program request."""
        try:
            # Route to appropriate handler
            if request.action == "search":
                return self._handle_search(request)
            elif request.action == "get_product":
                return self._handle_get_product(request)
            elif request.action == "get_service":
                return self._handle_get_service(request)
            elif request.action == "match":
                return self._handle_match(request)
            else:
                return MiniProgramResponse(
                    success=False,
                    error=f"Unknown action: {request.action}",
                    platform=self.platform_name,
                )
        except Exception as e:
            return MiniProgramResponse(
                success=False,
                error=str(e),
                platform=self.platform_name,
            )
    
    def _handle_search(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle search action."""
        from ..agents import EntityExtractionAgent, IntentClassificationAgent
        from ..core import Message
        
        text = request.parameters.get("keyword", "")
        
        # Extract entities
        extractor = EntityExtractionAgent()
        entity_msg = Message(task_type="extract_entities", content={"text": text})
        entity_resp = extractor.handle(entity_msg)
        
        # Classify intent
        classifier = IntentClassificationAgent()
        intent_msg = Message(task_type="classify_intent", content={"text": text})
        intent_resp = classifier.handle(intent_msg)
        
        # Format results
        data = {
            "extracted_entities": entity_resp.data if entity_resp.success else [],
            "intent": intent_resp.data if intent_resp.success else {},
            "wechat_card": self._create_wechat_card(entity_resp.data if entity_resp.success else {}),
        }
        
        return MiniProgramResponse(
            success=True,
            data=data,
            platform=self.platform_name,
        )
    
    def _handle_get_product(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle get product action."""
        from ..knowledge import get_graph, EntityType
        
        product_id = request.parameters.get("product_id")
        graph = get_graph()
        product = graph.get_entity(product_id)
        
        if not product:
            return MiniProgramResponse(
                success=False,
                error="Product not found",
                platform=self.platform_name,
            )
        
        return MiniProgramResponse(
            success=True,
            data=self.format_for_platform({
                "type": "product",
                "entity": product,
            }),
            platform=self.platform_name,
        )
    
    def _handle_get_service(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle get service action."""
        from ..knowledge import get_graph
        
        service_id = request.parameters.get("service_id")
        graph = get_graph()
        service = graph.get_entity(service_id)
        
        if not service:
            return MiniProgramResponse(
                success=False,
                error="Service not found",
                platform=self.platform_name,
            )
        
        return MiniProgramResponse(
            success=True,
            data=self.format_for_platform({
                "type": "service",
                "entity": service,
            }),
            platform=self.platform_name,
        )
    
    def _handle_match(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle match action."""
        from ..agents import MatchingAgent
        from ..core import Message
        
        query = request.parameters.get("query", {})
        direction = request.parameters.get("direction", "人找供给")
        
        matcher = MatchingAgent()
        msg = Message(
            task_type="match",
            content={"direction": direction, "query": query},
        )
        resp = matcher.handle(msg)
        
        return MiniProgramResponse(
            success=resp.success,
            data=self.format_for_platform(resp.data) if resp.success else None,
            error=resp.error,
            platform=self.platform_name,
        )
    
    def format_for_platform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format data for WeChat mini-program."""
        # Add WeChat-specific formatting
        formatted = {
            "errcode": 0,
            "errmsg": "ok",
            "data": data,
        }
        
        # Convert to WeChat card format if applicable
        if "wechat_card" in data:
            formatted["wechat_card"] = data["wechat_card"]
        
        return formatted
    
    def _create_wechat_card(self, entities: list[dict]) -> dict[str, Any]:
        """Create WeChat card for display."""
        return {
            "card_type": "merchant",
            "header": {
                "title": "为您推荐",
                "sub_title": "附近好店",
            },
            "entities": [
                {
                    "title": e.get("text", ""),
                    "type": e.get("type", ""),
                }
                for e in entities[:5]
            ],
        }


class AlipayAdapter(MiniProgramAdapter):
    """Adapter for Alipay mini-program."""
    
    @property
    def platform_name(self) -> str:
        return "alipay"
    
    def process_request(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Process Alipay mini-program request."""
        try:
            if request.action == "search":
                return self._handle_search(request)
            elif request.action == "get_product":
                return self._handle_get_product(request)
            elif request.action == "get_service":
                return self._handle_get_service(request)
            elif request.action == "match":
                return self._handle_match(request)
            else:
                return MiniProgramResponse(
                    success=False,
                    error=f"Unknown action: {request.action}",
                    platform=self.platform_name,
                )
        except Exception as e:
            return MiniProgramResponse(
                success=False,
                error=str(e),
                platform=self.platform_name,
            )
    
    def _handle_search(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle search action."""
        from ..agents import EntityExtractionAgent, IntentClassificationAgent
        from ..core import Message
        
        text = request.parameters.get("keyword", "")
        
        # Extract entities
        extractor = EntityExtractionAgent()
        entity_msg = Message(task_type="extract_entities", content={"text": text})
        entity_resp = extractor.handle(entity_msg)
        
        # Classify intent
        classifier = IntentClassificationAgent()
        intent_msg = Message(task_type="classify_intent", content={"text": text})
        intent_resp = classifier.handle(intent_msg)
        
        # Format results with Alipay style
        data = {
            "extracted_entities": entity_resp.data if entity_resp.success else [],
            "intent": intent_resp.data if intent_resp.success else {},
            "alipay_card": self._create_alipay_card(entity_resp.data if entity_resp.success else {}),
        }
        
        return MiniProgramResponse(
            success=True,
            data=data,
            platform=self.platform_name,
        )
    
    def _handle_get_product(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle get product action."""
        from ..knowledge import get_graph
        
        product_id = request.parameters.get("product_id")
        graph = get_graph()
        product = graph.get_entity(product_id)
        
        if not product:
            return MiniProgramResponse(
                success=False,
                error="Product not found",
                platform=self.platform_name,
            )
        
        return MiniProgramResponse(
            success=True,
            data=self.format_for_platform({
                "type": "product",
                "entity": product,
            }),
            platform=self.platform_name,
        )
    
    def _handle_get_service(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle get service action."""
        from ..knowledge import get_graph
        
        service_id = request.parameters.get("service_id")
        graph = get_graph()
        service = graph.get_entity(service_id)
        
        if not service:
            return MiniProgramResponse(
                success=False,
                error="Service not found",
                platform=self.platform_name,
            )
        
        return MiniProgramResponse(
            success=True,
            data=self.format_for_platform({
                "type": "service",
                "entity": service,
            }),
            platform=self.platform_name,
        )
    
    def _handle_match(self, request: MiniProgramRequest) -> MiniProgramResponse:
        """Handle match action."""
        from ..agents import MatchingAgent
        from ..core import Message
        
        query = request.parameters.get("query", {})
        direction = request.parameters.get("direction", "人找供给")
        
        matcher = MatchingAgent()
        msg = Message(
            task_type="match",
            content={"direction": direction, "query": query},
        )
        resp = matcher.handle(msg)
        
        return MiniProgramResponse(
            success=resp.success,
            data=self.format_for_platform(resp.data) if resp.success else None,
            error=resp.error,
            platform=self.platform_name,
        )
    
    def format_for_platform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format data for Alipay mini-program."""
        formatted = {
            "code": 10000,
            "msg": "Success",
            "data": data,
        }
        
        if "alipay_card" in data:
            formatted["alipay_card"] = data["alipay_card"]
        
        return formatted
    
    def _create_alipay_card(self, entities: list[dict]) -> dict[str, Any]:
        """Create Alipay card for display."""
        return {
            "card_type": "merchant",
            "header": {
                "title": "为您推荐",
                "sub_title": "附近好店",
            },
            "entities": [
                {
                    "title": e.get("text", ""),
                    "type": e.get("type", ""),
                }
                for e in entities[:5]
            ],
        }


class AdapterRegistry:
    """Registry for mini-program adapters."""
    
    def __init__(self) -> None:
        self._adapters: dict[str, MiniProgramAdapter] = {
            "wechat": WeChatAdapter(),
            "alipay": AlipayAdapter(),
        }
    
    def get_adapter(self, platform: str) -> MiniProgramAdapter | None:
        """Get adapter for a platform."""
        return self._adapters.get(platform.lower())
    
    def register(self, platform: str, adapter: MiniProgramAdapter) -> None:
        """Register a new adapter."""
        self._adapters[platform.lower()] = adapter
    
    def list_platforms(self) -> list[str]:
        """List available platforms."""
        return list(self._adapters.keys())


# Global adapter registry
_adapter_registry: AdapterRegistry | None = None


def get_adapter_registry() -> AdapterRegistry:
    """Get the global adapter registry."""
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry()
    return _adapter_registry
