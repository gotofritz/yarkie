# /archive

Archive `docs/project-plan.md` to `docs/dev-logs/{date}-{time}-{hash}-{description}.md` (e.g. `2024-11-12-1430-87356bd-demo-customers-removal.md`). Create dir if needed. Show filename created.

Use `date +%Y-%m-%d-%H%M` for the date-time portion (YYYY-MM-DD-HHMM format).

After archiving, reset `docs/project-plan.md` to clean template:

```markdown
# Project Plan

Ready for the next plan
```

This provides a fresh slate for the next feature.
