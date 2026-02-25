"""Unit tests for SupplyGraphDatabase."""

import unittest

from multi_agent_system.knowledge.supply_graph_database import (
    SupplyGraphDatabase,
    ValidationError,
    DuplicateGroup,
    MergeResult,
    ChangeType,
    ChangeHistory,
    Transaction,
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

    def test_find_paths_multiple(self):
        """Test finding multiple paths between entities.

        Creates a diamond graph: source -> a -> target
                              source -> b -> target

        Should find 2 distinct paths.
        """
        # Create diamond graph: product -> (brand/merchant) -> category
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
        merchant = SupplyEntity(
            id="merchant_1",
            type=SupplyEntityType.MERCHANT,
            properties={"name": "Merchant 1"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        )

        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(merchant)
        self.db.create_entity(category)

        # Two paths to category: via brand and via merchant
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
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="merchant_1",
            relation_type=SupplyRelationType.SELLS,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="merchant_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))

        paths = self.db.find_paths("product_1", "category_1", max_length=5)

        # Should find 2 paths
        self.assertEqual(len(paths), 2)

        # Each path should have length 2
        for path in paths:
            self.assertEqual(path.length, 2)

    def test_find_paths_max_length(self):
        """Test find_paths respects max_length parameter."""
        # Create a longer chain: a -> b -> c -> d -> e
        entities = ["a", "b", "c", "d", "e"]
        for e in entities:
            self.db.create_entity(SupplyEntity(
                id=e,
                type=SupplyEntityType.PRODUCT,
                properties={"name": e},
            ))

        # Create chain
        for i in range(len(entities) - 1):
            self.db.create_relation(SupplyRelation(
                source_id=entities[i],
                target_id=entities[i + 1],
                relation_type=SupplyRelationType.RELATED_TO,
            ))

        # Find paths from a to e with max_length=2
        paths = self.db.find_paths("a", "e", max_length=2)

        # Should find no paths (minimum path length is 4)
        self.assertEqual(len(paths), 0)

        # Find paths with max_length=5
        paths = self.db.find_paths("a", "e", max_length=5)

        # Should find 1 path
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].length, 4)

    def test_find_paths_no_path(self):
        """Test find_paths when no path exists."""
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

        paths = self.db.find_paths("product_1", "category_1")

        self.assertEqual(len(paths), 0)

    def test_find_paths_nonexistent_entities(self):
        """Test find_paths with nonexistent entities."""
        paths = self.db.find_paths("nonexistent1", "nonexistent2")
        self.assertEqual(len(paths), 0)

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


