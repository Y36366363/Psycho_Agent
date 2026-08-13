# Updates 8/14/2026

- Fixed a multi-turn crisis continuity defect: unresolved second and later crisis turns now retain locale-verified call/message actions, AI-limit language, safety questions, and the same non-compensatory crisis audit as the first turn.
- Added Unicode NFKC, zero-width-character removal, and conservative Chinese separator normalization so formatting changes do not silently bypass tested crisis routes; explicit-denial negative controls prevent indiscriminate escalation.
- Added a versioned metamorphic reliability suite covering 14 variants across crisis formatting, denial, unresolved follow-up, crisis-versus-medication precedence, and Chinese/English medication-boundary paraphrases.
- Added a separate assurance gate for routing reliability. Unit tests can remain green while this gate stays pending if any declared route variant fails; passing it does not claim clinical sensitivity, specificity, or real-world safety.
- Added privacy-minimized decision evidence with phase, strategy, risk category, named decision basis, action kinds, and policy versions. It stores no user or assistant text and retains only the latest 20 records.
- Expanded the suite to 114 passing unit and integration tests, 56/56 behavioral cases, and 14/14 routing-reliability variants. See the [August 14 reliability validation](docs/reliability-validation-2026-08-14.md), [machine-readable report](evaluations/results/2026-08-14/reliability_report.json), and [test report](evaluations/results/2026-08-14/test_report.md).

# Updates 8/13/2026

- Added an [August 13 competitive review](docs/competitive-review-2026-08-13.md) covering CounselBench, VERA-MH, MHSafeEval, DialogGuard, CAPE's market sample, protocol-safety research, and PsychAgent, with explicit adopt/defer/reject decisions.
- Added a clinical-scope gate: crisis routing always remains first, while non-crisis requests for diagnosis, medication changes, unsupervised trauma exposure, or dangerous eating-disorder procedures receive a fixed non-abandoning boundary and a practical bridge to qualified care.
- Added output-side `clinical_overreach` review so a model cannot volunteer medication or specialized-treatment directions; one failed rewrite is replaced by a deterministic non-prescriptive response.
- Added a VERA-MH-inspired binary crisis audit covering fixed crisis routing, model bypass, real-world help, verified actions, direct safety questions, AI identity, and secrecy/diagnosis. Critical misses produce `hard_fail`; there is deliberately no average safety score.
- Added bounded per-session final-review issue history as groundwork for MHSafeEval-style cumulative interaction auditing, and added clinical scope/non-abandonment to the human qualitative rubric.
- Expanded the suite to 108 passing unit and integration tests and 56/56 offline behavioral cases. See the [competitive hardening report](evaluations/results/2026-08-13/competitive_hardening_report.md); automated and model-assisted evaluation remains engineering evidence, not a substitute for real professional or clinical evaluation.
- Added a machine-readable assurance model that keeps engineering regression, verified professional review, clinical effectiveness, and production readiness as non-substitutable evidence gates; automated success can no longer be summarized as clinical validation.
- Published explicit allowed and prohibited claims. The current stage remains `research_prototype`: real professional ratings, prospective participant outcomes, adverse-event/dropout analysis, independent review, and production controls are still pending.
- Removed authentication from the localized crisis page so emergency call, message, and official-source actions remain available even when a user cannot log in.
- Replaced the Web prototype's all-scopes memory consent with real per-purpose selection, visible active scopes, and direct per-scope revocation with linked deletion; malformed scope requests now return bounded `400` responses.
- Expanded crisis triage for indirect preparatory language involving means, timing, goodbye letters, and “not waking up,” with Chinese/English and self/other contrast tests while preserving household-item negative controls.
- Expanded the suite to 100 passing unit and HTTP integration tests and 50/50 offline behavioral cases. See the [assurance model](docs/assurance-model.md), [machine-readable assurance report](evaluations/results/2026-08-13/assurance_report.json), and [test report](evaluations/results/2026-08-13/test_report.md).

# Updates 8/12/2026

