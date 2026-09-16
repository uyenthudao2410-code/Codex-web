const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const REQUIRE_STAGED = process.argv.includes('--require-staged');
const CANONICAL_LEDGER = '.coding-tools/orchestration/ledger.sqlite3';
const DELIVERY_RECEIPT = '.coding-tools/delivery-snapshot.json';
const APPROVED_IGNORED_EVIDENCE = [
  '.coding-tools/orchestration/ledger.sqlite3-shm',
  '.coding-tools/orchestration/ledger.sqlite3-wal',
];
const APPROVED_IGNORED_EVIDENCE_SET = new Set(APPROVED_IGNORED_EVIDENCE);

function normalizedPortable(value) {
  return String(value || '').split('\\').join('/');
}

function isApprovedIgnoredEvidence(value) {
  return APPROVED_IGNORED_EVIDENCE_SET.has(normalizedPortable(value));
}

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

function verifyStagedCanonicalLedger(root) {
  const script = path.join(root, 'scripts', 'stage-coding-tools-delivery.py');
  const launcher = path.join(root, 'scripts', 'run-python.js');
  return spawnSync(process.execPath, [launcher, script, '--verify-index'], {
    cwd: root,
    encoding: 'utf8',
    windowsHide: true,
  });
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
      const ignoredFiles = nulList(ignored.stdout).filter((item) => !isApprovedIgnoredEvidence(item));
      if (ignoredFiles.length) {
        failures.push(
          'coding-tools history check: ignored evidence is forbidden:',
          ...ignoredFiles.map((item) => `  ${item}`)
        );
      }
    }
  }

  const approvedIgnoreInput = `${APPROVED_IGNORED_EVIDENCE.join('\0')}\0`;
  const approvedIgnoreCheck = runGit(root, ['check-ignore', '--no-index', '-z', '--stdin'], {
    input: approvedIgnoreInput,
  });
  if (![0, 1].includes(approvedIgnoreCheck.status)) {
    failures.push(`coding-tools history check: approved sidecar ignore check failed (exit ${approvedIgnoreCheck.status})`);
  } else {
    const ignoredApproved = new Set(nulList(approvedIgnoreCheck.stdout).map(normalizedPortable));
    const missingIgnoreRules = APPROVED_IGNORED_EVIDENCE.filter((item) => !ignoredApproved.has(item));
    if (missingIgnoreRules.length) {
      failures.push(
        'coding-tools history check: approved transient SQLite sidecars must remain ignored:',
        ...missingIgnoreRules.map((item) => `  ${item}`)
      );
    }
  }

  const trackedApproved = runGit(root, ['ls-files', '-z', '--', ...APPROVED_IGNORED_EVIDENCE]);
  if (trackedApproved.status !== 0) {
    failures.push(`coding-tools history check: unable to inspect approved sidecar tracking (exit ${trackedApproved.status})`);
  } else {
    const trackedFiles = nulList(trackedApproved.stdout);
    if (trackedFiles.length) {
      failures.push(
        'coding-tools history check: approved transient SQLite sidecars must not be tracked:',
        ...trackedFiles.map((item) => `  ${item}`)
      );
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
    const stagedReceipt = runGit(root, ['diff', '--cached', '--name-only', '-z', '--', DELIVERY_RECEIPT]);
    if (unstaged.status !== 0 || untracked.status !== 0 || stagedReceipt.status !== 0) {
      failures.push('coding-tools delivery check: unable to inspect staged state');
    } else {
      const stagedReceiptPaths = new Set(nulList(stagedReceipt.stdout).map(normalizedPortable));
      const freshDeliverySnapshotStaged = stagedReceiptPaths.has(DELIVERY_RECEIPT);
      const missingFromDelivery = [...new Set([...nulList(unstaged.stdout), ...nulList(untracked.stdout)])]
        .filter((item) => {
          const normalized = normalizedPortable(item);
          if (isApprovedIgnoredEvidence(normalized)) return false;
          if (normalized === CANONICAL_LEDGER && freshDeliverySnapshotStaged) return false;
          return true;
        })
        .sort();
      if (!freshDeliverySnapshotStaged) {
        failures.push(
          'coding-tools delivery check: a fresh staged delivery snapshot receipt is required:',
          `  ${DELIVERY_RECEIPT}`,
          'Run: npm run stage:coding-tools-delivery'
        );
      }
      if (missingFromDelivery.length) {
        failures.push(
          'coding-tools delivery check: current evidence is not fully staged:',
          ...missingFromDelivery.map((item) => `  ${item}`),
          'Run: npm run stage:coding-tools-delivery'
        );
      }
      if (freshDeliverySnapshotStaged) {
        const verified = verifyStagedCanonicalLedger(root);
        if (verified.status !== 0) {
          failures.push(
            'coding-tools delivery check: staged canonical ledger snapshot is invalid:',
            `  ${String(verified.stderr || verified.stdout || '').trim() || `verification exit ${verified.status}`}`
          );
        }
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
