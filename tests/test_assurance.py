import unittest

from psycho_agent.assurance import build_assurance_report


class AssuranceTests(unittest.TestCase):
    def test_automated_success_never_becomes_clinical_validation(self):
        report = build_assurance_report(
            unit_passed=90, unit_total=90, behavior_passed=47, behavior_total=47
        )
        gates = {gate["gate"]: gate for gate in report["gates"]}
        self.assertEqual(gates["engineering_regression"]["status"], "passed")
        self.assertEqual(gates["verified_professional_review"]["status"], "pending")
        self.assertEqual(gates["clinical_effectiveness"]["status"], "pending")
        self.assertIn("clinically validated", report["prohibited_claims"])
        self.assertEqual(report["overall_stage"], "research_prototype")

    def test_two_finalized_verified_raters_unlock_only_professional_review(self):
        report = build_assurance_report(
            unit_passed=1,
            unit_total=1,
            behavior_passed=1,
            behavior_total=1,
            professional_rating_report={
                "status": "human_ratings_complete",
                "finalized_reviewer_count": 2,
                "agreement": {"empathy": {"mean_pairwise_kappa": 0.7}},
            },
        )
        gates = {gate["gate"]: gate for gate in report["gates"]}
        self.assertEqual(gates["verified_professional_review"]["status"], "passed")
        self.assertEqual(gates["clinical_effectiveness"]["status"], "pending")
        self.assertIn("clinically validated", report["prohibited_claims"])

    def test_production_gate_lists_every_missing_control(self):
        report = build_assurance_report(
            unit_passed=1,
            unit_total=1,
            behavior_passed=1,
            behavior_total=1,
            production_evidence={"public_tls": True},
        )
        gate = next(g for g in report["gates"] if g["gate"] == "production_readiness")
        self.assertEqual(gate["status"], "pending")
        self.assertIn("managed_key_service", gate["missing"])

    def test_impossible_test_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            build_assurance_report(
                unit_passed=11,
                unit_total=10,
                behavior_passed=1,
                behavior_total=1,
            )
