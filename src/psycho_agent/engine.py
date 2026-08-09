"""Top-level conversation orchestrator."""

from __future__ import annotations

from .intake import INTAKE_STEPS, build_intake_plan, intake_complete
from .models import ConversationPhase, RiskLevel, SessionState, Strategy, TurnPlan
from .safety import assess_safety, crisis_turn
from .strategy import build_support_plan


class ConversationEngine:
    """Plan the next conversational action and update auditable session state."""

    def start(self, session: SessionState) -> TurnPlan:
        return build_intake_plan(session)

    def process(self, session: SessionState, user_message: str) -> TurnPlan:
        if not user_message.strip():
            raise ValueError("user_message must not be empty")

        session.turn_count += 1
        session.risk = assess_safety(user_message)

        if session.risk.level in {RiskLevel.ELEVATED, RiskLevel.HIGH, RiskLevel.IMMINENT}:
            session.phase = ConversationPhase.CRISIS
            response, questions = crisis_turn(session.risk)
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
            )
            self._record_plan(session, plan)
            return plan

        if session.phase is ConversationPhase.CRISIS:
            # A single low-signal message does not automatically clear a prior crisis state.
            session.phase = ConversationPhase.STABILIZE

        if session.phase is ConversationPhase.INTAKE:
            session.learned_facts.append(user_message.strip())
            session.intake_step += 1
            if intake_complete(session):
                session.phase = ConversationPhase.EXPLORE
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
    return body
