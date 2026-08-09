# Updates 8/9/2026

- Initialized the project as a provider-neutral Python package with a runnable conversation-planning core.
- Added structured session state, staged intake, strategy routing, crisis-risk triage, repetition control, and unit tests.
- Documented the product boundaries: transparent AI support for everyday distress, not diagnosis or a replacement for professional care.

# Psycho Agent

Psycho Agent is an experimental, human-centered psychological support agent. Its goal is not to imitate a therapist's identity or simply sound agreeable. It tries to follow a disciplined support process: understand the person's current state, decide what kind of help is appropriate, respond naturally, track progress, and avoid repeating generic advice.

The current release is the first foundation milestone. It produces a structured plan for each conversation turn; connection to a language model and a user interface will come in later milestones.

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
Safety triage --------> Crisis response plan
    |
    v
Session-state update
    |
    v
Conversation phase -> Strategy router -> Turn plan
    |                                      |
    +-------------- Memory update <--------+
```

The system is intentionally provider-neutral. The orchestration layer decides *what the next response needs to accomplish*. A later model adapter will turn that plan into natural language, and a separate reviewer will check the draft for sycophancy, repetition, premature diagnosis, and unsafe advice.

## Run the demo

Requires Python 3.11 or newer.

```bash
python -m pip install -e .
python -m psycho_agent
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Repository layout

```text
src/psycho_agent/
  engine.py       conversation orchestrator
  intake.py       staged initial interview
  models.py       typed conversation state and turn plans
  safety.py       conservative first-pass risk triage
  strategy.py     phase-aware support strategy selection
tests/            behavior-focused unit tests
docs/             product and architecture decisions
```

## Safety scope

This repository is research-stage software. It must not be presented as medical care, emergency response, diagnosis, or a substitute for a licensed professional. The keyword-based safety detector in this milestone is only a first-pass guardrail and is not clinically validated. A production version needs expert review, localized crisis resources, privacy controls, evaluation with adversarial cases, and a reliable human-escalation path.

## Roadmap

1. Add an LLM adapter and draft-response reviewer.
2. Add a minimal web conversation interface.
3. Build evaluation cases for warmth, non-sycophancy, repetition, and safety.
4. Add consent-aware long-term memory and privacy controls.
5. Conduct review with qualified mental-health professionals before any public-facing trial.
