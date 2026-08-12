"""Local password authentication and short-lived, CSRF-bound web sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AuthSession:
    token: str
    csrf_token: str
    user_id: str
    role: str
    expires_at: float


class AuthService:
    def __init__(self, database: str | Path, *, session_seconds: int = 3600) -> None:
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.session_seconds = session_seconds
        self._sessions: dict[str, AuthSession] = {}
        self._failures: dict[str, tuple[int, float]] = {}
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, role TEXT NOT NULL, salt BLOB NOT NULL,
                password_hash BLOB NOT NULL, active INTEGER NOT NULL DEFAULT 1)"""
            )

    def create_user(self, user_id: str, password: str, *, role: str = "user") -> None:
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters.")
        if role not in {"user", "reviewer", "admin"}:
            raise ValueError("Unsupported role.")
        salt = secrets.token_bytes(16)
        password_hash = hashlib.scrypt(
            password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32
        )
        with self._connect() as db:
            db.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, 1)",
                (user_id, role, salt, password_hash),
            )

    def login(self, user_id: str, password: str, *, client_id: str = "local") -> AuthSession:
        failures, locked_until = self._failures.get(client_id, (0, 0.0))
        if time.time() < locked_until:
            raise PermissionError("Too many failed attempts; try again later.")
        with self._connect() as db:
            row = db.execute(
                "SELECT role, salt, password_hash, active FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        salt = row[1] if row else b"\x00" * 16
        candidate = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
        if not row or not row[3] or not hmac.compare_digest(candidate, row[2]):
            failures += 1
            self._failures[client_id] = (
                failures,
                time.time() + 30 if failures >= 5 else 0.0,
            )
            raise PermissionError("Invalid credentials.")
        self._failures.pop(client_id, None)
        token = secrets.token_urlsafe(32)
        session = AuthSession(
            token, secrets.token_urlsafe(24), user_id, row[0], time.time() + self.session_seconds
        )
        self._sessions[token] = session
        return session

    def authenticate(self, token: str, *, required_role: str | None = None) -> AuthSession:
        session = self._sessions.get(token)
        if session is None or session.expires_at <= time.time():
            self._sessions.pop(token, None)
            raise PermissionError("Authentication required.")
        if required_role and session.role not in {required_role, "admin"}:
            raise PermissionError("Insufficient role.")
        return session

    def require_csrf(self, session: AuthSession, csrf_token: str) -> None:
        if not hmac.compare_digest(session.csrf_token, csrf_token):
            raise PermissionError("Invalid CSRF token.")

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)
