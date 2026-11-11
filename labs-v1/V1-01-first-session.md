# Lab 1: First session

**Time:** 20 min  **You will:** ask about code, make an edit, undo and redo it.

## Steps

1. In T1, at `labs/skyroute`, run `opencode`. Press **Tab** until the footer shows **Plan**. Send:

   ```text
   What does this project do? List each module under skyroute/ with one line on
   its job. Use only files under labs/skyroute. Do not change any files.
   ```

   **Check:** the answer names `geo`, `fuel`, `route`, `navdata`, `report`, and `cli`.

2. Reference a file with `@`. Type `@skyroute/geo` and pick the file from the list, then finish the prompt:

   ```text
   @skyroute/geo.py Explain distance_nm in three sentences. Which earth radius does it use?
   ```

   **Check:** the answer says 3440.065 NM. Open `skyroute/geo.py` and confirm the value.

3. Run a shell command from the prompt. Type `!python -m unittest` and press Enter.

   **Check:** the output ends with `FAILED (failures=1)`.

4. Press **Tab** to switch to **Build**. Send:

   ```text
   Add a short comment above DEFAULT_RESERVE_MIN in skyroute/fuel.py that
   gives its unit. Change nothing else.
   ```

   **Check:** in T2, `git diff --stat` lists only `skyroute/fuel.py`.

5. Type `/undo`.

   **Check:** `git diff --stat` prints nothing. Your prompt is back in the input box.

6. Type `/redo`.

   **Check:** the comment is back. Run `git checkout -- skyroute/fuel.py` in T2 to drop it.

7. Type `/sessions` to see this session, then `/new` for a clean one.

## Done when

You can switch agents, reference a file, run a shell command, and undo a change.
