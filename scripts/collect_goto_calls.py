"""
DataOS — GoTo Connect Call History Collector

Pulls call-event report summaries from GoTo Connect into the `goto_calls` table.
The API caps each query at ~31 days, so we fetch in 30-day chunks across the lookback
window and upsert by call id (idempotent — safe to run daily).

Captures direction, answered/missed, caller name+number, duration, and outcome — so you
can track inbound patient calls, missed calls, and answer rates.

Requires a GoTo token (scripts/goto_auth.py) with cr.v1.read scope, and GOTO_ACCOUNT_KEY.

NOTE: caller names/numbers are patient contact data — the database is local & gitignored.

Tables created: goto_calls
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goto  # noqa: E402

LOOKBACK_DAYS = 90        # total history pulled each run
WINDOW_DAYS = 30          # per-request window (API max is ~31)
FMT = "%Y-%m-%dT%H:%M:%SZ"


def collect():
    if not goto.get_access_token():
        return {"source": "goto_calls", "status": "skipped",
                "reason": "No GoTo token — run scripts/goto_auth.py"}
    if not goto.get_account_key():
        return {"source": "goto_calls", "status": "skipped",
                "reason": "No GoTo account key — set GOTO_ACCOUNT_KEY in .env"}
    try:
        end = datetime.now(timezone.utc)
        overall_start = end - timedelta(days=LOOKBACK_DAYS)
        items, cursor = [], overall_start
        while cursor < end:
            chunk_end = min(cursor + timedelta(days=WINDOW_DAYS), end)
            items.extend(goto.report_summaries(cursor.strftime(FMT), chunk_end.strftime(FMT)))
            cursor = chunk_end
        return {"source": "goto_calls", "status": "success", "data": {"items": items}}
    except Exception as e:
        return {"source": "goto_calls", "status": "error", "reason": str(e)}


def _iso(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goto_calls (
            call_id        TEXT PRIMARY KEY,   -- conversationSpaceId
            date           TEXT,               -- call day (YYYY-MM-DD)
            account_key    TEXT,
            direction      TEXT,               -- INBOUND / OUTBOUND
            answered       INTEGER,            -- 1 if the call was answered, else 0
            missed         INTEGER,            -- 1 if inbound & unanswered
            call_created   TEXT,
            call_answered  TEXT,
            call_ended     TEXT,
            duration_sec   INTEGER,            -- total call length
            talk_sec       INTEGER,            -- answered -> ended
            caller_name    TEXT,
            caller_number  TEXT,
            outcome        TEXT,
            handled_by     TEXT,               -- first participant (line/user) name
            raw            TEXT,
            collected_at   TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_goto_day ON goto_calls(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_goto_dir ON goto_calls(direction)")

    if result.get("status") != "success":
        conn.commit()
        return 0

    now = datetime.now(timezone.utc).isoformat()
    n = 0
    for it in result["data"]["items"]:
        cid = it.get("conversationSpaceId") or it.get("id")
        if not cid:
            continue
        created, answered_ts, ended = it.get("callCreated"), it.get("callAnswered"), it.get("callEnded")
        direction = it.get("direction")
        answered = 1 if answered_ts else 0
        outcome = it.get("callerOutcome")
        # GoTo auto-answers via the dial plan, so use its outcome code for "missed"
        missed = 1 if (direction == "INBOUND" and outcome in
                       ("MISSED", "ABANDONED", "NO_ANSWER", "LEFT_ON_HOLD")) else 0

        dc, da, de = _iso(created), _iso(answered_ts), _iso(ended)
        duration = int((de - dc).total_seconds()) if dc and de else None
        talk = int((de - da).total_seconds()) if da and de else None

        caller = it.get("caller") or {}
        parts = it.get("participants") or []
        handled_by = parts[0].get("name") if parts else None

        conn.execute(
            "INSERT OR REPLACE INTO goto_calls (call_id,date,account_key,direction,answered,"
            "missed,call_created,call_answered,call_ended,duration_sec,talk_sec,caller_name,"
            "caller_number,outcome,handled_by,raw,collected_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, (created or "")[:10], it.get("accountKey"), direction, answered, missed,
             created, answered_ts, ended, duration, talk, caller.get("name"),
             caller.get("number"), it.get("callerOutcome"), handled_by, json.dumps(it), now),
        )
        n += 1
    conn.commit()
    return n


if __name__ == "__main__":
    res = collect()
    if res["status"] == "success":
        items = res["data"]["items"]
        inbound = sum(1 for i in items if i.get("direction") == "INBOUND")
        missed = sum(1 for i in items if i.get("direction") == "INBOUND" and not i.get("callAnswered"))
        print(f"Fetched {len(items)} calls (last {LOOKBACK_DAYS}d): "
              f"{inbound} inbound, {missed} missed inbound")
    else:
        print(f"{res['status']}: {res.get('reason')}")
