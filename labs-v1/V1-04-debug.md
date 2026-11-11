# Lab 4: Debug

**Time:** 25 min  **You will:** debug a failing test with hypotheses and an experiment before any fix.

## Steps

1. **See the failure** in T2:

   ```bash
   python -m unittest tests.test_route
   ```

   **Check:** `FAIL: test_total_distance_includes_every_leg`, `60.04... != 120.081`. The result is exactly one leg.

2. **Hypotheses, no fix.** `/new`, **Plan**. Send:

   ```text
   tests.test_route.RouteTests.test_total_distance_includes_every_leg fails:
   60.04 != 120.081. Do not fix anything. Give up to three hypotheses, ranked.
   For each: file:line evidence and one experiment that confirms or rules it out
   without changing files. Use only files under labs/skyroute.
   ```

   **Check:** the top hypothesis is the loop `range(len(self.fixes) - 2)` in `total_distance_nm`, `skyroute/route.py` around line 55.

3. **Run the experiment yourself** in T2:

   ```bash
   python -c "from skyroute.navdata import Fix; from skyroute.route import Route; r = Route([Fix('WP','A',0,0), Fix('WP','B',0,1), Fix('WP','C',0,2)]); print(len(r.legs()), sum(l.distance_nm for l in r.legs()), r.total_distance_nm())"
   ```

   **Check:** `2 120.08... 60.04...`. Two legs sum correctly; the total counts one. The loop bound is the cause.

4. **Smallest fix.** **Tab** to **Build**. Send:

   ```text
   Fix the cause we confirmed with the smallest change to skyroute/route.py.
   Do not edit any test. Run python -m unittest and show the result line.
   ```

   **Check:** in T2, `python -m unittest` ends with `OK`. `git diff --stat` lists only `skyroute/route.py`.

5. **Check what a user sees**, then commit:

   ```bash
   python -m skyroute plan --route KDVT,ZUNIX,KMSP --gs 450 --burn 2400
   git commit -am "Lab 4: include every leg in total distance"
   ```

   **Check:** `Total distance:   1101.5 NM` (it was `187.2 NM`).

## Stretch

Run `python -m skyroute plan --route KDVT,ZUNIX,KMSP --gs 420 --burn 2400 --alt FL35O`. Paste the traceback into **Plan** and ask for the owning file:line and the smallest check that proves it. Expected: `skyroute/report.py:17`.
