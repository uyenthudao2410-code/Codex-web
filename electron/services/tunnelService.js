const crypto = require('node:crypto');
const fs = require('node:fs');
const { spawn } = require('node:child_process');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { canConnect } = require('./environmentService');
const { run } = require('./commandRunner');
const {
  isAlive,
  captureSpawnedProcessIdentity,
  requireExactStoredProcessIdentity
} = require('./nativeService');
const { classifyStoredDeviceOwner } = require('./deviceIdentity');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  sameProcessIdentity,
  terminateExactProcessTree
} = require('./processIdentity');
const {
  CONNECTOR_ATTESTATION_HEADER,
  connectorAttestationHeader
} = require('./connectorAttestation');

function tunnelFingerprint(settings, deviceId = '', activationEpochId = '') {
  const payload = {
    device_id: String(deviceId || ''),
    tunnel_id: String(settings.tunnelId || ''),
    mcp_port: Number(settings.mcpPort),
    health_port: Number(settings.healthPort)
  };
  if (String(activationEpochId || '').trim()) payload.activation_epoch_id = String(activationEpochId).trim();
  return crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
}

function storedProcessReceipt(state) {
  const pid = Number(state?.tunnelPid);
  return {
    pid: Number.isSafeInteger(pid) && pid > 0 ? pid : null,
    process_start_token: normalizeProcessStartToken(state?.tunnelProcessStartToken)
  };
}

function sameStoredProcessReceipt(state, expected) {
  const actual = storedProcessReceipt(state);
  return actual.pid === (expected?.pid ?? null)
    && actual.process_start_token === (expected?.process_start_token ?? null);
}

function persistenceCleanupFailure(persistenceError, cleanupError) {
  cleanupError.persistenceError = persistenceError;
  cleanupError.details = {
    ...(cleanupError.details || {}),
    persistence_error_code: persistenceError?.code || '',
    persistence_error_message: persistenceError?.message || ''
  };
  if (!cleanupError.code) cleanupError.code = 'TUNNEL_PROCESS_PERSISTENCE_CLEANUP_FAILED';
  return cleanupError;
}

function parseLoopbackListenerPid(value, port) {
  const target = `127.0.0.1:${Number(port)}`;
  const matches = new Set();
  for (const line of String(value || '').split(/\r?\n/)) {
    const fields = line.trim().split(/\s+/);
    if (fields.length < 5 || String(fields[0]).toUpperCase() !== 'TCP') continue;
    if (fields[1] !== target || String(fields[3]).toUpperCase() !== 'LISTENING') continue;
    const pid = Number(fields[4]);
    if (Number.isInteger(pid) && pid > 0) matches.add(pid);
  }
  return matches.size === 1 ? [...matches][0] : null;
}

async function loopbackListenerPid(port) {
  const result = await run('netstat.exe', ['-ano', '-p', 'tcp'], { allowFailure: true, timeoutMs: 3000 });
  if (result.code !== 0) return null;
  return parseLoopbackListenerPid(result.stdout, port);
}

class TunnelService {
  constructor(log, paths = defaultPaths, device = null, options = {}) {
    this.log = log;
    this.paths = paths;
    this.device = device;
    this.listenerPidProbe = null;
    this.controlPlaneHealthProbe = null;
    this.processIdentityObserver = typeof options.processIdentityObserver === 'function'
      ? options.processIdentityObserver
      : observeProcessIdentity;
    this.exactProcessTerminator = typeof options.exactProcessTerminator === 'function'
      ? options.exactProcessTerminator
      : terminateExactProcessTree;
    this.identitySleep = typeof options.identitySleep === 'function'
      ? options.identitySleep
      : (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  }

  async probeControlPlaneHealth(settings, pid) {
    if (typeof this.controlPlaneHealthProbe === 'function') {
      return this.controlPlaneHealthProbe(settings, pid);
    }
    const executable = this.paths?.tunnelExecutable?.();
    if (!executable || !fs.existsSync(executable)) return false;
    const result = await run(executable, [
      'health', '--port', String(settings.healthPort), '--pid', String(pid),
      '--require-control-plane-poll', '--json'
    ], { allowFailure: true, timeoutMs: 3000 });
    return Number(result?.code) === 0;
  }

  assertOwnedLive(state) {
    if (!this.device || !isAlive(state.tunnelPid)) return;
    const ownership = classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId);
    if (ownership === 'owned') return;
    const code = ownership === 'foreign' ? 'TUNNEL_PROCESS_FOREIGN_DEVICE' : 'TUNNEL_PROCESS_OWNER_UNVERIFIED';
    throw Object.assign(new Error(ownership === 'foreign' ? 'Coding Tunnel process state belongs to another device; refusing to adopt or terminate it.' : 'Coding Tunnel process state predates device ownership metadata; refusing to adopt or terminate the live process.'), { code, ownerDeviceId: String(state.tunnelDeviceId || '') || null, expectedDeviceId: this.device.deviceId });
  }

