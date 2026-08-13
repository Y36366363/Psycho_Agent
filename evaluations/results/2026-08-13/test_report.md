# Confidence hardening test report — 2026-08-13

## Verified outcomes

- 100/100 unit and HTTP integration tests passed.
- 50/50 independent offline behavioral cases passed.
- The new assurance artifact reports only `engineering_regression` as passed. Verified
  professional review, clinical effectiveness, and production readiness remain pending.
- An independent Web process returned `200 OK` for `/crisis?locale=zh-CN` without a session
  cookie and included the verified 120, 110, and 12356 direct actions.
- The public crisis response retained CSP, `no-store`, `nosniff`, and `no-referrer` headers.
- Scope-specific memory consent and revocation were exercised through the WSGI interface;
  malformed scopes returned `400 Bad Request`, and missing CSRF returned `403 Forbidden`.
- Chinese and English indirect preparation language, including self/other contrasts, routed to
  imminent risk. Benign household-item mentions stayed low risk.

## Defect found and fixed by the expanded evaluation

The English other-person expression incorrectly used an unbounded `he` alternative, which also
matched the middle of words such as `the`. A first-person English preparation disclosure was
therefore initially classified as another person's risk. The pattern now requires word boundaries,
and both unit and behavioral regression cases preserve the fix.

## Commands

```bash
python -m unittest discover -s tests
python -m psycho_agent.evaluation
python -m compileall -q src tests
git diff --check
```

No model-provider API was called in this milestone because the changed surfaces are deterministic
safety triage, evidence reporting, consent UI, and crisis access. Earlier provider comparisons do
not need to be rerun to substantiate these changes.

## Residual limits

- Pattern matching is still a first-pass safety guardrail and cannot provide complete semantic or
  clinical risk assessment.
- The public crisis page is verified locally, not deployed as a highly available public service.
- There are no completed real professional ratings, representative participant outcomes, or
  clinical-effectiveness claims.
- Production TLS, managed keys, tested encrypted backups, penetration testing, incident exercises,
  and jurisdiction-specific review remain missing.
