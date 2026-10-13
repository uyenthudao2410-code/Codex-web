'use strict';

// Select one unchanged lane policy from a bounded workspace collection. Scope
// selection never merges approvals or infers a generation from UI selection.
const MAX_COLLECTION_BYTES = 2 * 1024 * 1024;
const MAX_POLICIES = 64;
const IDENTIFIER = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;

function selectWorkspacePolicy(value, target, { code, maxPolicyBytes }) {
  const fail = () => { throw Object.assign(new Error('Exact workspace policy is unavailable.'), { code }); };
  const identity = (policy) => {
    if (!policy || typeof policy !== 'object' || Array.isArray(policy)
      || !IDENTIFIER.test(policy.workspace_id || '') || !IDENTIFIER.test(policy.workspace_generation || '')) fail();
    return JSON.stringify([policy.workspace_id, policy.workspace_generation]);
  };
  let policies = [value];
  if (value && Object.hasOwn(value, 'policies')) {
    if (Object.keys(value).sort().join(',') !== 'policies,schema_version' || value.schema_version !== 1
      || !Array.isArray(value.policies) || value.policies.length < 1 || value.policies.length > MAX_POLICIES) fail();
    policies = value.policies;
  }
  const keys = policies.map(identity);
  if (new Set(keys).size !== keys.length || policies.some((policy) => Object.hasOwn(policy, 'policies'))) fail();
  const wanted = target == null ? null : identity(target);
  const matches = wanted == null ? policies : policies.filter((_policy, index) => keys[index] === wanted);
  if (matches.length !== 1 || Buffer.byteLength(JSON.stringify(matches[0]), 'utf8') > maxPolicyBytes) fail();
  return matches[0];
}

module.exports = { MAX_COLLECTION_BYTES, selectWorkspacePolicy };
