const CONTROL_CHAR_RE = /[\u0000-\u001f\u007f]/g

export const DEFAULT_ACTIVE_DEBOUNCE_MS = 120
export const DEFAULT_MAX_TRACKED_MESSAGES = 256

function boundedText(value, limit) {
  return String(value ?? "").replace(CONTROL_CHAR_RE, "").trim().slice(0, limit)
}

function nonNegativeNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) && number >= 0 ? number : 0
}

function nonNegativeInteger(value) {
  return Math.floor(nonNegativeNumber(value))
}

function errorClass(error) {
  if (!error) return ""
  if (typeof error !== "object") return "provider_error"
  const candidate = error.name ?? error.code ?? error.type ?? "provider_error"
  return boundedText(candidate, 120) || "provider_error"
}

export function telemetryFromEvent(event) {
  if (!event || event.type !== "message.updated") return null
  const info = event.properties?.info
  if (!info || info.role !== "assistant") return null

  const sessionId = boundedText(info.sessionID, 256)
  const messageId = boundedText(info.id, 256)
  const providerId = boundedText(info.providerID, 160)
  const modelId = boundedText(info.modelID, 200)
  if (!sessionId || !messageId || !providerId || !modelId) return null

  const startedAt = nonNegativeNumber(info.time?.created)
  const completedAt = info.time?.completed === undefined ? 0 : nonNegativeNumber(info.time.completed)
  const errorName = errorClass(info.error)
  const status = errorName ? "failed" : completedAt > 0 ? "completed" : "active"
  const telemetry = {
    schema_version: 1,
    event_type: "message.updated",
    session_id: sessionId,
    message_id: messageId,
    provider_id: providerId,
    model_id: modelId,
    status,
    started_at_ms: startedAt,
    provider_cost: nonNegativeNumber(info.cost),
    input_tokens: nonNegativeInteger(info.tokens?.input),
    output_tokens: nonNegativeInteger(info.tokens?.output),
    reasoning_output_tokens: nonNegativeInteger(info.tokens?.reasoning),
    cache_read_tokens: nonNegativeInteger(info.tokens?.cache?.read),
    cache_write_tokens: nonNegativeInteger(info.tokens?.cache?.write),
  }
  if (completedAt > 0) {
    telemetry.completed_at_ms = completedAt
    telemetry.duration_ms = Math.max(0, completedAt - startedAt)
  }
  const finish = boundedText(info.finish, 100)
  if (finish) telemetry.finish = finish
  if (errorName) telemetry.error_name = errorName
  return telemetry
}

function telemetryKey(telemetry) {
  return `${telemetry.session_id}\u0000${telemetry.message_id}`
}

function telemetryFingerprint(telemetry) {
  return JSON.stringify(telemetry)
}

function fireAndForget(send, telemetry) {
  try {
    const result = send(telemetry)
    if (result && typeof result.then === "function") result.catch(() => {})
  } catch {
    // Evidence telemetry must never affect the provider event loop.
  }
}

export function createTelemetryScheduler({
  send,
  debounceMs = DEFAULT_ACTIVE_DEBOUNCE_MS,
  maxTrackedMessages = DEFAULT_MAX_TRACKED_MESSAGES,
  setTimeoutFn = setTimeout,
  clearTimeoutFn = clearTimeout,
} = {}) {
  if (typeof send !== "function") throw new TypeError("send must be a function")
  const delay = Math.max(0, Number(debounceMs) || 0)
  const maxTracked = Math.max(1, Math.floor(Number(maxTrackedMessages) || DEFAULT_MAX_TRACKED_MESSAGES))
  const states = new Map()

  const touch = (key, state) => {
    if (states.has(key)) states.delete(key)
    states.set(key, state)
    while (states.size > maxTracked) {
      const oldestKey = states.keys().next().value
      const oldest = states.get(oldestKey)
      if (oldest?.timer) clearTimeoutFn(oldest.timer)
      states.delete(oldestKey)
    }
  }

  const getState = (key) => {
    const state = states.get(key) || {
      timer: null,
      pendingTelemetry: null,
      pendingFingerprint: "",
      lastSentFingerprint: "",
    }
    touch(key, state)
    return state
  }

  const deliver = (state, telemetry, fingerprint) => {
    if (!telemetry || fingerprint === state.lastSentFingerprint) return false
    state.lastSentFingerprint = fingerprint
    fireAndForget(send, telemetry)
    return true
  }

  const schedule = (telemetry) => {
    if (!telemetry) return false
    const key = telemetryKey(telemetry)
    const state = getState(key)
    const fingerprint = telemetryFingerprint(telemetry)
    const terminal = telemetry.status === "completed" || telemetry.status === "failed"

    if (terminal) {
      if (state.timer) clearTimeoutFn(state.timer)
      state.timer = null
      state.pendingTelemetry = null
      state.pendingFingerprint = ""
      return deliver(state, telemetry, fingerprint)
    }

    if (fingerprint === state.lastSentFingerprint || fingerprint === state.pendingFingerprint) return false
    state.pendingTelemetry = telemetry
    state.pendingFingerprint = fingerprint
    if (state.timer) return true

    state.timer = setTimeoutFn(() => {
      state.timer = null
      const pendingTelemetry = state.pendingTelemetry
      const pendingFingerprint = state.pendingFingerprint
      state.pendingTelemetry = null
      state.pendingFingerprint = ""
      deliver(state, pendingTelemetry, pendingFingerprint)
    }, delay)
    return true
  }

  const dispose = () => {
    for (const state of states.values()) {
      if (state.timer) clearTimeoutFn(state.timer)
    }
    states.clear()
  }

  return {
    handleEvent(event) {
      return schedule(telemetryFromEvent(event))
    },
    schedule,
    dispose,
    trackedCount() {
      return states.size
    },
  }
}
