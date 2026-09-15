#!/usr/bin/env node
'use strict';

const { execFile } = require('node:child_process');

const DEFAULT_INTERVAL_MS = 60_000;

function git(args, cwd = process.cwd()) {
  return new Promise((resolve, reject) => {
    execFile('git', args, { cwd, encoding: 'utf8' }, (error, stdout, stderr) => {
      if (error) {
        error.stdout = stdout;
        error.stderr = stderr;
        reject(error);
        return;
      }
      resolve({ stdout, stderr });
    });
  });
}

async function currentBranch(cwd) {
  const result = await git(['branch', '--show-current'], cwd);
  const branch = result.stdout.trim();
  if (!branch) throw new Error('Detached HEAD is not supported by git:auto-pull.');
  return branch;
}

async function hasLocalChanges(cwd) {
  const result = await git(['status', '--porcelain'], cwd);
  return result.stdout.trim().length > 0;
}

async function isAncestor(ancestor, descendant) {
  try {
    await git(['merge-base', '--is-ancestor', ancestor, descendant]);
    return true;
  } catch (error) {
    if (error.code === 1) return false;
    throw error;
  }
}

async function checkAndPull({ cwd = process.cwd(), output = console.log } = {}) {
  const branch = await currentBranch(cwd);
  if (await hasLocalChanges(cwd)) {
    output(`AUTO_PULL paused: local changes detected on ${branch}`);
    return { status: 'paused', branch };
  }

  await git(['fetch', '--prune', 'origin'], cwd);
  const local = (await git(['rev-parse', 'HEAD'], cwd)).stdout.trim();
  const remoteRef = `origin/${branch}`;
  const remote = (await git(['rev-parse', remoteRef], cwd)).stdout.trim();

  if (local === remote) {
    output(`AUTO_PULL current: ${branch}`);
    return { status: 'current', branch, commit: local };
  }

  if (!(await isAncestor(local, remote))) {
    output(`AUTO_PULL paused: ${branch} has diverged from ${remoteRef}`);
    return { status: 'diverged', branch, local, remote };
  }

  await git(['pull', '--ff-only', 'origin', branch], cwd);
  output(`AUTO_PULL updated: ${branch} ${local.slice(0, 7)} -> ${remote.slice(0, 7)}`);
  return { status: 'updated', branch, previous: local, commit: remote };
}

function intervalFromEnvironment() {
  const value = Number(process.env.GIT_AUTO_PULL_INTERVAL_MS || DEFAULT_INTERVAL_MS);
  if (!Number.isFinite(value) || value < 5_000) {
    throw new Error('GIT_AUTO_PULL_INTERVAL_MS must be at least 5000 milliseconds.');
  }
  return value;
}

async function main() {
  const intervalMs = intervalFromEnvironment();
  const run = async () => {
    try {
      await checkAndPull();
    } catch (error) {
      console.error(`AUTO_PULL error: ${error.message}`);
    }
  };

  await run();
  const timer = setInterval(run, intervalMs);
  const stop = () => {
    clearInterval(timer);
    process.exitCode = 0;
  };
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
}

if (require.main === module) void main();

module.exports = {
  DEFAULT_INTERVAL_MS,
  checkAndPull,
  intervalFromEnvironment,
  isAncestor
};
