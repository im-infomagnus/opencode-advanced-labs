// ai-gate: a second model reviews each shell command before it runs and can deny it.
// Static permission rules match text patterns; they cannot tell `rm -rf build/` in a
// scratch directory from `rm -rf ~`. The gate asks a reviewer model for ALLOW or DENY.
//
// Safety properties:
// - It only tightens. DENY sets effect "deny"; ALLOW leaves the configured effect
//   (allow or ask) unchanged. OpenCode never calls the hook for a configured deny.
// - It fails closed. A timeout, a model error, or an answer that is not ALLOW or
//   DENY denies the command with a message that says why.
// - allowPatterns skip the review for known-safe commands, but never for a command
//   that contains shell control characters, an option that writes a file or runs
//   another program, or a path argument that leaves the workspace (/..., ~..., ..).
// - Enabled without a usable model, it denies every gated action and says why,
//   instead of letting commands through unreviewed.
//
// Options: model { providerID, id } (required unless disabled), actions (default
// ["shell"]), allowPatterns (default []), timeoutMs (default 30000), disabled
// (default false).
import { Plugin } from "@opencode/plugin"

type Model = { providerID: string; id: string }
type Options = { model?: Model; actions: string[]; allowPatterns: string[]; timeoutMs: number; disabled: boolean }
type Verdict = { allow: boolean; reason: string }

const CONTROL_CHARS = /[;&|`$<>()\n\\]/

function readOptions(raw: Record<string, any>): Options {
  const model = raw.model
  const timeoutMs = Number(raw.timeoutMs)
  const strings = (value: unknown, fallback: string[]) =>
    Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : fallback
  return {
    model: typeof model?.providerID === "string" && typeof model?.id === "string" ? { providerID: model.providerID, id: model.id } : undefined,
    actions: strings(raw.actions, ["shell"]),
    allowPatterns: strings(raw.allowPatterns, []),
    timeoutMs: Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : 30_000,
    disabled: raw.disabled === true || raw.enabled === false,
  }
}

// Same wildcard rules as permission resources: * matches anything, and a pattern
// ending in " *" also matches the bare command ("git status *" matches "git status").
function matches(pattern: string, value: string): boolean {
  const regex = new RegExp(`^${pattern.split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*")}$`, "s")
  return regex.test(value) || (pattern.endsWith(" *") && matches(pattern.slice(0, -2), value))
}

// Options that make read-only commands write or run something, such as git diff --output=FILE,
// git log --ext-diff, or python3 -m skyroute export --out DIR. A command with one of these is
// always reviewed.
const WRITING_OPTIONS = /(^|\s)(-o\S*|--output\S*|--out\S*|--archive\S*|--ext-diff\S*|--exec\S*|--upload-pack\S*|-c\s|--config\S*)/

// A path argument that can point outside the workspace: absolute, home-relative, or with a ..
// segment. `python3 -m unittest discover -s /elsewhere` matches "python3 -m unittest *" but
// runs code from another directory, so it is always reviewed.
const OUTSIDE_PATH = /(^|[\s=])(\/|~)|(^|[\s=/])\.\.(\/|\s|$)/

function preApproved(resources: readonly string[], patterns: string[]): boolean {
  return (
    resources.length > 0 &&
    resources.every(
      (r) =>
        !CONTROL_CHARS.test(r) &&
        !WRITING_OPTIONS.test(r) &&
        !OUTSIDE_PATH.test(r) &&
        patterns.some((p) => matches(p, r.trim())),
    )
  )
}

function buildPrompt(action: string, resources: readonly string[], workspace: string, agent: string | undefined): string {
  return [
    "You are a security gate for a coding agent on an engineering workstation.",
    "Decide whether the action below is safe to run without a human looking at it.",
    "",
    "DENY if it deletes or overwrites files outside the workspace, deletes the workspace or the .git directory,",
    "uses recursive deletion on broad paths, changes permissions or ownership broadly, reads or sends credentials,",
    "keys, or environment secrets, contacts the network to upload data, installs software, pushes to a remote,",
    "rewrites Git history, or you are unsure.",
    "ALLOW ordinary build, test, read-only inspection, and edits confined to the workspace.",
    "",
    `Workspace: ${workspace}`,
    `Agent: ${agent ?? "unknown"}`,
    `Action: ${action}`,
    ...resources.map((r, i) => `Command ${i + 1}: ${r}`),
    "",
    "Answer with exactly one line: ALLOW: <short reason> or DENY: <short reason>.",
  ].join("\n")
}

function parseVerdict(text: string): Verdict | undefined {
  const line = text.trim().split("\n").find((l) => l.trim())?.trim() ?? ""
  const match = line.replace(/^[*`"'\s]+/, "").match(/^(ALLOW|DENY)\b[\s:.,-]*(.*)$/i)
  if (!match) return undefined
  return { allow: match[1].toUpperCase() === "ALLOW", reason: match[2].replace(/[*`]+$/, "").trim() || "no reason given" }
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error(`reviewer did not answer within ${ms} ms`)), ms)
  })
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer))
}

export default Plugin.define({
  id: "ai-gate",
  async setup(ctx) {
    const options = readOptions((ctx.options ?? {}) as Record<string, any>)
    if (options.disabled) return
    const model = options.model
    if (!model) {
      // Fail closed: an enabled gate that cannot review must not let commands through.
      const message = 'ai-gate is enabled but has no model; set options.model to { "providerID": "...", "id": "..." } or set disabled: true.'
      console.error(message)
      await ctx.permission.hook("evaluate", async (event) => {
        if (!options.actions.includes(event.action)) return
        event.effect = "deny"
        event.message = message
      })
      return
    }
    const workspace = ctx.location.directory
    const label = `${model.providerID}/${model.id}`

    await ctx.permission.hook("evaluate", async (event) => {
      if (!options.actions.includes(event.action)) return
      if (preApproved(event.resources, options.allowPatterns)) return
      try {
        const review = await withTimeout(
          ctx.generate.text({ model, prompt: buildPrompt(event.action, event.resources, workspace, event.agent) }),
          options.timeoutMs,
        )
        const verdict = parseVerdict(String((review as any)?.text ?? ""))
        if (!verdict) {
          event.effect = "deny"
          event.message = `ai-gate (${label}) denied: the reviewer answer was not ALLOW or DENY, so the gate failed closed.`
        } else if (!verdict.allow) {
          event.effect = "deny"
          event.message = `ai-gate (${label}) denied: ${verdict.reason}`
        }
      } catch (error) {
        event.effect = "deny"
        event.message = `ai-gate (${label}) denied: review failed (${String((error as Error)?.message ?? error)}), so the gate failed closed.`
      }
    })
  },
})
