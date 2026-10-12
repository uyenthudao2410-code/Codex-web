'use strict';
// Supersedes the first prepared patch; product bytes stay frozen.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '../../../../../..');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const replacements = [
  {
    file: 'electron/services/runtimeOrchestrator.js',
    before: '    let structured = await callLocalTool(APPROVED_PATCH_ACTION_TOOL_NAME, {',
    after: '    const verificationDeadline = verificationPlan\n      ? Date.now() + verificationPlan.timeout_ms + CONTROL_PLANE_APPROVED_PATCH_PROVISIONING_BUDGET_MS + 30000\n      : null;\n    let structured = await callLocalTool(APPROVED_PATCH_ACTION_TOOL_NAME, {'
  },
  {
    file: 'electron/services/runtimeOrchestrator.js',
    before: "    }, 'workflow');\n    if (verificationPlan && structured?.status === 'running') {",
    after: "    }, 'workflow', verificationPlan\n      ? Math.max(1, verificationDeadline - Date.now())\n      : CONTROL_PLANE_APPROVED_PATCH_TIMEOUT_MS);\n    if (verificationPlan && structured?.status === 'running') {"
  },
  {
    file: 'electron/services/runtimeOrchestrator.js',
    before: '      const deadline = Date.now() + verificationPlan.timeout_ms + CONTROL_PLANE_APPROVED_PATCH_PROVISIONING_BUDGET_MS + 30000;',
    after: '      const deadline = verificationDeadline;'
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "  const calls = [];\n  let workflowArguments;\n  const operationId = 'background_opaque_operation';",
    after: "  const calls = [];\n  const requestTimeouts = [];\n  const request = http.request;\n  let now = Date.now();\n  t.mock.method(Date, 'now', () => now);\n  t.mock.method(http, 'request', function (options, ...argumentsList) {\n    requestTimeouts.push(options.timeout);\n    return Reflect.apply(request, this, [options, ...argumentsList]);\n  });\n  let workflowArguments;\n  const operationId = 'background_opaque_operation';"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "        assert.equal(workflowArguments.verification, 'none');\n        fs.writeFileSync(item.target, action._after, 'utf8');",
    after: "        assert.equal(workflowArguments.verification, 'none');\n        now += 325_000; // Simulate elapsed handoff/setup without a real wait.\n        fs.writeFileSync(item.target, action._after, 'utf8');"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "      assert.equal(body.params.arguments.operation_id, operationId);\n      assert.equal(body.params.arguments.task_context_id, workflowArguments.task_context_id);",
    after: "      assert.equal(body.params.arguments.operation_id, operationId);\n      assert.equal(body.params.arguments.wait_ms, 5_000);\n      assert.equal(body.params.arguments.task_context_id, workflowArguments.task_context_id);"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "  assert.equal(result.initial_verification.proof_status, 'failed');\n  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);",
    after: "  assert.equal(result.initial_verification.proof_status, 'failed');\n  assert.deepEqual(requestTimeouts, [12_000, 330_000, 15_000]);\n  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);"
  },
  {
    file: 'tests/control-plane-approved-patch-runtime.test.js',
    before: "test('initial verification cannot write before independent local exec admission', async (t) => {",
    after: `test('initial verification expires its original observation budget without another write or poll', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  action.verification = { argv: ['node', '--test'], cwd: '', timeout_ms: 60000, max_output_bytes: 32768 };
  action.exec_policy_sha256 = 'e'.repeat(64);
  action.expires_at_ms = Date.now() + 600000;
  let now = Date.now();
  t.mock.method(Date, 'now', () => now);
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', chunk => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) return send(response, body.id, { workspace: item.registeredRoot });
      assert.equal(body.params.name, 'agent_workflow');
      assert.equal(calls.length, 2, 'an exhausted budget must not poll or start another workflow');
      fs.writeFileSync(item.target, action._after, 'utf8');
      now += 330_001;
      send(response, body.id, { status: 'running', background_operation: {
        operation_id: 'background_expired_operation', tool: 'agent_workflow', workspace: item.registeredRoot, status: 'running' } });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  await assert.rejects(context.orchestrator.controlPlaneApprovedPatch(action), {
    code: 'CONTROL_PLANE_APPROVED_PATCH_OPERATION_UNCONFIRMED'
  });
  assert.equal(calls.length, 2);
  assert.equal(calls.filter(call => call.params.name === 'agent_workflow').length, 1);
  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);
});

test('initial verification cannot write before independent local exec admission', async (t) => {`
  }
];
const manifest = { schema_version: 1, product_source_modified: false,
  supersedes_patch_sha256: 'd5253bfd9e06cb9337d7e8e6f85d3bdec098efd55ab7355b351897f5f70cdcf4', changes: [] };
let patch = '';
for (const relative of [...new Set(replacements.map(entry => entry.file))]) {
  const original = fs.readFileSync(path.join(root, relative));
  const normalized = original.toString('utf8').replace(/\r\n/g, '\n');
  let source = normalized;
  for (const entry of replacements.filter(entry => entry.file === relative)) {
    const index = source.indexOf(entry.before);
    if (index < 0 || source.indexOf(entry.before, index + 1) >= 0) throw new Error('EXACT_SOURCE_CONTEXT_CHANGED');
    source = source.slice(0, index) + entry.after + source.slice(index + entry.before.length);
  }
  const diff = spawnSync(process.execPath, [path.join(root, 'scripts/run-python.js'), '-B', '-c',
    "import difflib,json,sys;p=json.load(sys.stdin);sys.stdout.write(''.join(difflib.unified_diff(p['before'].splitlines(True),p['after'].splitlines(True),fromfile='a/'+p['file'],tofile='b/'+p['file'])))"],
  { input: JSON.stringify({ before: normalized, after: source, file: relative }), encoding: 'utf8', timeout: 10000, windowsHide: true });
  if (diff.status !== 0 || diff.error) throw new Error('PREPARATION_DIFF_FAILED');
  patch += `diff --git a/${relative} b/${relative}\n` + diff.stdout;
  manifest.changes.push({ file: relative, before_sha256: hash(original), candidate_normalized_sha256: hash(source) });
}
manifest.patch_sha256 = hash(patch);
manifest.replacements = replacements;
fs.writeFileSync(path.join(__dirname, 'approved-patch-initial-proof-timeout-r2.patch'), patch);
fs.writeFileSync(path.join(__dirname, 'approved-patch-initial-proof-timeout-r2.json'), JSON.stringify(manifest, null, 2) + '\n');
const priorWrapper = fs.readFileSync(path.join(__dirname, 'approved-patch-timeout-candidate.test.cjs'), 'utf8');
fs.writeFileSync(path.join(__dirname, 'approved-patch-timeout-r2-candidate.test.cjs'), priorWrapper.replace(
  'approved-patch-initial-proof-timeout.json', 'approved-patch-initial-proof-timeout-r2.json'));
process.stdout.write(JSON.stringify({ prepared: true, product_source_modified: false, patch_sha256: manifest.patch_sha256 }) + '\n');
