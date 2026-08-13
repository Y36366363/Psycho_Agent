"""Evidence-bounded maturity reporting that prevents confidence inflation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceGate:
    gate: str
    status: str
    evidence: list[str]
    missing: list[str]


def build_assurance_report(
    *,
    unit_passed: int,
    unit_total: int,
    behavior_passed: int,
    behavior_total: int,
    professional_rating_report: dict[str, Any] | None = None,
    production_evidence: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Keep engineering, professional, clinical, and production claims separate."""
    counts = (unit_passed, unit_total, behavior_passed, behavior_total)
    if any(value < 0 for value in counts):
        raise ValueError("Assurance counts cannot be negative.")
    if unit_passed > unit_total or behavior_passed > behavior_total:
        raise ValueError("Passed counts cannot exceed total counts.")
    engineering_ok = (
        unit_total > 0
        and behavior_total > 0
        and unit_passed == unit_total
        and behavior_passed == behavior_total
    )
    rating_report = professional_rating_report or {}
    professional_ok = (
        rating_report.get("status") == "human_ratings_complete"
        and int(rating_report.get("finalized_reviewer_count", 0)) >= 2
        and rating_report.get("agreement") is not None
    )
    required_production = {
        "public_tls",
        "managed_key_service",
        "encrypted_backups_tested",
        "independent_penetration_test",
        "incident_response_exercised",
        "jurisdiction_review_complete",
    }
    production = production_evidence or {}
    missing_production = sorted(
        key for key in required_production if production.get(key) is not True
    )
    production_ok = not missing_production

    gates = [
        EvidenceGate(
            "engineering_regression",
            "passed" if engineering_ok else "blocked",
            [f"unit:{unit_passed}/{unit_total}", f"behavior:{behavior_passed}/{behavior_total}"],
            [] if engineering_ok else ["all declared automated tests must pass"],
        ),
        EvidenceGate(
            "verified_professional_review",
            "passed" if professional_ok else "pending",
            (
                [f"finalized_verified_reviewers:{rating_report['finalized_reviewer_count']}"]
                if professional_ok
                else []
            ),
            [] if professional_ok else ["at least two verified professionals must finalize blind ratings"],
        ),
        EvidenceGate(
            "clinical_effectiveness",
            "pending",
            [],
            [
                "prospectively defined clinical protocol",
                "representative participant outcomes",
                "adverse-event and dropout analysis",
                "independent clinical/statistical review",
            ],
        ),
        EvidenceGate(
            "production_readiness",
            "passed" if production_ok else "pending",
            sorted(key for key, value in production.items() if value is True),
            missing_production,
        ),
    ]
    allowed = ["research prototype"]
    if engineering_ok:
        allowed.append("automated engineering regression passed")
    if professional_ok:
        allowed.append("verified professional blind review completed")
    if production_ok:
        allowed.append("declared production controls evidenced")
    prohibited = [
        "clinically validated",
        "proven safe or effective",
        "equivalent to a psychologist or therapist",
        "production ready",
    ]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_stage": "research_prototype",
        "gates": [asdict(gate) for gate in gates],
        "allowed_claims": allowed,
        "prohibited_claims": prohibited,
        "interpretation": (
            "Passing automated tests supports only the tested engineering behaviors. "
            "It does not establish clinical effectiveness, general safety, or production readiness."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a non-inflated assurance report")
    parser.add_argument("--unit-passed", type=int, required=True)
    parser.add_argument("--unit-total", type=int, required=True)
    parser.add_argument("--behavior-passed", type=int, required=True)
    parser.add_argument("--behavior-total", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_assurance_report(
        unit_passed=args.unit_passed,
        unit_total=args.unit_total,
        behavior_passed=args.behavior_passed,
        behavior_total=args.behavior_total,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
