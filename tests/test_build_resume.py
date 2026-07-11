"""Tests for the résumé generator (skills/resume-export/scripts/build_resume.py).

Runs the generator as the plugin does (as a subprocess over a JSON config) and
asserts the produced .docx is single-column, ATS-safe, and preserves the real
text (with inline **bold**/*italic* markers stripped to plain runs).
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "resume-export" / "scripts" / "build_resume.py"

# python-docx is required both to run the generator and to read the output back.
docx = pytest.importorskip("docx")


def _build(cfg, out_path):
    cfg = dict(cfg)
    cfg["out"] = str(out_path)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(cfg, f)
        cfg_path = f.name
    try:
        subprocess.run(
            [sys.executable, str(SCRIPT), cfg_path],
            check=True, capture_output=True, text=True,
        )
    finally:
        os.unlink(cfg_path)


def _all_text(path):
    d = docx.Document(str(path))
    return "\n".join(p.text for p in d.paragraphs)


def test_generates_docx_with_expected_content(tmp_path):
    out = tmp_path / "resume.docx"
    _build(
        {
            "name": "JANE DOE",
            "title": "Senior Software Engineer",
            "contact": "jane@example.com | City, ST",
            "summary": "Backend engineer with **distributed systems** depth.",
            "sections": [
                {
                    "heading": "Experience",
                    "type": "experience",
                    "roles": [
                        {
                            "title": "Senior Engineer — ACME",
                            "meta": "Remote | 2022 - Present",
                            "bullets": ["**Led** a migration cutting p99 latency by 40%."],
                        }
                    ],
                },
                {
                    "heading": "Skills",
                    "type": "skills",
                    "skills": [{"label": "Languages", "items": "Go, Python"}],
                },
            ],
        },
        out,
    )
    assert out.exists() and out.stat().st_size > 0
    text = _all_text(out)
    assert "JANE DOE" in text
    # Inline bold markers are stripped, the words survive:
    assert "distributed systems" in text
    assert "Led" in text and "p99 latency" in text
    assert "Go, Python" in text


def test_output_is_single_column_ats_safe(tmp_path):
    """ATS-safe means no tables / columns — the generator must never emit tables."""
    out = tmp_path / "ats.docx"
    _build(
        {"name": "X", "sections": [{"heading": "S", "type": "bullets", "bullets": ["a bullet"]}]},
        out,
    )
    d = docx.Document(str(out))
    assert len(d.tables) == 0
    assert len(d.sections) == 1  # single section, single column


def test_missing_config_arg_exits_nonzero():
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode != 0
