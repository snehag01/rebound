"""Tests for the knockout pre-check (skills/application-packet/scripts/knockout.py)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "application-packet" / "scripts"))

import knockout as ko  # noqa: E402

PROFILE = {
    "years_experience": "5 years",
    "situation": {"work_mode": "remote", "locations": ["Remote", "Austin, TX"]},
    "education": ["B.S. Computer Science — State University"],
}


def test_experience_gap_of_three_is_hard():
    r = ko.check({"min_years": 8}, PROFILE)
    assert r["verdict"] == "likely_blocked"
    assert any(f["type"] == "experience" and f["severity"] == "hard" for f in r["flags"])


def test_experience_gap_of_one_is_soft():
    r = ko.check({"min_years": 6}, PROFILE)
    assert r["verdict"] == "review"
    assert any(f["type"] == "experience" and f["severity"] == "soft" for f in r["flags"])


def test_onsite_when_targeting_remote_is_hard():
    r = ko.check({"work_mode": "onsite", "location": "New York, NY"}, PROFILE)
    assert r["verdict"] == "likely_blocked"
    assert any(f["type"] == "work_mode" and f["severity"] == "hard" for f in r["flags"])


def test_clearance_requirement_is_hard():
    r = ko.check({"clearance": True}, PROFILE)
    assert r["verdict"] == "likely_blocked"
    assert any(f["type"] == "clearance" for f in r["flags"])


def test_higher_degree_requirement_is_soft():
    r = ko.check({"degree": "Master's"}, PROFILE)  # profile has a B.S.
    assert any(f["type"] == "education" and f["severity"] == "soft" for f in r["flags"])


def test_met_degree_is_not_flagged():
    r = ko.check({"degree": "Bachelor"}, PROFILE)
    assert not any(f["type"] == "education" for f in r["flags"])


def test_unmet_must_have_is_soft():
    r = ko.check({"must_have": ["active CPA license"]}, PROFILE)
    assert any(f["type"] == "requirement" for f in r["flags"])


def test_all_requirements_met_is_clear():
    r = ko.check({"min_years": 3, "work_mode": "remote"}, PROFILE)
    assert r["verdict"] == "clear"
    assert r["flags"] == []
