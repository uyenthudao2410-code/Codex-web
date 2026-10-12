'use strict';
// Local artifact evidence only. No activation, credentials or external effects.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../../../..');
const tag = 'policy-contract-1012-r12';
const candidate = path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`);
const sources = [
  ...['controlPlaneApprovedPatchBridge.js', 'recoveryHost.js', 'runtimeOrchestrator.js',
    'controlPlaneEnrollment.js'].map(name => ({ source: `electron/services/${name}`,
      payload: `app.asar/electron/services/${name}` })),
  ...['renderer/app.js', 'renderer/index.html'].map(name => ({ source: name, payload: `app.asar/${name}` })),
  ...['approved_patch_verification.py', 'context_tools.py', 'exec_tools.py', 'file_tools.py',
    'workflow_tools.py', 'patching.py', 'tool_schema.py'].map(name => ({
    source: `resources/coding-tools-mcp/coding_tools_mcp/${name}`,
    payload: `resources/resources/coding-tools-mcp/coding_tools_mcp/${name}` })),
  ...['node_agent.py', 'recovery_approved_patch_bridge.cjs'].map(name => ({
    source: `control-plane/control_plane/${name}`, payload: `resources/resources/control-plane/${name}` }))
];
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const disk = file => fs.readFileSync(file);
const stamp = () => new Date().toISOString();
const writeNew = (name, data) => fs.writeFileSync(path.join(__dirname, name), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
function run() {
  const freezeFile = path.join(__dirname, 'source-freeze.json');
  if (process.argv[2] === 'freeze') {
    const head = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true });
    if (head.status !== 0 || !/^[a-f0-9]{40}$/.test(head.stdout.trim())) throw new Error('HEAD_UNAVAILABLE');
    writeNew('source-freeze.json', { kind: 'policy_contract_source_freeze', observed_at: stamp(),
      repository_root: repo, repository_head: head.stdout.trim(), candidate_tag: tag,
      source_files: sources.map(item => ({ ...item, sha256: sha(disk(path.join(repo, item.source))) })),
      runtime_activated: false, server_mutated: false });
    process.stdout.write(JSON.stringify({ ok: true, frozen_files: sources.length }) + '\n');
    return;
  }
  const freezeBytes = disk(freezeFile), freeze = JSON.parse(freezeBytes);
  if (freeze.candidate_tag !== tag || freeze.repository_root !== repo) throw new Error('FREEZE_IDENTITY_MISMATCH');
  const rows = freeze.source_files.map(item => {
    const current = sha(disk(path.join(repo, item.source)));
    const payload = item.payload.startsWith('app.asar/')
      ? asar.extractFile(path.join(candidate, 'resources/app.asar'), path.join(...item.payload.slice(9).split('/')))
      : disk(path.join(candidate, item.payload));
    return { ...item, current_sha256: current, packaged_sha256: sha(payload),
      source_stable: current === item.sha256, packaged_matches: sha(payload) === item.sha256 };
  });
  const packageJson = JSON.parse(disk(path.join(repo, 'package.json')));
  const report = { kind: 'policy_contract_candidate_parity', observed_at: stamp(),
    ok: rows.every(item => item.source_stable && item.packaged_matches), candidate_tag: tag,
    candidate_path: candidate, source_freeze_sha256: sha(freezeBytes), source_files: rows,
    app_asar_sha256: sha(disk(path.join(candidate, 'resources/app.asar'))),
    executable_sha256: sha(disk(path.join(candidate, `${packageJson.build.productName}.exe`))),
    runtime_activated: false, server_mutated: false };
  const name = `candidate-parity-${stamp().replace(/[^0-9TZ]/g, '')}.json`;
  writeNew(name, report);
  process.stdout.write(JSON.stringify({ ok: report.ok, matched_files: rows.filter(x => x.packaged_matches).length,
    source_drift: rows.filter(x => !x.source_stable).map(x => x.source), receipt: name,
    app_asar_sha256: report.app_asar_sha256 }) + '\n');
  if (!report.ok) process.exitCode = 1;
}
try { run(); } catch (error) {
  process.stderr.write(`CANDIDATE_PROOF_FAILED:${error.code || error.name}\n`);
  process.exitCode = 1;
}
