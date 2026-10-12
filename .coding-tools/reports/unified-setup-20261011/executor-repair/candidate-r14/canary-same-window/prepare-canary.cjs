'use strict';
// Static artifact preparation only. Does not patch the fixture, run tests or contact either runtime.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), zlib = require('node:zlib');
const repo = 'E:\\Github\\Tools-Codex-web', target = 'tests/fixtures/initial-proof-canary-target.cjs', checker = 'tests/fixtures/initial-proof-canary-check.cjs';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const raw = fs.readFileSync(path.join(repo, target)), check = fs.readFileSync(path.join(repo, checker));
if (sha(raw) !== 'd1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e'
  || sha(check) !== '059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230') throw new Error('EXACT_EXISTING_CANARY_FIXTURE_CHANGED');
const old = "if (['passed'].includes(proofStatus))", next = "if (proofStatus === 'passed')", source = raw.toString('utf8');
if (source.split(old).length !== 2) throw new Error('EXACT_ONE_LINE_PREIMAGE_REQUIRED');
const post = Buffer.from(source.replace(old, next), 'utf8');
const envelope = ['*** Begin Patch', '*** Write Exact File: ' + target,
  '@@ encoding=zlib-base64 preimage_sha256=' + sha(raw) + ' postimage_sha256=' + sha(post),
  '+' + zlib.deflateSync(post).toString('base64'), '*** End Patch'].join('\n');
const plan = { argv: ['node', '--test', checker], cwd: '', timeout_ms: 60000, max_output_bytes: 32768 };
const canonical = value => value && typeof value === 'object' && !Array.isArray(value)
  ? '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}'
  : Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']' : JSON.stringify(value);
fs.writeFileSync(path.join(__dirname, 'patch-envelope.txt'), envelope, { flag: 'wx' });
fs.writeFileSync(path.join(__dirname, 'prepared-target-postimage.cjs'), post, { flag: 'wx' });
const receipt = { kind: 'r14_new_canary_static_preparation', observed_at: new Date().toISOString(), target, checker,
  existing_preimage_sha256: sha(raw), proposed_postimage_sha256: sha(post), proposed_postimage_bytes: post.length,
  patch_sha256: sha(Buffer.from(envelope)), checker_sha256: sha(check), verification: plan, plan_sha256: sha(Buffer.from(canonical(plan))),
  old_r13_preimage_reset: false, fixture_mutated: false, checker_executed: false, runtime_contacted: false,
  new_idempotency_namespace: 'r14-same-window-new-canary', authority_expires_at_ms: 1791776571067 };
fs.writeFileSync(path.join(__dirname, 'static-preparation.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(receipt) + '\n');
