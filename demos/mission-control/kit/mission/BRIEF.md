# Mission brief: SkyRoute Ops Center

SkyRoute plans a route and its fuel. The Ops Center adds what a crew reads before a flight: decoded weather, NOTAMs for the route, weight and balance, takeoff distance, alternate airports, and one briefing package that puts them together. An assurance workstream keeps the requirements, the trace matrix, and the evidence pack in step with the code.

The work is split into six workstreams, W1 to W6. Each workstream owns its files. A commander agent plans and coordinates; one engineer subagent builds each workstream; a read-only reviewer checks finished work. The `engineer` agent's rules deny the shared files, `mission/`, and every path outside the mission, but they allow every workstream file, so which engineer edits which workstream file is set by the mission order and checked by the commander, not enforced by permissions.

## Ground rules

- Python 3.10 or later, standard library only. No third-party packages.
- Every new module starts with `from __future__ import annotations`. The interfaces below use `X | None`, and the background service may run an older `python3` than your terminal; with this import the annotations are never evaluated at import time.
- All data is synthetic. Use only the public airport identifiers already in `data/navdata.srn` (KDVT, KPHX, KMSP, KPIE, KBFI) and its fictional fixes and navaids. Never add real NOTAMs, real weather, or real aircraft performance data.
- Test first. Each workstream writes `tests/test_<module>.py` before the module, runs it red, then makes it green. Run tests with `python3 -m unittest`.
- Run every command from the workspace root without `cd`, pipes, or redirection, for example `python3 -m unittest tests.test_weather`, not `cd ~/opencode-mission && python3 -m unittest 2>&1 | tail -5`. Each part of a compound command is checked against the agent's rules: an engineer's is denied, and the commander's waits for a human, which can stall the mission overnight.
- Engineers run in parallel in one checkout, test first, so a sibling's test module is often red and its files are often uncommitted. A workstream is verified with `python3 tools/mission_status.py --verify W<n>`: its owned files exist, and its own test module, the modules of the workstreams it depends on, and the baseline modules pass. Changes and red tests that belong to other workstreams are not its failure. The full suite, `python3 -m unittest`, must pass only when no workstream is in progress: at each wave boundary, before Phase 2 commits, and in the final pass.
- Units go in names: `_nm`, `_kt`, `_ft`, `_lb`, `_in`, `_c`, `_sm`, `_inhg`.
- Validate input at file and CLI boundaries. Raise `ValueError` with a message that names the bad value.
- Never weaken an existing test. Every baseline test module (`baseline_test_modules` in `mission/workstreams.json`) stays green the whole time.
- The machine-readable registry of workstreams, files, requirement IDs, and interface lines is `mission/workstreams.json`. This brief and the registry must agree.

## Shared files

Only the commander edits these. Engineers never touch them.

| File | Why it is shared |
|------|------------------|
| `skyroute/cli.py` | Every workstream eventually surfaces here (Phase 2) |
| `tests/test_cli.py` | CLI tests for the Phase 2 subcommands |
| `requirements/requirements.json` | The merged requirement set; built from per-workstream fragments |
| `README.md` | Project overview |
| `mission/BOARD.md` | Mission status board |
| `mission/log.md` | Append-only log of engineer reports |

Requirement fragments keep engineers out of the shared requirements file. Each workstream writes its own `requirements/wN.json` with the same shape as `requirements/requirements.json`. In Phase 2 the commander merges them with the W6 tool.

## Workstreams

### W1 Weather

**Goal.** Decode synthetic METAR reports and compute the flight category for each airport.

**Requirements to add** (`requirements/w1.json`):

| ID | Text |
|----|------|
| SR-WX-001 | `parse_metar` shall decode station, observation time, wind, visibility, cloud layers, temperature, dew point, and altimeter, and shall raise `ValueError` naming the first group it cannot decode. |
| SR-WX-002 | The ceiling shall be the height of the lowest BKN, OVC, or VV layer, or `None` when there is no such layer. |
| SR-WX-003 | The flight category shall be the worse of the ceiling category and the visibility category: LIFR below 500 ft or below 1 SM; IFR 500 to below 1000 ft or 1 to below 3 SM; MVFR 1000 to 3000 ft or 3 to 5 SM; VFR otherwise. |
| SR-WX-004 | `load_metars` shall read `data/metar.txt`, skip blank and `#` lines, and keep the latest report per station. |

