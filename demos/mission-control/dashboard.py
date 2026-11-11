#!/usr/bin/env python3
"""Mission Control live dashboard for the instructor's second screen.

    python3 demos/mission-control/dashboard.py [--workspace ~/opencode-mission] [--interval 5] [--once]
        [--root-agent commander | --session ses_...]

Reads the OpenCode background service through `opencode api` (sessions, active sessions) and the
workspace itself (mission/BOARD.md, tools/mission_status.py). Standard library only. Ctrl+C exits.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path

OPENCODE = shutil.which("opencode") or "/opt/homebrew/bin/opencode"
CLEAR = "\033[2J\033[H"
if os.name == "nt":
    os.system("")  # enable ANSI escape codes in the Windows console


def opencode_command(args: list[str]) -> list[str] | str:
    """The command for subprocess. An npm install on Windows is opencode.cmd, which runs through
    cmd.exe; quote every argument so cmd does not split the query string at '&'."""
    if os.name == "nt" and OPENCODE.lower().endswith((".cmd", ".bat")):
        quoted = " ".join(f'"{a}"' for a in [OPENCODE, *args])
        return f'cmd.exe /d /s /c "{quoted}"'
    return [OPENCODE, *args]


def msys_to_windows(path: str) -> str:
    """Git Bash path /c/Users/me/x -> C:/Users/me/x, in case Git Bash did not convert it."""
    if os.name == "nt" and len(path) >= 3 and path[0] == "/" and path[1].isalpha() and path[2] == "/":
        return f"{path[1].upper()}:{path[2:]}"
    return path


def api(path: str, location: str, **params: str) -> object:
    """GET an API route at the workspace location; extra params (directory=, parentID=) filter session lists."""
    query = urllib.parse.urlencode({"location[directory]": location, "limit": "200", **params})
    # A pipe can truncate `opencode api` output at 256 KiB (2.1), so read it from a file.
    with tempfile.TemporaryFile("w+", encoding="utf-8") as out:
        proc = subprocess.run(opencode_command(["api", "GET", f"{path}?{query}"]), stdout=out, stderr=subprocess.PIPE,
                              text=True, encoding="utf-8", errors="replace", timeout=30)
        out.seek(0)
        stdout = out.read()
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or f"opencode api GET {path} failed")
    body = json.loads(stdout) if stdout.strip() else None
    return body["data"] if isinstance(body, dict) and "data" in body else body


def active_ids(data: object) -> set[str]:
    if isinstance(data, dict):
        return set(data)
    if isinstance(data, list):
        return {x if isinstance(x, str) else x.get("id", x.get("sessionID", "")) for x in data}
    return set()


def agent_of(s: dict) -> str:
    # Sessions started without --agent carry no agent field; they run the default agent, build.
    return s.get("agent") or "build"


def find_root(directory: str, root_agent: str, session_id: str | None) -> dict | None:
    """The session given by --session, else the newest root session of root_agent in the workspace."""
    if session_id:
        return api(f"/api/session/{session_id}", directory)
    sessions = api("/api/session", directory, directory=directory) or []
    roots = [s for s in sessions if agent_of(s) == root_agent and not s.get("parentID")]
    return max(roots, key=lambda s: s.get("time", {}).get("created", 0)) if roots else None


def children_of(root: dict, directory: str) -> list[dict]:
    """Children by parentID with no directory filter, so subagents working in worktrees still appear."""
    children = api("/api/session", directory, parentID=root["id"]) or []
    return sorted(children, key=lambda s: s.get("time", {}).get("created", 0))


def tokens(s: dict) -> tuple[int, int]:
    t = s.get("tokens") or {}
    cache = t.get("cache") or {}
    return (t.get("input", 0) + cache.get("read", 0) + cache.get("write", 0), t.get("output", 0) + t.get("reasoning", 0))


def pending_by_session(data: object) -> dict[str, list[str]]:
    """Pending permission requests at the location, as 'action resource' strings per session."""
    pending: dict[str, list[str]] = {}
    for req in data if isinstance(data, list) else []:
        pending.setdefault(req.get("sessionID", ""), []).append(f"{req.get('action')} {' '.join(req.get('resources', []))}")
    return pending


def session_rows(commander: dict, children: list[dict], active: set[str], now_ms: float,
                 pending: dict[str, list[str]] | None = None) -> list[tuple[str, ...]]:
    pending = pending or {}
    rows = []
    for s in [commander, *children]:
        tin, tout = tokens(s)
        updated = s.get("time", {}).get("updated") or s.get("time", {}).get("created") or now_ms
        title = s.get("title") or s["id"]
        rows.append((
            ("  " if s is not commander else "") + title[:38],
            agent_of(s),
            "WAITING" if s["id"] in pending else "active" if s["id"] in active else "idle",
            s.get("outcome") or "-",
            f"{tin:,}/{tout:,}",
            f"${s.get('cost', 0):.2f}",
            f"{max(0, (now_ms - updated) / 60000):.0f}",
        ))
    return rows


def table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    all_rows = [header, *rows]
    widths = [max(len(r[i]) for r in all_rows) for i in range(len(header))]
    return ["  ".join(c.ljust(widths[i]) for i, c in enumerate(r)).rstrip() for r in all_rows]


def load_status_module(workspace: Path):
    path = workspace / "tools" / "mission_status.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("mission_status", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StatusCache:
    """Runs mission_status.collect() in the background so redraws never wait on the test suite."""

    def __init__(self, module, every: float, run_tests: bool):
        self.module, self.every, self.run_tests = module, every, run_tests
        self.value: dict | None = None
        self.stamp = 0.0
        self.busy = False

    def refresh(self, wait: bool = False) -> None:
        if self.module is None or self.busy or (time.time() - self.stamp < self.every and self.value):
            return
        self.busy = True
        worker = threading.Thread(target=self._run, daemon=True)
        worker.start()
        if wait:
            worker.join()

    def _run(self) -> None:
        try:
            self.value = self.module.collect(run_tests=self.run_tests)
        except Exception as exc:
            self.value = {"error": str(exc)}
        self.stamp, self.busy = time.time(), False


def render(workspace: Path, status: StatusCache, root_agent: str = "commander", session_id: str | None = None) -> str:
    directory = str(workspace)
    now_ms = time.time() * 1000
    lines = [f"Mission Control   {workspace}   {time.strftime('%H:%M:%S')}", ""]
    try:
        commander = find_root(directory, root_agent, session_id)
        if commander is None:
            hint = " Launch it: Shift+Tab to commander, then /mission-launch." if root_agent == "commander" else ""
            lines.append(f"No {root_agent} session yet in this workspace.{hint}")
        else:
            children = children_of(commander, directory)
            active = active_ids(api("/api/session/active", directory))
            pending = pending_by_session(api("/api/permission/request", directory))
            rows = session_rows(commander, children, active, now_ms, pending)
            lines += table(("Session", "Agent", "State", "Outcome", "Tokens in/out", "Cost", "Min"), rows)
            group = [commander, *children]
            tin = sum(tokens(s)[0] for s in group)
            tout = sum(tokens(s)[1] for s in group)
            running = sum(1 for s in group if s["id"] in active)
            lines += ["", f"Sessions: {len(group)} ({len(children)} subagents, {running} active)   "
                          f"Tokens: {tin:,} in / {tout:,} out   Cost: ${sum(s.get('cost', 0) for s in group):.2f}"]
            for s in group:
                for req in pending.get(s["id"], []):
                    lines.append(f"WAITING for approval in {s.get('title') or s['id']}: {req[:90]}")
    except Exception as exc:
        lines.append(f"OpenCode service: {exc}. Is it running? Try: opencode service status")

    lines.append("")
    if status.module is None:
        lines.append("No tools/mission_status.py in this workspace, so no board or test summary.")
        return "\n".join(lines)
    board = status.module.read_board(workspace / "mission" / "BOARD.md")
    if board:
        rows = [(ws, r.get("workstream", ""), r.get("status", ""), r.get("session", ""), r.get("tests", ""), r.get("updated", ""))
                for ws, r in sorted(board.items())]
        lines += table(("WS", "Workstream", "Board", "Session", "Tests", "Updated"), rows)
    else:
        lines.append("mission/BOARD.md has no rows")
    value = status.value
    lines.append("")
    if value is None:
        lines.append("Tests: running...")
    elif "error" in value:
        lines.append(f"Tests: status failed: {value['error']}")
    else:
        s = value["suite"]
        built = [w["id"] for w in value["workstreams"] if w.get("built")]
        files = sum(w["files_present"] for w in value["workstreams"])
        total = sum(w["files_total"] for w in value["workstreams"])
        suite = "skipped" if s["state"] == "skipped" else f"{s['passed']}/{s['ran']} {s['state']}"
        if s["state"] != "skipped" and value.get("suite_informational"):
            suite += " (informational mid-wave)"
        lines.append(f"Tests: suite {suite}   Files: {files}/{total}   Built: {', '.join(built) or 'none'}   "
                     f"Commits since baseline: {len(value['commits_since_baseline'])}   (as of {value['time'][11:]})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", default=os.path.expanduser("~/opencode-mission"), help="mission workspace (default %(default)s)")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between redraws (default %(default)s)")
    parser.add_argument("--status-every", type=float, default=30.0, help="seconds between test runs (default %(default)s)")
    parser.add_argument("--no-tests", action="store_true", help="never run the tests")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument("--root-agent", default="commander", help="agent of the root session to follow (default %(default)s)")
    parser.add_argument("--session", help="follow this root session ID instead of the newest --root-agent session")
    args = parser.parse_args(argv)

    workspace = Path(os.path.realpath(os.path.expanduser(msys_to_windows(args.workspace))))
    if not workspace.is_dir():
        print(f"dashboard: {workspace} does not exist. Check the --workspace path.", file=sys.stderr)
        return 1
    status = StatusCache(load_status_module(workspace), args.status_every, not args.no_tests)

    if args.once:
        status.refresh(wait=True)
        print(render(workspace, status, args.root_agent, args.session))
        return 0
    try:
        while True:
            status.refresh()
            frame = render(workspace, status, args.root_agent, args.session)
            sys.stdout.write(CLEAR + frame + f"\n\nRefresh every {args.interval:g} s. Ctrl+C to exit.\n")
            sys.stdout.flush()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
