# Lab AL04: Build an MCP Server and Use Code Mode

**Time:** 30 min  **Modules:** A07  **You will:** finish a stdlib MCP server for SkyRoute navigation data, connect it next to the requirements server, watch the agent call both through one Code Mode `execute` script, then compare with `codemode: false` and gate one tool by name.

**Where:** `~/skyroute-al04`

Repeats Demo A07 (One step, many tools). Same as the demo: the `navdata` and `requirements` servers, one prompt that gets route legs and requirements in a single `execute` call, reading the script the model wrote, and the rerun with `codemode: false`. New in the lab: you write the three `navdata` tools yourself, test the handshake by hand, check the server through the API, and add a per-tool permission rule.

## Before you start

- You need the course repository clone and `python3`. Set `COURSE` to the clone in every terminal you open for this lab, for example `export COURSE=~/opencode-advanced-labs`.
- Create a fresh workspace. It is a Git repository with the SkyRoute starter as one commit, so it needs no earlier lab:

  ```bash
  bash "$COURSE/labs/AL01-power-session/new-workspace.sh" ~/skyroute-al04
  cd ~/skyroute-al04
  ```

  The script prints `created ... from skyroute-starter-v2` and then `FAILED (failures=1)`. That one failure is the seeded route defect D2; leave it. To start over, add `--force`.
- Open two terminals in `~/skyroute-al04`: one for OpenCode, one for **Check** commands. Always start OpenCode in the workspace. Both servers read SkyRoute files relative to it.
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README).
- Catch-up path: if you fall behind on step 2, copy the reference server over yours and continue from step 3: `cp "$COURSE/advanced-kit/mcp/navdata_server.py" .opencode/mcp/navdata_server.py`.

## Steps

1. **Copy the scaffold and talk to it by hand.** The scaffold has working JSON-RPC plumbing and three tool stubs. In the second terminal:

   ```bash
   mkdir -p .opencode/mcp
   cp "$COURSE/labs/AL04-mcp-codemode/navdata_server_scaffold.py" .opencode/mcp/navdata_server.py
   cp "$COURSE/starter-kit/mcp/requirements_server.py" .opencode/mcp/
   printf '%s\n' \
     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"lab","version":"1"}}}' \
     '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
     '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"lookup_fix","arguments":{"ident":"KDVT"}}}' \
     | python3 .opencode/mcp/navdata_server.py | grep -o '"name": "[a-z_]*"\|"text": "TODO[^"]*"\|"isError": [a-z]*'
   ```

   **Check:** one stderr line starts `navdata-mcp: initialize: client asked for 2025-06-18`, then six lines: `"name": "navdata"`, `"name": "lookup_fix"`, `"name": "distance_nm"`, `"name": "route_legs"`, `"text": "TODO(AL04): lookup_fix is not implemented yet"`, and `"isError": true`. A stub raises `ToolError`, and the server turns it into an error result the model can read instead of crashing.

