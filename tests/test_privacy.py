import json
import unittest
from datetime import UTC, datetime, timedelta

from psycho_agent.privacy import (
    ConsentAwareMemoryVault,
    ConsentRequiredError,
    MemoryScope,
)


class ConsentAwareMemoryVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vault = ConsentAwareMemoryVault(retention_days=30)

    def test_memory_write_requires_scope_specific_consent(self) -> None:
        with self.assertRaises(ConsentRequiredError):
            self.vault.remember("session", MemoryScope.GOALS, "改善睡眠")
        self.vault.grant_consent(
            "session", {MemoryScope.PREFERENCES}, policy_version="privacy-1"
        )
        with self.assertRaises(ConsentRequiredError):
            self.vault.remember("session", MemoryScope.GOALS, "改善睡眠")

    def test_user_can_view_export_and_delete_memory(self) -> None:
        self.vault.grant_consent(
            "session",
            {MemoryScope.GOALS, MemoryScope.PREFERENCES},
            policy_version="privacy-1",
        )
        item = self.vault.remember("session", MemoryScope.GOALS, "  改善   睡眠  ")
        self.assertEqual(self.vault.view("session")[0].value, "改善 睡眠")
        exported = json.loads(self.vault.export("session"))
        self.assertEqual(exported["memories"][0]["value"], "改善 睡眠")
        self.assertTrue(self.vault.delete_item("session", item.item_id))
        self.assertEqual(self.vault.view("session"), [])

    def test_revoking_scope_deletes_its_items_but_not_other_scopes(self) -> None:
        self.vault.grant_consent(
            "session",
            {MemoryScope.GOALS, MemoryScope.PREFERENCES},
            policy_version="privacy-1",
        )
        self.vault.remember("session", MemoryScope.GOALS, "改善睡眠")
        self.vault.remember("session", MemoryScope.PREFERENCES, "先听后建议")
        self.assertEqual(self.vault.revoke_scope("session", MemoryScope.GOALS), 1)
        remaining = self.vault.view("session")
        self.assertEqual([item.scope for item in remaining], [MemoryScope.PREFERENCES])

    def test_delete_all_revokes_consent_and_preserves_content_free_audit(self) -> None:
        receipt = self.vault.grant_consent(
            "session", {MemoryScope.GOALS}, policy_version="privacy-1"
        )
        self.vault.remember("session", MemoryScope.GOALS, "一段敏感内容")
        self.assertEqual(self.vault.delete_all("session"), 1)
        self.assertFalse(receipt.active)
        audit_text = " ".join(event.event for event in self.vault.audit_events("session"))
        self.assertNotIn("敏感内容", audit_text)

    def test_expired_items_are_purged(self) -> None:
        self.vault.grant_consent(
            "session", {MemoryScope.GOALS}, policy_version="privacy-1"
        )
        self.vault.remember("session", MemoryScope.GOALS, "改善睡眠")
        future = datetime.now(UTC) + timedelta(days=31)
        self.assertEqual(self.vault.purge_expired(now=future), 1)
        self.assertEqual(self.vault.view("session"), [])


if __name__ == "__main__":
    unittest.main()
