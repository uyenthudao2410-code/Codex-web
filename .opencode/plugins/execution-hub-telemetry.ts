import type { Plugin } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import path from "node:path"
import { createTelemetryScheduler } from "../execution-hub-telemetry-core.mjs"

const PROXY_CLIENT_ID = "opencode"
const PROXY_CLIENT_TYPE = "opencode"
const MAX_DESCRIPTOR_BYTES = 16 * 1024
const TELEMETRY_TIMEOUT_MS = 1200

function descriptorPath() {
  const configured = String(process.env.CODING_TOOLS_MCP_PROXY_DESCRIPTOR || "").trim()
  if (configured) return configured
  const appData = String(process.env.APPDATA || "").trim()
  return appData ? path.join(appData, "web-mcp-assistant", "execution-hub-proxy.json") : ""
}

async function loadDescriptor() {
  const target = descriptorPath()
  if (!target) return null
  try {
    const raw = await readFile(target, "utf8")
    if (Buffer.byteLength(raw, "utf8") > MAX_DESCRIPTOR_BYTES) return null
    const value = JSON.parse(raw)
    const host = String(value?.host || "")
    const port = Number(value?.port || 0)
    const token = String(value?.token || "")
    if (value?.version !== 1 || !["127.0.0.1", "localhost"].includes(host)) return null
    if (!Number.isInteger(port) || port < 1 || port > 65535 || token.length < 32) return null
    return { host: "127.0.0.1", port, token }
  } catch {
    return null
  }
}

async function sendTelemetry(telemetry: Record<string, unknown>) {
  const descriptor = await loadDescriptor()
  if (!descriptor) return
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TELEMETRY_TIMEOUT_MS)
  const outbound: Record<string, unknown> = { ...telemetry }
  for (const [envName, fieldName] of [
    ["CODING_TOOLS_MCP_PROVIDER_DISPATCH_ID", "provider_dispatch_id"],
    ["CODING_TOOLS_MCP_PROVIDER_DELEGATION_ID", "provider_delegation_id"],
  ] as const) {
    const value = String(process.env[envName] || "").trim()
    if (value && value.length <= 256 && !/[\u0000-\u001f]/.test(value)) outbound[fieldName] = value
  }
  try {
    await fetch(`http://${descriptor.host}:${descriptor.port}/__hub_proxy/telemetry`, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${descriptor.token}`,
        "Content-Type": "application/json",
        "X-Coding-Tools-Proxy-Client-Id": PROXY_CLIENT_ID,
        "X-Coding-Tools-Proxy-Client-Type": PROXY_CLIENT_TYPE,
      },
      body: JSON.stringify(outbound),
    })
  } catch {
    // Telemetry is evidence-only. An unavailable local hub must never break OpenCode.
  } finally {
    clearTimeout(timer)
  }
}

export const ExecutionHubTelemetry: Plugin = async () => {
  const scheduler = createTelemetryScheduler({ send: sendTelemetry })
  return {
    event: ({ event }) => {
      scheduler.handleEvent(event)
      return Promise.resolve()
    },
  }
}