  async start(settings, runtimeApiKey, token, progress, options = {}) {
    if (!fs.existsSync(this.paths.tunnelExecutable())) throw new Error('Gói cài đặt thiếu tệp tunnel-client.exe.');
    if (!runtimeApiKey) throw new Error('Vui lòng lưu OpenAI Runtime API Key trước.');
    if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    // Stop only the exact receipt observed from the current state.  The
    // helper re-reads the receipt immediately before terminating so a
    // concurrent replacement cannot be killed by a stale start call.
    const current = readJson(this.paths.stateFile(), {});
    const currentIdentity = await this.ownedIdentity(current);
    if (currentIdentity) await this.terminateOwnedIdentity(currentIdentity);
    else if (current.tunnelPid || current.tunnelProcessStartToken) this.clearOwnedState(storedProcessReceipt(current));
    const activationEpochId = String(options.activationEpochId || '').trim();
    progress('tunnel-start', 72, 'Đang kết nối OpenAI MCP Tunnel');
    ensureParent(this.paths.tunnelLogFile());
    rotateLog(this.paths.tunnelLogFile());
    const output = fs.openSync(this.paths.tunnelLogFile(), 'a');
    const env = {
      ...process.env,
      CONTROL_PLANE_API_KEY: runtimeApiKey,
      MCP_RUNTIME_HEADER_VALUE: `Bearer ${token}`
    };
    if (activationEpochId) env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID = activationEpochId;
    const attestation = options.connectorAttestation && typeof options.connectorAttestation === 'object'
      ? options.connectorAttestation
      : null;
    let attestationValue = '';
    if (attestation) {
      attestationValue = connectorAttestationHeader({
        secret: attestation.secret,
        clientId: attestation.clientId || 'chatweb',
        clientType: attestation.clientType || 'chatweb',
        activationEpochId: attestation.activationEpochId || activationEpochId,
        processInstanceId: attestation.processInstanceId,
        serverInstanceId: attestation.serverInstanceId,
        contractSha256: attestation.contractSha256
      });
      env.MCP_DISCOVERY_ATTESTATION_VALUE = attestationValue;
      // The attestation is deliberately added only to ordinary forwarded MCP
      // traffic.  tunnel-client's discovery-extra-headers are its own local
      // health/probe requests and must not manufacture a ChatWeb receipt.
    }
    const args = [
      'run',
      '--control-plane.tunnel-id', settings.tunnelId,
      '--control-plane.api-key', 'env:CONTROL_PLANE_API_KEY',
      '--health.listen-addr', `127.0.0.1:${settings.healthPort}`,
      '--mcp.server-url', `url=http://127.0.0.1:${settings.mcpPort}/mcp,channel=main`,
      '--mcp.extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE',
      '--mcp.extra-headers', 'X-Coding-Tools-Client-Id: chatweb',
      '--mcp.extra-headers', 'X-Coding-Tools-Client-Type: chatweb',
      ...(attestationValue ? ['--mcp.extra-headers', `${CONNECTOR_ATTESTATION_HEADER}: env:MCP_DISCOVERY_ATTESTATION_VALUE`] : []),
      '--mcp.discovery-extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE',
      '--mcp.discovery-extra-headers', 'X-Coding-Tools-Client-Id: chatweb',
      '--mcp.discovery-extra-headers', 'X-Coding-Tools-Client-Type: chatweb',
      '--log.file', this.paths.tunnelLogFile()
    ];
    const proxyUrl = Object.prototype.hasOwnProperty.call(settings, 'effectiveProxyUrl')
      ? settings.effectiveProxyUrl
      : settings.proxyUrl;
    if (proxyUrl) args.push('--control-plane.http-proxy', proxyUrl);
    let child;
    let spawnedIdentity;
    try {
      child = spawn(this.paths.tunnelExecutable(), args, {
        detached: true,
        windowsHide: true,
        stdio: ['ignore', output, output],
        env
      });
      await new Promise((resolve, reject) => {
        child.once('spawn', resolve);
        child.once('error', reject);
      });
      child.unref();
      spawnedIdentity = await captureSpawnedProcessIdentity(child.pid, {
        processIdentityObserver: this.processIdentityObserver,
        sleep: this.identitySleep,
        kind: 'TUNNEL'
      });
    } finally {
      fs.closeSync(output);
    }
    try {
      updateJsonAtomic(this.paths.stateFile(), (state) => {
        if (!sameStoredProcessReceipt(state, { pid: null, process_start_token: null })) {
          throw Object.assign(new Error('Coding Tunnel process state changed before launch receipt persistence.'), {
            code: 'TUNNEL_PROCESS_STATE_CHANGED'
          });
        }
        return {
          ...state,
          tunnelPid: child.pid,
          tunnelProcessStartToken: spawnedIdentity.process_start_token,
          tunnelId: settings.tunnelId,
          tunnelFingerprint: tunnelFingerprint(settings, this.device?.deviceId || '', activationEpochId),
          tunnelInstanceId: crypto.randomBytes(12).toString('hex'),
          tunnelActivationEpochId: activationEpochId || null,
          tunnelDeviceId: this.device?.deviceId || '',
          tunnelDeviceInstanceId: this.device?.deviceInstanceId || '',
          tunnelStartedAt: new Date().toISOString()
        };
      });
    } catch (error) {
      try {
        await this.exactProcessTerminator(spawnedIdentity, {
          observeProcessIdentity: this.processIdentityObserver
        });
      } catch (cleanupError) {
        throw persistenceCleanupFailure(error, cleanupError);
      }
      throw error;
    }
    for (let index = 0; index < 30; index += 1) {
      const listenerPid = await (this.listenerPidProbe || loopbackListenerPid)(settings.healthPort);
      if (listenerPid === child.pid && await canConnect('127.0.0.1', settings.healthPort, 500)) {
        const state = readJson(this.paths.stateFile(), {});
        let currentIdentity;
        try { currentIdentity = await this.ownedIdentity(state); } catch (error) { throw error; }
        if (currentIdentity && sameProcessIdentity(spawnedIdentity, currentIdentity)) {
          this.log.info('OpenAI Tunnel đã khởi động', { pid: child.pid, tunnelId: settings.tunnelId, activationEpochId: activationEpochId || null });
          return {
            pid: child.pid,
            processStartToken: spawnedIdentity.process_start_token,
            instanceId: state.tunnelInstanceId || null,
            activationEpochId: activationEpochId || null
          };
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    await this.exactProcessTerminator(spawnedIdentity, {
      observeProcessIdentity: this.processIdentityObserver
    });
    this.clearOwnedState(spawnedIdentity);
    throw new Error(`Tunnel đã khởi động nhưng cổng ${settings.healthPort} không qua kiểm tra sẵn sàng. Vui lòng xem nhật ký Tunnel.`);
  }

  async stop() {
    const state = readJson(this.paths.stateFile(), {});
    const identity = await this.ownedIdentity(state);
    if (!identity) {
      this.clearOwnedState(storedProcessReceipt(state));
      return false;
    }
    return this.terminateOwnedIdentity(identity);
  }

  async status(settings, options = {}) {
    const state = readJson(this.paths.stateFile(), {});
    let identity;
    try { identity = await this.ownedIdentity(state); } catch { return false; }
    if (!identity) return false;
    if (this.device && classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId) !== 'owned') return false;
    if (state.tunnelFingerprint !== tunnelFingerprint(settings, this.device?.deviceId || '', options.activationEpochId || '')) return false;
    const expectedEpoch = String(options.activationEpochId || '').trim();
    if (expectedEpoch && String(state.tunnelActivationEpochId || '').trim() !== expectedEpoch) return false;
    // A persisted fingerprint/epoch is not proof that the current listener is
    // our tunnel: another process may have claimed the same health port.  Bind
    // the health endpoint to the exact PID recorded at launch.
    const listenerPid = await (this.listenerPidProbe || loopbackListenerPid)(settings.healthPort);
    if (listenerPid !== Number(state.tunnelPid)) return false;
    if (!(await canConnect('127.0.0.1', settings.healthPort, 400))) return false;
    const healthy = await this.probeControlPlaneHealth(settings, Number(state.tunnelPid));
    if (!healthy) return false;
    try {
      const latest = await this.ownedIdentity(readJson(this.paths.stateFile(), {}));
      return Boolean(latest && sameProcessIdentity(identity, latest));
    } catch {
      return false;
    }
  }

  async ownedIdentity(state) {
    // Require the OS start token before applying device ownership.  A live
    // legacy receipt without a token must fail with the typed identity error.
    const identity = await requireExactStoredProcessIdentity({
      pid: state.tunnelPid,
      processStartToken: state.tunnelProcessStartToken
    }, {
      processIdentityObserver: this.processIdentityObserver,
      kind: 'TUNNEL'
    });
    this.assertOwnedLive(state);
    return identity;
  }

  async terminateOwnedIdentity(identity) {
    if (!identity) return false;
    const state = readJson(this.paths.stateFile(), {});
    if (!sameStoredProcessReceipt(state, identity)) {
      throw Object.assign(new Error('Coding Tunnel process state changed before exact termination.'), {
        code: 'TUNNEL_PROCESS_STATE_CHANGED'
      });
    }
    await this.exactProcessTerminator(identity, {
      observeProcessIdentity: this.processIdentityObserver
    });
    this.clearOwnedState(identity);
    return true;
  }

  clearOwnedState(expectedReceipt = null) {
    updateJsonAtomic(this.paths.stateFile(), (value) => {
      if (expectedReceipt && !sameStoredProcessReceipt(value, expectedReceipt)) {
        throw Object.assign(new Error('Coding Tunnel process state changed before exact cleanup.'), {
          code: 'TUNNEL_PROCESS_STATE_CHANGED'
        });
      }
      return {
        ...value,
        tunnelPid: null,
        tunnelProcessStartToken: null,
        tunnelId: '',
        tunnelFingerprint: '',
        tunnelInstanceId: null,
        tunnelActivationEpochId: null,
        tunnelDeviceId: '',
        tunnelDeviceInstanceId: ''
      };
    });
  }
}

module.exports = { TunnelService, tunnelFingerprint, parseLoopbackListenerPid, loopbackListenerPid };
