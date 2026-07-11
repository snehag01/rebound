#!/usr/bin/env python3
"""
Rebound — convert a .docx resume to a text-based (ATS-readable) PDF and verify it.

Usage:
    python3 to_pdf.py <input.docx> [output.pdf]

Conversion strategy (first that works wins):
  1) LibreOffice / soffice  --headless --convert-to pdf   (cross-platform, no GUI)
  2) macOS Microsoft Word    via AppleScript               (pixel-perfect)
  3) docx2pdf                (Word/pywin32 or macOS)

Then verifies the PDF actually carries an extractable text layer (BT/Tj operators
inside decompressed content streams) so it passes ATS parsers — never a scanned image.

With `--anchors "Name,Experience,Skills"` it also verifies **reading order**: that
those strings extract in that order. A multi-column layout *has* a text layer but
extracts scrambled, which plain text-layer detection cannot catch; this can.
Exit code 0 on success, non-zero otherwise.
"""
import sys, os, re, zlib, subprocess, shutil


def _libreoffice(inp, outdir):
    for exe in ("libreoffice", "soffice",
                "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        path = shutil.which(exe) if not exe.startswith("/") else (exe if os.path.exists(exe) else None)
        if path:
            subprocess.run([path, "--headless", "--convert-to", "pdf", "--outdir", outdir, inp],
                           check=True, capture_output=True, timeout=180)
            return True
    return False


def _word_applescript(inp, outp):
    if sys.platform != "darwin" or not os.path.exists("/Applications/Microsoft Word.app"):
        return False
    script = f'''
    tell application "Microsoft Word"
        activate
        open (POSIX file "{inp}")
        delay 1.2
        set d to active document
        save as d file name "{outp}" file format format PDF
        delay 0.4
        close d saving no
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=180)
    return True


def _docx2pdf(inp, outp):
    try:
        from docx2pdf import convert
    except Exception:
        return False
    convert(inp, outp)
    return True


def verify_text_layer(pdf):
    data = open(pdf, "rb").read()
    bt = tj = 0
    for s in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        try:
            x = zlib.decompress(s)
        except Exception:
            x = s
        bt += x.count(b"BT")
        tj += x.count(b"Tj") + x.count(b"TJ")
    return bt > 0 and tj > 0, bt, tj


def _strings_from_stream(stream):
    """Pull ( ... ) text literals from a content stream, in operator (reading) order."""
    out = []
    i, n = 0, len(stream)
    while i < n:
        if stream[i:i + 1] == b"(":
            j, depth, buf = i + 1, 1, bytearray()
            while j < n and depth > 0:
                ch = stream[j:j + 1]
                if ch == b"\\":
                    nxt = stream[j + 1:j + 2]
                    buf += {b"n": b"\n", b"t": b"\t", b"r": b"\r"}.get(nxt, nxt)
                    j += 2
                    continue
                if ch == b"(":
                    depth += 1
                    buf += ch
                elif ch == b")":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                    buf += ch
                else:
                    buf += ch
                j += 1
            out.append(buf.decode("latin-1", "ignore"))
            i = j
        else:
            i += 1
    return " ".join(out)


def _extract_stdlib(pdf):
    """Dependency-free text extraction in content-stream order — good enough for a
    single-column reading-order check (pdftotext / pdfminer are preferred when present)."""
    data = open(pdf, "rb").read()
    parts = []
    for s in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        try:
            x = zlib.decompress(s)
        except Exception:
            x = s
        parts.append(_strings_from_stream(x))
    return " ".join(parts)


def extract_text_ordered(pdf):
    """Extract text in reading order — poppler `pdftotext`, then pdfminer, then stdlib."""
    try:
        r = subprocess.run(["pdftotext", "-q", pdf, "-"], capture_output=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.decode("utf-8", "ignore")
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text
        t = extract_text(pdf)
        if t and t.strip():
            return t
    except Exception:
        pass
    return _extract_stdlib(pdf)


def _in_order(text, anchors):
    """True iff each anchor appears at/after the previous one (case-insensitive)."""
    hay = (text or "").lower()
    pos = 0
    for a in anchors:
        a = (a or "").strip().lower()
        if not a:
            continue
        idx = hay.find(a, pos)
        if idx < 0:
            return False, a
        pos = idx + len(a)
    return True, None


def verify_reading_order(pdf, anchors, extractor=None):
    """Check that `anchors` (e.g. the name, then each section heading, in order)
    extract in that order. A multi-column PDF *has* a text layer but extracts
    scrambled — this catches that, which plain text-layer detection cannot."""
    text = (extractor or extract_text_ordered)(pdf)
    return _in_order(text, anchors)


def to_pdf(inp, outp=None, anchors=None):
    inp = os.path.abspath(inp)
    if not outp:
        outp = os.path.splitext(inp)[0] + ".pdf"
    outp = os.path.abspath(outp)
    outdir = os.path.dirname(outp)
    os.makedirs(outdir, exist_ok=True)

    ok = False
    # 1) LibreOffice writes <basename>.pdf into outdir; rename if needed.
    try:
        if _libreoffice(inp, outdir):
            produced = os.path.join(outdir, os.path.splitext(os.path.basename(inp))[0] + ".pdf")
            if os.path.exists(produced):
                if os.path.abspath(produced) != outp:
                    shutil.move(produced, outp)
                ok = True
    except Exception:
        pass
    # 2) Word
    if not ok:
        try:
            ok = _word_applescript(inp, outp)
        except Exception:
            ok = False
    # 3) docx2pdf
    if not ok:
        try:
            ok = _docx2pdf(inp, outp)
        except Exception:
            ok = False

    if not ok or not os.path.exists(outp):
        print("ERROR: no PDF converter available. Install LibreOffice "
              "(`brew install --cask libreoffice`) or Microsoft Word, or `pip install docx2pdf`.",
              file=sys.stderr)
        return None

    good, bt, tj = verify_text_layer(outp)
    status = "TEXT-BASED (ATS-readable)" if good else "WARNING: no text layer detected"
    order_ok, bad = (True, None)
    if anchors:
        order_ok, bad = verify_reading_order(outp, anchors)
        status += "; reading-order OK" if order_ok else \
            f"; WARNING: reading order — '{bad}' not found in expected position"
    print(f"Saved: {outp}  [{status}; BT={bt}, Tj/TJ={tj}]")
    return outp if (good and order_ok) else None


if __name__ == "__main__":
    args = list(sys.argv[1:])
    anchors = None
    if "--anchors" in args:
        i = args.index("--anchors")
        anchors = args[i + 1].split(",") if i + 1 < len(args) else None
        del args[i:i + 2]
    if not args:
        print('usage: python3 to_pdf.py <input.docx> [output.pdf] [--anchors "Name,Experience,Skills"]',
              file=sys.stderr)
        sys.exit(2)
    res = to_pdf(args[0], args[1] if len(args) > 1 else None, anchors=anchors)
    sys.exit(0 if res else 1)
