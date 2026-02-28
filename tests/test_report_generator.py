"""Tests for Report Generator Module."""

import json
import unittest
from datetime import datetime
from pathlib import Path

from multi_agent_system.reporting import (
    Report,
    ReportFormat,
    ReportGenerator,
    ReportSection,
    ReportType,
)


class TestReportType(unittest.TestCase):
    """Tests for ReportType enum."""

    def test_report_type_values(self):
        """Test all report type values."""
        self.assertEqual(ReportType.TEST_ANALYSIS.value, "test_analysis")
        self.assertEqual(ReportType.KG_HEALTH.value, "kg_health")
        self.assertEqual(ReportType.BENCHMARK.value, "benchmark")
        self.assertEqual(ReportType.EXPERIMENT.value, "experiment")

    def test_report_type_count(self):
        """Test we have exactly 4 report types."""
        self.assertEqual(len(ReportType), 4)


class TestReportFormat(unittest.TestCase):
    """Tests for ReportFormat enum."""

    def test_report_format_values(self):
        """Test all format values."""
        self.assertEqual(ReportFormat.MARKDOWN.value, "markdown")
        self.assertEqual(ReportFormat.JSON.value, "json")
        self.assertEqual(ReportFormat.HTML.value, "html")

    def test_report_format_count(self):
        """Test we have exactly 3 formats."""
        self.assertEqual(len(ReportFormat), 3)


class TestReportSection(unittest.TestCase):
    """Tests for ReportSection dataclass."""

    def test_create_section(self):
        """Test creating a section."""
        section = ReportSection(title="Test", content="Content")
        self.assertEqual(section.title, "Test")
        self.assertEqual(section.content, "Content")
        self.assertEqual(section.level, 2)

    def test_section_with_custom_level(self):
        """Test section with custom heading level."""
        section = ReportSection(title="Test", content="Content", level=3)
        self.assertEqual(section.level, 3)

    def test_section_metadata(self):
        """Test section metadata."""
        section = ReportSection(title="Test", content="Content", metadata={"key": "value"})
        self.assertEqual(section.metadata["key"], "value")

    def test_section_to_dict(self):
        """Test section serialization."""
        section = ReportSection(title="Test", content="Content", level=3)
        d = section.to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["content"], "Content")
        self.assertEqual(d["level"], 3)


class TestReport(unittest.TestCase):
    """Tests for Report dataclass."""

    def test_create_report(self):
        """Test creating a report."""
        report = Report(title="Test Report", report_type=ReportType.TEST_ANALYSIS)
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.report_type, ReportType.TEST_ANALYSIS)
        self.assertEqual(len(report.sections), 0)

    def test_add_section(self):
        """Test adding a section to report."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        section = report.add_section("Section 1", "Content 1")
        self.assertEqual(len(report.sections), 1)
        self.assertEqual(section.title, "Section 1")

    def test_report_to_dict(self):
        """Test report serialization."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        report.add_section("Section", "Content")
        d = report.to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["report_type"], "test_analysis")
        self.assertIn("created_at", d)


class TestReportGenerator(unittest.TestCase):
    """Tests for ReportGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = ReportGenerator()

    def test_create_report(self):
        """Test basic report creation."""
        report = self.generator.create_report(
            title="Test Report",
            report_type=ReportType.TEST_ANALYSIS,
        )
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.report_type, ReportType.TEST_ANALYSIS)

    def test_create_report_with_sections(self):
        """Test report creation with sections."""
        sections_data = [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"},
        ]
        report = self.generator.create_report(
            title="Test",
            report_type=ReportType.BENCHMARK,
            sections_data=sections_data,
        )
        self.assertEqual(len(report.sections), 2)

    def test_generate_markdown(self):
        """Test Markdown generation."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        report.add_section("Overview", "This is a test.")
        output = self.generator.generate(report, ReportFormat.MARKDOWN)
        self.assertIn("# Test", output)
        self.assertIn("## Overview", output)

    def test_generate_json(self):
        """Test JSON generation."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        output = self.generator.generate(report, ReportFormat.JSON)
        data = json.loads(output)
        self.assertEqual(data["title"], "Test")

    def test_generate_html(self):
        """Test HTML generation."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        report.add_section("Overview", "Test content.")
        output = self.generator.generate(report, ReportFormat.HTML)
        self.assertIn("<!DOCTYPE html>", output)
        self.assertIn("<h2>Overview</h2>", output)

    def test_generate_invalid_format(self):
        """Test invalid format raises error."""
        report = Report(title="Test", report_type=ReportType.TEST_ANALYSIS)
        with self.assertRaises(ValueError):
            self.generator.generate(report, "invalid")

    def test_test_analysis_report(self):
        """Test test analysis report creation."""
        test_results = {
            "passed": 8,
            "failed": 2,
            "details": [
                {"name": "test_1", "passed": True},
                {"name": "test_2", "passed": False},
            ],
        }
        output = self.generator.create_test_analysis_report(test_results)
        self.assertIn("Test Analysis Report", output)
        self.assertIn("80.0%", output)

    def test_kg_health_report(self):
        """Test KG health report creation."""
        health_data = {
            "node_count": 100,
            "edge_count": 500,
            "health_score": 85,
            "issues": ["Missing edges"],
            "recommendations": ["Add more nodes"],
        }
        output = self.generator.create_kg_health_report(health_data)
        self.assertIn("Knowledge Graph Health Report", output)
        self.assertIn("85", output)

    def test_benchmark_report(self):
        """Test benchmark report creation."""
        benchmark_data = {
            "results": [
                {"name": "latency", "value": 100, "unit": "ms"},
                {"name": "throughput", "value": 500, "unit": "req/s"},
            ],
            "duration": 10.5,
        }
        output = self.generator.create_benchmark_report(benchmark_data)
        self.assertIn("Benchmark Report", output)
        self.assertIn("10.50s", output)

    def test_experiment_report(self):
        """Test experiment report creation."""
        experiment_data = {
            "name": "Test Experiment",
            "status": "completed",
            "metrics": {"accuracy": 0.95, "f1": 0.92},
            "conclusions": "The model performs well.",
        }
        output = self.generator.create_experiment_report(experiment_data)
        self.assertIn("Experiment Report: Test Experiment", output)
        self.assertIn("accuracy", output)

    def test_report_with_metadata(self):
        """Test report includes metadata in output."""
        report = Report(
            title="Test",
            report_type=ReportType.TEST_ANALYSIS,
            metadata={"version": "1.0"},
        )
        output = self.generator.generate(report, ReportFormat.MARKDOWN)
        self.assertIn("version", output)


if __name__ == "__main__":
    unittest.main()
