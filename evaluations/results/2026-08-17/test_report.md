# Test report — 2026-08-17

- Unit and integration tests: **138/138 passed**.
- Offline behavioral cases: **68/68 passed**.
- Metamorphic routing reliability: **14/14 variants passed**.
- Live connectivity: OpenAI, DeepSeek, and Gemini passed.
- Provider-blinded live regression: **21/21 turns completed** across three synthetic multi-turn conversations.
- Runtime release gate: all three aliases passed.
- Current-rule replay: OpenAI and DeepSeek passed; Gemini failed one released turn for unsupported physiological/effect certainty discovered in the blind audit.

New controls cover per-turn atomic checkpointing and resume, sealed-model consistency, unsupported nervous-system certainty, and tentative cold-water wording as a negative control.

These results establish declared engineering behaviors only. They do not establish clinical effectiveness, real-world safety, professional consensus, or production readiness.
