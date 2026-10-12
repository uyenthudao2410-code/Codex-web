'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../..');
const prior = JSON.parse(fs.readFileSync(path.join(repo, '.coding-tools/reports/mcp-web-contract-20261011/exec-coldstart-candidate.json'))).candidate;
const current = JSON.parse(fs.readFileSync(path.join(__dirname, 'windows-candidate.json'))).candidate;
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const priorAsar = path.join(prior, 'resources/app.asar');
const currentAsar = path.join(current, 'resources/app.asar');
const entries = (archive) => asar.listPackage(archive).filter((file) => /\.(js|cjs|html|css|json)$/.test(file)).map((file) => file.replace(/^[/\\]+/, ''));
const archivedFiles = [...new Set([...entries(priorAsar), ...entries(currentAsar)])];
const readEntry = (archive, file) => { try { return sha(asar.extractFile(archive, file)); } catch { return null; } };
const archiveDelta = archivedFiles.map((file) => ({file, prior: readEntry(priorAsar, file), current: readEntry(currentAsar, file)})).filter((entry) => entry.prior !== entry.current);
const resourceFiles = (root, prefix = '') => fs.readdirSync(path.join(root, prefix), {withFileTypes: true}).flatMap((entry) => {
  const file = path.posix.join(prefix, entry.name);
  return entry.isDirectory() ? resourceFiles(root, file) : /\.(py|cjs|js|json|toml)$/.test(file) ? [file] : [];
});
const resourceRoot = (candidate) => path.join(candidate, 'resources/resources');
const resources = [...new Set([...resourceFiles(resourceRoot(prior)), ...resourceFiles(resourceRoot(current))])];
const readResource = (candidate, file) => { try { return sha(fs.readFileSync(path.join(resourceRoot(candidate), file))); } catch { return null; } };
const resourceDelta = resources.map((file) => ({file, prior: readResource(prior, file), current: readResource(current, file)})).filter((entry) => entry.prior !== entry.current);
const receipt = { observed_at: new Date().toISOString(), kind: 'local_candidate_code_delta', prior, current, archive_delta: archiveDelta, resources_delta: resourceDelta,
  note: 'Local artifact comparison. Neither candidate read causes runtime activation.' };
fs.writeFileSync(path.join(__dirname, 'candidate-delta.json'), JSON.stringify(receipt, null, 2));
process.stdout.write(JSON.stringify({archive_delta: archiveDelta.map((entry) => entry.file), resources_delta: resourceDelta.map((entry) => entry.file)}) + '\n');
