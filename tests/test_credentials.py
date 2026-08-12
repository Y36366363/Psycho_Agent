import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from psycho_agent.credentials import ReviewerCredentialRegistry
from psycho_agent.governance import ChangeApproval, ClinicalChange, ClinicalChangeRegistry, GovernanceError, ReviewDecision, ReviewerRole


class CredentialGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.credentials = ReviewerCredentialRegistry(Path(self.temp.name) / "db.sqlite3")

    def tearDown(self): self.temp.cleanup()

    def register(self, reviewer="c1"):
        self.credentials.register_pending(reviewer, ReviewerRole.CLINICAL, jurisdiction="CN",
            credential_type="professional qualification", credential_number="SECRET-123",
            issuing_authority="official authority", source_url="https://example.gov.cn/check",
            conflict_declaration="No financial, personal, or intellectual conflict declared.")

    def test_manual_evidence_and_conflict_both_required(self):
        self.register()
        self.assertFalse(self.credentials.eligibility("c1", ReviewerRole.CLINICAL).eligible)
        self.credentials.record_manual_verification("c1", ReviewerRole.CLINICAL,
            verified_by="compliance", expires_at=datetime.now(UTC) + timedelta(days=30), evidence=b"snapshot")
        self.assertEqual(self.credentials.eligibility("c1", ReviewerRole.CLINICAL).reason, "conflict_not_cleared")
        self.credentials.record_conflict_review("c1", ReviewerRole.CLINICAL, reviewed_by="ethics", cleared=True)
        self.assertTrue(self.credentials.eligibility("c1", ReviewerRole.CLINICAL).eligible)

    def test_governance_rejects_unverified_reviewer(self):
        self.register()
        registry = ClinicalChangeRegistry(eligibility_registry=self.credentials)
        registry.submit(ClinicalChange("x", "policy", "1", "summary", "reason", ["test"], None, "owner"))
        with self.assertRaises(GovernanceError):
            registry.review("x", ChangeApproval("c1", ReviewerRole.CLINICAL, "recorded", ReviewDecision.APPROVE, "ok"))
