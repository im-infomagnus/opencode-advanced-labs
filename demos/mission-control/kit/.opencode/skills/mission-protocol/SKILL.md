---
name: mission-protocol
description: Reporting and board protocol for the SkyRoute Ops Center mission. Load it when you are the commander, an engineer, or the mission-reviewer working on mission/MISSION-PROMPT.md, before launching, building, or reporting.
---

# Mission protocol

One protocol for everyone on the mission. The commander follows all of it; engineers follow "Ownership", "Commands", "Report format", and step 1 of "Verification before done".

## Ownership

- Every file belongs to exactly one owner. `mission/workstreams.json` is the registry; the File ownership table in `mission/MISSION-PROMPT.md` repeats it.
- An engineer edits only its workstream's files. A change needed elsewhere goes under `Open issues:` in the report. The `engineer` agent's rules allow every workstream file, so this line is a rule the mission order sets and the commander checks with `git diff -- <owned paths>`, not a permission. The rules do deny the shared files, `mission/`, everything outside the mission files, Git writes, and the network.
- The commander alone edits `skyroute/cli.py`, `tests/test_cli.py`, `requirements/requirements.json`, `README.md`, `mission/BOARD.md`, and `mission/log.md`.
- The commander alone runs `git add` and `git commit`. Parallel engineers never touch the Git index.
- Requirements go in per-workstream fragments `requirements/wN.json`. The commander merges them with `python3 -m skyroute.assurance merge --write` in Phase 2.
- Every new module starts with `from __future__ import annotations`.

## Commands

- Run every shell command from the workspace root, exactly as your rules allow it, without `cd`, pipes, or redirection. Write `python3 -m unittest tests.test_weather`, not `cd ~/opencode-mission && python3 -m unittest tests.test_weather 2>&1 | tail -5`.
- Each part of a compound command is checked against your rules. An engineer's `cd`, `tail`, or `grep` is denied. A commander command outside its allowlist waits for a human approval, overnight if nobody is there.

## Launch rules

- Launch engineers with the `subagent` tool, `agent: engineer`, `background: true`.
- One engineer per workstream at a time. Never two engineers on the same file.
- Launch every ready workstream in the same turn. Ready means every workstream it depends on is `done`.
- Description: `W<n> <name>`, for example `W1 Weather`. It becomes the session title.
- The engineer prompt contains: the workstream ID and name, the full workstream section from the mission order, the exact list of owned files, the interfaces of finished dependencies, and the report format below.
- Reviews use `agent: mission-reviewer`. Nothing else is launched.

## Board

`mission/BOARD.md` has one row per workstream:

```
| WS | Workstream | Status | Session | Files | Tests | Updated |
```

- Status is one of `planned`, `in progress`, `review`, `tooling done`, `done`, `blocked`. Only W6 uses `tooling done`.
- `planned` to `in progress` when the engineer is launched (Session = the description).
- `in progress` to `review` when the report arrives and the commander starts verifying.
- `review` to `done` after `python3 tools/mission_status.py --verify W<n>` prints `Result: PASS` and the owned changes are committed. Tests = the summary, for example `24/24`.
- W6 has two milestones. Its wave 1 tooling goes `review` to `tooling done` after the same verify and commit. Its final pass goes `tooling done` to `in progress` to `review`, then to `done` after `python3 tools/mission_status.py --verify W6 --final` prints `Result: PASS`, which needs `docs/evidence/README.md`, `docs/evidence/trace-matrix.md`, and `docs/evidence/test-run.txt`. Phase 1 is finished for W6 at `tooling done`.
- Any state to `blocked` with the reason in the Tests cell when a report says blocked, the workstream's own verify fails, or the engineer stops without a report. Another workstream's files or red tests never block a workstream.
- Updated is `HH:MM` local time.
- Update the board on every launch and every report. Never batch updates.

## Report format

Engineers end with exactly this block:

```
REPORT W<n>
Status: done | blocked
Built: <files created or changed, and the public functions>
Tests: python3 tools/mission_status.py --verify W<n> -> <its Tests line summary>
Open issues: <none, or one line each>
```

The commander appends each report to `mission/log.md` under a `## HH:MM W<n>` heading, with one line of its own verification result below it.

Engineers report the per-workstream verify, never the whole suite. Siblings write their tests first in the same checkout, so the whole suite is often red because of files that are not yours.

## Verification before done

Engineers run in parallel in one checkout. Judge each workstream only by its own files and tests.

1. `python3 tools/mission_status.py --verify W<n>` prints `Result: PASS`. It checks the owned files exist and runs `python3 -m unittest` on the workstream's own test module, the modules of the workstreams it depends on, and `baseline_test_modules` from `mission/workstreams.json`.
2. The owned changes it lists (`git status --short -- <owned paths>`) are the files to commit. Read them with `git diff -- <owned paths>` and check they match the workstream section.
3. Changes outside the owned paths belong to other workstreams or to you. They are not a failure of this workstream.

Then `git add <owned files>` and `git commit -m "W<n>: <summary>"`.

## Full suite

`python3 -m unittest` with no module runs every test, including siblings' red test-first modules. Run it only when no row is `in progress` or `review`: at each wave boundary, before each Phase 2 commit, and in the final W6 pass. It must pass there. A failure at a wave boundary is in committed work: find the workstream with `python3 tools/mission_status.py` and block it.
