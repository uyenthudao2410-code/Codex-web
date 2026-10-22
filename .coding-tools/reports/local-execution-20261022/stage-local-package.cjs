'use strict';
// Guarded same-installation code update. Credentials/settings backups stay in AppData.
// Read the archive itself as bytes instead of Electron's virtual ASAR directory.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { SettingsStore } = require('../../../electron/services/settingsStore');
const { descriptorMatchesInstallation } = require('../../../electron/services/recoveryHostLauncher');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => fs.readFileSync(file);
const assert = (condition, code) => { if (!condition) throw new Error(code); };
function stagePackage({paths, descriptor, evidenceFile = 'activation-preflight.json', operationId = ''}) {
const report = path.resolve(__dirname);
const plan = JSON.parse(read(path.join(report, 'package-update-plan.json')));
assert(['activation-preflight.json', 'resume-05-stopped-census.json'].includes(evidenceFile), 'STAGING_EVIDENCE_PATH_INVALID');
const preflight = JSON.parse(read(path.join(report, evidenceFile)));
const target = path.resolve(plan.target);
const candidate = path.resolve(plan.candidate);
const expectedTarget = path.resolve('E:/DEV/Codex-web/dist/windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix/win-unpacked');
const expectedCandidate = path.resolve('E:/DEV/Codex-web/dist/windows-candidate-mxc-wsb-cbe1774-local-1022b/win-unpacked');
const allowed = new Set(['resources/app.asar',
  ...['exec_tools', 'runtime_config', 'server', 'workspace_scope'].map(x => `resources/resources/coding-tools-mcp/coding_tools_mcp/${x}.py`),
  'resources/resources/control-plane/node_agent.py']);
const stageId = `local-mode-${Date.now()}-${process.pid}`;
const backupRoot = path.join(report, 'package-backup', stageId);
const state = {schema_version:1, stage_id:stageId, observed_at:new Date().toISOString(), staged:[], settings_saved:false};
const receipt = path.join(report, `package-stage-${stageId}.json`);
function record() { fs.writeFileSync(receipt, JSON.stringify(state, null, 2) + '\n'); }
try {
  assert(target === expectedTarget && candidate === expectedCandidate, 'PACKAGE_TARGET_MISMATCH');
  assert(plan.code_sections_equal === true && plan.asar_integrity_validation === false, 'EXECUTABLE_UPDATE_REQUIRED');
  assert(plan.changes.length === allowed.size && plan.changes.every(item => allowed.delete(item.path)) && !allowed.size, 'PACKAGE_SCOPE_MISMATCH');
  const stoppedEvidence = preflight.evidence_kind === 'stopped_runtime_canonical_ledger_census';
  if (stoppedEvidence) {
    const census = preflight.canonical_ledger_census;
    const snapshot = census?.snapshot;
    const source = preflight.source_verification;
    assert(evidenceFile === 'resume-05-stopped-census.json' && operationId
      && preflight.operation_id === operationId && preflight.ok === true, 'STOPPED_CENSUS_IDENTITY_INVALID');
    assert(census?.safe === true && census.source_checkpoint_verified === true
      && census.content_free === true && census.mutated_canonical_ledger === false
      && snapshot?.backup_api_copy === true && snapshot.immutable === true && snapshot.query_only === true
      && JSON.stringify(snapshot.integrity_check) === '["ok"]' && snapshot.foreign_key_check_rows === 0
      && /^[a-f0-9]{64}$/.test(census.census_fingerprint || ''), 'SAFE_STOPPED_CENSUS_REQUIRED');
    assert(source?.verified === true && source.accepted_receipts_checked === true
      && source.whole_worktree_fp_verified === true && source.receipt_count === 26
      && source.current_git_head === preflight.checkpoint?.git_head
      && source.checkpoint_id === preflight.checkpoint?.checkpoint_id
      && source.current_worktree_fp === source.accepted_worktree_fp, 'STOPPED_SOURCE_VERIFICATION_REQUIRED');
    assert(preflight.runtime_observation?.stopped === true && preflight.runtime_observation?.busy === false
      && preflight.runtime_observation?.recovering === false, 'STOPPED_RUNTIME_OBSERVATION_REQUIRED');
  } else {
    assert(evidenceFile === 'activation-preflight.json'
      && preflight.ok === true && preflight.preflight?.safe === true, 'SAFE_PREFLIGHT_REQUIRED');
  }
  const requested = Number(preflight.verified_at_unix_ms || preflight.request?.requested_at_unix_ms || 0);
  assert(Date.now() - requested >= 0 && Date.now() - requested < 90000, 'PREFLIGHT_EXPIRED');
  // The standard Node coordinator loads source modules only: it must not open
  // the target ASAR and hold a file lock across this stopped-host boundary.
  assert(!process.versions.electron, 'PLAIN_NODE_COORDINATOR_REQUIRED');
  assert(paths && descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'INSTALLATION_MISMATCH');
  const before = preflight.authority?.recovery_host;
  assert(Number(before?.pid) === Number(descriptor.owner_pid)
    && before?.instance_id === descriptor.instance_id, 'RECOVERY_HOST_CHANGED');
  let absent = false;
  try { process.kill(Number(descriptor.owner_pid), 0); } catch (error) { if (error.code === 'ESRCH') absent = true; else throw error; }
  assert(absent, 'RECOVERY_HOST_MUST_HAVE_EXITED');
  assert(sha(read(path.join(target, 'Coding Tools MCP.exe'))) === plan.retained_executable_sha256, 'EXECUTABLE_DRIFT');
  const settingsFile = paths.settingsFile();
  const settingsBefore = read(settingsFile);
  const settings = new SettingsStore(paths);
  const oldSettings = settings.load();
  assert(oldSettings.executionRole === 'central_executor' && path.resolve(oldSettings.workspace) === path.resolve('E:/DEV/Codex-web'), 'RUNTIME_SCOPE_MISMATCH');
  const staged = plan.changes.map(item => {
    const destination = path.join(target, item.path), source = path.join(candidate, item.path);
    assert(!fs.lstatSync(destination).isSymbolicLink() && !fs.lstatSync(source).isSymbolicLink(), 'PACKAGE_SYMLINK');
    const original = read(destination), replacement = read(source);
    assert(sha(original) === item.before_sha256 && sha(replacement) === item.after_sha256, 'PACKAGE_BYTES_DRIFT');
    return {...item, destination, original, replacement};
  });
  fs.mkdirSync(backupRoot, {recursive:true});
  const privateBackup = path.join(path.dirname(settingsFile), 'backups', stageId);
  fs.mkdirSync(privateBackup, {recursive:true});
  fs.writeFileSync(path.join(privateBackup, 'settings-before.json'), settingsBefore, {flag:'wx',mode:0o600});
  state.backup_directory = backupRoot;
  state.settings_backup_directory = privateBackup;
  state.checkpoint = stoppedEvidence ? preflight.checkpoint : preflight.request.source_checkpoint;
  state.evidence_file = evidenceFile;
  record();
  for (const item of staged) {
    const backup = path.join(backupRoot, item.path);
    fs.mkdirSync(path.dirname(backup), {recursive:true});
    fs.writeFileSync(backup, item.original, {flag:'wx'});
  }
  for (const item of staged) {
    assert(sha(read(item.destination)) === item.before_sha256, 'PACKAGE_CHANGED_BEFORE_REPLACE');
    const temporary = item.destination + '.' + stageId + '.tmp';
    fs.writeFileSync(temporary, item.replacement, {flag:'wx'});
    fs.renameSync(temporary, item.destination);
    assert(sha(read(item.destination)) === item.after_sha256, 'PACKAGE_REPLACE_NOT_EXACT');
    state.staged.push({path:item.path,sha256:item.after_sha256});
    record();
  }
  assert(read(settingsFile).equals(settingsBefore), 'SETTINGS_CHANGED_CONCURRENTLY');
  settings.save({executionMode:'local'});
  state.settings_saved = settings.load().executionMode === 'local';
  assert(state.settings_saved, 'LOCAL_MODE_NOT_SAVED');
  state.ok = true;
  state.service_operations = false;
  record();
  console.log(JSON.stringify({ok:true,staged_file_count:state.staged.length,execution_mode:'local',backup_directory:backupRoot,receipt}));
  return state;
} catch (error) {
  state.ok = false;
  state.error_code = error.code || error.message;
  if (error.path) state.error_path = error.path;
  record();
  console.log(JSON.stringify({ok:false,code:state.error_code,error_path:state.error_path,staged_file_count:state.staged.length,settings_saved:state.settings_saved,receipt}));
  throw Object.assign(new Error(state.error_code), {code:state.error_code,stage_receipt:receipt});
}
}
module.exports = {stagePackage};
