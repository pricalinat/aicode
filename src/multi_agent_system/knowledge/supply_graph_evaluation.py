"""Supply Knowledge Graph Evaluation Metrics.

This module provides comprehensive evaluation metrics for measuring
the quality and performance of the supply knowledge graph.

Metrics include:
- Entity quality: completeness, consistency, uniqueness
- Relation quality: coverage, confidence distribution
- Graph-level: density, connectivity, diameter
- Performance: query latency, throughput
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .supply_graph_database import SupplyGraphDatabase
from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)


@dataclass
class EntityQualityMetrics:
    """Quality metrics for entities."""
    total_entities: int = 0
    entities_with_name: int = 0
    entities_with_description: int = 0
    entities_with_required_props: int = 0
    completeness_score: float = 0.0
    by_type: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class RelationQualityMetrics:
    """Quality metrics for relations."""
    total_relations: int = 0
    high_confidence_count: int = 0
    low_confidence_count: int = 0
    avg_confidence: float = 0.0
    coverage_by_type: dict[str, int] = field(default_factory=dict)
    orphan_entities: list[str] = field(default_factory=list)


@dataclass
class GraphMetrics:
    """Graph-level quality metrics."""
    total_entities: int = 0
    total_relations: int = 0
    density: float = 0.0
    avg_degree: float = 0.0
    connected_components: int = 0
    largest_component_size: int = 0
    isolated_entities: int = 0
    entity_type_distribution: dict[str, int] = field(default_factory=dict)
    relation_type_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance benchmark metrics."""
    query_latency_ms: dict[str, float] = field(default_factory=dict)
    throughput_ops_per_sec: dict[str, float] = field(default_factory=dict)
    batch_ingestion_time_ms: float = 0.0
    path_finding_avg_ms: float = 0.0


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    entity_quality: EntityQualityMetrics = field(default_factory=EntityQualityMetrics)
    relation_quality: RelationQualityMetrics = field(default_factory=RelationQualityMetrics)
    graph_metrics: GraphMetrics = field(default_factory=GraphMetrics)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    timestamp: str = ""


