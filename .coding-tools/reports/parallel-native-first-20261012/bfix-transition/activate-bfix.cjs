'use strict';
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '../../../..');
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix/win-unpacked');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const { RuntimePaths } = require(path.join(root, 'electron/services/runtimePaths'));
const { run } = require(path.join(root, 'scripts/full-clean-activation'));
const { selectTrustedRecoveryHostSource, revalidateTrustedRecoveryHostSource } = require(path.join(root, 'electron/services/trustedRecoveryBootstrap'));
const { bootstrapCurrentRecoveryHost } = require(path.join(root, 'electron/services/recoveryBootstrap'));
const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot: path.join(candidate, 'resources/app.asar'), resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
function packagedRevision() {
  const probe = "const {hashComponentRevision}=require(process.resourcesPath+'/app.asar/electron/services/componentRevision'); console.log(JSON.stringify(hashComponentRevision(process.resourcesPath+'/app.asar','recovery_host')))";
  const env = { ...process.env, ELECTRON_RUN_AS_NODE: '1' };
  const result = spawnSync(executable, ['-e', probe], { cwd: candidate, env, windowsHide: true, encoding: 'utf8', timeout: 15000, maxBuffer: 65536 });
  if (result.status !== 0) throw new Error('PACKAGED_REVISION_PROBE_FAILED');
  const value = JSON.parse(String(result.stdout || '').trim());
  if (!/^[a-f0-9]{64}$/.test(String(value.revision || ''))) throw new Error('PACKAGED_REVISION_PROBE_INVALID');
  return value.revision;
}
(async () => {
  const selected = await selectTrustedRecoveryHostSource(root);
  const activationEnv = { ...process.env, FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(selected.source_checkpoint) };
  const trustedRevalidate = (_workspace, checkpoint, attestation) => revalidateTrustedRecoveryHostSource(root, checkpoint, attestation);
  const revision = packagedRevision();
  const result = await run({ argv: process.argv.includes('--execute') ? ['--execute'] : ['--preflight'], paths, trustedRecoveryBootstrap: selected.attestation, hashComponentRevisionFn: () => ({ revision }), revalidateTrustedSourceFn: trustedRevalidate, bootstrapCurrentRecoveryHostFn: options => bootstrapCurrentRecoveryHost({ ...options, revalidateTrustedSourceFn: trustedRevalidate }), forceRecoveryHostBootstrap: process.argv.includes('--force-bootstrap'), timeoutMs: 300000 }, activationEnv);
  console.log(JSON.stringify({ ok: result?.ok !== false, result }, null, 2));
})().catch(error => { console.error(JSON.stringify({ ok: false, code: error?.code || 'BFIX_ACTIVATION_FAILED', message: String(error?.message || error), details: error?.details || {} }, null, 2)); process.exitCode = 1; });
