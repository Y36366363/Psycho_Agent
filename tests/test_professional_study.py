import csv
import json
import random
import tempfile
import unittest
from pathlib import Path

from psycho_agent.clinical_evaluation import Rating, agreement_report
from psycho_agent.professional_study import (
    DEFAULT_PREREGISTRATION,
    DEFAULT_RUBRIC,
    DEFAULT_SESSIONS,
    HardFailureRating,
    create_professional_rating_packet,
    load_study_sessions,
    professional_agreement_report,
    recover_study_outputs_from_packet,
    run_three_arm_study,
    validate_rating_form,
)


class FakeStudyModel:
    provider_name = "same-provider"
    model_name = "same-base-model"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return "我会根据你刚才说的具体内容回应，同时保留你的选择。"


class ProfessionalStudyTests(unittest.TestCase):
    def test_frozen_sessions_have_required_size_and_coverage(self) -> None:
        payload = load_study_sessions()
        self.assertEqual(len(payload["sessions"]), 24)
        self.assertTrue(payload["description"].startswith("Frozen"))

    def test_three_arm_collection_and_packet_are_blinded_and_complete(self) -> None:
        sessions = load_study_sessions()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_path, key_path = run_three_arm_study(
                FakeStudyModel(), sessions, root / "study", rng=random.Random(7), workers=4
            )
            outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
            self.assertEqual(outputs["status"], "complete")
            self.assertEqual(set(outputs["conditions"]), {"Condition-A", "Condition-B", "Condition-C"})
            self.assertTrue(
                all(len(condition["sessions"]) == 24 for condition in outputs["conditions"].values())
            )
            key = json.loads(key_path.read_text(encoding="utf-8"))
            self.assertEqual(set(key["condition_mapping"].values()), {
                "plain_llm", "therapist_prompt_llm", "psycho_agent"
            })
            self.assertEqual(key["model"], "same-base-model")

            packet_path, rating_key = create_professional_rating_packet(
                outputs_path,
                DEFAULT_SESSIONS,
                DEFAULT_RUBRIC,
                DEFAULT_PREREGISTRATION,
                root / "packet",
                rng=random.Random(11),
            )
            packet_text = packet_path.read_text(encoding="utf-8")
            packet = json.loads(packet_text)
            self.assertEqual(len(packet["cases"]), 24)
            self.assertEqual(len(packet["empty_rating_rows"]), 72)
            self.assertNotIn("plain_llm", packet_text)
            self.assertNotIn("therapist_prompt_llm", packet_text)
            self.assertNotIn("psycho_agent", packet_text)
            self.assertIn("Condition-", rating_key.read_text(encoding="utf-8"))

            damaged = json.loads(outputs_path.read_text(encoding="utf-8"))
            damaged["status"] = "running"
            damaged["conditions"]["Condition-A"]["sessions"] = []
            outputs_path.write_text(json.dumps(damaged), encoding="utf-8")
            recovered = recover_study_outputs_from_packet(
                outputs_path, packet_path, rating_key
            )
            self.assertEqual(set(recovered["condition_session_counts"].values()), {24})
            self.assertNotIn("condition_mapping", json.dumps(recovered))

            with (root / "packet" / "rating_form.csv").open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 72)
            self.assertTrue((root / "packet" / "packet_manifest.json").is_file())
            for plan in packet["assignment_plans"].values():
                counts = {case["case_id"]: 0 for case in packet["cases"]}
                for assigned in plan["assignments"].values():
                    for case_id in assigned:
                        counts[case_id] += 1
                self.assertTrue(all(count >= 2 for count in counts.values()))

            invalid = validate_rating_form(
                root / "packet" / "rating_form.csv",
                packet_path,
                reviewer_count=2,
                reviewer_slot="Reviewer-1",
                reviewer_id="professional-1",
            )
            self.assertEqual(invalid["status"], "invalid")
            self.assertTrue(any("reviewer_id mismatch" in error for error in invalid["errors"]))

            form_path = root / "packet" / "rating_form.csv"
            with form_path.open(encoding="utf-8", newline="") as handle:
                form_rows = list(csv.DictReader(handle))
                fieldnames = list(form_rows[0])
            dimension_ids = [dimension["id"] for dimension in packet["dimensions"]]
            for row in form_rows:
                row["reviewer_id"] = "professional-1"
                for dimension in dimension_ids:
                    row[dimension] = "3"
                row["acceptable_yes_no"] = "yes"
                row["hard_failure_yes_no"] = "no"
                row["within_case_rank_1_best_3_worst"] = {
                    "Dialogue-A": "1",
                    "Dialogue-B": "2",
                    "Dialogue-C": "3",
                }[row["dialogue_id"]]
            completed_form = root / "packet" / "completed.csv"
            with completed_form.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(form_rows)
            valid = validate_rating_form(
                completed_form,
                packet_path,
                reviewer_count=2,
                reviewer_slot="Reviewer-1",
                reviewer_id="professional-1",
            )
            self.assertEqual(valid["status"], "valid")

    def test_agreement_reports_ordinal_and_hard_failure_disagreement(self) -> None:
        ratings = [
            Rating("item-1", "empathy", "r1", 5),
            Rating("item-1", "empathy", "r2", 3),
            Rating("item-2", "empathy", "r1", 4),
            Rating("item-2", "empathy", "r2", 4),
        ]
        ordinal = agreement_report(ratings)["empathy"]["pairs"][0]
        self.assertEqual(ordinal["severe_disagreement_count"], 1)
        self.assertEqual(ordinal["severe_disagreement_items"], ["item-1"])
        hard = [
            HardFailureRating("item-1", "r1", True, ("unsupported_diagnosis",)),
            HardFailureRating("item-2", "r1", False),
            HardFailureRating("item-1", "r2", False),
            HardFailureRating("item-2", "r2", False),
        ]
        report = professional_agreement_report(ratings, hard)
        pair = report["hard_safety"]["pairs"][0]
        self.assertEqual(pair["exact_binary_agreement"], 0.5)
        self.assertEqual(len(pair["disagreements"]), 1)


if __name__ == "__main__":
    unittest.main()
