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

        with self.assertRaises(ValidationError):
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

        high_conf = self.db.get_high_confidence_relations(threshold=0.65)

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


class TestAdvancedQueryAPIs(unittest.TestCase):
    """Test cases for advanced query APIs."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        # Create test data
        self._create_test_data()

    def _create_test_data(self):
        """Create test entities and relations."""
        # Products
        product1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Laptop", "price": 999.99},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Phone", "price": 699.99},
        )
        product3 = SupplyEntity(
            id="product_3",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Tablet", "price": 499.99},
        )

        # Brands
        brand1 = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "TechCorp"},
        )
        brand2 = SupplyEntity(
            id="brand_2",
            type=SupplyEntityType.BRAND,
            properties={"name": "OtherBrand"},
        )

        # Suppliers
        supplier1 = SupplyEntity(
            id="supplier_1",
            type=SupplyEntityType.SUPPLIER,
            properties={"name": "China Supply Co"},
        )
        supplier2 = SupplyEntity(
            id="supplier_2",
            type=SupplyEntityType.SUPPLIER,
            properties={"name": "Local Supplier"},
        )

        # Category
        category1 = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        )

        # Services
        service1 = SupplyEntity(
            id="service_1",
            type=SupplyEntityType.SERVICE,
            properties={"name": "Repair Service"},
        )

        for entity in [product1, product2, product3, brand1, brand2, supplier1, supplier2, category1, service1]:
            self.db.create_entity(entity)

        # Relations
        self.db.create_relation(SupplyRelation(
            source_id="product_1", target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_2", target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_3", target_id="brand_2",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_1", target_id="supplier_1",
            relation_type=SupplyRelationType.SUPPLIES,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_2", target_id="supplier_2",
            relation_type=SupplyRelationType.SUPPLIES,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_1", target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_2", target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="service_1", target_id="product_1",
            relation_type=SupplyRelationType.PROVIDES_SERVICE,
        ))

    def test_query_entities_matching_pattern_basic(self):
        """Test basic pattern matching query."""
        # Find products that have a brand
        results = self.db.query_entities_matching_pattern(
            entity_type=SupplyEntityType.PRODUCT,
            required_relations=[
                (SupplyRelationType.HAS_BRAND, None, 'out'),
            ],
        )

        self.assertEqual(len(results), 3)  # All 3 products have brands

    def test_query_entities_matching_pattern_with_target_type(self):
        """Test pattern matching with specific target type."""
        # Find products that are supplied by a specific supplier
        results = self.db.query_entities_matching_pattern(
            entity_type=SupplyEntityType.PRODUCT,
            required_relations=[
                (SupplyRelationType.SUPPLIES, SupplyEntityType.SUPPLIER, 'out'),
            ],
        )

        self.assertEqual(len(results), 2)  # product_1 and product_2 have suppliers

    def test_query_entities_matching_pattern_property_filter(self):
        """Test pattern matching with property filters."""
        # Find products with price > 500
        results = self.db.query_entities_matching_pattern(
            entity_type=SupplyEntityType.PRODUCT,
            property_filters={"price": 999.99},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_query_entities_matching_pattern_combined(self):
        """Test pattern matching with both relations and properties."""
        # Find products that have brand AND belong to a category with price=999.99
        results = self.db.query_entities_matching_pattern(
            entity_type=SupplyEntityType.PRODUCT,
            required_relations=[
                (SupplyRelationType.HAS_BRAND, None, 'out'),
                (SupplyRelationType.BELONGS_TO, SupplyEntityType.CATEGORY, 'out'),
            ],
            property_filters={"price": 999.99},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_query_entities_matching_pattern_no_match(self):
        """Test pattern matching with no matches."""
        results = self.db.query_entities_matching_pattern(
            entity_type=SupplyEntityType.PRODUCT,
            required_relations=[
                (SupplyRelationType.PROVIDES_SERVICE, None, 'out'),
            ],
        )

        self.assertEqual(len(results), 0)

    def test_get_entity_statistics(self):
        """Test getting entity statistics."""
        stats = self.db.get_entity_statistics()

        self.assertEqual(stats["total_entities"], 9)
        self.assertEqual(stats["total_relations"], 8)
        self.assertIn("product", stats["entities_by_type"])
        self.assertEqual(stats["entities_by_type"]["product"], 3)
        self.assertIn("supplier", stats["entities_by_type"])
        self.assertEqual(stats["entities_by_type"]["supplier"], 2)

    def test_get_entity_statistics_relation_counts(self):
        """Test relation statistics."""
        stats = self.db.get_entity_statistics()

        self.assertIn("has_brand", stats["relations_by_type"])
        self.assertEqual(stats["relations_by_type"]["has_brand"], 3)
        self.assertIn("supplies", stats["relations_by_type"])
        self.assertEqual(stats["relations_by_type"]["supplies"], 2)

    def test_get_entity_statistics_connected_entities(self):
        """Test statistics about connected entities."""
        stats = self.db.get_entity_statistics()

        self.assertGreater(stats["avg_relations_per_entity"], 0)
        # All test entities have relations, so this should be 0
        self.assertEqual(stats["entities_with_no_relations"], 0)

    def test_find_similar_entities(self):
        """Test finding similar entities."""
        # product_1 and product_2 share brand and category
        similar = self.db.find_similar_entities("product_1", max_results=5)

        self.assertGreater(len(similar), 0)
        # Should find product_2 as similar (same brand, same category)
        similar_ids = [e.id for e, _ in similar]
        self.assertIn("product_2", similar_ids)

    def test_find_similar_entities_not_found(self):
        """Test finding similar entities for non-existent entity."""
        similar = self.db.find_similar_entities("nonexistent")
        self.assertEqual(len(similar), 0)

    def test_find_similar_entities_excludes_self(self):
        """Test that similar entities doesn't include the source entity."""
        similar = self.db.find_similar_entities("product_1", max_results=10)
        ids = [e.id for e, _ in similar]
        self.assertNotIn("product_1", ids)

    def test_get_connected_entities_distance_1(self):
        """Test getting connected entities at distance 1."""
        connected = self.db.get_connected_entities("product_1", max_distance=1)

        self.assertIn(1, connected)
        connected_ids = [e.id for e in connected[1]]
        self.assertIn("brand_1", connected_ids)
        self.assertIn("supplier_1", connected_ids)
        self.assertIn("category_1", connected_ids)

    def test_get_connected_entities_distance_2(self):
        """Test getting connected entities at distance 2."""
        connected = self.db.get_connected_entities("product_1", max_distance=2)

        # Distance 1: brand_1, supplier_1, category_1
        self.assertIn(1, connected)
        # Distance 2: service_1 (via PROVIDES_SERVICE from service to product)
        self.assertIn(2, connected)

    def test_get_connected_entities_with_relation_filter(self):
        """Test getting connected entities filtered by relation type."""
        connected = self.db.get_connected_entities(
            "product_1",
            max_distance=1,
            relation_types=[SupplyRelationType.HAS_BRAND],
        )

        self.assertIn(1, connected)
        connected_ids = [e.id for e in connected[1]]
        self.assertIn("brand_1", connected_ids)
        # supplier_1 and category_1 should not be included
        self.assertNotIn("supplier_1", connected_ids)
        self.assertNotIn("category_1", connected_ids)

    def test_get_connected_entities_not_found(self):
        """Test getting connected entities for non-existent entity."""
        connected = self.db.get_connected_entities("nonexistent", max_distance=2)
        self.assertEqual(len(connected), 0)


