"""Plain-text flight plan report, export, and upload helpers."""

import json
import os
import re
import tarfile
from pathlib import Path

from skyroute.geo import format_hours

DEFAULT_OUT = "out"
TOKEN_ENV = "SKYROUTE_UPLOAD_TOKEN"

_SAFE_NAME = re.compile(r"[A-Za-z0-9_-]+")
_FLIGHT_LEVEL = re.compile(r"FL([0-9]{2,3})")
_FEET = re.compile(r"[0-9]{1,5}")


def parse_altitude(text):
    """Cruise altitude in feet from 'FL350' or '12500' (SR-RPT-002)."""
    text = text.strip().upper()
    if m := _FLIGHT_LEVEL.fullmatch(text):
        return int(m.group(1)) * 100
    if _FEET.fullmatch(text):
        return int(text)
    raise ValueError(f"altitude must look like FL350 or 12500, not {text!r}")


def format_plan(route, fuel, groundspeed_kt, altitude_ft=None):
    lines = [
        "SkyRoute flight plan",
        "Route: " + " ".join(route.idents),
    ]
    if altitude_ft is not None:
        lines.append("Cruise: %d ft" % altitude_ft)
    lines += ["", "%-13s %8s %5s" % ("LEG", "DIST NM", "CRS")]
    for leg in route.legs():
        lines.append("%-13s %8.1f %5s" % (leg.name, leg.distance_nm,
                                          "%03d" % round(leg.bearing_deg)))
    lines += [
        "",
        "Total distance: %8.1f NM" % route.total_distance_nm(),
        "Ground speed:   %8.0f KT" % groundspeed_kt,
        "Time enroute:   %8s" % format_hours(route.ete_hours(groundspeed_kt)),
        "",
        "Fuel (lb)",
        "  Trip         %8.0f" % fuel.trip,
        "  Contingency  %8.0f" % fuel.contingency,
        "  Reserve      %8.0f" % fuel.reserve,
        "  Total        %8.0f" % fuel.total,
    ]
    return "\n".join(lines) + "\n"


def _output_path(out_dir, name, suffix):
    """Path for <name><suffix> inside out_dir, or ValueError (SR-RPT-003)."""
    if not _SAFE_NAME.fullmatch(name):
        raise ValueError(f"report name may contain only A-Z, a-z, 0-9, _ and -: {name!r}")
    root = Path(out_dir).resolve()
    path = (root / (name + suffix)).resolve()
    # Resolving catches a symlink inside out_dir that points somewhere else.
    if path.parent != root:
        raise ValueError(f"{path} is outside {root}")
    return path


def export(text, name, out_dir=DEFAULT_OUT):
    """Write a report to <out_dir>/<name>.txt and return the path."""
    path = _output_path(out_dir, name, ".txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def archive(name, out_dir=DEFAULT_OUT):
    """Bundle an exported report into <out_dir>/<name>.tar.gz for upload."""
    src = _output_path(out_dir, name, ".txt")
    dest = _output_path(out_dir, name, ".tar.gz")
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname=src.name)
    return str(dest)


def save_cached(summary, path):
    """Save a plan summary for the upload job as JSON (SR-RPT-005)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def load_cached(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path} is not a SkyRoute JSON cache file") from exc


def upload_headers():
    """Authorization header for the upload service (SR-RPT-006)."""
    token = os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(f"set {TOKEN_ENV} to upload plans")
    return {"Authorization": "Bearer " + token}
