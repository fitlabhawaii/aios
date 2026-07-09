#!/usr/bin/env python3
"""
One-time Telegram setup — capture your chat id and allowlist it.

Steps:
  1. Open Telegram and send any message (e.g. "hi") to @fitlabhawaiibot
  2. Run:  .venv/bin/python scripts/telegram_setup.py
  3. It finds your chat id and writes TELEGRAM_CHAT_ID into .env

After this, only your chat is served by the bot, and the daily brief knows
where to go. Re-run any time you need to point the bot at a different chat.
"""

import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import WORKSPACE_ROOT  # noqa: E402
import telegram as tg  # noqa: E402

ENV_PATH = WORKSPACE_ROOT / ".env"


def _latest_chat():
    updates = tg.get_updates(long_poll=0) or []
    for update in reversed(updates):
        msg = update.get("message") or update.get("edited_message") or {}
        chat = msg.get("chat", {})
        if chat.get("id") is not None:
            return chat
    return None


def _write_chat_id(chat_id):
    text = ENV_PATH.read_text(encoding="utf-8")
    line = f"TELEGRAM_CHAT_ID={chat_id}"
    if re.search(r"^TELEGRAM_CHAT_ID=.*$", text, flags=re.M):
        text = re.sub(r"^TELEGRAM_CHAT_ID=.*$", line, text, count=1, flags=re.M)
    else:
        text = text.rstrip() + "\n" + line + "\n"
    ENV_PATH.write_text(text, encoding="utf-8")


def main():
    chat = _latest_chat()
    if not chat:
        print("No messages found yet.")
        print("Open Telegram, send any message to @fitlabhawaiibot, then "
              "run this again.")
        sys.exit(1)
    chat_id = chat["id"]
    name = chat.get("first_name") or chat.get("title") or "you"
    _write_chat_id(chat_id)
    print(f"Found chat with {name}: id {chat_id}")
    print("Saved TELEGRAM_CHAT_ID to .env — the bot will now serve this chat.")


if __name__ == "__main__":
    main()
