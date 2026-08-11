import unittest

from psycho_agent.engine import ConversationEngine
from psycho_agent.models import ConversationPhase, SessionState, Strategy


class MultiTurnScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ConversationEngine()
        self.session = SessionState(session_id="scenario")

    def test_intake_preference_changes_first_support_strategy(self) -> None:
        messages = [
            "最近工作让我很疲惫",
            "大概持续两个月了",
            "难受程度6分，也影响睡眠",
            "我想和你一起想一个下一步的办法",
        ]
        for message in messages:
            plan = self.engine.process(self.session, message)
        self.assertEqual(plan.phase, ConversationPhase.EXPLORE)
        self.assertEqual(plan.strategy, Strategy.TINY_NEXT_STEP)

    def test_crisis_is_not_cleared_by_low_information_reply(self) -> None:
        self.engine.process(self.session, "我今晚准备自杀")
        plan = self.engine.process(self.session, "我现在不想谈这个了")
        self.assertEqual(plan.phase, ConversationPhase.CRISIS)
        self.assertEqual(plan.strategy, Strategy.SAFETY_FOLLOW_UP)
        self.assertFalse(plan.should_generate_normally)

    def test_crisis_clears_only_with_safety_and_protection(self) -> None:
        self.engine.process(self.session, "我今晚准备自杀")
        plan = self.engine.process(
            self.session,
            "我现在安全，家人在陪着我，危险物品已经交给家人",
        )
        self.assertEqual(plan.phase, ConversationPhase.STABILIZE)

    def test_other_person_crisis_uses_other_person_language(self) -> None:
        plan = self.engine.process(self.session, "我朋友说他今晚想自杀，我该怎么办")
        self.assertIn("对方", plan.fixed_response or "")
        self.assertNotIn("你此刻的安全", plan.fixed_response or "")

    def test_listen_then_tiny_step_changes_strategy_at_user_boundary(self) -> None:
        self.engine.process(self.session, "项目一直出错，我焦虑有8分")
        listening = self.engine.process(self.session, "先别给方法，我还没说完")
        self.assertEqual(listening.strategy, Strategy.REFLECT)
        action = self.engine.process(
            self.session, "我说完了，现在帮我找一个今天能做的最小下一步"
        )
        self.assertEqual(action.strategy, Strategy.TINY_NEXT_STEP)

    def test_exclusive_reliance_interrupts_intake(self) -> None:
        plan = self.engine.process(
            self.session, "只有你愿意听我说，我不打算告诉现实里的人"
        )
        self.assertEqual(plan.strategy, Strategy.REAL_WORLD_BRIDGE)


if __name__ == "__main__":
    unittest.main()
