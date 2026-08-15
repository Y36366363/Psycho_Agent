import json
import random
import tempfile
import unittest
from pathlib import Path

from psycho_agent.live_compare import (
    automatic_scores,
    load_rubric,
    load_scenarios,
    retry_failed_scenarios,
    run_comparison,
)


class FakeModel:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self.model_name = f"{provider_name}-test"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return "你提到的这个具体变化值得先弄清楚。哪一部分对你影响最大？"


class LiveComparisonTests(unittest.TestCase):
    def test_scenarios_are_synthetic_and_well_formed(self) -> None:
        data = load_scenarios()
        self.assertEqual(data["version"], "2026-08-10")
        self.assertGreaterEqual(len(data["scenarios"]), 4)
        self.assertTrue(all(len(scenario["turns"]) >= 4 for scenario in data["scenarios"]))

    def test_qualitative_rubric_is_stage_aware_and_anchored(self) -> None:
        rubric = load_rubric()
        stages = {dimension["stage"] for dimension in rubric["dimensions"]}
        self.assertEqual(stages, {"exploration", "insight", "action", "cross_cutting"})
        self.assertTrue(
            all(set(dimension["anchors"]) == {"1", "3", "5"} for dimension in rubric["dimensions"])
        )

    def test_comparison_separates_blind_outputs_from_mapping(self) -> None:
        models = {name: FakeModel(name) for name in ("one", "two", "three")}
        scenarios = {
            "version": "test",
            "scenarios": [
                {"id": "case", "title": "Case", "intent": "Test", "turns": ["我很烦。"]}
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            blind_path, key_path = run_comparison(
                models,
                scenarios,
                directory,
                rng=random.Random(7),
            )
            blind_text = blind_path.read_text(encoding="utf-8")
            key_data = json.loads(key_path.read_text(encoding="utf-8"))
            self.assertNotIn('"one"', blind_text)
            self.assertNotIn('"two"', blind_text)
            self.assertEqual(set(key_data["mapping"]), {"Model-A", "Model-B", "Model-C"})
            scores = automatic_scores(blind_path)
            self.assertTrue(all(score["successful_turns"] == 1 for score in scores.values()))

    def test_retry_replaces_complete_failed_scenario_without_unsealing_output(self) -> None:
        models = {name: FakeModel(name) for name in ("one", "two", "three")}
        scenarios = {
            "version": "test",
            "scenarios": [
                {
                    "id": "case",
                    "title": "Case",
                    "intent": "Test",
                    "turns": ["第一轮。", "第二轮。"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            blind_path, _ = run_comparison(
                models, scenarios, directory, rng=random.Random(7)
            )
            blind_data = json.loads(blind_path.read_text(encoding="utf-8"))
            first_alias = next(iter(blind_data["models"]))
            failed_turn = blind_data["models"][first_alias]["scenarios"][0]["turns"][1]
            failed_turn["response"] = None
            failed_turn["error"] = "temporary"
            blind_path.write_text(
                json.dumps(blind_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            _, retried_count = retry_failed_scenarios(models, scenarios, directory)
            retried_data = json.loads(blind_path.read_text(encoding="utf-8"))
            turns = retried_data["models"][first_alias]["scenarios"][0]["turns"]
            self.assertEqual(retried_count, 1)
            self.assertTrue(all(turn["error"] is None for turn in turns))
            self.assertEqual(len(retried_data["retry_history"]), 1)
            self.assertNotIn('"one"', blind_path.read_text(encoding="utf-8"))

    def test_repeated_comparison_tracks_runs_and_distribution_metrics(self) -> None:
        models = {name: FakeModel(name) for name in ("one", "two")}
        scenarios = {
            "version": "test",
            "scenarios": [
                {"id": "case", "title": "Case", "intent": "Test", "turns": ["第一轮。"]}
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            blind_path, _ = run_comparison(
                models,
                scenarios,
                directory,
                rng=random.Random(7),
                repetitions=2,
            )
            data = json.loads(blind_path.read_text(encoding="utf-8"))
            self.assertEqual(data["repetitions"], 2)
            for model_data in data["models"].values():
                self.assertEqual(
                    [scenario["replicate"] for scenario in model_data["scenarios"]],
                    [1, 2],
                )
            for score in automatic_scores(blind_path).values():
                self.assertEqual(score["scenario_runs"], 2)
                self.assertEqual(score["completed_scenario_runs"], 2)
                self.assertEqual(score["completion_rate"], 1.0)
                self.assertEqual(score["final_issue_turn_rate"], 0.0)
                self.assertIn("median_success_latency_seconds", score)

    def test_comparison_rejects_unbounded_repetitions(self) -> None:
        models = {name: FakeModel(name) for name in ("one", "two")}
        scenarios = {
            "version": "test",
            "scenarios": [
                {"id": "case", "title": "Case", "intent": "Test", "turns": ["第一轮。"]}
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_comparison(models, scenarios, directory, repetitions=11)


if __name__ == "__main__":
    unittest.main()
