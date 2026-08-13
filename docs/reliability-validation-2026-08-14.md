# Reliability validation — 2026-08-14

## Why this validation was added

Passing a collection of familiar examples is not enough for a psychological-support router.
Reliability also requires stable behavior under realistic input variation, correct precedence when
multiple rules apply, and continuity of safety controls over multiple turns.

The [NIST AI RMF](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) describes robustness as
maintaining performance across varied circumstances and calls for realistic, documented test sets,
ongoing evaluation, and prioritization of failures with more serious consequences. NIST's
[TEVV overview](https://www.nist.gov/ai-test-evaluation-validation-and-verification-tevv) also
separates accuracy, robustness, bias, interpretability, and transparency instead of treating one
metric as sufficient.

Recent multi-turn mental-health evaluation likewise reports performance variation by persona and
degradation as conversations grow longer; see
[Chandra et al., ACL 2026](https://aclanthology.org/2026.acl-long.2164/). This supports testing the
whole route trajectory rather than only isolated assistant replies.

## Implemented reliability controls

### Multi-turn crisis continuity

Previously, the first crisis turn exposed verified call/message actions, but an unresolved second
turn retained only text and questions. The continuation now reloads the same locale-verified actions,
states the AI limit, and passes the same non-compensatory crisis audit. Supported `zh-CN`, `en-US`,
and `en-GB` continuations are tested independently. An unknown locale intentionally fails the direct
action check instead of borrowing or inventing a number.

### Input normalization and metamorphic checks

Safety input is normalized with Unicode NFKC, zero-width-character removal, and conservative removal
of whitespace/separators inserted between Chinese characters. The versioned reliability set contains
14 variants across five invariants:

- imminent self-risk remains crisis-routed across formatting changes;
- an explicit current denial remains low risk across the same changes;
- unresolved crisis continuations retain actions and pass the crisis audit;
- crisis routing outranks a simultaneous medication-boundary request;
- medication-boundary paraphrases remain bounded in Chinese and English.

The report includes only synthetic case identifiers and route outputs. It does not calculate clinical
sensitivity, specificity, or a claim of real-world safety.

### Privacy-minimized decision evidence

Each turn now keeps a maximum of 20 structured routing records. They contain strategy, risk category,
decision basis, action kinds, and policy versions—but never the user's text, matched phrase, response,
or memory content. This gives incident reviewers a compact reason trail without silently creating a
second conversation transcript.

## Remaining limits

- Fourteen transformations are a regression baseline, not representative language coverage.
- Unicode normalization cannot solve euphemisms, code-switching, dialect, ambiguity, or semantic
  risk hidden across many turns.
- Policy-version labels are currently source constants rather than signed release artifacts.
- Decision evidence is process-local and not yet connected to a tamper-evident incident system.
- Real users and qualified professionals must still assess false positives, false negatives,
  comprehensibility, pressure, abandonment, and access outcomes.
