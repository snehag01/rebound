# Changelog

All notable changes to Rebound are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- _Nothing yet._

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
