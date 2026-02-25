"""Extended Test Analysis Assistant - Additional Capabilities.

This module extends the test assistant with:
- Test planning and coverage analysis
- Historical trend analysis
- Test data management
- Environment management
- Report export (HTML, JSON, Markdown)
- Risk-based testing
- Test impact analysis
"""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .test_assistant import TestAnalysisAssistant


class CoverageType(Enum):
    """Types of test coverage."""
    REQUIREMENT = "requirement"
    CODE = "code"
    FEATURE = "feature"
    USER_STORY = "user_story"
    RISK = "risk"


class RiskLevel(Enum):
    """Risk levels for testing."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Requirement:
    """A requirement to be tested."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""

    # Coverage
    test_case_ids: list[str] = field(default_factory=list)
    covered: bool = False

    # Risk
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Status
    status: str = "active"  # active, deprecated, fulfilled

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestEnvironment:
    """Test environment configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""

    # Configuration
    base_url: str = ""
    api_url: str = ""

    # Environment variables
    variables: dict[str, str] = field(default_factory=dict)

    # Browser config (for E2E)
    browser: str = "chrome"
    viewport: str = "1920x1080"

    # Status
    status: str = "available"  # available, busy, down

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestData:
    """Test data for test cases."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""

    # Data
    data: dict[str, Any] = field(default_factory=dict)

    # Usage
    test_case_ids: list[str] = field(default_factory=list)

    # Privacy
    contains_pii: bool = False

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HistoricalRecord:
    """Historical test execution record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    test_case_id: str = ""

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: int = 0

    # Result
    status: str = ""
    passed: bool = False

    # Environment
    environment: str = ""


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    period: str = ""  # daily, weekly, monthly

    # Metrics over time
    pass_rates: list[float] = field(default_factory=list)
    execution_counts: list[int] = field(default_factory=list)
    failure_counts: list[int] = field(default_factory=list)

    # Analysis
    trend_direction: str = "stable"  # improving, degrading, stable
    change_percentage: float = 0.0

    # Predictions
    predicted_pass_rate: float = 0.0
    confidence: float = 0.0


@dataclass
class CoverageReport:
    """Test coverage report."""
    total_requirements: int = 0
    covered_requirements: int = 0
    coverage_percentage: float = 0.0

    # By priority
    critical_covered: int = 0
    critical_total: int = 0
    high_covered: int = 0
    high_total: int = 0

    # Gaps
    uncovered_items: list[str] = field(default_factory=list)


class TestPlanningMixin:
    """Test planning and coverage analysis capabilities."""

    def __init__(self) -> None:
        self._requirements: dict[str, Requirement] = {}
        self._environments: dict[str, TestEnvironment] = {}
        self._test_data: dict[str, TestData] = {}
        self._history: list[HistoricalRecord] = []

    # Requirements Management
    def add_requirement(
        self,
        name: str,
        description: str = "",
        risk_level: RiskLevel = RiskLevel.MEDIUM,
    ) -> Requirement:
        """Add a requirement."""
        req = Requirement(
            name=name,
            description=description,
            risk_level=risk_level,
        )
        self._requirements[req.id] = req
        return req

    def link_requirement_to_test(
        self,
        requirement_id: str,
        test_case_id: str,
    ) -> bool:
        """Link requirement to test case."""
        req = self._requirements.get(requirement_id)
        if not req:
            return False

        if test_case_id not in req.test_case_ids:
            req.test_case_ids.append(test_case_id)
            req.covered = True
        return True

    def get_coverage_report(self) -> CoverageReport:
        """Generate coverage report."""
        report = CoverageReport()
        report.total_requirements = len(self._requirements)

        covered = [r for r in self._requirements.values() if r.covered]
        report.covered_requirements = len(covered)

        if report.total_requirements > 0:
            report.coverage_percentage = len(covered) / report.total_requirements * 100

        # By priority
        critical = [r for r in self._requirements.values() if r.risk_level == RiskLevel.CRITICAL]
        report.critical_total = len(critical)
        report.critical_covered = sum(1 for r in critical if r.covered)

        high = [r for r in self._requirements.values() if r.risk_level == RiskLevel.HIGH]
        report.high_total = len(high)
        report.high_covered = sum(1 for r in high if r.covered)

        # Gaps
        uncovered = [r.name for r in self._requirements.values() if not r.covered]
        report.uncovered_items = uncovered[:10]

        return report

    # Environment Management
    def add_environment(
        self,
        name: str,
        base_url: str,
        **kwargs,
    ) -> TestEnvironment:
        """Add test environment."""
        env = TestEnvironment(
            name=name,
            base_url=base_url,
            **kwargs,
        )
        self._environments[env.id] = env
        return env

    def get_environment(self, env_id: str) -> TestEnvironment | None:
        """Get environment by ID."""
        return self._environments.get(env_id)

    # Test Data Management
    def add_test_data(
        self,
        name: str,
        data: dict[str, Any],
        contains_pii: bool = False,
    ) -> TestData:
        """Add test data."""
        td = TestData(
            name=name,
            data=data,
            contains_pii=contains_pii,
        )
        self._test_data[td.id] = td
        return td

    def get_test_data(self, data_id: str) -> TestData | None:
        """Get test data by ID."""
        return self._test_data.get(data_id)

    def anonymize_test_data(self, data_id: str) -> bool:
        """Anonymize test data containing PII."""
        td = self._test_data.get(data_id)
        if not td or not td.contains_pii:
            return False

        # Simple anonymization (in production, use proper library)
        for key in td.data:
            if any(pii in key.lower() for pii in ['email', 'phone', 'name', 'address']):
                td.data[key] = "***"

        td.contains_pii = False
        return True

    # Historical Tracking
    def record_execution(
        self,
        test_case_id: str,
        status: str,
        passed: bool,
        duration_seconds: int,
        environment: str = "",
    ) -> None:
        """Record test execution for trend analysis."""
        record = HistoricalRecord(
            test_case_id=test_case_id,
            status=status,
            passed=passed,
            duration_seconds=duration_seconds,
            environment=environment,
        )
        self._history.append(record)

        # Keep only last 1000 records
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

    def analyze_trends(self, days: int = 7) -> TrendAnalysis:
        """Analyze test execution trends."""
        analysis = TrendAnalysis(period=f"{days} days")

        # Get records for period
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self._history if r.timestamp > cutoff]

        if not recent:
            return analysis

        # Group by day
        by_day: dict[str, list[HistoricalRecord]] = {}
        for r in recent:
            day = r.timestamp.strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(r)

        # Calculate daily pass rates
        for day, records in sorted(by_day.items()):
            total = len(records)
            passed = sum(1 for r in records if r.passed)
            pass_rate = passed / total if total > 0 else 0

            analysis.pass_rates.append(pass_rate)
            analysis.execution_counts.append(total)
            analysis.failure_counts.append(total - passed)

        # Determine trend
        if len(analysis.pass_rates) >= 2:
            first = analysis.pass_rates[0]
            last = analysis.pass_rates[-1]
            change = (last - first) / first * 100 if first > 0 else 0

            analysis.change_percentage = change

            if change > 5:
                analysis.trend_direction = "improving"
            elif change < -5:
                analysis.trend_direction = "degrading"
            else:
                analysis.trend_direction = "stable"

        # Simple prediction (moving average)
        if analysis.pass_rates:
            analysis.predicted_pass_rate = sum(analysis.pass_rates) / len(analysis.pass_rates)
            analysis.confidence = 0.7

        return analysis


class ReportExportMixin:
    """Report export capabilities."""

    def export_json(self) -> str:
        """Export test data as JSON."""
        data = {
            "test_cases": [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "type": tc.test_type.value,
                    "priority": tc.priority.value,
                    "status": tc.status.value,
                    "pass_rate": tc.pass_rate,
                }
                for tc in self._test_cases.values()
            ],
            "metrics": {
                "total": len(self._test_cases),
                "passed": sum(1 for tc in self._test_cases.values() if tc.status.value == "passed"),
                "failed": sum(1 for tc in self._test_cases.values() if tc.status.value == "failed"),
            },
            "exported_at": datetime.now().isoformat(),
        }
        return json.dumps(data, indent=2)

    def export_markdown(self) -> str:
        """Export test report as Markdown."""
        lines = [
            "# Test Analysis Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
        ]

        # Metrics
        metrics = self.get_test_metrics()
        lines.extend([
            f"- **Total Tests**: {metrics.total_tests}",
            f"- **Passed**: {metrics.passed}",
            f"- **Failed**: {metrics.failed}",
            f"- **Pass Rate**: {metrics.pass_rate:.1%}",
            "",
            "## Test Cases",
            "",
        ])

        # Test cases by priority
        for priority in ["critical", "high", "medium", "low"]:
            cases = [
                tc for tc in self._test_cases.values()
                if tc.priority.value == priority
            ]
            if cases:
                lines.append(f"### {priority.title()} Priority")
                lines.append("")
                for tc in cases:
                    status_icon = "✅" if tc.status.value == "passed" else "❌" if tc.status.value == "failed" else "⏳"
                    lines.append(f"- {status_icon} {tc.name}")
                lines.append("")

        # Insights
        insights = self.analyze_results()
        if insights:
            lines.extend([
                "## AI Insights",
                "",
            ])
            for i, insight in enumerate(insights, 1):
                lines.extend([
                    f"### {i}. {insight.title}",
                    "",
                    f"**Category**: {insight.category}",
                    f"**Confidence**: {insight.confidence:.0%}",
                    "",
                    insight.description,
                    "",
                    "**Action Items**:",
                ])
                for action in insight.action_items:
                    lines.append(f"- {action}")
                lines.append("")

        return "\n".join(lines)

    def export_html(self) -> str:
        """Export test report as HTML."""
        metrics = self.get_test_metrics()
        insights = self.analyze_results()

        # Calculate colors
        pass_color = "green" if metrics.pass_rate >= 0.8 else "orange" if metrics.pass_rate >= 0.5 else "red"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric-card {{
            background: white; border: 1px solid #ddd;
            padding: 20px; border-radius: 8px; min-width: 150px;
        }}
        .metric-value {{ font-size: 32px; font-weight: bold; }}
        .pass-rate {{ color: {pass_color}; }}
        .insight {{
            background: #fff3cd; border-left: 4px solid #ffc107;
            padding: 15px; margin: 10px 0; border-radius: 4px;
        }}
        .critical {{ border-color: #dc3545; background: #f8d7da; }}
        .test-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .test-table th, .test-table td {{
            border: 1px solid #ddd; padding: 10px; text-align: left;
        }}
        .test-table th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-label">Total Tests</div>
            <div class="metric-value">{metrics.total_tests}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Passed</div>
            <div class="metric-value" style="color: green">{metrics.passed}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Failed</div>
            <div class="metric-value" style="color: red">{metrics.failed}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Pass Rate</div>
            <div class="metric-value pass-rate">{metrics.pass_rate:.1%}</div>
        </div>
    </div>

    <h2>📋 Test Cases</h2>
    <table class="test-table">
        <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Priority</th>
            <th>Status</th>
        </tr>
"""

        for tc in list(self._test_cases.values())[:20]:
            status_color = "green" if tc.status.value == "passed" else "red" if tc.status.value == "failed" else "gray"
            html += f"""
        <tr>
            <td>{tc.name}</td>
            <td>{tc.test_type.value}</td>
            <td>{tc.priority.value}</td>
            <td style="color: {status_color}">{tc.status.value}</td>
        </tr>
"""

        html += """
    </table>
"""

        if insights:
            html += """
    <h2>💡 AI Insights</h2>
"""
            for i, insight in enumerate(insights, 1):
                critical_class = "critical" if insight.category == "anomaly" else ""
                html += f"""
    <div class="insight {critical_class}">
        <h3>{i}. {insight.title}</h3>
        <p>{insight.description}</p>
        <p><strong>Confidence:</strong> {insight.confidence:.0%}</p>
        <p><strong>Actions:</strong></p>
        <ul>
"""
                for action in insight.action_items:
                    html += f"<li>{action}</li>\n"
                html += """
        </ul>
    </div>
"""

        html += """
</body>
</html>
"""
        return html


