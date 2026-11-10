# Lab AL05: Change the Harness: Write a Plugin

**Time:** 55 min  **Modules:** A09  **You will:** write a local OpenCode plugin that adds a custom tool, checks every Python edit with the compiler and the matching tests before the model moves on, and keeps an audit trail, and prove each part with a real run.

**Where:** `~/skyroute-al05`

Repeats Demo A09 (Change the harness live). Same as the demo: a custom tool the model calls, an `execute.after` hook that runs `py_compile` and the matching test after an edit and shows the failure to the model in the same turn, and a JSON-lines audit log under `.opencode/audit/`. New in the lab: you write all three yourself in one plugin from a skeleton, instead of loading the finished kit plugins, and the AI permission gate becomes a stretch goal.

## Before you start

- You need the course repository clone. Set `COURSE` to it in every terminal for this lab, for example `export COURSE=~/opencode-advanced-labs`.
- Create a fresh workspace. It needs no earlier lab:

  ```bash
  bash "$COURSE/labs/AL01-power-session/new-workspace.sh" ~/skyroute-al05
  cd ~/skyroute-al05
  ```

  The script ends with `FAILED (failures=1)`, the seeded route defect D2 in `tests/test_route.py`. Leave it. To start over, add `--force`. On Windows, `--force` cannot delete a workspace while the OpenCode service still has its plugin or MCP files open, and the script says so. Quit every OpenCode TUI in the workspace, run `opencode service stop`, rerun the script with `--force`, then run `opencode service start`.
- Open two terminals in `~/skyroute-al05`: one for OpenCode, one for **Check** commands and your editor.
- A plugin is TypeScript in `.opencode/plugins/<id>/index.ts`. OpenCode loads it automatically, with no `npm install`, and reloads it when you save. It runs inside the background service with your user's authority, for every session in this directory. Treat it like any other code you run.
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README).
- Catch-up path: each step gives the full code for its TODO. If you fall behind, paste the code for the steps you missed and save. The finished kit plugins in `$COURSE/advanced-kit/plugins/` do the same jobs.

## Steps

1. **Load the skeleton.** The skeleton has helper functions and three TODO comments. It loads as is.

   ```bash
   mkdir -p .opencode/plugins/lab
   cp "$COURSE/labs/AL05-plugin/lab-plugin/index.ts" .opencode/plugins/lab/index.ts
   opencode api GET "/api/plugin?location[directory]=$(pwd -W 2>/dev/null || pwd)" | python3 -c "import json,sys; [print(p.get('id'), p['source']['type'], p['state']) for p in json.load(sys.stdin)['data'] if p['source']['type'] != 'builtin']"
   ```

   Open `.opencode/plugins/lab/index.ts` and read the helpers: `run()` starts a program without a shell and never throws, `appendText()` adds a text part to a tool result, `editedPythonFiles()` finds the `.py` files an `edit`, `write`, or `patch` call changed, `testFileFor()` maps `skyroute/geo.py` to `tests/test_geo.py`, and `trace()` reads one requirement.

   **Check:** the command prints `lab local {'status': 'active'}`. The first call for a new directory can take up to a minute and print nothing while the service loads it; run it again. Keep this command handy. You run it after every save in this lab.

2. **Add a custom tool.** Replace the `TODO 1` comment with:

   ```ts
       await ctx.tool.transform((editor) => {
         editor.add({
           name: "lab_trace",
           description:
             "Look up a SkyRoute requirement by ID, for example SR-FUEL-002. Returns its text, " +
             "the component that implements it, and its listed tests with whether each test file exists.",
           input: {
             type: "object",
             properties: { id: { type: "string", description: "Requirement ID, for example SR-GEO-002" } },
             required: ["id"],
             additionalProperties: false,
           },
           options: { codemode: false },
           execute: async (input: any) => ({ content: trace(root, String(input?.id ?? "")) }),
         })
       })
   ```

   `ctx.tool.transform` edits the tool registry. The model chooses the tool from its `description` and fills `input` from the JSON Schema. `codemode: false` puts it on the model's own tool list instead of behind `execute`. Save, run the step 1 check command, then start `opencode` in the first terminal and send:

   ```text
   Use the lab_trace tool for SR-GEO-002 and tell me whether it has tests.
   ```

   **Check:** the plugin is still `active`. The transcript shows a `lab_trace` call whose output starts `SR-GEO-002: Bearing range`, then `Text: Initial bearing shall be expressed in true degrees normalized to the range [0, 360).`, `Component: skyroute/geo.py`, and `Tests: none listed (gap)`. The answer says the requirement has no tests.

