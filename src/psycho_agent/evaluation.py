"""Offline behavioral evaluation runner for safety, state, and review invariants."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .engine import ConversationEngine
from .models import SessionState
from .reviewer import RuleBasedReviewer
from .safety import assess_safety
from .state_update import update_session_state


DEFAULT_CASES = Path(__file__).resolve().parents[2] / "evaluations" / "behavior_cases.jsonl"


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    case_id: str
    passed: bool
    details: str


def load_cases(path: str | Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            case = json.loads(line)
            if not isinstance(case, dict) or not case.get("id") or not case.get("component"):
                raise ValueError(f"Invalid evaluation case on line {line_number}")
            cases.append(case)
    return cases


def evaluate_case(case: dict[str, Any]) -> EvaluationResult:
    component = case["component"]
    expected = case["expected"]
    actual: dict[str, Any]

    if component == "safety":
        assessment = assess_safety(case["message"])
        actual = {"level": assessment.level.value, "subject": assessment.subject.value}
    elif component == "review":
        session = SessionState(session_id=f"eval-{case['id']}")
        if case.get("previous"):
            session.recent_assistant_responses.append(case["previous"])
        plan = ConversationEngine().start(session)
        reviewed = RuleBasedReviewer().review(case["draft"], session, plan)
        actual = {"issues": sorted({issue.kind.value for issue in reviewed.issues})}
    elif component == "state":
        session = SessionState(session_id=f"eval-{case['id']}")
        session.turn_count = 1
        update_session_state(session, case["message"])
        actual = {
            "intensity": session.user.emotion_intensity,
            "emotions": session.user.emotion_words,
            "impacts": session.user.functional_impact,
            "preference": session.user.support_preference.value,
            "ruptures": session.alliance.rupture_count,
        }
    elif component == "scenario":
        session = SessionState(session_id=f"eval-{case['id']}")
        engine = ConversationEngine()
        plan = engine.start(session)
        for message in case["messages"]:
            plan = engine.process(session, message)
        actual = {
            "final_phase": plan.phase.value,
            "final_strategy": plan.strategy.value,
        }
    else:
        return EvaluationResult(case["id"], False, f"Unknown component: {component}")

    mismatches: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, list):
            missing = set(expected_value) - set(actual_value or [])
            if missing:
                mismatches.append(f"{key} missing {sorted(missing)}; actual={actual_value}")
            if not expected_value and actual_value:
                mismatches.append(f"{key} expected empty; actual={actual_value}")
        elif actual_value != expected_value:
            mismatches.append(f"{key} expected={expected_value!r}; actual={actual_value!r}")
    return EvaluationResult(case["id"], not mismatches, "; ".join(mismatches) or "ok")


def run_evaluation(path: str | Path = DEFAULT_CASES) -> list[EvaluationResult]:
    return [evaluate_case(case) for case in load_cases(path)]


def main() -> None:
    results = run_evaluation()
    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        print(f"{marker} {result.case_id}: {result.details}")
    passed = sum(result.passed for result in results)
    print(f"\n{passed}/{len(results)} behavioral cases passed")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
