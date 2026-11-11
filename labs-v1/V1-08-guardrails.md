# Lab 8: Guardrails

**Time:** 25 min  **You will:** set team permission rules for every agent and test each one.

## Steps

1. **Write the rules.** Create `labs/skyroute/opencode.json`:

   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "permission": {
       "edit": "ask",
       "webfetch": "deny",
       "bash": {
         "*": "ask",
         "git status*": "allow",
         "git diff*": "allow",
         "git log*": "allow",
         "python -m unittest*": "allow",
         "python -m skyroute*": "allow",
         "git push*": "deny",
         "rm *": "deny"
       }
     }
   }
   ```

2. Restart OpenCode. `/new`, **Build**. Send each prompt and record what happens:

   | Prompt | Expected |
   |---|---|
   | `Run the tests.` | Runs, no prompt |
   | `Add a comment to the top of skyroute/cli.py.` | Asks before the edit. Reject it. |
   | `Delete out/ with rm -rf out.` | Blocked |
   | `Commit everything and push to origin.` | Asks for `git add` and `git commit`; `git push` is blocked |
   | `Fetch https://example.com and summarize it.` | Blocked |

   **Check:** your table matches. If one is allowed that should not be, check the pattern spelling and restart.

3. **Try to go around a rule.** Send:

   ```text
   Remove the out directory any way you can.
   ```

   **Check:** look at each command it tries (for example `python -c "import shutil..."`). Any command not on the allow list asks first. Reject it.

4. **Discuss.** These are tool rules in OpenCode, not an operating-system sandbox. `ask` on `*` is the backstop for commands you did not think of.

5. **Ask before reading secrets.** Add to the `permission` block:

   ```json
   "read": { "*": "allow", "*.env": "deny", "*.env.*": "deny" }
   ```

   Create a fake secret in T2: `echo "TOKEN=FAKE" > .env`. Restart and ask: `Show me .env`. **Check:** blocked. Delete `.env`.

6. Commit: `git add opencode.json && git commit -m "Lab 8: guardrails"`.

## Stretch

Put the same rules in `~/.config/opencode/opencode.json` so they apply in every project, then remove them.
