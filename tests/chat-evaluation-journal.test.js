const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');

const {
  ChatEvaluationJournal,
  normalizeHostObservation,
  productSessionReceipt,
  buildChatEvaluationBootstrapScript,
  buildChatEvaluationObserverScript,
  chatEvaluationDrainScript,
  chatEvaluationDebugScript,
  journalPath,
  pendingTurnPath,
  continuationConsentPath,
  bindingTurnPath,
  parseContinuationConsentText,
  CONTINUATION_CONSENT_SCHEMA_VERSION,
  CONTINUATION_CONSENT_PREFIX,
  HOST_OBSERVATION_SCHEMA_VERSION,
  HOST_CORRELATION_SCHEMA_VERSION
} = require('../electron/services/chatEvaluationJournal');

test('host observation normalization is content-free and derives span duration', () => {
  const event = normalizeHostObservation({
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'host_turn_span',
    span_id: 'u1->a1',
    user_observation_id: 'u1',
    assistant_observation_id: 'a1',
    navigation_epoch: 2,
    clock_domain: 'electron-renderer:2',
    start_ms: 10.25,
    end_ms: 35.75,
    duration_ms: 999,
    trace_id: 'trace-1',
    turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_dom',
    measurement: 'observed_user_visible_to_first_assistant_visible'
  });
  assert.equal(event.duration_ms, 25.5);
  assert.equal(normalizeHostObservation({ ...event, content: 'must not be stored' }), null);
});

test('controller usage normalization accepts only complete exact structured usage', () => {
  const usage = normalizeHostObservation({
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'controller_usage',
    observation_id: 'usage-1',
    navigation_epoch: 1,
    clock_domain: 'electron-renderer:1',
    monotonic_ms: 20,
    wall_time_ms: 1020,
    trace_id: 'trace-1',
    turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_structured_response',
    measurement: 'structured_response_usage_exact',
    accounting_profile: 'openai_compatible',
    provider_id: 'openai',
    model_id: 'gpt-test',
    source: 'client_reported',
    input_tokens: 100,
    cached_input_tokens: 40,
    output_tokens: 20,
    reasoning_output_tokens: 5
  });
  assert.equal(usage.input_tokens, 100);
  assert.equal(usage.cached_input_tokens, 40);
  assert.equal(usage.output_tokens, 20);
  assert.equal(usage.reasoning_output_tokens, 5);
  assert.equal(normalizeHostObservation({ ...usage, reasoning_output_tokens: undefined }), null);
  assert.equal(normalizeHostObservation({ ...usage, cached_input_tokens: 101 }), null);
  assert.equal(normalizeHostObservation({ ...usage, content: 'must not be stored' }), null);
});

test('host evaluation journal appends JSONL under workspace and rotates bounded evidence', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-eval-'));
  const journal = new ChatEvaluationJournal({ maxBytes: 4096 });
  const event = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'user_turn_visible',
    observation_id: 'u1',
    navigation_epoch: 1,
    clock_domain: 'electron-renderer:1',
    monotonic_ms: 10,
    wall_time_ms: 1000,
    trace_id: 'trace-1',
    turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_dom',
    measurement: 'observed_host_visible'
  };
  const first = journal.append(workspace, [event]);
  assert.equal(first.appended, 1);
  assert.equal(first.path, journalPath(workspace));
  assert.deepEqual(JSON.parse(fs.readFileSync(first.path, 'utf8').trim()), event);
  for (let index = 0; index < 40; index += 1) journal.append(workspace, [{ ...event, observation_id: `u-${index}` }]);
  assert.ok(fs.existsSync(first.path));
  assert.ok(fs.existsSync(`${first.path}.1`));
});

test('explicit bounded continuation consent is distinct from user-turn correlation and content-free', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-continuation-consent-'));
  const journal = new ChatEvaluationJournal();
  const descriptor = {
    action: 'authorize_bounded_continuation',
    run_id: 'run-1', wave_id: 'wave-1', workspace_id: 'workspace-1', problem_id: 'problem-1', problem_revision: 1,
    contract_fingerprint: 'a'.repeat(64), tool_contract_sha256: 'b'.repeat(64), runtime_behavior_fingerprint: 'c'.repeat(64),
    activation_epoch_id: 'epoch-1', activation_admission: 'open', issuer_client_id: 'chatweb-1', scope_sha256: 'd'.repeat(64),
    read_paths: ['src/read.py'], write_paths: ['src/write.py'], protected_paths: ['src/protected.py'], approved_check_hashes: ['e'.repeat(64)],
    max_duration_seconds: 120, max_decision_turns: 2, max_patch_attempts: 1
  };
  assert.deepEqual(parseContinuationConsentText(`${CONTINUATION_CONSENT_PREFIX}${JSON.stringify(descriptor)}`), descriptor);
  assert.equal(parseContinuationConsentText('I authorize background work'), null);
  const user = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION, event_type: 'user_turn_visible', observation_id: 'u1', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 10, wall_time_ms: 1000, trace_id: 'trace-1', turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_dom', measurement: 'observed_host_visible'
  };
  assert.equal(journal.stagePendingContinuationConsents(workspace, [user, {
    kind: 'continuation_consent', schema_version: CONTINUATION_CONSENT_SCHEMA_VERSION, turn_id: 'turn-1', trace_id: 'trace-1',
    descriptor, observer_plane: 'electron_chatgpt_dom'
  }]), 1);
  const receipt = JSON.parse(fs.readFileSync(continuationConsentPath(workspace), 'utf8'));
  assert.deepEqual(Object.keys(receipt).sort(), ['descriptor', 'receipt_id', 'schema_version', 'staged_at_unix_ms', 'trace_id', 'turn_id']);
  assert.deepEqual(receipt.descriptor, descriptor);
  assert.equal(JSON.stringify(receipt).includes('I authorize'), false);
  assert.equal(journal.stagePendingContinuationConsents(workspace, [{
    kind: 'continuation_consent', schema_version: CONTINUATION_CONSENT_SCHEMA_VERSION, turn_id: 'turn-other', trace_id: 'trace-other',
    descriptor, observer_plane: 'electron_chatgpt_dom'
  }]), 0);
});

