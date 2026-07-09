"""
Canva CLI — common Connect API operations (uses the OAuth token from canva_auth.py).

Usage:
    .venv/bin/python scripts/canva_cli.py list [--limit 50]
    .venv/bin/python scripts/canva_cli.py export <design_id> [--format png|pdf|jpg|pptx|mp4|gif] [--dest outputs/canva]
    .venv/bin/python scripts/canva_cli.py templates          # brand templates (Teams/Enterprise only)
    .venv/bin/python scripts/canva_cli.py autofill <template_id> '<json_data>'   # Enterprise only
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canva  # noqa: E402


def cmd_list(args):
    designs = canva.list_designs(limit=args.limit)
    print(f"{len(designs)} designs:")
    for d in designs:
        print(f"  {d.get('id')}  {d.get('title') or '(untitled)'}")


def cmd_export(args):
    saved = canva.export_design(args.design_id, fmt=args.format, dest_dir=args.dest)
    print(f"Exported {len(saved)} file(s):")
    for s in saved:
        print(f"  {s}")


def cmd_templates(args):
    tpls = canva.list_brand_templates(limit=args.limit)
    if not tpls:
        print("No brand templates found (requires Canva Teams/Enterprise).")
        return
    for t in tpls:
        print(f"  {t.get('id')}  {t.get('title')}")


def cmd_autofill(args):
    data = json.loads(args.data)
    job = canva.autofill(args.template_id, data)
    print(json.dumps(job, indent=2))


def main():
    p = argparse.ArgumentParser(description="Canva Connect API operations")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list"); s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("export"); s.add_argument("design_id")
    s.add_argument("--format", default="png"); s.add_argument("--dest", default="outputs/canva")
    s.set_defaults(fn=cmd_export)
    s = sub.add_parser("templates"); s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_templates)
    s = sub.add_parser("autofill"); s.add_argument("template_id"); s.add_argument("data")
    s.set_defaults(fn=cmd_autofill)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
