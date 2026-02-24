"""User profile agent for personalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge import Entity, EntityType, Relation, RelationType, get_graph


class UserProfileAgent(BaseAgent):
    """Agent for managing user profiles and personalization.
    
    Handles:
    - User profile creation and updates
    - Preference tracking
    - Interaction history
    - User segmentation
    """
    
    name = "user-profile-agent"
    capabilities = {"user_profile", "update_profile", "get_preferences"}
    
    def handle(self, message: Message) -> AgentResponse:
        try:
            action = message.content.get("action", "get")
            
            if action == "create":
                return self._create_profile(message)
            elif action == "update":
                return self._update_profile(message)
            elif action == "get":
                return self._get_profile(message)
            elif action == "add_interest":
                return self._add_interest(message)
            elif action == "record_interaction":
                return self._record_interaction(message)
            else:
                return AgentResponse(
                    agent=self.name,
                    success=False,
                    error=f"Unknown action: {action}",
                    trace_id=message.trace_id,
                )
                
        except Exception as exc:
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )
    
    def _create_profile(self, message: Message) -> AgentResponse:
        user_id = message.content.get("user_id")
        properties = message.content.get("properties", {})
        
        if not user_id:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing user_id",
                trace_id=message.trace_id,
            )
        
        graph = get_graph()
        
        # Create user entity
        user = Entity(
            id=user_id,
            type=EntityType.USER,
            properties={
                "name": properties.get("name", ""),
                "interests": properties.get("interests", []),
                "location": properties.get("location", ""),
                "preferences": properties.get("preferences", {}),
            },
        )
        
        try:
            graph.create_entity(user)
        except ValueError:
            # Already exists
            pass
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "user_id": user_id,
                "created": True,
            },
            trace_id=message.trace_id,
        )
    
    def _update_profile(self, message: Message) -> AgentResponse:
        user_id = message.content.get("user_id")
        properties = message.content.get("properties", {})
        
        if not user_id:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing user_id",
                trace_id=message.trace_id,
            )
        
        graph = get_graph()
        user = graph.get_entity(user_id)
        
        if not user:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="User not found",
                trace_id=message.trace_id,
            )
        
        # Update properties
        for key, value in properties.items():
            user.properties[key] = value
        
        graph.update_entity(user)
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "user_id": user_id,
                "updated": True,
            },
            trace_id=message.trace_id,
        )
    
    def _get_profile(self, message: Message) -> AgentResponse:
        user_id = message.content.get("user_id")
        
        if not user_id:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing user_id",
                trace_id=message.trace_id,
            )
        
        graph = get_graph()
        user = graph.get_entity(user_id)
        
        if not user:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="User not found",
                trace_id=message.trace_id,
            )
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "user_id": user.id,
                "name": user.properties.get("name"),
                "interests": user.properties.get("interests", []),
                "location": user.properties.get("location"),
                "preferences": user.properties.get("preferences", {}),
            },
            trace_id=message.trace_id,
        )
    
    def _add_interest(self, message: Message) -> AgentResponse:
        user_id = message.content.get("user_id")
        interest = message.content.get("interest")
        
        if not user_id or not interest:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing user_id or interest",
                trace_id=message.trace_id,
            )
        
        graph = get_graph()
        user = graph.get_entity(user_id)
        
        if not user:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="User not found",
                trace_id=message.trace_id,
            )
        
        # Add interest
        interests = user.properties.get("interests", [])
        if interest not in interests:
            interests.append(interest)
            user.properties["interests"] = interests
            graph.update_entity(user)
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "user_id": user_id,
                "interests": interests,
            },
            trace_id=message.trace_id,
        )
    
    def _record_interaction(self, message: Message) -> AgentResponse:
        user_id = message.content.get("user_id")
        target_id = message.content.get("target_id")
        interaction_type = message.content.get("type", "view")
        
        if not user_id or not target_id:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing user_id or target_id",
                trace_id=message.trace_id,
            )
        
        graph = get_graph()
        
        # Create interaction relation
        relation = Relation(
            source_id=user_id,
            target_id=target_id,
            relation_type=RelationType.RELATED_TO,
            properties={
                "type": interaction_type,
            },
        )
        
        graph.create_relation(relation)
        
        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "user_id": user_id,
                "target_id": target_id,
                "type": interaction_type,
                "recorded": True,
            },
            trace_id=message.trace_id,
        )
