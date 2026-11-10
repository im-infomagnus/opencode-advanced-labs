# SkyRoute agent instructions (everything in one file)

This file is deliberately too long. Lab AL02 uses it for the context-tier audit.
Every line below is sent on every request.

## Project

- SkyRoute is a synthetic flight-planning toolkit in standard-library Python.
- The package is `skyroute/`. Tests are in `tests/`. Requirements are in `requirements/requirements.json`.
- Run the suite with `python3 -m unittest`. Run one module with `python3 -m unittest tests.test_<module>`.
- Run the CLI with `python3 -m skyroute plan --route KDVT,ZUNIX,KMSP --gs 450 --burn 2400`.
- Never add third-party dependencies.

## Code style

- Use four spaces for indentation. Never use tabs.
- Keep lines under 100 characters.
- Put two blank lines between top-level functions and classes.
- Sort imports: standard library first, then local modules, one per line.
- Use double quotes for strings unless the string contains a double quote.
- Remove trailing whitespace and end every file with one newline.
- Format every Python file you edit before you finish.

## Tests

- Use `unittest` only. Do not use pytest.
- Name tests `test_<behavior>` and assert exact expected values.
- Start each test docstring with the requirement ID, for example `"""SR-FUEL-002: ..."""`.
- Put fuel tests in `tests/test_fuel.py`, report tests in `tests/test_report.py`, geometry tests in `tests/test_geo.py`.
- For legacy `navdata.py`, write characterization tests that pin current behavior before any refactor.
- Characterization tests must pass on the unchanged code before you change anything.

## Navigation data (SRN-1)

- SRN-1 records are fixed width, one record per line, LF or CRLF line endings.
- Columns 0 to 1 are the kind (`AP` airport, `WP` waypoint, `NV` navaid), then a space, then the ident in columns 3 to 7.
- Latitude is columns 9 to 17 and longitude 19 to 28: a hemisphere letter, then `DDMMSSss` (latitude) or `DDDMMSSss` (longitude). Only uppercase `S` and `W` make a value negative.
- Elevation (columns 30 to 34), frequency (36 to 41), and name (43 to end) are optional.
- Lines starting with `*` are comments. Blank lines are ignored. Unknown kinds, including lowercase `wp`, are ignored without a message.
- Malformed records are skipped. When an ident appears twice, the last record wins.
- The parser reads each file once per process and caches it until `navdata.clear()`. Do not remove the cache without a characterization test.
- Read the full SRN-1 specification before you change `navdata.py`.

## Fuel policy

- Trip fuel is burn rate times time enroute.
- Contingency fuel is a percentage (default 5) of trip fuel only.
- Final reserve is a fixed number of minutes (default 30) at the burn rate. It does not depend on the trip length.
- Total fuel is trip plus contingency plus reserve.

## Security

- Never read `.env` files or print secrets.
- Never run `git push`, `rm -rf`, `curl`, or `wget`.
- Never use `eval`, `exec`, `pickle.load`, or `shell=True`.
- Validate every path that comes from user input.

## Commits and reviews

- Write commit messages in the imperative mood, under 72 characters.
- Mention the requirement ID in the commit body.
- Before you commit, run the full suite and summarize the result.
- When asked for a review, check injection, paths, deserialization, and secrets, and rate each finding.
- When asked to modernize a file, plan first, list behavior to preserve, then refactor in small steps.
