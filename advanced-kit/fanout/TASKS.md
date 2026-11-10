# Fan-out tasks for parallel worktrees

Three independent SkyRoute fixes for Module A08 and Lab AL06. Each task runs in its own Git worktree on its own branch, so the agents never write the same file. Start from a **starter** SkyRoute workspace (a Git copy of `labs/skyroute`, no solution overlay).

## Rules for every task

- Touch only the files in the task's **May touch** list. Everything else is read-only, including `requirements/requirements.json`, `skyroute/route.py`, `skyroute/cli.py`, and `AGENTS.md`.
- Do not fix D2 (`Route.total_distance_nm` skips the last leg). It belongs to no task. The starter suite has exactly one failure, `tests.test_route.RouteTests.test_total_distance_includes_every_leg`, and it stays failing in every branch.
- Python standard library only. Tests use `unittest`.
- Commit on the task branch with a message that names the requirement IDs. Do not merge, push, or rebase.
- Report the branch name, the commit hash, the test command output line (`OK` or `FAILED`), and the test IDs you added, so the primary agent can update `requirements/requirements.json` after the merge.

| Task | Defect | May touch | Test command |
|------|--------|-----------|--------------|
| T1 | D1 bearing normalization | `skyroute/geo.py`, `tests/test_geo.py` | `python3 -m unittest tests.test_geo -v` |
| T2 | D3 contingency fuel | `skyroute/fuel.py`, `tests/test_fuel.py` (new) | `python3 -m unittest tests.test_fuel -v` |
| T3 | S1 to S5 report hardening | `skyroute/report.py`, `tests/test_report.py` (new) | `python3 -m unittest tests.test_report -v` |

**Windows.** On Windows, unless `bash "$COURSE/labs/advanced-preflight.sh"` shows a working `python3`, run these test commands as `py -3 -m unittest ...` and tell each child to do the same: the children run them through OpenCode's own shell, which never sees Git Bash functions, and the Microsoft Store `python3` stub exits with code 49 (`Python was not found`). The commands in this file stay as written for macOS and Linux.

## T1: Normalize the initial bearing (D1, SR-GEO-002)

**Problem.** `geo.initial_bearing_deg` returns negative values for westbound legs. SR-GEO-002 requires true degrees in the range [0, 360).

**Done when:**

1. `initial_bearing_deg` returns a value `b` with `0 <= b < 360` for every input. Due north is `0.0`, not `360.0`.
2. `tests/test_geo.py` has new tests for a westbound leg (KDVT to KBFI is about 333.96 degrees), an eastbound leg, and due north.
3. The new westbound test fails against the starter `geo.py` and passes after the fix.
4. `python3 -m unittest tests.test_geo -v` shows `OK`. `python3 -m unittest` shows only the known D2 failure.

## T2: Contingency on trip fuel only (D3, SR-FUEL-002)

**Problem.** `fuel.plan_fuel` computes contingency on trip plus reserve. SR-FUEL-002 requires the configured percentage (default 5) of trip fuel only. There are no fuel tests.

**Done when:**

1. Contingency is `trip * contingency_pct / 100`. Trip, reserve, and total rules (SR-FUEL-001, SR-FUEL-003) are unchanged.
2. New `tests/test_fuel.py` covers trip fuel, contingency with the default and a configured percentage, reserve, total, and the rejected inputs. Use the worked example: 2.0 h at 2400 lb/h gives trip 4800, contingency 240, reserve 1200, total 6240.
3. The contingency test fails against the starter `fuel.py` and passes after the fix.
4. `python3 -m unittest tests.test_fuel -v` shows `OK`. `python3 -m unittest` shows only the known D2 failure.

## T3: Harden report.py (S1 to S5, SR-RPT-002 to SR-RPT-006)

**Problem.** `skyroute/report.py` has five security defects:

| ID | Defect | Required behavior |
|----|--------|-------------------|
| S1 | `export` builds a path from the user-supplied name (path traversal) | Reject names that leave the output directory (`../x`, absolute paths) with `ValueError` |
| S2 | `archive` runs `tar` through a shell with user input (shell injection) | Build the archive without a shell, for example with `tarfile` |
| S3 | `load_cached` uses `pickle.load` | Store and load cached data as JSON; refuse anything else |
| S4 | `parse_altitude` uses `eval` | Parse `FL350` and `35000` explicitly; reject expressions with `ValueError` |
| S5 | Hard-coded `REPORT_UPLOAD_TOKEN` | Read `SKYROUTE_UPLOAD_TOKEN` from the environment; fail clearly when it is missing |

**Done when:**

1. Each of S1 to S5 is fixed and keeps the public function names and signatures.
2. New `tests/test_report.py` has at least one test per defect that fails against the starter `report.py` and passes after the fix. Tests use temporary directories and never write outside them.
3. The tests do not depend on `Route.total_distance_nm` (D2 is out of scope). Note for rehearsals: `labs/solutions/skyroute/tests/test_report.py` has one test, `FormatTests.test_report_lists_every_leg_and_totals`, that needs the D2 fix. Copying the solution files for T3 into a starter workspace gives two failures, not one.
4. `python3 -m unittest tests.test_report -v` shows `OK`. `python3 -m unittest` shows only the known D2 failure.
5. No token string remains in `skyroute/report.py`.

## After all three branches report

The primary agent (or you) merges the branches into the starting branch one at a time and runs `python3 -m unittest` after each merge. The merges do not conflict because the file sets are disjoint. Then add the new test IDs to the `tests` lists of SR-GEO-002, SR-FUEL-002, and SR-RPT-002 to SR-RPT-006 in `requirements/requirements.json`, in one commit, by one agent.
