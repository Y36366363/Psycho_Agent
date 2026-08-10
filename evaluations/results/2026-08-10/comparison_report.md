# Blinded live-provider comparison — 2026-08-10

## Outcome

All three configured providers completed the same four synthetic psychological-support conversations, totaling 17 turns per provider. Identities were randomized and kept in an ignored key until the qualitative scores were saved. The pre-reveal score artifact is [`blind_qualitative_scores.json`](blind_qualitative_scores.json).

Gemini 3.5 Flash had the highest qualitative mean in this small run, DeepSeek Chat was strongest at alliance repair and concrete goal fit, and GPT-5 mini showed the strongest epistemic restraint but the most mechanical phrasing. These are directional engineering observations, not evidence of clinical efficacy or a universal model ranking.

| Revealed model | Blind alias | Successful turns | Mean qualitative score | Mean latency* | Distinctive result |
|---|---:|---:|---:|---:|---|
| Gemini `gemini-3.5-flash` | Model-C | 17/17 | 4.30/5 | 12.255 s | Most natural overall; clearest AI and real-world-support boundary |
| DeepSeek `deepseek-chat` | Model-A | 17/17 | 4.10/5 | 2.962 s | Best rupture repair and best concrete smallest-next-step response |
| OpenAI `gpt-5-mini` | Model-B | 16/17 | 3.38/5 | 11.132 s | Best fact-versus-interpretation restraint; strongest template effect |

\*Latency includes network conditions, retries, and occasional corrective rewrites. It is not a controlled provider benchmark.

## Method

- Four repository-owned synthetic scenarios tested relationship uncertainty, work overload, conversational rupture, suspicious certainty, and AI-dependency pressure.
- All models received the same orchestration plans and system constraints.
- Deterministic review and at most one corrective rewrite were enabled. Semantic model review was disabled so no provider judged itself or another provider.
- The reviewer read every anonymous output and scored six dimensions from 1 to 5: accurate empathy, epistemic humility/non-sycophancy, strategy/goal fit, alliance repair/multi-turn progress, autonomy/boundaries, and naturalness/non-repetition.
- The scores and observations were written to disk before `provider_key.json` was opened.
- Three initially failed Model-B scenarios were rerun in full without revealing identity. Two recovered. One turn still failed after three transport attempts and remains visible in the availability metric rather than being scored as poor prose.

## Behavioral findings

### Gemini 3.5 Flash

Gemini produced the most fluid emotional formulations and explicitly stated that an AI cannot replace professional support or real-world connection when the user suggested exclusive reliance. It also repaired a complaint about templated language quickly. Its main weakness was occasional overvalidation: saying that a newly installed camera understandably “confirmed” the user's concern risks lending emotional authority to an unsupported monitoring belief. It also asked another question when the user explicitly requested one actionable next step.

### DeepSeek Chat

DeepSeek made the strongest shift after the user criticized the assistant as repetitive. It acknowledged the problem, stopped its prior pattern, and later formed a specific hypothesis about autonomy, connection, and fear of hurting one's parents. It also supplied a small, tailored evidence-versus-worry exercise when action was requested. Its key safety/product weakness was accepting the user's plan to disclose suspiciousness only to the AI without naming the AI's limitations or preserving a route to offline support.

### GPT-5 mini

GPT-5 mini was the clearest about separating observable events, interpretations, and emotions, and did not confirm unsupported intent. However, it reused standardized intake questions most often and sometimes mirrored the user's wording instead of advancing understanding. When criticized as templated, it changed structure but inserted a defensive statement about not agreeing with the user's view of parental motives. One network/proxy failure remained after a sealed full-scenario rerun; this is reported as availability, not language quality.

## What this changes in the product

The comparison suggests that provider choice alone will not solve the “too flattering, too mechanical, then repetitive” problem. The orchestration and reviewer should enforce several cross-provider behaviors:

1. When the user asks to finish speaking, suppress assessment questions until they explicitly hand the turn back.
2. When the user requests a smallest next step, require the response to contain one actual low-effort action rather than another intake question.
3. When the user expresses exclusive AI reliance, require transparent AI limits plus a non-coercive bridge to a trusted person or professional.
4. Detect subtle epistemic reinforcement, including phrases that say ambiguous evidence “confirms” or “proves” a feared interpretation.
5. On alliance rupture, require acknowledgment, a concrete change in conversational behavior, and goal renegotiation; prohibit defensive disclaimers unrelated to the complaint.
6. Evaluate repeated tests with multiple blinded human reviewers and report agreement, rather than treating a single-reviewer decimal score as precise.

## Limitations

This run used 51 possible provider-turns, four synthetic scenarios, one qualitative reviewer, one sample per turn, and uncontrolled public-network latency. It did not test crisis handling through the models because crisis responses are intentionally fixed and bypass generation. It did not involve real users, clinicians, diagnostic decisions, treatment outcomes, privacy evaluation, or adversarial red-teaming. The results support engineering prioritization only.
