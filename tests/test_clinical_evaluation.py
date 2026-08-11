import json
import random
import tempfile
import unittest
from pathlib import Path

from psycho_agent.clinical_evaluation import (
    Rating,
    agreement_report,
    create_blind_rating_packet,
    quadratic_weighted_kappa,
)


class ClinicalEvaluationTests(unittest.TestCase):
    def test_identical_ratings_have_perfect_kappa(self) -> None:
        self.assertEqual(quadratic_weighted_kappa([1, 2, 4, 5], [1, 2, 4, 5]), 1.0)

    def test_agreement_report_keeps_dimensions_separate(self) -> None:
        ratings = [
            Rating("item-1", "empathy", "r1", 4),
            Rating("item-2", "empathy", "r1", 2),
            Rating("item-1", "empathy", "r2", 4),
            Rating("item-2", "empathy", "r2", 3),
            Rating("item-1", "safety", "r1", 5),
            Rating("item-1", "safety", "r2", 5),
        ]
        report = agreement_report(ratings)
        self.assertEqual(set(report), {"empathy", "safety"})
        self.assertEqual(report["empathy"]["rater_count"], 2)
        self.assertEqual(report["safety"]["mean_pairwise_kappa"], 1.0)

    def test_rating_packet_contains_no_model_aliases(self) -> None:
        outputs = {
            "models": {
                "Model-A": {
                    "scenarios": [
                        {
                            "id": "case",
                            "title": "Case",
                            "intent": "Test",
                            "turns": [{"user": "hello", "response": "response"}],
                        }
                    ]
                }
            }
        }
        rubric = {
            "version": "test",
            "dimensions": [{"id": "empathy", "anchors": {"1": "", "3": "", "5": ""}}],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_path = root / "outputs.json"
            rubric_path = root / "rubric.json"
            outputs_path.write_text(json.dumps(outputs), encoding="utf-8")
            rubric_path.write_text(json.dumps(rubric), encoding="utf-8")
            packet_path, key_path = create_blind_rating_packet(
                outputs_path, rubric_path, root / "ratings", rng=random.Random(7)
            )
            self.assertNotIn("Model-A", packet_path.read_text(encoding="utf-8"))
            self.assertIn("Model-A", key_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
