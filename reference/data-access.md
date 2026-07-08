# Data Access Reference

> How to query the DataOS warehouse. Load this when you need to run SQL or analyze
> trends beyond what's in `context/group/key-metrics.md`.

## SQLite Data Warehouse

- **Location:** `data/data.db` (SQLite)
- **Connect (Python):**
  ```python
  import sqlite3
  conn = sqlite3.connect("data/data.db")
  conn.row_factory = sqlite3.Row
  rows = conn.execute("SELECT * FROM fx_rates ORDER BY date DESC LIMIT 5").fetchall()
  ```
- Claude can run SQL directly in a session — no need to write a script for one-off questions.

## Connected Data Sources

| Source | Table(s) | Collection Script | What It Tracks |
|--------|----------|-------------------|----------------|
| FX Rates (starter) | `fx_rates` | `scripts/collect_fx_rates.py` | USD exchange rates (proves the pipeline; not business-critical for FitLab) |
| _(more sources added as connected in the discovery workshop)_ | | | |

## Table Schemas

### `fx_rates`
| Column | Type | Description |
|--------|------|-------------|
| `date` | TEXT | Rate date (YYYY-MM-DD) |
| `currency` | TEXT | Currency code (e.g. EUR, GBP) |
| `rate` | REAL | Rate from USD to this currency |
| `base` | TEXT | Base currency (USD) |
| `collected_at` | TEXT | UTC timestamp of collection |

Primary key: `(date, currency)`

### `collection_log`
Tracks every collection run: `collected_at`, `source`, `status` (success/skipped/error), `reason`, `records_written`. Useful for debugging what ran and when.

## Common Queries

```sql
-- Latest snapshot for a source
SELECT * FROM fx_rates WHERE date = (SELECT MAX(date) FROM fx_rates);

-- Collection health over the last week
SELECT source, status, COUNT(*) AS runs
FROM collection_log
WHERE collected_at >= datetime('now', '-7 days')
GROUP BY source, status;

-- All tables in the warehouse
SELECT name FROM sqlite_master WHERE type='table'
AND name NOT LIKE 'sqlite_%' ORDER BY name;
```

*(As real sources are connected, add per-source trend and month-over-month queries here — e.g. revenue MTD vs last month, appointment volume by week.)*

## Data Collection

- **Run all sources:** `.venv/bin/python scripts/collect.py`
- **Run one source:** `.venv/bin/python scripts/collect.py --sources fx_rates`
- **Regenerate metrics only:** `.venv/bin/python scripts/generate_metrics.py`
- **Logs:** `data/collect.log` (once the daily job is set up)
- **Daily automation:** a launchd job (`config/com.aios.data-collect.plist`) runs collection each morning.
