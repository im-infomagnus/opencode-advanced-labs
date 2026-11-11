# Lab 2: AGENTS.md

**Time:** 20 min  **You will:** generate project rules, tighten them, and see the agent follow them.

## Steps

1. In OpenCode, at `labs/skyroute`, type `/init`.

   **Check:** `labs/skyroute/AGENTS.md` exists and lists `python -m unittest` as the test command.

2. Open `AGENTS.md` in your editor. Make sure it has these rules; add any that are missing:

   ```markdown
   ## Rules
   - Python 3.10+, standard library only. No third-party packages.
   - Units: nautical miles, knots, feet, pounds, pounds per hour. Put the unit in the name.
   - Bearings are true degrees in [0, 360).
   - Do not use eval, exec, pickle, shell=True, or os.system.
   - Run `python -m unittest` before saying a change is done and show the result line.
   - Never weaken a test to make it pass. Fix the code or explain why the test is wrong.
   - Requirement IDs look like SR-FUEL-002. Do not edit requirement text to match the code.
   ```

   Compare with the reference, or use it as is: `cp ../solutions/skyroute/AGENTS.md AGENTS.md`.

3. Type `/new`. In **Build**, send:

   ```text
   Add a function knots_to_kmh to skyroute/geo.py and install the requests
   package to test it against a web converter.
   ```

   **Check:** the agent refuses the package, cites your rule, and offers a standard-library test instead.

4. Send:

   ```text
   Add a test for knots_to_kmh in tests/test_geo.py, then finish.
   ```

   **Check:** the reply ends with the `python -m unittest` result line, as your rule requires.

5. Drop the experiment and keep the rules:

   ```bash
   git checkout -- skyroute tests
   git add AGENTS.md && git commit -m "Lab 2: AGENTS.md"
   ```

## Done when

`AGENTS.md` is committed and the agent quotes it back to you.
