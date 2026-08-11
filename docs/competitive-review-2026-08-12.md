# Competitive and research review — 2026-08-12

## Executive conclusion

Psycho Agent's strongest differentiation is not a new “therapist persona.” It is an inspectable control layer between the user and interchangeable language models: explicit pacing, strategy selection, alliance state, safety routing, and post-generation review. The most useful external work suggests strengthening that layer with stage-aware evaluation, varied artificial users, consent-aware longitudinal memory, explicit skill provenance, and qualified human review.

The project should not copy autonomous self-evolution, opaque reward optimization, or claims that a high LLM-judge score establishes therapeutic benefit. In a high-impact domain, learned changes need versioning, expert approval, rollback, and evidence tied to a defined use case.

## Project-by-project comparison

| Work | Bright spot worth absorbing | Limitation or risk | Psycho Agent decision |
|---|---|---|---|
| [PsychAgent](https://github.com/ECNU-ICALK/PsychAgent) | Cross-session planning, explicit counseling-skill retrieval, client-side and counselor-side metrics, and matched human ratings | Public release omits the complete skill-evolution pipeline and full benchmark assets; best-of-N reward selection can amplify judge bias; research repository lacks a license file | Adopt consent-aware session summaries, versioned skills, and client-side progress metrics. Defer self-evolution and reward optimization until clinical change control exists |
| [ESC-Judge](https://aclanthology.org/2025.emnlp-main.811/) | Theory-grounded head-to-head comparison across Exploration, Insight, and Action; paired sessions reduce some scenario variance | Synthetic users and an LLM judge can share model biases; reported judge–expert agreement does not make every individual judgment reliable | Adopt stage-aware behavioral anchors and paired provider comparisons; require blinded human review and agreement estimates |
| [ESC-Eval](https://aclanthology.org/2024.emnlp-main.883/) | 2,801 organized role cards, an intentionally confused help-seeker simulator, 14-model comparison, and human annotations | Simulated-user realism and dataset coverage limit generalization; benchmark success remains below human support quality | Expand scenarios across severity, communication style, trust, prior help, culture, and attitudes toward AI; keep roles synthetic until safety review |
| [Artificial users + psychotherapist assessment](https://arxiv.org/abs/2503.21540) | Patient-vignette variation protects vulnerable users during early testing; ten psychotherapists rated 48 dialogues and found action-plan appropriateness gaps | Artificial users were only moderately authentic; expert review is expensive and sampled | Add an expert-rating export workflow and assess whether each proposed activity is feasible, suitable, and collaboratively chosen |
| [LLM cognitive-restructuring chatbot evaluation](https://arxiv.org/abs/2501.15599) | Mental-health professionals identified power imbalance, advice-giving, missed cues, and excessive positivity as rapport risks | Small user study and one intervention style; prompt adherence alone does not establish benefit | Retain anti-sycophancy review, add user-goal-miss detection, and explicitly test whether advice was requested |
| [Therabot trial summary](https://home.dartmouth.edu/news/2025/03/first-therapy-chatbot-trial-yields-mental-health-benefits) | Controlled clinical evaluation, evidence-based training material, open-ended conversations, and direct high-risk escalation affordances | A controlled research system with diagnosed participants is not evidence that a general LLM wrapper is safe; symptom outcomes do not transfer to this implementation | Treat clinical outcomes as a future external-validation requirement, not a current product claim; design visible escalation affordances before public trials |
| [WHO AI-for-health guidance](https://www.who.int/news/item/28-06-2021-who-issues-first-global-report-on-ai-in-health-and-six-guiding-principles-for-its-design-and-use) | Autonomy, well-being, transparency, accountability, equity, and responsiveness are system properties rather than tone preferences | Principles require operational controls and governance; a disclaimer alone does not satisfy them | Translate principles into consent, data controls, audit logs, incident review, model/version traceability, accessibility, and redress mechanisms |

## What was absorbed today

### 1. Stage-aware evaluation

`evaluations/qualitative_rubric.json` now separates exploration pacing and empathic accuracy, insight humility and formulation, action fit and feasibility, plus cross-cutting alliance repair, boundaries, and naturalness. Every dimension has observable 1/3/5 anchors. This makes disagreement inspectable and prepares the project for inter-rater reliability rather than decorative decimal scores.

### 2. User-controlled pacing

Recent clinician evaluation warns that advice-giving and missed cues can erode rapport. The orchestration state now treats “I have not finished” as a durable boundary that interrupts intake and suppresses questions. The user—not the intake checklist—decides when conversation moves from exploration to action.

### 3. Action appropriateness

The artificial-user/psychotherapist study found deficits in activity-plan appropriateness. A direct request for a smallest next step now requires one actual, low-effort action tied to known details; another assessment question is a review failure.

### 4. Dependency and epistemic safety

Exclusive AI reliance now routes to a dedicated real-world bridge. Responses must state relevant AI limits without rejecting the user and offer one non-coercive connection to a trusted person or professional. Ambiguous evidence cannot be described as proving a feared interpretation. If one model rewrite still fails either high-impact requirement, a deterministic fallback closes the gap without an additional API call.

## Current gaps and prioritized improvements

### P0 — before any external pilot

1. **Privacy and consent model:** define what is stored, for how long, for what purpose, and how a user inspects or deletes it. Longitudinal memory should be opt-in and field-scoped.
2. **Localized crisis resources and escalation UI:** fixed text is insufficient; location-aware resources, direct-call affordances, accessibility review, and operational incident handling are needed.
3. **Clinical change control:** every strategy, deterministic fallback, rubric, and model change needs an owner, version, rationale, approval status, evaluation evidence, and rollback path.
4. **Human red-team review:** recruit qualified mental-health professionals to rate failures involving suicidality, mania, psychosis-like experiences, abuse, eating disorders, minors, and medication questions.

### P1 — evaluation maturity

1. Expand synthetic profiles across distress severity, personality/communication style, cultural context, prior treatment, trust, and attitudes toward AI.
2. Add user-side trajectory metrics: whether the user feels understood, corrects the agent, accepts/rejects an action, experiences pressure, or disengages.
3. Add blinded pairwise comparison and at least two independent raters; report agreement and adjudicate disagreements.
4. Separate intervention fidelity, conversational quality, safety, availability, cost, and latency. No aggregate score should hide a safety failure.
5. Test multi-session continuity for stale hypotheses, unwanted memory, changed goals, and the right to be forgotten before enabling persistent memory.

### P2 — product capability

1. Build a versioned skill catalog with indications, contraindications, prerequisites, evidence source, and examples rather than unconstrained retrieval over “therapy techniques.”
2. Add a minimal interface that makes AI identity, memory controls, feedback, crisis escalation, and conversation-goal choice visible.
3. Explore candidate generation only for low-risk language quality. Never let an unvalidated reward model autonomously select crisis or diagnostic behavior.

## What should not be copied

- **Human-therapist impersonation:** natural language should not obscure that the system is AI.
- **Automatic self-evolution in production:** user engagement and LLM-judge reward are unsafe substitutes for expert-approved learning objectives.
- **Attachment optimization:** longer conversations, exclusivity, and anthropomorphic bonding are not success metrics.
- **Diagnosis from conversational fluency:** a plausible formulation is not a clinical assessment.
- **Single-number leaderboards:** they obscure stage, subgroup, and safety trade-offs.
- **Synthetic-only validation:** artificial users are useful for coverage, not proof of benefit or absence of harm.
