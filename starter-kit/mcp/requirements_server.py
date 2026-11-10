#!/usr/bin/env python3
"""Read-only MCP server that exposes a requirements file over stdio.

Transport: newline-delimited JSON-RPC 2.0 on stdin/stdout. Logs go to stderr.
Data: REQUIREMENTS_FILE (default requirements/requirements.json, relative to
the working directory), shaped as {"requirements": [{"id": ..., ...}]}.
The file is re-read on every call so edits show up without a restart.
Python standard library only.
"""

import json
import os
import sys

SERVER_INFO = {"name": "requirements", "version": "1.0.0"}
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
DEFAULT_FILE = os.path.join("requirements", "requirements.json")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = [
    {
        "name": "list_requirements",
        "description": "List software requirements (id, title, text, component, verification, linked tests). "
        "Optionally filter by ID prefix such as SR-FUEL.",
        "inputSchema": {
            "type": "object",
            "properties": {"prefix": {"type": "string", "description": "Optional ID prefix, for example SR-GEO"}},
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    },
    {
        "name": "get_requirement",
        "description": "Get one requirement by its exact ID, for example SR-FUEL-002.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Requirement ID"}},
            "required": ["id"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    },
    {
        "name": "search_requirements",
        "description": "Case-insensitive search over requirement ID, title, text, and component. "
        "Every whitespace-separated word in the query must match.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Words to search for, for example 'contingency fuel'"}},
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    },
]


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class DataError(Exception):
    """The requirements file is missing or malformed."""


def log(message):
    print(f"requirements-mcp: {message}", file=sys.stderr, flush=True)


def requirements_path():
    return os.path.abspath(os.environ.get("REQUIREMENTS_FILE") or DEFAULT_FILE)


def load_requirements():
    path = requirements_path()
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise DataError(f"Requirements file not found: {path}. Set REQUIREMENTS_FILE.")
    except (OSError, ValueError) as exc:
        raise DataError(f"Cannot read requirements file {path}: {exc}")
    items = data.get("requirements") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise DataError(f'{path} must be an object with a "requirements" list')
    valid = [item for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)]
    if len(valid) != len(items):
        log(f"skipped {len(items) - len(valid)} entries without a string id")
    return valid


def string_arg(arguments, name, required):
    value = arguments.get(name)
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()):
        raise RpcError(INVALID_PARAMS, f'Argument "{name}" must be a non-empty string')
    return value.strip()


def list_requirements(arguments):
    prefix = string_arg(arguments, "prefix", required=False).upper()
    found = [r for r in load_requirements() if r["id"].upper().startswith(prefix)]
    return {"count": len(found), "requirements": found}


def get_requirement(arguments):
    wanted = string_arg(arguments, "id", required=True)
    for requirement in load_requirements():
        if requirement["id"].upper() == wanted.upper():
            return requirement
    raise LookupError(f"Unknown requirement id: {wanted}. Use list_requirements or search_requirements to find IDs.")


def search_requirements(arguments):
    words = string_arg(arguments, "query", required=True).lower().split()

    def haystack(requirement):
        return " ".join(str(requirement.get(field, "")) for field in ("id", "title", "text", "component")).lower()

    found = [r for r in load_requirements() if all(word in haystack(r) for word in words)]
    return {"count": len(found), "requirements": found}


HANDLERS = {
    "list_requirements": list_requirements,
    "get_requirement": get_requirement,
    "search_requirements": search_requirements,
}


def text_result(payload, is_error=False):
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def call_tool(params):
    name = params.get("name")
    handler = HANDLERS.get(name)
    if handler is None:
        raise RpcError(INVALID_PARAMS, f"Unknown tool: {name}")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise RpcError(INVALID_PARAMS, "Tool arguments must be an object")
    try:
        return text_result(handler(arguments))
    except (LookupError, DataError) as exc:
        return text_result(str(exc), is_error=True)


def initialize(params):
    requested = params.get("protocolVersion")
    version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
    log(f"initialize: client asked for {requested}, answering {version}; data file {requirements_path()}")
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": SERVER_INFO,
        "instructions": "Read-only access to the project's software requirements. Use get_requirement for one ID, "
        "search_requirements for keywords, and list_requirements for all requirements or an ID prefix.",
    }


METHODS = {
    "initialize": initialize,
    "ping": lambda params: {},
    "tools/list": lambda params: {"tools": TOOLS},
    "tools/call": call_tool,
}


def error_response(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(message):
    """Return the response for one message, or None when no response is due (notifications)."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        request_id = message.get("id") if isinstance(message, dict) else None
        return error_response(request_id, INVALID_REQUEST, "Invalid Request")
    if "id" not in message:
        return None
    request_id = message["id"]
    params = message.get("params") or {}
    try:
        if not isinstance(params, dict):
            raise RpcError(INVALID_PARAMS, "params must be an object")
        handler = METHODS.get(message["method"])
        if handler is None:
            raise RpcError(METHOD_NOT_FOUND, f"Method not found: {message['method']}")
        return {"jsonrpc": "2.0", "id": request_id, "result": handler(params)}
    except RpcError as exc:
        return error_response(request_id, exc.code, exc.message)
    except Exception as exc:
        log(f"internal error in {message['method']}: {exc!r}")
        return error_response(request_id, INTERNAL_ERROR, "Internal error")


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response = error_response(None, PARSE_ERROR, "Parse error")
        else:
            response = handle(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
