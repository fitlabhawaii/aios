"""
DataOS — Sales Dashboard Generator

Builds a standalone, self-contained HTML sales dashboard from the Jane data in
data/data.db. Pure HTML + CSS + inline SVG (no JS, no external files) so it opens
directly in a browser via file:// — just double-click outputs/jane-sales-dashboard.html.

All windows are dynamic (rolling weeks, latest full month, YTD), so it stays correct
as time passes. Regenerated automatically after each collection run.

Usage:
    .venv/bin/python scripts/generate_dashboard.py
"""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"
OUT_PATH = WORKSPACE_ROOT / "outputs" / "jane-sales-dashboard.html"

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def money(n):
    return "$" + format(round(n or 0), ",")


def money_k(n):
    n = n or 0
    return "$" + (f"{n/1000:.1f}k" if n < 10000 else f"{round(n/1000)}k")


def money_big(n):
    n = n or 0
    return f"${n/1_000_000:.2f}M" if n >= 1_000_000 else money_k(n).replace("k", "K")


def month_label(ym, short_year=False):
    y, m = ym.split("-")
    yy = y[2:] if short_year else y
    return f"{MONTHS[int(m)]} {yy}"


def q(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ── data ────────────────────────────────────────────────────────────────────

def gather(conn):
    today = date.today()
    iso = "%Y-%m-%d"

    monthly = q(conn, """
        SELECT substr(date,1,7) ym, ROUND(SUM(collected),2) rev,
               COUNT(DISTINCT patient_guid) pat,
               ROUND(SUM(CASE WHEN income_category='Product Income' THEN collected ELSE 0 END),2) prod
        FROM jane_sales WHERE date IS NOT NULL AND date<>''
        GROUP BY ym ORDER BY ym
    """)
    if not monthly:
        return None

    cur_ym = today.strftime("%Y-%m")
    # last full month = previous calendar month
    first_this = today.replace(day=1)
    last_full_end = first_this - timedelta(days=1)
    lf_ym = last_full_end.strftime("%Y-%m")
    by_ym = {m["ym"]: m for m in monthly}

    def rev_of(ym):
        return by_ym.get(ym, {}).get("rev", 0) or 0

    # YoY for last full month
    ly, lm = lf_ym.split("-")
    prev_year_ym = f"{int(ly)-1}-{lm}"
    lf_rev = rev_of(lf_ym)
    yoy = None
    if rev_of(prev_year_ym):
        yoy = round((lf_rev - rev_of(prev_year_ym)) / rev_of(prev_year_ym) * 100)

    # best month
    best = max(monthly, key=lambda m: m["rev"] or 0)
    # ytd + all time
    ytd = sum((m["rev"] or 0) for m in monthly if m["ym"].startswith(str(today.year)))
    all_time = sum((m["rev"] or 0) for m in monthly)
    mtd_rev = rev_of(cur_ym)

    kpis = {
        "last_full": {
            "label": f"{month_label(lf_ym)} (last full mo.)",
            "value": money(lf_rev),
            "delta": (f"▲ {yoy}%" if (yoy or 0) >= 0 else f"▼ {abs(yoy)}%") if yoy is not None else "",
            "dir": "up" if (yoy or 0) >= 0 else "down",
            "foot": f"vs {month_label(prev_year_ym)}" if yoy is not None else "",
        },
        "mtd": {"label": f"{MONTHS[today.month]} MTD", "value": money(mtd_rev),
                "chip": f"Through {MONTHS[today.month]} {today.day}"},
        "best": {"label": f"Best month · {month_label(best['ym'])}", "value": money(best["rev"]),
                 "foot": f"{best['pat']} patients · all-time high"},
        "ytd": {"label": f"{today.year} year-to-date", "value": money(ytd),
                "foot": f"Jan – {MONTHS[today.month]} {today.day} · all-time {money_big(all_time)}"},
    }

    # rolling last 6 weeks (Mon–Sun), ending with current week
    this_mon = today - timedelta(days=today.weekday())
    weeks = []
    for i in range(5, -1, -1):
        ws = this_mon - timedelta(days=7 * i)
        we = ws + timedelta(days=6)
        row = conn.execute(
            "SELECT ROUND(SUM(collected),2) rev, COUNT(DISTINCT patient_guid) pat "
            "FROM jane_sales WHERE date>=? AND date<=?",
            (ws.strftime(iso), we.strftime(iso))).fetchone()
        partial = we >= today
        endlbl = (f"{MONTHS[ws.month]} {ws.day}–{ws.day+6}" if ws.month == we.month
                  else f"{MONTHS[ws.month]} {ws.day}–{MONTHS[we.month]} {we.day}")
        weeks.append({"label": endlbl, "rev": row[0] or 0, "pat": row[1] or 0, "partial": partial})

    # deep-dive on last full month
    dd_start = last_full_end.replace(day=1).strftime(iso)
    dd_end = last_full_end.strftime(iso)
    services = q(conn, """
        SELECT item, ROUND(SUM(collected),2) rev, COUNT(*) n FROM jane_sales
        WHERE date>=? AND date<=? AND collected>0
        GROUP BY item ORDER BY rev DESC LIMIT 7""", (dd_start, dd_end))
    providers = q(conn, """
        SELECT staff_member nm, ROUND(SUM(collected),2) rev,
               COUNT(DISTINCT patient_guid) pat FROM jane_sales
        WHERE date>=? AND date<=? AND staff_member IS NOT NULL AND staff_member<>''
        GROUP BY staff_member ORDER BY rev DESC LIMIT 6""", (dd_start, dd_end))
    mixrow = conn.execute("""
        SELECT ROUND(SUM(CASE WHEN income_category='Treatment Income' THEN collected ELSE 0 END),2) treat,
               ROUND(SUM(collected),2) tot,
               COUNT(DISTINCT patient_guid) pat FROM jane_sales
        WHERE date>=? AND date<=?""", (dd_start, dd_end)).fetchone()
    dd_rev = mixrow[1] or 0
    dd_pat = mixrow[2] or 0
    treat_pct = round((mixrow[0] or 0) / dd_rev * 100) if dd_rev else 0

    deepdive = {
        "label": month_label(lf_ym),
        "sub": f"{money(dd_rev)} · {dd_pat} patients · {money(dd_rev/dd_pat) if dd_pat else '$0'} avg per patient",
        "services": [(s["item"], s["rev"]) for s in services],
        "providers": [(p["nm"], p["rev"], p["pat"]) for p in providers],
        "treat_pct": treat_pct,
    }

    return {
        "generated": today.strftime(iso),
        "range": f"{month_label(monthly[0]['ym'])} – {MONTHS[today.month]} {today.day}, {today.year}",
        "kpis": kpis, "monthly": monthly, "cur_ym": cur_ym, "peak_ym": best["ym"],
        "weeks": weeks, "deepdive": deepdive,
    }


# ── svg / html builders ───────────────────────────────────────────────────────

def build_monthly_svg(monthly, cur_ym, peak_ym):
    W, H, mL, mR, mT, mB = 960, 320, 40, 14, 22, 52
    iw, ih = W - mL - mR, H - mT - mB
    max_rev = max((m["rev"] or 0) for m in monthly) * 1.08 or 1
    max_pat = max((m["pat"] or 0) for m in monthly) * 1.10 or 1
    n = len(monthly)
    bw = iw / n
    bar = bw * 0.62
    s = ['<defs>',
         '<linearGradient id="gj" x1="0" y1="0" x2="0" y2="1">',
         '<stop offset="0" stop-color="var(--jade)"/><stop offset="1" stop-color="var(--jade-soft)"/></linearGradient>',
         '<linearGradient id="gp" x1="0" y1="0" x2="0" y2="1">',
         '<stop offset="0" stop-color="var(--jade-soft)"/><stop offset="1" stop-color="var(--surface-2)"/></linearGradient>',
         '</defs>']
    for g in range(5):
        y = mT + ih - (ih * g / 4)
        v = max_rev * g / 4
        s.append(f'<line class="grid-line" x1="{mL}" y1="{y:.1f}" x2="{W-mR}" y2="{y:.1f}"/>')
        s.append(f'<text class="axis-lbl" x="{mL-6}" y="{y+3:.1f}" text-anchor="end">{"0" if g==0 else money_k(v)}</text>')
    for i, m in enumerate(monthly):
        x = mL + i * bw + (bw - bar) / 2
        h = ih * (m["rev"] or 0) / max_rev
        y = mT + ih - h
        partial = m["ym"] == cur_ym
        peak = m["ym"] == peak_ym
        if partial:
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h:.1f}" rx="3" fill="url(#gp)" stroke="var(--muted)" stroke-dasharray="2 2" stroke-width="1" opacity=".9"/>')
        else:
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h:.1f}" rx="3" fill="{"var(--jade)" if peak else "url(#gj)"}"/>')
        if peak or partial:
            s.append(f'<text class="bar-val" x="{x+bar/2:.1f}" y="{y-5:.1f}" text-anchor="middle" fill="{"var(--down)" if partial else "var(--jade)"}">{money_k(m["rev"])}</text>')
        yy, mm = m["ym"].split("-")
        if mm == "01" or i == 0 or i == n - 1 or peak:
            lbl = f"{MONTHS[int(mm)]} {yy[2:]}"
            s.append(f'<text class="axis-lbl" x="{x+bar/2:.1f}" y="{mT+ih+16:.1f}" text-anchor="middle">{lbl}</text>')
    pts = " ".join(f'{mL+i*bw+bw/2:.1f},{mT+ih-(ih*(m["pat"] or 0)/max_pat):.1f}' for i, m in enumerate(monthly))
    s.append(f'<polyline points="{pts}" fill="none" stroke="var(--rose)" stroke-width="2" stroke-linejoin="round" opacity=".85"/>')
    for i, m in enumerate(monthly):
        cx = mL + i * bw + bw / 2
        cy = mT + ih - (ih * (m["pat"] or 0) / max_pat)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="var(--rose)"/>')
    return f'<svg viewBox="0 0 {W} {H}" style="min-width:640px" role="img" aria-label="Monthly revenue">{"".join(s)}</svg>'


