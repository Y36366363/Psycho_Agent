"""Staged intake that avoids interrogating the user with a questionnaire dump."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SessionState, Strategy, TurnPlan


@dataclass(frozen=True, slots=True)
class IntakeStep:
    goal: str
    question: str
    instruction: str


INTAKE_STEPS = (
    IntakeStep(
        goal="Understand what feels most important to the user right now.",
        question="此刻最困扰你的事情是什么？你可以从最想让我知道的部分开始。",
        instruction="Invite the story without demanding a complete history.",
    ),
    IntakeStep(
        goal="Understand duration and recent change without diagnosing.",
        question="这种状态大概持续多久了？最近有没有什么事情让它明显加重？",
        instruction="Ask about time course and triggers in one natural question.",
    ),
    IntakeStep(
        goal="Understand impact and emotional intensity.",
        question="它现在对睡眠、工作学习或关系影响最大的是哪一部分？如果用 0 到 10 分表示难受程度，大概是多少？",
        instruction="Focus on current functioning and let the user estimate intensity.",
    ),
    IntakeStep(
        goal="Learn what kind of support the user wants in this conversation.",
        question="你现在更希望我先听你说、帮你一起看清问题，还是共同想一个可执行的办法？",
        instruction="Offer choices without forcing the user into problem solving.",
    ),
)


def build_intake_plan(session: SessionState) -> TurnPlan:
    """Create the next intake turn, advancing only after the engine receives a reply."""
    index = min(session.intake_step, len(INTAKE_STEPS) - 1)
    step = INTAKE_STEPS[index]
    strategy = Strategy.OPEN_INVITATION if index == 0 else Strategy.CLARIFY
    return TurnPlan(
        phase=session.phase,
        strategy=strategy,
        response_goal=step.goal,
        instructions=[
            step.instruction,
            "Acknowledge one concrete detail from the user's message before asking.",
            "Ask at most one main question and avoid clinical labels.",
            "Do not promise that everything will be fine.",
        ],
        questions=[step.question],
        safety=session.risk,
    )


def intake_complete(session: SessionState) -> bool:
    return session.intake_step >= len(INTAKE_STEPS)
