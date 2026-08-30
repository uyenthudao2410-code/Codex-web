const fs = require('node:fs/promises');
const path = require('node:path');

const UI_PERFORMANCE_SCHEMA_VERSION = 1;
const MAX_RENDERER_SAMPLES = 180;
const MAX_MAIN_SAMPLES = 360;
const MAX_EVENT_LOOP_SAMPLES = 900;
const PERSIST_INTERVAL_MS = 30_000;
const MAX_DURATION_MS = 60_000;
const MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024;

const RENDERER_METRICS = Object.freeze({
  ipc_lightweight_snapshot_ms: MAX_DURATION_MS,
  ipc_live_orchestration_ms: MAX_DURATION_MS,
  snapshot_apply_ms: MAX_DURATION_MS,
  render_ms: MAX_DURATION_MS,
  overview_pulse_apply_ms: MAX_DURATION_MS,
  paint_commit_ms: MAX_DURATION_MS,
  dashboard_refresh_ms: MAX_DURATION_MS,
  refresh_work_ms: MAX_DURATION_MS,
  snapshot_age_ms: 24 * 60 * 60 * 1000,
  coalesced_updates: 1_000_000
});

const MAIN_METRICS = Object.freeze({
  snapshot_build_ms: MAX_DURATION_MS,
  snapshot_size_bytes: MAX_SNAPSHOT_BYTES,
  orchestration_build_ms: MAX_DURATION_MS,
  orchestration_size_bytes: MAX_SNAPSHOT_BYTES
});

function finiteMetric(value, maximum) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 && number <= maximum ? number : null;
}

function boundedText(value, maximum = 512) {
  return String(value || '').trim().slice(0, maximum);
}

function sanitizeContext(value = {}) {
  const source = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const context = {};
  for (const [key, maximum] of Object.entries({
    workspace: 1024,
    ui_instance_id: 160,
    ui_running_revision: 128,
    activation_epoch_id: 160,
    session_started_at: 64,
    platform: 32,
    architecture: 32,
    product_version: 64
  })) {
    const text = boundedText(source[key], maximum);
    if (text) context[key] = text;
  }
  const pid = Number(source.pid);
  if (Number.isSafeInteger(pid) && pid > 0) context.pid = pid;
  return context;
}

function sanitizeMetrics(sample, allowlist) {
  const metrics = {};
  for (const [key, maximum] of Object.entries(allowlist)) {
    const value = finiteMetric(sample?.[key], maximum);
    if (value !== null) metrics[key] = value;
  }
  return metrics;
}

function sanitizeEventLoopSamples(values) {
  if (!Array.isArray(values)) return [];
  return values.slice(-30)
    .map((value) => finiteMetric(value, MAX_DURATION_MS))
    .filter((value) => value !== null);
}

function normalizeObservedAt(value, nowUnixMs) {
  const observedAt = Number(value);
  if (!Number.isSafeInteger(observedAt) || observedAt <= 0) return nowUnixMs;
  if (observedAt > nowUnixMs + 5_000 || nowUnixMs - observedAt > 24 * 60 * 60 * 1000) return nowUnixMs;
  return observedAt;
}

function percentile(values, ratio) {
  if (!Array.isArray(values) || values.length === 0) return null;
  const sorted = values.slice().sort((left, right) => left - right);
  const index = Math.max(0, Math.min(sorted.length - 1, Math.ceil(sorted.length * ratio) - 1));
  return sorted[index];
}

function distribution(values) {
  const finite = (Array.isArray(values) ? values : []).filter((value) => Number.isFinite(value));
  if (!finite.length) return { count: 0, min: null, p50: null, p95: null, p99: null, max: null };
  return {
    count: finite.length,
    min: Math.min(...finite),
    p50: percentile(finite, 0.50),
    p95: percentile(finite, 0.95),
    p99: percentile(finite, 0.99),
    max: Math.max(...finite)
  };
}

function jsonByteLength(value) {
  try { return Buffer.byteLength(JSON.stringify(value), 'utf8'); }
  catch { return 0; }
}

function budgetStatus(metric, { minimumSamples, p95Below }) {
  if (!metric || metric.count < minimumSamples) {
    return { status: 'insufficient_samples', minimum_samples: minimumSamples, p95_below: p95Below };
  }
  return {
    status: metric.p95 < p95Below ? 'pass' : 'fail',
    minimum_samples: minimumSamples,
    p95_below: p95Below,
    observed_p95: metric.p95
  };
}

