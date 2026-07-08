"""
One-time Google Drive authorization.

Prerequisite: download an OAuth "Desktop app" client secret from Google Cloud and
save it to credentials/gdrive-client-secret.json (see the DataOS/Drive setup guide).

Run:
    .venv/bin/python scripts/gdrive_auth.py

This opens your browser to approve access. On success it writes
credentials/gdrive-token.json, which all Drive scripts then use.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gdrive  # noqa: E402


def main():
    if not gdrive.CLIENT_SECRET.exists():
        print("Missing credentials/gdrive-client-secret.json")
        print("Download an OAuth 'Desktop app' client from Google Cloud Console and save it there.")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(
        str(gdrive.CLIENT_SECRET), gdrive.SCOPES
    )
    # Opens a browser and captures the redirect on a local port.
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message=(
            "Opening your browser to authorize Google Drive access...\n"
            "If it does not open automatically, visit this URL:\n{url}"
        ),
        success_message="Authorization complete — you can close this tab and return to Claude.",
    )
    gdrive.CRED_DIR.mkdir(parents=True, exist_ok=True)
    gdrive.TOKEN_PATH.write_text(creds.to_json())
    print(f"\nAuthorized! Token saved to {gdrive.TOKEN_PATH}")
    print("Test it with: .venv/bin/python scripts/gdrive.py")


if __name__ == "__main__":
    main()
