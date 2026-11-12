#!/usr/bin/env python3
"""Print the text of a simple PDF. Standard library only.

Usage: python pdf_text.py <file.pdf>

Handles PDFs whose pages draw text with Tj, TJ, ' and " operators in plain or
FlateDecode streams, which covers most text-only documents exported by office
tools. Scanned images and custom font encodings print nothing useful; say so
instead of guessing.
"""
import re
import sys
import zlib

STREAM = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", re.S)
TOKEN = re.compile(rb"\((?:\\.|[^\\)])*\)|\[(?:\\.|[^\]])*\]|-?\d*\.?\d+|/[^\s/\[\]()<>]+|[A-Za-z'\"*]+")
ESC = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}


def literal(s: bytes) -> str:
    out, i = bytearray(), 1
    while i < len(s) - 1:
        c = s[i:i + 1]
        if c == b"\\":
            n = s[i + 1:i + 2]
            if n in ESC:
                out += ESC[n]
                i += 2
            elif n.isdigit():
                m = re.match(rb"[0-7]{1,3}", s[i + 1:i + 4])
                out.append(int(m.group(0), 8))
                i += 1 + len(m.group(0))
            else:
                i += 2
        else:
            out += c
            i += 1
    return out.decode("latin-1")


def page_text(content: bytes) -> str:
    lines, line = [], []
    for tok in TOKEN.findall(content):
        if tok.startswith(b"("):
            line.append(literal(tok))
        elif tok.startswith(b"["):
            for part in re.findall(rb"\((?:\\.|[^\\)])*\)", tok):
                line.append(literal(part))
        elif tok in (b"Td", b"TD", b"Tm", b"T*", b"ET", b"'", b'"'):
            if line:
                lines.append("".join(line))
                line = []
    if line:
        lines.append("".join(line))
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    data = open(sys.argv[1], "rb").read()
    if not data.startswith(b"%PDF"):
        print(f"pdf_text: {sys.argv[1]} is not a PDF", file=sys.stderr)
        return 1
    pages = []
    for header, body in STREAM.findall(data):
        if b"/FlateDecode" in header:
            try:
                body = zlib.decompress(body)
            except zlib.error:
                continue
        if b"BT" in body and (b"Tj" in body or b"TJ" in body):
            text = page_text(body).strip()
            if text:
                pages.append(text)
    if not pages:
        print("pdf_text: no extractable text (scanned or unusual encoding)", file=sys.stderr)
        return 1
    for n, text in enumerate(pages, 1):
        print(f"--- page {n} ---")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
