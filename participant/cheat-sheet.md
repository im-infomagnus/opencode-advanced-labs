# OpenCode v2 cheat sheet

Verified on OpenCode 2.1.x. Model references use the form `<provider>/<model>`. `opencode models` lists yours. In config examples, `company-ai/your-model` is a placeholder for the model your platform team configured. **Ctrl+X** is the leader key: press it, release, then press the next key.

## Start

| Command | Does |
|---------|------|
| `opencode` | Full-screen TUI in the current directory |
| `opencode --continue` | Continue the last session |
| `opencode mini` | Minimal interface |
| `opencode run "<message>"` | One message, no TUI (headless) |
| `opencode auth login [provider]` | Connect a provider (same as `/connect`) |
| `opencode auth list` | Show connected providers |
| `opencode models` | List usable models as `<provider>/<model>` |
| `opencode service status` | Check the background service |

## Keys

| Key | Action |
|-----|--------|
| **Enter** | Send. While the agent works, **Enter** steers the running session. |
| **Shift+Enter** or **Ctrl+J** | New line |
| **Esc** | Interrupt the current run |
| **Ctrl+X** then **Enter** | Queue a prompt for later |
| **Shift+Tab** | Cycle primary agents (`build`, `plan`, custom) |
| **Ctrl+X** then **A** | Pick an agent |
| **Ctrl+X** then **M** | Pick a model. **F2** cycles recent models. **Ctrl+T** cycles variants. |
| **Ctrl+P** | Command palette |
| **Ctrl+X** then **N** / **L** | New session / list sessions |
| **Ctrl+X** then **U** / **R** | Undo / redo |
| **Ctrl+X** then **E** | Edit the prompt in `$EDITOR` |
| **Ctrl+X** then **Q**, or **Ctrl+C** on an empty prompt | Exit |

## In the prompt

| Type | Does |
|------|------|
| `@skyroute/route.py` | Attach a file |
| `@skyroute/route.py#20-45` | Attach lines 20 to 45 |
| `@characterization-testing` | Load a skill by ID |
| `!` on an empty prompt | Shell mode. `!git status` runs it. **Esc** leaves. |
| `/` | List commands |

## Slash commands

`/new` new session. `/sessions` switch session. `/models` switch model for this session. `/agents` pick agent. `/connect` add provider credentials. `/mcps` MCP servers. `/compact` summarize context. `/btw <question>` side question, not added to the conversation. `/undo` and `/redo`. `/editor` external editor. `/init` guided `AGENTS.md` setup. `/review` review uncommitted changes, a commit, a branch, or a PR.

Team kit commands: `/explain <path>`, `/test-gaps <path>`, `/review-diff [focus]`, `/secure-review <path>`, `/modernize <path>`, `/trace <requirement-id or path>`, `/preflight`.

## Agents

| Agent | Mode | Use |
|-------|------|-----|
| `build` | primary, default | Make changes |
| `plan` | primary | Read and plan. No edits except plan files. |
| `general` | subagent | Multi-step research in a child session |
| `explore` | subagent | Search and read code in a child session (can run shell on 2.1.x) |

Kit agents: `reviewer`, `test-writer`, `security-auditor`, `explainer` (subagents); `modernizer`, `orchestrator` (primary). Ask for a subagent by name: "Use the reviewer subagent to review my changes."

`.opencode/agents/reviewer.md`:

```markdown
---
description: Read-only reviewer. Use after code changes.
mode: subagent
model: company-ai/your-model
permissions:
  - { action: edit, resource: "*", effect: deny }
  - { action: shell, resource: "*", effect: deny }
  - { action: shell, resource: "git diff *", effect: allow }
  - { action: shell, resource: "git log *", effect: allow }
  - { action: shell, resource: "git status *", effect: allow }
  - { action: shell, resource: "git *--output*", effect: deny }
  - { action: subagent, resource: "*", effect: deny }
---
Review the changes. Cite path:line for every finding.
```

`git *--output*` blocks `git diff --output=FILE`, which writes a file. The `subagent` deny stops the reviewer from handing work to `general`, which has a full shell.

