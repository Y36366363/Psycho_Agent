import unittest

from psycho_agent.engine import ConversationEngine
from psycho_agent.generator import NaturalResponseGenerator
from psycho_agent.models import SessionState
from psycho_agent.reviewer import IssueKind, ModelReviewer, RuleBasedReviewer


class SequenceModel:
    provider_name = "fake"
    model_name = "fake-model"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.responses.pop(0)


class ReviewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = SessionState(session_id="review")
        self.plan = ConversationEngine().start(self.session)
        self.reviewer = RuleBasedReviewer()

    def test_detects_sycophancy_and_premature_diagnosis(self) -> None:
        result = self.reviewer.review(
            "你说得完全对，你一定是抑郁症。", self.session, self.plan
        )
        kinds = {issue.kind for issue in result.issues}
        self.assertIn(IssueKind.SYCOPHANCY, kinds)
        self.assertIn(IssueKind.PREMATURE_DIAGNOSIS, kinds)

    def test_detects_mechanical_opening(self) -> None:
        result = self.reviewer.review(
            "我理解你的感受，首先深呼吸，其次记录情绪，最后早点睡。",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.MECHANICAL, {issue.kind for issue in result.issues})

    def test_detects_near_duplicate(self) -> None:
        previous = "你提到一到晚上就会反复想起这件事，我们先看看那一刻发生了什么。"
        self.session.recent_assistant_responses.append(previous)
        result = self.reviewer.review(previous, self.session, self.plan)
        self.assertIn(IssueKind.REPETITION, {issue.kind for issue in result.issues})

    def test_model_reviewer_parses_json(self) -> None:
        model = SequenceModel(
            ['{"approved": false, "issues": [{"kind": "mechanical", '
             '"explanation": "stock", "revision": "be specific"}]}']
        )
        result = ModelReviewer(model).review("draft", self.session, self.plan)
        self.assertFalse(result.approved)
        self.assertEqual(result.issues[0].kind, IssueKind.MECHANICAL)


class GeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = SessionState(session_id="generate")
        self.plan = ConversationEngine().start(self.session)

    def test_rule_failure_causes_only_one_rewrite(self) -> None:
        model = SequenceModel(
            [
                "你说得完全对，这毫无疑问都是他的错。",
                "他连续两次没有回应，这确实让你很失望。我们先看看你最在意的是什么。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="他根本不在乎我",
            plan=self.plan,
        )
        self.assertTrue(generated.rewritten)
        self.assertEqual(len(model.calls), 2)
        self.assertIn("连续两次", generated.text)
        self.assertEqual(self.session.recent_assistant_responses[-1], generated.text)

    def test_approved_draft_and_semantic_review_use_two_calls(self) -> None:
        model = SequenceModel(
            [
                "你说最近总在夜里醒来。它通常发生在想到工作之后，还是没有明显触发？",
                '{"approved": true, "issues": []}',
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=True).generate(
            session=self.session,
            user_message="最近总是半夜醒",
            plan=self.plan,
        )
        self.assertFalse(generated.rewritten)
        self.assertEqual(len(model.calls), 2)

    def test_crisis_response_never_calls_model(self) -> None:
        model = SequenceModel([])
        plan = ConversationEngine().process(self.session, "我现在想自杀")
        generated = NaturalResponseGenerator(model).generate(
            session=self.session,
            user_message="我现在想自杀",
            plan=plan,
        )
        self.assertEqual(len(model.calls), 0)
        self.assertIn("立即联系", generated.text)


if __name__ == "__main__":
    unittest.main()