def build_donut_svg(treat_pct):
    cx = cy = 60
    r = 44
    return (f'<svg viewBox="0 0 120 120" width="120" height="120" aria-label="Treatment vs product mix">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--rose)" stroke-width="16"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--jade)" stroke-width="16" '
            f'pathLength="100" stroke-dasharray="{treat_pct} {100-treat_pct}" stroke-dashoffset="0" '
            f'transform="rotate(-90 {cx} {cy})" stroke-linecap="butt"/></svg>')


def build_html(d):
    k = d["kpis"]
    kpi_html = f"""
      <div class="kpi"><span class="label">{k['last_full']['label']}</span>
        <span class="val tnum">{k['last_full']['value']}</span>
        <span class="foot"><span class="delta {k['last_full']['dir']}">{k['last_full']['delta']}</span> {k['last_full']['foot']}</span></div>
      <div class="kpi"><span class="label">{k['mtd']['label']}</span>
        <span class="val tnum">{k['mtd']['value']}</span>
        <span class="foot"><span class="chip partial">{k['mtd']['chip']}</span></span></div>
      <div class="kpi"><span class="label">{k['best']['label']}</span>
        <span class="val tnum">{k['best']['value']}</span>
        <span class="foot">{k['best']['foot']}</span></div>
      <div class="kpi"><span class="label">{k['ytd']['label']}</span>
        <span class="val tnum small">{k['ytd']['value']}</span>
        <span class="foot">{k['ytd']['foot']}</span></div>"""

    wk_max = max((w["rev"] or 0) for w in d["weeks"]) or 1
    weeks_html = "".join(
        f"""<div class="week{' partial' if w['partial'] else ''}">
          <span class="wk">{w['label']}{' · partial' if w['partial'] else ''}</span>
          <span class="wv tnum">{money(w['rev'])}</span>
          <div class="track"><i style="width:{round((w['rev'] or 0)/wk_max*100)}%"></i></div>
          <span class="wp tnum">{w['pat']} patients</span></div>""" for w in d["weeks"])

    dd = d["deepdive"]
    s_max = dd["services"][0][1] if dd["services"] else 1
    services_html = "".join(
        f"""<div class="row"><span class="nm">{nm}</span><span class="amt tnum">{money(rev)}</span>
          <span class="bar"><i style="width:{round(rev/s_max*100)}%"></i></span></div>"""
        for nm, rev in dd["services"])
    p_max = dd["providers"][0][1] if dd["providers"] else 1
    providers_html = "".join(
        f"""<div class="row"><span class="nm">{nm}</span><span class="amt tnum">{money(rev)}</span>
          <span class="bar"><i style="width:{round(rev/p_max*100)}%"></i></span></div>"""
        for nm, rev, pat in dd["providers"])

    monthly_svg = build_monthly_svg(d["monthly"], d["cur_ym"], d["peak_ym"])
    donut_svg = build_donut_svg(dd["treat_pct"])
    tp = dd["treat_pct"]

    return f"""<style>{CSS}</style>
<div class="wrap">
  <header>
    <div>
      <p class="eyebrow">FitLab Hawaii · Aesthetic &amp; Wellness</p>
      <h1>Sales Dashboard</h1>
      <p class="sub">Collected revenue from Jane · updated automatically</p>
    </div>
    <div class="range">Source <b>Jane sales export</b><br>{d['range']}</div>
  </header>

  <section aria-label="Key numbers"><div class="kpis">{kpi_html}</div></section>

  <section>
    <div class="sec-head"><h2>Monthly collected revenue</h2>
      <span class="sec-note">{len(d['monthly'])} months</span></div>
    <div class="card scroll">{monthly_svg}
      <div class="legend">
        <span><i class="dot" style="background:var(--jade)"></i> Collected revenue</span>
        <span><i class="dot" style="background:var(--rose)"></i> Patients seen (line)</span>
        <span><i class="dot" style="background:var(--surface-2);border:1px dashed var(--muted)"></i> Current month partial</span>
      </div></div>
  </section>

  <section>
    <div class="sec-head"><h2>Week&#8209;by&#8209;week · last 6 weeks</h2>
      <span class="sec-note">Mon–Sun weeks</span></div>
    <div class="weeks">{weeks_html}</div>
  </section>

  <section>
    <div class="sec-head"><h2>{dd['label']} deep&#8209;dive</h2>
      <span class="sec-note">{dd['sub']}</span></div>
    <div class="cols">
      <div class="card">
        <div class="sec-note" style="margin-bottom:12px;font-weight:600;color:var(--ink)">Top services by revenue</div>
        <div class="bars">{services_html}</div></div>
      <div style="display:flex;flex-direction:column;gap:20px;">
        <div class="card">
          <div class="sec-note" style="margin-bottom:12px;font-weight:600;color:var(--ink)">Revenue by provider</div>
          <div class="bars prov">{providers_html}</div></div>
        <div class="card">
          <div class="sec-note" style="margin-bottom:6px;font-weight:600;color:var(--ink)">Revenue mix</div>
          <div class="mix">{donut_svg}
            <div class="big"><b>{tp}%</b> Treatment&nbsp;·&nbsp;<b>{100-tp}%</b> Product</div>
          </div></div>
      </div>
    </div>
  </section>

  <footer>
    <span>Auto-built from <code>data/data.db</code> · updated {d['generated']}</span>
    <span>Revenue = cash collected (excludes $0 no-charge visits)</span>
  </footer>
</div>"""


