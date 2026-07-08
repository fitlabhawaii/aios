"""
DataOS / Drive — command-line wrapper for common Google Drive operations.

Uses the OAuth connection set up via gdrive_auth.py. All commands accept either a
Drive share URL or a raw file/folder id.

Usage:
    # List what's in a folder (or 'root' for top of My Drive)
    .venv/bin/python scripts/drive_cli.py list <folder_url|id|root>

    # Read docs for context: export every Doc/file in a folder to local markdown/files
    .venv/bin/python scripts/drive_cli.py pull-docs <folder_url> [--dest context/import/drive]

    # Pull spreadsheet data: dump a Google Sheet to CSV (stdout or --out file)
    .venv/bin/python scripts/drive_cli.py sheet <sheet_url> [--range A1:Z9999] [--out data/imports/x.csv]

    # Push a report out: upload a local file into a Drive folder
    .venv/bin/python scripts/drive_cli.py push <local_file> <folder_url>

    # Sync a folder: download everything in a Drive folder to a local directory
    .venv/bin/python scripts/drive_cli.py sync <folder_url> <local_dir>
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gdrive  # noqa: E402

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def _kind(mime):
    return {
        "application/vnd.google-apps.folder": "folder",
        "application/vnd.google-apps.document": "gdoc",
        "application/vnd.google-apps.spreadsheet": "gsheet",
        "application/vnd.google-apps.presentation": "gslides",
    }.get(mime, "file")


def _safe_name(name):
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).strip()


def cmd_list(args):
    fid = "root" if args.target in ("root", "my-drive") else gdrive.find_id_from_url(args.target)
    files = gdrive.list_folder(fid)
    print(f"{len(files)} items in {args.target}:\n")
    for f in sorted(files, key=lambda x: (_kind(x['mimeType']) != 'folder', x['name'].lower())):
        print(f"  [{_kind(f['mimeType']):7}] {f['name']}   ({f['id']})")


def cmd_pull_docs(args):
    fid = gdrive.find_id_from_url(args.target)
    dest = WORKSPACE_ROOT / args.dest
    dest.mkdir(parents=True, exist_ok=True)
    files = gdrive.list_folder(fid)
    pulled = 0
    for f in files:
        if _kind(f["mimeType"]) == "folder":
            continue
        name = _safe_name(f["name"])
        out = dest / name
        try:
            saved = gdrive.download_file(f["id"], f["mimeType"], out)
            print(f"  pulled: {Path(saved).name}")
            pulled += 1
        except Exception as e:
            print(f"  skipped {f['name']}: {e}")
    print(f"\nPulled {pulled} files into {dest.relative_to(WORKSPACE_ROOT)}")


def cmd_sheet(args):
    sid = gdrive.find_id_from_url(args.target)
    rows = gdrive.read_sheet(sid, args.range)
    if args.out:
        out = WORKSPACE_ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        print(f"Wrote {len(rows)} rows to {out.relative_to(WORKSPACE_ROOT)}")
    else:
        w = csv.writer(sys.stdout)
        for r in rows[:50]:
            w.writerow(r)
        if len(rows) > 50:
            print(f"... ({len(rows) - 50} more rows; use --out to save all)")


def cmd_push(args):
    folder_id = gdrive.find_id_from_url(args.folder)
    local = WORKSPACE_ROOT / args.file if not Path(args.file).is_absolute() else Path(args.file)
    if not local.exists():
        print(f"File not found: {local}")
        sys.exit(1)
    res = gdrive.upload_file(local, folder_id)
    print(f"Uploaded '{res['name']}' -> {res.get('webViewLink', res['id'])}")


def cmd_sync(args):
    fid = gdrive.find_id_from_url(args.target)
    dest = WORKSPACE_ROOT / args.dest if not Path(args.dest).is_absolute() else Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    files = gdrive.list_folder(fid)
    n = 0
    for f in files:
        if _kind(f["mimeType"]) == "folder":
            continue  # top-level only; folders would need recursion
        try:
            gdrive.download_file(f["id"], f["mimeType"], dest / _safe_name(f["name"]))
            n += 1
        except Exception as e:
            print(f"  skipped {f['name']}: {e}")
    print(f"Synced {n} files from Drive -> {dest}")


def main():
    p = argparse.ArgumentParser(description="Google Drive operations")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list"); s.add_argument("target"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("pull-docs"); s.add_argument("target")
    s.add_argument("--dest", default="context/import/drive"); s.set_defaults(fn=cmd_pull_docs)
    s = sub.add_parser("sheet"); s.add_argument("target")
    s.add_argument("--range", default="A1:Z9999"); s.add_argument("--out")
    s.set_defaults(fn=cmd_sheet)
    s = sub.add_parser("push"); s.add_argument("file"); s.add_argument("folder")
    s.set_defaults(fn=cmd_push)
    s = sub.add_parser("sync"); s.add_argument("target"); s.add_argument("dest")
    s.set_defaults(fn=cmd_sync)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
