"""
One-time GoTo authorization (OAuth 2.0 authorization-code flow).

Prerequisites in .env: GOTO_CLIENT_ID, GOTO_CLIENT_SECRET, and GOTO_REDIRECT_URI set to a
loopback URL registered on your GoTo OAuth client (default http://localhost:8080).

Run:
    .venv/bin/python scripts/goto_auth.py

Opens your browser to approve access, captures the code on a local server, exchanges it
for a token, and stores credentials/goto-token.json.
"""

import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goto  # noqa: E402

_captured = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        _captured.update({k: v[0] for k, v in qs.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        msg = ("Authorization complete — you can close this tab and return to Claude."
               if "code" in qs else f"Authorization error: {qs.get('error', ['unknown'])[0]}")
        self.wfile.write(f"<html><body><h3>{msg}</h3></body></html>".encode())

    def log_message(self, *args):
        pass  # silence default logging


def main():
    cid, secret, redirect = goto.client_config()
    if not cid or not secret:
        print("Missing GOTO_CLIENT_ID / GOTO_CLIENT_SECRET in .env")
        sys.exit(1)

    parsed = urlparse(redirect)
    if parsed.hostname not in ("localhost", "127.0.0.1"):
        print(f"GOTO_REDIRECT_URI is '{redirect}'. This flow needs a loopback URL like "
              f"http://localhost:8080 registered on your GoTo client. Update .env and the client.")
        sys.exit(1)
    port = parsed.port or 8080

    auth_url = f"{goto.AUTH_URL}?" + urlencode({
        "client_id": cid, "response_type": "code", "redirect_uri": redirect,
    })
    print("Opening your browser to authorize GoTo...")
    print(f"If it does not open, visit:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    server = HTTPServer(("localhost", port), _Handler)
    server.handle_request()  # serve exactly one request (the redirect)

    if "code" not in _captured:
        print(f"Authorization failed: {_captured}")
        sys.exit(1)

    goto.exchange_code(_captured["code"])
    print("\nAuthorized! Token saved to credentials/goto-token.json")
    print("Test it with: .venv/bin/python scripts/goto.py")


if __name__ == "__main__":
    main()
