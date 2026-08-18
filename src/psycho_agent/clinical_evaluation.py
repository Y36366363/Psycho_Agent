"""Create provider-blind rating packets and calculate inter-rater agreement."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True, slots=True)
class Rating:
    packet_item_id: str
    dimension: str
    rater_id: str
    score: int
    comment: str = ""


def create_blind_rating_packet(
    blind_outputs_path: str | Path,
    rubric_path: str | Path,
    destination: str | Path,
    *,
    rng: random.Random | None = None,
) -> tuple[Path, Path]:
    """Remove model aliases from rater material and keep the lookup separately."""
    rng = rng or random.SystemRandom()
    outputs = json.loads(Path(blind_outputs_path).read_text(encoding="utf-8"))
    rubric = json.loads(Path(rubric_path).read_text(encoding="utf-8"))
    sessions: list[tuple[str, dict[str, Any]]] = []
    for alias, model in outputs["models"].items():
        for scenario in model["scenarios"]:
            sessions.append((alias, scenario))
    rng.shuffle(sessions)

    packet_items: list[dict[str, Any]] = []
    key: dict[str, dict[str, str | int]] = {}
    for index, (alias, scenario) in enumerate(sessions, start=1):
        packet_id = f"Session-{index:03d}"
        key[packet_id] = {
            "alias": alias,
            "scenario_id": scenario["id"],
            "replicate": scenario.get("replicate", 1),
        }
        packet_items.append(
            {
                "packet_item_id": packet_id,
                "scenario_title": scenario["title"],
                "intent": scenario["intent"],
                "turns": [
                    {"user": turn["user"], "assistant": turn["response"]}
                    for turn in scenario["turns"]
                ],
                "ratings": {
                    dimension["id"]: {"score": None, "comment": ""}
                    for dimension in rubric["dimensions"]
                },
            }
        )

    output_dir = Path(destination)
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_path = output_dir / "rating_packet.json"
    key_path = output_dir / "rating_key.json"
    packet_path.write_text(
        json.dumps(
            {
                "rubric_version": rubric["version"],
                "instructions": (
                    "Rate independently. Do not attempt to identify providers. Use the "
                    "behavioral anchors and explain scores of 1 or 5."
                ),
                "dimensions": rubric["dimensions"],
                "items": packet_items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    return packet_path, key_path


def load_ratings(path: str | Path) -> list[Rating]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("ratings", [])
    ratings = [Rating(**row) for row in rows]
    if not ratings:
        raise ValueError("Rating file contains no ratings.")
    if any(not 1 <= rating.score <= 5 for rating in ratings):
        raise ValueError("Rating scores must be between 1 and 5.")
    return ratings


def quadratic_weighted_kappa(left: list[int], right: list[int]) -> float:
    """Calculate quadratic weighted kappa on a fixed 1–5 ordinal scale."""
    if len(left) != len(right) or not left:
        raise ValueError("Kappa requires two non-empty aligned score lists.")
    scale = range(1, 6)
    denominator = float((5 - 1) ** 2)
    observed = mean(((a - b) ** 2) / denominator for a, b in zip(left, right))
    left_prob = {score: left.count(score) / len(left) for score in scale}
    right_prob = {score: right.count(score) / len(right) for score in scale}
    expected = sum(
        left_prob[a] * right_prob[b] * ((a - b) ** 2) / denominator
        for a in scale
        for b in scale
    )
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return round(1 - observed / expected, 4)


def agreement_report(ratings: list[Rating]) -> dict[str, Any]:
    """Report pairwise agreement per dimension without averaging raw model quality."""
    report: dict[str, Any] = {}
    dimensions = sorted({rating.dimension for rating in ratings})
    for dimension in dimensions:
        subset = [rating for rating in ratings if rating.dimension == dimension]
        by_rater: dict[str, dict[str, int]] = {}
        for rating in subset:
            by_rater.setdefault(rating.rater_id, {})[rating.packet_item_id] = rating.score
        pairs: list[dict[str, Any]] = []
        for left_id, right_id in combinations(sorted(by_rater), 2):
            shared = sorted(set(by_rater[left_id]) & set(by_rater[right_id]))
            if not shared:
                continue
            left_scores = [by_rater[left_id][item] for item in shared]
            right_scores = [by_rater[right_id][item] for item in shared]
            pairs.append(
                {
                    "raters": [left_id, right_id],
                    "shared_items": len(shared),
                    "exact_agreement": round(
                        sum(a == b for a, b in zip(left_scores, right_scores)) / len(shared),
                        4,
                    ),
                    "quadratic_weighted_kappa": quadratic_weighted_kappa(
                        left_scores, right_scores
                    ),
                    "mean_absolute_difference": round(
                        mean(abs(a - b) for a, b in zip(left_scores, right_scores)), 4
                    ),
                    "severe_disagreement_count": sum(
                        abs(a - b) >= 2 for a, b in zip(left_scores, right_scores)
                    ),
                    "severe_disagreement_items": [
                        item
                        for item, a, b in zip(shared, left_scores, right_scores)
                        if abs(a - b) >= 2
                    ],
                }
            )
        report[dimension] = {
            "rater_count": len(by_rater),
            "pairs": pairs,
            "mean_pairwise_kappa": (
                round(mean(pair["quadratic_weighted_kappa"] for pair in pairs), 4)
                if pairs
                else None
            ),
        }
    return report


def ratings_to_json(ratings: list[Rating]) -> str:
    return json.dumps([asdict(rating) for rating in ratings], ensure_ascii=False, indent=2)
