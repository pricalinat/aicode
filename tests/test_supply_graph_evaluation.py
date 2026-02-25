"""Unit tests for SupplyGraphEvaluation."""

import unittest

from multi_agent_system.knowledge.supply_graph_evaluation import (
    GraphBenchmark,
    SupplyGraphEvaluator,
)
from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)


class TestSupplyGraphEvaluator(unittest.TestCase):
    """Test cases for SupplyGraphEvaluator."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.evaluator = SupplyGraphEvaluator(self.db)

    def _create_sample_data(self):
        """Create sample entities and relations for testing."""
        # Create categories
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics", "description": "Electronic products"},
        )
        self.db.create_entity(category)

        # Create brand
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Apple", "country": "US"},
        )
        self.db.create_entity(brand)

        # Create merchant
        merchant = SupplyEntity(
            id="merchant_1",
            type=SupplyEntityType.MERCHANT,
            properties={"name": "Amazon", "rating": 4.5},
        )
        self.db.create_entity(merchant)

        # Create product
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={
                "name": "iPhone 15",
                "description": "Latest iPhone",
                "price": 999.99,
                "category": "category_1",
                "brand": "brand_1",
                "merchant": "merchant_1",
            },
        )
        self.db.create_entity(product)

        # Create relations
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
            properties={"weight": 0.9},
        ))

        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"weight": 0.95},
        ))

        self.db.create_relation(SupplyRelation(
            source_id="merchant_1",
            target_id="product_1",
            relation_type=SupplyRelationType.SELLS,
            properties={"weight": 0.9},
        ))

    def test_evaluate_empty_graph(self):
        """Test evaluation on empty graph."""
        metrics = self.evaluator.evaluate()

        self.assertEqual(metrics.entity_quality.total_entities, 0)
        self.assertEqual(metrics.relation_quality.total_relations, 0)
        self.assertEqual(metrics.graph_metrics.total_entities, 0)

    def test_evaluate_entity_quality(self):
        """Test entity quality evaluation."""
        self._create_sample_data()

        metrics = self.evaluator.evaluate_entity_quality()

        self.assertEqual(metrics.total_entities, 4)
        self.assertGreater(metrics.entities_with_name, 0)
        self.assertGreater(metrics.completeness_score, 0)

    def test_evaluate_relation_quality(self):
        """Test relation quality evaluation."""
        self._create_sample_data()

        metrics = self.evaluator.evaluate_relation_quality()

        self.assertEqual(metrics.total_relations, 3)
        self.assertGreater(metrics.avg_confidence, 0)
        self.assertEqual(len(metrics.orphan_entities), 0)

    def test_evaluate_graph_structure(self):
        """Test graph structure evaluation."""
        self._create_sample_data()

        metrics = self.evaluator.evaluate_graph_structure()

        self.assertEqual(metrics.total_entities, 4)
        self.assertEqual(metrics.total_relations, 3)
        self.assertGreater(metrics.avg_degree, 0)
        self.assertGreaterEqual(metrics.connected_components, 1)

    def test_find_orphan_entities(self):
        """Test detection of orphan entities."""
        # Create an orphan entity
        orphan = SupplyEntity(
            id="orphan_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Orphan Product"},
        )
        self.db.create_entity(orphan)

        metrics = self.evaluator.evaluate_relation_quality()

        self.assertIn("orphan_1", metrics.orphan_entities)

    def test_get_quality_score(self):
        """Test overall quality score calculation."""
        self._create_sample_data()

        score = self.evaluator.get_quality_score()

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_recommendations(self):
        """Test getting improvement recommendations."""
        # Empty graph should have recommendations
        recommendations = self.evaluator.get_recommendations()

        self.assertGreater(len(recommendations), 0)

    def test_benchmark_performance(self):
        """Test performance benchmarking."""
        self._create_sample_data()

        metrics = self.evaluator.benchmark_performance(iterations=10)

        self.assertIn("query_by_type_avg", metrics.query_latency_ms)


class TestGraphBenchmark(unittest.TestCase):
    """Test cases for GraphBenchmark."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.benchmark = GraphBenchmark(self.db)

    def test_generate_test_data(self):
        """Test generating test data."""
        data = self.benchmark.generate_test_data(
            num_products=10,
            num_categories=5,
            num_brands=3,
            num_merchants=2,
        )

        self.assertEqual(len(data["categories"]), 5)
        self.assertEqual(len(data["brands"]), 3)
        self.assertEqual(len(data["merchants"]), 2)
        self.assertEqual(len(data["products"]), 10)

    def test_run_benchmark(self):
        """Test running benchmark."""
        result = self.benchmark.run_benchmark(num_products=50)

        self.assertIn("ingestion", result)
        self.assertIn("graph_stats", result)
        self.assertIn("quality", result)
        self.assertIn("performance", result)

        # Check that entities were created
        self.assertGreater(result["graph_stats"]["total_entities"], 0)
        self.assertGreater(result["graph_stats"]["total_relations"], 0)


