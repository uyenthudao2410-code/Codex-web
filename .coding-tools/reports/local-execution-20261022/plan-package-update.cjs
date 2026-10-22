'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { getCurrentFuseWire, FuseV1Options } = require('@electron/fuses');
const root = path.resolve(__dirname, '../../..');
const target = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix/win-unpacked');
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-local-1022b/win-unpacked');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function walk(base, relative = '') {
  return fs.readdirSync(path.join(base, relative), { withFileTypes: true }).flatMap(entry => {
    const next = path.join(relative, entry.name);
    if (entry.isSymbolicLink()) throw new Error('SYMLINK_NOT_ALLOWED');
    return entry.isDirectory() ? walk(base, next) : [next];
  });
}
function peSections(executable) {
  const bytes = fs.readFileSync(executable);
  const pe = bytes.readUInt32LE(0x3c);
  if (bytes.toString('ascii', pe, pe + 2) !== 'PE') throw new Error('INVALID_PE');
  const count = bytes.readUInt16LE(pe + 6);
  const first = pe + 24 + bytes.readUInt16LE(pe + 20);
  return Array.from({ length: count }, (_, index) => {
    const start = first + index * 40;
    const name = bytes.toString('ascii', start, start + 8).replace(/\0.*$/, '');
    const size = bytes.readUInt32LE(start + 16), offset = bytes.readUInt32LE(start + 20);
    return { name, sha256: sha(bytes.subarray(offset, offset + size)), size };
  });
}
(async () => {
  const executable = path.join(target, 'Coding Tools MCP.exe');
  const candidateExecutable = path.join(candidate, 'Coding Tools MCP.exe');
  const oldSections = peSections(executable), newSections = peSections(candidateExecutable);
  const codeSectionsEqual = JSON.stringify(oldSections.filter(x => x.name !== '.rsrc'))
    === JSON.stringify(newSections.filter(x => x.name !== '.rsrc'));
  const fuses = await getCurrentFuseWire(executable);
  const newFuses = await getCurrentFuseWire(candidateExecutable);
  if (!codeSectionsEqual || JSON.stringify(fuses) !== JSON.stringify(newFuses)
      || fuses[FuseV1Options.EnableEmbeddedAsarIntegrityValidation] !== 48) throw new Error('EXECUTABLE_UPDATE_REQUIRED');
  const relativeFiles = ['resources/app.asar', ...walk(path.join(candidate, 'resources/resources'))
    .map(relative => path.join('resources/resources', relative))];
  const changes = relativeFiles.flatMap(relative => {
    const before = fs.readFileSync(path.join(target, relative));
    const after = fs.readFileSync(path.join(candidate, relative));
    if (sha(before) === sha(after)) return [];
    return [{ path: relative.replaceAll('\\', '/'), before_sha256: sha(before), after_sha256: sha(after), bytes: after.length }];
  });
  if (changes.some(x => x.path !== 'resources/app.asar'
      && !/^resources\/resources\/(coding-tools-mcp\/coding_tools_mcp\/[A-Za-z_]+\.py|control-plane\/node_agent\.py)$/.test(x.path))) throw new Error('UNEXPECTED_PACKAGE_DIFF');
  const receipt = { version: 1, observed_at: new Date().toISOString(), target, candidate,
    code_sections_equal: codeSectionsEqual, asar_integrity_validation: false,
    retained_executable_sha256: sha(fs.readFileSync(executable)), changes };
  fs.writeFileSync(path.join(__dirname, 'package-update-plan.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(receipt));
})().catch(error => { console.log(JSON.stringify({ ok: false, code: error.code || error.message })); process.exitCode = 1; });