2. **Implement the three tools.** Open `.opencode/mcp/navdata_server.py` and find `Lab AL04: your code goes here`. Replace each `raise ToolError("TODO(AL04)...")` line. The helpers above that line do the plumbing: `skyroute()` imports the workspace package, `string_arg()` validates an argument, `find_fix()` turns an ident into a fix or a `ToolError`, and `fix_record()` turns a fix into a dict.

   - `lookup_fix`: `navdata, _, _ = skyroute()`, then return `fix_record(find_fix(navdata, string_arg(arguments, "ident")))`.
   - `distance_nm`: look up `from` and `to` the same way, then return `from` and `to` (each fix's normalized `ident`), plus `distance_nm` and `initial_bearing_deg` from `geo.distance_nm(lat1, lon1, lat2, lon2)` and `geo.initial_bearing_deg(lat1, lon1, lat2, lon2)`, each rounded to 3 places.
   - `route_legs`: split `route` on commas, strip each part, and skip empty parts, raise `ToolError("A route needs at least two fixes, for example KDVT,ZUNIX,KMSP")` for fewer than two, call `find_fix` on each ident so an unknown fix is a clear error, then build `route.Route.from_idents(idents).legs()`. Return `route` (the normalized idents, taken from the legs: each leg's `start.ident`, then the last leg's `end.ident`), `legs` (each with `from`, `to`, `distance_nm`, `bearing_deg`, the idents again from `leg.start.ident` and `leg.end.ident`), and `sum_of_legs_nm` (rounded to 3 places). Use the idents from the legs, not the strings the caller sent: the tests send `"KDVT, ZUNIX ,kmsp"` and expect `["KDVT", "ZUNIX", "KMSP"]` back.

   You may ask OpenCode to help, but read what it writes: this server is code your agent will trust. Then run the reference tests against your server and call one tool by hand:

   ```bash
   cp "$COURSE/advanced-kit/mcp/test_navdata_server.py" .opencode/mcp/
   SKYROUTE_ROOT="$PWD" python3 -m unittest discover -s .opencode/mcp -p 'test_*.py'
   printf '%s\n' \
     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"lab","version":"1"}}}' \
     '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"route_legs","arguments":{"route":"KMSP,ZUNIX,KDVT"}}}' \
     | python3 .opencode/mcp/navdata_server.py 2>/dev/null | tail -n 1 \
     | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['content'][0]['text'])"
   ```

   **Check:** the tests end with `Ran 12 tests` and `OK`. With the stubs they end `FAILED (failures=10)`. The hand call prints two legs, `KMSP` to `ZUNIX` at `"distance_nm": 914.295` and `ZUNIX` to `KDVT` at `"distance_nm": 187.18`, with `"bearing_deg": -122.563` and `-124.642`, and `"sum_of_legs_nm": 1101.475`. The negative bearings are not your bug. The server reports what the workspace code computes, and `geo.py` still has the seeded defect D1.

3. **Register both servers.** Create `opencode.jsonc` in the workspace:

   ```jsonc
   {
     "$schema": "https://opencode.ai/config.json",
     "mcp": {
       "servers": {
         // Your server. Tools become navdata_lookup_fix, navdata_distance_nm, navdata_route_legs.
         "navdata": {
           "type": "local",
           "command": ["python3", ".opencode/mcp/navdata_server.py"]
         },
         // Read-only requirements lookup from the starter kit.
         "requirements": {
           "type": "local",
           "command": ["python3", ".opencode/mcp/requirements_server.py"]
         }
       }
     }
   }
   ```

   Servers live under `mcp.servers`. On Windows, unless `bash "$COURSE/labs/advanced-preflight.sh"` shows a working `python3`, write `"command": ["py", "-3", ".opencode/mcp/navdata_server.py"]` (and the same for `requirements`): the service starts the server itself and never sees Git Bash functions, so the Microsoft Store `python3` stub makes the server show `failed`.

   Then ask the service, through the CLI and through the API the TUI uses:

   ```bash
   opencode mcp list
   opencode api GET "/api/mcp?location[directory]=$(pwd -W 2>/dev/null || pwd)"
   ```

   **Check:** `opencode mcp list` prints `✓ navdata  connected` and `✓ requirements  connected`. The API returns `"data":[{"name":"navdata","status":{"status":"connected"}},{"name":"requirements","status":{"status":"connected"}}]`. The first call after a config change can print `No MCP servers configured`, `pending`, `"data":[]`, or even the previous `failed` error while the service loads the directory. Run it again. Without `?location[directory]=$(pwd -W 2>/dev/null || pwd)` the API answers for your home directory and lists nothing.

4. **Make the agent call both servers in one script.** Start `opencode` in the first terminal and type `/mcps`. Both servers are listed as connected; press **Esc**. Make sure the footer shows **Build**, then send:

   ```text
   Check route KMSP,ZUNIX,KDVT against requirements SR-GEO-002 and SR-RTE-002.
   Get the legs from the navdata server and both requirements from the
   requirements server, all at once, and keep only what you need. Then tell me
   which legs violate SR-GEO-002 and quote the requirement text.
   ```

   Code Mode is on by default, so MCP tools are not on the model's tool list. They sit in the catalog behind one tool, `execute`, under a namespace per server: `tools.navdata` and `tools.requirements`.

   **Check:** the transcript shows an `execute` tool call, not separate `navdata_*` calls. The answer quotes `Initial bearing shall be expressed in true degrees normalized to the range [0, 360).` and says both legs violate it, because `-122.563` and `-124.642` are outside `[0, 360)`. A good answer also gives the normalized values, `237.437` and `235.358`.

5. **Read the script the model wrote.** The transcript shows the `execute` call; the full script is in the session record. In the second terminal:

   ```bash
   opencode session list | head -n 3
   opencode session export <session-id> > al04-codemode.json
   python3 - al04-codemode.json <<'EOF'
   import json, sys
   for m in json.load(open(sys.argv[1], encoding="utf-8"))["messages"]:
       for p in m.get("content", []) if m["type"] == "assistant" else []:
           if p.get("type") == "tool":
               print("TOOL", p["name"], p["state"]["status"], "(script error)" if p["state"].get("metadata", {}).get("error") else "")
               print(p["state"]["input"].get("code", json.dumps(p["state"]["input"])))
   EOF
   ```

   Use the newest ID from `opencode session list`; it lists sessions for the current directory. The script opens the export as UTF-8. On Windows, also set `export PYTHONUTF8=1` in Git Bash (the Windows note in [`labs/README.md`](../README.md#before-any-lab)); without it, other Python one-liners that read an export stop with `UnicodeDecodeError`.

   **Check:** at least one `TOOL execute completed` line, followed by JavaScript that calls `tools.navdata.route_legs({ route: "KMSP,ZUNIX,KDVT" })` and `tools.requirements.get_requirement(...)` twice, usually inside `Promise.all` or `Promise.allSettled`. Note how many tool calls the session made and whether the script returned a trimmed summary or the raw payloads.

6. **Turn Code Mode off and compare.** Add `"codemode": false` to both server entries in `opencode.jsonc`, for example:

   ```jsonc
         "navdata": {
           "type": "local",
           "command": ["python3", ".opencode/mcp/navdata_server.py"],
           "codemode": false
         },
   ```

   Save, type `/new` in the TUI, and send the step 4 prompt again. If you changed `command` to `py -3` in step 3, keep it in these snippets and in step 7. Export the new session with the step 5 commands into `al04-direct.json`.

   **Check:** the export has no `execute` call. It lists `navdata_route_legs` and `requirements_get_requirement` as separate tool calls, each with its input as JSON. Compare the two exports: the number of tool calls, and how much raw tool output the model had to read. With Code Mode, three MCP calls cost one model step; without it, each call is a step unless the model batches them itself.

7. **Gate one tool by name.** Remove both `"codemode": false` lines so Code Mode is back on. Add a `permissions` list next to `mcp`:

   ```jsonc
     "permissions": [
       { "action": "navdata_route_legs", "resource": "*", "effect": "ask" }
     ],
   ```

   The action is the full `<server>_<tool>` name, and the resource for an MCP tool is always `*`. Nested tools inside `execute` still enforce their own rules. Check that the rule is live, then type `/new` and send the step 4 prompt once more:

   ```bash
   opencode api GET "/api/agent?location[directory]=$(pwd -W 2>/dev/null || pwd)" | python3 -c "import json,sys; d=json.load(sys.stdin); d=d.get('data', d); print([r for a in d if a.get('id') == 'build' for r in a['permissions'] if r['action'].startswith('navdata')])"
   ```

   **Check:** the command prints `[{'action': 'navdata_route_legs', 'resource': '*', 'effect': 'ask'}]` (run it twice if the first call prints `[]`). In the TUI, the `execute` call stops on an approval prompt that names `navdata_route_legs`, with **Allow once**, **Always allow**, and **Reject**. Choose **Allow once**. The two `requirements` calls in the same script do not ask.

## Stretch goals

- Add a fourth tool, `nearest_fix` (input `lat`, `lon`; output the closest fix and its distance), to `TOOLS` and `HANDLERS`. Rerun the step 1 handshake to see it listed, then ask a question that needs it. If the agent does not see the new tool, disconnect and reconnect `navdata` from `/mcps`, then `/new`.
- Ask for the script explicitly: "Use one execute call that gets every leg of KDVT,ZUNIX,MESAS,PRARI,LOONZ,KMSP and returns only the legs whose bearing is negative." Compare the size of what the model read with step 4.
- Deny `execute` for this workspace with `{ "action": "execute", "resource": "*", "effect": "deny" }` while both servers still have Code Mode on. Ask the step 4 question and report what the agent says it can reach. Remove the rule afterward.
- Run the step 4 prompt headless with the step 7 `ask` rule still in place: `opencode run "<prompt>" 2> ask.err`. Headless runs cannot ask, so the rule is auto-rejected. On a check run, stderr showed `! permission requested: navdata_route_legs (*); auto-rejecting`. Inside the script, the `route_legs` call was rejected (the wording varies by version, for example `This non-interactive run cannot ask the user for permission, so the request was rejected.`). In the export, the `execute` part's `metadata.toolCalls` shows `navdata.route_legs` as `error` and both `requirements.get_requirement` calls as `completed`. Whether the model still sees the requirements depends on its script: with `Promise.allSettled` it does; with `Promise.all` the one rejection discards the whole batch, and the model reports that it has no data.

## Solution

Reference files in the course repository:

- [`advanced-kit/mcp/navdata_server.py`](../../advanced-kit/mcp/navdata_server.py) is the finished server. Diff it against your copy: `diff --strip-trailing-cr .opencode/mcp/navdata_server.py "$COURSE/advanced-kit/mcp/navdata_server.py"` should show only the module docstring, the scaffold comments, and your three function bodies.
- [`advanced-kit/mcp/test_navdata_server.py`](../../advanced-kit/mcp/test_navdata_server.py) is the test you ran in step 2. It drives the server over stdio the way an MCP client does.
- [`advanced-kit/opencode.advanced.jsonc`](../../advanced-kit/opencode.advanced.jsonc) registers the same `navdata` server. [`starter-kit/mcp/requirements_server.py`](../../starter-kit/mcp/requirements_server.py) is the second server.
- [`advanced-kit/install-advanced.sh`](../../advanced-kit/install-advanced.sh) installs the reference server and config into a workspace in one step: `bash "$COURSE/advanced-kit/install-advanced.sh" ~/skyroute-al04`.

A good result: 12 server tests pass, both servers show connected in `opencode mcp list` and `/api/mcp`, one `execute` script fetched legs and requirements together and found that both westbound legs break SR-GEO-002, the `codemode: false` run made the same calls one by one, and `navdata_route_legs` asked for approval by name even inside `execute`.
