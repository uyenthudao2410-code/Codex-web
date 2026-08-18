const { spawnSync } = require('node:child_process');

const FORBIDDEN_TRACKED_PATHS = ['ACC', 'docs/ac'];

function runGit(args) {
  return spawnSync('git', args, {
    encoding: 'utf8',
    windowsHide: true,
  });
}

function nulList(value) {
  return String(value || '').split('\0').filter(Boolean);
}

function fail(lines) {
  for (const line of lines) console.error(line);
  process.exit(1);
}

function main() {
  const root = runGit(['rev-parse', '--show-toplevel']);
  if (root.status !== 0) fail(['repository secret check: not inside a Git worktree']);

  const tracked = runGit([
    '-C',
    root.stdout.trim(),
    'ls-files',
    '-z',
    '--',
    ...FORBIDDEN_TRACKED_PATHS,
  ]);
  if (tracked.status !== 0) {
    fail([`repository secret check: git ls-files failed (exit ${tracked.status})`]);
  }

  const forbidden = nulList(tracked.stdout);
  if (forbidden.length) {
    fail([
      'repository secret check: credential/local-account paths must never be tracked:',
      ...forbidden.map((item) => `  ${item}`),
      'Remove these paths from the Git index and rotate/revoke any credential that was previously committed.',
    ]);
  }

  console.log('repository secret check: PASS');
}

main();
