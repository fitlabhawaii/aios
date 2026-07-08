# Integration: Jane Sales Pipeline

> Ingests FitLab's Jane App sales exports into the local warehouse and powers the weekly/monthly sales overview in key-metrics.md.

## Overview

Jane App has no public data API, so revenue data enters via **manual CSV/XLSX export**. You export a Sales report from Jane, drop it in `data/imports/jane/`, and the collector parses every line item into the `jane_sales` table. Runs daily via launchd (keeps the metric windows current even between exports).

## Key Files

| File | Purpose |
|------|---------|
| `scripts/collect_jane.py` | Reads the newest export in `data/imports/jane/`, upserts into `jane_sales` |
| `scripts/generate_metrics.py` | `section_jane_sales()` builds the weekly/monthly overview |
| `data/imports/jane/` | Drop Jane exports here (gitignored — contains PHI) |
| `reference/data-access.md` | Full `jane_sales` schema + example SQL |
| `config/com.aios.data-collect.plist` | launchd job, runs collection at 6 AM daily |

## Data Tables

| Table | Key Columns | Description |
|-------|-------------|-------------|
| `jane_sales` | `invoice_number` (PK), `date`, `collected`, `item`, `patient_guid`, `income_category` | One row per invoice line item |

## How It Works

1. User exports a Sales report from Jane (Reports → Sales → Export) → `.xlsx` or `.csv`
2. File is dropped into `data/imports/jane/`
3. `collect_jane.py` reads the **newest** file, maps Jane's columns to db columns, parses dates/amounts
4. Upserts keyed on `invoice_number` — re-importing a full history export is idempotent
5. `generate_metrics.py` recomputes weekly (Mon–Sun) and monthly (MTD) windows with WoW/MoM deltas

## Refreshing the Data

Jane numbers only change when you export a fresh report. Recommended cadence: **export weekly**
(or monthly) with the full date range, drop it in, and the newest file wins. Then:
```bash
.venv/bin/python scripts/collect.py --sources jane
```

## Gotchas

- Use `collected` (cash) for revenue, not `total` (invoiced). See reference/data-access.md.
- `no_charge` rows are $0 (bundled follow-ups/consults) — count as visits, not revenue.
- Export is `.xlsx` from Jane → requires `openpyxl` (in requirements.txt).
- **PHI:** `jane_sales` and `data/imports/` hold patient names — gitignored, never leave the Mac.

## Dependencies

- **Depends on:** manual Jane export, `openpyxl`, the DataOS framework (`db.py`, `collect.py`)
- **Used by:** `key-metrics.md` (loaded by `/prime`); future monthly follow-up outreach (phase 2)

## History

| Date | Change |
|------|--------|
| 2026-07-08 | Initial build — collector, jane_sales table, weekly/monthly metrics, daily launchd job |