**Synthetic METAR format.** One report per line: `METAR KDVT 011753Z 26008KT 10SM FEW050 SCT120 31/02 A2992 RMK SYNTH`. Wind `dddssKT`, `dddssGggKT`, `VRBssKT`, or `00000KT`. Visibility `10SM`, `3SM`, `1/2SM`, `1 1/2SM`, `M1/4SM` (less than 1/4). Clouds `FEW`, `SCT`, `BKN`, `OVC` plus height in hundreds of feet, `VVhhh`, `CLR`, or `SKC`. Temperatures use `M` for minus (`M05/M12`). Altimeter `Annnn` in hundredths of inHg. Everything after `RMK` is ignored.

**Public interface** (`skyroute/weather.py`):

```python
@dataclass(frozen=True)
class Metar:
    station: str
    day: int
    time_z: str                  # "1753"
    wind_dir_deg: int | None     # None for VRB
    wind_kt: int
    gust_kt: int | None
    visibility_sm: float
    layers: tuple[tuple[str, int], ...]   # (("FEW", 5000), ("BKN", 1200))
    ceiling_ft: int | None
    temp_c: int
    dewpoint_c: int
    altimeter_inhg: float
    raw: str

def parse_metar(text: str) -> Metar: ...
def flight_category(ceiling_ft: int | None, visibility_sm: float) -> str: ...   # "VFR" | "MVFR" | "IFR" | "LIFR"
def load_metars(path: str | None = None) -> dict[str, Metar]: ...
```

**Files owned.** `skyroute/weather.py`, `data/metar.txt` (one report for each of KDVT, KPHX, KMSP, KPIE, KBFI, covering at least three categories), `tests/test_weather.py`, `requirements/w1.json`.

**Tests.** `tests/test_weather.py`: every wind and visibility form above, ceiling with and without BKN/OVC/VV, each category boundary (499, 500, 999, 1000, 3000, 3001 ft; 0.75, 1, 2.75, 3, 5, 5.5 SM), a malformed group, and `load_metars` on the real data file.

**Done.** `python3 -m unittest tests.test_weather` passes; `python3 tools/mission_status.py --verify W1` prints `Result: PASS`; every SR-WX requirement lists at least one test ID.

### W2 NOTAMs

**Goal.** Parse synthetic NOTAMs and select the ones that apply to a route at a given time.

**Requirements to add** (`requirements/w2.json`):

| ID | Text |
|----|------|
| SR-NTM-001 | `parse_notam` shall decode location, NOTAM number, category, start, end, and text, and shall raise `ValueError` naming the bad field. |
| SR-NTM-002 | A NOTAM shall be active from its start time (inclusive) to its end time (exclusive). `PERM` has no end. |
| SR-NTM-003 | `notams_for_route` shall return only NOTAMs whose location is a route ident and that are active at the given time, ordered by route position and then start time. |
| SR-NTM-004 | `load_notams` shall raise `ValueError` that names the line number of a malformed line. |

**Synthetic NOTAM format.** One per line: `!KDVT 11/014 RWY 2611010600-2611011800 RWY 07R/25L CLSD`. Fields: `!` plus location ident, number `MM/NNN`, category (`RWY`, `TWY`, `NAV`, `AD`, `OBST`, `AIRSPACE`), validity `YYMMDDHHMM-YYMMDDHHMM` or `YYMMDDHHMM-PERM` in UTC, then free text. Lines starting with `#` and blank lines are ignored.

**Public interface** (`skyroute/notam.py`):

```python
@dataclass(frozen=True)
class Notam:
    location: str
    number: str
    category: str
    start: datetime              # timezone-aware UTC
    end: datetime | None         # None for PERM
    text: str

    def is_active(self, at: datetime) -> bool: ...

def parse_notam(text: str) -> Notam: ...
def load_notams(path: str | None = None) -> list[Notam]: ...
def notams_for_route(notams: list[Notam], idents: list[str], at: datetime) -> list[Notam]: ...
```

**Files owned.** `skyroute/notam.py`, `data/notams.txt` (at least eight NOTAMs across the five airports and the navaids SRV, PRV, LKV, including expired, future, and PERM entries), `tests/test_notam.py`, `requirements/w2.json`.

**Tests.** `tests/test_notam.py`: each field, PERM, start and end boundaries, route filter order, an ident not on the route, a malformed line with its line number.

