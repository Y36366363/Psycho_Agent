# Reliability hardening test report — 2026-08-14

## Outcome

- 114/114 unit and integration tests passed.
- 56/56 independent offline behavioral cases passed.
- 14/14 synthetic routing variants passed across five declared invariants.
- The assurance artifact marks engineering regression and declared routing reliability as passed;
  professional review, clinical effectiveness, and production readiness remain pending.

## Defect found and fixed

The initial crisis response included locale-verified call/message actions, but an unresolved second
turn preserved only text and questions. This created a control regression exactly when a person
might become ready to seek help. Follow-up turns now reload verified actions and AI-limit language.
All `zh-CN`, `en-US`, and `en-GB` continuation plans pass the same binary crisis audit as the first
turn. An unknown locale produces a visible `direct_action` hard failure rather than an invented or
mislocalized number.

## Reliability methods

- Meaning-preserving input transformations: inserted Chinese whitespace/separators, zero-width
  characters, and paraphrases.
- Negative contrasts: explicit current denial and benign routing remain non-crisis.
- Precedence conflict: imminent risk remains above a simultaneous medication-change request.
- Stateful checks: unresolved crisis continuation must retain phase, risk, fixed response, direct
  actions, and a passing crisis audit.
- Privacy check: bounded decision evidence contains no synthetic user text.
- Fail-closed assurance: one failed route variant prevents the routing-reliability gate from passing.

## Commands

```bash
python -m unittest discover -s tests
python -m psycho_agent.evaluation
python -m psycho_agent.reliability_evaluation \
  --output evaluations/results/2026-08-14/reliability_report.json
python -m psycho_agent.assurance \
  --unit-passed 114 --unit-total 114 \
  --behavior-passed 56 --behavior-total 56 \
  --reliability-report evaluations/results/2026-08-14/reliability_report.json \
  --output evaluations/results/2026-08-14/assurance_report.json
```

No provider APIs were called. The modified properties are deterministic routing, fixed crisis
controls, input normalization, evidence retention, and assurance gating; model prose comparisons
would not validate them.

## Limits

- The variant set is deliberately small and synthetic.
- Keyword/regex safety detection remains vulnerable to untested euphemisms, dialects, ambiguity,
  code-switching, and context distributed across many turns.
- Decision evidence is not a clinical explanation and is not yet tamper-evident.
- Passing results do not establish clinical safety, efficacy, regulatory compliance, or production
  availability.
