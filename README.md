# OpenCode v2 Power User: Advanced Workshop labs

Lab materials for the two-day advanced OpenCode workshop. Everything here is synthetic: SkyRoute is a made-up flight-planning toolkit with seeded defects, and none of it is real navigation data. Do not put program code, program data, or credentials in this repository or in your lab workspaces.

## Before the course

1. **Install the tools.** OpenCode v2 (`opencode --version` prints `opencode v2.x`), Git, and Python 3.10 or later. On Windows, also install Git for Windows and run every `bash` command in **Git Bash**.
2. **Connect your provider.** Run `/connect` in the OpenCode TUI, or `opencode auth login`, with the provider your team approved. `opencode models` lists the `<provider>/<model>` names you can use.
3. **Set your default model** in your global config, `~/.config/opencode/opencode.jsonc` (on Windows, `~` is `%USERPROFILE%`):

   ```jsonc
   {
     "$schema": "https://opencode.ai/config.json",
     "model": "<provider>/<model>"
   }
   ```

   Run `opencode debug config` and confirm your global file shows that `"model"`. `/models` in the TUI changes only the current session; new sessions, forks, and `opencode run` use this default.
4. **Clone this repository and its tags**, then set `COURSE` to the clone in every terminal you use for the labs:

   ```bash
   git clone https://github.com/im-infomagnus/opencode-advanced-labs.git ~/opencode-advanced-labs
   cd ~/opencode-advanced-labs
   git fetch --tags
   export COURSE="$(pwd -W 2>/dev/null || pwd)"
   ```

5. **Run the preflight** from the clone and fix every `FAIL` line (Windows: see the notes in [`labs/README.md`](labs/README.md#before-any-lab)):

   ```bash
   bash labs/advanced-preflight.sh
   ```

## The labs

| Lab | Title | Day |
|-----|-------|-----|
| [AL01](labs/AL01-power-session/README.md) | Power Session and Review with /diff | 1 |
| [AL02](labs/AL02-context-scale/README.md) | Context at Scale | 1 |
| [AL03](labs/AL03-agent-team/README.md) | Build an Agent Team and Run a Mini Mission | 1 |
| [AL04](labs/AL04-mcp-codemode/README.md) | Build an MCP Server and Use Code Mode | 2 |
| [AL05](labs/AL05-plugin/README.md) | Change the Harness: Write a Plugin | 2 |
| [AL06](labs/AL06-fanout/README.md) | Parallel Worktree Fan-out with a Live Dashboard | 2 |

Each lab repeats something the instructor demonstrated, then adds a step of its own. Start with [`labs/README.md`](labs/README.md): it explains workspaces, Windows setup, and how to catch up if you miss a lab.

## Labs for OpenCode 1

On OpenCode 1? Use the [OpenCode 1 lab track](labs-v1/README.md): a handbook and eleven hands-on labs on the same SkyRoute code.

## What is in this repository

| Path | What it is |
|------|------------|
| `labs/AL01-...` to `labs/AL06-...` | Lab guides and the files each lab uses |
| `labs/skyroute/` | The SkyRoute starter code (tag `skyroute-starter-v2`). Lab workspaces are copies of it |
| `labs/solutions/skyroute/` | Reference results, for catching up. Reading them before a lab spoils it |
| `advanced-kit/` | Plugins, the navdata MCP server, reference docs, the ops log, and the fan-out tasks the labs install |
| `demos/mission-control/` | The live dashboard, the TUI layout file, and the Mission Control kit the instructor runs, for comparison in Lab AL03 |
| `starter-kit/mcp/requirements_server.py` | The requirements MCP server used in Lab AL04 |
| `participant/cheat-sheet.md` | One-page OpenCode v2 reference |
| `labs-v1/` | Hands-on labs for teams on OpenCode 1 |
