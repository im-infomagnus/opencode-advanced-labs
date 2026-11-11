# OpenCode 1 hands-on labs: handbook

Ten labs on the SkyRoute flight planner (synthetic code). Each lab is 20 to 40 minutes. Do them in order; later labs reuse files from earlier ones.

| # | Lab | Time | You build |
|---|---|---|---|
| 1 | [First session](V1-01-first-session.md) | 20 min | A first edit, undone and redone |
| 2 | [AGENTS.md](V1-02-agents-md.md) | 20 min | Project rules the agent follows |
| 3 | [Explore and test](V1-03-explore-test.md) | 35 min | Tests that expose two seeded bugs |
| 4 | [Debug](V1-04-debug.md) | 25 min | A root-caused fix with proof |
| 5 | [Secure review](V1-05-secure-review.md) | 35 min | CWE findings, tests, and fixes |
| 6 | [Commands and skills](V1-06-commands-skills.md) | 30 min | `/test-gaps` and a review skill |
| 7 | [Agents](V1-07-agents.md) | 35 min | A read-only reviewer and a tester |
| 8 | [Guardrails](V1-08-guardrails.md) | 25 min | Team permission rules |
| 9 | [MCP server](V1-09-mcp.md) | 30 min | A requirements tool for the agent |
| 10 | [Plugin and headless](V1-10-plugin-headless.md) | 40 min | An audit plugin and a CI review |

## Before any lab

- Clone the course repository and open two terminals at `labs/skyroute`: **T1** for OpenCode, **T2** for checks.
- Windows: use Git Bash. Run Python as `py -3` wherever a guide says `python`.
- Work on a branch, from the repository root:

  ```bash
  bash labs/reset.sh --starter
  git switch -c v1-labs-<yourname>
  ```

- Confirm the starter in T2: `python -m unittest` ends with `FAILED (failures=1)`. That failure is the Lab 4 bug.
- Reset at any time: `bash labs/reset.sh` restores your last commit; `--starter` restores the original.

## SkyRoute in one minute

| Path | What it is |
|---|---|
| `skyroute/geo.py` | Distance and bearing |
| `skyroute/fuel.py` | Fuel plan: trip, contingency, reserve |
| `skyroute/route.py` | A route of fixes and its legs |
| `skyroute/navdata.py` | Reader for the fixed-width navdata file |
| `skyroute/report.py` | Plan export and archive (has security bugs) |
| `skyroute/cli.py` | Command line: `python -m skyroute plan` and `export` |
| `requirements/requirements.json` | Requirements `SR-*` with linked tests |
| `tests/` | `unittest` suite |

Try it: `python -m skyroute plan --route KDVT,ZUNIX,KMSP --gs 450 --burn 5000`.

## OpenCode 1 quick reference

| Do this | Keys or command |
|---|---|
| Switch Build and Plan | **Tab** |
| Reference a file | `@path` in the prompt |
| Run a shell command | `!` then the command |
| Undo or redo the last change | `/undo`, `/redo` |
| New session, list sessions | `/new`, `/sessions` |
| Pick a model | `/models` |
| Create AGENTS.md | `/init` |
| Compact a long session | `/compact` |
| Stop the agent | **Esc** |
| All commands | `/help` |
| Run without the TUI | `opencode run "prompt"` |

**Build** edits and runs commands. **Plan** reads and proposes, and does not edit.

## Where OpenCode 1 reads files

| What | Project path | Personal path |
|---|---|---|
| Config | `opencode.json` | `~/.config/opencode/opencode.json` |
| Rules | `AGENTS.md` | `~/.config/opencode/AGENTS.md` |
| Agents | `.opencode/agents/<name>.md` | `~/.config/opencode/agents/` |
| Commands | `.opencode/commands/<name>.md` | `~/.config/opencode/commands/` |
| Skills | `.opencode/skills/<name>/SKILL.md` | `~/.config/opencode/skills/` |
| Plugins | `.opencode/plugins/<name>.js` | `~/.config/opencode/plugins/` |

Restart OpenCode after you change config, agents, commands, skills, or plugins.

## House rules

- Ask in **Plan** first, then switch to **Build** to change files.
- Check every claim: run the test, open the line.
- The agent must not weaken a test to make it pass. `git diff tests/` shows if it did.
- Commit after each lab: `git add -A . && git commit -m "Lab N"`.
- Use only the synthetic SkyRoute code in these labs.

## If something goes wrong

| Symptom | Fix |
|---|---|
| Agent edits in Plan, or Build does not edit | Check the footer and press **Tab** |
| Answer cites files outside `labs/skyroute` | Start OpenCode in `labs/skyroute`; add "Use only files under labs/skyroute" |
| New agent, command, or skill not listed | Restart OpenCode; check the folder name and frontmatter |
| MCP tools missing | `opencode mcp list`; run the server command by hand to see its error |
| The agent changed a test | `git checkout -- tests/` and ask again, saying "do not change tests" |
| Lost | `bash labs/reset.sh` and repeat the step |
