const test = require('node:test');
const assert = require('node:assert/strict');

const { findSensitiveContentIssues } = require('../scripts/check-sensitive-tracked');

test('flags a raw HTTP dump containing multiple credential-bearing headers without reporting their values', () => {
  const content = Buffer.from([
    'GET /internal HTTP/1.1',
    `Authorization: Bearer ${'a'.repeat(32)}`,
    `Set-Cookie: session=${'b'.repeat(32)}; HttpOnly`,
    '',
  ].join('\r\n'));

  assert.deepEqual(findSensitiveContentIssues(content), ['raw_http_credential_dump']);
});

test('does not flag a single short or placeholder authorization header', () => {
  assert.deepEqual(
    findSensitiveContentIssues(Buffer.from('Authorization: Bearer example-token\n')),
    [],
  );
});

test('flags a serialized HTTP capture with authorization, cookie, and API-key header families', () => {
  const content = Buffer.from(JSON.stringify({
    protocol: Array(4).fill('HTTP/1.1'),
    headers: ['Authorization', 'Set-Cookie', 'X-API-Key'],
  }));

  assert.deepEqual(findSensitiveContentIssues(content), ['raw_http_credential_dump']);
});

test('does not scan binary tracked files as HTTP transcripts', () => {
  assert.deepEqual(
    findSensitiveContentIssues(Buffer.from([0, 1, 2, 3, 4, 5, 6, 7])),
    [],
  );
});
