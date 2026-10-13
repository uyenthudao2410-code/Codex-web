'use strict';
// Called only from the operator's already verified packaged controller.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const requireState = (condition, code) => { if (!condition) throw Object.assign(new Error(code), { code }); };
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const overlapScript = 'tests/fixtures/parallel-native-overlap-20261012/hold.cjs';

async function installCanaryApprovals({ enrollment, targets, expectedEpoch, observeActivation, approvalSet, fixtureManifestPath, onVerifiedTarget }) {
  requireState(['codex-build', 'overlap'].includes(approvalSet) && /^activation-[A-Za-z0-9_-]+$/.test(expectedEpoch || ''), 'EXACT_CANARY_APPROVAL_ARGUMENTS_REQUIRED');
  const activation = await observeActivation();
  requireState(activation.activation_epoch_id === expectedEpoch && activation.state === 'READY'
    && activation.admission_open === true, 'EXACT_READY_ACTIVATION_REQUIRED');
  const manifest = JSON.parse(fs.readFileSync(fixtureManifestPath, 'utf8').replace(/^\uFEFF/, ''));
  requireState(manifest.prepared === true, 'PREPARED_CANARY_FIXTURE_REQUIRED');
  const selected = approvalSet === 'codex-build' ? targets.filter(item => path.basename(item.workspace_path) === 'Codex-web') : targets;
  requireState(selected.length === (approvalSet === 'codex-build' ? 1 : 2), 'EXACT_CANARY_TARGET_COUNT_REQUIRED');
  const records = [];
  for (const target of selected) {
    const label = path.basename(target.workspace_path);
    requireState(['Codex-web', 'Autocad'].includes(label), 'EXACT_AUTHORIZED_ROOT_REQUIRED');
    const prepared = approvalSet === 'codex-build' ? manifest : manifest.targets?.find(item => item.workspace_label === label);
    const relative = approvalSet === 'codex-build' ? 'tests/fixtures/native-first-canary/trusted-build.js' : overlapScript;
    const file = path.join(target.workspace_path, relative);
    const record = prepared?.files?.find(item => item.path === relative);
    requireState(record && sha(file) === record.sha256 && fs.statSync(file).size === record.size_bytes, 'EXACT_TRUSTED_FIXTURE_SOURCE_REQUIRED');
    const scope = { workspaceId: target.workspace_id, workspaceGeneration: target.workspace_generation };
    const existing = await enrollment.inspectLocalExecPolicy(scope);
    requireState(existing.state === 'enabled' && existing.workspace_id === target.workspace_id
      && existing.workspace_generation === target.workspace_generation && Array.isArray(existing.native_argv_prefixes), 'EXACT_EXISTING_EXEC_POLICY_REQUIRED');
    const added = approvalSet === 'codex-build' ? ['node', 'trusted-build.js'] : ['node', overlapScript];
    const prefixes = [...existing.native_argv_prefixes.map(prefix => [...prefix])];
    if (!prefixes.some(prefix => JSON.stringify(prefix) === JSON.stringify(added))) prefixes.push(added);
    const current = await observeActivation();
    requireState(current.activation_epoch_id === expectedEpoch && current.state === 'READY' && current.admission_open === true, 'ACTIVATION_CHANGED_BEFORE_CANARY_APPROVAL');
    await enrollment.installStandingWorkspaceExecPolicy({ ...scope, executionMode: 'native_only',
      nativeArgvPrefixes: prefixes, probeSandbox: false, replaceExisting: true });
    const observed = await enrollment.inspectLocalExecPolicy(scope);
    requireState(observed.state === 'enabled' && observed.workspace_id === target.workspace_id
      && observed.workspace_generation === target.workspace_generation && observed.execution_mode === 'native_only'
      && JSON.stringify(observed.native_argv_prefixes) === JSON.stringify(prefixes), 'CANARY_APPROVAL_RECEIPT_NOT_EXACT');
    const verifiedTarget = { workspace_label: label, workspace_id: target.workspace_id, workspace_generation: target.workspace_generation,
      native_source_sha256: record.sha256, added_native_argv: added, added_native_cwd: approvalSet === 'codex-build' ? manifest.fixture : '',
      policy: observed };
    records.push(verifiedTarget);
    if (onVerifiedTarget) await onVerifiedTarget(verifiedTarget);
  }
  return { observed_at_ms: Date.now(), activation_epoch_id: expectedEpoch, approval_set: approvalSet,
    targets: records, existing_native_prefixes_preserved: true, no_vm_probe_performed: true };
}

module.exports = { installCanaryApprovals };
