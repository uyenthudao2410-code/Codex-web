'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = 'E:\\DEV\\Codex-web';
const candidateRoot = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c', 'win-unpacked');
const asar = require(path.join(root, 'node_modules', '@electron', 'asar'));
const verification = require(path.join(root, 'scripts', 'verify-packaged-resources'));
const archivePath = path.join(candidateRoot, 'resources', 'app.asar');
const packagedResourcesRoot = path.join(candidateRoot, 'resources', 'resources');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fileSha = filename => sha(fs.readFileSync(filename));
const applicationFiles = asar.listPackage(archivePath)
  .map(filename => filename.replace(/^[/\\]/, ''))
  .filter(filename => !asar.statFile(archivePath, filename).files)
  .filter(filename => filename !== 'package.json' && !filename.startsWith('node_modules\\'));
for (const filename of applicationFiles) {
  if (sha(asar.extractFile(archivePath, filename)) !== fileSha(path.join(root, filename))) {
    throw new Error(`APP_ASAR_SOURCE_MISMATCH:${filename}`);
  }
}
const sourcePackage = JSON.parse(fs.readFileSync(path.join(root, 'package.json')));
const packagedPackage = JSON.parse(asar.extractFile(archivePath, 'package.json'));
for (const key of ['name', 'version', 'main']) {
  if (sourcePackage[key] !== packagedPackage[key]) throw new Error(`PACKAGE_METADATA_MISMATCH:${key}`);
}
const resources = verification.assertExactPackagedResources(path.join(root, 'resources'), packagedResourcesRoot,
  { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
const adapters = verification.assertExactControlPlaneAdapter(path.join(root, 'control-plane', 'control_plane'),
  path.join(packagedResourcesRoot, 'control-plane'));
const sanitation = verification.assertSanitizedPackagedResources(packagedResourcesRoot);
const backendFiles = ['wxc-exec.exe', 'wxc-windows-sandbox-daemon.exe', 'wxc-windows-sandbox-guest.exe', 'mxc-windows-sandbox.provenance.json'];
const backend_hashes = Object.fromEntries(backendFiles.map(filename => [filename,
  fileSha(path.join(packagedResourcesRoot, 'tools', 'mxc-windows-sandbox', filename))]));
const nativeProvenance = verification.assertMxcWindowsSandboxCandidate(packagedResourcesRoot);
const result = {
  ok: true,
  observed_at: new Date().toISOString(),
  candidate: candidateRoot,
  application_source_files_verified: applicationFiles.length,
  package_metadata_verified: true,
  resources,
  adapters,
  sanitation,
  backend_hashes,
  nativeProvenance,
  packaged_adapter_sha256: fileSha(path.join(packagedResourcesRoot, 'coding-tools-mcp', 'coding_tools_mcp', 'windows_mxc_state_aware.py')),
  executable_sha256: fileSha(path.join(candidateRoot, 'Coding Tools MCP.exe')),
  app_asar_sha256: fileSha(archivePath),
  recovery_host_launcher_sha256: sha(asar.extractFile(archivePath, path.join('electron', 'services', 'recoveryHostLauncher.js')))
};
fs.writeFileSync(path.join(__dirname, 'r9c-candidate-verification.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));

