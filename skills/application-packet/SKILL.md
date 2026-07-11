---
name: application-packet
description: Assemble a ready-to-submit application packet — knockout pre-check, a tailored résumé, drafted answers to the form's recurring questions (from a local answer memory), and an honest "why this company" note. Use when the user is actually applying to a role.
---

# Application Packet — make a *good* application fast

Rebound helps people **apply well, not apply automatically.** The research is clear about where applying breaks: the tedium of form-filling burns people out, the real filters are *knockout questions* (answered on the form, not scored off the résumé), and generic content is what gets binned. This skill collapses the tedium and raises quality — the human still reviews and submits.

## The two engines (deterministic, in `scripts/`)

### 1. Knockout pre-check — `knockout.py`
Catches the form-level disqualifiers **before** the user invests 30 minutes.
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/application-packet/scripts/knockout.py" <requirements.json> <profile.json>
```
- You (the command) parse the JD into `requirements`: `{min_years, location, work_mode, degree, clearance, must_have:[...]}`.
- It returns `{"verdict": "clear|review|likely_blocked", "flags": [...]}` — each flag is **hard** (a real wall: onsite-vs-remote, clearance, a 3+ year gap) or **soft** (often flexible: 1–2 year gap, degree, a license to confirm).
- **Honesty rule:** it never fabricates eligibility. `likely_blocked` means *tell the user before they spend the time*; `review` means *these need an honest answer*.

### 2. Answer memory — `answers.py`
A private, local library so the same form questions aren't re-answered from scratch every time (`~/.rebound/data/answers.json`).
```bash
python3 .../answers.py suggest "Why do you want to work here?"   # reuse a prior answer
python3 .../answers.py add-qa "<question>" "<answer>"             # remember a new one
python3 .../answers.py set-reusable salary_expectation "<value>"
```
- `suggest` finds a previously-answered question by overlap so you can adapt it rather than start blank.
- Store the user's **real words** only. Never invent salary, notice period, or eligibility.

## The flow (driven by `/rebound:apply`)
1. **Knockout first.** Parse the JD → `requirements`; run `knockout.py`. If `likely_blocked`, surface the hard flags and ask the user whether to continue *before* doing the work.
2. **Tailor** the résumé (use the `resume-tailoring` + `resume-export` skills) — honest, JD-aligned, `.docx` for portals.
3. **Draft the form answers.** For each recurring question, `suggest` a prior answer and adapt it to this role; draft new ones from the profile, honestly and specifically (specificity is the anti-generic signal). Save reusable ones back with `add-qa` / `set-reusable`.
4. **Draft a "why this company" note** — short, specific, grounded in real company research + the profile; include the honest one-line gap/layoff framing if relevant.
5. **Assemble the packet** in the output folder: the résumé (`.docx` + `.pdf`), `answers.md` (Q→A), `cover_note.md`, and `knockout.md` (the flags). Tell the user exactly what still needs a human decision.
6. **Offer to `/rebound:track add`** the application so it lands on the dashboard.

## Rules
- **Assist, never auto-submit.** The user reviews every answer and clicks submit. This is the honest middle path — and the defensible one.
- Never fabricate an answer, a number, or eligibility. `unknown`/`needs your input` beats a made-up answer.
- The private `situation` never goes into a packet artifact.
