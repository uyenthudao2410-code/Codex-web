'use strict';
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict'), crypto = require('node:crypto');
const file = path.join(__dirname, 'resume.cjs'), source = fs.readFileSync(file, 'utf8');
const approvedSource = source.slice(source.indexOf('function approved('), source.indexOf('function launch('));
const reserveSource = source.slice(source.indexOf('function reserve('), source.indexOf('async function preflight('));
const now = 1791735600000, target = { binding_id: 'bind', device_id: 'device', workspace_id: 'workspace', workspace_generation: 'generation', profile: 'web-mcp-assistant' };
const server = { ok: true, host: '100.116.112.22', service: 'codex-control-plane.service', source_revision: 'revision', binding_id: 'bind', admission: 'recovery', observed_at_ms: now, service_instance_id: 'service', state: { queued_actions: 0, accepted_actions: 0, open_writers: 0, open_tasks: 0, target_unsettled_actions: 0 } };
const renewal = { ...server, requested_at_ms: now - 1000, expires_at_ms: now - 1000 + 3600000, root: 'repo', profile: target.profile, policy_assignment: target };
const context = { process: { argv: ['--operator-approved-r11-resume'] }, verifyCandidate() {}, sha: () => 'digest', arg: () => 'digest', __filename: file,
  pinned: name => name === 'server' ? server : renewal, Date: { now: () => now }, serverRevision: 'revision', target, repo: 'repo', key: x => x,
  fail: code => { throw Object.assign(new Error(), { code }); } };
vm.runInNewContext(approvedSource, context);
const passed = [];
assert.equal(context.approved(true), renewal); passed.push('new_exact60m_receipt_admitted');
server.admission = 'scoped_pilot'; assert.throws(() => context.approved(), { code: 'FRESH_QUIESCENT_RECOVERY_REQUIRED' }); server.admission = 'recovery'; passed.push('open_intake_rejected');
server.observed_at_ms = now - 60000; assert.throws(() => context.approved(), { code: 'FRESH_QUIESCENT_RECOVERY_REQUIRED' }); server.observed_at_ms = now; passed.push('stale_server_observation_rejected');
renewal.requested_at_ms = 1791734596302; renewal.expires_at_ms = renewal.requested_at_ms + 3600000; assert.throws(() => context.approved(true), { code: 'NEW_EXACT_APPROVED_60M_RENEWAL_REQUIRED' }); passed.push('old_authority_window_rejected');
let reserved = false;
const reservation = { path, __dirname: '/isolated-fixture', Date: { now: () => now }, __filename: file, sha: () => 'digest', fs: {
  openSync(_p, flag) { assert.equal(flag, 'wx'); if (reserved) throw Object.assign(new Error(), { code: 'EEXIST' }); reserved = true; return 1; },
  writeFileSync() {}, fsyncSync() {}, closeSync() {}
} };
vm.runInNewContext(reserveSource, reservation); reservation.reserve('runtime'); assert.throws(() => reservation.reserve('runtime'), { code: 'EEXIST' }); passed.push('durable_launch_reservation_refuses_duplicate');
assert(source.includes('ping?.process_start_token !== owner.process_start_token') && source.includes('!same(owner, started.identity)') && source.includes('descriptor.owner_pid !== started.pid'));
passed.push('descriptor_adoption_checks_exact_spawn_identity_and_authenticated_ping');
const launcher = fs.readFileSync(path.join(__dirname, 'breakaway-launch.py'), 'utf8');
assert(launcher.includes('subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP') && launcher.includes('if child_job["associated"]') && launcher.includes('"--recovery-host"'));
passed.push('fixed_hidden_recovery_launch_checks_child_job_independence');
const receipt = { at_utc: new Date().toISOString(), checks_passed: passed, check_count: passed.length, helper_sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'), launcher_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname, 'breakaway-launch.py'))).digest('hex'), runtime_spawned: false, external_mutation: false, proof_scope: 'focused offline guards; child-job independence requires live root launch' };
fs.writeFileSync(path.join(__dirname, 'proof-receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(receipt));
