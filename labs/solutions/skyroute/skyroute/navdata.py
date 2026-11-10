"""Reader for SRN-1 fixed-width navigation data. See docs/srn1-format.md.

Behavior matches the legacy reader, quirks included. The characterization
tests in tests/test_navdata_characterization.py pin each quirk.

History: ported from the old ground-station reader (Fortran) in 2009.
2014: NV records.  2017: added cache, the planner was re-reading the
file for every leg.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "navdata.srn"
RECORD_KINDS = ("AP", "WP", "NV")

KIND = slice(0, 2)
IDENT = slice(3, 8)
LAT = slice(9, 18)
LON = slice(19, 29)
ELEV = slice(30, 35)
FREQ = slice(36, 42)
NAME = slice(43, None)


@dataclass(frozen=True)
class Fix:
    """One navigation point. Degrees, feet, and MHz."""

    kind: str
    ident: str
    lat: float
    lon: float
    elev: int = 0
    freq: float | None = None
    name: str = ""


class RecordError(ValueError):
    """An SRN-1 record that cannot be parsed."""


def parse_angle(field: str) -> float:
    """Decimal degrees from 'N33411800' (DDMMSSss) or 'W112045700' (DDDMMSSss)."""
    hemisphere, digits = field[:1], field[1:]
    width = 2 if len(digits) == 8 else 3
    deg, rest = digits[:width], digits[width:]
    value = int(deg) + int(rest[0:2]) / 60 + int(rest[2:4]) / 3600 + int(rest[4:6]) / 360000
    # Legacy rule: only uppercase S and W are negative; any other letter is N or E.
    return -value if hemisphere in "SW" else value


def parse_record(line: str) -> Fix | None:
    """Parse one line. None means the line is not a record; RecordError means a bad record."""
    if not line.strip() or line.startswith("*"):
        return None
    kind = line[KIND]
    if kind not in RECORD_KINDS:
        return None
    try:
        raw_elev = line[ELEV].strip()
        raw_freq = line[FREQ].strip()
        ident = line[IDENT].strip()
        return Fix(
            kind=kind,
            ident=ident,
            lat=parse_angle(line[LAT]),
            lon=parse_angle(line[LON]),
            elev=int(raw_elev or 0),
            # Legacy rule: a frequency of 0.00 reads as no frequency.
            freq=(float(raw_freq) or None) if raw_freq else None,
            name=line[NAME].strip(),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def read(path: str | Path) -> dict[str, Fix]:
    """Parse an SRN-1 file into {ident: Fix}. Bad records are logged and skipped."""
    fixes: dict[str, Fix] = {}
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\r\n")
            try:
                fix = parse_record(line)
            except RecordError as exc:
                log.warning("%s:%d: skipped malformed record: %s", path, lineno, exc)
                continue
            if fix is None:
                continue
            if fix.ident in fixes:
                log.info("%s:%d: %s replaces an earlier record", path, lineno, fix.ident)
            fixes[fix.ident] = fix
    return fixes


@lru_cache(maxsize=None)
def _read_cached(path: str) -> dict[str, Fix]:
    return read(path)


def load(path: str | Path | None = None) -> dict[str, Fix]:
    """Return {ident: Fix} for an SRN-1 file. Each path is read once per process."""
    return _read_cached(str(path or DEFAULT_PATH))


def lookup(ident: object, path: str | Path | None = None) -> Fix | None:
    """Find a fix by ident, ignoring case and surrounding spaces. None if absent."""
    if not isinstance(ident, str):
        return None
    return load(path).get(ident.strip().upper())


def clear() -> None:
    """Forget cached files so the next load reads from disk."""
    _read_cached.cache_clear()


if __name__ == "__main__":
    for ident, fix in sorted(load(sys.argv[1] if len(sys.argv) > 1 else None).items()):
        print(f"{ident:<5} {fix}")