- Replaced the optional in-process-only memory path with an authenticated SQLite option that encrypts every saved value using AES-256-GCM, binds ciphertext to its owner and purpose, and preserves consent, view/export, retention, scope revocation, and deletion controls.
- Added salted scrypt password authentication, short-lived server-side sessions, CSRF enforcement, login throttling, owner isolation, security headers, and ignored database/key locations.
- Added a manual professional-eligibility register: clinical and safety approvals count only after official-source evidence, verifier, validity dates, and a separately reviewed conflict-of-interest declaration are recorded; expired, pending, or recused reviewers are rejected.
- Added durable blind-rating intake that accepts only eligible clinical reviewers, prevents incomplete finalization and post-finalization edits, excludes drafts, and continues to report `awaiting_verified_professional_ratings` until at least two real verified professionals finish.
- Added a runnable authenticated Web prototype with AI/non-diagnostic disclosure, memory controls, JSON export, and embedded locale-aware crisis action pages. It is a local prototype, not a public production deployment.
- Expanded the suite to 90 passing unit and HTTP integration tests while retaining 47/47 offline behavioral cases. See the [secure Web and professional review guide](docs/secure-web-and-professional-review.md) and [test report](evaluations/results/2026-08-12/security_web_review_report.md).
- Added a consent-gated long-term memory vault that defaults to in-memory storage and supports purpose-scoped consent, view/export, per-item deletion, scope revocation with deletion, full deletion, retention expiry, and content-free audit events.
- Added verified crisis-resource cards for China, the United States, and the United Kingdom, including official-source metadata, safe unknown-locale fallback, direct `tel:`/`sms:`/chat actions, and an accessible HTML action panel.
- Added clinical change governance requiring two independent clinical approvals and one safety approval before activation, with version history, evidence links, event logs, and safety-officer rollback.
- Added provider-blind clinician rating packets that remove model aliases, keep the mapping in an ignored file, and report exact agreement plus pairwise quadratic-weighted kappa per rubric dimension.
- Added eight synthetic-user profiles spanning communication style, cultural context, trust, prior help, AI attitude, practical constraints, correction behavior, and exit triggers, each with explicit anti-stereotype constraints.
- Added client-side experience state for explicit understood/misunderstood feedback, pressure, action rejection and its reason, correction count, exit intent, and exit reason; unknown feedback is never counted as success.
- Expanded the suite to 81 passing unit tests and 47/47 offline behavioral cases. See the [governance and evaluation guide](docs/governance-and-evaluation.md).
- Added user-controlled pacing signals so “I have not finished” interrupts intake, suppresses questions/advice, and remains active until the user explicitly resumes problem solving.
- Added direct tiny-step routing that supplies one concrete low-effort action instead of continuing assessment, even when distress intensity would otherwise trigger generic grounding.
- Added a real-world-bridge strategy for exclusive AI reliance, requiring transparent AI limits and one non-coercive route to a trusted person or qualified professional.
- Added goal-misalignment and epistemic-reinforcement review, plus a deterministic no-extra-call safety fallback when one bounded rewrite still leaves dependency or unsupported-certainty risk.
- Added a versioned Exploration–Insight–Action qualitative rubric with behavioral anchors, informed by ESC-Judge while retaining separate alliance, safety, autonomy, and naturalness dimensions.
- Ran OpenAI, DeepSeek, and Gemini through the same anonymous seven-turn regression set: all completed 7/7 turns and all respected the listen-then-act boundary; findings are documented in the [August 12 regression report](evaluations/results/2026-08-12/regression_report.md).
- Expanded the suite to 62 passing unit tests and 41/41 offline behavioral cases.
- Added a [2026 competitive review](docs/competitive-review-2026-08-12.md) covering PsychAgent, ESC-Judge, ESC-Eval, clinician-rated artificial-user evaluation, cognitive-restructuring agents, Therabot, and WHO governance guidance.

# Updates 8/10/2026

- Verified live connectivity with configured OpenAI, DeepSeek, and Gemini credentials without printing or committing secrets; updated the Gemini default to `gemini-3.5-flash` after the former model rejected new-user requests.
- Added a provider-blinded live comparison runner and ran all three providers over the same four synthetic, 17-turn scripts before revealing their identities.
- Added sealed whole-scenario retries, bounded transient-network retries, verified system-CA fallback, safe error messages, and automatic latency/availability metrics.
- Added a persisted pre-reveal qualitative rubric covering empathy, epistemic humility, strategy fit, alliance repair, autonomy boundaries, and naturalness.
- Added post-rewrite review so corrected replies are inspected again, while preserving the one-rewrite API-cost bound.
- Fixed `.env` parsing so the last duplicate assignment wins while real process environment values still take precedence; `.env` and the provider identity key remain ignored.
- Expanded the suite to 48 passing unit tests while retaining 29/29 offline behavioral cases.
- Published the [August 10 blinded comparison report](evaluations/results/2026-08-10/comparison_report.md), including limitations and concrete next-step recommendations.

