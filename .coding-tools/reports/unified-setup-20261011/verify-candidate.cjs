'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../..');
const tag = process.argv[2] || 'unified-setup-1011-r7';
if (!/^[a-z0-9][a-z0-9-]{0,31}$/.test(tag)) throw new Error('Invalid candidate tag');
const candidate = path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`);
const archive = path.join(candidate, 'resources/app.asar');
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const inputs = ['electron/main.js', 'electron/preload.js', 'electron/browserPreload.js',
  'renderer/index.html', 'renderer/app.js', 'renderer/styles.css', 'renderer/settings-compact.css', 'renderer/theme-bootstrap.js'];
const files = inputs.map((file) => {
  const source = fs.readFileSync(path.join(repo, file));
  const packaged = asar.extractFile(archive, file);
  return { file, source_sha256: sha(source), packaged_sha256: sha(packaged), bytes: source.length, matches: source.equals(packaged) };
});
const sourcePackage = JSON.parse(fs.readFileSync(path.join(repo, 'package.json')));
const packagedPackage = JSON.parse(asar.extractFile(archive, 'package.json'));
const packageKeys = ['name', 'version', 'description', 'author', 'license', 'main', 'dependencies'];
const packageIdentity = {
  source_sha256: sha(fs.readFileSync(path.join(repo, 'package.json'))),
  packaged_sha256: sha(asar.extractFile(archive, 'package.json')),
  expected_packaged_keys: packageKeys,
  matches: Object.keys(packagedPackage).sort().join(',') === packageKeys.slice().sort().join(',')
    && packageKeys.every((key) => JSON.stringify(sourcePackage[key]) === JSON.stringify(packagedPackage[key])),
  note: 'electron-builder removes scripts, devDependencies and build from packaged package.json.'
};
const receipt = { kind: 'isolated_candidate_source_parity', observed_at: new Date().toISOString(),
  repository_head: '2c554f59cb7b8ffc86ce5e0e28076c792777642f', candidate,
  app_asar_sha256: sha(fs.readFileSync(archive)), executable_sha256: sha(fs.readFileSync(path.join(candidate, 'Coding Tools MCP.exe'))),
  files, package_identity: packageIdentity, ok: files.every((entry) => entry.matches) && packageIdentity.matches, live_activation: false,
  note: 'This checks packaged code identity; it does not prove live ChatGPT execution or owner authority.' };
fs.writeFileSync(path.join(__dirname, 'windows-candidate.json'), JSON.stringify(receipt, null, 2));
process.stdout.write(JSON.stringify({ok: receipt.ok, matched_files: files.filter((entry) => entry.matches).length, candidate}) + '\n');
if (!receipt.ok) process.exitCode = 1;
