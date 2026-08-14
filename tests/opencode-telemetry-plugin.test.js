const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function loadCore() {
  return import(pathToFileURL(path.join(__dirname, '..', '.opencode', 'execution-hub-telemetry-core.mjs')).href);
}

function assistantEvent(overrides = {}) {
  const base = {
    role: 'assistant',
    sessionID: 'ses-1',
    id: 'msg-1',
    providerID: 'opencode-go',
    modelID: 'deepseek-v4-flash',
    time: { created: 1000 },
    cost: 0.001,
    tokens: { input: 10, output: 2, reasoning: 1, cache: { read: 4, write: 1 } },
  };
  return { type: 'message.updated', properties: { info: { ...base, ...overrides } } };
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

test('OpenCode telemetry builder only emits bounded quantitative assistant metadata', async () => {
  const { telemetryFromEvent } = await loadCore();
  assert.equal(telemetryFromEvent({ type: 'message.updated', properties: { info: { role: 'user' } } }), null);
  assert.equal(telemetryFromEvent({ type: 'other', properties: {} }), null);

  const telemetry = telemetryFromEvent(assistantEvent({
    content: 'secret transcript must not leave OpenCode',
    parts: [{ type: 'tool', input: 'secret tool input', output: 'secret tool output' }],
    prompt: 'secret prompt',
    tokens: { input: 10.9, output: 2.8, reasoning: 1.4, cache: { read: 4.7, write: 1.9 } },
  }));
  assert.deepEqual(Object.keys(telemetry), [
    'schema_version', 'event_type', 'session_id', 'message_id', 'provider_id', 'model_id', 'status',
    'started_at_ms', 'provider_cost', 'input_tokens', 'output_tokens', 'reasoning_output_tokens',
    'cache_read_tokens', 'cache_write_tokens'
  ]);
  assert.equal(telemetry.input_tokens, 10);
  assert.equal(telemetry.output_tokens, 2);
  assert.equal(telemetry.cache_read_tokens, 4);
  const serialized = JSON.stringify(telemetry);
  assert.equal(serialized.includes('secret'), false);
  assert.equal(serialized.includes('parts'), false);
  assert.equal(serialized.includes('prompt'), false);
});

test('OpenCode error telemetry fails terminally without copying error message text', async () => {
  const { telemetryFromEvent } = await loadCore();
  const telemetry = telemetryFromEvent(assistantEvent({
    error: { message: 'credential-like provider detail must not leave the plugin' },
  }));
  assert.equal(telemetry.status, 'failed');
  assert.equal(telemetry.error_name, 'provider_error');
  assert.equal(JSON.stringify(telemetry).includes('credential-like'), false);
});

test('OpenCode telemetry scheduler coalesces active updates, deduplicates, and sends terminal immediately', async (t) => {
  const { createTelemetryScheduler, telemetryFromEvent } = await loadCore();
  const sent = [];
  const unresolved = new Promise(() => {});
  const scheduler = createTelemetryScheduler({
    debounceMs: 10,
    maxTrackedMessages: 2,
    send: (telemetry) => {
      sent.push(telemetry);
      return unresolved;
    },
  });
  t.after(() => scheduler.dispose());

  scheduler.handleEvent(assistantEvent({ tokens: { input: 10, output: 1, reasoning: 0, cache: { read: 0, write: 0 } } }));
  scheduler.handleEvent(assistantEvent({ tokens: { input: 10, output: 2, reasoning: 0, cache: { read: 0, write: 0 } } }));
  scheduler.handleEvent(assistantEvent({ tokens: { input: 10, output: 3, reasoning: 0, cache: { read: 0, write: 0 } } }));
  assert.equal(sent.length, 0);
  await wait(25);
  assert.equal(sent.length, 1);
  assert.equal(sent[0].output_tokens, 3);

  scheduler.schedule(sent[0]);
  await wait(15);
  assert.equal(sent.length, 1);

  const terminal = telemetryFromEvent(assistantEvent({
    time: { created: 1000, completed: 1300 },
    finish: 'stop',
    tokens: { input: 10, output: 4, reasoning: 1, cache: { read: 2, write: 0 } },
  }));
  const scheduled = scheduler.schedule(terminal);
  assert.equal(scheduled, true);
  assert.equal(sent.length, 2, 'terminal telemetry is delivered synchronously to the fire-and-forget sender');
  assert.equal(sent[1].status, 'completed');
  assert.equal(sent[1].duration_ms, 300);
  scheduler.schedule(terminal);
  assert.equal(sent.length, 2, 'identical terminal updates are idempotent in the plugin');

  scheduler.handleEvent(assistantEvent({ id: 'msg-2' }));
  scheduler.handleEvent(assistantEvent({ id: 'msg-3' }));
  assert.ok(scheduler.trackedCount() <= 2);
});
