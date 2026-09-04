'use strict';

/**
 * Exact process identity and termination helpers.
 *
 * A PID is only a locator. Windows can recycle it while a stale descriptor or
 * activation request is still on disk, so every destructive caller must bind
 * the PID to the process creation/start token observed by the operating
 * system.  The token is deliberately represented as a decimal string: a
 * Windows FILETIME is wider than JavaScript's safe integer range.
 */

const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');

const PROCESS_START_TOKEN_PATTERN = /^[0-9]{1,32}$/;
const MAX_PROBE_OUTPUT_BYTES = 512;
const MAX_BROKER_LINE_BYTES = 1_024;
const MAX_BROKER_BUFFER_BYTES = 4_096;
const DEFAULT_PROBE_TIMEOUT_MS = 3_000;
const DEFAULT_WAIT_TIMEOUT_MS = 5_000;
const POWERSHELL_OBSERVE_SCRIPT = [
  '& { param([int]$processId)',
  '$ErrorActionPreference = "Stop"',
  'try { $process = Get-Process -Id $processId -ErrorAction Stop } catch { exit 3 }',
  '$creation = $process.StartTime.ToUniversalTime().ToFileTimeUtc()',
  'if ($creation -le 0) { exit 4 }',
  // Win32_Process.CreationDate, used by the original persisted receipt, has
  // microsecond precision. Get-Process avoids the much slower CIM/WMI path;
  // truncate its 100ns FILETIME to the same precision so existing and newly
  // captured tokens remain byte-for-byte compatible.
  '$creation = $creation - ($creation % 10)',
  '[Console]::Out.Write($creation.ToString([Globalization.CultureInfo]::InvariantCulture))',
  '}'
].join('; ');

const POWERSHELL_BROKER_SCRIPT = [
  '& {',
  '$ErrorActionPreference = "Stop"',
  'while ($true) {',
  '$line = [Console]::In.ReadLine()',
  'if ($null -eq $line) { break }',
  '$response = $null',
  'try {',
  '$request = $line | ConvertFrom-Json -ErrorAction Stop',
  '$requestId = [long]$request.id',
  '$processId = [int]$request.pid',
  'if ($requestId -le 0 -or $processId -le 0) { throw "invalid_request" }',
  'try { $process = Get-Process -Id $processId -ErrorAction Stop } catch { $response = @{ id = $requestId; pid = $processId; state = "absent" } }',
  'if ($null -eq $response) {',
  '$creation = $process.StartTime.ToUniversalTime().ToFileTimeUtc()',
  'if ($creation -le 0) { throw "invalid_creation" }',
  '$creation = $creation - ($creation % 10)',
  '$response = @{ id = $requestId; pid = $processId; state = "live"; process_start_token = $creation.ToString([Globalization.CultureInfo]::InvariantCulture) }',
  '}',
  '} catch {',
  '$response = @{ id = 0; pid = 0; state = "unavailable" }',
  '}',
  '[Console]::Out.WriteLine(($response | ConvertTo-Json -Compress))',
  '[Console]::Out.Flush()',
  '}',
  '}'
].join('; ');

let currentProcessToken = null;
let defaultWindowsIdentityBroker = null;
let defaultWindowsIdentityBrokerExitHookInstalled = false;

function windowsProbeArgs(pid) {
  return [
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy',
    'Bypass',
    '-Command',
    POWERSHELL_OBSERVE_SCRIPT,
    String(pid)
  ];
}

function identityError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function normalizePid(value) {
  const pid = Number(value);
  if (!Number.isSafeInteger(pid) || pid <= 0) return null;
  return pid;
}

function normalizeProcessStartToken(value) {
  if (typeof value === 'bigint') value = value.toString(10);
  const token = String(value ?? '').trim();
  if (!PROCESS_START_TOKEN_PATTERN.test(token)) return null;
  try {
    const canonical = BigInt(token).toString(10);
    return canonical === '0' ? null : canonical;
  } catch {
    return null;
  }
}

