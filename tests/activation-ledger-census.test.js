const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pythonStatus } = require('../electron/services/environmentService');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { canonicalLedgerCensus, FullCleanActivation } = require('../electron/services/fullCleanActivation');

const REPO_ROOT = path.resolve(__dirname, '..');
const PACKAGE_ROOT = path.join(REPO_ROOT, 'resources', 'coding-tools-mcp');

const FIXTURE_SOURCE = `
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from coding_tools_mcp.lifecycle_census import open_lifecycle_census_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger

workspace = Path(sys.argv[1])
ledger = OrchestrationLedger(workspace)
old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
with patch("coding_tools_mcp.orchestration_ledger.utc_now", return_value=old):
    accepting = ledger.create_run(objective="historical pending acceptance")
    accepting_wave = ledger.create_wave(accepting, execution_mode="mcp_only")
    ledger.append_event(accepting, wave_id=accepting_wave, event_type="state", state_after="ACCEPTING")

current = ledger.create_run(objective="current completed task context")
current_wave = ledger.create_wave(current, execution_mode="mcp_only")
ledger.append_event(current, wave_id=current_wave, event_type="state", state_after="CHECKPOINTED")
ledger.finish_wave(current_wave, status="accepted")
ledger.finish_run(current, status="accepted")
context_dir = workspace / ".coding-tools" / "task-contexts"
context_dir.mkdir(parents=True)
context = context_dir / "current.json"
context.write_text(json.dumps({"orchestration": {
    "run_id": current, "wave_id": current_wave, "orchestration_state": "CHECKPOINTED"
}}), encoding="utf-8")
with open_lifecycle_census_snapshot(workspace) as snapshot:
    initial_snapshot = snapshot.snapshot_metadata
print(json.dumps({"accepting_run_id": accepting, "snapshot": initial_snapshot}))
`;

test('canonical census leaves a clean packaged Python resource tree unchanged', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-census-bytecode-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'workspace');
  const resourcesRoot = path.join(root, 'resources');
  const packageRoot = path.join(resourcesRoot, 'coding-tools-mcp', 'coding_tools_mcp');
  const paths = createRuntimePaths({ dataRoot: path.join(root, 'data'), resourcesRoot, appRoot: REPO_ROOT });
  const ledger = path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3');
  fs.mkdirSync(path.dirname(ledger), { recursive: true });
  fs.mkdirSync(packageRoot, { recursive: true });
  fs.writeFileSync(ledger, 'bytecode-regression-fixture');
  fs.writeFileSync(path.join(packageRoot, '__init__.py'), '');
  fs.writeFileSync(path.join(packageRoot, 'imported_leaf.py'), 'VALUE = 1\n');
  fs.writeFileSync(path.join(packageRoot, 'activation_ledger_census.py'),
    'import json, sys\nfrom . import imported_leaf\nprint(json.dumps({"observed_at_unix_seconds": int(sys.dont_write_bytecode)}))\n');
  const before = fs.readdirSync(packageRoot).sort();
  const python = await pythonStatus(paths);
  assert.equal(python.installed, true);

  const census = await canonicalLedgerCensus({ paths, workspace, pythonStatusFn: async () => python });

  assert.equal(census.observed_at_unix_seconds, 1, 'the actual interpreter must disable bytecode writes');
  assert.deepEqual(fs.readdirSync(packageRoot).sort(), before, 'census and its import closure must not create __pycache__');
});

async function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-activation-census-'));
  const workspace = path.join(root, 'workspace');
  const paths = createRuntimePaths({
    dataRoot: path.join(root, 'data'),
    resourcesRoot: path.join(REPO_ROOT, 'resources'),
    appRoot: REPO_ROOT
  });
  fs.mkdirSync(workspace, { recursive: true });
  fs.mkdirSync(paths.dataRoot(), { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const python = await pythonStatus(paths);
  assert.equal(python.installed, true, 'canonical ledger census requires the supported Python runtime');
  const runPython = (source, ...args) => execFileSync(python.command, [
    ...(python.prefixArgs || []), '-c', source, ...args
  ], {
    cwd: workspace,
    encoding: 'utf8',
    windowsHide: true,
    timeout: 15_000,
    env: {
      ...process.env,
      PYTHONPATH: [PACKAGE_ROOT, path.join(PACKAGE_ROOT, 'python_vendor'), process.env.PYTHONPATH || '']
        .filter(Boolean).join(path.delimiter)
    }
  }).trim();
  const initial = JSON.parse(runPython(FIXTURE_SOURCE, workspace));
  const ledgerPath = path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3');
  const contextPath = path.join(workspace, '.coding-tools', 'task-contexts', 'current.json');
  const ledgerBefore = fs.readFileSync(ledgerPath);
  const contextBefore = fs.readFileSync(contextPath);
  const ledgerSha256 = crypto.createHash('sha256').update(ledgerBefore).digest('hex');
  const assertUnchanged = (census) => {
    assert.deepEqual(fs.readFileSync(ledgerPath), ledgerBefore, 'census must not rewrite the canonical ledger');
    assert.deepEqual(fs.readFileSync(contextPath), contextBefore, 'census must not rewrite current task context');
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(ledgerPath)).digest('hex'), ledgerSha256);
    assert.equal(census.snapshot.sha256, initial.snapshot.sha256);
    assert.equal(census.snapshot.logical_sha256, initial.snapshot.logical_sha256);
    assert.equal(census.snapshot.backup_api_copy, true);
    assert.equal(census.snapshot.immutable, true);
    assert.equal(census.snapshot.query_only, true);
    assert.deepEqual(census.snapshot.integrity_check, ['ok']);
    assert.equal(census.snapshot.foreign_key_check_rows, 0);
    assert.equal(census.mutated_canonical_ledger, false);
    assert.equal(census.content_free, true);
  };
  return { paths, workspace, ledgerPath, runPython, initial, assertUnchanged };
}

