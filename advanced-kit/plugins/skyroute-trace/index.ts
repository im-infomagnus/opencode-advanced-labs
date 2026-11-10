// skyroute-trace: one tool call answers "is this requirement implemented and tested?"
// Without it the model greps, opens requirements.json, and guesses which test IDs are
// real. This tool reads requirements/requirements.json, checks that every listed test
// module and test method exists, and greps skyroute/ and tests/ for the ID.
//
// Input: { id: "SR-FUEL-002" } traces one requirement. { mode: "gaps" } lists
// requirements with no tests and listed tests that do not exist.
import { Plugin } from "@opencode/plugin"
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs"
import { join, relative } from "node:path"

const MAX_HITS = 40

type Requirement = { id: string; title?: string; text?: string; component?: string; verification?: string; tests?: string[] }
type TestCheck = { test: string; file: string; status: "ok" | "missing module" | "missing class" | "missing method" }

function loadRequirements(root: string): Requirement[] {
  const path = join(root, "requirements", "requirements.json")
  const data = JSON.parse(readFileSync(path, "utf8"))
  if (!Array.isArray(data?.requirements)) throw new Error(`${path} has no "requirements" list`)
  return data.requirements.filter((r: any) => typeof r?.id === "string")
}

// tests.test_fuel.FuelTests.test_contingency -> tests/test_fuel.py, class FuelTests, method test_contingency
function checkTest(root: string, test: string): TestCheck {
  const parts = test.split(".")
  const method = parts.length >= 4 ? parts[parts.length - 1] : undefined
  const cls = parts.length >= 4 ? parts[parts.length - 2] : undefined
  const moduleParts = parts.length >= 4 ? parts.slice(0, -2) : parts.slice(0, 2)
  const file = `${moduleParts.join("/")}.py`
  const path = join(root, file)
  if (!existsSync(path)) return { test, file, status: "missing module" }
  if (!cls || !method) return { test, file, status: "ok" }
  // The class body runs from its header to the next line that starts at column 0.
  const lines = readFileSync(path, "utf8").split("\n")
  const start = lines.findIndex((line) => new RegExp(`^class ${cls}\\b`).test(line))
  if (start < 0) return { test, file, status: "missing class" }
  const end = lines.findIndex((line, i) => i > start && /^\S/.test(line))
  const body = lines.slice(start + 1, end < 0 ? undefined : end)
  if (!body.some((line) => new RegExp(`^\\s+def ${method}\\(`).test(line))) return { test, file, status: "missing method" }
  return { test, file, status: "ok" }
}

function pythonFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (name === "__pycache__" || name.startsWith(".")) return []
    if (statSync(path).isDirectory()) return pythonFiles(path)
    return name.endsWith(".py") ? [path] : []
  })
}

function grep(root: string, id: string): string[] {
  const hits: string[] = []
  for (const file of [...pythonFiles(join(root, "skyroute")), ...pythonFiles(join(root, "tests"))]) {
    readFileSync(file, "utf8")
      .split("\n")
      .forEach((line, index) => {
        if (line.includes(id)) hits.push(`${relative(root, file)}:${index + 1}: ${line.trim()}`)
      })
  }
  return hits
}

function trace(root: string, wanted: string): string {
  const requirements = loadRequirements(root)
  const id = wanted.trim().toUpperCase()
  const requirement = requirements.find((r) => r.id.toUpperCase() === id)
  if (!requirement) {
    const near = requirements.filter((r) => r.id.startsWith(id.split("-").slice(0, 2).join("-"))).map((r) => r.id)
    return `Unknown requirement ${id}.${near.length ? ` Known in that area: ${near.join(", ")}.` : ""} Use mode "gaps" or read requirements/requirements.json.`
  }
  const checks = (requirement.tests ?? []).map((test) => checkTest(root, test))
  const hits = grep(root, requirement.id)
  return [
    `${requirement.id}: ${requirement.title ?? ""}`,
    `Text: ${requirement.text ?? "(none)"}`,
    `Component: ${requirement.component ?? "(none)"}  Verification: ${requirement.verification ?? "(none)"}`,
    checks.length ? `Tests listed (${checks.length}):` : "Tests listed: none (gap)",
    ...checks.map((c) => `  [${c.status}] ${c.test} (${c.file})`),
    hits.length ? `References to ${requirement.id} in skyroute/ and tests/ (${hits.length}):` : `References to ${requirement.id} in skyroute/ and tests/: none`,
    ...hits.slice(0, MAX_HITS).map((hit) => `  ${hit}`),
    ...(hits.length > MAX_HITS ? [`  ... ${hits.length - MAX_HITS} more`] : []),
  ].join("\n")
}

function gaps(root: string): string {
  const requirements = loadRequirements(root)
  const untested = requirements.filter((r) => !r.tests?.length)
  const broken = requirements.flatMap((r) =>
    (r.tests ?? []).map((test) => ({ id: r.id, check: checkTest(root, test) })).filter(({ check }) => check.status !== "ok"),
  )
  return [
    `${requirements.length} requirements. ${untested.length} with no tests. ${broken.length} listed tests that do not exist.`,
    ...(untested.length ? ["No tests:", ...untested.map((r) => `  ${r.id}: ${r.title ?? ""} (${r.component ?? "no component"})`)] : []),
    ...(broken.length ? ["Listed but missing:", ...broken.map(({ id, check }) => `  ${id}: ${check.test} [${check.status}]`)] : []),
  ].join("\n")
}

export default Plugin.define({
  id: "skyroute-trace",
  async setup(ctx) {
    const root = ctx.location.directory
    await ctx.tool.transform((editor) => {
      editor.add({
        name: "skyroute_trace",
        description:
          "Trace a SkyRoute requirement (for example SR-FUEL-002) to its requirement text, listed tests (and whether each test exists), " +
          'and every mention of the ID in skyroute/ and tests/. Pass { "mode": "gaps" } instead to list requirements with no tests ' +
          "and listed tests that do not exist.",
        input: {
          type: "object",
          properties: {
            id: { type: "string", description: "Requirement ID, for example SR-FUEL-002" },
            mode: { type: "string", enum: ["trace", "gaps"], description: 'Default "trace" (needs id). "gaps" lists untested requirements.' },
          },
          additionalProperties: false,
        },
        options: { codemode: false },
        execute: async (input: any) => {
          try {
            if (input?.mode === "gaps") return { content: gaps(root) }
            if (typeof input?.id !== "string" || !input.id.trim()) return { content: 'Pass { "id": "SR-FUEL-002" } or { "mode": "gaps" }.' }
            return { content: trace(root, input.id) }
          } catch (error) {
            return { content: `skyroute_trace failed: ${String((error as Error)?.message ?? error)}` }
          }
        },
      })
    })
  },
})
