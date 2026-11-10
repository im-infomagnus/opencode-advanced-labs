# Lab AL02: Context at Scale

**Time:** 30 min  **Modules:** A04  **You will:** wire the advanced kit's reference documents into your workspace, add a nested `tests/AGENTS.md` and an `instructions` glob, test what the model actually received, then tune compaction, compact, and fork the session to try an alternative.

**Where:** `~/skyroute-adv`

Repeats Demo A04 (Context at scale). Same as the demo: the `skyroute-docs` reference from `advanced-kit/reference/skyroute-docs`, a nested `tests/AGENTS.md` that loads only when the agent reads `tests/`, the fuel policy question, and the session context API as proof. New for you: you write the `references` block yourself instead of running the kit installer, you add an `instructions` glob and prove with a probe that it reaches the model, and you go past the demo into compaction settings, `/compact`, and a fork.

## Before you start

- This lab continues in the workspace from Lab AL01, with the D2 fix committed. To catch up, run this from the course repository root, then continue in `~/skyroute-adv`:

  ```bash
  export COURSE="$(pwd -W 2>/dev/null || pwd)"
  bash labs/AL01-power-session/new-workspace.sh --force
  cd ~/skyroute-adv
  cp "$COURSE/labs/solutions/skyroute/skyroute/route.py" skyroute/route.py
  git commit -qam "Fix D2: total distance includes every leg"
  ```