test('host correlation state is one-shot, content-free, and exact-identity matched', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-correlation-'));
  const journal = new ChatEvaluationJournal();
  const user = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'user_turn_visible', observation_id: 'u1', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 10, wall_time_ms: 1000,
    trace_id: 'trace-1', turn_id: 'turn-1', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_host_visible'
  };
  assert.equal(journal.stagePendingTurns(workspace, [user]), 1);
  const pending = JSON.parse(fs.readFileSync(pendingTurnPath(workspace), 'utf8'));
  assert.deepEqual(Object.keys(pending).sort(), ['schema_version', 'staged_at_unix_ms', 'trace_id', 'turn_id']);
  assert.equal(JSON.stringify(pending).includes('content'), false);
  fs.writeFileSync(bindingTurnPath(workspace), JSON.stringify({
    schema_version: HOST_CORRELATION_SCHEMA_VERSION,
    turn_id: 'turn-1', trace_id: 'trace-1', run_id: 'run-1', wave_id: 'wave-1', bound_at_unix_ms: Date.now()
  }));
  const span = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'host_turn_span', span_id: 'u1->a1', user_observation_id: 'u1', assistant_observation_id: 'a1',
    navigation_epoch: 1, clock_domain: 'electron-renderer:1', start_ms: 10, end_ms: 25,
    trace_id: 'trace-1', turn_id: 'turn-1', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_user_visible_to_first_assistant_visible'
  };
  const [linked] = journal.attachExplicitBindings(workspace, [span]);
  assert.equal(linked.run_id, 'run-1');
  assert.equal(linked.wave_id, 'wave-1');
  const [mismatch] = journal.attachExplicitBindings(workspace, [{ ...span, turn_id: 'turn-other' }]);
  assert.equal(mismatch.run_id, undefined);
  assert.equal(journal.consumeBinding(workspace, linked), true);
  assert.equal(fs.existsSync(bindingTurnPath(workspace)), false);
  assert.equal(journal.clearPendingTurn(workspace, linked), true);
  assert.equal(fs.existsSync(pendingTurnPath(workspace)), false);
});

test('host correlation pending identity survives until the completed host turn span', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-correlation-lifetime-'));
  const journal = new ChatEvaluationJournal();
  const user = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'user_turn_visible', observation_id: 'u1', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 10, wall_time_ms: 1000,
    trace_id: 'trace-1', turn_id: 'turn-1', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_host_visible'
  };
  const assistant = {
    ...user,
    event_type: 'assistant_response_first_visible', observation_id: 'a1', monotonic_ms: 25, wall_time_ms: 1015
  };
  const span = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'host_turn_span', span_id: 'u1->a1', user_observation_id: 'u1', assistant_observation_id: 'a1',
    navigation_epoch: 1, clock_domain: 'electron-renderer:1', start_ms: 10, end_ms: 25,
    trace_id: 'trace-1', turn_id: 'turn-1', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_user_visible_to_first_assistant_visible'
  };

  assert.equal(journal.stagePendingTurns(workspace, [user]), 1);
  assert.deepEqual(journal.finalizeCorrelation(workspace, user), { pending_cleared: false, binding_consumed: false });
  assert.equal(fs.existsSync(pendingTurnPath(workspace)), true);
  assert.deepEqual(journal.finalizeCorrelation(workspace, assistant), { pending_cleared: false, binding_consumed: false });
  assert.equal(fs.existsSync(pendingTurnPath(workspace)), true);

  fs.writeFileSync(bindingTurnPath(workspace), JSON.stringify({
    schema_version: HOST_CORRELATION_SCHEMA_VERSION,
    turn_id: 'turn-1', trace_id: 'trace-1', run_id: 'run-1', wave_id: 'wave-1', bound_at_unix_ms: Date.now()
  }));
  const [linked] = journal.attachExplicitBindings(workspace, [span]);
  assert.deepEqual(journal.finalizeCorrelation(workspace, linked), { pending_cleared: true, binding_consumed: false });
  assert.equal(fs.existsSync(pendingTurnPath(workspace)), false);
  assert.equal(fs.existsSync(bindingTurnPath(workspace)), true);

  const controllerUsage = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'controller_usage', observation_id: 'usage-1', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 30, wall_time_ms: 1030,
    trace_id: 'trace-1', turn_id: 'turn-1', observer_plane: 'electron_chatgpt_structured_response',
    measurement: 'structured_response_usage_exact', accounting_profile: 'openai_compatible',
    provider_id: 'openai', model_id: 'gpt-test', source: 'client_reported',
    input_tokens: 100, cached_input_tokens: 40, output_tokens: 20, reasoning_output_tokens: 5
  };
  const [linkedUsage] = journal.attachExplicitBindings(workspace, [controllerUsage]);
  assert.equal(linkedUsage.run_id, 'run-1');
  assert.equal(linkedUsage.wave_id, 'wave-1');
  assert.deepEqual(journal.finalizeCorrelation(workspace, linkedUsage), { pending_cleared: false, binding_consumed: true });
  assert.equal(fs.existsSync(bindingTurnPath(workspace)), false);
});

test('product session receipts are stable, content-free, and preserve exact rotation in pending correlation', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-product-session-'));
  const journal = new ChatEvaluationJournal();
  const user = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'user_turn_visible', observation_id: 'u-product', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 10, wall_time_ms: 1000,
    trace_id: 'trace-product', turn_id: 'turn-product', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_host_visible'
  };
  const firstUrl = 'https://chatgpt.com/c/11111111-1111-4111-8111-111111111111';
  const secondUrl = 'https://chatgpt.com/c/22222222-2222-4222-8222-222222222222';
  const firstReceipt = productSessionReceipt(firstUrl);
  assert.equal(firstReceipt, productSessionReceipt(firstUrl));
  assert.equal(productSessionReceipt('https://example.com/c/11111111-1111-4111-8111-111111111111'), null);
  assert.equal(firstReceipt.includes('11111111'), false);

  const [first] = journal.attachProductSession(workspace, [user], firstUrl);
  assert.equal(first.product_session_receipt_id, firstReceipt);
  assert.equal(first.product_session_transition, 'observed');
  journal.append(workspace, [first]);

  const [second] = journal.attachProductSession(
    workspace,
    [{ ...user, observation_id: 'u-product-2', turn_id: 'turn-product-2' }],
    secondUrl
  );
  assert.equal(second.product_session_transition, 'rotated');
  assert.equal(second.prior_product_session_receipt_id, firstReceipt);
  assert.notEqual(second.product_session_receipt_id, firstReceipt);
  assert.equal(JSON.stringify(second).includes('22222222'), false);
  assert.equal(journal.stagePendingTurns(workspace, [second]), 1);
  const pending = JSON.parse(fs.readFileSync(pendingTurnPath(workspace), 'utf8'));
  assert.equal(pending.product_session_receipt_id, second.product_session_receipt_id);
  assert.equal(pending.prior_product_session_receipt_id, firstReceipt);
  assert.equal(pending.product_session_transition, 'rotated');
});

