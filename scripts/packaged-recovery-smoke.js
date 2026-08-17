const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const { assertExactPackagedResources } = require('./verify-packaged-resources');

const root = path.resolve(__dirname, '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const unpackedRoot = path.join(root, 'dist', 'win-unpacked');
const executable = path.join(unpackedRoot, `${packageJson.build.productName}.exe`);
const packagedResources = path.join(unpackedRoot, 'resources', 'resources');
const supervisorScript = path.join(packagedResources, 'recovery-supervisor', 'recovery-supervisor.ps1');
const sourceSupervisorScript = path.join(root, 'resources', 'recovery-supervisor', 'recovery-supervisor.ps1');
const productionDescriptor = path.join(process.env.APPDATA || '', 'web-mcp-assistant', 'recovery-host.json');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
function readJson(file) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; } }
function writeJson(file, value) { fs.writeFileSync(file, JSON.stringify(value), 'utf8'); }
function sha256File(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function isAlive(pid) { try { const value = Number(pid); if (!Number.isInteger(value) || value <= 0) return false; process.kill(value, 0); return true; } catch { return false; } }
function assert(value, code) { if (!value) throw new Error(code); }
function descriptorIdentity(value) { return value ? { owner_pid: Number(value.owner_pid || 0), instance_id: String(value.instance_id || '') } : null; }
function sameDescriptorIdentity(a, b) {
  if (!a && !b) return true;
  if (!a || !b) return false;
  return a.owner_pid === b.owner_pid && a.instance_id === b.instance_id;
}
function killTree(pid) {
  if (!isAlive(pid)) return;
  spawnSync('taskkill.exe', ['/PID', String(pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
}
function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close((error) => error ? reject(error) : resolve(port));
    });
  });
}
async function waitJson(file, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const value = readJson(file);
    if (value) return value;
    await wait(100);
  }
  return null;
}
async function pingRecoveryHost(descriptor) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ action: 'recovery.ping', args: [] });
    const request = http.request({
      host: '127.0.0.1', port: Number(descriptor.port), path: '/v1/call', method: 'POST', timeout: 1500,
      headers: { Authorization: `Bearer ${descriptor.token}`, 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    }, (response) => {
      let payload = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (payload.length < 65536) payload += chunk; });
      response.on('end', () => { try { resolve(JSON.parse(payload)); } catch (error) { reject(error); } });
    });
    request.on('timeout', () => request.destroy(new Error('PACKAGED_RECOVERY_PING_TIMEOUT')));
    request.on('error', reject);
    request.end(body);
  });
}
function runSupervisor(manifestPath, statusPath) {
  const result = spawnSync('powershell.exe', [
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', supervisorScript,
    '-Action', 'Once', '-ManifestPath', manifestPath, '-StatusPath', statusPath
  ], { cwd: unpackedRoot, windowsHide: true, encoding: 'utf8' });
  assert(result.status === 0, `PACKAGED_SUPERVISOR_COMMAND_FAILED:${String(result.stdout || result.stderr || '').slice(0, 300)}`);
  return JSON.parse(String(result.stdout || '').trim());
}
function packagedManifest(dataRoot) {
  return {
    schema_version: 1,
    mode: 'packaged',
    executable,
    executable_sha256: sha256File(executable),
    app_root: unpackedRoot,
    arguments: ['--recovery-host'],
    data_root: dataRoot,
    installed_script_sha256: sha256File(supervisorScript),
    installed_at: new Date().toISOString()
  };
}
function priorSupervisorState(extra = {}) {
  return {
    version: 1, supervisor_pid: 1, supervisor_started_at: new Date().toISOString(), state: 'degraded',
    last_check_at: null, last_healthy_at: null, last_host_pid: null, last_host_instance_id: null,
    consecutive_failures: 0, restart_attempts: [], next_attempt_after: null, suppressed_until: null,
    last_error_code: null, last_error_message: null, last_spawned_pid: null,
    manifest_sha256: '0'.repeat(64), task_name: 'WebMCP Recovery Supervisor', ...extra
  };
}

