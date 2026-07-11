#!/usr/bin/env python3
"""
Rebound — application answer memory.

A private, local library of the user's honest, reusable answers to the questions
application forms ask over and over (salary expectation, notice period,
"why this company", work-mode, common screening questions). /rebound:apply drafts
each answer per-application and saves the reusable ones here, so the next form is
mostly done — the single biggest reduction in apply-tedium.

Local only. Answers are the user's real words, never fabricated, never transmitted.

Store: ~/.rebound/data/answers.json
  {"reusable": {"salary_expectation": "...", "notice_period": "...", ...},
   "questions": [{"q": "...", "a": "...", "tags": [...]}]}

Usage:
  python3 answers.py get [--store f]
  python3 answers.py set-reusable <key> <value> [--store f]
  python3 answers.py add-qa "<question>" "<answer>" [--store f]
  python3 answers.py suggest "<question>" [--store f]   # reuse a prior answer
"""
import json
import os
import re
import sys

DEFAULT_STORE = os.path.expanduser("~/.rebound/data/answers.json")

_STOP = {"the", "and", "for", "with", "you", "your", "our", "are", "do", "does",
         "did", "what", "why", "how", "when", "where", "would", "will", "this",
         "that", "a", "an", "of", "in", "to", "is", "it", "at", "on", "we"}


def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9]{3,}", (s or "").lower()) if w not in _STOP}


def load(store=DEFAULT_STORE):
    if os.path.exists(store):
        with open(store, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("reusable", {})
    data.setdefault("questions", [])
    return data


def save(data, store=DEFAULT_STORE):
    os.makedirs(os.path.dirname(os.path.abspath(store)), exist_ok=True)
    with open(store, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return store


def set_reusable(data, key, value):
    data.setdefault("reusable", {})[key] = value
    return data


def add_qa(data, question, answer, tags=None):
    qs = data.setdefault("questions", [])
    for qa in qs:  # update in place if the same question already exists
        if _tokens(qa.get("q", "")) == _tokens(question):
            qa["a"] = answer
            if tags:
                qa["tags"] = tags
            return data
    qs.append({"q": question, "a": answer, "tags": tags or []})
    return data


def suggest(data, question, threshold=0.34):
    """Find a previously-answered question to reuse, by Jaccard token overlap."""
    q = _tokens(question)
    best, best_score = None, 0.0
    if q:
        for qa in data.get("questions", []):
            t = _tokens(qa.get("q", ""))
            if not t:
                continue
            score = len(q & t) / len(q | t)
            if score > best_score:
                best, best_score = qa, score
    return {"match": best if best and best_score >= threshold else None,
            "score": round(best_score, 2)}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    store = DEFAULT_STORE
    if "--store" in argv:
        i = argv.index("--store")
        store = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    data = load(store)

    if cmd == "get":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif cmd == "set-reusable" and len(rest) >= 2:
        save(set_reusable(data, rest[0], " ".join(rest[1:])), store)
        print("Saved reusable answer: %s" % rest[0])
    elif cmd == "add-qa" and len(rest) >= 2:
        save(add_qa(data, rest[0], rest[1]), store)
        print("Saved answer for: %s" % rest[0])
    elif cmd == "suggest" and rest:
        print(json.dumps(suggest(data, rest[0]), indent=2, ensure_ascii=False))
    else:
        print("bad usage; see --help / docstring", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
