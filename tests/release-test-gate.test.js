const assert = require('node:assert/strict');
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
});
