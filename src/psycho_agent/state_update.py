"""Conservative extraction of explicit user state from conversation turns."""

from __future__ import annotations

import re

from .client_metrics import update_client_feedback
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

_PAUSE_ADVICE_PATTERNS = (
    r"(?:先|现在|这会儿).{0,5}(?:别|不要|不想).{0,5}(?:方法|办法|建议|分析)",
    r"我还没(?:有)?说完",
    r"(?:先|只想).{0,5}(?:听我说|倾诉)",
)

_RESUME_ADVICE_PATTERNS = (
    r"我说完了",
    r"现在可以.{0,6}(?:方法|办法|建议|下一步)",
    r"可以开始.{0,6}(?:分析|想办法|给建议)",
)

_TINY_STEP_PATTERNS = (
    r"(?:最小|很小|最简单).{0,5}(?:一步|下一步|行动)",
    r"今天能做的.{0,6}(?:一步|事情|行动)",
)

_EXCLUSIVE_AI_PATTERNS = (
    r"只有你.{0,8}(?:愿意听|懂我|能理解|可以说)",
    r"(?:不打算|不会|不想).{0,8}(?:告诉|联系|找).{0,6}(?:现实|身边|其他人|任何人)",
    r"现实里.{0,6}(?:没人|没有人).{0,6}(?:能听|理解|可信)",
)


def update_session_state(session: SessionState, message: str) -> None:
    """Extract only explicit, auditable signals; never infer a diagnosis."""
    text = " ".join(message.strip().split())
    if not text:
        return

    update_client_feedback(session, text)

    # These two signals describe the current turn rather than a durable preference.
    session.user.tiny_step_requested = False
    session.user.exclusive_ai_reliance = False

    intensity_matches = re.findall(r"(?<!\d)(10|[0-9])\s*(?:分|/\s*10)(?!\d)", text)
    if intensity_matches:
        session.user.emotion_intensity = int(intensity_matches[-1])

    for emotion in _EMOTIONS:
        if emotion in text and emotion not in session.user.emotion_words:
            session.user.emotion_words.append(emotion)

    for area, markers in _IMPACT_AREAS.items():
        if any(marker in text for marker in markers) and area not in session.user.functional_impact:
            session.user.functional_impact.append(area)

    if any(re.search(pattern, text) for pattern in _PAUSE_ADVICE_PATTERNS):
        session.user.support_preference = SupportPreference.LISTEN
        session.user.advice_paused = True
    elif re.search(r"(?:帮我|一起).{0,5}(?:理清|看清|分析)|为什么会这样", text):
        session.user.support_preference = SupportPreference.UNDERSTAND
    elif re.search(r"(?:想|需要|帮我).{0,5}(?:办法|方案|建议|下一步)|我该怎么做", text):
        session.user.support_preference = SupportPreference.PLAN

    if any(re.search(pattern, text) for pattern in _RESUME_ADVICE_PATTERNS):
        session.user.advice_paused = False
        session.user.support_preference = SupportPreference.PLAN

    if any(re.search(pattern, text) for pattern in _TINY_STEP_PATTERNS):
        session.user.tiny_step_requested = True
        session.user.advice_paused = False
        session.user.support_preference = SupportPreference.PLAN

    if any(re.search(pattern, text) for pattern in _EXCLUSIVE_AI_PATTERNS):
        session.user.exclusive_ai_reliance = True

    if session.user.support_preference is not SupportPreference.UNKNOWN:
        session.alliance.goal_aligned = True

    if any(re.search(pattern, text) for pattern in _RUPTURE_PATTERNS):
        session.alliance.rupture_count += 1
        session.alliance.last_rupture_turn = session.turn_count
