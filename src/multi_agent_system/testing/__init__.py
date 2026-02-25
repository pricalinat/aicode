"""Testing module for multi-agent system."""

from .test_assistant import (
    TestAnalysisAssistant,
    TestCase,
    TestSuite,
    TestExecution,
    TestMetrics,
    Defect,
    TestPriority,
    TestStatus,
    TestType,
    AnalysisInsight,
    get_test_assistant,
)
from .samples import create_sample_tests
from .extended import (
    ExtendedTestAssistant,
    get_extended_test_assistant,
    # Coverage
    Requirement,
    CoverageReport,
    CoverageType,
    # Environment
    TestEnvironment,
    # Test Data
    TestData,
    # Risk
    RiskLevel,
    # Historical
    HistoricalRecord,
    TrendAnalysis,
)

__all__ = [
    # Base
    "TestAnalysisAssistant",
    "TestCase",
    "TestSuite",
    "TestExecution",
    "TestMetrics",
    "Defect",
    "TestPriority",
    "TestStatus",
    "TestType",
    "AnalysisInsight",
    "get_test_assistant",
    "create_sample_tests",
    # Extended
    "ExtendedTestAssistant",
    "get_extended_test_assistant",
    # Coverage
    "Requirement",
    "CoverageReport",
    "CoverageType",
    # Environment
    "TestEnvironment",
    # Test Data
    "TestData",
    # Risk
    "RiskLevel",
    # Historical
    "HistoricalRecord",
    "TrendAnalysis",
]
