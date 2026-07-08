"""
GoTo Connect helper — OAuth token management + call-history reports.

Credentials come from .env:
    GOTO_CLIENT_ID, GOTO_CLIENT_SECRET, GOTO_REDIRECT_URI (default http://localhost:8080)
Optional:
    GOTO_ACCOUNT_KEY  — set if it can't be auto-detected from the token

Token is stored in credentials/goto-token.json (gitignored). Authorize once with
scripts/goto_auth.py; this module loads and refreshes the token automatically.

Docs: https://developer.goto.com  (Authentication + Call Events Report APIs)
"""

import base64
import json
import os
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("Missing 'requests' — run: .venv/bin/pip install requests")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CRED_DIR = WORKSPACE_ROOT / "credentials"
TOKEN_PATH = CRED_DIR / "goto-token.json"

AUTH_URL = "https://authentication.logmeininc.com/oauth/authorize"
TOKEN_URL = "https://authentication.logmeininc.com/oauth/token"
API_BASE = "https://api.goto.com"


def _load_env():
    from dotenv import load_dotenv
    load_dotenv(WORKSPACE_ROOT / ".env")


def client_config():
    _load_env()
    return (
        os.getenv("GOTO_CLIENT_ID", "").strip(),
        os.getenv("GOTO_CLIENT_SECRET", "").strip(),
        os.getenv("GOTO_REDIRECT_URI", "http://localhost:8080").strip() or "http://localhost:8080",
    )


def _basic_auth(cid, secret):
    return "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()


def save_token(tok):
    tok["_saved_at"] = int(time.time())
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(tok, indent=2))


def load_token():
    return json.loads(TOKEN_PATH.read_text()) if TOKEN_PATH.exists() else None


def exchange_code(code):
    cid, secret, redirect = client_config()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": _basic_auth(cid, secret),
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect},
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()
    save_token(tok)
    return tok


def _refresh(tok):
    cid, secret, _ = client_config()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": _basic_auth(cid, secret),
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]},
        timeout=30,
    )
    r.raise_for_status()
    new = r.json()
    new.setdefault("refresh_token", tok.get("refresh_token"))
    save_token(new)
    return new


def get_access_token():
    tok = load_token()
    if not tok:
        return None
    if time.time() >= tok.get("_saved_at", 0) + tok.get("expires_in", 3600) - 120:
        if tok.get("refresh_token"):
            tok = _refresh(tok)
        else:
            return None
    return tok.get("access_token")


def get_account_key():
    """Try token claims, then GOTO_ACCOUNT_KEY env var, then the GoTo 'me' endpoint."""
    tok = load_token() or {}
    for k in ("account_key", "accountKey", "organizer_key"):
        if tok.get(k):
            return str(tok[k])
    _load_env()
    env_key = os.getenv("GOTO_ACCOUNT_KEY", "").strip()
    if env_key:
        return env_key
    # Auto-discover from the admin 'me' endpoint
    at = get_access_token()
    if at:
        try:
            r = requests.get("https://api.getgo.com/admin/rest/v1/me",
                             headers={"Authorization": f"Bearer {at}"}, timeout=15)
            if r.status_code == 200:
                return str(r.json().get("accountKey")) or None
        except Exception:
            pass
    return None


def report_summaries(start_iso, end_iso, account_key=None, page_size=100):
    """Fetch call-event report summaries between two ISO-8601 timestamps."""
    at = get_access_token()
    if not at:
        raise RuntimeError("No GoTo token — run: .venv/bin/python scripts/goto_auth.py")
    ak = account_key or get_account_key()
    if not ak:
        raise RuntimeError("No GoTo account key — set GOTO_ACCOUNT_KEY in .env")

    items, marker = [], None
    while True:
        params = {"accountKey": ak, "startTime": start_iso,
                  "endTime": end_iso, "pageSize": page_size}
        if marker:
            params["pageMarker"] = marker
        r = requests.get(f"{API_BASE}/call-events-report/v1/report-summaries",
                         headers={"Authorization": f"Bearer {at}"}, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        batch = data.get("items", [])
        items.extend(batch)
        marker = data.get("nextPageMarker") or data.get("pageMarker")
        if not marker or not batch:
            break
    return items


if __name__ == "__main__":
    at = get_access_token()
    if not at:
        print("Not connected — run: .venv/bin/python scripts/goto_auth.py")
    else:
        print("GoTo connected. Access token acquired.")
        print(f"Account key: {get_account_key() or '(not found — may need GOTO_ACCOUNT_KEY)'}")