class RiskBasedTestingMixin:
    """Risk-based testing capabilities."""

    def calculate_risk_score(
        self,
        test_case_id: str,
    ) -> dict[str, Any]:
        """Calculate risk score for a test case."""
        tc = self._test_cases.get(test_case_id)
        if not tc:
            return {}

        # Risk factors
        factors = {
            "business_impact": 0.0,
            "failure_frequency": 0.0,
            "complexity": 0.0,
            "dependency_count": 0.0,
        }

        # Business impact based on priority
        priority_scores = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
        }
        factors["business_impact"] = priority_scores.get(tc.priority.value, 0.5)

        # Failure frequency
        if tc.execution_count > 0:
            factors["failure_frequency"] = tc.fail_count / tc.execution_count

        # Complexity based on steps
        factors["complexity"] = min(1.0, len(tc.steps) / 10)

        # Calculate weighted risk score
        weights = {"business_impact": 0.4, "failure_frequency": 0.3, "complexity": 0.3}
        risk_score = sum(
            factors[k] * weights[k]
            for k in weights
        )

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "test_case_id": test_case_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": factors,
        }

    def prioritize_by_risk(self) -> list[dict[str, Any]]:
        """Prioritize test cases by risk."""
        priorities = []

        for tc in self._test_cases.values():
            risk = self.calculate_risk_score(tc.id)
            priorities.append({
                "test_case": tc,
                **risk,
            })

        # Sort by risk score
        priorities.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

        return priorities


# Extended Test Analysis Assistant
class ExtendedTestAssistant(
    TestAnalysisAssistant,
    TestPlanningMixin,
    ReportExportMixin,
    RiskBasedTestingMixin,
):
    """Extended test analysis assistant with all capabilities."""

    def __init__(self) -> None:
        """Initialize extended assistant."""
        # Initialize all base classes
        TestAnalysisAssistant.__init__(self)
        TestPlanningMixin.__init__(self)
        ReportExportMixin.__init__(self)
        RiskBasedTestingMixin.__init__(self)


# Convenience function
def get_extended_test_assistant() -> ExtendedTestAssistant:
    """Get extended test assistant instance."""
    return ExtendedTestAssistant()