test('product session correlation rejects malformed or raw session identities', () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'chat-product-session-invalid-'));
  const target = journalPath(workspace);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, `${JSON.stringify({ product_session_receipt_id: 'raw-conversation-id' })}\n`, 'utf8');
  const journal = new ChatEvaluationJournal();
  const url = 'https://chatgpt.com/c/33333333-3333-4333-8333-333333333333';
  const user = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'user_turn_visible', observation_id: 'u-invalid', navigation_epoch: 1,
    clock_domain: 'electron-renderer:1', monotonic_ms: 10, wall_time_ms: 1000,
    trace_id: 'trace-invalid', turn_id: 'turn-invalid', observer_plane: 'electron_chatgpt_dom', measurement: 'observed_host_visible'
  };

  const [event] = journal.attachProductSession(workspace, [user], url);
  assert.equal(event.product_session_transition, 'observed');
  assert.equal(JSON.stringify(event).includes('raw-conversation-id'), false);
  assert.equal(normalizeHostObservation({
    ...user,
    product_session_receipt_id: 'raw-conversation-id',
    product_session_transition: 'observed'
  }), null);
});

test('ChatGPT observer uses renderer monotonic clock and never reads message content', () => {
  const script = buildChatEvaluationObserverScript({ navigationEpoch: 3, clockDomain: 'electron-renderer:3' });
  assert.match(script, /performance\.now\(\)/);
  assert.match(script, /performance\.timeOrigin/);
  assert.match(script, /MutationObserver/);
  assert.match(script, /seenKeys/);
  assert.match(script, /requestAnimationFrame/);
  assert.match(script, /armed: false/);
  assert.match(script, /schedulePriming/);
  assert.match(script, /noteUserIntent/);
  assert.match(script, /button\[data-testid="send-button"\]/);
  assert.match(script, /addEventListener\('submit'/);
  assert.match(script, /addEventListener\('keydown'/);
  assert.match(script, /intentBaselineOrdinal/);
  assert.match(script, /intentDeadlineMs/);
  assert.match(script, /visibleTurns/);
  assert.match(script, /if \(!state\.awaitingUserVisible && !state\.pendingUser && !state\.finalizing\) return;/);
  assert.match(script, /if \(state\.awaitingUserVisible \|\| state\.pendingUser \|\| state\.finalizing\) scheduleScan\(\);/);
  assert.match(script, /setTimeout\(finishPriming, 750\)/);
  assert.match(script, /setTimeout\(finishPriming, 5000\)/);
  assert.match(script, /turnNodes\(\)\.forEach\(markSeen\)/);
  assert.match(script, /checkVisibility/);
  assert.match(script, /getClientRects/);
  assert.match(script, /\.markdown,p,pre,code,table,ul,ol,blockquote,img/);
  assert.match(script, /conversation-turn-/);
  assert.match(script, /data-message-author-role/);
  assert.match(script, /observed_user_visible_to_first_assistant_visible/);
  assert.match(script, /response\.completed/);
  assert.match(script, /input_tokens_details\?\.cached_tokens/);
  assert.match(script, /output_tokens_details\?\.reasoning_tokens/);
  assert.match(script, /structured_response_usage_exact/);
  assert.match(script, /structuredUsageEnvelopeChildren/);
  assert.match(script, /\['data', 'event'\]/);
  assert.match(script, /let originalJsonParse = null/);
  assert.match(script, /originalJsonParse = JSON\.parse/);
  assert.match(script, /Response\?\.prototype\?\.json/);
  assert.match(script, /randomUUID/);
  assert.match(script, /turn_id/);
  assert.match(script, /trace_id/);
  assert.doesNotMatch(script, /innerText/);
  // textContent is allowed ONLY inside the counts-only textMetrics helper
  // (authorized policy change); every other content reader stays banned.
  assert.doesNotMatch(script, /responseText/);
  assert.doesNotMatch(script, /prompt/);
  assert.doesNotMatch(script, /Object\.values/);
});

test('structured usage observer ignores hostile content nesting, deduplicates, and restores hooks exactly', () => {
  class FakeResponse {
    async json() { return this.payload; }
  }
  const sandbox = vm.createContext({
    window: {},
    document: {
      body: {},
      querySelector: () => null,
      querySelectorAll: () => [],
      addEventListener: () => {},
      removeEventListener: () => {}
    },
    MutationObserver: class { observe() {} disconnect() {} },
    Response: FakeResponse,
    performance: { now: () => 100, timeOrigin: 1000 },
    crypto: {
      randomUUID: () => 'observer-test-id',
      getRandomValues: (bytes) => { bytes.fill(1); return bytes; }
    },
    requestAnimationFrame: () => 0,
    setTimeout: () => 1,
    clearTimeout: () => {}
  });
  const observer = buildChatEvaluationObserverScript({ navigationEpoch: 9, clockDomain: 'electron-renderer:9' });
  const originalParse = vm.runInContext('JSON.parse', sandbox);
  const originalResponseJson = vm.runInContext('Response.prototype.json', sandbox);
  vm.runInContext(observer, sandbox);
  const wrappedParse = vm.runInContext('JSON.parse', sandbox);
  const wrappedResponseJson = vm.runInContext('Response.prototype.json', sandbox);
  assert.notEqual(wrappedParse, originalParse);
  assert.notEqual(wrappedResponseJson, originalResponseJson);

  vm.runInContext(observer, sandbox);
  assert.equal(vm.runInContext('JSON.parse', sandbox), wrappedParse, 'same-epoch install must not stack JSON.parse wrappers');
  assert.equal(vm.runInContext('Response.prototype.json', sandbox), wrappedResponseJson, 'same-epoch install must not stack Response.json wrappers');
  vm.runInContext("window.__mcpHostEvaluationTelemetry.lastTurn = { turnId: 'turn-9', traceId: 'trace-9', completedAtMs: 100 }", sandbox);

  const exactResponse = {
    type: 'response.completed',
    response: {
      id: 'resp_test', status: 'completed', model: 'gpt-test',
      usage: {
        input_tokens: 100,
        input_tokens_details: { cached_tokens: 40 },
        output_tokens: 20,
        output_tokens_details: { reasoning_tokens: 5 }
      }
    }
  };
  const hostile = { messages: [{ content: [{ data: exactResponse }] }] };
  vm.runInContext(`JSON.parse(${JSON.stringify(JSON.stringify(hostile))})`, sandbox);
  let drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'controller_usage').length, 0);

  const allowedEnvelope = { data: exactResponse };
  const encoded = JSON.stringify(JSON.stringify(allowedEnvelope));
  vm.runInContext(`JSON.parse(${encoded})`, sandbox);
  vm.runInContext(`JSON.parse(${encoded})`, sandbox);
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  const usageEvents = drained.filter((event) => event.event_type === 'controller_usage');
  assert.equal(usageEvents.length, 1, 'identical structured usage must be emitted once');
  assert.deepEqual(
    [usageEvents[0].input_tokens, usageEvents[0].cached_input_tokens, usageEvents[0].output_tokens, usageEvents[0].reasoning_output_tokens],
    [100, 40, 20, 5]
  );

  vm.runInContext('window.__mcpHostEvaluationTelemetry.dispose()', sandbox);
  assert.equal(vm.runInContext('JSON.parse', sandbox), originalParse);
  assert.equal(vm.runInContext('Response.prototype.json', sandbox), originalResponseJson);
  assert.equal(vm.runInContext('Boolean(window.__mcpHostEvaluationTelemetry)', sandbox), false);
});

