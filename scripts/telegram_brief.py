#!/usr/bin/env python3
"""
Daily brief → Telegram.

Composes a short morning brief from the current metrics and GTD dashboard
(via Claude) and sends it to the owner's Telegram chat (TELEGRAM_CHAT_ID).

Run on demand:
    .venv/bin/python scripts/telegram_brief.py

Or schedule it each morning (e.g. after the daily data collection) so the
brief lands on your phone before you open the laptop.

The bot itself calls build_brief() when you text it /brief.
"""

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import get_env  # noqa: E402
import telegram as tg  # noqa: E402

_BRIEF_PROMPT = (
    "Write my morning brief for FitLab Hawaii as a short Telegram message. "
    "Use the current metrics and GTD dashboard in your context. Structure it "
    "as: one-line headline, then 3-6 short bullet lines covering the numbers "
    "that moved and the most important things on deck today. Plain text only, "
    "no markdown. Keep it under 200 words and skip anything you don't have "
    "data for."
)


def build_brief():
    """Generate the brief text with Claude. Returns a plain-text string."""
    history = [{"role": "user", "content": _BRIEF_PROMPT}]
    return tg.ask_claude(history)


def main():
    chat_id = get_env("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("TELEGRAM_CHAT_ID is not set in .env — can't send the brief.")
        print("Message @fitlabhawaiibot once, then set your chat id in .env.")
        sys.exit(1)
    brief = build_brief()
    tg.send_message(chat_id, brief)
    print("Brief sent.")


if __name__ == "__main__":
    main()
