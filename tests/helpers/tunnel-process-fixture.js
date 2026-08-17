const fs = require('node:fs');
const path = require('node:path');

const RUN_SOURCE = String.raw`const http = require('node:http');

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? String(process.argv[index + 1] || '') : '';
}

const listenAddress = argValue('--health.listen-addr');
const separator = listenAddress.lastIndexOf(':');
const host = separator >= 0 ? listenAddress.slice(0, separator) : '';
const port = Number(separator >= 0 ? listenAddress.slice(separator + 1) : 0);
if (host !== '127.0.0.1' || !Number.isInteger(port) || port <= 0) process.exit(2);

const server = http.createServer((_request, response) => {
  const body = JSON.stringify({ ok: true, pid: process.pid, control_plane_poll: true });
  response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
  response.end(body);
});
server.listen(port, host);

const shutdown = () => server.close(() => process.exit(0));
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
`;

const HEALTH_SOURCE = String.raw`const http = require('node:http');

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? String(process.argv[index + 1] || '') : '';
}
function hasFlag(name) { return process.argv.includes(name); }
function alive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try { process.kill(pid, 0); return true; } catch { return false; }
}
function fail(message) {
  if (hasFlag('--json')) process.stdout.write(JSON.stringify({ ok: false, error: message }));
  else process.stderr.write(message + '\n');
  process.exit(1);
}

const port = Number(argValue('--port'));
const expectedPid = Number(argValue('--pid'));
if (!Number.isInteger(port) || port <= 0 || !alive(expectedPid)) fail('expected tunnel PID is not alive');

const request = http.get({ host: '127.0.0.1', port, path: '/healthz', timeout: 1000 }, (response) => {
  let body = '';
  response.setEncoding('utf8');
  response.on('data', (chunk) => { if (body.length < 16384) body += chunk; });
  response.on('end', () => {
    if (response.statusCode !== 200) fail('health endpoint returned non-200');
    let payload;
    try { payload = JSON.parse(body); } catch { fail('health endpoint returned invalid JSON'); }
    if (payload.ok !== true || Number(payload.pid) !== expectedPid) fail('health PID does not match expected tunnel PID');
    if (hasFlag('--require-control-plane-poll') && payload.control_plane_poll !== true) fail('control-plane poll proof missing');
    if (hasFlag('--json')) process.stdout.write(JSON.stringify(payload));
    process.exit(0);
  });
});
request.on('timeout', () => request.destroy(new Error('health timeout')));
request.on('error', (error) => fail(error.message));
`;

function installTunnelProcessFixture(directory) {
  fs.mkdirSync(directory, { recursive: true });
  const runPath = path.join(directory, 'run');
  const healthPath = path.join(directory, 'health');
  fs.writeFileSync(runPath, RUN_SOURCE, 'utf8');
  fs.writeFileSync(healthPath, HEALTH_SOURCE, 'utf8');
  return { runPath, healthPath };
}

async function withWorkingDirectory(directory, operation) {
  const previous = process.cwd();
  process.chdir(directory);
  try { return await operation(); }
  finally { process.chdir(previous); }
}

module.exports = { installTunnelProcessFixture, withWorkingDirectory };
