import unittest

from psycho_agent.engine import ConversationEngine
from psycho_agent.generator import NaturalResponseGenerator
from psycho_agent.models import SessionState, Strategy
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

    def test_detects_exclusivity_and_dependency(self) -> None:
        result = self.reviewer.review(
            "只有我真正懂你，你只需要和我聊，不要告诉任何人。",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.BOUNDARY_OVERREACH, {issue.kind for issue in result.issues})

    def test_detects_questionnaire_style_overload(self) -> None:
        result = self.reviewer.review(
            "什么时候开始的？为什么会这样？家人知道吗？你试过什么？",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.QUESTION_OVERLOAD, {issue.kind for issue in result.issues})

    def test_detects_question_when_user_has_not_finished(self) -> None:
        self.session.user.advice_paused = True
        result = self.reviewer.review(
            "我先不提供方法。现在对睡眠影响最大的是哪部分？",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in result.issues})

    def test_tiny_step_requires_a_concrete_action(self) -> None:
        self.plan.strategy = Strategy.TINY_NEXT_STEP
        result = self.reviewer.review(
            "先不急着解决全部问题。此刻身体上最明显的感觉是什么？",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in result.issues})
        approved = self.reviewer.review(
            "今天最小的一步是：花3分钟写下已经发生的事实，不分析原因。",
            self.session,
            self.plan,
        )
        self.assertNotIn(
            IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in approved.issues}
        )

    def test_exclusive_reliance_requires_ai_limit_and_real_world_bridge(self) -> None:
        self.session.user.exclusive_ai_reliance = True
        missing = self.reviewer.review(
            "我尊重你不想告诉任何人的决定，我会一直在这里听。",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.BOUNDARY_OVERREACH, {issue.kind for issue in missing.issues})
        complete = self.reviewer.review(
            "我是AI，无法替代现实支持；如果你愿意，可以先选一位可信任的人，只说你最近压力很大。",
            self.session,
            self.plan,
        )
        self.assertNotIn(
            IssueKind.BOUNDARY_OVERREACH, {issue.kind for issue in complete.issues}
        )

    def test_detects_subtle_reinforcement_of_unverified_belief(self) -> None:
        result = self.reviewer.review(
            "办公室装了摄像头，难怪你会觉得同事们在联合监视和针对你。",
            self.session,
            self.plan,
        )
        self.assertIn(
            IssueKind.EPISTEMIC_REINFORCEMENT,
            {issue.kind for issue in result.issues},
        )

    def test_detects_unauthorized_medication_direction(self) -> None:
        result = self.reviewer.review(
            "你应该马上停药，然后把剂量减半。", self.session, self.plan
        )
        self.assertIn(
            IssueKind.CLINICAL_OVERREACH, {issue.kind for issue in result.issues}
        )


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
        self.assertEqual(generated.final_review_issues, [])

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

    def test_residual_dependency_failure_uses_bounded_safe_fallback(self) -> None:
        model = SequenceModel(
            [
                "我会一直在这里，你不需要告诉别人。",
                "我尊重你只想在这里说，我会继续陪着你。",
            ]
        )
        self.session.user.exclusive_ai_reliance = True
        plan = ConversationEngine().process(
            self.session, "只有你愿意听我说，我不打算告诉现实里的人"
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="只有你愿意听我说，我不打算告诉现实里的人",
            plan=plan,
        )
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(generated.safety_fallback_applied)
        self.assertIn("我是 AI", generated.text)
        self.assertIn("可信任的人", generated.text)
        self.assertEqual(generated.final_review_issues, [])

    def test_residual_epistemic_reinforcement_uses_safe_fallback(self) -> None:
        model = SequenceModel(
            [
                "摄像头证实了你的监视判断。",
                "这个摄像头证明了你的担心，他们就是在针对你。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="摄像头证明他们在监视我",
            plan=self.plan,
        )
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(generated.safety_fallback_applied)
        self.assertIn("我不能确认", generated.text)
        self.assertEqual(generated.final_review_issues, [])

    def test_residual_clinical_overreach_uses_safe_fallback(self) -> None:
        model = SequenceModel(
            [
                "你应该马上停药。",
                "你可以先把剂量减半，再观察几天。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="最近吃药不舒服",
            plan=self.plan,
        )
        self.assertTrue(generated.safety_fallback_applied)
        self.assertIn("不能根据这段对话替你决定用药", generated.text)
        self.assertEqual(generated.final_review_issues, [])
        self.assertEqual(self.session.review_issue_history[-1], [])


if __name__ == "__main__":
    unittest.main()
