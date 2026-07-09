# Integration: Telegram Bot (@fitlabhawaiibot)

> A phone-first command center — text the bot for metrics, a daily brief, or free-form questions answered by Claude with full business context.

## Overview

Connects a Telegram bot to the AIOS. The bot long-polls Telegram's Bot API and
answers from the same context `/prime` loads. Runs always-on via launchd; a
second launchd job pushes a morning brief daily. Only the owner's chat is
served (allowlist).

## Key Files

| File | Purpose |
|------|---------|
| `scripts/telegram.py` | Shared helpers — Telegram API (`get_updates`, `send_message`), context loading, `ask_claude()` |
| `scripts/telegram_bot.py` | Interactive bot — long-poll loop, command routing, per-chat history |
| `scripts/telegram_brief.py` | Composes the morning brief and sends it to the owner chat |
| `scripts/telegram_setup.py` | One-time: captures owner chat id into `.env` |
| `config/com.aios.telegram-bot.plist` | launchd job — always-on bot (KeepAlive, RunAtLoad) |
| `config/com.aios.telegram-brief.plist` | launchd job — daily brief at 6:15 AM |

## Configuration (.env)

| Var | Notes |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Owner chat id — the allowlist. Set by `telegram_setup.py`. Group chats have negative ids. |
| `ANTHROPIC_API_KEY` | Powers free-form answers and the brief (`claude-opus-4-8`) |

## How It Works

1. `telegram_bot.py` calls `getUpdates` (60s long-poll), tracking `offset`
2. Each message is checked against `TELEGRAM_CHAT_ID`; other chats are refused
   (and told their own id, so they can be allowlisted)
3. Commands: `/metrics` (reads `context/group/key-metrics.md`), `/brief`
   (calls `telegram_brief.build_brief()`), `/reset`, `/help`
4. Any other text → `ask_claude()`: builds a system prompt from the context
   files (business-info, personal-info, strategy, current-data, key-metrics,
   GTD dashboard), keeps the last ~12 turns per chat, calls the Messages API
5. Replies are chunked to Telegram's 4096-char limit and sent via `sendMessage`

The morning brief (`telegram_brief.py`) reuses `ask_claude()` with a fixed
prompt to summarize current metrics + dashboard, and sends it to the owner.

## Running It (launchd)

| Job | Cadence |
|-----|---------|
| `com.aios.telegram-bot` | Always-on; starts on login, restarts on crash |
| `com.aios.telegram-brief` | Daily 6:15 AM (after the 6 AM data collect) |

Plists live in `config/`, installed to `~/Library/LaunchAgents/`. Logs:
`data/telegram-bot.log`, `data/telegram-brief.log`.

- Restart the bot: `launchctl unload ~/Library/LaunchAgents/com.aios.telegram-bot.plist && launchctl load ~/Library/LaunchAgents/com.aios.telegram-bot.plist`
- Run by hand (only if the launchd job is unloaded): `.venv/bin/python scripts/telegram_bot.py`

## Gotchas

- **One poller only:** Telegram allows a single `getUpdates` consumer. Don't run
  a manual bot while the launchd job is loaded — the second gets HTTP 409.
- **Allowlist first:** with no `TELEGRAM_CHAT_ID` set, the bot serves no one — it
  only replies with each sender's chat id so you can allowlist it.
- **Group privacy mode:** in Telegram groups, a bot with privacy mode ON sees
  only commands and @mentions, not plain text. The owner chat is a group where
  plain text reaches the bot, so privacy mode is effectively off; if free-form
  questions stop arriving, disable privacy via @BotFather (`/setprivacy`).
- **`http_timeout`:** Telegram's `getUpdates` takes a `timeout` body param that
  collides with the `requests` `timeout` kwarg — the helper uses `http_timeout`.
- **PHI:** the bot answers from business context, not the patient-level DB; keep
  it that way. Never surface `jane_sales` rows or contact data.
- **API cost:** every free-form question and each brief is a Claude call.

## Dependencies

- **Depends on:** `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `anthropic` SDK,
  `requests`, the `context/` files + `context/group/key-metrics.md` (DataOS)
- **Used by:** the owner, from their phone

## History

| Date | Change |
|------|--------|
| 2026-07-08 | Initial build — interactive bot, /metrics, /brief, Claude Q&A, launchd always-on + daily brief |
