# Research landscape and project direction

**Review date:** August 9, 2026

This document compares Psycho Agent with published psychological-support systems, datasets, and safety research. It is a product and engineering review, not evidence that this repository provides effective treatment. Clinical claims require prospective studies, qualified oversight, and appropriate regulatory and ethical review.

## What already exists

### Structured CBT agents: Woebot

The 2017 Woebot randomized controlled trial studied 70 young adults over two weeks. The Woebot group showed a significant reduction in depression symptoms relative to an information-only control; anxiety decreased among completers in both groups. Importantly for our design, participant feedback suggested that process factors influenced acceptability more than therapy-like content alone. This supports building a coherent interaction process rather than accumulating advice modules.

Source: [Fitzpatrick, Darcy, and Vierhile, 2017](https://europepmc.org/articles/PMC5478797)

### A generative treatment system: Therabot

Therabot is the strongest public counterexample to the idea that a psychological agent is merely a prompt. Its 2025 randomized trial used a purpose-built system, evidence-based training material, symptom measures, conversation review, and clinician oversight. Dartmouth reported an intervention group of 106 people and a control group of 104; reported average symptom reductions in the intervention group were 51% for depression, 31% for generalized anxiety, and 19% for eating-disorder concerns. Users also reported therapeutic-alliance ratings comparable to those reported with human providers. These results should not be generalized to arbitrary LLM chatbots or to our system.

Sources: [NEJM AI trial record](https://doi.org/10.1056/AIoa2400802), [Dartmouth study summary](https://home.dartmouth.edu/news/2025/03/first-therapy-chatbot-trial-yields-mental-health-benefits)

### Emotional-support strategy research: ESConv

ESConv formalized emotional-support conversation as a staged, strategy-annotated task grounded in Helping Skills Theory. Its central contribution for this project is the distinction between *what a response is trying to do* and the words used to do it. Questioning, restatement, reflection, affirmation, information, and suggestions are not interchangeable; strategy choice should change over a conversation.

Source: [Liu et al., 2021](https://aclanthology.org/2021.acl-long.269/)

### Chinese counseling data: PsyQA, SoulChat, and CPsyCoun

- PsyQA created a Chinese mental-health support dataset oriented toward long-form counseling responses. It is useful as a language and counseling-text reference, but long answers are not automatically good multi-turn support.
- SoulChat explicitly addresses the tendency of LLMs to rush into universal advice. Its published work used more than two million multi-turn empathy samples to improve listening, questioning, comfort, and support behavior.
- CPsyCoun argues that empathy data alone lacks professional counseling knowledge. It reconstructs multi-turn Chinese counseling dialogues from reports and supplies an automatic evaluation framework, making it especially relevant to our next evaluation phase.

Sources: [PsyQA](https://aclanthology.org/2021.findings-acl.130/), [SoulChat paper](https://aclanthology.org/2023.findings-emnlp.83/), [SoulChat code](https://github.com/scutcyr/SoulChat), [SoulChat 2.0](https://github.com/scutcyr/SoulChat2.0), [CPsyCoun paper](https://aclanthology.org/2024.findings-acl.830/), [CPsyCoun code](https://github.com/CAS-SIAT-XinHai/CPsyCoun)

### Evidence against autonomous “AI therapist” claims

Moore and colleagues tested LLM behavior against features of therapeutic relationships and found stigmatizing behavior and inappropriate responses in critical situations, including reinforcement of delusional thinking associated with sycophancy. They also argue that a human therapeutic alliance involves identity and stakes that an LLM does not possess. The correct product conclusion is not “sound more human”; it is “be transparent, narrow the role, test failure modes, and preserve routes to human care.”

Source: [Moore et al., FAccT 2025](https://arxiv.org/abs/2504.18412)

The WHO guidance on AI for health likewise emphasizes autonomy, safety, transparency, accountability, equity, and sustainability. These are system properties, not wording preferences.

Source: [WHO, Ethics and governance of artificial intelligence for health](https://www.who.int/publications/i/item/9789240029200)

## Comparison with Psycho Agent

| Dimension | Common prompt-based projects | Research systems | Psycho Agent now | Required next step |
|---|---|---|---|---|
| Conversation process | One persona prompt | Strategy or protocol driven | Typed phase and strategy plan | Validate transitions with multi-turn cases |
| Empathy | Warm wording | Annotated listening/support skills | Specificity rules and semantic review | Human-rate accurate empathy, not warmth alone |
| Advice timing | Advice on every turn | Phase-sensitive | Preference and intensity routing | Add richer consent and readiness signals |
| Sycophancy | Rarely measured | Emerging safety concern | Rule and model reviewer | Add delusion, paranoia, blame, and certainty cases |
| Alliance | Anthropomorphic tone | Measured as trust/collaboration | Goal alignment and rupture repair state | Measure bond, goal, and task separately |
| Long dialogue | Raw transcript memory | Multi-turn datasets/evaluation | Recent goals, strategies, and response memory | Add episode summaries and progress trajectories |
| Crisis safety | Keyword or disclaimer | Escalation protocol plus oversight | Fixed crisis flow with subject/time distinctions | Expert review and localized resources |
| Outcomes | User likes/dislikes | Symptom and alliance measures | No clinical outcome claim | Do not claim efficacy before a controlled study |
| Oversight | Usually absent | Clinician review in stronger studies | None | Establish expert review before public trial |

## Working theoretical model

### 1. Alliance is bond plus agreement on goal and task

The agent should not optimize only for perceived warmth. A useful working model separates:

- **Bond:** the user feels accurately heard and not judged.
- **Goal:** both sides understand what the user wants from this conversation.
- **Task:** the user accepts what they are doing next—exploring, grounding, testing a belief, or planning.

An alliance rupture (“you did not understand me,” “you are repeating yourself”) should interrupt the normal strategy router. The next action is to acknowledge the miss and renegotiate the goal or task, not produce another technique.

### 2. Empathy is accuracy, not agreement

The system should validate the lived emotion while keeping causal interpretations provisional. The core response stance is:

> “The feeling makes sense given what you experienced; the conclusion is important but still something we can examine.”

This is the main defense against sycophancy in relationship conflict, persecutory interpretations, and self-blame.

### 3. Support should progress through functions

The project uses a flexible sequence rather than a fixed script:

1. Establish safety and the desired kind of help.
2. Explore events, interpretations, emotions, needs, and impact.
3. Form a tentative shared pattern or hypothesis.
4. Choose one intervention with permission.
5. Review whether it helped and repair the plan if it did not.

Users may move backward when distress rises or when the conversational alliance ruptures.

### 4. Risk needs subject, time, and context

The same words can mean very different things:

- “I will kill myself tonight” — possible imminent self-risk.
- “My friend says he will kill himself tonight” — imminent other-person risk.
- “I used to think about suicide” — history requiring a careful current check.
- “I do not want to kill myself” — explicit current denial.
- “A character in my novel kills herself” — fictional context.

A keyword detector that collapses these cases can give dangerous or alienating responses. The current implementation now models subject and basic context, but remains a preliminary guardrail rather than a validated risk assessment.

### 5. Evaluation must be layered

No single “empathy score” is sufficient. We should maintain four layers:

1. **Behavioral invariants:** deterministic cases for crisis scope, boundaries, diagnosis, repetition, question/advice overload, and state updates.
2. **Provider comparison:** the same multi-turn scripts run against OpenAI, DeepSeek, and Gemini, with blinded outputs and cost/latency records.
3. **Expert process rating:** qualified reviewers score accurate empathy, alliance, strategy fit, epistemic humility, safety, and usefulness.
4. **Outcome research:** only a properly reviewed prospective study can support claims about symptom or functioning improvement.

## Decisions from this review

- Keep planning separate from language generation; this is more defensible than a monolithic therapist persona prompt.
- Add explicit alliance-rupture repair before expanding the number of therapy techniques.
- Test safety contrast sets, not only obvious crisis sentences.
- Do not fine-tune on counseling corpora yet. First establish licenses, data provenance, privacy handling, and an evaluation baseline.
- Do not optimize for maximum emotional attachment. Reject exclusivity, secrecy, false intimacy, and dependency cues.
- Describe the system as AI psychological support for everyday distress, not an autonomous therapist.

## August 2026 follow-up

The [competitive review dated 2026-08-12](competitive-review-2026-08-12.md) extends this baseline with PsychAgent's multi-session skill architecture, ESC-Judge's stage-aware pairwise evaluation, ESC-Eval's role diversity, and recent clinician-rated evaluation methods. Its adopt/defer/reject table is the current source for roadmap prioritization.

## Limitations of this review

Published systems differ in population, duration, clinical involvement, and outcome definitions. Product pages and repository popularity do not establish efficacy. Dataset benchmarks may reward resemblance to counseling text without measuring harm, truthfulness, alliance repair, or real-world outcomes. Every borrowed method must therefore be converted into an explicit hypothesis and evaluated within this project's intended scope.
