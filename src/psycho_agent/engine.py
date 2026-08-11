"""Top-level conversation orchestrator."""

from __future__ import annotations

from .intake import INTAKE_STEPS, build_intake_plan, intake_complete
from .models import ConversationPhase, RiskLevel, SessionState, Strategy, TurnPlan
from .safety import (
    assess_safety,
    crisis_follow_up_turn,
    crisis_turn,
    safety_resolution_confirmed,
)
from .state_update import update_session_state
from .strategy import build_support_plan


class ConversationEngine:
    """Plan the next conversational action and update auditable session state."""

    def start(self, session: SessionState) -> TurnPlan:
        return build_intake_plan(session)

    def process(self, session: SessionState, user_message: str) -> TurnPlan:
        if not user_message.strip():
            raise ValueError("user_message must not be empty")

        session.turn_count += 1
        update_session_state(session, user_message)
        previous_risk = session.risk
        was_crisis = session.phase is ConversationPhase.CRISIS
        session.risk = assess_safety(user_message)

        if session.risk.level in {RiskLevel.ELEVATED, RiskLevel.HIGH, RiskLevel.IMMINENT}:
            session.phase = ConversationPhase.CRISIS
            response, questions, actions = crisis_turn(session.risk, locale=session.locale)
            plan = TurnPlan(
                phase=ConversationPhase.CRISIS,
                strategy=Strategy.CRISIS_SUPPORT,
                response_goal="Establish immediate safety and connect the user to real-world help.",
                instructions=[
                    "Prioritize immediate safety over exploration or reassurance.",
                    "Ask directly about current danger and access to in-person support.",
                    "Do not debate, shame, diagnose, or leave the user with only a hotline suggestion.",
                ],
                questions=questions,
                safety=session.risk,
                should_generate_normally=False,
                fixed_response=response,
                actions=actions,
            )
            self._record_plan(session, plan)
            return plan

        if was_crisis:
            if safety_resolution_confirmed(user_message, previous_risk.subject):
                session.phase = ConversationPhase.STABILIZE
            else:
                session.phase = ConversationPhase.CRISIS
                # Preserve the active crisis subject/level across low-information replies.
                session.risk = previous_risk
                response, questions = crisis_follow_up_turn(
                    previous_risk.subject, locale=session.locale
                )
                plan = TurnPlan(
                    phase=ConversationPhase.CRISIS,
                    strategy=Strategy.SAFETY_FOLLOW_UP,
                    response_goal="Confirm concrete present safety before resuming normal support.",
                    instructions=[
                        "Keep the focus on concrete current safety and real-world support.",
                        "Do not treat silence or a vague denial as proof that risk is resolved.",
                    ],
                    questions=questions,
                    safety=session.risk,
                    should_generate_normally=False,
                    fixed_response=response,
                )
                self._record_plan(session, plan)
                return plan

        if session.phase is ConversationPhase.INTAKE:
            session.learned_facts.append(user_message.strip())
            session.intake_step += 1
            if intake_complete(session):
                session.phase = ConversationPhase.EXPLORE
            if (
                session.user.advice_paused
                or session.user.tiny_step_requested
                or session.user.exclusive_ai_reliance
                or intake_complete(session)
            ):
                plan = build_support_plan(session)
            else:
                plan = build_intake_plan(session)
        else:
            plan = build_support_plan(session)

        self._record_plan(session, plan)
        return plan

    @staticmethod
    def _record_plan(session: SessionState, plan: TurnPlan) -> None:
        session.used_strategies.append(plan.strategy)
        session.recent_response_goals.append(plan.response_goal)
        session.recent_response_goals[:] = session.recent_response_goals[-3:]


def format_plan(plan: TurnPlan) -> str:
    """Human-readable demo output before an LLM adapter exists."""
    if plan.fixed_response:
        body = plan.fixed_response
    else:
        body = f"[本轮目标] {plan.response_goal}"
    if plan.questions:
        body += "\n[建议问题] " + plan.questions[0]
    if plan.actions:
        body += "\n[可操作资源] " + " | ".join(
            f"{action.label}: {action.href}" for action in plan.actions
        )
    return body
