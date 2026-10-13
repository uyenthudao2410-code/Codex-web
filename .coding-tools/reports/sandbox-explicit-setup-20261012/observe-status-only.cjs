'use strict';
// Execute with the selected packaged Electron in ELECTRON_RUN_AS_NODE mode.
// This observer permits only node-agent policy/authority reads. Any attempt
// to launch an MXC probe is rejected before a child process can start.
const fs = require('node:fs');
const path = require('node:path');
const candidate = fs.realpathSync(path.resolve(process.argv[2] || ''));
const executable = path.join(candidate, 'Coding Tools MCP.exe');
if (process.execPath.toLowerCase() !== executable.toLowerCase()) throw new Error('SELECTED_PACKAGED_ELECTRON_REQUIRED');
const appRoot = path.join(candidate, 'resources', 'app.asar');
const load = (name) => require(path.join(appRoot, 'electron', 'services', name));
const { RuntimePaths } = load('runtimePaths');
const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
const { run } = load('commandRunner');
const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
  resourcesRoot: path.join(candidate, 'resources', 'resources'), executablePath: executable, runtimeMode: 'packaged' });
const operations = [];
const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true,
  runner: async (command, args, options) => {
    const operation = args[2];
    if (command !== paths.portablePython()
      || !['inspect-exec-policy', 'inspect-policy-authority'].includes(operation)) {
      throw Object.assign(new Error('STATUS_READ_ATTEMPTED_SANDBOX_LAUNCH'), { code: 'STATUS_READ_ATTEMPTED_SANDBOX_LAUNCH' });
    }
    operations.push(operation);
    return run(command, args, options);
  }
});
service.inspectStandingWorkspaceExecPolicy({ workspaceId: process.argv[3], workspaceGeneration: process.argv[4] })
  .then((observation) => {
    if (observation.sandbox.state !== 'not_checked' || observation.sandbox.reason !== 'SANDBOX_PROBE_REQUIRED'
      || observation.policy.state !== 'enabled' || !observation.policy.current_facade_contract
      || operations.join(',') !== 'inspect-exec-policy,inspect-policy-authority') {
      throw new Error('STATUS_ONLY_OBSERVATION_NOT_VERIFIED');
    }
    process.stdout.write(JSON.stringify({ observed_at: new Date().toISOString(), candidate,
      installation_id: paths.runtimeIdentity().installation_id, sandbox_launch_count: 0,
      policy_state: observation.policy.state, policy_sha256: observation.policy.policy_sha256,
      workspace_id: observation.policy.workspace_id, workspace_generation: observation.policy.workspace_generation,
      current_facade_contract: observation.policy.current_facade_contract,
      authority_observed_at_ms: observation.policy.authority_observed_at_ms,
      sandbox: observation.sandbox, operations }) + '\n');
  }).catch((error) => {
    process.stderr.write(JSON.stringify({ error_code: String(error.code || 'STATUS_ONLY_OBSERVATION_FAILED') }) + '\n');
    process.exitCode = 1;
  });
