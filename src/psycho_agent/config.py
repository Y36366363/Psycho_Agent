"""Local environment configuration with no third-party dependency."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when a requested provider is not configured safely."""


def _looks_like_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        normalized.startswith(("your_", "your-", "replace_", "replace-"))
        or normalized in {"changeme", "change-me", "api-key", "your api key"}
        or (normalized.startswith("<") and normalized.endswith(">"))
    )


def load_dotenv(path: str | Path = ".env", *, override: bool = False) -> bool:
    """Load a small, conventional subset of dotenv syntax.

    Existing process variables win by default. Values may be unquoted or wrapped in
    matching single/double quotes. The function never logs values.
    """
    dotenv_path = Path(path)
    if not dotenv_path.is_file():
        return False

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value[-1:] == value[:1]:
            value = value[1:-1]
        if key and (override or key not in os.environ):
            os.environ[key] = value
    return True


@dataclass(frozen=True, slots=True)
class ProviderSettings:
    provider: str
    api_key: str
    model: str
    timeout_seconds: float = 60.0
    model_review: bool = True

    @classmethod
    def from_env(cls, provider: str | None = None) -> "ProviderSettings":
        selected = (provider or os.getenv("PSYCHO_MODEL_PROVIDER", "openai")).strip().lower()
        aliases = {"chatgpt": "openai", "google": "gemini"}
        selected = aliases.get(selected, selected)

        definitions = {
            "openai": (
                ("OPENAI_API_KEY", "CHATGPT_API_KEY"),
                "OPENAI_MODEL",
                "gpt-5-mini",
            ),
            "deepseek": (("DEEPSEEK_API_KEY",), "DEEPSEEK_MODEL", "deepseek-chat"),
            "gemini": (("GEMINI_API_KEY",), "GEMINI_MODEL", "gemini-2.5-flash"),
        }
        if selected not in definitions:
            supported = ", ".join(sorted(definitions))
            raise ConfigurationError(f"Unsupported provider '{selected}'. Choose: {supported}.")

        key_names, model_name, default_model = definitions[selected]
        api_key = next((os.getenv(name, "").strip() for name in key_names if os.getenv(name)), "")
        if not api_key:
            raise ConfigurationError(
                f"Missing API key for {selected}. Set one of: {', '.join(key_names)}."
            )
        if _looks_like_placeholder(api_key):
            raise ConfigurationError(
                f"The configured {selected} key is still an example placeholder."
            )

        timeout_text = os.getenv("PSYCHO_REQUEST_TIMEOUT", "60")
        try:
            timeout = float(timeout_text)
        except ValueError as exc:
            raise ConfigurationError("PSYCHO_REQUEST_TIMEOUT must be a number.") from exc
        if not 1 <= timeout <= 300:
            raise ConfigurationError("PSYCHO_REQUEST_TIMEOUT must be between 1 and 300 seconds.")

        review_value = os.getenv("PSYCHO_MODEL_REVIEW", "true").strip().lower()
        model_review = review_value not in {"0", "false", "no", "off"}
        return cls(
            provider=selected,
            api_key=api_key,
            model=os.getenv(model_name, default_model).strip() or default_model,
            timeout_seconds=timeout,
            model_review=model_review,
        )
