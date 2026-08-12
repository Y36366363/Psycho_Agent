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

    def test_authenticated_crisis_page_and_secure_headers(self):
        response, _ = self.request("/login", method="POST", data={"user_id":"alice", "password":"correct horse battery"})
        cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        response, body = self.request("/crisis?locale=zh-CN", cookie=cookie)
        self.assertEqual(response["status"], "200 OK")
        self.assertIn("Content-Security-Policy", response["headers"])
        self.assertIn("crisis-card", body)
        self.assertIn("tel:", body)
        self.assertIn("Official source", body)

    def test_memory_mutation_rejects_missing_csrf(self):
        response, _ = self.request("/login", method="POST", data={"user_id":"alice", "password":"correct horse battery"})
        cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        response, _ = self.request("/memory/delete-all", method="POST", data={}, cookie=cookie)
        self.assertEqual(response["status"], "403 Forbidden")
