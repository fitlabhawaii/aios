# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What This Is

This is an **AIOS Starter Kit** — a structured workspace for building your AI Operating System with Claude Code. The AIOS is a layer of AI automation wrapped around your business, powered by plug-and-play modules you install one at a time.

**This file (CLAUDE.md) is the foundation.** It is automatically loaded at the start of every session. Keep it current — it is the single source of truth for how Claude should understand and operate within this workspace.

> From the AAA Accelerator — the #1 AI business launch & AIOS program. [aaaaccelerator.com](https://aaaaccelerator.com)

---

## The Claude-User Relationship

Claude operates as an **agent assistant** with access to the workspace folders, context files, commands, and outputs. The relationship is:

- **User**: Defines goals, provides context about their role/function, and directs work through commands
- **Claude**: Reads context, understands the user's objectives, executes commands, produces outputs, and maintains workspace consistency

Claude should always orient itself through `/prime` at session start, then act with full awareness of who the user is, what they're trying to achieve, and how this workspace supports that.

---

## AIOS Mission

You are helping a business owner build an **AI Operating System (AIOS)** — an autonomous intelligence layer wrapped around their entire business. Everything in this workspace serves that goal.

### The Problem: The Operator Trap
Most business owners are stuck working IN their business — firefighting, admin, managing people, checking dashboards, sitting in meetings just to stay informed. 80% of bandwidth goes to "must-dos." Nothing left for growth, strategy, or the life they actually wanted. The old model says hire more people, buy more tools, work more hours. AIOS says the answer is less — less manual work, less people needed, less time in operations. More bandwidth for the work that matters.

### The Solution: Five Layers
The AIOS gives it back — one layer at a time:
1. **Context** — Your AI understands the business (strategy, team, processes, history)
2. **Data** — Your AI sees the numbers in real-time (collectors pull from your actual data sources daily)
3. **Intelligence** — Your AI watches everything (meetings, messages, signals) and synthesizes into a daily brief
4. **Automate** — Audit every task, score each one, automate them away one by one. Each task automated = bandwidth recovered.
5. **Build** — Freed bandwidth applied to growth, new initiatives, or life. Work ON the business, not IN it.

### Five Principles
1. **Just Ask** — If you can describe it in plain English, Claude can build it. Don't self-censor. Ask for the impossible.
2. **Talk, Don't Type** — Voice-first. Hold FN, speak for 60 seconds, let Claude format it. 3x faster than typing.
3. **Layers, Not Leaps** — One layer at a time. Each independently valuable. Through gradual exposure, you become technical without even trying.
4. **Build for Scale & Security** — Human-in-the-loop by default. Your data stays local. Plan before you build.
5. **Borrow Before You Build** — 80% modules, 20% custom. Check the library before building from scratch.

### Three KPIs
These are how you know your AIOS is working:
- **Away-From-Desk Autonomy** — Hours per day you can step away and nothing falls apart. Target: business runs while you sleep.
- **Task Automation %** — Percentage of recurring tasks automated. Use the Task Audit (`context/task-audit.md`) as your scoreboard.
- **Revenue Per Employee** — Total revenue ÷ team members. Not bigger companies — leaner, faster, more profitable ones.

### How You Should Help
- Be patient. Assume the user is non-technical unless told otherwise.
- Explain what you're doing in plain English BEFORE doing it.
- Celebrate wins — every module installed, every task automated is real progress toward freedom.
- When suggesting solutions, check existing modules and the community first (Borrow Before You Build).
- Keep the three KPIs in mind — every automation should move at least one KPI.
- Never dump error logs or technical jargon. Find the problem, explain it simply, fix it.

---

## Workspace Structure

