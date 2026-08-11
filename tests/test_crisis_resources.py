import unittest

from psycho_agent.crisis_resources import (
    get_crisis_resource_card,
    load_crisis_resources,
    render_crisis_card_html,
)
from psycho_agent.engine import ConversationEngine, format_plan
from psycho_agent.models import SessionState


class CrisisResourceTests(unittest.TestCase):
    def test_registry_entries_are_verified_and_actionable(self) -> None:
        data = load_crisis_resources()
        self.assertEqual(set(data["locales"]), {"zh-CN", "en-US", "en-GB"})
        china = get_crisis_resource_card("zh-CN")
        self.assertIn("12356", china.support_message)
        self.assertIn("tel:12356", {action.href for action in china.actions})

    def test_unknown_locale_does_not_guess_a_phone_number(self) -> None:
        card = get_crisis_resource_card("fr-FR")
        self.assertTrue(card.used_fallback)
        self.assertEqual(card.actions, [])
        self.assertIsNone(card.source_url)

    def test_crisis_plan_exposes_direct_actions_for_interface(self) -> None:
        session = SessionState(session_id="us-crisis", locale="en-US")
        plan = ConversationEngine().process(session, "I will kill myself tonight")
        hrefs = {action.href for action in plan.actions}
        self.assertIn("tel:911", hrefs)
        self.assertIn("tel:988", hrefs)
        self.assertIn("tel:988", format_plan(plan))
        self.assertIn("priority now is immediate safety", plan.fixed_response or "")

        follow_up = ConversationEngine().process(session, "I do not want to discuss it")
        self.assertIn("danger has passed", follow_up.fixed_response or "")

    def test_accessible_html_card_contains_clickable_actions_and_source(self) -> None:
        html = render_crisis_card_html(get_crisis_resource_card("zh-CN"))
        self.assertIn('role="alert"', html)
        self.assertIn('href="tel:12356"', html)
        self.assertIn("Official source", html)


if __name__ == "__main__":
    unittest.main()
