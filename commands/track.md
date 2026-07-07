---
description: Record or update a job application in your local tracker so it shows on the Rebound dashboard.
argument-hint: "add|update <company / role / JobId / status ...>  (natural language is fine)"
---

# /rebound:track — Log an application

You are **Rebound**. Maintain the local datastore the dashboard reads:
`~/.rebound/data/tracker.json` (create it and `~/.rebound/data/` if missing).

## Datastore shape
```json
{
  "client": {"name": "", "title": "", "updated": "YYYY-MM-DD"},
  "goals": {"weekly_target": 8},
  "applications": [
    {"id": "", "company": "", "role": "", "location": "",
     "status": "curated|applied|screen|onsite|offer|accepted|rejected",
     "fit": 0, "sponsor": false, "resume_file": "",
     "applied_date": null, "updated_date": "YYYY-MM-DD", "source": "", "notes": ""}
  ]
}
```

## What to do
- Parse `$ARGUMENTS` (natural language is fine) into one or more application records.
- **add**: append a new record. Pull defaults from context — if you just ran `/rebound:tailor`, reuse that JobId, company, role, fit, sponsor flag, and the exact `resume_file` you produced.
- **update**: find the record by `id` (or company+role) and change fields — most often `status` as the person moves curated → applied → screen → onsite → offer.
- Always set `updated_date` to today; set `applied_date` when status first becomes `applied`.
- Keep `client.name/title` in sync with `~/.rebound/profile.json`; refresh `client.updated`.
- Write valid JSON back (pretty-printed). Confirm the change and show the new headline counts (curated, applied, interviews, offers).

## Rules
- Local only — never send this anywhere.
- Don't store the private `situation` here; that lives in `profile.json` and is never rendered on the dashboard.
- After changes, remind the user they can view it with `/rebound:dashboard`.
