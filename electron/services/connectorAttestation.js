const crypto = require('node:crypto');

const CONNECTOR_ATTESTATION_HEADER = 'X-Coding-Tools-Connector-Attestation';
const CONNECTOR_ATTESTATION_ENV = 'CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET';
const CONNECTOR_ATTESTATION_VERSION = 'v1';
const FIELD_PATTERN = /^[A-Za-z0-9._:-]{1,160}$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const NONCE_PATTERN = /^[0-9a-f]{16,128}$/;

function text(value) {
  return String(value || '').trim();
}

function canonical({ clientId, clientType, activationEpochId, processInstanceId, serverInstanceId, contractSha256, issuedAtUnixMs, nonce }) {
  return [
    CONNECTOR_ATTESTATION_VERSION,
    clientId,
    clientType,
    activationEpochId,
    processInstanceId,
    serverInstanceId,
    contractSha256,
    String(issuedAtUnixMs),
    nonce
  ].join('|');
}

// tunnel-client injects the returned value as a static header for one exact
// managed-Tunnel/MCP lifecycle. issuedAtUnixMs and nonce bind issuance and aid
// audit; they do not claim that the transport can re-sign every request.
function connectorAttestationHeader({
  secret,
  clientId = 'chatweb',
  clientType = 'chatweb',
  activationEpochId = '',
  processInstanceId,
  serverInstanceId,
  contractSha256,
  issuedAtUnixMs = Date.now(),
  nonce = crypto.randomBytes(16).toString('hex')
} = {}) {
  const key = text(secret);
  const values = {
    clientId: text(clientId),
    clientType: text(clientType).toLowerCase().replace(/-/g, '_'),
    activationEpochId: text(activationEpochId),
    processInstanceId: text(processInstanceId),
    serverInstanceId: text(serverInstanceId),
    contractSha256: text(contractSha256).toLowerCase(),
    issuedAtUnixMs: Number(issuedAtUnixMs),
    nonce: text(nonce)
  };
  if (!key) throw new Error('connector attestation secret is required');
  if (!FIELD_PATTERN.test(values.clientId) || !FIELD_PATTERN.test(values.clientType)) throw new Error('invalid connector attestation identity');
  for (const field of ['activationEpochId', 'processInstanceId', 'serverInstanceId']) {
    if (values[field] && !FIELD_PATTERN.test(values[field])) throw new Error(`invalid connector attestation ${field}`);
  }
  if (!SHA256_PATTERN.test(values.contractSha256)) throw new Error('invalid connector attestation contract sha256');
  if (!Number.isSafeInteger(values.issuedAtUnixMs) || values.issuedAtUnixMs <= 0) throw new Error('invalid connector attestation timestamp');
  if (!NONCE_PATTERN.test(values.nonce)) throw new Error('invalid connector attestation nonce');
  const body = canonical(values);
  const signature = crypto.createHmac('sha256', key).update(body, 'utf8').digest('hex');
  return `${body}|${signature}`;
}

module.exports = {
  CONNECTOR_ATTESTATION_HEADER,
  CONNECTOR_ATTESTATION_ENV,
  connectorAttestationHeader
};
