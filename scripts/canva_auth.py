"""
One-time Canva authorization (OAuth 2.0 Authorization Code + PKCE).

Prerequisites in .env: CANVA_CLIENT_ID, CANVA_CLIENT_SECRET, and CANVA_REDIRECT_URI set to a
loopback URL registered on your Canva integration (default http://localhost:8080/callback).

Run:
    .venv/bin/python scripts/canva_auth.py
"""

import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canva  # noqa: E402

_captured = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        _captured.update({k: v[0] for k, v in qs.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ok = "code" in qs
        msg = ("Authorization complete — you can close this tab and return to Claude."
               if ok else f"Authorization error: {qs.get('error', ['unknown'])[0]}")
        self.wfile.write(f"<html><body><h3>{msg}</h3></body></html>".encode())

    def log_message(self, *args):
        pass


def main():
    cid, secret, redirect = canva.client_config()
    if not cid or not secret:
        print("Missing CANVA_CLIENT_ID / CANVA_CLIENT_SECRET in .env")
        sys.exit(1)

    parsed = urlparse(redirect)
    if parsed.hostname not in ("localhost", "127.0.0.1"):
        print(f"CANVA_REDIRECT_URI is '{redirect}'. Use a loopback URL like "
              f"http://localhost:8080/callback and register it on your Canva integration.")
        sys.exit(1)
    port = parsed.port or 8080

    verifier, challenge = canva.make_pkce()
    auth_url = f"{canva.AUTH_URL}?" + urlencode({
        "client_id": cid, "response_type": "code", "redirect_uri": redirect,
        "scope": canva.SCOPES, "code_challenge": challenge, "code_challenge_method": "s256",
        "state": "aios",
    })
    print("Opening your browser to authorize Canva...")
    print(f"If it does not open, visit:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    server = HTTPServer((parsed.hostname, port), _Handler)
    server.handle_request()

    if "code" not in _captured:
        print(f"Authorization failed: {_captured}")
        sys.exit(1)

    canva.exchange_code(_captured["code"], verifier)
    print("\nAuthorized! Token saved to credentials/canva-token.json")
    print("Test it with: .venv/bin/python scripts/canva.py")


if __name__ == "__main__":
    main()