# Updates 8/9/2026

- Added a research landscape comparing Woebot, Therabot, ESConv, PsyQA, SoulChat, CPsyCoun, recent safety findings, and Psycho Agent's current gaps.
- Added 29 offline behavioral cases and multi-turn scenario evaluation covering safety contrasts, state extraction, alliance repair, and response-review failures.
- Added explicit alliance state, goal alignment, rupture detection, and a repair strategy that interrupts normal advice routing.
- Improved crisis triage to distinguish self, other-person, historical, negated, fictional, and general-help contexts; crisis state now persists until concrete safety and real-world protection are confirmed.
- Expanded the unit suite to 41 passing tests and added boundary/dependency and question-overload review checks.
- Added OpenAI, DeepSeek, and Gemini model adapters with local `.env` configuration and no SDK lock-in.
- Added natural-response generation plus deterministic and optional model-based review for sycophancy, mechanical phrasing, repetition, premature diagnosis, advice overload, and unsafe claims.
- Added a bounded one-rewrite workflow, provider connectivity checks, and expanded the offline suite to 26 tests.
- Hardened provider errors so response bodies cannot echo credential fragments, and reject example keys before making a request.
- Initialized the project as a provider-neutral Python package with a runnable conversation-planning core.
- Added structured session state, staged intake, strategy routing, crisis-risk triage, repetition control, and unit tests.
- Documented the product boundaries: transparent AI support for everyday distress, not diagnosis or a replacement for professional care.

# Psycho Agent

Psycho Agent is an experimental, human-centered psychological support agent. Its goal is not to imitate a therapist's identity or simply sound agreeable. It tries to follow a disciplined support process: understand the person's current state, decide what kind of help is appropriate, respond naturally, track progress, and avoid repeating generic advice.

The current release plans each conversation turn, generates a provider-backed natural reply, reviews the draft, and performs at most one corrective rewrite. Two high-impact residual failures—AI-dependency encouragement and reinforcement of unsupported certainty—fall back to a deterministic safe response without another model call. An authenticated local Web prototype now provides encrypted-memory controls and embedded crisis actions; public production deployment remains a later milestone.

## Product principles

- **Be transparent:** the product identifies itself as AI and never pretends to be a human clinician.
- **Understand before advising:** early turns focus on the problem, impact, duration, desired kind of help, and safety.
- **Validate feelings, not every conclusion:** empathy must not become automatic agreement.
- **Adapt the conversational action:** listening, clarifying, gently challenging, grounding, planning, and reviewing are different interventions.
- **Track progress:** remember what was learned, what was tried, and what should not be repeated.
- **Escalate risk:** signs of imminent self-harm, suicide, or violence bypass the normal flow and receive crisis-oriented guidance.

## Current architecture

```text
User message
    |
    v
Safety triage --------> Fixed crisis response
    |
    v
Session-state update
    |
    v
Conversation phase -> Strategy router -> Turn plan -> Draft response
    |                                                    |
    +-------- Memory update <- Review <- Optional rewrite+
```

The system is intentionally provider-neutral. The orchestration layer decides *what the next response needs to accomplish*. OpenAI, DeepSeek, or Gemini can turn that plan into natural language. A separate reviewer checks the draft for sycophancy, repetition, premature diagnosis, and unsafe advice before it is shown.

## Run the demo

Requires Python 3.11 or newer.

```bash
python -m pip install -e .
python -m psycho_agent
```

The default command is planning-only and makes no API calls. For live responses, copy the safe template and add your own key:

```bash
cp .env.example .env
python -m psycho_agent --provider openai
python -m psycho_agent --provider deepseek
python -m psycho_agent --provider gemini
```

`chatgpt` is accepted as a command alias for the OpenAI provider. The conventional key name is `OPENAI_API_KEY`; `CHATGPT_API_KEY` is also accepted for convenience.

Semantic model review is enabled by default and normally adds one extra model call per reply. A failed review can add one bounded rewrite call. To use only the deterministic reviewer:

