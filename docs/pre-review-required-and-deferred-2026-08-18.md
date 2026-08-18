# Before the first professional reviewer: required versus deferred

## Code and artifact must-haves

Only the following are blocking before the first real reviewer receives material:

1. Finish all 72 same-base-model synthetic dialogues without API errors or missing turns.
2. Generate the randomized rating packet and verify that no provider, model, condition, rewrite, latency, or arm identifiers leak into it.
3. Freeze and checksum the session set, prompts, preregistration, rubric, packet, CSV form, and instructions; preserve ignored arm keys separately.
4. Run the packet integrity and rating-form validation path once on a copied reviewer form.
5. Record the actual study status as `awaiting_verified_professional_ratings`; do not create placeholder ratings.

**Current status:** all five code/artifact requirements were satisfied on 2026-08-18. There is no remaining code blocker before the first reviewer. Do not add another feature merely to delay handoff.

The credential registry, conflict review, immutable finalization, ordinal agreement, hard-failure agreement, and disagreement reporting code already exist. Reviewer recruitment, license verification, conflict review, secure file transfer, compensation, scheduling, and informed reviewer instructions are operational responsibilities—not missing model features.

The immediate next actions are therefore operational: choose the 2–5 reviewer plan, verify the first reviewer's current credential, clear conflicts, assign an opaque ID, and deliver only the reviewer-visible files.

## Deferred backlog

Unless external reviewers identify a defect that blocks valid scoring, defer all of the following:

- additional conversational features, rules, synthetic profiles, model adapters, or provider rankings;
- expanding unit-test counts beyond regression needed to preserve the frozen study;
- LLM-as-judge scoring, automated prompt optimization, fine-tuning, RAG, or training on public mental-health text;
- new memory features, UI polish, mobile applications, public deployment, analytics, or production scaling;
- patient recruitment, symptom/outcome measures, treatment comparisons, or any clinical-effectiveness study;
- claims about therapist replacement, clinical equivalence, diagnosis, production safety, or jurisdictional compliance;
- additional benchmarks or datasets that do not answer a specific disagreement or failure found by professional reviewers.

After the packet is delivered, the next accepted research input is external professional evidence. Code changes should be triggered by packet integrity problems, reviewer workflow blockers, or predeclared findings—not by a desire to increase repository activity.
