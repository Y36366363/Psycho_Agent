import unittest

from psycho_agent.engine import ConversationEngine
from psycho_agent.intake import INTAKE_STEPS
from psycho_agent.models import (
    ConversationPhase,
    SessionState,
    Strategy,
    SupportPreference,
)
from psycho_agent.strategy import select_strategy


class ConversationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ConversationEngine()
        self.session = SessionState(session_id="test-session")

    def test_start_opens_with_invitation(self) -> None:
        plan = self.engine.start(self.session)
        self.assertEqual(plan.strategy, Strategy.OPEN_INVITATION)
        self.assertEqual(plan.questions[0], INTAKE_STEPS[0].question)

    def test_intake_advances_to_exploration(self) -> None:
        for index in range(len(INTAKE_STEPS)):
            plan = self.engine.process(self.session, f"第 {index + 1} 个回答")
        self.assertEqual(self.session.phase, ConversationPhase.EXPLORE)
        self.assertNotEqual(plan.strategy, Strategy.CLARIFY)

    def test_crisis_bypasses_normal_generation(self) -> None:
        plan = self.engine.process(self.session, "我现在想自杀")
        self.assertEqual(plan.phase, ConversationPhase.CRISIS)
        self.assertEqual(plan.strategy, Strategy.CRISIS_SUPPORT)
        self.assertFalse(plan.should_generate_normally)
        self.assertIsNotNone(plan.fixed_response)

    def test_empty_message_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.process(self.session, "  ")


class StrategyTests(unittest.TestCase):
    def test_high_intensity_prefers_grounding(self) -> None:
        session = SessionState(session_id="intense")
        session.user.emotion_intensity = 9
        self.assertEqual(select_strategy(session), Strategy.GROUND)

    def test_recent_strategy_is_not_immediately_repeated(self) -> None:
        session = SessionState(session_id="repeat")
        session.user.support_preference = SupportPreference.PLAN
        session.used_strategies = [Strategy.TINY_NEXT_STEP]
        self.assertEqual(select_strategy(session), Strategy.PROBLEM_SOLVE)


if __name__ == "__main__":
    unittest.main()
