"""Typed domain models shared by the conversation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    IMMINENT = "imminent"


class RiskSubject(StrEnum):
    SELF = "self"
    OTHER = "other"
    UNCLEAR = "unclear"


class ConversationPhase(StrEnum):
    INTAKE = "intake"
    STABILIZE = "stabilize"
    EXPLORE = "explore"
    INTERVENE = "intervene"
    ACTION = "action"
    REVIEW = "review"
    CRISIS = "crisis"


class SupportPreference(StrEnum):
    UNKNOWN = "unknown"
    LISTEN = "listen"
    UNDERSTAND = "understand"
    PLAN = "plan"


class Strategy(StrEnum):
    OPEN_INVITATION = "open_invitation"
    CLARIFY = "clarify"
    REFLECT = "reflect"
    GROUND = "ground"
    MAP_PATTERN = "map_pattern"
    GENTLE_CHALLENGE = "gentle_challenge"
    PROBLEM_SOLVE = "problem_solve"
    TINY_NEXT_STEP = "tiny_next_step"
    REVIEW_PROGRESS = "review_progress"
    REPAIR_ALLIANCE = "repair_alliance"
    REAL_WORLD_BRIDGE = "real_world_bridge"
    CLINICAL_SCOPE_BOUNDARY = "clinical_scope_boundary"
    SAFETY_FOLLOW_UP = "safety_follow_up"
    CRISIS_SUPPORT = "crisis_support"


@dataclass(slots=True)
class SafetyAssessment:
    level: RiskLevel = RiskLevel.LOW
    subject: RiskSubject = RiskSubject.UNCLEAR
    matched_signals: list[str] = field(default_factory=list)
    requires_direct_check: bool = False
    rationale: str = "No explicit risk signal detected."


@dataclass(slots=True)
class UserState:
    presenting_problem: str | None = None
    emotion_words: list[str] = field(default_factory=list)
    emotion_intensity: int | None = None
    duration: str | None = None
    functional_impact: list[str] = field(default_factory=list)
    support_preference: SupportPreference = SupportPreference.UNKNOWN
    attempted_actions: list[str] = field(default_factory=list)
    working_hypotheses: list[str] = field(default_factory=list)
    advice_paused: bool = False
    tiny_step_requested: bool = False
    exclusive_ai_reliance: bool = False


@dataclass(slots=True)
class AllianceState:
    """Small process model inspired by bond, goal, and task alignment."""

    goal_aligned: bool = False
    task_aligned: bool = False
    rupture_count: int = 0
    last_rupture_turn: int | None = None


@dataclass(slots=True)
class ClientFeedbackState:
    """Explicit user-side experience signals; unknown is distinct from positive."""

    felt_understood: bool | None = None
    pressure_reported: bool = False
    action_rejected: bool = False
    action_rejection_reasons: list[str] = field(default_factory=list)
    exit_intent: bool = False
    exit_reasons: list[str] = field(default_factory=list)
    correction_count: int = 0


@dataclass(frozen=True, slots=True)
class ActionLink:
    """A directly renderable escalation action for a future web or mobile UI."""

    label: str
    href: str
    kind: str


@dataclass(slots=True)
class SessionState:
    session_id: str
    locale: str = "zh-CN"
    phase: ConversationPhase = ConversationPhase.INTAKE
    user: UserState = field(default_factory=UserState)
    risk: SafetyAssessment = field(default_factory=SafetyAssessment)
    alliance: AllianceState = field(default_factory=AllianceState)
    client_feedback: ClientFeedbackState = field(default_factory=ClientFeedbackState)
    turn_count: int = 0
    intake_step: int = 0
    used_strategies: list[Strategy] = field(default_factory=list)
    learned_facts: list[str] = field(default_factory=list)
    unresolved_threads: list[str] = field(default_factory=list)
    recent_response_goals: list[str] = field(default_factory=list)
    recent_user_messages: list[str] = field(default_factory=list)
    recent_assistant_responses: list[str] = field(default_factory=list)
    review_issue_history: list[list[str]] = field(default_factory=list)


@dataclass(slots=True)
class TurnPlan:
    phase: ConversationPhase
    strategy: Strategy
    response_goal: str
    instructions: list[str]
    questions: list[str] = field(default_factory=list)
    safety: SafetyAssessment = field(default_factory=SafetyAssessment)
    should_generate_normally: bool = True
    fixed_response: str | None = None
    actions: list[ActionLink] = field(default_factory=list)

    def as_prompt_context(self) -> str:
        """Return a compact provider-neutral instruction block for an LLM adapter."""
        instruction_text = "\n".join(f"- {item}" for item in self.instructions)
        question_text = "\n".join(f"- {item}" for item in self.questions) or "- None required"
        return (
            f"Conversation phase: {self.phase.value}\n"
            f"Support strategy: {self.strategy.value}\n"
            f"Response goal: {self.response_goal}\n"
            f"Instructions:\n{instruction_text}\n"
            f"Candidate questions:\n{question_text}"
        )
