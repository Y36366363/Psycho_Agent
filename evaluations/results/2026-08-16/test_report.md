# Test report — 2026-08-16

- Unit and integration tests: **136/136 passed**.
- Offline behavioral cases: **66/66 passed**.
- Metamorphic routing reliability: **14/14 variants passed**.
- Provider connectivity: OpenAI, DeepSeek, and Gemini passed.
- Focused live comparison: **12/12 turns completed** across two separately preserved runs.
- Current-rule replay: first run 3/3 aliases passed after deterministic release; second run 2/3 passed and one current `unsafe_claim` blocker was identified.
- Governed public-data smoke test: **3/3 records accepted** from a pinned CounselingBench revision; answers/explanations were excluded, the report contains no source text, and the output is Git-ignored.

The four new data-governance tests cover registry status separation, prohibited training and agreement-gated sources, metadata minimization/direct-identifier rejection/deduplication, and enforcement of the private ignored output root.

The automated results establish only declared engineering behavior. Verified professional review, clinical effectiveness, and production readiness remain pending.