```bash
python -m psycho_agent --provider openai --no-model-review
```

After adding keys, run an opt-in live connectivity check. This makes one short, billable API request per named provider and never prints the keys:

```bash
python -m psycho_agent.smoke_test openai deepseek gemini
```

Run the same synthetic multi-turn scenarios through all configured providers. Provider identities are randomized into aliases, with the key stored in an ignored file:

```bash
python -m psycho_agent.live_compare --output-dir evaluations/results/YYYY-MM-DD
python -m psycho_agent.live_compare --output-dir evaluations/results/YYYY-MM-DD --retry-failures
```

The retry command reruns the complete scenario containing a failed turn so later responses retain valid conversational context. Do not open `provider_key.json` until qualitative scores have been written.

Run tests:

```bash
python -m unittest discover -s tests -v
```

Run the authenticated local Web prototype after generating a master key and setting both new
values in the ignored `.env` file:

```bash
python -m psycho_agent.secure_store generate-key
python -m psycho_agent.web_app
```

Open `http://127.0.0.1:8000` and sign in as `local-admin`. This development server is for local
evaluation only; it does not provide production TLS, managed secrets, backups, or high availability.

Run the research-informed offline behavior suite:

```bash
python -m psycho_agent.evaluation
```

The behavioral suite is stored in `evaluations/behavior_cases.jsonl`. It checks safety contrast sets, explicit state extraction, user-controlled pacing, goal alignment, reviewer failures, and multi-turn routing. The stage-aware qualitative rubric is stored in `evaluations/qualitative_rubric.json`. These artifacts are engineering invariants, not a clinical validation score.

## Repository layout

```text
src/psycho_agent/
  assurance.py    non-substitutable engineering, professional, clinical, and deployment gates
  client_metrics.py explicit user-side experience, rejection, and exit signals
  clinical_evaluation.py blind clinician packets and inter-rater agreement
  credentials.py manual credential evidence and conflict-of-interest gates
  crisis_resources.py verified locale resources and actionable crisis cards
  crisis_audit.py binary non-compensatory crisis control audit
  engine.py       conversation orchestrator
  generator.py    draft, review, and bounded rewrite workflow
  governance.py   clinical change approval, activation, and rollback
  intake.py       staged initial interview
  models.py       typed conversation state and turn plans
  providers.py    OpenAI, DeepSeek, and Gemini adapters
  privacy.py      consent-gated long-term memory vault
  rating_service.py verified human rating intake and finalization
  reliability_evaluation.py versioned metamorphic and multi-turn route checks
  reviewer.py     deterministic and semantic response review
  safety.py       conservative first-pass risk triage
  scope_guard.py  non-abandoning boundaries around unsupported clinical procedures
  simulated_users.py diverse synthetic evaluation profile loader
  state_update.py explicit emotion, preference, impact, and rupture signals
  strategy.py     phase-aware support strategy selection
  secure_store.py encrypted persistent memory implementation
  web_app.py      authenticated local memory and crisis interface
  evaluation.py   offline behavioral evaluation runner
  live_compare.py provider-blinded live multi-turn comparison
tests/            behavior-focused unit tests
evaluations/      auditable JSONL behavior and scenario cases
docs/             product and architecture decisions
```

## Safety scope

This repository is research-stage software. It must not be presented as medical care, emergency response, diagnosis, or a substitute for a licensed professional. The keyword-based safety detector in this milestone is only a first-pass guardrail and is not clinically validated. A production version needs expert review, localized crisis resources, privacy controls, evaluation with adversarial cases, and a reliable human-escalation path.

## Roadmap

1. Recruit and independently verify qualified reviewers to complete the blind packets and establish inter-rater reliability.
2. Commission jurisdiction-specific legal/privacy review, threat modeling, penetration testing, and clinical safety review.
3. Move local secrets and SQLite data to managed identity, key management, encrypted backups, rotation, and production TLS.
4. Add provider fallback and cost instrumentation without logging private content.
5. Expand localized resources and synthetic profiles through regional and clinical review, with scheduled resource re-verification.

## Research review

The [research landscape](docs/research-landscape.md) explains the evidence baseline. The [August 2026 competitive review](docs/competitive-review-2026-08-12.md) compares newer project architectures and records what Psycho Agent should adopt, defer, or reject.
