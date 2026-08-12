import base64
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from psycho_agent.privacy import ConsentRequiredError, MemoryScope
from psycho_agent.secure_store import EncryptedMemoryStore


class EncryptedMemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.sqlite3"
        self.store = EncryptedMemoryStore(self.path, AESGCM.generate_key(bit_length=256))

    def tearDown(self):
        self.temp.cleanup()

    def test_consent_encrypt_view_export_and_delete(self):
        with self.assertRaises(ConsentRequiredError):
            self.store.remember("alice", MemoryScope.GOALS, "private goal")
        self.store.grant_consent("alice", {MemoryScope.GOALS}, policy_version="v1")
        item_id = self.store.remember("alice", MemoryScope.GOALS, "private goal")
        self.assertEqual(self.store.view("alice")[0]["value"], "private goal")
        self.assertIn("private goal", self.store.export("alice"))
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.assertNotIn(b"private goal", self.path.read_bytes())
        self.assertTrue(self.store.delete_item("alice", item_id))
        self.assertEqual(self.store.view("alice"), [])

    def test_owner_isolation_and_full_deletion(self):
        self.store.grant_consent("alice", {MemoryScope.GOALS}, policy_version="v1")
        self.store.remember("alice", MemoryScope.GOALS, "one")
        self.assertEqual(self.store.view("bob"), [])
        self.assertEqual(self.store.delete_all("alice"), 1)
        with self.assertRaises(ConsentRequiredError):
            self.store.remember("alice", MemoryScope.GOALS, "two")