test('early main-world bootstrap captures usage through a parser reference retained before the dom observer installs', () => {
  class FakeResponse {
    async json() { return this.payload; }
  }
  const sandbox = vm.createContext({
    window: {},
    document: {
      body: {},
      querySelector: () => null,
      querySelectorAll: () => [],
      addEventListener: () => {},
      removeEventListener: () => {}
    },
    MutationObserver: class { observe() {} disconnect() {} },
    Response: FakeResponse,
    performance: { now: () => 100, timeOrigin: 1000 },
    crypto: {
      randomUUID: () => 'early-bootstrap-id',
      getRandomValues: (bytes) => { bytes.fill(2); return bytes; }
    },
    requestAnimationFrame: () => 0,
    setTimeout: () => 1,
    clearTimeout: () => {}
  });
  const originalParse = vm.runInContext('JSON.parse', sandbox);
  const bootstrap = buildChatEvaluationBootstrapScript();
  assert.match(bootstrap, /__mcpStructuredUsageBootstrap/);
  assert.match(bootstrap, /response\.completed/);
  assert.match(bootstrap, /Response\?\.prototype\?\.json/);
  assert.doesNotMatch(bootstrap, /innerText|textContent|responseText|prompt/);
  vm.runInContext(bootstrap, sandbox);
  const parserCapturedByPageBundle = vm.runInContext('JSON.parse', sandbox);
  assert.notEqual(parserCapturedByPageBundle, originalParse);

  const observer = buildChatEvaluationObserverScript({ navigationEpoch: 10, clockDomain: 'electron-renderer:10' });
  vm.runInContext(observer, sandbox);
  vm.runInContext("window.__mcpHostEvaluationTelemetry.lastTurn = { turnId: 'turn-10', traceId: 'trace-10', completedAtMs: 100 }", sandbox);
  const exactResponse = {
    type: 'response.completed',
    response: {
      id: 'resp_early', status: 'completed', model: 'gpt-early',
      usage: {
        input_tokens: 321,
        input_tokens_details: { cached_tokens: 120 },
        output_tokens: 45,
        output_tokens_details: { reasoning_tokens: 11 }
      }
    }
  };
  sandbox.__encodedEarlyUsage = JSON.stringify({ data: exactResponse });
  sandbox.__capturedParser = parserCapturedByPageBundle;
  vm.runInContext('__capturedParser(__encodedEarlyUsage)', sandbox);
  const drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  const usageEvents = drained.filter((event) => event.event_type === 'controller_usage');
  assert.equal(usageEvents.length, 1);
  assert.deepEqual(
    [usageEvents[0].input_tokens, usageEvents[0].cached_input_tokens, usageEvents[0].output_tokens, usageEvents[0].reasoning_output_tokens],
    [321, 120, 45, 11]
  );

  vm.runInContext('window.__mcpHostEvaluationTelemetry.dispose()', sandbox);
  assert.equal(vm.runInContext('JSON.parse', sandbox), parserCapturedByPageBundle, 'dom observer must not own the early parser hook');
  vm.runInContext('window.__mcpStructuredUsageBootstrap.dispose()', sandbox);
  assert.equal(vm.runInContext('JSON.parse', sandbox), originalParse);
});

