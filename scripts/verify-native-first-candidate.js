'use strict';

// Read-only package/source parity. The only write is a new evidence receipt.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const asar = require('@electron/asar');
const {
  assertExactPackagedResources, assertExactControlPlaneAdapter,
  assertMxcWindowsExecutor, assertMxcWindowsSandboxCandidate
} = require('./verify-packaged-resources');

const root = path.resolve(__dirname, '..');
const candidate = path.resolve(process.argv[2] || '');
const output = path.resolve(process.argv[3] || '');
const within = (base, target) => {
  const relative = path.relative(base, target);
  return !!relative && !relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative);
};
if (!within(path.join(root, 'dist'), candidate) || !within(path.join(root, '.coding-tools', 'reports'), output)
  || !output.endsWith('.json') || fs.existsSync(output)) {
  throw new Error('Specify an existing repository dist candidate and a new .coding-tools/reports JSON receipt.');
}
const started = new Date().toISOString();
const archive = path.join(candidate, 'resources', 'app.asar');
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const executable = path.join(candidate, packageJson.build.productName + '.exe');
const resources = path.join(candidate, 'resources', 'resources');
const expectedFiles = [];
function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    // electron-builder excludes Git metadata; it is not application content.
    if (entry.name === '.gitattributes') continue;
    if (entry.isDirectory()) walk(target);
    else if (entry.isFile()) expectedFiles.push(path.relative(root, target).replaceAll(path.sep, '/'));
    else throw new Error('Unsupported source entry: ' + target);
  }
}
walk(path.join(root, 'electron'));
walk(path.join(root, 'renderer'));
const actualFiles = asar.listPackage(archive).map((name) => name.replaceAll('\\', '/').replace(/^\//, ''))
  .filter((name) => /^(electron|renderer)\//.test(name) && !asar.statFile(archive, path.normalize(name)).files);
if (JSON.stringify(actualFiles.sort()) !== JSON.stringify(expectedFiles.sort())) {
  const differences = [
    ...expectedFiles.filter((name) => !actualFiles.includes(name)).map((name) => 'missing:' + name),
    ...actualFiles.filter((name) => !expectedFiles.includes(name)).map((name) => 'extra:' + name)
  ];
  throw new Error('Packaged application code file set differs from source: ' + differences.slice(0, 10).join(', '));
}
const codeHashes = {};
for (const relative of expectedFiles) {
  const sourceHash = sha(fs.readFileSync(path.join(root, relative)));
  if (sha(asar.extractFile(archive, path.normalize(relative))) !== sourceHash) throw new Error('Source mismatch: ' + relative);
  codeHashes[relative] = sourceHash;
}
const resourceProof = assertExactPackagedResources(path.join(root, 'resources'), resources,
  { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
const adapterProof = assertExactControlPlaneAdapter(path.join(root, 'control-plane', 'control_plane'), path.join(resources, 'control-plane'));
assertMxcWindowsExecutor(resources);
assertMxcWindowsSandboxCandidate(resources);
const receipt = {
  schema_version: 1, ok: true, proof_kind: 'exact_source_package_parity',
  observation_started_at: started, observation_finished_at: new Date().toISOString(),
  git_head: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', windowsHide: true }).trim(),
  candidate, executable_sha256: sha(fs.readFileSync(executable)),
  app_asar_sha256: sha(fs.readFileSync(archive)), application_code_files: expectedFiles.length,
  resource_proof: resourceProof, adapter_proof: adapterProof, code_sha256: codeHashes,
  installed_or_activated: false, service_operations: false
};
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ ok: true, report: output, application_code_files: expectedFiles.length,
  resource_files: resourceProof.file_count, adapter_files: adapterProof.file_count }));
