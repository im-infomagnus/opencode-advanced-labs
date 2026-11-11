# Lab 6: Commands and skills

**Time:** 30 min  **You will:** turn a prompt you repeat into a `/command`, and package a checklist as a skill.

## Steps

1. **Create a command.** In `labs/skyroute`, create `.opencode/commands/test-gaps.md`:

   ```markdown
   ---
   description: List requirements in a component that no test covers
   agent: plan
   ---
   Read requirements/requirements.json and the files in tests/.
   For each requirement whose component is $ARGUMENTS, say which test covers it, or NONE.
   Table: requirement ID, ten-word summary, covering test or NONE. Do not edit.

   Current test result:
   !`python -m unittest 2>&1`
   ```

   `$ARGUMENTS` is what you type after the command. `` !`...` `` runs a shell command and puts its output in the prompt.

2. Restart OpenCode. Type `/test-gaps skyroute/navdata.py`.

   **Check:** `/test-gaps` appears in the command list, and the answer is a table for the `SR-NAV` requirements.

3. **Create a skill.** Create `.opencode/skills/secure-review/SKILL.md`:

   ```markdown
   ---
   name: secure-review
   description: Security review checklist for SkyRoute Python code. Use when asked to review code for security.
   ---
   # Secure review

   Check each item. Report file:line, CWE ID, attack path, smallest fix.
   - CWE-22: file paths built from input must stay inside the target directory.
   - CWE-78: no shell=True or os.system with input.
   - CWE-95: no eval or exec.
   - CWE-502: no pickle on data from files or the network.
   - CWE-798: no credentials in code; read them from the environment.
   Never print a secret value. Give file and line only.
   ```

   The folder name must match `name`.

4. Restart OpenCode. `/new`, **Plan**. Send:

   ```text
   Review skyroute/navdata.py for security issues.
   ```

   **Check:** the session shows the `secure-review` skill being loaded, and findings use the checklist format.

5. Commit: `git add .opencode && git commit -m "Lab 6: command and skill"`.

## Stretch

Add a command `/fix-test <test id>` that runs the test, asks for hypotheses, and stops before editing.
