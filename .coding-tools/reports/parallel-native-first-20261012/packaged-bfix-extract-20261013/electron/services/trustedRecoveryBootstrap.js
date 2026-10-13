'use strict';

/**
 * The mixed-version Recovery Host handoff has a deliberately narrow source
 * authority.  Unlike the historical full-clean command, this module never
 * accepts a checkpoint from an operator or from a transport payload: it
 * derives one from the canonical accepted-checkpoint ledger and binds the
 * byte-exact receipt set to the recovery_host component.
 *
 * This is intentionally a small policy layer over the existing accepted-code
 * evaluator.  The evaluator owns receipt format, Git-root verification,
 * component mapping, and on-disk SHA-256 checks; keeping those rules in one
 * place prevents the break-glass path from becoming a parallel authority.
 */

const crypto = require('node:crypto');
const {
  gitStatus,
  readAcceptedCheckpoints,
  evaluateActivationEligibility
} = require('./recoveryActionStore');

const TRUSTED_RECOVERY_BOOTSTRAP_VERSION = 1;
const TRUSTED_COMPONENT = 'recovery_host';
const HEX64 = /^[a-f0-9]{64}$/;

function trustedBootstrapError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function canonicalCheckpoint(evaluation) {
  return {
    checkpoint_id: String(evaluation?.source_checkpoint_id || ''),
    run_id: String(evaluation?.run_id || ''),
    wave_id: String(evaluation?.wave_id || ''),
    proof_fingerprint: String(evaluation?.proof_fingerprint || '').toLowerCase(),
    git_head: String(evaluation?.accepted_head || '').toLowerCase()
  };
}

function checkpointMatches(left, right) {
  const fields = ['checkpoint_id', 'run_id', 'wave_id', 'proof_fingerprint', 'git_head'];
  return Boolean(left && right && fields.every((field) => String(left[field] || '').toLowerCase() === String(right[field] || '').toLowerCase()));
}

function canonicalReceiptDigest(evaluation) {
  const checkpoint = canonicalCheckpoint(evaluation);
  const receipts = Array.isArray(evaluation?.receipts) ? evaluation.receipts : [];
  const payload = {
    version: TRUSTED_RECOVERY_BOOTSTRAP_VERSION,
    component: TRUSTED_COMPONENT,
    source_checkpoint: checkpoint,
    receipts: receipts.map((receipt) => ({
      path: String(receipt?.path || ''),
      state: String(receipt?.state || ''),
      sha256: receipt?.sha256 === null ? null : String(receipt?.sha256 || '').toLowerCase(),
      size_bytes: Number(receipt?.size_bytes || 0),
      receipt_kind: String(receipt?.receipt_kind || ''),
      run_id: String(receipt?.run_id || ''),
      wave_id: String(receipt?.wave_id || ''),
      restart_safe: receipt?.restart_safe === true,
      content_addressed: receipt?.content_addressed === true,
      expected_sha256: receipt?.expected_sha256 === undefined
        ? null : String(receipt.expected_sha256 || '').toLowerCase()
    }))
  };
  return crypto.createHash('sha256').update(JSON.stringify(payload), 'utf8').digest('hex');
}

function assertRecoveryHostEligibility(evaluation) {
  const components = Array.isArray(evaluation?.affected_components)
    ? evaluation.affected_components : [];
  if (evaluation?.eligible !== true || evaluation?.code !== 'ACTIVATABLE') {
    throw trustedBootstrapError(
      'TRUSTED_BOOTSTRAP_SOURCE_NOT_ACTIVATABLE',
      'No accepted Recovery Host checkpoint is currently activatable.',
      { eligibility_code: String(evaluation?.code || '') || null }
    );
  }
  if (components.length !== 1 || components[0] !== TRUSTED_COMPONENT) {
    throw trustedBootstrapError(
      'TRUSTED_BOOTSTRAP_COMPONENT_MISMATCH',
      'Trusted bootstrap requires an accepted checkpoint affecting only recovery_host.',
      { affected_components: components }
    );
  }
  if (!Array.isArray(evaluation?.receipts) || evaluation.receipts.length === 0) {
    throw trustedBootstrapError(
      'TRUSTED_BOOTSTRAP_RECEIPTS_MISSING',
      'Trusted bootstrap requires one or more accepted source receipts.'
    );
  }
  const checkpoint = canonicalCheckpoint(evaluation);
  if (!HEX64.test(checkpoint.proof_fingerprint)) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_SOURCE_NOT_ACTIVATABLE', 'Trusted bootstrap source proof fingerprint is invalid.');
  }
  return checkpoint;
}

function trustedAttestation(evaluation) {
  const checkpoint = assertRecoveryHostEligibility(evaluation);
  return {
    version: TRUSTED_RECOVERY_BOOTSTRAP_VERSION,
    component: TRUSTED_COMPONENT,
    source_checkpoint: checkpoint,
    receipt_sha256: canonicalReceiptDigest(evaluation)
  };
}

