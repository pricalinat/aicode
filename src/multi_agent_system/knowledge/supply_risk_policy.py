"""Risk and Policy Tagging Pipeline for Supply Knowledge Graph.

This module provides risk classification, policy rule evaluation, and automatic
tagging capabilities for e-commerce compliance.

Features:
- Risk category classification (REGULATORY, SAFETY, COMPLIANCE, QUALITY, etc.)
- Policy rule engine with configurable rules
- Automatic risk detection based on entity properties
- Policy compliance validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .supply_graph_database import SupplyGraphDatabase
from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)


class RiskCategory(Enum):
    """Categories of risk that can be assigned to entities."""
    REGULATORY = "regulatory"  # Legal/regulatory compliance
    SAFETY = "safety"  # Product safety concerns
    COMPLIANCE = "compliance"  # Internal policy compliance
    QUALITY = "quality"  # Quality control issues
    FINANCIAL = "financial"  # Financial risk (pricing, payment)
    REPUTATIONAL = "reputational"  # Brand/reputation risk
    SUPPLY_CHAIN = "supply_chain"  # Supply chain disruption risk
    DATA_PRIVACY = "data_privacy"  # Data protection concerns


class RiskSeverity(Enum):
    """Severity levels for risk tags."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyAction(Enum):
    """Actions to take when a policy rule is triggered."""
    WARN = "warn"
    BLOCK = "block"
    TAG = "tag"
    FLAG = "flag"
    NOTIFY = "notify"


@dataclass
class RiskTag:
    """A risk tag applied to an entity."""
    category: RiskCategory
    severity: RiskSeverity
    description: str
    source: str  # How the tag was applied (manual, automatic, policy)
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """A policy rule for automatic risk detection."""
    name: str
    description: str
    entity_types: list[SupplyEntityType]  # Which entity types to evaluate
    condition: Callable[[SupplyEntity, SupplyGraphDatabase], bool]  # Rule condition
    risk_category: RiskCategory
    severity: RiskSeverity
    action: PolicyAction
    message: str  # Message when rule is triggered


@dataclass
class PolicyEvaluationResult:
    """Result of evaluating a policy rule."""
    rule_name: str
    triggered: bool
    entity_id: str
    risk_tag: RiskTag | None = None
    message: str = ""


