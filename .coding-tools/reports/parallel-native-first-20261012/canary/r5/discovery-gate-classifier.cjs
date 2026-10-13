'use strict';

// Offline-only classifier for the connector-discovery gate.
// It reads a bounded status receipt and never calls a runtime or mutates it.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const MAX_BYTES = 2 * 1024 * 1024;
const HEX64 = /^[0-9a-f]{64}$/i;

function fail(code, message = code) {
  const error = new Error(message);
  error.code = code;
  throw error;
}

function readBounded(file) {
  if (!path.isAbsolute(file)) fail('ABSOLUTE_RECEIPT_REQUIRED');
  let stat;
  try { stat = fs.statSync(file); } catch { fail('RECEIPT_NOT_FOUND'); }
  if (!stat.isFile() || stat.size > MAX_BYTES) fail('BOUNDED_RECEIPT_REQUIRED');
  try { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
  catch { fail('RECEIPT_JSON_INVALID'); }
}

function text(value) { return String(value ?? '').trim(); }

function classify(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) fail('RECEIPT_OBJECT_REQUIRED');
  // Status reports commonly wrap the runtime observation under `receipt`.
  // Unwrap only this known envelope; no fields are inferred from unrelated data.
  if (receipt.receipt && typeof receipt.receipt === 'object' && !Array.isArray(receipt.receipt)) {
    receipt = receipt.receipt;
  }
  const runtime = receipt.runtime && typeof receipt.runtime === 'object' ? receipt.runtime : receipt;
  const activation = receipt.activation && typeof receipt.activation === 'object' ? receipt.activation : {};
  const role = text(runtime.executionRole || receipt.execution_role);
  if (!role) fail('EXECUTION_ROLE_MISSING');

  const state = text(runtime.connectorContractState || receipt.connector_state || receipt.connectorContractState);
  const central = role === 'central_executor';
  const centralFacts = {
    fully_ready: runtime.fullyReady === true,
    mcp_running: runtime.mcpRunning === true,
    native_alive: runtime.nativeAlive === true,
    authority_ready: runtime.authorityReady === true,
    central_connected: runtime.centralConnected === true,
    activation_ready: text(activation.state || activation.epoch_state) === 'READY',
    admission_open: activation.admission_open === true,
  };
  const centralReady = Object.values(centralFacts).every(Boolean);
  const strictDiscovery = !central && state === 'CHANGED_NEEDS_DISCOVERY';
  const connectorApplicable = !central;
  const result = {
    schema_version: 1,
    operation: 'offline_connector_discovery_gate_classification',
    ok: true,
    live_endpoint_called: false,
    runtime_mutated: false,
    execution_role: role,
    connector_state: state || null,
    connector_applicability: central ? 'not_applicable_central_executor' : 'direct_connector',
    strict_discovery_required: strictDiscovery,
    central_runtime_ready: centralReady,
    central_facts: centralFacts,
    recommendation: central
      ? (centralReady
        ? 'CLOSE_DIRECT_CONNECTOR_GATE_FOR_CENTRAL_RUNTIME; retain CHANGED_NEEDS_DISCOVERY as unused direct-path diagnostic.'
        : 'KEEP_CENTRAL_RUNTIME_CLOSED; missing central readiness fact.')
      : (strictDiscovery
        ? 'KEEP_DIRECT_CONNECTOR_GATE_OPEN; obtain attested current-process tools/list or server/discover receipt.'
        : 'NO_STRICT_DISCOVERY_CONCLUSION_FROM_THIS_RECEIPT.'),
  };
  const contractSha = text(receipt.tool_contract_sha256 || runtime.tool_contract_sha256);
  if (contractSha) result.tool_contract_sha256 = HEX64.test(contractSha) ? contractSha : null;
  return result;
}

function main(argv = process.argv) {
  const inputIndex = argv.indexOf('--input');
  const outputIndex = argv.indexOf('--output');
  if (inputIndex < 0 || outputIndex < 0) fail('INPUT_AND_OUTPUT_REQUIRED');
  const input = path.resolve(argv[inputIndex + 1] || '');
  const output = path.resolve(argv[outputIndex + 1] || '');
  if (!path.isAbsolute(output) || !output) fail('ABSOLUTE_OUTPUT_REQUIRED');
  const result = classify(readBounded(input));
  result.source = { path: input, sha256: crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex') };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${JSON.stringify({ ok: true, report_path: output, connector_applicability: result.connector_applicability })}\n`);
}

if (require.main === module) {
  try { main(); }
  catch (error) {
    process.stderr.write(`${error.code || 'DISCOVERY_CLASSIFICATION_FAILED'}\n`);
    process.exitCode = 1;
  }
}

module.exports = { classify, readBounded, MAX_BYTES };
