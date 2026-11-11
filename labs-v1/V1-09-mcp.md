# Lab 9: MCP server

**Time:** 30 min  **You will:** connect a local MCP server that serves the requirements, and use it in prompts.

The server is `starter-kit/mcp/requirements_server.py` in the course repository. It is read-only, uses only the Python standard library, and reads `requirements/requirements.json`.

## Steps

1. **Run it by hand** in T2, from `labs/skyroute`:

   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python ../../starter-kit/mcp/requirements_server.py
   ```

   **Check:** the output lists `list_requirements`, `get_requirement`, and `search_requirements`.

2. **Connect it.** Add an `mcp` block to `labs/skyroute/opencode.json`, next to `permission`:

   ```json
   "mcp": {
     "requirements": {
       "type": "local",
       "command": ["python", "../../starter-kit/mcp/requirements_server.py"],
       "enabled": true
     }
   }
   ```

   Windows: use `"py", "-3", "../../starter-kit/mcp/requirements_server.py"`.

3. In T2: `opencode mcp list`. **Check:** `requirements` is connected.

4. Restart OpenCode. `/new`, **Plan**. Send:

   ```text
   Use the requirements tools to find every requirement about fuel.
   For each, give the ID, the text, and the tests it lists.
   ```

   **Check:** the session shows calls to `requirements_search_requirements` or `requirements_list_requirements`, and the answer lists `SR-FUEL-001` to `SR-FUEL-003`.

5. **Combine tool and code.** Send:

   ```text
   Get SR-RPT-003 with the requirements tool. Then read skyroute/report.py and
   tell me if the code meets it. Give file:line.
   ```

   **Check:** the answer quotes the requirement from the tool and cites `report.py`.

6. **Turn a tool off.** In the `permission` block of `opencode.json`, add:

   ```json
   "requirements_list_requirements": "deny"
   ```

   Restart and repeat step 4. **Check:** only `search_requirements` or `get_requirement` are used.

7. Commit: `git add opencode.json && git commit -m "Lab 9: MCP"`.

## Stretch

Point the server at another file by adding `"environment": { "REQUIREMENTS_FILE": "requirements/requirements.json" }` to the server entry, then copy and edit that file to see changes without a restart.
