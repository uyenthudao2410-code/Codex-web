#!/usr/bin/env node
'use strict';

// Small process fixture for the control-plane exec lane.  It intentionally
// owns the real RecoveryIpcServer and RuntimeOrchestrator boundary while using
// a deterministic HTTP MCP peer for the local Coding Tools process.  The
// Python node-agent test talks to this process only through the descriptor
// written by RecoveryIpcServer; no Recovery descriptor/token crosses the
// Python boundary.

const fs = require('node:fs');
const crypto = require('node:crypto');
const http = require('node:http');
const path = require('node:path');
const zlib = require('node:zlib');

const { createDevelopmentPaths } = require('../scripts/dev-ui-lifecycle');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { RecoveryHost } = require('../electron/services/recoveryHost');
const { RecoveryIpcServer } = require('../electron/services/recoveryIpc');

function fail(code, message = code) {
  const error = Object.assign(new Error(message), { code });
  throw error;
}

function argumentValue(argv, name) {
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === name) return String(argv[index + 1] || '');
    if (String(argv[index] || '').startsWith(`${name}=`)) return String(argv[index]).slice(name.length + 1);
  }
  return '';
}

function readFixture(argv) {
  const file = path.resolve(argumentValue(argv, '--fixture'));
  if (!file) fail('FIXTURE_ARGUMENT_MISSING');
  const value = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('FIXTURE_INVALID');
  for (const field of ['app_data', 'app_root', 'workspace', 'device_id', 'activation_epoch_id', 'mcp_token', 'ready_file', 'observation_file']) {
    if (typeof value[field] !== 'string' || !value[field].trim()) fail(`FIXTURE_${field.toUpperCase()}_MISSING`);
  }
  return { ...value, fixture_file: file };
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function readObservation(file) {
  try {
    const value = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (value && typeof value === 'object' && !Array.isArray(value) && value.schema_version === 1) {
      return value;
    }
  } catch { /* first launch or an incomplete prior crash */ }
  return null;
}

function sendJson(response, status, value) {
  const body = JSON.stringify(value);
  response.writeHead(status, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  });
  response.end(body);
}

function requestBody(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    request.on('data', (chunk) => {
      total += chunk.length;
      if (total > 512 * 1024) {
        request.destroy();
        reject(Object.assign(new Error('request too large'), { code: 'FIXTURE_REQUEST_TOO_LARGE' }));
        return;
      }
      chunks.push(chunk);
    });
    request.on('error', reject);
    request.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch (error) { reject(error); }
    });
  });
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function exactPatchResult(fixture, patchEnvelope, workspaceRoot) {
  if (typeof patchEnvelope !== 'string' || !patchEnvelope) fail('FIXTURE_PATCH_INVALID');
  const lines = patchEnvelope.replace(/\r\n/g, '\n').split('\n');
  if (lines.at(-1) === '') lines.pop();
  if (lines.length < 5 || lines[0] !== '*** Begin Patch' || lines.at(-1) !== '*** End Patch'
    || !lines[1].startsWith('*** Write Exact File: ') || !lines[2].startsWith('@@ ')) {
    fail('FIXTURE_PATCH_INVALID');
  }
  const relativePath = lines[1].slice('*** Write Exact File: '.length);
  if (!relativePath || relativePath.startsWith('/') || relativePath.includes('\\')
    || relativePath.split('/').some((part) => !part || part === '.' || part === '..')) {
    fail('FIXTURE_PATCH_PATH_INVALID');
  }
  const metadata = Object.fromEntries(lines[2].slice(3).split(' ').map((token) => {
    const separator = token.indexOf('=');
    return separator > 0 ? [token.slice(0, separator), token.slice(separator + 1)] : ['', ''];
  }));
  if (metadata.encoding !== 'zlib-base64' || !/^[a-f0-9]{64}$/.test(metadata.preimage_sha256 || '')
    || !/^[a-f0-9]{64}$/.test(metadata.postimage_sha256 || '')) {
    fail('FIXTURE_PATCH_METADATA_INVALID');
  }
  const chunks = lines.slice(3, -1);
  if (!chunks.length || chunks.some((line) => !line.startsWith('+'))) fail('FIXTURE_PATCH_PAYLOAD_INVALID');
  let postimage;
  try {
    postimage = zlib.inflateSync(Buffer.from(chunks.map((line) => line.slice(1)).join(''), 'base64'));
  } catch {
    fail('FIXTURE_PATCH_PAYLOAD_INVALID');
  }
  if (sha256(postimage) !== metadata.postimage_sha256) fail('FIXTURE_PATCH_POSTIMAGE_MISMATCH');
  const root = path.resolve(workspaceRoot);
  const target = path.resolve(root, relativePath);
  if (target !== root && !target.startsWith(`${root}${path.sep}`)) fail('FIXTURE_PATCH_PATH_INVALID');
  const current = fs.readFileSync(target);
  if (sha256(current) !== metadata.preimage_sha256) fail('FIXTURE_PATCH_PREIMAGE_MISMATCH');
  fs.writeFileSync(target, postimage);
  return {
    path: relativePath,
    preimage_sha256: metadata.preimage_sha256,
    postimage_sha256: metadata.postimage_sha256,
    bytes_written: postimage.length,
  };
}

