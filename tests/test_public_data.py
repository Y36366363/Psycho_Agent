import json
import tempfile
import unittest
from pathlib import Path

from psycho_agent.public_data import (
    DataGovernanceError,
    import_normalized_jsonl,
    load_registry,
)


class PublicDataGovernanceTests(unittest.TestCase):
    def test_registry_separates_approved_and_agreement_sources(self) -> None:
        sources = load_registry()
        self.assertEqual(sources["esconv"].status, "approved_restricted")
        self.assertIn("offline_evaluation", sources["esconv"].allowed_uses)
        self.assertEqual(sources["psyqa"].status, "blocked_pending_agreement")
        self.assertEqual(sources["psyqa"].allowed_uses, ())
        self.assertEqual(sources["soulchat_corpus"].license_scope, "unclear_for_dataset")

    def test_training_and_blocked_source_fail_closed(self) -> None:
        sources = load_registry()
        with self.assertRaises(DataGovernanceError):
            sources["esconv"].require_use("model_training")
        with self.assertRaises(DataGovernanceError):
            sources["psyqa"].require_use("offline_evaluation")

    def test_import_minimizes_metadata_rejects_identifiers_and_deduplicates(self) -> None:
        rows = [
            {
                "record_id": "one",
                "messages": [
                    {"role": "user", "content": "  最近工作压力很大。  "},
                    {"role": "assistant", "content": "哪一部分最影响你？"},
                ],
                "unused_sensitive_metadata": {"worker": "raw-id"},
            },
            {
                "record_id": "two",
                "messages": [
                    {"role": "user", "content": "联系我 test@example.com"},
                    {"role": "assistant", "content": "好的"},
                ],
            },
            {
                "record_id": "three",
                "messages": [
                    {"role": "user", "content": "最近工作压力很大。"},
                    {"role": "assistant", "content": "哪一部分最影响你？"},
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            destination = root / "normalized.jsonl"
            source.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = import_normalized_jsonl(
                source_id="esconv",
                intended_use="offline_evaluation",
                input_path=source,
                output_path=destination,
                artifact_revision="test-revision",
                enforce_private_output=False,
            )
            self.assertEqual(report["accepted_records"], 1)
            self.assertEqual(report["rejected_records"], 2)
            self.assertEqual(report["rejection_reasons"]["direct_identifier:email"], 1)
            self.assertEqual(report["rejection_reasons"]["duplicate_content"], 1)
            normalized = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(normalized["record_id"]), 20)
            self.assertEqual(normalized["artifact_revision"], "test-revision")
            self.assertNotIn("unused_sensitive_metadata", normalized)
            self.assertNotIn("test@example.com", json.dumps(report))
            self.assertEqual(len(report["input_sha256"]), 64)
            self.assertEqual(len(report["output_sha256"]), 64)

    def test_cli_policy_requires_ignored_private_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "record_id": "one",
                        "messages": [{"role": "user", "content": "测试"}],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(DataGovernanceError):
                import_normalized_jsonl(
                    source_id="counselingbench",
                    intended_use="offline_evaluation",
                    input_path=source,
                    output_path=root / "unsafe-output.jsonl",
                    artifact_revision="test-revision",
                )


if __name__ == "__main__":
    unittest.main()
