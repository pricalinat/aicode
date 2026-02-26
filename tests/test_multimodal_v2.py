"""Tests for V2 enhancements: multimodal, LLM judge, and cost/safety controls."""

import unittest

from multi_agent_system.ingestion import (
    DocumentChunker,
    KnowledgeChunk,
    MultiModalIngestor,
    SourceSpan,
)
from multi_agent_system.experiments import (
    CalibrationConfig,
    EvaluationBenchmark,
    EvaluationDimension,
    LlmJudgeEvaluator,
    LlmJudgeRubric,
    ScoreLevel,
)
from multi_agent_system.cost_safety import (
    AuditLogger,
    CostBudget,
    ModelRouter,
    ModelTier,
    ModelConfig,
    SafetyFilter,
)


class TestSourceSpan(unittest.TestCase):
    """Tests for SourceSpan."""

    def test_source_span_to_dict(self):
        span = SourceSpan(start_offset=10, end_offset=50, line_start=2, line_end=5, page=1)
        d = span.to_dict()
        self.assertEqual(d["start_offset"], 10)
        self.assertEqual(d["end_offset"], 50)
        self.assertEqual(d["line_start"], 2)
        self.assertEqual(d["line_end"], 5)
        self.assertEqual(d["page"], 1)


class TestKnowledgeChunk(unittest.TestCase):
    """Tests for KnowledgeChunk."""

    def test_knowledge_chunk_to_dict(self):
        chunk = KnowledgeChunk(
            chunk_id="test_1",
            modality="text",
            text="Hello world",
            confidence=0.95,
        )
        d = chunk.to_dict()
        self.assertEqual(d["chunk_id"], "test_1")
        self.assertEqual(d["modality"], "text")
        self.assertEqual(d["text"], "Hello world")
        self.assertEqual(d["confidence"], 0.95)

    def test_knowledge_chunk_with_span(self):
        span = SourceSpan(start_offset=0, end_offset=11, line_start=0, line_end=0)
        chunk = KnowledgeChunk(
            chunk_id="test_2",
            modality="text",
            text="Hello world",
            source_span=span,
            confidence=0.9,
        )
        d = chunk.to_dict()
        self.assertIsNotNone(d["source_span"])
        self.assertEqual(d["source_span"]["start_offset"], 0)


class TestMultiModalIngestor(unittest.TestCase):
    """Tests for MultiModalIngestor."""

    def setUp(self):
        self.ing = MultiModalIngestor()

    def test_text_ingest_with_spans(self):
        text = "Line one.\nLine two.\nLine three."
        chunks = self.ing.ingest(text=text)
        self.assertEqual(len(chunks), 3)
        # Check spans
        self.assertIsNotNone(chunks[0].source_span)
        self.assertEqual(chunks[0].modality, "text")

    def test_csv_ingest_with_confidence(self):
        csv_text = "name,value\ntest,123"
        chunks = self.ing.ingest(csv_text=csv_text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].modality, "table")
        self.assertEqual(chunks[0].confidence, 0.95)

    def test_markdown_table_ingest(self):
        md = "|a|b|\n|---|---|\n|1|2|"
        chunks = self.ing.ingest(markdown_table=md)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].modality, "table")

    def test_image_stub(self):
        chunks = self.ing.ingest(image_bytes=b"fake_image_data")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].modality, "image")
        self.assertIn("OCR_STUB", chunks[0].text)
        self.assertEqual(chunks[0].confidence, 0.3)

    def test_image_custom_ocr(self):
        def mock_ocr(b):
            return "Extracted text from image"

        chunks = self.ing.ingest(image_bytes=b"test", ocr_fn=mock_ocr)
        self.assertEqual(chunks[0].text, "Extracted text from image")
        self.assertEqual(chunks[0].confidence, 0.85)

    def test_pdf_stub(self):
        chunks = self.ing.ingest(pdf_bytes=b"fake_pdf_bytes")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].modality, "document")
        self.assertIn("PDF_STUB", chunks[0].text)

    def test_multi_input(self):
        chunks = self.ing.ingest(
            text="Hello",
            csv_text="a,b\n1,2",
            markdown_table="|c|d|\n|---|---|\n|3|4|",
        )
        self.assertGreaterEqual(len(chunks), 3)


