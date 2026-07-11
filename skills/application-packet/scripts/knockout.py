#!/usr/bin/env python3
"""
Rebound — knockout pre-check.

Before a user sinks 30+ minutes into an application, flag the *knockout questions*
they'd likely fail. These (work authorization, minimum years, location/work-mode,
degree, clearance, licenses) are the REAL automated filter — answered on the form,
not scored off the résumé — so catching them up front is pure time saved.

Honesty-first: it says "review" / "verify", never fabricates eligibility, and
distinguishes hard blockers from soft (often-flexible) ones. The JD is parsed into
structured `requirements` by /rebound:apply; this script only does the checking.

Usage:
  python3 knockout.py <requirements.json> <profile.json>

`requirements.json` shape (all optional):
  {"min_years": 8, "location": "New York, NY", "work_mode": "onsite",
   "degree": "Master", "clearance": true, "must_have": ["active US driver's license"]}

Prints: {"verdict": "clear|review|likely_blocked", "flags": [...]}.
"""
import json
import re
import sys

_STOP = {"the", "and", "for", "with", "you", "your", "our", "are", "have", "has",
         "must", "will", "able", "years", "year", "experience", "a", "an", "of", "in", "to"}

_DEG_RANK = [("phd", 4), ("ph.d", 4), ("doctor", 4), ("master", 3), ("m.s", 3),
             ("m.a", 3), ("mba", 3), ("bachelor", 2), ("b.s", 2), ("b.a", 2),
             ("undergraduate", 2), ("associate", 1)]


def _as_int(v):
    try:
        return int(re.search(r"\d+", str(v)).group())
    except (AttributeError, TypeError, ValueError):
        return None


def _profile_text(profile):
    return json.dumps(profile or {}, ensure_ascii=False).lower()


def _deg_level(s):
    s = (s or "").lower()
    lv = 0
    for k, r in _DEG_RANK:
        if k in s:
            lv = max(lv, r)
    return lv


def _loc_match(a, b):
    at = set(re.findall(r"[a-z]{3,}", (a or "").lower()))
    bt = set(re.findall(r"[a-z]{3,}", (b or "").lower()))
    return bool(at & bt)


def _mentions(item, profile):
    txt = _profile_text(profile)
    words = [w for w in re.findall(r"[a-z0-9+.#]{3,}", (item or "").lower()) if w not in _STOP]
    if not words:
        return True
    hits = sum(1 for w in words if w in txt)
    return hits >= max(1, len(words) // 2)


def _f(kind, severity, message, requirement, yours):
    return {"type": kind, "severity": severity, "message": message,
            "requirement": requirement, "yours": yours}


def check(requirements, profile):
    req = requirements or {}
    profile = profile or {}
    sit = profile.get("situation") or {}
    flags = []

    # 1) Years of experience (gap >= 3 is usually a hard wall; 1-2 is often flexible)
    min_y = _as_int(req.get("min_years"))
    yrs = _as_int(profile.get("years_experience"))
    if min_y is not None and yrs is not None and yrs < min_y:
        gap = min_y - yrs
        flags.append(_f("experience", "hard" if gap >= 3 else "soft",
                        "Role asks for %d+ years; profile shows ~%d." % (min_y, yrs),
                        "%d+ yrs" % min_y, "~%d yrs" % yrs))

    # 2) Work mode / location
    mode = (req.get("work_mode") or "").lower()
    loc = req.get("location") or ""
    pref_mode = (sit.get("work_mode") or "").lower()
    locs = [l.lower() for l in (sit.get("locations") or [])]
    user_remote = pref_mode == "remote" or any("remote" in l for l in locs)
    if mode == "onsite" and user_remote and "remote" not in loc.lower():
        flags.append(_f("work_mode", "hard",
                        "Role is onsite in %s; you're targeting remote." % (loc or "a set location"),
                        ("onsite: %s" % loc).strip(": "), "remote"))
    elif mode in ("onsite", "hybrid") and loc and locs and not user_remote \
            and not any(_loc_match(loc, l) for l in locs):
        flags.append(_f("location", "soft",
                        "Role is %s in %s; not in your listed locations." % (mode, loc),
                        "%s: %s" % (mode, loc), ", ".join(locs)))

    # 3) Degree
    if req.get("degree"):
        edu = " ".join(str(e) for e in (profile.get("education") or []))
        if _deg_level(edu) < _deg_level(req.get("degree")):
            flags.append(_f("education", "soft",
                            "Role lists a %s requirement; verify your education covers it." % req.get("degree"),
                            req.get("degree"), (edu[:60] or "none listed")))

    # 4) Security clearance (a genuine hard knockout)
    if req.get("clearance") and "clearance" not in _profile_text(profile):
        flags.append(_f("clearance", "hard",
                        "Role requires a security clearance; none found in your profile.",
                        "clearance required", "none found"))

    # 5) Freeform must-haves (licenses, certifications, specific eligibility)
    for item in (req.get("must_have") or []):
        if not _mentions(item, profile):
            flags.append(_f("requirement", "soft", "Verify you meet: %s" % item,
                            item, "not found in profile"))

    verdict = "likely_blocked" if any(f["severity"] == "hard" for f in flags) \
        else ("review" if flags else "clear")
    return {"verdict": verdict, "flags": flags}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 2:
        print("usage: python3 knockout.py <requirements.json> <profile.json>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as f:
        req = json.load(f)
    with open(argv[1], encoding="utf-8") as f:
        profile = json.load(f)
    print(json.dumps(check(req, profile), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
