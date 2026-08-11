import unittest

from psycho_agent.client_metrics import client_feedback_snapshot
from psycho_agent.models import SessionState
from psycho_agent.state_update import update_session_state


class ClientMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = SessionState(session_id="client-metrics")

    def test_understanding_is_unknown_until_user_explicitly_reports_it(self) -> None:
        self.assertIsNone(client_feedback_snapshot(self.session)["felt_understood"])
        update_session_state(self.session, "你这次终于理解我卡住的地方了")
        self.assertTrue(self.session.client_feedback.felt_understood)
        update_session_state(self.session, "不对，你还是没理解我")
        self.assertFalse(self.session.client_feedback.felt_understood)
        self.assertEqual(self.session.client_feedback.correction_count, 1)

    def test_pressure_rejection_and_exit_reasons_are_separate(self) -> None:
        update_session_state(self.session, "别逼我，这个方法我做不到，最近真的没时间")
        update_session_state(self.session, "我担心隐私会泄露，所以不聊了")
        state = self.session.client_feedback
        self.assertTrue(state.pressure_reported)
        self.assertTrue(state.action_rejected)
        self.assertIn("infeasible", state.action_rejection_reasons)
        self.assertTrue(state.exit_intent)
        self.assertIn("privacy_concern", state.exit_reasons)


if __name__ == "__main__":
    unittest.main()
