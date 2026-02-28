"""Report generation module for multi-agent system.

This module provides report generation capabilities for various types of analysis:
- Test Analysis: Test results and coverage reports
- KG Health: Knowledge Graph health and quality metrics
- Benchmark: Performance benchmark results
- Experiment: A/B testing and experiment results

Supports multiple output formats: Markdown, JSON, HTML
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ReportType(Enum):
    """Supported report types."""
    TEST_ANALYSIS = "test"
    KG_HEALTH = "kg"
    BENCHMARK = "benchmark"
    EXPERIMENT = "experiment"


class ReportFormat(Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


@dataclass
class ReportMetadata:
    """Metadata for a report."""
    title: str
    report_type: ReportType
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    author: str = "Multi-Agent System"
    tags: list[str] = field(default_factory=list)


class ReportFormatter(ABC):
    """Abstract base class for report formatters."""
    
    @abstractmethod
    def format(self, metadata: ReportMetadata, data: dict[str, Any]) -> str:
        """Format report with given metadata and data."""
        pass


class MarkdownFormatter(ReportFormatter):
    """Format reports as Markdown."""
    
    def format(self, metadata: ReportMetadata, data: dict[str, Any]) -> str:
        lines = []
        
        # Title
        lines.append(f"# {metadata.title}")
        lines.append("")
        
        # Metadata
        lines.append(f"**Report Type:** {metadata.report_type.value}")
        lines.append(f"**Generated:** {metadata.generated_at.isoformat()}")
        lines.append(f"**Version:** {metadata.version}")
        if metadata.author:
            lines.append(f"**Author:** {metadata.author}")
        if metadata.tags:
            lines.append(f"**Tags:** {', '.join(metadata.tags)}")
        lines.append("")
        
        # Content based on report type
        lines.extend(self._format_content(metadata.report_type, data))
        
        return "\n".join(lines)
    
    def _format_content(self, report_type: ReportType, data: dict[str, Any]) -> list[str]:
        """Format content based on report type."""
        lines = []
        
        if report_type == ReportType.TEST_ANALYSIS:
            lines.extend(self._format_test_analysis(data))
        elif report_type == ReportType.KG_HEALTH:
            lines.extend(self._format_kg_health(data))
        elif report_type == ReportType.BENCHMARK:
            lines.extend(self._format_benchmark(data))
        elif report_type == ReportType.EXPERIMENT:
            lines.extend(self._format_experiment(data))
        
        return lines
    
    def _format_test_analysis(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("## Summary")
            lines.append("")
            summary = data["summary"]
            lines.append(f"- **Total Tests:** {summary.get('total', 'N/A')}")
            lines.append(f"- **Passed:** {summary.get('passed', 'N/A')}")
            lines.append(f"- **Failed:** {summary.get('failed', 'N/A')}")
            lines.append(f"- **Skipped:** {summary.get('skipped', 'N/A')}")
            lines.append(f"- **Success Rate:** {summary.get('success_rate', 'N/A')}")
            lines.append("")
        
        if "coverage" in data:
            lines.append("## Coverage")
            lines.append("")
            coverage = data["coverage"]
            lines.append(f"- **Line Coverage:** {coverage.get('line', 'N/A')}%")
            lines.append(f"- **Branch Coverage:** {coverage.get('branch', 'N/A')}%")
            lines.append(f"- **Function Coverage:** {coverage.get('function', 'N/A')}%")
            lines.append("")
        
        if "failures" in data and data["failures"]:
            lines.append("## Failed Tests")
            lines.append("")
            for failure in data["failures"]:
                lines.append(f"### {failure.get('name', 'Unknown')}")
                lines.append(f"**Message:** {failure.get('message', 'N/A')}")
                if failure.get("traceback"):
                    lines.append("```")
                    lines.append(failure["traceback"])
                    lines.append("```")
                lines.append("")
        
        return lines
    
    def _format_kg_health(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("## Health Summary")
            lines.append("")
            summary = data["summary"]
            lines.append(f"- **Total Entities:** {summary.get('total_entities', 'N/A')}")
            lines.append(f"- **Total Relations:** {summary.get('total_relations', 'N/A')}")
            lines.append(f"- **Health Score:** {summary.get('health_score', 'N/A')}/100")
            lines.append("")
        
        if "issues" in data and data["issues"]:
            lines.append("## Issues")
            lines.append("")
            for issue in data["issues"]:
                severity = issue.get("severity", "unknown")
                lines.append(f"- **[{severity.upper()}]** {issue.get('description', 'N/A')}")
            lines.append("")
        
        if "metrics" in data:
            lines.append("## Detailed Metrics")
            lines.append("")
            metrics = data["metrics"]
            for key, value in metrics.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        return lines
    
    def _format_benchmark(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("## Benchmark Summary")
            lines.append("")
            summary = data["summary"]
            lines.append(f"- **Total Scenarios:** {summary.get('total_scenarios', 'N/A')}")
            lines.append(f"- **Total Runs:** {summary.get('total_runs', 'N/A')}")
            lines.append(f"- **Avg Duration:** {summary.get('avg_duration_ms', 'N/A')}ms")
            lines.append("")
        
        if "scenarios" in data:
            lines.append("## Scenario Results")
            lines.append("")
            lines.append("| Scenario | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) |")
            lines.append("|----------|----------|----------|----------|----------|")
            for scenario in data["scenarios"]:
                lines.append(
                    f"| {scenario.get('name', 'N/A')} | "
                    f"{scenario.get('avg_ms', 'N/A')} | "
                    f"{scenario.get('min_ms', 'N/A')} | "
                    f"{scenario.get('max_ms', 'N/A')} | "
                    f"{scenario.get('p95_ms', 'N/A')} |"
                )
            lines.append("")
        
        return lines
    
    def _format_experiment(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("## Experiment Summary")
            lines.append("")
            summary = data["summary"]
            lines.append(f"- **Experiment Name:** {summary.get('name', 'N/A')}")
            lines.append(f"- **Status:** {summary.get('status', 'N/A')}")
            lines.append(f"- **Start Date:** {summary.get('start_date', 'N/A')}")
            lines.append(f"- **End Date:** {summary.get('end_date', 'N/A')}")
            lines.append(f"- **Sample Size:** {summary.get('sample_size', 'N/A')}")
            lines.append("")
        
        if "metrics" in data:
            lines.append("## Key Metrics")
            lines.append("")
            metrics = data["metrics"]
            for metric_name, metric_data in metrics.items():
                lines.append(f"### {metric_name}")
                if isinstance(metric_data, dict):
                    for key, value in metric_data.items():
                        lines.append(f"- **{key}:** {value}")
                else:
                    lines.append(f"- **Value:** {metric_data}")
                lines.append("")
        
        if "conclusions" in data:
            lines.append("## Conclusions")
            lines.append("")
            for conclusion in data["conclusions"]:
                lines.append(f"- {conclusion}")
            lines.append("")
        
        return lines


class JSONFormatter(ReportFormatter):
    """Format reports as JSON."""
    
    def format(self, metadata: ReportMetadata, data: dict[str, Any]) -> str:
        report = {
            "metadata": {
                "title": metadata.title,
                "type": metadata.report_type.value,
                "generated_at": metadata.generated_at.isoformat(),
                "version": metadata.version,
                "author": metadata.author,
                "tags": metadata.tags,
            },
            "data": data,
        }
        return json.dumps(report, indent=2, ensure_ascii=False)


class HTMLFormatter(ReportFormatter):
    """Format reports as HTML."""
    
    def format(self, metadata: ReportMetadata, data: dict[str, Any]) -> str:
        html_parts = []
        
        # HTML header
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='en'>")
        html_parts.append("<head>")
        html_parts.append(f"<title>{metadata.title}</title>")
        html_parts.append("<style>")
        html_parts.append(self._get_css())
        html_parts.append("</style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        # Header
        html_parts.append("<header>")
        html_parts.append(f"<h1>{metadata.title}</h1>")
        html_parts.append("<div class='metadata'>")
        html_parts.append(f"<p><strong>Report Type:</strong> {metadata.report_type.value}</p>")
        html_parts.append(f"<p><strong>Generated:</strong> {metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html_parts.append(f"<p><strong>Version:</strong> {metadata.version}</p>")
        if metadata.tags:
            html_parts.append(f"<p><strong>Tags:</strong> {', '.join(metadata.tags)}</p>")
        html_parts.append("</div>")
        html_parts.append("</header>")
        
        # Content
        html_parts.append("<main>")
        html_parts.extend(self._format_content_html(metadata.report_type, data))
        html_parts.append("</main>")
        
        # Footer
        html_parts.append("<footer>")
        html_parts.append(f"<p>Generated by {metadata.author}</p>")
        html_parts.append("</footer>")
        
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _get_css(self) -> str:
        return """body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; } header { background: #2c3e50; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; } header h1 { margin: 0 0 20px 0; } .metadata { font-size: 14px; } .metadata p { margin: 5px 0; } main { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); } h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; } h3 { color: #34495e; } table { width: 100%; border-collapse: collapse; margin: 20px 0; } th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; } th { background: #3498db; color: white; } tr:hover { background: #f5f5f5; } ul { list-style-type: none; padding-left: 0; } li { padding: 8px 0; } .success { color: #27ae60; } .warning { color: #f39c12; } .error { color: #e74c3c; } footer { text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px; } code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Menlo', monospace; } pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }"""
    
    def _format_content_html(self, report_type: ReportType, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if report_type == ReportType.TEST_ANALYSIS:
            lines.extend(self._format_test_analysis_html(data))
        elif report_type == ReportType.KG_HEALTH:
            lines.extend(self._format_kg_health_html(data))
        elif report_type == ReportType.BENCHMARK:
            lines.extend(self._format_benchmark_html(data))
        elif report_type == ReportType.EXPERIMENT:
            lines.extend(self._format_experiment_html(data))
        
        return lines
    
    def _format_test_analysis_html(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("<section>")
            lines.append("<h2>Summary</h2>")
            summary = data["summary"]
            lines.append("<ul>")
            lines.append(f"<li><strong>Total Tests:</strong> {summary.get('total', 'N/A')}</li>")
            lines.append(f"<li><strong>Passed:</strong> <span class='success'>{summary.get('passed', 'N/A')}</span></li>")
            lines.append(f"<li><strong>Failed:</strong> <span class='error'>{summary.get('failed', 'N/A')}</span></li>")
            lines.append(f"<li><strong>Skipped:</strong> {summary.get('skipped', 'N/A')}</li>")
            lines.append(f"<li><strong>Success Rate:</strong> {summary.get('success_rate', 'N/A')}</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        if "coverage" in data:
            lines.append("<section>")
            lines.append("<h2>Coverage</h2>")
            coverage = data["coverage"]
            lines.append("<ul>")
            lines.append(f"<li><strong>Line Coverage:</strong> {coverage.get('line', 'N/A')}%</li>")
            lines.append(f"<li><strong>Branch Coverage:</strong> {coverage.get('branch', 'N/A')}%</li>")
            lines.append(f"<li><strong>Function Coverage:</strong> {coverage.get('function', 'N/A')}%</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        if "failures" in data and data["failures"]:
            lines.append("<section>")
            lines.append("<h2>Failed Tests</h2>")
            for failure in data["failures"]:
                lines.append(f"<h3>{failure.get('name', 'Unknown')}</h3>")
                lines.append(f"<p><strong>Message:</strong> {failure.get('message', 'N/A')}</p>")
                if failure.get("traceback"):
                    lines.append(f"<pre>{failure['traceback']}</pre>")
            lines.append("</section>")
        
        return lines
    
    def _format_kg_health_html(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("<section>")
            lines.append("<h2>Health Summary</h2>")
            summary = data["summary"]
            lines.append("<ul>")
            lines.append(f"<li><strong>Total Entities:</strong> {summary.get('total_entities', 'N/A')}</li>")
            lines.append(f"<li><strong>Total Relations:</strong> {summary.get('total_relations', 'N/A')}</li>")
            lines.append(f"<li><strong>Health Score:</strong> {summary.get('health_score', 'N/A')}/100</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        if "issues" in data and data["issues"]:
            lines.append("<section>")
            lines.append("<h2>Issues</h2>")
            lines.append("<ul>")
            for issue in data["issues"]:
                severity = issue.get("severity", "unknown")
                severity_class = "error" if severity == "critical" else "warning"
                lines.append(f"<li><span class='{severity_class}'>[{severity.upper()}]</span> {issue.get('description', 'N/A')}</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        if "metrics" in data:
            lines.append("<section>")
            lines.append("<h2>Detailed Metrics</h2>")
            metrics = data["metrics"]
            lines.append("<ul>")
            for key, value in metrics.items():
                lines.append(f"<li><strong>{key}:</strong> {value}</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        return lines
    
    def _format_benchmark_html(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("<section>")
            lines.append("<h2>Benchmark Summary</h2>")
            summary = data["summary"]
            lines.append("<ul>")
            lines.append(f"<li><strong>Total Scenarios:</strong> {summary.get('total_scenarios', 'N/A')}</li>")
            lines.append(f"<li><strong>Total Runs:</strong> {summary.get('total_runs', 'N/A')}</li>")
            lines.append(f"<li><strong>Avg Duration:</strong> {summary.get('avg_duration_ms', 'N/A')}ms</li>")
            lines.append("            lines.append("</ul>")
</section>")
        
        if "scenarios" in data:
            lines.append("<section>")
            lines.append("<h2>Scenario Results</h2>")
            lines.append("<table>")
            lines.append("<thead><tr><th>Scenario</th><th>Avg (ms)</th><th>Min (ms)</th><th>Max (ms)</th><th>P95 (ms)</th></tr></thead>")
            lines.append("<tbody>")
            for scenario in data["scenarios"]:
                lines.append(
                    f"<tr><td>{scenario.get('name', 'N/A')}</td>"
                    f"<td>{scenario.get('avg_ms', 'N/A')}</td>"
                    f"<td>{scenario.get('min_ms', 'N/A')}</td>"
                    f"<td>{scenario.get('max_ms', 'N/A')}</td>"
                    f"<td>{scenario.get('p95_ms', 'N/A')}</td></tr>"
                )
            lines.append("</tbody>")
            lines.append("</table>")
            lines.append("</section>")
        
        return lines
    
    def _format_experiment_html(self, data: dict[str, Any]) -> list[str]:
        lines = []
        
        if "summary" in data:
            lines.append("<section>")
            lines.append("<h2>Experiment Summary</h2>")
            summary = data["summary"]
            lines.append("<ul>")
            lines.append(f"<li><strong>Experiment Name:</strong> {summary.get('name', 'N/A')}</li>")
            lines.append(f"<li><strong>Status:</strong> {summary.get('status', 'N/A')}</li>")
            lines.append(f"<li><strong>Start Date:</strong> {summary.get('start_date', 'N/A')}</li>")
            lines.append(f"<li><strong>End Date:</strong> {summary.get('end_date', 'N/A')}</li>")
            lines.append(f"<li><strong>Sample Size:</strong> {summary.get('sample_size', 'N/A')}</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        if "metrics" in data:
            lines.append("<section>")
            lines.append("<h2>Key Metrics</h2>")
            metrics = data["metrics"]
            for metric_name, metric_data in metrics.items():
                lines.append(f"<h3>{metric_name}</h3>")
                if isinstance(metric_data, dict):
                    lines.append("<ul>")
                    for key, value in metric_data.items():
                        lines.append(f"<li><strong>{key}:</strong> {value}</li>")
                    lines.append("</ul>")
                else:
                    lines.append(f"<p><strong>Value:</strong> {metric_data}</p>")
            lines.append("</section>")
        
        if "conclusions" in data:
            lines.append("<section>")
            lines.append("<h2>Conclusions</h2>")
            lines.append("<ul>")
            for conclusion in data["conclusions"]:
                lines.append(f"<li>{conclusion}</li>")
            lines.append("</ul>")
            lines.append("</section>")
        
        return lines


class ReportGenerator:
    """Main report generator class.
    
    Generates reports for various types (test analysis, KG health, benchmark, experiment)
    in multiple formats (Markdown, JSON, HTML).
    
    Example:
        >>> generator = ReportGenerator()
        >>> report_data = {"summary": {"total": 10, "passed": 8, "failed": 2}}
        >>> content = generator.generate(
        ...     report_type=ReportType.TEST_ANALYSIS,
        ...     data=report_data,
        ...     format=ReportFormat.MARKDOWN,
        ...     title="Test Report"
        ... )
        >>> print(content)
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self._formatters: dict[ReportFormat, ReportFormatter] = {
            ReportFormat.MARKDOWN: MarkdownFormatter(),
            ReportFormat.JSON: JSONFormatter(),
            ReportFormat.HTML: HTMLFormatter(),
        }
    
    def generate(
        self,
        report_type: ReportType,
        data: dict[str, Any],
        format: ReportFormat = ReportFormat.MARKDOWN,
        title: str | None = None,
        version: str = "1.0.0",
        author: str = "Multi-Agent System",
        tags: list[str] | None = None,
    ) -> str:
        """Generate a report.
        
        Args:
            report_type: Type of report to generate
            data: Report data dictionary
            format: Output format (markdown, json, html)
            title: Report title (defaults to type name)
            version: Report version
            author: Report author
            tags: Optional list of tags
        
        Returns:
            Formatted report string
        """
        if title is None:
            title = f"{report_type.value.capitalize()} Report"
        
        metadata = ReportMetadata(
            title=title,
            report_type=report_type,
            version=version,
            author=author,
            tags=tags or [],
        )
        
        formatter = self._formatters.get(format)
        if formatter is None:
            raise ValueError(f"Unsupported format: {format}")
        
        return formatter.format(metadata, data)
    
    def generate_to_file(
        self,
        report_type: ReportType,
        data: dict[str, Any],
        output_path: str,
        format: ReportFormat | None = None,
        **kwargs,
    ) -> None:
        """Generate a report and save to file.
        
        Args:
            report_type: Type of report to generate
            data: Report data dictionary
            output_path: Path to save the report
            format: Output format (auto-detected from extension if not provided)
            **kwargs: Additional arguments passed to generate()
        """
        if format is None:
            ext = output_path.lower().split('.')[-1]
            format = {
                "md": ReportFormat.MARKDOWN,
                "markdown": ReportFormat.MARKDOWN,
                "json": ReportFormat.JSON,
                "html": ReportFormat.HTML,
            }.get(ext, ReportFormat.MARKDOWN)
        
        content = self.generate(report_type, data, format=format, **kwargs)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_supported_formats(self) -> list[ReportFormat]:
        """Get list of supported output formats."""
        return list(self._formatters.keys())


def load_report_data(file_path: str) -> dict[str, Any]:
    """Load report data from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary containing report data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