class TestEntityQualityMetrics(unittest.TestCase):
    """Test cases for entity quality metrics by type."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.evaluator = SupplyGraphEvaluator(self.db)

    def test_product_with_all_properties(self):
        """Test product entity with all required properties."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={
                "name": "Test Product",
                "description": "A test product",
                "price": 99.99,
            },
        )
        self.db.create_entity(product)

        metrics = self.evaluator.evaluate_entity_quality()

        self.assertIn("product", metrics.by_type)
        self.assertEqual(metrics.by_type["product"]["with_name"], 1)
        self.assertEqual(metrics.by_type["product"]["with_description"], 1)

    def test_product_missing_name(self):
        """Test product entity missing name."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"price": 99.99},
        )
        self.db.create_entity(product)

        metrics = self.evaluator.evaluate_entity_quality()

        self.assertEqual(metrics.by_type["product"]["with_name"], 0)


class TestRelationQualityMetrics(unittest.TestCase):
    """Test cases for relation quality metrics."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.evaluator = SupplyGraphEvaluator(self.db)

    def test_high_confidence_relation(self):
        """Test high confidence relation scoring."""
        # Create entities
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Brand"},
        )
        self.db.create_entity(product)
        self.db.create_entity(brand)

        # High confidence relation (HAS_BRAND is high weight type)
        relation = SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
            properties={"weight": 0.9, "source": "manual"},
        )
        self.db.create_relation(relation)

        metrics = self.evaluator.evaluate_relation_quality()

        self.assertGreater(metrics.avg_confidence, 0.6)
        self.assertEqual(metrics.high_confidence_count, 1)

    def test_low_confidence_relation(self):
        """Test low confidence relation scoring."""
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test"},
        )
        category = SupplyEntity(
            id="category_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Category"},
        )
        self.db.create_entity(product)
        self.db.create_entity(category)

        # Low confidence relation (SIMILAR_TO is low weight type)
        relation = SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.SIMILAR_TO,
            properties={"weight": 0.3},
        )
        self.db.create_relation(relation)

        metrics = self.evaluator.evaluate_relation_quality()

        self.assertLess(metrics.avg_confidence, 0.6)


