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
const bridgePath = path.join(app, 'electron/services/controlPlaneFileReadBridge.js');
const hostPath = path.join(app, 'electron/services/recoveryHost.js');
const bridgeBytes = fs.readFileSync(bridgePath);
const hostBytes = fs.readFileSync(hostPath);
const bridge = bridgeBytes.toString('utf8');
const host = hostBytes.toString('utf8');
const start = bridge.indexOf('function resolveDirectRegisteredFile(');
const end = bridge.indexOf('\nfunction admitFileReadBridgeRequest(', start);
if (start < 0 || end <= start) throw new Error('EXACT_RESOLVER_SOURCE_REQUIRED');
const resolver = bridge.slice(start, end).trim() + '\n';
const missing = resolver.indexOf("throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_MISSING'");
if (missing < resolver.indexOf('fs.lstatSync(cursor)') || missing < resolver.indexOf('fs.realpathSync.native(cursor)')
  || /readFile|createReadStream|openSync/.test(resolver)) throw new Error('PRE_CONTENT_MISSING_SOURCE_PROOF_UNAVAILABLE');
const hostStart = host.indexOf('async controlPlaneBoundedFileRead(');
const hostEnd = host.indexOf('\n  async ', hostStart + 1);
const hostFunction = host.slice(hostStart, hostEnd);
const validation = hostFunction.indexOf('resolveDirectRegisteredFile(workspaceRoot, admitted.path)');
const dispatch = hostFunction.indexOf('this.orchestrator.controlPlaneBoundedFileRead(');
if (validation < 0 || dispatch <= validation) throw new Error('VALIDATION_BEFORE_RUNTIME_DISPATCH_REQUIRED');
const bridgeOutput = path.join(__dirname, 'r9e-installed-controlPlaneFileReadBridge.js');
const resolverOutput = path.join(__dirname, 'r9e-installed-resolveDirectRegisteredFile.js');
const hostOutput = path.join(__dirname, 'r9e-installed-controlPlaneFileRead-host-excerpt.js');
fs.writeFileSync(bridgeOutput, bridgeBytes, { flag: 'wx' });
fs.writeFileSync(resolverOutput, resolver, { flag: 'wx' });
fs.writeFileSync(hostOutput, hostFunction, { flag: 'wx' });
const report = {
  schema_version: 1, operation: 'installed_file_read_pre_effect_source_proof', read_only: true, ok: true,
  observed_at: new Date().toISOString(), candidate,
  package: { executable_sha256: proof.executable_sha256, app_asar_sha256: proof.app_asar_sha256 },
  source: { bridge_asar_path: bridgePath, bridge_sha256: hash(bridgeBytes), bridge_saved_path: bridgeOutput,
    resolver_sha256: hash(resolver), resolver_saved_path: resolverOutput,
    recovery_host_sha256: hash(hostBytes), recovery_host_function_sha256: hash(hostFunction), recovery_host_excerpt_path: hostOutput },
  missing_throw_before_content_io: true,
  root_and_ancestor_validation_only: true,
  recovery_validation_before_orchestrator_dispatch: true,
  limitations: ['Source proof establishes rejection location; selected UNKNOWN journal/attempt/receipt lineage must independently match this diagnostic before reconciliation'],
  production_operations_performed: []
};
const output = path.join(__dirname, 'r9e-installed-file-read-source-proof.json');
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, report_path: output, source: report.source }) + '\n', () => process.exit(0));