3. **Check every Python edit.** Replace the `TODO 2` comment with:

   ```ts
       await ctx.tool.hook("execute.after", async (event: any) => {
         if (event.status !== "completed" || !["edit", "write", "patch"].includes(event.tool)) return
         const lines: string[] = []
         for (const file of editedPythonFiles(root, event)) {
           const compiled = await run("python3", ["-m", "py_compile", file], root)
           lines.push(`py_compile ${file}: ${compiled.ok ? "PASS" : "FAIL\n" + compiled.output}`)
           const test = compiled.ok ? testFileFor(root, file) : undefined
           if (!test) continue
           const tests = await run("python3", ["-m", "unittest", test], root)
           lines.push(`unittest ${test}: ${tests.ok ? "PASS" : "FAIL\n" + tests.output.slice(-2000)}`)
         }
         if (lines.length) event.result = appendText(event.result, `[lab verify-on-edit]\n${lines.join("\n")}`)
       })
   ```

   `execute.after` runs after every tool call and can replace `event.result`. A tool result is a list of content parts, and the model reads every part, so the appended verdict reaches the model inside the same tool result. V2 has no language server; this hook is your compile-and-test feedback loop. On Windows, the skeleton's `run()` turns `python3` into `py -3`, because the service does not see Git Bash functions and `python3` is often the Microsoft Store stub.

   **Check:** save and run the step 1 check command. It still prints `lab local {'status': 'active'}` and no `failed` entry. The proof needs a real edit, which is the next step.

4. **Watch the agent see a broken edit.** In the TUI, send a plausible but wrong change:

   ```text
   We want kilometres in geo.py. Change the line EARTH_RADIUS_NM = 3440.065 to
   EARTH_RADIUS_NM = 3440.065 * 1.852. Do not run any shell commands.
   ```

   Expand the `edit` call in the transcript after it finishes.

   **Check:** the edit result ends with `[lab verify-on-edit]`, `py_compile skyroute/geo.py: PASS`, and `unittest tests/test_geo.py: FAIL`, then the unittest output with `FAIL: test_distance_kdvt_to_kphx` (`AssertionError: 29.014130821110264 != 15.666 within 2 places`) and `FAIL: test_distance_one_degree_of_longitude_at_equator`, and `FAILED (failures=2)`. In the same turn, without a shell call, the reply names both failing tests and says the change breaks SR-GEO-001 or the tests. Then type `/undo` (or **Ctrl+X** then **U**) and confirm in the second terminal that `git diff --stat` prints nothing.

   To watch the agent repair its own edit in the same turn, as in Demo A09, add `Every existing test must still pass when you are done.` to the prompt. If the agent then restores the constant, its second `edit` result ends with `unittest tests/test_geo.py: PASS`.

5. **Keep an audit trail.** Replace the `TODO 3` comment with:

   ```ts
       const auditDir = join(root, ".opencode", "audit")
       await ctx.tool.hook("execute.after", async (event: any) => {
         const entry = { time: new Date().toISOString(), sessionID: event.sessionID, agent: event.agent, tool: event.tool, status: event.status }
         try {
           await mkdir(auditDir, { recursive: true })
           await appendFile(join(auditDir, "lab.jsonl"), JSON.stringify(entry) + "\n")
         } catch (error) {
           console.error(`lab audit: cannot write ${auditDir}: ${String(error)}`)
         }
       })
   ```

   `mkdir` and `appendFile` come from `node:fs/promises`, imported at the top of the skeleton. The hook awaits them instead of calling `mkdirSync` and `appendFileSync`, because a blocking call inside a hook stalls the service that every client shares. A failed write is reported on the service log and does not fail the tool call. The entry keeps metadata only. Tool input and output can carry file contents, commands, and secrets, so they stay out of the log. Keep the log out of Git:

   ```bash
   echo '.opencode/audit/' >> .gitignore
   ```

   Save, run the step 1 check command, then send in the TUI:

   ```text
   Use lab_trace for SR-FUEL-002, then read skyroute/fuel.py and tell me whether
   the contingency formula matches the requirement.
   ```

   In the second terminal:

   ```bash
   tail -n 3 .opencode/audit/lab.jsonl
   python3 -c "import json, collections; print(collections.Counter((e['tool'], e['status']) for e in map(json.loads, open('.opencode/audit/lab.jsonl', encoding='utf-8'))))"
   ```

   **Check:** each line looks like `{"time":"2026-...","sessionID":"ses_...","agent":"build","tool":"lab_trace","status":"completed"}`. The counter has at least `('lab_trace', 'completed')` and `('read', 'completed')`. A failed tool call shows `"status":"error"`. The answer says the starter computes contingency on trip plus reserve, which breaks SR-FUEL-002 (seeded defect D3).

6. **Compare with the kit, then commit.** Open the finished plugins and find, in each, the one thing yours does not do:

   ```bash
   ls "$COURSE/advanced-kit/plugins"
   grep -n 'timeoutMs\|ENOENT\|disabled' "$COURSE/advanced-kit/plugins/verify-on-edit/index.ts" | head
   grep -n 'event.subscribe\|permission' "$COURSE/advanced-kit/plugins/audit-log/index.ts" | head
   ```

   The kit's `verify-on-edit` reads options, times out a hung test, and reports a missing `python3`. The kit's `audit-log` reads the server event stream instead of tool hooks, so it also records permission requests and replies. Commit your plugin:

   ```bash
   git add .gitignore .opencode/plugins/lab/index.ts
   git commit -m "Lab plugin: lab_trace, verify on edit, audit trail"
   ```

   **Check:** `ls` lists `ai-gate`, `audit-log`, `skyroute-trace`, and `verify-on-edit`. `git log --oneline` shows two commits. `git status --short` prints nothing, because the audit log is ignored.

