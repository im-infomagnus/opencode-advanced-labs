# Mini mission brief: two SkyRoute fixes in parallel

Two independent workstreams. Each one owns its files, and each engineer agent's rules allow edits only to its own files, so both can run at the same time. Python standard library only. Run tests with `python3 -m unittest`. Never weaken an existing test.

Both engineers work test first in one checkout, so the other workstream's tests can be red at any moment. Each workstream is done when its own Done command passes: its test module plus the baseline modules no workstream owns (`tests.test_navdata`, `tests.test_route`). The commander runs the full suite once no workstream is in progress.

## WA Fuel

**Requirement.** SR-FUEL-002 in `requirements/requirements.json`: contingency fuel is the configured percentage (default 5 percent) of trip fuel only.

**Defect.** `plan_fuel` in `skyroute/fuel.py` applies the percentage to trip plus reserve.

**Owned files.** `skyroute/fuel.py`, `tests/test_fuel.py` (new).

**Tests to write first** in `tests/test_fuel.py`, class `FuelTests`:

- `test_contingency_is_percent_of_trip`: `plan_fuel(2.0, 2400)` has contingency 240.0 lb (5 percent of trip 4800).
- `test_total_is_sum_of_parts`: the same plan has total 6240.0 lb (4800 + 240 + 1200).
- `test_contingency_uses_configured_percent`: `plan_fuel(2.0, 2400, contingency_pct=10)` has contingency 480.0 lb.

**Done.** `python3 -m unittest tests.test_fuel tests.test_navdata tests.test_route` ends in `OK`.

## WB Bearing

**Requirement.** SR-GEO-002: the initial bearing is normalized to the range [0, 360).

**Defect.** `initial_bearing_deg` in `skyroute/geo.py` returns negative values for westbound legs.

**Owned files.** `skyroute/geo.py`, `tests/test_geo.py` (add tests; keep every existing test).

**Tests to write first** in `tests/test_geo.py`, class `GeoTests`:

- `test_westbound_bearing_is_normalized`: `initial_bearing_deg(0, 0, 0, -1)` is 270.0 (to 6 places).
- `test_due_north_bearing_is_zero`: `initial_bearing_deg(0, 0, 1, 0)` equals 0.0 exactly, not 360.0.

**Done.** `python3 -m unittest tests.test_geo tests.test_navdata tests.test_route` ends in `OK`.
