"""Durable blind-rating intake that only reports finalized human assessments."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .clinical_evaluation import Rating, agreement_report
from .credentials import ReviewerCredentialRegistry
from .governance import ReviewerRole


class BlindRatingRepository:
    def __init__(self, database: str | Path, packet_path: str | Path,
                 credentials: ReviewerCredentialRegistry) -> None:
        self.database = str(database)
        self.packet = json.loads(Path(packet_path).read_text(encoding="utf-8"))
        self.credentials = credentials
        self.item_ids = {item["packet_item_id"] for item in self.packet["items"]}
        self.dimensions = {item["id"] for item in self.packet["dimensions"]}
        with sqlite3.connect(self.database) as db:
            db.executescript(
                """CREATE TABLE IF NOT EXISTS blind_ratings (
                reviewer_id TEXT, item_id TEXT, dimension TEXT, score INTEGER,
                comment TEXT, PRIMARY KEY(reviewer_id,item_id,dimension));
                CREATE TABLE IF NOT EXISTS rating_finalizations (
                reviewer_id TEXT PRIMARY KEY, finalized_at TEXT DEFAULT CURRENT_TIMESTAMP);"""
            )

    def _require_reviewer(self, reviewer_id: str) -> None:
        result = self.credentials.eligibility(reviewer_id, ReviewerRole.CLINICAL)
        if not result.eligible:
            raise PermissionError(f"Reviewer is ineligible: {result.reason}.")

    def save(self, rating: Rating) -> None:
        self._require_reviewer(rating.rater_id)
        if rating.packet_item_id not in self.item_ids or rating.dimension not in self.dimensions:
            raise ValueError("Unknown blinded item or rubric dimension.")
        if not 1 <= rating.score <= 5:
            raise ValueError("Score must be between 1 and 5.")
        with sqlite3.connect(self.database) as db:
            if db.execute("SELECT 1 FROM rating_finalizations WHERE reviewer_id=?",
                          (rating.rater_id,)).fetchone():
                raise PermissionError("Finalized ratings are immutable.")
            db.execute("INSERT OR REPLACE INTO blind_ratings VALUES(?,?,?,?,?)",
                       (rating.rater_id, rating.packet_item_id, rating.dimension,
                        rating.score, rating.comment))

    def finalize(self, reviewer_id: str) -> None:
        self._require_reviewer(reviewer_id)
        expected = len(self.item_ids) * len(self.dimensions)
        with sqlite3.connect(self.database) as db:
            actual = db.execute("SELECT count(*) FROM blind_ratings WHERE reviewer_id=?",
                                (reviewer_id,)).fetchone()[0]
            if actual != expected:
                raise ValueError(f"Complete all {expected} ratings before finalizing; found {actual}.")
            db.execute("INSERT INTO rating_finalizations(reviewer_id) VALUES(?)", (reviewer_id,))

    def report(self) -> dict[str, Any]:
        with sqlite3.connect(self.database) as db:
            finalized = [row[0] for row in db.execute(
                "SELECT reviewer_id FROM rating_finalizations ORDER BY reviewer_id")]
            rows = db.execute(
                """SELECT reviewer_id,item_id,dimension,score,comment FROM blind_ratings
                WHERE reviewer_id IN (SELECT reviewer_id FROM rating_finalizations)"""
            ).fetchall()
        if len(finalized) < 2:
            return {"status": "awaiting_verified_professional_ratings",
                    "finalized_reviewer_count": len(finalized), "agreement": None}
        ratings = [Rating(item, dimension, reviewer, score, comment)
                   for reviewer, item, dimension, score, comment in rows]
        return {"status": "human_ratings_complete", "finalized_reviewer_count": len(finalized),
                "agreement": agreement_report(ratings)}
