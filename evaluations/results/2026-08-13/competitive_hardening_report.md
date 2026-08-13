# Competitive hardening test report — 2026-08-13

## Evidence translated into implementation

- CounselBench's expert-versus-LLM-judge gap led to a deterministic `clinical_overreach` rule and
  fixed residual fallback rather than another model judge.
- VERA-MH's sequential Yes/No design led to a seven-check crisis audit. Missing verified actions or
  real-world escalation is a `hard_fail`; no warmth or aggregate score can compensate.
- MHSafeEval's interaction-level framing led to bounded session history for final review issues,
  preserving the basis for later trajectory/role adjudication.
- Protocol-safety findings led to a narrow clinical-scope gate instead of pretending a general
  support model can safely perform diagnosis, medication management, trauma exposure, or harmful
  eating-disorder procedures.

## Results

- 108/108 unit and integration tests passed.
- 56/56 offline behavioral cases passed.
- Crisis always precedes the clinical-scope boundary in mixed-risk messages.
- Medication, diagnosis, exposure, and dangerous eating-procedure requests are bounded, while
  ordinary discussion of medication or trauma remains in scope.
- Model drafts and failed rewrites containing individualized medication direction are blocked by a
  deterministic final response.
- A complete fixed crisis plan passes every binary critical check; a constructed plan without
  verified actions or real-world help produces a visible hard failure.
- The human qualitative rubric now separately rates clinical scope and non-abandonment.

## Commands

```bash
python -m unittest discover -s tests
python -m psycho_agent.evaluation
python -m compileall -q src tests
git diff --check
```

No provider API calls were needed: this milestone evaluates orchestration and deterministic safety
properties, not comparative prose quality. The previous provider-blind runs remain separate
language-quality evidence and do not substantiate clinical or crisis claims.

## Residual risk

- Pattern rules have limited recall across euphemisms, dialects, typos, mixed languages, and long
  context. They are guardrails, not validated clinical classifiers.
- The session history records issue kinds but does not yet assign MHSafeEval interaction roles or
  estimate cumulative harm.
- A bare boundary can itself feel rejecting; the current fixed response attempts non-abandonment,
  but real users and professionals still need to rate it.
- Model-assisted review sensitivity remains uncalibrated against real professional annotations.
