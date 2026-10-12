# Additive r10 transition v2: expired authority preparation

This packet preserves `activate-r10.cjs`, `r9-identity-pin.json`, the original README, every prior receipt and the failed 19:34 preflight. It changes only the repository-local operational helper. Product source, public API, packaged bytes and pending semantic acceptance remain unchanged.

## Observed reason for the new preparation

At 19:36:54 +07, a fresh read-only observation proved the durable old epoch `activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7` remained `READY` with durable admission `OPEN`, operation `full-clean-mv3qdvfq-a83d4dacc8a5de0588fb6ba5`, and ready-commit digest `f85415b88bd6b9b1442a40fbb308d69d6aa4d7e0a8c9ee690a86ef5a5f22fe3e`. The independent raw epoch IPC returned the same READY/open result with `update_incomplete=false`.

The decorated runtime reported `localReady=true`, `componentsReady=true`, `centralConnected=false`, `authorityReady=false`, and `CENTRAL_ROUTE_EVIDENCE_STALE`. Its projected epoch admission was closed with `RUNTIME_READINESS_INCOMPLETE`. The local metadata policy retained the exact target but its old deadline had passed. Host, UI and native component revisions were current and byte-matching; there was no pending revision, bootstrap operation, ready-adoption block or runtime recovery operation. The bounded r9 agent had ended; its pinned PID was absent.

This is a read-model authority gap. The new helper does not reopen admission, modify the durable epoch, forge readiness or start a replacement r9 agent. In r9 the agent derives its heartbeat epoch only when aggregate readiness is ready; restarting that agent would emit `unreported` while this gap remained. The server's additive v3 owner driver uses fresh independent local preparation proof for close/renew instead.

## Exact guard

`activate-r10-v2.cjs` still checks all frozen source/package hashes and the exact old Host/UI/native identities, immutable old helper/pin hashes, existing standing policy hashes/exec allowlist, canonical quiescent census, unchanged pending run/wave records, and two independent zero VM/backend observations.

Only preparation accepts either fully current readiness or the demonstrated authority gap. The gap requires durable and raw epoch READY/open with the exact operation/digest, current exact three component revisions, adopted ready state, no bootstrap/recovery, local executor ready, exact metadata target, and the precise stale-route or expired-policy reason. Other `updateIncomplete` causes refuse. Retirement boundaries still recheck fresh identities, no active work and zero VM/backend immediately before each stop. No Windows VM/HCS termination exists.

## Root execution sequence

The user has approved the grouped r10/Store/60-minute operation in `authorization.json`; the root has performed the frozen Store deployment and service restart, leaving intake in recovery. Local runtime remains r9. Only the root executes further mutations.

1. Produce a fresh read-only proof immediately before each server close/renew call:

   ```powershell
   $r10TransitionV2 = '.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/activation/activate-r10-v2.cjs'
   node $r10TransitionV2 server-preparation-proof
   ```

   This writes immutable `server-preparation-proof-TIMESTAMP.json` with `kind=r9_local_authority_preparation_v1`. Feed its exact bytes and SHA256 to the pinned server v3 owner driver using `--local-preparation-stdin --expected-local-preparation-sha256`. Each server call requires proof less than 60 seconds old. Close and renewal may use different fresh proofs; preserve both. The server marker retains the original renewal deadline and does not reanchor it.

2. Save the exact fresh Store preflight, intake-closed and authority-renewal outputs under the original local names. Each mutation receipt carries `local_preparation_sha256` so the transition can verify the independently observed predecessor. Mutation receipts retain the same exact source/service/state/target/duration fields as the original packet.

3. Use the original four explicit hash CLI arguments plus the two actual local proof filenames:

   ```powershell
   node $r10TransitionV2 preflight
   node $r10TransitionV2 activate @r10MutationArguments --closure-local-proof-file=server-preparation-proof-CLOSE_TIMESTAMP.json --renewal-local-proof-file=server-preparation-proof-RENEW_TIMESTAMP.json
   ```

   `@r10MutationArguments` contains `--operator-approved` and exact `--authorization-sha256`, `--server-preflight-sha256`, `--closure-sha256` and `--renewal-sha256` as in the original README. Replace the example filenames with the immutable files actually consumed by the server. The old absent agent needs no retirement or restart. The helper does not create an authority grant itself.

4. Use v2 `policy`, `refresh` if needed, and `agent` with the same arguments and proof filenames. The policy step uses the existing assignment sync route, preserving standing policies and doing no standalone Sandbox probe. The new r10 connected trial keeps the existing 200-iteration, 15-second bounded agent limit.

5. Observe a fresh distinct r10 epoch, then use the server v3 owner driver to reopen the scoped pilot against fresh r10 heartbeat and enabled policy. Run v2 `proof` afterward. No old command/test action is replayed and pending run acceptance is left untouched.

If the anchored 60-minute renewal expires, obtain new explicit approval for another window. Refreshing stale preflight or closure observations is allowed only within the still-valid approved window. Do not edit evidence timestamps or deadlines.

## Current proof and limits

The preliminary read-only v2 preparation at 19:39:02 proved the exact authority gap, unchanged pending acceptance and zero active work; independent host and daemon observations were both zero. That receipt predates final helper freeze and must not be used for server mutation. Root must generate new proof from the final frozen v2 helper immediately before close and renewal.

The strongest proof here is source/package parity plus fresh local preparation observations. It is not a new runtime activation, live r10 execution, or task acceptance. All original failure evidence remains immutable.
