import sqlite3
import tempfile
import unittest
from pathlib import Path

from psycho_agent.auth import AuthService


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "auth.sqlite3"
        self.auth = AuthService(self.path, session_seconds=60)
        self.auth.create_user("u1", "correct horse battery", role="reviewer")

    def tearDown(self): self.temp.cleanup()

    def test_password_session_role_and_csrf(self):
        with sqlite3.connect(self.path) as db:
            value = db.execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertNotIn(b"correct horse", value)
        session = self.auth.login("u1", "correct horse battery")
        self.assertEqual(self.auth.authenticate(session.token, required_role="reviewer").user_id, "u1")
        self.auth.require_csrf(session, session.csrf_token)
        with self.assertRaises(PermissionError): self.auth.require_csrf(session, "wrong")
        self.auth.logout(session.token)
        with self.assertRaises(PermissionError): self.auth.authenticate(session.token)

    def test_lockout_after_five_failures(self):
        for _ in range(5):
            with self.assertRaises(PermissionError): self.auth.login("u1", "wrong", client_id="x")
        with self.assertRaisesRegex(PermissionError, "Too many"):
            self.auth.login("u1", "correct horse battery", client_id="x")
