"""
Telegram helper — shared plumbing for the AIOS Telegram bot.

Provides:
  * low-level Telegram Bot API calls (get_updates, send_message) via requests
  * business-context loading (the same files /prime reads) for Claude
  * ask_claude() — answer a question with full FitLab business context

Credentials come from .env (loaded by config.py):
  TELEGRAM_BOT_TOKEN   the bot token from @BotFather
  TELEGRAM_CHAT_ID     the owner's chat id (allowlist — only this chat is served)
  ANTHROPIC_API_KEY    powers the "ask AIOS anything" replies

Nothing here is FitLab-specific except the file paths, which follow the
standard AIOS workspace layout.
"""

import sys
from pathlib import Path

import requests

# Make sibling scripts importable when run directly
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from config import get_env, WORKSPACE_ROOT  # noqa: E402

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE = 4000  # Telegram hard limit is 4096; leave headroom

# Context files loaded into Claude's system prompt (same spirit as /prime).
_CONTEXT_FILES = [
    "context/business-info.md",
    "context/personal-info.md",
    "context/strategy.md",
    "context/current-data.md",
    "context/group/key-metrics.md",
    "gtd/dashboard.md",
]


# ─── Telegram API ────────────────────────────────────────────────────────────

def _token():
    token = get_env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set in .env — add your @BotFather token."
        )
    return token


def tg_call(method, http_timeout=65, **params):
    """Call a Telegram Bot API method. Returns the parsed 'result' or raises."""
    url = TELEGRAM_API.format(token=_token(), method=method)
    resp = requests.post(url, json=params, timeout=http_timeout)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error on {method}: {data}")
    return data.get("result")


def get_updates(offset=None, long_poll=60):
    """Long-poll for new updates. Returns a list of update objects."""
    params = {"timeout": long_poll}
    if offset is not None:
        params["offset"] = offset
    # requests timeout must exceed the long-poll window
    return tg_call("getUpdates", http_timeout=long_poll + 5, **params)


def send_message(chat_id, text):
    """Send text to a chat, splitting to respect Telegram's length limit."""
    text = text if text.strip() else "(no content)"
    for chunk in _chunk(text, MAX_MESSAGE):
        tg_call("sendMessage", http_timeout=20, chat_id=chat_id, text=chunk,
                disable_web_page_preview=True)


def _chunk(text, size):
    """Split text into <=size pieces, preferring line boundaries."""
    if len(text) <= size:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        # A single line longer than size gets hard-split.
        while len(line) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:size])
            line = line[size:]
        if len(current) + len(line) + 1 > size:
            chunks.append(current)
            current = line
        else:
            current = line if not current else current + "\n" + line
    if current:
        chunks.append(current)
    return chunks


# ─── Business context ────────────────────────────────────────────────────────

def load_context():
    """Read the AIOS context files into one string for Claude's system prompt."""
    parts = []
    for rel in _CONTEXT_FILES:
        path = WORKSPACE_ROOT / rel
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                parts.append(f"===== {rel} =====\n{text}")
    return "\n\n".join(parts)


def read_metrics():
    """Return the auto-generated key metrics, or a friendly fallback."""
    path = WORKSPACE_ROOT / "context/group/key-metrics.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return "No metrics file yet. Run the data collector to generate one."


# ─── Claude ──────────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """You are the AIOS assistant for FitLab Hawaii, texting the \
owner through a Telegram bot. Answer using the business context below.

Rules:
- Be concise and direct — this is a phone chat, not a report. A few sentences \
is usually right. Lead with the answer.
- Ground answers in the context. If a number or fact isn't in the context, say \
so plainly rather than guessing.
- Never expose secrets, API keys, or patient/PHI details.
- Plain text only (no markdown tables or headers) — it's a text message.

===== BUSINESS CONTEXT =====
{context}
"""


def ask_claude(history, context=None):
    """
    Answer using Claude with FitLab business context.

    history: list of {"role": "user"|"assistant", "content": str}
    Returns the assistant's reply text.
    """
    import anthropic  # imported lazily so metrics/brief work without it

    api_key = get_env("ANTHROPIC_API_KEY")
    if not api_key:
        return ("I can't answer questions right now — ANTHROPIC_API_KEY isn't "
                "set in .env. Metrics and the daily brief still work.")

    if context is None:
        context = load_context()
    system = _SYSTEM_TEMPLATE.format(context=context)

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        messages=history,
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip() \
        or "(no reply)"
