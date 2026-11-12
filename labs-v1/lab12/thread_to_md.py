#!/usr/bin/env python3
"""Turn an exported OpenCode session (JSON) into a short Markdown handoff.

Usage: python thread_to_md.py <export.json> > handoff.md

Keeps the title and the text of user and assistant messages. Drops tool calls,
tool output, and reasoning, so the handoff is short and has no file contents.
Works with exports from OpenCode 1 (`opencode export`) and OpenCode 2
(`opencode session export`). Standard library only.
"""
import json
import sys


def texts(node):
    """Yield (role, text) pairs from any nesting of messages and parts."""
    if isinstance(node, dict):
        # OpenCode 2: {"type": "user", "text": ...} or {"type": "assistant", "content": [...]}
        if node.get("type") == "user" and isinstance(node.get("text"), str):
            if node["text"].strip():
                yield "user", node["text"].strip()
            return
        if node.get("type") == "assistant" and isinstance(node.get("content"), list):
            chunks = [c.get("text", "") for c in node["content"] if isinstance(c, dict) and c.get("type") == "text"]
            text = "\n\n".join(c.strip() for c in chunks if c and c.strip())
            if text:
                yield "assistant", text
            return
        # OpenCode 1: {"info": {"role": ...}, "parts": [...]}
        info = node.get("info") if isinstance(node.get("info"), dict) else {}
        role = node.get("role") or info.get("role")
        parts = node.get("parts")
        if role in ("user", "assistant") and isinstance(parts, list):
            chunks = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
            text = "\n\n".join(c.strip() for c in chunks if c and c.strip())
            if text:
                yield role, text
            return
        for value in node.values():
            yield from texts(value)
    elif isinstance(node, list):
        for item in node:
            yield from texts(item)


def title(data):
    for key in ("info", "session"):
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, dict) and value.get("title"):
            return value["title"]
    return "Untitled session"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python thread_to_md.py <export.json>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        data = json.load(f)
    pairs = list(texts(data))
    if not pairs:
        print("thread_to_md: no user or assistant text found", file=sys.stderr)
        return 1
    print(f"# Handoff: {title(data)}\n")
    for role, text in pairs:
        print(f"## {'Request' if role == 'user' else 'Answer'}\n\n{text}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