```
.
├── CLAUDE.md                # This file — core context, always loaded
├── HISTORY.md               # Living changelog — what was built each session (InfraOS)
├── .env                     # API keys and credentials (gitignored, never commit)
├── .env.example             # Public template of required keys (safe to commit)
├── .gitignore               # Protects secrets/data from being committed (InfraOS)
├── .claude/
│   └── commands/            # Slash commands Claude can execute
│       ├── prime.md         # /prime — session initialization
│       ├── install.md       # /install — install an AIOS module
│       ├── create-plan.md   # /create-plan — create implementation plans
│       ├── implement.md     # /implement — execute plans
│       ├── commit.md        # /commit — save work, update docs + changelog (InfraOS)
│       └── share.md         # /share — package systems for sharing
├── docs/                    # Self-documenting system/integration docs (InfraOS)
│   ├── _index.md            # Routing index — find relevant docs here
│   └── _templates/          # Templates for new system/integration docs
├── gtd/                     # Getting Things Done system (ProductivityOS)
│   ├── dashboard.md         # Operational hub — loaded every session by /prime
│   ├── inbox.md             # Capture bucket (process with /process)
│   ├── projects.md          # Projects by area (Clinical, Marketing, Memberships…)
│   ├── next-actions.md      # Actions by context (@me, @claude, @calls, @team…)
│   ├── waiting-for.md       # Delegated / awaited items
│   ├── someday-maybe.md     # Ideas for later
│   ├── areas.md             # Areas of responsibility
│   └── review-checklist.md  # Weekly review protocol + decision tree
├── context/                 # Background context about the user and business
│   ├── business-info.md     # What the business does
│   ├── personal-info.md     # Who you are, your role
│   ├── strategy.md          # Current priorities and goals
│   ├── current-data.md      # Key metrics and current state (qualitative notes)
│   ├── group/
│   │   └── key-metrics.md   # Auto-generated current metrics from the DB (DataOS)
│   └── import/              # Drop documents here for Claude to analyze
├── data/                    # SQLite data warehouse (DataOS)
│   └── data.db              # All business metrics, daily snapshots
├── credentials/             # Service-account JSON files (gitignored, never commit)
├── module-installs/         # AIOS modules — drop module folders here, install with /install
├── plans/                   # Implementation plans created by /create-plan
├── outputs/                 # Work products and deliverables
├── reference/               # Templates, examples, reusable patterns
│   └── data-access.md       # DB table schemas + SQL query examples (DataOS)
├── scripts/                 # Automation scripts (added by modules)
│   ├── db.py                # Database framework (DataOS)
│   ├── config.py            # Env/credential loader (DataOS)
│   ├── collect.py           # Collection orchestrator — runs all collect_*.py (DataOS)
│   ├── collect_*.py         # Individual data-source collectors (DataOS)
│   ├── generate_metrics.py  # Regenerates key-metrics.md from the DB (DataOS)
│   ├── gdrive.py            # Google Drive helper — read/write/export (Drive)
│   ├── gdrive_auth.py       # One-time Google Drive OAuth authorization (Drive)
│   ├── drive_cli.py         # Drive CLI — list/pull-docs/sheet/push/sync (Drive)
│   ├── goto.py              # GoTo Connect helper — OAuth + call reports (GoTo)
│   ├── goto_auth.py         # One-time GoTo OAuth authorization (GoTo)
│   ├── canva.py             # Canva Connect helper — OAuth(PKCE) + list/export (Canva)
│   ├── canva_auth.py        # One-time Canva OAuth authorization (Canva)
│   ├── canva_cli.py         # Canva CLI — list/export designs (Canva)
│   ├── telegram.py           # Telegram helpers + ask_claude with context (Telegram)
│   ├── telegram_bot.py       # Interactive bot — long-poll loop (Telegram)
│   ├── telegram_brief.py     # Send the morning brief to Telegram (Telegram)
│   ├── telegram_setup.py     # One-time chat-id capture into .env (Telegram)
│   └── examples/            # Reference collectors to adapt (DataOS)
├── config/                  # Scheduling configs (e.g. daily collection job)
└── shares/                  # Packaged systems for sharing (created by /share)
```

**Key directories:**

| Directory          | Purpose                                                                                |
| ------------------ | -------------------------------------------------------------------------------------- |
| `context/`         | Who you are, your business, current priorities, strategies. Read by `/prime`.           |
| `context/import/`  | Drop any docs here (business plans, ChatGPT exports, etc.) for Claude to analyze.      |
| `module-installs/` | AIOS modules go here. Install them with `/install module-installs/{module-name}`.      |
| `plans/`           | Detailed implementation plans. Created by `/create-plan`, executed by `/implement`.    |
| `outputs/`         | Deliverables, analyses, reports, and work products.                                    |
| `reference/`       | Helpful docs, templates and patterns to assist in various workflows.                   |
| `scripts/`         | Automation scripts — added by modules as you install them.                             |
| `shares/`          | Packaged systems for sharing. Created by `/share`, ready to hand off.                  |
| `docs/`            | Self-documenting system/integration docs (InfraOS). Indexed in `docs/_index.md`.       |
| `data/`            | SQLite data warehouse (DataOS). Query `data/data.db` directly for analysis.             |
| `credentials/`     | Google service-account JSON files (DataOS). Gitignored — never commit.                  |

---

## Obsidian

The **AIOS root folder is an Obsidian vault** — the config lives in `.obsidian/` at the workspace root, and the vault is registered in Obsidian as "AIOS" (`/Users/fitlabhawaii/AIOS`). This means every markdown note the AIOS produces (context, GTD, docs, outputs, plans) is a live Obsidian note — single source of truth, no syncing or duplication.

