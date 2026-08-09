import unittest

from psycho_agent.models import SessionState, Strategy, SupportPreference
from psycho_agent.state_update import update_session_state
from psycho_agent.strategy import select_strategy


class StateUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = SessionState(session_id="state")
        self.session.turn_count = 1

    def test_extracts_explicit_intensity_emotion_and_impact(self) -> None:
        update_session_state(self.session, "焦虑大概8分，最近总是半夜醒")
        self.assertEqual(self.session.user.emotion_intensity, 8)
        self.assertIn("焦虑", self.session.user.emotion_words)
        self.assertIn("sleep", self.session.user.functional_impact)

    def test_no_advice_request_prefers_listening(self) -> None:
        update_session_state(self.session, "我只想倾诉，现在不想要建议")
        self.assertEqual(self.session.user.support_preference, SupportPreference.LISTEN)
        self.assertTrue(self.session.alliance.goal_aligned)

    def test_rupture_routes_to_repair_before_more_advice(self) -> None:
        update_session_state(self.session, "你还是没理解我，而且一直在重复")
        self.assertEqual(select_strategy(self.session), Strategy.REPAIR_ALLIANCE)


if __name__ == "__main__":
    unittest.main()