**Done.** `python3 -m unittest tests.test_notam` passes; `python3 tools/mission_status.py --verify W2` prints `Result: PASS`; every SR-NTM requirement lists at least one test ID.

### W3 Performance

**Goal.** Weight and balance for a synthetic training aircraft, and takeoff distance from a table by interpolation.

**Requirements to add** (`requirements/w3.json`):

| ID | Text |
|----|------|
| SR-PERF-001 | `weight_and_balance` shall compute total weight, total moment, and CG arm as moment divided by weight. |
| SR-PERF-002 | The result shall be out of limits, with a message naming the limit, when weight exceeds the maximum or the CG is outside the limits. Limits are inclusive. |
| SR-PERF-003 | `takeoff_distance_ft` shall interpolate linearly in weight, pressure altitude, and temperature between table points. |
| SR-PERF-004 | Inputs outside the table shall raise `ValueError` naming the axis. The function shall not extrapolate. |

**Synthetic data.** `data/takeoff_table.csv` with header `weight_lb,pressure_alt_ft,temp_c,distance_ft` and a full grid: weights 2000 and 2550 lb, pressure altitudes 0, 4000, 8000 ft, temperatures 0, 20, 40 C. Invent the distances; they must grow with each axis. The aircraft is the fictional "SR-TRAINER": maximum takeoff weight 2550 lb, CG limits 35.0 to 47.3 in.

**Public interface** (`skyroute/performance.py`):

```python
MAX_TAKEOFF_WEIGHT_LB = 2550.0
CG_LIMITS_IN = (35.0, 47.3)

@dataclass(frozen=True)
class LoadItem:
    name: str
    weight_lb: float
    arm_in: float

@dataclass(frozen=True)
class WeightBalance:
    total_weight_lb: float
    total_moment_lbin: float
    cg_in: float
    within_limits: bool
    messages: tuple[str, ...]

def weight_and_balance(items: list[LoadItem], max_weight_lb: float = MAX_TAKEOFF_WEIGHT_LB,
                       cg_limits_in: tuple[float, float] = CG_LIMITS_IN) -> WeightBalance: ...
def load_takeoff_table(path: str | None = None) -> dict[tuple[float, float, float], float]: ...
def takeoff_distance_ft(weight_lb: float, pressure_alt_ft: float, temp_c: float,
                        table: dict[tuple[float, float, float], float] | None = None) -> float: ...
```

**Files owned.** `skyroute/performance.py`, `data/takeoff_table.csv`, `tests/test_performance.py`, `requirements/w3.json`.

**Tests.** `tests/test_performance.py`: CG by hand for three items, each limit edge (inclusive), an exact table point, a midpoint on each axis, a point inside all three axes, and each axis out of range.

**Done.** `python3 -m unittest tests.test_performance` passes; `python3 tools/mission_status.py --verify W3` prints `Result: PASS`; every SR-PERF requirement lists at least one test ID.

### W4 Alternates

**Depends on.** W1 (`Metar`, `flight_category`, `load_metars`). Start only after W1 is done.

**Goal.** Choose alternate airports for a destination from airports in the navigation data, by weather and distance.

**Requirements to add** (`requirements/w4.json`):

| ID | Text |
|----|------|
| SR-ALT-001 | Candidates shall be airport (`AP`) records other than the destination within the maximum distance (default 400 NM). |
| SR-ALT-002 | A candidate shall be accepted only when it has a METAR and its flight category is in the accepted set (default VFR and MVFR). |
| SR-ALT-003 | Alternates shall be ordered by distance, then by ident. |

**Public interface** (`skyroute/alternates.py`):

```python
@dataclass(frozen=True)
class Alternate:
    ident: str
    distance_nm: float
    category: str

def select_alternates(destination: str, metars: dict[str, Metar], max_distance_nm: float = 400.0,
                      accepted: tuple[str, ...] = ("VFR", "MVFR"),
                      navdata_path: str | None = None) -> list[Alternate]: ...
```

Use `skyroute.navdata.load` and `skyroute.geo.distance_nm`. An unknown destination raises `ValueError`.

**Files owned.** `skyroute/alternates.py`, `tests/test_alternates.py`, `requirements/w4.json`.

**Tests.** `tests/test_alternates.py`: KDVT finds KPHX; distance cutoff; category filter; missing METAR; ordering ties; unknown destination. Build `Metar` values in the test with `parse_metar` so the test does not depend on `data/metar.txt` contents.

