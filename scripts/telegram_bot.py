#!/usr/bin/env python3
"""
AIOS Telegram bot — @fitlabhawaiibot

A phone-first command center for FitLab Hawaii. Long-polls Telegram and:
  * /metrics        → current key numbers from the DataOS warehouse
  * /brief          → an on-demand version of the morning brief
  * anything else   → answered by Claude with full business context

Only the owner's chat (TELEGRAM_CHAT_ID in .env) is served; every other chat
gets a polite "not authorised" and its own chat id, so you can allowlist it.

Run it:
    .venv/bin/python scripts/telegram_bot.py

Leave it running (a terminal, tmux, or a launchd job) and text the bot.
Stop with Ctrl-C.
"""

import sys
import time
import traceback
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import get_env  # noqa: E402
import telegram as tg  # noqa: E402

HISTORY_TURNS = 12  # keep the last N messages per chat for context
_history = {}       # chat_id -> list[{"role","content"}]

HELP = (
    "AIOS command center for FitLab Hawaii.\n\n"
    "/metrics — current key numbers\n"
    "/brief — today's summary\n"
    "/reset — clear our conversation\n"
    "/help — this message\n\n"
    "Or just text me a question about the business and I'll answer with "
    "your context."
)


def _reply(chat_id, text):
    try:
        tg.send_message(chat_id, text)
    except Exception:
        traceback.print_exc()


def handle_command(chat_id, text):
    """Return True if the text was a recognised command."""
    cmd = text.split()[0].lower().lstrip("/")
    cmd = cmd.split("@")[0]  # strip @botname suffix Telegram may add
    if cmd in ("start", "help"):
        _reply(chat_id, HELP)
    elif cmd == "metrics":
        _reply(chat_id, tg.read_metrics())
    elif cmd == "brief":
        _reply(chat_id, "Putting your brief together…")
        try:
            import telegram_brief
            _reply(chat_id, telegram_brief.build_brief())
        except Exception:
            traceback.print_exc()
            _reply(chat_id, "Couldn't build the brief — check the bot logs.")
    elif cmd == "reset":
        _history.pop(chat_id, None)
        _reply(chat_id, "Cleared. Fresh start.")
    else:
        return False
    return True


def handle_question(chat_id, text):
    hist = _history.setdefault(chat_id, [])
    hist.append({"role": "user", "content": text})
    del hist[:-HISTORY_TURNS]
    try:
        answer = tg.ask_claude(hist)
    except Exception:
        traceback.print_exc()
        _reply(chat_id, "Something went wrong answering that — check the logs.")
        # drop the unanswered user turn so history stays valid
        if hist and hist[-1]["role"] == "user":
            hist.pop()
        return
    hist.append({"role": "assistant", "content": answer})
    _reply(chat_id, answer)


def process(update, allowed):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    text = msg.get("text")
    chat_id = msg.get("chat", {}).get("id")
    if not text or chat_id is None:
        return

    # Authorisation: only the allowlisted owner chat is served.
    if not allowed:
        _reply(chat_id,
               "Setup needed: your Telegram chat id is "
               f"{chat_id}\nAdd it as TELEGRAM_CHAT_ID in .env to activate me.")
        return
    if str(chat_id) != str(allowed):
        _reply(chat_id,
               f"Sorry, this bot is private. (Your chat id is {chat_id}.)")
        return

    if text.startswith("/"):
        if not handle_command(chat_id, text):
            _reply(chat_id, "Unknown command. Try /help.")
    else:
        handle_question(chat_id, text)


def main():
    if not get_env("TELEGRAM_BOT_TOKEN"):
        print("TELEGRAM_BOT_TOKEN is not set in .env. Aborting.")
        sys.exit(1)
    allowed = get_env("TELEGRAM_CHAT_ID")
    if allowed:
        print(f"Bot running. Serving chat id {allowed}. Ctrl-C to stop.")
    else:
        print("Bot running WITHOUT an allowlist — message it to learn your "
              "chat id, then set TELEGRAM_CHAT_ID in .env. Ctrl-C to stop.")

    offset = None
    while True:
        try:
            updates = tg.get_updates(offset=offset, long_poll=60)
        except KeyboardInterrupt:
            print("\nStopped.")
            return
        except Exception:
            traceback.print_exc()
            time.sleep(5)
            continue
        for update in updates or []:
            offset = update["update_id"] + 1
            try:
                process(update, allowed)
            except Exception:
                traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