class SupplyGraphEvaluator:
    """Evaluator for supply knowledge graph quality.

    Provides comprehensive metrics for assessing graph health,
    identifying gaps, and benchmarking performance.
    """

    # Required properties by entity type
    REQUIRED_PROPERTIES: dict[SupplyEntityType, list[str]] = {
        SupplyEntityType.PRODUCT: ["name"],
        SupplyEntityType.SERVICE: ["name"],
        SupplyEntityType.PROCEDURE: ["name"],
        SupplyEntityType.INTENT: ["name"],
        SupplyEntityType.SLOT: ["name", "slot_type"],
        SupplyEntityType.CATEGORY: ["name"],
        SupplyEntityType.BRAND: ["name"],
        SupplyEntityType.SUPPLIER: ["name"],
        SupplyEntityType.MERCHANT: ["name"],
        SupplyEntityType.REGION: ["name"],
        SupplyEntityType.CHANNEL: ["name"],
        SupplyEntityType.POLICY: ["name"],
        SupplyEntityType.RISK_TAG: ["name"],
        SupplyEntityType.SKU: ["name"],
        SupplyEntityType.USER: ["name"],
    }

    # High-value relation types (should have good coverage)
    CORE_RELATION_TYPES: set[SupplyRelationType] = {
        SupplyRelationType.HAS_BRAND,
        SupplyRelationType.BELONGS_TO,
        SupplyRelationType.SUPPLIES,
        SupplyRelationType.SELLS,
        SupplyRelationType.PROVIDES_SERVICE,
        SupplyRelationType.HAS_INTENT,
    }

    def __init__(self, db: SupplyGraphDatabase | None = None):
        self.db = db or SupplyGraphDatabase()

    def evaluate_entity_quality(self) -> EntityQualityMetrics:
        """Evaluate entity quality metrics.

        Measures:
        - Completeness: percentage of entities with required properties
        - Name coverage: entities with names
        - Description coverage: entities with descriptions
        """
        metrics = EntityQualityMetrics()
        metrics.total_entities = self.db.count()

        if metrics.total_entities == 0:
            return metrics

        # Track by type
        for entity_type in SupplyEntityType:
            type_entities = self.db.query_by_type(entity_type)
            if not type_entities:
                continue

            type_metrics: dict[str, int] = {
                "total": len(type_entities),
                "with_name": 0,
                "with_description": 0,
                "complete": 0,
            }

            required_props = self.REQUIRED_PROPERTIES.get(entity_type, [])

            for entity in type_entities:
                # Name coverage
                if entity.name and entity.name != entity.id:
                    type_metrics["with_name"] += 1

                # Description coverage
                if entity.description:
                    type_metrics["with_description"] += 1

                # Required properties
                if required_props:
                    has_all_required = all(
                        entity.properties.get(prop) is not None
                        for prop in required_props
                    )
                    if has_all_required:
                        type_metrics["complete"] += 1

            metrics.by_type[entity_type.value] = type_metrics

        # Aggregate
        total_with_name = sum(m.get("with_name", 0) for m in metrics.by_type.values())
        total_with_desc = sum(m.get("with_description", 0) for m in metrics.by_type.values())
        total_complete = sum(m.get("complete", 0) for m in metrics.by_type.values())

        metrics.entities_with_name = total_with_name
        metrics.entities_with_description = total_with_desc
        metrics.entities_with_required_props = total_complete

        # Calculate completeness score (0-1)
        if metrics.total_entities > 0:
            name_score = total_with_name / metrics.total_entities
            desc_score = total_with_desc / metrics.total_entities * 0.3  # Lower weight
            required_score = total_complete / metrics.total_entities * 0.5  # Higher weight
            metrics.completeness_score = min(1.0, name_score + desc_score + required_score)

        return metrics

    def evaluate_relation_quality(self) -> RelationQualityMetrics:
        """Evaluate relation quality metrics.

        Measures:
        - Confidence distribution
        - Coverage by relation type
        - Orphan entities (no relations)
        """
        metrics = RelationQualityMetrics()
        metrics.total_relations = self.db.count_relations()

        # Find orphan entities (no incoming or outgoing relations)
        # This needs to run even when there are no relations
        connected_entities: set[str] = set()
        for relation in self.db._relations:
            connected_entities.add(relation.source_id)
            connected_entities.add(relation.target_id)

        metrics.orphan_entities = [
            eid for eid in self.db._entities
            if eid not in connected_entities
        ]

        if metrics.total_relations == 0:
            return metrics

        # Calculate confidence for all relations
        confidences = []
        relation_type_counts: dict[str, int] = {}

        for relation in self.db._relations:
            confidence = self.db.calculate_relation_confidence(relation)
            confidences.append(confidence)

            # Count by type
            rel_type = relation.relation_type.value
            relation_type_counts[rel_type] = relation_type_counts.get(rel_type, 0) + 1

            # High/low confidence threshold
            if confidence >= 0.7:
                metrics.high_confidence_count += 1
            else:
                metrics.low_confidence_count += 1

        metrics.coverage_by_type = relation_type_counts
        metrics.avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return metrics

    def evaluate_graph_structure(self) -> GraphMetrics:
        """Evaluate graph structural metrics.

        Measures:
        - Density: actual edges / possible edges
        - Average degree
        - Connected components
        - Isolated entities
        - Entity/relation type distributions
        """
        metrics = GraphMetrics()
        metrics.total_entities = self.db.count()
        metrics.total_relations = self.db.count_relations()

        if metrics.total_entities == 0:
            return metrics

        # Type distributions
        for entity_type in SupplyEntityType:
            count = self.db.count(entity_type)
            if count > 0:
                metrics.entity_type_distribution[entity_type.value] = count

        for relation_type in SupplyRelationType:
            count = self.db.count_relations(relation_type)
            if count > 0:
                metrics.relation_type_distribution[relation_type.value] = count

        # Calculate average degree
        total_degree = sum(self.db.get_degree(eid) for eid in self.db._entities)
        metrics.avg_degree = total_degree / metrics.total_entities

        # Calculate density
        # For undirected graph: density = 2 * E / (V * (V - 1))
        max_edges = metrics.total_entities * (metrics.total_entities - 1)
        if max_edges > 0:
            metrics.density = (2 * metrics.total_relations) / max_edges

        # Find connected components using BFS
        visited: set[str] = set()
        components: list[set[str]] = []

        for entity_id in self.db._entities:
            if entity_id in visited:
                continue

            # BFS to find component
            component: set[str] = set()
            queue = [entity_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.add(current)

                # Add neighbors
                for neighbor in self.db.get_neighbors(current):
                    if neighbor.id not in visited:
                        queue.append(neighbor.id)

            components.append(component)

        metrics.connected_components = len(components)
        metrics.largest_component_size = max(len(c) for c in components) if components else 0
        metrics.isolated_entities = sum(1 for c in components if len(c) == 1)

        return metrics

    def benchmark_performance(
        self,
        iterations: int = 100,
    ) -> PerformanceMetrics:
        """Benchmark query and operation performance.

        Tests:
        - Query by type
        - Property queries
        - Text search
        - Path finding
        - Batch operations
        """
        metrics = PerformanceMetrics()

        # Benchmark: query_by_type
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            for entity_type in SupplyEntityType:
                self.db.query_by_type(entity_type)
            end = time.perf_counter()
            times.append((end - start) * 1000)
        metrics.query_latency_ms["query_by_type_avg"] = sum(times) / len(times)

        # Benchmark: query_by_property
        times = []
        for _ in range(min(iterations, 20)):  # Fewer iterations for more complex query
            start = time.perf_counter()
            self.db.query_by_property(SupplyEntityType.PRODUCT, "category", "electronics")
            end = time.perf_counter()
            times.append((end - start) * 1000)
        metrics.query_latency_ms["query_by_property_avg"] = sum(times) / len(times)

        # Benchmark: search
        times = []
        for _ in range(min(iterations, 20)):
            start = time.perf_counter()
            self.db.search("product")
            end = time.perf_counter()
            times.append((end - start) * 1000)
        metrics.query_latency_ms["search_avg"] = sum(times) / len(times)

        # Benchmark: get_neighbors
        entity_ids = list(self.db._entities.keys())
        times = []
        for _ in range(iterations):
            if entity_ids:
                entity_id = entity_ids[len(times) % len(entity_ids)]
                start = time.perf_counter()
                self.db.get_neighbors(entity_id)
                end = time.perf_counter()
                times.append((end - start) * 1000)
        if times:
            metrics.query_latency_ms["get_neighbors_avg"] = sum(times) / len(times)

        # Benchmark: path finding (if we have enough entities)
        if len(entity_ids) >= 2:
            times = []
            for i in range(min(iterations, 10)):
                if len(entity_ids) > 1:
                    source = entity_ids[i % len(entity_ids)]
                    target = entity_ids[(i + 1) % len(entity_ids)]
                    start = time.perf_counter()
                    self.db.find_shortest_path(source, target)
                    end = time.perf_counter()
                    times.append((end - start) * 1000)
            if times:
                metrics.path_finding_avg_ms = sum(times) / len(times)

        # Calculate throughput
        if metrics.query_latency_ms.get("query_by_type_avg"):
            metrics.throughput_ops_per_sec["query_by_type"] = (
                1000 / metrics.query_latency_ms["query_by_type_avg"]
            )

        return metrics

    def evaluate(self) -> EvaluationResult:
        """Run complete evaluation.

        Returns all metrics in a single result object.
        """
        result = EvaluationResult()
        result.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        result.entity_quality = self.evaluate_entity_quality()
        result.relation_quality = self.evaluate_relation_quality()
        result.graph_metrics = self.evaluate_graph_structure()
        result.performance = self.benchmark_performance()

        return result

    def get_quality_score(self) -> float:
        """Get overall quality score (0-100).

        Combines entity quality, relation quality, and graph structure.
        """
        entity_metrics = self.evaluate_entity_quality()
        relation_metrics = self.evaluate_relation_quality()
        graph_metrics = self.evaluate_graph_structure()

        # Weighted average
        entity_score = entity_metrics.completeness_score * 40

        # Relation quality score based on confidence
        if relation_metrics.total_relations > 0:
            confidence_score = (
                relation_metrics.avg_confidence * 30 +
                (relation_metrics.high_confidence_count / relation_metrics.total_relations) * 30
            )
        else:
            confidence_score = 0

        # Graph structure score
        graph_score = 0
        if graph_metrics.total_entities > 0:
            density_score = min(1.0, graph_metrics.density * 100) * 15
            connectivity_score = (
                graph_metrics.largest_component_size / graph_metrics.total_entities
            ) * 15 if graph_metrics.total_entities > 0 else 0
            graph_score = density_score + connectivity_score

        total = entity_score + confidence_score + graph_score
        return min(100.0, total)

    def get_recommendations(self) -> list[str]:
        """Get recommendations for improving graph quality.

        Analyzes metrics and suggests improvements.
        """
        recommendations = []

        # Entity quality recommendations
        entity_metrics = self.evaluate_entity_quality()
        if entity_metrics.total_entities > 0:
            name_coverage = entity_metrics.entities_with_name / entity_metrics.total_entities
            if name_coverage < 0.8:
                recommendations.append(
                    f"Low name coverage ({name_coverage:.1%}). Add names to entities."
                )

            desc_coverage = entity_metrics.entities_with_description / entity_metrics.total_entities
            if desc_coverage < 0.5:
                recommendations.append(
                    f"Low description coverage ({desc_coverage:.1%}). Add descriptions."
                )

        # Relation quality recommendations
        relation_metrics = self.evaluate_relation_quality()
        if relation_metrics.total_relations == 0:
            recommendations.append("No relations in graph. Add entity relationships.")
        elif relation_metrics.orphan_entities:
            recommendations.append(
                f"Found {len(relation_metrics.orphan_entities)} orphan entities. "
                "Connect them to the main graph."
            )

        # Graph structure recommendations
        graph_metrics = self.evaluate_graph_structure()
        if graph_metrics.density < 0.01:
            recommendations.append(
                f"Low graph density ({graph_metrics.density:.4f}). "
                "Consider adding more relations."
            )

        if graph_metrics.connected_components > 1:
            recommendations.append(
                f"Graph has {graph_metrics.connected_components} connected components. "
                "Consider linking them."
            )

        if graph_metrics.isolated_entities > 0:
            recommendations.append(
                f"Found {graph_metrics.isolated_entities} isolated entities. "
                "Remove or connect them."
            )

        # Relation type coverage
        missing_core_relations = []
        for rel_type in self.CORE_RELATION_TYPES:
            count = relation_metrics.coverage_by_type.get(rel_type.value, 0)
            if count == 0:
                missing_core_relations.append(rel_type.value)

        if missing_core_relations:
            recommendations.append(
                f"Missing core relation types: {', '.join(missing_core_relations)}"
            )

        return recommendations


class GraphBenchmark:
    """Benchmark utilities for stress testing the knowledge graph.

    Provides utilities for:
    - Generating test data
    - Load testing
    - Memory profiling
    """

    def __init__(self, db: SupplyGraphDatabase | None = None):
        self.db = db or SupplyGraphDatabase()

    def generate_test_data(
        self,
        num_products: int = 100,
        num_categories: int = 20,
        num_brands: int = 30,
        num_merchants: int = 10,
    ) -> dict[str, Any]:
        """Generate test data for benchmarking.

        Creates a realistic supply graph with products, categories,
        brands, and merchants.
        """
        data: dict[str, list[dict]] = {
            "categories": [],
            "brands": [],
            "merchants": [],
            "products": [],
        }

        # Create categories
        categories = ["Electronics", "Clothing", "Food", "Home", "Sports"]
        for i, cat in enumerate(categories):
            data["categories"].append({
                "id": f"category_{i}",
                "name": cat,
                "description": f"{cat} products",
            })

        # Create brands
        for i in range(num_brands):
            data["brands"].append({
                "id": f"brand_{i}",
                "name": f"Brand {i}",
                "country": "US" if i % 2 == 0 else "CN",
            })

        # Create merchants
        for i in range(num_merchants):
            data["merchants"].append({
                "id": f"merchant_{i}",
                "name": f"Merchant {i}",
                "rating": 4.5,
            })

        # Create products
        import random
        for i in range(num_products):
            product = {
                "id": f"product_{i}",
                "name": f"Product {i}",
                "description": f"Description for product {i}",
                "price": round(random.uniform(10, 1000), 2),
                "category": f"category_{i % len(categories)}",
                "brand": f"brand_{i % num_brands}",
                "merchant": f"merchant_{i % num_merchants}",
            }
            data["products"].append(product)

        return data

    def run_benchmark(
        self,
        num_products: int = 1000,
    ) -> dict[str, Any]:
        """Run complete benchmark with test data.

        Returns timing and quality metrics.
        """
        import random
        from multi_agent_system.knowledge.supply_ingestion import (
            SupplyGraphIngestionPipeline,
            BatchConfig,
        )

        # Generate data
        data = self.generate_test_data(
            num_products=num_products,
            num_categories=50,
            num_brands=100,
            num_merchants=50,
        )

        # Benchmark ingestion
        pipeline = SupplyGraphIngestionPipeline(self.db)
        config = BatchConfig(
            skip_duplicates=True,
            normalize_names=True,
            create_relations=True,
        )

        start = time.perf_counter()
        result = pipeline.ingest_full_schema(data, config)
        ingestion_time = (time.perf_counter() - start) * 1000

        # Run evaluation
        evaluator = SupplyGraphEvaluator(self.db)
        eval_result = evaluator.evaluate()

        return {
            "ingestion": {
                "time_ms": ingestion_time,
                "entities_created": result.created,
                "entities_updated": result.updated,
                "entities_skipped": result.skipped,
                "errors": result.errors,
            },
            "graph_stats": {
                "total_entities": eval_result.graph_metrics.total_entities,
                "total_relations": eval_result.graph_metrics.total_relations,
                "density": eval_result.graph_metrics.density,
                "avg_degree": eval_result.graph_metrics.avg_degree,
            },
            "quality": {
                "entity_completeness": eval_result.entity_quality.completeness_score,
                "relation_confidence": eval_result.relation_quality.avg_confidence,
                "overall_score": evaluator.get_quality_score(),
            },
            "performance": {
                "query_by_type_ms": eval_result.performance.query_latency_ms.get("query_by_type_avg", 0),
                "search_ms": eval_result.performance.query_latency_ms.get("search_avg", 0),
            },
        }
