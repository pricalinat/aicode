"""Unit tests for Supply Risk/Policy Tagging."""

import unittest

from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)
from multi_agent_system.knowledge.supply_risk_policy import (
    RiskCategory,
    RiskSeverity,
    RiskPolicyTagger,
    RiskTag,
    PolicyRule,
    PolicyAction,
    PolicyEvaluationResult,
    ComplianceReport,
)


class TestRiskPolicyTagger(unittest.TestCase):
    """Test cases for RiskPolicyTagger."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SupplyGraphDatabase()
        self.tagger = RiskPolicyTagger(self.db)

    def test_tag_entity(self):
        """Test manually tagging an entity with a risk."""
        # Create an entity first
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        # Tag the entity
        tag = self.tagger.tag_entity(
            entity_id="product_1",
            category=RiskCategory.SAFETY,
            severity=RiskSeverity.HIGH,
            description="Product safety concern",
            source="manual",
        )

        self.assertEqual(tag.category, RiskCategory.SAFETY)
        self.assertEqual(tag.severity, RiskSeverity.HIGH)

        # Check tags were stored
        tags = self.tagger.get_risk_tags("product_1")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].category, RiskCategory.SAFETY)

    def test_untag_entity(self):
        """Test removing risk tags from an entity."""
        # Create and tag an entity
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        self.tagger.tag_entity(
            entity_id="product_1",
            category=RiskCategory.SAFETY,
            severity=RiskSeverity.HIGH,
            description="Test tag",
        )

        # Untag
        count = self.tagger.untag_entity("product_1")
        self.assertEqual(count, 1)

        tags = self.tagger.get_risk_tags("product_1")
        self.assertEqual(len(tags), 0)

    def test_untag_specific_category(self):
        """Test removing tags of a specific category."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test Product"},
        )
        self.db.create_entity(entity)

        # Add two different category tags
        self.tagger.tag_entity(
            entity_id="product_1",
            category=RiskCategory.SAFETY,
            severity=RiskSeverity.HIGH,
            description="Safety tag",
        )
        self.tagger.tag_entity(
            entity_id="product_1",
            category=RiskCategory.QUALITY,
            severity=RiskSeverity.LOW,
            description="Quality tag",
        )

        # Only remove safety tags
        count = self.tagger.untag_entity("product_1", RiskCategory.SAFETY)
        self.assertEqual(count, 1)

        remaining = self.tagger.get_risk_tags("product_1")
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].category, RiskCategory.QUALITY)

    def test_high_value_product_rule(self):
        """Test high value product policy rule."""
        # Create a high-value product
        entity = SupplyEntity(
            id="expensive_product",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Expensive Item", "price": 15000},
        )
        self.db.create_entity(entity)

        # Evaluate policies
        results = self.tagger.evaluate_policies(entity_id="expensive_product")

        # Should trigger high_value_requires_compliance rule
        triggered = [r for r in results if r.triggered]
        self.assertTrue(len(triggered) > 0)
        rule_names = [r.rule_name for r in triggered]
        self.assertIn("high_value_requires_compliance", rule_names)

    def test_age_restricted_rule(self):
        """Test age-restricted product policy rule."""
        entity = SupplyEntity(
            id="alcohol_product",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Alcohol", "age_restricted": True},
        )
        self.db.create_entity(entity)

        results = self.tagger.evaluate_policies(entity_id="alcohol_product")

        triggered = [r for r in results if r.triggered]
        rule_names = [r.rule_name for r in triggered]
        self.assertIn("age_restricted_needs_safety", rule_names)

    def test_health_category_rule(self):
        """Test health category product policy rule."""
        entity = SupplyEntity(
            id="supplement",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Vitamin Supplement", "category": "health"},
        )
        self.db.create_entity(entity)

        results = self.tagger.evaluate_policies(entity_id="supplement")

        triggered = [r for r in results if r.triggered]
        rule_names = [r.rule_name for r in triggered]
        self.assertIn("health_product_quality", rule_names)

    def test_apply_automatic_tags(self):
        """Test automatic tag application."""
        # Create multiple products
        products = [
            SupplyEntity(
                id="expensive",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Expensive", "price": 20000},
            ),
            SupplyEntity(
                id="alcohol",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Alcohol", "age_restricted": True},
            ),
            SupplyEntity(
                id="normal",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Normal", "price": 50},
            ),
        ]
        for p in products:
            self.db.create_entity(p)

        # Apply automatic tags
        count = self.tagger.apply_automatic_tags()

        # Should have at least 2 tags (expensive + alcohol)
        self.assertGreaterEqual(count, 2)

    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        # Create products that trigger rules
        products = [
            SupplyEntity(
                id="expensive",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Expensive", "price": 20000},
            ),
            SupplyEntity(
                id="alcohol",
                type=SupplyEntityType.PRODUCT,
                properties={"name": "Alcohol", "age_restricted": True},
            ),
        ]
        for p in products:
            self.db.create_entity(p)

        # Generate report
        report = self.tagger.generate_compliance_report(
            entity_types=[SupplyEntityType.PRODUCT]
        )

        self.assertEqual(report.total_entities, 2)
        self.assertGreater(report.entities_with_risks, 0)
        self.assertGreater(len(report.policy_violations), 0)
        self.assertGreater(len(report.recommendations), 0)

    def test_get_entities_by_risk(self):
        """Test filtering entities by risk category/severity."""
        entity = SupplyEntity(
            id="product_1",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Test"},
        )
        self.db.create_entity(entity)

        self.tagger.tag_entity(
            entity_id="product_1",
            category=RiskCategory.SAFETY,
            severity=RiskSeverity.HIGH,
            description="Test",
        )

        # Query by category
        results = self.tagger.get_entities_by_risk(category=RiskCategory.SAFETY)
        self.assertIn("product_1", results)

        # Query by severity
        results = self.tagger.get_entities_by_risk(severity=RiskSeverity.HIGH)
        self.assertIn("product_1", results)

        # Query by non-matching category
        results = self.tagger.get_entities_by_risk(category=RiskCategory.FINANCIAL)
        self.assertNotIn("product_1", results)

    def test_get_high_risk_entities(self):
        """Test getting high-risk entities."""
        entity1 = SupplyEntity(
            id="high_risk",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "High Risk"},
        )
        entity2 = SupplyEntity(
            id="low_risk",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Low Risk"},
        )
        self.db.create_entity(entity1)
        self.db.create_entity(entity2)

        self.tagger.tag_entity(
            entity_id="high_risk",
            category=RiskCategory.SAFETY,
            severity=RiskSeverity.CRITICAL,
            description="Critical risk",
        )
        self.tagger.tag_entity(
            entity_id="low_risk",
            category=RiskCategory.QUALITY,
            severity=RiskSeverity.LOW,
            description="Low risk",
        )

        # Get HIGH and above
        high_risk = self.tagger.get_high_risk_entities(min_severity=RiskSeverity.HIGH)
        self.assertIn("high_risk", high_risk)
        self.assertNotIn("low_risk", high_risk)

    def test_add_custom_rule(self):
        """Test adding a custom policy rule."""

        def custom_condition(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            return entity.properties.get("custom_flag", False) is True

        rule = PolicyRule(
            name="custom_rule",
            description="Custom test rule",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=custom_condition,
            risk_category=RiskCategory.REPUTATIONAL,
            severity=RiskSeverity.MEDIUM,
            action=PolicyAction.TAG,
            message="Custom rule triggered",
        )

        self.tagger.add_policy_rule(rule)

        entity = SupplyEntity(
            id="flagged_product",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Flagged", "custom_flag": True},
        )
        self.db.create_entity(entity)

        results = self.tagger.evaluate_policies(entity_id="flagged_product")

        triggered = [r for r in results if r.rule_name == "custom_rule"]
        self.assertEqual(len(triggered), 1)

    def test_remove_policy_rule(self):
        """Test removing a policy rule."""
        # Try to remove a default rule
        result = self.tagger.remove_policy_rule("high_value_requires_compliance")
        self.assertTrue(result)

        # Verify it's removed by evaluating
        entity = SupplyEntity(
            id="expensive",
            type=SupplyEntityType.PRODUCT,
            properties={"name": "Expensive", "price": 20000},
        )
        self.db.create_entity(entity)

        results = self.tagger.evaluate_policies(entity_id="expensive")
        rule_names = [r.rule_name for r in results if r.triggered]

        self.assertNotIn("high_value_requires_compliance", rule_names)


class TestRiskTag(unittest.TestCase):
    """Test cases for RiskTag dataclass."""

    def test_risk_tag_creation(self):
        """Test creating a risk tag."""
        tag = RiskTag(
            category=RiskCategory.REGULATORY,
            severity=RiskSeverity.HIGH,
            description="Test risk",
            source="manual",
            evidence={"test": True},
        )

        self.assertEqual(tag.category, RiskCategory.REGULATORY)
        self.assertEqual(tag.severity, RiskSeverity.HIGH)
        self.assertEqual(tag.source, "manual")
        self.assertTrue(tag.evidence["test"])


class TestPolicyRule(unittest.TestCase):
    """Test cases for PolicyRule dataclass."""

    def test_policy_rule_creation(self):
        """Test creating a policy rule."""
        def condition(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            return True

        rule = PolicyRule(
            name="test_rule",
            description="Test description",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=condition,
            risk_category=RiskCategory.COMPLIANCE,
            severity=RiskSeverity.MEDIUM,
            action=PolicyAction.WARN,
            message="Test message",
        )

        self.assertEqual(rule.name, "test_rule")
        self.assertIn(SupplyEntityType.PRODUCT, rule.entity_types)
        self.assertEqual(rule.risk_category, RiskCategory.COMPLIANCE)


class TestComplianceReport(unittest.TestCase):
    """Test cases for ComplianceReport dataclass."""

    def test_compliance_report_creation(self):
        """Test creating a compliance report."""
        report = ComplianceReport(
            total_entities=10,
            entities_with_risks=3,
            risks_by_category={RiskCategory.SAFETY: 2, RiskCategory.QUALITY: 1},
            risks_by_severity={RiskSeverity.HIGH: 2, RiskSeverity.LOW: 1},
            policy_violations=[],
            recommendations=["Test recommendation"],
        )

        self.assertEqual(report.total_entities, 10)
        self.assertEqual(report.entities_with_risks, 3)
        self.assertEqual(report.risks_by_category[RiskCategory.SAFETY], 2)


if __name__ == "__main__":
    unittest.main()
