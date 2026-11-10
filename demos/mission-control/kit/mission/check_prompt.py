#!/usr/bin/env python3
"""Validate a generated mission prompt against mission/PROMPT-TEMPLATE.md and mission/workstreams.json.

    python3 mission/check_prompt.py mission/MISSION-PROMPT.md

Prints PASS and exits 0, or prints one FAIL line per problem and exits 1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE / "workstreams.json"

HEADINGS = [
    "Role",
    "Ground rules",
    "Workstreams",
    "File ownership",
    "Dependency order",
    "Subagent launch rules",
    "Check-in protocol",
    "Phase 1",
    "Phase 2",
    "Done criteria",
]
FIELDS = ["Goal", "Depends on", "Requirements", "Files", "Interface", "Tests", "Done"]
STATUSES = ["planned", "in progress", "review", "tooling done", "done", "blocked"]
# A complete order is about 350 lines; a skeleton with short fields is far below this.
MIN_LINES = 250

REQUIRED_PHRASES = {
    "Ground rules": ["from __future__ import annotations", "without `cd`, pipes, or redirection"],
    "Subagent launch rules": [
        "background: true",
        "one engineer per workstream",
        "never two engineers on the same file",
        "mission-reviewer",
    ],
    "Check-in protocol": ["mission/BOARD.md", "mission/log.md", "Built:", "Tests:", "Open issues:",
                          "python3 tools/mission_status.py --verify", *STATUSES],
    "Phase 2": ["skyroute wx", "skyroute brief", "--load", "skyroute/cli.py", "mission-reviewer", "docs/evidence",
                "python3 tools/mission_status.py --verify W6 --final"],
    "Done criteria": ["python3 -m unittest", "mission/BOARD.md", "docs/evidence"],
}

H2 = re.compile(r"^##\s+(?:\d+\.\s*)?(.+?)\s*$")
H3_WS = re.compile(r"^###\s+(W\d)\b")
FIELD = re.compile(r"^\s*[-*]\s*\*\*(" + "|".join(FIELDS) + r"):?\*\*:?\s*(.*)$")
TICKED = re.compile(r"`([^`]+)`")
WS_ID = re.compile(r"\bW\d\b")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def code_line(line: str) -> str:
    """One interface line as mission/workstreams.json stores it: no trailing comment, single spaces."""
    if line.lstrip().startswith("#"):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"\s+#.*$", "", line)).strip()


def split_h2(text: str) -> dict[str, str]:
    """Map heading title (lowercase) to its body. Code fences are skipped when finding headings."""
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    current = None
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        m = None if in_code else H2.match(line)
        if m:
            current = m.group(1).strip().lower()
            order.append(current)
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    result = {k: "\n".join(v) for k, v in sections.items()}
    result["__order__"] = "\n".join(order)
    return result


def split_workstreams(body: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current = None
    for line in body.splitlines():
        m = H3_WS.match(line)
        if m:
            current = m.group(1)
            blocks.setdefault(current, [])
            continue
        if line.startswith("### "):
            current = None
        if current:
            blocks[current].append(line)
    return {k: "\n".join(v) for k, v in blocks.items()}


def parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current = None
    for line in block.splitlines():
        m = FIELD.match(line)
        if m:
            current = m.group(1)
            fields[current] = [m.group(2)]
        elif current:
            fields[current].append(line)
    return {k: "\n".join(v).strip() for k, v in fields.items()}


def parse_table(body: str) -> list[list[str]]:
    rows = []
    for line in body.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            if rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def path_of(cell: str) -> str:
    m = TICKED.search(cell)
    return (m.group(1) if m else cell).strip()


def check(text: str, registry: dict) -> list[str]:
    errors: list[str] = []
    workstreams = {w["id"]: w for w in registry["workstreams"]}

    if len(text.splitlines()) < MIN_LINES:
        errors.append(f"only {len(text.splitlines())} lines; a complete mission order has at least {MIN_LINES}. "
                      "Copy each workstream section from mission/BRIEF.md in full")

    for n, line in enumerate(text.splitlines(), 1):
        if re.search("[\u2013\u2014]", line):
            errors.append(f"line {n}: em or en dash; rewrite the sentence")
        if "{{" in line:
            errors.append(f"line {n}: template placeholder left in: {line.strip()[:60]}")

    sections = split_h2(text)
    order = sections.pop("__order__").splitlines()
    present = [h for h in HEADINGS if h.lower() in sections]
    for i, h in enumerate(HEADINGS, 1):
        if h.lower() not in sections:
            errors.append(f"missing heading '## {i}. {h}'")
    positions = [order.index(h.lower()) for h in present]
    if positions != sorted(positions):
        errors.append("headings out of order; follow mission/PROMPT-TEMPLATE.md")

    ws_body = sections.get("workstreams", "")
    blocks = split_workstreams(ws_body)
    for wid, ws in workstreams.items():
        if wid not in blocks:
            errors.append(f"{wid}: missing '### {wid} {ws['name']}' under ## 3. Workstreams")
            continue
        fields = parse_fields(blocks[wid])
        for f in FIELDS:
            if not fields.get(f):
                errors.append(f"{wid}: missing or empty **{f}:** field")
        listed = {path_of(p) for p in TICKED.findall(fields.get("Files", ""))}
        if fields.get("Files"):
            for p in ws["files"]:
                if p not in listed:
                    errors.append(f"{wid}: **Files:** does not list `{p}`")
            for p in sorted(listed - set(ws["files"])):
                errors.append(f"{wid}: **Files:** lists `{p}`, which mission/workstreams.json does not assign to {wid}")
        if fields.get("Interface"):
            lines = {code_line(l) for l in fields["Interface"].splitlines()}
            for sig in ws["signatures"]:
                if sig not in lines:
                    errors.append(f"{wid}: **Interface:** lacks this line from mission/BRIEF.md, copy it exactly: {sig}")
        test_file = ws["test_module"].replace(".", "/") + ".py"
        if fields.get("Tests") and test_file not in fields["Tests"]:
            errors.append(f"{wid}: **Tests:** does not name {test_file}")
        if fields.get("Requirements"):
            for rid in ws["requirements"]:
                if not re.search(rf"(?<![\w-]){re.escape(rid)}(?![\w-])", fields["Requirements"]):
                    errors.append(f"{wid}: **Requirements:** does not list {rid}")
        if fields.get("Depends on"):
            mentioned = set(WS_ID.findall(fields["Depends on"]))
            for dep in ws["depends_on"]:
                if dep not in mentioned:
                    errors.append(f"{wid}: **Depends on:** must name {dep}")
        if fields.get("Done") and ws["test_module"] not in fields["Done"]:
            errors.append(f"{wid}: **Done:** must include `python3 -m unittest {ws['test_module']}`")
        if fields.get("Done") and f"mission_status.py --verify {wid}" not in fields["Done"]:
            errors.append(f"{wid}: **Done:** must include `python3 tools/mission_status.py --verify {wid}`")
    for wid in sorted(set(blocks) - set(workstreams)):
        errors.append(f"{wid}: unknown workstream; the brief defines W1 to W6 only")

    errors += check_ownership(sections.get("file ownership"), registry)
    errors += check_waves(sections.get("dependency order"), workstreams)

    for heading, phrases in REQUIRED_PHRASES.items():
        body = sections.get(heading.lower())
        if body is None:
            continue
        for phrase in phrases:
            if norm(phrase) not in norm(body):
                errors.append(f"## {heading}: must contain '{phrase}'")
    return errors


def check_ownership(body: str | None, registry: dict) -> list[str]:
    if body is None:
        return []
    rows = parse_table(body)
    if not rows:
        return ["## File ownership: no | File | Owner | table"]
    errors = []
    expected = {p: w["id"] for w in registry["workstreams"] for p in w["files"]}
    expected.update({p: "commander" for p in registry["commander_files"]})
    seen: dict[str, str] = {}
    for cells in rows:
        if len(cells) < 2:
            continue
        path, owner = path_of(cells[0]), cells[1].strip("` ").strip()
        owner = "commander" if owner.lower().startswith("commander") else owner
        if path in seen:
            errors.append(f"## File ownership: `{path}` owned twice ({seen[path]} and {owner})")
            continue
        seen[path] = owner
        if path not in expected:
            errors.append(f"## File ownership: `{path}` is not in the brief")
        elif expected[path] != owner:
            errors.append(f"## File ownership: `{path}` belongs to {expected[path]}, not {owner}")
    for path, owner in expected.items():
        if path not in seen:
            errors.append(f"## File ownership: no row for `{path}` ({owner})")
    return errors


def check_waves(body: str | None, workstreams: dict) -> list[str]:
    if body is None:
        return []
    rows = parse_table(body)
    if not rows:
        return ["## Dependency order: no | Wave | Workstreams | Starts when | table"]
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    waves = []
    for cells in rows:
        m = re.search(r"\d+", cells[0])
        if not m or len(cells) < 2:
            return [f"## Dependency order: cannot read row {' | '.join(cells)}"]
        wave = int(m.group())
        waves.append(wave)
        for wid in WS_ID.findall(cells[1]):
            first.setdefault(wid, wave)
            last[wid] = wave
    errors = []
    if waves != sorted(waves):
        errors.append("## Dependency order: waves are not in ascending order")
    for wid, ws in workstreams.items():
        if wid not in first:
            errors.append(f"## Dependency order: {wid} is in no wave")
            continue
        if not ws["depends_on"] and first[wid] != min(waves):
            errors.append(f"## Dependency order: {wid} has no dependencies, so it starts in wave {min(waves)} with the other parallel workstreams")
        for dep in ws["depends_on"]:
            if dep in first and first[wid] <= first[dep]:
                errors.append(f"## Dependency order: {wid} starts in wave {first[wid]} but depends on {dep} (wave {first[dep]})")
        for dep in ws.get("final_after", []):
            if dep in first and last[wid] <= first[dep]:
                errors.append(f"## Dependency order: the final {wid} pass (wave {last[wid]}) must come after {dep} (wave {first[dep]})")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prompt", type=Path, help="generated mission prompt, for example mission/MISSION-PROMPT.md")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="workstream registry (default %(default)s)")
    args = parser.parse_args(argv)
    if not args.prompt.is_file():
        print(f"FAIL: {args.prompt} does not exist")
        return 1
    errors = check(args.prompt.read_text(encoding="utf-8"), json.loads(args.registry.read_text(encoding="utf-8")))
    for e in errors:
        print(f"FAIL: {e}")
    if errors:
        print(f"{len(errors)} problem(s) in {args.prompt}. Fix them and run the check again.")
        return 1
    print(f"PASS: {args.prompt} has every section, all six workstreams with every requirement ID and interface line, one owner per file, a valid dependency order, the launch rules, the check-in protocol, and done criteria.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
