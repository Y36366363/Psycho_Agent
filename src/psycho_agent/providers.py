"""Provider-neutral text model adapters using the Python standard library."""

from __future__ import annotations

import http.client
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .config import ProviderSettings


class ModelError(RuntimeError):
    """Safe provider error that never includes an API key."""


class TextModel(Protocol):
    provider_name: str
    model_name: str

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class JsonTransport(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        attempts = 3
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=timeout,
                    context=_verified_ssl_context(),
                ) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                # Provider error bodies may echo masked credential fragments or user input.
                # Keep the public error useful without passing any response body upstream.
                safe_messages = {
                    400: "The provider rejected the request or API key.",
                    401: "Authentication failed; check the API key.",
                    403: "Access was denied; check key permissions and model access.",
                    404: "The endpoint or configured model was not found.",
                    429: "The provider rate limit or quota was reached.",
                }
                detail = safe_messages.get(exc.code, "The provider rejected the request.")
                raise ModelError(f"Provider returned HTTP {exc.code}. {detail}") from exc
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                http.client.HTTPException,
                OSError,
            ) as exc:
                if attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                reason = exc.reason if hasattr(exc, "reason") else exc
                raise ModelError(
                    f"Could not reach provider after {attempts} attempts: {reason}"
                ) from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ModelError("Provider returned an unreadable response.") from exc
        raise ModelError("Provider request failed after bounded retries.")


def _verified_ssl_context() -> ssl.SSLContext:
    """Create a verified TLS context, including a safe macOS framework fallback."""
    paths = ssl.get_default_verify_paths()
    if paths.cafile is None:
        system_bundle = Path("/etc/ssl/cert.pem")
        if system_bundle.is_file():
            return ssl.create_default_context(cafile=str(system_bundle))
    return ssl.create_default_context()


@dataclass(slots=True)
class OpenAIAdapter:
    api_key: str
    model_name: str
    timeout: float = 60.0
    transport: JsonTransport | None = None
    provider_name: str = "openai"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        transport = self.transport or UrllibJsonTransport()
        data = transport.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload={"model": self.model_name, "instructions": system_prompt, "input": user_prompt},
            timeout=self.timeout,
        )
        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"].strip()
        pieces: list[str] = []
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    pieces.append(content["text"])
        if not pieces:
            raise ModelError("OpenAI response contained no output text.")
        return "\n".join(pieces).strip()


@dataclass(slots=True)
class DeepSeekAdapter:
    api_key: str
    model_name: str
    timeout: float = 60.0
    transport: JsonTransport | None = None
    provider_name: str = "deepseek"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        transport = self.transport or UrllibJsonTransport()
        data = transport.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=self.timeout,
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("DeepSeek response contained no output text.") from exc
        if not isinstance(text, str) or not text.strip():
            raise ModelError("DeepSeek response contained no output text.")
        return text.strip()


@dataclass(slots=True)
class GeminiAdapter:
    api_key: str
    model_name: str
    timeout: float = 60.0
    transport: JsonTransport | None = None
    provider_name: str = "gemini"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        transport = self.transport or UrllibJsonTransport()
        model_path = urllib.parse.quote(self.model_name, safe="-_.")
        data = transport.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_path}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            payload={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            },
            timeout=self.timeout,
        )
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "\n".join(part["text"] for part in parts if part.get("text"))
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("Gemini response contained no output text.") from exc
        if not text.strip():
            raise ModelError("Gemini response contained no output text.")
        return text.strip()


def create_model(settings: ProviderSettings, transport: JsonTransport | None = None) -> TextModel:
    common = {
        "api_key": settings.api_key,
        "model_name": settings.model,
        "timeout": settings.timeout_seconds,
        "transport": transport,
    }
    if settings.provider == "openai":
        return OpenAIAdapter(**common)
    if settings.provider == "deepseek":
        return DeepSeekAdapter(**common)
    if settings.provider == "gemini":
        return GeminiAdapter(**common)
    raise ValueError(f"Unsupported provider: {settings.provider}")
