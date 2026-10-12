'use strict';
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../../../../../..');
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked');
const files = { archive: path.join(candidate, 'resources/app.asar'), executable: path.join(candidate, 'Coding Tools MCP.exe'),
  parity: path.join(__dirname, '../candidate-parity-20261011T115907669Z.json'),
  freeze: path.join(__dirname, '../source-freeze-20261011T115648871Z.json') };
const result = { phase: 'observer_provenance_diagnosis', read_only: true, files: {} };
for (const [name, file] of Object.entries(files)) {
  try { result.files[name] = { ok: true, sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex') }; }
  catch (error) { result.files[name] = { ok: false, code: /^[A-Z0-9_]+$/.test(error.code || '') ? error.code : 'READ_FAILED' }; }
}
try { result.git = { ok: true, head: require('node:child_process').execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, windowsHide: true, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim() }; }
catch (error) { result.git = { ok: false, code: /^[A-Z0-9_]+$/.test(error.code || '') ? error.code : 'GIT_FAILED' }; }
fs.writeFileSync(path.join(__dirname, 'observer-provenance-diagnosis.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(result) + '\n');
