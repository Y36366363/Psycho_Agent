"""Consent-gated, data-minimized long-term memory primitives."""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


def _now() -> datetime:
    return datetime.now(UTC)


class MemoryScope(StrEnum):
    PREFERENCES = "preferences"
    GOALS = "goals"
    SUPPORT_NETWORK = "support_network"
    ATTEMPTED_ACTIONS = "attempted_actions"


@dataclass(slots=True)
class ConsentReceipt:
    session_id: str
    policy_version: str
    granted_scopes: set[MemoryScope]
    granted_at: datetime = field(default_factory=_now)
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None and bool(self.granted_scopes)


@dataclass(frozen=True, slots=True)
class MemoryItem:
    item_id: str
    session_id: str
    scope: MemoryScope
    value: str
    source: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class MemoryAuditEvent:
    event: str
    session_id: str
    occurred_at: datetime
    scope: str | None = None
    item_id: str | None = None


class ConsentRequiredError(PermissionError):
    """Raised when long-term memory is attempted without scope consent."""


class ConsentAwareMemoryVault:
    """In-memory by default; applications must opt into persistence explicitly."""

    def __init__(self, *, retention_days: int = 30) -> None:
        if retention_days <= 0:
            raise ValueError("retention_days must be positive")
        self.retention_days = retention_days
        self._consents: dict[str, ConsentReceipt] = {}
        self._items: dict[str, MemoryItem] = {}
        self._audit: list[MemoryAuditEvent] = []

    def grant_consent(
        self,
        session_id: str,
        scopes: set[MemoryScope],
        *,
        policy_version: str,
    ) -> ConsentReceipt:
        if not scopes:
            raise ValueError("At least one memory scope must be selected explicitly.")
        receipt = ConsentReceipt(session_id, policy_version, set(scopes))
        self._consents[session_id] = receipt
        self._record("consent_granted", session_id)
        return receipt

    def consent_status(self, session_id: str) -> ConsentReceipt | None:
        return self._consents.get(session_id)

    def remember(
        self,
        session_id: str,
        scope: MemoryScope,
        value: str,
        *,
        source: str = "user_explicit",
    ) -> MemoryItem:
        receipt = self._consents.get(session_id)
        if not receipt or not receipt.active or scope not in receipt.granted_scopes:
            raise ConsentRequiredError(f"No active consent for memory scope: {scope.value}")
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Memory value must not be empty")
        item = MemoryItem(
            item_id=secrets.token_urlsafe(12),
            session_id=session_id,
            scope=scope,
            value=normalized,
            source=source,
            created_at=_now(),
            expires_at=_now() + timedelta(days=self.retention_days),
        )
        self._items[item.item_id] = item
        self._record("memory_created", session_id, scope=scope.value, item_id=item.item_id)
        return item

    def view(self, session_id: str, scope: MemoryScope | None = None) -> list[MemoryItem]:
        self.purge_expired()
        return sorted(
            (
                item
                for item in self._items.values()
                if item.session_id == session_id and (scope is None or item.scope is scope)
            ),
            key=lambda item: item.created_at,
        )

    def delete_item(self, session_id: str, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None or item.session_id != session_id:
            return False
        del self._items[item_id]
        self._record("memory_deleted", session_id, scope=item.scope.value, item_id=item_id)
        return True

    def revoke_scope(self, session_id: str, scope: MemoryScope) -> int:
        receipt = self._consents.get(session_id)
        if receipt:
            receipt.granted_scopes.discard(scope)
            if not receipt.granted_scopes:
                receipt.revoked_at = _now()
        item_ids = [
            item.item_id
            for item in self._items.values()
            if item.session_id == session_id and item.scope is scope
        ]
        for item_id in item_ids:
            del self._items[item_id]
        self._record("scope_revoked_and_deleted", session_id, scope=scope.value)
        return len(item_ids)

    def delete_all(self, session_id: str, *, revoke_consent: bool = True) -> int:
        item_ids = [
            item.item_id for item in self._items.values() if item.session_id == session_id
        ]
        for item_id in item_ids:
            del self._items[item_id]
        if revoke_consent and session_id in self._consents:
            self._consents[session_id].granted_scopes.clear()
            self._consents[session_id].revoked_at = _now()
        self._record("all_memory_deleted", session_id)
        return len(item_ids)

    def purge_expired(self, *, now: datetime | None = None) -> int:
        current = now or _now()
        expired = [item_id for item_id, item in self._items.items() if item.expires_at <= current]
        for item_id in expired:
            item = self._items.pop(item_id)
            self._record(
                "memory_expired", item.session_id, scope=item.scope.value, item_id=item_id
            )
        return len(expired)

    def export(self, session_id: str) -> str:
        receipt = self._consents.get(session_id)
        payload: dict[str, Any] = {
            "session_id": session_id,
            "consent": self._serialize(receipt) if receipt else None,
            "memories": [self._serialize(item) for item in self.view(session_id)],
            "audit": [
                self._serialize(event) for event in self._audit if event.session_id == session_id
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def audit_events(self, session_id: str) -> list[MemoryAuditEvent]:
        return [event for event in self._audit if event.session_id == session_id]

    def _record(
        self,
        event: str,
        session_id: str,
        *,
        scope: str | None = None,
        item_id: str | None = None,
    ) -> None:
        self._audit.append(MemoryAuditEvent(event, session_id, _now(), scope, item_id))

    @staticmethod
    def _serialize(value: object) -> Any:
        data = asdict(value)  # type: ignore[arg-type]
        for key, item in list(data.items()):
            if isinstance(item, datetime):
                data[key] = item.isoformat()
            elif isinstance(item, set):
                data[key] = sorted(str(entry) for entry in item)
            elif isinstance(item, StrEnum):
                data[key] = item.value
        return data
