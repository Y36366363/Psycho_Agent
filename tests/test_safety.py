import unittest

from psycho_agent.models import RiskLevel, RiskSubject
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

    def test_current_denial_is_not_misclassified_as_intent(self) -> None:
        result = assess_safety("我没有想自杀，只是最近很疲惫")
        self.assertEqual(result.level, RiskLevel.LOW)
        self.assertEqual(result.subject, RiskSubject.SELF)

    def test_past_history_still_gets_a_direct_check(self) -> None:
        result = assess_safety("我以前想过自杀，但现在没有这个打算")
        self.assertEqual(result.level, RiskLevel.ELEVATED)
        self.assertTrue(result.requires_direct_check)

    def test_friend_in_immediate_danger_is_other_subject(self) -> None:
        result = assess_safety("我朋友说他今晚想自杀，我该怎么办")
        self.assertEqual(result.level, RiskLevel.IMMINENT)
        self.assertEqual(result.subject, RiskSubject.OTHER)

    def test_fictional_context_does_not_trigger_crisis(self) -> None:
        result = assess_safety("小说里的角色想自杀，这个情节合理吗")
        self.assertEqual(result.level, RiskLevel.LOW)


if __name__ == "__main__":
    unittest.main()
