---
name: mini-protocol
description: Board and report protocol for the SkyRoute mini mission. Load it when you are the commander, an engineer, or the mini-reviewer working on mission/MINI-BRIEF.md, before launching, building, or reporting.
---

# Mini mission protocol

## Ownership

- WA owns `skyroute/fuel.py` and `tests/test_fuel.py`. WB owns `skyroute/geo.py` and `tests/test_geo.py`.
- An engineer edits only its own files. A change needed elsewhere goes under `Open issues:`.
- Only the commander edits `mission/BOARD.md`, and only the commander runs `git add` and `git commit`.
- Run shell commands from the workspace root without `cd`, pipes, or redirection, for example `python3 -m unittest tests.test_fuel`, not `cd <path> && python3 -m unittest tests.test_fuel 2>&1 | tail -1`. Each part of a compound command is checked against your rules.

## Launch

- Use the `subagent` tool with `background: true`: `eng-fuel` for WA, `eng-geo` for WB. Launch both in the same turn.
- Description `WA Fuel` or `WB Bearing`. It becomes the child session title.
- The prompt holds the full workstream section of the brief, the owned files, and the report format below.

## Board

`mission/BOARD.md` has one row per workstream:

```
| WS | Workstream | Status | Session | Tests | Updated |
```

- Status is `planned`, `in progress`, `review`, `done`, or `blocked`.
- `in progress` on launch (Session = the description). `review` when the report arrives. `done` after the workstream's Done command passes and the commit is made (Tests = the summary, for example `6/6`). `blocked` with the reason in Tests.
- Updated is `HH:MM` local time. Get it with `date +%H:%M`. Update the board on every launch and every report.

## Report format

Engineers end with exactly this block:

```
REPORT W<x>
Status: done | blocked
Built: <files changed and what changed>
Tests: <the Done command from your section> -> <the unittest summary line>
Open issues: <none, or one line each>
```

## Verification

- Both engineers work test first in one checkout. A workstream is judged by its own Done command (its test module plus the baseline modules no workstream owns) and by `git diff -- <its owned files>`. The other workstream's uncommitted or red files are not its failure.
- The full suite, `python3 -m unittest`, runs only when no row is `in progress` or `review`. It must end in `OK` before the mission is finished.
