"""Conservative extraction of explicit user state from conversation turns."""

from __future__ import annotations

import re

from .models import SessionState, SupportPreference


_EMOTIONS = (
    "焦虑",
    "害怕",
    "恐惧",
    "难过",
    "伤心",
    "愤怒",
    "生气",
    "委屈",
    "羞耻",
    "内疚",
    "孤独",
    "麻木",
    "绝望",
    "烦躁",
    "疲惫",
    "压力",
)

_IMPACT_AREAS = {
    "sleep": ("睡眠", "睡不着", "失眠", "半夜醒", "噩梦"),
    "work": ("工作", "上班", "绩效", "同事", "领导"),
    "study": ("学习", "考试", "作业", "学校", "成绩"),
    "relationships": ("关系", "伴侣", "家人", "朋友", "同事", "吵架"),
    "appetite": ("食欲", "吃不下", "暴食", "饮食"),
}

_RUPTURE_PATTERNS = (
    r"你(?:根本|还是)?没(?:有)?(?:听懂|理解|明白)",
    r"你(?:又|一直|总是)在重复",
    r"别再(?:说|问|建议)",
    r"这(?:回答|说法).{0,6}(?:没用|很机械|像模板)",
)


def update_session_state(session: SessionState, message: str) -> None:
    """Extract only explicit, auditable signals; never infer a diagnosis."""
    text = " ".join(message.strip().split())
    if not text:
        return

    intensity_matches = re.findall(r"(?<!\d)(10|[0-9])\s*(?:分|/\s*10)(?!\d)", text)
    if intensity_matches:
        session.user.emotion_intensity = int(intensity_matches[-1])

    for emotion in _EMOTIONS:
        if emotion in text and emotion not in session.user.emotion_words:
            session.user.emotion_words.append(emotion)

    for area, markers in _IMPACT_AREAS.items():
        if any(marker in text for marker in markers) and area not in session.user.functional_impact:
            session.user.functional_impact.append(area)

    if re.search(r"(?:先|只想).{0,5}(?:听我说|倾诉)|不(?:想|需要).{0,4}建议", text):
        session.user.support_preference = SupportPreference.LISTEN
    elif re.search(r"(?:帮我|一起).{0,5}(?:理清|看清|分析)|为什么会这样", text):
        session.user.support_preference = SupportPreference.UNDERSTAND
    elif re.search(r"(?:想|需要|帮我).{0,5}(?:办法|方案|建议|下一步)|我该怎么做", text):
        session.user.support_preference = SupportPreference.PLAN

    if session.user.support_preference is not SupportPreference.UNKNOWN:
        session.alliance.goal_aligned = True

    if any(re.search(pattern, text) for pattern in _RUPTURE_PATTERNS):
        session.alliance.rupture_count += 1
        session.alliance.last_rupture_turn = session.turn_count
