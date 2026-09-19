const { spawnSync } = require('node:child_process');

function resolvePythonExecutable({
  environment = process.env,
  platform = process.platform,
  probe = spawnSync
} = {}) {
  const configured = typeof environment.PYTHON === 'string' && environment.PYTHON.trim()
    ? [environment.PYTHON.trim()]
    : platform === 'win32'
      ? ['python', 'py']
      : ['python3', 'python'];

  for (const executable of configured) {
    const result = probe(executable, ['--version'], {
      encoding: 'utf8',
      windowsHide: true
    });
    if (result?.error?.code === 'ENOENT') continue;
    if (result?.error) {
      throw new Error(`Unable to start configured Python interpreter: ${result.error.code || 'unknown error'}`);
    }
    if (result?.signal || result?.status !== 0) {
      throw new Error(`Python interpreter probe failed: ${executable}`);
    }
    return executable;
  }

  throw new Error('Python 3 interpreter is unavailable');
}

module.exports = { resolvePythonExecutable };
