"use strict";

// The central enrollment UI is only a node-identity request.  It does not
// alter executionRole, create a binding/context/policy, or receive an OpenAI
// credential.  The Ubuntu operator must still approve this request and issue
// every later authority record independently.

const fs = require('node:fs');
const { URL } = require('node:url');
const { normalizeDeviceIdentity } = require('./deviceIdentity');
const { run } = require('./commandRunner');

const ENROLLMENT_TIMEOUT_MS = 15_000;
const MAX_AGENT_OUTPUT_BYTES = 16 * 1024;
const ENROLLMENT_ID_PATTERN = /^enroll_[a-z0-9][a-z0-9_-]{7,127}$/;
const CONTEXT_ID_PATTERN = /^ctx_[a-f0-9]{32}$/;
const NODE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const SAFE_ENVIRONMENT_NAMES = new Set([
  'PATH', 'SystemRoot', 'WINDIR', 'ComSpec', 'APPDATA', 'LOCALAPPDATA',
  'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'TEMP', 'TMP', 'LANG', 'LC_ALL',
  'SSL_CERT_FILE', 'SSL_CERT_DIR'
]);

function enrollmentError(code, message) {
  return Object.assign(new Error(message), { code });
}

function centralServerOrigin(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  let parsed;
  try { parsed = new URL(text); }
  catch { throw enrollmentError('CONTROL_PLANE_SERVER_URL_INVALID', 'Địa chỉ Ubuntu phải là HTTPS origin hợp lệ.'); }
  if (parsed.protocol !== 'https:' || !parsed.hostname || parsed.username || parsed.password
    || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw enrollmentError('CONTROL_PLANE_SERVER_URL_INVALID', 'Địa chỉ Ubuntu phải là HTTPS origin không có path hoặc credential.');
  }
  return parsed.origin;
}

function endpointId(deviceId) {
  const normalized = String(deviceId || '').trim().toLowerCase();
  if (!NODE_ID_PATTERN.test(normalized)) {
    throw enrollmentError('CONTROL_PLANE_DEVICE_ID_INVALID', 'Định danh thiết bị cục bộ không hợp lệ.');
  }
  return `executor-${normalized}`;
}

function centralContextId(value) {
  const contextId = typeof value === 'string' ? value.trim().toLowerCase() : '';
  if (!CONTEXT_ID_PATTERN.test(contextId)) {
    throw enrollmentError('CONTROL_PLANE_CONTEXT_ID_INVALID', 'Context ID từ Ubuntu không hợp lệ.');
  }
  return contextId;
}

function safeEnrollmentEnvironment(source = process.env) {
  const result = {};
  for (const name of SAFE_ENVIRONMENT_NAMES) {
    if (typeof source?.[name] === 'string' && source[name]) result[name] = source[name];
  }
  return result;
}

function parseEnrollmentResult(stdout, expectedDeviceId) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'device_id,enrollment_id,state'
    || !ENROLLMENT_ID_PATTERN.test(String(payload.enrollment_id || ''))
    || String(payload.device_id || '').toLowerCase() !== String(expectedDeviceId || '').toLowerCase()
    || payload.state !== 'pending_operator_approval') {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment receipt không đúng target hoặc trạng thái.');
  }
  return Object.freeze({
    enrollment_id: String(payload.enrollment_id),
    device_id: String(payload.device_id).toLowerCase(),
    state: 'pending_operator_approval'
  });
}

function parseReadOnlyPolicyInstallResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'enabled,expires_at_ms,operation,policy_sha256,runtime_mode,windows_acl_verified'
    || payload.operation !== 'control_plane_read_only_policy_installed'
    || payload.enabled !== true
    || !Number.isSafeInteger(payload.expires_at_ms) || payload.expires_at_ms <= Date.now()
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || payload.runtime_mode !== 'packaged'
    || payload.windows_acl_verified !== false) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy receipt không đúng trạng thái read-only đã xác nhận.');
  }
  return Object.freeze({
    enabled: true,
    expires_at_ms: payload.expires_at_ms,
    policy_sha256: String(payload.policy_sha256).toLowerCase(),
    runtime_mode: 'packaged',
    windows_acl_verified: false
  });
}

class ControlPlaneEnrollmentService {
  constructor({ paths, runner = run, environment = process.env } = {}) {
    if (!paths || typeof paths.runtimeMode !== 'function' || typeof paths.portablePython !== 'function'
      || typeof paths.controlPlaneNodeAgent !== 'function' || typeof paths.controlPlaneNodeConfigFile !== 'function'
      || typeof paths.appRoot !== 'function' || typeof paths.executablePath !== 'function') {
      throw new TypeError('ControlPlaneEnrollmentService requires complete runtime paths.');
    }
    this.paths = paths;
    this.runner = runner;
    this.environment = environment;
  }

  async request({ serverUrl, deviceIdentity } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_ENROLLMENT_PACKAGED_REQUIRED', 'Pairing chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const origin = centralServerOrigin(serverUrl);
    const identity = normalizeDeviceIdentity(deviceIdentity);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_ENROLLMENT_RUNTIME_MISSING', `${label} đóng gói cho pairing không sẵn sàng.`);
      }
    }
    const endpoint = endpointId(identity.device_id);
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'request-enrollment',
        '--config', config,
        '--server-url', origin,
        '--device-id', identity.device_id,
        '--endpoint-id', endpoint,
        '--display-name', identity.display_name,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_ENROLLMENT_FAILED');
      throw enrollmentError(code, 'Không thể gửi yêu cầu pairing tới Ubuntu.');
    }
    const receipt = parseEnrollmentResult(result?.stdout, identity.device_id);
    return Object.freeze({
      ...receipt,
      server_origin: origin,
      endpoint_id: endpoint,
      display_name: identity.display_name
    });
  }

  async installReadOnlyPolicy({ contextId, replaceExisting = false } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_POLICY_PACKAGED_REQUIRED', 'Policy read-only chỉ cài từ candidate packaged đã được xác minh.');
    }
    const normalizedContextId = centralContextId(contextId);
    if (typeof replaceExisting !== 'boolean') {
      throw enrollmentError('CONTROL_PLANE_POLICY_REPLACE_INVALID', 'Lựa chọn thay thế policy cục bộ không hợp lệ.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_POLICY_RUNTIME_MISSING', `${label} đóng gói cho read-only policy không sẵn sàng.`);
      }
    }
    const args = [
      '-I', agent, 'install-read-only-policy-from-context',
      '--config', config,
      '--context-id', normalizedContextId,
      '--confirm-install',
      '--project-root', this.paths.appRoot(),
      '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ];
    if (replaceExisting) args.push('--replace');
    let result;
    try {
      result = await this.runner(python, args, {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_POLICY_INSTALL_FAILED');
      throw enrollmentError(code, 'Không thể cài read-only policy từ context của Ubuntu.');
    }
    return parseReadOnlyPolicyInstallResult(result?.stdout);
  }
}

module.exports = {
  ENROLLMENT_TIMEOUT_MS,
  MAX_AGENT_OUTPUT_BYTES,
  centralServerOrigin,
  centralContextId,
  endpointId,
  safeEnrollmentEnvironment,
  parseEnrollmentResult,
  parseReadOnlyPolicyInstallResult,
  ControlPlaneEnrollmentService
};
