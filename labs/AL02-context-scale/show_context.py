#!/usr/bin/env python3
"""Summarize what a session's model sees, one line per context entry.

    opencode api session.context --param sessionID=<id> > .git/context.json
    python3 show_context.py .git/context.json

Write the API output to a file first: OpenCode 2.1 can cut `opencode api` output
written to a pipe at 256 KiB. With no file argument the script reads stdin. The input is the JSON from GET /api/session/{sessionID}/context: the messages after
the last compaction. Tool calls show their main input (path, pattern, or command).
"""
import json
import os
import sys


def short(path):
    try:
        rel = os.path.relpath(path)
    except ValueError:
        return path.replace("\\", "/")
    # Forward slashes on every platform, so the lab's expected strings match on Windows too.
    return (path if rel.startswith(("../..", "..\\..")) else rel).replace("\\", "/")


def tool_summary(part):
    args = part.get("state", {}).get("input") or {}
    target = args.get("path") or args.get("pattern") or args.get("command") or args.get("description") or args.get("id") or ""
    status = part.get("state", {}).get("status", "")
    target = short(str(target))
    if len(target) > 70:
        target = "..." + target[-67:]
    return f"{part.get('name')}({target}) {status}".strip()


def describe(entry):
    kind = entry.get("type")
    if kind == "user":
        return json.dumps(entry.get("text", "")[:90])
    if kind == "assistant":
        parts = []
        for part in entry.get("content", []):
            if part.get("type") == "tool":
                parts.append(tool_summary(part))
            elif part.get("type") == "text" and part.get("text"):
                parts.append("text: " + json.dumps(part["text"][:60]))
        tokens = entry.get("tokens") or {}
        cached = (tokens.get("cache") or {}).get("read", 0)
        return "; ".join(parts) + f"  [tokens in {tokens.get('input', 0)} + cached {cached}]"
    if kind == "synthetic":
        paths = entry.get("metadata", {}).get("instruction", {}).get("paths")
        if paths:
            return "instructions loaded: " + ", ".join(short(p) for p in paths)
        text = " ".join((entry.get("description") or entry.get("text", "")).split())
        return text[:90]
    if kind == "compaction":
        if entry.get("error"):
            err = entry["error"]
            return f"{entry.get('status')} ({entry.get('reason')}) {err.get('type')}: {err.get('message', '')[:60]}"
        first = (entry.get("summary") or "").strip().splitlines()[:1]
        return f"{entry.get('status')} ({entry.get('reason')}) summary starts: {first[0] if first else '(empty)'}"
    if kind == "system":
        text = " ".join((entry.get("description") or entry.get("text", "")).split())
        return text[:90]
    if kind == "agent-switched":
        return f"agent {entry.get('agent')}"
    if kind == "idle":
        return entry.get("outcome", "")
    return json.dumps(entry)[:90]


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as stream:
            data = json.load(stream)
    else:
        data = json.load(sys.stdin)
    entries = data["data"] if isinstance(data, dict) else data
    for i, entry in enumerate(entries):
        print(f"{i:>3} {entry.get('type', '?'):<10} {describe(entry)}")
    print(f"{len(entries)} entries")


if __name__ == "__main__":
    main()
