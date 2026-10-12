'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../../..');
const { createRuntimePaths } = require(path.join(repo, 'electron/services/runtimePaths'));
const { ControlPlaneEnrollmentService } = require(path.join(repo, 'electron/services/controlPlaneEnrollment'));
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked');
const scope = {
  workspaceId: 'workspace_dda1d78e9a21402aa6213f72af64f788',
  workspaceGeneration: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6'
};
const expiry = 1791710784008;
function emit(value) {
  const receipt = { observed_at: new Date().toISOString(), ...value };
  const line = JSON.stringify(receipt) + '\n';
  fs.appendFileSync(path.join(__dirname, 'postreboot-exec-policy.jsonl'), line);
  process.stdout.write(line);
}
function requireState(condition, code) {
  if (!condition) throw Object.assign(new Error(), { code });
}
function policyFields(policy) {
  return Object.fromEntries(['state', 'enabled', 'workspace_id', 'workspace_generation', 'authority_mode', 'policy_sha256', 'allowed_argv_prefix_count', 'allowed_argv_prefixes_sha256', 'max_timeout_ms', 'max_output_bytes', 'windows_acl_verified', 'reason'].filter((key) => key in policy).map((key) => [key, policy[key]]));
}
(async () => {
  requireState(Date.now() < expiry, 'APPROVED_AUTHORITY_WINDOW_EXPIRED');
  const receipt = JSON.parse(fs.readFileSync(path.join(__dirname, 'windows-candidate.json'), 'utf8'));
  for (const key of ['candidate_node_agent', 'candidate_app_asar', 'candidate_executable']) {
    const entry = receipt.hashes[key];
    requireState(entry && crypto.createHash('sha256').update(fs.readFileSync(entry.path)).digest('hex') === entry.sha256, 'CANDIDATE_HASH_CHANGED');
  }
  const paths = createRuntimePaths({
    dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'),
    appRoot: path.join(candidate, 'resources/app.asar'),
    resourcesRoot: path.join(candidate, 'resources/resources'),
    runtimeMode: 'packaged', executablePath: path.join(candidate, 'Coding Tools MCP.exe')
  });
  const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
  emit({ phase: 'sandbox_probe_started', candidate, scope, approved_expires_at_ms: expiry });
  const observation = await service.inspectStandingWorkspaceExecPolicy(scope);
  emit({ phase: 'sandbox_probe_completed', sandbox: observation.sandbox, policy: policyFields(observation.policy) });
  requireState(observation.sandbox.state === 'available', observation.sandbox.reason || 'SANDBOX_UNAVAILABLE');
  requireState(Date.now() < expiry, 'APPROVED_AUTHORITY_WINDOW_EXPIRED');
  if (observation.policy.enabled === true) {
    requireState(observation.policy.workspace_id === scope.workspaceId && observation.policy.workspace_generation === scope.workspaceGeneration, 'EXISTING_EXEC_POLICY_TARGET_MISMATCH');
    emit({ phase: 'exec_policy_already_enabled', policy: policyFields(observation.policy) });
    return;
  }
  const installed = await service.installStandingWorkspaceExecPolicy({ ...scope, replaceExisting: false });
  const observed = await service.inspectLocalExecPolicy();
  requireState(observed.enabled === true && observed.workspace_id === scope.workspaceId && observed.workspace_generation === scope.workspaceGeneration && observed.policy_sha256 === installed.policy_sha256, 'FINAL_EXEC_POLICY_MISMATCH');
  emit({ phase: 'exec_policy_installed', install: policyFields(installed), policy: policyFields(observed), sandbox: installed.sandbox, ok: true });
})().catch((error) => {
  emit({ phase: 'postreboot_exec_setup', ok: false, code: String(error.code || 'POSTREBOOT_EXEC_SETUP_FAILED') });
  process.exitCode = 1;
});
