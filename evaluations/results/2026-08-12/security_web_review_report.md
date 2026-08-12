# Security, Web, and Professional Review Test Report — 2026-08-12

## Outcome

- 90/90 unit and HTTP integration tests passed.
- 47/47 offline behavioral cases passed.
- A separate server process successfully bound to `127.0.0.1:8765`; `GET /health`
  returned `200 OK`, `Cache-Control: no-store`, CSP, `nosniff`, and `no-referrer`.
- An encrypted-memory test confirmed a saved secret was absent from the checkpointed SQLite
  database bytes while remaining viewable with the correct key.
- Authentication tests covered password hashing, roles, session logout, CSRF rejection, and
  temporary lockout after five failed attempts.
- Eligibility tests confirmed that verification evidence and conflict clearance are both needed
  before a reviewer can count toward governance.
- Rating tests confirmed that unverified people cannot submit, incomplete/draft work is not
  reported as completed clinical evaluation, two finalized verified reviewers unlock agreement
  reporting, and finalized ratings cannot be edited.

## Commands

```bash
python -m unittest discover -s tests
python -m psycho_agent.evaluation
python -m compileall -q src tests
git diff --check
```

The tracked-file credential scan found no common OpenAI, Gemini, or DeepSeek key pattern. Provider
APIs were not called because this milestone changes storage, identity, review governance, and the
local interface rather than model behavior; the prior same-day multi-provider regression remains
the relevant provider result.

## Important limits

- The local development server is not a production deployment and does not supply TLS.
- SQLite metadata and audit identifiers are not whole-database encrypted; memory values are
  application-layer AES-GCM ciphertext. Production should use managed encrypted storage plus
  application-layer encryption for especially sensitive fields.
- Professional verification is a documented human control, not an automated government-register
  integration. No real reviewer record or clinical score was created during testing.
- System-wide `pip check` reported pre-existing LangChain/Streamlit dependency conflicts outside
  this project's dependency set. Psycho Agent's declared `cryptography` dependency imported and
  passed its tests.
