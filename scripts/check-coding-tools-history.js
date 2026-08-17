const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const REQUIRE_STAGED = process.argv.includes('--require-staged');

function runGit(root, args, options = {}) {
  const result = spawnSync('git', ['-C', root, ...args], {
    encoding: 'utf8',
    windowsHide: true,
    ...options,
  });
  return result;
}

function gitRoot() {
  const result = spawnSync('git', ['rev-parse', '--show-toplevel'], {
    encoding: 'utf8',
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error('not inside a Git worktree');
  }
  return result.stdout.trim();
}

function portable(root, target) {
  return path.relative(root, target).split(path.sep).join('/');
}

function collectEvidence(root, directory) {
  const files = [];
  const nestedGit = [];

  function visit(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      if (entry.name === '.git') {
        nestedGit.push(portable(root, full));
        continue;
      }
      if (entry.isDirectory()) {
        visit(full);
      } else {
        files.push(portable(root, full));
      }
    }
  }

  visit(directory);
  return { files, nestedGit };
}

function nulList(value) {
  return String(value || '').split('\0').filter(Boolean);
}

function fail(lines) {
  for (const line of lines) console.error(line);
  process.exit(1);
}

function main() {
  const root = gitRoot();
  const evidenceRoot = path.join(root, '.coding-tools');
  if (!fs.existsSync(evidenceRoot)) {
    console.log('coding-tools history check: .coding-tools is absent');
    return;
  }

  const { files, nestedGit } = collectEvidence(root, evidenceRoot);
  const failures = [];

  if (nestedGit.length) {
    failures.push(
      'coding-tools history check: nested Git metadata is forbidden under .coding-tools:',
      ...nestedGit.map((item) => `  ${item}`),
      'Move automation worktrees/repositories outside .coding-tools so individual evidence files can be versioned.'
    );
  }

  if (files.length) {
    const input = `${files.join('\0')}\0`;
    const ignored = runGit(root, ['check-ignore', '--no-index', '-z', '--stdin'], { input });
    if (![0, 1].includes(ignored.status)) {
      failures.push(`coding-tools history check: git check-ignore failed (exit ${ignored.status})`);
    } else {
      const ignoredFiles = nulList(ignored.stdout);
      if (ignoredFiles.length) {
        failures.push(
          'coding-tools history check: ignored evidence is forbidden:',
          ...ignoredFiles.map((item) => `  ${item}`)
        );
      }
    }
  }

  const stagedEntries = runGit(root, ['ls-files', '--stage', '-z', '--', '.coding-tools']);
  if (stagedEntries.status !== 0) {
    failures.push(`coding-tools history check: git ls-files failed (exit ${stagedEntries.status})`);
  } else {
    const gitlinks = nulList(stagedEntries.stdout).filter((item) => item.startsWith('160000 '));
    if (gitlinks.length) {
      failures.push(
        'coding-tools history check: gitlinks are forbidden under .coding-tools:',
        ...gitlinks.map((item) => `  ${item}`)
      );
    }
  }

  if (REQUIRE_STAGED) {
    const unstaged = runGit(root, ['diff', '--name-only', '-z', '--', '.coding-tools']);
    const untracked = runGit(root, ['ls-files', '--others', '--exclude-standard', '-z', '--', '.coding-tools']);
    if (unstaged.status !== 0 || untracked.status !== 0) {
      failures.push('coding-tools delivery check: unable to inspect staged state');
    } else {
      const missingFromDelivery = [...new Set([...nulList(unstaged.stdout), ...nulList(untracked.stdout)])].sort();
      if (missingFromDelivery.length) {
        failures.push(
          'coding-tools delivery check: current evidence is not fully staged:',
          ...missingFromDelivery.map((item) => `  ${item}`),
          'Run: git add -A -- .coding-tools'
        );
      }
    }
  }

  if (failures.length) fail(failures);
  console.log(`coding-tools ${REQUIRE_STAGED ? 'delivery' : 'history'} check: PASS (${files.length} files)`);
}

try {
  main();
} catch (error) {
  fail([`coding-tools history check: ${error.message}`]);
}
