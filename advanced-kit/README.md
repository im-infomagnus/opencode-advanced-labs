# Advanced kit

The advanced kit extends a SkyRoute workspace for the 2-day advanced course (option `advanced`). It adds four OpenCode plugins, a navigation data MCP server, kit commands, a generated ops log, a set of reference documents, and a fan-out exercise for parallel worktrees. Everything is local files and the Python standard library. The plugins need no `node_modules`.

Tested on OpenCode 2.1.x.

## Contents

| Piece | Path | Used in | What it does |
|-------|------|---------|--------------|
| Verify-on-edit plugin | `plugins/verify-on-edit/index.ts` | A09, AL05 | After `edit`, `write`, or `patch` of a `.py` file, runs `python3 -m py_compile` and the matching `tests/test_<module>.py`, and appends PASS or FAIL to the tool result the model reads |
| Trace tool plugin | `plugins/skyroute-trace/index.ts` | A09, AL05 | Adds the tool `skyroute_trace`: requirement ID to text, listed tests (and whether they exist), and mentions in code and tests. `{ "mode": "gaps" }` lists untested requirements |
| Audit log plugin | `plugins/audit-log/index.ts` | A09, A05 | Appends one JSON line per tool call and permission event to `.opencode/audit/YYYY-MM-DD.jsonl`. Metadata only: which tool ran and its status, and how each permission request was answered, not the command or file |
| AI permission gate | `plugins/ai-gate/index.ts` | A09, AL05 stretch | Asks a second model to allow or deny each shell command. Only tightens. Fails closed |
| Navdata MCP server | `mcp/navdata_server.py` | A07, AL04 | Tools `lookup_fix`, `distance_nm`, `route_legs` over the workspace's own SkyRoute package |
| MCP server tests | `mcp/test_navdata_server.py` | A07, AL04 | Drives the server over stdio, as an MCP client does |
| Lab scaffold | `../labs/AL04-mcp-codemode/navdata_server_scaffold.py` | AL04 | The same server with the three tool bodies left as `TODO(AL04)` |
| Reference documents | `reference/skyroute-docs/` | A04, AL02 | Synthetic SRN-1 format spec, fuel policy excerpt, glossary |
| References snippet | `reference/opencode.references.jsonc` | A04, AL02 | The V2 `references` block that points at the documents |
| Ops log | `logs/make_ops_log.py`, `logs/ops.log` | A04, AL01, AL02 | Deterministic generator for a 400-run SkyRoute ops log, and the log it writes on the starter code: three failure classes, one of them a valid flight level (`FL085`) that crashes |
| Log triage command | `commands/triage-log.md` | A04, AL02 | `/triage-log <path>`: Plan agent counts failure classes with filters and shell pipelines, never reads the whole log, ends with `TOP CAUSE:` |
| Review command | `commands/review-ranked.md` | A06, AL03 | `/review-ranked`: Plan agent reviews the staged diff (injected with `` !`git diff --cached` ``) and ranks findings by severity, category, evidence, smallest fix, and follow-up test |
| Review candidate | `review/review-candidate.patch` | A06, AL03 | Planted-smell change that adds `skyroute/digest.py` and `tests/test_digest.py`; its two tests pass. Apply with `git apply --index` in a standalone SkyRoute workspace (such as `~/skyroute-review` from Demo A06). Inside the course repository it does not reach `labs/skyroute`: from a subdirectory `git apply` prints `Skipped patch`, and from the root it creates stray top-level `skyroute/` and `tests/` folders |
| Fan-out tasks | `fanout/TASKS.md`, `fanout/fanout-prompt.md` | A08, AL06 | Three independent fixes (D1, D3, S1 to S5) and the prompt that runs them in parallel worktrees |
| Kit config | `opencode.advanced.jsonc` | all | Plugin options, a `permissions` deny for edits to `.opencode/audit/`, `mcp.servers.navdata`, `references` |
| Installer | `install-advanced.sh` | all | Copies the kit into a workspace |

