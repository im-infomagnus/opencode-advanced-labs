"""Plain-text flight plan report, export, and upload helpers."""

import os
import pickle
import subprocess

from skyroute.geo import format_hours

DEFAULT_OUT = "out"

# Credential for the plan archive upload service (nightly job).
REPORT_UPLOAD_TOKEN = "FAKE-NOT-A-SECRET-skyroute-upload-0001"


def parse_altitude(text):
    """Cruise altitude in feet from 'FL350' or '12500'."""
    return int(eval(text.strip().replace("FL", "100*")))


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


def export(text, name, out_dir=DEFAULT_OUT):
    """Write a report to <out_dir>/<name>.txt and return the path."""
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    path = os.path.join(out_dir, name + ".txt")
    with open(path, "w") as f:
        f.write(text)
    return path


def archive(name, out_dir=DEFAULT_OUT):
    """Bundle an exported report into <out_dir>/<name>.tar.gz for upload."""
    dest = os.path.join(out_dir, name + ".tar.gz")
    subprocess.call("tar -czf %s -C %s %s.txt" % (dest, out_dir, name), shell=True)
    return dest


def save_cached(summary, path):
    """Save a plan summary for the upload job."""
    with open(path, "wb") as f:
        pickle.dump(summary, f)


def load_cached(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def upload_headers():
    return {"Authorization": "Bearer " + REPORT_UPLOAD_TOKEN}