**Done.** `python3 -m unittest tests.test_alternates` passes; `python3 tools/mission_status.py --verify W4` prints `Result: PASS` (it also runs the W1 tests); every SR-ALT requirement lists at least one test ID.

### W5 Briefing package

**Depends on.** The public interfaces of W1, W2, W3, and W4. Start only after all four are done.

**Goal.** Build one pre-flight briefing from a route and render it as plain text and as a single self-contained HTML page.

**Requirements to add** (`requirements/w5.json`):

| ID | Text |
|----|------|
| SR-BRF-001 | The briefing shall contain route, distance, ETE, fuel plan, departure and destination weather with flight category, active route NOTAMs, weight and balance, takeoff distance at the departure, and alternates for the destination. |
| SR-BRF-002 | The HTML rendering shall escape every data value. |
| SR-BRF-003 | Text and HTML shall carry the same facts and shall be identical for identical inputs. The briefing time is an input, never read from the clock. |
| SR-BRF-004 | Missing weather for the departure or destination shall show a `NO WEATHER` warning instead of raising. |

**Public interface** (`skyroute/briefing.py`):

```python
@dataclass(frozen=True)
class Briefing:
    route: list[str]
    distance_nm: float
    ete_hours: float
    fuel: FuelPlan
    weather: dict[str, Metar | None]      # departure and destination
    categories: dict[str, str]            # ident -> category or "NO WEATHER"
    notams: list[Notam]
    weight_balance: WeightBalance
    takeoff_distance_ft: float | None
    alternates: list[Alternate]
    issued_at: datetime
    warnings: list[str]

def build_briefing(route_idents: list[str], groundspeed_kt: float, burn_lb_per_hr: float,
                   at: datetime, load: list[LoadItem], *, metar_path: str | None = None,
                   notam_path: str | None = None, navdata_path: str | None = None,
                   takeoff_table_path: str | None = None) -> Briefing: ...
def render_text(briefing: Briefing) -> str: ...
def render_html(briefing: Briefing) -> str: ...
```

Takeoff distance uses the departure elevation as pressure altitude and the departure METAR temperature. When either is outside the table, record a warning and set `takeoff_distance_ft` to `None`.

**Files owned.** `skyroute/briefing.py`, `tests/test_briefing.py`, `requirements/w5.json`.

**Tests.** `tests/test_briefing.py`: every SR-BRF-001 section present in both renderings, an injected `<script>` in a NOTAM text comes out escaped, two renders are identical, a station with no METAR shows `NO WEATHER`.

**Done.** `python3 -m unittest tests.test_briefing` passes; `python3 tools/mission_status.py --verify W5` prints `Result: PASS` (it also runs the W1 to W4 tests); every SR-BRF requirement lists at least one test ID.

### W6 Assurance

**Runs.** In two milestones. Tooling: W6 starts in wave 1 with W1, W2, and W3 and builds the tooling against the baseline requirements; when it is verified and committed, its board row is `tooling done`. Final pass: after W5 is `done` and the commander has merged the fragments, the commander launches a fresh W6 engineer to produce the evidence pack; when that is verified and committed, the row is `done`.

**Goal.** Keep requirements, tests, and evidence consistent: merge fragments, build the trace matrix, and assemble the evidence pack.

**Requirements to add** (`requirements/w6.json`):

| ID | Text |
|----|------|
| SR-ASR-001 | `merge_requirements` shall add fragment requirements to the base set and shall raise `ValueError` naming the ID when two definitions of one ID differ. |
| SR-ASR-002 | `trace_matrix` shall list every requirement with its tests and a status: `traced` (every listed test exists), `untested` (no tests), or `missing test` (a listed test does not exist). |
| SR-ASR-003 | The evidence pack shall contain `docs/evidence/README.md`, `docs/evidence/trace-matrix.md`, and `docs/evidence/test-run.txt`. |

**Public interface** (`skyroute/assurance.py`):

```python
@dataclass(frozen=True)
class TraceRow:
    requirement_id: str
    component: str
    tests: tuple[str, ...]
    status: str                  # "traced" | "untested" | "missing test"

def load_fragments(directory: str = "requirements") -> list[dict]: ...      # requirements/w*.json
def merge_requirements(base: dict, fragments: list[dict]) -> dict: ...
def trace_matrix(requirements: dict, test_ids: set[str]) -> list[TraceRow]: ...
def render_trace_matrix(rows: list[TraceRow]) -> str: ...                   # Markdown table
def main(argv: list[str] | None = None) -> int: ...
```

