# Test report — 2026-08-16

- Unit and integration tests: **132/132 passed**.
- Offline behavioral cases: **66/66 passed**.
- Metamorphic routing reliability: **14/14 variants passed**.
- Provider connectivity: OpenAI, DeepSeek, and Gemini passed.
- Focused live comparison: **12/12 turns completed** across two separately preserved runs.
- Current-rule replay: first run 3/3 aliases passed after deterministic release; second run 2/3 passed and one current `unsafe_claim` blocker was identified.

The automated results establish only declared engineering behavior. Verified professional review, clinical effectiveness, and production readiness remain pending.
