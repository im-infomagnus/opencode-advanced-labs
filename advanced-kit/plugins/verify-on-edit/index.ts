// verify-on-edit: after the agent edits a Python file, compile it and run its unit
// tests, then append the verdict to the tool result. The model reads PASS or FAIL in
// the same turn, so it fixes a broken edit before it moves on, instead of finding out
// later (or never). V2 has no LSP; this is the cheap, deterministic feedback loop.
//
// Options (plugins entry in opencode.jsonc): disabled (default false), timeoutMs
// (default 60000), runTests (default true), python (default "python3").
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { existsSync } from "node:fs"
import { isAbsolute, relative, resolve, sep } from "node:path"

const EDIT_TOOLS = new Set(["edit", "write", "patch"])
const MAX_ERROR_LINES = 12

type Options = { disabled: boolean; timeoutMs: number; runTests: boolean; python: string }
type Outcome = { ok: boolean; timedOut: boolean; output: string }
type Part = { type: string; text?: string; [key: string]: unknown }

function readOptions(raw: Record<string, unknown>): Options {
  const timeoutMs = Number(raw.timeoutMs)
  return {
    disabled: raw.disabled === true || raw.enabled === false,
    timeoutMs: Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : 60_000,
    runTests: raw.runTests !== false,
    python: typeof raw.python === "string" && raw.python ? raw.python : process.platform === "win32" ? "py" : "python3",
  }
}

// edit and write carry `path`; patch carries `patchText` with one header per file.
// The result's output.files list, when present, names the files actually changed.
function editedPaths(input: any, result: any): string[] {
  const found = new Set<string>()
  for (const key of ["path", "filePath"]) if (typeof input?.[key] === "string") found.add(input[key])
  for (const file of result?.output?.files ?? []) if (typeof file?.file === "string") found.add(file.file)
  const patch = typeof input?.patchText === "string" ? input.patchText : ""
  for (const match of patch.matchAll(/^\*\*\* (?:Add File|Update File|Move to): (.+)$/gm)) found.add(match[1].trim())
  return [...found]
}

function insideWorkspace(root: string, path: string): string | undefined {
  const rel = relative(root, isAbsolute(path) ? path : resolve(root, path))
  if (!rel || rel.startsWith("..") || isAbsolute(rel)) return undefined
  return rel.split(sep).join("/")
}

function testModuleFor(root: string, rel: string): string | undefined {
  const test = rel.match(/^tests\/(test_\w+)\.py$/)
  if (test) return `tests.${test[1]}`
  const source = rel.match(/^skyroute\/(\w+)\.py$/)
  if (source && existsSync(resolve(root, "tests", `test_${source[1]}.py`))) return `tests.test_${source[1]}`
  return undefined
}

function run(python: string, args: string[], cwd: string, timeoutMs: number): Promise<Outcome> {
  return new Promise((done) => {
    execFile(python, args, { cwd, timeout: timeoutMs, maxBuffer: 4 * 1024 * 1024 }, (error: any, stdout, stderr) => {
      const output = `${stderr ?? ""}${stdout ?? ""}`.trim()
      if (!error) return done({ ok: true, timedOut: false, output })
      if (error.code === "ENOENT") return done({ ok: false, timedOut: false, output: `cannot run ${python}: not found on the service PATH` })
      done({ ok: false, timedOut: error.killed === true, output: output || String(error.message ?? error) })
    })
  })
}

function firstLines(text: string, count: number): string {
  const lines = text.split("\n")
  const start = Math.max(0, lines.findIndex((line) => /^(FAIL|ERROR):/.test(line)))
  const picked = lines.slice(start, start + count)
  const summary = lines.findLast((line) => /^(FAILED|OK)\b/.test(line))
  if (summary && !picked.includes(summary)) picked.push("...", summary)
  return picked.map((line) => `  ${line}`).join("\n")
}

function testCount(text: string): string {
  return text.match(/^Ran \d+ tests?/m)?.[0] ?? "no test count"
}

async function verify(root: string, files: string[], options: Options): Promise<string> {
  const lines: string[] = []
  const modules = new Set<string>()
  for (const rel of files) {
    const compiled = await run(options.python, ["-m", "py_compile", rel], root, options.timeoutMs)
    if (!compiled.ok) {
      lines.push(`py_compile ${rel}: FAIL${compiled.timedOut ? " (timeout)" : ""}`, firstLines(compiled.output, MAX_ERROR_LINES))
      continue
    }
    lines.push(`py_compile ${rel}: PASS`)
    const module = options.runTests ? testModuleFor(root, rel) : undefined
    if (module) modules.add(module)
  }
  for (const module of modules) {
    const tests = await run(options.python, ["-m", "unittest", module], root, options.timeoutMs)
    if (tests.timedOut) lines.push(`unittest ${module}: FAIL (timeout after ${options.timeoutMs} ms)`)
    else if (tests.ok) lines.push(`unittest ${module}: PASS (${testCount(tests.output)})`)
    else lines.push(`unittest ${module}: FAIL`, firstLines(tests.output, MAX_ERROR_LINES))
  }
  const failed = lines.some((line) => /: FAIL/.test(line))
  return [`verify-on-edit: ${failed ? "FAIL" : "PASS"}`, ...lines].join("\n")
}

function withNote(result: any, note: string) {
  const content: Part[] =
    typeof result?.content === "string" ? [{ type: "text", text: result.content }] : Array.isArray(result?.content) ? result.content : []
  return { ...result, content: [...content, { type: "text", text: note }] }
}

export default Plugin.define({
  id: "verify-on-edit",
  async setup(ctx) {
    const options = readOptions((ctx.options ?? {}) as Record<string, unknown>)
    if (options.disabled) return
    const root = ctx.location.directory

    await ctx.tool.hook("execute.after", async (event: any) => {
      if (event.status !== "completed" || !EDIT_TOOLS.has(event.tool)) return
      try {
        const files = [...new Set(editedPaths(event.input, event.result).map((path) => insideWorkspace(root, path)))]
          .filter((rel): rel is string => !!rel && rel.endsWith(".py") && existsSync(resolve(root, rel)))
        if (files.length === 0) return
        event.result = withNote(event.result, await verify(root, files, options))
      } catch (error) {
        event.result = withNote(event.result, `verify-on-edit: ERROR (check not run): ${String((error as Error)?.message ?? error)}`)
      }
    })
  },
})
