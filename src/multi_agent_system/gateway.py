"""Unified API Gateway for the multi-agent system."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..adapters import AdapterRegistry, MiniProgramRequest, get_adapter_registry
from ..agents import (
    ArxivAgent,
    EntityExtractionAgent,
    IntentClassificationAgent,
    MatchingAgent,
    SemanticSearchAgent,
)
from ..core import AgentResponse, Message, Orchestrator, get_tracer, trace, TraceLevel
from ..knowledge import Entity, EntityType, Relation, RelationType, get_graph


@dataclass
class APIRequest:
    """Unified API request format."""
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    platform: str | None = None  # "wechat", "alipay", or None for direct
    user_id: str | None = None


@dataclass
class APIResponse:
    """Unified API response format."""
    success: bool
    data: Any = None
    error: str | None = None
    trace_id: str | None = None


class APIGateway:
    """Unified API Gateway for the multi-agent system.
    
    Provides a single entry point for:
    - Direct agent invocation
    - Mini-program platform integration (WeChat, Alipay)
    - Knowledge graph operations
    """
    
    def __init__(self) -> None:
        # Initialize orchestrator with all agents
        self.orchestrator = Orchestrator([
            ArxivAgent(),
            EntityExtractionAgent(),
            IntentClassificationAgent(),
            MatchingAgent(),
            SemanticSearchAgent(),
        ])
        
        # Initialize adapter registry
        self.adapter_registry = get_adapter_registry()
        
        # Action handlers
        self._handlers: dict[str, callable] = {
            # Knowledge graph operations
            "graph.create_entity": self._handle_create_entity,
            "graph.get_entity": self._handle_get_entity,
            "graph.update_entity": self._handle_update_entity,
            "graph.delete_entity": self._handle_delete_entity,
            "graph.create_relation": self._handle_create_relation,
            "graph.search": self._handle_graph_search,
            
            # Agent operations
            "agent.extract_entities": self._handle_extract_entities,
            "agent.classify_intent": self._handle_classify_intent,
            "agent.match": self._handle_match,
            "agent.semantic_search": self._handle_semantic_search,
            
            # Arxiv (paper search)
            "arxiv.search": self._handle_arxiv_search,
            
            # Mini-program operations
            "miniprogram.search": self._handle_miniprogram_search,
            "miniprogram.match": self._handle_miniprogram_match,
        }
    
    def process(self, request: APIRequest) -> APIResponse:
        """Process an API request."""
        trace_id = request.parameters.get("trace_id")
        trace(trace_id or "unknown", TraceLevel.ORCHESTRATOR_START, message=f"API request: {request.action}")
        
        try:
            # Handle mini-program requests
            if request.platform in ("wechat", "alipay"):
                return self._handle_miniprogram(request)
            
            # Handle direct actions
            handler = self._handlers.get(request.action)
            if handler is None:
                return APIResponse(
                    success=False,
                    error=f"Unknown action: {request.action}",
                    trace_id=trace_id,
                )
            
            result = handler(request.parameters)
            
            trace(trace_id or "unknown", TraceLevel.ORCHESTRATOR_END, message=f"API request completed: {request.action}")
            
            return APIResponse(
                success=True,
                data=result,
                trace_id=trace_id,
            )
            
        except Exception as exc:
            trace(trace_id or "unknown", TraceLevel.AGENT_ERROR, message=f"API error: {exc}")
            return APIResponse(
                success=False,
                error=str(exc),
                trace_id=trace_id,
            )
    
    def _handle_miniprogram(self, request: APIRequest) -> APIResponse:
        """Handle mini-program platform request."""
        adapter = self.adapter_registry.get_adapter(request.platform)
        if adapter is None:
            return APIResponse(
                success=False,
                error=f"Unknown platform: {request.platform}",
            )
        
        mp_request = MiniProgramRequest(
            platform=request.platform,
            action=request.parameters.get("action", "search"),
            parameters=request.parameters,
            user_id=request.user_id,
        )
        
        mp_response = adapter.process_request(mp_request)
        
        return APIResponse(
            success=mp_response.success,
            data=mp_response.data,
            error=mp_response.error,
        )
    
    # Graph handlers
    def _handle_create_entity(self, params: dict) -> dict:
        graph = get_graph()
        entity = Entity(
            id=params["id"],
            type=EntityType(params["type"]),
            properties=params.get("properties", {}),
        )
        graph.create_entity(entity)
        return {"id": entity.id, "type": entity.type.value}
    
    def _handle_get_entity(self, params: dict) -> dict | None:
        graph = get_graph()
        entity = graph.get_entity(params["id"])
        if entity:
            return {
                "id": entity.id,
                "type": entity.type.value,
                "name": entity.name,
                "properties": entity.properties,
            }
        return None
    
    def _handle_update_entity(self, params: dict) -> dict:
        graph = get_graph()
        entity = Entity(
            id=params["id"],
            type=EntityType(params["type"]),
            properties=params.get("properties", {}),
        )
        graph.update_entity(entity)
        return {"id": entity.id, "updated": True}
    
    def _handle_delete_entity(self, params: dict) -> dict:
        graph = get_graph()
        deleted = graph.delete_entity(params["id"])
        return {"id": params["id"], "deleted": deleted}
    
    def _handle_create_relation(self, params: dict) -> dict:
        graph = get_graph()
        relation = Relation(
            source_id=params["source_id"],
            target_id=params["target_id"],
            relation_type=RelationType(params["relation_type"]),
            properties=params.get("properties", {}),
        )
        graph.create_relation(relation)
        return {"source": relation.source_id, "target": relation.target_id, "created": True}
    
    def _handle_graph_search(self, params: dict) -> dict:
        graph = get_graph()
        entity_type = None
        if params.get("entity_type"):
            entity_type = EntityType(params["entity_type"])
        
        entities = graph.search(
            entity_type=entity_type,
            text=params.get("text"),
            filters=params.get("filters"),
            limit=params.get("limit", 20),
        )
        
        return {
            "results": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "name": e.name,
                    "properties": e.properties,
                }
                for e in entities
            ],
            "total": len(entities),
        }
    
    # Agent handlers
    def _handle_extract_entities(self, params: dict) -> dict:
        message = Message(
            task_type="extract_entities",
            content={"text": params["text"]},
        )
        response = self.orchestrator.dispatch(message)
        return response.data if response.success else {"error": response.error}
    
    def _handle_classify_intent(self, params: dict) -> dict:
        message = Message(
            task_type="classify_intent",
            content={"text": params["text"]},
        )
        response = self.orchestrator.dispatch(message)
        return response.data if response.success else {"error": response.error}
    
    def _handle_match(self, params: dict) -> dict:
        message = Message(
            task_type="match",
            content={
                "direction": params.get("direction", "人找供给"),
                "query": params.get("query", {}),
            },
        )
        response = self.orchestrator.dispatch(message)
        return response.data if response.success else {"error": response.error}
    
    def _handle_semantic_search(self, params: dict) -> dict:
        message = Message(
            task_type="semantic_search",
            content={
                "query": params["query"],
                "top_k": params.get("top_k", 10),
                "entity_type": params.get("entity_type"),
            },
        )
        response = self.orchestrator.dispatch(message)
        return response.data if response.success else {"error": response.error}
    
    def _handle_arxiv_search(self, params: dict) -> dict:
        message = Message(
            task_type="search_arxiv",
            content={
                "query": params["query"],
                "category": params.get("category"),
                "max_results": params.get("max_results", 10),
            },
        )
        response = self.orchestrator.dispatch(message)
        return response.data if response.success else {"error": response.error}
    
    # Mini-program handlers
    def _handle_miniprogram_search(self, params: dict) -> dict:
        platform = params.get("platform", "wechat")
        adapter = self.adapter_registry.get_adapter(platform)
        if adapter is None:
            return {"error": f"Unknown platform: {platform}"}
        
        mp_request = MiniProgramRequest(
            platform=platform,
            action="search",
            parameters={"keyword": params.get("keyword", "")},
        )
        
        response = adapter.process_request(mp_request)
        return response.data if response.success else {"error": response.error}
    
    def _handle_miniprogram_match(self, params: dict) -> dict:
        platform = params.get("platform", "wechat")
        adapter = self.adapter_registry.get_adapter(platform)
        if adapter is None:
            return {"error": f"Unknown platform: {platform}"}
        
        mp_request = MiniProgramRequest(
            platform=platform,
            action="match",
            parameters={
                "direction": params.get("direction", "人找供给"),
                "query": params.get("query", {}),
            },
        )
        
        response = adapter.process_request(mp_request)
        return response.data if response.success else {"error": response.error}


# Global gateway instance
_gateway: APIGateway | None = None


def get_gateway() -> APIGateway:
    """Get the global API gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway
