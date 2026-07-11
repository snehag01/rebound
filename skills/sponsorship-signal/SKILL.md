---
name: sponsorship-signal
description: Tell the user whether a company actually sponsors H-1B visas, from official public USCIS data — a fresh, defensible "will they sponsor?" signal to prioritize roles. Use when a sponsorship-dependent user is discovering or ranking companies.
---

# Sponsorship signal — official data, honestly labeled

For a user who needs work sponsorship, the single most time-saving question is **"does this employer actually file H-1B petitions?"** Most tools answer it with stale, retrospective employer profiles. Rebound answers it from the **official public data**, with the freshness limits stated plainly — and never touches the user's private immigration category.

## Why this matters in 2026 (the "why now")
- **Wage-level-weighted selection** (DHS final rule, effective 2026-02-27, governing FY2027) replaces the random lottery with weighting by DOL wage level: **Level IV = 4 entries … Level I = 1.** Which wage level a posting is filed at is now decisive for lottery odds.
- **The $100k supplemental fee** (signed Sept 2025; in active litigation / a circuit split; still being collected as of mid-2026) is shifting employer behavior toward beneficiaries already in the US.

Both make "does this employer sponsor, and roughly how?" a much higher-value signal than a year ago. *(This is context, not legal advice — immigration law here is fast-moving; re-check current status before relying on the fee/wage rules.)*

## Data sources
| Signal | Source | Cadence | Notes |
|---|---|---|---|
| **Sponsor likelihood** (built here) | **USCIS H-1B Employer Data Hub** (petition approvals/denials by employer + fiscal year) | Annual | Public CSV download. `Initial Approval` ≈ new/cap petitions → the real "will they sponsor a new hire?" signal. |
| **Wage level** (follow-up) | **DOL FLAG / OFLC LCA disclosure** data | Quarterly | `PW_WAGE_LEVEL` (I–IV) per case; large Excel files. Populates the `wage_level` field (currently `unknown`). |

**Get the CSV once:** download the H-1B Employer Data Hub file for the fiscal year(s) you want from USCIS (`uscis.gov` → Tools → Reports and Studies → H-1B Employer Data Hub). Then:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sponsorship-signal/scripts/sponsorship.py" build <hub.csv>
# -> ~/.rebound/data/h1b_index.json  (local, reusable)
```

## Using it
```bash
# One company:
python3 .../sponsorship.py lookup "Stripe"

# Annotate discovered roles (from /rebound:discover):
python3 .../sponsorship.py annotate /tmp/rebound_roles.json --out /tmp/rebound_roles_sponsored.json
```
Each result carries `likelihood` (high / medium / low / none / unknown), the matched employer, the approval counts, and a plain-English `note`.

## Honesty rules (critical)
- **State the limits.** The data is annual and retrospective — `LCA ≠ petition ≠ approval`, and *last year's* filings don't guarantee *this* posting. Say `unknown` when there's no match rather than implying "won't sponsor" — a small or newly-growing employer may sponsor without a big footprint.
- **It's a heuristic, labeled as one.** `high/medium/low` come from approval volume (see `classify`), not a promise. Present it to help the user prioritize, never as a guarantee.
- **Never expose the private situation.** Use `situation.work_authorization` only to decide *whether* to run this and how to rank — never print the user's immigration details.
- **Not legal advice.** Encourage a qualified immigration attorney for anything consequential.