- **`Home.md`** is the vault landing page — a dashboard of `[[wikilinks]]` to the key notes. Keep its links current when major files are added.
- Use Obsidian-style `[[wikilinks]]` when cross-referencing notes so the graph and backlinks work.
- **Excluded folders** (hidden from Obsidian to keep the vault clean, set in `.obsidian/app.json` → `userIgnoreFilters`): `.claude/`, `.venv/`, `scripts/`, `module-installs/`, `credentials/`, `data/`, `config/`, `node_modules/`, `.git/`, `shares/`. These still exist on disk — Claude uses them behind the scenes.
- `.obsidian/workspace.json` (per-machine UI state) is gitignored; shared settings (`app.json`, `appearance.json`, etc.) are committed.

---

## Commands

### /install [module-path]

**Purpose:** Install an AIOS module into this workspace.

Point it at a module folder in `module-installs/` and Claude walks you through the guided setup. Each module adds a new capability to your AIOS.

Example: `/install module-installs/context-os`

### /prime

**Purpose:** Initialize a new session with full context awareness.

Run this at the start of every session. Claude will:

1. Read CLAUDE.md and context files
2. Summarize understanding of the user, workspace, and goals
3. Confirm readiness to assist

### /create-plan [request]

**Purpose:** Create a detailed implementation plan before making changes.

Use when adding new functionality, commands, scripts, or making structural changes. Produces a thorough plan document in `plans/` that captures context, rationale, and step-by-step tasks.

Example: `/create-plan add a competitor analysis command`

### /implement [plan-path]

**Purpose:** Execute a plan created by /create-plan.

Reads the plan, executes each step in order, validates the work, and updates the plan status.

Example: `/implement plans/2026-01-28-competitor-analysis-command.md`

### /commit [optional message]

**Purpose:** Save your work to Git, update documentation, and keep the changelog current — in one command (InfraOS).

Creates a clean, structured Git commit, checks whether any `docs/` need creating or updating, and appends an entry to `HISTORY.md`. Run this at the end of a work session or after completing meaningful work, then push to back up to GitHub.

Example: `/commit` or `/commit feat: add competitor analysis command`

### /update-data

**Purpose:** Refresh the data warehouse on demand (DataOS).

Runs `.venv/bin/python scripts/collect.py` to pull fresh numbers from all connected sources, then regenerates `context/group/key-metrics.md`. A daily job also does this automatically each morning, so you normally only run this when you want up-to-the-minute figures.

Example: run `.venv/bin/python scripts/collect.py` (all sources) or `... collect.py --sources stripe` (one source)

### /drive [request]

**Purpose:** Work with the connected Google Drive in plain English (Drive integration).

Reads business docs for context, pulls Google Sheet data to CSV, pushes generated reports to a Drive folder, or syncs a Drive folder locally — via `scripts/drive_cli.py`. Connected as `fitlabhawaii@gmail.com`; token in `credentials/` (gitignored).

Example: `/drive pull the July memberships tab into a CSV` or `/drive push the latest sales overview to AIOS Reports`

### /process

**Purpose:** Empty your GTD inbox to zero using the decision tree (ProductivityOS).

Walks each `gtd/inbox.md` item through: actionable? → project? → next action → do (2-min rule) / delegate (waiting-for) / defer (next-actions by context) / someday / trash. Refreshes the dashboard after.

### /review

**Purpose:** Guided weekly GTD review (ProductivityOS).

A 4-phase review — empty inbox, walk all lists, surface stuck projects, brainstorm — to keep the system trustworthy. Run weekly (Friday is the classic time).

### /canva [request]

**Purpose:** Work with the connected Canva account (Canva integration).

Lists and exports designs (PNG/PDF/etc. into `outputs/canva/`) via `scripts/canva_cli.py`. Autofill/brand templates require Canva Teams/Enterprise (account is on Pro).

Example: `/canva export the spa services flyer as PDF`

### /brainstorm [topic]

**Purpose:** Scan the workspace and find what to build or automate next (Slash Command Toolkit).

Reads your tasks, processes, and current setup to surface manual work worth automating, ranks opportunities by impact × feasibility, deep-dives the top pick, and points you to `/explore` or `/implement`. Run without arguments to scan everything, or with a topic to focus on a specific area.

Example: `/brainstorm` or `/brainstorm memberships`

### /explore [idea]

**Purpose:** Shape a rough idea into a clear, buildable concept (Slash Command Toolkit).

