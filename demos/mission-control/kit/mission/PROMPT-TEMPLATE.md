# Mission prompt template

`mission/MISSION-PROMPT.md` is the commander's full mission order. Generate it from `mission/BRIEF.md` with this exact skeleton. `python3 mission/check_prompt.py mission/MISSION-PROMPT.md` checks it and names every gap.

Rules for the generated file:

- Keep every heading below, with the same text and numbering, in the same order.
- Replace every `{{...}}` placeholder. Leave none behind.
- Copy file paths, requirement IDs, and test modules from `mission/BRIEF.md` and `mission/workstreams.json` exactly. Put each file path in backticks.
- Copy every workstream's whole python interface block from `mission/BRIEF.md` line for line. The check compares each line with `signatures` in `mission/workstreams.json`; only trailing comments and spacing may differ.
- Keep each workstream section complete. A full mission order is about 350 lines; the check fails anything under 250.
- Write to the commander in the second person. Short sentences. No em or en dashes.

The skeleton starts below the line.

---

```markdown
# Mission order: SkyRoute Ops Center

## 1. Role

{{Who the commander is, what it may and may not do: it plans, launches engineers and the mission-reviewer, updates the board, commits finished work, and never writes workstream code. In Phase 2 the only code it writes is the integration glue in skyroute/cli.py and tests/test_cli.py.}}

## 2. Ground rules

{{The ground rules from the brief: Python 3.10+ stdlib only, `from __future__ import annotations` at the top of every new module, synthetic data, test first, units in names, every command from the workspace root without `cd`, pipes, or redirection, how a workstream is verified in a shared checkout, baseline tests stay green, the shared files only the commander edits.}}

## 3. Workstreams

### W1 Weather

- **Goal:** {{one or two sentences}}
- **Depends on:** {{none, or the workstream IDs}}
- **Requirements:** {{every requirement ID from the brief and its text, written to requirements/w1.json}}
- **Files:** {{every owned file in backticks, comma separated}}
- **Interface:** {{the module path, then the brief's whole python interface block, copied line for line in a python code block below this line}}
- **Tests:** {{the test module path and what it must cover}}
- **Done:** {{the done criteria, including the exact unittest command and python3 tools/mission_status.py --verify W1}}

### W2 NOTAMs

{{same seven fields}}

### W3 Performance

{{same seven fields}}

### W4 Alternates

{{same seven fields}}

### W5 Briefing package

{{same seven fields}}

### W6 Assurance

{{same seven fields}}

## 4. File ownership

| File | Owner |
|------|-------|
| {{`path`}} | {{W1 to W6, or commander}} |

{{One row per file: every workstream file and every commander-owned shared file. No file appears twice.}}

## 5. Dependency order

| Wave | Workstreams | Starts when |
|------|-------------|-------------|
| 1 | {{IDs}} | {{condition}} |

{{One row per wave, in order. A workstream that depends on another starts in a later wave. The W6 final pass is the last wave.}}

## 6. Subagent launch rules

{{Must state, in these words: launch with background: true; one engineer per workstream; never two engineers on the same file. Also: launch every workstream in a wave in the same turn; the engineer prompt contains the full workstream section and its owned files; use mission-reviewer for reviews; launch nothing else.}}

## 7. Check-in protocol

{{How the board works: mission/BOARD.md, the statuses planned, in progress, review, tooling done (W6 only), done, blocked, when to update it (on launch and on every report). The engineer report format with the lines Built:, Tests:, Open issues:. Append every report to mission/log.md. Verify a report with python3 tools/mission_status.py --verify W<n> before marking done; other workstreams' changes and red tests are not a failure. Commit only the owned files. Run the full suite only when no workstream is in progress.}}

## 8. Phase 1

{{Step-by-step launch plan for waves 1 to 3, what to do as each report arrives, and the W6 tooling milestone.}}

## 9. Phase 2

{{Integration of skyroute wx and skyroute brief (with --load and the fixed synthetic load from the brief) in skyroute/cli.py with tests/test_cli.py, mission-reviewer review of each workstream, fix rounds, fragment merge, final W6 pass with docs/evidence verified by python3 tools/mission_status.py --verify W6 --final.}}

## 10. Done criteria

{{Mission done criteria from the brief, including python3 -m unittest, mission/BOARD.md all done, docs/evidence complete.}}
```
