"""Manual professional-credential and conflict-of-interest verification gates."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from .governance import ReviewerRole


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ConflictStatus(StrEnum):
    PENDING = "pending"
    CLEARED = "cleared"
    RECUSED = "recused"


@dataclass(frozen=True, slots=True)
class ReviewerEligibility:
    eligible: bool
    reason: str


class ReviewerCredentialRegistry:
    """Persist human verification evidence; never claims automated license verification."""

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS reviewer_credentials (
                reviewer_id TEXT NOT NULL, role TEXT NOT NULL, jurisdiction TEXT NOT NULL,
                credential_type TEXT NOT NULL, credential_digest TEXT NOT NULL,
                issuing_authority TEXT NOT NULL, source_url TEXT NOT NULL,
                status TEXT NOT NULL, verified_by TEXT, verified_at TEXT, expires_at TEXT,
                evidence_digest TEXT, conflict_declaration TEXT NOT NULL,
                conflict_status TEXT NOT NULL, conflict_reviewed_by TEXT,
                PRIMARY KEY(reviewer_id, role))"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database)

    def register_pending(
        self, reviewer_id: str, role: ReviewerRole, *, jurisdiction: str,
        credential_type: str, credential_number: str, issuing_authority: str,
        source_url: str, conflict_declaration: str,
    ) -> None:
        if role not in {ReviewerRole.CLINICAL, ReviewerRole.SAFETY}:
            raise ValueError("Only clinical and safety roles require this gate.")
        if not source_url.startswith("https://") or not conflict_declaration.strip():
            raise ValueError("Official HTTPS source and COI declaration are required.")
        digest = hashlib.sha256(credential_number.strip().encode()).hexdigest()
        with self._connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO reviewer_credentials VALUES
                (?,?,?,?,?,?,?, ?,NULL,NULL,NULL,NULL, ?,?,NULL)""",
                (reviewer_id, role.value, jurisdiction, credential_type, digest,
                 issuing_authority, source_url, VerificationStatus.PENDING.value,
                 conflict_declaration.strip(), ConflictStatus.PENDING.value),
            )

    def record_manual_verification(
        self, reviewer_id: str, role: ReviewerRole, *, verified_by: str,
        expires_at: datetime, evidence: bytes,
    ) -> None:
        if not evidence or expires_at <= datetime.now(UTC):
            raise ValueError("Evidence and a future expiry are required.")
        with self._connect() as db:
            changed = db.execute(
                """UPDATE reviewer_credentials SET status=?, verified_by=?, verified_at=?,
                expires_at=?, evidence_digest=? WHERE reviewer_id=? AND role=?""",
                (VerificationStatus.VERIFIED.value, verified_by, datetime.now(UTC).isoformat(),
                 expires_at.isoformat(), hashlib.sha256(evidence).hexdigest(),
                 reviewer_id, role.value),
            ).rowcount
        if not changed:
            raise KeyError("Unknown reviewer credential.")

    def record_conflict_review(
        self, reviewer_id: str, role: ReviewerRole, *, reviewed_by: str, cleared: bool,
    ) -> None:
        with self._connect() as db:
            changed = db.execute(
                """UPDATE reviewer_credentials SET conflict_status=?, conflict_reviewed_by=?
                WHERE reviewer_id=? AND role=?""",
                (ConflictStatus.CLEARED.value if cleared else ConflictStatus.RECUSED.value,
                 reviewed_by, reviewer_id, role.value),
            ).rowcount
        if not changed:
            raise KeyError("Unknown reviewer credential.")

    def eligibility(self, reviewer_id: str, role: ReviewerRole) -> ReviewerEligibility:
        with self._connect() as db:
            row = db.execute(
                """SELECT status,expires_at,evidence_digest,conflict_status
                FROM reviewer_credentials WHERE reviewer_id=? AND role=?""",
                (reviewer_id, role.value),
            ).fetchone()
        if not row:
            return ReviewerEligibility(False, "credential_not_registered")
        if row[0] != VerificationStatus.VERIFIED.value or not row[2]:
            return ReviewerEligibility(False, "credential_not_verified")
        if not row[1] or datetime.fromisoformat(row[1]) <= datetime.now(UTC):
            return ReviewerEligibility(False, "credential_expired")
        if row[3] != ConflictStatus.CLEARED.value:
            return ReviewerEligibility(False, "conflict_not_cleared")
        return ReviewerEligibility(True, "eligible")
