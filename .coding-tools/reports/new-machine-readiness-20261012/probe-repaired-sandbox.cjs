'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const repoRoot = 'E:\\DEV\\Codex-web';
const candidateRoot = path.join(repoRoot, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-coldstart-1012-r1', 'win-unpacked');
const reportPath = path.join(__dirname, 'repaired-sandbox-probe.json');
const { RuntimePaths } = require(path.join(repoRoot, 'electron', 'services', 'runtimePaths'));
const { ControlPlaneEnrollmentService } = require(path.join(repoRoot, 'electron', 'services', 'controlPlaneEnrollment'));
const dataRoot = path.join(process.env.APPDATA, 'web-mcp-assistant');

function digestFile(filename) {
  try { return crypto.createHash('sha256').update(fs.readFileSync(path.join(dataRoot, filename))).digest('hex'); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

async function main() {
  const hostScript = "@(Get-Process | Where-Object { $_.ProcessName -in @('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox') }).Count";
  const host = spawnSync(path.join(process.env.SystemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'),
    ['-NoLogo', '-NoProfile', '-NonInteractive', '-Command', hostScript],
    { encoding: 'utf8', timeout: 5000, windowsHide: true });
  if (host.status !== 0 || !/^0\s*$/.test(host.stdout || '')) throw new Error('SAFE_EMPTY_SANDBOX_HOST_BASELINE_REQUIRED');

  const trackedFiles = ['settings.json', 'secrets.bin', 'control-plane-node.json', 'control-plane-workspaces.json',
    'control-plane-exec-policy.json', 'recovery-host.json'];
  const before = Object.fromEntries(trackedFiles.map(filename => [filename, digestFile(filename)]));
  const paths = new RuntimePaths({
    dataRoot,
    appRoot: path.join(candidateRoot, 'resources', 'app.asar'),
    resourcesRoot: path.join(candidateRoot, 'resources', 'resources'),
    runtimeMode: 'packaged',
    executablePath: path.join(candidateRoot, 'Coding Tools MCP.exe')
  });
  const startedAt = new Date().toISOString();
  console.log(JSON.stringify({ operation: 'repaired_packaged_sandbox_probe', started_at: startedAt, candidate: candidateRoot }));
  const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
  const observation = await service.inspectMxcSandbox({ workspaceRoot: repoRoot });
  const after = Object.fromEntries(trackedFiles.map(filename => [filename, digestFile(filename)]));
  const protectedFilesUnchanged = trackedFiles.every(filename => before[filename] === after[filename]);
  const result = {
    operation: 'repaired_packaged_sandbox_probe',
    candidate: candidateRoot,
    started_at: startedAt,
    completed_at: new Date().toISOString(),
    elapsed_ms: Date.now() - Date.parse(startedAt),
    observation,
    protected_profile_and_descriptor_files_unchanged: protectedFilesUnchanged,
    ok: observation.state === 'available' && observation.child_process_spawn === true && protectedFilesUnchanged
  };
  fs.writeFileSync(reportPath, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
  process.exitCode = result.ok ? 0 : 1;
}

main().catch(error => { console.error(JSON.stringify({ ok: false, code: error.code || error.message })); process.exitCode = 1; });
