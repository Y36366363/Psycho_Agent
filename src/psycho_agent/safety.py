"""Conservative, explainable first-pass safety triage.

This module is deliberately small and testable. It is not a clinical assessment and
must eventually be combined with semantic classification and expert-reviewed policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .crisis_resources import get_crisis_resource_card
from .models import ActionLink, RiskLevel, RiskSubject, SafetyAssessment


_IMMINENT_PATTERNS = (
    r"(?:现在|马上|今晚|今天).{0,8}(?:自杀|去死|结束生命|杀了自己)",
    r"(?:已经|正在).{0,8}(?:准备|实施|割腕|服药|上吊)",
    r"I (?:am going to|will) kill myself (?:now|tonight|today)",
)

_HIGH_PATTERNS = (
    r"(?:想|打算|计划|准备).{0,8}(?:自杀|去死|结束生命|杀了自己)",
    r"(?:自杀|轻生).{0,8}(?:方法|计划|遗书)",
    r"(?:想|打算|计划).{0,8}(?:杀人|伤害别人|伤害他人)",
    r"(?:suicide plan|kill myself|end my life|hurt someone)",
)

_ELEVATED_PATTERNS = (
    r"(?:不想活|活着没意思|活不下去|消失就好了)",
    r"(?:伤害自己|自残|割自己)",
    r"(?:wish I were dead|don't want to live|hurt myself)",
)

_NEGATED_RISK_PATTERNS = (
    r"(?:没有|并没有|没|从没|从未|不再)(?:真的)?(?:想|打算|计划|准备)?(?:过)?"
    r".{0,4}(?:自杀|轻生|去死|结束生命|伤害自己|自残)",
    r"(?:do not|don't|never|no longer).{0,12}(?:kill myself|end my life|hurt myself)",
)

_HISTORICAL_PATTERNS = (
    r"(?:以前|过去|曾经|前几年|那时候).{0,14}(?:自杀|轻生|不想活|伤害自己|自残)",
    r"(?:used to|in the past|years? ago).{0,20}(?:suicid|kill myself|hurt myself)",
)

_OTHER_SUBJECT_PATTERNS = (
    r"(?:朋友|同学|家人|伴侣|对象|孩子|室友|同事|他|她).{0,18}"
    r"(?:自杀|轻生|不想活|伤害自己|自残|杀人|伤害别人)",
    r"(?:my |a )?(?:friend|partner|child|roommate|colleague|he|she|they).{0,24}"
    r"(?:suicid|kill (?:himself|herself|themself)|hurt (?:himself|herself|themself|someone))",
)

_FICTION_OR_GENERAL_PATTERNS = (
    r"(?:小说|电影|电视剧|剧本|故事|新闻|案例).{0,18}(?:角色|人物|有人|他|她)?.{0,12}"
    r"(?:自杀|轻生|不想活|自残)",
    r"如果有人.{0,18}(?:自杀|轻生|不想活|自残).{0,18}(?:怎么办|怎么帮助|如何帮助)",
    r"(?:novel|movie|story|character|news).{0,30}(?:suicid|kill themselves|self-harm)",
)


def _matches(text: str, patterns: Iterable[str]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, re.IGNORECASE)]


def _without_negated_risk(text: str) -> str:
    result = text
    for pattern in _NEGATED_RISK_PATTERNS:
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
    return result


def _risk_subject(text: str) -> RiskSubject:
    if _matches(text, _OTHER_SUBJECT_PATTERNS):
        return RiskSubject.OTHER
    return RiskSubject.SELF


def assess_safety(message: str) -> SafetyAssessment:
    """Detect explicit safety signals and return an auditable preliminary level."""
    normalized = " ".join(message.strip().split())
    if not normalized:
        return SafetyAssessment()

    if _matches(normalized, _FICTION_OR_GENERAL_PATTERNS):
        return SafetyAssessment(
            level=RiskLevel.LOW,
            subject=RiskSubject.OTHER,
            rationale="Risk language appears inside a fictional or general-help context.",
        )

    subject = _risk_subject(normalized)
    historical = _matches(normalized, _HISTORICAL_PATTERNS)
    if historical:
        return SafetyAssessment(
            level=RiskLevel.ELEVATED,
            subject=subject,
            matched_signals=historical,
            requires_direct_check=True,
            rationale="Language suggests a history of self-harm or suicidal thinking.",
        )

    assessment_text = _without_negated_risk(normalized)
    had_negated_risk = assessment_text != normalized
    if not assessment_text.strip():
        return SafetyAssessment(
            level=RiskLevel.LOW,
            subject=subject,
            rationale="Risk language is explicitly negated in the current statement.",
        )

    imminent = _matches(assessment_text, _IMMINENT_PATTERNS)
    if imminent:
        return SafetyAssessment(
            level=RiskLevel.IMMINENT,
            subject=subject,
            matched_signals=imminent,
            requires_direct_check=True,
            rationale="Language suggests possible immediate intent or action.",
        )

    high = _matches(assessment_text, _HIGH_PATTERNS)
    if high:
        return SafetyAssessment(
            level=RiskLevel.HIGH,
            subject=subject,
            matched_signals=high,
            requires_direct_check=True,
            rationale="Language suggests possible intent, planning, or harm to others.",
        )

    elevated = _matches(assessment_text, _ELEVATED_PATTERNS)
    if elevated:
        return SafetyAssessment(
            level=RiskLevel.ELEVATED,
            subject=subject,
            matched_signals=elevated,
            requires_direct_check=True,
            rationale="Language suggests hopelessness or self-harm and needs a direct check-in.",
        )

    if had_negated_risk:
        return SafetyAssessment(
            level=RiskLevel.LOW,
            subject=subject,
            rationale="Risk language is explicitly negated in the current statement.",
        )
    return SafetyAssessment()


def crisis_turn(
    assessment: SafetyAssessment, *, locale: str = "zh-CN"
) -> tuple[str, list[str], list[ActionLink]]:
    """Return a crisis message, follow-up questions, and direct escalation actions."""
    card = get_crisis_resource_card(locale)
    use_english = locale != "zh-CN"
    if assessment.subject is RiskSubject.OTHER:
        response = (
            "The person you described may be in immediate danger. Do not handle this "
            "alone or promise secrecy. Contact emergency services and involve a trusted "
            "adult or family member, while keeping yourself safe. I am an AI and cannot "
            "provide emergency rescue. "
            if use_english
            else (
                "你提到的这个人可能正面临需要立即处理的危险。请不要独自承担或承诺保密："
                "如果危险正在发生，立即联系当地急救或警方，并尽量让一位可信任的成年人或家属到场。"
                "如果你能安全地陪伴对方，可以保持联系并减少其接触危险物品的机会，但不要让自己置身危险。"
                "我是 AI，不能提供紧急救援。"
            )
        )
        response += card.immediate_message + card.support_message
        return (
            response,
            (
                [
                    "Does the person have a specific plan, access to means, or an action "
                    "already underway?",
                    "Do you know their location and can you contact real-world support?",
                ]
                if use_english
                else [
                    "对方现在是否有明确计划、手段或正在实施？",
                    "你是否知道对方的位置并能联系现实中的支援？",
                ]
            ),
            card.actions,
        )

    if assessment.level is RiskLevel.IMMINENT:
        response = (
            "I am taking what you said seriously. The priority now is immediate safety, "
            "not working this out alone. Contact emergency help and ask a trusted person "
            "to be physically present; move away from anything you could use to hurt "
            "yourself. I am an AI and cannot provide emergency rescue. "
            if use_english
            else (
                "我很重视你刚才说的情况。现在最重要的不是独自把它想明白，而是先确保你此刻的安全。"
                "请立即联系当地急救或警方，或者让一个你信任的人现在来到你身边；如果可以，先远离任何可能伤害自己的物品和地点。"
                "我是 AI，无法提供紧急救援，但我可以在你联系现实中的帮助时继续陪你梳理下一步。"
            )
        )
    else:
        response = (
            "Thank you for saying something this difficult. I need to check your safety "
            "before analyzing anything else. I am an AI and cannot replace emergency or "
            "professional help. "
            if use_english
            else (
                "谢谢你把这么难说的事情告诉我。我需要先认真确认你的安全，而不是马上分析其他问题。"
                "我是 AI，不能替代紧急服务或专业人员；如果危险正在逼近，请立即联系当地急救、警方或可信任的人。"
            )
        )
    response += card.immediate_message + card.support_message
    return (
        response,
        (
            [
                "Are you in immediate danger of hurting yourself or someone else?",
                "Who can you contact to be with you right now?",
            ]
            if use_english
            else [
                "你现在是否正处于立即伤害自己或他人的危险中？",
                "此刻有没有一个可以联系并陪着你的人？",
            ]
        ),
        card.actions,
    )


def safety_resolution_confirmed(message: str, subject: RiskSubject) -> bool:
    """Require an explicit safety statement plus a concrete protective condition."""
    text = " ".join(message.strip().split())
    if subject is RiskSubject.OTHER:
        safe = re.search(r"(?:对方|他|她).{0,8}(?:现在|已经)?.{0,4}(?:安全|脱离危险)", text)
    else:
        safe = re.search(
            r"(?:我)?(?:现在|目前|此刻).{0,5}(?:安全|不会伤害自己|没有立即危险)", text
        )
    protection = re.search(
        r"(?:有人陪|朋友在|家人在|陪着|联系了|已经报警|急救.{0,4}(?:到了|在路上)|"
        r"医生.{0,4}(?:到了|联系)|远离.{0,6}(?:药|刀|危险|手段)|交给.{0,6}(?:家人|朋友|警方))",
        text,
    )
    return bool(safe and protection)


def crisis_follow_up_turn(
    subject: RiskSubject, *, locale: str = "zh-CN"
) -> tuple[str, list[str]]:
    """Keep the safety conversation active until protection is explicitly established."""
    use_english = locale != "zh-CN"
    if subject is RiskSubject.OTHER:
        if use_english:
            return (
                "Before continuing, I need to confirm that the person has real-world help. "
                "Not mentioning suicide again does not show that the danger has passed.",
                [
                    "Are they currently safe, with family, emergency responders, or police "
                    "actually involved?"
                ],
            )
        return (
            "在继续分析其他事情前，我还需要确认对方是否已经获得现实中的帮助。"
            "仅仅暂时没再提到自杀，并不能说明危险已经解除。",
            ["对方现在安全吗，并且是否已有家人、急救人员或警方实际介入？"],
        )
    if use_english:
        return (
            "You have not repeated the intent to harm yourself, but that alone does not "
            "show the danger has passed. We need one concrete safety condition first.",
            [
                "Are you safe now, with someone present, real-world help contacted, or "
                "access to means reduced?"
            ],
        )
    return (
        "我听到你这一刻没有再次表达伤害自己的打算，但我还不能据此判断危险已经过去。"
        "我们先确认一个具体的安全条件，再继续谈其他问题。",
        ["你现在是否安全，并且已经有人陪着、联系了现实支援，或远离了可能伤害自己的手段？"],
    )
