# Fan-out prompt

Paste the prompt below into a primary agent session (the `build` agent) started in the root of a starter SkyRoute workspace with a clean Git tree. It creates one worktree per task in `TASKS.md` with the Code Mode worktree tools, launches one background subagent per worktree, and reports the branches to merge.

Before you start:

- Copy `advanced-kit/fanout/TASKS.md` to the workspace root, commit it, and check that `git status` is clean. Worktrees start from the committed state.
- Optional: set `"worktree": { "directory": "../worktrees" }` in `opencode.jsonc` to put worktrees next to the workspace. Without it they go under the OpenCode data directory, for example `~/.local/share/opencode/worktree/<first six characters of the project ID>/t1-bearing`.
- On 2.1.x, `worktree_create` returns only `{ "directory": ... }` and the worktree starts on a detached HEAD at the current commit. The prompt records that commit as BASE and compares each worktree against it, not against `HEAD~1`, so a child that made two commits is still checked in full. `worktree_list` returns `{ "worktrees": [ { "directory", "strategy" } ] }`, including the main checkout. In the observed run the model called them as `tools.opencode["worktree_create"]({ name: "t1-bearing" })` inside one `execute` script. The prompt has each subagent create its own branch.
- On Windows, OpenCode's shell is PowerShell 5.1, where `&&` is a syntax error, so the `cd "<worktree directory>" &&` form in the prompt fails on the first command of each child. Add this line at the end of the prompt: `On Windows the shell is PowerShell 5.1: tell each child to separate commands with ; instead of &&.`
- Run the prompt in the TUI, or headless without `--standalone`. Under `--standalone` a background subagent stops when the run ends. A headless `opencode run` returns as soon as the children are launched; they keep working in the service, and the service resumes the parent on each completion notice so it still posts its final table in the session. Wait for that before you check or merge: watch `demos/mission-control/dashboard.py --root-agent build` until every row is `idle`, or poll `opencode api session.active` until it prints `{"data":{}}`.

## Prompt

```text
Read TASKS.md. It defines three independent tasks, T1, T2, and T3, with disjoint file sets.

1. Run git rev-parse HEAD in this workspace and record the hash as BASE. Then use
   the execute tool (Code Mode). In one execute call, call the opencode namespace
   worktree_create tool three times, with names "t1-bearing", "t2-fuel", and
   "t3-report", then call worktree_list. Record each worktree's directory exactly as
   the tools return it. Do not create worktrees with git commands. The new worktrees
   are on a detached HEAD at BASE; each subagent creates its own branch in step 2.

2. Launch three general subagents with background: true, one per task, in one turn.
   Give each one a complete prompt that contains:
   - the absolute worktree directory it owns, and the instruction to work only there:
     read and edit files by absolute path inside that directory, and start every shell
     command with cd "<worktree directory>" &&
   - the instruction to run cd "<worktree directory>" && git switch -c fanout/<name>
     before any edit, where <name> is the worktree name (for example fanout/t1-bearing)
   - the full text of its task section from TASKS.md, including May touch, Done when,
     and the test command
   - the rule that it must not touch any file outside its May touch list, must not
     edit the main checkout, and must not merge, push, or rebase
   - the instruction to commit on its worktree branch and finish with a report:
     branch, commit hash, test result line, and the test IDs it added

3. While they run, do not edit files. When each completion notification arrives,
   check its work yourself. Run git -C "<worktree directory>" log --oneline BASE..HEAD,
   git -C "<worktree directory>" diff --stat BASE..HEAD, and
   git -C "<worktree directory>" status --short. Confirm that only the files in that
   task's May touch list changed since BASE, and that status prints nothing (no
   uncommitted or untracked files left behind).

4. When all three are done, reply with a table: task, branch, worktree directory,
   commit, test result, files changed, and whether the file check passed. Then list
   the merge commands in order, and the test IDs to add to
   requirements/requirements.json after the merge. Do not merge.
```

## What to look for

| Step | Evidence |
|------|----------|
| Worktrees created | `git worktree list` in the workspace shows three extra entries; `worktree_list` returns them |
| Subagents in parallel | The TUI shows three child sessions; Down opens the subagent picker. `opencode api GET /api/session/active` lists them |
| File isolation | `git -C <worktree> diff --stat <BASE>..HEAD` shows only the task's files, across every commit the child made; `git -C <worktree> status --short` prints nothing, so no uncommitted or untracked file was left out of the diff |
| Result | Each branch passes its test command; merged together, `python3 -m unittest` shows only the known D2 failure |
| Trace | After the merge, one commit by the coordinator (you or the parent agent) adds the reported test IDs to SR-GEO-002, SR-FUEL-002, and SR-RPT-002 to SR-RPT-006 in `requirements/requirements.json`. No child edits that file |

## Clean up

Ask the agent to call `worktree_remove` for each worktree (set `force` only to discard uncommitted work), or run `git worktree remove <directory>` yourself. `worktree_remove` asks for the `edit` permission on the worktree directory. On 2.1.x it returns `{ "directory", "removed": true }` and keeps the `fanout/<name>` branch, so merge after removal works.
