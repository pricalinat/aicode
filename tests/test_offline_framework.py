from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from multi_agent_system.closed_loop import (
    FeatureStore,
    FeedbackLoop,
    SyntheticSupplyGenerator,
    SyntheticUserBehaviorGenerator,
)
from multi_agent_system.experiments import AttributionModel, OfflineABRunner, OfflineMetrics
from multi_agent_system.ingestion import MultiModalIngestor
from multi_agent_system.knowledge.supply_graph_database import SupplyGraphDatabase
from multi_agent_system.knowledge.supply_graph_models import SupplyEntity, SupplyEntityType
from multi_agent_system.matching import DualMatcher


class TestSyntheticSupplyGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = SyntheticSupplyGenerator(seed=123)

    def test_generate_count(self):
        data = self.gen.generate(num_supplies=5, num_users=4)
        self.assertEqual(len(data["supplies"]), 5)
        self.assertEqual(len(data["users"]), 4)

    def test_generate_deterministic(self):
        a = self.gen.generate(4, 3)
        b = SyntheticSupplyGenerator(seed=123).generate(4, 3)
        self.assertEqual(a, b)

    def test_supply_fields_exist(self):
        supply = self.gen.generate(1, 1)["supplies"][0]
        self.assertIn("risk_level", supply)
        self.assertIn("quality_score", supply)

    def test_user_fields_exist(self):
        user = self.gen.generate(1, 1)["users"][0]
        self.assertIn("preferred_categories", user)
        self.assertIn("risk_tolerance", user)


class TestSyntheticBehavior(unittest.TestCase):
    def setUp(self):
        generated = SyntheticSupplyGenerator(seed=1).generate(6, 4)
        self.supplies = generated["supplies"]
        self.users = generated["users"]
        self.beh = SyntheticUserBehaviorGenerator(seed=2)

    def test_events_non_empty(self):
        events = self.beh.generate(self.users, self.supplies, days=1, max_events_per_user_per_day=8)
        self.assertTrue(len(events) > 0)

    def test_event_type_is_valid(self):
        events = self.beh.generate(self.users, self.supplies, days=1, max_events_per_user_per_day=6)
        allowed = {"impression", "click", "favorite", "add_to_cart", "order", "consult"}
        self.assertTrue(all(e["event_type"] in allowed for e in events))

    def test_event_has_ids(self):
        evt = self.beh.generate(self.users, self.supplies, days=1, max_events_per_user_per_day=5)[0]
        self.assertIn("user_id", evt)
        self.assertIn("supply_id", evt)

    def test_deterministic(self):
        a = self.beh.generate(self.users, self.supplies, days=1, max_events_per_user_per_day=5)
        b = SyntheticUserBehaviorGenerator(seed=2).generate(self.users, self.supplies, days=1, max_events_per_user_per_day=5)
        self.assertEqual(a, b)


class TestFeatureAndFeedback(unittest.TestCase):
    def setUp(self):
        generated = SyntheticSupplyGenerator(seed=11).generate(5, 3)
        events = SyntheticUserBehaviorGenerator(seed=12).generate(generated["users"], generated["supplies"], days=1, max_events_per_user_per_day=8)
        self.supplies = generated["supplies"]
        self.events = events
        self.store = FeatureStore()

    def test_build_features(self):
        feats = self.store.build(self.supplies, self.events)
        self.assertEqual(len(feats), len(self.supplies))

    def test_feature_has_ctr(self):
        feats = self.store.build(self.supplies, self.events)
        one = next(iter(feats.values()))
        self.assertIn("ctr", one)

    def test_snapshot(self):
        self.store.build(self.supplies, self.events)
        snap = self.store.snapshot()
        self.assertEqual(len(snap), len(self.supplies))

    def test_feedback_updates_weight(self):
        feats = self.store.build(self.supplies, self.events)
        sid = self.supplies[0]["supply_id"]
        old = feats[sid]["train_weight"]
        updated = FeedbackLoop().apply(feats, {sid: {"reward": 1.0, "risk_violation": 0.0}})
        self.assertGreater(updated[sid]["train_weight"], old)


