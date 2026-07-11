# Changelog

All notable changes to Rebound are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- **Local dashboard** (`dashboard/`, React + Vite) — visualizes the job search from `~/.rebound/data/tracker.json`: stat cards, pipeline funnel, applications-over-time, fit-score distribution, and a per-company table with the résumé curated for each role. Rich CSS, pure CSS/SVG charts, live datastore via a Vite `/api/tracker` middleware (sample-data fallback). All analytics local.
- `/rebound:track` — record/update applications in the local datastore.
- `/rebound:dashboard` — launch the dashboard.
- Roadmap `07072026` updated with the **v0.2.0 Local Application Dashboard** milestone.

### Tests / CI
- Added a **test suite and GitHub Actions CI**: pytest for the résumé generator (`build_resume.py` — content preserved, ATS-safe single-column, no tables) and the PDF text-layer verifier (`to_pdf.py` — detects real text vs image-only, compressed & uncompressed streams); Vitest for the dashboard metrics (`metrics.js` — honest counting, funnel monotonicity, empty/null input). CI runs both on every push and PR.

### Fixed
- Corrected the plugin manifest `homepage`/`repository` URLs (`snehag` → `snehag01`) so they resolve to the real repository.
- Dashboard **"Résumés curated"** now counts only applications that actually have a curated résumé file, instead of every tracked row.

### Changed
- **Honesty-first privacy language.** Clarified across the README, roadmap, contributing guide, and dashboard docs that Rebound is local-first (no backend, no cloud, no upload) while being transparent that reasoning runs through the user's own AI assistant (Claude Code). This replaces the blanket "never leaves your machine" claim, which was inaccurate for the AI-processing step. Added a **"How your data is handled"** section to the README.
- Replaced an unsourced "~2.5× interview rate" figure in the roadmap with a primary-sourced, direction-only framing.

## [0.1.0] — 2026-07-07
Foundation release: the honesty-first résumé engine and private profile.

### Added
- **Commands**
  - `/rebound:start` — onboarding: reads the base résumé, builds a private profile, and captures the sensitive "situation" (work authorization, timeline) stored locally only.
  - `/rebound:tailor <JD|URL>` — curates a résumé from the base for one role → ATS-safe `.docx` + text-based `.pdf`; parses Workday/board JSON; asks about material gaps; applies honesty flags, fast-learner framing, and primary-over-secondary; folder logic (`--out` or `<Name>_resumes`).
  - `/rebound:profile` — view/update the profile, including the private situation.
  - `/rebound:match <URLs>` — basic role fit-scoring and ranking.
  - `/rebound:rise` — supportive, runway-aware check-in.
- **Skills**
  - `resume-tailoring` — the honesty-first method (fit analysis, gap handling, framing).
  - `resume-export` — generic JSON → `.docx` (`build_resume.py`) and verified text-layer PDF (`to_pdf.py`; LibreOffice → Word → docx2pdf).
  - `profile-memory` — profile schema and private-situation handling.
- **Project**
  - MIT license, README, bundled `examples/example.config.json`.
  - Date-versioned roadmap under `roadmap/` (`mmddyyyy`).

[Unreleased]: https://github.com/snehag01/rebound/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/snehag01/rebound/releases/tag/v0.1.0
