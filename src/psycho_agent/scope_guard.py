"""Bound unsupported clinical procedures without abandoning ordinary support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ClinicalScope(StrEnum):
    MEDICATION_CHANGE = "medication_change"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    TRAUMA_EXPOSURE = "trauma_exposure"
    EATING_DISORDER_PROCEDURE = "eating_disorder_procedure"


@dataclass(frozen=True, slots=True)
class ScopeBoundary:
    scope: ClinicalScope
    rationale: str


_PATTERNS = {
    ClinicalScope.MEDICATION_CHANGE: (
        r"(?:要不要|能不能|可以|该不该|帮我决定).{0,8}"
        r"(?:停药|停掉|减药|减量|加药|加量|换药)",
        r"(?:should|can) I.{0,12}(?:stop|increase|decrease|change).{0,8}"
        r"(?:my )?(?:medication|dose|antidepressant)",
    ),
    ClinicalScope.DIAGNOSIS_REQUEST: (
        r"(?:你|帮我|给我).{0,8}(?:诊断|确诊|判断).{0,10}"
        r"(?:抑郁症|焦虑症|双相|人格障碍|精神病|创伤后应激|什么病)",
        r"(?:diagnose me|tell me if I have).{0,20}(?:disorder|depression|anxiety|bipolar|ptsd)",
    ),
    ClinicalScope.TRAUMA_EXPOSURE: (
        r"(?:带我|指导我|现在).{0,8}(?:做|进行).{0,8}(?:暴露疗法|暴露治疗|创伤暴露|重现创伤)",
        r"(?:guide|walk) me through.{0,20}(?:exposure therapy|trauma exposure|reliving my trauma)",
    ),
    ClinicalScope.EATING_DISORDER_PROCEDURE: (
        r"(?:教我|告诉我|怎么).{0,8}(?:催吐|断食|绝食|清除).{0,8}"
        r"(?:更有效|不被发现|最快|减肥|体重)",
        r"(?:how (?:can|do) I|teach me to).{0,16}(?:purge|starve|hide my purging)",
    ),
}


def assess_clinical_scope(message: str) -> ScopeBoundary | None:
    text = " ".join(message.strip().split())
    for scope, patterns in _PATTERNS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return ScopeBoundary(
                scope,
                "The request requires individualized clinical assessment or supervised treatment.",
            )
    return None


def clinical_boundary_response(boundary: ScopeBoundary, *, locale: str = "zh-CN") -> str:
    if locale != "zh-CN":
        lead = {
            ClinicalScope.MEDICATION_CHANGE: "I cannot decide medication or dose changes.",
            ClinicalScope.DIAGNOSIS_REQUEST: "I cannot diagnose you from this conversation.",
            ClinicalScope.TRAUMA_EXPOSURE: (
                "I should not lead an unsupervised trauma-exposure exercise."
            ),
            ClinicalScope.EATING_DISORDER_PROCEDURE: (
                "I cannot give instructions for purging or starvation."
            ),
        }[boundary.scope]
        return (
            f"{lead} That needs an appropriately qualified professional who can assess your "
            "history, current safety, and follow-up. I will not leave you with only a refusal: "
            "I can help you write down the symptoms, questions, and recent changes to take to "
            "that person, or discuss how this is affecting you without directing treatment."
        )
    lead = {
        ClinicalScope.MEDICATION_CHANGE: "我不能替你决定停药、换药或调整剂量。",
        ClinicalScope.DIAGNOSIS_REQUEST: "我不能仅凭这段对话给你诊断或确诊。",
        ClinicalScope.TRAUMA_EXPOSURE: "我不适合在没有专业评估和跟进的情况下带你做创伤暴露。",
        ClinicalScope.EATING_DISORDER_PROCEDURE: "我不能提供催吐、绝食或隐藏这些行为的方法。",
    }[boundary.scope]
    return (
        f"{lead}这需要有相应资质的专业人员结合病史、当前安全和后续观察来处理。"
        "我不会只留下一句拒绝：我可以帮你整理最近的症状、变化和想问专业人员的"
        "问题，"
        "也可以继续讨论这件事对你的影响，但不替你制定诊疗操作。"
    )
