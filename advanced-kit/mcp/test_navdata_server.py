"""Drive navdata_server.py over stdio the way an MCP client does.

    python3 -m unittest advanced-kit/mcp/test_navdata_server.py   (from the repository root)
    SKYROUTE_ROOT=/path/to/workspace python3 -m unittest test_navdata_server

SKYROUTE_ROOT selects the SkyRoute workspace; the default is labs/skyroute in this
repository. Python standard library only.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE / "navdata_server.py"
DEFAULT_ROOT = HERE.parent.parent / "labs" / "skyroute"
INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}}


def exchange(messages, root=None):
    env = dict(os.environ, SKYROUTE_ROOT=str(root or os.environ.get("SKYROUTE_ROOT") or DEFAULT_ROOT))
    payload = "".join(json.dumps(m) + "\n" for m in [INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"}, *messages])
    proc = subprocess.run([sys.executable, str(SERVER)], input=payload, capture_output=True, text=True, env=env, timeout=30)
    responses = {r["id"]: r for r in map(json.loads, proc.stdout.splitlines())}
    return responses, proc


def call(name, arguments, root=None):
    responses, _ = exchange([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}], root)
    return responses[1]


def payload(response):
    result = response["result"]
    return result["isError"], result["content"][0]["text"]


class HandshakeTests(unittest.TestCase):
    def test_initialize_and_list_tools(self):
        responses, proc = exchange([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 2, "method": "ping"}])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(sorted(responses), [0, 1, 2])
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "navdata")
        self.assertEqual([t["name"] for t in responses[1]["result"]["tools"]], ["lookup_fix", "distance_nm", "route_legs"])
        self.assertEqual(responses[2]["result"], {})

    def test_unknown_method_and_tool(self):
        responses, _ = exchange([
            {"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "no_such_tool", "arguments": {}}},
        ])
        self.assertEqual(responses[1]["error"]["code"], -32601)
        self.assertEqual(responses[2]["error"]["code"], -32602)


class LookupFixTests(unittest.TestCase):
    def test_airport(self):
        is_error, text = payload(call("lookup_fix", {"ident": "kdvt"}))
        self.assertFalse(is_error)
        self.assertEqual(json.loads(text), {
            "ident": "KDVT", "kind": "AP", "name": "PHOENIX DEER VALLEY",
            "lat": 33.688333, "lon": -112.0825, "elev_ft": 1478, "freq_mhz": None,
        })

    def test_navaid_frequency(self):
        is_error, text = payload(call("lookup_fix", {"ident": "SRV"}))
        self.assertFalse(is_error)
        self.assertEqual(json.loads(text)["freq_mhz"], 113.9)

    def test_unknown_fix_is_tool_error(self):
        is_error, text = payload(call("lookup_fix", {"ident": "NOPE1"}))
        self.assertTrue(is_error)
        self.assertIn("Unknown fix: NOPE1", text)

    def test_missing_argument_is_tool_error(self):
        is_error, text = payload(call("lookup_fix", {}))
        self.assertTrue(is_error)
        self.assertIn('"ident"', text)


class DistanceTests(unittest.TestCase):
    def test_kdvt_to_kphx(self):
        is_error, text = payload(call("distance_nm", {"from": "KDVT", "to": "KPHX"}))
        self.assertFalse(is_error)
        result = json.loads(text)
        self.assertEqual((result["from"], result["to"]), ("KDVT", "KPHX"))
        self.assertAlmostEqual(result["distance_nm"], 15.666, places=2)

    def test_unknown_destination(self):
        is_error, text = payload(call("distance_nm", {"from": "KDVT", "to": "ZZZZZ"}))
        self.assertTrue(is_error)
        self.assertIn("ZZZZZ", text)


class RouteLegsTests(unittest.TestCase):
    def test_three_fix_route(self):
        is_error, text = payload(call("route_legs", {"route": "KDVT, ZUNIX ,kmsp"}))
        self.assertFalse(is_error)
        result = json.loads(text)
        self.assertEqual(result["route"], ["KDVT", "ZUNIX", "KMSP"])
        self.assertEqual([(leg["from"], leg["to"]) for leg in result["legs"]], [("KDVT", "ZUNIX"), ("ZUNIX", "KMSP")])
        self.assertAlmostEqual(result["sum_of_legs_nm"], sum(leg["distance_nm"] for leg in result["legs"]), places=2)

    def test_single_fix_is_tool_error(self):
        is_error, text = payload(call("route_legs", {"route": "KDVT"}))
        self.assertTrue(is_error)
        self.assertIn("at least two fixes", text)

    def test_unknown_fix_in_route(self):
        is_error, text = payload(call("route_legs", {"route": "KDVT,BOGUS,KMSP"}))
        self.assertTrue(is_error)
        self.assertIn("Unknown fix: BOGUS", text)


class WorkspaceTests(unittest.TestCase):
    def test_missing_skyroute_is_tool_error(self):
        is_error, text = payload(call("lookup_fix", {"ident": "KDVT"}, root=HERE))
        self.assertTrue(is_error)
        self.assertIn("No SkyRoute package", text)


if __name__ == "__main__":
    unittest.main()
