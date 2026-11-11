# Lab 7: Agents

**Time:** 35 min  **You will:** build a read-only reviewer and a test-writer, try to break their limits, and have Build delegate to them.

## Steps

1. **Reviewer.** Create `.opencode/agents/reviewer.md`:

   ```markdown
   ---
   description: Use after code changes to find bugs, regressions, and missing tests. Never edits files.
   mode: subagent
   permission:
     edit: deny
     webfetch: deny
     bash:
       "*": deny
       "git diff*": allow
       "git log*": allow
       "git status*": allow
       "python -m unittest*": allow
   ---
   Review the current changes. List findings by severity with file:line.
   For each, say how to confirm it. Do not fix anything.
   ```

2. **Test-writer.** Create `.opencode/agents/test-writer.md`:

   ```markdown
   ---
   description: Use to add tests for a requirement ID. Edits only files under tests/.
   mode: subagent
   permission:
     edit: allow
     bash:
       "*": deny
       "python -m unittest*": allow
   ---
   Write unittest tests for the requirement you are given. Assert literal values
   worked out from the requirement text. Edit only files under tests/.
   Never change files under skyroute/.
   ```

3. Restart OpenCode. Type `@` and confirm both agents are listed. In T2, `opencode agent list` shows them too.

4. **Use the reviewer.** Make a small change in T2, for example change `DEFAULT_RESERVE_MIN = 30` to `20` in `skyroute/fuel.py`. Then send:

   ```text
   @reviewer review my current changes.
   ```

   **Check:** it runs `git diff`, flags the reserve change against `SR-FUEL-003`, and edits nothing.

5. **Try to break it.** Send:

   ```text
   @reviewer fix the issue you found, then commit it.
   ```

   **Check:** no edit and no commit happen. `git status` still shows only your change. Restore it: `git checkout -- skyroute/fuel.py`.

6. **Delegate.** In **Build**, send:

   ```text
   Use the test-writer agent to add a test for SR-FUEL-003, then use the reviewer
   agent to review the result. Summarize both.
   ```

   **Check:** the session shows two subagent runs. `git status` lists only files under `tests/`.

7. **Close a gap.** `git diff --output=x.txt` writes a file, and `"git diff*"` allows it. Add this line after `"git status*"` in the reviewer:

   ```yaml
       "git diff*--output*": deny
   ```

   Restart and ask `@reviewer run git diff --output=x.txt`. **Check:** it is blocked and `x.txt` does not exist.

8. Commit: `git add -A . && git commit -m "Lab 7: agents"`.

## Stretch

Add a primary agent `docs` (`mode: primary`) that may edit only `*.md` files. Press **Tab** until it appears and try it.
