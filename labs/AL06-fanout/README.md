# Lab AL06: Parallel Worktree Fan-out with a Live Dashboard

**Time:** 45 min  **Modules:** A08, A10  **You will:** fan three independent SkyRoute fixes out to three background subagents in three Git worktrees, watch them in the TUI and on a live API dashboard, then merge, review, and test the result.

**Where:** `~/skyroute-al06`

Repeats Demo A08 (Fan out into worktrees) and Demo A10 (A live dashboard on the server API). Same as Demo A08: the three tasks in `advanced-kit/fanout/TASKS.md`, the prompt in `advanced-kit/fanout/fanout-prompt.md`, the tabs and subagent picker, the merge into `fanout/integration`, and `/diff` against `main`. Same as Demo A10: `demos/mission-control/dashboard.py` and the two API reads behind it. New in the lab: you run the fan-out in your own workspace, point the dashboard at a `build` session instead of the mission commander, check each worktree's isolation yourself before you merge, and make the coordinator's trace commit to `requirements/requirements.json` that the demo skips. Driving a session through the API (the second half of Demo A10) is a stretch goal here.

## Before you start

- You need the course repository clone. Set `COURSE` to it in every terminal for this lab, for example `export COURSE=~/opencode-advanced-labs`.
- Run the preflight once, from the course repository root, if you have not already (Lab AL01 runs it): `bash "$COURSE/labs/advanced-preflight.sh"`. Fix every `FAIL` line before step 1. On Windows it catches the Microsoft Store `python3` stub (exit code 49, `Python was not found`), which breaks the `python3 -m unittest` commands the three child agents run through OpenCode's own shell.
  - **If it reports the stub, repair it, then check again.** Run `bash "$COURSE/labs/advanced-preflight.sh" --fix-python3`, then run the check-only `bash "$COURSE/labs/advanced-preflight.sh"` again in a new terminal. The repair run's own `PASS  created ...python3.exe` line shows only that a file was copied. You are done when the check-only run prints `PASS  python3 3.x (...)`. If it still prints the stub `FAIL` (your Python folder comes after `WindowsApps` on PATH), follow the App execution aliases steps in the Windows note in [`labs/README.md`](../README.md#before-any-lab), then run the check-only preflight again.
  - **If you cannot fix the `python3` line** (for example your Python folder is locked down), use the `py -3` route in full, not only the prompt line:
    - In every Git Bash terminal you use for this lab (T1, T2, and T3), set up the Windows functions and variables from the Windows note in [`labs/README.md`](../README.md#before-any-lab): the `python3` and `python` functions, `PYTHON="py -3"`, and `PYTHONUTF8=1`.
    - Add this line at the end of the step 3 prompt: `On Windows run Python as py -3: tell each child to run py -3 -m unittest instead of python3.`
    - Check it before step 3. In the TUI, type `!py -3 -m unittest tests.test_geo`: it runs in OpenCode's own shell and ends with `OK`. In Git Bash, run `python3 -m unittest tests.test_geo` and the step 2 dashboard command: neither may print `Python was not found`. The prompt line changes only what the children are told; it does not change the dashboard or your manual checks.
  - The `py -3` route does not waive any other preflight `FAIL`. Fix those too, for example the default `model` line.
- Create a fresh starter workspace. It needs no earlier lab, and it must be the starter: the tasks fix seeded defects D1, D3, and S1 to S5.

  ```bash
  bash "$COURSE/labs/AL01-power-session/new-workspace.sh" ~/skyroute-al06
  cd ~/skyroute-al06
  ```

  The script ends with `FAILED (failures=1)`. That is D2, which no task fixes. To start over, add `--force`, and remove old worktrees first: `git worktree remove --force ~/worktrees/<name>` for each, then `git worktree prune`.
- Worktrees go in `~/worktrees` (the `../worktrees` setting below). If `~/worktrees/t1-bearing` exists from Demo A08 or an earlier try, remove it: `git -C ~/skyroute-a08 worktree remove --force ~/worktrees/t1-bearing`, and the same for `t2-fuel` and `t3-report`.
- Open three terminals in `~/skyroute-al06`: **T1** for OpenCode, **T2** for the dashboard, **T3** for Git and **Check** commands. A second screen helps.
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README). The child sessions start with that default, not with a model you picked with `/models`. Three children run at once, so your rate limit matters more here than in other labs.
- Catch-up path: if the fan-out is still running when the room moves to step 6, keep it running and follow steps 6 to 9 on the instructor's screen. If a child failed, the Solution section says how to finish that task by hand.