class UiPerformanceMetrics {
  constructor({ filePath = '', context = {}, now = () => Date.now(), persistIntervalMs = PERSIST_INTERVAL_MS } = {}) {
    this.filePath = boundedText(filePath, 4096);
    this.context = sanitizeContext(context);
    this.now = now;
    this.persistIntervalMs = Math.max(1_000, Number(persistIntervalMs) || PERSIST_INTERVAL_MS);
    this.rendererSamples = [];
    this.mainSamples = [];
    this.eventLoopSamples = [];
    this.startedAtUnixMs = this.now();
    this.lastPersistedAtUnixMs = 0;
    this.persistTimer = null;
    this.persistInFlight = null;
    this.mutationSequence = 0;
  }

  updateContext(patch = {}) {
    this.context = { ...this.context, ...sanitizeContext(patch) };
  }

  recordRenderer(sample = {}) {
    const nowUnixMs = this.now();
    const metrics = sanitizeMetrics(sample, RENDERER_METRICS);
    const eventLoopLagMs = sanitizeEventLoopSamples(sample.event_loop_lag_samples_ms);
    if (!Object.keys(metrics).length && !eventLoopLagMs.length) return { accepted: false };
    this.rendererSamples.push({
      observed_at_unix_ms: normalizeObservedAt(sample.observed_at_unix_ms, nowUnixMs),
      metrics
    });
    this.eventLoopSamples.push(...eventLoopLagMs);
    if (this.rendererSamples.length > MAX_RENDERER_SAMPLES) {
      this.rendererSamples.splice(0, this.rendererSamples.length - MAX_RENDERER_SAMPLES);
    }
    if (this.eventLoopSamples.length > MAX_EVENT_LOOP_SAMPLES) {
      this.eventLoopSamples.splice(0, this.eventLoopSamples.length - MAX_EVENT_LOOP_SAMPLES);
    }
    this.mutationSequence += 1;
    this.schedulePersist();
    return {
      accepted: true,
      renderer_sample_count: this.rendererSamples.length,
      event_loop_sample_count: this.eventLoopSamples.length
    };
  }

  recordMain(sample = {}) {
    const metrics = sanitizeMetrics(sample, MAIN_METRICS);
    if (!Object.keys(metrics).length) return { accepted: false };
    this.mainSamples.push({
      observed_at_unix_ms: normalizeObservedAt(sample.observed_at_unix_ms, this.now()),
      metrics
    });
    if (this.mainSamples.length > MAX_MAIN_SAMPLES) {
      this.mainSamples.splice(0, this.mainSamples.length - MAX_MAIN_SAMPLES);
    }
    this.mutationSequence += 1;
    this.schedulePersist();
    return { accepted: true, main_sample_count: this.mainSamples.length };
  }

  valuesFor(key, samples = this.rendererSamples) {
    return samples.map((sample) => sample.metrics?.[key]).filter((value) => Number.isFinite(value));
  }

