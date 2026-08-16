"""License- and privacy-gated intake for normalized public research data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "evaluations" / "public_data_sources.json"
PRIVATE_DATA_ROOT = ROOT / "data" / "public"
SUPPORTED_USES = {
    "offline_evaluation",
    "strategy_taxonomy_analysis",
    "model_training",
    "production_retrieval",
}
ALLOWED_ROLES = {"user", "assistant", "system"}
_DIRECT_IDENTIFIER_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)"),
    "url": re.compile(r"https?://\S+", re.IGNORECASE),
    "cn_id": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "named_self_id": re.compile(
        r"(?:我叫[\u4e00-\u9fff]{2,4}|\bmy name is\s+[A-Z][A-Za-z'-]+)", re.IGNORECASE
    ),
}


class DataGovernanceError(ValueError):
    """Raised when source, use, path, or content fails a declared data gate."""


@dataclass(frozen=True, slots=True)
class PublicDataSource:
    id: str
    title: str
    landing_url: str
    access_mode: str
    declared_license: str
    license_scope: str
    provenance: str
    contains_sensitive_text: bool
    status: str
    allowed_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]
    requirements: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PublicDataSource":
        return cls(
            **{
                **value,
                "allowed_uses": tuple(value.get("allowed_uses", [])),
                "prohibited_uses": tuple(value.get("prohibited_uses", [])),
                "requirements": tuple(value.get("requirements", [])),
            }
        )

    def require_use(self, intended_use: str) -> None:
        if intended_use not in SUPPORTED_USES:
            raise DataGovernanceError(f"Unsupported intended use: {intended_use}.")
        if self.status != "approved_restricted":
            raise DataGovernanceError(
                f"Source {self.id} is not approved: status={self.status}."
            )
        if intended_use not in self.allowed_uses or intended_use in self.prohibited_uses:
            raise DataGovernanceError(
                f"Source {self.id} does not permit intended use {intended_use}."
            )


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, PublicDataSource]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not payload.get("version") or not isinstance(payload.get("sources"), list):
        raise DataGovernanceError("Registry needs a version and sources list.")
    sources: dict[str, PublicDataSource] = {}
    for raw in payload["sources"]:
        source = PublicDataSource.from_dict(raw)
        if source.id in sources:
            raise DataGovernanceError(f"Duplicate source id: {source.id}.")
        if not source.landing_url.startswith("https://"):
            raise DataGovernanceError(f"Source {source.id} must use an HTTPS landing URL.")
        unknown_uses = set(source.allowed_uses) - SUPPORTED_USES
        if unknown_uses:
            raise DataGovernanceError(
                f"Source {source.id} has unknown uses: {sorted(unknown_uses)}."
            )
        if source.status != "approved_restricted" and source.allowed_uses:
            raise DataGovernanceError(
                f"Blocked source {source.id} cannot declare allowed uses."
            )
        sources[source.id] = source
    return sources


def _private_output(path: Path) -> bool:
    try:
        path.resolve().relative_to(PRIVATE_DATA_ROOT.resolve())
    except ValueError:
        return False
    return True


def _identifier_findings(text: str) -> set[str]:
    return {
        name for name, pattern in _DIRECT_IDENTIFIER_PATTERNS.items() if pattern.search(text)
    }


def _normalize_record(
    raw: dict[str, Any],
    source: PublicDataSource,
    intended_use: str,
    artifact_revision: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    reasons: list[str] = []
    record_id = str(raw.get("record_id", "")).strip()
    messages = raw.get("messages")
    if not record_id:
        reasons.append("missing_record_id")
    if not isinstance(messages, list) or not messages:
        reasons.append("missing_messages")
        return None, reasons

    normalized_messages: list[dict[str, str]] = []
    total_characters = 0
    for message in messages:
        if not isinstance(message, dict):
            reasons.append("invalid_message")
            continue
        role = str(message.get("role", "")).strip().lower()
        content = " ".join(str(message.get("content", "")).strip().split())
        if role not in ALLOWED_ROLES or not content:
            reasons.append("invalid_message")
            continue
        findings = _identifier_findings(content)
        reasons.extend(f"direct_identifier:{finding}" for finding in sorted(findings))
        total_characters += len(content)
        normalized_messages.append({"role": role, "content": content})

    if total_characters > 12_000:
        reasons.append("record_too_long")
    if reasons:
        return None, sorted(set(reasons))

    stable_id = hashlib.sha256(
        f"{source.id}:{artifact_revision}:{record_id}".encode()
    ).hexdigest()[:20]
    return (
        {
            "record_id": stable_id,
            "source_id": source.id,
            "artifact_revision": artifact_revision,
            "permitted_use": intended_use,
            "messages": normalized_messages,
        },
        [],
    )


def import_normalized_jsonl(
    *,
    source_id: str,
    intended_use: str,
    input_path: str | Path,
    output_path: str | Path,
    artifact_revision: str,
    registry_path: str | Path = DEFAULT_REGISTRY,
    enforce_private_output: bool = True,
    max_records: int = 10_000,
) -> dict[str, Any]:
    sources = load_registry(registry_path)
    if source_id not in sources:
        raise DataGovernanceError(f"Unknown source: {source_id}.")
    source = sources[source_id]
    source.require_use(intended_use)
    artifact_revision = artifact_revision.strip()
    if not artifact_revision or len(artifact_revision) > 200:
        raise DataGovernanceError("artifact_revision must contain 1-200 characters.")
    destination = Path(output_path)
    if enforce_private_output and not _private_output(destination):
        raise DataGovernanceError(
            f"Imported text must stay under ignored directory {PRIVATE_DATA_ROOT}."
        )
    if not 1 <= max_records <= 100_000:
        raise DataGovernanceError("max_records must be between 1 and 100000.")

    accepted: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_content: set[str] = set()
    rejection_reasons: Counter[str] = Counter()
    input_records = 0
    with Path(input_path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            input_records += 1
            if input_records > max_records:
                rejection_reasons["record_limit_exceeded"] += 1
                break
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                rejection_reasons["invalid_json"] += 1
                continue
            if not isinstance(raw, dict):
                rejection_reasons["invalid_record"] += 1
                continue
            normalized, reasons = _normalize_record(
                raw, source, intended_use, artifact_revision
            )
            if reasons or normalized is None:
                rejection_reasons.update(reasons or [f"invalid_record_line:{line_number}"])
                continue
            if normalized["record_id"] in seen_ids:
                rejection_reasons["duplicate_record_id"] += 1
                continue
            content_hash = hashlib.sha256(
                json.dumps(normalized["messages"], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            if content_hash in seen_content:
                rejection_reasons["duplicate_content"] += 1
                continue
            seen_ids.add(normalized["record_id"])
            seen_content.add(content_hash)
            accepted.append(normalized)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in accepted),
        encoding="utf-8",
    )
    input_digest = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
    output_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "registry_version": json.loads(Path(registry_path).read_text())["version"],
        "source_id": source.id,
        "artifact_revision": artifact_revision,
        "intended_use": intended_use,
        "input_records": input_records,
        "accepted_records": len(accepted),
        "rejected_records": input_records - len(accepted),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "output_is_private": _private_output(destination),
        "raw_content_in_report": False,
        "input_sha256": input_digest,
        "output_sha256": output_digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed import of normalized public data")
    parser.add_argument("--source", required=True)
    parser.add_argument("--use", required=True, choices=sorted(SUPPORTED_USES))
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--artifact-revision",
        required=True,
        help="Upstream commit, tag, or dataset revision used for this import",
    )
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--max-records", type=int, default=10_000)
    args = parser.parse_args()
    try:
        report = import_normalized_jsonl(
            source_id=args.source,
            intended_use=args.use,
            input_path=args.input,
            output_path=args.output,
            artifact_revision=args.artifact_revision,
            registry_path=args.registry,
            max_records=args.max_records,
        )
    except DataGovernanceError as exc:
        raise SystemExit(f"Data governance error: {exc}") from exc
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
