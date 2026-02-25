"""Tests for Mini-Program Structured Input Adapter."""

import unittest

from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelationType,
)
from multi_agent_system.knowledge.supply_mini_program_adapter import (
    MiniProgramFormAdapter,
    MiniProgramIntentAdapter,
    MiniProgramDataAdapter,
    MiniProgramFormData,
    MiniProgramIntent,
    ConversionResult,
)


class TestMiniProgramFormAdapter(unittest.TestCase):
    """Test cases for MiniProgramFormAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.adapter = MiniProgramFormAdapter(self.db)

    def test_parse_form_data(self):
        """Test parsing form data."""
        form_data = {
            "page_name": "product_form",
            "fields": {
                "name": "iPhone 15",
                "price": 999.99,
                "category": "electronics",
            },
            "user_id": "user_123",
            "session_id": "session_456",
        }

        result = self.adapter.parse_form_data(form_data)

        self.assertEqual(result.page_name, "product_form")
        self.assertEqual(result.fields["name"], "iPhone 15")
        self.assertEqual(result.fields["price"], 999.99)
        self.assertEqual(result.user_id, "user_123")
        self.assertEqual(result.session_id, "session_456")

    def test_parse_form_data_minimal(self):
        """Test parsing minimal form data."""
        form_data = {"name": "Test Product"}

        result = self.adapter.parse_form_data(form_data)

        self.assertEqual(result.page_name, "unknown")
        self.assertEqual(result.fields["name"], "Test Product")

    def test_convert_to_entity_product(self):
        """Test converting form data to product entity."""
        form_data = MiniProgramFormData(
            page_name="product_form",
            fields={
                "id": "prod_001",
                "name": "iPhone 15",
                "price": 999.99,
                "category": "electronics",
            },
        )

        entity = self.adapter.convert_to_entity(form_data, "product")

        self.assertIsNotNone(entity)
        self.assertEqual(entity.id, "prod_001")
        self.assertEqual(entity.type, SupplyEntityType.PRODUCT)
        self.assertEqual(entity.properties["name"], "iPhone 15")
        self.assertEqual(entity.properties["price"], 999.99)

    def test_convert_to_entity_service(self):
        """Test converting form data to service entity."""
        form_data = MiniProgramFormData(
            page_name="service_form",
            fields={
                "name": "Repair Service",
                "description": "Phone repair service",
            },
        )

        entity = self.adapter.convert_to_entity(form_data, "service")

        self.assertIsNotNone(entity)
        self.assertEqual(entity.type, SupplyEntityType.SERVICE)
        self.assertEqual(entity.properties["name"], "Repair Service")

    def test_convert_to_entity_unknown_type(self):
        """Test converting with unknown entity type returns None."""
        form_data = MiniProgramFormData(
            page_name="unknown_form",
            fields={"name": "Test"},
        )

        entity = self.adapter.convert_to_entity(form_data, "unknown_type")

        self.assertIsNone(entity)

    def test_convert_form_to_entities(self):
        """Test converting form to entities in KG."""
        form_data = {
            "page_name": "product_form",
            "fields": {
                "id": "prod_test",
                "name": "Test Product",
                "price": 99.99,
            },
        }

        result = self.adapter.convert_form_to_entities(form_data, "product")

        self.assertEqual(result.entities_created, 1)
        self.assertEqual(len(result.entity_ids), 1)
        self.assertEqual(result.entity_ids[0], "prod_test")
        self.assertEqual(len(result.errors), 0)

    def test_field_name_normalization(self):
        """Test field name normalization."""
        form_data = MiniProgramFormData(
            page_name="product_form",
            fields={
                "product_name": "Test",
                "prod_desc": "Description",
                "prod_price": 100,
            },
        )

        entity = self.adapter.convert_to_entity(form_data, "product")

        self.assertEqual(entity.properties["name"], "Test")
        self.assertEqual(entity.properties["description"], "Description")
        self.assertEqual(entity.properties["price"], 100)

    def test_metadata_added(self):
        """Test that source metadata is added."""
        form_data = MiniProgramFormData(
            page_name="test_page",
            fields={"name": "Test"},
            user_id="user_123",
        )

        entity = self.adapter.convert_to_entity(form_data, "category")

        self.assertEqual(entity.properties["_source"], "mini_program")
        self.assertEqual(entity.properties["_page"], "test_page")
        self.assertEqual(entity.properties["_user_id"], "user_123")


class TestMiniProgramIntentAdapter(unittest.TestCase):
    """Test cases for MiniProgramIntentAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.adapter = MiniProgramIntentAdapter(self.db)

    def test_extract_intent_search_product(self):
        """Test extracting search product intent."""
        intent = self.adapter.extract_intent("I want to search for a phone")

        self.assertEqual(intent.intent_name, "search_product")
        self.assertGreater(intent.confidence, 0.3)

    def test_extract_intent_add_to_cart(self):
        """Test extracting add to cart intent."""
        # Use query without "cart" to avoid view_cart matching
        intent = self.adapter.extract_intent("I want to add this to my purchase")

        self.assertEqual(intent.intent_name, "add_to_cart")

    def test_extract_intent_view_product(self):
        """Test extracting view product intent."""
        intent = self.adapter.extract_intent("Show me the product details")

        self.assertEqual(intent.intent_name, "view_product")

    def test_extract_intent_unknown(self):
        """Test extracting unknown intent."""
        intent = self.adapter.extract_intent("Hello world")

        self.assertEqual(intent.intent_name, "general_query")
        self.assertEqual(intent.confidence, 0.5)

    def test_extract_intent_with_slots(self):
        """Test extracting intent with slots."""
        slots = {"category": "electronics", "max_price": 1000}
        intent = self.adapter.extract_intent("Find me a laptop", slots)

        self.assertEqual(intent.slots, slots)

    def test_convert_intent_to_entities(self):
        """Test converting intent to KG entities."""
        intent = MiniProgramIntent(
            intent_name="search_product",
            confidence=0.9,
            slots={"category": "electronics"},
        )

        result = self.adapter.convert_intent_to_entities(intent)

        self.assertEqual(result.entities_created, 2)  # Intent + Slot
        self.assertEqual(result.relations_created, 1)  # HAS_SLOT
        self.assertEqual(len(result.entity_ids), 2)
        self.assertEqual(len(result.relation_triplets), 1)

    def test_convert_intent_with_service(self):
        """Test converting intent with service link."""
        # Create a service first
        service_entity = SupplyEntity(
            id="service_1",
            type=SupplyEntityType.SERVICE,
            properties={"name": "Test Service"},
        )
        self.db.create_entity(service_entity)

        intent = MiniProgramIntent(
            intent_name="search_product",
            confidence=0.9,
        )

        result = self.adapter.convert_intent_to_entities(intent, "service_1")

        self.assertEqual(result.entities_created, 1)
        self.assertEqual(result.relations_created, 1)
        # Should have has_intent relation
        self.assertTrue(
            any(r[1] == "has_intent" for r in result.relation_triplets)
        )

    def test_infer_slot_type(self):
        """Test slot type inference."""
        self.assertEqual(self.adapter._infer_slot_type("text"), "string")
        self.assertEqual(self.adapter._infer_slot_type(123), "integer")
        self.assertEqual(self.adapter._infer_slot_type(1.5), "float")
        self.assertEqual(self.adapter._infer_slot_type(True), "boolean")
        self.assertEqual(self.adapter._infer_slot_type([1, 2]), "array")
        self.assertEqual(self.adapter._infer_slot_type(None), "string")


