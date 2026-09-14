const fs = require('node:fs');
const net = require('node:net');
const { performance } = require('node:perf_hooks');
const { run } = require('./commandRunner');
const defaultPaths = require('../paths');
const { resolveProxy } = require('./proxyService');

const PYTHON_DISCOVERY_TIMEOUT_MS = 5_000;

async function commandExists(name, options = {}) {
  const runner = options.runFn || run;
  const result = await runner('where.exe', [name], { allowFailure: true, ...options.runOptions });
  return result.code === 0;
}

function canConnect(host, port, timeout = 800) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    const done = (value) => { socket.destroy(); resolve(value); };
    socket.setTimeout(timeout);
    socket.once('connect', () => done(true));
    socket.once('timeout', () => done(false));
    socket.once('error', () => done(false));
  });
}

async function pythonStatus(paths = defaultPaths, options = {}) {
  const now = typeof options.monotonicNow === 'function' ? options.monotonicNow : () => performance.now();
  const startedAt = now();
  const explicitDeadline = Number(options.deadlineMs);
  const requestedBudget = Number(options.budgetMs);
  const deadlineMs = Number.isFinite(explicitDeadline) && explicitDeadline > 0
    ? explicitDeadline
    : (Number.isFinite(requestedBudget) && requestedBudget > 0 ? startedAt + requestedBudget : 0);
  const budgetMs = deadlineMs > 0 ? Math.max(0, deadlineMs - startedAt) : 0;
  const bounded = deadlineMs > 0;
  const runner = options.runFn || run;
  const remainingMs = () => bounded ? Math.max(0, deadlineMs - now()) : 0;
  const discoveryTimeout = (error = null) => ({
    installed: false,
    command: '',
    launchCommand: '',
    prefixArgs: [],
    version: '',
    code: 'PYTHON_DISCOVERY_TIMEOUT',
    timedOut: true,
    cleanupConfirmed: error?.cleanupConfirmed !== false,
    elapsedMs: Math.max(0, Math.round(now() - startedAt)),
    budgetMs: Math.max(0, Math.round(budgetMs))
  });
  const runProbe = async (command, args = []) => {
    if (!bounded) return runner(command, args, { allowFailure: true });
    const remaining = remainingMs();
    if (remaining <= 0) {
      throw Object.assign(new Error('Python discovery exceeded its bounded deadline.'), {
        code: 'PYTHON_DISCOVERY_TIMEOUT', timedOut: true, cleanupConfirmed: true
      });
    }
    try {
      return await runner(command, args, {
        allowFailure: true,
        timeoutMs: Math.max(1, Math.ceil(remaining)),
        timeoutCleanupMs: Math.max(1, Math.min(1_000, Math.ceil(remaining)))
      });
    } catch (error) {
      if (error?.timedOut === true
        || ['COMMAND_TIMEOUT', 'COMMAND_TIMEOUT_CLEANUP_UNCERTAIN'].includes(String(error?.code || ''))) {
        error.code = 'PYTHON_DISCOVERY_TIMEOUT';
      }
      throw error;
    }
  };
  const exists = async (name) => (await runProbe('where.exe', [name])).code === 0;
  const candidates = [];
  try {
    if (fs.existsSync(paths.portablePython())) {
      const pythonw = pathForPythonw(paths.portablePython());
      candidates.push({ command: paths.portablePython(), launchCommand: fs.existsSync(pythonw) ? pythonw : paths.portablePython(), args: [] });
    }
    if (await exists('py.exe')) candidates.push({ command: 'py.exe', launchCommand: await exists('pyw.exe') ? 'pyw.exe' : 'py.exe', args: ['-3'] });
    if (await exists('python.exe')) candidates.push({ command: 'python.exe', launchCommand: await exists('pythonw.exe') ? 'pythonw.exe' : 'python.exe', args: [] });
    for (const candidate of candidates) {
      const result = await runProbe(candidate.command, [...candidate.args, '--version']);
      const output = `${result.stdout} ${result.stderr}`.trim();
      const match = output.match(/Python\s+(\d+)\.(\d+)\.(\d+)/i);
      const major = match ? Number(match[1]) : 0;
      const minor = match ? Number(match[2]) : 0;
      if (result.code === 0 && match && (major > 3 || (major === 3 && minor >= 11))) {
        return { installed: true, command: candidate.command, launchCommand: candidate.launchCommand, prefixArgs: candidate.args, version: match[0] };
      }
    }
  } catch (error) {
    if (String(error?.code || '') === 'PYTHON_DISCOVERY_TIMEOUT') return discoveryTimeout(error);
    throw error;
  }
  return { installed: false, command: '', launchCommand: '', prefixArgs: [], version: '' };
}

function pathForPythonw(pythonPath) {
  return require('node:path').join(require('node:path').dirname(pythonPath), 'pythonw.exe');
}

class EnvironmentService {
  constructor(paths = defaultPaths) {
    this.paths = paths;
  }

  async inspect(settings, options = {}) {
    const [python, proxy, mcpListening, tunnelListening] = await Promise.all([
      pythonStatus(this.paths),
      resolveProxy(settings, { force: options.forceProxy === true }).catch(() => ({ mode: settings.proxyMode, resolvedUrl: '', source: 'error', reachable: false })),
      canConnect('127.0.0.1', settings.mcpPort),
      canConnect('127.0.0.1', settings.healthPort)
    ]);
    return {
      platform: process.platform,
      python,
      proxy: {
        mode: proxy.mode,
        configured: Boolean(proxy.resolvedUrl),
        reachable: proxy.reachable,
        url: proxy.resolvedUrl,
        source: proxy.source
      },
      tunnelClient: { installed: fs.existsSync(this.paths.tunnelExecutable()), path: this.paths.tunnelExecutable() },
      workspace: { configured: Boolean(settings.workspace), exists: Boolean(settings.workspace && fs.existsSync(settings.workspace)) },
      ports: { mcpListening, tunnelListening },
      nativePortableReady: fs.existsSync(this.paths.portablePython())
    };
  }

}

module.exports = { EnvironmentService, commandExists, canConnect, pythonStatus, PYTHON_DISCOVERY_TIMEOUT_MS };
