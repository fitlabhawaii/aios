# Canva

> Work with the connected Canva account (list and export designs).

## Variables

request: $ARGUMENTS (plain-English description of the Canva task)

---

## Instructions

Canva is connected via OAuth (Connect API). Use `scripts/canva_cli.py` for operations, or
import `canva` for custom logic. Always run through the venv: `.venv/bin/python`.

**List designs:**
```bash
.venv/bin/python scripts/canva_cli.py list --limit 50
```

**Export a design** (png/pdf/jpg/pptx/mp4/gif) into `outputs/canva/`:
```bash
.venv/bin/python scripts/canva_cli.py export <design_id> --format png
```

### Guidance

- If the user names a design rather than an id, run `list` first and match the title.
- Exports land in `outputs/canva/` (gitignored). Report the saved paths.
- **Autofill / brand templates** require Canva Teams/Enterprise; the account is on Pro, so
  those return nothing. Don't promise autofill on the current plan.
- If a call fails with an auth error, re-run `.venv/bin/python scripts/canva_auth.py`.

Interpret the request, run the right command(s), and report what you did in plain English.