Fields: `description`, `mode` (`primary`, `subagent`, `all`), `model`, `permissions`, `steps`, `hidden`, `color`, `disabled`. Do not add V1 fields such as `temperature`, `maxSteps`, or `prompt`: on 2.1.x one V1 field makes OpenCode ignore the `permissions` list.

## Permissions

```jsonc
"permissions": [
  { "action": "shell", "resource": "*", "effect": "ask" },
  { "action": "shell", "resource": "git status *", "effect": "allow" },
  { "action": "shell", "resource": "git push *", "effect": "deny" }
]
```

- Effects: `allow`, `ask`, `deny`. **The last matching rule wins.** Global rules first, agent rules appended.
- Actions: `read`, `edit`, `glob`, `grep`, `shell`, `subagent`, `skill`, `question`, `webfetch`, `websearch`, `external_directory`, `<server>_<tool>` (MCP), `execute`.
- `"git status *"` also matches `git status` with no arguments.
- Defaults on 2.1.x: `build` runs shell and edits **without asking**. Only `*.env` and `*.env.*` reads ask. The team baseline (`opencode.jsonc` from the kit) adds the prompts.
- Prompts: **Allow once**, **Always allow** (saves a project rule), **Reject**. A configured `deny` always wins over a saved approval.
- `Blocked by configuration policy` means an admin policy. You cannot approve past it.

## Project instructions

- `AGENTS.md` at the repository root. V2 does not read `CLAUDE.md`.
- Nested `AGENTS.md` files load when the agent works in that folder.
- More files: `"instructions": ["CONTRIBUTING.md", "docs/guidelines/*.md"]`.

## Commands

`.opencode/commands/explain.md` becomes `/explain`:

```markdown
---
description: Explain a file for onboarding
agent: explainer
---
Explain $ARGUMENTS. Cite path:line for each claim.
```

- `$ARGUMENTS` is the whole argument string. `$1`, `$2` are positional. No placeholder: arguments are appended.
- `` !`git diff` `` inserts command output before sending. It runs outside the permission flow. Never put `$ARGUMENTS` or `$1` inside it.
- `subagent: true` runs the command in a background child session that reports back.
- Run commands in the TUI. `opencode run "/explain x"` sends the text literally on 2.1.x.

## Skills

`.opencode/skills/<id>/SKILL.md`. The folder name is the ID.

```markdown
---
name: Change summary
description: Write a reviewable change summary and commit message. Use before committing.
---
1. Run git diff ...
```

No `description` means the model is never offered the skill. Type `@<id>` to load it yourself.

## MCP

```jsonc
"mcp": {
  "servers": {
    "requirements": {
      "type": "local",
      "command": ["python3", ".opencode/mcp/requirements_server.py"],
      "environment": { "REQUIREMENTS_FILE": "requirements/requirements.json" }
    }
  }
}
```

Remote: `"type": "remote", "url": "..."`. Use `{env:NAME}` for secrets. `opencode mcp list` and `/mcps` show status. Tools appear as `<server>_<tool>`, for example `requirements_get_requirement`.

## Headless

```sh
opencode run "Summarize the failing tests"
opencode run --agent reviewer --file skyroute/route.py "Review this file"
opencode run --format json "List TODO comments"
opencode run --continue "Now add a test"
opencode run --standalone "Review this repository"
```

Flags: `--model provider/model#variant`, `--agent` (subagents accepted), `--file`, `--format json`, `--continue`, `--session <id>`, `--fork`, `--title`, `--standalone`, `--auto` (approves everything not explicitly denied; avoid on real code). `cd` into the repository first: OpenCode takes the project from `$PWD`. With `--format json`, assistant text is in `part.text` of `"type":"text"` events, and failures are `"type":"error"` events.

## Undo and safety

- `/undo` reverts the last message and its file changes. `/redo` restores. Snapshots do not replace Git: commit before big changes.
- `opencode session export <id> --sanitize` exports a session with sensitive data redacted.
- Export classification decisions come from your export compliance office, not from this tool.