test('real stopped-runtime census preserves historical pending acceptance without contextual projection drift', async (t) => {
  const { paths, workspace, ledgerPath, runPython, initial, assertUnchanged } = await fixture(t);
  const refused = await canonicalLedgerCensus({ paths, workspace });
  assert.equal(refused.safe, false);
  assert.equal(refused.code, 'ACCEPTANCE_PENDING');
  assert.deepEqual(refused.lifecycle.awaiting_acceptance_runs, [initial.accepting_run_id]);
  assert.equal(refused.lifecycle.projection_drift, false);
  assert.deepEqual(refused.lifecycle.blockers, ['acceptance_pending']);
  assertUnchanged(refused);

  const allowed = await canonicalLedgerCensus({ paths, workspace, allowAcceptancePending: true });
  assert.equal(allowed.safe, true);
  assert.equal(allowed.code, 'READY');
  assert.deepEqual(allowed.lifecycle.awaiting_acceptance_runs, [initial.accepting_run_id]);
  assert.equal(allowed.lifecycle.ordinary_active_runs, 1, 'historical acceptance must remain active in the ledger');
  assert.equal(allowed.lifecycle.projection_drift, false);
  assert.deepEqual(allowed.lifecycle.blockers, []);
  assertUnchanged(allowed);

  const held = await canonicalLedgerCensus({ paths, workspace, allowAcceptancePending: true, holdExclusive: true });
  try {
    assert.equal(held.safe, true);
    assert.equal(held.census_fingerprint, allowed.census_fingerprint, 'held recheck must bind the same census');
    assert.equal(typeof held.release_exclusive_gate, 'function');
    assert.equal(Object.keys(held).includes('release_exclusive_gate'), false);
    const gateProbe = `
import sys
from pathlib import Path
from coding_tools_mcp.ledger_file_gate import LedgerGateTimeout, ledger_access_gate
try:
    with ledger_access_gate(Path(sys.argv[1]), timeout_seconds=0.05):
        print("available")
except LedgerGateTimeout:
    print("held")
`;
    assert.equal(runPython(gateProbe, ledgerPath), 'held', 'held census must fence supported ledger writers');
    assert.equal(await held.release_exclusive_gate(), true);
    assert.equal(runPython(gateProbe, ledgerPath), 'available', 'release must close the census child and unblock writers');
    assertUnchanged(held);
  } finally {
    await held.release_exclusive_gate();
  }
});

test('full-clean preflight admits real historical acceptance only with explicit acceptance-pending permission', async (t) => {
  const { paths, workspace, initial, assertUnchanged } = await fixture(t);
  const requests = [];
  const coordinator = new FullCleanActivation({
    paths,
    settings: { load: () => ({ workspace }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ safe: true, code: 'COMPONENT_STOPPED', workspace })
    },
    canonicalLedgerCensus: (options) => {
      requests.push(options);
      return canonicalLedgerCensus({ paths, ...options });
    }
  });

  await assert.rejects(coordinator.preflight(), (error) => {
    assert.equal(error.code, 'ACCEPTANCE_PENDING');
    assert.deepEqual(error.details.lifecycle.blockers, ['acceptance_pending']);
    assertUnchanged(error.details);
    return true;
  });
  const preflight = await coordinator.preflight({ allowAcceptancePending: true });
  assert.equal(preflight.safe, true);
  assert.equal(preflight.code, 'COMPONENT_STOPPED');
  const census = preflight.runtime.canonical_ledger_census;
  assert.equal(census.safe, true);
  assert.equal(census.code, 'READY');
  assert.deepEqual(census.lifecycle.awaiting_acceptance_runs, [initial.accepting_run_id]);
  assert.deepEqual(requests.map((item) => item.allowAcceptancePending), [false, true]);
  assertUnchanged(census);
  assert.equal(fs.existsSync(paths.activationEpochFile()), false, 'preflight must not create an activation or start services');
});
