"""Opt-in live connectivity checks for configured model providers."""

from __future__ import annotations

import argparse

from .config import ConfigurationError, ProviderSettings, load_dotenv
from .providers import ModelError, create_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Test configured model API connectivity")
    parser.add_argument(
        "providers",
        nargs="*",
        choices=("openai", "chatgpt", "deepseek", "gemini"),
        default=["openai", "deepseek", "gemini"],
    )
    args = parser.parse_args()
    load_dotenv()

    failed = False
    for provider in args.providers:
        try:
            settings = ProviderSettings.from_env(provider)
            model = create_model(settings)
            reply = model.complete(
                "Reply with exactly the two uppercase letters OK and nothing else.",
                "Connectivity check.",
            )
            accepted = reply.strip().upper() == "OK"
            marker = "PASS" if accepted else "REACHABLE"
            print(f"{marker} {settings.provider}/{settings.model}: response received")
        except (ConfigurationError, ModelError) as exc:
            failed = True
            print(f"FAIL {provider}: {exc}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