function documentWorkflowResult(fixture, args, workspaceRoot) {
  const action = String(args?.action || '');
  const targetRelative = String(args?.target || '');
  const sourceRelative = args?.source == null ? null : String(args.source);
  if (!['create', 'convert'].includes(action)
    || !targetRelative || targetRelative.startsWith('/') || targetRelative.includes('\\')
    || targetRelative.split('/').some((part) => !part || part === '.' || part === '..')) {
    fail('FIXTURE_DOCUMENT_REQUEST_INVALID');
  }
  if (action === 'convert' && (!sourceRelative || sourceRelative.startsWith('/') || sourceRelative.includes('\\')
    || sourceRelative.split('/').some((part) => !part || part === '.' || part === '..'))) {
    fail('FIXTURE_DOCUMENT_SOURCE_INVALID');
  }
  const root = path.resolve(workspaceRoot);
  const target = path.resolve(root, targetRelative);
  if (target !== root && !target.startsWith(`${root}${path.sep}`)) fail('FIXTURE_DOCUMENT_PATH_INVALID');
  if (action === 'convert') {
    const source = path.resolve(root, sourceRelative);
    if (source !== root && !source.startsWith(`${root}${path.sep}`)) fail('FIXTURE_DOCUMENT_PATH_INVALID');
    if (!fs.existsSync(source) || !fs.statSync(source).isFile()) fail('FIXTURE_DOCUMENT_SOURCE_MISSING');
  }
  if (fs.existsSync(target) && args.overwrite !== true) fail('FIXTURE_DOCUMENT_TARGET_EXISTS');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const content = action === 'create'
    ? Buffer.from(String(args.content || ''), 'utf8')
    : Buffer.from(`converted:${sourceRelative}\n`, 'utf8');
  fs.writeFileSync(target, content);
  return {
    action,
    result: {
      target: targetRelative,
      size: content.length,
      format: path.extname(targetRelative).slice(1).toLowerCase()
    }
  };
}

function identity(fixture) {
  return {
    activation_epoch_id: fixture.activation_epoch_id,
    process_instance_id: fixture.process_instance_id || 'process-recovery-exec-fixture-001',
    server_instance_id: fixture.server_instance_id || 'server-recovery-exec-fixture-001',
    tool_contract_sha256: fixture.tool_contract_sha256 || 'a'.repeat(64)
  };
}

