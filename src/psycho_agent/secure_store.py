"""Authenticated AES-256-GCM encryption over a consent-aware SQLite memory store."""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .privacy import ConsentRequiredError, MemoryScope


def generate_master_key() -> str:
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode()


def load_master_key(value: str | None = None) -> bytes:
    encoded = value or os.environ.get("PSYCHO_AGENT_MASTER_KEY", "")
    try:
        key = base64.urlsafe_b64decode(encoded.encode())
    except Exception as exc:
        raise ValueError("PSYCHO_AGENT_MASTER_KEY must be URL-safe base64.") from exc
    if len(key) != 32:
        raise ValueError("PSYCHO_AGENT_MASTER_KEY must decode to exactly 32 bytes.")
    return key


class EncryptedMemoryStore:
    """Persist only ciphertext; user identity is bound as AES-GCM associated data."""

    def __init__(
        self, database: str | Path, key: bytes, *, retention_days: int = 30
    ) -> None:
        if retention_days <= 0:
            raise ValueError("retention_days must be positive.")
        self.database = str(database)
        self.cipher = AESGCM(key)
        self.retention_days = retention_days
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database)
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """CREATE TABLE IF NOT EXISTS consents (
                owner_id TEXT NOT NULL, scope TEXT NOT NULL, policy_version TEXT NOT NULL,
                granted_at TEXT NOT NULL, PRIMARY KEY(owner_id, scope));
                CREATE TABLE IF NOT EXISTS memories (
                item_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, scope TEXT NOT NULL,
                nonce BLOB NOT NULL, ciphertext BLOB NOT NULL, created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS memories_owner ON memories(owner_id);
                CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT NOT NULL,
                event TEXT NOT NULL, scope TEXT, item_id TEXT, occurred_at TEXT NOT NULL);
                """
            )

    def grant_consent(
        self, owner_id: str, scopes: set[MemoryScope], *, policy_version: str
    ) -> None:
        if not scopes:
            raise ValueError("Select at least one scope.")
        now = datetime.now(UTC).isoformat()
        with self._connect() as db:
            for scope in scopes:
                db.execute(
                    "INSERT OR REPLACE INTO consents VALUES (?, ?, ?, ?)",
                    (owner_id, scope.value, policy_version, now),
                )
            self._audit(db, owner_id, "consent_granted")

    def remember(self, owner_id: str, scope: MemoryScope, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Memory value must not be empty.")
        with self._connect() as db:
            consent = db.execute(
                "SELECT 1 FROM consents WHERE owner_id=? AND scope=?",
                (owner_id, scope.value),
            ).fetchone()
            if not consent:
                raise ConsentRequiredError(f"No consent for {scope.value}.")
            item_id = secrets.token_urlsafe(12)
            nonce = secrets.token_bytes(12)
            aad = f"{owner_id}:{scope.value}:{item_id}".encode()
            ciphertext = self.cipher.encrypt(nonce, normalized.encode(), aad)
            now = datetime.now(UTC)
            db.execute(
                "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    item_id,
                    owner_id,
                    scope.value,
                    nonce,
                    ciphertext,
                    now.isoformat(),
                    (now + timedelta(days=self.retention_days)).isoformat(),
                ),
            )
            self._audit(db, owner_id, "memory_created", scope.value, item_id)
        return item_id

    def view(self, owner_id: str) -> list[dict[str, str]]:
        self.purge_expired()
        with self._connect() as db:
            rows = db.execute(
                "SELECT item_id, scope, nonce, ciphertext, created_at, expires_at "
                "FROM memories WHERE owner_id=? ORDER BY created_at",
                (owner_id,),
            ).fetchall()
        results = []
        for item_id, scope, nonce, ciphertext, created_at, expires_at in rows:
            aad = f"{owner_id}:{scope}:{item_id}".encode()
            value = self.cipher.decrypt(nonce, ciphertext, aad).decode()
            results.append({
                "item_id": item_id, "scope": scope, "value": value,
                "created_at": created_at, "expires_at": expires_at,
            })
        return results

    def delete_item(self, owner_id: str, item_id: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT scope FROM memories WHERE owner_id=? AND item_id=?",
                (owner_id, item_id),
            ).fetchone()
            if not row:
                return False
            db.execute("DELETE FROM memories WHERE item_id=?", (item_id,))
            self._audit(db, owner_id, "memory_deleted", row[0], item_id)
        return True

    def revoke_scope(self, owner_id: str, scope: MemoryScope) -> int:
        with self._connect() as db:
            count = db.execute(
                "SELECT count(*) FROM memories WHERE owner_id=? AND scope=?",
                (owner_id, scope.value),
            ).fetchone()[0]
            db.execute("DELETE FROM memories WHERE owner_id=? AND scope=?", (owner_id, scope.value))
            db.execute("DELETE FROM consents WHERE owner_id=? AND scope=?", (owner_id, scope.value))
            self._audit(db, owner_id, "scope_revoked_and_deleted", scope.value)
        return count

    def delete_all(self, owner_id: str) -> int:
        with self._connect() as db:
            count = db.execute(
                "SELECT count(*) FROM memories WHERE owner_id=?", (owner_id,)
            ).fetchone()[0]
            db.execute("DELETE FROM memories WHERE owner_id=?", (owner_id,))
            db.execute("DELETE FROM consents WHERE owner_id=?", (owner_id,))
            self._audit(db, owner_id, "all_memory_deleted")
        return count

    def export(self, owner_id: str) -> str:
        return json.dumps(
            {"owner_id": owner_id, "memories": self.view(owner_id)},
            ensure_ascii=False,
            indent=2,
        )

    def purge_expired(self) -> int:
        now = datetime.now(UTC).isoformat()
        with self._connect() as db:
            rows = db.execute(
                "SELECT item_id, owner_id, scope FROM memories WHERE expires_at<=?", (now,)
            ).fetchall()
            for item_id, owner_id, scope in rows:
                db.execute("DELETE FROM memories WHERE item_id=?", (item_id,))
                self._audit(db, owner_id, "memory_expired", scope, item_id)
        return len(rows)

    @staticmethod
    def _audit(
        db: sqlite3.Connection, owner_id: str, event: str,
        scope: str | None = None, item_id: str | None = None,
    ) -> None:
        db.execute(
            "INSERT INTO audit(owner_id,event,scope,item_id,occurred_at) VALUES(?,?,?,?,?)",
            (owner_id, event, scope, item_id, datetime.now(UTC).isoformat()),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate-key"])
    args = parser.parse_args()
    if args.command == "generate-key":
        print(generate_master_key())


if __name__ == "__main__":
    main()