## Steps

1. **Commit the task file.** Worktrees start from the committed state, so commit before you fan out. In T3:

   ```bash
   cp "$COURSE/advanced-kit/fanout/TASKS.md" .
   printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "worktree": { "directory": "../worktrees" }\n}\n' > opencode.jsonc
   git add TASKS.md opencode.jsonc && git commit -qm "fan-out tasks"
   git tag fanout-base
   git status --short; git worktree list; sed -n '/^| Task/,/^$/p' TASKS.md
   ```

   The tag `fanout-base` marks the commit every worktree starts from. Step 5 compares each worktree against it, so a child that made two commits is checked in full.

   **Check:** `git status --short` prints nothing. `git worktree list` prints one line, the workspace on `[main]`. The table lists T1 (`skyroute/geo.py`, `tests/test_geo.py`), T2 (`skyroute/fuel.py`, `tests/test_fuel.py` new), and T3 (`skyroute/report.py`, `tests/test_report.py` new). No file appears in two rows; that split is what makes the fan-out safe.

2. **Open the TUI with tabs and start the dashboard.** In T1, start OpenCode with the Mission Control layout (vertical tabs with status icons) for this run only:

   ```bash
   OPENCODE_CLI_CONFIG_CONTENT="$(cat "$COURSE/demos/mission-control/cli.json")" opencode
   ```

   Send one short prompt so the workspace has a `build` session, for example `Read TASKS.md and list the three tasks in one line each. Do not start them.` In T2:

   ```bash
   python3 "$COURSE/demos/mission-control/dashboard.py" --workspace ~/skyroute-al06 --root-agent build --no-tests
   ```

   The dashboard follows the newest root session of the `build` agent in this workspace and redraws every 5 seconds. It reads the same server API the TUI uses, through `opencode api`.

   **Check:** the dashboard header is `Mission Control   <path to your skyroute-al06>   <time>` (a `C:\...` path on Windows), followed by a table with one row, your session with agent `build`. The last line is `No tools/mission_status.py in this workspace, so no board or test summary.` That is expected, because this workspace has no mission board. Before your first prompt the dashboard says `No build session yet in this workspace.`

3. **Fan out.** Open `$COURSE/advanced-kit/fanout/fanout-prompt.md`, copy the prompt block under **Prompt**, and send it in T1 in the same session. It asks for one `execute` call that creates three worktrees, three background `general` subagents launched in one turn, a file check on each result, and a final table, with no merge.

   **Check:** the transcript shows an `execute` call with three `worktree_create` calls and a `worktree_list`, then three `subagent` calls, and the parent says all three are launched. In T3, `git worktree list` prints four lines: the workspace on `[main]` and `t1-bearing`, `t2-fuel`, and `t3-report` under `~/worktrees`, each `(detached HEAD)` at your commit until its child runs `git switch -c fanout/<name>`.

   Run the fan-out in the TUI, as written. If you run the prompt headless instead (`opencode run "<prompt>"`), the command returns as soon as the children are launched. The children keep working in the service, and the parent resumes on each completion notice and posts its final table in the session (read it with `opencode session export <id>`). Wait for all of that before step 5. The best signal is the dashboard: every row `idle` with an outcome. As a fallback, poll from T3 until no session is running, for at most 40 minutes:

   ```bash
   while [ "$(opencode api session.active | tr -d ' \r\n')" != '{"data":{}}' ] && [ "$SECONDS" -lt 2400 ]; do sleep 30; date +%H:%M; done
   ```

   `session.active` lists running sessions for the whole service, so this loop also waits for other sessions you have running, such as a Mission you left open. Do not use `--standalone` for a headless fan-out: background children stop when the run ends.

4. **Watch the children.** In T1, on the parent session, press **Down** on an empty prompt to open the subagent picker. Select a child and press **Enter**. Press **Right** and **Left** to move between children, and **Up** to return to the parent. Use **Ctrl+1** to **Ctrl+0** to jump to a tab, and **Alt+Shift+Down** for the next tab with unread output. Then look at T2, and in T3 run:

   ```bash
   opencode api session.active
   git status --short
   git -C ../worktrees/t1-bearing status --short
   ```

   **Check:** each child's first message is its full brief: its worktree directory, `git switch -c fanout/<name>`, its task section, and the file rules. The dashboard shows the parent row and three indented child rows with agent `general` and state `active`, and the totals line reads `Sessions: 4 (3 subagents, ...)`. `session.active` lists every running session on the service, including your four. The main checkout's `git status --short` prints nothing, while `t1-bearing` shows changes to `skyroute/geo.py` or `tests/test_geo.py` only.