function createMcpServer(fixture, observation) {
  const command = {
    command_id: fixture.command_id || 'command-recovery-exec-fixture-001',
    job_id: fixture.job_id || 'job-recovery-exec-fixture-001',
    run_id: fixture.run_id || 'run-recovery-exec-fixture-001',
    wave_id: fixture.wave_id || 'wave-recovery-exec-fixture-001'
  };
  let execRuns = 0;
  let patchRuns = 0;
  let documentRuns = 0;
  const server = http.createServer(async (request, response) => {
    if (request.headers.authorization !== `Bearer ${fixture.mcp_token}`) {
      sendJson(response, 401, { error: 'unauthorized' });
      return;
    }
    if (request.method === 'GET' && request.url === '/__control/health') {
      sendJson(response, 200, {
        ready: true,
        workspace: fixture.workspace,
        device_id: fixture.device_id,
        activation_epoch_id: fixture.activation_epoch_id,
        process_instance_id: identity(fixture).process_instance_id,
        instance_id: identity(fixture).server_instance_id,
        tool_contract: { sha256: identity(fixture).tool_contract_sha256 }
      });
      return;
    }
    if (request.method !== 'POST' || request.url !== '/mcp') {
      sendJson(response, 404, { error: 'not found' });
      return;
    }
    let body;
    try { body = await requestBody(request); }
    catch { sendJson(response, 400, { error: 'invalid json' }); return; }
    const name = String(body?.params?.name || '');
    const args = body?.params?.arguments && typeof body.params.arguments === 'object'
      ? body.params.arguments : {};
    observation.mcp_calls.push({
      name,
      operation: name === 'command_control'
        ? String(args.action || '')
        : name === 'exec_command'
          ? 'exec_run'
          : name === 'agent_workflow'
            ? 'apply_patch'
            : name === 'document_workflow'
              ? String(args.action || '')
            : 'bind',
      command_id: args.command_id || null,
      argv: name === 'exec_command' && Array.isArray(args.argv) ? [...args.argv] : null,
      has_attestation: Boolean(request.headers['x-coding-tools-connector-attestation']),
      client_id: String(request.headers['x-coding-tools-client-id'] || '')
    });
    writeJson(fixture.observation_file, observation);

    if (name === 'workspace_context') {
      sendJson(response, 200, { jsonrpc: '2.0', id: body.id, result: { structuredContent: { workspace: fixture.workspace } } });
      return;
    }
    if (name === 'document_workflow') {
      documentRuns += 1;
      const result = documentWorkflowResult(fixture, args, fixture.workspace);
      observation.document_runs = documentRuns;
      observation.document = result;
      writeJson(fixture.observation_file, observation);
      if (fixture.crash_after_document_result === true && documentRuns === 1) {
        observation.crash = {
          stage: 'after_document_result',
          pid: process.pid,
          operation: String(args.action || '')
        };
        writeJson(fixture.observation_file, observation);
        setImmediate(() => process.exit(74));
        return;
      }
      if (fixture.drop_after_document_result === true && documentRuns === 1) {
        response.destroy();
        return;
      }
      sendJson(response, 200, { jsonrpc: '2.0', id: body.id, result: { structuredContent: result } });
      return;
    }
    if (name === 'agent_workflow') {
      patchRuns += 1;
      const file = exactPatchResult(fixture, args.patch, fixture.workspace);
      const runId = fixture.patch_run_id || '1'.repeat(32);
      const waveId = fixture.patch_wave_id || '2'.repeat(32);
      const affectedFiles = [{ path: file.path, operation: 'update' }];
      const workflowResult = {
        workflow: 'custom',
        phase: 'execute',
        durable_idempotency: true,
        execution: {
          ok: true,
          status: 'passed',
          affected_files: affectedFiles,
          patch_results: [{ dry_run: false, clean: true, affected_files: affectedFiles }]
        },
        orchestration: {
          run_id: runId,
          wave_id: waveId,
          orchestration_state: 'ACCEPTING'
        },
        idempotency: {
          operation: 'agent_workflow',
          status: 'completed',
          idempotency_key: String(args.idempotency_key || ''),
          request_hash: sha256(JSON.stringify(args)),
          run_id: runId,
          wave_id: waveId,
          summary: {
            execution_ok: true,
            execution_status: 'passed',
            run_id: runId,
            wave_id: waveId,
            orchestration_state: 'ACCEPTING'
          }
        }
      };
      observation.patch_runs = patchRuns;
      observation.patch = { path: file.path, postimage_sha256: file.postimage_sha256 };
      writeJson(fixture.observation_file, observation);
      if (fixture.crash_after_patch_result === true && patchRuns === 1) {
        // The local MCP has applied the exact file but Recovery dies before
        // the approved-patch bridge can receive its result.  This is the
        // prepared/effect-unknown boundary; a restart must never redeliver.
        observation.crash = {
          stage: 'after_patch_result',
          pid: process.pid,
          operation: 'apply_patch'
        };
        writeJson(fixture.observation_file, observation);
        setImmediate(() => process.exit(73));
        return;
      }
      if (fixture.drop_after_patch_result === true && patchRuns === 1) {
        // Preserve the local effect but drop the response so the node records
        // an unknown bridge outcome without a second mutation attempt.
        response.destroy();
        return;
      }
      sendJson(response, 200, {
        jsonrpc: '2.0',
        id: body.id,
        result: { structuredContent: workflowResult }
      });
      return;
    }
    if (name === 'exec_command') {
      execRuns += 1;
      const terminalFirst = fixture.crash_after_terminal_result === true && execRuns === 1;
      const terminalImmediately = fixture.exec_terminal_first === true;
      if (fixture.crash_after_exec_run === true && execRuns === 1) {
        // Simulate the Recovery process dying after the local MCP accepted
        // exec_run but before the bridge can receive a result.  The sync
        // observation write is the only evidence intentionally left behind;
        // the node must classify the boundary as unknown and never redeliver.
        observation.crash = {
          stage: 'after_exec_run',
          pid: process.pid,
          operation: 'exec_run'
        };
        writeJson(fixture.observation_file, observation);
        setImmediate(() => process.exit(70));
        return;
      }
      if (fixture.drop_after_exec_run === true && execRuns === 1) {
        // Simulate the local MCP process disappearing after it accepted the
        // call but before the bridge receives a result.  The node must record
        // unknown/reconcile and never issue a replacement exec_run.
        response.destroy();
        return;
      }
      sendJson(response, 200, {
        jsonrpc: '2.0',
        id: body.id,
        result: {
          structuredContent: {
            command_id: command.command_id,
            status: execRuns === 1 && !terminalFirst && !terminalImmediately ? 'running' : 'exited',
            exit_code: execRuns === 1 && !terminalFirst && !terminalImmediately ? null : 0,
            stdout: execRuns === 1 && !terminalFirst && !terminalImmediately ? 'fixture process running\n' : 'fixture process completed\n',
            stderr: '',
            truncated: false,
            timed_out: false,
            output_refs: null,
            execution_owner: {
              job_id: command.job_id,
              run_id: command.run_id,
              wave_id: command.wave_id
            }
          }
        }
      });
      return;
    }
    if (name === 'command_control') {
      const action = String(args.action || '');
      const stopped = action === 'kill';
      const hadKill = observation.mcp_calls.some((item) => item && item.operation === 'kill');
      const alreadyStopped = action === 'poll' && hadKill;
      const keepRunning = action === 'poll' && fixture.poll_running_until_stop === true && !hadKill;
      if (stopped && fixture.crash_after_exec_stop === true && !observation.crash) {
        // The local MCP has accepted the exact stop request, but Recovery
        // dies before the bridge can receive its terminal response.  The
        // persisted observation is the only evidence left for the next
        // process, which must poll the same handle and never spawn again.
        observation.crash = {
          stage: 'after_exec_stop',
          pid: process.pid,
          operation: 'exec_stop'
        };
        writeJson(fixture.observation_file, observation);
        setImmediate(() => process.exit(72));
        return;
      }
      sendJson(response, 200, {
        jsonrpc: '2.0',
        id: body.id,
        result: {
          structuredContent: {
            command_id: command.command_id,
            status: stopped || alreadyStopped ? (alreadyStopped ? 'stopped' : 'terminated') : keepRunning ? 'running' : 'exited',
            exit_code: stopped || alreadyStopped || keepRunning ? (stopped || alreadyStopped ? 143 : null) : 0,
            stdout: stopped || alreadyStopped ? '' : keepRunning ? 'fixture process still running\n' : 'fixture process completed\n',
            stderr: stopped || alreadyStopped ? 'fixture process terminated\n' : '',
            truncated: false,
            timed_out: false,
            output_refs: null,
            execution_owner: {
              job_id: command.job_id,
              run_id: command.run_id,
              wave_id: command.wave_id
            }
          }
        }
      });
      return;
    }
    sendJson(response, 400, { error: 'unexpected tool' });
  });
  return { server, command };
}

