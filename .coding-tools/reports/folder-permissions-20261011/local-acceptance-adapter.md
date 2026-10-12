# Central patch receipt and local acceptance adapter

Observed: 2026-10-11 12:37:31 Asia/Saigon. This is a source-analysis/design report on the shared working tree. It is not implementation, packaged activation, or live acceptance proof. Only this report was added by the analysis agent; runtime, server, credentials, leases, source and ledger were not changed.

## Finding

The current bridge applies one bounded exact patch through the existing local `agent_workflow` primitive and returns a verified effect receipt. The local RUN/WAVE intentionally remains `ACCEPTING` with `local_semantic_acceptance=pending`. The bridge actor is `electron-control-plane-approved-patch-bridge`, type `electron`; that is a supervisor/effect actor, not a ChatWeb semantic controller.

The bridge sends `verification=none` without commands/checks. Local proof records are created by admitted checks or test/build execution, so this path normally leaves no passed proof even though the workflow reaches `ACCEPTING`. Independently verifying the postimage for the outbound effect receipt does not currently create an exact-wave proof in the local proof ledger.

Recording acceptance in the Ubuntu owner Console writes `mcp_patch_acceptances` and a central action event. It does not enqueue an acceptance relay or call the Windows local acceptance primitive. Central status can subsequently say accepted while the local RUN/WAVE is still pending.

Evidence:

- [Bridge actor and explicit no-self-accept contract](E:/Github/Tools-Codex-web/electron/services/controlPlaneApprovedPatchBridge.js:21).
- [Action/attempt-specific local context](E:/Github/Tools-Codex-web/electron/services/runtimeOrchestrator.js:1837).
- [Workflow call, independent postimage verification and pending receipt](E:/Github/Tools-Codex-web/electron/services/runtimeOrchestrator.js:1994).
- [Check proof creation and source binding](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:906).
- [Local accept requires controller, passed proof and current source binding](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/coordination.py:1103).
- [Controller claiming limited to ChatWeb](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/server.py:1332).
- [Central owner acceptance storage](E:/Github/Tools-Codex-web/control-plane/control_plane/store.py:4598).
- [Central status overlays the owner verdict](E:/Github/Tools-Codex-web/control-plane/control_plane/mcp_facade.py:3190).

## What is actually blocked

**Another central patch action is not blocked solely by this pending wave.** Each bridge context contains action ID and delivery attempt ID. A new action therefore obtains a different context. `begin_proof()` revokes the workspace write fence before entering `PROVING`, so the prior accepting wave is not an active writer.

**Normal full-clean activation is blocked.** The canonical lifecycle census classifies the row as `AWAITING_ACCEPTANCE`. Default activation returns `ACCEPTANCE_PENDING`; the supported `allow_acceptance_pending=true` path preserves that durable decision queue while refreshing the process. It does not accept the result. Accepting rows do not age out through stale-run reconciliation.

An implementation wave in that same context also fails `FINAL_ACCEPTANCE_REQUIRED`. There is no public task-control action for appending an arbitrary proof to an accepting wave. A source-file attestation in `task_control(action=accept)` verifies current bytes but cannot replace a passed proof or a semantic controller.

Evidence:

- [Fence release before proof](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py:842).
- [Same-context implementation gate](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py:358).
- [Canonical accepting classification](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/lifecycle_census.py:678).
- [Activation requires explicit preservation](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py:257).
- [Full-clean census gate](E:/Github/Tools-Codex-web/electron/services/fullCleanActivation.js:744).
- [Accepting rows excluded from stale retirement](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py:5021).

## Smallest legitimate completion adapter

Add a narrow **owner-verdict relay for already applied exact patches**. Successful effect execution must still return pending. Only a separately recorded owner decision can complete semantic acceptance. Do not change generic controller claiming, impersonate ChatWeb, grant a controller lease to the Electron bridge, or turn every successful patch into accepted work.

### 1. Read the authentic central decision

Add a Node-authenticated internal HTTP endpoint, for example `POST /v1/nodes/{device_id}/patch-acceptance-observations`, with a bounded set of action IDs already present in the node's completed approved-patch journal. Reuse node authentication and the existing central acceptance row; this is a read of prior authority, not a new action or MCP tool.

The server resolves all correlations from its action/intent/completed receipt, rather than trusting caller-selected RUN/WAVE identifiers. Return only an owner decision bound to:

- owner, device, endpoint, workspace ID/generation, binding and central task;
- action and completed attempt;
- local handle, local RUN/WAVE, and the exact completed receipt digest;
- file path, postimage SHA-256 and byte count;
- facade contract and effect runtime identity;
- `decision`, `decided_by`, `decided_at_ms`, and a canonical decision-envelope digest.

Unknown/reconcile-required effects, another device, a missing completed receipt or conflicting acceptance must fail closed. The observed receipt must come from the configured server via the existing authenticated HTTPS node transport. A caller-supplied string such as `accepted_by=owner_console` is not sufficient provenance.

### 2. Admit it through the existing Recovery boundary

The connected agent reuses the approved-patch journal and transports the authenticated observation to a new internal Recovery IPC method, for example `runtime.control_plane_patch_acceptance`. This method is limited to an existing completed local patch and contains no patch text, shell command, new root, or authority expansion.