5. **Check each worktree yourself.** Wait until all three children report and the parent posts its table. Do not trust the table. Check the work. In T3:

   ```bash
   for t in t1-bearing t2-fuel t3-report; do
     echo "== $t"
     git -C ../worktrees/$t branch --show-current
     git -C ../worktrees/$t log --oneline fanout-base..HEAD
     git -C ../worktrees/$t diff --stat fanout-base..HEAD
     git -C ../worktrees/$t status --short
     (cd ../worktrees/$t && python3 -m unittest 2>&1 | tail -n 1)
   done
   ```

   **Check:** each block shows branch `fanout/<name>`, at least one new commit that names its requirement IDs, a diff since `fanout-base` that touches only that task's two files, no leftover untracked or modified files from `status --short`, and `FAILED (failures=1)`, the D2 failure every branch keeps. A stray file that was never committed does not show in the diff, which is why the loop also runs `status`. If `branch --show-current` prints nothing, that child committed on a detached HEAD; name it with `git -C ../worktrees/<name> switch -c fanout/<name>`.

6. **Merge into an integration branch.** Merge one branch at a time and run the suite after each merge. In T3:

   ```bash
   git switch -c fanout/integration
   for b in fanout/t1-bearing fanout/t2-fuel fanout/t3-report; do
     git merge --no-edit "$b" && python3 -m unittest 2>&1 | tail -n 1
   done
   python3 -m unittest 2>&1 | grep '^FAIL:'
   ```

   **Check:** three merges with no conflicts, because no two tasks touched the same file. The first is usually a `Fast-forward`, because `fanout/integration` starts at the same commit as the worktrees; the other two print `Merge made by the 'ort' strategy.` Each test line is `FAILED (failures=1)`, and the `grep` prints only `FAIL: test_total_distance_includes_every_leg (tests.test_route.RouteTests.test_total_distance_includes_every_leg)`. Run `python3 -m unittest 2>&1 | grep '^Ran'`: the count is higher than the starter's 17, because each task added tests.

7. **Make the trace commit.** TASKS.md forbids every child to touch `requirements/requirements.json`, so the coordinator adds the new test IDs in one commit after the merge. The parent agent has the children's reports. In T1, on the parent session, send:

   ```text
   You are the coordinator. On the current branch, fanout/integration, add the test IDs
   your children reported to the "tests" lists of SR-GEO-002, SR-FUEL-002, and
   SR-RPT-002 to SR-RPT-006 in requirements/requirements.json. Read the test files on
   this branch to confirm each class and method name. Change no other file. Then
   commit with the message "Trace fan-out tests to requirements".
   ```

   In T3:

   ```bash
   git show --stat --oneline HEAD | tail -n 2
   python3 - <<'EOF'
   import json, subprocess, sys
   reqs = {r["id"]: r.get("tests", []) for r in json.load(open("requirements/requirements.json", encoding="utf-8"))["requirements"]}
   ids = ["SR-GEO-002", "SR-FUEL-002"] + [f"SR-RPT-00{n}" for n in range(2, 7)]
   print({i: len(reqs[i]) for i in ids})
   sys.exit(subprocess.run([sys.executable, "-m", "unittest", "-q", *(t for i in ids for t in reqs[i])]).returncode)
   EOF
   ```

   **Check:** the commit changes only `requirements/requirements.json`. Every ID in the printed dictionary has at least one test, and the listed tests run and end with `OK`: each ID names a test that exists and passes. If you finished a task by hand from the Solution files, the agent reads the names from the test file, so this still works.

8. **Review with `/diff` against `main`.** In T1, type `/diff`. Press **d** and choose the **Base** scope with `main`. Press **b** for the file tree. Open each test file before its code file, press **m** to mark a file reviewed, and **n** for the next file. **v** switches between split and unified views.

   **Check:** the file tree shows exactly seven files: `skyroute/geo.py`, `tests/test_geo.py`, `skyroute/fuel.py`, `tests/test_fuel.py`, `skyroute/report.py`, `tests/test_report.py`, and `requirements/requirements.json`. In T3, `git diff --stat main..fanout/integration` lists the same seven files. If `/diff` does not offer `main`, close and reopen it, and use the `git diff` line meanwhile.

