"""
DataOS / Drive — Google Drive helper (OAuth user credentials)

Full read/write access to your Google Drive using an OAuth "Desktop app" client.
Authorize once with `gdrive_auth.py`; this module loads and refreshes the token.

Credentials (both gitignored, live in credentials/):
    gdrive-client-secret.json  — downloaded from Google Cloud (OAuth Desktop client)
    gdrive-token.json          — created by gdrive_auth.py after you authorize

Capabilities:
    list_folder(folder_id)              -> [ {id,name,mimeType,modifiedTime,size}, ... ]
    download_file(id, mime, dest)       -> saves file (exports native Docs/Sheets)
    export_doc_markdown(id, dest)       -> Google Doc -> markdown/text
    read_sheet(spreadsheet_id, range)   -> [[row], [row], ...] cell values
    upload_file(local_path, folder_id)  -> uploads/creates a file in a Drive folder
    find_id_from_url(url)               -> extract a Drive file/folder id from a share URL
"""

import io
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CRED_DIR = WORKSPACE_ROOT / "credentials"
CLIENT_SECRET = CRED_DIR / "gdrive-client-secret.json"
TOKEN_PATH = CRED_DIR / "gdrive-token.json"

# Full Drive read/write + read Google Sheets cell values
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

# Native Google formats must be exported; map -> (export mime, file extension)
EXPORT_MAP = {
    "application/vnd.google-apps.document": ("text/markdown", ".md"),
    "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
    "application/vnd.google-apps.presentation": ("text/plain", ".txt"),
}


def get_credentials():
    """Load stored OAuth creds, refreshing if expired. Returns creds or None."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not TOKEN_PATH.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
        return creds
    return None


def _service(name, version):
    from googleapiclient.discovery import build
    creds = get_credentials()
    if not creds:
        raise RuntimeError(
            "No Google Drive credentials yet — run: .venv/bin/python scripts/gdrive_auth.py"
        )
    return build(name, version, credentials=creds, cache_discovery=False)


def drive_service():
    return _service("drive", "v3")


def sheets_service():
    return _service("sheets", "v4")


def find_id_from_url(url):
    """Extract a Drive file/folder id from a typical share URL (or return input)."""
    for pat in (r"/folders/([A-Za-z0-9_-]+)", r"/d/([A-Za-z0-9_-]+)", r"[?&]id=([A-Za-z0-9_-]+)"):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return url.strip()


def list_folder(folder_id, page_size=200):
    """List non-trashed files directly inside a folder."""
    svc = drive_service()
    q = f"'{folder_id}' in parents and trashed=false"
    files, token = [], None
    while True:
        resp = svc.files().list(
            q=q, spaces="drive", pageSize=page_size,
            fields="nextPageToken, files(id,name,mimeType,modifiedTime,size)",
            pageToken=token, supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        files.extend(resp.get("files", []))
        token = resp.get("nextPageToken")
        if not token:
            break
    return files


def download_file(file_id, mime_type, dest_path):
    """Download a Drive file. Native Google types are exported per EXPORT_MAP."""
    from googleapiclient.http import MediaIoBaseDownload
    svc = drive_service()
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if mime_type in EXPORT_MAP:
        export_mime, ext = EXPORT_MAP[mime_type]
        try:
            data = svc.files().export(fileId=file_id, mimeType=export_mime).execute()
        except Exception:
            data = svc.files().export(fileId=file_id, mimeType="text/plain").execute()
        if isinstance(data, str):
            data = data.encode("utf-8")
        if dest_path.suffix == "":
            dest_path = dest_path.with_suffix(ext)
        dest_path.write_bytes(data)
    else:
        req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        dest_path.write_bytes(buf.getvalue())
    return str(dest_path)


def export_doc_markdown(file_id, dest_path):
    """Export a Google Doc to markdown (or plain text fallback)."""
    return download_file(file_id, "application/vnd.google-apps.document", dest_path)


def read_sheet(spreadsheet_id, cell_range="A1:Z10000"):
    """Return cell values from a Google Sheet as a list of rows."""
    svc = sheets_service()
    resp = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=cell_range
    ).execute()
    return resp.get("values", [])


def upload_file(local_path, folder_id, name=None):
    """Upload a local file into a Drive folder. Returns {id,name,webViewLink}."""
    from googleapiclient.http import MediaFileUpload
    svc = drive_service()
    local_path = Path(local_path)
    meta = {"name": name or local_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(local_path), resumable=False)
    return svc.files().create(
        body=meta, media_body=media, fields="id,name,webViewLink",
        supportsAllDrives=True,
    ).execute()


if __name__ == "__main__":
    # Quick connectivity check
    try:
        svc = drive_service()
        about = svc.about().get(fields="user(emailAddress,displayName)").execute()
        u = about.get("user", {})
        print(f"Connected to Google Drive as: {u.get('displayName')} <{u.get('emailAddress')}>")
    except Exception as e:
        print(f"Not connected: {e}")