class TestMiniProgramDataAdapter(unittest.TestCase):
    """Test cases for MiniProgramDataAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.adapter = MiniProgramDataAdapter(self.db)

    def test_import_products(self):
        """Test importing products."""
        products = [
            {
                "id": "prod_1",
                "name": "iPhone 15",
                "price": 999.99,
                "category": "cat_electronics",
                "brand": "brand_apple",
            },
            {
                "name": "Samsung Galaxy",
                "price": 899.99,
            },
        ]

        result = self.adapter.import_products(products)

        # Creates 2 products + category + brand (for first product)
        self.assertEqual(result.entities_created, 4)
        # Should have created category and brand too
        self.assertGreater(result.entities_created, 2)

    def test_import_products_with_relations(self):
        """Test importing products with relations."""
        # First create category and brand
        category = SupplyEntity(
            id="cat_electronics",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        )
        brand = SupplyEntity(
            id="brand_apple",
            type=SupplyEntityType.BRAND,
            properties={"name": "Apple"},
        )
        self.db.create_entity(category)
        self.db.create_entity(brand)

        products = [
            {
                "id": "prod_1",
                "name": "iPhone 15",
                "category": "cat_electronics",
                "brand": "brand_apple",
            },
        ]

        result = self.adapter.import_products(products)

        self.assertEqual(result.entities_created, 1)
        self.assertEqual(result.relations_created, 2)  # BELONGS_TO + HAS_BRAND

    def test_import_services(self):
        """Test importing services."""
        services = [
            {
                "id": "service_1",
                "name": "Repair Service",
                "description": "Phone repair",
                "category": "cat_services",
            },
        ]

        result = self.adapter.import_services(services)

        # Creates service + category
        self.assertEqual(result.entities_created, 2)
        self.assertEqual(result.entity_ids[0], "service_1")

    def test_import_user_queries(self):
        """Test importing user queries."""
        queries = [
            {
                "query": "Find me an iPhone",
                "slots": {"category": "phone"},
            },
            {
                "query": "Show product details",
            },
        ]

        result = self.adapter.import_user_queries(queries)

        self.assertGreater(result.entities_created, 0)
        self.assertGreater(result.relations_created, 0)

    def test_import_user_queries_with_service(self):
        """Test importing queries linked to service."""
        # Create service first
        service = SupplyEntity(
            id="service_1",
            type=SupplyEntityType.SERVICE,
            properties={"name": "E-commerce Service"},
        )
        self.db.create_entity(service)

        queries = [
            {
                "query": "Find me a product",
            },
        ]

        result = self.adapter.import_user_queries(queries, "service_1")

        self.assertGreater(result.entities_created, 0)
        # Should have relation to service
        self.assertTrue(
            any("has_intent" in r[1] for r in result.relation_triplets)
        )


class TestConversionResult(unittest.TestCase):
    """Test cases for ConversionResult."""

    def test_default_values(self):
        """Test default values."""
        result = ConversionResult()

        self.assertEqual(result.entities_created, 0)
        self.assertEqual(result.relations_created, 0)
        self.assertEqual(len(result.entity_ids), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)


if __name__ == "__main__":
    unittest.main()
