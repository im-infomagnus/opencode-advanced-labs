# Lab 11: Skills, before and after

**Time:** 35 min  **You will:** ask a custom agent to do two team tasks, add one skill per task, and ask again. One task reads a PDF.

| Task | Skill |
|---|---|
| Turn change request `CR-042` (a PDF) into SkyRoute requirements | `change-request-intake` |
| Write a test plan for a requirement | `test-plan` |

## Steps

1. **Get the change request.** In T2, at `labs/skyroute`:

   ```bash
   mkdir -p docs
   cp ../../labs-v1/lab11/CR-042-fuel-policy.pdf docs/
   ```

   Open `docs/CR-042-fuel-policy.pdf` in a PDF viewer and skim it: four "shall" items, some notes, one example.

2. **Analyst agent.** Create `.opencode/agents/analyst.md`:

   ```markdown
   ---
   description: Reads requirements, change requests, and code, and answers in the team's formats. Never edits.
   mode: all
   permission:
     edit: deny
     task: deny
     webfetch: deny
     bash:
       "*": deny
       "python .opencode/skills/*": allow
   ---
   You are a requirements analyst for SkyRoute. Answer questions about
   requirements, change requests, and tests. Do not edit files.
   ```

3. **Before: ask twice.** Restart OpenCode. Press **Tab** until the footer shows **analyst**. Send:

   ```text
   Read docs/CR-042-fuel-policy.pdf and turn it into requirements for this project.
   ```

   Then `/new`, **Tab** to **analyst**, and send:

   ```text
   Write a test plan for SR-FUEL-002.
   ```

   Note for each answer: Did it read the PDF? Which IDs did it use? What format? Did it separate "shall" from "should"? Does the test plan give literal expected values?

4. **Skill 1: change request intake.** In T2:

   ```bash
   mkdir -p .opencode/skills/change-request-intake/scripts
   cp ../../labs-v1/lab11/pdf_text.py .opencode/skills/change-request-intake/scripts/
   python .opencode/skills/change-request-intake/scripts/pdf_text.py docs/CR-042-fuel-policy.pdf
   ```

   **Check:** the text of both pages prints. Create `.opencode/skills/change-request-intake/SKILL.md`:

   ```markdown
   ---
   name: change-request-intake
   description: Turn a change request (PDF or text) into SkyRoute requirement entries. Use when asked to read, summarize, or extract requirements from a change request, memo, or PDF.
   ---
   # Change request intake

   1. Get the text. For a PDF run
      `python .opencode/skills/change-request-intake/scripts/pdf_text.py <file>`.
      Do not read PDFs with the read tool.
   2. One requirement per "shall" statement. Quote it word for word.
   3. Read requirements/requirements.json. Give each new requirement the next
      free ID in its area (SR-FUEL-004, SR-RPT-007, ...). If the request says it
      replaces an existing ID, reuse that ID and say "replaces".
   4. Answer in exactly this order:
      - `## CR-<number>: <title>`
      - Table: ID | Requirement (verbatim) | Component | New or replaces
      - A JSON block of entries shaped like requirements.json: id, title, text,
        component, verification "test", tests [].
      - `## Not requirements`: each "should", "may", or note, and why.
      - `## Questions`: anything ambiguous, for the request owner.
   5. Do not edit files.
   ```

5. **Skill 2: test plan.** Create `.opencode/skills/test-plan/SKILL.md`:

   ```markdown
   ---
   name: test-plan
   description: Write a SkyRoute test plan for one or more requirement IDs. Use when asked for a test plan, test cases, or how to verify a requirement.
   ---
   # Test plan

   Read the requirement text in requirements/requirements.json and the code it names.
   Answer with exactly:

   `## Test plan: <IDs>`

   | Test ID | Requirement | Input | Expected | Why |

   - Test ID: tests.test_<module>.<Module>Tests.test_<behaviour>
   - Per requirement: one nominal case, one boundary case, one invalid-input case.
   - Expected: a literal value worked out by hand. Show the arithmetic in Why.
     Never "matches the code".
   - Last line: "Trace: add these test IDs to <ID> in requirements/requirements.json."

   Do not write test code. Do not edit files.
   ```

6. **After: ask again.** Restart OpenCode. **Tab** to **analyst**, send the PDF prompt from step 3. Then `/new`, **Tab** to **analyst**, send the test plan prompt.

   **Check, PDF:** the session shows `Skill "change-request-intake"` and the `pdf_text.py` command. The table has one row per "shall": five rows, because item 2.1 holds two. Item 2.2 reuses `SR-FUEL-002` as "replaces". "Reserve should probably be raised" is under **Not requirements** or **Questions**.

   **Check, test plan:** the session shows `Skill "test-plan"`. Every row has a test ID in the team format and a literal expected value, for example 240 lb for 5% of 4800 lb. The last line is the trace line.

7. **Compare.** Fill in:

   | | Before | After |
   |---|---|---|
   | PDF read how? | | |
   | IDs right? | | |
   | Format as asked? | | |
   | "should" separated? | | |
   | Test IDs and literal values? | | |

8. Commit: `git add .opencode docs && git commit -m "Lab 11: analyst and skills"`.

## Why it works

A skill is a folder the agent loads only when its `description` matches the task. The description is the trigger; the body is the procedure; files beside it, like `pdf_text.py`, make a step repeatable. The script turns the PDF into text, so it also works with models that cannot read PDFs.

## Stretch

Change the `description` of `test-plan` to something vague, such as `Testing help.`, restart, and ask for a test plan again. Does the skill still load?
