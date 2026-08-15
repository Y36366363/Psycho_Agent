"""Run a provider-blinded live comparison over shared synthetic scenarios."""

from __future__ import annotations

import argparse
import json
import random
import secrets
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import ConfigurationError, ProviderSettings, load_dotenv
from .engine import ConversationEngine
from .generator import NaturalResponseGenerator
from .models import SessionState
from .providers import ModelError, TextModel, create_model


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENARIOS = ROOT / "evaluations" / "live_scenarios.json"
DEFAULT_RUBRIC = ROOT / "evaluations" / "qualitative_rubric.json"


@dataclass(slots=True)
class TurnRecord:
    turn: int
    user: str
    phase: str
    strategy: str
    response: str | None
    draft: str | None
    rewritten: bool
    draft_issues: list[str]
    final_issues: list[str]
    safety_fallback_applied: bool
    latency_seconds: float
    error: str | None = None


def load_scenarios(path: str | Path = DEFAULT_SCENARIOS) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data.get("scenarios"), list) or not data["scenarios"]:
        raise ValueError("Live scenario file must contain a non-empty scenarios list.")
    for scenario in data["scenarios"]:
        if not scenario.get("id") or not scenario.get("turns"):
            raise ValueError("Every live scenario needs an id and at least one turn.")
    return data


