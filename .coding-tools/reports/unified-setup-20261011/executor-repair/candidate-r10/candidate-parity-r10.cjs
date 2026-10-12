'use strict';
// Evidence-only helper. No process launch, service operation, policy write or activation.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../../../..');
const headExpected = '2c554f59cb7b8ffc86ce5e0e28076c792777642f';
const tag = 'setup-exec-contract-1011-r10';
const roots = {
  r9: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked'),
  candidate: path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`)
};
const priorReceipt = path.join(__dirname, '../candidate-parity-executor-lifecycle-1011-r9-20261011T110727929Z.json');
const priorReceiptExpected = 'c2427d0ff484a94f4437762700ddf144fc41e7f57412491e4421aa22f0e36ec6';
const changedSources = [
  { source: 'renderer/app.js', payload: 'app.asar/renderer/app.js' },
  { source: 'electron/services/runtimeOrchestrator.js', payload: 'app.asar/electron/services/runtimeOrchestrator.js' },
  { source: 'electron/services/recoveryIpc.js', payload: 'app.asar/electron/services/recoveryIpc.js' },
  { source: 'electron/services/controlPlaneExecBridge.js', payload: 'app.asar/electron/services/controlPlaneExecBridge.js' },
  { source: 'electron/services/fullCleanActivation.js', payload: 'app.asar/electron/services/fullCleanActivation.js' },
  { source: 'control-plane/control_plane/node_agent.py', payload: 'resources/resources/control-plane/node_agent.py' },
  { source: 'control-plane/control_plane/recovery_exec_bridge.cjs', payload: 'resources/resources/control-plane/recovery_exec_bridge.cjs' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py' }
];
const unchangedResources = [
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_sandbox.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_sandbox.py' },
  ...['wxc-exec.exe', 'wxc-windows-sandbox-daemon.exe', 'wxc-windows-sandbox-guest.exe'].map(name => ({
    source: `resources/tools/mxc-windows-sandbox/${name}`,
    payload: `resources/resources/tools/mxc-windows-sandbox/${name}`
  }))
];
const uiFiles = ['electron/main.js', 'electron/preload.js', 'electron/browserPreload.js',
  'renderer/index.html', 'renderer/styles.css', 'renderer/settings-compact.css', 'renderer/theme-bootstrap.js'];
const sourceFiles = [...changedSources, ...unchangedResources,
  ...uiFiles.map(source => ({ source, payload: `app.asar/${source}` }))];
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const slash = value => value.replaceAll('\\', '/');
const localName = value => path.join(...value.split('/'));
const fail = code => { throw Object.assign(new Error(), { code }); };
const statIdentity = value => `${value.size}:${value.mtimeMs}:${value.ctimeMs}`;
function stableRead(file) {
  const before = fs.statSync(file);
  if (!before.isFile()) fail('EXPECTED_FILE_MISSING');
  const bytes = fs.readFileSync(file);
  if (statIdentity(before) !== statIdentity(fs.statSync(file))) fail('FILE_CHANGED_DURING_OBSERVATION');
  return bytes;
}
function currentHead() {
  const root = execFileSync('git', ['rev-parse', '--show-toplevel'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  if (path.resolve(root).toLowerCase() !== repo.toLowerCase()) fail('REPOSITORY_ROOT_MISMATCH');
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  if (head !== headExpected) fail('REPOSITORY_HEAD_MISMATCH');
  return head;
}
function priorProof() {
  const bytes = stableRead(priorReceipt);
  if (sha(bytes) !== priorReceiptExpected) fail('R9_RECEIPT_CHANGED');
  const receipt = JSON.parse(bytes);
  if (!receipt.ok || receipt.repository_head !== headExpected) fail('R9_RECEIPT_SCOPE_MISMATCH');
  const archiveHash = sha(stableRead(path.join(roots.r9, 'resources/app.asar')));
  const exeHash = sha(stableRead(path.join(roots.r9, 'Coding Tools MCP.exe')));
  if (archiveHash !== receipt.packages.candidate.app_asar_sha256 || exeHash !== receipt.packages.candidate.executable_sha256) fail('R9_PACKAGE_IDENTITY_CHANGED');
  return { receipt, summary: { path: priorReceipt, sha256: priorReceiptExpected, app_asar_sha256: archiveHash, executable_sha256: exeHash } };
}
function sourceManifest() {
  return sourceFiles.map(item => ({ ...item, bytes: fs.statSync(path.join(repo, localName(item.source))).size,
    sha256: sha(stableRead(path.join(repo, localName(item.source)))) }));
}
function archiveBytes(which, file) {
  return asar.extractFile(path.join(roots[which], 'resources/app.asar'), localName(file));
}
function payloadBytes(which, file) {
  return file.startsWith('app.asar/') ? archiveBytes(which, file.slice(9)) : stableRead(path.join(roots[which], localName(file)));
}
function manifest(which) {
  const archive = path.join(roots[which], 'resources/app.asar');
  const initial = statIdentity(fs.statSync(archive));
  const entries = {};
  for (const listed of asar.listPackage(archive)) {
    const file = slash(listed).replace(/^\/+/, '');
    const info = asar.statFile(archive, localName(file), false);
    if (info.files) continue;
    entries[`app.asar/${file}`] = info.link
      ? { type: 'link', sha256: sha(Buffer.from(info.link)) }
      : (() => { const bytes = archiveBytes(which, file); return { type: 'file', bytes: bytes.length, sha256: sha(bytes) }; })();
  }
  const walk = folder => {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const file = path.join(folder, entry.name), relative = slash(path.relative(roots[which], file));
      if (relative === 'resources/app.asar') continue;
      if (entry.isDirectory()) walk(file);
      else if (entry.isSymbolicLink()) entries[relative] = { type: 'link', sha256: sha(Buffer.from(fs.readlinkSync(file))) };
      else if (entry.isFile()) { const bytes = stableRead(file); entries[relative] = { type: 'file', bytes: bytes.length, sha256: sha(bytes) }; }
      else fail('UNSUPPORTED_PAYLOAD_ENTRY');
    }
  };
  walk(path.join(roots[which], 'resources'));
  if (initial !== statIdentity(fs.statSync(archive))) fail('ARCHIVE_CHANGED_DURING_OBSERVATION');
  return { candidate: roots[which], app_asar_sha256: sha(stableRead(archive)),
    executable_sha256: sha(stableRead(path.join(roots[which], 'Coding Tools MCP.exe'))),
    entries: Object.fromEntries(Object.entries(entries).sort(([a], [b]) => a.localeCompare(b))) };
}
function exclusions() {
  const bytes = stableRead(path.join(repo, 'package.json'));
  const config = JSON.parse(bytes), rule = config.build.extraResources.find(item => item.from === 'resources' && item.to === 'resources');
  const filters = rule && Array.isArray(rule.filter) ? rule.filter : [];
  return { proven: filters.includes('!**/__pycache__/**') && filters.includes('!**/*.pyc') && config.build.afterPack === 'scripts/verify-packaged-resources.js',
    package_json_sha256: sha(bytes), filters, after_pack: config.build.afterPack,
    verifier_sha256: sha(stableRead(path.join(repo, 'scripts/verify-packaged-resources.js'))) };
}
function classifyCache(diff, packages, expected) {
  if (!['added', 'removed'].includes(diff.kind)) return null;
  const match = /^resources\/resources\/(.+)\/__pycache__\/([^/]+)\.cpython-312(?:\.opt-[0-2])?\.pyc$/.exec(diff.file);
  if (!match) return null;
  const source = `resources/resources/${match[1]}/${match[2]}.py`;
  const old = packages.r9.entries[source], current = packages.candidate.entries[source];
  if (!old || !current || old.type !== 'file' || current.type !== 'file') return null;
  if (old.sha256 !== current.sha256 && !expected.has(source)) return null;
  if ((diff.r9 || diff.candidate).type !== 'file') return null;
  return { ...diff, corresponding_source: source, r9_source: old, candidate_source: current,
    source_unchanged: old.sha256 === current.sha256, source_change_expected: old.sha256 !== current.sha256 && expected.has(source),
    classification: 'verified_python_bytecache_delta', creation_chronology_proven: false };
}
function writeReceipt(name, receipt) {
  const file = path.join(__dirname, name);
  fs.writeFileSync(file, `${JSON.stringify(receipt, null, 2)}\n`, { flag: 'wx' });
  return { receipt: file, receipt_sha256: sha(stableRead(file)) };
}
function compareSources(which, files) {
  return files.map(item => { const source = stableRead(path.join(repo, localName(item.source))), packaged = payloadBytes(which, item.payload);
    return { ...item, source_sha256: sha(source), packaged_sha256: sha(packaged), bytes: source.length, byte_identical: source.equals(packaged) }; });
}
function run() {
  const mode = process.argv[2];
  if (!['prepare', 'verify'].includes(mode) || (mode === 'prepare' ? process.argv.length !== 3 : process.argv.length !== 4)) fail('INVALID_HELPER_MODE');
  const observedAt = new Date().toISOString(), head = currentHead(), prior = priorProof();
  if (mode === 'prepare') {
    const source = sourceManifest(), unchanged = compareSources('r9', unchangedResources);
    if (!unchanged.every(item => item.byte_identical)) fail('UNCHANGED_SOURCE_DRIFT_FROM_R9');
    const receipt = { kind: 'r10_source_freeze', observed_at: observedAt, repository_root: repo, repository_head: head,
      candidate_tag: tag, r9_identity: prior.summary, source_files: source, unchanged_source_parity: unchanged,
      helper_sha256: sha(stableRead(__filename)), runtime_activated: false, server_mutated: false };
    const saved = writeReceipt(`source-freeze-${observedAt.replace(/[^0-9TZ]/g, '')}.json`, receipt);
    process.stdout.write(`${JSON.stringify({ ok: true, mode, ...saved, source_files: source.length, unchanged_source_files: unchanged.length })}\n`);
    return;
  }
  const freezeName = process.argv[3];
  if (!/^source-freeze(?:-[0-9TZ]+)?\.json$/.test(freezeName)) fail('INVALID_SOURCE_FREEZE_NAME');
  const freezeBytes = stableRead(path.join(__dirname, freezeName)), freeze = JSON.parse(freezeBytes);
  if (freeze.repository_head !== head || freeze.candidate_tag !== tag || freeze.r9_identity.sha256 !== priorReceiptExpected) fail('SOURCE_FREEZE_SCOPE_MISMATCH');
  if (freeze.helper_sha256 !== sha(stableRead(__filename))) fail('HELPER_CHANGED_SINCE_SOURCE_FREEZE');
  const currentSource = sourceManifest();
  const sourceDrift = currentSource.filter(item => !freeze.source_files.some(old => old.source === item.source && old.sha256 === item.sha256 && old.bytes === item.bytes));
  const packages = { r9: manifest('r9'), candidate: manifest('candidate') }, expected = new Set(changedSources.map(item => item.payload));
  const differences = [];
  for (const file of [...new Set([...Object.keys(packages.r9.entries), ...Object.keys(packages.candidate.entries)])].sort()) {
    const old = packages.r9.entries[file], current = packages.candidate.entries[file];
    if (JSON.stringify(old) !== JSON.stringify(current)) differences.push({ file, kind: !old ? 'added' : !current ? 'removed' : 'changed',
      expected: expected.has(file), code: /\.(?:py|pyc|js|cjs|mjs|ts|node|exe|dll|ps1|cmd|bat|sh|rs)$/i.test(file), r9: old || null, candidate: current || null });
  }
  const packagingExclusions = exclusions(), strictUnexpected = differences.filter(item => !item.expected);
  const bytecacheDeltas = strictUnexpected.map(item => classifyCache(item, packages, expected)).filter(Boolean);
  const cachePaths = new Set(bytecacheDeltas.map(item => item.file));
  const unexpected = strictUnexpected.filter(item => !cachePaths.has(item.file));
  const candidateCacheAdditions = bytecacheDeltas.filter(item => item.kind === 'added');
  const absentExpected = changedSources.filter(item => !differences.some(diff => diff.file === item.payload)).map(item => item.payload);
  const sourceParity = compareSources('candidate', changedSources), resourceSourceParity = compareSources('candidate', unchangedResources);
  const unchangedNative = unchangedResources.map(item => ({ ...item, r9_sha256: sha(payloadBytes('r9', item.payload)), candidate_sha256: sha(payloadBytes('candidate', item.payload)),
    byte_identical: payloadBytes('r9', item.payload).equals(payloadBytes('candidate', item.payload)) }));
  const unchangedUi = uiFiles.map(file => ({ file, r9_sha256: sha(archiveBytes('r9', file)), candidate_sha256: sha(archiveBytes('candidate', file)),
    byte_identical: archiveBytes('r9', file).equals(archiveBytes('candidate', file)) }));
  const ok = !sourceDrift.length && !unexpected.length && !absentExpected.length && !candidateCacheAdditions.length && packagingExclusions.proven
    && sourceParity.every(item => item.byte_identical) && resourceSourceParity.every(item => item.byte_identical)
    && unchangedNative.every(item => item.byte_identical) && unchangedUi.every(item => item.byte_identical);
  if (currentHead() !== head) fail('HEAD_CHANGED_DURING_OBSERVATION');
  const receipt = { kind: 'r10_immutable_candidate_parity', observed_at: observedAt, completed_at: new Date().toISOString(), repository_root: repo,
    repository_head: head, candidate_tag: tag, helper_sha256: sha(stableRead(__filename)), ok,
    source_freeze_sha256: sha(freezeBytes), r9_identity: prior.summary, packages, differences,
    strict_payload_gate: { ok: strictUnexpected.length === 0, unexpected_payload_differences: strictUnexpected },
    packaging_exclusions: packagingExclusions, verified_bytecache_deltas: bytecacheDeltas,
    candidate_bytecache_additions: candidateCacheAdditions, unexpected_payload_differences: unexpected,
    expected_code_changes_not_observed: absentExpected, source_drift_since_freeze: sourceDrift,
    changed_source_parity: sourceParity, unchanged_resource_source_parity: resourceSourceParity,
    unchanged_r9_native_resources: unchangedNative, unchanged_r9_ui: unchangedUi,
    runtime_activated: false, smoke_performed: false, server_mutated: false,
    note: 'Checks exact eleven product deltas, source bytes, full app.asar/resource manifest, pinned r9 archive/executable identities, seven unchanged UI inputs and four unchanged native resources. Verified cache-only removals are accepted; cache additions are classified but fail packaging exclusion. Root executable is recorded, not required to match because packaging can embed changed app.asar integrity. This is payload proof, not activation, Job or acceptance proof.' };
  const saved = writeReceipt(`candidate-parity-${observedAt.replace(/[^0-9TZ]/g, '')}.json`, receipt);
  process.stdout.write(`${JSON.stringify({ ok, mode, ...saved, repository_head: head, app_asar_sha256: packages.candidate.app_asar_sha256,
    executable_sha256: packages.candidate.executable_sha256, changed_files: differences.length,
    source_files_match: sourceParity.filter(item => item.byte_identical).length,
    unchanged_resources_match: unchangedNative.filter(item => item.byte_identical).length,
    unchanged_ui_match: unchangedUi.filter(item => item.byte_identical).length,
    verified_bytecache_deltas: bytecacheDeltas.length, candidate_cache_additions: candidateCacheAdditions.length,
    unexpected_payload_differences: unexpected.map(item => item.file), expected_code_changes_not_observed: absentExpected,
    source_drift_since_freeze: sourceDrift.map(item => item.source) })}\n`);
  if (!ok) process.exitCode = 1;
}
try { run(); } catch (error) {
  const observedAt = new Date().toISOString();
  const failure = { ok: false, kind: 'r10_candidate_parity_failure', observed_at: observedAt,
    code: String(error.code || 'CANDIDATE_PARITY_FAILED').replace(/[^A-Z0-9_]/g, '').slice(0, 96), runtime_activated: false, server_mutated: false };
  const saved = writeReceipt(`candidate-parity-failed-${observedAt.replace(/[^0-9TZ]/g, '')}.json`, failure);
  process.stdout.write(`${JSON.stringify({ ...failure, ...saved })}\n`); process.exitCode = 1;
}