class TestDocumentChunker(unittest.TestCase):
    """Tests for DocumentChunker."""

    def test_chunk_by_size(self):
        text = "A" * 600  # Long text
        chunks = DocumentChunker.chunk_by_size(text, chunk_size=200, overlap=20)
        self.assertGreater(len(chunks), 1)

    def test_chunk_by_size_has_spans(self):
        text = "Hello world. This is a test."
        chunks = DocumentChunker.chunk_by_size(text, chunk_size=50)
        for chunk in chunks:
            self.assertIsNotNone(chunk.source_span)

    def test_chunk_by_sentence(self):
        text = "First sentence. Second sentence. Third sentence. Fourth."
        chunks = DocumentChunker.chunk_by_sentence(text, sentences_per_chunk=2)
        # Should have at least 2 chunks
        self.assertGreaterEqual(len(chunks), 2)


class TestLlmJudgeRubric(unittest.TestCase):
    """Tests for LLM Judge Rubric."""

    def test_default_rubric(self):
        rubric = LlmJudgeRubric.default_supply_matching()
        self.assertEqual(rubric.name, "supply_matching_v1")
        self.assertGreater(len(rubric.criteria), 0)
        # Check weights sum to 1
        total_weight = sum(c.weight for c in rubric.criteria)
        self.assertAlmostEqual(total_weight, 1.0, places=2)

    def test_rubric_to_prompt_format(self):
        rubric = LlmJudgeRubric.default_supply_matching()
        prompt = rubric.to_prompt_format()
        self.assertIn("Evaluation Rubric", prompt)
        self.assertIn("RELEVANCE", prompt)

    def test_rubric_to_dict(self):
        rubric = LlmJudgeRubric.default_supply_matching()
        d = rubric.to_dict()
        self.assertEqual(d["name"], "supply_matching_v1")
        self.assertIn("criteria", d)


class TestLlmJudgeEvaluator(unittest.TestCase):
    """Tests for LLM Judge Evaluator."""

    def setUp(self):
        self.rubric = LlmJudgeRubric.default_supply_matching()
        self.evaluator = LlmJudgeEvaluator(self.rubric)

    def test_evaluate_single_result(self):
        result = self.evaluator.evaluate(
            query="I want electronics",
            result={"id": "s1", "category": "electronics", "quality_score": 0.8, "risk_level": "low"},
        )
        self.assertEqual(result.rubric_name, "supply_matching_v1")
        self.assertIsNotNone(result.overall_score)
        self.assertIsNotNone(result.overall_level)

    def test_evaluate_stores_history(self):
        self.evaluator.evaluate(
            query="test",
            result={"id": "s1"},
        )
        self.assertEqual(len(self.evaluator._score_history), 1)

    def test_calibration_hooks(self):
        hooks = self.evaluator.get_calibration_hooks()
        self.assertIn("on_score", hooks)
        self.assertIn("calibrate", hooks)
        self.assertIn("get_history", hooks)

    def test_score_to_level(self):
        self.assertEqual(self.evaluator._score_to_level(0.95), ScoreLevel.EXCELLENT)
        self.assertEqual(self.evaluator._score_to_level(0.75), ScoreLevel.GOOD)
        self.assertEqual(self.evaluator._score_to_level(0.55), ScoreLevel.FAIR)
        self.assertEqual(self.evaluator._score_to_level(0.35), ScoreLevel.POOR)
        self.assertEqual(self.evaluator._score_to_level(0.15), ScoreLevel.VERY_POOR)


