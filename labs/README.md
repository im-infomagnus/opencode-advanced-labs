# Labs

Hands-on labs for the OpenCode v2 Power User advanced workshop. Every lab runs against SkyRoute, a small synthetic flight-planning toolkit in [`labs/skyroute`](skyroute/). SkyRoute is Python 3.10 or later with the standard library only. It contains seeded bugs and security defects for the labs to find. All its data is synthetic and not for navigation.

## Labs

Each one repeats an instructor demo, so learners have already seen it work, and then adds something new. Labs AL01 to AL03 run in `~/skyroute-adv`, which `AL01-power-session/new-workspace.sh` creates. AL04 to AL06 each start from their own fresh workspace. Before Lab AL01, run `bash labs/advanced-preflight.sh` from the course clone (in Git Bash on Windows) and fix every `FAIL` line; see the Windows note below.

| Lab | Title | Time | Repeats demo | What you do |
|-----|-------|------|--------------|-------------|
| [AL01](AL01-power-session/README.md) | Power Session and Review with /diff | 25 min | A02 | Shell mode, `@` ranges, steering and queueing, `/btw`, a fix reviewed in the `/diff` viewer, undo and redo, tabs. |
| [AL02](AL02-context-scale/README.md) | Context at Scale | 30 min | A04 | Outside references, nested `AGENTS.md`, probing whether `instructions` reached the model, the context API, compaction, and fork. |
| [AL03](AL03-agent-team/README.md) | Build an Agent Team and Run a Mini Mission | 50 min | A05, A06, A01 | A commander, two engineers, and a read-only reviewer with enforced permissions, a command, and a skill. Run two workstreams in parallel. |
| [AL04](AL04-mcp-codemode/README.md) | Build an MCP Server and Use Code Mode | 30 min | A07 | Implement the `navdata` MCP server, register it, read the Code Mode script, compare with `codemode: false`, add an `ask` rule. |
| [AL05](AL05-plugin/README.md) | Change the Harness: Write a Plugin | 55 min | A09 | One plugin with a custom tool, a verify-after-edit hook, and a JSON-lines audit log. AI permission gate as a stretch goal. |
| [AL06](AL06-fanout/README.md) | Parallel Worktree Fan-out with a Live Dashboard | 45 min | A08, A10 | Three subagents in three worktrees, watched on a live dashboard, merged and reviewed with `/diff`. |

## Before any lab

