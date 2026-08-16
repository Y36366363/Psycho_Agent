"""Non-compensatory response-release policy shared by live and replay evaluation."""

from __future__ import annotations

from collections.abc import Iterable


ALWAYS_BLOCKING_FINAL_ISSUES = frozenset(
    {
        "boundary_overreach",
        "clinical_overreach",
        "epistemic_reinforcement",
        "premature_diagnosis",
        "unsafe_claim",
        "goal_misalignment",
    }
)


def release_blocking_issues(strategy: str, issues: Iterable[str]) -> list[str]:
    """Return sorted issue kinds that make a response ineligible for release."""
    kinds = set(issues)
    blockers = kinds & ALWAYS_BLOCKING_FINAL_ISSUES
    if strategy == "tiny_next_step" and "advice_overload" in kinds:
        blockers.add("advice_overload")
    return sorted(blockers)
