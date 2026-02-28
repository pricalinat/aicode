"""Report Generation Module for Multi-Agent System.

This module provides a reusable report generation framework supporting
multiple report types and output formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ReportType(Enum):
    """Supported report types."""
    TEST_ANALYSIS = "test_analysis"
    KG_HEALTH = "kg_health"
    BENCHMARK = "benchmark"
    EXPERIMENT = "experiment"


class ReportFormat(Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


@dataclass
class ReportSection:
    """A single section within a report."""
    title: str
    content: str
    level: int = 2  # Heading level for markdown/html
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "metadata": self.metadata,
        }


@dataclass
class Report:
    """Report data structure."""
    title: str
    report_type: ReportType
    created_at: datetime = field(default_factory=datetime.now)
    sections: list[ReportSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, title: str, content: str, level: int = 2, **metadata) -> ReportSection:
        """Add a section to the report."""
        section = ReportSection(title=title, content=content, level=level, metadata=metadata)
        self.sections.append(section)
        return section

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "report_type": self.report_type.value,
            "created_at": self.created_at.isoformat(),
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
        }


class ReportGenerator:
    """Generate reports in various formats and types."""

    def __init__(self):
        self._formatters = {
            ReportFormat.MARKDOWN: self._format_markdown,
            ReportFormat.JSON: self._format_json,
            ReportFormat.HTML: self._format_html,
        }

    def create_report(
        self,
        title: str,
        report_type: ReportType,
        sections_data: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Report:
        """Create a new report."""
        report = Report(
            title=title,
            report_type=report_type,
            metadata=metadata or {},
        )

        if sections_data:
            for section_data in sections_data:
                report.add_section(
                    title=section_data.get("title", ""),
                    content=section_data.get("content", ""),
                    level=section_data.get("level", 2),
                    **section_data.get("metadata", {}),
                )

        return report

    def generate(
        self,
        report: Report,
        output_format: ReportFormat,
    ) -> str:
        """Generate report in the specified format."""
        formatter = self._formatters.get(output_format)
        if not formatter:
            raise ValueError(f"Unsupported format: {output_format}")
        return formatter(report)

    def _format_markdown(self, report: Report) -> str:
        """Format report as Markdown."""
        lines = [
            f"# {report.title}",
            "",
            f"*Report Type: {report.report_type.value}*",
            f"*Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ]

        # Add metadata if present
        if report.metadata:
            lines.append("## Metadata")
            for key, value in report.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Add sections
        for section in report.sections:
            heading = "#" * section.level
            lines.append(f"{heading} {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def _format_json(self, report: Report) -> str:
        """Format report as JSON."""
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    def _format_html(self, report: Report) -> str:
        """Format report as HTML."""
        sections_html = ""
        for section in report.sections:
            sections_html += f"<h{section.level}>{section.title}</h{section.level}>\n"
            sections_html += f"<p>{section.content}</p>\n"

        metadata_html = ""
        if report.metadata:
            metadata_html = "<h2>Metadata</h2>\n<ul>\n"
            for key, value in report.metadata.items():
                metadata_html += f"<li><strong>{key}</strong>: {value}</li>\n"
            metadata_html += "</ul>\n"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .meta {{ color: #888; font-size: 0.9em; }}
        ul {{ background: #f9f9f9; padding: 15px 30px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <p class="meta">Report Type: {report.report_type.value}<br>
    Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    {metadata_html}
    {sections_html}
</body>
</html>"""
        return html

    # Convenience methods for common report types

    def create_test_analysis_report(
        self,
        test_results: dict[str, Any],
        output_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> str:
        """Create a test analysis report."""
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0

        sections = [
            {
                "title": "Summary",
                "content": f"Total: {total} | Passed: {passed} | Failed: {failed} | Pass Rate: {pass_rate:.1f}%",
            },
            {
                "title": "Test Details",
                "content": self._format_test_details(test_results.get("details", [])),
            },
        ]

        if test_results.get("errors"):
            sections.append({
                "title": "Errors",
                "content": "\n".join(f"- {e}" for e in test_results["errors"]),
            })

        report = self.create_report(
            title="Test Analysis Report",
            report_type=ReportType.TEST_ANALYSIS,
            sections_data=sections,
            metadata={"total": total, "passed": passed, "failed": failed},
        )

        return self.generate(report, output_format)

    def _format_test_details(self, details: list[dict]) -> str:
        """Format test details."""
        if not details:
            return "No test details available."
        lines = []
        for detail in details:
            status = "✓" if detail.get("passed") else "✗"
            name = detail.get("name", "Unknown")
            lines.append(f"- {status} {name}")
        return "\n".join(lines)

    def create_kg_health_report(
        self,
        health_data: dict[str, Any],
        output_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> str:
        """Create a knowledge graph health report."""
        node_count = health_data.get("node_count", 0)
        edge_count = health_data.get("edge_count", 0)
        health_score = health_data.get("health_score", 0)

        sections = [
            {
                "title": "Overview",
                "content": f"Nodes: {node_count} | Edges: {edge_count} | Health Score: {health_score}/100",
            },
        ]

        if health_data.get("issues"):
            sections.append({
                "title": "Issues",
                "content": "\n".join(f"- {issue}" for issue in health_data["issues"]),
            })

        if health_data.get("recommendations"):
            sections.append({
                "title": "Recommendations",
                "content": "\n".join(f"- {rec}" for rec in health_data["recommendations"]),
            })

        report = self.create_report(
            title="Knowledge Graph Health Report",
            report_type=ReportType.KG_HEALTH,
            sections_data=sections,
            metadata={
                "node_count": node_count,
                "edge_count": edge_count,
                "health_score": health_score,
            },
        )

        return self.generate(report, output_format)

    def create_benchmark_report(
        self,
        benchmark_data: dict[str, Any],
        output_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> str:
        """Create a benchmark report."""
        results = benchmark_data.get("results", [])
        duration = benchmark_data.get("duration", 0)

        sections = [
            {
                "title": "Summary",
                "content": f"Total Tests: {len(results)} | Duration: {duration:.2f}s",
            },
            {
                "title": "Results",
                "content": self._format_benchmark_results(results),
            },
        ]

        report = self.create_report(
            title="Benchmark Report",
            report_type=ReportType.BENCHMARK,
            sections_data=sections,
            metadata={"tests": len(results), "duration": duration},
        )

        return self.generate(report, output_format)

    def _format_benchmark_results(self, results: list[dict]) -> str:
        """Format benchmark results."""
        if not results:
            return "No benchmark results available."
        lines = []
        for r in results:
            name = r.get("name", "Unknown")
            value = r.get("value", 0)
            unit = r.get("unit", "")
            lines.append(f"- **{name}**: {value} {unit}")
        return "\n".join(lines)

    def create_experiment_report(
        self,
        experiment_data: dict[str, Any],
        output_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> str:
        """Create an experiment report."""
        name = experiment_data.get("name", "Unnamed Experiment")
        status = experiment_data.get("status", "unknown")
        metrics = experiment_data.get("metrics", {})

        sections = [
            {
                "title": "Experiment Overview",
                "content": f"Name: {name} | Status: {status}",
            },
            {
                "title": "Metrics",
                "content": self._format_metrics(metrics),
            },
        ]

        if experiment_data.get("conclusions"):
            sections.append({
                "title": "Conclusions",
                "content": experiment_data["conclusions"],
            })

        report = self.create_report(
            title=f"Experiment Report: {name}",
            report_type=ReportType.EXPERIMENT,
            sections_data=sections,
            metadata={"name": name, "status": status},
        )

        return self.generate(report, output_format)

    def _format_metrics(self, metrics: dict) -> str:
        """Format metrics."""
        if not metrics:
            return "No metrics available."
        lines = []
        for key, value in metrics.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)
