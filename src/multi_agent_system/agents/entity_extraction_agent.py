"""Entity extraction agent for knowledge graph population."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge import Entity, EntityType, Relation, RelationType, get_graph


@dataclass
class ExtractedEntity:
    """An entity extracted from user input."""
    text: str
    entity_type: EntityType
    confidence: float
    properties: dict[str, Any]


class EntityExtractionAgent(BaseAgent):
    """Agent for extracting entities from user queries.
    
    Identifies:
    - Products (items being searched for)
    - Services (offerings)
    - Merchants (sellers/providers)
    - Categories (product/service categories)
    - Locations (geo information)
    - Brands
    - Price ranges
    """
    
    name = "entity-extraction-agent"
    capabilities = {"extract_entities", "entity_extraction"}
    
    # Patterns for entity extraction
    CATEGORY_PATTERNS = [
        r"(\w+\s+category|category\s+:?\s*)(\w+)",
        r"(category|categories)\s+(?:of\s+)?(\w+)",
    ]
    
    BRAND_PATTERNS = [
        r"(brand|brand\s+name)\s*:?\s*(\w+)",
        r"(\w+)\s+brand",
    ]
    
    LOCATION_PATTERNS = [
        r"(in|near|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(location)\s*:?\s*(\w+)",
    ]
    
    PRICE_PATTERNS = [
        r"(price| budget | cost | 价位 | 价格)[^\d]*(\d+(?:\.\d+)?)\s*(?:到|-|~)\s*(\d+(?:\.\d+)?)",
        r"(under|below|less than|低于|小于)\s*[^\d]*(\d+(?:\.\d+)?)",
        r"(above|over|more than|高于|大于)\s*[^\d]*(\d+(?:\.\d+)?)",
    ]
    
    def handle(self, message: Message) -> AgentResponse:
        try:
            text = message.content.get("text", "")
            if not text:
                return AgentResponse(
                    agent=self.name,
                    success=False,
                    error="Missing 'text' in content",
                    trace_id=message.trace_id,
                )
            
            entities = self._extract_entities(text)
            
            return AgentResponse(
                agent=self.name,
                success=True,
                data={
                    "entities": [
                        {
                            "text": e.text,
                            "type": e.entity_type.value,
                            "confidence": e.confidence,
                            "properties": e.properties,
                        }
                        for e in entities
                    ],
                    "count": len(entities),
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
    
    def _extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract entities from text."""
        entities = []
        
        # Extract categories
        entities.extend(self._extract_categories(text))
        
        # Extract brands
        entities.extend(self._extract_brands(text))
        
        # Extract locations
        entities.extend(self._extract_locations(text))
        
        # Extract price ranges
        entities.extend(self._extract_prices(text))
        
        # Extract products/services (default)
        entities.extend(self._extract_products_services(text))
        
        return entities
    
    def _extract_categories(self, text: str) -> list[ExtractedEntity]:
        entities = []
        for pattern in self.CATEGORY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                category = match.group(2) if len(match.groups()) > 1 else match.group(1)
                entities.append(ExtractedEntity(
                    text=category.strip(),
                    entity_type=EntityType.CATEGORY,
                    confidence=0.8,
                    properties={"source": "pattern"},
                ))
        return entities
    
    def _extract_brands(self, text: str) -> list[ExtractedEntity]:
        entities = []
        for pattern in self.BRAND_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                brand = match.group(2) if len(match.groups()) > 1 else match.group(1)
                entities.append(ExtractedEntity(
                    text=brand.strip(),
                    entity_type=EntityType.BRAND,
                    confidence=0.7,
                    properties={"source": "pattern"},
                ))
        return entities
    
    def _extract_locations(self, text: str) -> list[ExtractedEntity]:
        entities = []
        for pattern in self.LOCATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                location = match.group(2) if len(match.groups()) > 1 else match.group(1)
                entities.append(ExtractedEntity(
                    text=location.strip(),
                    entity_type=EntityType.LOCATION,
                    confidence=0.7,
                    properties={"source": "pattern"},
                ))
        return entities
    
    def _extract_prices(self, text: str) -> list[ExtractedEntity]:
        entities = []
        for pattern in self.PRICE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 3 and groups[1] and groups[2]:
                    # Range price
                    entities.append(ExtractedEntity(
                        text=f"{groups[1]}-{groups[2]}",
                        entity_type=EntityType.TAG,
                        confidence=0.9,
                        properties={
                            "source": "pattern",
                            "price_min": float(groups[1]),
                            "price_max": float(groups[2]),
                            "price_type": "range",
                        },
                    ))
                elif len(groups) >= 2 and groups[1]:
                    # Single price
                    entities.append(ExtractedEntity(
                        text=groups[1],
                        entity_type=EntityType.TAG,
                        confidence=0.8,
                        properties={
                            "source": "pattern",
                            "price_value": float(groups[1]),
                            "price_type": "single",
                        },
                    ))
        return entities
    
    def _extract_products_services(self, text: str) -> list[ExtractedEntity]:
        """Extract products or services from text.
        
        This is a simple heuristic - in production, use NLP models.
        """
        entities = []
        
        # Remove known patterns to get the core query
        cleaned = text
        for pattern in self.CATEGORY_PATTERNS + self.BRAND_PATTERNS + self.LOCATION_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        cleaned = cleaned.strip()
        if cleaned:
            # Determine if it's a product or service based on keywords
            service_keywords = {"service", "services", "repair", "cleaning", "delivery", "consultation"}
            is_service = any(kw in cleaned.lower() for kw in service_keywords)
            
            entity_type = EntityType.SERVICE if is_service else EntityType.PRODUCT
            
            entities.append(ExtractedEntity(
                text=cleaned,
                entity_type=entity_type,
                confidence=0.6,
                properties={"source": "inference"},
            ))
        
        return entities
