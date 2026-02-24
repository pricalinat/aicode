"""Recommendation agent for personalized suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge import Entity, EntityType, RelationType, get_graph


@dataclass
class RecommendationItem:
    """A recommended item with score."""
    entity: Entity
    score: float
    reason: str


class RecommendationAgent(BaseAgent):
    """Agent for generating personalized recommendations.
    
    Supports:
    - Collaborative filtering (based on similar users)
    - Content-based filtering (based on item similarity)
    - Popularity-based recommendations
    - Hybrid recommendations
    """
    
    name = "recommendation-agent"
    capabilities = {"recommend", "recommendations", "personalized_recommend"}
    
    def handle(self, message: Message) -> AgentResponse:
        try:
            user_id = message.content.get("user_id")
            context = message.content.get("context", {})
            limit = message.content.get("limit", 10)
            strategy = message.content.get("strategy", "hybrid")
            
            if not user_id:
                return AgentResponse(
                    agent=self.name,
                    success=False,
                    error="Missing 'user_id' in content",
                    trace_id=message.trace_id,
                )
            
            recommendations = self._generate_recommendations(
                user_id=user_id,
                context=context,
                limit=limit,
                strategy=strategy,
            )
            
            return AgentResponse(
                agent=self.name,
                success=True,
                data={
                    "user_id": user_id,
                    "strategy": strategy,
                    "recommendations": [
                        {
                            "id": r.entity.id,
                            "type": r.entity.type.value,
                            "name": r.entity.name,
                            "properties": r.entity.properties,
                            "score": round(r.score, 4),
                            "reason": r.reason,
                        }
                        for r in recommendations
                    ],
                    "total": len(recommendations),
                },
                trace_id=message.trace_id,
            )
            
        except Exception as exc:
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )
    
    def _generate_recommendations(
        self,
        user_id: str,
        context: dict,
        limit: int,
        strategy: str,
    ) -> list[RecommendationItem]:
        """Generate recommendations based on strategy."""
        if strategy == "collaborative":
            return self._collaborative_recommend(user_id, limit)
        elif strategy == "content":
            return self._content_recommend(user_id, context, limit)
        elif strategy == "popularity":
            return self._popularity_recommend(limit)
        else:  # hybrid
            return self._hybrid_recommend(user_id, context, limit)
    
    def _collaborative_recommend(self, user_id: str, limit: int) -> list[RecommendationItem]:
        """Collaborative filtering recommendations."""
        graph = get_graph()
        
        # Get user
        user = graph.get_entity(user_id)
        if not user:
            return self._popularity_recommend(limit)
        
        # Find similar users
        similar_users = graph.get_neighbors(user_id, relation_type=RelationType.RELATED_TO)
        
        # Get items similar users interacted with
        recommendations = []
        for similar_user in similar_users:
            interactions = graph.get_outgoing_relations(similar_user.id, relation_type=RelationType.RELATED_TO)
            for interaction in interactions:
                target = graph.get_entity(interaction.target_id)
                if target and target.type in (EntityType.PRODUCT, EntityType.SERVICE):
                    if target not in [r.entity for r in recommendations]:
                        recommendations.append(RecommendationItem(
                            entity=target,
                            score=interaction.weight,
                            reason=f"与您相似的用户也喜欢",
                        ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _content_recommend(
        self,
        user_id: str,
        context: dict,
        limit: int,
    ) -> list[RecommendationItem]:
        """Content-based recommendations."""
        graph = get_graph()
        
        # Get user preferences
        user = graph.get_entity(user_id)
        if not user:
            return []
        
        # Get user's interests
        interests = user.properties.get("interests", [])
        
        # Find matching products/services
        recommendations = []
        for interest in interests:
            entities = graph.search(
                entity_type=EntityType.PRODUCT,
                text=interest,
                limit=limit,
            )
            for entity in entities:
                score = 0.8  # Base score for interest match
                recommendations.append(RecommendationItem(
                    entity=entity,
                    score=score,
                    reason=f"符合您对{interest}的兴趣",
                ))
        
        # Also check services
        for interest in interests:
            entities = graph.search(
                entity_type=EntityType.SERVICE,
                text=interest,
                limit=limit,
            )
            for entity in entities:
                score = 0.7
                recommendations.append(RecommendationItem(
                    entity=entity,
                    score=score,
                    reason=f"符合您对{interest}的兴趣",
                ))
        
        # Remove duplicates and sort
        seen = set()
        unique = []
        for r in recommendations:
            if r.entity.id not in seen:
                seen.add(r.entity.id)
                unique.append(r)
        
        unique.sort(key=lambda x: x.score, reverse=True)
        return unique[:limit]
    
    def _popularity_recommend(self, limit: int) -> list[RecommendationItem]:
        """Popularity-based recommendations."""
        graph = get_graph()
        
        # Get popular products
        products = graph.search(entity_type=EntityType.PRODUCT, limit=limit * 2)
        services = graph.search(entity_type=EntityType.SERVICE, limit=limit)
        
        recommendations = []
        
        # Add popularity score based on interaction count
        for product in products:
            interactions = graph.get_incoming_relations(product.id)
            score = min(len(interactions) / 100.0, 1.0)  # Normalize
            recommendations.append(RecommendationItem(
                entity=product,
                score=score,
                reason="热门商品",
            ))
        
        for service in services:
            interactions = graph.get_incoming_relations(service.id)
            score = min(len(interactions) / 100.0, 1.0)
            recommendations.append(RecommendationItem(
                entity=service,
                score=score,
                reason="热门服务",
            ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _hybrid_recommend(
        self,
        user_id: str,
        context: dict,
        limit: int,
    ) -> list[RecommendationItem]:
        """Hybrid recommendations combining multiple strategies."""
        # Get recommendations from all strategies
        collab = self._collaborative_recommend(user_id, limit)
        content = self._content_recommend(user_id, context, limit)
        popularity = self._popularity_recommend(limit)
        
        # Combine with weights
        combined: dict[str, RecommendationItem] = {}
        
        for rec in collab:
            if rec.entity.id not in combined:
                combined[rec.entity.id] = rec
            else:
                combined[rec.entity.id].score += rec.score * 0.3
        
        for rec in content:
            if rec.entity.id not in combined:
                combined[rec.entity.id] = rec
            else:
                combined[rec.entity.id].score += rec.score * 0.4
        
        for rec in popularity:
            if rec.entity.id not in combined:
                combined[rec.entity.id] = rec
            else:
                combined[rec.entity.id].score += rec.score * 0.3
        
        # Sort by combined score
        result = list(combined.values())
        result.sort(key=lambda x: x.score, reverse=True)
        
        return result[:limit]
