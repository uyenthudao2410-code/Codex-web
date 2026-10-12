'use strict';
// Additive v2: authority-only gap preparation, preserving original immutable helper/pin.
// Mutation phases require new exact authorization + fresh server closure/renewal pins.
// No VM/HCS termination, standalone Sandbox probe, authority, acceptance or test replay.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn, spawnSync, execFileSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../../..');
const services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const { ControlPlaneEnrollmentService, safeEnrollmentEnvironment } = require(path.join(services, 'controlPlaneEnrollment'));
const { loadExecBridgePolicy, resolveRegisteredWorkspaceRoot } = require(path.join(services, 'controlPlaneExecBridge'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const roots = {
  r9: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked'),
  r10: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked')
};
const expectedHead = '2c554f59cb7b8ffc86ce5e0e28076c792777642f';
const candidateTag = 'setup-exec-contract-1011-r10';
const target = { workspaceId: 'workspace_dda1d78e9a21402aa6213f72af64f788', workspaceGeneration: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' };
const bindingId = 'bind_3e05bf64cb3e4bab93d930ae1692bebb';
const deviceId = '72ceec2d-e3f2-472f-8e3c-99fffe053035';
const serverRevision = '395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5';
const serverPackageHash = 'sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419';
const serverHelperFile = path.join(__dirname, '../../store-delta/ubuntu-r10-store-authority-v3-local-proof.py');
const serverHelperHash = 'a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec';
const serviceGrantId = 'mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd';
const historicalDigest = '825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed';
const acceptanceDigest = '52be68a0dac2b56af51271fb8278bae1b04187f4573266c0051beabbec349309';
const awaitingAcceptance = ['95e909f0040a448faa9f1f3257e2ee2c'];
const waveId = 'c101beadfc6d4f2fbc13845052c84693';
const oldEpoch = 'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7';
const oldIdentities = {
  installation_id: 'e65d60602938af2f1c6e8cd9e8c59352ff2a5e24a268a45a98114726cdd8210d',
  instance_id: '6006092b7a061f47b20a0b27c1f34f1d', ui_instance_id: '2d80b88288e54bcc40f86f6ad45adcf6',
  owner: { pid: 1128, process_start_token: '134361911908524600' },
  ui: { pid: 25296, process_start_token: '134361911886531150' },
  native: { pid: 9212, process_start_token: '134361911931895600' },
  agent: { pid: 7108, process_start_token: '134361912150770020' }
};
const candidateHashes = {
  r9: { archive: '3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226', executable: 'fadc2feb4bb566b3fa22f22ea918c7175f39fa6b74eb7ccb9d2a1d6bab1b6211' },
  r10: { archive: 'c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9', executable: '6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f' }
};
const serviceHashes = {
  runtimePaths: 'a28fe23a10daa10baeb9c437ccee13cff2c1d28585d1c6daa3e5a23844d23474',
  recoveryIpc: '57e0154c4d9f80bcfc5fa95ec5c4643de436d8fe945e9b3ab884afd9b8faebc2',
  recoveryHostLauncher: '92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a',
  processIdentity: 'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f',
  fullCleanActivation: '881ffbdc57d4332ec1d6316199d2876d58821447b30cc861eade4c2c3d31baf1',
  controlPlaneEnrollment: 'c72766572150b5f2ce1e7ed7f976eb408ff3a75a7191951fddf0ccb7a28c6405',
  controlPlaneExecBridge: 'a699a8e035f56c9e588c6e1657863b78ca040a149d48424ba464c7a6942b73ff'
};
const parityFile = path.join(__dirname, '../candidate-parity-20261011T115907669Z.json');
const parityHash = 'c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c';
const freezeFile = path.join(__dirname, '../source-freeze-20261011T115648871Z.json');
const freezeHash = '030893e3e3f056debb1ee8b4213e4b4c1ae0fdb28af63ba8313567a3e231049f';
const censusFile = path.join(__dirname, '../../rollout-r9/final-census/census-2026-10-11T11-49-11-340Z.json');
const censusHash = '5c3079df5d0d20c81182de09fb2520a17efcdabe8c11db787b0222f14b7245b0';
const pinFile = path.join(__dirname, 'r9-identity-pin.json');
const evidence = path.join(__dirname, 'windows-activation-v2.jsonl');
const oldHelperHash = '8af0a6ac4a2dda2fc1a41dd075185fe609a0b1032ca1a81bbd517be24c009104';
const oldPinHash = 'c82a566d793278e0e831e20e8153fa48dbdb8d04db7fe3e1162c8245bbbab24b';
const oldOperation = 'full-clean-mv3qdvfq-a83d4dacc8a5de0588fb6ba5';
const oldReadyCommit = 'f85415b88bd6b9b1442a40fbb308d69d6aa4d7e0a8c9ee690a86ef5a5f22fe3e';
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const fail = code => { throw Object.assign(new Error(), { code }); };
const shaBytes = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => shaBytes(fs.readFileSync(file));
const safeText = value => String(value || '').replace(/[^a-zA-Z0-9_.:-]/g, '').slice(0, 128);
const pathKey = value => path.resolve(value).toLowerCase();
function readJson(file, limit = 1024 * 1024) {
  const bytes = fs.readFileSync(file); if (bytes.length > limit) fail('EVIDENCE_SIZE_EXCEEDED');
  return JSON.parse(bytes.toString('utf8'));
}
function emit(value) {
  const row = { observed_at: new Date().toISOString(), ...value };
  fs.appendFileSync(evidence, `${JSON.stringify(row)}\n`); process.stdout.write(`${JSON.stringify(row)}\n`); return row;
}
function pathsFor(tag) {
  if (!Object.hasOwn(roots, tag)) fail('CANDIDATE_TAG_INVALID');
  return createRuntimePaths({ dataRoot, appRoot: path.join(roots[tag], 'resources/app.asar'), resourcesRoot: path.join(roots[tag], 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(roots[tag], 'Coding Tools MCP.exe') });
}
function verifyResourceTree(tag, manifest) {
  const actualFiles = new Set();
  const walk = folder => {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
      const file = path.join(folder, entry.name), relative = path.relative(roots[tag], file).replaceAll('\\', '/');
      if (relative === 'resources/app.asar') continue;
      if (entry.isDirectory()) { walk(file); continue; }
      const cache = /^resources\/resources\/(.+)\/__pycache__\/([^/]+)\.cpython-312(?:\.opt-[0-2])?\.pyc$/.exec(relative);
      if (cache) {
        const parent = `resources/resources/${cache[1]}/${cache[2]}.py`;
        if (!entry.isFile() || manifest.entries[parent]?.type !== 'file' || sha(path.join(roots[tag], ...parent.split('/'))) !== manifest.entries[parent].sha256) fail('UNVERIFIED_RUNTIME_BYTECACHE');
        continue;
      }
      const expected = manifest.entries[relative]; if (!expected) fail('UNEXPECTED_CANDIDATE_RESOURCE');
      const digest = entry.isSymbolicLink() ? shaBytes(Buffer.from(fs.readlinkSync(file))) : entry.isFile() ? sha(file) : null;
      if (digest !== expected.sha256) fail('CANDIDATE_RESOURCE_CHANGED'); actualFiles.add(relative);
    }
  };
  walk(path.join(roots[tag], 'resources'));
  for (const file of Object.keys(manifest.entries)) {
    if (file.startsWith('app.asar/') || /\/__pycache__\//.test(file)) continue;
    if (!actualFiles.has(file)) fail('CANDIDATE_RESOURCE_REMOVED');
  }
}
function verifyFiles() {
  if (pathKey(process.env.APPDATA || '') !== pathKey(path.dirname(dataRoot))) fail('PROFILE_MISMATCH');
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  if (head !== expectedHead || sha(parityFile) !== parityHash || sha(freezeFile) !== freezeHash || sha(censusFile) !== censusHash) fail('IMMUTABLE_PROOF_CHANGED');
  const parity = readJson(parityFile, 32 * 1024 * 1024), freeze = readJson(freezeFile);
  if (parity.ok !== true || parity.repository_head !== head || parity.candidate_tag !== candidateTag || parity.source_freeze_sha256 !== freezeHash
    || parity.changed_source_parity.length !== 11 || parity.changed_source_parity.some(item => !item.byte_identical)
    || parity.unchanged_r9_native_resources.length !== 4 || parity.unchanged_r9_native_resources.some(item => !item.byte_identical)
    || parity.unchanged_r9_ui.length !== 7 || parity.unchanged_r9_ui.some(item => !item.byte_identical)
    || parity.unexpected_payload_differences.length || parity.expected_code_changes_not_observed.length || parity.source_drift_since_freeze.length || parity.candidate_bytecache_additions.length) fail('R10_PARITY_SCOPE_MISMATCH');
  if (freeze.source_files.length !== 22) fail('SOURCE_FREEZE_SCOPE_MISMATCH');
  for (const item of freeze.source_files) if (sha(path.join(repo, ...item.source.split('/'))) !== item.sha256) fail('FROZEN_CURRENT_SOURCE_CHANGED');
  for (const [name, expected] of Object.entries(serviceHashes)) if (sha(path.join(services, `${name}.js`)) !== expected) fail('ACTIVATION_SERVICE_SOURCE_CHANGED');
  for (const tag of ['r9', 'r10']) {
    const manifest = parity.packages[tag === 'r9' ? 'r9' : 'candidate'];
    if (pathKey(manifest.candidate) !== pathKey(roots[tag]) || sha(path.join(roots[tag], 'resources/app.asar')) !== candidateHashes[tag].archive || sha(pathsFor(tag).executablePath()) !== candidateHashes[tag].executable) fail('CANDIDATE_IDENTITY_CHANGED');
    verifyResourceTree(tag, manifest);
  }
  const old = readJson(censusFile);
  if (!old.ok || old.epoch.activation_epoch_id !== oldEpoch || old.active_package.installation_id !== oldIdentities.installation_id || old.active_package.instance_id !== oldIdentities.instance_id
    || ['host', 'ui', 'native', 'agent'].some(name => !sameProcessIdentity(oldIdentities[name === 'host' ? 'owner' : name], old.identities[name]))) fail('R9_FINAL_CENSUS_PIN_MISMATCH');
}
function argumentHash(name) {
  const prefix = `--${name}-sha256=`, args = process.argv.filter(value => value.startsWith(prefix));
  if (args.length !== 1 || !/^[a-f0-9]{64}$/.test(args[0].slice(prefix.length))) fail('EXPLICIT_APPROVAL_ARTIFACT_HASH_REQUIRED');
  return args[0].slice(prefix.length);
}
function pinnedArtifact(name, file, limit) {
  if (sha(file) !== argumentHash(name)) fail('APPROVAL_OR_SERVER_ARTIFACT_CHANGED'); return readJson(file, limit);
}
function authorizationGuard() {
  const file = path.join(__dirname, 'authorization.json'), value = pinnedArtifact('authorization', file, 32768);
  const actions = ['activate_r10', 'close_reopen_intake', 'renew_read_edit_exec_60m', 'metadata_sync', 'start_bounded_agent'];
  if (!process.argv.includes('--operator-approved') || value.kind !== 'operator_authorized_r10_transition' || value.approval_received !== true || value.candidate_tag !== candidateTag
    || value.profile !== 'web-mcp-assistant' || pathKey(value.repository_root || '') !== pathKey(repo) || value.host !== '100.116.112.22' || value.binding_id !== bindingId
    || value.duration_ms !== 3600000 || !Array.isArray(value.actions) || value.actions.slice().sort().join(',') !== actions.slice().sort().join(',')
    || value.parity_sha256 !== parityHash || value.app_asar_sha256 !== candidateHashes.r10.archive || value.executable_sha256 !== candidateHashes.r10.executable
    || value.windows_reboot !== false || value.vm_termination !== false) fail('NEW_EXACT_OPERATOR_AUTHORIZATION_REQUIRED');
  return { authorization_sha256: sha(file) };
}
function serverStateGuard(receipt) {
  if (receipt.ok !== true || receipt.host !== '100.116.112.22' || receipt.service !== 'codex-control-plane.service' || receipt.source_revision !== serverRevision
    || receipt.binding_id !== bindingId || !/^cp_[a-f0-9]{32}$/.test(receipt.service_instance_id || '')
    || receipt.state?.unsettled_actions !== 13 || receipt.state.historical_action_families_sha256 !== historicalDigest || receipt.state.patch_acceptances_sha256 !== acceptanceDigest
    || ['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks', 'unsettled_acceptances', 'target_unsettled_actions'].some(key => receipt.state[key] !== 0)
    || !/^[a-f0-9]{64}$/.test(receipt.state.all_action_task_intent_families_sha256 || '') || receipt.service_grant_preserved !== serviceGrantId
    || receipt.service_grant_changed !== false || receipt.service_restart !== false || receipt.ubuntu_code_deployed !== false) fail('EXACT_QUIESCENT_STORE_SERVER_EVIDENCE_REQUIRED');
}
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
function serverPreflightGuard() {
  if (sha(serverHelperFile) !== serverHelperHash) fail('PINNED_SERVER_AUTHORITY_HELPER_CHANGED');
  const receipt = pinnedArtifact('server-preflight', path.join(__dirname, 'server-preflight.json'), 65536), age = Date.now() - Number(receipt.observed_at_ms);
  if (receipt.phase !== 'r10_store_read_only_preflight' || receipt.ok !== true || receipt.remote_mutation !== false || receipt.source_revision !== serverRevision || receipt.package_source_sha256 !== serverPackageHash
    || receipt.admission !== 'recovery' || receipt.binding_id !== bindingId || !/^cp_[a-f0-9]{32}$/.test(receipt.service_instance_id || '') || receipt.service_grant_preserved !== serviceGrantId
    || receipt.service_grant_scopes?.slice().sort().join(',') !== 'control-plane.inventory,control-plane.patch,control-plane.read'
    || receipt.node?.device_id !== deviceId || !Number.isFinite(age) || age < 0 || age >= 600000
    || shaBytes(Buffer.from(JSON.stringify(canonical(receipt.state)))) !== receipt.state_sha256) fail('FRESH_PINNED_STORE_R9_PREFLIGHT_REQUIRED');
  return receipt;
}
function closureGuard() {
  const receipt = pinnedArtifact('closure', path.join(__dirname, 'server-intake-closed.json'), 65536), age = Date.now() - Number(receipt.observed_at_ms);
  serverStateGuard(receipt);
  if (receipt.phase !== 'intake_closed' || receipt.admission !== 'recovery' || !Number.isFinite(age) || age < 0 || age >= 600000) fail('FRESH_RECOVERY_INTAKE_CLOSURE_REQUIRED');
  return receipt;
}
function renewalGuard() {
  const receipt = pinnedArtifact('renewal', path.join(__dirname, 'server-authority-renewal.json'), 65536), assignment = receipt.policy_assignment;
  serverStateGuard(receipt);
  if (receipt.phase !== 'same_scope_renewal_complete' || receipt.duration_ms !== 3600000 || receipt.expires_at_ms !== receipt.requested_at_ms + 3600000
    || receipt.expires_at_ms <= Date.now() || receipt.requested_at_ms > Date.now() || receipt.admission !== 'recovery'
    || assignment?.workspace_id !== target.workspaceId || assignment.workspace_generation !== target.workspaceGeneration || assignment.device_id !== deviceId
    || assignment.expires_at_ms !== receipt.expires_at_ms || assignment.context_id !== receipt.context_id || !/^ctx_[a-f0-9]{32}$/.test(receipt.context_id || '')
    || !/^pilot_[a-f0-9]{32}$/.test(receipt.pilot_id || '')) fail('EXACT_UNEXPIRED_60M_RENEWAL_REQUIRED');
  return receipt;
}
function mutationGuard() {
  const approval = authorizationGuard(); verifyFiles(); const preflight = serverPreflightGuard(), closure = closureGuard(), renewal = renewalGuard();
  if (closure.service_instance_id !== renewal.service_instance_id || closure.state.historical_action_families_sha256 !== renewal.state.historical_action_families_sha256
    || closure.service_instance_id !== preflight.service_instance_id || closure.service_grant_preserved !== renewal.service_grant_preserved || renewal.observed_at_ms < closure.observed_at_ms
    || closure.observed_at_ms < preflight.observed_at_ms || closure.activation_epoch !== null || renewal.activation_epoch !== null
    || shaBytes(Buffer.from(JSON.stringify(canonical(closure.state)))) !== preflight.state_sha256
    || shaBytes(Buffer.from(JSON.stringify(canonical(renewal.state)))) !== preflight.state_sha256) fail('SERVER_CLOSURE_RENEWAL_CORRELATION_MISMATCH');
  approvedLocalPreparationGuard('closure', closure); approvedLocalPreparationGuard('renewal', renewal);
  return { ...renewal, ...approval, server_preflight_sha256: argumentHash('server-preflight'), closure_sha256: argumentHash('closure'), renewal_sha256: argumentHash('renewal') };
}
function approvedLocalPreparationGuard(kind, receipt) {
  const prefix = `--${kind}-local-proof-file=`, values = process.argv.filter(value => value.startsWith(prefix));
  if (values.length !== 1 || !/^server-preparation-proof-[0-9TZ]+\.json$/.test(values[0].slice(prefix.length))) fail('EXACT_SERVER_LOCAL_PROOF_FILE_REQUIRED');
  const file = path.join(__dirname, values[0].slice(prefix.length)), proof = readJson(file, 128 * 1024), observedAt = Date.parse(proof.observed_at), ageAtServer = receipt.observed_at_ms - observedAt;
  if (sha(file) !== receipt.local_preparation_sha256 || receipt.local_preparation_observed_at_ms !== observedAt || !/^[a-f0-9]{64}$/.test(receipt.initial_local_preparation_sha256 || '')
    || proof.helper_sha256 !== sha(__filename) || proof.kind !== 'r9_local_authority_preparation_v1' || proof.schema_version !== 1
    || !Number.isFinite(ageAtServer) || ageAtServer < 0 || ageAtServer >= 60000 || proof.repository_head !== expectedHead || proof.parity_sha256 !== parityHash
    || proof.target?.binding_id !== bindingId || proof.target.device_id !== deviceId || proof.target.workspace_id !== target.workspaceId || proof.target.workspace_generation !== target.workspaceGeneration
    || pathKey(proof.target.root || '') !== pathKey(repo) || proof.target.profile !== 'web-mcp-assistant' || proof.packages?.r9?.archive_sha256 !== candidateHashes.r9.archive || proof.packages.r9.executable_sha256 !== candidateHashes.r9.executable
    || proof.runtime_mutated !== false || proof.server_mutated !== false || proof.sandbox_probe_performed !== false || proof.agent?.state !== 'absent' || proof.agent.pid !== oldIdentities.agent.pid
    || proof.durable?.activation_epoch_id !== oldEpoch || proof.durable.operation_id !== oldOperation || proof.durable.ready_commit_digest !== oldReadyCommit || proof.durable.state !== 'READY' || proof.durable.admission_state !== 'OPEN'
    || proof.raw_epoch?.activation_epoch_id !== oldEpoch || proof.raw_epoch.operation_id !== oldOperation || proof.raw_epoch.ready_commit_digest !== oldReadyCommit || proof.raw_epoch.state !== 'READY' || proof.raw_epoch.admission_open !== true || proof.raw_epoch.update_incomplete !== false
    || proof.vm_zero_proof?.ok !== true || proof.vm_zero_proof.host?.count !== 0 || proof.vm_zero_proof.daemon?.count !== 0) fail('CORRELATED_OWNER_LOCAL_PREPARATION_PROOF_REQUIRED');
  for (const component of ['owner', 'ui', 'native']) if (proof[component]?.state !== 'live' || !sameProcessIdentity(oldIdentities[component], proof[component])) fail('CORRELATED_LOCAL_RUNTIME_IDENTITY_CHANGED');
  const prior = pinGuard();
  if (JSON.stringify(proof.pending_acceptance) !== JSON.stringify(prior.pending_acceptance)) fail('CORRELATED_PENDING_ACCEPTANCE_CHANGED');
  const census = proof.census;
  if (census?.ledger_mutated !== false || census.content_free !== true || census.snapshot?.integrity_check?.join(',') !== 'ok'
    || ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes'].some(key => census.counts?.[key] !== 0)
    || census.lifecycle?.awaiting_acceptance_runs?.join(',') !== awaitingAcceptance.join(',') || census.lifecycle.live_owned_runs.length || census.lifecycle.unexplained_active_runs || census.lifecycle.unbound_live_resource_residues) fail('CORRELATED_LOCAL_CENSUS_NOT_QUIESCENT');
  assertPoliciesUnchanged(proof.policies); return proof;
}
const trustedPowerShell = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
const vmHostScript = String.raw`$ErrorActionPreference='Stop'; $wanted=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); $found=@(Get-Process | Where-Object { $wanted -contains $_.ProcessName }); @{count=$found.Count;observer='GetProcessWindowsSandbox'} | ConvertTo-Json -Compress`;
const vmDaemonScript = String.raw`$ErrorActionPreference='Stop'; $found=@(Get-CimInstance Win32_Process -Filter "Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'"); @{count=$found.Count;observer='CimMxcBackend'} | ConvertTo-Json -Compress`;
function vmObservation(script, observer) {
  if (pathKey(fs.realpathSync.native(trustedPowerShell)) !== pathKey(trustedPowerShell)) fail('TRUSTED_OBSERVER_PATH_CHANGED');
  const begun = Date.now(), result = spawnSync(trustedPowerShell, ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, timeout: 5000, encoding: 'utf8', maxBuffer: 16384 });
  if (result.error || result.status !== 0) fail('VM_OBSERVATION_UNAVAILABLE');
  let value; try { value = JSON.parse(result.stdout.replace(/^\uFEFF/, '').trim()); } catch { fail('VM_OBSERVATION_MALFORMED'); }
  if (value.observer !== observer || !Number.isSafeInteger(value.count) || value.count < 0) fail('VM_OBSERVATION_MALFORMED');
  const done = Date.now(); if (done < begun || done - begun > 5000) fail('VM_OBSERVATION_NOT_FRESH');
  return { observer, begun_at_ms: begun, observed_at_ms: done, count: value.count, content_free: true };
}
function zeroVmProof(boundary) {
  // Independent host VM process and CIM backend observations; no probe or cleanup.
  const host = vmObservation(vmHostScript, 'GetProcessWindowsSandbox'), daemon = vmObservation(vmDaemonScript, 'CimMxcBackend');
  const ok = host.count === 0 && daemon.count === 0 && Date.now() - host.observed_at_ms <= 5000;
  const receipt = emit({ phase: 'independent_vm_zero_proof', boundary, ok, host, daemon, vm_termination_performed: false, sandbox_probe_performed: false });
  if (!ok) fail('OLD_R9_VM_OR_BACKEND_STILL_PRESENT'); return receipt;
}
function lastReceipt(phase, tag) {
  if (!fs.existsSync(evidence)) return null;
  return fs.readFileSync(evidence, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse).findLast(row => row.phase === phase && (!tag || row.tag === tag));
}
function descriptorIdentity(value) {
  return { installation_id: value.installation_id, instance_id: value.instance_id, owner_pid: value.owner_pid, owner_process_start_token: value.owner_process_start_token };
}
async function observedDescriptor() {
  let descriptor;
  try { descriptor = loadRecoveryDescriptor(pathsFor('r9')); }
  catch (error) {
    if (error.code !== 'RECOVERY_DESCRIPTOR_STALE') throw error;
    descriptor = readJson(pathsFor('r9').recoveryHostDescriptorFile(), 16384);
    if (descriptor.version !== 1 || descriptor.host !== '127.0.0.1' || descriptor.owner !== 'recovery-host' || !/^[a-f0-9]{64}$/.test(descriptor.installation_id || '') || !/^[a-f0-9]{32}$/.test(descriptor.instance_id || '') || !Number.isInteger(descriptor.owner_pid)) fail('RECOVERY_DESCRIPTOR_INVALID');
  }
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if (owner.state === 'unavailable' || (owner.state === 'live' && !sameProcessIdentity({ pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }, owner))) fail('RECOVERY_OWNER_IDENTITY_CHANGED');
  const tag = ['r9', 'r10'].find(value => descriptorMatchesInstallation(descriptor, pathsFor(value).runtimeIdentity()));
  if (!tag) fail('UNEXPECTED_INSTALLATION'); return { descriptor, owner, tag, paths: pathsFor(tag) };
}
function authenticated(observed) { return { client: new RecoveryIpcClient({ paths: observed.paths }), options: descriptorRequestOptions(observed.descriptor) }; }
function assertDescriptorPin(observed) {
  if (observed.tag !== 'r9' || observed.descriptor.installation_id !== oldIdentities.installation_id || observed.descriptor.instance_id !== oldIdentities.instance_id
    || observed.descriptor.owner_pid !== oldIdentities.owner.pid || observed.descriptor.owner_process_start_token !== oldIdentities.owner.process_start_token
    || (observed.owner.state === 'live' && !sameProcessIdentity(oldIdentities.owner, observed.owner))) fail('PINNED_R9_DESCRIPTOR_CHANGED');
}
async function agentObservation(tag) {
  const identityPin = tag === 'r9' ? oldIdentities.agent : lastReceipt('agent_spawned', 'r10')?.identity;
  if (!identityPin) return { identity: { state: 'absent', pid: null }, summary: null };
  const identity = await observeLifecycleProcessIdentity(identityPin.pid);
  if (identity.state === 'unavailable' || (identity.state === 'live' && !sameProcessIdentity(identityPin, identity))) fail('CONNECTED_AGENT_IDENTITY_CHANGED');
  const file = path.join(dataRoot, 'control-plane-connected-agent-status.json'), raw = fs.existsSync(file) ? readJson(file) : {};
  if (identity.state === 'live' && raw.agent_pid !== identity.pid) fail('CONNECTED_AGENT_STATUS_IDENTITY_CHANGED');
  return { identity, summary: { agent_pid: raw.agent_pid, last_iteration_state: safeText(raw.last_iteration_state), last_heartbeat_state: safeText(raw.last_heartbeat_state), last_heartbeat_at_ms: raw.last_heartbeat_at_ms } };
}
async function inspectRuntime(observed, phase = 'status') {
  if (observed.owner.state !== 'live') return emit({ phase, tag: observed.tag, descriptor: descriptorIdentity(observed.descriptor), owner: observed.owner });
  const r = authenticated(observed), status = await r.client.status({ ...r.options, fresh: true }), snapshot = await r.client.call('runtime.lightweight_snapshot', [], r.options), ui = status.electron_ui_recovery;
  const uiIdentity = ui?.pid ? await observeLifecycleProcessIdentity(ui.pid) : { state: 'absent', pid: null };
  if (uiIdentity.state === 'unavailable') fail('UI_IDENTITY_UNVERIFIED');
  const state = readJson(observed.paths.stateFile()), components = {};
  for (const name of ['native', 'tunnel']) {
    const pid = Number(state[`${name}Pid`] || 0), seen = pid ? await observeLifecycleProcessIdentity(pid) : { state: 'absent', pid: null };
    if (seen.state === 'unavailable' || (seen.state === 'live' && !sameProcessIdentity({ pid, process_start_token: state[`${name}ProcessStartToken`] }, seen))) fail('MANAGED_PROCESS_IDENTITY_CHANGED'); components[name] = seen;
  }
  const agent = await agentObservation(observed.tag), epoch = status.activation_epoch;
  return emit({ phase, tag: observed.tag, descriptor: descriptorIdentity(observed.descriptor), owner: observed.owner,
    ui: { pid: ui?.pid, instance_id: ui?.instance_id, alive: ui?.alive, registered: ui?.registered, ui_installation_id: ui?.ui_installation_id, identity: uiIdentity }, components,
    epoch: { activation_epoch_id: epoch?.activation_epoch_id, state: epoch?.state, admission_open: epoch?.admission_open, update_incomplete: epoch?.update_incomplete },
    fully_ready: snapshot.fullyReady, local_ready: snapshot.localReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady,
    update_incomplete: snapshot.updateIncomplete, failure_kind: safeText(snapshot.failureKind), agent: { identity: agent.identity, ...agent.summary } });
}
function censusSummary(value) {
  return { safe: value.safe, code: value.code, counts: value.counts, lifecycle: value.lifecycle, reason: value.reason,
    ledger_mutated: value.mutated_canonical_ledger, content_free: value.content_free, census_fingerprint: value.census_fingerprint,
    snapshot: { logical_sha256: value.snapshot.logical_sha256, integrity_check: value.snapshot.integrity_check } };
}
function assertCensus(value, liveAllowed = false) {
  if (value.lifecycle.awaiting_acceptance_runs.slice().sort().join(',') !== awaitingAcceptance.join(',')) fail('PENDING_ACCEPTANCE_SET_CHANGED');
  if (value.mutated_canonical_ledger || !value.content_free || value.snapshot.integrity_check?.join(',') !== 'ok') fail('CENSUS_CONTRACT_INVALID');
  if (['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes'].some(key => value.counts[key] !== 0)
    || value.lifecycle.live_owned_runs.length || value.lifecycle.unexplained_active_runs || value.lifecycle.unbound_live_resource_residues || value.lifecycle.projection_drift) fail('ACTIVE_JOB_OR_LANE_BLOCKS_ACTIVATION');
  if (liveAllowed && value.code === 'RUNTIME_BUSY' && value.lifecycle.blockers.join(',') === 'live_runtime_state_process') return;
  if (!value.safe) fail(value.code || 'CENSUS_REFUSED');
}
async function censusFor(observed, phase = 'census', holdExclusive = false) {
  const value = await canonicalLedgerCensus({ paths: observed.paths, workspace: repo, allowAcceptancePending: true, holdExclusive,
    pythonStatusFn: async () => ({ installed: true, command: observed.paths.portablePython(), prefixArgs: ['-B'] }) });
  emit({ phase, tag: observed.tag, ...censusSummary(value) }); return value;
}
const pendingReadCode = String.raw`import hashlib,json,sqlite3,sys
from pathlib import Path
database=Path(sys.argv[1]).resolve(strict=True)
source=sqlite3.connect(database.as_uri()+"?mode=ro",uri=True,timeout=5);source.execute("PRAGMA query_only=ON")
snapshot=sqlite3.connect(":memory:");source.backup(snapshot);source.close();snapshot.row_factory=sqlite3.Row;snapshot.execute("PRAGMA query_only=ON")
result={}
for table,key,value in (("runs","run_id",sys.argv[2]),("waves","wave_id",sys.argv[3])):
 rows=snapshot.execute(f"SELECT * FROM {table} WHERE {key}=?",(value,)).fetchall()
 if len(rows)!=1:raise SystemExit(2)
 result[table]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
snapshot.close();print(json.dumps(result,separators=(",",":")))`;
function assertPendingRecords(paths) {
  const result = spawnSync(paths.portablePython(), ['-B', '-I', '-c', pendingReadCode, path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), awaitingAcceptance[0], waveId], { windowsHide: true, timeout: 10000, encoding: 'utf8', maxBuffer: 16384 });
  if (result.error || result.status !== 0) fail('PENDING_ACCEPTANCE_RECORD_OBSERVATION_FAILED');
  let hashes; try { hashes = JSON.parse(result.stdout.trim()); } catch { fail('PENDING_ACCEPTANCE_RECORD_OBSERVATION_FAILED'); }
  const expected = readJson(censusFile).pending_acceptance.before;
  if (hashes.runs !== expected.runs.record_sha256 || hashes.waves !== expected.waves.record_sha256) fail('PENDING_ACCEPTANCE_RECORD_CHANGED');
  return { run_id: awaitingAcceptance[0], wave_id: waveId, run_record_sha256: hashes.runs, wave_record_sha256: hashes.waves, unchanged: true };
}
function policySafe(policy) { return { state: safeText(policy?.state), enabled: policy?.enabled === true, workspace_id: policy?.workspace_id, workspace_generation: policy?.workspace_generation,
  policy_sha256: policy?.policy_sha256, allowed_argv_prefix_count: policy?.allowed_argv_prefix_count, allowed_argv_prefixes_sha256: policy?.allowed_argv_prefixes_sha256 }; }
async function inspectPoliciesNoProbe(observed) {
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths }), files = await service.inspectStandingWorkspaceFilePolicies(), exec = await service.inspectLocalExecPolicy(), admitted = loadExecBridgePolicy(observed.paths);
  const root = resolveRegisteredWorkspaceRoot(observed.paths, admitted), policies = { file_read: policySafe(files.file_read), approved_patch: policySafe(files.approved_patch), exec: policySafe(exec) };
  const ready = item => item?.state === 'enabled' && item.enabled === true && item.workspace_id === target.workspaceId && item.workspace_generation === target.workspaceGeneration;
  if (pathKey(root) !== pathKey(fs.realpathSync.native(repo)) || admitted.workspace_id !== target.workspaceId || admitted.workspace_generation !== target.workspaceGeneration || admitted.device_id !== deviceId
    || admitted.authority_mode !== 'standing' || admitted.expires_at_ms !== null || admitted.policy_sha256 !== exec.policy_sha256 || !Object.values(policies).every(ready)) fail('STANDING_POLICY_TARGET_NOT_READY');
  return { ...policies, workspace_root_verified: true, standalone_probe_performed: false };
}
function pinGuard() {
  const pin = readJson(pinFile, 65536);
  if (sha(pinFile) !== oldPinHash || sha(path.join(__dirname, 'activate-r10.cjs')) !== oldHelperHash || pin.kind !== 'immutable_r9_identity_pin_for_r10' || pin.helper_sha256 !== oldHelperHash || pin.parity_sha256 !== parityHash || pin.repository_head !== expectedHead) fail('R9_ACTIVATION_PIN_CHANGED');
  return pin;
}
function assertPoliciesUnchanged(policies) {
  const pin = pinGuard();
  for (const kind of ['file_read', 'approved_patch', 'exec']) if (policies[kind].policy_sha256 !== pin.policies[kind].policy_sha256) fail('STANDING_POLICY_HASH_CHANGED');
  if (policies.exec.allowed_argv_prefixes_sha256 !== pin.policies.exec.allowed_argv_prefixes_sha256) fail('EXISTING_EXEC_ALLOWLIST_CHANGED');
}
async function r9PreparationObservation(observed) {
  assertDescriptorPin(observed);
  const r = authenticated(observed), status = await r.client.status({ ...r.options, fresh: true });
  const projection = await r.client.call('runtime.lightweight_snapshot', [], r.options), raw = await r.client.call('runtime.activation_epoch_status', [], r.options);
  const durable = readJson(observed.paths.activationEpochFile()).current, metadata = readJson(observed.paths.controlPlaneReadOnlyPolicyFile()), route = readJson(observed.paths.controlPlaneRouteEvidenceFile());
  const exactDurable = durable?.activation_epoch_id === oldEpoch && durable.operation_id === oldOperation && durable.state === 'READY' && durable.admission_state === 'OPEN' && durable.ready_commit_digest === oldReadyCommit && durable.error === null;
  const exactRaw = raw?.activation_epoch_id === oldEpoch && raw.operation_id === oldOperation && raw.state === 'READY' && raw.admission_open === true && raw.update_incomplete === false && raw.ready_commit_digest === oldReadyCommit && !raw.error && !raw.error_code;
  const revisions = [status.code_revision, status.electron_ui_revision, projection.codeRevision?.codingMcp];
  const expectedRevisions = ['919e2fd308bc6c0f408accdb04a9039c0d418e9d96b8a94696622e9702f67b5d', '9a3c20b510aebd92b7806b6cb6e5dd64a4cd4d00219b269e152bb4021d27e868', '17c21f8e7783c05572f42f662adf60b1ad94eb33be7e8e7f155bfbd2e90314c7'];
  const revisionsReady = revisions.every((value, index) => value?.state === 'current' && value.running_revision === expectedRevisions[index] && value.disk_revision === expectedRevisions[index] && !value.update_pending && !value.updatePending && !value.pending_revision);
  if (!exactDurable || !exactRaw || !revisionsReady || status.ready_adoption?.state !== 'adopted' || status.recovery_bootstrap !== null
    || status.full_clean_activation?.available !== true || status.full_clean_activation.state !== 'current' || status.full_clean_activation.activation_epoch_id !== oldEpoch
    || projection.executionRole !== 'central_executor' || projection.localReady !== true || projection.componentsReady !== true || projection.failureKind
    || status.runtime?.recovering !== false) fail('R9_LOCAL_PREPARATION_NOT_EXACT_READY_HISTORY');
  const ready = projection.fullyReady === true && projection.centralConnected === true && projection.authorityReady === true && projection.updateIncomplete === false;
  const projected = projection.activationEpoch;
  const metadataExact = metadata.enabled === true && metadata.device_id === deviceId && metadata.workspace_id === target.workspaceId && metadata.workspace_generation === target.workspaceGeneration;
  const staleRoute = route.device_id === deviceId && route.observed_at_ms > 0 && Date.now() - route.observed_at_ms > 60000;
  const gap = projection.fullyReady === false && projection.authorityReady === false && projection.updateIncomplete === true
    && projected?.activation_epoch_id === oldEpoch && projected.operation_id === oldOperation && projected.state === 'READY' && projected.admission_open === false && projected.update_incomplete === true && projected.error_code === 'RUNTIME_READINESS_INCOMPLETE'
    && status.runtime.central_status_reason === projection.centralStatusReason && metadataExact
    && ((projection.centralConnected === false && projection.centralStatusReason === 'CENTRAL_ROUTE_EVIDENCE_STALE' && staleRoute)
      || (projection.centralConnected === true && projection.centralStatusReason === 'CENTRAL_LOCAL_POLICY_NOT_READY' && route.policy_expires_at_ms <= Date.now()));
  if (!ready && !gap) fail('R9_PREPARATION_GAP_NOT_PROVEN_AUTHORITY_ONLY');
  const pick = (value, fields) => Object.fromEntries(fields.map(field => [field, value?.[field] ?? null]));
  return { classification: ready ? 'ready_current' : 'authority_only_read_model_closed',
    durable: pick(durable, ['activation_epoch_id', 'operation_id', 'state', 'admission_state', 'ready_commit_digest']),
    raw_epoch: pick(raw, ['activation_epoch_id', 'operation_id', 'state', 'admission_open', 'update_incomplete', 'ready_commit_digest']),
    projected_epoch: pick(projected, ['activation_epoch_id', 'operation_id', 'state', 'admission_open', 'update_incomplete', 'error_code']),
    projection: pick(projection, ['fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'centralStatusReason', 'updateIncomplete']),
    revisions: revisions.map(value => pick(value, ['state', 'running_revision', 'disk_revision', 'update_pending', 'pending_revision'])),
    metadata: pick(metadata, ['enabled', 'expires_at_ms', 'device_id', 'workspace_id', 'workspace_generation']),
    route: pick(route, ['device_id', 'observed_at_ms', 'policy_state', 'policy_expires_at_ms']),
    readiness_not_forged: true, local_admission_opened: false };
}
async function serverPreparationProof() {
  verifyFiles(); pinGuard(); const observed = await observedDescriptor(), row = await inspectRuntime(observed, 'server_preparation_identity_observation'); assertOldLiveRow(observed, row);
  const preparation = await r9PreparationObservation(observed), policies = await inspectPoliciesNoProbe(observed); assertPoliciesUnchanged(policies);
  const census = await censusFor(observed, 'server_preparation_census'); assertCensus(census, true); const pending = assertPendingRecords(observed.paths);
  if (row.agent.identity.state !== 'absent') fail('OLD_AGENT_MUST_REMAIN_ABSENT_FOR_OWNER_PREPARATION');
  const vm = zeroVmProof('server_preparation'), observedAt = new Date().toISOString();
  const proof = { kind: 'r9_local_authority_preparation_v1', schema_version: 1, observed_at: observedAt,
    target: { binding_id: bindingId, device_id: deviceId, workspace_id: target.workspaceId, workspace_generation: target.workspaceGeneration, root: repo, profile: 'web-mcp-assistant' },
    repository_head: expectedHead, parity_sha256: parityHash, packages: { r9: { archive_sha256: candidateHashes.r9.archive, executable_sha256: candidateHashes.r9.executable } },
    descriptor: row.descriptor, owner: row.owner, ui: row.ui.identity, native: row.components.native, agent: { state: 'absent', pid: oldIdentities.agent.pid }, ui_instance_id: row.ui.instance_id,
    ...preparation, census: censusSummary(census), pending_acceptance: pending, vm_zero_proof: vm, policies, helper_sha256: sha(__filename),
    runtime_mutated: false, server_mutated: false, sandbox_probe_performed: false };
  const file = path.join(__dirname, `server-preparation-proof-${observedAt.replace(/[^0-9TZ]/g, '')}.json`);
  fs.writeFileSync(file, `${JSON.stringify(proof, null, 2)}\n`, { flag: 'wx' }); emit({ phase: 'server_preparation_proof_saved', file, proof_sha256: sha(file), classification: preparation.classification, root_execution_required: true });
}
function assertOldLiveRow(observed, row) {
  assertDescriptorPin(observed);
  if (observed.owner.state !== 'live' || !sameProcessIdentity(oldIdentities.ui, row.ui.identity) || row.ui.instance_id !== oldIdentities.ui_instance_id
    || row.ui.ui_installation_id !== oldIdentities.installation_id || row.ui.registered !== true || row.ui.alive !== true || !sameProcessIdentity(oldIdentities.native, row.components.native)
    || row.components.tunnel.state !== 'absent' || row.epoch.activation_epoch_id !== oldEpoch || row.epoch.state !== 'READY'
    || (row.agent.identity.state === 'live' && !sameProcessIdentity(oldIdentities.agent, row.agent.identity))) fail('PINNED_R9_RUNTIME_IDENTITIES_OR_EPOCH_CHANGED');
}
async function freeze() {
  verifyFiles(); const observed = await observedDescriptor(), row = await inspectRuntime(observed, 'freeze_observation'); assertOldLiveRow(observed, row);
  const census = await censusFor(observed, 'freeze_census'); assertCensus(census, true);
  const policies = await inspectPoliciesNoProbe(observed), pending = assertPendingRecords(observed.paths), vm = zeroVmProof('freeze');
  const pin = { kind: 'immutable_r9_identity_pin_for_r10', observed_at: new Date().toISOString(), repository_head: expectedHead, parity_sha256: parityHash, helper_sha256: sha(__filename),
    ...oldIdentities, old_epoch: oldEpoch, policies, census: censusSummary(census), pending_acceptance: pending, vm_zero_proof: vm, runtime_mutated: false, server_mutated: false };
  fs.writeFileSync(pinFile, `${JSON.stringify(pin, null, 2)}\n`, { flag: 'wx' }); emit({ phase: 'r9_pin_frozen', tag: 'r9', pin_file: pinFile, pin_sha256: sha(pinFile), runtime_mutated: false });
}
async function preflight() {
  verifyFiles(); pinGuard(); const observed = await observedDescriptor(), row = await inspectRuntime(observed, 'preflight'); assertOldLiveRow(observed, row);
  const preparation = await r9PreparationObservation(observed); emit({ phase: 'r9_preparation_observation', ...preparation });
  assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed)); assertCensus(await censusFor(observed, 'preflight_census'), true); assertPendingRecords(observed.paths); zeroVmProof('preflight');
  return observed;
}
async function effectBoundary(name, observed, { uiMayBeAbsent = false, nativeMayBeAbsent = false, agentMustBeAbsent = false, heldCensus = null } = {}) {
  mutationGuard(); const current = await observedDescriptor(); assertDescriptorPin(current);
  for (const [component, mayBeAbsent] of [['ui', uiMayBeAbsent], ['native', nativeMayBeAbsent], ['agent', agentMustBeAbsent]]) {
    const identity = await observeLifecycleProcessIdentity(oldIdentities[component].pid);
    if (identity.state === 'unavailable' || (identity.state === 'live' && !sameProcessIdentity(oldIdentities[component], identity)) || (identity.state === 'absent' && !mayBeAbsent) || (component === 'agent' && agentMustBeAbsent && identity.state !== 'absent')) fail('EFFECT_BOUNDARY_IDENTITY_CHANGED');
  }
  if (current.owner.state !== 'live' || !sameProcessIdentity(oldIdentities.owner, current.owner)) fail('EFFECT_BOUNDARY_HOST_CHANGED');
  if (!uiMayBeAbsent && !nativeMayBeAbsent) await r9PreparationObservation(current);
  const census = heldCensus || await censusFor(observed, `${name}_census`); assertCensus(census, nativeMayBeAbsent !== true); assertPendingRecords(observed.paths);
  // Last observations immediately before the effect; the old endpoint lacks cleanup.
  return zeroVmProof(name);
}
async function activate() {
  mutationGuard(); const before = await preflight(), agent = await agentObservation('r9');
  if (agent.identity.state === 'live') {
    if (agent.summary.last_iteration_state !== 'completed') fail('OLD_CONNECTED_AGENT_NOT_QUIESCENT');
    await effectBoundary('before_exact_agent_retirement', before); const result = await terminateExactProcessTree(oldIdentities.agent, { includeDescendants: false }); emit({ phase: 'agent_retired', tag: 'r9', result, identity: oldIdentities.agent });
  }
  const r = authenticated(before); await effectBoundary('before_ui_recovery_suppression', before, { agentMustBeAbsent: true });
  await r.client.call('client.suppress_ui_recovery', [{ instance_id: oldIdentities.ui_instance_id, reason: 'operator_quit' }], r.options);
  const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
  await effectBoundary('before_exact_ui_stop', before, { agentMustBeAbsent: true });
  const signal = spawnSync(before.paths.executablePath(), [`--dev-ui-stop=${oldIdentities.ui_instance_id}`], { env, windowsHide: true, timeout: 15000, stdio: 'ignore' });
  if (signal.status !== 0) fail('EXACT_UI_STOP_SIGNAL_FAILED'); await waitForExactProcessExit(oldIdentities.ui, { timeoutMs: 15000 }); emit({ phase: 'ui_retired', tag: 'r9', identity: oldIdentities.ui });
  await effectBoundary('immediately_before_old_native_stop', before, { uiMayBeAbsent: true, agentMustBeAbsent: true });
  // r9 stop uses exact native ownership, but lacks r10 executor cleanup; zero proof is mandatory.
  await r.client.stop({ manual: true }, r.options); await waitForExactProcessExit(oldIdentities.native, { timeoutMs: 15000 }); emit({ phase: 'runtime_stopped', tag: 'r9', exact_native_identity_verified: true, vm_termination_performed: false });
  const census = await censusFor(before, 'stopped_exclusive_census', true);
  try {
    assertCensus(census); assertPendingRecords(before.paths);
    await effectBoundary('immediately_before_exact_host_retirement', before, { uiMayBeAbsent: true, nativeMayBeAbsent: true, agentMustBeAbsent: true, heldCensus: census });
    const result = await terminateExactProcessTree(oldIdentities.owner, { includeDescendants: false }); emit({ phase: 'host_retired', tag: 'r9', identity: oldIdentities.owner, result });
    mutationGuard(); for (const identity of [oldIdentities.owner, oldIdentities.ui, oldIdentities.native, oldIdentities.agent]) if ((await observeLifecycleProcessIdentity(identity.pid)).state !== 'absent') fail('OLD_RUNTIME_NOT_FULLY_RETIRED');
    zeroVmProof('immediately_before_r10_spawn'); assertPendingRecords(before.paths);
    const child = spawn(pathsFor('r10').executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref(); emit({ phase: 'candidate_spawned', tag: 'r10', pid: child.pid, candidate: roots.r10, pending_acceptance_preserved: true });
  } finally { await census.release_exclusive_gate(); }
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    try { const live = await observedDescriptor(); if (live.tag === 'r10' && live.owner.state === 'live') { await inspectRuntime(live, 'candidate_started'); return; } }
    catch (error) { if (!['RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_DESCRIPTOR_MISSING', 'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_TIMEOUT'].includes(error.code)) throw error; }
    await wait(500);
  }
  fail('R10_START_NOT_OBSERVED');
}
async function currentR10() {
  const observed = await observedDescriptor(); if (observed.tag !== 'r10' || observed.owner.state !== 'live') fail('R10_HOST_NOT_LIVE');
  const started = lastReceipt('candidate_started', 'r10');
  if (!started || JSON.stringify(descriptorIdentity(observed.descriptor)) !== JSON.stringify(started.descriptor) || !sameProcessIdentity(observed.owner, started.owner)) fail('NEW_R10_DESCRIPTOR_IDENTITY_CHANGED');
  return observed;
}
async function policy() {
  const renewal = mutationGuard(), observed = await currentR10(); assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed));
  assertCensus(await censusFor(observed, 'policy_preflight_census'), true); assertPendingRecords(observed.paths); zeroVmProof('before_optional_metadata_sync');
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths }); mutationGuard();
  const metadata = await service.installReadOnlyPolicyAssignment({ ...target, replaceExisting: true });
  if (metadata.expires_at_ms !== renewal.expires_at_ms) fail('METADATA_EXPIRY_MISMATCH'); assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed)); assertPendingRecords(observed.paths);
  emit({ phase: 'metadata_policy_synced', tag: 'r10', policy_sha256: metadata.policy_sha256, expires_at_ms: metadata.expires_at_ms, workspace_id: target.workspaceId, workspace_generation: target.workspaceGeneration,
    standing_policies_reinstalled: false, standalone_sandbox_probe_performed: false });
}
async function refresh() {
  mutationGuard(); const observed = await currentR10(); assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed)); assertCensus(await censusFor(observed, 'refresh_preflight_census'), true);
  assertPendingRecords(observed.paths); zeroVmProof('before_r10_full_clean_refresh'); const r = authenticated(observed); mutationGuard();
  const result = await r.client.restart({ refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null, allowAcceptancePending: true,
    reason: 'operator approved r10 setup exec contract activation preserving pending acceptance' }, { ...r.options, timeout: 120000 });
  emit({ phase: 'refresh', tag: 'r10', state: safeText(result.state), epoch: result.activation_epoch_id, pending_acceptance: assertPendingRecords(observed.paths) });
}
async function startAgent() {
  mutationGuard(); const observed = await currentR10(); if ((await agentObservation('r9')).identity.state !== 'absent') fail('OLD_AGENT_STILL_LIVE');
  const prior = await agentObservation('r10'); if (prior.identity.state === 'live') { emit({ phase: 'agent_already_live', tag: 'r10', identity: prior.identity }); return; }
  assertCensus(await censusFor(observed, 'agent_preflight_census'), true); assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed)); assertPendingRecords(observed.paths);
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths }), output = fs.openSync(path.join(__dirname, 'r10-agent.stdout.jsonl'), 'a'), errors = fs.openSync(path.join(__dirname, 'r10-agent.stderr.log'), 'a'); let child;
  try {
    mutationGuard(); child = spawn(observed.paths.portablePython(), ['-B', '-I', '-u', observed.paths.controlPlaneNodeAgent(), 'run-connected-agent', '--config', observed.paths.controlPlaneNodeConfigFile(),
      '--workspace-registry', observed.paths.controlPlaneWorkspaceRegistryFile(), '--project-root', service.agentProjectRoot, '--node', observed.paths.executablePath(), '--runtime-mode', 'packaged',
      '--interval-seconds', '15', '--max-backoff-seconds', '60', '--max-iterations', '200'], { cwd: service.agentProjectRoot, env: safeEnrollmentEnvironment(process.env), windowsHide: true, detached: true, stdio: ['ignore', output, errors] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
  } finally { fs.closeSync(output); fs.closeSync(errors); }
  const identity = await observeLifecycleProcessIdentity(child.pid); if (identity.state !== 'live') fail('R10_AGENT_NOT_LIVE');
  emit({ phase: 'agent_spawned', tag: 'r10', identity, node_agent: observed.paths.controlPlaneNodeAgent(), candidate: roots.r10, interval_seconds: 15, max_iterations: 200 });
}
async function proof() {
  verifyFiles(); const observed = await currentR10(), row = await inspectRuntime(observed), state = readJson(observed.paths.stateFile());
  if (row.ui.registered !== true || row.ui.alive !== true || row.ui.identity.state !== 'live' || row.ui.ui_installation_id !== observed.descriptor.installation_id || row.components.native.state !== 'live') fail('R10_COMPONENT_IDENTITIES_NOT_READY');
  if (row.epoch.state !== 'READY' || row.epoch.admission_open !== true || row.fully_ready !== true || row.update_incomplete === true || state.nativeActivationEpochId !== row.epoch.activation_epoch_id) fail('R10_READINESS_INCOMPLETE');
  if (row.agent.identity.state !== 'live' || row.agent.last_heartbeat_state !== 'succeeded' || Date.now() - Number(row.agent.last_heartbeat_at_ms) > 90000) fail('R10_AGENT_HEARTBEAT_NOT_FRESH');
  const census = await censusFor(observed, 'final_census'); assertCensus(census, true); assertPoliciesUnchanged(await inspectPoliciesNoProbe(observed)); renewalGuard();
  emit({ phase: 'final_proof', tag: 'r10', candidate: roots.r10, profile: 'web-mcp-assistant', identities: { host: observed.owner, ui: row.ui.identity, native: row.components.native, agent: row.agent.identity },
    epoch: row.epoch, fully_ready: row.fully_ready, local_ready: row.local_ready, central_connected: row.central_connected, authority_ready: row.authority_ready,
    awaiting_acceptance_runs: census.lifecycle.awaiting_acceptance_runs, pending_acceptance: assertPendingRecords(observed.paths), app_asar_sha256: candidateHashes.r10.archive, executable_sha256: candidateHashes.r10.executable,
    parity_sha256: parityHash, ledger_mutated_by_helper: false, standing_policies_reinstalled: false, standalone_sandbox_probe_performed: false, live_sandbox_exec_proven: false,
    acceptance_performed: false, command_replay_performed: false, vm_termination_performed: false, windows_restarted: false, pushed: false });
}
async function main() {
  const phase = process.argv[2];
  if (phase === 'server-preparation-proof') await serverPreparationProof(); else if (phase === 'preflight') await preflight();
  else if (phase === 'census') { verifyFiles(); const observed = await observedDescriptor(); assertCensus(await censusFor(observed), observed.owner.state === 'live'); assertPendingRecords(observed.paths); }
  else if (phase === 'status') { verifyFiles(); await inspectRuntime(await observedDescriptor()); }
  else if (phase === 'activate') await activate(); else if (phase === 'policy') await policy(); else if (phase === 'refresh') await refresh(); else if (phase === 'agent') await startAgent(); else if (phase === 'proof') await proof();
  else fail('PHASE_OUTSIDE_R10_ACTIVATION_SCOPE');
}
main().catch(error => { emit({ ok: false, code: safeText(error.code || 'R10_ACTIVATION_FAILED'), cause_code: safeText(error.cause?.code), no_automatic_retry: true }); process.exitCode = 1; });