function processIdentityFrom(value, { allowMissing = false } = {}) {
  const source = value && typeof value === 'object' ? value : {};
  const pid = normalizePid(source.pid ?? source.owner_pid);
  const token = normalizeProcessStartToken(
    source.process_start_token
      ?? source.owner_process_start_token
      ?? source.processStartToken
      ?? source.start_token
  );
  if (!pid) throw identityError('PROCESS_IDENTITY_INVALID', 'Process identity PID is invalid.');
  if (!token && !allowMissing) {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process creation/start identity is unavailable.', { pid });
  }
  return { pid, ...(token ? { process_start_token: token } : {}) };
}

function liveIdentity(pid, token) {
  return { state: 'live', pid, process_start_token: token };
}

function absentIdentity(pid) {
  return { state: 'absent', pid, process_start_token: null };
}

function unavailableIdentity(pid, code = 'PROCESS_IDENTITY_UNVERIFIED', details = {}) {
  return { state: 'unavailable', pid, process_start_token: null, code, details };
}

function normalizeObservation(value, pid) {
  const normalizedPid = normalizePid(pid);
  if (!normalizedPid) return unavailableIdentity(null, 'PROCESS_IDENTITY_INVALID');
  if (value === null || value === undefined || value === false) return unavailableIdentity(normalizedPid);
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'bigint') {
    const token = normalizeProcessStartToken(value);
    return token ? liveIdentity(normalizedPid, token) : unavailableIdentity(normalizedPid);
  }
  if (typeof value !== 'object') return unavailableIdentity(normalizedPid);
  if (value.pid !== undefined && normalizePid(value.pid) !== normalizedPid) {
    return unavailableIdentity(normalizedPid);
  }
  const state = String(value.state || '').trim().toLowerCase();
  if (state === 'absent' || value.absent === true) return absentIdentity(normalizedPid);
  const token = normalizeProcessStartToken(
    value.process_start_token
      ?? value.owner_process_start_token
      ?? value.processStartToken
      ?? value.start_token
  );
  if (state === 'live' && token) return liveIdentity(normalizedPid, token);
  if (token && state !== 'unavailable') return liveIdentity(normalizedPid, token);
  return unavailableIdentity(normalizedPid, 'PROCESS_IDENTITY_UNVERIFIED', {
    ...(value.details || {}),
    ...(value.code && value.code !== 'PROCESS_IDENTITY_UNVERIFIED' ? { cause_code: String(value.code) } : {})
  });
}

function readLinuxProcessIdentity(pid) {
  const file = `/proc/${pid}/stat`;
  let stat;
  try { stat = fs.readFileSync(file, 'utf8'); }
  catch (error) {
    if (error?.code === 'ENOENT' || error?.code === 'ESRCH') return absentIdentity(pid);
    return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' });
  }
  // The executable name can contain spaces and ')'; parse from the final ')'
  // exactly as the kernel's stat format requires.
  const close = stat.lastIndexOf(')');
  const fields = close >= 0 ? stat.slice(close + 2).trim().split(/\s+/) : [];
  if (fields[0] === 'Z') return absentIdentity(pid);
  const token = normalizeProcessStartToken(fields[19]); // field 22 overall
  return token ? liveIdentity(pid, token) : unavailableIdentity(pid);
}

function defaultWindowsProbe(pid, options = {}) {
  const spawn = options.spawnSync || spawnSync;
  let result;
  try {
    result = spawn('powershell.exe', windowsProbeArgs(pid), {
      windowsHide: true,
      shell: false,
      encoding: 'utf8',
      timeout: Math.max(100, Number(options.timeoutMs) || DEFAULT_PROBE_TIMEOUT_MS),
      maxBuffer: MAX_PROBE_OUTPUT_BYTES,
      stdio: ['ignore', 'pipe', 'ignore']
    });
  } catch (error) {
    return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' });
  }
  if (!result || result.error || result.status === null || result.status === undefined) {
    return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: result?.error?.code || '' });
  }
  const output = Buffer.isBuffer(result.stdout) ? result.stdout.toString('utf8') : String(result.stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_PROBE_OUTPUT_BYTES) {
    return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { reason: 'probe_output_too_large' });
  }
  const tokenText = output.replace(/^\uFEFF/, '').trim();
  if (Number(result.status) === 3) return absentIdentity(pid);
  if (Number(result.status) !== 0) return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { exit_code: result.status });
  const token = normalizeProcessStartToken(tokenText);
  return token ? liveIdentity(pid, token) : unavailableIdentity(pid);
}

