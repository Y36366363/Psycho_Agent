import json
import random
import tempfile
import unittest
from pathlib import Path

from psycho_agent.live_compare import (
    automatic_scores,
    load_rubric,
    load_scenarios,
    resume_comparison,
    retry_failed_scenarios,
    run_comparison,
)


class FakeModel:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self.model_name = f"{provider_name}-test"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return "你提到的这个具体变化值得先弄清楚。哪一部分对你影响最大？"


class InterruptingModel(FakeModel):
    def __init__(self, provider_name: str, interrupt_after: int) -> None:
        super().__init__(provider_name)
        self.calls = 0
        self.interrupt_after = interrupt_after

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls > self.interrupt_after:
            raise RuntimeError("simulated process interruption")
        return super().complete(system_prompt, user_prompt)


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
                self.assertEqual(score["deterministic_fallback_count"], 0)
                self.assertEqual(score["alignment_fallback_count"], 0)
                self.assertEqual(score["release_gate"], "passed")
                self.assertEqual(score["release_blocker_turn_count"], 0)
                self.assertIn("median_success_latency_seconds", score)

    def test_automatic_scores_fail_release_gate_for_blocking_final_issue(self) -> None:
        data = {
            "models": {
                "Model-A": {
                    "scenarios": [
                        {
                            "turns": [
                                {
                                    "response": "这个办法一定有效。",
                                    "strategy": "tiny_next_step",
                                    "final_issues": ["unsafe_claim"],
                                    "draft_issues": [],
                                    "rewritten": True,
                                    "safety_fallback_applied": False,
                                    "alignment_fallback_applied": False,
                                    "deterministic_fallback": None,
                                    "latency_seconds": 1.0,
                                }
                            ]
                        }
                    ]
                }
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blind.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            score = automatic_scores(path)["Model-A"]
            self.assertEqual(score["release_gate"], "failed")
            self.assertEqual(score["release_blocker_turn_count"], 1)

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

    def test_interrupted_run_checkpoints_and_resumes_missing_scenarios(self) -> None:
        scenarios = {
            "version": "checkpoint-test",
            "scenarios": [
                {
                    "id": "one",
                    "title": "One",
                    "intent": "Test",
                    "turns": ["一", "继续"],
                },
                {"id": "two", "title": "Two", "intent": "Test", "turns": ["二"]},
            ],
        }
        interrupted_models = {
            "one": InterruptingModel("one", interrupt_after=1),
            "two": FakeModel("two"),
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "simulated process interruption"):
                run_comparison(
                    interrupted_models, scenarios, directory, rng=random.Random(7)
                )
            checkpoint = json.loads(
                (Path(directory) / "blind_outputs.json").read_text(encoding="utf-8")
            )
            self.assertEqual(checkpoint["checkpoint_status"], "running")
            stored_scenarios = [
                scenario
                for model in checkpoint["models"].values()
                for scenario in model["scenarios"]
            ]
            self.assertEqual(len(stored_scenarios), 1)
            self.assertEqual(sum(len(scenario["turns"]) for scenario in stored_scenarios), 1)

            changed_models = {name: FakeModel(name) for name in ("one", "two")}
            changed_models["one"].model_name = "changed-after-checkpoint"
            with self.assertRaisesRegex(ValueError, "Configured model changed"):
                resume_comparison(changed_models, scenarios, directory)

            models = {name: FakeModel(name) for name in ("one", "two")}
            blind_path, resumed = resume_comparison(models, scenarios, directory)
            completed = json.loads(blind_path.read_text(encoding="utf-8"))
            self.assertEqual(resumed, 4)
            self.assertEqual(completed["checkpoint_status"], "complete")
            self.assertEqual(
                sum(len(model["scenarios"]) for model in completed["models"].values()),
                4,
            )


if __name__ == "__main__":
    unittest.main()
