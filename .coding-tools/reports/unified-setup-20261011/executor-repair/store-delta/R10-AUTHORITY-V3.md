# R10 authority preparation from independent local proof

Prepared only. No authority/runtime/service calls were made by the preparing agent.

Primary helper: `ubuntu-r10-store-authority-v3-local-proof.py`

SHA-256: `a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec`.

Base v2 remains unchanged: `ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af`.

## Reason

The expired r9 window leaves its decorated aggregate admission closed while the actual durable and raw local epoch remains READY/OPEN. `runtime_heartbeat` only emits exact native identity when aggregate readiness is ready; otherwise it emits `activation_epoch=unreported`. Starting another old connected agent cannot satisfy the prior v2 fresh r9 epoch guard and would add unnecessary poll activity.

V3 accepts **fresh exact bytes of an independently pinned local r9 proof transmitted by the authorized owner driver** for close/renew. It does not manufacture central heartbeat/readiness, start an old agent, reopen intake early, or relax native execution admission. Existing service/source/package/grant/full action-family/quarantine protections and the actual fresh r10 reopen guard remain in place.

## Input and receipt contract

Default/observe is read-only. Close/renew require the existing flags plus:

- `--local-preparation-stdin`
- `--expected-local-preparation-sha256 <sha256 of actual immutable proof file bytes>`

Transmit the exact file bytes on stdin, maximum 131072 bytes. Use the current frozen local transition v2 producer, not the earlier schema-only fixture. The owner driver must compute the hash from the same bytes it transmits. Prefer an argv process call with binary `input=proof_path.read_bytes()`; a PowerShell text pipeline may rewrite newline/encoding and should not be used as an equivalent binary transport. Remote arguments remain the reviewed fixed helper/action/target and validated opaque hashes/identities; never interpolate arbitrary proof content into a shell command.

The server validates kind/schema, timestamp under 60 seconds, exact scope/root/profile/HEAD/package/parity, descriptor/Host/UI/native PIDs and process start tokens, absent old agent, matching durable/raw READY/OPEN epoch/operation/commit digest, unchanged pending RUN/WAVE hashes, standing policies and argv allowlist, quiescent canonical census with only the exact live runtime blocker, integrity, and fresh independent zero VM observations. It checks freshness again before owner mutation and archives the raw bytes under a protected immutable filename.

Existing receipt fields are preserved. Closure and renewal additionally emit:

```json
{
  "local_preparation_sha256": "hash of proof consumed by this action",
  "local_preparation_observed_at_ms": 0,
  "initial_local_preparation_sha256": "hash first used in this operation"
}
```

Close and renew may consume distinct freshly produced proofs; the local driver must retain both files and match each receipt to its corresponding actual bytes. The marker preserves initial and latest proof hashes. The single 60-minute deadline is still anchored at first renewal and never extended by retry. A pre-existing alternate r10 authority marker blocks a new v3 marker so changing helper variants cannot reanchor authority.

## Authorized root sequence

1. Store395 deployment has completed according to root, leaving admission recovery. Observe v3 to capture the current exact serving service/source and protected state digest.
2. Generate a fresh local preparation proof with the final local transition v2 helper. Read its bytes/hash and immediately invoke v3 close with the expected service, state, predecessor epoch, operator/execute flags and binary stdin.
3. Generate another fresh proof if needed, then invoke v3 renew with matching pins and bytes. Preserve the original returned requested/expires values and all exact receipt files.
4. Continue the reviewed r10 activation/policy synchronization. Only r10 starts its bounded agent.
5. V3 reopen still requires a different r10 epoch, real fresh node heartbeat, readiness ready, enabled and nonexpired policy, same service/state/grant and original single-window marker. There is no local-proof fallback for reopen.

## Static proof

`r10-authority-v3-guard-verification.json` records one positive schema case and 13 negative cases: changed target/package/process token/durable/raw epoch/old agent/pending hash/active Job/VM/argv allowlist, mismatched raw-byte hash, stale proof and future timestamp. All passed. The earlier proof fixture was evaluated at a synthetic fresh time only; it is not live authority evidence and must not be used for mutation. Syntax was compiled without running main or service routines. Production source and old helpers were not modified.

Final preparing-agent state: dirty `main @ 2c554f59`, only new evidence/helpers beneath this report directory; no new Job, commit, push, deployment, restart, or authority mutation by this agent. Root owns authorized execution and must preserve each operator-visible checkpoint.
