"""Small terminal demo for inspecting conversation plans."""

from __future__ import annotations

from uuid import uuid4

from .engine import ConversationEngine, format_plan
from .models import SessionState


def main() -> None:
    engine = ConversationEngine()
    session = SessionState(session_id=str(uuid4()))
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
        print("\nAgent：" + format_plan(engine.process(session, message)))


if __name__ == "__main__":
    main()
