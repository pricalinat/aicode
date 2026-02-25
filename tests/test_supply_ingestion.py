"""Unit tests for SupplyGraphIngestionPipeline."""

import unittest

from multi_agent_system.knowledge.supply_ingestion import (
    EntityNormalizer,
    EntityDeduplicator,
    SupplyGraphIngestionPipeline,
    BatchConfig,
    IngestionResult,
)
from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelationType,
)


class TestEntityNormalizer(unittest.TestCase):
    """Test cases for EntityNormalizer."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        normalizer = EntityNormalizer()
        result = normalizer.normalize("  Hello   World  ")
        self.assertEqual(result, "Hello World")

    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        normalizer = EntityNormalizer()
        # NFC vs NFD forms
        result = normalizer.normalize("café")
        self.assertEqual(result, "café")

    def test_normalize_lowercase(self):
        """Test lowercase normalization."""
        normalizer = EntityNormalizer(lowercase=True)
        result = normalizer.normalize("HELLO World")
        self.assertEqual(result, "hello world")

    def test_normalize_remove_punctuation(self):
        """Test punctuation removal."""
        normalizer = EntityNormalizer(remove_punctuation=True)
        result = normalizer.normalize("Hello, World! #123")
        self.assertEqual(result, "Hello World 123")

    def test_get_normalized_key(self):
        """Test normalized key generation."""
        normalizer = EntityNormalizer()
        entity = SupplyEntity(
            id="prod_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product", "brand": "BrandA"},
        )

        key = normalizer.get_normalized_key(entity)
        # Default normalizer does not lowercase
        self.assertEqual(key, "product|Test Product")

        key_with_fields = normalizer.get_normalized_key(entity, ["brand"])
        self.assertEqual(key_with_fields, "product|Test Product|BrandA")

    def test_get_normalized_key_lowercase(self):
        """Test normalized key with lowercase option."""
        normalizer = EntityNormalizer(lowercase=True)
        entity = SupplyEntity(
            id="prod_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product", "brand": "BrandA"},
        )

        key = normalizer.get_normalized_key(entity)
        self.assertEqual(key, "product|test product")


class TestEntityDeduplicator(unittest.TestCase):
    """Test cases for EntityDeduplicator."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.normalizer = EntityNormalizer()
        self.deduplicator = EntityDeduplicator(self.normalizer)

        # Add some existing entities
        self.db.create_entity(SupplyEntity(
            id="existing_product",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        ))

    def test_find_duplicates_existing(self):
        """Test finding duplicates against existing entities."""
        entities = [
            SupplyEntity(
                id="new_product_1",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Test Product"},
            ),
            SupplyEntity(
                id="new_product_2",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Different Product"},
            ),
        ]

        duplicates = self.deduplicator.find_duplicates(entities, self.db)
        # Default normalizer doesn't lowercase
        self.assertIn("product|Test Product", duplicates)
        self.assertIn("new_product_1", duplicates["product|Test Product"])

    def test_find_duplicates_batch(self):
        """Test finding duplicates within a batch."""
        entities = [
            SupplyEntity(
                id="product_1",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Test Product"},
            ),
            SupplyEntity(
                id="product_2",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Test Product"},
            ),
        ]

        duplicates = self.deduplicator.find_duplicates(entities, self.db)
        # Default normalizer doesn't lowercase
        self.assertIn("product|Test Product", duplicates)
        # Both products are duplicates of each other
        self.assertEqual(len(duplicates["product|Test Product"]), 2)

    def test_merge_entities_primary_wins(self):
        """Test merging entities with primary_wins strategy."""
        primary = SupplyEntity(
            id="prod_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product", "price": 100},
        )
        secondary = SupplyEntity(
            id="prod_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product", "description": "Desc"},
        )

        merged = self.deduplicator.merge_entities(primary, secondary, "primary_wins")

        self.assertEqual(merged.id, "prod_1")
        self.assertEqual(merged.properties["price"], 100)
        self.assertEqual(merged.properties["description"], "Desc")


