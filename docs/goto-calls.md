# Integration: GoTo Connect Call History

> Pulls FitLab's phone call history from GoTo Connect into the warehouse (call volume, inbound/outbound, missed).

## Overview

OAuth connection to GoTo Connect (account `fitlabhawaii@gmail.com` / Kiani Kaaua). Fetches
call-event report summaries into `goto_calls`, powering the "Phone Calls" section of
`key-metrics.md`. Refreshes daily via the launchd collection job.

## Key Files

| File | Purpose |
|------|---------|
| `scripts/goto.py` | OAuth token load/refresh, account-key discovery, report_summaries() |
| `scripts/goto_auth.py` | One-time OAuth authorization (loopback flow on :8080) |
| `scripts/collect_goto_calls.py` | Collector — 90-day trailing window in 30-day chunks |
| `credentials/goto-token.json` | Token (gitignored) |

## Configuration (.env)

| Var | Notes |
|-----|-------|
| `GOTO_CLIENT_ID` / `GOTO_CLIENT_SECRET` | OAuth client from developer.goto.com |
| `GOTO_REDIRECT_URI` | `http://localhost:8080` (must be registered on the client) |
| `GOTO_ACCOUNT_KEY` | `2666010478388802806` (auto-discoverable via admin/me) |

## How It Works

1. `goto_auth.py` runs the auth-code flow → stores refresh token
2. `goto.get_access_token()` refreshes the 1-hour access token as needed
3. Collector pulls `GET api.goto.com/call-events-report/v1/report-summaries` per 30-day chunk (API caps ~31 days), paginating via `nextPageMarker`
4. Upserts by `call_id`; `generate_metrics.section_goto_calls` builds weekly/monthly volume

## Endpoints & Scopes

- Auth: `https://authentication.logmeininc.com/oauth/authorize` + `/oauth/token`
- Call reports: `GET https://api.goto.com/call-events-report/v1/report-summaries` (scope `cr.v1.read`)
- Account key: `GET https://api.getgo.com/admin/rest/v1/me`

## Gotchas

- **Max query window ~31 days** — collector chunks at 30. Requesting 35+ days returns 400.
- **Missed calls:** the dial plan auto-answers, so `callAnswered` isn't a reliable "answered by human" signal. Use `outcome` — most inbound are `LEFT_DIAL_PLAN`; only explicit `MISSED` is flagged. True missed-call analytics need the detailed Call Events API.
- **SMS/texts:** GoTo exposes messaging via real-time webhooks only (no history pull) — not collected here; would need a public webhook endpoint.
- **PHI:** caller names/numbers are patient contact data — DB is gitignored, keep it local.
- Token access expires hourly; refresh token handles renewal. App may be in testing mode — re-run `goto_auth.py` if refresh fails.

## Dependencies

- **Depends on:** GoTo OAuth token, `requests`, DataOS framework
- **Used by:** `key-metrics.md` Phone Calls section; future missed-call / response-time analysis

## History

| Date | Change |
|------|--------|
| 2026-07-08 | Initial build — OAuth flow, call-history collector, weekly/monthly metrics |