## Install into a SkyRoute workspace

The installer does not create the workspace. Start from a Git copy of `labs/skyroute` (add the `labs/solutions/skyroute` overlay when you want all tests green), then run:

```bash
advanced-kit/install-advanced.sh ~/skyroute-adv
```

| Writes | From |
|--------|------|
| `.opencode/plugins/<id>/index.ts` for the four plugins | `plugins/` |
| `.opencode/mcp/navdata_server.py` | `mcp/navdata_server.py` |
| `.opencode/commands/<name>.md` for each kit command | `commands/` |
| `opencode.jsonc`, only when the workspace has no OpenCode config | `opencode.advanced.jsonc`, with the absolute path of `reference/skyroute-docs` filled in |
| `opencode.advanced.jsonc`, when an `opencode.jsonc`, `opencode.json`, or `.opencode/opencode.json(c)` already exists | same |
| One `.opencode/audit/` line in `.gitignore`, when it is not there yet | the audit log is local evidence, not source |

Rules:

- The installer never overwrites an existing `opencode.jsonc`, even with `--force`. When it writes `opencode.advanced.jsonc`, merge its `plugins`, `permissions`, `mcp.servers.navdata`, and `references` blocks into your config by hand. If you installed the starter kit first, this is the path you take.
- Rerunning is safe. Identical files are left alone. A file that differs is replaced only with `--force`, and the old copy is kept as `<file>.bak`. The script exits nonzero when it skipped a file.
- Plugins in `.opencode/plugins/` load automatically with default options, even before you merge the config. The config entries only add options.

## Plugins

Each plugin is one TypeScript file that imports `Plugin` from `@opencode/plugin`. The plugin host is Bun (1.4.2 observed on 2.0.28), and the plugins use only `node:fs`, `node:path`, and `node:child_process`. Set options in the `plugins` list:

```jsonc
{
  "plugins": [
    { "package": "./.opencode/plugins/verify-on-edit", "options": { "timeoutMs": 60000 } }
  ]
}
```

An entry for a plugin that also sits in `.opencode/plugins/` does not load it twice. OpenCode lists it once and passes the options.

### verify-on-edit

Hook: `ctx.tool.hook("execute.after")`. For each completed `edit`, `write`, or `patch` that touched a `.py` file inside the workspace:

1. Runs `python3 -m py_compile <file>` from the workspace root.
2. When it compiles and `runTests` is on, runs `python3 -m unittest tests.test_<module>` for `skyroute/<module>.py` when `tests/test_<module>.py` exists, or for the test file itself.
3. Appends one text part to the tool result, for example:

```text
verify-on-edit: FAIL
py_compile skyroute/geo.py: FAIL
    File "skyroute/geo.py", line 18
  ...
```

The hook never throws. An unexpected error becomes a `verify-on-edit: ERROR` note. Paths come from the tool input (`path`), the result's file list, and, for `patch`, the `*** Add File`, `*** Update File`, and `*** Move to` lines of `patchText`.

| Option | Default | Meaning |
|--------|---------|---------|
| `disabled` | `false` | Do not register the hook |
| `timeoutMs` | `60000` | Limit for each `py_compile` and `unittest` run |
| `runTests` | `true` | Run the matching test module after a clean compile |
| `python` | `"python3"` | Interpreter. Resolved on the OpenCode service PATH, not your shell PATH |

The checks run inside the tool call, so a slow test module slows every edit. Keep the per-module tests fast, or set `runTests` to `false`.

### skyroute-trace

Adds the tool `skyroute_trace` with `ctx.tool.transform`. It reads `requirements/requirements.json` and the files under `skyroute/` and `tests/` on every call.

| Input | Output |
|-------|--------|
| `{ "id": "SR-FUEL-002" }` | Requirement text, component, each listed test with `[ok]`, `[missing module]`, or `[missing method]`, and every line in `skyroute/` and `tests/` that mentions the ID |
| `{ "mode": "gaps" }` | Requirements with no tests, and listed tests that do not exist |