function normalizeTrustedAttestation(value, sourceCheckpoint = null) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_ATTESTATION_INVALID', 'Trusted bootstrap attestation is invalid.');
  }
  const allowed = ['version', 'component', 'source_checkpoint', 'receipt_sha256'];
  const keys = Object.keys(value).sort();
  if (JSON.stringify(keys) !== JSON.stringify([...allowed].sort())
    || Number(value.version) !== TRUSTED_RECOVERY_BOOTSTRAP_VERSION
    || value.component !== TRUSTED_COMPONENT
    || !HEX64.test(String(value.receipt_sha256 || '').toLowerCase())) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_ATTESTATION_INVALID', 'Trusted bootstrap attestation fields are invalid.');
  }
  const checkpoint = value.source_checkpoint;
  if (!checkpoint || typeof checkpoint !== 'object' || Array.isArray(checkpoint)
    || Object.keys(checkpoint).sort().join(',') !== 'checkpoint_id,git_head,proof_fingerprint,run_id,wave_id') {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_ATTESTATION_INVALID', 'Trusted bootstrap source checkpoint is invalid.');
  }
  if (sourceCheckpoint && !checkpointMatches(checkpoint, sourceCheckpoint)) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_ATTESTATION_MISMATCH', 'Trusted bootstrap attestation does not match its source checkpoint.');
  }
  return {
    version: TRUSTED_RECOVERY_BOOTSTRAP_VERSION,
    component: TRUSTED_COMPONENT,
    source_checkpoint: {
      checkpoint_id: String(checkpoint.checkpoint_id || ''),
      run_id: String(checkpoint.run_id || ''),
      wave_id: String(checkpoint.wave_id || ''),
      proof_fingerprint: String(checkpoint.proof_fingerprint || '').toLowerCase(),
      git_head: String(checkpoint.git_head || '').toLowerCase()
    },
    receipt_sha256: String(value.receipt_sha256 || '').toLowerCase()
  };
}

async function currentHead(workspace, gitStatusFn) {
  let status;
  try {
    status = await gitStatusFn(workspace, true);
  } catch (error) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_GIT_UNAVAILABLE', 'Trusted bootstrap could not verify the configured Git workspace.', {
      cause_code: String(error?.code || '') || null
    });
  }
  const head = String(status?.head || '').toLowerCase();
  if (!/^[a-f0-9]{40,64}$/.test(head)) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_GIT_UNAVAILABLE', 'Trusted bootstrap Git HEAD is unavailable.');
  }
  return head;
}

async function selectTrustedRecoveryHostSource(workspace, {
  readAcceptedCheckpointsFn = readAcceptedCheckpoints,
  gitStatusFn = gitStatus,
  evaluateEligibilityFn = evaluateActivationEligibility
} = {}) {
  const head = await currentHead(workspace, gitStatusFn);
  let checkpoints;
  try {
    checkpoints = readAcceptedCheckpointsFn(workspace);
  } catch (error) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_LEDGER_UNAVAILABLE', 'Trusted bootstrap could not read accepted source authority.', {
      cause_code: String(error?.code || '') || null
    });
  }
  const candidates = [];
  for (const checkpoint of (Array.isArray(checkpoints) ? checkpoints : [])) {
    if (String(checkpoint?.git_head || '').toLowerCase() !== head) continue;
    const evaluation = evaluateEligibilityFn(checkpoint, { workspace, currentHead: head });
    if (evaluation?.eligible === true
      && Array.isArray(evaluation.affected_components)
      && evaluation.affected_components.length === 1
      && evaluation.affected_components[0] === TRUSTED_COMPONENT) {
      candidates.push(evaluation);
    }
  }
  const selected = candidates.at(-1);
  if (!selected) {
    throw trustedBootstrapError(
      'TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE',
      'No byte-exact EOCL-accepted recovery_host checkpoint is available at the current Git HEAD.',
      { git_head: head }
    );
  }
  const attestation = trustedAttestation(selected);
  return {
    source_checkpoint: attestation.source_checkpoint,
    attestation,
    receipt_count: selected.receipts.length
  };
}

async function revalidateTrustedRecoveryHostSource(workspace, sourceCheckpoint, attestation, {
  readAcceptedCheckpointsFn = readAcceptedCheckpoints,
  gitStatusFn = gitStatus,
  evaluateEligibilityFn = evaluateActivationEligibility
} = {}) {
  const normalizedAttestation = normalizeTrustedAttestation(attestation, sourceCheckpoint);
  const head = await currentHead(workspace, gitStatusFn);
  if (head !== normalizedAttestation.source_checkpoint.git_head) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_SOURCE_DRIFT', 'Trusted bootstrap source Git HEAD changed before handoff.');
  }
  let checkpoints;
  try {
    checkpoints = readAcceptedCheckpointsFn(workspace);
  } catch (error) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_LEDGER_UNAVAILABLE', 'Trusted bootstrap could not re-read source authority.', {
      cause_code: String(error?.code || '') || null
    });
  }
  const checkpoint = (Array.isArray(checkpoints) ? checkpoints : []).find((item) => checkpointMatches(item, normalizedAttestation.source_checkpoint));
  if (!checkpoint) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE', 'The trusted bootstrap checkpoint is no longer accepted at the current Git HEAD.');
  }
  const evaluation = evaluateEligibilityFn(checkpoint, { workspace, currentHead: head });
  const canonical = trustedAttestation(evaluation);
  if (!checkpointMatches(canonical.source_checkpoint, normalizedAttestation.source_checkpoint)
    || canonical.receipt_sha256 !== normalizedAttestation.receipt_sha256) {
    throw trustedBootstrapError('TRUSTED_BOOTSTRAP_SOURCE_DRIFT', 'Trusted bootstrap receipt bytes changed before handoff.');
  }
  return { source_checkpoint: canonical.source_checkpoint, attestation: canonical };
}

module.exports = {
  TRUSTED_RECOVERY_BOOTSTRAP_VERSION,
  TRUSTED_COMPONENT,
  trustedBootstrapError,
  canonicalCheckpoint,
  canonicalReceiptDigest,
  checkpointMatches,
  assertRecoveryHostEligibility,
  trustedAttestation,
  normalizeTrustedAttestation,
  selectTrustedRecoveryHostSource,
  revalidateTrustedRecoveryHostSource
};
