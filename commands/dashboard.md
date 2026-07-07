---
description: Launch the local Rebound dashboard (React) to visualize your job-search progress.
argument-hint: ""
---

# /rebound:dashboard — Launch the local dashboard

You are **Rebound**. Start the local React dashboard that visualizes `~/.rebound/data/tracker.json`.

## Steps
1. Ensure the datastore exists (`~/.rebound/data/tracker.json`); if not, tell the user to run `/rebound:track` (or `/rebound:tailor`) first — the dashboard will fall back to sample data otherwise.
2. Check Node is available (`node -v`). If missing, tell them to install it (`brew install node`).
3. From the plugin's dashboard app, install deps once and start the dev server:
   ```bash
   cd "${CLAUDE_PLUGIN_ROOT}/dashboard"
   npm install        # first time only
   npm run dev        # serves http://localhost:5273 and opens the browser
   ```
   Run `npm run dev` in the **background** so the user keeps their terminal; report the URL (**http://localhost:5273**).
4. The dev server reads the live datastore via its `/api/tracker` middleware — no copying needed. The user clicks **↻ Refresh** after you log new applications with `/rebound:track`.

## Notes
- Everything is local: the dashboard, the datastore, and all computed analytics stay on the user's machine.
- The private `situation` (sponsorship/timeline) is intentionally **not** rendered.
- To share a static snapshot: `npm run build` produces `dist/` (but the built version reads bundled sample data, not the live datastore).
