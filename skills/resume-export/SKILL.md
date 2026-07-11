---
name: resume-export
description: Render a resume config to a clean, ATS-safe Word (.docx) and a text-based (ATS-readable) PDF. Use when producing resume output files. Covers the JSON config schema, the generator/converter scripts, dependency setup, and conversion fallbacks.
---

# Resume Export — .docx + ATS-safe .pdf

Turn a tailored resume config into files. Layout is intentionally **ATS-safe**: single column, real text (no tables, text boxes, columns, or images-of-text), standard fonts, navy section rules.

## Scripts (in this skill's `scripts/`)
- `build_resume.py <config.json>` → writes the `.docx`.
- `to_pdf.py <in.docx> [out.pdf]` → converts and **verifies a real text layer** (ATS-readable), trying LibreOffice → macOS Word → docx2pdf.

Run them with the plugin root env var:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/resume-export/scripts/build_resume.py" /path/config.json
python3 "${CLAUDE_PLUGIN_ROOT}/skills/resume-export/scripts/to_pdf.py"  /path/out.docx /path/out.pdf
```

## Dependency: python-docx
The generator needs `python-docx`. Install once into a bundled dir and point the scripts at it:
```bash
python3 -m pip install --target="$HOME/.rebound/pylibs" python-docx >/dev/null 2>&1
export REBOUND_PYLIBS="$HOME/.rebound/pylibs"
```
`build_resume.py` auto-adds `$REBOUND_PYLIBS` (and `~/.rebound/pylibs`, `/tmp/pylibs`) to its path.

## Config schema (fully generic — assemble it from the base resume + JD)
```json
{
  "out": "/abs/path/<JobId>_<Init>.docx",
  "name": "FIRST LAST",
  "title": "Senior Software Engineer  |  Focus A  ·  Focus B  ·  Focus C",
  "contact": "+1 ...  |  email  |  linkedin.com/in/...  |  City, ST",
  "accent": "1F3A5F",
  "summary": "3-4 sentences, JD-mirrored, truthful.",
  "sections": [
    {"heading": "Work Experience", "type": "experience",
     "roles": [{"title": "Senior Engineer — Company", "meta": "City, ST  |  2022 – Present",
                "bullets": ["**Bolded outcome** then detail with a metric.", "..."]}]},
    {"heading": "Selected Highlights", "type": "bullets", "bullets": ["**Thing** ...", "..."]},
    {"heading": "Technical Skills", "type": "skills",
     "skills": [{"label": "Languages", "items": "Java, Go, Python"},
                {"label": "Cloud & DevOps", "items": "AWS, Kubernetes, CI/CD"}]},
    {"heading": "Education", "type": "roles_only",
     "roles": [{"title": "B.S. Computer Science — University", "meta": "GPA 3.9  |  2016"}]},
    {"heading": "Certifications & Achievements", "type": "bullets", "bullets": ["**AWS ...**", "..."]}
  ]
}
```
- Section `type`: `experience` (title/meta + bullets), `bullets` (heading + list), `skills` (label: items), `roles_only` (title + right-aligned meta, no bullets — for education).
- Inline markup in any string: `**bold**`, `*italic*`.

## Conversion fallbacks
`to_pdf.py` tries, in order: **LibreOffice** (`soffice --headless --convert-to pdf`, best for headless/CI), **macOS Microsoft Word** (AppleScript, pixel-perfect), then **docx2pdf**. If none exist, tell the user to `brew install --cask libreoffice`.

If running the converter directly is blocked in a sandbox, the equivalent macOS+Word one-liner also works from a granted shell:
```bash
osascript -e 'tell application "Microsoft Word" to open (POSIX file "/abs/in.docx")' \
          -e 'tell application "Microsoft Word" to save as active document file name "/abs/out.pdf" file format format PDF' \
          -e 'tell application "Microsoft Word" to close active document saving no'
```

## Always verify
A resume PDF must be **text-based**, never a scanned image — `to_pdf.py` confirms this by finding `BT`/`Tj` operators in the (decompressed) content streams. If verification fails, re-convert with a different engine before delivering.

**Reading order, not just presence.** A multi-column PDF *has* a text layer but extracts **scrambled** — which is what actually breaks ATS parsing. Pass the name + section headings as anchors and `to_pdf.py` verifies they extract *in that order* (via poppler `pdftotext` → pdfminer → a stdlib fallback):
```bash
python3 .../to_pdf.py out.docx out.pdf --anchors "Jane Doe,Summary,Work Experience,Skills,Education"
```
Rebound already generates single-column, so this is a **guarantee/regression check** on its own output — especially valuable because LibreOffice vs Word embed text streams differently. If the reading-order check warns, re-convert with a different engine before delivering.