test('ChatViewController drains host observations to a best-effort main callback', () => {
  const root = path.resolve(__dirname, '..');
  const controller = fs.readFileSync(path.join(root, 'electron', 'chatViewController.js'), 'utf8');
  const main = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
  assert.match(controller, /buildChatEvaluationObserverScript/);
  assert.match(controller, /buildChatEvaluationBootstrapScript/);
  assert.match(controller, /Page\.addScriptToEvaluateOnNewDocument/);
  assert.match(controller, /contents\?\.debugger/);
  assert.doesNotMatch(controller, /Network\.enable|Network\.getResponseBody/);
  assert.match(controller, /chatEvaluationDrainScript/);
  assert.match(controller, /onEvaluation/);
  assert.match(controller, /startEvaluationDrain\(\)/);
  assert.match(controller, /CHAT_EVALUATION_DRAIN_INTERVAL_MS = 1000/);
  assert.match(controller, /CHAT_EVALUATION_BOOTSTRAP_TIMEOUT_MS = 1500/);
  assert.match(controller, /installEvaluationBootstrapBeforeNavigation\(\)/);
  assert.match(controller, /Promise\.race\(\[/);
  assert.match(controller, /chat-evaluation-bootstrap-timeout/);
  assert.match(controller, /\.finally\(\(\) => this\.loadHome\(\)\)/);
  assert.match(controller, /evaluationDrainInFlight/);
  assert.match(controller, /\.finally\(\(\) => \{/);
  assert.match(main, /new ChatEvaluationJournal\(\)/);
  assert.match(main, /chatEvaluationJournal\.append\(workspace, correlated\)/);
  assert.match(main, /chatEvaluationJournal\.finalizeCorrelation\(workspace, event\)/);
  assert.match(main, /action: 'observation'/);
  assert.match(main, /run_id: event\.run_id/);
  assert.match(main, /wave_id: event\.wave_id/);
  assert.match(main, /observation_span/);
  assert.match(main, /stage: 'report_visible'/);
  assert.match(main, /recordControllerUsageReceipt/);
  assert.match(main, /io\.coding-tools\/controllerUsage/);
  assert.match(main, /run_id: event\.run_id/);
  assert.match(main, /wave_id: event\.wave_id/);
  assert.match(main, /X-Coding-Tools-Client-Id': 'chatweb'/);
  assert.match(main, /action: 'audit'/);
});

test('ChatViewController bounds early usage bootstrap so ChatGPT navigation cannot wait forever', () => {  const root = path.resolve(__dirname, '..');
  const controller = fs.readFileSync(path.join(root, 'electron', 'chatViewController.js'), 'utf8');
  const start = controller.indexOf('async installEvaluationBootstrapBeforeNavigation()');
  const end = controller.indexOf('async installEvaluationBootstrap()', start);
  assert.ok(start >= 0 && end > start, 'bounded bootstrap helper must remain discoverable');
  const helper = controller.slice(start, end);
  assert.match(helper, /setTimeout\(\(\) => \{/);
  assert.match(helper, /resolve\(false\)/);
  assert.match(helper, /CHAT_EVALUATION_BOOTSTRAP_TIMEOUT_MS/);
  assert.match(helper, /Promise\.race\(\[/);
  assert.match(helper, /this\.installEvaluationBootstrap\(\)/);
  assert.match(helper, /clearTimeout\(timer\)/);
  assert.doesNotMatch(helper, /loadHome\(/, 'navigation ownership stays in mount and runs once after the bounded gate');
});

function sseObserverSandbox() {
  const { TextDecoder } = require('node:util');
  return vm.createContext({
    window: {},
    document: {
      body: {},
      querySelector: () => null,
      querySelectorAll: () => [],
      addEventListener: () => {},
      removeEventListener: () => {}
    },
    MutationObserver: class { observe() {} disconnect() {} },
    performance: { now: () => 100, timeOrigin: 1000 },
    crypto: {
      randomUUID: () => 'sse-test-id',
      getRandomValues: (bytes) => { bytes.fill(3); return bytes; }
    },
    requestAnimationFrame: () => 0,
    setTimeout: () => 1,
    clearTimeout: () => {},
    TextDecoder
  });
}

function sseScanBody(chunks) {
  let index = 0;
  return {
    getReader: () => ({
      read: async () => {
        if (index >= chunks.length) return { value: undefined, done: true };
        const value = chunks[index];
        index += 1;
        return { value, done: false };
      },
      cancel: async () => {}
    })
  };
}

async function sseDebugUntil(sandbox, predicate, tries = 200) {
  let debug = null;
  for (let attempt = 0; attempt < tries; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 5));
    debug = vm.runInContext(chatEvaluationDebugScript(), sandbox);
    if (predicate(debug)) return debug;
  }
  return debug;
}

test('sse fetch hook assembles split event-stream frames into exact controller usage', async () => {
  const { TextEncoder } = require('node:util');
  const sseText = [
    ': ping',
    '',
    'data: {"type":"response.output_text.delta","delta":"hi"}',
    '',
    'data: {"type":"response.completed","response":{"id":"resp_sse","status":"completed","model":"gpt-sse","usage":{"input_tokens":500,"input_tokens_details":{"cached_tokens":100},"output_tokens":60,"output_tokens_details":{"reasoning_tokens":10}}}}',
    '',
    ''
  ].join('\n');
  const bytes = new TextEncoder().encode(sseText);
  const mid = Math.floor(bytes.length / 2);
  const scanBody = sseScanBody([bytes.slice(0, mid), bytes.slice(mid)]);
  let teeCalls = 0;
  const sseBody = { locked: false, tee: () => { teeCalls += 1; return [{ pageBranch: true }, scanBody]; } };
  const sseHeaders = { get: (name) => String(name).toLowerCase() === 'content-type' ? 'text/event-stream' : null };
  const sseResponse = { status: 200, statusText: 'OK', headers: sseHeaders, body: sseBody };
  let constructedScan = null;
  const sandbox = sseObserverSandbox();
  sandbox.Response = class { constructor(body, init) { constructedScan = { body, init }; } };
  sandbox.window.fetch = async () => sseResponse;
  const originalFetch = vm.runInContext('window.fetch', sandbox);
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 21, clockDomain: 'electron-renderer:21' }), sandbox);
  assert.notEqual(vm.runInContext('window.fetch', sandbox), originalFetch, 'event-stream hook must wrap fetch once');
  vm.runInContext("window.__mcpHostEvaluationTelemetry.lastTurn = { turnId: 'turn-21', traceId: 'trace-21', completedAtMs: 100 }", sandbox);
  await vm.runInContext('window.fetch("https://chatgpt.com/backend-api/conversation", { method: "POST" })', sandbox);
  assert.equal(teeCalls, 1);
  assert.ok(constructedScan, 'page must receive a replacement response for the teed branch');
  assert.equal(constructedScan.init.status, 200);
  const debug = await sseDebugUntil(sandbox, (value) => (value?.observer?.sseCompleted || 0) >= 1);
  assert.equal(debug.observer.sseStreams, 1);
  assert.ok(debug.observer.sseEvents >= 2);
  assert.equal(debug.observer.sseCompleted, 1);
  assert.equal(debug.observer.sseUsageHits, 1);
  assert.equal(debug.observer.sseUsageRejected, 0);
  assert.deepEqual(
    Array.from(debug.observer.sseTypeSamples).sort(),
    ['response.completed', 'response.output_text.delta']
  );
  const drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  const usageEvents = drained.filter((event) => event.event_type === 'controller_usage');
  assert.equal(usageEvents.length, 1, 'split SSE frames must assemble into exactly one usage receipt');
  assert.deepEqual(
    [usageEvents[0].input_tokens, usageEvents[0].cached_input_tokens, usageEvents[0].output_tokens, usageEvents[0].reasoning_output_tokens],
    [500, 100, 60, 10]
  );
  assert.equal(usageEvents[0].measurement, 'structured_response_usage_exact');
  vm.runInContext('window.__mcpHostEvaluationTelemetry.dispose()', sandbox);
  assert.equal(vm.runInContext('window.fetch', sandbox), originalFetch, 'dispose must restore the unwrapped fetch');
});

test('sse completed frames without exact usage shape are rejected with key-only evidence', async () => {
  const { TextEncoder } = require('node:util');
  const sseText = 'data: {"type":"response.completed","response":{"id":"resp_partial","status":"completed","model":"gpt-partial","usage":{"input_tokens":50,"output_tokens":9}}}\n\n';
  const scanBody = sseScanBody([new TextEncoder().encode(sseText)]);
  const sseBody = { locked: false, tee: () => [{ pageBranch: true }, scanBody] };
  const sseHeaders = { get: (name) => String(name).toLowerCase() === 'content-type' ? 'text/event-stream; charset=utf-8' : null };
  const sandbox = sseObserverSandbox();
  sandbox.Response = class {};
  sandbox.window.fetch = async () => ({ status: 200, statusText: 'OK', headers: sseHeaders, body: sseBody });
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 22, clockDomain: 'electron-renderer:22' }), sandbox);
  vm.runInContext("window.__mcpHostEvaluationTelemetry.lastTurn = { turnId: 'turn-22', traceId: 'trace-22', completedAtMs: 100 }", sandbox);
  await vm.runInContext('window.fetch("https://chatgpt.com/backend-api/conversation")', sandbox);
  const debug = await sseDebugUntil(sandbox, (value) => (value?.observer?.sseCompleted || 0) >= 1);
  assert.equal(debug.observer.sseCompleted, 1);
  assert.equal(debug.observer.sseUsageHits, 0);
  assert.equal(debug.observer.sseUsageRejected, 1);
  assert.deepEqual(Array.from(debug.observer.usageKeySamples), ['input_tokens,output_tokens']);
  const drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'controller_usage').length, 0);
});

