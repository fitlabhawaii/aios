# Integration: Canva Connect API

> OAuth-connected Canva — list and export designs (autofill gated to Enterprise).

## Overview

Connect API integration (OAuth 2.0 + PKCE) for the FitLab Canva account (team `oBY1DBbGkZTo8kwbL6W7xg`).
Lists designs and exports them to PNG/PDF/etc. Brand-template autofill is coded but requires
Canva Teams/Enterprise — the account is on **Pro**, so autofill is unavailable (0 brand templates).

## Key Files

| File | Purpose |
|------|---------|
| `scripts/canva.py` | OAuth (PKCE) token mgmt + list/export/brand-template/autofill helpers |
| `scripts/canva_auth.py` | One-time OAuth authorization (loopback :8080/callback) |
| `scripts/canva_cli.py` | CLI — `list`, `export`, `templates`, `autofill` |
| `credentials/canva-token.json` | Token (gitignored) |

## Configuration (.env)

| Var | Notes |
|-----|-------|
| `CANVA_CLIENT_ID` / `CANVA_CLIENT_SECRET` | From canva.com/developers → Your integrations |
| `CANVA_REDIRECT_URI` | `http://127.0.0.1:8080/callback` (Canva requires 127.0.0.1, **not** localhost) |

## Common Operations

```bash
.venv/bin/python scripts/canva_cli.py list --limit 50
.venv/bin/python scripts/canva_cli.py export <design_id> --format png --dest outputs/canva
```

## Endpoints & Scopes

- Auth: `https://www.canva.com/api/oauth/authorize` (PKCE S256) + token `https://api.canva.com/rest/v1/oauth/token`
- API base: `https://api.canva.com/rest/v1` (`/designs`, `/exports`, `/brand-templates`, `/autofills`, `/users/me`)
- Scopes: design meta/content read+write, asset:read, folder:read, profile:read, brandtemplate read

## Gotchas

- **Redirect must be `127.0.0.1`, not `localhost`** — Canva rejects localhost.
- **Creating an integration requires account MFA** — a Google-SSO account needs a password/passkey + MFA first.
- **Autofill/brand templates need Teams/Enterprise** — not available on Pro (returns 0 templates).
- **Export is async** — create job → poll → download URLs (handled in `export_design`).
- Exports land in gitignored `outputs/canva/` (regenerable; may contain sensitive design content).
- Access token ~4h; refresh token rotates (handled automatically).

## Dependencies

- **Depends on:** Canva OAuth token, `requests`
- **Used by:** on-demand design export; content workflows

## History

| Date | Change |
|------|--------|
| 2026-07-08 | Initial build — PKCE OAuth, list/export designs, CLI, /canva command |