Command line: `python3 -m skyroute.assurance merge` prints the merged JSON; `merge --write` writes `requirements/requirements.json` (only the commander runs this); `matrix --out docs/evidence/trace-matrix.md` writes the matrix using test IDs found by `unittest` discovery.

**Files owned.** `skyroute/assurance.py`, `tests/test_assurance.py`, `requirements/w6.json`, everything under `docs/evidence/` (the final pass writes `docs/evidence/README.md`, `docs/evidence/trace-matrix.md`, and `docs/evidence/test-run.txt`).

**Tests.** `tests/test_assurance.py`: merge adds, merge accepts identical duplicates, merge rejects a conflict by ID, each matrix status, Markdown output for two rows. Tests write only to temporary directories.

**Done.** Tooling done: `python3 -m unittest tests.test_assurance` passes; `python3 tools/mission_status.py --verify W6` prints `Result: PASS`; every SR-ASR requirement lists at least one test ID. Done after the final pass: `python3 tools/mission_status.py --verify W6 --final` prints `Result: PASS`, which needs all three evidence files, a matrix with no `missing test` rows, and a green full suite; every SR requirement from W1 to W6 appears in the matrix.

## Dependency order

| Wave | Workstreams | Starts when |
|------|-------------|-------------|
| 1 | W1, W2, W3, W6 (tooling) | Mission launch (Phase 1). All four in parallel. |
| 2 | W4 | W1 is done |
| 3 | W5 | W1, W2, W3, and W4 are done |
| 4 | W6 (final pass) | W5 is done and the commander has merged the fragments |

## Phases

**Phase 1 (Day 1 morning).** Waves 1 to 3. The commander launches W1, W2, W3, and W6 in parallel in the background, then W4 when W1 is done, then W5 when W1 to W4 are done. The commander verifies and commits each finished workstream. Phase 1 ends when W1 to W5 are `done` or `blocked` and W6 is `tooling done` or `blocked`. Whenever no workstream is in progress, the commander runs the full suite.

**Phase 2 (launched at the end of Day 1).**

1. Integration. The commander writes the integration glue, the only code it writes: `skyroute wx` (decode and categorize one station or all stations) and `skyroute brief` (text or HTML briefing to stdout or a file) in `skyroute/cli.py`, with tests in `tests/test_cli.py`. It runs the full suite before it commits, when no engineer is running.

   `skyroute brief --route <idents> --gs <kt> --burn <lb/hr> --at <UTC time> --format text|html [--out <file>] [--load NAME:WEIGHT_LB:ARM_IN ...]`. Each `--load` adds one `LoadItem`; when there is none, the CLI uses this fixed synthetic load (2310 lb, CG 39.86 in):

   | Item | Weight (lb) | Arm (in) |
   |------|-------------|----------|
   | empty aircraft | 1650 | 39.0 |
   | pilot | 190 | 37.0 |
   | passenger | 170 | 37.0 |
   | fuel | 300 | 48.0 |
2. Review. The commander launches `mission-reviewer` on each finished workstream, one at a time or in parallel.
3. Fix rounds. For each finding the commander launches a fresh engineer for that workstream with the finding and the original workstream brief.
4. Merge. The commander runs `python3 -m skyroute.assurance merge --write` and commits `requirements/requirements.json`.
5. Evidence. The commander launches the final W6 pass, then runs `python3 tools/mission_status.py --verify W6 --final`. The full suite is green; `docs/evidence/` is complete; W6 is `done`.

## Mission done criteria

- `python3 -m unittest` passes: every baseline test plus every new test.
- Every workstream row on `mission/BOARD.md` is `done` (W6 after its final pass).
- `requirements/requirements.json` holds every SR-WX, SR-NTM, SR-PERF, SR-ALT, SR-BRF, and SR-ASR requirement, each with at least one test ID.
- `docs/evidence/trace-matrix.md` has no `missing test` rows.
- `python3 -m skyroute brief --route KDVT,ZUNIX,KMSP --gs 450 --burn 2400 --at 2026-11-01T12:00Z --format html` prints one HTML page.
- `git log` shows one or more commits per workstream, made by the commander.
