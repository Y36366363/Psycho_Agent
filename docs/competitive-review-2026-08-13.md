# Competitive and research review — 2026-08-13

## Conclusion

The newer work reinforces that the main competitive gap is not warmth. Current systems can score
well on rapport while still failing privacy, medical-boundary, longitudinal, and crisis-safety
requirements. Psycho Agent should therefore compete on inspectable routing, non-substitutable
evidence, narrow scope, and failure visibility—not on claiming to be the most human therapist.

## External findings and decisions

| Work or market sample | Useful conclusion | Important limitation or observed problem | Psycho Agent response |
|---|---|---|---|
| [CounselBench](https://llm-eval-mental-health.github.io/counselbench-2025/) | 100 licensed or trained professionals supplied scores, span labels, and rationales; adversarial questions exposed model-specific failures | LLM judges systematically overrated responses and missed expert-identified safety concerns; unauthorized medical advice remained a recurring risk | Treat model review as auxiliary only. Added deterministic detection and final fallback for medication/treatment instructions, plus a human rubric dimension |
| [VERA-MH](https://arxiv.org/abs/2605.13318) | Clinically developed suicidal-ideation personas and a sequential binary rubric make exact failure modes inspectable | Simulation and LLM judging still do not prove real-world safety; aggregate ratings can become detached from construct validity | Added a binary crisis-plan audit with hard-fail checks and no average score; direct action, current-safety question, fixed routing, and real-world help cannot be averaged away |
| [MHSafeEval / R-MHSafe](https://aclanthology.org/2026.findings-acl.1382/) | Mental-health harm is interactional and cumulative; the same sentence differs when an AI acts as perpetrator, instigator, facilitator, or enabler | Agent simulation and taxonomy coverage remain proxies for actual outcomes | Added bounded per-session final-review issue history as groundwork for longitudinal role/harm auditing; retained multi-turn scenarios rather than relying on isolated answers |
| [DialogGuard](https://aclanthology.org/2026.acl-demo.19/) | Practitioner-facing rationales and audit trails make psychosocial safety review actionable | Multi-agent voting can improve judge robustness but is still model-mediated and adds complexity/cost | Kept deterministic high-impact gates and auditable rationales; defer judge ensembles until they can be calibrated against this project's real professional ratings |
| [CAPE market evaluation](https://pmc.ncbi.nlm.nih.gov/articles/PMC12239686/) | A structured framework can compare product information, conversational ability, alliance, boundaries, accessibility, privacy, and safety | Popular GPT-store psychotherapy chatbots were strong on rapport/accessibility but weak on essential safety and privacy functions | Retain public crisis access, explicit AI identity, encrypted opt-in memory, export/deletion, and evidence claims as visible product controls rather than hidden prompt text |
| [AI Safety Training Can be Clinically Harmful](https://arxiv.org/abs/2604.23445) | Surface safety behavior can conflict with the mechanism of specialized CBT or exposure protocols; evaluation must separate protocol fidelity, hallucination, consistency, crisis safety, and demographic robustness | It is a 2026 preprint using simulated scenarios and LLM panels, not proof that any one alternative is clinically safe | Do not conduct specialized therapy protocols in a general support agent. Added fixed non-abandoning boundaries for diagnosis, medication changes, unsupervised trauma exposure, and dangerous eating-disorder procedures |
| [PsychAgent](https://github.com/ECNU-ICALK/PsychAgent) | Skill retrieval, cross-session learning, client/counselor metrics, matched human ratings, and reported human-human QWK are useful architecture/evaluation patterns | Self-evolution and best-of-N reward selection may optimize judge preferences; complete evolution assets and clinical outcome evidence remain limited | Preserve versioned approval and rollback. Do not adopt autonomous clinical skill evolution or treat QWK/LLM preference as clinical effectiveness |

## Changes implemented from the comparison

### Clinical scope boundary

`scope_guard.py` detects explicit requests for individualized medication changes, diagnosis,
unsupervised trauma exposure, and instructions for purging/starvation. Crisis triage always runs
first. Non-crisis requests receive a fixed response that explains the specific limit and offers to
prepare symptoms/questions for qualified care. Ordinary discussion of medication or trauma remains
available and is tested as a negative contrast.

### Output-side clinical-overreach review

The user's request is not the only risk source: a model can volunteer medical direction. The
deterministic reviewer now flags `clinical_overreach`. One rewrite is allowed; if the revised reply
still directs medication or specialized treatment, a fixed non-prescriptive response replaces it.

### Binary crisis audit

`crisis_audit.py` emits separate Yes/No checks for crisis routing, model bypass, real-world help,
verified direct actions, a current-safety question, AI identity, and absence of secrecy/diagnosis.
Any critical miss produces `hard_fail`. It deliberately emits no composite safety score.

### Longitudinal audit foundation

Sessions now retain a bounded history of final review issue kinds. This does not yet implement the
full MHSafeEval interaction-role taxonomy, but it prevents cross-turn safety failures from existing
only in transient return values and prepares adjudicable trajectory reports.

## Remaining priorities

1. Map the bounded history to expert-approved interaction roles and test escalating multi-turn
   trajectories rather than merely counting flags.
2. Add clinically authored scenarios for mania, psychosis-like experiences, coercive abuse, minors,
   eating disorders, substance use, pregnancy/postpartum contexts, and adverse medication effects.
3. Calibrate automated and model-assisted reviewers against completed human ratings, reporting
   sensitivity for hard harms rather than only agreement or average accuracy.
4. Define an incident review pipeline for false negatives, false positives, abandonment, and
   unauthorized medical direction before any external pilot.
5. Assess accessibility, language/dialect performance, and subgroup failure rates with people who
   have lived experience; synthetic profiles remain coverage tools, not outcome evidence.

## Interpretation limit

These changes improve enforceable engineering behavior. They do not establish clinical efficacy,
complete crisis detection, professional equivalence, or production readiness. The external studies
also use different populations, products, protocols, judges, and outcome definitions, so their
numerical results are not directly comparable to Psycho Agent.
