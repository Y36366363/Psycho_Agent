"""Review generated support responses before they reach the user."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum

from .models import SessionState, Strategy, TurnPlan
from .providers import ModelError, TextModel


class IssueKind(StrEnum):
    SYCOPHANCY = "sycophancy"
    MECHANICAL = "mechanical"
    REPETITION = "repetition"
    PREMATURE_DIAGNOSIS = "premature_diagnosis"
    ADVICE_OVERLOAD = "advice_overload"
    UNSAFE_CLAIM = "unsafe_claim"
    BOUNDARY_OVERREACH = "boundary_overreach"
    QUESTION_OVERLOAD = "question_overload"
    GOAL_MISALIGNMENT = "goal_misalignment"
    EPISTEMIC_REINFORCEMENT = "epistemic_reinforcement"
    REVIEW_FAILURE = "review_failure"


@dataclass(frozen=True, slots=True)
class ReviewIssue:
    kind: IssueKind
    explanation: str
    revision: str


@dataclass(slots=True)
class ReviewResult:
    approved: bool
    issues: list[ReviewIssue] = field(default_factory=list)
    source: str = "rules"


class RuleBasedReviewer:
    """Deterministic guardrails for common style and safety failures."""

    _SYCOPHANTIC = (
        r"你说得(?:完全|太|非常)对",
        r"毫无疑问.*(?:都是|就是).*(?:他们|他|她)的错",
        r"你没有任何问题",
        r"你值得全世界最好的",
    )
    _MECHANICAL = (
        r"^(?:我理解你的感受|听起来你感到|感谢你的分享)[，,。]",
        r"(?:首先|第一)[，,].*(?:其次|第二)[，,].*(?:最后|第三)[，,]",
        r"作为(?:一个)?AI(?:语言模型)?",
    )
    _DIAGNOSIS = (
        r"你(?:就是|一定是|显然是|患有).{0,8}(?:抑郁症|焦虑症|双相|人格障碍|创伤后应激)",
        r"这证明你.{0,8}(?:有病|心理疾病|人格障碍)",
        r"you (?:definitely|clearly) have .{0,20}(?:disorder|depression|anxiety)",
    )
    _UNSAFE = (
        r"你(?:肯定|一定)会好起来",
        r"不需要找(?:医生|心理咨询师|专业人士)",
        r"我能保证",
    )
    _BOUNDARY = (
        r"只有我(?:真正)?懂你",
        r"你只需要(?:跟|和)我聊",
        r"不要告诉任何人",
        r"别去找别人",
        r"我永远不会离开你",
        r"我是你唯一(?:能|可以)?依靠",
    )
    _EPISTEMIC_REINFORCEMENT = (
        r"(?:这|那|摄像头|他们的反应).{0,16}(?:印证|证实|证明)(?:了|你的|你之前|这个).{0,12}(?:担心|判断|监视|针对)",
        r"难怪你会觉得.{0,16}(?:他们|同事).{0,8}(?:针对|监视|合谋)",
    )
    _CONCRETE_ACTION = (
        r"(?:最小|下一|第一)步(?:可以|是|：|:)",
        r"(?:花|用)\s*\d+\s*(?:分钟|秒)",
        r"(?:写下|记下|发一条|打一个|关掉|放下|走到|喝一口|设置一个)",
    )
    _AI_LIMIT = (
        r"(?:我|这里|这个系统).{0,8}(?:是|只是).{0,4}(?:AI|人工智能)",
        r"(?:AI|人工智能).{0,12}(?:不能|无法|能力有限|替代不了|不能替代)",
    )
    _REAL_WORLD_SUPPORT = (
        r"(?:现实|线下|身边).{0,10}(?:支持|帮助|人|连接)",
        r"(?:可信任的人|信任的人|家人|朋友|心理咨询师|专业人士|医生)",
    )

    def review(self, draft: str, session: SessionState, plan: TurnPlan) -> ReviewResult:
        issues: list[ReviewIssue] = []
        self._match_patterns(
            draft,
            self._SYCOPHANTIC,
            issues,
            IssueKind.SYCOPHANCY,
            "The response agrees with a conclusion too absolutely.",
            "Validate the emotion while treating conclusions as hypotheses.",
        )
        self._match_patterns(
            draft,
            self._MECHANICAL,
            issues,
            IssueKind.MECHANICAL,
            "The response uses a stock or visibly templated opening.",
            "Open with one specific detail from the user's message and use natural prose.",
        )
        self._match_patterns(
            draft,
            self._DIAGNOSIS,
            issues,
            IssueKind.PREMATURE_DIAGNOSIS,
            "The response assigns a clinical label without a proper assessment.",
            "Remove diagnosis and describe only observed experiences or patterns.",
        )
        self._match_patterns(
            draft,
            self._UNSAFE,
            issues,
            IssueKind.UNSAFE_CLAIM,
            "The response makes an unsafe promise or discourages professional care.",
            "Remove guarantees and preserve appropriate professional-care options.",
        )
        self._match_patterns(
            draft,
            self._BOUNDARY,
            issues,
            IssueKind.BOUNDARY_OVERREACH,
            "The response encourages exclusivity, secrecy, or emotional dependency.",
            "Preserve relational boundaries and support safe real-world connection.",
        )
        self._match_patterns(
            draft,
            self._EPISTEMIC_REINFORCEMENT,
            issues,
            IssueKind.EPISTEMIC_REINFORCEMENT,
            "The response treats ambiguous evidence as confirmation of a feared interpretation.",
            "Validate distress while clearly separating observations from unverified conclusions.",
        )

        if session.user.advice_paused and re.search(r"[？?]", draft):
            issues.append(
                ReviewIssue(
                    IssueKind.GOAL_MISALIGNMENT,
                    "The user said they had not finished, but the response asks another question.",
                    "Reflect one specific meaning without questions, techniques, or advice.",
                )
            )

        if plan.strategy is Strategy.TINY_NEXT_STEP and not any(
            re.search(pattern, draft, re.IGNORECASE) for pattern in self._CONCRETE_ACTION
        ):
            issues.append(
                ReviewIssue(
                    IssueKind.GOAL_MISALIGNMENT,
                    "The user requested a small next step, but no concrete action was supplied.",
                    "Give one low-effort action directly instead of continuing assessment.",
                )
            )

        if session.user.exclusive_ai_reliance:
            has_limit = any(
                re.search(pattern, draft, re.IGNORECASE) for pattern in self._AI_LIMIT
            )
            has_bridge = any(
                re.search(pattern, draft, re.IGNORECASE)
                for pattern in self._REAL_WORLD_SUPPORT
            )
            if not (has_limit and has_bridge):
                issues.append(
                    ReviewIssue(
                        IssueKind.BOUNDARY_OVERREACH,
                        "Exclusive AI reliance was expressed without both an AI limit "
                        "and an offline bridge.",
                        "Name the AI's limits and offer one non-coercive route to "
                        "real-world support.",
                    )
                )

        if len(re.findall(r"[？?]", draft)) >= 3:
            issues.append(
                ReviewIssue(
                    IssueKind.QUESTION_OVERLOAD,
                    "The response asks three or more questions at once.",
                    "Ask one main question that matches the current conversation goal.",
                )
            )

        if len(re.findall(r"(?:^|\n)\s*(?:\d+[.、]|[-*])\s+", draft)) >= 4:
            issues.append(
                ReviewIssue(
                    IssueKind.ADVICE_OVERLOAD,
                    "The response gives four or more list items in one turn.",
                    "Keep only the single most useful idea or next step.",
                )
            )

        for previous in session.recent_assistant_responses[-3:]:
            if self._similarity(draft, previous) >= 0.68:
                issues.append(
                    ReviewIssue(
                        IssueKind.REPETITION,
                        "The draft substantially repeats a recent assistant response.",
                        "Use a different conversational action and add information not "
                        "already stated.",
                    )
                )
                break
        return ReviewResult(approved=not issues, issues=issues, source="rules")

    @staticmethod
    def _match_patterns(
        draft: str,
        patterns: tuple[str, ...],
        issues: list[ReviewIssue],
        kind: IssueKind,
        explanation: str,
        revision: str,
    ) -> None:
        if any(re.search(pattern, draft, re.IGNORECASE | re.DOTALL) for pattern in patterns):
            issues.append(ReviewIssue(kind, explanation, revision))

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        def bigrams(text: str) -> set[str]:
            compact = re.sub(r"\s+", "", text.lower())
            return {compact[index : index + 2] for index in range(max(0, len(compact) - 1))}

        left_parts, right_parts = bigrams(left), bigrams(right)
        if not left_parts or not right_parts:
            return 0.0
        return len(left_parts & right_parts) / len(left_parts | right_parts)


class ModelReviewer:
    """A second-pass semantic reviewer using a text model as a constrained critic."""

    _SYSTEM = """You are a strict quality reviewer for a transparent AI psychological-support product.
