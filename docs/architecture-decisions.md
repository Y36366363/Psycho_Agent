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