  summary() {
    const lightweightIpc = this.valuesFor('ipc_lightweight_snapshot_ms');
    const orchestrationIpc = this.valuesFor('ipc_live_orchestration_ms');
    const metrics = {
      ui_event_loop_lag_ms: distribution(this.eventLoopSamples),
      ipc_roundtrip_ms: distribution([...lightweightIpc, ...orchestrationIpc]),
      ipc_lightweight_snapshot_ms: distribution(lightweightIpc),
      ipc_live_orchestration_ms: distribution(orchestrationIpc),
      snapshot_build_ms: distribution(this.valuesFor('snapshot_build_ms', this.mainSamples)),
      snapshot_size_bytes: distribution(this.valuesFor('snapshot_size_bytes', this.mainSamples)),
      orchestration_build_ms: distribution(this.valuesFor('orchestration_build_ms', this.mainSamples)),
      orchestration_size_bytes: distribution(this.valuesFor('orchestration_size_bytes', this.mainSamples)),
      snapshot_apply_ms: distribution(this.valuesFor('snapshot_apply_ms')),
      render_ms: distribution(this.valuesFor('render_ms')),
      overview_pulse_apply_ms: distribution(this.valuesFor('overview_pulse_apply_ms')),
      paint_commit_ms: distribution(this.valuesFor('paint_commit_ms')),
      dashboard_refresh_ms: distribution(this.valuesFor('dashboard_refresh_ms')),
      refresh_work_ms: distribution(this.valuesFor('refresh_work_ms')),
      snapshot_age_ms: distribution(this.valuesFor('snapshot_age_ms'))
    };
    const budgets = {
      ui_event_loop_p95_ms: budgetStatus(metrics.ui_event_loop_lag_ms, { minimumSamples: 30, p95Below: 50 }),
      normal_ipc_p95_ms: budgetStatus(metrics.ipc_roundtrip_ms, { minimumSamples: 20, p95Below: 100 }),
      snapshot_apply_p95_ms: budgetStatus(metrics.snapshot_apply_ms, { minimumSamples: 10, p95Below: 50 }),
      dashboard_refresh_p95_ms: budgetStatus(metrics.dashboard_refresh_ms, { minimumSamples: 10, p95Below: 500 })
    };
    const budgetStates = Object.values(budgets).map((budget) => budget.status);
    const readiness = budgetStates.includes('insufficient_samples')
      ? 'insufficient_samples'
      : budgetStates.includes('fail') ? 'fail' : 'pass';
    return {
      readiness,
      renderer_sample_count: this.rendererSamples.length,
      main_sample_count: this.mainSamples.length,
      event_loop_sample_count: this.eventLoopSamples.length,
      coalesced_updates_total: this.valuesFor('coalesced_updates').reduce((total, value) => total + value, 0),
      metrics,
      budgets
    };
  }

  report({ includeSamples = false } = {}) {
    const endedAtUnixMs = this.now();
    return {
      schema_version: UI_PERFORMANCE_SCHEMA_VERSION,
      kind: 'electron_ui_real_machine_performance_window',
      context: { ...this.context },
      window: {
        started_at: new Date(this.startedAtUnixMs).toISOString(),
        ended_at: new Date(endedAtUnixMs).toISOString(),
        duration_ms: Math.max(0, endedAtUnixMs - this.startedAtUnixMs)
      },
      limits: {
        renderer_samples: MAX_RENDERER_SAMPLES,
        main_samples: MAX_MAIN_SAMPLES,
        event_loop_samples: MAX_EVENT_LOOP_SAMPLES,
        persist_interval_ms: this.persistIntervalMs
      },
      summary: this.summary(),
      ...(includeSamples ? {
        samples: {
          renderer: this.rendererSamples.map((sample) => ({ ...sample, metrics: { ...sample.metrics } })),
          main: this.mainSamples.map((sample) => ({ ...sample, metrics: { ...sample.metrics } })),
          event_loop_lag_ms: this.eventLoopSamples.slice()
        }
      } : {})
    };
  }

  schedulePersist() {
    if (!this.filePath || this.persistTimer) return;
    const elapsed = Math.max(0, this.now() - this.lastPersistedAtUnixMs);
    const delay = this.lastPersistedAtUnixMs === 0 ? 0 : Math.max(0, this.persistIntervalMs - elapsed);
    this.persistTimer = setTimeout(() => {
      this.persistTimer = null;
      void this.flush().catch(() => {});
    }, delay);
    this.persistTimer.unref?.();
  }

  async flush() {
    if (!this.filePath) return false;
    if (this.persistTimer) {
      clearTimeout(this.persistTimer);
      this.persistTimer = null;
    }
    if (this.persistInFlight) return this.persistInFlight;
    const flushedSequence = this.mutationSequence;
    const payload = `${JSON.stringify(this.report({ includeSamples: true }), null, 2)}\n`;
    const directory = path.dirname(this.filePath);
    const temporary = `${this.filePath}.${process.pid}.tmp`;
    this.persistInFlight = (async () => {
      await fs.mkdir(directory, { recursive: true });
      await fs.writeFile(temporary, payload, { encoding: 'utf8', mode: 0o600 });
      await fs.rename(temporary, this.filePath);
      this.lastPersistedAtUnixMs = this.now();
      return true;
    })().finally(() => {
      this.persistInFlight = null;
      if (this.mutationSequence > flushedSequence) this.schedulePersist();
    });
    return this.persistInFlight;
  }
}

module.exports = {
  UiPerformanceMetrics,
  UI_PERFORMANCE_SCHEMA_VERSION,
  MAX_RENDERER_SAMPLES,
  MAX_MAIN_SAMPLES,
  MAX_EVENT_LOOP_SAMPLES,
  distribution,
  jsonByteLength
};
