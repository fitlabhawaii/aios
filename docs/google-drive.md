# Integration: Google Drive

> OAuth-connected Google Drive — read docs, pull spreadsheet data, push reports, sync folders.

## Overview

Connected to `fitlabhawaii@gmail.com` (Kiani & Maddy) via an OAuth "Desktop app" client.
Full Drive read/write plus Google Sheets read. Used for four things: reading business docs
for context, pulling spreadsheet data, pushing generated reports back to Drive, and syncing
folders locally.

## Key Files

| File | Purpose |
|------|---------|
| `scripts/gdrive.py` | Core helper — auth, list, download/export, read sheet, upload |
| `scripts/gdrive_auth.py` | One-time OAuth authorization (creates the token) |
| `scripts/drive_cli.py` | CLI wrapper — `list`, `pull-docs`, `sheet`, `push`, `sync` |
| `.claude/commands/drive.md` | `/drive` command guidance |
| `credentials/gdrive-client-secret.json` | OAuth client (gitignored) |
| `credentials/gdrive-token.json` | Authorized token (gitignored) |

## How It Works

1. `gdrive_auth.py` runs the OAuth Desktop flow (`run_local_server`) → stores a refresh token
2. `gdrive.get_credentials()` loads and auto-refreshes that token for every call
3. Scopes: `auth/drive` (read+write) and `auth/spreadsheets.readonly`
4. Native Google types are exported: Docs → markdown, Sheets → CSV

## Common Operations

```bash
.venv/bin/python scripts/drive_cli.py list root
.venv/bin/python scripts/drive_cli.py sheet <sheet_url> --range "'JULY 2026'!A1:H200" --out data/imports/memberships.csv
.venv/bin/python scripts/drive_cli.py pull-docs <folder_url> --dest context/import/drive
.venv/bin/python scripts/drive_cli.py push context/group/key-metrics.md <folder_url>
.venv/bin/python scripts/drive_cli.py sync <folder_url> <local_dir>
```

## Known Drive Content (useful IDs)

| Item | Type | Notes |
|------|------|-------|
| AIOS Reports | folder | Created by AIOS — push generated reports here |
| FITLAB MEMBERSHIPS | sheet | Monthly tabs (e.g. `JULY 2026`) — patient, membership type, paid/unpaid |
| Inventory | sheet | Category / item / on-hand stock levels |
| Employee Treatment Log | sheet | — |

## Gotchas

- **Multi-tab sheets** need the tab name in the range: `--range "'JUNE 2026'!A1:H200"`. Default range hits the first tab only.
- `Fitlab rev` sheet is currently empty.
- Token can expire/revoke → re-run `gdrive_auth.py`.
- App is in "testing" mode in Google Cloud — only added test users can authorize; refresh tokens can expire after 7 days in testing mode (re-auth if so, or publish the app).
- **PHI:** membership lists, appointment exports, consent forms contain patient data. Drive pulls land in gitignored `data/imports/` or `context/import/drive/`. Never commit patient data.

## Dependencies

- **Depends on:** `google-api-python-client`, `google-auth`, `google-auth-oauthlib`; OAuth token
- **Used by:** context enrichment, spreadsheet-based data sources, report distribution

## History

| Date | Change |
|------|--------|
| 2026-07-08 | Initial build — OAuth connection, gdrive helper, drive_cli, /drive command |