In the starter workspace, `gaps` lists 12 of the 18 requirements: SR-GEO-002, SR-NAV-002, SR-NAV-003, all SR-FUEL, and all SR-RPT. With the solution overlay it lists none.

### audit-log

Subscribes with `ctx.event.subscribe` and aborts the stream in its cleanup function. Writes `.opencode/audit/YYYY-MM-DD.jsonl` (local date) in the workspace.

| Event | Fields kept |
|-------|-------------|
| `session.created` | `time`, `type`, `sessionID` |
| `session.tool.called`, `session.tool.success`, `session.tool.failed` | plus `callID`, `tool`, `status`, and `error` (the error type, such as `permission.rejected`) |
| `permission.asked`, `permission.replied` | plus `requestID`, `action`, `reply` |

It never writes tool input or output, file contents, shell commands, or permission resources, because those can carry secrets. So the log tells a reviewer which tools ran, whether each succeeded, and how each permission request was answered. It does not tell them what a command did or what an edit changed; use Git and the session for that. The event stream carries events for every workspace the service hosts, so the plugin keeps only events for its own directory. It takes the tool name from the `session.tool.input.started` event, because `session.tool.called` does not carry it on 2.1.x.

Writes use `node:fs/promises` in event order, so a slow disk does not block the shared service. If the event stream ends, the plugin subscribes again after 1 second, doubling the wait up to 60 seconds, and logs each retry on the service log. Events published while it is not subscribed are not recorded.

Protection for the log:

- The installer adds `.opencode/audit/` to `.gitignore`.
- The kit config denies the `edit` action for `.opencode/audit/*` and `*/.opencode/audit/*`, so the `edit`, `write`, and `patch` tools cannot change the log.
- It is still a local file. A shell command can change it, and an agent rule that allows `edit` on `*` comes after the kit rule and wins. Ship the files to your log system if you need a tamper-evident record.

### ai-gate

Hook: `ctx.permission.hook("evaluate")`. For each action in `actions` (default `shell`), it sends the command, the action, the agent, and the workspace path to `options.model` through `ctx.generate.text`, with a prompt that asks for exactly `ALLOW: <reason>` or `DENY: <reason>`.

How it combines with your permission rules:

