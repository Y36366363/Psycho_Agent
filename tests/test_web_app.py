import io
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from psycho_agent.auth import AuthService
from psycho_agent.secure_store import EncryptedMemoryStore
from psycho_agent.web_app import PsychoWebApp


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); path = Path(self.temp.name) / "web.sqlite3"
        self.auth = AuthService(path); self.auth.create_user("alice", "correct horse battery")
        self.app = PsychoWebApp(self.auth, EncryptedMemoryStore(path, AESGCM.generate_key(bit_length=256)))

    def tearDown(self): self.temp.cleanup()

    def request(self, path, *, method="GET", data=None, cookie=""):
        raw = urlencode(data or {}).encode(); captured = {}
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
                   "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
                   "REMOTE_ADDR": "test", "HTTP_COOKIE": cookie}
        if "?" in path:
            environ["PATH_INFO"], environ["QUERY_STRING"] = path.split("?", 1)
        def start(status, headers): captured.update(status=status, headers=dict(headers))
        body = b"".join(self.app(environ, start)).decode()
        return captured, body

    def test_crisis_page_never_requires_authentication(self):
        response, body = self.request("/crisis?locale=zh-CN")
        self.assertEqual(response["status"], "200 OK")
        self.assertIn("Content-Security-Policy", response["headers"])
        self.assertIn("crisis-card", body)
        self.assertIn("tel:", body)
        self.assertIn("Official source", body)

    def test_memory_consent_is_scope_specific_and_revocable(self):
        response, _ = self.request("/login", method="POST", data={"user_id":"alice", "password":"correct horse battery"})
        session = next(iter(self.auth._sessions.values()))
        cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        response, _ = self.request(
            "/memory/consent", method="POST", cookie=cookie,
            data={"csrf": session.csrf_token, "scope_goals": "1"},
        )
        self.assertEqual(response["status"], "303 See Other")
        response, body = self.request("/memory", cookie=cookie)
        self.assertIn("撤销 goals", body)
        self.assertNotIn("撤销 preferences", body)
        response, _ = self.request(
            "/memory/revoke", method="POST", cookie=cookie,
            data={"csrf": session.csrf_token, "scope": "goals"},
        )
        self.assertEqual(response["status"], "303 See Other")
        self.assertEqual(self.app.memory.consent_scopes("alice"), set())

    def test_invalid_scope_is_a_bounded_bad_request(self):
        response, _ = self.request("/login", method="POST", data={"user_id":"alice", "password":"correct horse battery"})
        session = next(iter(self.auth._sessions.values()))
        cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        response, body = self.request(
            "/memory/revoke", method="POST", cookie=cookie,
            data={"csrf": session.csrf_token, "scope": "diagnosis"},
        )
        self.assertEqual(response["status"], "400 Bad Request")
        self.assertIn("无法完成操作", body)

    def test_memory_mutation_rejects_missing_csrf(self):
        response, _ = self.request("/login", method="POST", data={"user_id":"alice", "password":"correct horse battery"})
        cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        response, _ = self.request("/memory/delete-all", method="POST", data={}, cookie=cookie)
        self.assertEqual(response["status"], "403 Forbidden")
