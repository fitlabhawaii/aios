# Drive

> Work with the connected Google Drive (read docs, pull spreadsheet data, push reports, sync folders).

## Variables

request: $ARGUMENTS (plain-English description of what to do with Drive)

---

## Instructions

The workspace is connected to the user's Google Drive via OAuth (`scripts/gdrive.py`,
authorized token in `credentials/gdrive-token.json`). Use the CLI wrapper
`scripts/drive_cli.py` for common operations, or import `gdrive` directly for custom logic.

Always run Python via the venv: `.venv/bin/python`.

### Common operations

**List a folder** (accepts a Drive URL, id, or `root`):
```bash
.venv/bin/python scripts/drive_cli.py list <folder_url|id|root>
```

**Read docs for context** — export every Doc/file in a folder to local files
(Google Docs become markdown). Pull into `context/import/drive/` then read them:
```bash
.venv/bin/python scripts/drive_cli.py pull-docs <folder_url> --dest context/import/drive
```

**Pull spreadsheet data** — dump a Google Sheet to CSV. For multi-tab sheets, pass a
range that includes the tab name, e.g. `--range "'JULY 2026'!A1:H200"`:
```bash
.venv/bin/python scripts/drive_cli.py sheet <sheet_url> --range "A1:Z9999" --out data/imports/<name>.csv
```

**Push a report out** — upload a local file into a Drive folder (e.g. the "AIOS Reports"
folder). Good for sharing generated overviews with the team:
```bash
.venv/bin/python scripts/drive_cli.py push <local_file> <folder_url>
```

**Sync a folder** — download everything in a Drive folder to a local directory:
```bash
.venv/bin/python scripts/drive_cli.py sync <folder_url> <local_dir>
```

### Guidance

- If the user names a file/folder rather than giving a URL, list first to find its id.
- Multi-tab sheets: check tab names via `gdrive.sheets_service()` metadata before reading.
- **PHI/privacy:** some Drive files (membership lists, appointment exports, consent forms)
  contain patient info. `data/imports/` and `context/import/drive/` are gitignored — Drive
  pulls land there safely. Only promote a specific doc into committed `context/` if you're
  sure it has no patient/sensitive data. Never commit or share patient data.
- If a command fails with an auth error, the token may have expired — re-run
  `.venv/bin/python scripts/gdrive_auth.py`.

### Execution

Interpret the user's request, choose the right command(s), run them, and report what you
did (files pulled/pushed, rows read, links). Keep it plain-English.
