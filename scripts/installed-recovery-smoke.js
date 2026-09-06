const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const installer = path.join(root, 'dist', `coding-tools-mcp-setup-${packageJson.version}.exe`);
const productName = packageJson.build.productName;
const productionDescriptor = path.join(process.env.APPDATA || '', 'web-mcp-assistant', 'recovery-host.json');

function assert(value, code) {
  if (!value) throw new Error(code);
}

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { return null; }
}

function descriptorIdentity(file) {
  const value = readJson(file);
  return value ? { owner_pid: Number(value.owner_pid || 0), instance_id: String(value.instance_id || '') } : null;
}

function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function scheduledTaskFingerprint() {
  const result = spawnSync('schtasks.exe', ['/Query', '/TN', 'WebMCP Recovery Supervisor', '/XML'], {
    windowsHide: true,
    encoding: 'buffer',
  });
  if (result.status !== 0) return null;
  return sha256(result.stdout);
}

function installedProductCount(appRoot = '') {
  const script = appRoot
    ? "$root=[IO.Path]::GetFullPath($env:CODEX_INSTALLED_SMOKE_ROOT).TrimEnd('\\'); @(Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue | Where-Object { ($_.InstallLocation -and [IO.Path]::GetFullPath([string]$_.InstallLocation).TrimEnd('\\') -eq $root) -or ($_.UninstallString -and [string]$_.UninstallString -like ('*'+$root+'*')) }).Count"
    : "@(Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -in @('Coding Tools MCP','coding-tools-mcp') }).Count";
  const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], {
    windowsHide: true,
    encoding: 'utf8',
    env: { ...process.env, CODEX_INSTALLED_SMOKE_ROOT: appRoot },
  });
  assert(result.status === 0, 'INSTALLED_PRODUCT_QUERY_FAILED');
  const count = Number(String(result.stdout || '').trim());
  assert(Number.isInteger(count) && count >= 0, 'INSTALLED_PRODUCT_QUERY_INVALID');
  return count;
}

function run(file, args, options = {}) {
  return spawnSync(file, args, {
    cwd: options.cwd || root,
    env: options.env || process.env,
    windowsHide: true,
    encoding: 'utf8',
    timeout: options.timeout || 120000,
  });
}

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function waitUntil(predicate, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  do {
    if (predicate()) return true;
    sleep(100);
  } while (Date.now() < deadline);
  return predicate();
}

function safeRemoveScratch(scratchRoot) {
  const resolved = path.resolve(scratchRoot);
  const tempRoot = `${path.resolve(os.tmpdir())}${path.sep}`;
  assert(resolved.startsWith(tempRoot), 'INSTALLED_SMOKE_SCRATCH_OUTSIDE_TEMP');
  assert(path.basename(resolved).startsWith('webmcp-installed-recovery-'), 'INSTALLED_SMOKE_SCRATCH_IDENTITY_INVALID');
  let lastError = null;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      fs.rmSync(resolved, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
      return;
    } catch (error) {
      if (!['EPERM', 'EBUSY', 'ENOTEMPTY'].includes(error?.code)) throw error;
      lastError = error;
      sleep(250);
    }
  }
  throw lastError;
}

function parseSmokeResult(stdout) {
  const lines = String(stdout || '').trim().split(/\r?\n/).filter(Boolean);
  assert(lines.length > 0, 'INSTALLED_PACKAGED_SMOKE_RESULT_MISSING');
  try { return JSON.parse(lines.at(-1)); }
  catch { throw new Error('INSTALLED_PACKAGED_SMOKE_RESULT_INVALID'); }
}

function main() {
  if (process.platform !== 'win32') {
    console.log(JSON.stringify({ ok: true, skipped: true, reason: 'windows_only' }));
    return;
  }
  assert(fs.existsSync(installer), 'CURRENT_NSIS_INSTALLER_MISSING');
  assert(installedProductCount() === 0, 'INSTALLED_SMOKE_REQUIRES_NO_EXISTING_USER_INSTALL');

  const productionBefore = descriptorIdentity(productionDescriptor);
  const taskBefore = scheduledTaskFingerprint();
  const scratchRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-installed-recovery-'));
  const appRoot = path.join(scratchRoot, 'app');
  let uninstallResult = null;
  let packageResult = null;
  let installationRegistered = false;
  let installedFilesRemoved = false;

  try {
    const installResult = run(installer, ['/S', `/D=${appRoot}`]);
    assert(installResult.status === 0, `NSIS_INSTALL_FAILED:${installResult.status}`);
    const executable = path.join(appRoot, `${productName}.exe`);
    assert(fs.existsSync(executable), 'NSIS_INSTALLED_EXECUTABLE_MISSING');
    installationRegistered = installedProductCount(appRoot) === 1;
    assert(installationRegistered, 'NSIS_INSTALLATION_NOT_REGISTERED');

    const smoke = run(process.execPath, [path.join(root, 'scripts', 'packaged-recovery-smoke.js')], {
      env: { ...process.env, CODEX_PACKAGED_APP_ROOT: appRoot },
    });
    assert(smoke.status === 0, `INSTALLED_PACKAGED_SMOKE_FAILED:${String(smoke.stderr || smoke.stdout || '').slice(0, 300)}`);
    packageResult = parseSmokeResult(smoke.stdout);
    assert(packageResult.ok === true, 'INSTALLED_PACKAGED_SMOKE_NOT_OK');

    const uninstaller = fs.readdirSync(appRoot)
      .find((name) => /^Uninstall.*\.exe$/i.test(name));
    assert(uninstaller, 'NSIS_UNINSTALLER_MISSING');
    uninstallResult = run(path.join(appRoot, uninstaller), ['/S']);
    assert(uninstallResult.status === 0, `NSIS_UNINSTALL_FAILED:${uninstallResult.status}`);
    installedFilesRemoved = waitUntil(() => !fs.existsSync(executable));
    assert(installedFilesRemoved, 'NSIS_INSTALLED_EXECUTABLE_REMAINS');
    assert(waitUntil(() => installedProductCount(appRoot) === 0), 'NSIS_UNINSTALL_REGISTRATION_REMAINS');
    assert(sameJson(descriptorIdentity(productionDescriptor), productionBefore), 'PRODUCTION_RECOVERY_DESCRIPTOR_CHANGED');
    assert(scheduledTaskFingerprint() === taskBefore, 'PRODUCTION_SUPERVISOR_TASK_CHANGED');

    console.log(JSON.stringify({
      ok: true,
      installer: { version: packageJson.version, installed: true, registered: installationRegistered },
      packaged_smoke: packageResult,
      uninstall: { exit_code: uninstallResult.status, installed_files_removed: installedFilesRemoved, registration_removed: true },
      isolation: { production_descriptor_stable: true, scheduled_task_definition_stable: true },
    }));
  } finally {
    if (!uninstallResult && fs.existsSync(appRoot)) {
      const uninstaller = fs.readdirSync(appRoot).find((name) => /^Uninstall.*\.exe$/i.test(name));
      if (uninstaller) uninstallResult = run(path.join(appRoot, uninstaller), ['/S']);
    }
    if (!uninstallResult || uninstallResult.status === 0) safeRemoveScratch(scratchRoot);
  }
}

try { main(); }
catch (error) {
  console.error(error?.stack || String(error));
  process.exitCode = 1;
}