Recovery verifies the installed policy and exact registered generation, local journal correlation, central receipt/decision digest, and current strict runtime identity. It uses the existing MCP credential and connector attestation internally. The bridge keeps its Electron supervisor identity.

Use a narrow internal MCP HTTP handler for this operation, not a ninth public tool and not a generic acceptance bypass in `task_control`. The handler admits only the attested approved-patch bridge and an immutable central-patch origin/correlation recorded when the RUN was created. Add that origin metadata at creation if it is not already sufficient. Legacy rows without a proven origin remain pending; do not infer authority from timestamps or manually retrofit ledger data.

### 3. Produce actual exact-wave proof, then checkpoint the owner verdict

For an accepted owner verdict, independently re-read the bounded direct regular file, reject reparse/path drift, and compare current SHA-256/length with the completed effect and central verdict. Record a deterministic `exact_patch_postimage` proof through the existing `ProofLedger` runner, bound to the original exact RUN/WAVE, current HEAD/contract and the affected-path fingerprint. The runner must perform the read/comparison; accepting a passed flag from the node is insufficient.

This proof establishes that the exact requested bytes are still present. The authentic owner decision establishes semantic satisfaction. Preserve those two facts separately in the accepted checkpoint metadata, with `acceptance_authority=central_owner` and the decision-envelope/receipt digests. Do not claim ChatWeb/controller acceptance or general test/build success.

Finish through `checkpoint_with_receipt()` and its existing atomic terminal transaction. Reuse the file-receipt and proof-source validation used by ordinary acceptance. An internal owner-admission method may share the mechanical checkpoint checks, but must leave ordinary `task_control(action=accept)` controller requirements intact.

For a rejected owner verdict, retain the file and record the rejection. Do not revert bytes automatically. Keep correction explicit using the existing rejection/replan semantics; a separately authorized correction can be a new central action.

Retries key off action, attempt and decision digest. A duplicate returns the existing local checkpoint/decision result. A timeout or interrupted prepared finalization remains unknown/reconcile-required until observation establishes the outcome; it must never reapply the patch. A conflicting verdict or a changed postimage leaves the original wave pending with a typed failure.

Existing atomic completion primitive: [checkpoint_with_receipt](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py:963), [atomic event/run/wave/checkpoint transaction](E:/Github/Tools-Codex-web/resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py:2676).

## Minimum implementation surface

| Area | Required change |
| --- | --- |
| Central `store.py` / `http_api.py` | Device-bound read of authentic owner verdict plus completed receipt correlation; no new authority grant or public MCP tool. |
| Node `node_agent.py` / packaged Recovery adapter | Observe pending local completions from the existing approved-patch journal; relay verdict; persist retry-safe completion outcome. |
| Electron `controlPlaneApprovedPatchBridge.js`, `recoveryHost.js`, `runtimeOrchestrator.js` | Strict verdict envelope admission and current identity checks; new narrow internal IPC/relay operation; retain the actor identity. |
| Local MCP internal HTTP handler and coordination/proof implementation | Immutable central-patch origin, exact postimage proof, independently admitted owner completion, atomic checkpoint and projections. Keep generic controller rules unchanged. |
| Maintained docs | Explain effect receipt, central owner verdict, local checkpoint, failure/retry and activation-preservation semantics. |

No general policy framework, new scheduler, new controller role, custom ledger writer or public tool is needed. A packaged candidate and focused boundary tests are required before claiming live completion support. This design is proposed only; no adapter has been implemented or activated by this report.

## Focused acceptance tests

1. **Current baseline:** exact patch succeeds and remains pending until an owner verdict exists; a second action-specific central patch is admitted; default activation blocks while explicit preservation retains the queue.
2. **Authentic positive path:** central owner verdict + matching completed receipt + current exact bytes → one passed exact-wave proof and one atomic accepted checkpoint. Bridge remains Electron supervisor and does not acquire a controller lease.
3. **Authority denial:** forged/absent verdict, other device/root/generation/action/attempt/run/wave, invalid decision/receipt digest, unbound origin, revoked policy or stale runtime identity → no proof/checkpoint or workspace mutation. Ordinary Electron `task_control accept` still fails controller admission.
4. **Byte binding:** changed bytes, missing file, size mismatch, symlink/junction/reparse replacement, HEAD/contract/path-fingerprint drift → typed failure and pending wave; no rollback or rewrite of the file.
5. **Replay/fault boundary:** duplicate accepted verdict returns the same checkpoint; conflicting verdict is rejected; injected checkpoint failure rolls back terminal changes; lost finalization ACK and restart reconcile without another patch effect or checkpoint.
6. **Rejection:** records owner rejection with original bytes intact; correction requires another explicit action; never reports accepted.
7. **End-to-end boundary:** real central Node-auth observation → node journal → Recovery → local MCP → accepted checkpoint → central status, including temporary disconnect and eventual observation. Use a disposable fixture, not production source or broad suites.

## Operational conclusion

The current successful fixture proves read/write effect delivery and independently verified postimage. Owner Console acceptance proves the central verdict. Those do not yet prove local terminal acceptance. The supported immediate operational option is preserving the pending acceptance queue during an explicitly authorized full-clean refresh. Completing local acceptance requires the narrow adapter above; effect success alone must not self-accept it.
