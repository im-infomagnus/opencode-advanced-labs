# Lab 10: Plugin and headless

**Time:** 40 min  **You will:** write a plugin that audits and blocks tool calls, then run a review from a script with no TUI.

## Part A: plugin (20 min)

1. Create `labs/skyroute/.opencode/plugins/audit.js`:

   ```js
   import { appendFileSync } from "node:fs";

   export const Audit = async ({ directory }) => ({
     "tool.execute.before": async (input, output) => {
       const line = `${new Date().toISOString()} ${input.tool} ${JSON.stringify(output.args)}\n`;
       appendFileSync(`${directory}/audit.log`, line);

       const path = String(output.args?.filePath ?? "").toLowerCase();
       if (input.tool === "read" && path.includes("navdata.srn")) {
         throw new Error("Blocked by team plugin: navdata is off-limits in this exercise.");
       }
     },
   });
   ```

2. Restart OpenCode. `/new`, **Build**. Send:

   ```text
   Run the tests, then read skyroute/geo.py.
   ```

   **Check:** in T2, `cat audit.log` shows a `bash` line and a `read` line with their arguments.

3. Send:

   ```text
   Read data/navdata.srn and tell me how many fixes it has.
   ```

   **Check:** the read fails with the "Blocked by team plugin" message. The agent may try another way, such as `cat` through bash. Note what it tries: rules for one tool do not cover the others.

4. **Close the gap.** Add this inside the hook, after the `read` check:

   ```js
   if (input.tool === "bash" && String(output.args?.command).toLowerCase().includes("navdata.srn")) {
     throw new Error("Blocked by team plugin: navdata is off-limits in this exercise.");
   }
   ```

   Restart and repeat step 3. **Check:** both paths are blocked.

5. Add `audit.log` to `.gitignore`, then commit: `git add -A . && git commit -m "Lab 10: audit plugin"`.

## Part B: headless review (20 min)

1. Make a change to review in T2: set `DEFAULT_CONTINGENCY_PCT = 10.0` in `skyroute/fuel.py`.

2. Run the reviewer from Lab 7 with no TUI:

   ```bash
   opencode run --agent reviewer "Review the uncommitted changes. Output a markdown list of findings with file:line and the requirement ID they affect." > review.md
   cat review.md
   ```

   **Check:** `review.md` flags the contingency change against `SR-FUEL-002`. `git status` shows no other edits.

3. **Machine-readable output.** Run:

   ```bash
   opencode run --agent reviewer --format json "List the changed files." > review.json
   ```

   **Check:** `review.json` holds JSON events, one per line. Open it and find the final text.

4. **Make it a CI step.** Create `ci-review.sh`:

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   python -m unittest
   opencode run --agent reviewer "Review the diff against main. Markdown list, file:line, requirement ID." > review.md
   grep -q . review.md || { echo "empty review"; exit 1; }
   ```

   Restore the file first (`git checkout -- skyroute/fuel.py`), then run `bash ci-review.sh`. **Check:** the tests run first, then `review.md` is written.

5. Commit: `rm review.md review.json && git add ci-review.sh && git commit -m "Lab 10: CI review"`.

## Stretch

Run `opencode serve --port 4096` in T2 and open `http://localhost:4096/doc` to see the API that scripts and tools use.
