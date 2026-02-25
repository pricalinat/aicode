"""Unit tests for SupplyGraphDatabase."""

import unittest

from multi_agent_system.knowledge.supply_graph_database import (
    SupplyGraphDatabase,
    ValidationError,
)
from multi_agent_system.knowledge.supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)


class TestSupplyGraphDatabase(unittest.TestCase):
    """Test cases for SupplyGraphDatabase."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()

    def test_create_entity(self):
        """Test creating an entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product", "price": 99.99},
        )

        result = self.db.create_entity(entity)

        self.assertEqual(result.id, "product_1")
        self.assertEqual(result.type, SupplyEntityType.PRODUCT)
        self.assertEqual(self.db.count(), 1)

    def test_create_entity_duplicate(self):
        """Test creating duplicate entity raises error."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        with self.assertRaises(ValueError):
            self.db.create_entity(entity)

    def test_create_entity_empty_id(self):
        """Test creating entity with empty ID raises validation error."""
        entity = SupplyEntity(
            id="",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )

        with self.assertRaises(ValidationError):
            self.db.create_entity(entity)

    def test_get_entity(self):
        """Test retrieving an entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        result = self.db.get_entity("product_1")

        self.assertIsNotNone(result)
        self.assertEqual(result.id, "product_1")

    def test_get_entity_not_found(self):
        """Test retrieving non-existent entity returns None."""
        result = self.db.get_entity("nonexistent")
        self.assertIsNone(result)

    def test_update_entity(self):
        """Test updating an entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 79.99
        result = self.db.update_entity(entity)

        self.assertEqual(result.properties["price"], 79.99)

    def test_delete_entity(self):
        """Test deleting an entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        result = self.db.delete_entity("product_1")

        self.assertTrue(result)
        self.assertIsNone(self.db.get_entity("product_1"))
        self.assertEqual(self.db.count(), 0)

    def test_delete_entity_not_found(self):
        """Test deleting non-existent entity returns False."""
        result = self.db.delete_entity("nonexistent")
        self.assertFalse(result)

    def test_create_relation(self):
        """Test creating a relation."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Test Brand"},
        )
        self.db.create_entity(product)
        self.db.create_entity(brand)

        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"weight": 0.9},
        )

        result = self.db.create_relation(relation)

        self.assertEqual(result.source_id, "product_1")
        self.assertEqual(result.target_id, "brand_1")
        self.assertEqual(self.db.count_relations(), 1)

    def test_create_relation_missing_entity(self):
        """Test creating relation with missing entity raises error."""
        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        )

        with self.assertRaises(ValueError):
            self.db.create_relation(relation)

    def test_delete_relation(self):
        """Test deleting a relation."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Test Brand"},
        )
        self.db.create_entity(product)
        self.db.create_entity(brand)

        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        )
        self.db.create_relation(relation)

        result = self.db.delete_relation(
            "product_1",
            "brand_1",
            SupplyRelationType.HAS_BRAND,
        )

        self.assertTrue(result)
        self.assertEqual(self.db.count_relations(), 0)

    def test_query_by_type(self):
        """Test querying entities by type."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 2"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(product2)
        self.db.create_entity(brand)

        products = self.db.query_by_type(SupplyEntityType.PRODUCT)

        self.assertEqual(len(products), 2)

    def test_query_by_property(self):
        """Test querying entities by property value."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1", "category": "electronics"},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 2", "category": "clothing"},
        )

        self.db.create_entity(product)
        self.db.create_entity(product2)

        results = self.db.query_by_property(
            SupplyEntityType.PRODUCT,
            "category",
            "electronics",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_search(self):
        """Test text search."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Wireless Mouse", "description": "Bluetooth mouse"},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Keyboard", "description": "Mechanical keyboard"},
        )

        self.db.create_entity(product)
        self.db.create_entity(product2)

        results = self.db.search("mouse")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_get_neighbors(self):
        """Test getting neighboring entities."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(category)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))

        neighbors = self.db.get_neighbors("product_1")

        self.assertEqual(len(neighbors), 2)

    def test_get_outgoing_relations(self):
        """Test getting outgoing relations."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        relations = self.db.get_outgoing_relations("product_1")

        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].target_id, "brand_1")

    def test_get_incoming_relations(self):
        """Test getting incoming relations."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        relations = self.db.get_incoming_relations("brand_1")

        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].source_id, "product_1")

    def test_find_shortest_path(self):
        """Test finding shortest path between entities."""
        # Create a chain: product_1 -> brand_1 -> category_1
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(category)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="brand_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))

        path = self.db.find_shortest_path("product_1", "category_1")

        self.assertIsNotNone(path)
        self.assertEqual(path.length, 2)
        self.assertEqual(len(path.entities), 3)

    def test_find_shortest_path_no_path(self):
        """Test finding path when none exists."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(category)

        path = self.db.find_shortest_path("product_1", "category_1")

        self.assertIsNone(path)

    def test_calculate_relation_confidence(self):
        """Test calculating relation confidence."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)

        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"source": "manual"},
        )

        confidence = self.db.calculate_relation_confidence(relation)

        self.assertGreater(confidence, 0.5)
        self.assertLessEqual(confidence, 1.0)

    def test_get_high_confidence_relations(self):
        """Test getting high confidence relations."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(category)

        # High confidence relation
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"source": "manual"},
        ))

        # Low confidence relation
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.SIMILAR_TO,
        ))

        high_conf = self.db.get_high_confidence_relations(threshold=0.7)

        self.assertEqual(len(high_conf), 1)
        self.assertEqual(high_conf[0][0].target_id, "brand_1")

    def test_get_degree(self):
        """Test getting entity degree."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(category)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))

        degree = self.db.get_degree("product_1")

        self.assertEqual(degree, 2)

    def test_get_graph_stats(self):
        """Test getting graph statistics."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        stats = self.db.get_graph_stats()

        self.assertEqual(stats["total_entities"], 2)
        self.assertEqual(stats["total_relations"], 1)
        self.assertIn("product", stats["entity_counts"])
        self.assertIn("has_brand", stats["relation_counts"])

    def test_export_import_graph(self):
        """Test exporting and importing graph."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        # Export
        exported = self.db.export_graph()
        self.assertEqual(len(exported.entities), 2)
        self.assertEqual(len(exported.relations), 1)

        # Create new db and import
        new_db = SupplyGraphDatabase()
        new_db.load_graph(exported)

        self.assertEqual(new_db.count(), 2)
        self.assertEqual(new_db.count_relations(), 1)

    def test_clear(self):
        """Test clearing the graph."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )

        self.db.create_entity(product)
        self.assertEqual(self.db.count(), 1)

        self.db.clear()
        self.assertEqual(self.db.count(), 0)
        self.assertEqual(self.db.count_relations(), 0)


class TestValidationRules(unittest.TestCase):
    """Test cases for validation rules."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()

    def test_weight_validation(self):
        """Test relation weight validation."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand 1"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)

        # Weight out of range should fail validation
        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"weight": 1.5},
        )

        with self.assertRaises(ValidationError):
            self.db.create_relation(relation)


if __name__ == "__main__":
    unittest.main()
