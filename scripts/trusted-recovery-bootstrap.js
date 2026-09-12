#!/usr/bin/env node
'use strict';

/**
 * One-purpose mixed-version Recovery Supervisor entry point.
 *
 * There is intentionally no checkpoint, path, PID, shell command, endpoint,
 * or operation-id input here.  The command derives a single current-HEAD,
 * receipt-verified recovery_host checkpoint, then hands it to the existing
 * deferred full-clean coordinator.  The worker revalidates the same source
 * after the originating MCP call closes, and the replacement Recovery Host
 * validates it again before it creates its durable epoch.
 */

const path = require('node:path');
const { createDevelopmentPaths } = require('./dev-ui-lifecycle');
const { deferExecute, assessDeferredHandoff } = require('./full-clean-activation');
const {
  selectTrustedRecoveryHostSource,
  TRUSTED_COMPONENT
} = require('../electron/services/trustedRecoveryBootstrap');

function commandError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function parseArgs(argv = []) {
  if (!Array.isArray(argv) || argv.length === 0) return { preflight: false };
  if (argv.length === 1 && String(argv[0] || '') === '--preflight') return { preflight: true };
  throw commandError(
    'TRUSTED_BOOTSTRAP_ARGUMENT_INVALID',
    'Usage: node scripts/trusted-recovery-bootstrap.js [--preflight]'
  );
}

function configuredWorkspace(paths = null) {
  const candidate = paths && typeof paths.appRoot === 'function'
    ? paths.appRoot()
    : path.resolve(__dirname, '..');
  if (!candidate || !path.isAbsolute(candidate)) {
    throw commandError('TRUSTED_BOOTSTRAP_WORKSPACE_MISMATCH', 'Trusted Recovery Supervisor bootstrap workspace is unavailable.');
  }
  return path.resolve(candidate);
}

async function run(options = {}) {
  const parsed = parseArgs(options.argv || []);
  const workspace = configuredWorkspace(options.paths || null);
  const selectSource = options.selectTrustedRecoveryHostSourceFn || selectTrustedRecoveryHostSource;
  const selected = await selectSource(workspace, options.sourceSelectionOptions || {});
  const paths = options.paths || createDevelopmentPaths({ appRoot: workspace });
  if (path.resolve(paths.appRoot()).toLowerCase() !== workspace.toLowerCase()) {
    throw commandError('TRUSTED_BOOTSTRAP_WORKSPACE_MISMATCH', 'Trusted Recovery Supervisor bootstrap paths do not match the fixed workspace.');
  }
  const assessHandoff = options.assessDeferredHandoffFn || assessDeferredHandoff;
  const handoff = assessHandoff(paths, options.deferredHandoffOptions || {});
  if (handoff?.ready !== true) {
    throw commandError(
      String(handoff?.code || 'DEFERRED_SUPERVISOR_UNAVAILABLE'),
      'Trusted Recovery Supervisor bootstrap has no current durable post-tool-call owner.',
      { handoff }
    );
  }
  if (parsed.preflight) {
    return {
      ok: true,
      mode: 'preflight',
      component: TRUSTED_COMPONENT,
      source_checkpoint: selected.source_checkpoint,
      receipt_count: selected.receipt_count,
      deferred_handoff: handoff,
      mutable_operation_started: false
    };
  }
  const defer = options.deferExecuteFn || deferExecute;
  const deferred = await defer({
    paths,
    checkpoint: selected.source_checkpoint,
    trustedRecoveryBootstrap: selected.attestation
  });
  return {
    ...deferred,
    trusted_recovery_bootstrap: {
      component: TRUSTED_COMPONENT,
      source_checkpoint: selected.source_checkpoint,
      receipt_count: selected.receipt_count
    }
  };
}

async function main(argv = process.argv.slice(2)) {
  try {
    const result = await run({ argv });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    return result;
  } catch (error) {
    const result = {
      ok: false,
      code: String(error?.code || 'TRUSTED_BOOTSTRAP_FAILED'),
      message: String(error?.message || error)
    };
    process.stdout.write(`${JSON.stringify(result)}\n`);
    process.exitCode = 1;
    return result;
  }
}

if (require.main === module) void main();

module.exports = {
  parseArgs,
  configuredWorkspace,
  run,
  main
};
