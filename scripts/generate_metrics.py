"""
DataOS — Key Metrics Generator

Reads the database and generates a human-readable key-metrics.md file.
This file is loaded by your /prime command so your AI always has fresh data.

Automatically discovers which tables exist and generates sections for each.
Claude will customize this file during installation to match your data sources.

Usage:
    python scripts/generate_metrics.py
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"
OUTPUT_PATH = WORKSPACE_ROOT / "context" / "group" / "key-metrics.md"


# --- Formatting helpers ---

def fmt_number(value, prefix="", suffix=""):
    """Format a number with commas. Returns 'No data' if None."""
    if value is None:
        return "No data"
    if isinstance(value, float):
        return f"{prefix}{value:,.0f}{suffix}"
    return f"{prefix}{value:,}{suffix}"


def fmt_currency(value, symbol="$"):
    """Format currency value with symbol and commas."""
    if value is None:
        return "No data"
    return f"{symbol}{value:,.0f}"


def fmt_pct(value):
    """Format a percentage to 1 decimal place."""
    if value is None:
        return "No data"
    return f"{value:.1f}%"


def query_one(conn, sql):
    """Query helper — returns first row as dict or None."""
    try:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def query_all(conn, sql):
    """Query helper — returns all rows as list of dicts."""
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []


def table_exists(conn, name):
    """Check if a table exists."""
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


# ============================================================
# SECTION GENERATORS
# Each function returns a list of markdown lines for its section.
# Claude will add custom section functions here during installation.
# ============================================================


def _pct_change(cur, prev):
    """Signed percent change as a short string, or '—' if no baseline."""
    if not prev:
        return "—"
    return f"{(cur - prev) / prev * 100:+.0f}%"


def _sum_between(conn, start, end):
    """Return (collected, line_items, distinct_patients) for date in [start, end]."""
    row = conn.execute(
        "SELECT COALESCE(SUM(collected),0) s, COUNT(*) n, "
        "COUNT(DISTINCT patient_guid) p FROM jane_sales "
        "WHERE date >= ? AND date <= ?",
        (start, end),
    ).fetchone()
    return (row["s"] or 0.0), (row["n"] or 0), (row["p"] or 0)


def section_jane_sales(conn):
    """Jane App sales — weekly + monthly overview with WoW / MoM comparisons."""
    if not table_exists(conn, "jane_sales"):
        return []

    today = datetime.now().date()
    iso = "%Y-%m-%d"

    # Week windows (Mon–Sun)
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)

    # Month windows
    month_start = today.replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    days_in = (today - month_start).days
    lm_same_point = last_month_start + timedelta(days=days_in)  # fair MTD comparison

    tw_s, _, tw_p = _sum_between(conn, this_week_start.strftime(iso), today.strftime(iso))
    lw_s, _, lw_p = _sum_between(conn, last_week_start.strftime(iso), last_week_end.strftime(iso))
    tm_s, tm_n, tm_p = _sum_between(conn, month_start.strftime(iso), today.strftime(iso))
    lm_pt_s, _, _ = _sum_between(conn, last_month_start.strftime(iso), lm_same_point.strftime(iso))
    lm_full_s, lm_full_n, lm_full_p = _sum_between(
        conn, last_month_start.strftime(iso), last_month_end.strftime(iso))

    lines = [
        "## Sales (Jane)",
        "",
        f"> Source: Jane sales export | Data through {today.strftime(iso)}",
        "",
        "| Window | Collected | Patients | vs Prior |",
        "|--------|-----------|----------|----------|",
        f"| This week (Mon {this_week_start.strftime('%b %-d')}–today) | "
        f"{fmt_currency(tw_s)} | {tw_p} | {_pct_change(tw_s, lw_s)} WoW |",
        f"| Last week ({last_week_start.strftime('%b %-d')}–{last_week_end.strftime('%b %-d')}) | "
        f"{fmt_currency(lw_s)} | {lw_p} | — |",
        f"| This month ({month_start.strftime('%b')} MTD) | "
        f"{fmt_currency(tm_s)} | {tm_p} | {_pct_change(tm_s, lm_pt_s)} vs same point last mo |",
        f"| Last month ({last_month_start.strftime('%b %Y')}) | "
        f"{fmt_currency(lm_full_s)} | {lm_full_p} | — |",
        "",
    ]

    # Trailing 6 months
    trailing = query_all(conn, """
        SELECT substr(date,1,7) ym, SUM(collected) s,
               COUNT(DISTINCT patient_guid) p
        FROM jane_sales WHERE date IS NOT NULL
        GROUP BY ym ORDER BY ym DESC LIMIT 6
    """)
    if trailing:
        lines.append("### Trailing 6 Months")
        lines.append("| Month | Collected | Patients |")
        lines.append("|-------|-----------|----------|")
        for r in trailing:
            lines.append(f"| {r['ym']} | {fmt_currency(r['s'])} | {r['p']} |")
        lines.append("")

    # Top services this month
    top = query_all(conn, f"""
        SELECT item, SUM(collected) s, COUNT(*) n
        FROM jane_sales WHERE date >= '{month_start.strftime(iso)}'
        GROUP BY item ORDER BY s DESC LIMIT 5
    """)
    if top and tm_s > 0:
        lines.append(f"### Top Services — {month_start.strftime('%b %Y')} (MTD)")
        lines.append("| Service | Collected | Count |")
        lines.append("|---------|-----------|-------|")
        for r in top:
            lines.append(f"| {r['item']} | {fmt_currency(r['s'])} | {r['n']} |")
        lines.append("")

    return lines


# --- CUSTOMIZATION ZONE ---
# Claude adds your custom section functions below during installation.
# Each follows the same pattern:
#
#   def section_NAME(conn):
#       if not table_exists(conn, "TABLE_NAME"):
#           return []
#       lines = ["## Section Title", "| Metric | Value | As Of |", ...]
#       row = query_one(conn, "SELECT ... FROM TABLE_NAME ORDER BY date DESC LIMIT 1")
#       if row:
#           lines.append(f"| Metric | {fmt_number(row['value'])} | {row['date']} |")
#       return lines


# ============================================================
# MAIN GENERATOR
# ============================================================

# Register all section functions here. Claude adds new ones during install.
SECTIONS = [
    section_jane_sales,
    # section_instagram,   # added when Instagram/Meta is connected
]


def generate(conn):
    """Generate the key-metrics markdown content."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Key Metrics",
        "",
        f"> Auto-generated from database. Last updated: {today}",
        f"> Source: `data/data.db` | Regenerate: `python scripts/generate_metrics.py`",
        "",
    ]

    # Run all registered section generators
    for section_fn in SECTIONS:
        try:
            section_lines = section_fn(conn)
            if section_lines:
                lines.extend(section_lines)
        except Exception as e:
            lines.append(f"<!-- Error in {section_fn.__name__}: {e} -->")
            lines.append("")

    # Data freshness table (auto-discovers all tables)
    lines.append("## Data Freshness")
    lines.append("| Source | Latest Record | Status |")
    lines.append("|--------|---------------|--------|")

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name != 'collection_log' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()

    for t in tables:
        name = t["name"]
        try:
            row = conn.execute(f"SELECT MAX(date) as d FROM {name}").fetchone()
            if row and row["d"]:
                lines.append(f"| {name} | {row['d']} | Connected |")
            else:
                lines.append(f"| {name} | — | Empty |")
        except Exception:
            lines.append(f"| {name} | — | No date column |")

    lines.append("")
    return "\n".join(lines)


def main():
    """Generate key-metrics.md from the database."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run collection first: python scripts/collect.py")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    content = generate(conn)
    conn.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content)
    print(f"Key metrics written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