class TestEntityNormalization(unittest.TestCase):
    """Test cases for entity normalization and deduplication."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()

    def test_calculate_entity_similarity_identical(self):
        """Test similarity of identical entities."""
        entity1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone 15", "price": 999.99},
        )
        entity2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone 15", "price": 999.99},
        )

        similarity = self.db.calculate_entity_similarity(entity1, entity2)

        self.assertEqual(similarity, 1.0)

    def test_calculate_entity_similarity_same_name_different_type(self):
        """Test similarity when names match but types differ."""
        entity1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        entity2 = SupplyEntity(
            id="service_1",
            type=SupplyEntityType.SERVICE,
            properties={"name": "Test Product"},
        )

        similarity = self.db.calculate_entity_similarity(entity1, entity2)

        # Same name but different type - should have type penalty
        self.assertLess(similarity, 1.0)
        self.assertGreater(similarity, 0.5)

    def test_calculate_entity_similarity_different_names(self):
        """Test similarity with different names."""
        entity1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone 15"},
        )
        entity2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Samsung Galaxy"},
        )

        similarity = self.db.calculate_entity_similarity(entity1, entity2)

        self.assertLess(similarity, 0.5)

    def test_calculate_entity_similarity_substring(self):
        """Test similarity with substring match."""
        entity1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone 15 Pro"},
        )
        entity2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone 15"},
        )

        similarity = self.db.calculate_entity_similarity(entity1, entity2)

        # Should get boost for substring match
        self.assertGreater(similarity, 0.7)

    def test_find_potential_duplicates_exact_match(self):
        """Test finding exact duplicate entities."""
        # Add duplicate entities
        entities = [
            SupplyEntity(
                id="product_1",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Test Product", "price": 99.99},
            ),
            SupplyEntity(
                id="product_2",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Test Product", "price": 99.99},
            ),
        ]
        for e in entities:
            self.db.create_entity(e)

        duplicates = self.db.find_potential_duplicates(
            entity_type=SupplyEntityType.PRODUCT,
            similarity_threshold=0.8,
        )

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].count, 2)

    def test_find_potential_duplicates_no_duplicates(self):
        """Test when no duplicates exist."""
        entities = [
            SupplyEntity(
                id="product_1",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "iPhone 15"},
            ),
            SupplyEntity(
                id="product_2",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Samsung Galaxy"},
            ),
        ]
        for e in entities:
            self.db.create_entity(e)

        duplicates = self.db.find_potential_duplicates(
            entity_type=SupplyEntityType.PRODUCT,
            similarity_threshold=0.8,
        )

        self.assertEqual(len(duplicates), 0)

    def test_find_potential_duplicates_filter_by_type(self):
        """Test filtering duplicates by entity type."""
        # Add products and services with similar names
        entities = [
            SupplyEntity(
                id="product_1",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Repair Service"},
            ),
            SupplyEntity(
                id="service_1",
                type=SupplyEntityType.SERVICE,
                properties={"name": "Repair Service"},
            ),
        ]
        for e in entities:
            self.db.create_entity(e)

        # Find duplicates only for products
        product_dupes = self.db.find_potential_duplicates(
            entity_type=SupplyEntityType.PRODUCT,
            similarity_threshold=0.8,
        )

        self.assertEqual(len(product_dupes), 0)

        # Find duplicates for services
        service_dupes = self.db.find_potential_duplicates(
            entity_type=SupplyEntityType.SERVICE,
            similarity_threshold=0.8,
        )

        self.assertEqual(len(service_dupes), 0)

    def test_merge_entities_basic(self):
        """Test basic merge of two entities."""
        # Create entities with relations
        product1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product A", "price": 100},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product A", "color": "red"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Test Brand"},
        )

        for e in [product1, product2, brand]:
            self.db.create_entity(e)

        # Add relations
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_2",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        # Merge
        result = self.db.merge_entities(
            entity_ids=["product_1", "product_2"],
            canonical_id="product_1",
        )

        self.assertEqual(result.merged_entity.id, "product_1")
        self.assertIn("price", result.merged_entity.properties)
        self.assertIn("color", result.merged_entity.properties)
        self.assertEqual(result.relations_preserved, 2)

    def test_merge_entities_deletes_duplicates(self):
        """Test that merge deletes duplicate entities."""
        product1 = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product A"},
        )
        product2 = SupplyEntity(
            id="product_2",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product A"},
        )

        for e in [product1, product2]:
            self.db.create_entity(e)

        self.assertEqual(self.db.count(), 2)

        result = self.db.merge_entities(
            entity_ids=["product_1", "product_2"],
            canonical_id="product_1",
        )

        self.assertEqual(self.db.count(), 1)
        self.assertIsNotNone(self.db.get_entity("product_1"))
        self.assertIsNone(self.db.get_entity("product_2"))

    def test_merge_entities_invalid_entity(self):
        """Test merge with non-existent entity raises error."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product A"},
        )
        self.db.create_entity(entity)

        with self.assertRaises(ValueError):
            self.db.merge_entities(
                entity_ids=["product_1", "nonexistent"],
            )

    def test_deduplicate(self):
        """Test automatic deduplication."""
        # Create multiple duplicate products
        products = [
            SupplyEntity(id="p1", type=SupplyEntityType.PRODUCT, properties={"name": "Phone"}),
            SupplyEntity(id="p2", type=SupplyEntityType.PRODUCT, properties={"name": "Phone"}),
            SupplyEntity(id="p3", type=SupplyEntityType.PRODUCT, properties={"name": "Tablet"}),
            SupplyEntity(id="p4", type=SupplyEntityType.PRODUCT, properties={"name": "Tablet"}),
        ]
        for p in products:
            self.db.create_entity(p)

        results = self.db.deduplicate(similarity_threshold=0.8)

        # Should have merged 2 groups (phones and tablets)
        self.assertEqual(len(results), 2)
        # Should have 2 entities left (one canonical per group)
        self.assertEqual(self.db.count(), 2)

    def test_deduplicate_empty_graph(self):
        """Test deduplication on empty graph."""
        results = self.db.deduplicate()

        self.assertEqual(len(results), 0)

    def test_get_normalized_entity_representatives(self):
        """Test getting normalized entity representatives."""
        # Create products with duplicates
        entities = [
            SupplyEntity(id="p1", type=SupplyEntityType.PRODUCT, properties={"name": "Phone"}),
            SupplyEntity(id="p2", type=SupplyEntityType.PRODUCT, properties={"name": "Phone"}),
            SupplyEntity(id="p3", type=SupplyEntityType.PRODUCT, properties={"name": "Tablet"}),
        ]
        for e in entities:
            self.db.create_entity(e)

        representatives = self.db.get_normalized_entity_representatives(
            entity_type=SupplyEntityType.PRODUCT
        )

        # Should return 2 - one for Phone group, one for Tablet
        self.assertEqual(len(representatives), 2)