class TestDualMatcher(unittest.TestCase):
    def setUp(self):
        generated = SyntheticSupplyGenerator(seed=22).generate(8, 5)
        events = SyntheticUserBehaviorGenerator(seed=23).generate(generated["users"], generated["supplies"], days=1, max_events_per_user_per_day=8)
        features = FeatureStore().build(generated["supplies"], events)
        self.db = SupplyGraphDatabase()
        for s in generated["supplies"]:
            self.db.create_entity(SupplyEntity(id=s["supply_id"], type=SupplyEntityType.PRODUCT, properties=s), validate=False)
        for u in generated["users"]:
            self.db.create_entity(SupplyEntity(id=u["user_id"], type=SupplyEntityType.USER, properties=u), validate=False)
        self.matcher = DualMatcher(db=self.db, feature_map=features)
        self.user_id = generated["users"][0]["user_id"]
        self.supply_id = generated["supplies"][0]["supply_id"]

    def test_match_supply_non_empty(self):
        result = self.matcher.match_supply_for_user(self.user_id, {"top_k": 3})
        self.assertLessEqual(len(result), 3)

    def test_match_users_non_empty(self):
        result = self.matcher.match_users_for_supply(self.supply_id, {"top_k": 4})
        self.assertLessEqual(len(result), 4)

    def test_match_supply_unknown_user(self):
        self.assertEqual(self.matcher.match_supply_for_user("missing", {}), [])

    def test_match_users_unknown_supply(self):
        self.assertEqual(self.matcher.match_users_for_supply("missing", {}), [])

    def test_score_sorted(self):
        result = self.matcher.match_supply_for_user(self.user_id, {"top_k": 5})
        scores = [x["score"] for x in result]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestMetricsAttributionAB(unittest.TestCase):
    def test_recall(self):
        val = OfflineMetrics.recall_at_k(["a", "b", "c"], {"b", "x"}, 2)
        self.assertEqual(val, 0.5)

    def test_ndcg(self):
        val = OfflineMetrics.ndcg_at_k(["a", "b"], {"a": 2.0, "b": 1.0}, 2)
        self.assertGreater(val, 0)

    def test_conversion_proxy(self):
        events = [{"event_type": "click"}, {"event_type": "order"}]
        self.assertEqual(OfflineMetrics.conversion_proxy(events), 1.0)

    def test_coverage(self):
        self.assertEqual(OfflineMetrics.coverage({"a", "b"}, 4), 0.5)

    def test_risk_violation_rate(self):
        rate = OfflineMetrics.risk_violation_rate([{"risk_violated": True}, {"risk_violated": False}])
        self.assertEqual(rate, 0.5)

    def test_attribution(self):
        model = AttributionModel()
        events = [{"event_type": "order", "supply_id": "s1", "context": {"channel": "search"}}]
        out = model.attribute(events, {"s1": 100.0})
        self.assertGreater(out["attributed_revenue"], 0)

    def test_ab_runner_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            runner = OfflineABRunner(output_dir=Path(td))
            report = runner.run(
                baseline={"u1": ["s1", "s2"]},
                treatment={"u1": ["s2", "s1"]},
                relevance={"u1": {"s1": 2.0, "s2": 1.0}},
                events=[],
                order_value_map={"s1": 100},
                report_name="r.json",
            )
            self.assertIn("baseline", report)
            self.assertTrue((Path(td) / "r.json").exists())


class TestMultimodalIngest(unittest.TestCase):
    def setUp(self):
        self.ing = MultiModalIngestor()

    def test_text_ingest(self):
        chunks = self.ing.ingest(text="a\nb")
        self.assertEqual(len(chunks), 2)

    def test_csv_ingest(self):
        chunks = self.ing.ingest(csv_text="a,b\n1,2")
        self.assertEqual(chunks[0].modality, "table")

    def test_markdown_table_ingest(self):
        md = "|a|b|\n|---|---|\n|1|2|"
        chunks = self.ing.ingest(markdown_table=md)
        self.assertEqual(len(chunks), 1)

    def test_image_stub(self):
        chunks = self.ing.ingest(image_bytes=b"12345")
        self.assertIn("OCR_STUB", chunks[0].text)

    def test_image_custom_ocr(self):
        chunks = self.ing.ingest(image_bytes=b"x", ocr_fn=lambda b: "detected")
        self.assertEqual(chunks[0].text, "detected")

    def test_multi_input(self):
        chunks = self.ing.ingest(text="t", csv_text="a\n1", image_bytes=b"1")
        self.assertGreaterEqual(len(chunks), 3)


class TestIntegration(unittest.TestCase):
    def test_end_to_end_small(self):
        generated = SyntheticSupplyGenerator(seed=31).generate(5, 4)
        events = SyntheticUserBehaviorGenerator(seed=32).generate(generated["users"], generated["supplies"], days=1, max_events_per_user_per_day=6)
        feats = FeatureStore().build(generated["supplies"], events)
        updated = FeedbackLoop().apply(feats, {k: {"reward": 0.2, "risk_violation": 0.0} for k in feats})
        self.assertEqual(len(updated), 5)

    def test_report_json_serializable(self):
        with tempfile.TemporaryDirectory() as td:
            runner = OfflineABRunner(output_dir=Path(td))
            report = runner.run(
                baseline={"u": ["s1"]},
                treatment={"u": ["s1"]},
                relevance={"u": {"s1": 1.0}},
                events=[],
                order_value_map={"s1": 1.0},
            )
            json.dumps(report)


if __name__ == "__main__":
    unittest.main()
