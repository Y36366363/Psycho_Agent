# Frozen-study maintenance report — 2026-08-19

## Outcome

`PA-PRO-001` remains intact and ready for a future verified professional reviewer. No frozen session, prompt, generated response, arm label, rubric, endpoint, rating packet, rating form, instruction file, or blinding key was regenerated or edited during this maintenance pass.

The study status remains `awaiting_verified_professional_ratings`. There are zero professional ratings, no inter-rater estimate, and no allowed comparative conclusion.

## Packet audit

- 24 synthetic cases and 72 blinded dialogues remain present.
- All 72 rating rows remain empty; no mock rating was retained.
- Every case receives at least two assignments in each 2–5 reviewer plan.
- All seven reviewer-visible manifest hashes match their files.
- The searched provider, model, arm, condition, latency, and rewrite terms were absent from reviewer-visible material.
- `.env`, `study_key.json`, and `rating_key.json` remain Git-ignored.
- The real `validate-rating` CLI rejected the untouched empty form with exit code 2, as required by fail-closed behavior.

## Defect corrected

The rating validator previously treated an unassigned row as contaminated only if its reviewer ID, numeric dimensions, acceptable field, or hard-failure yes/no field was populated. An accidental rank, hard-failure category, or comment in an unassigned case could therefore be ignored.

The validator now treats every rating-bearing field as evidence of an unassigned rating and rejects the form. A focused regression exercises the exact gap. This changes rating intake validation only; it does not alter any frozen study content or response.

## Supporting regression

- Unit and integration tests: 141/141 passed.
- Offline behavioral cases: 68/68 passed.
- Metamorphic routing variants: 14/14 passed.

These are maintenance checks, not research outcomes. They do not substitute for a qualified professional reviewer and provide no evidence of clinical effectiveness, therapist equivalence, treatment benefit, or production safety.

## Boundary until reviewers are available

No additional conversational feature, synthetic benchmark, automatic judge, provider comparison, or prompt optimization is justified merely because professional recruitment is delayed. The next permitted code changes are limited to newly discovered packet-integrity defects, reviewer-workflow blockers, security defects, or findings triggered by external professional feedback. Everything else remains deferred.
