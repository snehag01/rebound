# Contributing to Rebound

Thanks for helping people rebound. 🥊 Contributions of all sizes are welcome — bug fixes, new JD-source parsers, skills, docs, or roadmap ideas.

## Principles (please preserve these)
Rebound is **honesty-first**. Any change must keep these intact:
1. **The base résumé is the source of truth** — the tool re-words and re-orders, it never fabricates.
2. **No claimed expertise in unused tech** — label unproven tools "working knowledge" / "familiar".
3. **Primary over secondary** — relevant secondary skills support; they never headline over real strengths.
4. **The user's situation is private** — work-authorization / timeline data stays in local files (`~/.rebound/`), is never written into a résumé, and is never sent to any job board, recruiter, or third-party service. (It runs through the user's own AI assistant to help them, like anything in Claude Code — never to an external career service.)

## Project layout
```
.claude-plugin/   manifest + marketplace entry
commands/         slash commands (/rebound:start, tailor, profile, match, rise)
skills/           resume-tailoring · resume-export (scripts) · profile-memory
roadmap/          dated snapshots (mmddyyyy) — see below
examples/         sample resume config
```

## Dev setup
```bash
python3 -m pip install --target="$HOME/.rebound/pylibs" python-docx
export REBOUND_PYLIBS="$HOME/.rebound/pylibs"
# PDF conversion: LibreOffice (brew install --cask libreoffice) or Microsoft Word
```
Smoke-test the generator + converter:
```bash
python3 skills/resume-export/scripts/build_resume.py examples/example.config.json   # after setting a real "out" path
python3 skills/resume-export/scripts/to_pdf.py <that.docx> <that.pdf>
```

## Making changes
- **Commands & skills** are Markdown; keep them focused and instruction-clear.
- **`build_resume.py`** must stay generic (JSON-config-driven) and ATS-safe (single column, real text — no tables/text-boxes/images-of-text).
- **PDFs must be text-based** — `to_pdf.py` verifies this; don't regress it.

## Roadmap changes
The roadmap is **versioned by date**. Don't edit an old snapshot — add a new file:
```
roadmap/roadmap_<mmddyyyy>.md
```
Update the "Latest" pointer in `roadmap/README.md`.

## Pull requests
1. Fork and branch from `main` (`feat/…`, `fix/…`, `docs/…`).
2. Keep PRs focused; describe the change and how you tested it.
3. Update `CHANGELOG.md` under an "Unreleased" heading.
4. Be kind in reviews — a lot of Rebound's users are having a hard month.

## Reporting issues
Use the issue templates. For anything touching the private `situation` data, please flag it clearly so we review the privacy implications.

By contributing, you agree your contributions are licensed under the [MIT License](./LICENSE).