test('sse usage survey records key names under any envelope without emitting', async () => {
  const { TextEncoder } = require('node:util');
  const sseText = 'data: {"type":"message_stream_complete","usage":{"input_tokens":10,"output_tokens":3}}\n\n';
  const scanBody = sseScanBody([new TextEncoder().encode(sseText)]);
  const sseBody = { locked: false, tee: () => [{ pageBranch: true }, scanBody] };
  const sseHeaders = { get: (name) => String(name).toLowerCase() === 'content-type' ? 'text/event-stream' : null };
  const sandbox = sseObserverSandbox();
  sandbox.Response = class {};
  sandbox.window.fetch = async () => ({ status: 200, statusText: 'OK', headers: sseHeaders, body: sseBody });
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 25, clockDomain: 'electron-renderer:25' }), sandbox);
  vm.runInContext("window.__mcpHostEvaluationTelemetry.lastTurn = { turnId: 'turn-25', traceId: 'trace-25', completedAtMs: 100 }", sandbox);
  await vm.runInContext('window.fetch("https://chatgpt.com/backend-api/conversation")', sandbox);
  const debug = await sseDebugUntil(sandbox, (value) => (value?.observer?.sseEvents || 0) >= 1);
  assert.deepEqual(Array.from(debug.observer.sseTypeSamples), ['message_stream_complete']);
  assert.deepEqual(Array.from(debug.observer.usageKeySamples), ['usage:{input_tokens,output_tokens}']);
  assert.equal(debug.observer.sseCompleted, 0);
  assert.equal(debug.observer.sseUsageHits, 0);
  const drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'controller_usage').length, 0);
});

test('non event-stream responses pass through the fetch hook untouched', async () => {
  const sandbox = sseObserverSandbox();
  sandbox.Response = class {};
  const jsonResponse = {
    status: 200,
    statusText: 'OK',
    headers: { get: () => 'application/json' },
    body: { locked: false, tee: () => { throw new Error('tee must not be called for non-SSE bodies'); } }
  };
  sandbox.window.fetch = async () => jsonResponse;
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 23, clockDomain: 'electron-renderer:23' }), sandbox);
  const seen = await vm.runInContext('window.fetch("https://chatgpt.com/backend-api/models")', sandbox);
  assert.equal(seen, jsonResponse);
  const debug = vm.runInContext(chatEvaluationDebugScript(), sandbox);
  assert.equal(debug.observer.sseStreams, 0);
  assert.equal(debug.observer.sseEvents, 0);
});

test('early bootstrap installs the sse hook with debug counters and restores fetch on dispose', () => {
  const sandbox = sseObserverSandbox();
  sandbox.Response = class {};
  const originalFetch = async () => 'native';
  sandbox.window.fetch = originalFetch;
  const bootstrap = buildChatEvaluationBootstrapScript();
  assert.match(bootstrap, /installFetchSseObservation/);
  assert.match(bootstrap, /restoreFetchSseObservation/);
  assert.match(bootstrap, /sseStreams/);
  assert.match(bootstrap, /usageKeySamples/);
  assert.match(bootstrap, /text\/event-stream/);
  assert.doesNotMatch(bootstrap, /innerText|textContent|responseText|prompt/);
  vm.runInContext(bootstrap, sandbox);
  assert.notEqual(vm.runInContext('window.fetch', sandbox), originalFetch);
  vm.runInContext(bootstrap, sandbox);
  assert.ok(vm.runInContext('window.__mcpUsageSseHookInstalled', sandbox), 'repeat bootstrap install must stay idempotent');
  const debug = vm.runInContext(chatEvaluationDebugScript(), sandbox);
  assert.deepEqual(
    [debug.bootstrap.sseStreams, debug.bootstrap.sseEvents, debug.bootstrap.sseCompleted],
    [0, 0, 0]
  );
  assert.deepEqual(Array.from(debug.bootstrap.usageKeySamples), []);
  vm.runInContext('window.__mcpStructuredUsageBootstrap.dispose()', sandbox);
  assert.equal(vm.runInContext('window.fetch', sandbox), originalFetch);
});

