"""Procedural Knowledge System based on "Procedural Knowledge Improves Agentic LLM Workflows".

Reference: Procedural Knowledge improves agentic LLM workflows by providing
domain-dependent procedural guidance for complex tasks.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ProcedureStep:
    """A single step in a procedure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    order: int = 0
    action: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    conditions: list[str] = field(default_factory=list)  # Preconditions
    expected_output: str = ""  # What this step should produce
    error_handling: str = ""  # How to handle errors


@dataclass
class Procedure:
    """A procedure representing a domain-specific workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: str = ""  # e.g., "finance", "medical", "engineering"
    description: str = ""
    version: str = "1.0"
    steps: list[ProcedureStep] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # Required inputs
    outputs: list[str] = field(default_factory=list)  # Expected outputs
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_step(self, step_id: str) -> ProcedureStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> list[str]:
        """Validate procedure structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.name:
            errors.append("Procedure name is required")

        if not self.steps:
            errors.append("Procedure must have at least one step")

        # Check for circular dependencies
        step_ids = {s.id for s in self.steps}
        for step in self.steps:
            for dep in step.depends_on if hasattr(step, 'depends_on') else []:
                if dep not in step_ids:
                    errors.append(f"Step {step.id} depends on unknown step {dep}")

        # Check step order
        orders = [s.order for s in self.steps]
        if len(orders) != len(set(orders)):
            errors.append("Step orders must be unique")

        return errors


