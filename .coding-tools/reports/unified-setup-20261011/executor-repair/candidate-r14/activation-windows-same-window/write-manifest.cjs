'use strict';
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const repo = 'E:\\Github\\Tools-Codex-web', h = require('./transition-r14.cjs');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const helperFiles = ['transition-r14.cjs', 'launch-child.ps1', 'query-job.py', 'observe-r14.cjs', 'offline-check.cjs', 'README.md'];
const dependencyFiles = ['runtimePaths.js', 'recoveryIpc.js', 'recoveryHostLauncher.js', 'processIdentity.js', 'fullCleanActivation.js', 'controlPlaneRouteEvidence.js'];
const manifest = { kind: 'r14_same_window_windows_activation_helper_manifest', observed_at: new Date().toISOString(),
  approval_required: 'Separate future human approval explicitly covering r13 owned idle Sandbox cleanup/refresh, r14 activation and same-expiry replacement pilot',
  operation: h.activationOperation, target: h.target, existing_authority_window: h.currentAuthorityWindow,
  authority_extension: false, ubuntu_deploy_or_restart: false, windows_reboot: false, semantic_acceptance: false,
  new_canary_scope: 'one new edit-test-proof identity; exact pre/post file chosen after activation; supported stdout/TAP captured immediately; semantic acceptance remains pending',
  based_on_r13_transition_sha256: sha(path.join(__dirname, '../../candidate-r13/activation-windows-5h/transition-r13.cjs')),
  package_parity_sha256: sha(path.join(__dirname, '../candidate-parity-20261011T231029495Z.json')),
  source_freeze_sha256: sha(path.join(__dirname, '../source-freeze.json')),
  preserved_pending_families: h.oldPending, runtime_activated: false, server_mutated: false,
  supported_cleanup_operation: 'one r13 full_clean_refresh with allowAcceptancePending=true before post-cleanup freeze',
  scoped_pilot_operation: 'recovery revokes prior pilot; one same-principal/binding/expiry replacement before reopening scoped_pilot',
  helper_files: helperFiles.map(file => ({ file, sha256: sha(path.join(__dirname, file)) })),
  dependencies: dependencyFiles.map(name => { const file = 'electron/services/' + name; return { file, sha256: sha(path.join(repo, file)) }; }) };
const file = path.join(__dirname, 'helper-manifest.json');
if (fs.existsSync(file)) {
  const pin = process.argv.find(value => value.startsWith('--supersede-sha256='))?.slice(19);
  const priorName = process.argv.find(value => value.startsWith('--preserved-prior='))?.slice(18) || 'helper-manifest.pre-canary-envelope.json';
  if (!/^helper-manifest\.pre-[A-Za-z0-9_-]+\.json$/.test(priorName)) throw new Error('EXACT_PRESERVED_PRIOR_NAME_REQUIRED');
  const prior = path.join(__dirname, priorName);
  if (!pin || sha(file) !== pin || !fs.existsSync(prior) || sha(prior) !== pin) throw new Error('EXACT_PRESERVED_MANIFEST_REQUIRED');
  fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + '\n');
} else fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, manifest: file, manifest_sha256: sha(file), runtime_mutated: false, server_mutated: false }) + '\n');
