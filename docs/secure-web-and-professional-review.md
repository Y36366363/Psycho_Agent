# Secure web and professional review operations

This milestone turns four earlier design artifacts into enforceable local workflows. It is
still a research prototype, not a medical device or a production clinical service.

## Encrypted memory and authentication

Long-term memory uses SQLite with AES-256-GCM authenticated encryption. A random 96-bit nonce
is generated per item and the owner, scope, and item identifier are authenticated as associated
data. Consent is explicit and purpose-scoped; users can view, export, delete one item, revoke a
scope with deletion, or delete everything. Audit rows contain events and identifiers, not memory
plaintext. Passwords use salted scrypt hashes, sessions are short-lived random tokens, POST
requests require CSRF tokens, and repeated login failures are temporarily locked.

Generate a key and place it in the ignored `.env` file:

```bash
python -m psycho_agent.secure_store generate-key
python -m psycho_agent.web_app
```

Set `PSYCHO_AGENT_ADMIN_PASSWORD` to at least 12 characters. The local account is
`local-admin`. The default listener is `127.0.0.1:8000`. Production deployment additionally
requires TLS, a managed secrets service, database backups/key rotation, persistent distributed
sessions, external identity verification, monitoring, and an incident-response process.

## Professional eligibility gate

`ReviewerCredentialRegistry` deliberately does not claim that a name or credential number has
been verified automatically. A compliance operator must record an official HTTPS lookup source,
the issuing authority, verifier, evidence digest, verification time, and expiry. A separate
operator reviews a written financial, personal, and intellectual conflict declaration. Pending,
expired, rejected, or recused reviewers cannot count toward clinical governance or submit blind
ratings. Raw credential numbers and evidence files are not stored; only SHA-256 digests are kept.

The applicable authority varies by jurisdiction and profession. Operators must use the relevant
official register and document why it applies; a generic web search is not sufficient.

Reference baselines used for this implementation:

- [NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final) specifies GCM authenticated encryption.
- [China's Ministry of Human Resources and Social Security professional-title verification service](https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/zcfg/gfxwj/rcrs/202309/t20230920_506592.html) documents an official verification route for credentials in its scope.
- [National Health Commission information query portal](https://zwfw.nhc.gov.cn/cxx/) is an official health-practitioner lookup entry point; applicability still requires human jurisdiction/profession matching.
- The [APA guideline-development manual](https://www.apa.org/about/offices/directorates/guidelines/manual) provides a baseline for declaring and managing actual, potential, and perceived conflicts.

## Real blind ratings only

`BlindRatingRepository` accepts scores only from eligible clinical reviewers. Drafts are excluded
from reports, incomplete packets cannot be finalized, and finalized ratings are immutable. The
report status remains `awaiting_verified_professional_ratings` until at least two verified people
finish. Only then does it calculate exact agreement and quadratic-weighted kappa. Synthetic or
developer-authored scores must never be described as clinical evaluation.

The packet at `evaluations/ratings/2026-08-12/rating_packet.json` is ready for independent human
completion. As of 2026-08-12 this repository contains no claim that real clinicians completed it.

## Crisis interface

The authenticated web prototype now embeds the locale-aware crisis card in a navigable page,
with direct call/message actions, accessible alert semantics, official-source metadata, a safe
unknown-locale fallback, security headers, and an explicit AI/non-diagnostic disclosure. Resource
verification dates still require scheduled operational review. The prototype is locally runnable;
it is not a public production deployment.
