// Lab AL05 plugin skeleton. Copy it to <workspace>/.opencode/plugins/lab/index.ts.
// It loads as is. Each TODO is one step of the lab; the README has the code for each.
// Finished versions of the same ideas: advanced-kit/plugins/ in the course repository.
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { existsSync, readFileSync } from "node:fs"
import { appendFile, mkdir } from "node:fs/promises"
import { isAbsolute, join, relative, resolve } from "node:path"

type Requirement = { id: string; title?: string; text?: string; component?: string; tests?: string[] }
type Part = { type: string; text?: string; [key: string]: unknown }

// Runs a program without a shell and never rejects. Async on purpose: a blocking
// call inside a hook stalls the service that every client shares.
// On Windows, "python3" is often the Microsoft Store stub, so run the py launcher instead.
function run(program: string, args: string[], cwd: string): Promise<{ ok: boolean; output: string }> {
  if (program === "python3" && process.platform === "win32") [program, args] = ["py", ["-3", ...args]]
  return new Promise((done) => {
    execFile(program, args, { cwd, timeout: 60_000 }, (error, stdout, stderr) => {
      const output = `${stderr ?? ""}${stdout ?? ""}`.trim()
      done({ ok: !error, output: output || (error ? String(error.message) : "") })
    })
  })
}

// A tool result is a list of content parts, and the model reads every part.
function appendText(result: any, text: string) {
  const content: Part[] = Array.isArray(result?.content)
    ? result.content
    : typeof result?.content === "string"
      ? [{ type: "text", text: result.content }]
      : []
  return { ...result, content: [...content, { type: "text", text }] }
}

// "/abs/workspace/skyroute/geo.py" or "skyroute/geo.py" -> "skyroute/geo.py"; outside -> undefined.
function workspacePath(root: string, path: unknown): string | undefined {
  if (typeof path !== "string" || !path) return undefined
  const rel = relative(root, isAbsolute(path) ? path : resolve(root, path))
  return rel && !rel.startsWith("..") && !isAbsolute(rel) ? rel.split("\\").join("/") : undefined
}

// Workspace-relative .py files changed by an edit, write, or patch call.
// edit and write carry input.path; patch carries input.patchText with one header per file.
function editedPythonFiles(root: string, event: any): string[] {
  const found = new Set<string>()
  if (typeof event.input?.path === "string") found.add(event.input.path)
  for (const file of event.result?.output?.files ?? []) if (typeof file?.file === "string") found.add(file.file)
  const patch = typeof event.input?.patchText === "string" ? event.input.patchText : ""
  for (const m of patch.matchAll(/^\*\*\* (?:Add File|Update File|Move to): (.+)$/gm)) found.add(m[1].trim())
  return [...found]
    .map((path) => workspacePath(root, path))
    .filter((rel): rel is string => !!rel && rel.endsWith(".py") && existsSync(join(root, rel)))
    .filter((rel, i, all) => all.indexOf(rel) === i)
}

// skyroute/geo.py -> tests/test_geo.py when that file exists; a test file maps to itself.
function testFileFor(root: string, rel: string): string | undefined {
  if (/^tests\/test_\w+\.py$/.test(rel)) return rel
  const match = rel.match(/^skyroute\/(\w+)\.py$/)
  const test = match ? `tests/test_${match[1]}.py` : undefined
  return test && existsSync(join(root, test)) ? test : undefined
}

// Reads requirements/requirements.json on every call, so edits show up without a reload.
function trace(root: string, id: string): string {
  const data = JSON.parse(readFileSync(join(root, "requirements", "requirements.json"), "utf8"))
  const wanted = id.trim().toUpperCase()
  const req: Requirement | undefined = data.requirements.find((r: Requirement) => r.id === wanted)
  if (!req) return `Unknown requirement ${wanted}. IDs look like SR-GEO-002.`
  const tests = (req.tests ?? []).map((t) => {
    const file = `${t.split(".").slice(0, 2).join("/")}.py`
    return `  ${t} (${existsSync(join(root, file)) ? "file exists" : "file missing"})`
  })
  return [
    `${req.id}: ${req.title ?? ""}`,
    `Text: ${req.text ?? ""}`,
    `Component: ${req.component ?? "(none)"}`,
    tests.length ? "Tests:" : "Tests: none listed (gap)",
    ...tests,
  ].join("\n")
}

export default Plugin.define({
  id: "lab",
  async setup(ctx) {
    const root = ctx.location.directory

    // TODO 1 (step 2): register a tool named lab_trace that takes { id } and
    // returns { content: trace(root, id) }. Use ctx.tool.transform.

    // TODO 2 (step 3): after a completed edit, write, or patch of .py files, run
    // py_compile on each and unittest on its test file, then append the verdict
    // to event.result with appendText(). Use ctx.tool.hook("execute.after").

    // TODO 3 (step 5): append one JSON line per finished tool call to
    // .opencode/audit/lab.jsonl with time, sessionID, agent, tool, and status.
    // Use mkdir and appendFile from node:fs/promises, not the Sync versions.
    // Never write tool input or output: they can carry secrets.
  },
})
