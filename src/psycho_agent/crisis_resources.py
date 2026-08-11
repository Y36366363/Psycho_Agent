"""Verified, locale-aware crisis resources with directly renderable actions."""

from __future__ import annotations

import json
from html import escape
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ActionLink


DEFAULT_RESOURCES = (
    Path(__file__).resolve().parents[2] / "evaluations" / "crisis_resources.json"
)


@dataclass(frozen=True, slots=True)
class CrisisResourceCard:
    locale: str
    immediate_message: str
    support_message: str
    actions: list[ActionLink]
    verified_at: str | None
    source_url: str | None
    used_fallback: bool = False


def load_crisis_resources(path: str | Path = DEFAULT_RESOURCES) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    locales = data.get("locales")
    if not data.get("version") or not isinstance(locales, dict) or not locales:
        raise ValueError("Crisis resources need a version and locale entries.")
    for locale, entry in locales.items():
        if not entry.get("verified_at") or not entry.get("source_url"):
            raise ValueError(f"Crisis locale {locale} lacks verification metadata.")
        for action in entry.get("actions", []):
            href = str(action.get("href", ""))
            if not href.startswith(("tel:", "sms:", "https://")):
                raise ValueError(f"Unsafe crisis action URI for locale {locale}.")
    return data


def get_crisis_resource_card(
    locale: str, path: str | Path = DEFAULT_RESOURCES
) -> CrisisResourceCard:
    data = load_crisis_resources(path)
    entry = data["locales"].get(locale)
    if entry is None:
        return CrisisResourceCard(
            locale=locale,
            immediate_message=(
                "If danger is immediate, contact local emergency services now and ask a "
                "trusted person to stay with you."
            ),
            support_message=(
                "This system does not know a verified crisis number for your locale. "
                "Do not rely on an unverified number."
            ),
            actions=[],
            verified_at=None,
            source_url=None,
            used_fallback=True,
        )
    return CrisisResourceCard(
        locale=locale,
        immediate_message=entry["immediate_message"],
        support_message=entry["support_message"],
        actions=[ActionLink(**action) for action in entry["actions"]],
        verified_at=entry["verified_at"],
        source_url=entry["source_url"],
    )


def render_crisis_card_html(card: CrisisResourceCard) -> str:
    """Render an accessible action panel; callers still control page integration."""
    action_html = "".join(
        (
            f'<a class="crisis-action crisis-action--{escape(action.kind)}" '
            f'href="{escape(action.href, quote=True)}">{escape(action.label)}</a>'
        )
        for action in card.actions
    )
    verification = ""
    if card.source_url and card.verified_at:
        verification = (
            '<p class="crisis-verification">'
            f'<a href="{escape(card.source_url, quote=True)}">Official source</a> · '
            f'verified {escape(card.verified_at)}</p>'
        )
    return (
        '<section class="crisis-card" role="alert" aria-live="assertive">'
        '<h2>Immediate support</h2>'
        f'<p>{escape(card.immediate_message)}</p>'
        f'<p>{escape(card.support_message)}</p>'
        f'<div class="crisis-actions">{action_html}</div>'
        f'{verification}</section>'
    )
