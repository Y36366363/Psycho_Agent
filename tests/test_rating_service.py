import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from psycho_agent.clinical_evaluation import Rating
from psycho_agent.credentials import ReviewerCredentialRegistry
from psycho_agent.governance import ReviewerRole
from psycho_agent.rating_service import BlindRatingRepository


class RatingRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); root = Path(self.temp.name)
        self.db = root / "db.sqlite3"; self.packet = root / "packet.json"
        self.packet.write_text(json.dumps({"dimensions":[{"id":"empathy"}], "items":[{"packet_item_id":"S1"}]}))
        self.creds = ReviewerCredentialRegistry(self.db)
        self.repo = BlindRatingRepository(self.db, self.packet, self.creds)

    def tearDown(self): self.temp.cleanup()

    def verify(self, rid):
        self.creds.register_pending(rid, ReviewerRole.CLINICAL, jurisdiction="CN", credential_type="license",
            credential_number=rid, issuing_authority="authority", source_url="https://gov.example/check",
            conflict_declaration="none")
        self.creds.record_manual_verification(rid, ReviewerRole.CLINICAL, verified_by="compliance",
            expires_at=datetime.now(UTC)+timedelta(days=10), evidence=b"evidence")
        self.creds.record_conflict_review(rid, ReviewerRole.CLINICAL, reviewed_by="ethics", cleared=True)

    def test_never_reports_drafts_as_completed_human_evaluation(self):
        self.assertEqual(self.repo.report()["status"], "awaiting_verified_professional_ratings")
        with self.assertRaises(PermissionError): self.repo.save(Rating("S1", "empathy", "fake", 5))
        self.verify("r1"); self.repo.save(Rating("S1", "empathy", "r1", 4)); self.repo.finalize("r1")
        self.assertEqual(self.repo.report()["finalized_reviewer_count"], 1)
        self.verify("r2"); self.repo.save(Rating("S1", "empathy", "r2", 5)); self.repo.finalize("r2")
        self.assertEqual(self.repo.report()["status"], "human_ratings_complete")
        with self.assertRaises(PermissionError): self.repo.save(Rating("S1", "empathy", "r1", 3))
