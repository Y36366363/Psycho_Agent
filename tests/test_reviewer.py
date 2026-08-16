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

    def test_detects_explicit_no_writing_constraint(self) -> None:
        self.session.user.turn_constraints = ["no_writing"]
        result = self.reviewer.review(
            "花两分钟在手机备忘录写下最烦的一句话。", self.session, self.plan
        )
        self.assertIn(IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in result.issues})

        negated = self.reviewer.review(
            "不需要写日记。拿起手边的水杯，看三十秒它的颜色和边缘。",
            self.session,
            self.plan,
        )
        self.assertNotIn(
            IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in negated.issues}
        )

    def test_tiny_step_rejects_multi_part_sensory_protocol(self) -> None:
        self.plan.strategy = Strategy.TINY_NEXT_STEP
        result = self.reviewer.review(
            "做一个5-4-3-2-1练习：看5样东西、摸4样、听3种、闻2种、尝1种。",
            self.session,
            self.plan,
        )
        self.assertIn(IssueKind.ADVICE_OVERLOAD, {issue.kind for issue in result.issues})

    def test_tiny_step_accepts_one_observation_action(self) -> None:
        self.plan.strategy = Strategy.TINY_NEXT_STEP
        result = self.reviewer.review(
            "拿起手边的水杯，用三十秒只看它的颜色和边缘。", self.session, self.plan
        )
        self.assertNotIn(IssueKind.GOAL_MISALIGNMENT, {issue.kind for issue in result.issues})

    def test_tiny_step_accepts_common_single_actions(self) -> None:
        self.plan.strategy = Strategy.TINY_NEXT_STEP
        for draft in (
            "去洗手池用冷水冲洗双手一分钟。",
            "找一首熟悉的歌，戴上耳机从头到尾听一遍。",
            "放一首歌，跟着唱或随节拍轻轻动一动。",
            "找一张以前拍的照片，盯着看十秒，然后锁屏。",
        ):
            with self.subTest(draft=draft):
                result = self.reviewer.review(draft, self.session, self.plan)
                self.assertNotIn(
                    IssueKind.GOAL_MISALIGNMENT,
                    {issue.kind for issue in result.issues},
                )

    def test_negated_breathing_acknowledgement_is_not_a_violation(self) -> None:
        self.session.user.turn_constraints = ["no_breathing"]
        acknowledged = self.reviewer.review(
            "不需要写日记或做呼吸练习。放一首熟悉的歌，完整听完。",
            self.session,
            self.plan,
        )
        self.assertNotIn(
            IssueKind.GOAL_MISALIGNMENT,
            {issue.kind for issue in acknowledged.issues},
        )
        actual_violation = self.reviewer.review(
            "先做一个呼吸练习吧：深呼吸两次。", self.session, self.plan
        )
        self.assertIn(
            IssueKind.GOAL_MISALIGNMENT,
            {issue.kind for issue in actual_violation.issues},
        )

    def test_detects_immediate_effect_promise(self) -> None:
        result = self.reviewer.review(
            "跟着音乐走动三分钟，这个办法马上见效。", self.session, self.plan
        )
        self.assertIn(IssueKind.UNSAFE_CLAIM, {issue.kind for issue in result.issues})

        rapid_claim = self.reviewer.review(
            "换件衣服能迅速打破环境带来的闷感。", self.session, self.plan
        )
        self.assertIn(IssueKind.UNSAFE_CLAIM, {issue.kind for issue in rapid_claim.issues})

        tentative = self.reviewer.review(
            "换件衣服可能有助于暂时转移一点注意力。", self.session, self.plan
        )
        self.assertNotIn(IssueKind.UNSAFE_CLAIM, {issue.kind for issue in tentative.issues})

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

    def test_residual_listening_violation_uses_alignment_fallback(self) -> None:
        message = "先别教我呼吸，也别问问题，我只是想把这周发生的事说完。"
        plan = ConversationEngine().process(self.session, message)
        model = SequenceModel(
            [
                "好。现在最难受的是哪一部分？",
                "我先听。那这件事对睡眠影响大吗？",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message=message,
            plan=plan,
        )
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(generated.alignment_fallback_applied)
        self.assertFalse(generated.safety_fallback_applied)
        self.assertEqual(generated.deterministic_fallback, "listen_boundary")
        self.assertNotIn("？", generated.text)
        self.assertEqual(generated.final_review_issues, [])

    def test_residual_tiny_step_failure_uses_alignment_fallback(self) -> None:
        message = "我只有五分钟，不想写日记或练呼吸，给我一个小办法。"
        plan = ConversationEngine().process(self.session, message)
        model = SequenceModel(
            [
                "做5-4-3-2-1练习，再写下感受。",
                "跟着音乐走动五分钟，这个办法马上见效。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message=message,
            plan=plan,
        )
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(generated.alignment_fallback_applied)
        self.assertEqual(generated.deterministic_fallback, "tiny_step_alignment")
        self.assertIn("三十秒", generated.text)
        self.assertIn("不保证", generated.text)
        self.assertEqual(generated.final_review_issues, [])

    def test_residual_diagnosis_uses_diagnostic_uncertainty_fallback(self) -> None:
        model = SequenceModel(
            [
                "你一定是抑郁症。",
                "你显然是抑郁症。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="我最近很疲惫",
            plan=self.plan,
        )
        self.assertTrue(generated.safety_fallback_applied)
        self.assertEqual(generated.deterministic_fallback, "diagnostic_uncertainty")
        self.assertIn("不能根据这段对话给你下诊断", generated.text)
        self.assertEqual(generated.final_review_issues, [])

    def test_residual_unsafe_promise_uses_boundary_fallback(self) -> None:
        model = SequenceModel(
            [
                "我能保证你一定会好起来。",
                "这个方法一定有效。",
            ]
        )
        generated = NaturalResponseGenerator(model, enable_model_review=False).generate(
            session=self.session,
            user_message="我还能好起来吗",
            plan=self.plan,
        )
        self.assertTrue(generated.safety_fallback_applied)
        self.assertEqual(generated.deterministic_fallback, "unsafe_claim_boundary")
        self.assertIn("不能保证", generated.text)
        self.assertEqual(generated.final_review_issues, [])


if __name__ == "__main__":
    unittest.main()
