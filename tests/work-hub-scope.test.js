'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const mainSource = fs.readFileSync(path.join(__dirname, '..', 'electron/main.js'), 'utf8');
const preloadSource = fs.readFileSync(path.join(__dirname, '..', 'electron/preload.js'), 'utf8');
// P3: the scope fragment in main.js calls the real pathHasPrefix (canonical
// prefix, same definition as gitWorktreeRemove) and the real
// canonicalPathKey; both are pure node functions, so the fixture uses the
// real implementations instead of re-stubbing them.
const { canonicalPathKey } = require('../electron/services/pathSemantics');
const { pathHasPrefix } = require('../electron/services/workHubFiles');
function fragment(source, start, end) {
  const from = source.indexOf(start), to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing source boundary: ${start}`);
  return source.slice(from, to);
}
function fixture({ platform = 'win32', workspace = 'E:\\Project', runDetail = () => ({ available: true, found: false, waves: [] }) } = {}) {
  const handlers = new Map(), calls = [];
  let activeWorkspace = workspace;
  const pathApi = platform === 'win32' ? path.win32 : path.posix;
  const workHubFiles = { pathHasPrefix };
  for (const method of ['listDir', 'readTextFile', 'searchText', 'writeTextFile', 'copyIntoWorkspace', 'gitStatus', 'gitFileDiff', 'gitLog', 'gitShow', 'gitBlame', 'readImageData']) {
    workHubFiles[method] = (...args) => { calls.push({ method, args }); return { method, root: args[0] }; };
  }
  // Faithful to the real resolveInsideRoot: inside paths resolve, outside
  // paths (including '..' escapes) throw instead of resolving.
  workHubFiles.resolveInsideRoot = (root, rel) => {
    calls.push({ method: 'resolveInsideRoot', args: [root, rel] });
    const target = pathApi.resolve(root, rel || '');
    const relative = pathApi.relative(root, target);
    if (relative === '..' || relative.startsWith(`..${pathApi.sep}`) || pathApi.isAbsolute(relative)) throw new Error('Đường dẫn nằm ngoài thư mục làm việc.');
    return { target };
  };
  const workHubCoordination = { runDetail: (root, runId) => { calls.push({ method: 'runDetail', args: [root, runId] }); return runDetail(root, runId); } };
  vm.runInNewContext(fragment(mainSource, '  const workHubRoot =', "  secureHandle('workhub:check-url'"), {
    path: pathApi, process: { platform }, workHubFiles, workHubCoordination, canonicalPathKey,
    settings: { load: () => ({ workspace: activeWorkspace }) },
    secureHandle: (channel, handler) => { handlers.set(channel, handler); },
    invokeSafely: async (action) => { try { return { ok: true, data: await action() }; } catch (error) { return { ok: false, error: error.message }; } },
    shell: {
      openPath: async (target) => { calls.push({ method: 'openPath', args: [target] }); return ''; },
      showItemInFolder: (target) => { calls.push({ method: 'showItemInFolder', args: [target] }); },
    },
    callMcpTool: async (tool, args) => { calls.push({ method: tool, args }); return { status: 'running', command_id: 'command-1' }; },
  });
  return { calls, setWorkspace: (value) => { activeWorkspace = value; }, invoke: (channel, ...args) => handlers.get(channel)({}, ...args) };
}

const endpointCases = [
  ['workhub:list', ['src']],
  ['workhub:read', ['src/a.js']],
  ['workhub:search', ['hello']],
  ['workhub:write', ['src/a.js', 'changed', 'hash']],
  ['workhub:copy-in', ['C:\\source.txt', 'imports']],
  ['workhub:git-status', []],
  ['workhub:git-diff', ['src/a.js']],
  ['workhub:git-log', [5]],
  ['workhub:git-show', ['deadbeef']],
  ['workhub:git-blame', ['src/a.js']],
  ['workhub:read-image', ['image.png']],
  ['workhub:open-path', ['report.md', false]],
  ['workhub:open-path', ['report.md', true]],
];

test('Requests from the previous project are rejected before any file, Git or open side effect', async () => {
  const f = fixture();
  const expected = 'E:\\Project';
  f.setWorkspace('E:\\AnotherProject');
  for (const [channel, args] of endpointCases) {
    const result = await f.invoke(channel, ...args, expected);
    assert.equal(result.ok, false, channel);
    assert.match(result.error, /Dự án đã thay đổi/, channel);
  }
  const job = await f.invoke('workhub:job-run', { command: 'npm test', cwd: expected, expectedWorkspace: expected });
  assert.equal(job.ok, false);
  assert.equal(f.calls.length, 0, 'scope guard runs before reaching any service or MCP call');
});

test('Exact normalized Windows project is accepted for every scoped endpoint', async () => {
  const f = fixture();
  for (const [channel, args] of endpointCases) {
    const result = await f.invoke(channel, ...args, 'e:/project/src/..');
    assert.equal(result.ok, true, `${channel}: ${result.error || ''}`);
  }
  const serviceCalls = f.calls.filter((call) => call.method !== 'openPath' && call.method !== 'showItemInFolder');
  assert.ok(serviceCalls.length >= endpointCases.length);
  for (const call of serviceCalls) assert.equal(call.args[0], 'E:\\Project');
});

test('Job dispatch validates the expected project and preserves the visible cwd', async () => {
  const f = fixture();
  const first = await f.invoke('workhub:job-run', { command: 'npm test', expectedWorkspace: 'E:\\Project' });
  assert.equal(first.ok, true);
  const firstExec = f.calls.find((call) => call.method === 'exec_command');
  assert.equal(firstExec.args.cwd, 'E:\\Project');
  await f.invoke('workhub:job-run', { command: 'npm test', cwd: 'E:\\Project\\submodule', expectedWorkspace: 'E:\\Project' });
  const secondExec = f.calls.filter((call) => call.method === 'exec_command').at(-1);
  assert.equal(secondExec.args.cwd, 'E:\\Project\\submodule');
});

test('Existing callsites can omit the optional scope while explicit empty scope is rejected', async () => {
  const f = fixture();
  for (const [channel, args] of endpointCases) assert.equal((await f.invoke(channel, ...args)).ok, true, channel);
  const previousCalls = f.calls.length;
  assert.equal((await f.invoke('workhub:write', 'a.js', 'text', null, '')).ok, false);
  assert.equal(f.calls.length, previousCalls);
  f.setWorkspace('');
  assert.equal((await f.invoke('workhub:read', 'a.js')).ok, false);
  assert.equal(f.calls.length, previousCalls);
});

test('Scope comparison respects case-sensitive paths on non-Windows hosts', async () => {
  const f = fixture({ platform: 'linux', workspace: '/projects/Example' });
  assert.equal((await f.invoke('workhub:read', 'a.js', '/projects/example')).ok, false);
  assert.equal(f.calls.length, 0);
  assert.equal((await f.invoke('workhub:read', 'a.js', '/projects/Example/./')).ok, true);
});

test('Preload forwards the final expectedWorkspace argument without changing existing argument order', async () => {
  const calls = [];
  const api = vm.runInNewContext(`({${fragment(preloadSource, '  workhubList:', '  workhubJobControl:')}})`, {
    ipcRenderer: { invoke: async (...args) => { calls.push(args); return { ok: true }; } },
  });
  const methods = ['workhubList', 'workhubRead', 'workhubSearch', 'workhubWrite', 'workhubCopyIn', 'workhubGitStatus', 'workhubGitDiff', 'workhubGitLog', 'workhubGitShow', 'workhubGitBlame', 'workhubReadImage', 'workhubOpenPath', 'workhubOpenPath'];
  const expected = 'E:\\Project';
  for (let i = 0; i < endpointCases.length; i += 1) {
    const [channel, args] = endpointCases[i];
    await api[methods[i]](...args, expected);
    assert.deepEqual(calls.at(-1), [channel, ...args, expected]);
  }
  const job = { command: 'npm test', cwd: expected, expectedWorkspace: expected };
  await api.workhubJobRun(job);
  assert.deepEqual(calls.at(-1), ['workhub:job-run', job]);
});

// ---------------- P1 (audit P1): terminal fence + RUN binding -----------

test('Job dispatch rejects a cwd outside the scoped root before any MCP call', async () => {
  const f = fixture();
  const result = await f.invoke('workhub:job-run', { command: 'npm test', cwd: 'E:\\Other\\sub', expectedWorkspace: 'E:\\Project' });
  assert.equal(result.ok, false);
  assert.match(result.error, /nằm ngoài thư mục làm việc/);
  assert.equal(f.calls.filter((call) => call.method === 'exec_command').length, 0);
});

test('Job dispatch binds the panel RUN and its current wave to exec_command', async () => {
  const f = fixture({ runDetail: () => ({ available: true, found: true, waves: [{ waveId: 'wave-1', ordinal: 1 }, { waveId: 'wave-2', ordinal: 2 }] }) });
  const result = await f.invoke('workhub:job-run', { command: 'npm test', cwd: 'E:\\Project', expectedWorkspace: 'E:\\Project', runId: 'run-9' });
  assert.equal(result.ok, true);
  const exec = f.calls.find((call) => call.method === 'exec_command');
  assert.equal(exec.args.run_id, 'run-9');
  assert.equal(exec.args.wave_id, 'wave-2', 'the last ordinal wave is the current wave');
  // Field-wise asserts: the binding object crosses the vm realm boundary,
  // so deepStrictEqual rejects it on prototype identity alone.
  assert.equal(result.data.workhubRunBinding.runId, 'run-9');
  assert.equal(result.data.workhubRunBinding.waveId, 'wave-2');
});

test('Job dispatch refuses an unknown RUN and runs unbound when the RUN has no wave yet', async () => {
  const unknown = fixture({ runDetail: () => ({ available: true, found: false }) });
  const refused = await unknown.invoke('workhub:job-run', { command: 'npm test', expectedWorkspace: 'E:\\Project', runId: 'run-ghost' });
  assert.equal(refused.ok, false);
  assert.match(refused.error, /không tồn tại trong ledger/);
  assert.equal(unknown.calls.filter((call) => call.method === 'exec_command').length, 0);

  const waveless = fixture({ runDetail: () => ({ available: true, found: true, waves: [] }) });
  const result = await waveless.invoke('workhub:job-run', { command: 'npm test', expectedWorkspace: 'E:\\Project', runId: 'run-new' });
  assert.equal(result.ok, true);
  const exec = waveless.calls.find((call) => call.method === 'exec_command');
  assert.equal(exec.args.run_id, undefined);
  assert.equal(result.data.workhubRunBinding, null);
});

// P3: a managed worktree of the active project is a valid scope, so the
// handlers work in the worktree without a global project switch (L9). The
// fixture uses posix paths: the real pathHasPrefix/canonicalPathKey resolve
// through the host path module, so on this Linux host only posix spellings
// exercise the prefix branch; the Windows shape of the same branch is
// covered by the Windows dev-suite run of this file.
test('Managed worktree scope is accepted and routes handlers to the worktree root', async () => {
  const f = fixture({ platform: 'linux', workspace: '/projects/Example' });
  const worktree = '/projects/Example.worktrees/feat';
  for (const [channel, args] of endpointCases) {
    const result = await f.invoke(channel, ...args, worktree);
    assert.equal(result.ok, true, `${channel}: ${result.error || ''}`);
  }
  for (const call of f.calls.filter((c) => ['listDir', 'readTextFile', 'searchText', 'writeTextFile', 'copyIntoWorkspace', 'gitStatus', 'gitFileDiff', 'gitLog', 'gitShow', 'gitBlame', 'readImageData'].includes(c.method))) {
    assert.equal(call.args[0], worktree);
  }
  const openCall = f.calls.find((c) => c.method === 'resolveInsideRoot');
  assert.equal(openCall.args[0], worktree);
});

test('Worktree scope outside the managed base is rejected before any side effect', async () => {
  const f = fixture({ platform: 'linux', workspace: '/projects/Example' });
  const rejected = [
    '/projects/Example.worktrees', // the base itself is not a worktree
    '/projects/Example.worktrees-evil/feat', // separator boundary, not a prefix
    '/projects/Other.worktrees/feat', // another project's worktrees
    '/projects/Other', // outside the project entirely
    '/projects/Example.worktrees/../Other', // resolves outside the base
  ];
  for (const scope of rejected) {
    const before = f.calls.length;
    const result = await f.invoke('workhub:read', 'a.js', scope);
    assert.equal(result.ok, false, scope);
    assert.match(result.error, /Dự án đã thay đổi/, scope);
    assert.equal(f.calls.length, before, scope);
  }
});

test('Worktree scope with dot segments and a trailing slash still routes to the worktree', async () => {
  const f = fixture({ platform: 'linux', workspace: '/projects/Example' });
  const result = await f.invoke('workhub:read', 'a.js', '/projects/Example.worktrees/./feat/');
  assert.equal(result.ok, true, result.error || '');
  const call = f.calls.find((c) => c.method === 'readTextFile');
  assert.equal(call.args[0], '/projects/Example.worktrees/feat');
});

test('Job dispatch in a worktree scope fences cwd to the worktree', async () => {
  const f = fixture({ platform: 'linux', workspace: '/projects/Example' });
  const worktree = '/projects/Example.worktrees/feat';
  const first = await f.invoke('workhub:job-run', { command: 'npm test', expectedWorkspace: worktree });
  assert.equal(first.ok, true, first.error || '');
  assert.equal(f.calls.find((c) => c.method === 'exec_command').args.cwd, worktree);
  const inside = await f.invoke('workhub:job-run', { command: 'npm test', cwd: `${worktree}/sub`, expectedWorkspace: worktree });
  assert.equal(inside.ok, true, inside.error || '');
  assert.equal(f.calls.filter((c) => c.method === 'exec_command').at(-1).args.cwd, `${worktree}/sub`);
  const execBefore = f.calls.filter((c) => c.method === 'exec_command').length;
  const outside = await f.invoke('workhub:job-run', { command: 'npm test', cwd: '/projects/Example', expectedWorkspace: worktree });
  assert.equal(outside.ok, false);
  assert.equal(f.calls.filter((c) => c.method === 'exec_command').length, execBefore);
});