class TestSupplyGraphIngestionPipeline(unittest.TestCase):
    """Test cases for SupplyGraphIngestionPipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.pipeline = SupplyGraphIngestionPipeline(self.db)

    def test_ingest_product_basic(self):
        """Test basic product ingestion."""
        product_data = {
            "id": "product_1",
            "name": "Test Product",
            "price": 99.99,
        }

        result = self.pipeline.ingest_product(product_data)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(self.db.count(SupplyEntityType.PRODUCT), 1)

        entity = self.db.get_entity("product_1")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.properties["price"], 99.99)

    def test_ingest_product_skip_duplicate(self):
        """Test skipping duplicate products."""
        product_data = {
            "id": "product_1",
            "name": "Test Product",
        }

        # First ingestion
        result1 = self.pipeline.ingest_product(product_data)
        self.assertEqual(result1.created, 1)

        # Second ingestion with skip_duplicates
        result2 = self.pipeline.ingest_product(product_data, BatchConfig(skip_duplicates=True))
        self.assertEqual(result2.skipped, 1)

    def test_ingest_product_with_relations(self):
        """Test product ingestion with relations."""
        # First create category and brand
        self.db.create_entity(SupplyEntity(
            id="cat_electronics",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        ))
        self.db.create_entity(SupplyEntity(
            id="brand_apple",
            type=SupplyEntityType.BRAND,
            properties={"name": "Apple"},
        ))

        product_data = {
            "id": "product_1",
            "name": "iPhone",
            "category": "cat_electronics",
            "brand": "brand_apple",
        }

        result = self.pipeline.ingest_product(product_data, BatchConfig(create_relations=True))

        self.assertEqual(result.created, 1)
        # Check relations were created
        neighbors = self.db.get_neighbors("product_1")
        neighbor_ids = [n.id for n in neighbors]
        self.assertIn("cat_electronics", neighbor_ids)
        self.assertIn("brand_apple", neighbor_ids)

    def test_ingest_service(self):
        """Test service ingestion."""
        service_data = {
            "id": "service_1",
            "name": "Phone Repair",
            "description": "Professional phone repair",
        }

        result = self.pipeline.ingest_service(service_data)

        self.assertEqual(result.created, 1)
        entity = self.db.get_entity("service_1")
        self.assertEqual(entity.type, SupplyEntityType.SERVICE)

    def test_ingest_procedure(self):
        """Test procedure ingestion."""
        procedure_data = {
            "id": "procedure_1",
            "name": "Screen Replacement",
            "steps": ["Diagnose", "Replace", "Test"],
        }

        result = self.pipeline.ingest_procedure(procedure_data)

        self.assertEqual(result.created, 1)
        entity = self.db.get_entity("procedure_1")
        self.assertEqual(entity.type, SupplyEntityType.PROCEDURE)

    def test_ingest_intent(self):
        """Test intent ingestion."""
        intent_data = {
            "id": "intent_1",
            "name": "Book Appointment",
            "description": "User wants to book an appointment",
        }

        result = self.pipeline.ingest_intent(intent_data)

        self.assertEqual(result.created, 1)
        entity = self.db.get_entity("intent_1")
        self.assertEqual(entity.type, SupplyEntityType.INTENT)

    def test_ingest_slot(self):
        """Test slot ingestion."""
        slot_data = {
            "id": "slot_date",
            "name": "Appointment Date",
            "slot_type": "date",
            "required": True,
        }

        result = self.pipeline.ingest_slot(slot_data)

        self.assertEqual(result.created, 1)
        entity = self.db.get_entity("slot_date")
        self.assertEqual(entity.type, SupplyEntityType.SLOT)
        self.assertEqual(entity.properties["slot_type"], "date")
        self.assertTrue(entity.properties["required"])

    def test_ingest_batch(self):
        """Test batch ingestion."""
        products = [
            {"id": f"product_{i}", "name": f"Product {i}", "price": i * 10}
            for i in range(5)
        ]

        result = self.pipeline.ingest_batch(products, "product")

        self.assertEqual(result.created, 5)
        self.assertEqual(self.db.count(SupplyEntityType.PRODUCT), 5)

    def test_ingest_full_schema(self):
        """Test full schema ingestion."""
        data = {
            "categories": [
                {"id": "cat_1", "name": "Electronics"},
                {"id": "cat_2", "name": "Services"},
            ],
            "brands": [
                {"id": "brand_1", "name": "Apple"},
            ],
            "products": [
                {"id": "product_1", "name": "iPhone", "category": "cat_1", "brand": "brand_1"},
            ],
            "services": [
                {"id": "service_1", "name": "Repair", "category": "cat_2"},
            ],
            "procedures": [
                {"id": "procedure_1", "name": "Screen Fix"},
            ],
            "intents": [
                {"id": "intent_1", "name": "Get Help"},
            ],
            "slots": [
                {"id": "slot_1", "name": "Issue Type"},
            ],
        }

        result = self.pipeline.ingest_full_schema(data)

        self.assertEqual(result.created, 8)  # 2 cats + 1 brand + 1 product + 1 service + 1 proc + 1 intent + 1 slot
        self.assertEqual(self.db.count(SupplyEntityType.CATEGORY), 2)
        self.assertEqual(self.db.count(SupplyEntityType.BRAND), 1)
        self.assertEqual(self.db.count(SupplyEntityType.PRODUCT), 1)
        self.assertEqual(self.db.count(SupplyEntityType.SERVICE), 1)

    def test_ingest_dry_run(self):
        """Test dry run mode."""
        products = [
            {"id": "product_1", "name": "Product 1"},
            {"id": "product_2", "name": "Product 2"},
        ]

        # First add one product
        self.pipeline.ingest_product(products[0])

        # Dry run should show what would be created/updated
        result = self.pipeline.ingest_batch(products, "product", BatchConfig(dry_run=True))

        self.assertEqual(result.created, 1)  # product_2 would be created
        self.assertEqual(result.skipped, 1)  # product_1 already exists

    def test_ingest_normalize_names(self):
        """Test name normalization during ingestion."""
        product_data = {
            "id": "product_1",
            "name": "  TEST   PRODUCT  ",
            "price": 100,
        }

        result = self.pipeline.ingest_product(product_data, BatchConfig(normalize_names=True))

        entity = self.db.get_entity("product_1")
        # Default normalizer trims whitespace but does not lowercase
        self.assertEqual(entity.properties["name"], "TEST PRODUCT")


if __name__ == "__main__":
    unittest.main()
