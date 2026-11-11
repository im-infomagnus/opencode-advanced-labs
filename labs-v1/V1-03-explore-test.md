# Lab 3: Explore and test

**Time:** 35 min  **You will:** find untested requirements, write tests that expose two seeded bugs, then fix the code without touching the tests.

## Steps

1. **Map the gaps.** `/new`, **Plan**. Send:

   ```text
   Read requirements/requirements.json. For each requirement whose component is
   skyroute/fuel.py or skyroute/geo.py, tell me whether a test in tests/ checks it.
   Table: requirement ID, the requirement in ten words, covering test or NONE.
   Read the test files yourself. Use only files under labs/skyroute. Do not edit.
   ```

   **Check:** `SR-FUEL-001` to `SR-FUEL-003` are NONE (there is no `tests/test_fuel.py`). `SR-GEO-002` has no westbound bearing test.

2. **Write failing tests.** **Tab** to **Build**. Send:

   ```text
   Write exactly two tests. Do not change skyroute/ or requirements/.
   - tests/test_fuel.py, class FuelTests, for SR-FUEL-002:
     plan_fuel(2.0, 2400) has trip 4800 lb, so 5% contingency is 240 lb.
   - tests/test_geo.py, class GeoTests, for SR-GEO-002:
     bearing from (0, 0) to (0, -1) is 270 degrees.
   Assert literal numbers, with the arithmetic in a comment.
   Run python -m unittest and tell me which tests fail and why.
   ```

   **Check:** in T2, `python -m unittest` shows `300.0 != 240` and `-90.0 != 270`, plus the known route failure. Each new failure is `FAIL`, not `ERROR`.

3. **Explain the numbers.** 300 is 5% of trip plus reserve (6000 lb): the code adds reserve first. -90 is the raw `atan2` result, never normalized to [0, 360).

4. **Commit the tests** in T2:

   ```bash
   git add . && git commit -m "Lab 3: failing tests for SR-FUEL-002 and SR-GEO-002"
   ```

5. **Fix the code.** In **Build**, send:

   ```text
   Make the SR-FUEL-002 and SR-GEO-002 tests pass with the smallest change to
   skyroute/fuel.py and skyroute/geo.py. Do not edit tests/.
   Run python -m unittest and show the result line.
   ```

   **Check:** only `test_total_distance_includes_every_leg` still fails.

6. **Prove it** in T2:

   ```bash
   git diff --stat tests/
   python -m skyroute plan --route KMSP,KBFI --gs 450 --burn 2400
   git commit -am "Lab 3: fix contingency and bearing"
   ```

   **Check:** the first command prints nothing. The plan line reads `KMSP-KBFI       1211.5   288` (it was `-72`).

## Stretch

In **Plan**: `Which tests in tests/test_fuel.py would still pass if plan_fuel returned all zeros?` Strengthen any it names.

## Solution

In the course repository: `labs/solutions/skyroute/skyroute/fuel.py` and `geo.py`, and `labs/solutions/skyroute/tests/test_fuel.py` and `test_geo.py`.
