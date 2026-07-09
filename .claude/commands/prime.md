# Prime

> Read the context files and summarize your understanding of this workspace.

## Read

./context

Also read these workspace-memory files (added by InfraOS):

- `HISTORY.md` — Workspace changelog (what was built, when, by whom)
- `docs/_index.md` — Documentation routing index (find relevant system/integration docs here)

And this current-metrics file (added by DataOS):

- `context/group/key-metrics.md` — Current business metrics, auto-generated daily from the database

And this GTD operational hub (added by ProductivityOS):

- `gtd/dashboard.md` — Active projects, next actions, waiting-for, flagged items

## On-Demand Loading

Do NOT read these during /prime — load them only when a task requires the detail:

- `reference/data-access.md` — Full table schemas, SQL query examples, and collection details for the `data/data.db` warehouse. Load this when you need to run queries or analyze trends beyond what's in key-metrics.md.

## Summary

After reading, provide:

1. A brief summary of who I am, what this workspace is for and what your role is
2. Your understanding of the workspace structure and the purpose of each section/file
3. What commands are available
4. A summary of my/our current strategies and priorities
5. **Data status** — Review key-metrics.md and report the current numbers. Flag anything stale (latest record >2 days old). Note that you can run live SQL queries against `data/data.db` for deeper analysis (see `reference/data-access.md`).
6. **GTD status** — From `gtd/dashboard.md`, note active projects, flagged/urgent items, and anything waiting-for that's aging. Remind me if a weekly `/review` is due.
7. Confirmation you're ready to help me with pursuing these goals through use of this workspace
