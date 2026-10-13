'use strict';
// Read-only package verification. Does not invoke the afterPack fuse mutator.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = 'E:\\DEV\\Codex-web';
const reportRoot = __dirname;
const candidateRoot = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e', 'win-unpacked');
const previousRoot = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9d', 'win-unpacked');
const previousProof = JSON.parse(fs.readFileSync(path.join(root, '.coding-tools', 'reports', 'folder-access-20261012-r9', 'r9d-candidate-verification.json')));
const asar = require(path.join(root, 'node_modules', '@electron', 'asar'));
const verification = require(path.join(root, 'scripts', 'verify-packaged-resources'));
const archivePath = path.join(candidateRoot, 'resources', 'app.asar');
const previousArchivePath = path.join(previousRoot, 'resources', 'app.asar');
const packagedResourcesRoot = path.join(candidateRoot, 'resources', 'resources');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fileSha = filename => sha(fs.readFileSync(filename));
function requireState(condition, code) { if (!condition) throw new Error(code); }
requireState(previousProof.ok === true && previousProof.candidate === previousRoot
  && fileSha(previousArchivePath) === previousProof.app_asar_sha256
  && fileSha(path.join(previousRoot, 'Coding Tools MCP.exe')) === previousProof.executable_sha256, 'PREVIOUS_PACKAGE_CHANGED');
const listFiles = archive => asar.listPackage(archive)
  .map(filename => filename.replace(/^[/\\]/, ''))
  .filter(filename => !asar.statFile(archive, filename).files);
const applicationFiles = listFiles(archivePath)
  .filter(filename => filename !== 'package.json' && !filename.startsWith('node_modules\\') && !filename.startsWith('node_modules/'));
for (const filename of applicationFiles) {
  requireState(sha(asar.extractFile(archivePath, filename)) === fileSha(path.join(root, filename)), `APP_ASAR_SOURCE_MISMATCH:${filename}`);
}
const sourcePackage = JSON.parse(fs.readFileSync(path.join(root, 'package.json')));
const packagedPackage = JSON.parse(asar.extractFile(archivePath, 'package.json'));
for (const key of ['name', 'version', 'main']) requireState(sourcePackage[key] === packagedPackage[key], `PACKAGE_METADATA_MISMATCH:${key}`);
const oldFiles = listFiles(previousArchivePath);
const newFiles = listFiles(archivePath);
requireState(JSON.stringify(oldFiles.slice().sort()) === JSON.stringify(newFiles.slice().sort()), 'PREVIOUS_ASAR_FILE_SET_CHANGED');
const changedFiles = newFiles.filter(filename => sha(asar.extractFile(previousArchivePath, filename)) !== sha(asar.extractFile(archivePath, filename)));
requireState(JSON.stringify(changedFiles.map(filename => filename.replace(/\\/g, '/')).sort())
  === JSON.stringify(['electron/app-icon.ico', 'electron/app-icon.png', 'renderer/app-icon.png', 'renderer/app.js', 'renderer/index.html']), 'UNEXPECTED_NON_UI_PACKAGE_CHANGE');
const expectedSourceHashes = {
  'renderer/app.js': '8dbc227e9f762c035d339d37e1f37aa4a4785c69dd48f46a50283f5b2c2e70ab',
  'renderer/index.html': '0bdce1403a81b2c3a12082912520de931beb0e63dd1b53913ee0c8cf89883505'
};
for (const [file, expected] of Object.entries(expectedSourceHashes)) requireState(fileSha(path.join(root, file)) === expected, `RENDERER_SOURCE_CHANGED:${file}`);
const resources = verification.assertExactPackagedResources(path.join(root, 'resources'), packagedResourcesRoot,
  { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
const adapters = verification.assertExactControlPlaneAdapter(path.join(root, 'control-plane', 'control_plane'), path.join(packagedResourcesRoot, 'control-plane'));
const sanitation = verification.assertSanitizedPackagedResources(packagedResourcesRoot);
const backendFiles = ['wxc-exec.exe', 'wxc-windows-sandbox-daemon.exe', 'wxc-windows-sandbox-guest.exe', 'mxc-windows-sandbox.provenance.json'];
const backend_hashes = Object.fromEntries(backendFiles.map(filename => [filename,
  fileSha(path.join(packagedResourcesRoot, 'tools', 'mxc-windows-sandbox', filename))]));
requireState(JSON.stringify(backend_hashes) === JSON.stringify(previousProof.backend_hashes), 'NON_UI_EXECUTOR_CHANGED');
for (const file of fs.readdirSync(path.join(packagedResourcesRoot, 'control-plane'))) {
  requireState(fileSha(path.join(packagedResourcesRoot, 'control-plane', file)) === fileSha(path.join(previousRoot, 'resources', 'resources', 'control-plane', file)), `NON_UI_ADAPTER_CHANGED:${file}`);
}
const nativeProvenance = verification.assertMxcWindowsSandboxCandidate(packagedResourcesRoot);
const generatedIconHashes = Object.fromEntries(['electron/app-icon.ico', 'electron/app-icon.png', 'renderer/app-icon.png']
  .map(file => [file, { previous_sha256: sha(asar.extractFile(previousArchivePath, file)), current_source_sha256: fileSha(path.join(root, file)), packaged_sha256: sha(asar.extractFile(archivePath, file)) }]));
const resourceFiles = directory => fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
  const filename = path.join(directory, entry.name);
  return entry.isDirectory() ? resourceFiles(filename) : [filename];
});
for (const file of resourceFiles(packagedResourcesRoot)) {
  const relative = path.relative(packagedResourcesRoot, file);
  requireState(fileSha(file) === fileSha(path.join(previousRoot, 'resources', 'resources', relative)), `NON_UI_RESOURCE_CHANGED:${relative}`);
}
const result = {
  ok: true, observed_at: new Date().toISOString(), candidate: candidateRoot,
  application_source_files_verified: applicationFiles.length, package_metadata_verified: true,
  resources, adapters, sanitation, backend_hashes, nativeProvenance,
  previous_candidate: previousRoot, previous_app_asar_sha256: previousProof.app_asar_sha256,
  changed_application_files: changedFiles, non_ui_application_files_unchanged: true,
  control_plane_adapters_unchanged: true, executor_binaries_unchanged: true, all_resources_unchanged: true,
  generated_icon_assets: { command: 'node scripts/generate-icon.js', input: 'docs/ICON.png', input_sha256: fileSha(path.join(root, 'docs', 'ICON.png')), generator_sha256: fileSha(path.join(root, 'scripts', 'build-icon-from-source.py')), hashes: generatedIconHashes, explanation: 'The normal build workflow regenerated three UI icon assets from the current source image; packaged bytes exactly match the generated source. No electron service or native resource changed.' },
  renderer_source_hashes: expectedSourceHashes,
  packaged_adapter_sha256: fileSha(path.join(packagedResourcesRoot, 'coding-tools-mcp', 'coding_tools_mcp', 'windows_mxc_state_aware.py')),
  executable_sha256: fileSha(path.join(candidateRoot, 'Coding Tools MCP.exe')),
  app_asar_sha256: fileSha(archivePath),
  recovery_host_launcher_sha256: sha(asar.extractFile(archivePath, path.join('electron', 'services', 'recoveryHostLauncher.js')))
};
requireState(result.packaged_adapter_sha256 === previousProof.packaged_adapter_sha256
  && result.recovery_host_launcher_sha256 === previousProof.recovery_host_launcher_sha256, 'NON_UI_RUNTIME_COMPONENT_CHANGED');
fs.writeFileSync(path.join(reportRoot, 'r9e-candidate-verification.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(result));
