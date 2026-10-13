'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const candidate = 'E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r6\\win-unpacked';
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources', 'app.asar');
const expectedEpoch = 'activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4';
const requireState = (condition, code) => { if (!condition) throw Object.assign(new Error(code), { code }); };
const hash = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
async function main() {
  requireState(process.execPath.toLowerCase() === executable.toLowerCase(), 'EXACT_R6_EXECUTABLE_REQUIRED');
  requireState(hash(executable) === 'a18ba16a640c30ad67758d6ba19aaf7044d947cea2f8026796b6e88f930243a8'
    && hash(appRoot) === '69bac603b0dab1ad27f86fa114da140b059a93c695a4b7dfdbe24b53b3c007ae', 'EXACT_R6_PACKAGE_REQUIRED');
  const load = name => require(path.join(appRoot, 'electron', 'services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { readVerifiedReadyHost, descriptorMatchesInstallation, descriptorRequestOptions } = load('recoveryHostLauncher');
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
    resourcesRoot: path.join(candidate, 'resources', 'resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2);
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'READY_HOST_NOT_VERIFIED');
  const options = descriptorRequestOptions(verified.descriptor);
  const runtime = await client.call('runtime.lightweight_snapshot', [], options);
  const recovery = await client.call('recovery.status', [{ fresh: true }], options);
  const activation = await client.call('runtime.activation_epoch_status', [], options);
  requireState(runtime.fullyReady === true && runtime.mcpRunning === true && runtime.authorityReady === true
    && runtime.centralConnected === true && runtime.updateIncomplete === false, 'RUNTIME_NOT_READY');
  requireState(activation.activation_epoch_id === expectedEpoch && activation.state === 'READY'
    && activation.admission_open === true && recovery.activation_epoch.activation_epoch_id === expectedEpoch
    && recovery.activation_epoch.admission_open === true, 'READY_OPEN_EPOCH_CHANGED');
  requireState(recovery.pid === 25028 && recovery.instance_id === '8b8992a71407cd61f37317ae0b438cb4'
    && recovery.code_revision.state === 'current'
    && recovery.code_revision.running_revision === recovery.code_revision.disk_revision, 'EXACT_HOST_CHANGED');
  const receipt = { operation: 'shortcut_runtime_readonly_r6', ok: true, observed_at: new Date().toISOString(),
    activation_epoch_id: expectedEpoch, state: activation.state, admission_open: activation.admission_open,
    host_pid: recovery.pid, host_instance_id: recovery.instance_id,
    installation_id: paths.runtimeIdentity().installation_id,
    code_revision_current: recovery.code_revision.state === 'current',
    fully_ready: runtime.fullyReady, authority_ready: runtime.authorityReady, central_connected: runtime.centralConnected };
  const outputPath = path.join(__dirname, `shortcut-runtime-readonly-r6-${Date.now()}.json`);
  fs.writeFileSync(outputPath, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ ...receipt, output_path: outputPath }));
}
main().then(() => process.exit(0), error => { console.error(JSON.stringify({ ok: false, code: error.code || error.name })); process.exit(1); });
