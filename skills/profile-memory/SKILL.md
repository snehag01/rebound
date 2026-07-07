---
name: profile-memory
description: How Rebound stores and reuses the user's career profile, including the private "situation" (work authorization, timeline). Use when reading, writing, or reasoning about the saved profile at ~/.rebound/.
---

# Profile & Memory

Rebound persists one profile per machine so the user never re-enters their details. It is the reusable base for every `/rebound:tailor`, `/rebound:match`, and `/rebound:rise`.

## Location & format
- `~/.rebound/profile.json` — machine-readable (authoritative).
- `~/.rebound/profile.md` — human-readable mirror (keep in sync on every write).
- `~/.rebound/pylibs/` — bundled python deps (python-docx).

Create `~/.rebound/` if missing. On updates, rewrite both files and confirm.

## Schema
```json
{
  "name": "", "contact": "", "current_title": "", "years_experience": "",
  "base_resume_path": "",
  "primary_stack": [], "secondary_stack": [], "differentiators": [],
  "roles": [{"title": "", "org": "", "location": "", "dates": "", "bullets": []}],
  "education": [], "certifications": [],
  "situation": {
    "work_authorization": null,      // Citizen | GC | H-1B | F-1 OPT | STEM-OPT | O-1 | TN | needs-sponsorship | null
    "timeline": null,                // absolute dates + runway, e.g. "OPT EAD until 2026-08-15; ~60 days"
    "target_roles": [], "locations": [], "work_mode": null, "notes": null
  },
  "preferences": {
    "framing_notes": [
      "fast learner across stacks; strong OOP/systems fundamentals",
      "surface secondary skills but never above primary stack",
      "honesty-first: never claim expertise in unused tech"
    ]
  }
}
```

## The private "situation" — handle with care
This block is sensitive and personal. Rules:
- **Local only.** Never transmit it to any external service or include it in a resume/PDF.
- **Don't echo** the values unless the user explicitly asks to see them.
- **Use it to serve the user**: set urgency from `timeline`; respect `work_authorization` when judging whether a role must sponsor; prioritize accordingly.
- **Be supportive** — this is often stressful, time-boxed information. Never pressure or judge.

## Reasoning with the profile
- `primary_stack` ranks first in every tailored resume; `secondary_stack` is surfaced only when a JD needs it.
- `differentiators` lead in summaries and referral notes.
- `framing_notes` are defaults applied during tailoring; the user can edit them via `/rebound:profile`.
- Keep the raw `roles[].bullets` verbatim as the truth source; tailoring re-words copies of them, never the stored originals.
