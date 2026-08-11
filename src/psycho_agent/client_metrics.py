"""Extract explicit client-side experience and disengagement signals."""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .models import SessionState


_UNDERSTOOD_POSITIVE = (
    r"你.{0,6}(?:理解|懂|明白)我",
    r"这(?:很|比较)?(?:贴近|符合)我的感受",
    r"你抓到(?:重点|我卡住的地方)了",
)
_UNDERSTOOD_NEGATIVE = (
    r"你(?:根本|还是|并没有)?没(?:有)?(?:理解|懂|明白)我",
    r"你理解错了",
    r"这不是我(?:想说|的意思|需要)的",
)
_PRESSURE = (
    r"别(?:再)?逼我",
    r"你这样让我(?:更有压力|觉得被迫|很有压力)",
    r"我不想被(?:要求|催着|逼着)",
)
_ACTION_REJECTION = (
    r"这个(?:方法|建议|办法|行动).{0,8}(?:不适合|没用|做不到|不想试)",
    r"我(?:不想|不会|没法|做不到).{0,8}(?:试|做|执行)",
    r"这个我已经试过了",
)
_EXIT = (
    r"我不想(?:再)?聊了",
    r"(?:先到这里|就这样吧|不聊了|我要退出)",
    r"我不会再用(?:这个|你|这个系统)",
)

_REASON_PATTERNS = {
    "unwanted_advice": r"(?:不想要|别再|没有要).{0,6}(?:建议|方法|办法)",
    "infeasible": r"(?:做不到|没时间|没精力|不现实|太难)",
    "already_tried": r"(?:已经|以前).{0,5}(?:试过|做过).{0,6}(?:没用|没有用|无效)?",
    "misunderstood": r"(?:没理解|理解错|不是我的意思|答非所问)",
    "privacy_concern": r"(?:隐私|记录|保存|泄露|谁能看到)",
    "low_trust": r"(?:不信任|不相信|不敢信)",
    "felt_pressured": r"(?:逼我|被迫|压力更大|催着)",
}


def update_client_feedback(session: SessionState, message: str) -> None:
    """Update only from explicit first-person feedback, never infer satisfaction."""
    text = " ".join(message.strip().split())
    if not text:
        return
    state = session.client_feedback

    if any(re.search(pattern, text) for pattern in _UNDERSTOOD_POSITIVE):
        state.felt_understood = True
    if any(re.search(pattern, text) for pattern in _UNDERSTOOD_NEGATIVE):
        state.felt_understood = False
        state.correction_count += 1
    if any(re.search(pattern, text) for pattern in _PRESSURE):
        state.pressure_reported = True
    if any(re.search(pattern, text) for pattern in _ACTION_REJECTION):
        state.action_rejected = True
        _append_reasons(state.action_rejection_reasons, text)
    if any(re.search(pattern, text) for pattern in _EXIT):
        state.exit_intent = True
        _append_reasons(state.exit_reasons, text)


def _append_reasons(destination: list[str], text: str) -> None:
    matched = [name for name, pattern in _REASON_PATTERNS.items() if re.search(pattern, text)]
    for reason in matched or ["unspecified"]:
        if reason not in destination:
            destination.append(reason)


def client_feedback_snapshot(session: SessionState) -> dict[str, Any]:
    """Return an exportable snapshot without pretending unknown feedback is positive."""
    return asdict(session.client_feedback)
