'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const root = 'E:\\DEV\\Codex-web';
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e/win-unpacked');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const app = path.join(candidate, 'resources/app.asar');
const proof = JSON.parse(fs.readFileSync(path.join(root, '.coding-tools/reports/workspace-display-20261012-r10/r9e-candidate-verification.json'), 'utf8'));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
if (fs.realpathSync(process.execPath).toLowerCase() !== fs.realpathSync(executable).toLowerCase()
  || hash(originalFs.readFileSync(executable)) !== proof.executable_sha256
  || hash(originalFs.readFileSync(app)) !== proof.app_asar_sha256) throw new Error('EXACT_INSTALLED_PACKAGE_REQUIRED');
const modulePath = path.join(app, 'electron/services/runtimeOrchestrator.js');
const bytes = fs.readFileSync(modulePath);
const source = bytes.toString('utf8');
const start = source.indexOf('async controlPlaneBoundedFileRead(');
const end = source.indexOf('\n  async ', start + 1);
if (start < 0 || end <= start) throw new Error('BOUNDED_FILE_READ_SOURCE_UNAVAILABLE');
const method = source.slice(start, end);
const readIndex = method.indexOf('const structured = await callLocalTool(FILE_READ_LOCAL_TOOL_NAME, readArguments, \'read\')');
const resolveIndex = method.indexOf('resolveDirectRegisteredFile(expectedWorkspace, admission.path)');
if (readIndex < 0 || resolveIndex <= readIndex) throw new Error('POST_READ_SOURCE_ORDER_UNVERIFIED');
const evidencePath = path.join(__dirname, 'r9e-installed-controlPlaneBoundedFileRead-orchestrator-excerpt.js');
fs.writeFileSync(evidencePath, method, { flag: 'wx' });
const previousSource = path.join(__dirname, 'r9e-installed-file-read-source-proof.json');
const previousJournal = path.join(__dirname, 'local-unknown-file-read-action-evidence.json');
const report = {
  schema_version: 1, operation: 'installed_file_read_source_effect_phase_correction', read_only: true, ok: true,
  observed_at: new Date().toISOString(), candidate,
  package: { executable_sha256: proof.executable_sha256, app_asar_sha256: proof.app_asar_sha256 },
  source: { asar_module_path: modulePath, module_sha256: hash(bytes), method_sha256: hash(method), excerpt_path: evidencePath },
  after_read_resolver_call_present: true,
  applicable_branch: 'structured.path is absolute, including registered AutoCAD outside native primary Codex-web root',
  read_call_precedes_same_resolver: true,
  failure_phase_from_target_missing_code: 'ambiguous: upfront Recovery Host validation or post-read absolute path projection',
  known_pre_effect_refusal_proven: false,
  selected_unknown_action_effect_outcome: 'unknown; retain without replay or rejected/completed inference',
  corrected_prior_claims: [
    { path: previousSource, sha256: hash(fs.readFileSync(previousSource)), correction: 'Resolver performs only metadata operations, but can be invoked after File API read. Upfront call existence does not establish exclusive failure origin.' },
    { path: previousJournal, sha256: hash(fs.readFileSync(previousJournal)), correction: 'Remove inference that TARGET_MISSING proves no content read; exact action journals establish only UNKNOWN and diagnostic correlation.' }
  ],
  next_action: 'Require authenticated phase-specific original trace/receipt before terminal rejection; otherwise preserve UNKNOWN and use supported unknown reconciliation/quarantine workflow without completing action',
  production_operations_performed: []
};
const output = path.join(__dirname, 'file-read-source-effect-phase-correction.json');
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, report_path: output, source: report.source, known_pre_effect_refusal_proven: false }) + '\n', () => process.exit(0));