Interactive 5-stage session — Discovery → Research → Shape → Scope → Output — that walks an idea into a scoped feature doc saved in `plans/` (`explore-YYYY-MM-DD-{name}.md`), ready to hand to `/create-plan` or `/implement`.

Example: `/explore a daily summary of what I accomplished today`

### /share [system or feature]

**Purpose:** Package a system or feature from your workspace for sharing.

Deep-dives the code first to fully understand it, then produces a self-contained, beginner-friendly package with a Claude-guided installer (INSTALL.md + README.md + scripts). The recipient gives the folder to Claude Code and says "read INSTALL.md and set this up" — Claude walks them through everything step by step. Runs a 6-stage interactive flow: Research → Scope → Frame → Write → Validate → Deliver. Outputs to `shares/`.

Example: `/share the daily brief system`

---

## Data (DataOS)

This workspace has a local **SQLite data warehouse** at `data/data.db`. Business metrics are collected into it as daily snapshots by the collectors in `scripts/` (`collect_*.py`), orchestrated by `scripts/collect.py`.

- **`context/group/key-metrics.md`** is auto-generated from the database and loaded by `/prime` every session — so Claude always knows the current numbers.
- **For deeper analysis**, Claude can query `data/data.db` directly via Python's sqlite3 module (`sqlite3.connect("data/data.db")`). Load `reference/data-access.md` first for all table schemas and example SQL.
- **Snapshot model:** most sources report current totals, so we store one row per day and compute changes by comparing dates. This is why daily collection matters.
- **Graceful degradation:** a collector with missing credentials is skipped, never breaking the rest of the pipeline.

---

## Telegram Bot (@fitlabhawaiibot)

A phone-first command center. Long-polls Telegram and answers from the same
business context `/prime` loads. Credentials live in `.env`
(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).

- **`scripts/telegram_bot.py`** — the interactive bot. Commands: `/metrics`
  (current numbers), `/brief` (on-demand morning summary), `/reset`, `/help`;
  any other text is answered by Claude (`claude-opus-4-8`) with full context.
- **`scripts/telegram_brief.py`** — composes the morning brief and sends it to
  `TELEGRAM_CHAT_ID`. Run on demand or schedule it after the daily collection.
- **`scripts/telegram_setup.py`** — one-time: message the bot, then run this to
  capture your chat id into `.env`.
- **`scripts/telegram.py`** — shared helpers (Telegram API + `ask_claude`).
- **Security:** only `TELEGRAM_CHAT_ID` is served; other chats are refused.
- **Always-on (launchd):** the bot runs as `com.aios.telegram-bot` (KeepAlive,
  starts on login) and the brief as `com.aios.telegram-brief` (daily 6:15 AM,
  after the 6 AM data collect). Plists live in `config/` and are installed to
  `~/Library/LaunchAgents/`. Logs: `data/telegram-bot.log`,
  `data/telegram-brief.log`.
  - Restart the bot: `launchctl unload ~/Library/LaunchAgents/com.aios.telegram-bot.plist && launchctl load ~/Library/LaunchAgents/com.aios.telegram-bot.plist`
  - Run the bot by hand instead: `.venv/bin/python scripts/telegram_bot.py`

---

## Getting Started

**First time?** Start here:

1. Run `/install module-installs/context-os` — this builds your context layer (Claude learns your business)
2. After ContextOS is done, run `/prime` — verify Claude knows you
3. Install more modules from `module-installs/` as you're ready

**Returning?** Run `/prime` at the start of every session.

---

## Critical Instruction: Maintain This File

**Whenever Claude makes changes to the workspace, Claude MUST consider whether CLAUDE.md needs updating.**

After any change — adding commands, scripts, workflows, or modifying structure — ask:

1. Does this change add new functionality users need to know about?
2. Does it modify the workspace structure documented above?
3. Should a new command be listed?
4. Does context/ need new files to capture this?

If yes to any, update the relevant sections. This file must always reflect the current state of the workspace so future sessions have accurate context.

---

## Session Workflow

1. **Start**: Run `/prime` to load context
2. **Work**: Use commands or direct Claude with tasks
3. **Install modules**: Use `/install` to add new AIOS capabilities
4. **Plan changes**: Use `/create-plan` before significant additions
5. **Execute**: Use `/implement` to execute plans
6. **Share**: Use `/share` to package systems for team, clients, or community
7. **Maintain**: Claude updates CLAUDE.md and context/ as the workspace evolves

---

## Notes

- Keep context minimal but sufficient — avoid bloat
- Plans live in `plans/` with dated filenames for history
- Outputs are organized by type/purpose in `outputs/`
- Reference materials go in `reference/` for reuse
- API keys go in `.env` — never commit this file
