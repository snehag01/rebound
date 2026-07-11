"""Offline tests for the job-discovery normalizers (no network).

Each ATS returns a different JSON shape; these lock in the mapping to Rebound's
normalized schema and the text/remote/keyword helpers.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "job-discovery" / "scripts"))

import fetch_jobs as fj  # noqa: E402

NORM_KEYS = {"source", "company", "id", "title", "location", "remote", "url", "posted", "description"}


def test_greenhouse_normalizer():
    data = {"jobs": [{
        "id": 123, "title": "Senior Backend Engineer",
        "location": {"name": "Remote - US"},
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
        "updated_at": "2026-07-05T10:00:00-04:00",
        "content": "&lt;p&gt;Build &lt;strong&gt;distributed systems&lt;/strong&gt; in Go.&lt;/p&gt;",
    }]}
    jobs = fj.normalize_greenhouse("acme", data)
    assert len(jobs) == 1
    j = jobs[0]
    assert set(j) == NORM_KEYS
    assert j["source"] == "greenhouse" and j["company"] == "acme" and j["id"] == "123"
    assert j["title"] == "Senior Backend Engineer"
    assert j["remote"] is True
    assert j["url"].endswith("/123")
    # HTML entities + tags are stripped from the description:
    assert "distributed systems" in j["description"]
    assert "<" not in j["description"] and "&lt;" not in j["description"]


def test_lever_normalizer_epoch_and_list():
    data = [{
        "id": "abc", "text": "Platform Engineer",
        "categories": {"location": "New York", "commitment": "Full-time"},
        "hostedUrl": "https://jobs.lever.co/acme/abc",
        "createdAt": 1751731200000,  # ms epoch
        "descriptionPlain": "Own the platform.",
    }]
    jobs = fj.normalize_lever("acme", data)
    assert jobs[0]["title"] == "Platform Engineer"
    assert jobs[0]["location"] == "New York"
    assert jobs[0]["remote"] is False
    assert jobs[0]["posted"] and jobs[0]["posted"].count("-") == 2  # YYYY-MM-DD


def test_ashby_normalizer_prefers_explicit_remote_flag():
    data = {"jobs": [{
        "id": "x1", "title": "SRE", "location": "Berlin", "isRemote": False,
        "jobUrl": "https://jobs.ashbyhq.com/acme/x1", "publishedDate": "2026-07-01",
        "descriptionPlain": "Keep it up.",
    }]}
    j = fj.normalize_ashby("acme", data)[0]
    assert j["remote"] is False  # honors the explicit flag even though location isn't "remote"
    assert j["url"].endswith("/x1")


def test_smartrecruiters_builds_location_and_url():
    data = {"content": [{
        "id": "9", "name": "Data Engineer",
        "location": {"city": "Austin", "region": "TX", "country": "US", "remote": False},
        "releasedDate": "2026-06-20",
    }]}
    j = fj.normalize_smartrecruiters("acme", data)[0]
    assert j["location"] == "Austin, TX, US"
    assert j["url"] == "https://jobs.smartrecruiters.com/acme/9"


def test_keyword_filter_matches_title_or_description():
    job = {"title": "Backend Engineer", "location": "Remote", "description": "Go and Kubernetes."}
    assert fj.matches(job, ["kubernetes"]) is True   # case-insensitive, in description
    assert fj.matches(job, ["rust"]) is False
    assert fj.matches(job, None) is True             # no filter → keep


def test_unknown_source_raises():
    import pytest
    with pytest.raises(ValueError):
        fj.fetch("workday", "acme")


def test_text_helper_truncates():
    long = "word " * 400
    out = fj._text(long, limit=100)
    assert len(out) <= 101 and out.endswith("…")
