"""Conservative, explainable first-pass safety triage.

This module is deliberately small and testable. It is not a clinical assessment and
must eventually be combined with semantic classification and expert-reviewed policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import RiskLevel, SafetyAssessment


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


def _matches(text: str, patterns: Iterable[str]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, re.IGNORECASE)]


def assess_safety(message: str) -> SafetyAssessment:
    """Detect explicit safety signals and return an auditable preliminary level."""
    normalized = " ".join(message.strip().split())
    if not normalized:
        return SafetyAssessment()

    imminent = _matches(normalized, _IMMINENT_PATTERNS)
    if imminent:
        return SafetyAssessment(
            level=RiskLevel.IMMINENT,
            matched_signals=imminent,
            requires_direct_check=True,
            rationale="Language suggests possible immediate intent or action.",
        )

    high = _matches(normalized, _HIGH_PATTERNS)
    if high:
        return SafetyAssessment(
            level=RiskLevel.HIGH,
            matched_signals=high,
            requires_direct_check=True,
            rationale="Language suggests possible intent, planning, or harm to others.",
        )

    elevated = _matches(normalized, _ELEVATED_PATTERNS)
    if elevated:
        return SafetyAssessment(
            level=RiskLevel.ELEVATED,
            matched_signals=elevated,
            requires_direct_check=True,
            rationale="Language suggests hopelessness or self-harm and needs a direct check-in.",
        )

    return SafetyAssessment()


def crisis_turn(assessment: SafetyAssessment) -> tuple[str, list[str]]:
    """Return a localized-neutral crisis message and follow-up questions."""
    if assessment.level is RiskLevel.IMMINENT:
        response = (
            "我很重视你刚才说的情况。现在最重要的不是独自把它想明白，而是先确保你此刻的安全。"
            "请立即联系当地急救或警方，或者让一个你信任的人现在来到你身边；如果可以，先远离任何可能伤害自己的物品和地点。"
            "我是 AI，无法提供紧急救援，但我可以在你联系现实中的帮助时继续陪你梳理下一步。"
        )
    else:
        response = (
            "谢谢你把这么难说的事情告诉我。我需要先认真确认你的安全，而不是马上分析其他问题。"
            "我是 AI，不能替代紧急服务或专业人员；如果危险正在逼近，请立即联系当地急救、警方或可信任的人。"
        )
    return response, ["你现在是否正处于立即伤害自己或他人的危险中？", "此刻有没有一个可以联系并陪着你的人？"]
