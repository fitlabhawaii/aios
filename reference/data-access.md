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
| Jane App (sales) | `jane_sales` | `scripts/collect_jane.py` | Every sales line item — service/product, patient, staff, amounts, status |
| _(Instagram/Meta added when connected)_ | | | |

## Table Schemas

### `jane_sales`
One row per invoice line item, imported from a Jane **Sales** report export (`.xlsx`/`.csv`).
Primary key: `invoice_number` (unique per line). Re-importing a fresh full export upserts,
so the table always reflects the latest export.

| Column | Type | Description |
|--------|------|-------------|
| `invoice_number` | TEXT | Unique line-item id (PK), e.g. `14-P01` |
| `date` | TEXT | Purchase day (YYYY-MM-DD) — use this for all grouping/trends |
| `location` | TEXT | Clinic location |
| `purchase_date` | TEXT | Full purchase timestamp as exported |
| `invoice_date` | TEXT | Full invoice timestamp |
| `patient_guid` | TEXT | Stable patient id — use for distinct-patient counts |
| `patient` | TEXT | Patient name (**PHI — local only**) |
| `item` | TEXT | Service or product name (e.g. `Dysport`, `VIP Membership`) |
| `staff_member` | TEXT | Provider (may be blank for product-only lines) |
| `payer` | TEXT | Payer type (usually `Patient`) |
| `income_category` | TEXT | `Treatment Income` or `Product Income` |
| `details` | TEXT | Free text, e.g. `Quantity: 16` |
| `status` | TEXT | `paid`, `no_charge`, `refunded`, `unpaid`, etc. |
| `subtotal` | REAL | Pre-tax amount |
| `sales_tax` | REAL | Tax amount |
| `total` | REAL | Invoiced total |
| `collected` | REAL | **Cash actually collected — use this for revenue** |
| `balance` | REAL | Outstanding balance |
| `imported_at` | TEXT | UTC timestamp of import |

Notes:
- Use **`collected`** for revenue (actual cash). `total` is gross invoiced.
- `no_charge` rows (bundled follow-ups/consults) have `collected = 0` — they don't inflate revenue but do count as visits.
- Negative `total`/`collected` = refunds.

### `collection_log`
Tracks every collection run: `collected_at`, `source`, `status` (success/skipped/error), `reason`, `records_written`.

## Common Queries

```sql
-- Revenue collected this month vs last month
SELECT substr(date,1,7) AS month, ROUND(SUM(collected),2) AS revenue,
       COUNT(DISTINCT patient_guid) AS patients
FROM jane_sales GROUP BY month ORDER BY month DESC LIMIT 12;

-- This week's sales (Mon–today)
SELECT ROUND(SUM(collected),2) AS revenue, COUNT(DISTINCT patient_guid) AS patients
FROM jane_sales
WHERE date >= date('now','localtime','weekday 1','-7 days');

-- Top services by revenue, last 90 days
SELECT item, ROUND(SUM(collected),2) AS revenue, COUNT(*) AS times_sold
FROM jane_sales WHERE date >= date('now','localtime','-90 days')
GROUP BY item ORDER BY revenue DESC LIMIT 15;

-- Revenue by provider, last full month
SELECT staff_member, ROUND(SUM(collected),2) AS revenue
FROM jane_sales
WHERE date >= date('now','localtime','start of month','-1 month')
  AND date <  date('now','localtime','start of month')
GROUP BY staff_member ORDER BY revenue DESC;

-- Treatment vs Product income mix, this month
SELECT income_category, ROUND(SUM(collected),2) AS revenue
FROM jane_sales WHERE date >= date('now','localtime','start of month')
GROUP BY income_category;

-- Lapsed patients: last visit > 60 days ago (basis for monthly follow-up outreach)
SELECT patient, patient_guid, MAX(date) AS last_visit
FROM jane_sales GROUP BY patient_guid
HAVING last_visit < date('now','localtime','-60 days')
ORDER BY last_visit DESC;
```

## Data Collection

- **Import fresh Jane data:** export a Sales report from Jane, drop the `.xlsx`/`.csv` into `data/imports/jane/`, then run collection. The collector reads the newest file in that folder.
- **Run all sources:** `.venv/bin/python scripts/collect.py`
- **Run one source:** `.venv/bin/python scripts/collect.py --sources jane`
- **Regenerate metrics only:** `.venv/bin/python scripts/generate_metrics.py`
- **Logs:** `data/collect.log` (once the daily job is set up)
- **Daily automation:** a launchd job (`config/com.aios.data-collect.plist`) re-runs collection each morning, keeping the weekly/monthly windows in `key-metrics.md` current.

## Privacy (PHI)

`jane_sales` contains patient names — protected health information. It lives only in the local
database and `data/imports/`, both gitignored. Never commit, upload, or paste this data externally.
