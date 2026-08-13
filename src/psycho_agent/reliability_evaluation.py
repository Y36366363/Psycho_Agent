"""Evaluate routing invariants across synthetic paraphrases and multi-turn states."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .crisis_audit import audit_crisis_plan
from .engine import ConversationEngine
from .models import SessionState


DEFAULT_CASES = (
    Path(__file__).resolve().parents[2] / "evaluations" / "reliability_cases.json"
)


@dataclass(frozen=True, slots=True)
class ReliabilityResult:
    case_id: str
    variant: int
    passed: bool
    expected: dict[str, Any]
    actual: dict[str, Any]


def load_reliability_cases(path: str | Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not data.get("version") or not isinstance(cases, list) or not cases:
        raise ValueError("Reliability cases require a version and non-empty case list.")
    for case in cases:
        if not case.get("id") or not case.get("variants") or not case.get("expected"):
            raise ValueError("Each reliability case needs id, variants, and expected output.")
    return cases


def run_reliability_evaluation(
    path: str | Path = DEFAULT_CASES,
) -> list[ReliabilityResult]:
    results: list[ReliabilityResult] = []
    for case in load_reliability_cases(path):
        for index, turns in enumerate(case["variants"], start=1):
            messages = [turns] if isinstance(turns, str) else turns
            session = SessionState(
                session_id=f"reliability-{case['id']}-{index}",
                locale=case.get("locale", "zh-CN"),
            )
            engine = ConversationEngine()
            plan = None
            for message in messages:
                plan = engine.process(session, message)
            assert plan is not None
            actual: dict[str, Any] = {
                "phase": plan.phase.value,
                "strategy": plan.strategy.value,
                "risk_level": plan.safety.level.value,
                "risk_subject": plan.safety.subject.value,
                "minimum_actions": len(plan.actions),
                "fixed_response": plan.fixed_response is not None,
            }
            if plan.phase.value == "crisis":
                actual["crisis_audit"] = audit_crisis_plan(plan)["status"]
            expected = case["expected"]
            passed = all(
                actual.get(key, 0) >= value
                if key == "minimum_actions"
                else actual.get(key) == value
                for key, value in expected.items()
            )
            results.append(
                ReliabilityResult(case["id"], index, passed, expected, actual)
            )
    return results


def report_payload(results: list[ReliabilityResult]) -> dict[str, Any]:
    passed = sum(result.passed for result in results)
    by_case: dict[str, bool] = {}
    for result in results:
        by_case[result.case_id] = by_case.get(result.case_id, True) and result.passed
    return {
        "status": "passed" if passed == len(results) else "failed",
        "passed_variants": passed,
        "total_variants": len(results),
        "case_invariance": by_case,
        "failures": [asdict(result) for result in results if not result.passed],
        "interpretation": (
            "Synthetic routing invariance is engineering evidence only; it does not estimate "
            "clinical sensitivity, specificity, or real-world safety."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic routing invariance checks")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = run_reliability_evaluation(args.cases)
    payload = report_payload(results)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if payload["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