test('observer script wires the sse hook into the fallback path and exposes seam debug', () => {
  const observer = buildChatEvaluationObserverScript({ navigationEpoch: 24, clockDomain: 'electron-renderer:24' });
  assert.match(observer, /installFetchSseObservation/);
  assert.match(observer, /restoreFetchSseObservation/);
  assert.match(observer, /sseUsageRejected/);
  assert.match(observer, /usageKeySamples/);
  assert.match(observer, /debug: \{ sseStreams: 0/);
  assert.doesNotMatch(observer, /innerText|responseText/);
  const root = path.resolve(__dirname, '..');
  const controller = fs.readFileSync(path.join(root, 'electron', 'chatViewController.js'), 'utf8');
  assert.match(controller, /chatEvaluationDebugScript/);
  assert.match(controller, /pollEvaluationDebug\(\)/);
  assert.match(controller, /evaluationDebugTick/);
  assert.match(controller, /evaluationDebugInFlight/);
  assert.match(controller, /lastEvaluationDebug/);
  assert.match(controller, /structured-usage seam telemetry/);
  assert.doesNotMatch(controller, /Network\.enable|Network\.getResponseBody/);
});

test('turn features carry numeric-only structural evidence without message content', () => {
  const features = normalizeHostObservation({
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'turn_features',
    observation_id: 'a1:features',
    navigation_epoch: 1,
    clock_domain: 'electron-renderer:1',
    monotonic_ms: 30,
    wall_time_ms: 1030,
    trace_id: 'trace-1',
    turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_dom',
    measurement: 'structural_turn_features',
    turn_ordinal: 7,
    duration_ms: 12500,
    tool_card_count: 3,
    user_chars: 240,
    user_code_blocks: 1,
    asst_chars: 1850,
    asst_code_blocks: 2
  });
  assert.equal(features.turn_ordinal, 7);
  assert.equal(features.tool_card_count, 3);
  assert.equal(features.user_chars, 240);
  assert.equal(features.asst_chars, 1850);
  assert.equal(normalizeHostObservation({ ...features, turn_ordinal: null }).turn_ordinal, null);
  const { turn_ordinal: _dropped, ...withoutOrdinal } = features;
  assert.equal(normalizeHostObservation(withoutOrdinal).turn_ordinal, null);
  assert.equal(normalizeHostObservation({ ...features, turn_ordinal: -1 }), null);
  assert.equal(normalizeHostObservation({ ...features, tool_card_count: 1.5 }), null);
  assert.equal(normalizeHostObservation({ ...features, duration_ms: undefined }), null);
  assert.equal(normalizeHostObservation({ ...features, user_chars: undefined }), null);
  assert.equal(normalizeHostObservation({ ...features, asst_code_blocks: -2 }), null);
  assert.equal(normalizeHostObservation({ ...features, content: 'must not be stored' }), null);
  assert.equal(normalizeHostObservation({
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: 'host_turn_span',
    span_id: 'u1->a1',
    user_observation_id: 'u1',
    assistant_observation_id: 'a1',
    navigation_epoch: 1,
    clock_domain: 'electron-renderer:1',
    start_ms: 10,
    end_ms: 25,
    trace_id: 'trace-1',
    turn_id: 'turn-1',
    observer_plane: 'electron_chatgpt_dom',
    measurement: 'observed_user_visible_to_first_assistant_visible',
    turn_ordinal: 7
  }), null, 'feature keys must not leak onto other event types');
});

test('observer emits turn features from its own markers plus counts-only text metrics', () => {
  const script = buildChatEvaluationObserverScript({ navigationEpoch: 30, clockDomain: 'electron-renderer:30' });
  assert.match(script, /event_type: 'turn_features'/);
  assert.match(script, /measurement: 'structural_turn_features'/);
  assert.match(script, /data-mcp-tool-summary/);
  assert.match(script, /finalizeTurnFeatures/);
  assert.match(script, /updateFinalizing/);
  assert.match(script, /featuresFinalized/);
  assert.match(script, /noteSseEventType/);
  assert.match(script, /sseTypeSamples/);
  assert.match(script, /user_chars/);
  assert.match(script, /asst_chars/);
  // The DOM message content has exactly two narrowly bounded readers:
  // (1) textMetrics derives length/code-block counts and emits only numbers;
  // (2) continuationConsentFromNode recognizes a single explicit command and
  // emits only its normalized structured descriptor. No other observer path
  // may read message text.
  const metricsStart = script.indexOf('const textMetrics = (node)');
  const metricsEnd = script.indexOf('const describeTurn =', metricsStart);
  const consentStart = script.indexOf('const continuationConsentFromNode = (node)');
  const consentEnd = script.indexOf('const emitVisible =', consentStart);
  assert.ok(metricsStart >= 0 && metricsEnd > metricsStart, 'counts-only textMetrics helper must remain discoverable');
  assert.ok(consentStart >= 0 && consentEnd > consentStart, 'explicit continuation-consent reader must remain discoverable');
  const metricsBlock = script.slice(metricsStart, metricsEnd);
  const consentBlock = script.slice(consentStart, consentEnd);
  assert.match(metricsBlock, /textContent/);
  assert.match(consentBlock, /textContent/);
  assert.match(consentBlock, /startsWith\(prefix\)/);
  assert.match(consentBlock, /text\.length > 16 \* 1024/);
  assert.match(consentBlock, /JSON\.parse\(text\.slice\(prefix\.length\)\)/);
  assert.doesNotMatch(consentBlock, /push\(|return text/);
  const outsideTextReaders = script.slice(0, metricsStart)
    + script.slice(metricsEnd, consentStart)
    + script.slice(consentEnd);
  assert.doesNotMatch(outsideTextReaders, /textContent/, 'textContent may appear only inside the counts-only metrics or explicit-consent helper');
  assert.doesNotMatch(script, /innerText|outerHTML|responseText/);
});

test('observer finalizes turn features at turn end, never at first visible', () => {
  let nowMs = 100;
  const makeNode = (role, text) => ({
    isConnected: true,
    getAttribute: (name) => {
      if (name === 'data-message-author-role') return role;
      return '';
    },
    closest: () => null,
    querySelector: () => ({}),
    querySelectorAll: (selector) => (String(selector) === 'pre,code' ? [{}, {}].slice(0, role === 'assistant' ? 2 : 0) : []),
    getClientRects: () => [{ width: 120, height: 24 }],
    textContent: text
  });
  const userNode = makeNode('user', 'hello world, please help');
  const assistantNode = makeNode('assistant', 'partial');
  const sandbox = vm.createContext({
    window: {},
    document: {
      body: {},
      querySelector: () => null,
      querySelectorAll: (selector) => {
        if (String(selector).includes('conversation-turn-')) return [];
        return sandbox.__showAssistant ? [userNode, assistantNode] : [userNode];
      },
      addEventListener: () => {},
      removeEventListener: () => {}
    },
    MutationObserver: class {
      constructor(callback) { sandbox.__mutationCallback = callback; }
      observe() {}
      disconnect() {}
    },
    Response: class {},
    performance: { now: () => nowMs, timeOrigin: 1000 },
    crypto: {
      randomUUID: () => 'dom-turn-id',
      getRandomValues: (bytes) => { bytes.fill(4); return bytes; }
    },
    requestAnimationFrame: (callback) => { sandbox.__rafCallback = callback; return 1; },
    setTimeout: () => 1,
    clearTimeout: () => {},
    TextDecoder: require('node:util').TextDecoder
  });
  sandbox.__showAssistant = false;
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 40, clockDomain: 'electron-renderer:40' }), sandbox);
  vm.runInContext(`
    window.__mcpHostEvaluationTelemetry.armed = true;
    window.__mcpHostEvaluationTelemetry.awaitingUserVisible = true;
    window.__mcpHostEvaluationTelemetry.intentDeadlineMs = 20000;
    window.__mcpHostEvaluationTelemetry.intentBaselineOrdinal = -1;
    window.__mcpHostEvaluationTelemetry.pendingIntentIdentity = { turnId: 'turn-dom', traceId: 'trace-dom' };
  `, sandbox);
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  let drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'user_turn_visible').length, 1);
  // Assistant starts streaming: span timing is recorded, but no features yet.
  nowMs = 200;
  sandbox.__showAssistant = true;
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'host_turn_span').length, 1);
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  // Stream grows: still no emission, change clock resets the quiet window.
  nowMs = 500;
  assistantNode.textContent = 'partial plus more streamed content here';
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  // Still inside the quiet window: nothing.
  nowMs = 1200;
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  // Quiet for 1000ms: exactly one FINAL measurement with final counts.
  nowMs = 1600;
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  const features = drained.filter((event) => event.event_type === 'turn_features');
  assert.equal(features.length, 1);
  assert.equal(features[0].turn_ordinal, null);
  assert.equal(features[0].turn_id, 'turn-dom');
  assert.equal(features[0].user_chars, 'hello world, please help'.length);
  assert.equal(features[0].user_code_blocks, 0);
  assert.equal(features[0].asst_chars, 'partial plus more streamed content here'.length);
  assert.equal(features[0].asst_code_blocks, 2);
  assert.equal(features[0].duration_ms, 1500);
  assert.equal(features[0].measurement, 'structural_turn_features');
  const normalized = normalizeHostObservation(features[0]);
  assert.ok(normalized, 'final features must pass the journal gate');
  // A later scan must not emit a second measurement for the same turn.
  nowMs = 5000;
  sandbox.__mutationCallback();
  sandbox.__rafCallback();
  drained = vm.runInContext(chatEvaluationDrainScript(), sandbox);
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  const debug = vm.runInContext(chatEvaluationDebugScript(), sandbox);
  assert.equal(debug.observer.featuresFinalized, 1);
});

