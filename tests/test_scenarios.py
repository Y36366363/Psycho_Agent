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
        self.assertGreaterEqual(len(plan.actions), 1)
        evidence = self.session.decision_history[-1]
        self.assertIn("unresolved_prior_crisis", evidence.decision_basis)
        self.assertTrue(evidence.fixed_response)
        self.assertNotIn("我现在不想谈这个了", repr(evidence))

    def test_decision_evidence_is_bounded_and_contains_no_user_text(self) -> None:
        for index in range(25):
            self.engine.process(self.session, f"普通压力描述 {index}")
        self.assertEqual(len(self.session.decision_history), 20)
        evidence = self.session.decision_history[-1]
        self.assertEqual(evidence.turn, 25)
        self.assertNotIn("普通压力描述", repr(evidence))

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

    def test_explicit_tiny_step_overrides_previous_turn_rupture_repair(self) -> None:
        self.engine.process(
            self.session,
            "我试过找朋友，对方只说想开点，所以别再建议我找朋友。",
        )
        action = self.engine.process(
            self.session,
            "我只有五分钟，也不想写日记。给我一个不像心理作业的小办法。",
        )
        self.assertEqual(action.strategy, Strategy.TINY_NEXT_STEP)

    def test_exclusive_reliance_interrupts_intake(self) -> None:
        plan = self.engine.process(
            self.session, "只有你愿意听我说，我不打算告诉现实里的人"
        )
        self.assertEqual(plan.strategy, Strategy.REAL_WORLD_BRIDGE)


if __name__ == "__main__":
    unittest.main()
