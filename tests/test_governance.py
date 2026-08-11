import json
import unittest

from psycho_agent.governance import (
    ChangeApproval,
    ChangeStatus,
    ClinicalChange,
    ClinicalChangeRegistry,
    GovernanceError,
    ReviewDecision,
    ReviewerRole,
)


def change(change_id: str, version: str, rollback: str | None = None) -> ClinicalChange:
    return ClinicalChange(
        change_id=change_id,
        component="safety_policy",
        version=version,
        summary="Update one observable behavior",
        rationale="Regression evidence showed a gap",
        evidence=["tests/test_safety.py"],
        rollback_version=rollback,
        submitted_by="owner",
    )


def approval(reviewer: str, role: ReviewerRole) -> ChangeApproval:
    return ChangeApproval(
        reviewer_id=reviewer,
        role=role,
        credential_or_responsibility="credential recorded externally",
        decision=ReviewDecision.APPROVE,
        comment="Reviewed evidence and foreseeable harms",
    )


class ClinicalChangeRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ClinicalChangeRegistry()

    def approve(self, change_id: str) -> None:
        self.registry.review(change_id, approval("clinician-1", ReviewerRole.CLINICAL))
        self.registry.review(change_id, approval("clinician-2", ReviewerRole.CLINICAL))
        self.registry.review(change_id, approval("safety-1", ReviewerRole.SAFETY))

    def test_activation_requires_two_clinical_and_one_safety_approval(self) -> None:
        item = change("safety-1", "1.0.0")
        self.registry.submit(item)
        self.registry.review("safety-1", approval("clinician-1", ReviewerRole.CLINICAL))
        self.registry.review("safety-1", approval("clinician-2", ReviewerRole.CLINICAL))
        with self.assertRaises(GovernanceError):
            self.registry.activate("safety-1", actor_id="release-owner")
        self.registry.review("safety-1", approval("safety-1", ReviewerRole.SAFETY))
        active = self.registry.activate("safety-1", actor_id="release-owner")
        self.assertEqual(active.status, ChangeStatus.ACTIVE)

    def test_reviewer_identity_cannot_be_counted_twice(self) -> None:
        self.registry.submit(change("safety-1", "1.0.0"))
        self.registry.review("safety-1", approval("same-person", ReviewerRole.CLINICAL))
        with self.assertRaises(GovernanceError):
            self.registry.review("safety-1", approval("same-person", ReviewerRole.SAFETY))

    def test_safety_role_can_rollback_to_previously_active_version(self) -> None:
        first = change("safety-1", "1.0.0")
        self.registry.submit(first)
        self.approve("safety-1")
        self.registry.activate("safety-1", actor_id="owner")
        second = change("safety-2", "2.0.0", rollback="1.0.0")
        self.registry.submit(second)
        self.approve("safety-2")
        self.registry.activate("safety-2", actor_id="owner")
        restored = self.registry.rollback(
            "safety_policy",
            "safety-1",
            actor_id="safety-officer",
            actor_role=ReviewerRole.SAFETY,
            reason="Post-release safety regression",
        )
        self.assertEqual(restored.version, "1.0.0")
        self.assertEqual(self.registry.get("safety-2").status, ChangeStatus.ROLLED_BACK)
        self.assertIn("active_by_component", json.loads(self.registry.export()))


if __name__ == "__main__":
    unittest.main()
