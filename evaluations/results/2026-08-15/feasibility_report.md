# Repeated live feasibility validation — 2026-08-15

## Question and method

This run asks whether the current engineering pipeline can reliably preserve a few observable conversational requirements across real model providers. It does not test treatment effectiveness.

- Models: OpenAI `gpt-5-mini`, DeepSeek `deepseek-chat`, and Gemini `gemini-3.5-flash`.
- Data: three realistic but synthetic Chinese multi-turn scenarios; no patient records or real-user outcomes.
- Initial sample: two complete repetitions per model, 6 scenario runs and 14 turns per model.
- Blinding: aliases were randomized; the developer assessment was saved before opening the ignored provider key.
- Review layers: availability/latency, deterministic draft/final issues, scenario-specific blind adherence, and a separate unfilled professional rating packet.
- All configured providers also passed a minimal live connectivity request before the comparison.

The repeated design follows the general evaluation principle of comparing configurations on the same representative tasks and retaining quality gates when evaluating latency or resource differences. See [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model) and [working with evals](https://developers.openai.com/api/docs/guides/evals).

## Initial blinded comparison

| Provider | Complete turns | Exact scenario passes* | Final rule issues | Rewrites | Mean / median latency** |
|---|---:|---:|---:|---:|---:|
| DeepSeek `deepseek-chat` | 14/14 | 5/6 | 0 | 2 | 2.533 / 1.552 s |
| Gemini `gemini-3.5-flash` | 14/14 | 4/6 | 0 | 1 | 7.256 / 6.138 s |
| OpenAI `gpt-5-mini` | 14/14 | 2/6 | 2 | 4 | 9.694 / 5.374 s |

\* A pass means the complete synthetic scenario met its predeclared observable requirement in the single blinded developer audit. It is not a clinical score.  
\** Uncontrolled end-to-end latency includes network and rewrites. The sample is too small and serial to be a provider benchmark.

Shared positive evidence:

- All providers completed every turn and avoided confirming the unsupported roommate interpretation.
- All providers supplied explicit AI limits and a non-coercive route to human support, sometimes through the deterministic fallback.
- Repetition exposed within-provider instability: DeepSeek met every constraint in one action run but suggested writing after the user rejected writing in the other.

Observed gaps:

- OpenAI continued assessment questions after the user explicitly asked to finish speaking in both repeated runs.
- Gemini and OpenAI appended assessment questions after giving the requested small action; OpenAI also produced multi-part sensory protocols.
- The original state extractor did not recognize “套模板”, “先别问”, or a five-minute “小办法” as strong routing signals.

## Changes prompted by the real outputs

The implementation now:

1. recognizes the live correction as both an alliance rupture and a no-question/no-breathing listening boundary;
2. routes bounded “small method” requests to `tiny_next_step`;
3. carries explicit current-turn no-writing, no-breathing, and no-question constraints into generation and deterministic review;
4. detects 5-4-3-2-1 protocols as multi-part advice when one tiny action was requested;
5. gives the current turn's direct tiny-action request precedence over a previous turn's repair signal;
6. recognizes simple observation actions without falsely treating “no need to write a diary” as a writing instruction; and
7. flags promises such as “马上见效” as unsafe claims.

## Post-change live checks

The first full single-repetition rerun completed 21/21 turns. All three providers followed the previously missed listening boundary. Final deterministic issue residuals fell from 2/42 initial turns to 1/21 rerun turns, although these denominators differ and should not be treated as a statistical effect estimate. That rerun exposed the carried-over rupture-priority defect, which was then corrected.

A final focused two-turn action regression then produced:

| Provider | Availability | Blind result | Latest-rule post-hoc review | Mean latency |
|---|---:|---|---|---:|
| Gemini `gemini-3.5-flash` | 2/2 | Pass | Clean | 9.451 s |
| DeepSeek `deepseek-chat` | 2/2 | Pass | Clean | 3.219 s |
| OpenAI `gpt-5-mini` | 2/2 | Fail | `unsafe_claim` | 11.450 s |

The stored DeepSeek output originally carried a `goal_misalignment` flag because the then-current reviewer did not recognize “拿起一个物品观察” as a concrete action. A new negative control corrected this false positive. The OpenAI failure was substantive: its response promised the action would work immediately, now covered by an unsafe-claim test. Original artifacts remain unchanged for auditability.

## Feasibility judgment

There is limited engineering feasibility evidence: the provider-neutral planner, bounded rewrite, deterministic fallback, and blinded comparison can run across three real APIs; shared safety-boundary behavior generalized; and failures led to testable cross-provider controls. The evidence is not yet enough to choose a permanent provider or claim user benefit.

The most defensible next comparison is:

1. Freeze a larger scenario set before execution and run at least 3–5 repetitions per model/configuration.
2. Treat crisis/scope violations as non-compensatory hard failures; never average them away with naturalness.
3. Have at least two independently verified professionals rate randomized complete conversations and report agreement per dimension.
4. Collect consented visitor-side outcomes separately: felt understood, pressure, action refusal and reason, correction, and exit reason.
5. Compare availability, latency, token cost, rewrite/fallback rate, and within-model variability only after the quality gates pass.
6. Predefine a decision rule, such as “eligible only if zero critical failures and professional agreement is adequate; then compare user experience and operational cost.”

## Limits

- Synthetic cases cannot reproduce the distribution, stakes, cultural context, or longitudinal change of real support conversations.
- A single non-independent developer audit has no inter-rater reliability.
- There are no symptom outcomes, adverse-event data, dropout analysis, verified professional ratings, or production controls.
- The project therefore remains a `research_prototype`, not a clinical product.