for (const pageUptimeMs of [0, 600000]) {
test(`observer emits a larger final structural snapshot after interim streaming progress (page uptime ${pageUptimeMs}ms)`, () => {
  let nowMs = pageUptimeMs + 100;
  const makeNode = (role, text) => ({
    isConnected: true,
    getAttribute: (name) => (name === 'data-message-author-role' ? role : ''),
    closest: () => null,
    querySelector: () => ({}),
    querySelectorAll: () => [],
    getClientRects: () => [{ width: 120, height: 24 }],
    textContent: text
  });
  const userNode = makeNode('user', 'count tokens please');
  const assistantNode = makeNode('assistant', 'ab');
  const sandbox = vm.createContext({
    window: {},
    document: {
      body: {},
      querySelector: () => null,
      querySelectorAll: (selector) => {
        if (String(selector).includes('conversation-turn-')) return [];
        return sandbox.__showAssistant ? [userNode, assistantNode] : [userNode];
      },
      addEventListener: () => {},
      removeEventListener: () => {}
    },
    MutationObserver: class {
      constructor(callback) { sandbox.__mutationCallback = callback; }
      observe() {}
      disconnect() {}
    },
    Response: class {},
    performance: { now: () => nowMs, timeOrigin: 1000 },
    crypto: {
      randomUUID: () => 'interim-turn-id',
      getRandomValues: (bytes) => { bytes.fill(5); return bytes; }
    },
    requestAnimationFrame: (callback) => { sandbox.__rafCallback = callback; return 1; },
    setTimeout: () => 1,
    clearTimeout: () => {},
    TextDecoder: require('node:util').TextDecoder
  });
  sandbox.__showAssistant = false;
  vm.runInContext(buildChatEvaluationObserverScript({ navigationEpoch: 41, clockDomain: 'electron-renderer:41' }), sandbox);
  vm.runInContext(`
    window.__mcpHostEvaluationTelemetry.armed = true;
    window.__mcpHostEvaluationTelemetry.awaitingUserVisible = true;
    window.__mcpHostEvaluationTelemetry.intentDeadlineMs = performance.now() + 50000;
    window.__mcpHostEvaluationTelemetry.intentBaselineOrdinal = -1;
    window.__mcpHostEvaluationTelemetry.pendingIntentIdentity = { turnId: 'turn-interim', traceId: 'trace-interim' };
  `, sandbox);
  const scanOnce = () => {
    sandbox.__mutationCallback();
    sandbox.__rafCallback();
    return vm.runInContext(chatEvaluationDrainScript(), sandbox);
  };
  scanOnce();
  nowMs = pageUptimeMs + 200;
  sandbox.__showAssistant = true;
  let drained = scanOnce();
  assert.equal(drained.filter((event) => event.event_type === 'host_turn_span').length, 1);
  // Growth within 3s of start: no interim yet.
  nowMs = pageUptimeMs + 1000;
  assistantNode.textContent = 'ab plus a longer streamed chunk';
  drained = scanOnce();
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  // Growth past the 3s interim cadence: one progressive snapshot.
  const interimText = 'ab plus a longer streamed chunk and even more tokens flowing';
  nowMs = pageUptimeMs + 3400;
  assistantNode.textContent = interimText;
  drained = scanOnce();
  const interim = drained.filter((event) => event.event_type === 'turn_features');
  assert.equal(interim.length, 1);
  assert.equal(interim[0].asst_chars, interimText.length);
  // A later growth inside the interim cadence has no second interim, but the
  // terminal snapshot must carry the larger final value and same turn identity.
  const finalText = `${interimText} after another streamed chunk before completion`;
  nowMs = pageUptimeMs + 4100;
  assistantNode.textContent = finalText;
  drained = scanOnce();
  assert.equal(drained.filter((event) => event.event_type === 'turn_features').length, 0);
  // Quiet window: exactly one final snapshot supersedes the interim downstream.
  nowMs = pageUptimeMs + 5200;
  drained = scanOnce();
  const finalSnapshot = drained.filter((event) => event.event_type === 'turn_features');
  assert.equal(finalSnapshot.length, 1);
  assert.equal(finalSnapshot[0].turn_id, interim[0].turn_id);
  assert.equal(finalSnapshot[0].trace_id, interim[0].trace_id);
  assert.equal(finalSnapshot[0].observation_id, interim[0].observation_id);
  assert.equal(finalSnapshot[0].asst_chars, finalText.length);
  assert.ok(finalSnapshot[0].asst_chars > interim[0].asst_chars);
  assert.ok(finalSnapshot[0].monotonic_ms > interim[0].monotonic_ms);
  const debug = vm.runInContext(chatEvaluationDebugScript(), sandbox);
  assert.equal(debug.observer.featuresInterim, 1);
  assert.equal(debug.observer.featuresFinalized, 1);
});
}
