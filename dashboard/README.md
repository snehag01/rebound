# Rebound Dashboard 🥊📊

A **local** React dashboard that visualizes your job search — applications, résumés curated per company, pipeline funnel, momentum over time, and fit-score distribution. Everything is computed **on your machine**; nothing leaves it.

## Run it
```bash
cd dashboard
npm install      # first time only
npm run dev      # → http://localhost:5273
```

## How the data flows
```
Claude Code  ──writes──►  ~/.rebound/data/tracker.json  ──served by Vite──►  React dashboard
   (/rebound:track)              (local datastore)          (/api/tracker)        (localhost)
```
- The Vite dev server has a small middleware that serves `~/.rebound/data/tracker.json` at `/api/tracker`.
- If that file doesn't exist yet, it falls back to `public/data/tracker.sample.json` — **fictional dummy data** (Alex Rivera / made-up companies) so you can try the UI immediately. It's labeled **sample data** in the header.
- **Privacy:** only the dummy sample is committed to the repo. Your real data lives in `~/.rebound/data/tracker.json` and is git-ignored — it never leaves your machine.
- Click **↻ Refresh** after logging applications with `/rebound:track`.

## What you see
- **Stat cards** — résumés curated, companies applied, applications, interviews (+response rate), offers, sponsorship-flagged roles.
- **Pipeline funnel** — curated → applied → screen → onsite → offer, with conversion %.
- **Applications over time** — weekly bars to show momentum.
- **Fit-score distribution** — how strong the roles you targeted are.
- **Applications table** — status pills, fit %, sponsor flag, the exact **résumé file** curated for each role, dates, source; searchable + filterable.

## Datastore schema
See [`public/data/tracker.sample.json`](./public/data/tracker.sample.json). Each application:
`id, company, role, location, status, fit, sponsor, resume_file, applied_date, updated_date, source, notes`.

## Privacy
The private **situation** (work authorization, timeline) lives in `~/.rebound/profile.json` and is **never** rendered here. This dashboard shows only your activity metrics.

## Build a static snapshot
```bash
npm run build   # → dist/ (reads bundled sample data, not the live datastore)
```

Stack: React 18 + Vite. No chart library — charts are pure CSS/SVG for a light footprint.
