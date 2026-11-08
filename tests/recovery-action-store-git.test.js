const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { gitStatus, resolveGitCommand } = require('../electron/services/recoveryActionStore');

test('git resolves by absolute path when a standard Windows install exists', () => {
  const resolved = resolveGitCommand();
  assert.equal(typeof resolved, 'string');
  assert.ok(resolved.length > 0);
  if (fs.existsSync('C:\\Program Files\\Git\\cmd\\git.exe')) {
    assert.equal(resolved, 'C:\\Program Files\\Git\\cmd\\git.exe');
  } else if (fs.existsSync('C:\\Program Files\\Git\\bin\\git.exe')) {
    assert.equal(resolved, 'C:\\Program Files\\Git\\bin\\git.exe');
  } else {
    assert.equal(resolved, 'git', 'no standard install on this machine, so the bare command is kept');
  }
});

test('a failed git probe keeps the GIT_UNAVAILABLE code and records the underlying cause', async () => {
  const bogus = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-git-')), 'missing-workspace');
  await assert.rejects(gitStatus(bogus, false), (error) => {
    assert.equal(error.code, 'AUTO_ACTIVATION_GIT_UNAVAILABLE');
    assert.equal(typeof error.details.git_command, 'string');
    assert.ok(error.details.git_command.length > 0);
    // git itself rejects a bad -C directory with exit 128; a machine without
    // git fails at spawn instead. Either way the cause must be recorded.
    assert.ok(error.details.exit_code === 128 || typeof error.details.cause_code === 'string');
    return true;
  });
});