9. **Read the bill, then clean up.** Stop the live dashboard with **Ctrl+C** in T2 and take one snapshot:

   ```bash
   python3 "$COURSE/demos/mission-control/dashboard.py" --workspace ~/skyroute-al06 --root-agent build --no-tests --once
   ```

   Then in T1, send:

   ```text
   Use one execute call to remove the three worktrees t1-bearing, t2-fuel, and
   t3-report with worktree_remove (no force), then call worktree_list and show me
   the result. Do not delete the branches.
   ```

   **Check:** the snapshot lists four sessions with tokens in and out for each, and the totals line `Sessions: 4 (3 subagents, 0 active)`. Compare the children's tokens with the parent's. `worktree_remove` checks the `edit` permission on each worktree directory. The default `build` rules allow edits, so it runs without a prompt; under a team baseline that asks for edits outside the workspace, answer **Allow once** for each. Afterward `git worktree list` in T3 prints one line, and `git branch` still lists the three `fanout/` branches and `fanout/integration`.

## Stretch goals

- **Threat model before T3 (5 min).** Do this before step 3, while the tree is still clean. In a new session in **Plan**, send: `Threat-model skyroute/report.py with STRIDE. For each finding give file:line, category, and the S1 to S5 ID it matches. Change nothing.` **Check:** `git status --short` prints nothing, and each of S1 to S5 is matched to a category, for example S2 shell injection in `archive` as Elevation of privilege and S5 the hard-coded token as Information disclosure. Add any finding that matches no S ID to the T3 brief before you fan out.
- **List the children from a script.** Write `out/children.py` in about 15 lines that prints the newest root session in this workspace and every child of it, with agent, input and output tokens, and title. Use two reads, as the dashboard does: `opencode api GET "/api/session?directory=$PWD&limit=50"` for the root, then `opencode api GET "/api/session?parentID=<root-id>"` for its children. Both return `{"data": [...]}`; tokens are in `tokens.input`, `tokens.output`, and `tokens.cache.read`. Compare your totals with the dashboard.
- **Run a custom command through the API.** Create `.opencode/commands/suite.md` with a body such as ``Run `python3 -m unittest` and summarize every failure in one line each.``. Then create a session and run the command with `session.create` and `session.command`, as in Demo A10. The script is `$COURSE/labs/AL06-fanout/run-command.sh` (the one from Demo A10); call it with `suite` as the first argument. The new session appears on the dashboard if you start it with `--session <id>`, and in the TUI with **Ctrl+X** then **L**. `opencode run "/suite"` would send the literal text instead.
- **Break the ownership rule on purpose.** Add a fourth task to a copy of `TASKS.md` that also edits `skyroute/geo.py`, fan out T1 and the new task, and merge both. Read the conflict, then `git merge --abort`. The fix is in the task split, not in Git.

## Solution

Reference files in the course repository:

- [`advanced-kit/fanout/TASKS.md`](../../advanced-kit/fanout/TASKS.md) defines the three tasks, their file ownership, and their done criteria.
- [`advanced-kit/fanout/fanout-prompt.md`](../../advanced-kit/fanout/fanout-prompt.md) is the prompt, what to look for at each stage, and the cleanup.
- [`demos/mission-control/dashboard.py`](../../demos/mission-control/dashboard.py) is the dashboard. Read `find_root`, `children_of`, `tokens`, and `render` to see the API calls.
- [`labs/solutions/skyroute/`](../solutions/skyroute/) holds reference fixes and tests for each task: `skyroute/geo.py` and `tests/test_geo.py` (T1), `skyroute/fuel.py` and `tests/test_fuel.py` (T2), `skyroute/report.py` and `tests/test_report.py` (T3). If one child failed, finish that task by hand in its worktree: copy the two solution files in, run its test command, commit on its `fanout/` branch, and continue from step 6. One caveat for T3: the reference `tests/test_report.py` includes `test_report_lists_every_leg_and_totals`, which needs the D2 fix, so with it the suite shows `FAILED (failures=2)`. Delete that one test method in the worktree before you commit.

A good result: three worktrees existed at the same time, three children ran in the background while you moved between them, the dashboard showed them live, each branch changed only its own two files, the merged `fanout/integration` branch fails only the known D2 test, one coordinator commit traced the new tests to their requirements, and `/diff` against `main` showed seven files.
