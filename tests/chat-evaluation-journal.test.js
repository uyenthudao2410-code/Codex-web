const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  ChatEvaluationJournal,
  normalizeHostObservation,
  buildChatEvaluationObserverScript,
  journalPath,
  pendingTurnPath,
  bindingTurnPath,
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
  assert.match(script, /if \(!state\.awaitingUserVisible && !state\.pendingUser\) return;/);
  assert.match(script, /if \(state\.awaitingUserVisible \|\| state\.pendingUser\) scheduleScan\(\);/);
  assert.match(script, /setTimeout\(finishPriming, 750\)/);
  assert.match(script, /setTimeout\(finishPriming, 5000\)/);
  assert.match(script, /turnNodes\(\)\.forEach\(markSeen\)/);
  assert.match(script, /checkVisibility/);
  assert.match(script, /getClientRects/);
  assert.match(script, /\.markdown,p,pre,code,table,ul,ol,blockquote,img/);
  assert.match(script, /conversation-turn-/);
  assert.match(script, /data-message-author-role/);
  assert.match(script, /observed_user_visible_to_first_assistant_visible/);
  assert.match(script, /randomUUID/);
  assert.match(script, /turn_id/);
  assert.match(script, /trace_id/);
  assert.doesNotMatch(script, /innerText/);
  assert.doesNotMatch(script, /textContent/);
  assert.doesNotMatch(script, /responseText/);
  assert.doesNotMatch(script, /prompt/);
});

test('ChatViewController drains host observations to a best-effort main callback', () => {
  const root = path.resolve(__dirname, '..');
  const controller = fs.readFileSync(path.join(root, 'electron', 'chatViewController.js'), 'utf8');
  const main = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
  assert.match(controller, /buildChatEvaluationObserverScript/);
  assert.match(controller, /chatEvaluationDrainScript/);
  assert.match(controller, /onEvaluation/);
  assert.match(controller, /startEvaluationDrain\(\)/);
  assert.match(controller, /CHAT_EVALUATION_DRAIN_INTERVAL_MS = 1000/);
  assert.match(controller, /evaluationDrainInFlight/);
  assert.match(controller, /\.finally\(\(\) => \{/);
  assert.match(main, /new ChatEvaluationJournal\(\)/);
  assert.match(main, /chatEvaluationJournal\.append\(workspace, correlated\)/);
  assert.match(main, /action: 'observation'/);
  assert.match(main, /run_id: event\.run_id/);
  assert.match(main, /wave_id: event\.wave_id/);
  assert.match(main, /observation_span/);
});
