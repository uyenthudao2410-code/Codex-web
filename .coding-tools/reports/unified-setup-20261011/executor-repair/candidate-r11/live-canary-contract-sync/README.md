# Separate r11 canary after contract sync

Local derivative; root alone executes live phases. This is a new explicit trial after the first action settled rejected before patch/proof. It uses the same approval/window/context/pilot and unchanged `NEXT_AUTHORITY_MARKER`. It does not retry the old action.

All trial intents/results use `NEXT_OPERATION_DIR/canary-after-contract-sync`. Task/patch idempotency prefixes are `r11-contract-sync-task-` and `r11-contract-sync-patch-`, further bound to fresh pins. The rejected trial's directory and receipts remain intact.

Before dispatch, root must prove:

1. Exact rejected task is closed and its writer released, with zero active VM/Job work and unchanged target preimage/checker/old pending RUN/WAVE hashes.
2. Standing policy's facade contract is synchronized within the same already-approved scope. Product source/service/package/native identities remain pinned.
3. A fresh native preflight is less than 60 seconds old; actual pins bind its receipt and current service/epoch/process/server identities. The exact approved window remains `1791735729910` to `1791739329910`, with at least 120 seconds left.
4. Initial original guard succeeds. The prior rejected internal context expires at `1791737017246`; it receives no special exemption in this trial.

Use `root-canary-ssh.py prepare` with new actual pins and native receipt, then the returned manifest for `stage`, `preflight`, exactly one `dispatch`, repeated read-only `observe`, and settled `cleanup`. The unchanged transport is reused by bytes and still pins the original common and SSH helpers.

After dispatch, `own_context_view` first invokes the existing `ids` verifier, which proves this trial's immutable intent/task/action/patch/plan/facade/history. Read-only joins then prove that action's internal context shares its request/owner/complete target/creation/600000ms lifespan and has no other action/request. Only that exact context is removed from a copy before the frozen authority guard runs. Any unrelated live context remains rejected. No in-memory common constants or guards are overridden.

Patch, checker, proof plan, public result shape, native reader/correlator, previous authority marker postcondition and pending native semantic acceptance are unchanged. Thirteen focused offline tests passed for the new path/idempotency isolation, no-replay boundary and own-context causal guards. Unchanged helper tests reuse previous proof; no broad product suites were rerun. No live dispatch or external effect occurred in this lane.
