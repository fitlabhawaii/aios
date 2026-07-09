# Current Data

> Current-state snapshot. **Live metrics are auto-generated in `context/group/key-metrics.md`** (loaded by `/prime`); this file holds the qualitative state and where data comes from.

---

## How This Connects

- **business-info.md** provides organizational context
- **personal-info.md** defines what you're responsible for
- **strategy.md** outlines what you're optimizing toward
- **This file** + **key-metrics.md** give Claude the numbers behind the narrative

---

## Live Metrics → see `context/group/key-metrics.md`

Auto-refreshed daily from the local warehouse (`data/data.db`):
- **Sales (Jane):** weekly/monthly collected revenue, patients, trailing 6 months, top services
- **Phone (GoTo):** call volume by week/month, inbound/outbound, missed

Rough baseline (Jan–Jun 2026): ~$75K–$105K collected/month, ~170–225 patients/month; ~110–380 calls/month.

## Current State (2026-07-08)

- **AIOS build in progress** — connected: Jane sales, GoTo calls, Google Drive, Canva. Context layer just enriched from Drive docs.
- **Manual workflows still in place:** membership tracking/reconciliation (Sheet ↔ Jane), lead follow-up logging, weekly email + IG content.
- **Not yet connected:** GA4 (website traffic), form submissions, Instagram metrics, membership/inventory sheets as live data sources.
- **Data still to fill:** confirmed owner identity & top priorities (see personal-info / strategy), target numbers.

## Data Sources

| Source | Status | Notes |
| ------ | ------ | ----- |
| Jane App (sales) | ✅ Connected | Manual XLSX export → `data/imports/jane/` |
| GoTo Connect (calls) | ✅ Connected | OAuth, daily pull |
| Google Drive/Sheets | ✅ Connected | `drive_cli.py`; membership & inventory sheets readable |
| Canva | ✅ Connected | list/export designs |
| Mailchimp, Instagram, GA4 | ⬜ Not connected | Email/social/traffic — future |

---

## Automation Note

_`key-metrics.md` refreshes via the daily launchd job. As more sources connect (memberships sheet, GA4), add collectors in `scripts/` and sections in `generate_metrics.py`._

---

_Update the qualitative state as things change; the numbers refresh themselves._
