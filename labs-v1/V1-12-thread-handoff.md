# Lab 12: Hand off between threads

**Time:** 25 min  **You will:** research in one session, carry its results into a new session, and keep working from them. No subagents: two separate conversations, with a handoff you can read and check.

## Steps

1. **Thread A: research.** In T1, `/new`, **Plan**. Send:

   ```text
   Plan how to add alternate fuel to the fuel plan: alternate fuel is burn rate
   times alternate time, the default alternate time is 45 minutes, and total fuel
   includes it. Read the code and tests first. Answer with a numbered plan: each
   step names the file, the function, and the test to add, and give the expected
   FuelPlan values for plan_fuel(1.0, 2400). Do not edit.
   ```

   **Check:** a numbered plan, and expected values `trip 2400`, `contingency 120`, `alternate 1800`, `reserve 1200`, `total 5520`.

2. **Find thread A.** In T2:

   ```bash
   opencode session list
   ```

   Copy the ID (`ses_...`) of the session whose title is about alternate fuel.

3. **Export it and make a handoff.** In T2, with your ID:

   ```bash
   mkdir -p handoff
   opencode export ses_PASTE_ID > handoff/thread-a.json
   python ../../labs-v1/lab12/thread_to_md.py handoff/thread-a.json > handoff/thread-a.md
   ```

   Open `handoff/thread-a.md`. It keeps the request and the answers and drops tool output, so it is short and holds no file contents.

   **Check:** the plan and the five expected values are in the file.

4. **Thread B: continue.** In T1, `/new`, **Build**. Send:

   ```text
   Read @handoff/thread-a.md. It is the plan and results from another session.
   Do not repeat that research. Implement only the plan steps that change
   skyroute/fuel.py and tests/test_fuel.py, exactly as written. Run
   python -m unittest and show the result line. Then say which plan step each
   change comes from, and confirm plan_fuel(1.0, 2400) matches the values in the
   handoff.
   ```

   Approve the edits if Lab 8's rules ask.

   **Check:** the answer names a plan step for each change. In T2:

   ```bash
   python -m unittest
   python -c "from skyroute.fuel import plan_fuel; p = plan_fuel(1.0, 2400); print(p, p.total)"
   git status --short skyroute tests
   ```

   Tests end `OK`, the plan shows `alternate=1800.0` and total `5520.0`, and only `skyroute/fuel.py` and `tests/test_fuel.py` changed.

5. **Compare.**

   | | Subagent (Lab 7) | Thread handoff (this lab) |
   |---|---|---|
   | Who starts it | The agent | You |
   | What carries over | What the parent passes | What you put in the handoff |
   | Can you read and edit it first? | No | Yes |
   | Can a teammate continue it? | No | Yes, send the handoff file |

6. Commit the work, not the export: `git add skyroute tests && git commit -m "Lab 12: alternate fuel from handoff"`.

## Why it works

Each session is its own conversation with its own context. `opencode export` writes a session as JSON; `thread_to_md.py` keeps only what was asked and answered. Thread B starts clean and reads only the handoff, so it spends its context on the work, not on repeating the research.

## Stretch

Edit `handoff/thread-a.md` before step 4: delete a plan step, or change the default to 30 minutes. Run step 4 in a new session. Does thread B follow your edit?
