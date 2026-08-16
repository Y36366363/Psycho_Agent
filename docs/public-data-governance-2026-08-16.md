# Public data intake and governance — 2026-08-16

## Decision

Public availability is not treated as permission to train a mental-health product. Psycho Agent now separates four questions for every artifact: whether it can be downloaded, what the exact artifact license permits, whether the collection contains sensitive human text, and which product use is justified. No registered source is approved for model training or production retrieval by default.

The repeatable discovery path is:

1. Start with a paper or benchmark citation, then find the authors' official repository or dataset card.
2. Review the exact data artifact, not only the code repository license.
3. Record collection provenance, synthetic transformations, access agreements, privacy statements, and redistribution terms.
4. Assign an allowed purpose before download: offline evaluation, taxonomy analysis, training, or production retrieval are separate decisions.
5. Pin an upstream commit, tag, or revision and retain checksums without committing source text.
6. Normalize only necessary fields, scan for obvious direct identifiers, deduplicate, and keep all imported text under ignored `data/public/`.
7. Keep benchmark items out of training and report only aggregate import/evaluation results.

## Source decisions

| Source | Public evidence | Current project decision |
|---|---|---|
| ESConv | The official repository describes 1,300 crowd-worker role-play conversations and limits the data/code to academic research. | Offline evaluation and strategy-taxonomy analysis only; no training, retrieval, or redistribution. |
| PsyQA | The official repository requires a signed user agreement for the full dataset. | Blocked until an agreement, authorized-purpose record, and privacy review exist. |
| SoulChatCorpus | The project reports a large mixed corpus and extensive filtering, while the visible repository license does not by itself settle every dataset artifact's terms. | Blocked pending artifact-level license, provenance, privacy, and safety review. |
| CPsyCounD / CPsyCounR | CPsyCounR requires a privacy agreement; CPsyCounD is reconstructed from reports and literature structures. | Both blocked until the relevant agreement or artifact/provenance review is complete. |
| CounselingBench | The dataset card declares Apache-2.0 and describes 1,621 multiple-choice items derived from NCMHCE mock-exam case studies. | Offline knowledge/process evaluation only. It is not conversational-outcome evidence. |
| CounselBench Eval / Adv | The official project describes professional ratings and adversarial prompts; its evaluation artifact has artifact-specific noncommercial/no-derivatives terms. | Blocked pending exact-artifact and privacy review. |

Registry details and requirements are machine-readable in `evaluations/public_data_sources.json`.

## Implemented intake boundary

`python -m psycho_agent.public_data` accepts only normalized JSONL records with `record_id` and a non-empty `messages` list. The importer:

- fails closed unless the source and intended use are explicitly approved;
- requires an upstream artifact revision;
- refuses normal CLI output outside ignored `data/public/`;
- strips arbitrary source metadata and hashes source record IDs;
- rejects malformed records, duplicate IDs/content, records above 12,000 characters, and obvious emails, phone numbers, URLs, Chinese identity numbers, or self-name phrases;
- emits content-free counts, rejection reasons, and input/output SHA-256 values.

The identifier scan is a conservative engineering screen, **not proof of anonymization**. Human-derived help-seeking text still requires privacy/ethics review, sampling, jurisdictional analysis, and a documented retention/deletion process. Reports must not quote rejected or accepted records.

## Reproducible sample check

For the initial smoke test, three CounselingBench rows were retrieved through the official Hugging Face dataset service and pinned to repository revision `1de4c291d1b30e23cc71ee483914b49089505579`. The transformation retained only case context, the question, and answer choices; correct-answer and explanation fields were deliberately excluded. All three records passed normalization, the output contains only the five declared fields, and the file is ignored by Git.

This check demonstrates a traceable ingestion boundary. It does not demonstrate clinical effectiveness, conversational quality, benchmark validity, or safe use with real help-seekers.

## References

- [ESConv official repository](https://github.com/thu-coai/Emotional-Support-Conversation)
- [PsyQA official repository](https://github.com/thu-coai/PsyQA)
- [SoulChat official repository](https://github.com/scutcyr/SoulChat)
- [CPsyCoun official repository](https://github.com/CAS-SIAT-XinHai/CPsyCoun)
- [CounselingBench dataset card](https://huggingface.co/datasets/ckmjx/CounselingBench)
- [CounselBench official repository](https://github.com/llm-eval-mental-health/CounselBench)

