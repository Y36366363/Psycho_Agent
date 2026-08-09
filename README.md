# Updates 8/9/2026

- Added OpenAI, DeepSeek, and Gemini model adapters with local `.env` configuration and no SDK lock-in.
- Added natural-response generation plus deterministic and optional model-based review for sycophancy, mechanical phrasing, repetition, premature diagnosis, advice overload, and unsafe claims.
- Added a bounded one-rewrite workflow, provider connectivity checks, and expanded the offline suite to 26 tests.
- Hardened provider errors so response bodies cannot echo credential fragments, and reject example keys before making a request.
- Initialized the project as a provider-neutral Python package with a runnable conversation-planning core.
- Added structured session state, staged intake, strategy routing, crisis-risk triage, repetition control, and unit tests.
- Documented the product boundaries: transparent AI support for everyday distress, not diagnosis or a replacement for professional care.

# Psycho Agent

Psycho Agent is an experimental, human-centered psychological support agent. Its goal is not to imitate a therapist's identity or simply sound agreeable. It tries to follow a disciplined support process: understand the person's current state, decide what kind of help is appropriate, respond naturally, track progress, and avoid repeating generic advice.

The current release plans each conversation turn, generates a provider-backed natural reply, reviews the draft, and performs at most one corrective rewrite. A minimal user interface will come in a later milestone.

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

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Repository layout

```text
src/psycho_agent/
  engine.py       conversation orchestrator
  generator.py    draft, review, and bounded rewrite workflow
  intake.py       staged initial interview
  models.py       typed conversation state and turn plans
  providers.py    OpenAI, DeepSeek, and Gemini adapters
  reviewer.py     deterministic and semantic response review
  safety.py       conservative first-pass risk triage
  strategy.py     phase-aware support strategy selection
tests/            behavior-focused unit tests
docs/             product and architecture decisions
```

## Safety scope

This repository is research-stage software. It must not be presented as medical care, emergency response, diagnosis, or a substitute for a licensed professional. The keyword-based safety detector in this milestone is only a first-pass guardrail and is not clinically validated. A production version needs expert review, localized crisis resources, privacy controls, evaluation with adversarial cases, and a reliable human-escalation path.

## Roadmap

1. Add a minimal web conversation interface.
2. Build a reusable evaluation corpus for warmth, non-sycophancy, repetition, and safety.
3. Add consent-aware long-term memory and privacy controls.
4. Add provider fallback and cost/latency instrumentation without logging private content.
5. Conduct review with qualified mental-health professionals before any public-facing trial.
