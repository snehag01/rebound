#!/usr/bin/env python3
"""
Rebound — honest, legally-clean job discovery.

Pulls fresh postings from the PUBLIC, official job-board JSON endpoints that ATS
vendors publish for syndication. No login, no scraping behind auth, no
ToS-violating automation — only endpoints employers deliberately expose so their
jobs can be distributed. See the job-discovery SKILL for the full risk model and
which sources to avoid (LinkedIn/Indeed: closed APIs + active litigation — out).

Supported sources (the "token" is the company's board slug in its careers URL):
  greenhouse       boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
  lever            api.lever.co/v0/postings/{token}?mode=json
  ashby            api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true
  smartrecruiters  api.smartrecruiters.com/v1/companies/{token}/postings

Usage:
  python3 fetch_jobs.py <source> <token> [--keywords a,b,c] [--limit N] [--out file.json]
  python3 fetch_jobs.py --spec sources.json      # [{"source": "...", "token": "..."}, ...]

Output: a normalized JSON list, each item:
  {source, company, id, title, location, remote, url, posted, description}

Discovery ONLY. Fit scoring against your profile, sponsorship checks, and
tailoring are done by the /rebound:discover command — never here, and never
against your private `situation`. Not legal advice.
"""
import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request

TIMEOUT = 20
UA = "Rebound-JobDiscovery/0.1 (+https://github.com/snehag01/rebound)"

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{token}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{token}/postings",
}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _text(raw, limit=600):
    """HTML/entity-strip a description and truncate — discovery needs a gist, not the full JD."""
    if not raw:
        return None
    t = _WS.sub(" ", _TAG.sub(" ", html.unescape(str(raw)))).strip()
    return (t[:limit] + "…") if len(t) > limit else t


def _remote(*fields):
    """Best-effort remote flag from any location/title/commitment text."""
    blob = " ".join(str(f) for f in fields if f).lower()
    if not blob:
        return None
    return "remote" in blob or "anywhere" in blob


def _ms_to_date(ms):
    """Lever timestamps are epoch-ms; return a YYYY-MM-DD string without wall-clock deps."""
    try:
        import datetime
        return datetime.datetime.fromtimestamp(
            int(ms) / 1000, datetime.timezone.utc
        ).strftime("%Y-%m-%d")
    except Exception:
        return None


def _job(source, company, jid, title, location, remote, url, posted, description):
    return {
        "source": source, "company": company, "id": str(jid) if jid is not None else None,
        "title": title, "location": location, "remote": remote,
        "url": url, "posted": posted, "description": description,
    }


# ---- normalizers (pure; unit-tested offline) --------------------------------

def normalize_greenhouse(company, data):
    out = []
    for j in (data or {}).get("jobs", []):
        loc = (j.get("location") or {}).get("name")
        out.append(_job("greenhouse", company, j.get("id"), j.get("title"), loc,
                        _remote(loc, j.get("title")), j.get("absolute_url"),
                        j.get("updated_at"), _text(j.get("content"))))
    return out


def normalize_lever(company, data):
    out = []
    for j in (data or []):
        cats = j.get("categories") or {}
        loc = cats.get("location")
        out.append(_job("lever", company, j.get("id"), j.get("text"), loc,
                        _remote(loc, cats.get("commitment"), cats.get("workplaceType")),
                        j.get("hostedUrl"), _ms_to_date(j.get("createdAt")),
                        _text(j.get("descriptionPlain") or j.get("description"))))
    return out


def normalize_ashby(company, data):
    out = []
    for j in (data or {}).get("jobs", []):
        loc = j.get("location")
        remote = j.get("isRemote")
        out.append(_job("ashby", company, j.get("id"), j.get("title"), loc,
                        remote if remote is not None else _remote(loc),
                        j.get("jobUrl") or j.get("applyUrl"),
                        j.get("publishedDate") or j.get("publishedAt"),
                        _text(j.get("descriptionPlain") or j.get("description"))))
    return out


def normalize_smartrecruiters(company, data):
    out = []
    for j in (data or {}).get("content", []):
        loc = j.get("location") or {}
        parts = [loc.get("city"), loc.get("region"), loc.get("country")]
        locstr = ", ".join(p for p in parts if p) or None
        url = "https://jobs.smartrecruiters.com/{c}/{i}".format(c=company, i=j.get("id"))
        out.append(_job("smartrecruiters", company, j.get("id"), j.get("name"), locstr,
                        loc.get("remote"), url, j.get("releasedDate"), None))
    return out


NORMALIZERS = {
    "greenhouse": normalize_greenhouse,
    "lever": normalize_lever,
    "ashby": normalize_ashby,
    "smartrecruiters": normalize_smartrecruiters,
}


def matches(job, keywords):
    if not keywords:
        return True
    hay = " ".join(str(job.get(k) or "") for k in ("title", "location", "description")).lower()
    return any(kw.lower() in hay for kw in keywords)


def fetch(source, token, keywords=None, limit=None):
    """Fetch + normalize one source. Network errors return [] (with a stderr note)."""
    if source not in ENDPOINTS:
        raise ValueError("unknown source '{}' (supported: {})".format(source, ", ".join(ENDPOINTS)))
    url = ENDPOINTS[source].format(token=token)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
        print("WARN: {}/{} — {}".format(source, token, e), file=sys.stderr)
        return []
    jobs = [j for j in NORMALIZERS[source](token, data) if matches(j, keywords)]
    return jobs[:limit] if limit else jobs


def run(specs, keywords=None, limit=None):
    all_jobs = []
    for s in specs:
        all_jobs.extend(fetch(s["source"], s["token"], keywords=keywords, limit=limit))
    return all_jobs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rebound job discovery via official ATS APIs.")
    ap.add_argument("source", nargs="?", help="greenhouse | lever | ashby | smartrecruiters")
    ap.add_argument("token", nargs="?", help="company board slug")
    ap.add_argument("--spec", help="JSON file: [{source, token}, ...]")
    ap.add_argument("--keywords", help="comma-separated title/description filters")
    ap.add_argument("--limit", type=int, help="max results per source")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    a = ap.parse_args(argv)

    keywords = [k.strip() for k in a.keywords.split(",")] if a.keywords else None
    if a.spec:
        with open(a.spec, encoding="utf-8") as f:
            specs = json.load(f)
    elif a.source and a.token:
        specs = [{"source": a.source, "token": a.token}]
    else:
        ap.error("give <source> <token>, or --spec file.json")

    jobs = run(specs, keywords=keywords, limit=a.limit)
    payload = json.dumps(jobs, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print("Wrote {} jobs to {}".format(len(jobs), a.out))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
