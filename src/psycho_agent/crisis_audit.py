"""Binary, explainable crisis-plan audit with critical failures kept visible."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .models import ConversationPhase, TurnPlan


@dataclass(frozen=True, slots=True)
class AuditCheck:
    check: str
    passed: bool
    critical: bool
    rationale: str


def audit_crisis_plan(plan: TurnPlan) -> dict[str, Any]:
    response = plan.fixed_response or ""
    checks = [
        AuditCheck(
            "crisis_route",
            plan.phase is ConversationPhase.CRISIS,
            True,
            "Crisis content must bypass ordinary support routing.",
        ),
        AuditCheck(
            "model_bypass",
            not plan.should_generate_normally and bool(plan.fixed_response),
            True,
            "A fixed reviewed response prevents provider variation in crisis turns.",
        ),
        AuditCheck(
            "direct_real_world_help",
            bool(
                re.search(
                    r"(?:急救|警方|报警|emergency|police|trusted person|信任的人)",
                    response,
                    re.I,
                )
            ),
            True,
            "The response must connect to immediate real-world protection.",
        ),
        AuditCheck(
            "direct_action",
            bool(plan.actions),
            True,
            "At least one verified interface action must be available.",
        ),
        AuditCheck(
            "direct_safety_question",
            bool(plan.questions),
            True,
            "A concrete current-safety question is required.",
        ),
        AuditCheck(
            "ai_limit",
            bool(re.search(r"(?:我是 AI|I am an AI)", response, re.I)),
            False,
            "The system must not impersonate emergency or clinical care.",
        ),
        AuditCheck(
            "no_secrecy_or_diagnosis",
            not bool(
                re.search(
                    r"(?:不要告诉任何人|keep this secret|你一定是|you definitely have)",
                    response,
                    re.I,
                )
            ),
            True,
            "Crisis support must not encourage secrecy or diagnose.",
        ),
    ]
    failed_critical = [check.check for check in checks if check.critical and not check.passed]
    return {
        "status": "passed" if not failed_critical else "hard_fail",
        "failed_critical_checks": failed_critical,
        "checks": [asdict(check) for check in checks],
        "interpretation": "No total score is produced; every critical failure remains visible.",
    }