## Stretch goals

- **AI permission gate.** A second model reviews each shell command and can deny it. Copy the kit plugin and give it a model through a `plugins` entry with options in `opencode.jsonc`:

  ```bash
  mkdir -p .opencode/plugins/ai-gate
  cp "$COURSE/advanced-kit/plugins/ai-gate/index.ts" .opencode/plugins/ai-gate/
  ```

  ```jsonc
  {
    "$schema": "https://opencode.ai/config.json",
    "plugins": [
      {
        "package": "./.opencode/plugins/ai-gate",
        "options": {
          // Placeholders: use the provider ID and model your platform team configures.
          "model": { "providerID": "company-ai", "id": "your-model" },
          "allowPatterns": ["git status *", "git diff *", "python3 -m unittest *"]
        }
      }
    ]
  }
  ```

  Then, in the second terminal, ask for a command that must never run without a human, as in Demo A09. The workspace has no remote, so the push cannot do harm even if it ran:

  ```bash
  opencode run --auto \
    "Run exactly this shell command once and report its output: git push --force origin main"
  ```

  Replace `company-ai` and `your-model` with a `<provider>/<model>` from `opencode models`. The `shell` call fails with a message that starts `ai-gate (<provider>/<model>) denied:` and gives the reviewer's reason, even under `--auto`. Run the same line with `git status` instead: it matches an `allowPatterns` entry, so it runs without a review. The gate needs a model that answers `ctx.generate`; the free `opencode/*` models refuse it, and the gate then fails closed and denies every reviewed command. If you leave out `model`, the gate denies every shell command, including `git status`, with `ai-gate is enabled but has no model`. Add the model or set `"disabled": true`. The gate also reviews an allowed pattern when the command has a writing option such as `--output` or `--out`, or a path outside the workspace: try `git diff --output=../diff.txt`.
- **Shell environment.** Add a shell hook that sets a variable for every command the agent runs:

  ```ts
      await ctx.shell.hook("create.before", (event) => {
        event.env.SKYROUTE_LAB = "AL05"
      })
  ```

  Ask the agent to run `echo SKYROUTE_LAB=$SKYROUTE_LAB` (on Windows the agent's shell is PowerShell, so ask for `echo SKYROUTE_LAB=$env:SKYROUTE_LAB`). The output is `SKYROUTE_LAB=AL05`.
- **Escalate one path.** Make any shell command that touches `requirements/` ask a human, even though the `build` agent allows shell:

  ```ts
      await ctx.permission.hook("evaluate", (event) => {
        if (event.action === "shell" && event.resources.some((r) => r.includes("requirements/"))) {
          event.effect = "ask"
          event.message = "lab: shell commands that touch requirements/ need a human"
        }
      })
  ```

  Ask the agent to run `head -n 3 requirements/requirements.json`. The approval prompt shows **Allow once**, **Always allow**, and **Reject**. Choose **Reject**. A configured `deny` never reaches this hook, so a hook can tighten an `allow` or `ask` but cannot loosen a `deny`.
- Run `python3 -m unittest` from the hook only once per turn instead of after every edit. Which hook or event tells you a turn ended?

## Solution

Reference files in the course repository:

- [`labs/AL05-plugin/lab-plugin/index.ts`](lab-plugin/index.ts) is the skeleton. With the code from steps 2, 3, and 5 pasted in, it is the lab solution.
- [`advanced-kit/plugins/skyroute-trace/index.ts`](../../advanced-kit/plugins/skyroute-trace/index.ts) is the full trace tool, `skyroute_trace`, with a `gaps` mode and checks that each listed test method exists.
- [`advanced-kit/plugins/verify-on-edit/index.ts`](../../advanced-kit/plugins/verify-on-edit/index.ts) is the full edit hook with options, timeouts, and trimmed failure output.
- [`advanced-kit/plugins/audit-log/index.ts`](../../advanced-kit/plugins/audit-log/index.ts) writes `.opencode/audit/YYYY-MM-DD.jsonl` from the event stream, including permission events.
- [`advanced-kit/plugins/ai-gate/index.ts`](../../advanced-kit/plugins/ai-gate/index.ts) is the stretch gate. [`advanced-kit/opencode.advanced.jsonc`](../../advanced-kit/opencode.advanced.jsonc) shows the plugin options for all of them.
- [`advanced-kit/install-advanced.sh`](../../advanced-kit/install-advanced.sh) installs all four kit plugins into a workspace. Do not install them next to your `lab` plugin in the same workspace, or every Python edit gets checked twice.

A good result: the plugin shows `active`, the model called `lab_trace` and quoted its output, a wrong edit came back with `unittest tests/test_geo.py: FAIL` and the agent said so in the same turn without running a shell command, and `.opencode/audit/lab.jsonl` has one line per tool call with no tool input or output in it.
