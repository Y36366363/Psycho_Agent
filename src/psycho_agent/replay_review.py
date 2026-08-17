"""Re-audit immutable blinded outputs with the current deterministic rules."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .engine import ConversationEngine
from .models import SessionState
from .release_policy import release_blocking_issues
from .reviewer import RuleBasedReviewer


RULESET_VERSION = "2026-08-17"


def replay_review(blind_outputs: str | Path) -> dict[str, Any]:
    source = json.loads(Path(blind_outputs).read_text(encoding="utf-8"))
    reviewer = RuleBasedReviewer()
    models: dict[str, Any] = {}

    for alias, model_data in source["models"].items():
        records: list[dict[str, Any]] = []
        for scenario in model_data["scenarios"]:
            engine = ConversationEngine()
            session = SessionState(
                session_id=(
                    f"replay-{alias}-{scenario['id']}-r{scenario.get('replicate', 1)}"
                )
            )
            for turn in scenario["turns"]:
                plan = engine.process(session, turn["user"])
                draft = turn.get("draft")
                response = turn.get("response")
                draft_issues = (
                    sorted(
                        {issue.kind.value for issue in reviewer.review(draft, session, plan).issues}
                    )
                    if draft
                    else []
                )
                released_issues = (
                    sorted(
                        {
                            issue.kind.value
                            for issue in reviewer.review(response, session, plan).issues
                        }
                    )
                    if response
                    else []
                )
                blockers = release_blocking_issues(plan.strategy.value, released_issues)
                records.append(
                    {
                        "scenario_id": scenario["id"],
                        "replicate": scenario.get("replicate", 1),
                        "turn": turn["turn"],
                        "strategy": plan.strategy.value,
                        "draft_issues_current": draft_issues,
                        "released_issues_current": released_issues,
                        "release_blockers_current": blockers,
                    }
                )
                if response:
                    session.recent_user_messages.append(turn["user"].strip())
                    session.recent_assistant_responses.append(response.strip())
                    session.recent_user_messages[:] = session.recent_user_messages[-6:]
                    session.recent_assistant_responses[:] = session.recent_assistant_responses[-6:]
        blocked_turns = sum(bool(record["release_blockers_current"]) for record in records)
        models[alias] = {
            "release_gate": "passed" if blocked_turns == 0 else "failed",
            "release_blocker_turn_count": blocked_turns,
            "turns": records,
        }

    return {
        "audited_at": datetime.now(UTC).isoformat(),
        "ruleset_version": RULESET_VERSION,
        "source_run_at": source.get("run_at"),
        "provider_mapping_used": False,
        "interpretation": (
            "Read-only current-rule replay; original stored issues and outputs are unchanged."
        ),
        "models": models,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay blind outputs through current rules")
    parser.add_argument("blind_outputs")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = replay_review(args.blind_outputs)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