- OpenCode evaluates the configured rules first. The hook runs only when the result is `allow` or `ask`. An explicit `deny` rule is final and the gate never sees it.
- The gate only tightens. `DENY` sets the effect to `deny` and the reason becomes the denial message the model reads. `ALLOW` leaves the rule result alone, so an `ask` still asks a human.
- It fails closed. A timeout, a provider error, or an answer that does not start with `ALLOW` or `DENY` denies the command and says why.
- Enabled without a usable `model`, it denies every action in `actions` with `ai-gate is enabled but has no model; set options.model ... or set disabled: true.` A gate that cannot review does not let commands through unreviewed.
- `allowPatterns` skip the review for known-safe commands, with the same wildcard rules as permission resources. A command that contains `;`, `&`, `|`, `` ` ``, `$`, `<`, `>`, parentheses, a backslash, or a newline is always reviewed. So is a command with an option that writes a file or runs another program, such as `--output`, `--out`, `--archive`, `-o`, `--ext-diff`, `--exec`, or `-c`, because `git diff --output=FILE` matches `git diff *` but writes anywhere. So is a command with a path argument that can leave the workspace: one that starts with `/` or `~`, or has a `..` segment. That is why `python3 -m unittest discover -s /elsewhere` is reviewed even though it matches `python3 -m unittest *`. The guard reads text only; a relative symbolic link that points outside the workspace still passes, so keep `allowPatterns` to commands that only read or run the workspace tests.
- Do not pre-approve a command that writes files, such as `python3 -m skyroute *`: `python3 -m skyroute export --name x` writes a report even without `--out`.

| Option | Default | Meaning |
|--------|---------|---------|
| `model` | none | `{ "providerID": "...", "id": "..." }`. Required unless `disabled` is `true`. Without it the gate denies every action it covers |
| `actions` | `["shell"]` | Permission actions to review |
| `allowPatterns` | `[]` | Commands that skip the review, for example `"git status *"` |
| `timeoutMs` | `30000` | Limit for one review. Local models can need more |
| `disabled` | `false` | Do not register the hook |

The kit config ships the gate with `"disabled": true` and the placeholder model `company-ai/your-model`. Set it to the provider ID and reviewer model your team uses. Set `disabled` to `false` in Lab AL05. On 2.1.x the free `opencode/*` models refuse `generate` outside a session, so with one of them as the reviewer every reviewed command is denied. Use the class provider or a local model.

Each reviewed command costs one model call. Keep `allowPatterns` for the commands the agent runs most, such as the test command.

## Navdata MCP server

`mcp/navdata_server.py` speaks newline-delimited JSON-RPC 2.0 on stdio, like the starter kit's requirements server. It imports `skyroute` from `SKYROUTE_ROOT`, or from its working directory, which for a local MCP server is the workspace root. Answers come from the workspace code, seeded defects included: on the starter code, `route_legs` shows negative bearings (D1).

| Tool | Arguments | Result |
|------|-----------|--------|
| `lookup_fix` | `ident` | kind, name, `lat`, `lon`, `elev_ft`, `freq_mhz` |
| `distance_nm` | `from`, `to` | `distance_nm`, `initial_bearing_deg` |
| `route_legs` | `route`, such as `"KDVT,ZUNIX,KMSP"` | legs with distance and bearing, `sum_of_legs_nm` |

An unknown fix, a missing argument, a one-fix route, or a workspace without SkyRoute returns an `isError` result with a message the model can act on. With Code Mode on (the default), the model reaches the tools through the `execute` tool as `tools.navdata.route_legs({ route: "KDVT,ZUNIX,KMSP" })`, and can combine several calls in one script. Permission actions use the names `navdata_lookup_fix`, `navdata_distance_nm`, and `navdata_route_legs`.

Run the tests from the repository root:

```bash
python3 -m unittest advanced-kit/mcp/test_navdata_server.py
```

## Reference documents

`reference/skyroute-docs/` is synthetic and safe to share. `reference/opencode.references.jsonc` shows the `references` block. A relative `path` resolves from the directory of the config file that holds it, so the installer writes the absolute path into the workspace config. Check what OpenCode loaded:

```bash
cd ~/skyroute-adv && opencode api GET "/api/reference?location%5Bdirectory%5D=$(pwd -P)"
```

## Fan-out

`fanout/TASKS.md` defines three tasks with disjoint file sets. `fanout/fanout-prompt.md` has the prompt that creates one worktree per task with the Code Mode worktree tools and runs one background subagent in each. Read its notes on 2.1.x behavior before class: new worktrees start on a detached HEAD, so each subagent creates its own branch.

## Verify

By hand, in an installed workspace:

| Check | Command | Expect |
|-------|---------|--------|
| Plugins loaded | `opencode api GET "/api/plugin?location%5Bdirectory%5D=$(pwd -P)"` | `verify-on-edit`, `skyroute-trace`, `audit-log`, `ai-gate` with `source.type` `local` and `state.status` `active`. The first call for a new directory can return `[]`; run it again |
| MCP connected | `opencode api GET "/api/mcp?location%5Bdirectory%5D=$(pwd -P)"` | `navdata` with status `connected` |
| Config accepted | `opencode api GET "/api/config?location%5Bdirectory%5D=$(pwd -P)"` | your `opencode.jsonc` with `plugins`, `mcp`, and `references` intact |
| Audit trail | `tail .opencode/audit/*.jsonl` | one line per tool call after a prompt |
