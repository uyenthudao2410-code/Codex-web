'use strict';
// Local freeze and package parity evidence only; never activates a runtime.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../../../..');
const tag = 'workflow-timeout-1012-r14';
const candidate = path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const disk = file => fs.readFileSync(file);
const stamp = () => new Date().toISOString();
const writeNew = (name, data) => fs.writeFileSync(path.join(__dirname, name), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
function run() {
  const freezeFile = path.join(__dirname, 'source-freeze.json');
  if (process.argv[2] === 'freeze') {
    const priorFile = path.join(__dirname, '../candidate-r13/source-freeze.json');
    const priorBytes = disk(priorFile), prior = JSON.parse(priorBytes);
    if (prior.source_files.length !== 17 || prior.candidate_tag !== 'source-fingerprint-1012-r13') throw new Error('R13_FREEZE_SCOPE_CHANGED');
    const head = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true });
    if (head.status !== 0 || !/^[a-f0-9]{40}$/.test(head.stdout.trim())) throw new Error('HEAD_UNAVAILABLE');
    writeNew('source-freeze.json', { kind: 'workflow_timeout_source_freeze', observed_at: stamp(),
      repository_root: repo, repository_head: head.stdout.trim(), candidate_tag: tag,
      prior_r13_freeze_sha256: sha(priorBytes),
      source_files: prior.source_files.map(({ source, payload }) => ({ source, payload, sha256: sha(disk(path.join(repo, source))) })),
      document_and_runtime_evidence_excluded_from_source_identity: true,
      runtime_activated: false, server_mutated: false });
    process.stdout.write(JSON.stringify({ ok: true, frozen_files: 17, candidate_tag: tag }) + '\n');
    return;
  }
  if (process.argv[2] !== 'parity') throw new Error('EXPLICIT_FREEZE_OR_PARITY_REQUIRED');
  const freezeBytes = disk(freezeFile), freeze = JSON.parse(freezeBytes);
  if (freeze.candidate_tag !== tag || freeze.repository_root !== repo || freeze.source_files.length !== 17) throw new Error('FREEZE_IDENTITY_MISMATCH');
  const rows = freeze.source_files.map(item => {
    const current = sha(disk(path.join(repo, item.source)));
    const payload = item.payload.startsWith('app.asar/')
      ? asar.extractFile(path.join(candidate, 'resources/app.asar'), path.join(...item.payload.slice(9).split('/')))
      : disk(path.join(candidate, item.payload));
    return { ...item, current_sha256: current, packaged_sha256: sha(payload),
      source_stable: current === item.sha256, packaged_matches: sha(payload) === item.sha256 };
  });
  const packageJson = JSON.parse(disk(path.join(repo, 'package.json')));
  const report = { kind: 'workflow_timeout_candidate_parity', observed_at: stamp(),
    ok: rows.every(item => item.source_stable && item.packaged_matches), candidate_tag: tag,
    candidate_path: candidate, source_freeze_sha256: sha(freezeBytes), source_files: rows,
    app_asar_sha256: sha(disk(path.join(candidate, 'resources/app.asar'))),
    executable_sha256: sha(disk(path.join(candidate, `${packageJson.build.productName}.exe`))),
    runtime_activated: false, server_mutated: false };
  const name = `candidate-parity-${stamp().replace(/[^0-9TZ]/g, '')}.json`;
  writeNew(name, report);
  process.stdout.write(JSON.stringify({ ok: report.ok, matched_files: rows.filter(item => item.packaged_matches).length,
    source_drift: rows.filter(item => !item.source_stable).map(item => item.source), receipt: name,
    app_asar_sha256: report.app_asar_sha256 }) + '\n');
  if (!report.ok) process.exitCode = 1;
}
try { run(); } catch (error) {
  process.stderr.write(`CANDIDATE_PROOF_FAILED:${error.code || error.name}\n`);
  process.exitCode = 1;
}