class ProcedureRegistry:
    """Registry for managing procedures.

    Provides storage, retrieval, and versioning for procedures.
    """

    def __init__(self, storage_path: str = "./data/procedures") -> None:
        """Initialize procedure registry.

        Args:
            storage_path: Path to store procedure definitions
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._procedures: dict[str, Procedure] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all procedures from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    proc = self._deserialize_procedure(data)
                    self._procedures[proc.id] = proc
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    def _get_file_path(self, procedure_id: str) -> Path:
        """Get file path for procedure."""
        return self.storage_path / f"{procedure_id}.json"

    def _serialize_procedure(self, proc: Procedure) -> dict[str, Any]:
        """Serialize procedure to dict."""
        return {
            "id": proc.id,
            "name": proc.name,
            "domain": proc.domain,
            "description": proc.description,
            "version": proc.version,
            "steps": [
                {
                    "id": s.id,
                    "order": s.order,
                    "action": s.action,
                    "description": s.description,
                    "parameters": s.parameters,
                    "conditions": s.conditions,
                    "expected_output": s.expected_output,
                    "error_handling": s.error_handling,
                }
                for s in proc.steps
            ],
            "prerequisites": proc.prerequisites,
            "outputs": proc.outputs,
            "metadata": proc.metadata,
            "created_at": proc.created_at.isoformat(),
            "updated_at": proc.updated_at.isoformat(),
        }

    def _deserialize_procedure(self, data: dict[str, Any]) -> Procedure:
        """Deserialize procedure from dict."""
        steps = []
        for s in data.get("steps", []):
            step = ProcedureStep(
                id=s.get("id", ""),
                order=s.get("order", 0),
                action=s.get("action", ""),
                description=s.get("description", ""),
                parameters=s.get("parameters", {}),
                conditions=s.get("conditions", []),
                expected_output=s.get("expected_output", ""),
                error_handling=s.get("error_handling", ""),
            )
            steps.append(step)

        return Procedure(
            id=data.get("id", ""),
            name=data.get("name", ""),
            domain=data.get("domain", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            steps=steps,
            prerequisites=data.get("prerequisites", []),
            outputs=data.get("outputs", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
        )

    def register(self, procedure: Procedure) -> Procedure:
        """Register a procedure.

        Args:
            procedure: Procedure to register

        Returns:
            Registered procedure
        """
        procedure.updated_at = datetime.now()
        self._procedures[procedure.id] = procedure

        # Save to file
        file_path = self._get_file_path(procedure.id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._serialize_procedure(procedure), f, ensure_ascii=False, indent=2)

        return procedure

    def get(self, procedure_id: str) -> Procedure | None:
        """Get procedure by ID."""
        return self._procedures.get(procedure_id)

    def find_by_domain(self, domain: str) -> list[Procedure]:
        """Find procedures by domain."""
        return [p for p in self._procedures.values() if p.domain == domain]

    def find_by_name(self, name: str) -> list[Procedure]:
        """Find procedures by name (partial match)."""
        return [p for p in self._procedures.values() if name.lower() in p.name.lower()]

    def search(self, query: str) -> list[Procedure]:
        """Search procedures by query."""
        query_lower = query.lower()
        results = []
        for proc in self._procedures.values():
            if (query_lower in proc.name.lower() or
                query_lower in proc.description.lower() or
                query_lower in proc.domain.lower()):
                results.append(proc)
        return results

    def list_all(self) -> list[Procedure]:
        """List all procedures."""
        return list(self._procedures.values())

    def delete(self, procedure_id: str) -> bool:
        """Delete a procedure."""
        if procedure_id in self._procedures:
            del self._procedures[procedure_id]
            file_path = self._get_file_path(procedure_id)
            if file_path.exists():
                file_path.unlink()
            return True
        return False


class ProceduralKnowledge:
    """Procedural Knowledge system for guiding agent workflows.

    Provides:
    - Procedure storage and retrieval
    - Step-by-step guidance for complex tasks
    - Domain-specific workflow templates
    """

    def __init__(self, storage_path: str = "./data/procedures") -> None:
        """Initialize procedural knowledge system."""
        self.registry = ProcedureRegistry(storage_path)
        self._load_default_procedures()

    def _load_default_procedures(self) -> None:
        """Load default procedures if none exist."""
        if not self.registry.list_all():
            # Add some default procedures
            self._add_default_procedures()

    def _add_default_procedures(self) -> None:
        """Add default procedures."""
        # Research Paper Analysis Procedure
        research_proc = Procedure(
            name="Research Paper Analysis",
            domain="academic",
            description="Analyze and extract key information from research papers",
            steps=[
                ProcedureStep(
                    order=1,
                    action="extract_metadata",
                    description="Extract paper metadata (title, authors, year, venue)",
                    expected_output="Paper metadata dictionary",
                ),
                ProcedureStep(
                    order=2,
                    action="extract_abstract",
                    description="Extract and summarize abstract",
                    expected_output="Abstract summary",
                ),
                ProcedureStep(
                    order=3,
                    action="extract_methods",
                    description="Identify and describe research methodology",
                    expected_output="Methodology description",
                ),
                ProcedureStep(
                    order=4,
                    action="extract_results",
                    description="Extract key results and findings",
                    expected_output="Results summary",
                ),
                ProcedureStep(
                    order=5,
                    action="assess_quality",
                    description="Assess paper quality and validity",
                    expected_output="Quality assessment",
                ),
            ],
            prerequisites=["pdf_url or paper_text"],
            outputs=["metadata", "summary", "methodology", "results", "quality_score"],
        )
        self.registry.register(research_proc)

        # Code Review Procedure
        code_review_proc = Procedure(
            name="Code Review",
            domain="software_engineering",
            description="Perform comprehensive code review",
            steps=[
                ProcedureStep(
                    order=1,
                    action="parse_code",
                    description="Parse and understand code structure",
                    expected_output="Code AST/structure",
                ),
                ProcedureStep(
                    order=2,
                    action="check_style",
                    description="Check code style and conventions",
                    expected_output="Style violations list",
                ),
                ProcedureStep(
                    order=3,
                    action="check_security",
                    description="Check for security vulnerabilities",
                    expected_output="Security issues list",
                ),
                ProcedureStep(
                    order=4,
                    action="analyze_complexity",
                    description="Analyze code complexity",
                    expected_output="Complexity metrics",
                ),
                ProcedureStep(
                    order=5,
                    action="suggest_improvements",
                    description="Suggest improvements and refactoring",
                    expected_output="Improvement suggestions",
                ),
            ],
            prerequisites=["source_code"],
            outputs=["style_violations", "security_issues", "complexity", "suggestions"],
        )
        self.registry.register(code_review_proc)

    def get_guidance(self, procedure_id: str) -> list[dict[str, Any]]:
        """Get step-by-step guidance for a procedure.

        Args:
            procedure_id: Procedure ID

        Returns:
            List of guidance steps
        """
        proc = self.registry.get(procedure_id)
        if not proc:
            return []

        return [
            {
                "step": step.order,
                "action": step.action,
                "description": step.description,
                "expected_output": step.expected_output,
                "error_handling": step.error_handling,
            }
            for step in sorted(proc.steps, key=lambda s: s.order)
        ]

    def get_next_step(
        self,
        procedure_id: str,
        completed_steps: list[str],
    ) -> dict[str, Any] | None:
        """Get next step to execute based on completed steps.

        Args:
            procedure_id: Procedure ID
            completed_steps: List of completed step IDs

        Returns:
            Next step info or None if complete
        """
        proc = self.registry.get(procedure_id)
        if not proc:
            return None

        for step in sorted(proc.steps, key=lambda s: s.order):
            if step.id not in completed_steps:
                return {
                    "step_id": step.id,
                    "action": step.action,
                    "description": step.description,
                    "parameters": step.parameters,
                    "expected_output": step.expected_output,
                }

        return None  # All steps complete


# Global instance
_procedural_knowledge: ProceduralKnowledge | None = None


def get_procedural_knowledge(storage_path: str = "./data/procedures") -> ProceduralKnowledge:
    """Get global procedural knowledge instance."""
    global _procedural_knowledge
    if _procedural_knowledge is None:
        _procedural_knowledge = ProceduralKnowledge(storage_path)
    return _procedural_knowledge
