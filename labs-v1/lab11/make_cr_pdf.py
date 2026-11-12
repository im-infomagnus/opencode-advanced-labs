"""Build CR-042-fuel-policy.pdf, the synthetic change request for Lab 11. Standard library only."""
import pathlib
import zlib

PAGES = [
    [
        ("H", "SkyRoute Change Request CR-042"),
        ("S", "Title: Fuel policy update for dispatch planning"),
        ("S", "Status: Approved for implementation    Owner: SkyRoute Ops (synthetic)"),
        ("S", "Date: 2026-10-30    Applies to: skyroute/fuel.py, skyroute/report.py"),
        ("B", ""),
        ("H2", "1. Background"),
        ("P", "Dispatch reviewed fuel planning after two diversions in the synthetic"),
        ("P", "test fleet. The current plan has no alternate fuel and a contingency"),
        ("P", "that can be very small on short legs."),
        ("B", ""),
        ("H2", "2. Changes"),
        ("P", "2.1 The fuel plan shall include alternate fuel, computed as burn rate"),
        ("P", "times alternate time. The default alternate time shall be 45 minutes."),
        ("P", "2.2 Contingency fuel shall be the greater of 5 percent of trip fuel"),
        ("P", "and 200 lb."),
        ("P", "2.3 Total fuel shall be trip plus contingency plus alternate plus"),
        ("P", "final reserve."),
        ("P", "2.4 The plan report shall show total fuel rounded up to the next 10 lb."),
    ],
    [
        ("H2", "3. Notes for implementers"),
        ("P", "Reserve should probably be raised for long flights, but dispatch has"),
        ("P", "not agreed a number yet."),
        ("P", "The CLI may later accept an --alternate-min option. Not in this change."),
        ("P", "Existing requirement SR-FUEL-002 is replaced by item 2.2."),
        ("B", ""),
        ("H2", "4. Example"),
        ("P", "Trip 1.0 h at 2400 lb/h: trip 2400 lb, contingency 200 lb (5 percent is"),
        ("P", "120 lb, below the 200 lb floor), alternate 1800 lb, reserve 1200 lb,"),
        ("P", "total 5600 lb."),
        ("B", ""),
        ("S", "All content is synthetic training data. Not for operational use."),
    ],
]
SIZES = {"H": 18, "H2": 13, "S": 10, "P": 11, "B": 11}


def esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def content(lines):
    out, y = ["BT"], 760
    for kind, text in lines:
        size = SIZES[kind]
        font = "/F2" if kind in ("H", "H2") else "/F1"
        out.append(f"{font} {size} Tf 1 0 0 1 60 {y} Tm ({esc(text)}) Tj")
        y -= size + 9
    out.append("ET")
    return "\n".join(out).encode("latin-1")


objs = []
kids = []
font1, font2 = 3, 4
objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
objs.append(None)
objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
for page in PAGES:
    data = zlib.compress(content(page))
    objs.append(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream")
    cnum = len(objs)
    objs.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {cnum} 0 R "
        f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >> >> >>".encode()
    )
    kids.append(len(objs))
objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>".encode()

pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
offsets = []
for i, body in enumerate(objs, 1):
    offsets.append(len(pdf))
    pdf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
xref = len(pdf)
pdf += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
for off in offsets:
    pdf += f"{off:010d} 00000 n \n".encode()
pdf += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
out = pathlib.Path(__file__).with_name("CR-042-fuel-policy.pdf")
out.write_bytes(bytes(pdf))
print(f"wrote {out} ({len(pdf)} bytes)")