class TestGraphMetrics(unittest.TestCase):
    """Test cases for graph-level metrics."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.evaluator = SupplyGraphEvaluator(self.db)

    def test_density_calculation(self):
        """Test graph density calculation."""
        # Create a small connected graph
        for i in range(4):
            entity = SupplyEntity(
                id=f"entity_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": f"Entity {i}"},
            )
            self.db.create_entity(entity)

        # Create 3 relations (complete graph would have 6)
        for i in range(3):
            self.db.create_relation(SupplyRelation(
                source_id=f"entity_{i}",
                target_id=f"entity_{i+1}",
                relation_type=SupplyRelationType.RELATED_TO,
            ))

        metrics = self.evaluator.evaluate_graph_structure()

        # Density should be between 0 and 1
        self.assertGreater(metrics.density, 0)
        self.assertLess(metrics.density, 1)

    def test_connected_components(self):
        """Test connected components detection."""
        # Create two disconnected entities
        for i in range(2):
            entity = SupplyEntity(
                id=f"entity_a_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": f"Entity A {i}"},
            )
            self.db.create_entity(entity)

        # Create another disconnected pair
        for i in range(2):
            entity = SupplyEntity(
                id=f"entity_b_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": f"Entity B {i}"},
            )
            self.db.create_entity(entity)

        # Connect each pair internally
        self.db.create_relation(SupplyRelation(
            source_id="entity_a_0",
            target_id="entity_a_1",
            relation_type=SupplyRelationType.RELATED_TO,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="entity_b_0",
            target_id="entity_b_1",
            relation_type=SupplyRelationType.RELATED_TO,
        ))

        metrics = self.evaluator.evaluate_graph_structure()

        self.assertEqual(metrics.connected_components, 2)
        self.assertEqual(metrics.largest_component_size, 2)

    def test_isolated_entities(self):
        """Test isolated entity detection."""
        # Create connected pair
        entity1 = SupplyEntity(
            id="entity_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Entity 1"},
        )
        entity2 = SupplyEntity(
            id="entity_2",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Entity 2"},
        )
        self.db.create_entity(entity1)
        self.db.create_entity(entity2)

        # Create isolated entity
        entity3 = SupplyEntity(
            id="entity_3",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Entity 3"},
        )
        self.db.create_entity(entity3)

        # Connect first two
        self.db.create_relation(SupplyRelation(
            source_id="entity_1",
            target_id="entity_2",
            relation_type=SupplyRelationType.RELATED_TO,
        ))

        metrics = self.evaluator.evaluate_graph_structure()

        self.assertEqual(metrics.isolated_entities, 1)

    def test_entity_type_distribution(self):
        """Test entity type distribution calculation."""
        # Create products
        for i in range(3):
            entity = SupplyEntity(
                id=f"product_{i}",
                type=SupplyEntityType.PRODUCT,
                properties={"name": f"Product {i}"},
            )
            self.db.create_entity(entity)

        # Create categories
        for i in range(2):
            entity = SupplyEntity(
                id=f"category_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": f"Category {i}"},
            )
            self.db.create_entity(entity)

        metrics = self.evaluator.evaluate_graph_structure()

        self.assertEqual(metrics.entity_type_distribution["product"], 3)
        self.assertEqual(metrics.entity_type_distribution["category"], 2)

    def test_relation_type_distribution(self):
        """Test relation type distribution calculation."""
        # Create entities
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
        self.db.create_entity(product)
        self.db.create_entity(brand)
        self.db.create_entity(category)

        # Create relations of different types
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
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="category_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))

        metrics = self.evaluator.evaluate_graph_structure()

        self.assertEqual(metrics.relation_type_distribution["has_brand"], 1)
        self.assertEqual(metrics.relation_type_distribution["belongs_to"], 2)

    def test_evaluate_full_graph_with_relations(self):
        """Test complete evaluation of graph with relations."""
        # Create a more complete graph
        category = SupplyEntity(
            id="cat_1",
            type=SupplyEntityType.CATEGORY,
            properties={"name": "Electronics"},
        )
        brand = SupplyEntity(
            id="brand_1",
            type=SupplyEntityType.BRAND,
            properties={"name": "Apple"},
        )
        merchant = SupplyEntity(
            id="merchant_1",
            type=SupplyEntityType.MERCHANT,
            properties={"name": "Store"},
        )
        product = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "iPhone", "price": 999},
        )

        for entity in [category, brand, merchant, product]:
            self.db.create_entity(entity)

        # Create multiple relations
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="cat_1",
            relation_type=SupplyRelationType.BELONGS_TO,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="product_1",
            target_id="brand_1",
            relation_type=SupplyRelationType.HAS_BRAND,
        ))
        self.db.create_relation(SupplyRelation(
            source_id="merchant_1",
            target_id="product_1",
            relation_type=SupplyRelationType.SELLS,
        ))

        result = self.evaluator.evaluate()

        self.assertEqual(result.entity_quality.total_entities, 4)
        self.assertEqual(result.relation_quality.total_relations, 3)
        self.assertGreater(result.graph_metrics.density, 0)
        self.assertIn("query_by_type_avg", result.performance.query_latency_ms)

    def test_recommendations_with_empty_graph(self):
        """Test recommendations for empty graph."""
        recommendations = self.evaluator.get_recommendations()

        # Empty graph should have recommendation about adding relations
        self.assertTrue(any("relation" in r.lower() for r in recommendations))

    def test_recommendations_with_connected_graph(self):
        """Test recommendations for well-connected graph."""
        # Create well-connected graph
        for i in range(5):
            entity = SupplyEntity(
                id=f"entity_{i}",
                type=SupplyEntityType.CATEGORY,
                properties={"name": f"Entity {i}"},
            )
            self.db.create_entity(entity)

        # Connect all entities
        for i in range(4):
            self.db.create_relation(SupplyRelation(
                source_id=f"entity_{i}",
                target_id=f"entity_{i+1}",
                relation_type=SupplyRelationType.RELATED_TO,
            ))

        recommendations = self.evaluator.get_recommendations()

        # Should have fewer recommendations for well-connected graph
        self.assertIsInstance(recommendations, list)


class TestBenchmarkPerformance(unittest.TestCase):
    """Test cases for benchmark performance metrics."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.benchmark = GraphBenchmark(self.db)

    def test_benchmark_creates_entities(self):
        """Test that benchmark creates expected number of entities."""
        result = self.benchmark.run_benchmark(num_products=100)

        # Should create multiple entities
        self.assertGreater(result["graph_stats"]["total_entities"], 100)

    def test_benchmark_performance_metrics(self):
        """Test benchmark returns performance metrics."""
        result = self.benchmark.run_benchmark(num_products=50)

        # Should have performance metrics
        self.assertIn("query_by_type_ms", result["performance"])
        self.assertIn("search_ms", result["performance"])

    def test_benchmark_quality_metrics(self):
        """Test benchmark returns quality metrics."""
        result = self.benchmark.run_benchmark(num_products=30)

        # Should have quality metrics
        self.assertIn("entity_completeness", result["quality"])
        self.assertIn("relation_confidence", result["quality"])
        self.assertIn("overall_score", result["quality"])


if __name__ == "__main__":
    unittest.main()
