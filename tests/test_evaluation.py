import unittest

from psycho_agent.evaluation import load_cases, run_evaluation


class BehavioralEvaluationTests(unittest.TestCase):
    def test_case_ids_are_unique(self) -> None:
        case_ids = [case["id"] for case in load_cases()]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_all_built_in_cases_pass(self) -> None:
        failures = [result for result in run_evaluation() if not result.passed]
        self.assertEqual(failures, [], failures)


if __name__ == "__main__":
    unittest.main()
