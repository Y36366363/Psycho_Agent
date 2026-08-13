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

    def test_preparatory_language_without_suicide_word_is_imminent(self) -> None:
        messages = (
            "炭已经买好了，今晚等家人睡着以后我就可以解脱了。",
            "今晚不想再醒来了，安眠药都已经准备好放在桌上。",
            "告别信已经写好了，今晚就结束吧。",
            "I have the pills laid out beside me and I do not want to wake up tonight.",
        )
        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(assess_safety(message).level, RiskLevel.IMMINENT)

    def test_mentions_of_household_items_alone_are_not_crisis(self) -> None:
        messages = ("我买了烧烤用的木炭。", "医生让我把安眠药放在桌上。")
        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(assess_safety(message).level, RiskLevel.LOW)

    def test_english_substrings_do_not_create_an_other_person_subject(self) -> None:
        result = assess_safety(
            "I have the pills laid out beside me and I do not want to wake up tonight."
        )
        self.assertEqual(result.subject, RiskSubject.SELF)

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

    def test_friend_preparation_without_suicide_word_is_other_subject(self) -> None:
        result = assess_safety("我朋友把炭都准备好了，说今晚等家人睡着就能解脱。")
        self.assertEqual(result.level, RiskLevel.IMMINENT)
        self.assertEqual(result.subject, RiskSubject.OTHER)

    def test_fictional_context_does_not_trigger_crisis(self) -> None:
        result = assess_safety("小说里的角色想自杀，这个情节合理吗")
        self.assertEqual(result.level, RiskLevel.LOW)


if __name__ == "__main__":
    unittest.main()