def load_rubric(path: str | Path = DEFAULT_RUBRIC) -> dict[str, Any]:
    """Load the versioned, stage-aware qualitative comparison rubric."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    dimensions = data.get("dimensions")
    if not data.get("version") or not isinstance(dimensions, list) or not dimensions:
        raise ValueError("Qualitative rubric needs a version and non-empty dimensions.")
    for dimension in dimensions:
        if not dimension.get("id") or dimension.get("stage") not in {
            "exploration",
            "insight",
            "action",
            "cross_cutting",
        }:
            raise ValueError("Every rubric dimension needs an id and supported stage.")
        anchors = dimension.get("anchors", {})
        if not all(str(score) in anchors for score in (1, 3, 5)):
            raise ValueError("Every rubric dimension needs behavioral anchors for 1, 3, and 5.")
    return data


def _aliases(
    provider_names: list[str], rng: random.Random | secrets.SystemRandom
) -> dict[str, str]:
    labels = [f"Model-{chr(65 + index)}" for index in range(len(provider_names))]
    rng.shuffle(labels)
    return dict(zip(provider_names, labels, strict=True))


def _run_scenario(
    alias: str,
    model: TextModel,
    scenario: dict[str, Any],
    *,
    replicate: int = 1,
) -> dict[str, Any]:
    """Run a complete scenario so retries retain their conversational context."""
    engine = ConversationEngine()
    session = SessionState(session_id=f"live-{alias}-{scenario['id']}-r{replicate}")
    generator = NaturalResponseGenerator(model, enable_model_review=False)
    records: list[TurnRecord] = []
    for turn_number, user_message in enumerate(scenario["turns"], start=1):
        plan = engine.process(session, user_message)
        started = time.perf_counter()
        try:
            generated = generator.generate(
                session=session,
                user_message=user_message,
                plan=plan,
            )
            elapsed = time.perf_counter() - started
            record = TurnRecord(
                turn=turn_number,
                user=user_message,
                phase=plan.phase.value,
                strategy=plan.strategy.value,
                response=generated.text,
                draft=generated.draft,
                rewritten=generated.rewritten,
                draft_issues=[issue.kind.value for issue in generated.review_issues],
                final_issues=[issue.kind.value for issue in generated.final_review_issues],
                safety_fallback_applied=generated.safety_fallback_applied,
                latency_seconds=round(elapsed, 3),
            )
        except ModelError as exc:
            elapsed = time.perf_counter() - started
            record = TurnRecord(
                turn=turn_number,
                user=user_message,
                phase=plan.phase.value,
                strategy=plan.strategy.value,
                response=None,
                draft=None,
                rewritten=False,
                draft_issues=[],
                final_issues=[],
                safety_fallback_applied=False,
                latency_seconds=round(elapsed, 3),
                error=str(exc),
            )
        records.append(record)
    return {
        "id": scenario["id"],
        "replicate": replicate,
        "title": scenario["title"],
        "intent": scenario["intent"],
        "turns": [asdict(record) for record in records],
    }


def run_comparison(
    models: dict[str, TextModel],
    scenario_data: dict[str, Any],
    output_dir: str | Path,
    *,
    rng: random.Random | secrets.SystemRandom | None = None,
    repetitions: int = 1,
) -> tuple[Path, Path]:
    """Generate outputs and seal provider identities in a separate ignored file."""
    if len(models) < 2:
        raise ValueError("Blind comparison requires at least two providers.")
    if not 1 <= repetitions <= 10:
        raise ValueError("Repetitions must be between 1 and 10.")
    rng = rng or secrets.SystemRandom()
    mapping = _aliases(list(models), rng)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    by_alias: dict[str, Any] = {}
    for provider_name, model in models.items():
        alias = mapping[provider_name]
        scenario_results = [
            _run_scenario(alias, model, scenario, replicate=replicate)
            for replicate in range(1, repetitions + 1)
            for scenario in scenario_data["scenarios"]
        ]
        by_alias[alias] = {"scenarios": scenario_results}

    ordered = {alias: by_alias[alias] for alias in sorted(by_alias)}
    blind_data = {
        "run_at": datetime.now(UTC).isoformat(),
        "scenario_version": scenario_data.get("version"),
        "repetitions": repetitions,
        "rubric_version": load_rubric().get("version"),
        "review_mode": (
            "deterministic rules with at most one rewrite; semantic model review disabled"
        ),
        "models": ordered,
    }
    key_data = {
        "sealed_at": blind_data["run_at"],
        "mapping": {
            alias: {
                "provider": provider_name,
                "model": models[provider_name].model_name,
            }
            for provider_name, alias in mapping.items()
        },
    }
    blind_path = destination / "blind_outputs.json"
    key_path = destination / "provider_key.json"
    blind_path.write_text(
        json.dumps(blind_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    key_path.write_text(json.dumps(key_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return blind_path, key_path


def retry_failed_scenarios(
    models: dict[str, TextModel],
    scenario_data: dict[str, Any],
    output_dir: str | Path,
) -> tuple[Path, int]:
    """Re-run entire failed scenarios while keeping provider identities sealed."""
    destination = Path(output_dir)
    blind_path = destination / "blind_outputs.json"
    key_path = destination / "provider_key.json"
    blind_data = json.loads(blind_path.read_text(encoding="utf-8"))
    key_data = json.loads(key_path.read_text(encoding="utf-8"))
    scenarios_by_id = {scenario["id"]: scenario for scenario in scenario_data["scenarios"]}
    retried: dict[str, list[str]] = {}

    for alias, model_data in blind_data["models"].items():
        failed_runs = [
            (scenario["id"], scenario.get("replicate", 1))
            for scenario in model_data["scenarios"]
            if any(turn.get("error") for turn in scenario["turns"])
        ]
        if not failed_runs:
            continue
        provider_name = key_data["mapping"][alias]["provider"]
        if provider_name not in models:
            raise ValueError(f"No configured model for the sealed provider behind {alias}.")
        retried[alias] = [f"{scenario_id}:r{replicate}" for scenario_id, replicate in failed_runs]
        replacements = {
            (scenario_id, replicate): _run_scenario(
                alias,
                models[provider_name],
                scenarios_by_id[scenario_id],
                replicate=replicate,
            )
            for scenario_id, replicate in failed_runs
        }
        model_data["scenarios"] = [
            replacements.get((scenario["id"], scenario.get("replicate", 1)), scenario)
            for scenario in model_data["scenarios"]
        ]

    if retried:
        blind_data.setdefault("retry_history", []).append(
            {
                "retried_at": datetime.now(UTC).isoformat(),
                "scenarios_by_alias": retried,
                "policy": "complete scenario rerun after any failed turn",
            }
        )
        blind_path.write_text(
            json.dumps(blind_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    score_path = destination / "automatic_scores.json"
    score_path.write_text(
        json.dumps(automatic_scores(blind_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return blind_path, sum(len(ids) for ids in retried.values())


def automatic_scores(blind_path: str | Path) -> dict[str, dict[str, float | int]]:
    data = json.loads(Path(blind_path).read_text(encoding="utf-8"))
    scores: dict[str, dict[str, float | int]] = {}
    for alias, model_data in data["models"].items():
        turns = [turn for scenario in model_data["scenarios"] for turn in scenario["turns"]]
        successful = [turn for turn in turns if turn["response"] is not None]
        latencies = [turn["latency_seconds"] for turn in successful]
        completed_runs = sum(
            all(turn.get("response") is not None for turn in scenario["turns"])
            for scenario in model_data["scenarios"]
        )
        final_issue_turns = sum(bool(turn["final_issues"]) for turn in successful)
        scores[alias] = {
            "scenario_runs": len(model_data["scenarios"]),
            "completed_scenario_runs": completed_runs,
            "turns": len(turns),
            "successful_turns": len(successful),
            "failed_turns": len(turns) - len(successful),
            "completion_rate": round(len(successful) / max(1, len(turns)), 3),
            "draft_issue_count": sum(len(turn["draft_issues"]) for turn in turns),
            "final_issue_count": sum(len(turn["final_issues"]) for turn in turns),
            "final_issue_turn_rate": round(final_issue_turns / max(1, len(successful)), 3),
            "rewrite_count": sum(bool(turn["rewritten"]) for turn in turns),
            "rewrite_rate": round(
                sum(bool(turn["rewritten"]) for turn in turns) / max(1, len(turns)), 3
            ),
            "safety_fallback_count": sum(
                bool(turn.get("safety_fallback_applied")) for turn in turns
            ),
            "average_latency_seconds": round(
                sum(turn["latency_seconds"] for turn in turns) / len(turns), 3
            ),
            "median_success_latency_seconds": round(statistics.median(latencies), 3)
            if latencies
            else 0.0,
            "max_success_latency_seconds": round(max(latencies), 3) if latencies else 0.0,
            "average_response_characters": round(
                sum(len(turn["response"] or "") for turn in successful) / max(1, len(successful))
            ),
        }
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a blind live model comparison")
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Run each complete scenario 1-10 times to expose sampling variability",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="Re-run complete scenarios containing failures without revealing the mapping",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["openai", "deepseek", "gemini"],
        choices=["openai", "deepseek", "gemini"],
    )
    args = parser.parse_args()

    load_dotenv()
    try:
        settings = [ProviderSettings.from_env(provider) for provider in args.providers]
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
    models = {item.provider: create_model(item) for item in settings}
    scenario_data = load_scenarios(args.scenarios)
    if args.retry_failures:
        blind_path, retried_count = retry_failed_scenarios(
            models, scenario_data, args.output_dir
        )
        print(f"Retried complete scenarios: {retried_count}")
    else:
        blind_path, _ = run_comparison(
            models,
            scenario_data,
            args.output_dir,
            repetitions=args.repetitions,
        )
    scores = automatic_scores(blind_path)
    score_path = Path(args.output_dir) / "automatic_scores.json"
    score_path.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Blind outputs: {blind_path}")
    print(f"Automatic scores: {score_path}")
    print("Provider mapping sealed separately; do not open it before qualitative scoring.")


if __name__ == "__main__":
    main()
