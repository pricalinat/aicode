"""Intent classification agent for understanding user queries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message


class IntentType(Enum):
    """Types of user intents."""
    # 人找供给 (People finding supply)
    SEARCH_PRODUCT = "search_product"  # Looking for products
    SEARCH_SERVICE = "search_service"  # Looking for services
    SEARCH_MERCHANT = "search_merchant"  # Looking for merchants
    BROWSE_CATEGORY = "browse_category"  # Browsing categories
    
    # 供给找人 (Supply finding people)
    PROMOTE_PRODUCT = "promote_product"  # Supplier promoting products
    PROMOTE_SERVICE = "promote_service"  # Supplier promoting services
    FIND_CUSTOMERS = "find_customers"  # Looking for potential customers
    
    # General
    COMPARE = "compare"  # Compare products/services
    RECOMMEND = "recommend"  # Get recommendations
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Classified user intent."""
    intent_type: IntentType
    confidence: float
    properties: dict


class IntentClassificationAgent(BaseAgent):
    """Agent for classifying user intent.
    
    Distinguishes between:
    - 人找供给 (searching for products/services)
    - 供给找人 (promoting/finding customers)
    """
    
    name = "intent-classification-agent"
    capabilities = {"classify_intent", "intent_classification"}
    
    # Keywords for intent detection
    SEARCH_KEYWORDS = {
        IntentType.SEARCH_PRODUCT: ["buy", "purchase", "find", "search", "找", "购买", "查找", "搜索"],
        IntentType.SEARCH_SERVICE: ["service", " услуга", "服务", "repair", "cleaning"],
        IntentType.SEARCH_MERCHANT: ["store", "shop", "merchant", "商家", "店铺", "vendor"],
        IntentType.BROWSE_CATEGORY: ["category", "categories", "分类", "种类"],
    }
    
    SUPPLY_KEYWORDS = {
        IntentType.PROMOTE_PRODUCT: ["sell", "promote", "listing", "上架", "出售", "推广"],
        IntentType.PROMOTE_SERVICE: ["offer", "provide", "提供", "服务"],
        IntentType.FIND_CUSTOMERS: ["customer", "lead", "客户", "顾客", "潜在客户"],
    }
    
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
            
            intent = self._classify_intent(text)
            
            return AgentResponse(
                agent=self.name,
                success=True,
                data={
                    "intent": intent.intent_type.value,
                    "confidence": intent.confidence,
                    "properties": intent.properties,
                    "direction": self._get_direction(intent.intent_type),
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
    
    def _classify_intent(self, text: str) -> Intent:
        """Classify the user intent from text."""
        text_lower = text.lower()
        
        # Check supply keywords first (供给找人)
        for intent_type, keywords in self.SUPPLY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                confidence = min(0.5 + (matches * 0.15), 0.95)
                return Intent(
                    intent_type=intent_type,
                    confidence=confidence,
                    properties={"matched_keywords": [kw for kw in keywords if kw in text_lower]},
                )
        
        # Check search keywords (人找供给)
        for intent_type, keywords in self.SEARCH_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                confidence = min(0.5 + (matches * 0.15), 0.95)
                return Intent(
                    intent_type=intent_type,
                    confidence=confidence,
                    properties={"matched_keywords": [kw for kw in keywords if kw in text_lower]},
                )
        
        # Check for comparison requests
        if any(kw in text_lower for kw in ["compare", "vs", "versus", "对比", "比较"]):
            return Intent(
                intent_type=IntentType.COMPARE,
                confidence=0.7,
                properties={},
            )
        
        # Check for recommendation requests
        if any(kw in text_lower for kw in ["recommend", "suggest", "推荐", "建议"]):
            return Intent(
                intent_type=IntentType.RECOMMEND,
                confidence=0.7,
                properties={},
            )
        
        # Default - assume search
        return Intent(
            intent_type=IntentType.SEARCH_PRODUCT,
            confidence=0.5,
            properties={"fallback": True},
        )
    
    def _get_direction(self, intent_type: IntentType) -> str:
        """Get the direction of the intent.
        
        Returns:
            "人找供给" (people finding supply) or "供给找人" (supply finding people)
        """
        if intent_type in {
            IntentType.PROMOTE_PRODUCT,
            IntentType.PROMOTE_SERVICE,
            IntentType.FIND_CUSTOMERS,
        }:
            return "供给找人"
        
        return "人找供给"
