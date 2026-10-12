'use strict';
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const files = ['r14_same_window_mcp_canary.py', 'root-canary-ssh.py', 'native-preflight.cjs', 'make-pins.cjs', 'root-capture.cjs', 'correlate_r14_same_window.py',
  'output-reader-app/capture.cjs', 'output-reader-app/package.json', 'output-reader-binary-pin.json', 'patch-envelope.txt',
  'prepared-target-postimage.cjs', 'static-preparation.json', 'README.md'];
const preparation = JSON.parse(fs.readFileSync(path.join(__dirname, 'static-preparation.json')));
const manifest = { kind: 'r14_same_window_new_canary_helper_manifest', observed_at: new Date().toISOString(),
  prior_manifest_sha256: 'fa4f926fca886903cfa50a0880d7e6400a7d6f2b64db1a765636911310f413d9',
  existing_window: { context_id: 'ctx_1e7e2fec6f0e43018db7a51c6980e5c2', requested_at_ms: 1791758571067, expires_at_ms: 1791776571067 },
  activation_helper_manifest_sha256: '77ab6e95eef25874c309d6233cf0f3f855f7b8f39ed14ffe03455e55de76b389',
  target: preparation.target, preimage_sha256: preparation.existing_preimage_sha256, postimage_sha256: preparation.proposed_postimage_sha256,
  checker_sha256: preparation.checker_sha256, plan_sha256: preparation.plan_sha256,
  prepared_only: true, fixture_mutated: false, checker_executed: false, runtime_contacted: false,
  credentials_read: false, canary_dispatched: false, authority_extended: false, semantic_acceptance: false,
  files: files.map(name => { const raw = fs.readFileSync(path.join(__dirname, name)); return { path: name, sha256: hash(raw), bytes: raw.length }; }) };
const file = path.join(__dirname, 'helper-manifest.json'); fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ manifest: file, sha256: hash(fs.readFileSync(file)), prepared_only: true }) + '\n');