function createWindowsIdentityBroker({ spawnProcess = spawn } = {}) {
  let child = null;
  let outputBuffer = Buffer.alloc(0);
  let nextRequestId = 1;
  const pending = new Map();

  const setReferenced = (referenced) => {
    for (const handle of [child, child?.stdin, child?.stdout]) {
      try {
        if (referenced) handle?.ref?.();
        else handle?.unref?.();
      } catch {}
    }
  };

  const settle = (requestId, value) => {
    const entry = pending.get(requestId);
    if (!entry) return;
    pending.delete(requestId);
    if (entry.timer) clearTimeout(entry.timer);
    entry.resolve(value);
    if (pending.size === 0) setReferenced(false);
  };

  const failBroker = (reason, details = {}) => {
    const active = child;
    child = null;
    outputBuffer = Buffer.alloc(0);
    for (const [requestId, entry] of pending) {
      pending.delete(requestId);
      if (entry.timer) clearTimeout(entry.timer);
      entry.resolve(unavailableIdentity(entry.pid, 'PROCESS_IDENTITY_UNVERIFIED', { reason, ...details }));
    }
    try { active?.stdin?.end?.(); } catch {}
    try { active?.kill?.(); } catch {}
  };

  const onStdoutData = (chunk) => {
    const value = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    if (outputBuffer.length + value.length > MAX_BROKER_BUFFER_BYTES) {
      failBroker('probe_output_too_large');
      return;
    }
    outputBuffer = Buffer.concat([outputBuffer, value]);
    while (true) {
      const newline = outputBuffer.indexOf(0x0A);
      if (newline < 0) break;
      const lineBuffer = outputBuffer.subarray(0, newline);
      outputBuffer = outputBuffer.subarray(newline + 1);
      if (lineBuffer.length === 0 || lineBuffer.length > MAX_BROKER_LINE_BYTES) {
        failBroker(lineBuffer.length > MAX_BROKER_LINE_BYTES ? 'probe_output_too_large' : 'probe_protocol_invalid');
        return;
      }
      let response;
      try { response = JSON.parse(lineBuffer.toString('utf8').replace(/^\uFEFF/, '').trim()); }
      catch {
        failBroker('probe_protocol_invalid');
        return;
      }
      const requestId = Number(response?.id);
      const entry = Number.isSafeInteger(requestId) ? pending.get(requestId) : null;
      if (!entry || normalizePid(response?.pid) !== entry.pid) {
        failBroker('probe_protocol_invalid');
        return;
      }
      settle(requestId, normalizeObservation(response, entry.pid));
    }
    if (outputBuffer.length > MAX_BROKER_LINE_BYTES) failBroker('probe_output_too_large');
  };

  const ensureChild = () => {
    if (child && !child.killed && child.stdin && !child.stdin.destroyed) return { child };
    let started;
    try {
      started = spawnProcess('powershell.exe', [
        '-NoLogo',
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-Command',
        POWERSHELL_BROKER_SCRIPT
      ], {
        windowsHide: true,
        shell: false,
        cwd: path.dirname(process.execPath),
        stdio: ['pipe', 'pipe', 'ignore']
      });
    } catch (error) {
      return { error: { reason: 'broker_spawn_failed', cause_code: error?.code || '' } };
    }
    if (!started?.stdin || typeof started.stdin.write !== 'function' || !started?.stdout || typeof started.stdout.on !== 'function' || typeof started.once !== 'function') {
      try { started?.kill?.(); } catch {}
      return { error: { reason: 'broker_process_invalid' } };
    }
    child = started;
    outputBuffer = Buffer.alloc(0);
    started.stdout.on('data', onStdoutData);
    started.stdout.on('error', (error) => {
      if (child === started) failBroker('broker_stdout_error', { cause_code: error?.code || '' });
    });
    started.stdin.on?.('error', (error) => {
      if (child === started) failBroker('broker_stdin_error', { cause_code: error?.code || '' });
    });
    started.once('error', (error) => {
      if (child === started) failBroker('broker_process_error', { cause_code: error?.code || '' });
    });
    started.once('close', (code) => {
      if (child === started) failBroker('broker_process_closed', { exit_code: code ?? null });
    });
    setReferenced(false);
    return { child: started };
  };

  const observe = (pidValue, { timeoutMs = DEFAULT_PROBE_TIMEOUT_MS } = {}) => {
    const pid = normalizePid(pidValue);
    if (!pid) return Promise.resolve(unavailableIdentity(null, 'PROCESS_IDENTITY_INVALID'));
    const started = ensureChild();
    if (!started.child) {
      return Promise.resolve(unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', started.error || { reason: 'broker_spawn_failed' }));
    }
    const requestId = nextRequestId;
    nextRequestId = nextRequestId >= Number.MAX_SAFE_INTEGER ? 1 : nextRequestId + 1;
    const payload = Buffer.from(`${JSON.stringify({ id: requestId, pid })}\n`, 'utf8');
    return new Promise((resolve) => {
      const entry = { pid, resolve, timer: null };
      pending.set(requestId, entry);
      setReferenced(true);
      entry.timer = setTimeout(() => {
        if (!pending.has(requestId)) return;
        pending.delete(requestId);
        resolve(unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { reason: 'probe_timeout' }));
        failBroker('probe_timeout');
      }, Math.max(100, Number(timeoutMs) || DEFAULT_PROBE_TIMEOUT_MS));
      entry.timer.unref?.();
      try {
        started.child.stdin.write(payload, (error) => {
          if (error && pending.has(requestId)) {
            failBroker('broker_pipe_write_failed', { cause_code: error?.code || '' });
          }
        });
      } catch (error) {
        failBroker('broker_pipe_write_failed', { cause_code: error?.code || '' });
      }
    });
  };

  return {
    observe,
    close: () => failBroker('broker_closed_by_parent')
  };
}

