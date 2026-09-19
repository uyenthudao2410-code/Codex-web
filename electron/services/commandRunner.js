const { spawn } = require('node:child_process');

const DEFAULT_TIMEOUT_CLEANUP_MS = 5_000;

function run(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const {
      timeoutMs = 0,
      timeoutCleanupMs = DEFAULT_TIMEOUT_CLEANUP_MS,
      onOutput,
      allowFailure,
      ...spawnOptions
    } = options;
    const child = spawn(command, args, {
      windowsHide: true,
      shell: false,
      ...spawnOptions
    });
    let stdout = '';
    let stderr = '';
    let settled = false;
    let timedOut = false;
    let timeout;
    let cleanupTimeout;
    const clearTimers = () => {
      if (timeout) clearTimeout(timeout);
      if (cleanupTimeout) clearTimeout(cleanupTimeout);
    };
    const rejectOnce = (error) => {
      if (settled) return;
      settled = true;
      clearTimers();
      reject(error);
    };
    const resolveOnce = (result) => {
      if (settled) return;
      settled = true;
      clearTimers();
      resolve(result);
    };
    child.stdout?.on('data', (chunk) => {
      const text = chunk.toString();
      stdout += text;
      onOutput?.('stdout', text);
    });
    child.stderr?.on('data', (chunk) => {
      const text = chunk.toString();
      stderr += text;
      onOutput?.('stderr', text);
    });
    if (timeoutMs > 0) {
      timeout = setTimeout(() => {
        if (settled) return;
        timedOut = true;
        const cleanupBudgetMs = Math.max(1, Number(timeoutCleanupMs) || DEFAULT_TIMEOUT_CLEANUP_MS);
        let cleanupSettled = false;
        const onTerminated = () => finishCleanup(true);
        const onCleanupError = (error) => finishCleanup(false, error);
        const finishCleanup = (confirmed, cause = null) => {
          if (cleanupSettled || settled) return;
          cleanupSettled = true;
          if (cleanupTimeout) clearTimeout(cleanupTimeout);
          child.removeListener('exit', onTerminated);
          child.removeListener('close', onTerminated);
          child.removeListener('error', onCleanupError);
          if (confirmed) {
            rejectOnce(Object.assign(new Error(`命令执行超时（${timeoutMs} ms）`), {
              code: 'COMMAND_TIMEOUT',
              stdout,
              stderr,
              timedOut: true,
              timeoutMs,
              cleanupConfirmed: true,
              cleanupOutcome: 'confirmed'
            }));
            return;
          }
          rejectOnce(Object.assign(new Error('Command timeout cleanup could not confirm child termination.'), {
            code: 'COMMAND_TIMEOUT_CLEANUP_UNCERTAIN',
            timedOut: true,
            timeoutMs,
            cleanupConfirmed: false,
            cleanupOutcome: 'unconfirmed',
            cleanupBudgetMs,
            causeCode: String(cause?.code || '') || null
          }));
        };
        child.once('exit', onTerminated);
        child.once('close', onTerminated);
        child.once('error', onCleanupError);
        cleanupTimeout = setTimeout(() => finishCleanup(false), cleanupBudgetMs);
        // Keep this deadline referenced until the command reaches a terminal
        // outcome. Otherwise an unconfirmed child could outlive the caller
        // without producing the typed uncertainty result below.
        try {
          const signalled = child.kill();
          if (!signalled && (child.exitCode !== null || child.signalCode !== null)) queueMicrotask(onTerminated);
        } catch (error) {
          finishCleanup(false, error);
        }
      }, timeoutMs);
      // A caller awaiting a bounded command needs this deadline to remain
      // live even when a mocked, detached, or already-lost child exposes no
      // other event-loop handle. The command must settle as success, failure,
      // or typed timeout rather than silently disappearing.
    }
    child.on('error', (error) => {
      if (timedOut) return;
      rejectOnce(error);
    });
    child.on('close', (code) => {
      if (timedOut) return;
      const result = { code: code ?? -1, stdout, stderr };
      if (code === 0 || allowFailure) resolveOnce(result);
      else rejectOnce(Object.assign(new Error(stderr.trim() || stdout.trim() || `${command} 执行失败（${code}）`), result));
    });
  });
}

module.exports = { run, DEFAULT_TIMEOUT_CLEANUP_MS };
