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
        update_session_state(self.session, "先别给我方法，我还没说完")
        self.assertEqual(self.session.user.support_preference, SupportPreference.LISTEN)
        self.assertTrue(self.session.user.advice_paused)
        self.assertTrue(self.session.alliance.goal_aligned)

    def test_finished_speaking_releases_advice_pause_and_requests_tiny_step(self) -> None:
        update_session_state(self.session, "先别给我方法，我还没说完")
        update_session_state(self.session, "我说完了，现在给我一个今天能做的最小下一步")
        self.assertFalse(self.session.user.advice_paused)
        self.assertTrue(self.session.user.tiny_step_requested)
        self.assertEqual(self.session.user.support_preference, SupportPreference.PLAN)

    def test_detects_exclusive_ai_reliance_as_turn_signal(self) -> None:
        update_session_state(self.session, "只有你愿意听我说，我不打算告诉现实里的人")
        self.assertTrue(self.session.user.exclusive_ai_reliance)
        update_session_state(self.session, "我今天还在正常上班")
        self.assertFalse(self.session.user.exclusive_ai_reliance)

    def test_rupture_routes_to_repair_before_more_advice(self) -> None:
        update_session_state(self.session, "你还是没理解我，而且一直在重复")
        self.assertEqual(select_strategy(self.session), Strategy.REPAIR_ALLIANCE)


if __name__ == "__main__":
    unittest.main()
