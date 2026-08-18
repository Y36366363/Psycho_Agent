# Integrity and regression report — 2026-08-18

The primary milestone is the frozen external professional-evaluation package, not an increase in automated-test counts.

## Study-package integrity

- 24/24 frozen synthetic cases present.
- 72/72 same-base-model arm dialogues complete.
- 216/216 scripted dialogue turns present.
- 12 anchored professional dimensions and 9 hard-failure categories present.
- 72/72 empty rating rows present; zero professional scores populated.
- Assignment plans support 2–5 reviewers and give every dialogue at least two ratings.
- Reviewer-visible arm/model leakage scan passed.
- Seven public artifact checksums matched.
- A fully populated non-human validator fixture passed the rating-form validator and was retained only in `/tmp`; it is not human evidence.
- `study_key.json` and `rating_key.json` remain ignored and unopened for outcome analysis.

## Supporting engineering regression

- Unit/integration tests: 141/141 passed.
- Offline behavioral cases: 68/68 passed.
- Metamorphic routing variants: 14/14 passed.
- Assurance stage: `research_prototype`.
- Verified professional review gate: `pending`.
- Clinical-effectiveness and production-readiness gates: `pending`.

These automated checks only establish that the frozen study can be generated, blinded, assigned, validated, recovered, and analyzed as declared. They do not answer the research question. Only independently finalized ratings from verified professionals can begin to do that.
