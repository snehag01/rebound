---
name: job-discovery
description: Find fresh, relevant roles the honest, legally-clean way — via the public official ATS job APIs (Greenhouse, Lever, Ashby, SmartRecruiters) rather than scraping behind logins. Use whenever discovering or refreshing roles for the user to consider.
---

# Job Discovery — official APIs first, never scrape behind a login

Rebound discovers roles the same way it writes résumés: **honestly and defensibly.** The goal is a fresh, relevant list of *real* openings the user can act on — not a spam list, and never at the cost of the user's accounts or a Terms-of-Service violation.

## The risk model (why we only use certain sources)

Public, logged-out job data is not a computer-crime to read (post-*hiQ v. LinkedIn*), but the enforceable risk moved to **contract/ToS breach** (which turns on whether you logged in and assented) and **trespass-to-chattels** (which turns on server load). So Rebound draws a hard line:

- ✅ **Use — official public ATS endpoints.** Vendors publish these *so that jobs get syndicated*. No auth, no assent, employer-intended. This is the backbone.
- ✅ **Use — official aggregator APIs** (e.g., Adzuna's free developer tier) and **`JobPosting` JSON-LD** embedded in public career pages (the publisher put it there for machines).
- ✅ **Use — user-authorized fetching:** the user is logged into their own account and asks Rebound to read a page they can already see.
- ⚠️ **Only with care — public logged-out scraping** (e.g., a Workday `myworkdayjobs` JSON page): don't create accounts or defeat anti-bot measures, rate-limit hard, respect `robots.txt`, take only factual job data.
- 🚫 **Never — anything behind a login, especially LinkedIn / Indeed.** Closed/partner-only APIs, active litigation, and you assent to the ToS the moment you log in. Keep them out of automated discovery entirely.

> This is a risk model, not legal advice. Anything in the ⚠️ tier should get a data/tech-attorney review before it ships in a product.

## The fetcher

`scripts/fetch_jobs.py` pulls and normalizes postings from the official endpoints:

| Source | Endpoint | Company "token" |
|---|---|---|
| `greenhouse` | `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | slug in `boards.greenhouse.io/<token>` |
| `lever` | `api.lever.co/v0/postings/{token}?mode=json` | slug in `jobs.lever.co/<token>` |
| `ashby` | `api.ashbyhq.com/posting-api/job-board/{token}` | slug in `jobs.ashbyhq.com/<token>` |
| `smartrecruiters` | `api.smartrecruiters.com/v1/companies/{token}/postings` | company identifier |

```bash
# One company:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/job-discovery/scripts/fetch_jobs.py" greenhouse stripe --keywords "backend,go" --limit 25

# Many at once (JSON: [{"source","token"}, ...]):
python3 "${CLAUDE_PLUGIN_ROOT}/skills/job-discovery/scripts/fetch_jobs.py" --spec sources.json --keywords "platform,distributed" --out /tmp/roles.json
```

It is **stdlib-only** (no dependencies), and returns a normalized list:
`{source, company, id, title, location, remote, url, posted, description}`.

## How to use it in a flow

1. **Get the target set.** Ask the user for target companies (or maintain a per-user `~/.rebound/data/sources.json`). If you only have a company name, help them find the board slug (the careers URL usually reveals which ATS + token).
2. **Fetch + keyword-filter** with the script. Keywords should come from the user's `primary_stack` + `target_roles`, not a generic head term.
3. **Score fit locally** against `~/.rebound/profile.json` using the same weighting as `/rebound:match` (required 70% / preferred 30%, real evidence only; partial credit for "working knowledge"; no credit for untouched tech). Be honest — an inflated score wastes scarce time.
4. **Respect the situation.** If `situation.work_authorization` requires sponsorship, flag roles that likely can't sponsor; never surface the situation itself.
5. **Rank and hand off** — recommend the top roles to `/rebound:tailor`, and offer to `/rebound:track add` them so they land on the dashboard.

## Honesty rules
- Only surface **real, currently-listed** roles from the fetched data — never invent a company, role, or URL.
- Deduplicate by `company + title + location`; note freshness from `posted` and say when a source returned nothing.
- If a source errors or a company's ATS isn't supported, say so plainly rather than silently dropping it.
