# Governance, privacy, crisis escalation, and evaluation

This milestone supplies testable foundations for six high-priority controls. It does not turn the repository into a production health service. Authentication, encryption, professional credential verification, operational incident response, legal review, and a deployed user interface remain required before real-user use.

## Consent-aware memory

`ConsentAwareMemoryVault` is non-persistent by default. An application must obtain consent for each named scope before writing:

```python
from psycho_agent.privacy import ConsentAwareMemoryVault, MemoryScope

vault = ConsentAwareMemoryVault(retention_days=30)
vault.grant_consent(
    "session-123",
    {MemoryScope.PREFERENCES, MemoryScope.GOALS},
    policy_version="privacy-1",
)
item = vault.remember("session-123", MemoryScope.GOALS, "希望改善睡眠")
vault.view("session-123")
vault.export("session-123")
vault.delete_item("session-123", item.item_id)
vault.revoke_scope("session-123", MemoryScope.GOALS)
vault.delete_all("session-123")
```

The vault deliberately excludes a raw-transcript scope. Applications should store the smallest user-approved fact needed for continuity. Revocation deletes linked items by default. Audit events contain action, scope, item identifier, and time—not the memory text.

Current limitation: the vault is process-local and does not authenticate the caller. Production persistence needs encryption at rest and in transit, per-user authorization, backup deletion, retention jobs, breach response, and jurisdiction-specific legal review. China's Personal Information Protection Law includes rights around consent withdrawal and deletion; this implementation is an engineering primitive, not a compliance certification. [Official law text](https://www.gov.cn/xinwen/2021-08/20/content_5632486.htm)

## Localized crisis actions

`evaluations/crisis_resources.json` currently contains three reviewed locales:

- China: 120, 110, and the national 12356 psychological-assistance hotline. The National Health Commission required nationwide 12356 connection by May 2025 and emphasized linkage with emergency services. [Official NHC notice](https://www.nhc.gov.cn/yzygj/c100068/202412/49a1a65386cd4be582d4702fd0926ee8.shtml)
- United States: 911 and call/text/chat access to 988. [Official 988 Lifeline](https://988lifeline.org/)
- United Kingdom: 999 for immediate danger, NHS 111, and Samaritans 116 123. [NHS guidance](https://www.nhs.uk/mental-health/feelings-symptoms-behaviours/behaviours/help-for-suicidal-thoughts/)

The conversation plan includes `ActionLink` objects. A future interface can render them directly, or use the provided accessible HTML fragment:

```python
from psycho_agent.crisis_resources import get_crisis_resource_card, render_crisis_card_html

card = get_crisis_resource_card("zh-CN")
html = render_crisis_card_html(card)
```

Unknown locales contain no guessed number. Resource expansion requires a primary official source, verification date, native-language review, accessibility review, and a re-verification schedule.

## Clinical change control

`ClinicalChangeRegistry` models submission, independent review, activation, supersession, rejection, and emergency rollback. Activation requires:

1. evaluation evidence;
2. two different reviewers with a clinical role;
3. one different reviewer with a safety role;
4. a unique component version and a named rollback target when applicable.

The machine can enforce distinct identities and role counts, but it cannot verify licenses or conflicts of interest. Those checks belong to organizational identity management. The starter artifact is `governance/clinical_change_template.json` and is intentionally marked unapproved.

## Multiple blinded professional raters

`create_blind_rating_packet` reads already blinded provider outputs, removes the remaining `Model-A/B/C` alias, shuffles sessions, and writes:

- `rating_packet.json`: dialogue, rubric, and empty score fields;
- `rating_key.json`: packet-to-alias mapping, ignored by Git.

Raters work independently on the 1/3/5 behavioral anchors. `agreement_report` calculates exact agreement and quadratic-weighted kappa for every rater pair and every dimension. Missing shared items are not fabricated. Safety, empathy, action fit, and other dimensions remain separate.

Recommended workflow:

1. Give each professional a copy of the same packet with a unique rater identifier.
2. Freeze all ratings before opening the mapping.
3. Calculate agreement and inspect dimensions below a predeclared threshold.
4. Adjudicate disagreements while preserving original scores.
5. Only then compare providers or approve a behavioral change.

## Diverse artificial users

`evaluations/simulated_user_profiles.json` contains eight evaluation profiles varying:

- direct versus indirect communication;
- cultural and access context;
- low, mixed, or high trust;
- prior support experience;
- skepticism, neutrality, privacy concern, or enthusiasm toward AI;
- practical constraints, correction behavior, and disengagement triggers.

Each profile includes `avoid_assumptions`. The simulator is instructed to react to actual assistant behavior, reject unsuitable actions with a reason, and not become satisfied simply because the response sounds warm. Profiles are synthetic coverage tools, not diagnoses or claims about demographic groups.

## Client-side metrics

`ClientFeedbackState` records only explicit signals:

- `felt_understood`: `true`, `false`, or unknown;
- `pressure_reported`;
- `action_rejected` and categorized reasons such as infeasible, already tried, unwanted advice, low trust, or privacy concern;
- `exit_intent` and exit reasons;
- `correction_count`.

These signals complement counselor-side rubric scores. They do not infer outcome improvement, symptom change, or satisfaction from conversation length. Production evaluation should add direct user-reported measures, optional reason prompts at exit, subgroup analysis, and clinician review of adverse experiences.
