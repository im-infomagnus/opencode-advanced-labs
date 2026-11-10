#!/usr/bin/env python3
"""Check the Lab AL03 agent team's effective permissions without calling a model.

Run from the workspace root (the directory you start OpenCode in):

    python3 /path/to/opencode-advanced-labs/labs/AL03-agent-team/check_team.py

It reads the effective rules from `opencode debug agents` and evaluates each case
below the way OpenCode does: wildcards `*` (any characters, including `/`) and `?`
(one character), a shell pattern ending in " *" also matches the bare command, the
last matching rule wins, and no match means ask.
"""
import json
import re
import shutil
import subprocess
import sys
import time

# shutil.which also finds opencode.cmd from an npm install on Windows, which a bare "opencode" does not.
OPENCODE = shutil.which("opencode") or "opencode"

AGENT_MODES = {
    "commander": "primary",
    "eng-fuel": "subagent",
    "eng-geo": "subagent",
    "mini-reviewer": "subagent",
}

# (agent, action, resource, expected effect)
CASES = [
    ("commander", "subagent", "eng-fuel", "allow"),
    ("commander", "subagent", "mini-reviewer", "allow"),
    ("commander", "subagent", "general", "deny"),
    ("commander", "edit", "mission/BOARD.md", "allow"),
    ("commander", "edit", "skyroute/fuel.py", "deny"),
    ("commander", "shell", "git commit -m WA", "allow"),
    ("commander", "shell", "git diff --output=board.patch", "deny"),
    ("commander", "shell", "git push origin main", "deny"),
    ("commander", "shell", "date +%H:%M", "allow"),
    ("commander", "shell", "py -3 -m unittest", "allow"),
    ("commander", "shell", "date -u", "ask"),
    ("commander", "shell", "rm -rf skyroute", "ask"),
    ("eng-fuel", "edit", "skyroute/fuel.py", "allow"),
    ("eng-fuel", "edit", "tests/test_fuel.py", "allow"),
    ("eng-fuel", "edit", "skyroute/geo.py", "deny"),
    ("eng-fuel", "edit", "mission/BOARD.md", "deny"),
    ("eng-fuel", "shell", "python3 -m unittest tests.test_fuel", "allow"),
    ("eng-fuel", "shell", "py -3 -m unittest tests.test_fuel", "allow"),
    ("eng-fuel", "shell", "py -3 -c print(1)", "deny"),
    ("eng-fuel", "shell", "git commit -m WA", "deny"),
    ("eng-fuel", "shell", "git diff --output=leak.patch", "deny"),
    ("eng-fuel", "subagent", "general", "deny"),
    ("eng-geo", "edit", "skyroute/geo.py", "allow"),
    ("eng-geo", "edit", "tests/test_geo.py", "allow"),
    ("eng-geo", "edit", "skyroute/fuel.py", "deny"),
    ("eng-geo", "subagent", "general", "deny"),
    ("mini-reviewer", "edit", "skyroute/fuel.py", "deny"),
    ("mini-reviewer", "shell", "git show HEAD", "allow"),
    ("mini-reviewer", "shell", "python3 -m unittest", "allow"),
    ("mini-reviewer", "shell", "py -3 -m unittest", "allow"),
    ("mini-reviewer", "shell", "git diff --output=leak.patch", "deny"),
    ("mini-reviewer", "shell", "git commit -m x", "deny"),
    ("mini-reviewer", "subagent", "general", "deny"),
]


def wildcard(pattern):
    body = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.compile(f"^{body}$", re.S)


def matches(rule, action, resource):
    if not wildcard(rule["action"]).match(action):
        return False
    pattern = rule["resource"]
    if wildcard(pattern).match(resource):
        return True
    return action == "shell" and pattern.endswith(" *") and wildcard(pattern[:-2]).match(resource) is not None


def evaluate(rules, action, resource):
    effect = "ask"
    for rule in rules:
        if matches(rule, action, resource):
            effect = rule["effect"]
    return effect


def load_agents():
    for attempt in range(3):
        out = subprocess.run([OPENCODE, "debug", "agents"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if out.returncode != 0:
            sys.exit(f"opencode debug agents failed: {out.stderr.strip()}")
        data = json.loads(out.stdout or "[]")
        data = data["data"] if isinstance(data, dict) else data
        agents = {a["id"]: a for a in data}
        if all(name in agents for name in AGENT_MODES):
            return agents
        time.sleep(2)  # The service can return [] or a stale list on the first call for a directory.
    missing = sorted(set(AGENT_MODES) - set(agents))
    sys.exit(f"not discovered: {', '.join(missing)}. Run from the workspace root; check .opencode/agents/.")


def main():
    agents = load_agents()
    failures = 0
    for name, mode in AGENT_MODES.items():
        ok = agents[name]["mode"] == mode
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<14} mode {agents[name]['mode']} (want {mode})")
    for name, action, resource, want in CASES:
        got = evaluate(agents[name]["permissions"], action, resource)
        ok = got == want
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<14} {action} {resource!r} -> {got} (want {want})")
    total = len(AGENT_MODES) + len(CASES)
    print(f"{total - failures} of {total} checks pass")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
