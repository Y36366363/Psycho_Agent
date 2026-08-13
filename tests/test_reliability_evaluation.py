import unittest

from psycho_agent.reliability_evaluation import (
    load_reliability_cases,
    report_payload,
    run_reliability_evaluation,
)


class ReliabilityEvaluationTests(unittest.TestCase):
    def test_case_ids_are_unique(self):
        cases = load_reliability_cases()
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_synthetic_route_variants_are_invariant(self):
        report = report_payload(run_reliability_evaluation())
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["passed_variants"], report["total_variants"])
        self.assertEqual(report["failures"], [])
