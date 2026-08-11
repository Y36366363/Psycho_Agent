"""Clinical change control with independent approval, activation, and rollback."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now() -> datetime:
    return datetime.now(UTC)


class ChangeStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class ReviewerRole(StrEnum):
    CLINICAL = "clinical"
    SAFETY = "safety"
    PRODUCT = "product"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class ChangeApproval:
    reviewer_id: str
    role: ReviewerRole
    credential_or_responsibility: str
    decision: ReviewDecision
    comment: str
    reviewed_at: datetime = field(default_factory=_now)


@dataclass(slots=True)
class ClinicalChange:
    change_id: str
    component: str
    version: str
    summary: str
    rationale: str
    evidence: list[str]
    rollback_version: str | None
    submitted_by: str
    status: ChangeStatus = ChangeStatus.DRAFT
    submitted_at: datetime = field(default_factory=_now)
    approvals: list[ChangeApproval] = field(default_factory=list)
    activated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GovernanceEvent:
    event: str
    change_id: str
    actor_id: str
    reason: str
    occurred_at: datetime = field(default_factory=_now)


class GovernanceError(RuntimeError):
    pass


class ClinicalChangeRegistry:
    """Require two clinical reviewers plus an independent safety approval."""

    def __init__(
        self, *, required_clinical_approvals: int = 2, required_safety_approvals: int = 1
    ) -> None:
        self.required_clinical_approvals = required_clinical_approvals
        self.required_safety_approvals = required_safety_approvals
        self._changes: dict[str, ClinicalChange] = {}
        self._active_by_component: dict[str, str] = {}
        self._events: list[GovernanceEvent] = []

    def submit(self, change: ClinicalChange) -> None:
        if change.change_id in self._changes:
            raise GovernanceError("change_id must be unique")
        if not change.evidence:
            raise GovernanceError("Clinical changes require evaluation evidence.")
        change.status = ChangeStatus.IN_REVIEW
        self._changes[change.change_id] = change
        self._events.append(
            GovernanceEvent("submitted", change.change_id, change.submitted_by, change.rationale)
        )

    def review(self, change_id: str, approval: ChangeApproval) -> ChangeStatus:
        change = self.get(change_id)
        if change.status not in {ChangeStatus.IN_REVIEW, ChangeStatus.APPROVED}:
            raise GovernanceError(f"Change cannot be reviewed in status {change.status.value}.")
        if any(item.reviewer_id == approval.reviewer_id for item in change.approvals):
            raise GovernanceError("A reviewer may submit only one decision per change.")
        change.approvals.append(approval)
        if approval.decision is ReviewDecision.REJECT:
            change.status = ChangeStatus.REJECTED
            return change.status
        if self._approval_threshold_met(change):
            change.status = ChangeStatus.APPROVED
        return change.status

    def activate(self, change_id: str, *, actor_id: str) -> ClinicalChange:
        change = self.get(change_id)
        if change.status is not ChangeStatus.APPROVED:
            raise GovernanceError("Only independently approved changes may be activated.")
        previous_id = self._active_by_component.get(change.component)
        if previous_id:
            self._changes[previous_id].status = ChangeStatus.SUPERSEDED
        change.status = ChangeStatus.ACTIVE
        change.activated_at = _now()
        self._active_by_component[change.component] = change_id
        self._events.append(GovernanceEvent("activated", change_id, actor_id, change.summary))
        return change

    def rollback(
        self,
        component: str,
        target_change_id: str,
        *,
        actor_id: str,
        actor_role: ReviewerRole,
        reason: str,
    ) -> ClinicalChange:
        if actor_role is not ReviewerRole.SAFETY:
            raise GovernanceError("Emergency rollback requires a safety-role actor.")
        current_id = self._active_by_component.get(component)
        target = self.get(target_change_id)
        if target.component != component or target.status not in {
            ChangeStatus.SUPERSEDED,
            ChangeStatus.ROLLED_BACK,
        }:
            raise GovernanceError("Rollback target must be a previously active component version.")
        if current_id:
            self._changes[current_id].status = ChangeStatus.ROLLED_BACK
        target.status = ChangeStatus.ACTIVE
        target.activated_at = _now()
        self._active_by_component[component] = target_change_id
        self._events.append(GovernanceEvent("rollback", target_change_id, actor_id, reason))
        return target

    def get(self, change_id: str) -> ClinicalChange:
        try:
            return self._changes[change_id]
        except KeyError as exc:
            raise GovernanceError(f"Unknown change: {change_id}") from exc

    def active(self, component: str) -> ClinicalChange | None:
        change_id = self._active_by_component.get(component)
        return self._changes.get(change_id) if change_id else None

    def events(self) -> list[GovernanceEvent]:
        return list(self._events)

    def export(self) -> str:
        payload = {
            "requirements": {
                "clinical_approvals": self.required_clinical_approvals,
                "safety_approvals": self.required_safety_approvals,
            },
            "active_by_component": self._active_by_component,
            "changes": [self._serialize(change) for change in self._changes.values()],
            "events": [self._serialize(event) for event in self._events],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _approval_threshold_met(self, change: ClinicalChange) -> bool:
        approved = [
            approval
            for approval in change.approvals
            if approval.decision is ReviewDecision.APPROVE
        ]
        clinical = {item.reviewer_id for item in approved if item.role is ReviewerRole.CLINICAL}
        safety = {item.reviewer_id for item in approved if item.role is ReviewerRole.SAFETY}
        return (
            len(clinical) >= self.required_clinical_approvals
            and len(safety) >= self.required_safety_approvals
        )

    @classmethod
    def _serialize(cls, value: object) -> dict[str, Any]:
        data = asdict(value)  # type: ignore[arg-type]
        return cls._normalize(data)

    @classmethod
    def _normalize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._normalize(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, StrEnum):
            return value.value
        return value
