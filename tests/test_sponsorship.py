"""Offline tests for the H-1B sponsorship signal (no USCIS download needed).

Uses a tiny synthetic CSV in the real Employer Data Hub column shape.
"""
import io
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "sponsorship-signal" / "scripts"))

import sponsorship as sp  # noqa: E402

# Mirrors the USCIS H-1B Employer Data Hub export headers.
CSV = """Fiscal Year,Employer (Petitioner) Name,Tax ID,Industry (NAICS) Code,Petitioner City,Petitioner State,Petitioner Zip Code,Initial Approval,Initial Denial,Continuing Approval,Continuing Denial
2024,"AMAZON.COM SERVICES LLC",111,54,Seattle,WA,98109,"4,000",50,"6,000",20
2023,"AMAZON.COM SERVICES LLC",111,54,Seattle,WA,98109,"3,500",40,"5,500",15
2024,"TINY STARTUP INC",222,54,Austin,TX,73301,3,0,1,0
2024,"MOSTLY TRANSFERS CORP",333,54,Reston,VA,20190,0,0,12,1
"""


def _index():
    return sp.build_index(csv.DictReader(io.StringIO(CSV)))


def test_build_index_aggregates_across_years():
    idx = _index()
    amazon = idx[sp.normalize_employer("AMAZON.COM SERVICES LLC")]
    assert amazon["initial"] == 7500      # 4000 + 3500 across two fiscal years
    assert amazon["continuing"] == 11500  # 6000 + 5500
    assert amazon["years"] == ["2023", "2024"]


def test_normalize_strips_legal_suffixes():
    assert sp.normalize_employer("Amazon.com Services LLC") == "amazon com services"
    assert sp.normalize_employer("Tiny Startup, Inc.") == "tiny startup"


def test_lookup_exact_and_fuzzy():
    idx = _index()
    # Fuzzy: user types "Amazon", data says "AMAZON.COM SERVICES LLC"
    r = sp.lookup(idx, "Amazon")
    assert r["matched"] == "AMAZON.COM SERVICES LLC"
    assert r["likelihood"] == "high"
    assert r["initial_approvals"] == 7500


def test_classify_thresholds():
    idx = _index()
    assert sp.lookup(idx, "Tiny Startup")["likelihood"] == "low"        # 3 initial
    assert sp.lookup(idx, "Mostly Transfers")["likelihood"] == "low"    # 0 initial, some continuing
    assert sp.lookup(idx, "Nonexistent Co")["likelihood"] == "unknown"  # no match


def test_unknown_is_not_a_negative():
    idx = _index()
    r = sp.lookup(idx, "Brand New Ai Lab")
    assert r["matched"] is None
    assert r["likelihood"] == "unknown"
    assert "won't" not in r["note"].lower()  # never implies "won't sponsor"


def test_annotate_adds_signal_to_roles():
    idx = _index()
    roles = [
        {"company": "AMAZON.COM SERVICES LLC", "title": "SWE"},
        {"company": "Nonexistent Co", "title": "SWE"},
    ]
    out = sp.annotate(idx, roles)
    assert out[0]["sponsor_signal"]["likelihood"] == "high"
    assert out[1]["sponsor_signal"]["likelihood"] == "unknown"


def test_build_index_missing_name_column_raises():
    import pytest
    with pytest.raises(ValueError):
        sp.build_index(csv.DictReader(io.StringIO("Foo,Bar\n1,2\n")))
