"use strict";

const path = require('node:path');
const { randomBytes } = require('node:crypto');
const { spawnSync } = require('node:child_process');

function runPackagedRecoverySmoke({
  root = path.resolve(__dirname, '..'),
  candidateTag = `recovery-${randomBytes(10).toString('hex')}`,
  nodeExecutable = process.execPath,
  environment = process.env,
  spawnSyncFn = spawnSync
} = {}) {
  const candidateRoot = path.join(root, 'dist', `windows-candidate-mxc-wsb-cbe1774-${candidateTag}`, 'win-unpacked');
  const options = { cwd: root, stdio: 'inherit', windowsHide: true, env: { ...environment } };
  const stages = [
    // Use the same icon gate as dist:dir without a shell/npm.cmd dependency.
    { args: [path.join(root, 'scripts', 'generate-icon.js')] },
    { args: [path.join(root, 'scripts', 'build-dev-candidate.js'), candidateTag] },
    {
      args: [path.join(root, 'scripts', 'packaged-recovery-smoke.js')],
      env: { ...environment, CODEX_PACKAGED_APP_ROOT: candidateRoot }
    }
  ];

  for (const stage of stages) {
    const result = spawnSyncFn(nodeExecutable, stage.args, { ...options, env: stage.env || options.env });
    const status = result.error || result.signal || !Number.isInteger(result.status) ? 1 : result.status;
    if (status !== 0) return status;
  }
  return 0;
}

if (require.main === module) {
  process.exitCode = runPackagedRecoverySmoke();
}

module.exports = { runPackagedRecoverySmoke };
