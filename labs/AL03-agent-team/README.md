# Lab AL03: Build an Agent Team and Run a Mini Mission

**Time:** 50 min  **Modules:** A05, A06, A01  **You will:** install a commander and a read-only reviewer, write one engineer agent yourself and derive the second, prove every least-privilege rule, add a `/mini-status` command and a `mini-protocol` skill, then run a two-workstream mission in parallel and review the result.

**Where:** `~/skyroute-adv`

Repeats Demo A05 (guardrails), Demo A06 (Inside Mission Control), and Demo A01 (Launch Mission Control). Same as the demos: the shape of the instructor's Mission Control kit (a primary `commander` that never writes workstream code, engineer subagents launched in the background in one turn, a read-only reviewer, a board only the commander edits, a status command that injects shell output, and a protocol skill), the two permission traps from A05 (`git diff --output` writes a file, and a subagent can hand work to `general`), and the same subagent picker and dashboard to watch it. New for you: you read every rule, write one engineer's rules yourself, prove each rule with a checker before anything runs, give each engineer its own agent file so OpenCode enforces file ownership (the kit's single `engineer` relies on the brief for that, a tradeoff Demo A06 names), and run a mission small enough to finish in the lab.

## Before you start

- This lab continues in the workspace from Labs AL01 and AL02. It needs a green suite: run `python3 -m unittest 2>&1 | tail -1` in `~/skyroute-adv` and expect `OK`. To catch up, run this from the course repository root:

  ```bash
  export COURSE="$(pwd -W 2>/dev/null || pwd)"
  bash labs/AL01-power-session/new-workspace.sh --force
  cd ~/skyroute-adv
  cp "$COURSE/labs/solutions/skyroute/skyroute/route.py" skyroute/route.py
  git commit -qam "Fix D2: total distance includes every leg"
  ```

- `COURSE` must hold the absolute path of your course repository clone in every terminal.
- The engineers are child sessions of the commander session. You reach them with **Down** (subagent picker), **Left**, **Right**, and **Up**. The tab layout from Lab AL01 step 8 (`tabs.layout: "vertical"`, `tabs.indicators: "status"`) shows the sessions you have open as tabs with status icons.
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README). `/models` switches only the current session. The agents in this lab have no `model` field, so they use the session's model, and a new session starts with the configured default.
- Commands use `python3`. On Windows, run Python as `py -3`; see the Windows note in [`labs/README.md`](../README.md#before-any-lab). Use Git Bash. The agent rules in this lab also allow `py -3 -m unittest *`, so the agents can run the tests on Windows. Run `bash "$COURSE/labs/advanced-preflight.sh"` first: if `python3` is still the Microsoft Store stub, the agents' `python3 -m unittest` and the `/mini-status` test run fail with `Python was not found` (exit code 49). Fix it with the preflight's `--fix-python3`, or tell the agents to use `py -3` (see step 6).
- Scripts in this lab run `opencode` from Python. They find it with `shutil.which`, so an npm install (`opencode.cmd` on Windows) works too.
- Terminal 1 runs OpenCode. Terminal 2 runs every **Check** command. Both are at `~/skyroute-adv`.
- The mission is two independent defects from earlier labs:

  | ID | Workstream | Owns | Requirement |
  |----|------------|------|-------------|
  | WA | Fuel: contingency on trip fuel only (D3) | `skyroute/fuel.py`, `tests/test_fuel.py` | SR-FUEL-002 |
  | WB | Bearing: normalize to [0, 360) (D1) | `skyroute/geo.py`, `tests/test_geo.py` | SR-GEO-002 |

## Steps

1. **Install the brief and the board.** The brief is the mission order; the board is the shared state. Copy both from the lab folder and read the brief:

   ```bash
   mkdir -p mission
   cp "$COURSE/labs/AL03-agent-team/team/mission/MINI-BRIEF.md" "$COURSE/labs/AL03-agent-team/team/mission/BOARD.md" mission/
   cat mission/MINI-BRIEF.md
   ```

   Compare it with the instructor's [`BRIEF.md`](../../demos/mission-control/kit/mission/BRIEF.md): the same parts (requirement, owned files, tests to write first, done criteria) for two workstreams instead of six.

   **Check:** `ls mission` prints `BOARD.md` and `MINI-BRIEF.md`, and `grep -c planned mission/BOARD.md` prints `3` (two rows plus the legend line).

2. **Install and read the commander.** Copy it from the lab folder. It is a primary agent: you select it with **Shift+Tab**.

   ```bash
   mkdir -p .opencode/agents
   cp "$COURSE/labs/AL03-agent-team/team/.opencode/agents/commander.md" .opencode/agents/
   ```

   Open it in your editor. This is its content:

   ```markdown
   ---
   description: Mini mission commander. Launches one engineer subagent per workstream in the background, launches mini-reviewer for reviews, keeps mission/BOARD.md current, verifies and commits finished work. Never writes code or tests.
   mode: primary
   permissions:
     - action: subagent
       resource: "*"
       effect: deny
     - action: subagent
       resource: eng-fuel
       effect: allow
     - action: subagent
       resource: eng-geo
       effect: allow
     - action: subagent
       resource: mini-reviewer
       effect: allow
     - action: edit
       resource: "*"
       effect: deny
     - action: edit
       resource: mission/BOARD.md
       effect: allow
     - action: shell
       resource: "*"
       effect: ask
     - action: shell
       resource: "python3 -m unittest *"
       effect: allow
     - action: shell
       resource: "py -3 -m unittest *"
       effect: allow
     - action: shell
       resource: "date +%H:%M"
       effect: allow
     - action: shell
       resource: "git status *"
       effect: allow
     - action: shell
       resource: "git diff *"
       effect: allow
     - action: shell
       resource: "git log *"
       effect: allow
     - action: shell
       resource: "git add *"
       effect: allow
     - action: shell
       resource: "git commit *"
       effect: allow
     - action: shell
       resource: "git *--output*"
       effect: deny
     - action: shell
       resource: "git push *"
       effect: deny
     - action: webfetch
       resource: "*"
       effect: deny
     - action: websearch
       resource: "*"
       effect: deny
   ---

   You are the commander of a two-workstream mini mission on SkyRoute. The mission order is `mission/MINI-BRIEF.md`. Load the `mini-protocol` skill before you launch anything and follow it exactly.

   1. Read the brief and `mission/BOARD.md`.
   2. Launch both workstreams in the same turn: `eng-fuel` for WA and `eng-geo` for WB, each with `background: true`. Give each engineer its full section of the brief, its owned files, and the report format. Set the description to `WA Fuel` or `WB Bearing`.
   3. Set each row to `in progress` when you launch it. Your turn may end while the engineers work.
   4. On each report: set the row to `review` and run that workstream's Done command from the brief: its own test module plus the baseline modules no workstream owns. Then `git status --short -- <its owned files>` lists its changes; read them with `git diff -- <its owned files>`. The other workstream may still be working test first in the same checkout, so its files can be uncommitted or red. That is not a failure of this workstream.
   5. If the Done command ends in `OK`, commit only that workstream's files with `git add <files>` and `git commit -m "WA: <summary>"` (or `WB`), then set the row to `done` with the test count. Otherwise set it to `blocked` with the reason. Never block a workstream because of the other workstream's files.
   6. When no row is `in progress` or `review`, run the full suite, `python3 -m unittest`. If it fails, set the workstream whose commit broke it to `blocked`.

   Run shell commands from the workspace root without `cd`, pipes, or redirection: each part of a compound command is checked, and anything outside your allowlist asks. You never edit code or tests. You never push.
   ```

   Read the rules from the top. The last matching rule wins, so each block starts with a broad rule and adds exceptions. Read steps 4 to 6 of the body too: both engineers work test first in one checkout, so each workstream is verified on its own module and files, and the full suite runs only when nothing is in progress. Delegation is an allowlist: every subagent is denied, then three are allowed. Edits are denied except the board. Shell asks for anything unlisted. `date +%H:%M` is an exact command, not a pattern: the board needs the time, and nothing else about `date` is needed. `git diff *` would allow `git diff --output=FILE`, which writes a file, so a later rule denies `git *--output*`.

   **Check:** in terminal 2, OpenCode lists the new agent:

   ```bash
   opencode debug agents | python3 -c "import json,sys; d=json.load(sys.stdin); d=d['data'] if isinstance(d,dict) else d; print([(a['id'], a['mode']) for a in d if a['id'] in ('commander','eng-fuel','eng-geo','mini-reviewer')])"
   ```

   It prints `[('commander', 'primary')]`. If it prints `[]`, run it again: the first call for a directory can return before the workspace is loaded.

3. **Write the WA engineer yourself.** This is the agent you type by hand: its rules are what keep two parallel engineers out of each other's files. Create `.opencode/agents/eng-fuel.md`:

   ```markdown
   ---
   description: Mini mission engineer for workstream WA. Fixes one SkyRoute defect test first. Edits only skyroute/fuel.py and tests/test_fuel.py. Reports with the REPORT block.
   mode: subagent
   permissions:
     - action: subagent
       resource: "*"
       effect: deny
     - action: edit
       resource: "*"
       effect: deny
     - action: edit
       resource: skyroute/fuel.py
       effect: allow
     - action: edit
       resource: tests/test_fuel.py
       effect: allow
     - action: shell
       resource: "*"
       effect: deny
     - action: shell
       resource: "python3 -m unittest *"
       effect: allow
     - action: shell
       resource: "py -3 -m unittest *"
       effect: allow
     - action: shell
       resource: "git status *"
       effect: allow
     - action: shell
       resource: "git diff *"
       effect: allow
     - action: shell
       resource: "git *--output*"
       effect: deny
     - action: webfetch
       resource: "*"
       effect: deny
     - action: websearch
       resource: "*"
       effect: deny
   ---

   You are a workstream engineer on the SkyRoute mini mission. The commander gives you one workstream section. Load the `mini-protocol` skill first.

   1. Write the tests named in your section first. Run `python3 -m unittest <your test module>` and see them fail.
   2. Make the smallest code change that makes them pass. Then run the Done command from your section: your test module plus the baseline modules. Do not gate on the whole suite: the other engineer writes its tests first in the same checkout, so the whole suite can be red because of files that are not yours.
   3. Edit only the files you own. Never commit. If you need a change elsewhere, list it under Open issues.
   4. Run shell commands exactly as allowed, from the workspace root, with no `cd`, pipes, or redirection: each part of a compound command is checked, and `cd`, `tail`, or `grep` is denied.

   Finish with the REPORT block from the `mini-protocol` skill and nothing after it.
   ```

   Make the WB engineer from it. Only the workstream ID and the two owned files change:

   ```bash
   sed -e 's/workstream WA/workstream WB/' -e 's/fuel\.py/geo.py/g' -e 's/test_fuel/test_geo/g' \
     .opencode/agents/eng-fuel.md > .opencode/agents/eng-geo.md
   diff --strip-trailing-cr .opencode/agents/eng-fuel.md .opencode/agents/eng-geo.md
   ```

   `--strip-trailing-cr` ignores Windows line ends (CRLF), which a Windows editor may have used for your file.

   An engineer may not launch subagents, may not commit, and may edit only its two files. Shell is denied except tests and Git reads. These are the rules that let two engineers run at once without touching each other's files or the Git index.

   **Check:** the `diff` shows exactly three changed lines: the `description`, `skyroute/geo.py`, and `tests/test_geo.py`. The step 2 command now prints `[('commander', 'primary'), ('eng-fuel', 'subagent'), ('eng-geo', 'subagent')]`.

4. **Install the reviewer, then prove every rule.** Copy it from the lab folder and read it:

   ```bash
   cp "$COURSE/labs/AL03-agent-team/team/.opencode/agents/mini-reviewer.md" .opencode/agents/
   ```

   This is its content:

   ````markdown
   ---
   description: Read-only mini mission reviewer. Use after a workstream is done to check its diff against its section of mission/MINI-BRIEF.md and its tests. Reports findings by severity with file:line evidence. Never edits files.
   mode: subagent
   permissions:
     - action: edit
       resource: "*"
       effect: deny
     - action: subagent
       resource: "*"
       effect: deny
     - action: shell
       resource: "*"
       effect: deny
     - action: shell
       resource: "python3 -m unittest *"
       effect: allow
     - action: shell
       resource: "py -3 -m unittest *"
       effect: allow
     - action: shell
       resource: "git status *"
       effect: allow
     - action: shell
       resource: "git diff *"
       effect: allow
     - action: shell
       resource: "git log *"
       effect: allow
     - action: shell
       resource: "git show *"
       effect: allow
     - action: shell
       resource: "git *--output*"
       effect: deny
     - action: webfetch
       resource: "*"
       effect: deny
     - action: websearch
       resource: "*"
       effect: deny
   ---

   You review finished mini mission workstreams. You read and run tests; you never change files.

   1. Read the workstream section in `mission/MINI-BRIEF.md`.
   2. Read its commits with `git log --stat` and `git show`, and the files it owns.
   3. Run `python3 -m unittest <its test module> -v` and `python3 -m unittest` from the workspace root, without `cd`, pipes, or redirection. Quote the summary lines.
   4. Check that each named test exists and would fail if the requirement were broken, and that no file outside the workstream changed.

   Report:

   ```
   REVIEW W<x>
   Verdict: pass | changes needed
   Findings:
   - [high|medium|low] path:line - problem - suggested fix
   Tests: <summary lines>
   ```

   Every finding cites a `path:line` you read. No evidence, no finding.
   ````

   The two traps from Demo A05 are both here. Without `git *--output*` deny, the allowed `git diff *` writes files. Without `subagent` deny, a read-only agent can launch `general`, which has a full shell and can edit.

   Keep the frontmatter entirely V2. One V1 field such as `temperature`, `maxSteps`, or `prompt` makes OpenCode 2.1.x read the whole entry as V1, and the `permissions` list stops applying.

   Now prove the team's rules without calling a model. The lab's checker reads the effective rules from `opencode debug agents` (built-in defaults first, then your agent's rules, then the built-in `browser` deny) and evaluates each case the way OpenCode does: last match wins, no match asks.

   ```bash
   opencode reload
   python3 "$COURSE/labs/AL03-agent-team/check_team.py"
   ```

   `opencode reload` makes the service read the agent files you just wrote; without it, the checker can see older rules.

   **Check:** every line starts with `PASS` and the last line is `37 of 37 checks pass`. Then see a trap fail: delete the three lines of the `git *--output*` rule from `mini-reviewer.md`, run `opencode reload` and the checker again, and read the `FAIL  mini-reviewer  shell 'git diff --output=leak.patch' -> allow (want deny)` line. Put the rule back, run `opencode reload`, and confirm `37 of 37` again.

   To see OpenCode enforce the rule with a real model, run the reviewer directly:

   ```bash
   opencode run --agent mini-reviewer "Run this exact shell command once and report the result verbatim: git diff --output=leak.patch"
   ls leak.patch
   ```

   The reviewer reports `Permission denied: shell`, and `ls` prints `No such file or directory`.

5. **Add the status command and the protocol skill.** Create `.opencode/commands/mini-status.md`. Each `` !`cmd` `` line runs in the shell before the prompt is sent, and its output replaces the line. It runs outside the permission flow, so it holds only fixed commands, never arguments.

   ```markdown
   ---
   description: Mini mission status from the board, Git, and a test run (no edits)
   ---

   This is the current state of the mini mission, collected by shell before you were called.

   Board:

   !`cat mission/BOARD.md`

   Commits since the starter:

   !`git log --oneline -5`

   Uncommitted files:

   !`git status --short`

   Test run:

   !`python3 -m unittest`

   Write a 3-line status. Line 1: workstreams done out of 2 and the test summary. Line 2: what is running or waiting for review. Line 3: anything blocked or failing, or "Nothing blocked." Use only the facts above. Do not run commands and do not edit files.
   ```

   Copy the protocol skill from the lab folder and read it. It is the scaled-down twin of the kit's `mission-protocol`: ownership, launch rules, the board state machine (`planned`, `in progress`, `review`, `done`, `blocked`), and the `REPORT` block every engineer ends with.

   ```bash
   mkdir -p .opencode/skills/mini-protocol
   cp "$COURSE/labs/AL03-agent-team/team/.opencode/skills/mini-protocol/SKILL.md" .opencode/skills/mini-protocol/
   cat .opencode/skills/mini-protocol/SKILL.md
   ```

   Commit the team and mark the starting point, so the mission's work is easy to see in `/diff` later:

   ```bash
   git add .opencode mission
   git commit -m "Add mini mission team"
   git branch mission-start
   ```

   **Check:** in terminal 1, start `opencode` (or press **Ctrl+X** then **N** for a new session), type `/mini-status` in the TUI, and press **Enter**. Do not pass it on the Git Bash command line (`opencode run "/mini-status"`): Git Bash rewrites an argument that starts with `/` into `C:/Program Files/Git/mini-status`, and `opencode run` sends command names as plain text anyway. The prompt contains the board with both rows `planned`, your commit at the top of the log, and `OK` from the test run, followed by a 3-line status. On Windows, `` !`...` `` lines run in Windows PowerShell, not Git Bash, so they see neither your Bash functions nor commands such as `tail`. That is why the test line has no pipe. If the preflight still reports the `python3` stub, the test run shows `Python was not found`: change the line to `` !`py -3 -m unittest` `` in `.opencode/commands/mini-status.md`. In terminal 2:

   ```bash
   opencode api command.list --param "location[directory]=$(pwd -W 2>/dev/null || pwd -P)" | python3 -c "import json,sys; print([c['name'] for c in json.load(sys.stdin)['data']])"
   opencode api skill.list --param "location[directory]=$(pwd -W 2>/dev/null || pwd -P)" > .git/al03-skills.json
   python3 -c "import json,sys; print('mini-protocol' in [s['id'] for s in json.load(open(sys.argv[1], encoding='utf-8'))['data']])" .git/al03-skills.json
   ```

   The first prints the built-in commands plus yours, for example `['init', 'review', 'goal', 'mini-status']` (the built-ins vary by version; check that `mini-status` is in it). The second prints `True`. Right after `opencode reload`, the first call can return the old lists; if `mini-status` is missing or the second prints `False`, run both again. The skill list goes through a file because OpenCode 2.1 can cut `opencode api` output written to a pipe at 256 KiB, and a machine with many global skills passes that size.

6. **Launch the mission.** In terminal 1, press **Shift+Tab** until the footer shows **commander**. Send the launch prompt:

   ```text
   Run the mini mission in mission/MINI-BRIEF.md. Load the mini-protocol skill, then
   launch eng-fuel for WA and eng-geo for WB in this turn, both with background: true.
   Update mission/BOARD.md, then verify, commit, and update the board as each report
   arrives.
   ```

   On Windows, unless the preflight shows a working `python3`, add one line to the prompt: `On Windows run Python as py -3: tell each engineer to run py -3 -m unittest instead of python3.` The commander passes it on in each brief.

   The commander loads the skill, reads the brief and the board, runs `date +%H:%M` without asking, sets both rows to `in progress`, and makes two `subagent` calls in one step. On an empty prompt, press **Down**: the subagent picker lists `WA Fuel` and `WB Bearing`. Press **Esc** to close it. If a permission prompt appears, read it before you answer: a command outside the commander's allowlist is the `ask` rule working. On Windows the commander may first try PowerShell's `Get-Date -Format HH:mm`, which asks; **Reject** it and it falls back to the allowed `date +%H:%M`. Choose **Allow once** only for a command you would run yourself, and **Reject** otherwise. With a fast model, the whole mission (both engineers, verification, and commits) can finish within a minute, before you open the picker; then read the child sessions afterwards instead of watching them live.

   **Check:** in terminal 2, `tail -2 mission/BOARD.md` shows both rows `in progress` with sessions `WA Fuel` and `WB Bearing`. The service lists the two child sessions with their agents:

   ```bash
   opencode api session.list > .git/al03-sessions.json
   python3 -c "import json,os,sys; here=os.path.normcase(os.path.realpath('.')); [print(s['title'], s['agent']) for s in json.load(open(sys.argv[1], encoding='utf-8'))['data'] if s.get('parentID') and os.path.normcase(s['location']['directory'])==here]" .git/al03-sessions.json
   ```

   It prints `WA Fuel eng-fuel` and `WB Bearing eng-geo` (in either order).

7. **Watch the engineers.** While they work, use the same views as the instructor at a check-in:

   | Key or command | What it does |
   |----------------|--------------|
   | **Down** on an empty prompt | Open the subagent picker in the commander session |
   | **Left** and **Right** | Previous or next child session |
   | **Up** | Back to the parent (commander) session |
   | Tab sidebar, **Ctrl+1** to **Ctrl+0**, **Alt+Shift+Down** | Sessions you have open, with status icons: jump to a tab, or to the next unread one. A child session is a tab only if you opened it, or if your TUI opens it. |

   Open the `WA Fuel` child and read the prompt the commander wrote for it: the brief section, the owned files, and the report format. Then run the instructor's dashboard against your workspace in terminal 2:

   ```bash
   python3 "$COURSE/demos/mission-control/dashboard.py" --workspace "$PWD" --once
   ```

   **Check:** the dashboard lists your commander session (agent `commander`, with the title the TUI gave it), and below it `WA Fuel eng-fuel` and `WB Bearing eng-geo`, each `active` or `idle`, with tokens. It ends with `No tools/mission_status.py in this workspace, so no board or test summary.`: your `/mini-status` plays that role. `git status --short` shows changes only in `mission/BOARD.md` and the two workstreams' files. If `/mini-status` shows a red test run now, look at which module fails: while an engineer is between its red test and its fix, that is expected.

8. **Let the commander verify and commit.** Each engineer ends with a `REPORT` block. The commander wakes up on each completion, sets the row to `review`, runs the tests, commits that workstream's files, and sets the row to `done`. With background engineers, the commander's turn can end before the reports arrive; it continues on its own when they do. When both rows are `done`, run `/mini-status` again in a separate session (**Ctrl+X** then **N**).

   **Check:** in terminal 2:

   ```bash
   git log --oneline mission-start..HEAD
   python3 -m unittest 2>&1 | tail -1
   for t in test_fuel.py test_geo.py; do python3 -m unittest discover -s "$COURSE/labs/solutions/skyroute/tests" -t "$COURSE/labs/solutions/skyroute/tests" -p $t 2>&1 | tail -1; done
   git status --short
   ```

   The log shows two commits, one starting `WA:` and one starting `WB:`. The suite prints `OK`. The two reference test modules from the course solution, run against your code, print `OK` twice. `git status --short` shows only ` M mission/BOARD.md`: the commander edits the board but commits only workstream files. Both board rows read `done`.

9. **Review with /diff and the reviewer.** In the commander session type `/diff`, press **d**, choose **Base**, and pick `mission-start`. Press **d** again and choose **Committed**: only the commits since `mission-start`, without the board edits the commander never commits. The file tree shows the four files the engineers changed. Walk each workstream test file first, then its module, and mark each file reviewed with **m**.

   Then open a new session (**Ctrl+X** then **N**), keep **Build**, and send:

   ```text
   Use the mini-reviewer subagent in the foreground to review workstreams WA and WB.
   Give it a complete brief: the sections are in mission/MINI-BRIEF.md, the commits
   start with "WA:" and "WB:", and it should use its REVIEW report format. Do not
   edit any file. Show me its report as returned.
   ```

   On Windows, unless the preflight shows a working `python3`, add: `Tell it to run py -3 -m unittest instead of python3.` Its rules allow `py -3 -m unittest` exactly; `py -m unittest` without `-3` is denied.

   **Check:** with **Committed**, the `/diff` file tree lists `skyroute/fuel.py`, `skyroute/geo.py`, `tests/test_fuel.py`, and `tests/test_geo.py`, and nothing else. With **All** it also lists `mission/BOARD.md`, the uncommitted board. The reviewer returns `REVIEW` blocks with a `Verdict:` line and quotes the unittest summary lines. In terminal 2, `git status --short` still shows only ` M mission/BOARD.md`: the review changed nothing.

   If the reviewer says it could not run the tests, read why. `Permission denied: shell` means it added something its rules deny, such as `cd`, a pipe, `2>&1`, or `-v` after a pipe: send `Ask mini-reviewer to run exactly python3 -m unittest, with nothing before or after it.` `Python was not found` means the Windows `python3` stub: send the same with `py -3 -m unittest`. If it still cannot, run the tests yourself in terminal 2 and judge its review against your result; its findings from reading the diff still count.

## Stretch goals

- **Blocked path.** Reset one workstream (`git revert --no-edit HEAD`), then tell the commander: "WB was reverted. Set it to blocked with the reason, then launch a fresh eng-geo with its section and the failure." Watch the board go `blocked`, then `in progress`, then `done`.
- **Command for the launch.** The kit starts its commander with `/mission-launch`. Write `.opencode/commands/mini-launch.md` with `agent: commander`, your launch prompt as the body, and `` !`cat mission/BOARD.md` `` at the end. Compare it with [`mission-launch.md`](../../demos/mission-control/kit/.opencode/commands/mission-launch.md).
- **One engineer instead of two.** Merge `eng-fuel` and `eng-geo` into one `engineer` whose rules allow all four files, as the kit does. Run the checker: which cases change from `deny` to `allow`? That is the ownership the kit leaves to the brief.
- **Review a planted-smell patch (12 min).** Do this in a separate scratch workspace, so nothing touches your mission files. In terminal 2:

  ```bash
  bash "$COURSE/labs/AL01-power-session/new-workspace.sh" ~/skyroute-review --force
  cd ~/skyroute-review
  mkdir -p .opencode/commands
  cp "$COURSE/advanced-kit/commands/review-ranked.md" .opencode/commands/
  git apply --index "$COURSE/advanced-kit/review/review-candidate.patch"
  python3 -m unittest tests.test_digest
  ```

  The patch adds `skyroute/digest.py` and `tests/test_digest.py`. **Check:** the test run prints `OK`. Start `opencode` in `~/skyroute-review` in a new terminal tab and run `/review-ranked`. **Check:** findings come one per line, worst first, each with severity, category, `skyroute/digest.py:<line>`, a fix, and a test, ending `VERDICT: FAIL`. There are five planted smells: a module-level `_last_digest`, a bare `except` that returns stale output, the `"Radio"` versus `.lower()` compare (`channel == "Radio"` is case-sensitive while the datalink branch lowercases the channel), a stray `print`, and `INTERNAL:` remarks that leak as `NOTE:`. Count how many the review found. Then, in Build, fix the top two with a regression test each, run `git add -A` in `~/skyroute-review`, and run `/review-ranked` again on the new staged diff. When you are done, quit that OpenCode and run `rm -rf ~/skyroute-review`. Your mission workspace never changed: `git -C ~/skyroute-adv status --short` shows the same lines as before.
- **Audit the child.** `opencode session export <child id> --sanitize` shows the engineer's tool calls and timing with the text redacted.

## Solution

Reference files, in [`labs/AL03-agent-team/team/`](team/mission/MINI-BRIEF.md):

- `team/.opencode/agents/commander.md`, `eng-fuel.md`, `eng-geo.md`, `mini-reviewer.md`: the four agents exactly as in steps 2 to 4. Steps 2 and 4 copy the commander and the reviewer from here; step 3 is the one you type.
- `team/.opencode/commands/mini-status.md` and `team/.opencode/skills/mini-protocol/SKILL.md`: step 5.
- `team/mission/MINI-BRIEF.md` and `team/mission/BOARD.md`: step 1.
- [`check_team.py`](check_team.py): the rule checker from step 4.

Catch up to the launch (step 6) in one move, from `~/skyroute-adv` with a green suite:

```bash
cp -R "$COURSE/labs/AL03-agent-team/team/." .
git add .opencode mission && git commit -m "Add mini mission team" && git branch mission-start
opencode reload
python3 "$COURSE/labs/AL03-agent-team/check_team.py" | tail -1
```

Compare your files with the reference: `diff -r --strip-trailing-cr .opencode "$COURSE/labs/AL03-agent-team/team/.opencode"`.

How the mini mission maps to the instructor's Mission Control (`demos/mission-control/kit/`):

| Mini mission | Mission Control | Difference |
|--------------|-----------------|------------|
| `commander` | `commander` | Same shape; the kit also owns four shared files and runs the status and validator scripts |
| `eng-fuel`, `eng-geo` | `engineer` | One agent per workstream here, so OpenCode enforces ownership; the kit uses one agent and the brief |
| `mini-reviewer` | `mission-reviewer` | Same rules |
| `/mini-status` (shell output, no model needed for facts) | `/mission-status` with `tools/mission_status.py` | The kit's status is a script that also reads files on disk |
| `mini-protocol` skill | `mission-protocol` skill | Same board states and report block |
| `MINI-BRIEF.md` | `BRIEF.md`, then a generated and validated `MISSION-PROMPT.md` | The kit generates its long mission order and checks it with `check_prompt.py` |

A good result: `check_team.py` prints `37 of 37 checks pass`, the log shows one `WA:` and one `WB:` commit made by the commander, both reference test modules print `OK`, and the reviewer changed nothing.
