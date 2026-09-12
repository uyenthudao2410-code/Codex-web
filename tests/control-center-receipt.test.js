const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { RPC_ACTIONS, RecoveryIpcClient } = require('../electron/services/recoveryIpc');

function listen(server) { return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve)); }

test('Execution Control Center sender uses exact managed connector attestation and bounded observation payload', async (t) => {
  const secret = 'n24-control-center-secret';
  const activationEpochId = 'activation-n24-control-center';
  const processInstanceId = 'process-n24-control-center';
  const serverInstanceId = 'server-n24-control-center';
  const contractSha256 = 'd'.repeat(64);
  const runId = 'a'.repeat(32);
  const waveId = 'b'.repeat(32);
  const snapshotFingerprint = 'c'.repeat(64);
  let requests = 0;
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      requests += 1;
      assert.equal(request.headers.authorization, 'Bearer mcp-test-token');
      assert.equal(request.headers['x-coding-tools-client-id'], 'electron-control-center');
      assert.equal(request.headers['x-coding-tools-client-type'], 'electron');
      const attestation = String(request.headers['x-coding-tools-connector-attestation'] || '');
      const parts = attestation.split('|');
      const signature = parts.pop();
      const canonical = parts.join('|');
      assert.equal(parts[0], 'v1');
      assert.equal(parts[1], 'electron-control-center');
      assert.equal(parts[2], 'electron');
      assert.equal(parts[3], activationEpochId);
      assert.equal(parts[4], processInstanceId);
      assert.equal(parts[5], serverInstanceId);
      assert.equal(parts[6], contractSha256);
      assert.equal(signature, crypto.createHmac('sha256', secret).update(canonical, 'utf8').digest('hex'));
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      assert.equal(body.method, 'tools/call');
      assert.equal(body.params.name, 'task_control');
      assert.deepEqual(body.params.arguments, {
        action: 'observation', run_id: runId, wave_id: waveId,
        observation_span: {span_id: `execution-control-center:${snapshotFingerprint}`,
          stage: 'report_visible', source: 'electron_execution_control_center',
          measurement: 'observed_control_center_progress',
          clock_domain: `execution-control-center:${snapshotFingerprint}`,
          start_ms: 0, end_ms: 0, observer_plane: 'execution_control_center'}
      });
      const payload = JSON.stringify({jsonrpc: '2.0', id: body.id,
        result: {structuredContent: {control_center_receipt: {event_id: 'n24-control-center-event'}}}});
      response.writeHead(200, {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload)});
      response.end(payload);
    });
  });
  await listen(server);
  t.after(() => server.close());
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  orchestrator.settingsStore = {load: () => ({mcpPort: server.address().port})};
  orchestrator.secrets = {get: (name) => name === 'mcpAuthToken' ? 'mcp-test-token' : null};
  orchestrator.activationEpochId = activationEpochId;
  orchestrator.connectorAttestationSecret = secret;
  orchestrator.connectorAttestationBinding = {activationEpochId, processInstanceId, serverInstanceId, contractSha256};
  orchestrator.currentMcpHealth = async () => ({ready: true, activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId, instance_id: serverInstanceId, tool_contract: {sha256: contractSha256}});
  const result = await orchestrator.recordExecutionControlCenterProgress({run_id: runId, wave_id: waveId,
    snapshot_fingerprint: snapshotFingerprint});
  assert.equal(result.control_center_receipt.event_id, 'n24-control-center-event');
  assert.equal(requests, 1);
  orchestrator.connectorAttestationBinding = {...orchestrator.connectorAttestationBinding,
    processInstanceId: 'wrong-process-instance'};
  await assert.rejects(orchestrator.recordExecutionControlCenterProgress({run_id: runId, wave_id: waveId,
    snapshot_fingerprint: snapshotFingerprint}), {code: 'CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE'});
  assert.equal(requests, 1, 'mismatched binding must fail before any MCP request');
});

test('Control Center ingress remains a private Recovery IPC path and main UI only piggybacks it on the live panel read', () => {
  assert.equal(RPC_ACTIONS.includes('runtime.record_execution_control_center_progress'), true);
  assert.equal(typeof RecoveryIpcClient.prototype.recordExecutionControlCenterProgress, 'function');
  const root = path.resolve(__dirname, '..');
  const main = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
  const recoveryHost = fs.readFileSync(path.join(root, 'electron', 'services', 'recoveryHost.js'), 'utf8');
  assert.match(main, /executionControlCenterProgressObservation\(orchestration\)/);
  assert.match(main, /orchestrator\.recordExecutionControlCenterProgress\(progressObservation\)/);
  assert.match(recoveryHost, /'runtime\.record_execution_control_center_progress'/);
});