class TestMultiCriteriaQueries(unittest.TestCase):
    """Test cases for multi-criteria query API."""

    def setUp(self):
        """Set up test fixtures with sample data."""
        self.db = SupplyGraphDatabase()

        # Create products with various properties
        products = [
            ("product_1", "iPhone 15", 999.99, "electronics", "Apple"),
            ("product_2", "Samsung Galaxy", 899.99, "electronics", "Samsung"),
            ("product_3", "MacBook Pro", 1999.99, "electronics", "Apple"),
            ("product_4", "Nike Air Max", 149.99, "clothing", "Nike"),
            ("product_5", "Adidas Shoes", 129.99, "clothing", "Adidas"),
        ]

        for pid, name, price, category, brand in products:
            entity = SupplyEntity(
                id=pid,
                type=SupplyEntityType.PRODUCT,
                properties={
                    "name": name,
                    "price": price,
                    "category": category,
                    "brand": brand,
                },
            )
            self.db.create_entity(entity)

        # Create categories
        for i, cat in enumerate(["electronics", "clothing"]):
            entity = SupplyEntity(
                id=f"category_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": cat},
            )
            self.db.create_entity(entity)

    def test_query_by_properties_match_all(self):
        """Test query with AND (match_all=True)."""
        results = self.db.query_by_properties(
            SupplyEntityType.PRODUCT,
            {"brand": "Apple", "category": "electronics"},
            match_all=True,
        )

        self.assertEqual(len(results), 2)
        ids = [e.id for e in results]
        self.assertIn("product_1", ids)
        self.assertIn("product_3", ids)

    def test_query_by_properties_match_any(self):
        """Test query with OR (match_all=False)."""
        results = self.db.query_by_properties(
            SupplyEntityType.PRODUCT,
            {"brand": "Apple"},
            match_all=False,
        )

        self.assertEqual(len(results), 2)
        ids = [e.id for e in results]
        self.assertIn("product_1", ids)
        self.assertIn("product_3", ids)

    def test_query_by_property_range(self):
        """Test query by numeric property range."""
        # Price between 100 and 500
        results = self.db.query_by_property_range(
            SupplyEntityType.PRODUCT,
            "price",
            min_value=100,
            max_value=500,
        )

        self.assertEqual(len(results), 2)
        ids = [e.id for e in results]
        self.assertIn("product_4", ids)  # Nike Air Max: 149.99
        self.assertIn("product_5", ids)  # Adidas Shoes: 129.99

    def test_query_by_property_range_no_min(self):
        """Test query with no minimum value."""
        results = self.db.query_by_property_range(
            SupplyEntityType.PRODUCT,
            "price",
            max_value=200,
        )

        # product_4 (149.99), product_5 (129.99) are <= 200
        self.assertEqual(len(results), 2)
        ids = [e.id for e in results]
        self.assertIn("product_4", ids)
        self.assertIn("product_5", ids)

    def test_query_by_property_range_no_max(self):
        """Test query with no maximum value."""
        results = self.db.query_by_property_range(
            SupplyEntityType.PRODUCT,
            "price",
            min_value=1000,
        )

        # product_3 (1999.99) is >= 1000; product_1 (999.99) is NOT >= 1000
        self.assertEqual(len(results), 1)
        ids = [e.id for e in results]
        self.assertIn("product_3", ids)

    def test_advanced_search_with_type_filter(self):
        """Test advanced search with entity type filter."""
        results = self.db.advanced_search(
            "phone",
            entity_types=[SupplyEntityType.PRODUCT],
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_advanced_search_with_property_filters(self):
        """Test advanced search with property filters."""
        results = self.db.advanced_search(
            "phone",
            property_filters={"brand": "Apple"},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")

    def test_advanced_search_no_results(self):
        """Test advanced search with no matches."""
        results = self.db.advanced_search(
            "xyznonexistent",
            entity_types=[SupplyEntityType.PRODUCT],
        )

        self.assertEqual(len(results), 0)

    def test_count_by_type(self):
        """Test count by entity type."""
        counts = self.db.count_by_type()

        self.assertEqual(counts[SupplyEntityType.PRODUCT], 5)
        self.assertEqual(counts[SupplyEntityType.CATEGORY], 2)

    def test_get_entities_with_most_relations(self):
        """Test getting entities with most relations."""
        # First add some relations
        product = self.db.get_entity("product_1")
        brand = SupplyEntity(
            id="brand_test",
            type=SupplyEntityType.BRAND,
            properties={"name": "Test Brand"},
        )
        self.db.create_entity(brand)

        # Add multiple relations to product_1
        for i in range(5):
            supplier = SupplyEntity(
                id=f"supplier_{i}",
                type=SupplyEntityType.SUPPLIER,
                properties={"name": f"Supplier {i}"},
            )
            self.db.create_entity(supplier)
            self.db.create_relation(SupplyRelation(
                source_id="product_1",
                target_id=f"supplier_{i}",
                relation_type=SupplyRelationType.SUPPLIES,
            ))

        top_entities = self.db.get_entities_with_most_relations(limit=3)

        self.assertEqual(len(top_entities), 3)
        self.assertEqual(top_entities[0][0].id, "product_1")
        self.assertEqual(top_entities[0][1], 5)  # degree

    def test_query_with_relations_min_relations(self):
        """Test query requiring minimum number of relations."""
        # Add relations to product_1
        for i in range(3):
            supplier = SupplyEntity(
                id=f"supplier_rel_{i}",
                type=SupplyEntityType.SUPPLIER,
                properties={"name": f"Supplier {i}"},
            )
            self.db.create_entity(supplier)
            self.db.create_relation(SupplyRelation(
                source_id="product_1",
                target_id=f"supplier_rel_{i}",
                relation_type=SupplyRelationType.SUPPLIES,
            ))

        # Query entities with at least 2 relations
        results = self.db.query_with_relations(
            entity_type=SupplyEntityType.PRODUCT,
            min_relations=2,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "product_1")


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
