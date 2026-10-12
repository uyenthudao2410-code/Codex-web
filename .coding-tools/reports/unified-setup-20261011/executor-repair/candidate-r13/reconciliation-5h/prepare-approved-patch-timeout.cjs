'use strict';
// Prepare reviewable source/test changes without editing the product tree.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../../../../../..');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const replacements = [
  {
    file: 'electron/services/runtimeOrchestrator.js',
    before: "    }, 'workflow');\n    if (verificationPlan && structured?.status === 'running') {",
    after: "    }, 'workflow', verificationPlan\n      ? verificationPlan.timeout_ms + CONTROL_PLANE_APPROVED_PATCH_PROVISIONING_BUDGET_MS + 30000\n      : CONTROL_PLANE_APPROVED_PATCH_TIMEOUT_MS);\n    if (verificationPlan && structured?.status === 'running') {"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "  const calls = [];\n  let workflowArguments;\n  const operationId = 'background_opaque_operation';",
    after: "  const calls = [];\n  const requestTimeouts = [];\n  const request = http.request;\n  t.mock.method(http, 'request', function (options, ...argumentsList) {\n    requestTimeouts.push(options.timeout);\n    return Reflect.apply(request, this, [options, ...argumentsList]);\n  });\n  let workflowArguments;\n  const operationId = 'background_opaque_operation';"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "  assert.equal(result.initial_verification.proof_status, 'failed');\n  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);",
    after: "  assert.equal(result.initial_verification.proof_status, 'failed');\n  assert.deepEqual(requestTimeouts, [12_000, 330_000, 15_000]);\n  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);"
  }
];
const files = [...new Set(replacements.map(entry => entry.file))];
const manifest = { schema_version: 1, product_source_modified: false, changes: [] };
let patch = '';
for (const relative of files) {
  const original = fs.readFileSync(path.join(root, relative));
  let source = original.toString('utf8').replace(/\r\n/g, '\n');
  const entries = replacements.filter(entry => entry.file === relative);
  patch += `diff --git a/${relative} b/${relative}\n--- a/${relative}\n+++ b/${relative}\n`;
  let lineDelta = 0;
  for (const entry of entries) {
    const index = source.indexOf(entry.before);
    if (index < 0 || source.indexOf(entry.before, index + 1) >= 0) throw new Error('EXACT_SOURCE_CONTEXT_CHANGED');
    const currentLine = source.slice(0, index).split('\n').length;
    const before = entry.before.split('\n');
    const after = entry.after.split('\n');
    const lines = source.split('\n');
    const contextBefore = lines.slice(Math.max(0, currentLine - 4), currentLine - 1);
    const contextAfter = lines.slice(currentLine - 1 + before.length, currentLine - 1 + before.length + 3);
    patch += `@@ -${currentLine - lineDelta - contextBefore.length},${before.length + contextBefore.length + contextAfter.length} +${currentLine - contextBefore.length},${after.length + contextBefore.length + contextAfter.length} @@\n`;
    patch += contextBefore.map(line => ` ${line}\n`).join('');
    patch += before.map(line => `-${line}\n`).join('');
    patch += after.map(line => `+${line}\n`).join('');
    patch += contextAfter.map(line => ` ${line}\n`).join('');
    source = source.slice(0, index) + entry.after + source.slice(index + entry.before.length);
    lineDelta += after.length - before.length;
  }
  manifest.changes.push({ file: relative, before_sha256: hash(original), candidate_normalized_sha256: hash(source) });
}
const patchPath = path.join(__dirname, 'approved-patch-initial-proof-timeout.patch');
fs.writeFileSync(patchPath, patch);
manifest.patch_sha256 = hash(patch);
manifest.replacements = replacements;
fs.writeFileSync(path.join(__dirname, 'approved-patch-initial-proof-timeout.json'), JSON.stringify(manifest, null, 2) + '\n');
process.stdout.write(JSON.stringify({ prepared: true, product_source_modified: false, patch_sha256: manifest.patch_sha256, files }) + '\n');