CSS = """
:root{--bg:#F4F7F4;--surface:#FFFFFF;--surface-2:#EEF3EE;--ink:#16302A;--muted:#586A62;
--line:#E1E9E2;--jade:#2E8B7F;--jade-soft:#8FC4BB;--rose:#C57B86;--rose-soft:#E3B9BF;
--up:#2F9E6B;--down:#C0803A;--shadow:0 1px 2px rgba(22,48,42,.04),0 8px 24px rgba(22,48,42,.06);
--serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
@media (prefers-color-scheme:dark){:root{--bg:#0E1D19;--surface:#152A24;--surface-2:#1A322B;
--ink:#E8F1EC;--muted:#9DB0A7;--line:#254038;--jade:#4FB6A6;--jade-soft:#2E5A52;--rose:#D896A0;
--rose-soft:#5A3A40;--up:#4FBE86;--down:#D6A25C;--shadow:0 1px 2px rgba(0,0,0,.2),0 10px 30px rgba(0,0,0,.28);}}
:root[data-theme="light"]{--bg:#F4F7F4;--surface:#FFFFFF;--surface-2:#EEF3EE;--ink:#16302A;--muted:#586A62;
--line:#E1E9E2;--jade:#2E8B7F;--jade-soft:#8FC4BB;--rose:#C57B86;--rose-soft:#E3B9BF;--up:#2F9E6B;--down:#C0803A;}
:root[data-theme="dark"]{--bg:#0E1D19;--surface:#152A24;--surface-2:#1A322B;--ink:#E8F1EC;--muted:#9DB0A7;
--line:#254038;--jade:#4FB6A6;--jade-soft:#2E5A52;--rose:#D896A0;--rose-soft:#5A3A40;--up:#4FBE86;--down:#D6A25C;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px;}
.tnum{font-variant-numeric:tabular-nums;}
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;padding-bottom:20px;border-bottom:1px solid var(--line);}
.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--jade);font-weight:700;margin:0 0 6px;}
h1{font-family:var(--serif);font-weight:600;font-size:34px;line-height:1.05;margin:0;letter-spacing:-.01em;text-wrap:balance;}
.sub{color:var(--muted);font-size:14px;margin:6px 0 0;}
.range{text-align:right;color:var(--muted);font-size:13px;}
.range b{color:var(--ink);font-weight:600;}
section{margin-top:34px;}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:14px;}
h2{font-family:var(--serif);font-weight:600;font-size:20px;margin:0;letter-spacing:-.01em;}
.sec-note{color:var(--muted);font-size:12.5px;}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:6px;min-width:0;}
.kpi .label{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600;}
.kpi .val{font-size:27px;font-weight:650;letter-spacing:-.02em;line-height:1;}
.kpi .val.small{font-size:22px;}
.kpi .foot{font-size:12.5px;color:var(--muted);display:flex;align-items:center;gap:6px;}
.delta{font-weight:650;display:inline-flex;align-items:center;gap:3px;}
.delta.up{color:var(--up);}.delta.down{color:var(--down);}
.chip{font-size:10.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:2px 7px;border-radius:999px;background:var(--surface-2);color:var(--muted);border:1px solid var(--line);}
.chip.partial{color:var(--down);border-color:color-mix(in srgb,var(--down) 40%,transparent);}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:var(--shadow);}
.scroll{overflow-x:auto;}
svg{display:block;max-width:100%;height:auto;}
.axis-lbl{fill:var(--muted);font-size:10px;font-family:var(--sans);}
.grid-line{stroke:var(--line);stroke-width:1;}
.bar-val{fill:var(--muted);font-size:9.5px;font-weight:600;font-family:var(--sans);font-variant-numeric:tabular-nums;}
.weeks{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;}
.week{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:13px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:8px;min-width:0;}
.week .wk{font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.02em;}
.week .wv{font-size:19px;font-weight:650;letter-spacing:-.02em;}
.week .wp{font-size:11.5px;color:var(--muted);}
.track{height:6px;border-radius:99px;background:var(--surface-2);overflow:hidden;}
.track>i{display:block;height:100%;background:linear-gradient(90deg,var(--jade-soft),var(--jade));border-radius:99px;}
.week.partial{border-style:dashed;}
.week.partial .track>i{background:repeating-linear-gradient(45deg,var(--jade-soft),var(--jade-soft) 4px,transparent 4px,transparent 8px);}
.cols{display:grid;grid-template-columns:1.4fr 1fr;gap:20px;align-items:start;}
.bars{display:flex;flex-direction:column;gap:11px;}
.row{display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;}
.row .nm{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.row .amt{font-size:13px;font-weight:650;font-variant-numeric:tabular-nums;}
.row .bar{grid-column:1/-1;height:8px;border-radius:99px;background:var(--surface-2);overflow:hidden;}
.row .bar>i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--jade-soft),var(--jade));}
.prov .row .bar>i{background:linear-gradient(90deg,var(--rose-soft),var(--rose));}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;font-size:12.5px;color:var(--muted);}
.legend span{display:inline-flex;align-items:center;gap:6px;}
.dot{width:10px;height:10px;border-radius:3px;display:inline-block;}
.mix{display:flex;flex-direction:column;gap:14px;align-items:center;justify-content:center;height:100%;}
.mix .big{font-size:15px;color:var(--muted);text-align:center;}
.mix .big b{color:var(--ink);}
footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px;display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between;}
@media (max-width:820px){.kpis{grid-template-columns:repeat(2,1fr);}.weeks{grid-template-columns:repeat(2,1fr);}.cols{grid-template-columns:1fr;}h1{font-size:28px;}}
"""

DOCTYPE = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>FitLab Hawaii — Sales Dashboard</title></head><body>')


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    d = gather(conn)
    conn.close()
    if not d:
        print("No Jane sales data to build dashboard.")
        return
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Standalone file (with doctype/html/body) so it opens directly in a browser
    OUT_PATH.write_text(DOCTYPE + build_html(d) + "</body></html>", encoding="utf-8")
    print(f"Dashboard written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
