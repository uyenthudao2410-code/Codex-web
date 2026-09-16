'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  parseRuntimeInvocation,
  packagedRuntime
} = require('../control_plane/recovery_runtime_adapter.cjs');

test('adapter accepts the explicit development invocation and rejects an injected packaged root', () => {
  assert.deepEqual(parseRuntimeInvocation(['--runtime-mode', 'development', '--project-root', path.resolve('project')]), {
    runtimeMode: 'development',
    appRoot: path.resolve('project')
  });
  assert.throws(
    () => parseRuntimeInvocation(['--runtime-mode', 'packaged', '--project-root', path.resolve('other-install')]),
    { code: 'RUNTIME_ADAPTER_PACKAGED_ROOT_FORBIDDEN' }
  );
});

test('packaged adapter derives its paths from the installed resource layout, not a workspace', (t) => {
  const installRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-installed-adapter-'));
  t.after(() => fs.rmSync(installRoot, { recursive: true, force: true }));
  const runtimeResources = path.join(installRoot, 'resources', 'resources');
  const adapterDirectory = path.join(runtimeResources, 'control-plane');
  const appRoot = path.join(installRoot, 'resources', 'app.asar');
  const appData = path.join(installRoot, 'appdata');
  const executablePath = path.join(installRoot, 'Coding Tools MCP.exe');
  fs.mkdirSync(adapterDirectory, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  fs.mkdirSync(appData, { recursive: true });
  fs.writeFileSync(executablePath, 'fixture');
  let received = null;
  const paths = { runtimeIdentity: () => ({ mode: 'packaged', installation_id: 'a'.repeat(64) }) };
  const runtime = packagedRuntime({
    adapterDirectory,
    dependencies: {
      appData,
      executablePath,
      createRuntimePaths: (options) => { received = options; return paths; },
      RecoveryIpcClient: class RecoveryIpcClient {},
      loadRecoveryDescriptor: () => ({}),
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: () => ({})
    }
  });
  assert.equal(runtime.mode, 'packaged');
  assert.equal(runtime.paths, paths);
  assert.deepEqual(received, {
    dataRoot: path.join(appData, 'web-mcp-assistant'),
    resourcesRoot: runtimeResources,
    appRoot,
    runtimeMode: 'packaged',
    executablePath
  });
});
