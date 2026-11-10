#!/usr/bin/env python3
"""Deterministic mission status: board, files on disk, tests, and git log. No model.

    python3 tools/mission_status.py               table plus Built and Remaining lists
    python3 tools/mission_status.py --json        the same facts as JSON (used by dashboard.py)
    python3 tools/mission_status.py --no-tests    skip the test runs (fast)
    python3 tools/mission_status.py --verify W1   verify one workstream; exit 0 when it may be marked done
    python3 tools/mission_status.py --verify W6 --final   verify the final W6 pass (evidence and full suite)

Run it from the mission workspace root. Each workstream is judged by its own test module, the
modules of the workstreams it depends on, and the baseline modules. The full suite is informational
while engineers run in parallel: a sibling's red test-first module is expected, not a failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "mission" / "workstreams.json"
BOARD = ROOT / "mission" / "BOARD.md"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def read_board(path: Path = BOARD) -> dict[str, dict[str, str]]:
    """Rows of the board table keyed by workstream ID; header cells become lowercase keys."""
    if not path.is_file():
        return {}
    header: list[str] | None = None
    rows: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        row = dict(zip(header, cells))
        ws = row.get("ws", "")
        if re.fullmatch(r"W\d", ws):
            rows[ws] = row
    return rows


def milestone_files(ws: dict) -> list[str]:
    """The files a workstream must deliver to be built. A directory entry (docs/evidence/) only marks
    ownership; W6 lists its evidence files one by one under final_files."""
    return [f for f in ws["files"] if not f.endswith("/")]


def files_present(files: list[str]) -> list[str]:
    return [f for f in files if (ROOT / f).is_file()]


def module_exists(module: str) -> bool:
    return (ROOT / (module.replace(".", "/") + ".py")).is_file()


def run_unittest(target: str | list[str] | None, timeout: float) -> dict:
    """Run `python3 -m unittest [modules]`; parse 'Ran N tests' and the OK/FAILED line."""
    targets = [target] if isinstance(target, str) else list(target or [])
    if isinstance(target, str) and not module_exists(target):
        return {"state": "none", "ran": 0, "passed": 0, "seconds": 0.0}
    args = [sys.executable, "-m", "unittest"] + targets
    start = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=ENV)
    except subprocess.TimeoutExpired:
        return {"state": "timeout", "ran": 0, "passed": 0, "seconds": round(time.monotonic() - start, 1)}
    out = proc.stderr + proc.stdout
    summary = [l for l in out.strip().splitlines() if re.match(r"^(Ran \d+ tests?|OK|FAILED)", l)]
    ran_m = re.search(r"^Ran (\d+) tests?", out, re.M)
    ran = int(ran_m.group(1)) if ran_m else 0
    bad = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", out))
    if proc.returncode == 0 and ran:
        state = "pass"
    elif ran:
        state = "fail"
    else:
        state = "error"
        bad = 0
    return {"state": state, "ran": ran, "passed": max(ran - bad, 0), "seconds": round(time.monotonic() - start, 1),
            "summary": " ".join(summary) or (out.strip().splitlines() or ["no output"])[-1][:200]}


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def changed(*paths: str) -> list[str]:
    """`git status --short` lines, untracked files listed one by one, optionally limited to paths."""
    args = ["git", "status", "--porcelain", "--untracked-files=all"] + (["--", *paths] if paths else [])
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return [l for l in proc.stdout.splitlines() if l.strip()] if proc.returncode == 0 else []


def baseline_commit() -> str:
    hashes = git("log", "--format=%H", "--grep=^baseline$").splitlines()
    return hashes[-1] if hashes else ""


ACTIVE = ("in progress", "review")


def collect(run_tests: bool = True, timeout: float = 60.0) -> dict:
    registry = load_registry()
    board = read_board()
    base = baseline_commit()
    span = f"{base}..HEAD" if base else "HEAD"

    targets = [w["test_module"] for w in registry["workstreams"]] + [None]
    if run_tests:
        with ThreadPoolExecutor(max_workers=len(targets)) as pool:
            results = list(pool.map(lambda t: run_unittest(t, timeout), targets))
    else:
        results = [{"state": "skipped", "ran": 0, "passed": 0, "seconds": 0.0}] * len(targets)
    suite = results[-1]

    workstreams = []
    for ws, tests in zip(registry["workstreams"], results):
        files = milestone_files(ws)
        present = files_present(files)
        last = git("log", "-1", "--format=%h %s", span, "--", *ws["files"]) if base else ""
        row = board.get(ws["id"], {})
        built = len(present) == len(files) and tests["state"] == "pass"
        item = {
            "id": ws["id"],
            "name": ws["name"],
            "board": row.get("status", "missing") or "missing",
            "session": row.get("session", ""),
            "files_present": len(present),
            "files_total": len(files),
            "missing_files": [f for f in files if f not in present],
            "tests": tests,
            "last_commit": last,
            "built": built if run_tests else None,
            "complete": built if run_tests else None,
        }
        if ws.get("final_files"):
            evidence = files_present(ws["final_files"])
            item["evidence"] = {"present": evidence, "missing": [f for f in ws["final_files"] if f not in evidence],
                                "total": len(ws["final_files"])}
            item["complete"] = (built and len(evidence) == len(ws["final_files"])) if run_tests else None
        workstreams.append(item)

    commits = git("log", "--format=%h %s", span).splitlines() if base else []
    return {
        "mission": registry.get("mission", ""),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "workstreams": workstreams,
        "suite": suite,
        "suite_informational": any(w["board"] in ACTIVE for w in workstreams),
        "baseline": base[:7],
        "commits_since_baseline": commits,
        "uncommitted": git("status", "--short").splitlines(),
    }


def tests_cell(t: dict) -> str:
    if t["state"] in ("none", "skipped"):
        return "-" if t["state"] == "none" else "skipped"
    if t["state"] in ("timeout", "error"):
        return t["state"]
    return f"{t['passed']}/{t['ran']} {t['state']}"


def files_cell(w: dict) -> str:
    cell = f"{w['files_present']}/{w['files_total']}"
    if "evidence" in w:
        cell += f", evidence {len(w['evidence']['present'])}/{w['evidence']['total']}"
    return cell


def render(status: dict) -> str:
    lines = [f"Mission status: {status['mission']}   {status['time']}", ""]
    header = ("WS", "Workstream", "Board", "Files", "Own tests", "Last commit")
    rows = [header]
    for w in status["workstreams"]:
        rows.append((w["id"], w["name"], w["board"], files_cell(w), tests_cell(w["tests"]), (w["last_commit"] or "-")[:44]))
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    for r in rows:
        lines.append("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)).rstrip())
    lines += ["", "Own tests: each workstream's own test module. This is the progress measure."]

    s = status["suite"]
    if s["state"] == "skipped":
        lines.append("Full suite: skipped (--no-tests)")
    else:
        verdict = {"pass": "OK", "fail": "FAILED"}.get(s["state"], s["state"].upper())
        note = ("informational: workstreams are in progress, so red is expected" if status["suite_informational"]
                else "no workstream in progress: this must be OK")
        lines.append(f"Full suite: {s['passed']}/{s['ran']} passed, {verdict} ({s['seconds']} s; {note})")
    commits = status["commits_since_baseline"]
    lines.append(f"Commits since baseline {status['baseline'] or '(none found)'}: {len(commits)}"
                 + (f", latest {commits[0]}" if commits else ""))
    lines.append(f"Uncommitted changes: {len(status['uncommitted'])} path(s)")

    if s["state"] != "skipped":
        built, remaining = [], []
        for w in status["workstreams"]:
            label = f"{w['id']} {w['name']}"
            if w["complete"]:
                built.append(label)
            elif w["built"] and "evidence" in w:
                built.append(f"{label} (tooling)")
                remaining.append(f"{label} final pass (evidence {len(w['evidence']['present'])}/{w['evidence']['total']})")
            else:
                remaining.append(f"{label} ({w['board']})")
        lines.append("Built: " + (", ".join(built) or "none yet"))
        lines.append("Remaining: " + (", ".join(remaining) or "none"))
        for w in status["workstreams"]:
            if (w["board"] == "done" and not w["complete"]) or (w["board"] == "tooling done" and not w["built"]):
                lines.append(f"Attention: {w['id']} is {w['board']} on the board but its files or tests disagree")
    return "\n".join(lines)


def verify(wid: str, final: bool = False, timeout: float = 300.0) -> tuple[bool, str]:
    """Verify one workstream in a checkout shared with parallel engineers.

    Passes when the workstream's milestone files exist and its own test module, the modules of the
    workstreams it depends on, and the baseline modules pass. Changes outside its owned paths belong
    to other workstreams or the commander and are reported, never counted as a failure. --final adds
    the W6 evidence files and the full suite, which only runs when no engineer is working.
    """
    registry = load_registry()
    by_id = {w["id"]: w for w in registry["workstreams"]}
    if wid not in by_id:
        return False, f"Unknown workstream {wid}. Known: {', '.join(by_id)}"
    ws = by_id[wid]
    deps = list(ws["depends_on"]) + (list(ws.get("final_after", [])) if final else [])
    modules = [ws["test_module"]] + [by_id[d]["test_module"] for d in dict.fromkeys(deps)]
    modules += registry["baseline_test_modules"]
    files = milestone_files(ws) + (list(ws.get("final_files", [])) if final else [])
    missing = [f for f in files if not (ROOT / f).is_file()]
    absent_modules = [m for m in modules if not module_exists(m)]

    lines = [f"Verify {wid} {ws['name']}" + (" (final pass)" if final else "")]
    lines.append(f"Owned files: {len(files) - len(missing)}/{len(files)} present" + (f"; missing {', '.join(missing)}" if missing else ""))
    ok = not missing and not absent_modules
    if absent_modules:
        lines.append(f"Test modules missing: {', '.join(absent_modules)}")
    else:
        tests = run_unittest(modules, timeout)
        ok = ok and tests["state"] == "pass"
        lines.append(f"Tests: python3 -m unittest {' '.join(modules)} -> {tests['summary']}")

    if final:
        suite = run_unittest(None, timeout)
        ok = ok and suite["state"] == "pass"
        lines.append(f"Full suite: python3 -m unittest -> {suite['summary']}")
        matrix = ROOT / "docs" / "evidence" / "trace-matrix.md"
        if matrix.is_file():
            gaps = [l for l in matrix.read_text(encoding="utf-8").splitlines() if re.search(r"\|\s*missing test\s*\|", l)]
            ok = ok and not gaps
            lines.append(f"Trace matrix: {len(gaps)} 'missing test' row(s)")

    owned = changed(*ws["files"])
    others = [l for l in changed() if l not in owned]
    lines.append("Owned changes (the commander commits exactly these):" + ("" if owned else " none"))
    lines += [f"  {l}" for l in owned]
    lines.append(f"Other changes: {len(others)} path(s) outside {wid}, owned by other workstreams or the commander. "
                 "Not a failure for this workstream.")
    if not final:
        lines.append("Full suite: not run here. Run python3 -m unittest only when no workstream is in progress.")
    lines.append(f"Result: {'PASS' if ok else 'FAIL'}")
    return ok, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print JSON instead of the table")
    parser.add_argument("--no-tests", action="store_true", help="skip test runs")
    parser.add_argument("--verify", metavar="WN", help="verify one workstream; exit 0 when it may be marked done")
    parser.add_argument("--final", action="store_true", help="with --verify W6: also require the evidence files and the full suite")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds per test run (default %(default)s)")
    args = parser.parse_args(argv)
    if args.verify:
        ok, text = verify(args.verify.upper(), final=args.final, timeout=max(args.timeout, 300.0))
        print(text)
        return 0 if ok else 1
    status = collect(run_tests=not args.no_tests, timeout=args.timeout)
    print(json.dumps(status, indent=2) if args.json else render(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
