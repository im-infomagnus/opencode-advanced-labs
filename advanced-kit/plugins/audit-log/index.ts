// audit-log: an append-only record of what the agent did in this workspace, kept
// outside the session store so a reviewer can read it with grep and jq. One JSON line
// per tool call and permission event in .opencode/audit/YYYY-MM-DD.jsonl.
//
// Records metadata only: event type, time, session, tool name, call ID, status,
// permission action and reply, error type. Never tool input, output, file contents,
// shell commands, or permission resources, because those can carry secrets. So it
// shows which tools ran and how each permission request was answered, not what a
// command or edit did.
//
// If the event stream ends, it subscribes again after 1 s, doubling to at most 60 s.
// Events published while it is not subscribed are not recorded.
import { Plugin } from "@opencode/plugin"
import { appendFile, mkdir } from "node:fs/promises"
import { join } from "node:path"

type Entry = Record<string, string | number | boolean | undefined>

// Event type -> the metadata fields kept for it. Anything not listed is ignored.
const RECORDERS: Record<string, (data: any, toolName: (callID: string) => string | undefined) => Entry> = {
  "session.created": (d) => ({ sessionID: d.sessionID }),
  "session.tool.called": (d, tool) => ({ sessionID: d.sessionID, callID: d.id, tool: tool(d.id) }),
  "session.tool.success": (d, tool) => ({ sessionID: d.sessionID, callID: d.id, tool: tool(d.id), status: "success" }),
  "session.tool.failed": (d, tool) => ({ sessionID: d.sessionID, callID: d.id, tool: tool(d.id), status: "failed", error: d.error?.type }),
  "permission.asked": (d) => ({ sessionID: d.sessionID, requestID: d.id, action: d.action, callID: d.source?.id }),
  "permission.replied": (d) => ({ sessionID: d.sessionID, requestID: d.requestID, reply: d.reply }),
}

function day(time: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${time.getFullYear()}-${pad(time.getMonth() + 1)}-${pad(time.getDate())}`
}

export default Plugin.define({
  id: "audit-log",
  async setup(ctx) {
    const root = ctx.location.directory
    const dir = join(root, ".opencode", "audit")
    const toolNames = new Map<string, string>()
    const sessions = new Set<string>()
    const controller = new AbortController()

    // The event stream carries every location the service hosts; keep only this one.
    const ours = (event: any): boolean => {
      const sessionID = event.data?.sessionID
      if (event.location?.directory === root) {
        if (typeof sessionID === "string") sessions.add(sessionID)
        return true
      }
      return !event.location && typeof sessionID === "string" && sessions.has(sessionID)
    }

    // Writes are asynchronous, so the shared service never blocks on the disk, and
    // chained, so lines keep the order of the events.
    let pending: Promise<void> = Promise.resolve()
    const write = (event: any, entry: Entry) => {
      const time = new Date(typeof event.created === "number" ? event.created : Date.now())
      const line = JSON.stringify({ time: time.toISOString(), type: event.type, ...entry })
      pending = pending
        .then(() => mkdir(dir, { recursive: true }))
        .then(() => appendFile(join(dir, `${day(time)}.jsonl`), line + "\n"))
        .catch((error) => console.error(`audit-log: cannot write ${dir}: ${String(error)}`))
    }

    const pause = (ms: number) =>
      new Promise<void>((done) => {
        const timer = setTimeout(done, ms)
        controller.signal.addEventListener("abort", () => (clearTimeout(timer), done()), { once: true })
      })

    void (async () => {
      let delay = 1_000
      while (!controller.signal.aborted) {
        let reason = "the stream closed"
        try {
          for await (const event of ctx.event.subscribe({ signal: controller.signal }) as AsyncIterable<any>) {
            delay = 1_000
            if (!ours(event)) continue
            if (event.type === "session.tool.input.started") toolNames.set(event.data.id, event.data.name)
            const record = RECORDERS[event.type]
            if (!record) continue
            write(event, record(event.data ?? {}, (callID) => toolNames.get(callID)))
            if (event.type === "session.tool.success" || event.type === "session.tool.failed") toolNames.delete(event.data.id)
          }
        } catch (error) {
          reason = String(error)
        }
        if (controller.signal.aborted) break
        console.error(`audit-log: event stream ended (${reason}); subscribing again in ${delay / 1000} s`)
        await pause(delay)
        delay = Math.min(delay * 2, 60_000)
      }
    })()

    return () => controller.abort()
  },
})
