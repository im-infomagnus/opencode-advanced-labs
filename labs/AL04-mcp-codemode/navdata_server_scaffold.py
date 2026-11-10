#!/usr/bin/env python3
"""Lab AL04 scaffold: an MCP server for SkyRoute navigation data over stdio.

The protocol plumbing works as is. Implement the three tools marked TODO(AL04);
the reference solution is advanced-kit/mcp/navdata_server.py.

Transport: newline-delimited JSON-RPC 2.0 on stdin/stdout. Logs go to stderr.
Data: the SkyRoute package of the workspace. The server imports `skyroute` from
SKYROUTE_ROOT, or from the working directory when SKYROUTE_ROOT is unset, so the
answers come from the same code the tests run (seeded defects included).
Python standard library only.
"""

import importlib
import json
import os
import sys

SERVER_INFO = {"name": "navdata", "version": "1.0.0"}
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = [
    {
        "name": "lookup_fix",
        "description": "Look up one navigation fix (airport, waypoint, or navaid) by identifier, for example KDVT or ZUNIX. "
        "Returns kind, name, latitude and longitude in decimal degrees, elevation in feet, and frequency in MHz.",
        "inputSchema": {
            "type": "object",
            "properties": {"ident": {"type": "string", "description": "Fix identifier, case-insensitive"}},
            "required": ["ident"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    },
    {
        "name": "distance_nm",
        "description": "Great-circle distance in nautical miles and initial true bearing in degrees between two fixes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from": {"type": "string", "description": "Departure fix identifier"},
                "to": {"type": "string", "description": "Destination fix identifier"},
            },
            "required": ["from", "to"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    },
    {
        "name": "route_legs",
        "description": "Split a route such as KDVT,ZUNIX,KMSP into legs with distance and initial bearing, "
        "plus the sum of the leg distances.",
        "inputSchema": {
            "type": "object",
            "properties": {"route": {"type": "string", "description": "Comma-separated fix identifiers, at least two"}},
            "required": ["route"],
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


class ToolError(Exception):
    """A problem the model can fix: bad arguments, unknown fix, SkyRoute not found."""


def log(message):
    print(f"navdata-mcp: {message}", file=sys.stderr, flush=True)


def skyroute_root():
    return os.path.abspath(os.environ.get("SKYROUTE_ROOT") or os.getcwd())


def skyroute():
    """Import skyroute.navdata, skyroute.geo, and skyroute.route from the workspace."""
    root = skyroute_root()
    if not os.path.isfile(os.path.join(root, "skyroute", "navdata.py")):
        raise ToolError(f"No SkyRoute package at {root}. Start the server in the workspace or set SKYROUTE_ROOT.")
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        return tuple(importlib.import_module(f"skyroute.{name}") for name in ("navdata", "geo", "route"))
    except Exception as exc:
        raise ToolError(f"Cannot import skyroute from {root}: {exc}")


def string_arg(arguments, name):
    value = arguments.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f'Argument "{name}" must be a non-empty string')
    return value.strip()


def find_fix(navdata, ident):
    fix = navdata.lookup(ident)
    if fix is None:
        raise ToolError(f"Unknown fix: {ident.upper()}. Check the identifier in data/navdata.srn.")
    return fix


def fix_record(fix):
    return {
        "ident": fix.ident,
        "kind": fix.kind,
        "name": fix.name,
        "lat": round(fix.lat, 6),
        "lon": round(fix.lon, 6),
        "elev_ft": fix.elev,
        "freq_mhz": fix.freq,
    }


# ---------------------------------------------------------------- Lab AL04: your code goes here
# Each tool receives the `arguments` object the model sent and returns a dict (sent
# as JSON text) or raises ToolError (sent as an isError result the model can read).
# The helpers above do the plumbing: skyroute() imports the workspace package,
# string_arg() validates one argument, find_fix() turns an ident into a Fix or a
# ToolError, and fix_record() turns a Fix into a dict.


def lookup_fix(arguments):
    # TODO(AL04): return fix_record() for arguments["ident"].
    # Hint: navdata, _, _ = skyroute()
    raise ToolError("TODO(AL04): lookup_fix is not implemented yet")


def distance_nm(arguments):
    # TODO(AL04): look up arguments["from"] and arguments["to"], then return
    # {"from", "to", "distance_nm", "initial_bearing_deg"} using geo.distance_nm and
    # geo.initial_bearing_deg (round to 3 places).
    raise ToolError("TODO(AL04): distance_nm is not implemented yet")


def route_legs(arguments):
    # TODO(AL04): split arguments["route"] on commas, require at least two fixes,
    # build route.Route.from_idents(idents), and return the legs (from, to,
    # distance_nm, bearing_deg) plus "sum_of_legs_nm".
    raise ToolError("TODO(AL04): route_legs is not implemented yet")


HANDLERS = {
    "lookup_fix": lookup_fix,
    "distance_nm": distance_nm,
    "route_legs": route_legs,
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
    except ToolError as exc:
        return text_result(str(exc), is_error=True)


def initialize(params):
    requested = params.get("protocolVersion")
    version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
    log(f"initialize: client asked for {requested}, answering {version}; SkyRoute root {skyroute_root()}")
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": SERVER_INFO,
        "instructions": "Read-only SkyRoute navigation data. Use lookup_fix for one identifier, distance_nm between two fixes, "
        "and route_legs for a comma-separated route.",
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
