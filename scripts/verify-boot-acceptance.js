// Offline consistency oracle, not a receipt issuer or lifecycle authority.
// Inputs are normalized observations from the operator's authenticated readers.
const fs = require('node:fs');
const crypto = require('node:crypto');

const MAX_BYTES = 256 * 1024;
const MAX_AGE_MS = 30_000;
const digest = (v) => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const id = (v) => typeof v === 'string' && /^[A-Za-z0-9._:-]{1,256}$/.test(v);
const integer = (v) => Number.isSafeInteger(v) && v > 0;
const roleValid = (v) => ['direct_legacy', 'central_executor'].includes(v);
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

function verifyBootAcceptance(expected, receipt, { nowMs = Date.now() } = {}) {
  const failures = [];
  const check = (ok, code) => { if (!ok) failures.push(code); };
  const e = expected || {};
  const r = receipt || {};
  const b = r.before || {};
  const a = r.after || {};
  const runtime = a.runtime || {};
  const client = r.client || {};
  const fresh = (at) => integer(nowMs) && integer(at) && at <= nowMs && nowMs - at <= MAX_AGE_MS;
  check(e.schema_version === 2 && r.schema_version === 2, 'SCHEMA_V2_REQUIRED');
  check(id(e.problem_id) && integer(e.problem_revision) && digest(e.criteria_fingerprint), 'EXPECTED_PROBLEM_INVALID');
  check(roleValid(e.execution_role), 'EXPECTED_ROLE_INVALID');
  check(['strict', 'exact_or_reviewed_compatible'].includes(e.connector_policy), 'CONNECTOR_POLICY_REQUIRED');
  check(r.problem_id === e.problem_id && r.problem_revision === e.problem_revision
    && r.criteria_fingerprint === e.criteria_fingerprint, 'PROBLEM_REVISION_MISMATCH');
  check(fresh(a.observed_at_ms) && fresh(client.observed_at_ms), 'OBSERVATION_STALE_OR_FUTURE');
  check(integer(b.boot_time_ms) && integer(a.boot_time_ms) && integer(b.observed_at_ms)
    && b.boot_time_ms <= b.observed_at_ms && b.observed_at_ms < a.boot_time_ms
    && a.boot_time_ms <= a.observed_at_ms, 'REBOOT_SEQUENCE_UNPROVEN');
  check(['restart', 'cold_power_on', 'fast_startup'].includes(a.boot_mode), 'BOOT_MODE_UNKNOWN');
  check(client.observed_at_ms >= a.boot_time_ms && client.observed_at_ms <= a.observed_at_ms,
    'CLIENT_NOT_IN_POST_BOOT_WINDOW');
  for (const field of ['device_id', 'endpoint_id', 'workspace_id']) {
    check(id(e[field]) && a[field] === e[field] && client[field] === e[field], `TARGET_${field.toUpperCase()}_MISMATCH`);
  }
  check(integer(e.workspace_generation) && a.workspace_generation === e.workspace_generation
    && client.workspace_generation === e.workspace_generation, 'WORKSPACE_GENERATION_MISMATCH');
  check(a.execution_role === e.execution_role && runtime.executionRole === e.execution_role, 'EXECUTION_ROLE_MISMATCH');
  check(digest(e.package_sha256) && a.package_sha256 === e.package_sha256
    && digest(e.executable_sha256) && a.host?.executable_sha256 === e.executable_sha256, 'PACKAGE_IDENTITY_MISMATCH');
  check(a.host?.runtime_mode === 'packaged' && integer(a.host?.pid)
    && id(a.host?.instance_id) && id(b.host?.instance_id)
    && a.host.instance_id !== b.host.instance_id
    && typeof a.host.process_start_token === 'string' && /^[1-9][0-9]{8,24}$/.test(a.host.process_start_token)
    && typeof b.host?.process_start_token === 'string' && /^[1-9][0-9]{8,24}$/.test(b.host.process_start_token)
    && a.host.process_start_token !== b.host.process_start_token, 'FRESH_PACKAGED_HOST_UNPROVEN');
  check(integer(a.host?.started_at_ms) && a.host.started_at_ms >= a.boot_time_ms
    && a.host.started_at_ms <= a.observed_at_ms
    && a.host.activation_epoch_id === runtime.activationEpoch?.activation_epoch_id, 'HOST_BOOT_EPOCH_MISMATCH');
  check(a.supervisor?.installed === true && a.supervisor?.state === 'healthy'
    && integer(a.supervisor?.pid) && fresh(a.supervisor?.observed_at_ms)
    && a.supervisor.observed_at_ms >= a.boot_time_ms && a.supervisor.observed_at_ms <= a.observed_at_ms
    && a.supervisor.last_host_pid === a.host?.pid && digest(e.supervisor_script_sha256)
    && a.supervisor.script_sha256 === e.supervisor_script_sha256, 'SUPERVISOR_UNPROVEN');
  check(e.startup_intent === 'enabled' && a.startup_intent === 'enabled', 'AUTOSTART_NOT_OPTED_IN');
  for (const component of ['recovery_host', 'coding_mcp']) {
    const revision = a.revisions?.[component];
    check(digest(e.revisions?.[component]) && revision?.running_revision === e.revisions[component]
      && revision?.disk_revision === e.revisions[component] && revision?.update_pending === false,
    `REVISION_${component.toUpperCase()}_MISMATCH`);
  }
  check(id(runtime.activationEpoch?.activation_epoch_id) && id(runtime.activationEpoch?.operation_id)
    && runtime.activationEpoch?.state === 'READY' && runtime.activationEpoch?.admission_open === true
    && runtime.updateIncomplete === false, 'ACTIVATION_NOT_READY');
  check(runtime.mcpRunning === true && runtime.nativeAlive === true
    && runtime.componentsReady === true && runtime.fullyReady === true, 'PRIMARY_RUNTIME_NOT_READY');
  check(id(runtime.process_instance_id) && id(runtime.server_instance_id)
    && client.process_instance_id === runtime.process_instance_id
    && client.server_instance_id === runtime.server_instance_id
    && client.activation_epoch_id === runtime.activationEpoch?.activation_epoch_id, 'CLIENT_RUNTIME_BINDING_MISMATCH');
  check(digest(e.contract_sha256) && runtime.toolContract?.sha256 === e.contract_sha256
    && client.contract_sha256 === e.contract_sha256, 'CLIENT_CONTRACT_MISMATCH');
  check(client.tool === 'workspace_context' && client.ok === true && client.completed === true
    && client.workspace_accessed === true && id(client.request_id), 'REAL_WORKSPACE_READ_UNPROVEN');
  check(r.manual_repair_count === 0 && Array.isArray(r.attempts) && r.attempts.length > 0
    && r.attempts.length <= 100 && r.attempts.every((item) => id(item?.operation_id)
      && ['failed', 'succeeded'].includes(item?.outcome)), 'ATTEMPT_HISTORY_OR_MANUAL_REPAIR_INVALID');
  const lastAttempt = Array.isArray(r.attempts) ? r.attempts.at(-1) : null;
  check(lastAttempt?.outcome === 'succeeded' && lastAttempt?.operation_id === runtime.activationEpoch?.operation_id,
    'FINAL_ATTEMPT_NOT_SUCCESSFUL_ACTIVATION');
  if (e.execution_role === 'central_executor') {
    const route = a.central_route || {};
    check(runtime.localReady === true && runtime.centralConnected === true && runtime.authorityReady === true
      && fresh(route.observed_at_ms) && route.observed_at_ms >= a.boot_time_ms && route.observed_at_ms <= a.observed_at_ms
      && integer(route.policy_expires_at_ms) && route.policy_expires_at_ms > nowMs
      && route.authority_ready === true && route.admission_open === true,
    'CENTRAL_ROUTE_NOT_READY');
    check(id(e.binding_id) && id(e.principal_id) && route.binding_id === e.binding_id
      && client.binding_id === e.binding_id && route.principal_id === e.principal_id
      && client.principal_id === e.principal_id && route.workspace_id === e.workspace_id
      && route.workspace_generation === e.workspace_generation && route.device_id === e.device_id
      && route.endpoint_id === e.endpoint_id, 'CENTRAL_BINDING_MISMATCH');
    check(client.connector_rediscovered === true && fresh(client.connector_observed_at_ms)
      && client.connector_observed_at_ms >= a.boot_time_ms
      && client.connector_observed_at_ms <= client.observed_at_ms, 'CENTRAL_CLIENT_DISCOVERY_UNPROVEN');
  } else if (e.execution_role === 'direct_legacy') {
    check(runtime.tunnelRunning === true, 'DIRECT_TUNNEL_NOT_READY');
    const strict = runtime.connectorRediscovered === true && fresh(runtime.connector_observed_at_ms)
      && runtime.connectorContractState === 'CURRENT_ACKNOWLEDGED'
      && runtime.connectorContractAcknowledgedSha256 === e.contract_sha256;
    const compatible = e.connector_policy === 'exact_or_reviewed_compatible'
      && runtime.connectorContractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
      && runtime.connectorCompatibilityAcknowledged === true && fresh(runtime.connector_observed_at_ms)
      && digest(e.reviewed_ack_sha256) && runtime.connectorContractAcknowledgedSha256 === e.reviewed_ack_sha256;
    check(runtime.connectorRefreshRequired === false && runtime.connector_observed_at_ms >= a.boot_time_ms
      && runtime.connector_observed_at_ms <= a.observed_at_ms && (strict || compatible), 'DIRECT_CONNECTOR_UNPROVEN');
  }
  return {
    schema_version: 2, kind: 'boot_acceptance_consistency_report',
    status: failures.length ? 'NOT_PROVEN' : 'EVIDENCE_CONSISTENT', failures,
    authority_granted: false, live_accepted: false, receipt_authenticity_verified: false,
    required_external_gate: 'Controller must verify original reader/client provenance and exact criterion coverage.'
  };
}

