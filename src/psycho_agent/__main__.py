"""Terminal demo for either plans or live provider-backed responses."""

from __future__ import annotations

import argparse
import sys
from uuid import uuid4

from .config import ConfigurationError, ProviderSettings, load_dotenv
from .engine import ConversationEngine, format_plan
from .generator import NaturalResponseGenerator
from .models import SessionState
from .providers import ModelError, create_model


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Psycho Agent conversation demo")
    parser.add_argument(
        "--provider",
        choices=("openai", "chatgpt", "deepseek", "gemini"),
        help="Generate live replies with the selected provider; omit for planning-only mode.",
    )
    parser.add_argument(
        "--no-model-review",
        action="store_true",
        help="Disable the optional second model call used for semantic review.",
    )
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    engine = ConversationEngine()
    session = SessionState(session_id=str(uuid4()))
    generator: NaturalResponseGenerator | None = None
    if args.provider:
        load_dotenv()
        try:
            settings = ProviderSettings.from_env(args.provider)
            model = create_model(settings)
            generator = NaturalResponseGenerator(
                model,
                enable_model_review=settings.model_review and not args.no_model_review,
            )
        except ConfigurationError as exc:
            print(f"配置错误：{exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        print(f"Psycho Agent live demo ({settings.provider}/{settings.model}). 输入 quit 退出。")
    else:
        print("Psycho Agent planning demo. 输入 quit 退出。")
    print(format_plan(engine.start(session)))

    while True:
        try:
            message = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in {"quit", "exit", "退出"}:
            break
        if not message:
            continue
        plan = engine.process(session, message)
        if generator is None:
            output = format_plan(plan)
        else:
            try:
                output = generator.generate(
                    session=session,
                    user_message=message,
                    plan=plan,
                ).text
            except ModelError as exc:
                output = f"模型调用失败：{exc}"
        print("\nAgent：" + output)


if __name__ == "__main__":
    main()