@dataclass
class ComplianceReport:
    """Report summarizing compliance status."""
    total_entities: int = 0
    entities_with_risks: int = 0
    risks_by_category: dict[RiskCategory, int] = field(default_factory=dict)
    risks_by_severity: dict[RiskSeverity, int] = field(default_factory=dict)
    policy_violations: list[PolicyEvaluationResult] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class RiskPolicyTagger:
    """Risk and policy tagging engine for supply knowledge graph.

    Provides:
    - Risk classification
    - Policy rule evaluation
    - Automatic risk detection
    - Compliance reporting
    """

    def __init__(self, db: SupplyGraphDatabase | None = None):
        self.db = db or SupplyGraphDatabase()
        self._risk_tags: dict[str, list[RiskTag]] = {}  # entity_id -> risk tags
        self._policy_rules: list[PolicyRule] = []
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default policy rules for e-commerce compliance."""

        # Rule: High-value products need compliance verification
        def high_value_check(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            price = entity.properties.get("price", 0)
            return price is not None and float(price) > 10000

        self._policy_rules.append(PolicyRule(
            name="high_value_requires_compliance",
            description="Products over 10000 require compliance verification",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=high_value_check,
            risk_category=RiskCategory.COMPLIANCE,
            severity=RiskSeverity.MEDIUM,
            action=PolicyAction.TAG,
            message="High-value product requires compliance verification",
        ))

        # Rule: Age-restricted products need safety review
        def age_restricted_check(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            return entity.properties.get("age_restricted", False) is True

        self._policy_rules.append(PolicyRule(
            name="age_restricted_needs_safety",
            description="Age-restricted products require safety review",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=age_restricted_check,
            risk_category=RiskCategory.SAFETY,
            severity=RiskSeverity.HIGH,
            action=PolicyAction.TAG,
            message="Age-restricted product requires safety review",
        ))

        # Rule: Products from new suppliers need verification
        def new_supplier_check(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            established = entity.properties.get("established_years", 0)
            return established is not None and int(established) < 2

        self._policy_rules.append(PolicyRule(
            name="new_supplier_verification",
            description="Products from new suppliers need verification",
            entity_types=[SupplyEntityType.SUPPLIER],
            condition=new_supplier_check,
            risk_category=RiskCategory.SUPPLY_CHAIN,
            severity=RiskSeverity.MEDIUM,
            action=PolicyAction.FLAG,
            message="New supplier requires verification",
        ))

        # Rule: International products need regulatory review
        def international_check(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            origin = entity.properties.get("origin", "")
            return origin not in ("", "domestic", "local")

        self._policy_rules.append(PolicyRule(
            name="international_needs_regulatory",
            description="International products need regulatory review",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=international_check,
            risk_category=RiskCategory.REGULATORY,
            severity=RiskSeverity.MEDIUM,
            action=PolicyAction.TAG,
            message="International product requires regulatory review",
        ))

        # Rule: Food/health products need quality check
        def health_category_check(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            category = entity.properties.get("category", "").lower()
            return category in ("food", "health", "supplements", "cosmetics", "medical")

        self._policy_rules.append(PolicyRule(
            name="health_product_quality",
            description="Health-related products need quality verification",
            entity_types=[SupplyEntityType.PRODUCT],
            condition=health_category_check,
            risk_category=RiskCategory.QUALITY,
            severity=RiskSeverity.HIGH,
            action=PolicyAction.TAG,
            message="Health product requires quality verification",
        ))

        # Rule: Missing required fields is a compliance risk
        def missing_required_fields(entity: SupplyEntity, db: SupplyGraphDatabase) -> bool:
            required = ["name", "category"]
            return not all(entity.properties.get(f) for f in required)

        self._policy_rules.append(PolicyRule(
            name="required_fields_missing",
            description="Entities must have required fields",
            entity_types=[SupplyEntityType.PRODUCT, SupplyEntityType.SERVICE],
            condition=missing_required_fields,
            risk_category=RiskCategory.COMPLIANCE,
            severity=RiskSeverity.LOW,
            action=PolicyAction.WARN,
            message="Missing required fields",
        ))

    def add_policy_rule(self, rule: PolicyRule) -> None:
        """Add a custom policy rule."""
        self._policy_rules.append(rule)

    def remove_policy_rule(self, rule_name: str) -> bool:
        """Remove a policy rule by name."""
        for i, rule in enumerate(self._policy_rules):
            if rule.name == rule_name:
                self._policy_rules.pop(i)
                return True
        return False

    def tag_entity(
        self,
        entity_id: str,
        category: RiskCategory,
        severity: RiskSeverity,
        description: str,
        source: str = "manual",
        evidence: dict[str, Any] | None = None,
    ) -> RiskTag:
        """Manually tag an entity with a risk category."""
        tag = RiskTag(
            category=category,
            severity=severity,
            description=description,
            source=source,
            evidence=evidence or {},
        )

        if entity_id not in self._risk_tags:
            self._risk_tags[entity_id] = []
        self._risk_tags[entity_id].append(tag)

        # Also create a RISK_TAG entity in the graph
        risk_entity = SupplyEntity(
            id=f"risk_{entity_id}_{category.value}_{severity.value}",
            type=SupplyEntityType.RISK_TAG,
            properties={
                "name": f"{category.value} - {severity.value}",
                "description": description,
                "severity": severity.value,
                "source": source,
            },
        )

        # Create HAS_RISK relation if entity exists
        entity = self.db.get_entity(entity_id)
        if entity:
            try:
                self.db.create_entity(risk_entity, validate=False)
                self.db.create_relation(SupplyRelation(
                    source_id=entity_id,
                    target_id=risk_entity.id,
                    relation_type=SupplyRelationType.HAS_RISK,
                    properties={"category": category.value},
                ), validate=False)
            except (ValueError, KeyError):
                pass  # Entity already exists

        return tag

    def untag_entity(self, entity_id: str, category: RiskCategory | None = None) -> int:
        """Remove risk tags from an entity.

        If category is specified, only removes tags of that category.
        Returns number of tags removed.
        """
        if entity_id not in self._risk_tags:
            return 0

        if category is None:
            count = len(self._risk_tags[entity_id])
            del self._risk_tags[entity_id]
            return count

        original_count = len(self._risk_tags[entity_id])
        self._risk_tags[entity_id] = [
            t for t in self._risk_tags[entity_id]
            if t.category != category
        ]
        return original_count - len(self._risk_tags[entity_id])

    def get_risk_tags(self, entity_id: str) -> list[RiskTag]:
        """Get all risk tags for an entity."""
        return self._risk_tags.get(entity_id, [])

    def evaluate_policies(
        self,
        entity_id: str | None = None,
        entity_types: list[SupplyEntityType] | None = None,
    ) -> list[PolicyEvaluationResult]:
        """Evaluate policy rules against entities.

        If entity_id is provided, only evaluates that entity.
        If entity_types is provided, only evaluates entities of those types.
        """
        results: list[PolicyEvaluationResult] = []

        # Determine which entities to evaluate
        entities_to_evaluate: list[SupplyEntity] = []

        if entity_id:
            entity = self.db.get_entity(entity_id)
            if entity:
                entities_to_evaluate = [entity]
        elif entity_types:
            for etype in entity_types:
                entities_to_evaluate.extend(self.db.query_by_type(etype))
        else:
            # Evaluate all entities
            for entity in self.db._entities.values():
                entities_to_evaluate.append(entity)

        # Evaluate each entity against relevant rules
        for entity in entities_to_evaluate:
            for rule in self._policy_rules:
                if entity.type not in rule.entity_types:
                    continue

                try:
                    triggered = rule.condition(entity, self.db)
                except Exception:
                    triggered = False

                if triggered:
                    tag = RiskTag(
                        category=rule.risk_category,
                        severity=rule.severity,
                        description=rule.message,
                        source="policy",
                        evidence={"rule": rule.name},
                    )
                    result = PolicyEvaluationResult(
                        rule_name=rule.name,
                        triggered=True,
                        entity_id=entity.id,
                        risk_tag=tag,
                        message=rule.message,
                    )
                    results.append(result)

                    # Apply automatic tagging if action is TAG
                    if rule.action == PolicyAction.TAG:
                        if entity.id not in self._risk_tags:
                            self._risk_tags[entity.id] = []
                        # Check if tag already exists
                        existing = [t for t in self._risk_tags[entity.id]
                                   if t.category == rule.risk_category]
                        if not existing:
                            self._risk_tags[entity.id].append(tag)

        return results

    def apply_automatic_tags(self, entity_id: str | None = None) -> int:
        """Apply automatic risk tags based on policy rules.

        Returns number of new tags applied.
        """
        if entity_id is not None:
            before_counts = {entity_id: len(self._risk_tags.get(entity_id, []))}
        else:
            before_counts = {
                eid: len(tags) for eid, tags in self._risk_tags.items()
            }

        self.evaluate_policies(entity_id=entity_id)

        if entity_id is not None:
            after_count = len(self._risk_tags.get(entity_id, []))
            return max(0, after_count - before_counts.get(entity_id, 0))

        total_new_tags = 0
        for eid, tags in self._risk_tags.items():
            before_count = before_counts.get(eid, 0)
            total_new_tags += max(0, len(tags) - before_count)
        return total_new_tags

    def generate_compliance_report(
        self,
        entity_types: list[SupplyEntityType] | None = None,
    ) -> ComplianceReport:
        """Generate a compliance report for the graph."""
        report = ComplianceReport()

        # Determine entities to include
        entities: list[SupplyEntity] = []
        if entity_types:
            for etype in entity_types:
                entities.extend(self.db.query_by_type(etype))
        else:
            entities = list(self.db._entities.values())

        report.total_entities = len(entities)

        # Evaluate policies
        policy_results = self.evaluate_policies(
            entity_types=entity_types,
        )
        report.policy_violations = [r for r in policy_results if r.triggered]

        # Count entities with risks
        entities_with_risks = set()
        for result in policy_results:
            if result.triggered:
                entities_with_risks.add(result.entity_id)
        report.entities_with_risks = len(entities_with_risks)

        # Aggregate risk counts
        for result in policy_results:
            if result.risk_tag:
                cat = result.risk_tag.category
                sev = result.risk_tag.severity
                report.risks_by_category[cat] = report.risks_by_category.get(cat, 0) + 1
                report.risks_by_severity[sev] = report.risks_by_severity.get(sev, 0) + 1

        # Generate recommendations
        if report.risks_by_severity.get(RiskSeverity.CRITICAL, 0) > 0:
            report.recommendations.append(
                "Critical risks identified - immediate action required"
            )
        if report.risks_by_severity.get(RiskSeverity.HIGH, 0) > 0:
            report.recommendations.append(
                "High severity risks require review within 24 hours"
            )
        if RiskCategory.QUALITY in report.risks_by_category:
            count = report.risks_by_category[RiskCategory.QUALITY]
            report.recommendations.append(
                f"{count} quality issues found - verify product certifications"
            )
        if RiskCategory.REGULATORY in report.risks_by_category:
            count = report.risks_by_category[RiskCategory.REGULATORY]
            report.recommendations.append(
                f"{count} regulatory risks found - ensure compliance documentation"
            )

        return report

    def get_entities_by_risk(
        self,
        category: RiskCategory | None = None,
        severity: RiskSeverity | None = None,
    ) -> list[str]:
        """Get entity IDs that match the given risk criteria."""
        results: list[str] = []

        for entity_id, tags in self._risk_tags.items():
            for tag in tags:
                if category and tag.category != category:
                    continue
                if severity and tag.severity != severity:
                    continue
                if entity_id not in results:
                    results.append(entity_id)

        return results

    def get_high_risk_entities(self, min_severity: RiskSeverity = RiskSeverity.HIGH) -> list[str]:
        """Get entities with risk severity >= min_severity."""
        severity_order = [
            RiskSeverity.LOW,
            RiskSeverity.MEDIUM,
            RiskSeverity.HIGH,
            RiskSeverity.CRITICAL,
        ]
        min_index = severity_order.index(min_severity)

        results: list[str] = []
        for entity_id, tags in self._risk_tags.items():
            for tag in tags:
                if severity_order.index(tag.severity) >= min_index:
                    if entity_id not in results:
                        results.append(entity_id)

        return results


# Global instance
_global_tagger: RiskPolicyTagger | None = None


def get_risk_tagger() -> RiskPolicyTagger:
    """Get the global risk tagger instance."""
    global _global_tagger
    if _global_tagger is None:
        _global_tagger = RiskPolicyTagger()
    return _global_tagger


def set_risk_tagger(tagger: RiskPolicyTagger) -> None:
    """Set the global risk tagger instance."""
    global _global_tagger
    _global_tagger = tagger