Judge only the proposed reply, not the user. Look for unsupported agreement or flattery,
mechanical stock phrasing, repetition, premature diagnosis, too much advice, false promises,
and failure to follow the turn plan. Return JSON only, with this exact shape:
{"approved": true, "issues": [{"kind": "mechanical", "explanation": "...", "revision": "..."}]}
Allowed kinds: sycophancy, mechanical, repetition, premature_diagnosis, advice_overload,
unsafe_claim, boundary_overreach, question_overload, goal_misalignment,
epistemic_reinforcement. Do not include markdown."""

    def __init__(self, model: TextModel) -> None:
        self.model = model

    def review(self, draft: str, session: SessionState, plan: TurnPlan) -> ReviewResult:
        previous = "\n---\n".join(session.recent_assistant_responses[-2:]) or "None"
        prompt = (
            f"TURN PLAN\n{plan.as_prompt_context()}\n\n"
            f"RECENT ASSISTANT RESPONSES\n{previous}\n\nPROPOSED REPLY\n{draft}"
        )
        try:
            raw = self.model.complete(self._SYSTEM, prompt)
            data = self._parse_json(raw)
            issues = [self._parse_issue(item) for item in data.get("issues", [])]
            issues = [issue for issue in issues if issue is not None]
            approved = bool(data.get("approved", False)) and not issues
            return ReviewResult(approved=approved, issues=issues, source="model")
        except (ModelError, ValueError, TypeError, json.JSONDecodeError):
            return ReviewResult(
                approved=True,
                issues=[
                    ReviewIssue(
                        IssueKind.REVIEW_FAILURE,
                        "The optional semantic reviewer did not return valid JSON.",
                        "No automatic revision requested; retain deterministic review result.",
                    )
                ],
                source="model-fallback",
            )

    @staticmethod
    def _parse_json(raw: str) -> dict[str, object]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Reviewer output must be an object")
        return data

    @staticmethod
    def _parse_issue(item: object) -> ReviewIssue | None:
        if not isinstance(item, dict):
            return None
        try:
            kind = IssueKind(str(item["kind"]))
            explanation = str(item["explanation"]).strip()
            revision = str(item["revision"]).strip()
        except (KeyError, ValueError):
            return None
        return ReviewIssue(kind, explanation, revision)
