# Architecture decisions

## ADR-001: Separate conversation planning from language generation

**Status:** accepted

The core produces a typed `TurnPlan` before any model writes prose. This makes the agent's intended action inspectable, testable, and provider-neutral. It also prevents a single system prompt from owning intake, safety, memory, therapeutic strategy, and writing style simultaneously.

## ADR-002: Use dynamic state, not personality labels

**Status:** accepted

The agent stores current emotions, impact, preferences, attempted actions, and explicitly provisional working hypotheses. It does not assign a personality type or diagnosis from a few opening questions.

## ADR-003: Crisis flow takes precedence

**Status:** accepted

Any elevated explicit safety signal bypasses ordinary response generation. The first implementation is intentionally conservative and explainable, while recognizing that keyword rules alone are insufficient for production.

## ADR-004: Repetition is a state-management problem

**Status:** accepted

The session remembers recently used strategies and response goals. Routing avoids immediate reuse. Later milestones will add semantic similarity checks across generated responses.

## ADR-005: Keep model providers behind one text interface

**Status:** accepted

OpenAI Responses, DeepSeek Chat Completions, and Gemini GenerateContent use separate adapters behind the same `TextModel` protocol. The psychological-support workflow and reviewer do not depend on a provider-specific SDK.

## ADR-006: Review every normal draft with bounded correction

**Status:** accepted

Deterministic checks run on every normal generated response. An optional semantic model reviewer catches contextual failures that patterns cannot. A rejected draft receives at most one rewrite, preventing loops and unbounded API cost. Fixed crisis responses bypass model generation and rewriting.

## ADR-007: Treat alliance rupture as a routing event

**Status:** accepted

User statements that the agent misunderstood, repeated itself, or became templated update an explicit alliance state. The next strategy repairs the conversational goal or task before offering another intervention.

## ADR-008: Use contrast-set safety evaluation

**Status:** accepted

Safety tests must distinguish self from other, present from historical risk, current intent from explicit denial, and lived disclosures from fictional or general questions. Obvious keyword-positive examples alone are not an adequate safety evaluation.

## ADR-009: Build an evaluation baseline before fine-tuning

**Status:** accepted

Published counseling datasets can inform strategy taxonomy and future evaluation, but fine-tuning is deferred until licensing, provenance, privacy, and a provider-comparison baseline are established.

## ADR-010: Blind provider comparisons before interpretation

**Status:** accepted

Every provider receives the same ordered synthetic multi-turn scenarios with semantic self-review disabled. Provider names are randomized into aliases and stored in a separate ignored key. Qualitative scores must be persisted before the key is opened. This reduces brand anchoring, but it does not remove reviewer subjectivity or establish clinical validity.

Failed turns are treated separately from response quality. Transient network failures receive bounded retries; if a turn still fails, the complete scenario can be rerun while sealed so subsequent turns retain coherent context. Availability, latency, deterministic review flags, and qualitative language scores remain separate measurements.

## ADR-011: Preserve verified TLS while supporting incomplete Python CA configuration

**Status:** accepted

Provider requests use Python's verified default SSL context. If the local Python installation exposes no default certificate authorities, the transport falls back to the operating system bundle at `/etc/ssl/cert.pem`. Certificate verification is never disabled. Transient transport errors and selected retryable HTTP statuses receive at most three attempts with short backoff; normal client errors are not retried.

## ADR-012: User pacing interrupts intake

**Status:** accepted

An intake sequence is subordinate to an explicit conversational boundary. “I have not finished” creates a durable advice pause: normal assessment questions and techniques stop until the user explicitly asks to analyze, plan, or take a next step. A request for one smallest next step routes directly to a concrete action, even when high reported distress would otherwise select grounding. These signals are auditable state, not prompt-only suggestions.

## ADR-013: Bound model correction and deterministically close residual high-impact failures

**Status:** accepted

Normal drafts still receive at most one model rewrite. If the rewritten response continues to encourage exclusive AI reliance or reinforce an unsupported high-certainty interpretation, a deterministic response replaces it without another provider call. This trades some stylistic variety for a stable boundary on high-impact failures while avoiding an unbounded self-correction loop. The final replacement is reviewed again and recorded in evaluation metadata.

## ADR-014: Evaluate stages and cross-cutting safeguards separately

**Status:** accepted

Qualitative comparison uses versioned behavioral anchors divided into exploration, insight, action, and cross-cutting dimensions. This borrows the interpretable stage structure of ESC-Judge but does not collapse alliance repair, safety boundaries, autonomy, or naturalness into a therapy-effectiveness claim. Automated judges may assist scaling later, but blinded human and clinician ratings remain necessary for consequential evaluation.

## ADR-015: Long-term memory is opt-in, purpose-scoped, and erasable

**Status:** accepted

Ordinary session state remains ephemeral. Long-term memory cannot be written until the user grants explicit consent for a named scope such as preferences, goals, support network, or attempted actions. Consent for one scope does not authorize another. Users can inspect and export stored items, delete one item, revoke a scope with linked deletion, or delete everything. Retention expiry is mandatory. Audit events record operations and identifiers, not memory text. The current vault is deliberately in-memory; encrypted persistence and authentication are separate deployment requirements.

## ADR-016: Crisis resources are verified data, not generated text

**Status:** accepted

Phone numbers and escalation links live in a versioned registry with locale, official source, and verification date. Supported actions are rendered as `tel:`, `sms:`, or HTTPS links. An unknown locale never borrows another country's number or asks a model to invent one; it returns a neutral instruction to contact local emergency services with no direct number. The registry currently covers `zh-CN`, `en-US`, and `en-GB` and requires periodic regional review.

## ADR-017: Clinical behavior changes require independent approval and rollback

**Status:** accepted

Changes to safety, strategies, reviewer rules, crisis text, or therapeutic-sounding skills require linked evidence, two distinct clinical approvals, and one independent safety approval before activation. Reviewer identity cannot be counted twice. Previously active versions remain addressable, and a safety-role actor can perform a reasoned emergency rollback. This code provides workflow enforcement and audit records; verifying professional credentials remains an organizational responsibility.

## ADR-018: Evaluate the client side and reviewer agreement

**Status:** accepted

Silence is not satisfaction. Felt understanding remains unknown until explicitly reported. Pressure, correction, action rejection, rejection reasons, exit intent, and exit reasons are independent client-side signals. Clinician evaluation removes even anonymous model aliases from rating packets and reports agreement per dimension using exact agreement and pairwise quadratic-weighted kappa; it does not average safety and warmth into one score.
