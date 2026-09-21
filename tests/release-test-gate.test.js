const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

test('Windows installer build executes the complete Node and MCP test gate', () => {
  const packagePath = path.join(__dirname, '..', 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

  assert.match(packageJson.scripts.dist, /(?:^|&&\s*)npm run test:all(?:\s*&&|$)/);
  assert.doesNotMatch(packageJson.scripts.dist, /(?:^|&&\s*)npm test(?:\s*&&|$)/);
  assert.match(packageJson.scripts['test:all'], /npm test/);
  assert.match(packageJson.scripts['test:all'], /npm run test:mcp/);
  assert.match(packageJson.scripts['test:mcp'], /node \.\.\/\.\.\/scripts\/run-python\.js --module pytest tests/);
});

test('Python module runner selects the host interpreter without changing module failures', () => {
  const runner = path.join(__dirname, '..', 'scripts', 'run-python.js');
  const result = spawnSync(process.execPath, [runner, '--module', 'compileall', '--help'], {
    encoding: 'utf8',
    env: process.env,
  });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 0, result.stderr || result.stdout);
});