async function main() {
  const fixture = readFixture(process.argv.slice(2));
  process.env.APPDATA = path.resolve(fixture.app_data);
  const appRoot = path.resolve(fixture.app_root);
  const paths = createDevelopmentPaths({
    appRoot,
    appData: process.env.APPDATA,
    electronExecutable: require('electron')
  });
  fs.mkdirSync(paths.dataRoot(), { recursive: true });
  const previousObservation = readObservation(fixture.observation_file);
  const observation = {
    ...(previousObservation || {}),
    schema_version: 1,
    pid: process.pid,
    mcp_calls: Array.isArray(previousObservation?.mcp_calls) ? previousObservation.mcp_calls : [],
    recovery_calls: Array.isArray(previousObservation?.recovery_calls) ? previousObservation.recovery_calls : [],
    launches: [
      ...(Array.isArray(previousObservation?.launches) ? previousObservation.launches : []),
      { pid: process.pid, started_at: new Date().toISOString() }
    ],
    stopped: false
  };
  writeJson(fixture.observation_file, observation);
  const { server: mcpServer, command } = createMcpServer(fixture, observation);
  await new Promise((resolve, reject) => {
    mcpServer.once('error', reject);
    mcpServer.listen(0, '127.0.0.1', resolve);
  });
  const mcpPort = Number(mcpServer.address()?.port || 0);
  const settings = {
    workspace: path.resolve(fixture.workspace),
    authorizedRoots: [path.resolve(fixture.workspace)],
    mcpPort,
    healthPort: 0,
    executionRole: 'central_executor',
    tunnelId: ''
  };
  const secrets = {
    get(name) { return name === 'mcpAuthToken' ? fixture.mcp_token : null; }
  };
  const deviceIdentity = {
    version: 1,
    device_id: fixture.device_id,
    display_name: 'Recovery exec process fixture',
    created_at: '2026-09-20T00:00:00.000Z'
  };
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({ ...settings }), save: () => ({ ...settings }) },
    secrets,
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    deviceIdentity,
    deviceInstanceId: 'fixture-device-instance-001',
    activationEpochId: fixture.activation_epoch_id
  });
  // Use the real RecoveryHost admission/identity wrapper without constructing
  // its unrelated supervisor, activation and UI services in this focused
  // process fixture.  The method still loads the real local policy and
  // registry, checks strict runtime/identity evidence, then calls the real
  // RuntimeOrchestrator.controlPlaneExec method below.
  orchestrator.lightweightSnapshot = async () => ({
    executionRole: 'central_executor',
    componentsReady: true,
    fullyReady: true,
    updateIncomplete: false,
    centralConnected: true,
    authorityReady: true,
    centralStatusReason: null
  });
  const recoveryHost = Object.create(RecoveryHost.prototype);
  recoveryHost.paths = paths;
  recoveryHost.deviceIdentity = deviceIdentity;
  recoveryHost.orchestrator = orchestrator;
  recoveryHost.mcpIdentityObservation = async () => ({
    mcp_ready: true,
    identity_current: true,
    activation_epoch_id: identity(fixture).activation_epoch_id,
    current_activation_epoch_id: identity(fixture).activation_epoch_id,
    mcp_process_instance_id: identity(fixture).process_instance_id,
    mcp_server_instance_id: identity(fixture).server_instance_id,
    tool_contract_sha256: identity(fixture).tool_contract_sha256
  });
  orchestrator.connectorAttestationSecret = fixture.attestation_secret || 'fixture-attestation-secret-001';
  orchestrator.connectorAttestationBinding = {
    activationEpochId: fixture.activation_epoch_id,
    processInstanceId: identity(fixture).process_instance_id,
    serverInstanceId: identity(fixture).server_instance_id,
    contractSha256: identity(fixture).tool_contract_sha256
  };
  const instanceId = 'recovery-exec-fixture-instance-001';
  const ipc = new RecoveryIpcServer({
    paths,
    instanceId,
    startedAt: new Date().toISOString(),
    deviceIdentity,
    deviceInstanceId: 'fixture-device-instance-001',
    activationEpochId: fixture.activation_epoch_id,
    log: { warn() {} },
    handlers: {
      'recovery.ping': async () => ({ ready: true, instance_id: instanceId }),
      'runtime.control_plane_exec': async (request) => {
        const call = {
          action: 'runtime.control_plane_exec',
          operation: request?.operation || null,
          request: request && typeof request === 'object' ? { ...request } : null
        };
        observation.recovery_calls.push(call);
        writeJson(fixture.observation_file, observation);
        const result = await RecoveryHost.prototype.controlPlaneExec.call(recoveryHost, request);
        call.result = result && typeof result === 'object'
          ? {
            operation_kind: result.operation_kind,
            action_id: result.action_id,
            attempt_id: result.attempt_id,
            task_id: result.task_id,
            writer_lease_generation: result.writer_lease_generation,
            local_handle: result.local_handle,
            policy_sha256: result.policy_sha256,
            actor: result.actor,
            facade_contract: result.facade_contract,
            command_id: result.command_id,
            job_id: result.job_id,
            status: result.status,
            runtime_identity: result.runtime_identity,
            response_sha256: result.response_sha256
          }
          : null;
        writeJson(fixture.observation_file, observation);
        if (fixture.crash_after_terminal_result === true && call.operation === 'exec_run') {
          // The local MCP already returned terminal evidence, but Recovery
          // dies before the node bridge receives/acknowledges it.  The node
          // must retain UNKNOWN rather than guessing that the terminal result
          // was delivered or issuing a second exec_run after restart.
          observation.crash = {
            stage: 'after_terminal_result',
            pid: process.pid,
            operation: 'exec_run'
          };
          writeJson(fixture.observation_file, observation);
          process.exit(71);
        }
        return result;
      },
      'runtime.control_plane_approved_patch': async (request) => {
        const call = {
          action: 'runtime.control_plane_approved_patch',
          operation: request?.operation || null,
          request: request && typeof request === 'object' ? { ...request } : null
        };
        observation.recovery_calls.push(call);
        writeJson(fixture.observation_file, observation);
        const result = await RecoveryHost.prototype.controlPlaneApprovedPatch.call(recoveryHost, request);
        call.result = result && typeof result === 'object'
          ? {
            operation_kind: result.operation_kind,
            action_id: result.action_id,
            attempt_id: result.attempt_id,
            task_id: result.task_id,
            writer_lease_generation: result.writer_lease_generation,
            local_handle: result.local_handle,
            patch_applied: result.patch_applied,
            local_semantic_acceptance: result.local_semantic_acceptance,
            policy_sha256: result.policy_sha256,
            actor: result.actor,
            runtime_identity: result.runtime_identity,
            facade_contract: result.facade_contract,
            file: result.file,
            response_sha256: result.response_sha256
          }
          : null;
        writeJson(fixture.observation_file, observation);
        if (fixture.crash_after_patch_result === true && call.operation === 'apply_patch') {
          // The MCP response and local file effect exist, but the Recovery
          // process terminates before the IPC caller receives the result.
          observation.crash = {
            stage: 'after_patch_result',
            pid: process.pid,
            operation: 'apply_patch'
          };
          writeJson(fixture.observation_file, observation);
          process.exit(73);
        }
        return result;
      },
      'runtime.control_plane_document_write': async (request) => {
        const call = {
          action: 'runtime.control_plane_document_write',
          operation: request?.operation || null,
          request: request && typeof request === 'object' ? { ...request } : null
        };
        observation.recovery_calls.push(call);
        writeJson(fixture.observation_file, observation);
        const result = await RecoveryHost.prototype.controlPlaneDocumentWrite.call(recoveryHost, request);
        call.result = result && typeof result === 'object'
          ? {
            operation_kind: result.operation_kind,
            action_id: result.action_id,
            attempt_id: result.attempt_id,
            task_id: result.task_id,
            writer_lease_generation: result.writer_lease_generation,
            local_handle: result.local_handle,
            operation: result.operation,
            target: result.target,
            source: result.source,
            result: result.result,
            policy_sha256: result.policy_sha256,
            actor: result.actor,
            runtime_identity: result.runtime_identity,
            facade_contract: result.facade_contract,
            response_sha256: result.response_sha256
          }
          : null;
        writeJson(fixture.observation_file, observation);
        if (fixture.crash_after_document_result === true && call.operation) {
          observation.crash = {
            stage: 'after_document_result',
            pid: process.pid,
            operation: call.operation
          };
          writeJson(fixture.observation_file, observation);
          process.exit(74);
        }
        return result;
      }
    }
  });
  const descriptor = await ipc.start();
  writeJson(fixture.ready_file, {
    schema_version: 1,
    pid: process.pid,
    mcp_port: mcpPort,
    descriptor_file: paths.recoveryHostDescriptorFile(),
    data_root: paths.dataRoot(),
    command
  });
  const shutdown = async () => {
    try { await ipc.stop(); } catch { /* best effort in fixture teardown */ }
    await new Promise((resolve) => mcpServer.close(() => resolve()));
    writeJson(fixture.observation_file, { ...observation, stopped: true });
  };
  let shuttingDown = null;
  const requestShutdown = () => {
    if (!shuttingDown) shuttingDown = shutdown().finally(() => process.exit(0));
    return shuttingDown;
  };
  process.once('SIGTERM', requestShutdown);
  process.once('SIGINT', requestShutdown);
  process.on('uncaughtException', (error) => {
    writeJson(fixture.observation_file, { ...observation, fatal: String(error?.stack || error) });
    process.exitCode = 1;
  });
  process.on('unhandledRejection', (error) => {
    writeJson(fixture.observation_file, { ...observation, fatal: String(error?.stack || error) });
    process.exitCode = 1;
  });
  void descriptor;
}

main().catch((error) => {
  const file = process.argv.includes('--fixture') ? argumentValue(process.argv.slice(2), '--fixture') : '';
  if (file) {
    try {
      const fixture = JSON.parse(fs.readFileSync(path.resolve(file), 'utf8'));
      writeJson(fixture.observation_file, { schema_version: 1, fatal: String(error?.stack || error) });
    } catch { /* no safe output path */ }
  }
  process.stderr.write(`${String(error?.stack || error)}\n`);
  process.exitCode = 1;
});
