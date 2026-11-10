# Lab AL01: Power Session and Review with /diff

**Time:** 25 min  **Modules:** A02  **You will:** fix SkyRoute defect D2 using only power moves, review the turn in the `/diff` viewer, prove `/undo` and `/redo` with Git, and save your tab and diff preferences in `cli.json`.

**Where:** `~/skyroute-adv`

Repeats Demo A02 (Power session). Same as the demo: the D2 fix, the prompts, and the order of moves (shell mode, Plan with `@` ranges, steer, queue, `/btw`, Build, `/diff` Last turn, `/undo` and `/redo`, a second tab). New for you: your own Git workspace, where `/diff` and `git diff` show only your work; a check from the shell after every move, including the session API; and your own `cli.json` defaults, which Lab AL03 uses to watch subagents.

## Before you start

- This lab needs no earlier lab. It creates the workspace that Labs AL02 and AL03 continue in.
- Run the preflight once, from the course repository root: `bash labs/advanced-preflight.sh`. Fix every `FAIL` line before step 1. If you cannot fix the `python3` line (for example your Python folder is locked down), you may continue: type `py -3` wherever a step runs Python in the TUI, and keep the "On Windows run Python as py -3" line in prompts. On Windows it catches the Microsoft Store `python3` stub (exit code 49, `Python was not found`), which breaks `!python3` in the TUI and every agent that runs tests; see the Windows note in [`labs/README.md`](../README.md#before-any-lab).
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README). If the footer shows another model, fix the config and check with `opencode debug config`; `/models` switches only the current session. New sessions and `opencode run` use the configured `"model"`; without one, they use the newest model your provider offers, which is not a bug but a missing setting.
- Commands use `python3`. On Windows, run Python as `py -3`; see the Windows note in [`labs/README.md`](../README.md#before-any-lab). Run every command from Git Bash, not PowerShell: PowerShell strips the quotes inside the commands and truncates commit messages.
- From the root of your course repository clone, remember its path and create the workspace:

  ```bash
  export COURSE="$(pwd -W 2>/dev/null || pwd)"
  bash labs/AL01-power-session/new-workspace.sh
  ```

  It prints `new-workspace.sh: created /Users/<you>/skyroute-adv from skyroute-starter-v2.` and then `FAILED (failures=1)`. The one failing test is defect D2. You may also see a note that it set a Git `user.name` for this workspace only, and on Windows an `LF will be replaced by CRLF` warning; both are harmless. If the workspace exists from an earlier try, add `--force` to recreate it.
- Open two terminals at `~/skyroute-adv`. Terminal 1 runs OpenCode (`opencode`). Terminal 2 runs every **Check** command. In terminal 2, also set `COURSE` to the course repository path.
- Keys used in this lab: **Shift+Tab** cycles primary agents (Build and Plan). **Ctrl+X** is the leader key: press it, release, then press the next key.

## Steps

1. **Run the failing test in shell mode.** In terminal 1, start `opencode`. On an empty prompt, type `!`, then type the command and press **Enter**:

   ```text
   !python3 -m unittest tests.test_route
   ```

   The output stays in the session, so the model sees it without a paste. On Windows, if the preflight still reports the `python3` stub, type `!py -3 -m unittest tests.test_route` instead.

   **Check:** the session shows `FAILED (failures=1)` and names `test_total_distance_includes_every_leg`. In terminal 2, `python3 -m unittest tests.test_route 2>&1 | tail -1` prints `FAILED (failures=1)`.

2. **Plan with exact ranges, then steer and queue.** Press **Shift+Tab** until the footer shows **Plan**. Send prompt A. Type the `@` paths in full. If the file picker opens, select the file and type the `#range` right after it.

   ```text
   Plan the fix for the failing test. The code is @skyroute/route.py#53-58 and the
   requirement is @requirements/requirements.json#69-78. Name the exact line and the
   change. Do not edit.
   ```

   A fast model can finish Plan in a few seconds, before you can type. Copy prompt B before you send prompt A, then paste it and press **Enter** as soon as prompt A is sent. Enter steers: the message joins the running turn.

   ```text
   Also tell me whether ete_hours depends on total_distance_nm.
   ```

   Still while it works (or right after), type prompt C and press **Ctrl+X** then **Enter**. This queues it: it waits until the turn ends and then runs as its own message.

   ```text
   Summarize the plan in at most three numbered steps.
   ```

   **Check:** the plan names the loop bound `range(len(self.fixes) - 2)` in `total_distance_nm` as the reason the last leg is skipped, and the same answer covers `ete_hours` (your steer). If Plan finished before prompt B arrived, prompt B runs as its own message instead; that is fine, note the difference and go on. The numbered summary arrives after that turn ends. In terminal 2, `git status --short -- skyroute tests` prints nothing: Plan changed no project file.

3. **Ask a side question with /btw.** Wait until the queued summary has finished. Type this and press **Enter**:

   ```text
   /btw Read requirements/requirements.json. Which requirement ID covers total route distance?
   ```

   The answer opens in a dialog. Press **C** to copy it or **Esc** to close it. The question and answer are not added to the conversation. Name the file in the question: `/btw` does not reliably get the files you attached with `@` in step 2, and without the file it can answer that it does not know.

   **Check:** the dialog answers `SR-RTE-002`, and the transcript shows no `/btw` message. Confirm that the model's context does not contain it. In terminal 2:

   ```bash
   SID=$(opencode session list --format json -n 1 | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
   opencode api session.context --param sessionID=$SID > .git/al01-context.json
   grep -c "Which requirement ID" .git/al01-context.json
   ```

   It prints `0`. The output goes to a file first because OpenCode 2.1 can cut `opencode api` output written to a pipe at 256 KiB, and a session's context can pass that size. The file is in `.git/` so it never shows in `git status`. Keep this terminal open: later checks reuse `$SID`.

4. **Build the fix.** Before you send, make sure nothing is queued (**Ctrl+X** then **Q** shows the queue) and the session is idle. Prompt E must be the last message in the session for steps 5 and 6 to work. Press **Shift+Tab** until the footer shows **Build**, then send prompt E:

   ```text
   Implement the plan. Edit only skyroute/route.py. Then run
   python3 -m unittest tests.test_route and report the summary line.
   On Windows run Python as py -3.
   ```

   On 2.1.x, Build edits files and runs shell commands without asking. If your workspace has a team baseline that asks, choose **Allow once** for the test command.

   **Check:** in terminal 2, `python3 -m unittest 2>&1 | tail -1` prints `OK`, and `git diff --stat` ends with `1 file changed` and lists only `skyroute/route.py`.

5. **Review the turn in /diff.** Type `/diff` and press **Enter**. Press **d** and choose **Last turn**: the files the session changed in its latest turn. Then work through the viewer keys:

   | Key | Does |
   |-----|------|
   | **b** | Show or hide the file tree |
   | **v** | Switch between split and unified view |
   | **]** and **[** | Next or previous hunk |
   | **n** and **p** | Next or previous file |
   | **m** | Mark the file reviewed (its patch collapses) |
   | **q** or **Esc** | Close the viewer |

   Press **d** again and look at **All** (branch and local changes) and **Uncommitted** (staged, unstaged, and untracked). Both include your change, because you have not committed yet. Choose **Last turn** again, mark `skyroute/route.py` reviewed with **m**, and close with **q**.

   **Check:** Last turn lists only `skyroute/route.py`, and its hunk changes the loop so every leg is counted. The session API reports the same file set for the latest turn. In terminal 2:

   ```bash
   opencode api session.diff --param sessionID=$SID | python3 -c "import json,sys; print([f['file'] for f in json.load(sys.stdin)['data']])"
   ```

   It prints `['skyroute/route.py']`.

   If **Last turn** says `No changes to show` and the API prints `[]`, a message ran after prompt E (a queued prompt, or a follow-up you sent), and that latest turn changed no file. Review with **Uncommitted** instead, which shows the same change, and in step 6 press undo until prompt E is back in the composer.

6. **Undo, then redo.** Press **Ctrl+X** then **U** (or type `/undo`). Each press reverts the latest message and the file changes it made, and puts that message back in the composer. If prompt E is not in the composer after the first press, a later message was reverted first: press **Ctrl+X** then **U** again until prompt E is in the composer. Do not send it.

   **Check:** in terminal 2, `git diff --stat` prints nothing and `python3 -m unittest 2>&1 | tail -1` prints `FAILED (failures=1)`.

   Now press **Ctrl+X** then **R** (or type `/redo`) once for each undo you made. Clear the composer if prompt E is still in it.

   **Check:** `git diff --stat` again lists `skyroute/route.py` with `1 file changed`, and `python3 -m unittest 2>&1 | tail -1` prints `OK`. Sending a new prompt instead of `/redo` would have accepted the revert.

7. **Open a second tab.** Press **Ctrl+X** then **N** for a new session. It opens as a new tab. Send prompt F:

   ```text
   How does @skyroute/fuel.py compute contingency fuel? Cite path:line. Do not edit.
   ```

   Press **Ctrl+1** to jump to the first tab and **Ctrl+2** to come back. If your terminal or operating system takes **Ctrl+number**, use **Ctrl+X** then **1** and **Ctrl+X** then **2**. Press **Ctrl+O** to see recent sessions, then **Esc**.

   **Check:** two tabs are visible and switch with the keys. The answer cites `skyroute/fuel.py` and says contingency is computed on trip plus reserve (that is defect D3, fixed in Lab AL03). In terminal 2, `opencode session list -n 2` lists two sessions, and `git diff --stat` still shows only `skyroute/route.py`.

8. **Save your tab and diff preferences.** CLI settings live in one global file, `~/.config/opencode/cli.json`. There is no project-level CLI settings file. Back it up if it exists, then write the settings. If you already have a `cli.json` with other settings, merge the `tabs` and `diffs` blocks into it by hand instead of overwriting it.

   ```bash
   mkdir -p ~/.config/opencode
   [ -f ~/.config/opencode/cli.json ] && cp ~/.config/opencode/cli.json ~/.config/opencode/cli.json.bak
   cat > ~/.config/opencode/cli.json <<'EOF'
   {
     "$schema": "https://opencode.ai/v2/cli.json",
     "tabs": { "mode": "on", "layout": "vertical", "indicators": "status" },
     "diffs": { "source": "turn", "view": "split", "tree": true }
   }
   EOF
   ```

   Valid edits reload while the TUI is running. `diffs.source: "turn"` opens `/diff` on Last turn, so you no longer press **d** after every turn. The vertical tab sidebar with status icons is the layout the instructor uses for Mission Control, and you use it in Lab AL03 to watch subagents.

   **Check:** in terminal 2:

   ```bash
   python3 -c "import json,os; c=json.load(open(os.path.expanduser('~/.config/opencode/cli.json'))); print(c['tabs']['layout'], c['tabs']['indicators'], c['diffs']['source'], c['diffs']['view'])"
   ```

   It prints `vertical status turn split`. In the TUI, the tabs move to a vertical sidebar. Type `/diff`: it opens directly on Last turn in split view. Close it with **q**.

9. **Commit the fix.** Labs AL02 and AL03 continue in this workspace and expect a green suite. In terminal 2:

   ```bash
   git commit -am "Fix D2: total distance includes every leg"
   ```

   **Check:** `git log --oneline` shows two commits, your fix and `SkyRoute starter`, `python3 -m unittest 2>&1 | tail -1` prints `OK`, and `git status --short` prints nothing. If it lists a leftover file (for example a test from a stretch goal), remove it now, or Lab AL02's checks show it.

## Stretch goals

- **Base scope.** Make a second change in Build (for example "add a docstring to `Route.legs`"), then open `/diff`, press **d**, and pick **Base**, then `main`. Compare it with **Last turn** and **Committed**. Undo the change with **Ctrl+X** then **U**.
- **Timeline.** Type `/timeline` to see the session's messages. Pick prompt C and look at what you can do from a single message, such as forking from it. Lab AL02 uses forks.
- **Inline settings.** Try settings without touching the file: quit, then start `OPENCODE_CLI_CONFIG_CONTENT='{"tabs":{"layout":"horizontal"}}' opencode`. Inline settings merge over `cli.json` while the variable is set.
- **Reproduce first (5 min).** The kit's ops log ([`advanced-kit/logs/ops.log`](../../advanced-kit/logs/ops.log)) shows `alt=FL085` crashing with `leading zeros`, although FL085 is a valid flight level. In Build, send: `Write a failing unittest proving parse_altitude("FL085") returns 8500. Run it. Do not fix yet.` **Check:** the run shows the new test as an error with `SyntaxError: leading zeros in decimal integer literals`, and `git diff` touches only `tests/`. Keep the red test out of your commit: `git stash -u`, or `git checkout -- tests/ && git clean -fd tests/`. The fix belongs to Lab AL06 T3.
- **Queue manager.** Queue two prompts while Build works, then press **Ctrl+X** then **Q** to see and manage the queue before they run.

## Solution

- The D2 fix is in [`labs/solutions/skyroute/skyroute/route.py`](../solutions/skyroute/skyroute/route.py): `total_distance_nm` sums `leg.distance_nm` over `self.legs()`. A one-line change of the loop bound to `range(len(self.fixes) - 1)` is also correct. Compare yours from the workspace: `diff --strip-trailing-cr skyroute/route.py "$COURSE/labs/solutions/skyroute/skyroute/route.py"`.
- The instructor ran the same prompts in Demo A02.
- The instructor's TUI layout for Mission Control is [`demos/mission-control/cli.json`](../../demos/mission-control/cli.json). It uses the same `tabs` settings with `diffs.source: "branch"`.
- The workspace script is [`new-workspace.sh`](new-workspace.sh). Run it with `--help` for the options.

A good result: `python3 -m unittest` prints `OK`, `git log --oneline` shows the fix on top of `SkyRoute starter`, `/diff` opens on Last turn in split view, and the tabs show in a vertical sidebar.

Catch-up for the next lab, if you could not finish: from the course repository root run `bash labs/AL01-power-session/new-workspace.sh --force`, then in `~/skyroute-adv` run `cp "$COURSE/labs/solutions/skyroute/skyroute/route.py" skyroute/route.py && git commit -am "Fix D2: total distance includes every leg"`.
