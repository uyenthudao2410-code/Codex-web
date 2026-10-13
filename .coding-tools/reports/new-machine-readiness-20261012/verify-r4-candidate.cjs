'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = 'E:\\DEV\\Codex-web';
const candidateRoot = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-coldstart-1012-r4', 'win-unpacked');
const priorRoot = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-coldstart-1012-r1', 'win-unpacked');
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
const nativeProofReusable = backendFiles.every(filename => fileSha(path.join(packagedResourcesRoot, 'tools', 'mxc-windows-sandbox', filename)) ===
  fileSha(path.join(priorRoot, 'resources', 'resources', 'tools', 'mxc-windows-sandbox', filename)));
if (!nativeProofReusable) throw new Error('R1_NATIVE_SANDBOX_PROOF_NOT_REUSABLE');
const result = {
  ok: true,
  observed_at: new Date().toISOString(),
  candidate: candidateRoot,
  application_source_files_verified: applicationFiles.length,
  package_metadata_verified: true,
  resources,
  adapters,
  sanitation,
  repaired_native_sandbox_proof_reused_from_r1: true,
  executable_sha256: fileSha(path.join(candidateRoot, 'Coding Tools MCP.exe')),
  app_asar_sha256: fileSha(archivePath),
  recovery_host_launcher_sha256: sha(asar.extractFile(archivePath, path.join('electron', 'services', 'recoveryHostLauncher.js')))
};
fs.writeFileSync(path.join(__dirname, 'r4-candidate-verification.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