class TestCostBudget(unittest.TestCase):
    """Tests for CostBudget."""

    def test_check_budget_within_limit(self):
        budget = CostBudget(daily_limit=10.0)
        allowed, reason = budget.check_budget("user1", 5.0)
        self.assertTrue(allowed)
        self.assertEqual(reason, "OK")

    def test_check_budget_exceeds_limit(self):
        budget = CostBudget(daily_limit=10.0)
        allowed, reason = budget.check_budget("user1", 15.0)
        self.assertFalse(allowed)
        self.assertIn("exceeded", reason.lower())

    def test_record_spend(self):
        budget = CostBudget(daily_limit=10.0)
        budget.record_spend("user1", 5.0)
        remaining = budget.get_remaining("user1")
        self.assertEqual(remaining["daily_remaining"], 5.0)


class TestModelRouter(unittest.TestCase):
    """Tests for ModelRouter."""

    def setUp(self):
        self.router = ModelRouter()

    def test_route_low_complexity(self):
        decision = self.router.route({"text": "hello"})
        self.assertEqual(decision.selected_model, "haiku")

    def test_route_high_complexity(self):
        decision = self.router.route({
            "text": "analyze this complex code and compute mathematical equations"
        })
        self.assertIn(decision.selected_model, ["sonnet", "opus"])

    def test_route_has_fallback(self):
        decision = self.router.route({"text": "test"})
        self.assertIsNotNone(decision.reasoning)
        self.assertIsNotNone(decision.estimated_cost)

    def test_route_with_budget_exceeded(self):
        budget = CostBudget(daily_limit=0.001)
        router = ModelRouter(budget=budget)
        # Will route to haiku since budget is exceeded
        decision = router.route({"text": "hello"}, user_id="user1")
        self.assertEqual(decision.selected_model, "haiku")


class TestAuditLogger(unittest.TestCase):
    """Tests for AuditLogger."""

    def setUp(self):
        self.logger = AuditLogger()

    def test_log_entry(self):
        entry = self.logger.log(
            operation="test_op",
            model="haiku",
            input_tokens=100,
            output_tokens=50,
            latency_ms=150.0,
            success=True,
        )
        self.assertEqual(entry.operation, "test_op")
        self.assertEqual(entry.model, "haiku")

    def test_query_logs(self):
        self.logger.log("op1", "haiku", 100, 50, 100, True)
        self.logger.log("op2", "sonnet", 200, 100, 200, True)

        results = self.logger.query(operation="op1")
        self.assertEqual(len(results), 1)

    def test_get_statistics(self):
        self.logger.log("op1", "haiku", 100, 50, 100, True)
        self.logger.log("op2", "sonnet", 200, 100, 200, True)

        stats = self.logger.get_statistics()
        self.assertEqual(stats["total_requests"], 2)
        self.assertIn("by_model", stats)


class TestSafetyFilter(unittest.TestCase):
    """Tests for SafetyFilter."""

    def setUp(self):
        self.filter = SafetyFilter()

    def test_safe_content_passes(self):
        allowed, reason = self.filter.check_request("This is normal content")
        self.assertTrue(allowed)

    def test_blocked_pattern_fails(self):
        self.filter.add_blocked_pattern("badword")
        allowed, reason = self.filter.check_request("This contains badword here")
        self.assertFalse(allowed)


class TestEvaluationBenchmark(unittest.TestCase):
    """Tests for EvaluationBenchmark."""

    def test_run_evaluation_set(self):
        evaluator = LlmJudgeEvaluator()
        test_cases = [
            {"query": "test1", "result": {"id": "s1", "category": "a"}},
            {"query": "test2", "result": {"id": "s2", "category": "b"}},
        ]

        stats = EvaluationBenchmark.run_evaluation_set(evaluator, test_cases)
        self.assertEqual(stats["total_cases"], 2)
        self.assertIn("overall_mean", stats)
        self.assertIn("dimension_stats", stats)


if __name__ == "__main__":
    unittest.main()
