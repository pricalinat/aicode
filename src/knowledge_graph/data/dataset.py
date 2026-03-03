"""Data layer: Dataset loading and preprocessing."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class KnowledgeGraphDataset:
    """Dataset for knowledge graph construction.

    Loads and preprocesses goldset data for both user intent graph
    and supply capability graph construction.
    """

    data_dir: str
    ecom_records: List[Dict[str, Any]] = field(default_factory=list)
    miniapp_records: List[Dict[str, Any]] = field(default_factory=list)
    challenge_records: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Load data after initialization."""
        self._load_data()

    def _load_data(self):
        """Load all data files from the data directory."""
        data_path = Path(self.data_dir)

        # Load e-commerce data
        ecom_file = data_path / "gold_ecom.jsonl"
        if ecom_file.exists():
            with open(ecom_file, "r", encoding="utf-8") as f:
                self.ecom_records = [json.loads(line) for line in f]

        # Load miniapp data
        miniapp_file = data_path / "gold_miniapp.jsonl"
        if miniapp_file.exists():
            with open(miniapp_file, "r", encoding="utf-8") as f:
                self.miniapp_records = [json.loads(line) for line in f]

        # Load challenge data
        challenge_types = ["confusion", "long_tail", "robustness", "adversarial"]
        for challenge_type in challenge_types:
            challenge_file = data_path / f"challenge_{challenge_type}.jsonl"
            if challenge_file.exists():
                with open(challenge_file, "r", encoding="utf-8") as f:
                    self.challenge_records.extend([json.loads(line) for line in f])

    @property
    def all_records(self) -> List[Dict[str, Any]]:
        """Get all records (ecom + miniapp)."""
        return self.ecom_records + self.miniapp_records

    def get_ecom_dataframe(self) -> pd.DataFrame:
        """Get e-commerce data as DataFrame."""
        return pd.DataFrame(self.ecom_records)

    def get_miniapp_dataframe(self) -> pd.DataFrame:
        """Get miniapp data as DataFrame."""
        return pd.DataFrame(self.miniapp_records)

    def extract_unique_entities(self) -> Dict[str, set]:
        """Extract unique entities from all records."""
        entities = {
            "categories_lv1": set(),
            "categories_lv2": set(),
            "brands": set(),
            "cities": set(),
            "intents": set(),
            "attributes": set(),
            "channels": set(),
            "service_categories": set(),
            "service_names": set(),
        }

        # Extract from e-commerce
        for record in self.ecom_records:
            product = record.get("product", {})
            label = record.get("label", {})

            entities["categories_lv1"].add(product.get("category_lv1", ""))
            entities["categories_lv2"].add(product.get("category_lv2", ""))
            entities["brands"].add(product.get("brand", ""))
            entities["intents"].add(label.get("intent", ""))

            # Attributes
            attrs = product.get("attributes", {})
            for attr_type, value in attrs.items():
                entities["attributes"].add(f"{attr_type}_{value}")

            # Must have / exclude
            for must_have in label.get("must_have", []):
                entities["attributes"].add(must_have)

        # Extract from miniapp
        for record in self.miniapp_records:
            service = record.get("service", {})
            label = record.get("label", {})

            entities["service_categories"].add(service.get("category", ""))
            entities["service_names"].add(service.get("name", ""))
            entities["cities"].add(service.get("city", ""))
            entities["channels"].add(service.get("channel", ""))
            entities["intents"].add(label.get("intent", ""))

        # Clean up
        for key in entities:
            entities[key] = {e for e in entities[key] if e}

        return entities

    def get_intent_distribution(self) -> Dict[str, int]:
        """Get distribution of intents."""
        intents = {}
        for record in self.all_records:
            label = record.get("label", {})
            intent = label.get("intent", "unknown")
            intents[intent] = intents.get(intent, 0) + 1
        return intents

    def get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of categories."""
        categories = {}
        for record in self.ecom_records:
            product = record.get("product", {})
            cat = product.get("category_lv2", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return categories

    def get_service_distribution(self) -> Dict[str, int]:
        """Get distribution of services."""
        services = {}
        for record in self.miniapp_records:
            service = record.get("service", {})
            name = service.get("name", "unknown")
            services[name] = services.get(name, 0) + 1
        return services

    def create_user_supply_pairs(
        self, include_ecom: bool = True, include_miniapp: bool = True
    ) -> List[Dict[str, Any]]:
        """Create user-supply interaction pairs for training."""
        pairs = []

        if include_ecom:
            for record in self.ecom_records:
                pairs.append({
                    "user_id": record["id"],
                    "supply_id": record["id"],
                    "supply_type": "product",
                    "query": record["query"],
                    "intent": record["label"]["intent"],
                    "target_category": record["label"]["target_category"],
                    "price_range": record["label"]["price_range"],
                    "properties": record,
                })

        if include_miniapp:
            for record in self.miniapp_records:
                pairs.append({
                    "user_id": record["id"],
                    "supply_id": record["id"],
                    "supply_type": "service",
                    "query": record["query"],
                    "intent": record["label"]["intent"],
                    "category": record["service"]["category"],
                    "city": record["service"]["city"],
                    "properties": record,
                })

        return pairs


@dataclass
class DataPreprocessor:
    """Preprocessor for knowledge graph data."""

    dataset: KnowledgeGraphDataset

    def normalize_intent(self, intent: str) -> str:
        """Normalize intent names."""
        intent_mapping = {
            "商品检索": "search",
            "价格约束": "price_constraint",
            "搭配推荐": "recommendation",
            "属性筛选": "attribute_filter",
            "对比决策": "comparison",
            "服务查询": "service_query",
            "状态追踪": "status_tracking",
            "服务办理": "service_application",
            "预约": "appointment",
            "投诉反馈": "complaint",
        }
        return intent_mapping.get(intent, intent.lower())

    def normalize_category(self, category: str) -> str:
        """Normalize category names."""
        return category.strip().lower()

    def create_train_test_split(
        self, test_ratio: float = 0.2, random_seed: int = 42
    ) -> Tuple[List[Dict], List[Dict]]:
        """Create train/test split for evaluation."""
        import random

        random.seed(random_seed)
        pairs = self.dataset.create_user_supply_pairs()
        random.shuffle(pairs)

        split_idx = int(len(pairs) * (1 - test_ratio))
        return pairs[:split_idx], pairs[split_idx:]
