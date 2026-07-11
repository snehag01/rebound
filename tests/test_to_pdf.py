"""Tests for the PDF text-layer verifier (skills/resume-export/scripts/to_pdf.py).

The core promise Rebound makes is that its PDFs are *text-based* (ATS-readable),
never scanned images. `verify_text_layer` is what enforces that, so it gets
direct unit coverage — both the positive (real text) and negative (image-only)
cases, with compressed and uncompressed content streams.
"""
import pathlib
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "resume-export" / "scripts"))

import to_pdf  # noqa: E402


def _pdf_with_stream(payload: bytes, compress: bool = True) -> bytes:
    body = zlib.compress(payload) if compress else payload
    return b"%PDF-1.7\n1 0 obj\n<< >>\nstream\n" + body + b"\nendstream\nendobj\n%%EOF"


def test_detects_real_text_layer(tmp_path):
    p = tmp_path / "text.pdf"
    p.write_bytes(_pdf_with_stream(b"BT /F1 12 Tf (Hello world) Tj ET"))
    good, bt, tj = to_pdf.verify_text_layer(str(p))
    assert good is True
    assert bt >= 1 and tj >= 1


def test_flags_image_only_pdf(tmp_path):
    """A scanned/image PDF has drawing ops but no BT/Tj text operators."""
    p = tmp_path / "image.pdf"
    p.write_bytes(_pdf_with_stream(b"q 100 0 0 100 0 0 cm /Im0 Do Q"))
    good, bt, tj = to_pdf.verify_text_layer(str(p))
    assert good is False


def test_handles_uncompressed_stream(tmp_path):
    p = tmp_path / "raw.pdf"
    p.write_bytes(_pdf_with_stream(b"BT (hi) Tj ET", compress=False))
    good, _, _ = to_pdf.verify_text_layer(str(p))
    assert good is True


def test_counts_tj_array_operator(tmp_path):
    """The TJ (array show) operator must count as text, not just Tj."""
    p = tmp_path / "tj.pdf"
    p.write_bytes(_pdf_with_stream(b"BT [(a) -250 (b)] TJ ET"))
    good, _, tj = to_pdf.verify_text_layer(str(p))
    assert good is True and tj >= 1
