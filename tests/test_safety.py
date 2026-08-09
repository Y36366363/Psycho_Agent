import unittest

from psycho_agent.models import RiskLevel
from psycho_agent.safety import assess_safety


class SafetyAssessmentTests(unittest.TestCase):
    def test_ordinary_distress_is_low(self) -> None:
        result = assess_safety("最近工作压力很大，晚上总是睡不好")
        self.assertEqual(result.level, RiskLevel.LOW)
        self.assertFalse(result.requires_direct_check)

    def test_hopelessness_requires_direct_check(self) -> None:
        result = assess_safety("有时候觉得活着没意思")
        self.assertEqual(result.level, RiskLevel.ELEVATED)
        self.assertTrue(result.requires_direct_check)

    def test_explicit_plan_is_high(self) -> None:
        result = assess_safety("我想自杀，也已经在考虑方法")
        self.assertEqual(result.level, RiskLevel.HIGH)

    def test_immediate_intent_is_imminent(self) -> None:
        result = assess_safety("我今晚准备自杀")
        self.assertEqual(result.level, RiskLevel.IMMINENT)


if __name__ == "__main__":
    unittest.main()
