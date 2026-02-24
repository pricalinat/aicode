"""Matching agent for supply-demand matching in e-commerce."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge import Entity, EntityType, get_graph


@dataclass
class MatchResult:
    """Result of a matching operation."""
    score: float
    entity: Entity
    reason: str


@dataclass
class MatchingResponse:
    """Response from matching operation."""
    direction: str  # "人找供给" or "供给找人"
    query: dict[str, Any]
    results: list[MatchResult]
    total: int


class MatchingAgent(BaseAgent):
    """Agent for matching suppliers with customers.
    
    Supports:
    - 人找供给: Finding products/services based on user needs
    - 供给找人: Finding potential customers for suppliers
    """
    
    name = "matching-agent"
    capabilities = {"match", "matching", "find_suppliers", "find_customers"}
    
    def handle(self, message: Message) -> AgentResponse:
        try:
            direction = message.content.get("direction", "人找供给")
            query = message.content.get("query", {})
            
            if direction == "人找供给":
                return self._find_suppliers(message, query)
            else:
                return self._find_customers(message, query)
                
        except Exception as exc:
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )
    
    def _find_suppliers(self, message: Message, query: dict[str, Any]) -> AgentResponse:
        """Find suppliers (products/services) for customers."""
        graph = get_graph()
        
        # Build search parameters
        entity_type = EntityType.PRODUCT
        if query.get("type") == "service":
            entity_type = EntityType.SERVICE
        
        text = query.get("text", "")
        category = query.get("category")
        location = query.get("location")
        brand = query.get("brand")
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = brand
        
        # Search products/services
        entities = graph.search(
            entity_type=entity_type,
            text=text,
            filters=filters if filters else None,
            limit=query.get("limit", 20),
        )
        
        # If location specified, filter by location
        if location:
            entities = self._filter_by_location(entities, location, graph)
        
        # Build results with scoring
        results = []
        for entity in entities:
            score = self._calculate_relevance_score(entity, query)
            results.append(MatchResult(
                score=score,
                entity=entity,
                reason=self._get_match_reason(entity, query),
            ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "direction": "人找供给",
                "query": query,
                "results": [
                    {
                        "score": r.score,
                        "entity": {
                            "id": r.entity.id,
                            "type": r.entity.type.value,
                            "name": r.entity.name,
                            "properties": r.entity.properties,
                        },
                        "reason": r.reason,
                    }
                    for r in results[:query.get("limit", 20)]
                ],
                "total": len(results),
            },
            trace_id=message.trace_id,
        )
    
    def _find_customers(self, message: Message, query: dict[str, Any]) -> AgentResponse:
        """Find potential customers for suppliers."""
        graph = get_graph()
        
        # Get supplier's offerings
        supplier_id = query.get("supplier_id")
        product_id = query.get("product_id")
        service_id = query.get("service_id")
        
        # Find users or build user profiles
        target_type = EntityType.USER
        
        # Search for users interested in similar products/services
        entities = graph.search(
            entity_type=target_type,
            text=query.get("text"),
            limit=query.get("limit", 20),
        )
        
        # Also consider category-based matching
        if product_id or service_id:
            product = graph.get_entity(product_id) if product_id else None
            service = graph.get_entity(service_id) if service_id else None
            
            target = product or service
            if target:
                # Find users in same category
                related = graph.get_neighbors(target.id, relation_type=None)
                for e in related:
                    if e.type == EntityType.CATEGORY:
                        category_users = graph.search(
                            entity_type=EntityType.USER,
                            filters={"interested_categories": e.name},
                        )
                        entities.extend(category_users)
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for e in entities:
            if e.id not in seen:
                seen.add(e.id)
                unique_entities.append(e)
        
        # Build results
        results = []
        for entity in unique_entities:
            score = self._calculate_customer_score(entity, query)
            results.append(MatchResult(
                score=score,
                entity=entity,
                reason=self._get_customer_match_reason(entity, query),
            ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "direction": "供给找人",
                "query": query,
                "results": [
                    {
                        "score": r.score,
                        "entity": {
                            "id": r.entity.id,
                            "type": r.entity.type.value,
                            "name": r.entity.name,
                            "properties": r.entity.properties,
                        },
                        "reason": r.reason,
                    }
                    for r in results[:query.get("limit", 20)]
                ],
                "total": len(results),
            },
            trace_id=message.trace_id,
        )
    
    def _filter_by_location(self, entities: list[Entity], location: str, graph) -> list[Entity]:
        """Filter entities by location."""
        # Find merchants at the location
        location_merchants = graph.search(
            entity_type=EntityType.MERCHANT,
            text=location,
        )
        
        merchant_ids = {m.id for m in location_merchants}
        
        # Filter products/services by merchant location
        filtered = []
        for entity in entities:
            # Get the merchant for this product/service
            merchants = graph.get_neighbors(entity.id, relation_type=RelationType.OFFERS)
            for m in merchants:
                if m.id in merchant_ids:
                    filtered.append(entity)
                    break
        
        return filtered if filtered else entities
    
    def _calculate_relevance_score(self, entity: Entity, query: dict[str, Any]) -> float:
        """Calculate relevance score for an entity."""
        score = 0.5  # Base score
        
        # Text match
        text = query.get("text", "").lower()
        if text:
            if text in entity.name.lower():
                score += 0.3
            if entity.description and text in entity.description.lower():
                score += 0.1
        
        # Price match (if specified)
        price_min = query.get("price_min")
        price_max = query.get("price_max")
        if price_min or price_max:
            entity_price = entity.properties.get("price")
            if entity_price:
                if price_min and entity_price >= price_min:
                    score += 0.1
                if price_max and entity_price <= price_max:
                    score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_customer_score(self, entity: Entity, query: dict[str, Any]) -> float:
        """Calculate match score for potential customers."""
        score = 0.3  # Base score
        
        # Category interest match
        interests = entity.properties.get("interests", [])
        product_id = query.get("product_id")
        
        if product_id:
            product = get_graph().get_entity(product_id)
            if product:
                product_category = product.properties.get("category")
                if product_category in interests:
                    score += 0.4
        
        # Location proximity
        user_location = entity.properties.get("location")
        supplier_location = query.get("supplier_location")
        if user_location and supplier_location:
            if user_location == supplier_location:
                score += 0.3
        
        return min(score, 1.0)
    
    def _get_match_reason(self, entity: Entity, query: dict[str, Any]) -> str:
        """Get reason for the match."""
        reasons = []
        
        if query.get("text"):
            if query["text"].lower() in entity.name.lower():
                reasons.append("匹配您搜索的关键词")
        
        if query.get("category"):
            if entity.properties.get("category") == query["category"]:
                reasons.append("符合您选择的分类")
        
        if query.get("location"):
            reasons.append("在您指定的位置有售")
        
        return "; ".join(reasons) if reasons else "推荐给您"
    
    def _get_customer_match_reason(self, entity: Entity, query: dict[str, Any]) -> str:
        """Get reason for customer match."""
        reasons = []
        
        interests = entity.properties.get("interests", [])
        if interests:
            reasons.append(f"对{', '.join(interests)}感兴趣")
        
        location = entity.properties.get("location")
        if location:
            reasons.append(f"位于{location}")
        
        return "; ".join(reasons) if reasons else "可能是潜在客户"


# Import RelationType
from ..knowledge import RelationType
