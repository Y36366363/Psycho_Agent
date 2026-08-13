# Assurance model

Psycho Agent uses four evidence gates that cannot substitute for one another:

1. **Engineering regression** — deterministic unit, integration, and behavioral tests.
2. **Verified professional review** — completed blinded ratings from at least two independently
   verified professionals, including agreement reporting.
3. **Clinical effectiveness** — a prospective protocol, representative participants, user outcomes,
   adverse events, dropout reasons, and independent clinical/statistical interpretation.
4. **Production readiness** — TLS, managed keys, tested encrypted backups, independent security
   testing, incident-response exercise, and jurisdiction-specific review.

`python -m psycho_agent.assurance` produces a machine-readable report. A green engineering gate
means only that declared tests passed. It does not mean the system is clinically validated, safe in
all cases, equivalent to a therapist, or ready for public deployment.

This separation follows the testing, evaluation, verification, and validation orientation of the
[NIST AI Risk Management Framework resources](https://airc.nist.gov/) and the
[NIST Generative AI Profile](https://www.nist.gov/itl/ai-risk-management-framework/ai-risk-management-framework-resources).
WHO guidance calls for well-defined tasks, diverse stakeholder involvement, continuous assessment,
and post-release independent auditing; see the [WHO LMM governance guidance](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models).

Regulatory classification depends on the product's intended claims and jurisdiction. For example,
UK guidance says digital mental-health software intended to diagnose, prevent, or treat conditions
may fall under medical-device requirements; see the [MHRA digital mental-health guidance](https://www.gov.uk/government/news/digital-mental-health-technologies-guidance-launched-to-help-manufacturers-and-safeguard-users).

## Current 2026-08-13 status

- Engineering regression: passed, 100/100 unit and HTTP integration tests and 50/50 behavioral cases.
- Verified professional review: pending; no real rating is claimed.
- Clinical effectiveness: pending; no clinical validation is claimed.
- Production readiness: pending; the Web server remains local-development software.