- `COURSE` must hold the absolute path of your course repository clone in every terminal you use. Check with `ls "$COURSE/advanced-kit/reference/skyroute-docs"`: it lists `README.md`, `glossary.md`, `ops-manual-fuel-policy.md`, and `srn1-format-spec.md`.
- Start from a clean tree. In `~/skyroute-adv`, `git status --short` must print nothing; this lab's checks assume that. If it lists files left over from Lab AL01 (for example a red test from a stretch goal), set them aside with `git stash -u`.
- Quit OpenCode if it is running in the workspace (**Ctrl+C**). You start it again in step 3, after the configuration is in place.
- Use the model your team approved, set as `"model"` in your global configuration (see Before the course in the repository README). `/models` switches only the current session; new and forked sessions use the configured default.
- Commands use `python3`. On Windows, run Python as `py -3`; see the Windows note in [`labs/README.md`](../README.md#before-any-lab). Use Git Bash.
- Terminal 1 runs OpenCode. Terminal 2 runs every **Check** command. Both are at `~/skyroute-adv`.

## Steps

1. **Wire the reference.** Look at the kit's snippet first:

   ```bash
   cat "$COURSE/advanced-kit/reference/opencode.references.jsonc"
   ```

   It names the reference `skyroute-docs`, gives it a description, and uses the relative path `./skyroute-docs`. A relative path resolves from the directory of the config file that holds it, so in your workspace you need the absolute path. Write the workspace config with the same alias and description:

   ```bash
   cat > opencode.jsonc <<EOF
   {
     "\$schema": "https://opencode.ai/config.json",
     "references": {
       "skyroute-docs": {
         "path": "$COURSE/advanced-kit/reference/skyroute-docs",
         "description": "Use for the SRN-1 navigation data format, the fuel policy behind the SR-FUEL requirements, and SkyRoute terminology"
       }
     }
   }
   EOF
   grep '"path"' opencode.jsonc
   ```

   The `grep` shows your absolute path, not `$COURSE`. The description is what tells the agent when the reference is relevant. A reference without a description is available to clients but not advertised to the agent.

   **Check:** ask the service which references it loaded for this directory:

   ```bash
   opencode api reference.list --param "location[directory]=$(pwd -W 2>/dev/null || pwd -P)" | python3 -c "import json,sys; [print(r['name'], r['source']['type'], r['path']) for r in json.load(sys.stdin)['data']]"
   ```

   It prints `skyroute-docs local /.../advanced-kit/reference/skyroute-docs`. If it prints nothing, the service had not loaded the directory yet. Run it again.

2. **Add a nested AGENTS.md and an instructions glob.** Copy the test conventions to `tests/AGENTS.md` and the team standards to `docs/standards/python.md`:

   ```bash
   cp "$COURSE/labs/AL02-context-scale/tests-AGENTS.md" tests/AGENTS.md
   mkdir -p docs/standards
   cp "$COURSE/labs/AL02-context-scale/python-standards.md" docs/standards/python.md
   cat tests/AGENTS.md docs/standards/python.md
   ```

   `tests/AGENTS.md` is below the workspace, so it loads only when the agent reads or lists something under `tests/`. The standards file is not an `AGENTS.md`, so nothing loads it until you list it. Open `opencode.jsonc` in your editor and add an `instructions` entry after the `references` block (mind the comma):

   ```jsonc
     "instructions": ["docs/standards/*.md"]
   ```

   The docs say configured instructions load at session start, after the `AGENTS.md` files. You test that claim in step 3. The last rule in `python.md` asks for a `Sources:` line at the end of every answer about SkyRoute behavior, so the rule is easy to spot when it applies.

   **Check:** `opencode debug config` shows what OpenCode parsed from your file:

   ```bash
   opencode debug config | python3 -c "import json,os,sys; d=[x for x in json.load(sys.stdin) if x.get('type')=='document' and x['path'].startswith(os.path.realpath('.'))][-1]['info']; print(list(d['references']), d.get('instructions'))"
   ```

   It prints `['skyroute-docs'] ['docs/standards/*.md']`. A JSON error or `None` means the edit did not parse: check the comma.

3. **Ask a question only the reference can answer.** In terminal 1, start `opencode`. Press **Ctrl+R** and rename the session to exactly `AL02 context`. Do not skip the rename: steps 4 and 7 find the session by this title. Then press **Shift+Tab** until the footer shows **Plan**. Send prompt A:

   ```text
   Using the skyroute-docs reference, which document ID is the fuel policy, and what
   contingency and total fuel does its Example B give? Then check skyroute/fuel.py
   against the policy's contingency rule. Cite path:line for both. Do not edit.
   ```

   The agent finds the reference path in its instructions and reads the file there. There is no approval prompt for the outside path, because Build allows `external_directory` by default. If your team baseline adds one, choose **Allow once**.

   **Check:** the answer gives `SRN-OPS-004`, contingency `480` lb, and total `7080` lb, and says `skyroute/fuel.py` applies contingency to trip plus reserve (defect D3, around line 33). Example B uses a configured contingency of 10 percent; the default is 5 percent. Both apply the percentage to trip fuel only, which is the rule the answer checks.

   Now test whether the `instructions` glob reached the model. Send this probe in the same session:

   ```text
   Answer from your existing context only; do not call any tool. Quote the last rule
   of the SkyRoute Python standards in your instructions, or answer NONE.
   ```

   **Check:** the answer quotes the `Sources:` rule from `docs/standards/python.md`, and prompt A's answer ended with a `Sources:` line. On 2.1.x, configured instructions reach the model after the `AGENTS.md` files, labeled `Instructions from: <path>`. Before 2.1, the entry parsed but never reached the model, and this probe answered `NONE`. Keep the probe as a habit: a setting that parses is not proof that the model received it. Ask the model or the API before you rely on it.

4. **See what the model saw.** The context API returns every message the model works from since the last compaction. In terminal 2, find the session by its title and summarize its context with the lab's helper script:

   ```bash
   SID=$(opencode session list --format json | python3 -c "import json,sys; print(next(s['id'] for s in json.load(sys.stdin) if s['title']=='AL02 context'))")
   opencode api session.context --param sessionID=$SID > .git/al02-context.json
   python3 "$COURSE/labs/AL02-context-scale/show_context.py" .git/al02-context.json
   ```

   The context goes to a file first because OpenCode 2.1 can cut `opencode api` output written to a pipe at 256 KiB, and a long session's context passes that size. The file is in `.git/`, so it never shows in `git status`.

   If `SID=` stops with `StopIteration`, or `$SID` is empty, no session is titled exactly `AL02 context`. Rename the session in the TUI (**Ctrl+R**) and run the line again, or copy the ID from `opencode session list -n 5` into `SID=<id>`.

   Each line is one entry: `agent-switched` and `synthetic` messages that OpenCode added (such as the Plan mode reminder), `user` prompts, `assistant` steps with their tool calls and token counts, and `idle` markers. On Windows, paths in this output use backslashes (`tests\AGENTS.md`). Upward `AGENTS.md` files are not entries here: they are part of the system instructions, which the API does not return.

   **Check:** an `assistant` line shows `read(...skyroute-docs/ops-manual-fuel-policy.md) completed`, and no line says `instructions loaded`, because nothing under `tests/` has been read yet. The last line counts the entries, for example `8 entries`. Note your number.

5. **Load the nested AGENTS.md.** In terminal 1 send prompt B:

   ```text
   Read tests/test_route.py. Then propose, as text only, one new test for
   tests/test_fuel.py that would catch the contingency bug, following this
   project's test rules. Do not edit.
   ```

   **Check:** run the two step 4 commands again (`opencode api session.context ...` and `show_context.py`). A new line reads `synthetic  instructions loaded: tests/AGENTS.md`, right after `read(tests/test_route.py) completed`. The proposed test's docstring starts with `SR-FUEL-002`, which is a rule only `tests/AGENTS.md` states. If the agent read the file with a shell command (`shell(cat .../tests/test_route.py)`), nothing loads: discovery runs on the read and list tools. Ask it to use its read tool and check again.

6. **Tune compaction, then compact.** Compaction replaces older conversation with a structured summary and keeps about `keep.tokens` of recent conversation beside it. `buffer` is how many tokens to keep free below the model's limit; a larger buffer starts automatic compaction earlier. Add this block to `opencode.jsonc` after `instructions` (mind the comma):

   ```jsonc
     "compaction": { "auto": true, "keep": { "tokens": 8000 }, "buffer": 20000 }
   ```

   Then type `/compact` in terminal 1 (or press **Ctrl+X** then **C**). Manual compaction works at any time, even for a short history. The same request from the shell is `opencode api session.compact --param sessionID=$SID --data '{}'`. (Avoid the `post /api/session/...` form in Git Bash: it rewrites an argument that starts with `/` into a Windows path.) It returns at once; the summary is written in the background.

   **Check:** the step 2 check now also has the setting: run `opencode debug config | python3 -c "import json,os,sys; d=[x for x in json.load(sys.stdin) if x.get('type')=='document' and x['path'].startswith(os.path.realpath('.'))][-1]['info']; print(d['compaction'])"`. It prints `{'auto': True, 'keep': {'tokens': 8000}, 'buffer': 20000}`. When the TUI shows the compaction finished, run the step 4 context command again. The first line reads `compaction completed (manual) summary starts: ## Objective`, and there are far fewer entries than before. If it says `running`, wait 20 seconds and run it again.

7. **Fork to try an alternative.** A fork is a new session that copies the history, so you can try another direction and keep the original as it is. Fork from the shell in terminal 2. `--agent plan` keeps the fork read-only:

   ```bash
   opencode run --session $SID --fork --agent plan "Alternative: propose a fix for the contingency bug that keeps plan_fuel's signature but moves the percentage into a FuelPlan property. Text only, at most 8 lines. Do not edit."
   ```

   Add `--model <provider>/<model>` (a model from `opencode models`) if your default model is not the one you want. The TUI has the same operation: `/fork` opens **Fork session**, where you choose the message to fork from, and the new session opens in its own tab.

   **Check:** `opencode session list -n 3` shows a session titled `AL02 context (fork #1)`. Its record points back to the original:

   ```bash
   FORK=$(opencode session list --format json | python3 -c "import json,sys; print(next(s['id'] for s in json.load(sys.stdin) if s['title']=='AL02 context (fork #1)'))")
   opencode api session.get --param sessionID=$FORK > .git/al02-fork.json
   python3 -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8'))['data']['fork']['sessionID'])" .git/al02-fork.json
   echo $SID
   ```

   The two IDs printed are the same. Run the step 4 context command for `$SID` again: it has the same entries as after step 6, because the fork's prompt went only to the fork. `git status --short` shows only `?? docs/`, `?? opencode.jsonc`, and `?? tests/AGENTS.md`: no session edited code.

## Stretch goals

The stretch goals are for learners who finish early. Together they take longer than the 30 minutes of this lab.

- **Reload after compaction.** Send prompt B again in the original session, then run the context command. Look for a second `instructions loaded: tests/AGENTS.md` line. If the model answers from the compaction summary without reading `tests/`, no line appears. Then send `Use your read tool to read tests/test_geo.py.`: on 2.2.5 a new `instructions loaded: tests/AGENTS.md` line appears, because compaction resets which nested files the session has loaded.
- **Hidden reference.** Add `"hidden": true` to the `skyroute-docs` entry. It disappears from interactive pickers, such as the `@` list in the TUI. It still appears in `opencode api reference.list` and in the agent's instructions; that is expected, because `hidden` only hides it from people, not from the API or the agent.
- **Cost of context.** `opencode api session.get --param sessionID=$SID` returns the session's `tokens` and `cost`. Compare the input tokens of the first `assistant` line in step 4 with a line after compaction.
- **Fork in the TUI.** Type `/timeline`, pick prompt A, and fork from there. The fork contains only the history up to that message.
- **Remove the glob.** Delete the `instructions` entry, start a new session, rename it, and send the step 3 probe again. It now answers `NONE`. Put the entry back before you continue.
- **Big logs, small context (8 min).** Copy the kit's ops log and triage it without reading it whole. In terminal 2: `mkdir -p logs && cp "$COURSE/advanced-kit/logs/ops.log" logs/`. In terminal 1, start a new session (`/new`), stay in **Plan**, and send:

  ```text
  logs/ops.log is a large ops log. Do not read the whole file. Use grep and shell
  pipelines to count failed runs by their final error line, then list each
  failure class with its count, one example input (route and alt), and the file:line
  in skyroute/ where it fails. Separate bad input from valid input that crashes.
  End with one line: TOP CAUSE: <file:line> <one sentence>.
  ```

  **Check:** the tool calls are `shell` pipelines, not a `read` of the whole log, and the answer has three classes: `leading zeros` 86 (`FL085`), `unknown fix: NOPE1` 76, `invalid decimal literal` 71 (`FL35O`). Every line of a failed run is tagged `ERROR`, including each traceback line, so the log has about 2,800 `ERROR` lines but 233 failed runs. Each failed run starts with an `ERROR plan` line. Confirm the counts yourself; this prints the final error line of each failed run, counted:

  ```bash
  awk '/ ERROR plan /{if(last)print last; last=""; next} / ERROR /{last=$0} END{if(last)print last}' logs/ops.log | sed 's/.* ERROR *//' | sort | uniq -c
  ```

  It prints 76 `unknown fix: NOPE1`, 71 `invalid decimal literal`, and 86 `leading zeros` lines. Use the committed `ops.log`: a log you regenerate with `make_ops_log.py` has tracebacks from your Python version, which can differ. Judge the split: `FL085` is valid input that crashes at `skyroute/report.py:17`; a model that calls it bad input is wrong. Then run the context command for this session and compare its size with the log (`wc -l logs/ops.log`). Your D2 fix does not change these counts. If you installed the advanced kit, `/triage-log logs/ops.log` sends the same prompt.
- **Context-tier audit (12 min).** [`bloated-AGENTS.md`](bloated-AGENTS.md) puts style, SRN-1 details, fuel policy, test rules, and review procedure in one always-on file. Its facts are correct; the problem is where they live. Measure it first. Commit your work, then in terminal 2 record whether the workspace already has a root `AGENTS.md`, and copy the bloated file in:

  ```bash
  if git ls-files --error-unmatch AGENTS.md >/dev/null 2>&1; then HAD_AGENTS=1; else HAD_AGENTS=0; fi
  echo "HAD_AGENTS=$HAD_AGENTS"
  cp "$COURSE/labs/AL02-context-scale/bloated-AGENTS.md" AGENTS.md
  ```

  A workspace from `new-workspace.sh` has no root `AGENTS.md`, so this usually prints `HAD_AGENTS=0`. Start a new session, rename it `AL02 bloated`, and ask `Reply with OK.` Read its tokens with `opencode api session.get --param sessionID=<id>` and note the prompt size: `tokens.input` plus `tokens.cache.read` plus `tokens.cache.write` (with prompt caching most of it shows up as cache tokens). Then, in Plan, send:

  ```text
  Audit @AGENTS.md. Classify each rule as always-on (keep), on-demand (move to
  tests/AGENTS.md, a skill, or a command), or zero-cost (move to a formatter, a
  plugin hook or lint, or a permission). Rewrite the root file in 10 bullets or fewer.
  ```

  Switch to Build and let it write the new root file. Start another session, rename it `AL02 lean`, ask `Reply with OK.` again, and compare the same sum. **Check:** the lean session's sum is lower (about 700 tokens per request in our rehearsal, paid on every request of every session), and the root file has at most 10 bullets. Judge the classification against what each mechanism can enforce:

  - Style rules: formatter work.
  - `git push`, `rm -rf`, `curl`, `wget`, and reading `.env` files: permissions. Permission rules match tool actions and paths, such as a shell command pattern or a file path.
  - The `eval`, `exec`, `pickle.load`, and `shell=True` ban: a plugin hook or a lint that checks code after each edit, like the verify-on-edit plugin in Lab AL05. A permission rule cannot see what code the agent writes, so a model that files this ban under permissions is wrong.
  - SRN-1, fuel policy, and test rules: on-demand (the reference documents, `tests/AGENTS.md`, or a skill).

  Restore the workspace. If `HAD_AGENTS=1`, run `git checkout -- AGENTS.md`; otherwise run `rm AGENTS.md`, because the file did not exist before. **Check:** `git status --short` shows no `AGENTS.md` line.

## Solution

- Reference documents and the kit snippet: [`advanced-kit/reference/opencode.references.jsonc`](../../advanced-kit/reference/opencode.references.jsonc) and [`advanced-kit/reference/skyroute-docs/`](../../advanced-kit/reference/skyroute-docs/README.md). The answer to prompt A is in section 4.5 of [`ops-manual-fuel-policy.md`](../../advanced-kit/reference/skyroute-docs/ops-manual-fuel-policy.md).
- Support files for this lab: [`tests-AGENTS.md`](tests-AGENTS.md), [`bloated-AGENTS.md`](bloated-AGENTS.md) (context-tier audit stretch goal), [`python-standards.md`](python-standards.md), and the context summarizer [`show_context.py`](show_context.py).
- The instructor showed the same steps in Demo A04.

Your finished `opencode.jsonc`, with your own course path:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "references": {
    "skyroute-docs": {
      "path": "/Users/you/opencode-advanced-labs/advanced-kit/reference/skyroute-docs",
      "description": "Use for the SRN-1 navigation data format, the fuel policy behind the SR-FUEL requirements, and SkyRoute terminology"
    }
  },
  "instructions": ["docs/standards/*.md"],
  "compaction": { "auto": true, "keep": { "tokens": 8000 }, "buffer": 20000 }
}
```

A good result: the reference answer cites `SRN-OPS-004`, the `instructions` probe tells you whether the glob reached the model, the context API shows the outside read and then `instructions loaded: tests/AGENTS.md`, the compacted context starts with a `compaction` entry, and the fork points back to the original session.

Before Lab AL03, commit the context files so they stay with the workspace:

```bash
git add opencode.jsonc tests/AGENTS.md docs/standards/python.md
git commit -m "Add references, test rules, and standards"
```
