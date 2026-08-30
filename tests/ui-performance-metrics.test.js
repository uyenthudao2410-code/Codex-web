const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  UiPerformanceMetrics,
  MAX_RENDERER_SAMPLES,
  MAX_MAIN_SAMPLES,
  MAX_EVENT_LOOP_SAMPLES,
  distribution,
  jsonByteLength
} = require('../electron/services/uiPerformanceMetrics');

test('UI performance metrics retain only bounded numeric telemetry and never arbitrary renderer content', () => {
  let now = 1_700_000_000_000;
  const metrics = new UiPerformanceMetrics({ now: () => now });
  for (let index = 0; index < MAX_RENDERER_SAMPLES + 25; index += 1) {
    now += 1_000;
    metrics.recordRenderer({
      observed_at_unix_ms: now,
      ipc_lightweight_snapshot_ms: index + 1,
      event_loop_lag_samples_ms: Array.from({ length: 30 }, (_, offset) => offset),
      authorization: 'must-not-be-persisted',
      payload: { prompt: 'private' }
    });
  }
  for (let index = 0; index < MAX_MAIN_SAMPLES + 25; index += 1) {
    metrics.recordMain({ snapshot_build_ms: index % 10, snapshot_size_bytes: 1024, secret: 'hidden' });
  }
  const report = metrics.report({ includeSamples: true });
  const serialized = JSON.stringify(report);
  assert.equal(report.samples.renderer.length, MAX_RENDERER_SAMPLES);
  assert.equal(report.samples.main.length, MAX_MAIN_SAMPLES);
  assert.equal(report.samples.event_loop_lag_ms.length, MAX_EVENT_LOOP_SAMPLES);
  assert.doesNotMatch(serialized, /must-not-be-persisted|private|hidden|authorization|payload|secret/);
});

test('UI performance summary computes exact percentile budgets and keeps insufficient windows explicit', () => {
  let now = 1_700_000_000_000;
  const metrics = new UiPerformanceMetrics({ now: () => now });
  assert.equal(metrics.summary().readiness, 'insufficient_samples');
  for (let index = 1; index <= 10; index += 1) {
    now += 1_000;
    metrics.recordRenderer({
      observed_at_unix_ms: now,
      ipc_lightweight_snapshot_ms: index,
      ipc_live_orchestration_ms: index + 10,
      snapshot_apply_ms: index,
      dashboard_refresh_ms: index * 10,
      event_loop_lag_samples_ms: [index, index + 1, index + 2],
      coalesced_updates: index === 10 ? 2 : 0
    });
  }
  const summary = metrics.summary();
  assert.equal(summary.readiness, 'pass');
  assert.equal(summary.metrics.ui_event_loop_lag_ms.count, 30);
  assert.equal(summary.metrics.ipc_roundtrip_ms.count, 20);
  assert.equal(summary.metrics.snapshot_apply_ms.p95, 10);
  assert.equal(summary.metrics.dashboard_refresh_ms.p95, 100);
  assert.equal(summary.coalesced_updates_total, 2);
  assert.equal(summary.budgets.ui_event_loop_p95_ms.status, 'pass');
  assert.equal(summary.budgets.normal_ipc_p95_ms.status, 'pass');
});

test('UI performance report persists atomically as a bounded real-machine window', async (t) => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'coding-ui-performance-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const filePath = path.join(directory, 'ui-performance.json');
  const metrics = new UiPerformanceMetrics({
    filePath,
    context: {
      workspace: 'E:\\DEV\\Codex-web',
      ui_instance_id: 'ui-instance-1',
      unknown_secret: 'do-not-copy'
    }
  });
  metrics.recordRenderer({ snapshot_apply_ms: 4, event_loop_lag_samples_ms: [1, 2, 3] });
  metrics.recordMain({ snapshot_build_ms: 8, snapshot_size_bytes: jsonByteLength({ ok: true }) });
  assert.equal(await metrics.flush(), true);
  const persisted = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  assert.equal(persisted.schema_version, 1);
  assert.equal(persisted.context.workspace, 'E:\\DEV\\Codex-web');
  assert.equal(persisted.samples.renderer.length, 1);
  assert.equal(persisted.samples.main.length, 1);
  assert.doesNotMatch(JSON.stringify(persisted), /do-not-copy|unknown_secret/);
  assert.equal(fs.existsSync(`${filePath}.${process.pid}.tmp`), false);
});

test('distribution uses nearest-rank percentiles without inventing values', () => {
  assert.deepEqual(distribution([]), { count: 0, min: null, p50: null, p95: null, p99: null, max: null });
  assert.deepEqual(distribution([5, 1, 3, 2, 4]), { count: 5, min: 1, p50: 3, p95: 5, p99: 5, max: 5 });
});

test('samples arriving during a flush schedule one later bounded persistence window', async (t) => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'coding-ui-performance-race-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  let now = 1_700_000_000_000;
  const filePath = path.join(directory, 'ui-performance.json');
  const metrics = new UiPerformanceMetrics({ filePath, now: () => now, persistIntervalMs: 1_000 });
  metrics.recordMain({ snapshot_build_ms: 1 });
  const firstFlush = metrics.flush();
  metrics.recordRenderer({ snapshot_apply_ms: 2, event_loop_lag_samples_ms: [1] });
  await firstFlush;
  assert.ok(metrics.persistTimer, 'a concurrent renderer mutation must remain scheduled after the first flush');
  now += 1_000;
  clearTimeout(metrics.persistTimer);
  metrics.persistTimer = null;
  await metrics.flush();
  const persisted = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  assert.equal(persisted.samples.main.length, 1);
  assert.equal(persisted.samples.renderer.length, 1);
});