- Clone this repository. You need OpenCode v2, Git, and Python 3.10 or later; `bash labs/advanced-preflight.sh` checks them.
- The guides write `python`. On macOS and Linux, use `python3` if `python` is not found.
- **Windows.** Run every `bash` command in **Git Bash**, never in PowerShell or cmd: PowerShell strips the quotes inside the lab commands and truncates prompts and commit messages. Run Python as `py -3`. In Git Bash, define the functions and export them once per terminal (or put these lines in `~/.bashrc`), so the commands in the guides and the lab scripts work as written:

  ```bash
  python3() { py -3 "$@"; }
  python() { py -3 "$@"; }
  export -f python3 python
  export PYTHON="py -3"
  export PYTHONUTF8=1
  ```

  `export -f` passes the functions to the scripts you run with `bash`. Scripts that run Python, such as `headless-review.sh` and `new-workspace.sh`, also read `PYTHON`. `PYTHONUTF8=1` makes Python read files as UTF-8; without it, reading a session export can fail with `UnicodeDecodeError`. Where a guide passes the current directory to `opencode api`, use `pwd -W` instead of `pwd -P`, because the service expects a Windows path. Prompts that make the agent run Python end with the hint "On Windows run Python as `py -3`." Keep it on Windows and drop it elsewhere.

  - **OpenCode's shell is PowerShell.** On Windows, the agent's shell tool, `!` commands in the TUI, and `` !`...` `` lines in command files run in Windows PowerShell, not Git Bash. Bash-only syntax there fails: `tail`, `$VAR` (PowerShell writes `$env:VAR`), `2>&1 | tail`, and `&&` (Windows PowerShell 5.1 needs `;`). Keep command-file lines and agent test commands to a plain program call such as `py -3 -m unittest`.
  - **The `python3` stub.** On many Windows machines `python3` is a Microsoft Store placeholder that prints `Python was not found` and exits with code 49. The Bash functions above do not reach programs that OpenCode starts itself: `!` commands in the TUI, agent shell commands, plugins, and MCP servers. For the advanced labs, run `bash labs/advanced-preflight.sh` from the course clone before Lab AL01. If it reports the stub, run `bash labs/advanced-preflight.sh --fix-python3`: it copies `python.exe` to `python3.exe` in your Python folder, and the preflight run after it should pass. If `python3` still resolves to the stub (your Python folder comes after `WindowsApps` on PATH), turn off the `python.exe` and `python3.exe` entries under **Settings > Apps > Advanced app settings > App execution aliases**, run `opencode service restart`, and run the preflight again. If you cannot change your Python folder, type `py -3` wherever a guide types `python3` in the TUI, and use `"command": ["py", "-3", ...]` for MCP servers.
  - **Line endings.** With `core.autocrlf=true`, kit files have CRLF line ends, and a Windows editor may save your files with CRLF too. A `diff` between a CRLF file and an LF file then shows every line as changed. Compare files with `diff --strip-trailing-cr`; the advanced guides already do.
  - **Temporary files.** A Git Bash path such as `/tmp/x.json` means nothing to Windows Python when it appears inside a `python -c "..."` string. The advanced guides write their scratch files to `.git/` in the workspace (always present, never committed) and pass file paths to Python as arguments.
  - **Paths that start with `/`.** Git Bash rewrites an argument that starts with `/` into a Windows path before a Windows program sees it, so `opencode api post /api/session/...` arrives as `C:/Program Files/Git/api/...`. Use the operation-ID form the guides give (for example `opencode api session.compact --param sessionID=...`). Custom slash commands such as `/review-diff` run only in the TUI: `opencode run "/review-diff"` sends the text to the model as a plain message on every platform.
  - **`opencode` from Python.** An npm install of OpenCode on Windows is `opencode.cmd`. The course scripts find it with `shutil.which("opencode")`; if you write your own script, do the same instead of calling a bare `opencode`.
- **Model.** The labs work with any model your OpenCode can reach. The repository README shows how to set your default model. Model names have the form `<provider>/<model>`. Results differ between models, so each **Check** describes what to look for, not exact output.
- **Agents.** **Shift+Tab** switches between Build and Plan in the TUI. Outside the TUI, `opencode run --agent plan "<prompt>"` or `--agent build` does the same for one prompt.
- **`@` in a prompt.** `@` attaches a file (`@skyroute/route.py`) or loads a skill (`@skill-id`).
- **Stay in the lab folder.** `labs/solutions/` holds reference answers, and an agent started in `labs/skyroute` can read them. Prompts in the early labs say "Use only files under labs/skyroute." Keep that line, or the result may come from the answer key.
- Open two terminals at `labs/skyroute`. Run `opencode` in the first. Run the **Check** commands in the second, so your checks stay out of the conversation.

## Start clean or catch up

Each lab says what it needs from earlier labs. Most need nothing.

- [`reset.sh`](reset.sh) restores `labs/skyroute` to your last commit. It discards uncommitted changes and deletes untracked files under `labs/skyroute`, and touches nothing else. Run it from the course repository root:

  ```bash
  bash labs/reset.sh
  ```

- Labs that commit tell you to work on a branch first: `git switch -c my-labs`, or `git switch my-labs` if it exists. Your commits then stay off the course branch. Because `reset.sh` restores to your last commit, committed lab work survives a reset. To go back to the original starter and discard lab work, run `bash labs/reset.sh --starter`. It restores the starter files but does not move your branch, so `git status --short` then lists the restored files as staged changes (`M` and `D` lines). Commit them with `git commit -m "Back to SkyRoute starter"` to make the starter your last commit. If you do not commit, a later plain `bash labs/reset.sh` brings your lab work back.
- [`solutions/skyroute/`](solutions/skyroute/) holds the reference result: fixed source files, added tests, a sample `AGENTS.md`, and `docs/srn1-format.md`. Each lab's **Solution** section names the files to copy if you skipped a lab it builds on.

## The starter state

From a fresh SkyRoute workspace, `python -m unittest` runs 17 tests and ends with `FAILED (failures=1)`. The one failure is `tests.test_route.RouteTests.test_total_distance_includes_every_leg` (defect D2). That is intended; Lab AL01 fixes it.
