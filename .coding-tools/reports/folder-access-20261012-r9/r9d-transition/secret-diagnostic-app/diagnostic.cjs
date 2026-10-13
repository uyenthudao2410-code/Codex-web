'use strict';
// Offline diagnostic only: never opens MCP, never emits secret values.
const fs = require('node:fs');
const path = require('node:path');
const { app, safeStorage } = require('electron');
const here = path.resolve(__dirname, '..');
const product = path.join(process.env.APPDATA, 'web-mcp-assistant');
const isolated = path.join(here, 'secret-diagnostic-profile');
const same = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();
async function main() {
  if (!same(app.commandLine.getSwitchValue('user-data-dir'), isolated) || same(isolated, product)) throw new Error();
  fs.mkdirSync(isolated, { recursive: true });
  app.setPath('userData', isolated);
  app.setPath('sessionData', path.join(isolated, 'session-data'));
  await app.whenReady();
  const { SecretStore } = require(path.join('E:\\DEV\\Codex-web', 'electron', 'services', 'secretStore'));
  const store = new SecretStore({ secretsFile: () => path.join(product, 'secrets.bin') });
  const result = store._readResult();
  const localState = path.join(product, 'Local State');
  let productHasProfileKey = false;
  try { productHasProfileKey = !!JSON.parse(fs.readFileSync(localState, 'utf8')).os_crypt?.encrypted_key; } catch { /* fixed booleans only */ }
  const code = result.unavailable ? 'ENCRYPTION_UNAVAILABLE' : !result.found ? 'SECRET_FILE_ABSENT'
    : !result.valid ? 'SECRET_DECRYPT_OR_DECODE_FAILED' : !result.value?.mcpAuthToken ? 'MCP_KEY_ABSENT' : 'EXISTING_MCP_KEY_AVAILABLE';
  process.stdout.write(JSON.stringify({ ok: true, operation: 'offline_secret_diagnostic', code,
    encryption_available: safeStorage.isEncryptionAvailable(), primary_exists: fs.existsSync(path.join(product, 'secrets.bin')),
    backup_exists: fs.existsSync(path.join(product, 'secrets.bin.bak')), product_has_profile_key: productHasProfileKey,
    secret_values_emitted: false, native_calls_performed: false, product_files_written: false }) + '\n');
}
const timeout = setTimeout(() => app.exit(2), 10000); timeout.unref();
main().then(() => app.exit(0)).catch(() => {
  process.stdout.write(JSON.stringify({ ok: false, code: 'OFFLINE_SECRET_DIAGNOSTIC_FAILED', secret_values_emitted: false, native_calls_performed: false }) + '\n');
  app.exit(1);
});
