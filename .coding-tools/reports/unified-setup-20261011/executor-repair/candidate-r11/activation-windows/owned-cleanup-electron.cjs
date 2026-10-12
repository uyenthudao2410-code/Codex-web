'use strict';
// Root launches the ordinary Electron binary with this isolated entrypoint.
// No BrowserWindow, profile mutex, native runtime, node agent or VM is started.
// SecretStore decrypts the requested MCP credential in memory; nothing emits it.
const path = require('node:path');
const { app } = require('electron');
// Electron normally redirects fs operations through ASAR. Validation hashes
// the complete archive bytes; disable that redirection only in this isolated
// helper process before loading the validation module.
process.noAsar = true;
const transition = require('./transition-r11.cjs');
const repo = path.resolve(__dirname, '../../../../../..');
// Windows safeStorage reads its key through Chromium's session Local State.
// The root launcher must select the authorized profile before crypto startup.
// No requestSingleInstanceLock call is made by this credential-only helper.
const profile = transition.pathsFor('r10').dataRoot();
const selected = app.commandLine.getSwitchValue('user-data-dir');
if (!selected || path.resolve(selected).toLowerCase() !== path.resolve(profile).toLowerCase()) {
  transition.reportError(Object.assign(new Error(), { code: 'EXPLICIT_AUTHORIZED_CRYPTO_PROFILE_REQUIRED' }));
  app.exit(1);
}
app.setPath('userData', profile);
app.setPath('sessionData', profile);
app.whenReady().then(async () => {
  const { SecretStore } = require(path.join(repo, 'electron/services/secretStore'));
  const store = new SecretStore(transition.pathsFor('r10'));
  const observation = store._readResult();
  transition.secretStoreObservation({
    found: observation.found === true, valid: observation.valid === true,
    unavailable: observation.unavailable === true, recovered: observation.recovered === true,
    mcpAuthToken: Boolean(observation.valid && observation.value?.mcpAuthToken),
    user_data_matches: path.resolve(app.getPath('userData')).toLowerCase() === path.resolve(profile).toLowerCase(),
    session_data_matches: path.resolve(app.getPath('sessionData')).toLowerCase() === path.resolve(profile).toLowerCase(),
    cli_profile_matches: true
  });
  if (!observation.valid || !observation.value?.mcpAuthToken) throw Object.assign(new Error(), { code: 'NATIVE_AUTH_TOKEN_NOT_AVAILABLE_IN_CRYPTO_PROFILE' });
  await transition.ownedCleanup(store);
  app.exit(0);
}).catch(error => { transition.reportError(error); app.exit(1); });
