# AGENTS.md

SkyRoute is a small synthetic flight-planning toolkit used for training. It is Python 3.10 or later with the standard library only. All data is synthetic. Do not add real program data, real procedures, or third-party packages.

## Commands

Run every command from this directory (the one that holds this file).

| Task | Command |
|------|---------|
| Run all tests | `python -m unittest` |
| Run one test module | `python -m unittest tests.test_fuel -v` |
| Run one test | `python -m unittest tests.test_route.RouteTests.test_total_distance_includes_every_leg` |
| Print a plan | `python -m skyroute plan --route KDVT,ZUNIX,KMSP --gs 450 --burn 2400` |
| Export a plan | `python -m skyroute export --route KDVT,ZUNIX,KMSP --gs 450 --burn 2400 --name kdvt_kmsp` |

There is no build step and no linter. On machines where `python` is missing, use `python3`.

## Layout

| Path | Contents |
|------|----------|
| `skyroute/geo.py` | Great-circle distance and initial bearing |
| `skyroute/navdata.py` | Reader for the fixed-width SRN-1 navigation data format |
| `skyroute/route.py` | `Route` and `Leg`: legs, total distance, time enroute |
| `skyroute/fuel.py` | `FuelPlan`: trip, contingency, reserve, total |
| `skyroute/report.py` | Text report, export, archive, cache, upload headers |
| `skyroute/cli.py` | `argparse` CLI with `plan` and `export` |
| `data/navdata.srn` | Navigation data. See `docs/srn1-format.md` |
| `requirements/requirements.json` | Software requirements with the tests that verify them |
| `tests/` | `unittest` tests, one module per source module |

## Conventions

- Units: degrees for angles, nautical miles for distance, knots for speed, feet for altitude, pounds for fuel, pounds per hour for burn. Put the unit in the name when it is not obvious (`distance_nm`, `groundspeed_kt`).
- Bearings are true degrees in the range [0, 360).
- Validate input at the CLI and file boundaries. Raise `ValueError` with a message that names the bad value.
- Do not use `eval`, `exec`, `pickle`, `shell=True`, or `os.system`. Never build file paths from user input without checking that the result stays in the intended directory.
- Read secrets from environment variables. The upload token is `SKYROUTE_UPLOAD_TOKEN`. Never commit a credential.
- Keep modules small. Add a comment only to explain a reason the code cannot show.

## Requirements

Requirement IDs look like `SR-FUEL-002`. Areas are `SR-GEO`, `SR-NAV`, `SR-RTE`, `SR-FUEL`, and `SR-RPT`. When you change behavior covered by a requirement:

1. Read the requirement text in `requirements/requirements.json`.
2. Add or update a test that checks it.
3. Add the test ID (for example `tests.test_fuel.FuelTests.test_contingency_is_percent_of_trip`) to the requirement's `tests` list.

Do not edit requirement text to match the code. If the code and a requirement disagree, report it.

## Verification rules

- Run `python -m unittest` before you say a change is done, and show the result line (`OK` or `FAILED`).
- Never weaken a test to make it pass. Do not delete a test, loosen an assertion, change an expected value, or add a skip to get a green run. Fix the code, or stop and explain why the test is wrong.
- A bug fix comes with a test that fails before the fix and passes after it.
- `skyroute/navdata.py` has characterization tests in `tests/test_navdata_characterization.py`. They pin current behavior, quirks included. A refactor must keep them passing without edits.
- Check the CLI by hand after a change to `route.py`, `fuel.py`, `report.py`, or `cli.py`: run the plan command above and read the output.
