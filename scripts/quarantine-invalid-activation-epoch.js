#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');

function commandError(code, message) {
  return Object.assign(new Error(message), { code });
}

function parseArgs(argv = []) {
  let confirm = false;
  let expectedPrimarySha256 = '';
  let reason = 'operator-confirmed-invalid-activation-epoch';
  for (const raw of argv) {
    const value = String(raw || '');
    if (value === '--confirm') {
      confirm = true;
      continue;
    }
    if (value.startsWith('--expected-primary-sha256=')) {
      expectedPrimarySha256 = value.slice('--expected-primary-sha256='.length).trim().toLowerCase();
      continue;
    }
    if (value.startsWith('--reason=')) {
      reason = value.slice('--reason='.length).trim();
      continue;
    }
    throw commandError(
      'ACTIVATION_EPOCH_QUARANTINE_ARGUMENT_INVALID',
      'Usage: node scripts/quarantine-invalid-activation-epoch.js --confirm [--expected-primary-sha256=<sha256>] [--reason=<text>]'
    );
  }
  if (!confirm) {
    throw commandError(
      'ACTIVATION_EPOCH_QUARANTINE_CONFIRM_REQUIRED',
      'Refusing activation-epoch quarantine without --confirm.'
    );
  }
  return { confirm, expectedPrimarySha256, reason };
}

function dataRoot() {
  const appData = String(process.env.APPDATA || '').trim();
  if (!appData || !path.isAbsolute(appData)) {
    throw commandError('APPDATA_UNAVAILABLE', 'APPDATA is required to target the current Windows profile.');
  }
  return path.join(path.resolve(appData), 'web-mcp-assistant');
}

async function main(argv = process.argv.slice(2)) {
  try {
    const args = parseArgs(argv);
    const root = dataRoot();
    const file = path.join(root, 'activation-epoch.json');
    const store = new ActivationEpochStore({ file });
    const result = store.quarantineInvalidSnapshot(args);
    const output = {
      ok: true,
      data_root: root,
      activation_epoch_file: file,
      ...result
    };
    process.stdout.write(`${JSON.stringify(output)}\n`);
    return output;
  } catch (error) {
    const output = {
      ok: false,
      code: String(error?.code || 'ACTIVATION_EPOCH_QUARANTINE_FAILED'),
      message: String(error?.message || error)
    };
    process.stdout.write(`${JSON.stringify(output)}\n`);
    process.exitCode = 1;
    return output;
  }
}

if (require.main === module) void main();

module.exports = { parseArgs, dataRoot, main };