async function main() {
  if (process.platform !== 'win32') {
    console.log(JSON.stringify({ ok: true, skipped: true, reason: 'windows_only' }));
    return;
  }
  const required = [
    executable,
    path.join(unpackedRoot, 'resources', 'app.asar'),
    supervisorScript,
    path.join(packagedResources, 'recovery-mcp', 'recovery_mcp.py'),
    path.join(packagedResources, 'native-python', 'python.exe'),
    path.join(packagedResources, 'tools', 'tunnel-client.exe'),
    path.join(packagedResources, 'coding-tools-mcp', 'coding_tools_mcp', 'server.py')
  ];
  for (const file of required) assert(fs.existsSync(file), `PACKAGED_RESOURCE_MISSING:${path.basename(file)}`);
  assertExactPackagedResources(path.join(root, 'resources'), packagedResources);
  assert(sha256File(supervisorScript) === sha256File(sourceSupervisorScript), 'PACKAGED_RECOVERY_SUPERVISOR_SOURCE_MISMATCH');

  const productionBefore = descriptorIdentity(readJson(productionDescriptor));
  const dataRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-packaged-recovery-'));
  const recoveryMcpPort = await freePort();
  const recoveryHealthPort = await freePort();
  writeJson(path.join(dataRoot, 'settings.json'), {
    recoveryMcpPort, recoveryHealthPort, recoveryTunnelId: '', autoStartServices: false
  });

  let child = null;
  let descriptor = null;
  try {
    child = spawn(executable, ['--recovery-host', `--user-data-dir=${dataRoot}`], {
      cwd: unpackedRoot, windowsHide: true, stdio: 'ignore',
      env: { ...process.env, WEBCODEX_PROCESS_ROLE: 'recovery-host' }
    });
    descriptor = await waitJson(path.join(dataRoot, 'recovery-host.json'), 12000);
    assert(descriptor, `PACKAGED_USER_DATA_ISOLATION_FAILED:child_alive=${isAlive(child.pid)}`);

    const ping = await pingRecoveryHost(descriptor);
    assert(ping?.ok === true && ping?.data?.ready === true, 'PACKAGED_RECOVERY_HOST_NOT_READY');
    assert(Number(ping.data.pid) === Number(descriptor.owner_pid), 'PACKAGED_RECOVERY_HOST_IDENTITY_MISMATCH');
    assert(Boolean(ping.data.device_id), 'PACKAGED_DEVICE_IDENTITY_MISSING');
    assert(ping.data.recovery_plane_mode === 'independent_mcp_tunnel_v1', 'PACKAGED_RECOVERY_MODE_MISMATCH');

    let plane = null;
    const planeDeadline = Date.now() + 12000;
    while (Date.now() < planeDeadline) {
      plane = readJson(path.join(dataRoot, 'recovery-plane-state.json'));
      if (isAlive(Number(plane?.recoveryMcpPid || 0))) break;
      await wait(150);
    }
    const recoveryMcpPid = Number(plane?.recoveryMcpPid || 0);
    assert(isAlive(recoveryMcpPid), 'PACKAGED_RECOVERY_MCP_NOT_ALIVE');

    const manifestPath = path.join(dataRoot, 'packaged-manifest.json');
    const statusPath = path.join(dataRoot, 'supervisor-status.json');
    writeJson(manifestPath, packagedManifest(dataRoot));
    const healthy = runSupervisor(manifestPath, statusPath);
    assert(healthy.state === 'healthy' && Number(healthy.last_host_pid) === Number(descriptor.owner_pid), 'PACKAGED_SUPERVISOR_HEALTH_NOT_PROVEN');

    const liveOwnerRoot = path.join(dataRoot, 'fault-live-owner');
    fs.mkdirSync(liveOwnerRoot);
    writeJson(path.join(liveOwnerRoot, 'recovery-host.lock'), { version: 1, pid: process.pid, instance_id: 'packaged-live-owner' });
    const liveOwnerManifest = path.join(liveOwnerRoot, 'manifest.json');
    const liveOwnerStatus = path.join(liveOwnerRoot, 'status.json');
    writeJson(liveOwnerManifest, packagedManifest(liveOwnerRoot));
    const liveOwner = runSupervisor(liveOwnerManifest, liveOwnerStatus);
    assert(liveOwner.state === 'blocked_live_owner' && liveOwner.last_error_code === 'LIVE_OWNER_UNRESPONSIVE' && liveOwner.last_spawned_pid === null, 'PACKAGED_SUPERVISOR_LIVE_OWNER_NOT_FAIL_CLOSED');

    const hashRoot = path.join(dataRoot, 'fault-hash');
    fs.mkdirSync(hashRoot);
    const badManifestPath = path.join(hashRoot, 'manifest.json');
    const badStatusPath = path.join(hashRoot, 'status.json');
    writeJson(badManifestPath, { ...packagedManifest(hashRoot), executable_sha256: '0'.repeat(64) });
    writeJson(badStatusPath, priorSupervisorState({ consecutive_failures: 3 }));
    const hashMismatch = runSupervisor(badManifestPath, badStatusPath);
    assert(hashMismatch.state === 'spawn_failed' && hashMismatch.last_error_code === 'SPAWN_FAILED' && hashMismatch.last_spawned_pid === null, 'PACKAGED_SUPERVISOR_HASH_MISMATCH_NOT_FAIL_CLOSED');

    const productionAfter = descriptorIdentity(readJson(productionDescriptor));
    assert(sameDescriptorIdentity(productionBefore, productionAfter), 'PRODUCTION_RECOVERY_DESCRIPTOR_CHANGED');
    console.log(JSON.stringify({
      ok: true,
      package: { executable: true, app_asar: true, required_resources: required.length },
      isolation: { user_data_isolated: true, production_descriptor_stable: true },
      recovery: { host_ready: true, device_identity_present: true, mode: ping.data.recovery_plane_mode, mcp_alive: true },
      supervisor: { healthy: true, live_owner_fail_closed: true, hash_mismatch_fail_closed: true, scheduled_task_mutation: false }
    }));
  } finally {
    const plane = readJson(path.join(dataRoot, 'recovery-plane-state.json'));
    const cleanup = new Set([
      Number(plane?.recoveryTunnelPid || 0), Number(plane?.recoveryTunnelCandidatePid || 0),
      Number(plane?.recoveryMcpPid || 0), Number(descriptor?.owner_pid || child?.pid || 0)
    ]);
    for (const pid of cleanup) if (pid > 0) killTree(pid);
    await wait(300);
    for (const pid of cleanup) assert(!isAlive(pid), `PACKAGED_RECOVERY_CLEANUP_FAILED:${pid}`);
    const productionAfterCleanup = descriptorIdentity(readJson(productionDescriptor));
    assert(sameDescriptorIdentity(productionBefore, productionAfterCleanup), 'PRODUCTION_RECOVERY_DESCRIPTOR_CHANGED_DURING_CLEANUP');
    try { fs.rmSync(dataRoot, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 }); } catch {}
  }
}

main().catch((error) => {
  console.error(error?.stack || String(error));
  process.exitCode = 1;
});
