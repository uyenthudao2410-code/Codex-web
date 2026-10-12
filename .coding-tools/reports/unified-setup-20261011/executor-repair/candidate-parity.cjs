'use strict';
// Read-only payload/source verification. Execute only after the chosen build ends.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../../..');
const candidateTag = process.argv[2] || 'executor-diagnostics-1011-r8';
const candidateTagValid = /^[a-z][a-z0-9-]{0,31}$/.test(candidateTag) && process.argv.length <= 3;
const roots = {
  r7: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-unified-setup-1011-r7/win-unpacked'),
  candidate: candidateTagValid ? path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${candidateTag}/win-unpacked`) : null
};
const changedSources = [
  { source: 'electron/services/runtimeOrchestrator.js', payload: 'app.asar/electron/services/runtimeOrchestrator.js' },
  { source: 'electron/services/recoveryIpc.js', payload: 'app.asar/electron/services/recoveryIpc.js' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py' },
  { source: 'resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py', payload: 'resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py' },
  { source: 'control-plane/control_plane/node_agent.py', payload: 'resources/resources/control-plane/node_agent.py' },
  { source: 'control-plane/control_plane/recovery_exec_bridge.cjs', payload: 'resources/resources/control-plane/recovery_exec_bridge.cjs' }
];
const uiFiles = [
  'electron/main.js', 'electron/preload.js', 'electron/browserPreload.js',
  'renderer/index.html', 'renderer/app.js', 'renderer/styles.css',
  'renderer/settings-compact.css', 'renderer/theme-bootstrap.js'
];
const nativeNames = ['wxc-exec.exe', 'wxc-windows-sandbox-daemon.exe', 'wxc-windows-sandbox-guest.exe'];
const initialStrictReceiptName = 'candidate-parity-20261011T110137148Z.json';
const initialStrictReceiptSha256 = '6e4dcb5eda37f6376d2b44e87ca45c6e43436358e31c7d482475a81ff0e313f4';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const slash = value => value.replaceAll('\\', '/');
const fail = code => { throw Object.assign(new Error(), { code }); };
const statIdentity = stat => `${stat.size}:${stat.mtimeMs}:${stat.ctimeMs}`;
function stableRead(file) {
  const before = fs.statSync(file);
  if (!before.isFile()) fail('EXPECTED_PAYLOAD_FILE_MISSING');
  const bytes = fs.readFileSync(file);
  if (statIdentity(before) !== statIdentity(fs.statSync(file))) fail('PAYLOAD_CHANGED_DURING_OBSERVATION');
  return bytes;
}
function unpackedName(name) { return path.join(...name.split('/')); }
function archiveBytes(tag, file) {
  return asar.extractFile(path.join(roots[tag], 'resources/app.asar'), unpackedName(file));
}
function payloadBytes(tag, file) {
  return file.startsWith('app.asar/')
    ? archiveBytes(tag, file.slice('app.asar/'.length))
    : stableRead(path.join(roots[tag], unpackedName(file)));
}
function packagingExclusions() {
  const configFile = path.join(repo, 'package.json');
  const configBytes = stableRead(configFile);
  const config = JSON.parse(configBytes);
  const resourceRule = config.build.extraResources.find(rule => rule.from === 'resources' && rule.to === 'resources');
  const filters = resourceRule && Array.isArray(resourceRule.filter) ? resourceRule.filter : [];
  const verifierFile = path.join(repo, 'scripts/verify-packaged-resources.js');
  const verifierBytes = stableRead(verifierFile);
  const afterPack = config.build.afterPack;
  return {
    proven: filters.includes('!**/__pycache__/**') && filters.includes('!**/*.pyc')
      && afterPack === 'scripts/verify-packaged-resources.js',
    config_file: 'package.json', config_sha256: sha(configBytes),
    from: resourceRule ? resourceRule.from : null, to: resourceRule ? resourceRule.to : null,
    filters, after_pack: afterPack, verifier_file: 'scripts/verify-packaged-resources.js',
    verifier_sha256: sha(verifierBytes),
    semantics: 'Current resource copy excludes __pycache__ paths and .pyc files; afterPack independently rejects cache files. This proves packaging exclusion, not cache creation time.'
  };
}
function bytecacheRemoval(diff, packages, exclusions, expected) {
  if (!exclusions.proven || diff.kind !== 'removed' || diff.r7.type !== 'file') return null;
  const match = /^resources\/resources\/(.+)\/__pycache__\/([^/]+)\.cpython-312(?:\.opt-[0-2])?\.pyc$/.exec(diff.file);
  if (!match) return null;
  const sourceFile = `resources/resources/${match[1]}/${match[2]}.py`;
  const oldSource = packages.r7.entries[sourceFile];
  const newSource = packages.candidate.entries[sourceFile];
  if (!oldSource || !newSource || oldSource.type !== 'file' || newSource.type !== 'file') return null;
  const sourceUnchanged = oldSource.sha256 === newSource.sha256;
  if (!sourceUnchanged && !expected.has(sourceFile)) return null;
  return {
    file: diff.file, kind: diff.kind, r7_bytecache: diff.r7,
    corresponding_source: sourceFile, r7_source: oldSource, candidate_source: newSource,
    source_unchanged: sourceUnchanged, source_change_expected: !sourceUnchanged && expected.has(sourceFile),
    classification: 'runtime_bytecache_sanitation',
    justification: 'Removed CPython 3.12 cache has corresponding .py in both candidates and is excluded by the current packaging resource filter; any .py change is separately allowlisted.',
    creation_chronology_proven: false
  };
}
function manifest(tag) {
  const archive = path.join(roots[tag], 'resources/app.asar');
  const before = statIdentity(fs.statSync(archive));
  const entries = {};
  for (const listed of asar.listPackage(archive)) {
    const file = slash(listed).replace(/^\/+/, '');
    const info = asar.statFile(archive, unpackedName(file), false);
    if (info.files) continue;
    if (info.link) {
      entries[`app.asar/${file}`] = { type: 'link', sha256: sha(Buffer.from(info.link)) };
    } else {
      const bytes = archiveBytes(tag, file);
      entries[`app.asar/${file}`] = { type: 'file', bytes: bytes.length, sha256: sha(bytes) };
    }
  }
  const walk = folder => {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const file = path.join(folder, entry.name);
      const relative = slash(path.relative(roots[tag], file));
      if (relative === 'resources/app.asar') continue;
      if (entry.isDirectory()) walk(file);
      else if (entry.isSymbolicLink()) entries[relative] = { type: 'link', sha256: sha(Buffer.from(fs.readlinkSync(file))) };
      else if (entry.isFile()) {
        const bytes = stableRead(file);
        entries[relative] = { type: 'file', bytes: bytes.length, sha256: sha(bytes) };
      } else fail('UNSUPPORTED_PAYLOAD_ENTRY');
    }
  };
  walk(path.join(roots[tag], 'resources'));
  if (before !== statIdentity(fs.statSync(archive))) fail('ARCHIVE_CHANGED_DURING_OBSERVATION');
  return {
    candidate: roots[tag],
    app_asar_sha256: sha(stableRead(archive)),
    executable_sha256: sha(stableRead(path.join(roots[tag], 'Coding Tools MCP.exe'))),
    entries: Object.fromEntries(Object.entries(entries).sort(([a], [b]) => a.localeCompare(b)))
  };
}
(async () => {
  if (!candidateTagValid) fail('INVALID_CANDIDATE_TAG');
  const observedAt = new Date().toISOString();
  const root = execFileSync('git', ['rev-parse', '--show-toplevel'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  if (path.resolve(root).toLowerCase() !== repo.toLowerCase()) fail('REPOSITORY_ROOT_MISMATCH');
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  const initialStrictReceiptPath = path.join(__dirname, initialStrictReceiptName);
  const initialStrictReceiptBytes = stableRead(initialStrictReceiptPath);
  if (sha(initialStrictReceiptBytes) !== initialStrictReceiptSha256) fail('INITIAL_STRICT_RECEIPT_CHANGED');
  const initialStrictReceipt = JSON.parse(initialStrictReceiptBytes);
  if (initialStrictReceipt.ok !== false || initialStrictReceipt.repository_head !== head) fail('INITIAL_STRICT_RECEIPT_SCOPE_MISMATCH');
  const exclusions = packagingExclusions();
  const packages = { r7: manifest('r7'), candidate: manifest('candidate') };
  const expected = new Set(changedSources.map(item => item.payload));
  const differences = [];
  for (const file of [...new Set([...Object.keys(packages.r7.entries), ...Object.keys(packages.candidate.entries)])].sort()) {
    const old = packages.r7.entries[file], current = packages.candidate.entries[file];
    if (JSON.stringify(old) !== JSON.stringify(current)) differences.push({
      file, kind: !old ? 'added' : !current ? 'removed' : 'changed',
      expected: expected.has(file), code: /\.(?:py|pyc|js|cjs|mjs|ts|node|exe|dll|ps1|cmd|bat|sh|rs)$/i.test(file),
      r7: old || null, candidate: current || null
    });
  }
  const sourceParity = changedSources.map(item => {
    const source = stableRead(path.join(repo, unpackedName(item.source)));
    const packaged = payloadBytes('candidate', item.payload);
    return { ...item, source_sha256: sha(source), packaged_sha256: sha(packaged), bytes: source.length, byte_identical: source.equals(packaged) };
  });
  const unchangedUi = uiFiles.map(file => {
    const old = archiveBytes('r7', file), current = archiveBytes('candidate', file);
    return { file, r7_sha256: sha(old), candidate_sha256: sha(current), byte_identical: old.equals(current) };
  });
  const unchangedNative = nativeNames.map(name => {
    const file = `resources/resources/tools/mxc-windows-sandbox/${name}`;
    const old = payloadBytes('r7', file), current = payloadBytes('candidate', file);
    return { file, r7_sha256: sha(old), candidate_sha256: sha(current), byte_identical: old.equals(current) };
  });
  const strictUnexpected = differences.filter(item => !item.expected);
  const verifiedBytecacheRemovals = strictUnexpected.map(item => bytecacheRemoval(item, packages, exclusions, expected)).filter(Boolean);
  const verifiedBytecacheFiles = new Set(verifiedBytecacheRemovals.map(item => item.file));
  const unexpected = strictUnexpected.filter(item => !verifiedBytecacheFiles.has(item.file));
  const absentExpected = changedSources.filter(item => !differences.some(diff => diff.file === item.payload)).map(item => item.payload);
  const ok = !unexpected.length && !absentExpected.length && sourceParity.every(item => item.byte_identical)
    && unchangedUi.every(item => item.byte_identical) && unchangedNative.every(item => item.byte_identical);
  if (execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim() !== head) fail('HEAD_CHANGED_DURING_OBSERVATION');
  const receipt = {
    kind: 'executor_repair_immutable_candidate_parity', candidate_tag: candidateTag,
    observed_at: observedAt, completed_at: new Date().toISOString(), repository_root: repo,
    repository_head: head, helper_sha256: sha(stableRead(__filename)),
    ok, packages, differences,
    initial_strict_gate_receipt: {
      path: initialStrictReceiptPath, sha256: initialStrictReceiptSha256, ok: initialStrictReceipt.ok,
      observed_at: initialStrictReceipt.observed_at,
      unexpected_payload_difference_count: initialStrictReceipt.unexpected_payload_differences.length
    },
    strict_payload_gate: { ok: strictUnexpected.length === 0, unexpected_payload_differences: strictUnexpected },
    current_packaging_exclusions: exclusions, verified_bytecache_removals: verifiedBytecacheRemovals,
    unexpected_payload_differences: unexpected,
    expected_code_changes_not_observed: absentExpected, source_parity: sourceParity,
    unchanged_r7_ui: unchangedUi, unchanged_mxc_binaries: unchangedNative,
    runtime_activated: false, smoke_performed: false, server_mutated: false,
    note: 'Source/payload parity plus verified cache-only removals consistent with current packaging exclusion. Initial strict gate remains failed and immutable. Cache creation chronology is not proven. No runtime, Job, Sandbox or ChatGPT acceptance proof.'
  };
  const filename = path.join(__dirname, `candidate-parity-${candidateTag}-${observedAt.replace(/[^0-9TZ]/g, '')}.json`);
  fs.writeFileSync(filename, `${JSON.stringify(receipt, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${JSON.stringify({ ok, candidate_tag: candidateTag, receipt: filename, receipt_sha256: sha(stableRead(filename)), repository_head: head, changed_files: differences.length, source_files_match: sourceParity.filter(item => item.byte_identical).length, unchanged_ui_files: unchangedUi.filter(item => item.byte_identical).length, unchanged_mxc_binaries: unchangedNative.filter(item => item.byte_identical).length, strict_payload_gate_ok: strictUnexpected.length === 0, verified_bytecache_removals: verifiedBytecacheRemovals.length, initial_strict_receipt_sha256: initialStrictReceiptSha256, unexpected_payload_differences: unexpected.map(item => item.file), expected_code_changes_not_observed: absentExpected })}\n`);
  if (!ok) process.exitCode = 1;
})().catch(error => {
  process.stdout.write(`${JSON.stringify({ ok: false, code: String(error.code || 'CANDIDATE_PARITY_FAILED').replace(/[^A-Z0-9_]/g, '').slice(0, 96) })}\n`);
  process.exitCode = 1;
});
