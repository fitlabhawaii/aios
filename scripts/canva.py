"""
Canva Connect helper — OAuth 2.0 (PKCE) token management + design export/autofill.

Credentials from .env:
    CANVA_CLIENT_ID, CANVA_CLIENT_SECRET, CANVA_REDIRECT_URI (default http://localhost:8080/callback)

Authorize once with scripts/canva_auth.py; this module loads/refreshes the token
(credentials/canva-token.json, gitignored).

Docs: https://www.canva.dev/docs/connect/
"""

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("Missing 'requests' — run: .venv/bin/pip install requests")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CRED_DIR = WORKSPACE_ROOT / "credentials"
TOKEN_PATH = CRED_DIR / "canva-token.json"

AUTH_URL = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
API_BASE = "https://api.canva.com/rest/v1"

# Read = list/export designs & assets; write/brandtemplate = autofill (Enterprise/trial)
SCOPES = (
    "design:meta:read design:content:read design:content:write "
    "asset:read folder:read profile:read "
    "brandtemplate:meta:read brandtemplate:content:read"
)


def _load_env():
    from dotenv import load_dotenv
    load_dotenv(WORKSPACE_ROOT / ".env")


def client_config():
    _load_env()
    return (
        os.getenv("CANVA_CLIENT_ID", "").strip(),
        os.getenv("CANVA_CLIENT_SECRET", "").strip(),
        os.getenv("CANVA_REDIRECT_URI", "http://localhost:8080/callback").strip()
        or "http://localhost:8080/callback",
    )


def _basic_auth(cid, secret):
    return "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()


def make_pkce():
    """Return (code_verifier, code_challenge) for PKCE S256."""
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def save_token(tok):
    tok["_saved_at"] = int(time.time())
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(tok, indent=2))


def load_token():
    return json.loads(TOKEN_PATH.read_text()) if TOKEN_PATH.exists() else None


def exchange_code(code, code_verifier):
    cid, secret, redirect = client_config()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": _basic_auth(cid, secret),
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code", "code": code,
              "code_verifier": code_verifier, "redirect_uri": redirect},
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
    if time.time() >= tok.get("_saved_at", 0) + tok.get("expires_in", 14400) - 120:
        if tok.get("refresh_token"):
            tok = _refresh(tok)
        else:
            return None
    return tok.get("access_token")


def _headers():
    at = get_access_token()
    if not at:
        raise RuntimeError("No Canva token — run: .venv/bin/python scripts/canva_auth.py")
    return {"Authorization": f"Bearer {at}"}


def list_designs(limit=50):
    """List the user's designs."""
    items, token = [], None
    while len(items) < limit:
        params = {"continuation": token} if token else {}
        r = requests.get(f"{API_BASE}/designs", headers=_headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        items.extend(data.get("items", []))
        token = data.get("continuation")
        if not token:
            break
    return items[:limit]


def export_design(design_id, fmt="png", dest_dir="outputs/canva"):
    """Export a design; returns list of saved file paths."""
    # 1) Create export job
    r = requests.post(f"{API_BASE}/exports", headers=_headers(),
                      json={"design_id": design_id, "format": {"type": fmt}}, timeout=30)
    r.raise_for_status()
    job = r.json()["job"]
    job_id = job["id"]
    # 2) Poll until done
    for _ in range(60):
        jr = requests.get(f"{API_BASE}/exports/{job_id}", headers=_headers(), timeout=30)
        jr.raise_for_status()
        job = jr.json()["job"]
        if job["status"] in ("success", "failed"):
            break
        time.sleep(2)
    if job["status"] != "success":
        raise RuntimeError(f"Export failed: {job.get('error')}")
    # 3) Download
    dest = WORKSPACE_ROOT / dest_dir
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, url in enumerate(job.get("urls", [])):
        content = requests.get(url, timeout=60).content
        out = dest / f"{design_id}_{i}.{fmt}"
        out.write_bytes(content)
        saved.append(str(out))
    return saved


def list_brand_templates(limit=50):
    r = requests.get(f"{API_BASE}/brand-templates", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])[:limit]


def get_brand_template_dataset(template_id):
    r = requests.get(f"{API_BASE}/brand-templates/{template_id}/dataset",
                     headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json().get("dataset", {})


def autofill(template_id, data, poll=True):
    """Create an autofill job from a brand template + data dict. Returns the job."""
    r = requests.post(f"{API_BASE}/autofills", headers=_headers(),
                      json={"brand_template_id": template_id, "data": data}, timeout=30)
    r.raise_for_status()
    job = r.json()["job"]
    if not poll:
        return job
    for _ in range(60):
        jr = requests.get(f"{API_BASE}/autofills/{job['id']}", headers=_headers(), timeout=30)
        jr.raise_for_status()
        job = jr.json()["job"]
        if job["status"] in ("success", "failed"):
            break
        time.sleep(2)
    return job


if __name__ == "__main__":
    at = get_access_token()
    if not at:
        print("Not connected — run: .venv/bin/python scripts/canva_auth.py")
    else:
        try:
            r = requests.get(f"{API_BASE}/users/me", headers=_headers(), timeout=15)
            print(f"Canva connected. /users/me -> {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"Connected (token ok) but probe failed: {e}")
