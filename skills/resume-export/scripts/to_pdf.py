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


def to_pdf(inp, outp=None):
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
    print(f"Saved: {outp}  [{status}; BT={bt}, Tj/TJ={tj}]")
    return outp if good else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 to_pdf.py <input.docx> [output.pdf]", file=sys.stderr)
        sys.exit(2)
    res = to_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if res else 1)
