"""Select support actions from session state instead of using one response template."""

from __future__ import annotations

from .models import ConversationPhase, SessionState, Strategy, SupportPreference, TurnPlan


_GOALS = {
    Strategy.REFLECT: "Reflect the central emotional conflict without merely paraphrasing.",
    Strategy.GROUND: "Reduce immediate emotional overload before deeper analysis.",
    Strategy.MAP_PATTERN: "Separate events, interpretations, emotions, and repeated responses.",
    Strategy.GENTLE_CHALLENGE: "Test an important conclusion while preserving emotional safety.",
    Strategy.PROBLEM_SOLVE: "Compare realistic options and their trade-offs collaboratively.",
    Strategy.TINY_NEXT_STEP: "Choose one small action that remains possible under current strain.",
    Strategy.REVIEW_PROGRESS: "Identify what changed, what did not, and what needs a new approach.",
}


def _candidate_strategies(session: SessionState) -> list[Strategy]:
    if (session.user.emotion_intensity or 0) >= 8:
        return [Strategy.GROUND, Strategy.REFLECT]
    if session.user.support_preference is SupportPreference.LISTEN:
        return [Strategy.REFLECT, Strategy.MAP_PATTERN]
    if session.user.support_preference is SupportPreference.PLAN:
        return [Strategy.TINY_NEXT_STEP, Strategy.PROBLEM_SOLVE]
    if session.turn_count >= 8:
        return [Strategy.REVIEW_PROGRESS, Strategy.MAP_PATTERN, Strategy.GENTLE_CHALLENGE]
    return [Strategy.MAP_PATTERN, Strategy.REFLECT, Strategy.GENTLE_CHALLENGE]


def select_strategy(session: SessionState) -> Strategy:
    """Choose a suitable strategy, preferring one not used in the latest two turns."""
    candidates = _candidate_strategies(session)
    recent = set(session.used_strategies[-2:])
    return next((candidate for candidate in candidates if candidate not in recent), candidates[0])


def build_support_plan(session: SessionState) -> TurnPlan:
    strategy = select_strategy(session)
    phase = ConversationPhase.STABILIZE if strategy is Strategy.GROUND else session.phase
    instructions = [
        "Refer to specific user details; do not produce a generic empathy preface.",
        "Distinguish validating an emotion from agreeing with every interpretation.",
        "Introduce no more than one new idea in this turn.",
        "Do not repeat advice or framing used in the two most recent turns.",
        "Use plain, natural language and vary sentence length.",
    ]
    questions: list[str] = []
    if strategy is Strategy.GROUND:
        questions = ["先不急着解决全部问题。此刻身体上最明显的感觉是什么？"]
    elif strategy is Strategy.MAP_PATTERN:
        questions = ["如果只看最近一次发生的情况，事实、你的判断和你的感受分别是什么？"]
    elif strategy is Strategy.GENTLE_CHALLENGE:
        questions = ["有没有哪怕一个细节，可能不完全符合你现在最担心的那个结论？"]
    elif strategy is Strategy.TINY_NEXT_STEP:
        questions = ["在不要求自己立刻好起来的前提下，今天最小但有用的一步会是什么？"]

    return TurnPlan(
        phase=phase,
        strategy=strategy,
        response_goal=_GOALS[strategy],
        instructions=instructions,
        questions=questions,
        safety=session.risk,
    )
