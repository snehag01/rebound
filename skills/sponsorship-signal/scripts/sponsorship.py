#!/usr/bin/env python3
"""
Rebound — H-1B sponsorship signal from official public data.

Builds a local index from the **USCIS H-1B Employer Data Hub** export (a public,
downloadable CSV of petition approvals/denials by employer and fiscal year) and
answers, per employer: *does this company actually file H-1B petitions, and how
much?* — a fresh-ish, defensible "will they sponsor?" signal to prioritize roles.

It does NOT scrape, and it is NOT legal advice. See the sponsorship-signal SKILL
for how to obtain the CSV, the freshness caveats (annual data; LCA != petition
!= approval), and the 2026 context (wage-level-weighted selection + the $100k
supplemental fee) that make this signal newly decisive.

Usage:
  python3 sponsorship.py build <uscis_hub.csv> [--out ~/.rebound/data/h1b_index.json]
  python3 sponsorship.py lookup "<employer name>" [--index <index.json>]
  python3 sponsorship.py annotate <roles.json> [--index <index.json>] [--out <file>]
    # roles.json is /rebound:discover output; adds a "sponsor_signal" to each role.
"""
import argparse
import csv
import json
import os
import re
import sys

DEFAULT_INDEX = os.path.expanduser("~/.rebound/data/h1b_index.json")

# Dropped when normalizing an employer name (legal form / filler).
_SUFFIXES = {
    "inc", "llc", "llp", "lp", "ltd", "limited", "corp", "corporation", "co",
    "company", "the", "plc", "gmbh", "sa", "ag", "nv", "bv", "pvt", "private",
    "usa", "us", "na", "holdings", "holding", "group",
}
# De-weighted (generic) tokens — kept in the name but ignored when fuzzy-matching.
_GENERIC = {
    "services", "service", "technologies", "technology", "tech", "solutions",
    "systems", "system", "software", "labs", "lab", "global", "international",
    "worldwide", "america", "americas", "consulting", "digital", "data",
}


def normalize_employer(name):
    n = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower())
    toks = [t for t in n.split() if t and t not in _SUFFIXES]
    return " ".join(toks)


def _core(name):
    return {t for t in normalize_employer(name).split() if t not in _GENERIC}


def _to_int(v):
    try:
        return int(str(v).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0


def _find_col(headers, *needles):
    for h in headers:
        hl = h.lower()
        if all(n in hl for n in needles):
            return h
    return None


def build_index(rows):
    """rows: iterable of dicts (csv.DictReader). Returns {normalized_employer: {...}}."""
    rows = iter(rows)
    try:
        first = next(rows)
    except StopIteration:
        return {}
    headers = list(first.keys())
    name_c = _find_col(headers, "employer") or _find_col(headers, "petitioner")
    init_c = _find_col(headers, "initial", "approval")
    cont_c = _find_col(headers, "continuing", "approval")
    year_c = _find_col(headers, "fiscal")
    if not name_c:
        raise ValueError("could not find an employer/petitioner name column in: %s" % headers)

    index = {}
    for row in _chain(first, rows):
        raw = (row.get(name_c) or "").strip()
        if not raw:
            continue
        key = normalize_employer(raw)
        if not key:
            continue
        e = index.setdefault(key, {"display": raw, "initial": 0, "continuing": 0, "years": []})
        e["initial"] += _to_int(row.get(init_c)) if init_c else 0
        e["continuing"] += _to_int(row.get(cont_c)) if cont_c else 0
        if year_c:
            y = str(row.get(year_c) or "").strip()
            if y and y not in e["years"]:
                e["years"].append(y)
    for e in index.values():
        e["years"].sort()
    return index


def _chain(first, rest):
    yield first
    for r in rest:
        yield r


def classify(initial, continuing):
    """Honest heuristic. 'initial' approvals ~ new/cap petitions => the real
    'will they sponsor a new hire?' signal; 'continuing' ~ transfers/extensions."""
    if initial >= 50:
        return "high", "files many new H-1B petitions (%d initial approvals)" % initial
    if initial >= 5:
        return "medium", "files some new H-1B petitions (%d initial approvals)" % initial
    if initial + continuing > 0:
        return "low", "little/no new filing (%d initial, %d continuing)" % (initial, continuing)
    return "none", "no H-1B approvals in the indexed data"


def lookup(index, employer):
    norm = normalize_employer(employer)
    entry = index.get(norm)
    if not entry:
        q = _core(employer)
        best = None
        if q:
            for key, e in index.items():
                kt = _core(key)
                if not kt:
                    continue
                # subset match either direction (e.g. "amazon" ~ "amazon com services")
                if q <= kt or kt <= q:
                    if best is None or e["initial"] > best[1]["initial"]:
                        best = (key, e)
        if best:
            entry = best[1]
    if not entry:
        return {"query": employer, "matched": None, "likelihood": "unknown",
                "note": "no match in the H-1B index (may still sponsor — data is not exhaustive)"}
    lk, note = classify(entry["initial"], entry["continuing"])
    return {
        "query": employer, "matched": entry["display"],
        "initial_approvals": entry["initial"], "continuing_approvals": entry["continuing"],
        "years": entry.get("years", []), "wage_level": "unknown",  # populated from DOL FLAG in a follow-up
        "likelihood": lk, "note": note,
    }


def annotate(index, roles):
    for r in roles:
        r["sponsor_signal"] = lookup(index, r.get("company") or r.get("matched") or "")
    return roles


# ---- CLI --------------------------------------------------------------------

def _load_index(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rebound H-1B sponsorship signal (official USCIS data).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build the local index from a USCIS Data Hub CSV")
    b.add_argument("csv")
    b.add_argument("--out", default=DEFAULT_INDEX)

    lk = sub.add_parser("lookup", help="look up one employer")
    lk.add_argument("employer")
    lk.add_argument("--index", default=DEFAULT_INDEX)

    an = sub.add_parser("annotate", help="annotate /rebound:discover roles JSON with sponsor signals")
    an.add_argument("roles")
    an.add_argument("--index", default=DEFAULT_INDEX)
    an.add_argument("--out")

    a = ap.parse_args(argv)

    if a.cmd == "build":
        with open(a.csv, newline="", encoding="utf-8-sig") as f:
            index = build_index(csv.DictReader(f))
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(index, f)
        print("Indexed %d employers -> %s" % (len(index), a.out))
    elif a.cmd == "lookup":
        print(json.dumps(lookup(_load_index(a.index), a.employer), indent=2, ensure_ascii=False))
    elif a.cmd == "annotate":
        with open(a.roles, encoding="utf-8") as f:
            roles = json.load(f)
        roles = annotate(_load_index(a.index), roles)
        out = json.dumps(roles, indent=2, ensure_ascii=False)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(out)
            print("Annotated %d roles -> %s" % (len(roles), a.out))
        else:
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