function readPacket(file) {
  const stat = fs.lstatSync(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_BYTES) throw new Error('INPUT_INVALID');
  const fd = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0));
  try {
    if (!fs.fstatSync(fd).isFile()) throw new Error('INPUT_INVALID');
    const buffer = Buffer.alloc(MAX_BYTES + 1);
    let length = 0;
    while (length < buffer.length) {
      const read = fs.readSync(fd, buffer, length, buffer.length - length, null);
      if (!read) break;
      length += read;
    }
    if (length > MAX_BYTES) throw new Error('INPUT_INVALID');
    const bytes = buffer.subarray(0, length);
    return { value: JSON.parse(bytes.toString('utf8')), sha256: hash(bytes) };
  } finally { fs.closeSync(fd); }
}

function main(argv) {
  try {
    if (argv.length !== 2) throw new Error('INPUT_INVALID');
    const expected = readPacket(argv[0]);
    const receipt = readPacket(argv[1]);
    const result = verifyBootAcceptance(expected.value, receipt.value);
    process.stdout.write(JSON.stringify({ ...result, expected_sha256: expected.sha256, receipt_sha256: receipt.sha256 }) + '\n');
    return result.status === 'EVIDENCE_CONSISTENT' ? 0 : 1;
  } catch {
    // Never echo paths, JSON values, credentials or parser error excerpts.
    process.stdout.write(JSON.stringify({ status: 'INVALID_INPUT', authority_granted: false, live_accepted: false }) + '\n');
    return 2;
  }
}

if (require.main === module) process.exitCode = main(process.argv.slice(2));
module.exports = { verifyBootAcceptance };
