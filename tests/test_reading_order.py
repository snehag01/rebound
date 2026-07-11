"""Tests for reading-order verification in to_pdf.py.

The pure pieces (`_in_order`, `_strings_from_stream`, `_extract_stdlib`) are
tested directly; `verify_reading_order` is driven with the stdlib extractor so
the result is deterministic regardless of whether poppler/pdfminer are installed.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "resume-export" / "scripts"))

import to_pdf  # noqa: E402


def _pdf(*payloads):
    body = b"%PDF-1.7\n"
    for p in payloads:
        body += b"1 0 obj\n<< >>\nstream\n" + p + b"\nendstream\nendobj\n"
    return body + b"%%EOF"


def test_in_order_accepts_correct_sequence():
    ok, bad = to_pdf._in_order("JANE DOE  SUMMARY  EXPERIENCE  SKILLS", ["Jane Doe", "Experience", "Skills"])
    assert ok is True and bad is None


def test_in_order_rejects_scrambled_sequence():
    ok, bad = to_pdf._in_order("JANE DOE  SKILLS  EXPERIENCE", ["Experience", "Skills"])
    assert ok is False and bad == "skills"  # Skills wanted before Experience, appears after


def test_in_order_rejects_missing_anchor():
    ok, bad = to_pdf._in_order("JANE DOE  EXPERIENCE", ["Jane Doe", "Publications"])
    assert ok is False and bad == "publications"


def test_strings_from_stream_preserves_order_and_escapes():
    s = b"BT (JANE DOE) Tj (Skills: C\\(++\\)) Tj ET"
    out = to_pdf._strings_from_stream(s)
    assert out.index("JANE DOE") < out.index("Skills")
    assert "C(++)" in out  # escaped parens decoded


def test_extract_stdlib_reads_stream_order():
    pdf = _pdf(b"BT (JANE DOE) Tj (EXPERIENCE) Tj (SKILLS) Tj ET")
    p = ROOT / "tests" / "_tmp_order.pdf"
    p.write_bytes(pdf)
    try:
        text = to_pdf._extract_stdlib(str(p))
        assert text.index("JANE DOE") < text.index("EXPERIENCE") < text.index("SKILLS")
    finally:
        p.unlink()


def test_verify_reading_order_pass_and_fail(tmp_path):
    p = tmp_path / "resume.pdf"
    p.write_bytes(_pdf(b"BT (JANE DOE) Tj (SUMMARY) Tj (EXPERIENCE) Tj (SKILLS) Tj ET"))

    ok, bad = to_pdf.verify_reading_order(
        str(p), ["Jane Doe", "Summary", "Experience", "Skills"], extractor=to_pdf._extract_stdlib
    )
    assert ok is True and bad is None

    # Ask for Skills before Experience → must fail (they're scrambled vs the doc).
    ok, bad = to_pdf.verify_reading_order(
        str(p), ["Skills", "Experience"], extractor=to_pdf._extract_stdlib
    )
    assert ok is False and bad == "experience"


def test_verify_text_layer_still_works(tmp_path):
    """Regression: the original text-layer check is untouched."""
    p = tmp_path / "t.pdf"
    p.write_bytes(_pdf(b"BT (hello) Tj ET"))
    good, bt, tj = to_pdf.verify_text_layer(str(p))
    assert good is True and bt >= 1 and tj >= 1