class TestIncrementalUpdatePipeline(unittest.TestCase):
    """Test cases for incremental update pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()

    def test_change_history_records_entity_creation(self):
        """Test that entity creation is recorded in change history."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        history = self.db.get_change_history()

        self.assertEqual(len(history.events), 1)
        self.assertEqual(history.events[0].change_type, ChangeType.ENTITY_CREATED)
        self.assertEqual(history.events[0].entity_id, "product_1")

    def test_change_history_records_entity_update(self):
        """Test that entity update is recorded in change history."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 99.99
        self.db.update_entity(entity)

        history = self.db.get_change_history()

        self.assertEqual(len(history.events), 2)
        self.assertEqual(history.events[1].change_type, ChangeType.ENTITY_UPDATED)

    def test_change_history_records_entity_deletion(self):
        """Test that entity deletion is recorded in change history."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)
        self.db.delete_entity("product_1")

        history = self.db.get_change_history()

        self.assertEqual(len(history.events), 2)
        self.assertEqual(history.events[1].change_type, ChangeType.ENTITY_DELETED)

    def test_change_history_records_relation_creation(self):
        """Test that relation creation is recorded in change history."""
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

        history = self.db.get_change_history()

        self.assertEqual(len(history.events), 3)
        self.assertEqual(history.events[2].change_type, ChangeType.RELATION_CREATED)

    def test_get_entity_version(self):
        """Test getting entity version."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        version = self.db.get_entity_version("product_1")

        self.assertEqual(version, 1)

    def test_get_entity_version_increment(self):
        """Test that version increments on update."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 99.99
        self.db.update_entity(entity)

        version = self.db.get_entity_version("product_1")

        self.assertEqual(version, 2)

    def test_get_graph_version(self):
        """Test getting overall graph version."""
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
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        version = self.db.get_graph_version()

        self.assertEqual(version, 3)

    def test_get_change_history_for_specific_entity(self):
        """Test getting change history for a specific entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 99.99
        self.db.update_entity(entity)

        history = self.db.get_change_history(entity_id="product_1")

        self.assertEqual(len(history.events), 2)

    def test_transaction_commit(self):
        """Test committing a transaction."""
        self.db.begin_transaction()

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
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        self.db.commit()

        self.assertEqual(self.db.count(), 2)
        self.assertEqual(self.db.count_relations(), 1)

    def test_transaction_rollback(self):
        """Test rolling back a transaction."""
        self.db.begin_transaction()

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
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))

        self.db.rollback()

        self.assertEqual(self.db.count(), 0)
        self.assertEqual(self.db.count_relations(), 0)

    def test_transaction_rollback_on_error(self):
        """Test that transaction is rolled back on error."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(product)

        self.db.begin_transaction()

        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Test Brand"},
        )
        self.db.create_entity(brand)

        # Try to create a relation with non-existent entity
        relation = SupplyRelation(
            source_id="product_1",
            target_id="nonexistent",
            relation_type=SupplyRelationType.HAS_BRAND,
        )

        with self.assertRaises(ValidationError):
            self.db.create_relation(relation)

        # Transaction should have been rolled back
        self.assertEqual(self.db.count(), 1)  # Only product remains

    def test_nested_transaction_raises_error(self):
        """Test that nested transactions raise an error."""
        self.db.begin_transaction()

        with self.assertRaises(RuntimeError):
            self.db.begin_transaction()

    def test_upsert_new_entity(self):
        """Test upserting a new entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )

        result, created = self.db.upsert_entity(entity)

        self.assertTrue(created)
        self.assertEqual(self.db.count(), 1)

    def test_upsert_existing_entity(self):
        """Test upserting an existing entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 99.99
        result, created = self.db.upsert_entity(entity)

        self.assertFalse(created)
        self.assertEqual(result.version, 2)
        self.assertEqual(result.properties["price"], 99.99)
        self.assertEqual(result.properties["name"], "Test Product")

    def test_incrementally_update_entity_create(self):
        """Test incrementally updating a new entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )

        result = self.db.incrementally_update_entity(entity)

        self.assertEqual(self.db.count(), 1)
        self.assertEqual(result.id, "product_1")

    def test_incrementally_update_entity_update(self):
        """Test incrementally updating an existing entity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        entity.properties["price"] = 99.99
        result = self.db.incrementally_update_entity(entity)

        self.assertEqual(result.version, 2)
        self.assertEqual(self.db.count(), 1)

    def test_batch_create_entities(self):
        """Test batch creating entities."""
        entities = [
            SupplyEntity(
                id=f"product_{i}",
                type=SupplyEntityType.PRODUCT,
                properties={"name": f"Product {i}"},
            )
            for i in range(5)
        ]

        results = self.db.batch_create_entities(entities)

        self.assertEqual(len(results), 5)
        self.assertEqual(self.db.count(), 5)

    def test_batch_create_relations(self):
        """Test batch creating relations."""
        # Create entities first
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category"},
        )
        self.db.batch_create_entities([product, brand, category])

        # Create relations
        relations = [
            SupplyRelation(
                source_id="product_1",
                target_id="brand_1",
                relation_type=SupplyRelationType.HAS_BRAND,
            ),
            SupplyRelation(
                source_id="product_1",
                target_id="category_1",
                relation_type=SupplyRelationType.BELONGS_TO,
            ),
        ]

        results = self.db.batch_create_relations(relations)

        self.assertEqual(len(results), 2)
        self.assertEqual(self.db.count_relations(), 2)

    def test_apply_incremental_changes(self):
        """Test applying incremental changes."""
        # Create some base entities
        self.db.create_entity(SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        ))

        result = self.db.apply_incremental_changes(
            entities_to_create=[
                SupplyEntity(
                    id="product_2",
                    type=SupplyEntityType.PRODUCT,
                    properties={"name": "Product 2"},
                ),
            ],
            entities_to_update=[
                SupplyEntity(
                    id="product_1",
                    type=SupplyEntityType.PRODUCT,
                    properties={"name": "Updated Product 1"},
                ),
            ],
        )

        self.assertEqual(result["entities_created"], 1)
        self.assertEqual(result["entities_updated"], 1)

    def test_apply_incremental_changes_rollback(self):
        """Test that incremental changes rollback on error."""
        # Create a base entity
        self.db.create_entity(SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Product 1"},
        ))

        with self.assertRaises(ValidationError):
            self.db.apply_incremental_changes(
                entities_to_create=[
                    SupplyEntity(
                        id="product_2",
                        type=SupplyEntityType.PRODUCT,
                        properties={"name": "Product 2"},
                    ),
                ],
                relations_to_create=[
                    SupplyRelation(
                        source_id="product_1",
                        target_id="nonexistent",
                        relation_type=SupplyRelationType.HAS_BRAND,
                    ),
                ],
            )

        # Should have rolled back - only original entity remains
        self.assertEqual(self.db.count(), 1)
        self.assertEqual(self.db.count_relations(), 0)

    def test_change_history_limit(self):
        """Test getting limited change history."""
        for i in range(20):
            entity = SupplyEntity(
                id=f"product_{i}",
                type=SupplyEntityType.PRODUCT,
                properties={"name": f"Product {i}"},
            )
            self.db.create_entity(entity)

        history = self.db.get_change_history(limit=10)

        self.assertEqual(len(history.events), 10)
        self.assertEqual(history.version, 20)


if __name__ == "__main__":
    unittest.main()