function defaultWindowsBroker() {
  if (!defaultWindowsIdentityBroker) {
    defaultWindowsIdentityBroker = createWindowsIdentityBroker();
  }
  if (!defaultWindowsIdentityBrokerExitHookInstalled) {
    defaultWindowsIdentityBrokerExitHookInstalled = true;
    process.once('exit', () => {
      try { defaultWindowsIdentityBroker?.close?.(); } catch {}
    });
  }
  return defaultWindowsIdentityBroker;
}

async function defaultWindowsProbeAsync(pid, options = {}) {
  const timeoutMs = Math.max(100, Number(options.timeoutMs) || DEFAULT_PROBE_TIMEOUT_MS);
  if (options.broker && typeof options.broker.observe === 'function') {
    try { return normalizeObservation(await options.broker.observe(pid, { timeoutMs }), pid); }
    catch (error) { return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' }); }
  }
  if (typeof options.spawn === 'function' && options.spawn !== spawn) {
    const broker = createWindowsIdentityBroker({ spawnProcess: options.spawn });
    try { return normalizeObservation(await broker.observe(pid, { timeoutMs }), pid); }
    catch (error) { return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' }); }
    finally { broker.close(); }
  }
  try { return normalizeObservation(await defaultWindowsBroker().observe(pid, { timeoutMs }), pid); }
  catch (error) { return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' }); }
}

/**
 * Observe the OS process identity without mutating the process.
 *
 * `options.observe` is intentionally supported for deterministic focused
 * tests and for callers that already have a platform-native probe.  It must
 * return an observation object (or a token/absent marker); an unavailable or
 * malformed result is never interpreted as a live process.
 */
function observeProcessIdentity(pidValue, options = {}) {
  const pid = normalizePid(pidValue);
  if (!pid) return unavailableIdentity(null, 'PROCESS_IDENTITY_INVALID');
  if (typeof options.observe === 'function') {
    try { return normalizeObservation(options.observe(pid), pid); }
    catch (error) { return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' }); }
  }
  if (pid === process.pid && process.platform === 'win32' && currentProcessToken && !options.noCache) {
    return liveIdentity(pid, currentProcessToken);
  }
  let observed;
  if (process.platform === 'win32') observed = defaultWindowsProbe(pid, options);
  else if (process.platform === 'linux') observed = readLinuxProcessIdentity(pid);
  else observed = unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { reason: 'unsupported_platform' });
  if (pid === process.pid && observed.state === 'live' && !options.noCache) currentProcessToken = observed.process_start_token;
  return observed;
}

async function observeProcessIdentityAsync(pidValue, options = {}) {
  const pid = normalizePid(pidValue);
  if (!pid) return unavailableIdentity(null, 'PROCESS_IDENTITY_INVALID');
  if (typeof options.observe === 'function') {
    try { return normalizeObservation(await options.observe(pid), pid); }
    catch (error) { return unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { cause_code: error?.code || '' }); }
  }
  const platform = String(options.platform || process.platform);
  if (pid === process.pid && platform === 'win32' && currentProcessToken && !options.noCache) {
    return liveIdentity(pid, currentProcessToken);
  }
  let observed;
  if (platform === 'win32') observed = await defaultWindowsProbeAsync(pid, options);
  else if (platform === 'linux') observed = readLinuxProcessIdentity(pid);
  else observed = unavailableIdentity(pid, 'PROCESS_IDENTITY_UNVERIFIED', { reason: 'unsupported_platform' });
  if (pid === process.pid && observed.state === 'live' && !options.noCache) currentProcessToken = observed.process_start_token;
  return observed;
}

function sameProcessIdentity(expectedValue, observedValue) {
  let expected;
  try { expected = processIdentityFrom(expectedValue); } catch { return false; }
  const observed = normalizeObservation(observedValue, expected.pid);
  return observed.state === 'live'
    && observed.pid === expected.pid
    && observed.process_start_token === expected.process_start_token;
}

function requireLiveProcessIdentity(value, options = {}) {
  const expected = processIdentityFrom(value);
  const observer = options.observeProcessIdentity || observeProcessIdentity;
  let observed;
  try { observed = normalizeObservation(observer(expected.pid), expected.pid); }
  catch (error) {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process creation/start identity could not be observed.', { pid: expected.pid, cause_code: error?.code || '' });
  }
  if (observed.state === 'absent') {
    throw identityError('PROCESS_IDENTITY_EXITED', 'The exact target process has already exited.', { pid: expected.pid });
  }
  if (observed.state !== 'live') {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process creation/start identity could not be observed.', { pid: expected.pid });
  }
  if (!sameProcessIdentity(expected, observed)) {
    throw identityError('PROCESS_IDENTITY_CHANGED', 'The target PID now belongs to another process identity.', {
      pid: expected.pid,
      expected_process_start_token: expected.process_start_token,
      observed_process_start_token: observed.process_start_token
    });
  }
  return expected;
}

function defaultRunProcess(command, args, options) {
  // Require lazily so unit tests can inject a runner and so this low-level
  // module does not create an import cycle during Recovery Host startup.
  // eslint-disable-next-line global-require
  const { run } = require('./commandRunner');
  return run(command, args, options);
}

async function waitForExactProcessExit(identityValue, {
  observeProcessIdentity: observer = observeProcessIdentity,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  timeoutMs = DEFAULT_WAIT_TIMEOUT_MS
} = {}) {
  const identity = processIdentityFrom(identityValue);
  const deadline = Date.now() + Math.max(100, Number(timeoutMs) || DEFAULT_WAIT_TIMEOUT_MS);
  while (Date.now() < deadline) {
    let observed;
    try { observed = normalizeObservation(await observer(identity.pid), identity.pid); }
    catch (error) {
      throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity became unavailable while waiting for exit.', { pid: identity.pid, cause_code: error?.code || '' });
    }
    if (observed.state === 'absent') return { state: 'exited', identity };
    if (observed.state === 'unavailable') {
      throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity became unavailable while waiting for exit.', { pid: identity.pid });
    }
    if (!sameProcessIdentity(identity, observed)) {
      // A different creation token proves the original process is gone.  The
      // replacement must never be touched by this operation.
      return { state: 'replaced', identity, observed };
    }
    await sleep(50);
  }
  let final;
  try { final = normalizeObservation(await observer(identity.pid), identity.pid); }
  catch (error) {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity became unavailable while waiting for exit.', { pid: identity.pid, cause_code: error?.code || '' });
  }
  if (final.state === 'absent') return { state: 'exited', identity };
  if (final.state === 'live' && !sameProcessIdentity(identity, final)) return { state: 'replaced', identity, observed: final };
  if (final.state === 'unavailable') {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity became unavailable while waiting for exit.', { pid: identity.pid });
  }
  throw identityError('PROCESS_TERMINATION_TIMEOUT', 'The exact target process remained alive after the termination timeout.', { pid: identity.pid });
}

/**
 * Terminate exactly the process represented by `identity`, including its
 * Windows descendant tree.  The pre-termination observation is mandatory;
 * a recycled PID or an unavailable probe can never reach taskkill.
 */
async function terminateExactProcessTree(identityValue, {
  observeProcessIdentity: observer = observeProcessIdentity,
  runProcess = defaultRunProcess,
  processKill = process.kill,
  sleep,
  timeoutMs = DEFAULT_WAIT_TIMEOUT_MS
} = {}) {
  const identity = processIdentityFrom(identityValue);
  let observed;
  try { observed = normalizeObservation(await observer(identity.pid), identity.pid); }
  catch (error) {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity could not be verified before termination.', { pid: identity.pid, cause_code: error?.code || '' });
  }
  if (observed.state === 'absent') return { state: 'already_exited', identity };
  if (observed.state !== 'live') {
    throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity could not be verified before termination.', { pid: identity.pid });
  }
  if (!sameProcessIdentity(identity, observed)) {
    throw identityError('PROCESS_IDENTITY_CHANGED', 'Refused to terminate a recycled PID.', {
      pid: identity.pid,
      expected_process_start_token: identity.process_start_token,
      observed_process_start_token: observed.process_start_token
    });
  }

  if (process.platform === 'win32') {
    let result;
    try {
      result = await runProcess('taskkill.exe', ['/PID', String(identity.pid), '/T', '/F'], { allowFailure: true });
    } catch (error) {
      throw identityError('PROCESS_TERMINATION_FAILED', 'Exact process tree termination command failed.', {
        pid: identity.pid,
        cause_code: error?.code || ''
      });
    }
    if (Number(result?.code) !== 0) {
      // A non-zero taskkill may mean the exact target exited concurrently.  A
      // fresh identity observation decides that case; never infer success from
      // the exit code alone.
      let after;
      try { after = normalizeObservation(await observer(identity.pid), identity.pid); }
      catch (error) {
        throw identityError('PROCESS_IDENTITY_UNVERIFIED', 'Process identity could not be verified after termination failure.', { pid: identity.pid, cause_code: error?.code || '' });
      }
      if (after.state === 'absent' || (after.state === 'live' && !sameProcessIdentity(identity, after))) {
        return { state: 'already_exited', identity, observed: after };
      }
      throw identityError('PROCESS_TERMINATION_FAILED', 'Exact process tree termination command failed.', {
        pid: identity.pid,
        exit_code: result?.code ?? null
      });
    }
  } else {
    try { processKill(identity.pid, 'SIGTERM'); }
    catch (error) {
      if (error?.code !== 'ESRCH') throw identityError('PROCESS_TERMINATION_FAILED', 'Exact process termination failed.', { pid: identity.pid, cause_code: error?.code || '' });
    }
  }
  const waited = await waitForExactProcessExit(identity, {
    observeProcessIdentity: observer,
    sleep,
    timeoutMs
  });
  return { ...waited, state: 'terminated', exit_state: waited.state };
}

// Compatibility wrapper for the non-destructive launcher helper.  Callers
// performing a mutation use waitForExactProcessExit directly.
async function waitForProcessExit(value, options = {}) {
  if (value && typeof value === 'object') return waitForExactProcessExit(value, options);
  const pid = normalizePid(value);
  if (!pid) return false;
  const processAlive = options.processAlive || ((candidate) => {
    try { process.kill(Number(candidate), 0); return true; } catch { return false; }
  });
  const deadline = Date.now() + Math.max(100, Number(options.timeoutMs) || DEFAULT_WAIT_TIMEOUT_MS);
  while (Date.now() < deadline) {
    if (!processAlive(pid)) return true;
    await (options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms))))(50);
  }
  return !processAlive(pid);
}

module.exports = {
  PROCESS_START_TOKEN_PATTERN,
  POWERSHELL_OBSERVE_SCRIPT,
  POWERSHELL_BROKER_SCRIPT,
  createWindowsIdentityBroker,
  normalizePid,
  normalizeProcessStartToken,
  processIdentityFrom,
  observeProcessIdentity,
  observeProcessIdentityAsync,
  sameProcessIdentity,
  requireLiveProcessIdentity,
  terminateExactProcessTree,
  waitForExactProcessExit,
  waitForProcessExit,
  identityError
};
