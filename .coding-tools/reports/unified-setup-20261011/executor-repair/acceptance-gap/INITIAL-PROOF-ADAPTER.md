# Initial proof adapter for a new approved patch

Observed: 2026-10-11 19:27:40 +07:00. Repository: `E:\Github\Tools-Codex-web`, dirty `main` at `2c554f59cb7b8ffc86ce5e0e28076c792777642f`.

This is focused source analysis and a next-wave proposal. It is not implementation, test execution, runtime activation, or acceptance evidence. No production source was edited and no runtime, authority, SSH, service, deployment, commit, or push operation was performed for this investigation. Existing pending and quarantined RUN/WAVE records were not accepted, rejected, or replayed.

## Finding and smallest proposal

Use the **initial native workflow's existing proof path for a NEW exact patch**, followed by **existing native `task_control action=accept` from the actual attested ChatWeb controller**. Do not add a prove-existing-wave endpoint or a parallel proof/acceptance framework for this wave. Do not replay any old applied patch to add tests retroactively.

The native implementation already executes requested verification after the patch, records source-bound ProofLedger evidence for that exact RUN/WAVE, and reaches technical ACCEPTING. The current Electron approved-patch adapter suppresses that path with `verification: 'none'`. The central facade currently has no local acceptance relay. Therefore proof can be added to the initial adapter without changing native proof/checkpoint semantics, but a complete central-only finishline must not be claimed before its controller transport is proven.

## Exact implementation evidence

| File and line | Symbol / observation |
| --- | --- |
| `electron/services/runtimeOrchestrator.js:1776` | `controlPlaneApprovedPatch` derives a caller-scoped local context from exact action/attempt/task/writer/policy/facade identities. |
| `electron/services/runtimeOrchestrator.js:1991` | Initial `agent_workflow` call already applies the exact patch through custom/execute/mcp_only/deterministic, but sets `verification: 'none'`. |
| `electron/services/runtimeOrchestrator.js:2049` | Comment and result keep local semantic acceptance pending; the bridge does not self-accept. |
| `electron/services/controlPlaneApprovedPatchBridge.js:591` | `normaliseApprovedPatchWorkflowResult` validates the local RUN/WAVE result. This is the adapter boundary to extend for proof status, including post-effect proof failure. |
| `resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py:1467` | `_agent_workflow_impl` forwards commands/checks, verification, test/build commands, limits, workdir and exact orchestration context into `apply_changes_and_verify`. |
| `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:751` | `apply_changes_and_verify` supports checks; verification supports none/tests/build/all. |
| `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:892` | EXECUTING transitions to PROVING. Affected/adopted paths generate `proof_source_binding`. |
| `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:1001` | Checks use `ProofLedger.fingerprint` and `run_cached`; execution receives the owning RUN/WAVE. |
| `resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:1060` | Non-none verification executes `verify_build` through the same proof ledger and exact RUN/WAVE. |
| `resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py:349` | A regular new workflow on an ACCEPTING context is denied by `FINAL_ACCEPTANCE_REQUIRED`; a subsequent exec alone does not fill its proof ledger. |
| `control-plane/control_plane/mcp_facade.py:415` | `_approved_patch_input_schema` exposes apply_patch/patch_status, without a verification plan. |
| `control-plane/control_plane/mcp_facade.py:545` | `_exec_input_schema` exposes separate exec_run/exec_status, without caller-supplied native RUN/WAVE. |
| `control-plane/control_plane/mcp_facade.py:3215` | `_approved_patch_status` explicitly distinguishes central owner verdict from pending local proof/checkpoint. |
| `resources/coding-tools-mcp/coding_tools_mcp/server.py:1287` | `_require_hub_controller` requires the active matching controller lease for an identified caller; a missing lease can be claimed only by client_type chatweb. |
| `resources/coding-tools-mcp/coding_tools_mcp/server.py:1332` | `_claim_hub_controller_for_run` does not let an Electron bridge claim the ChatWeb controller. |
| `resources/coding-tools-mcp/coding_tools_mcp/controller_reattach.py:37` | `controller_identity` requires chatweb/controller identity; reattach is not an authority grant to a central service. |
| `resources/coding-tools-mcp/coding_tools_mcp/coordination.py:920` | `task_control handoff` records/reads a bounded continuity capsule, not a controller transfer to Control Plane. |
| `resources/coding-tools-mcp/coding_tools_mcp/coordination.py:1101` | Existing accept validates ACCEPTING/current wave and native controller authority. |
| `resources/coding-tools-mcp/coding_tools_mcp/coordination.py:1178` | Mutation-bearing acceptance requires passed proof in this exact RUN/WAVE. |
| `resources/coding-tools-mcp/coding_tools_mcp/coordination.py:1228` | Acceptance invokes existing atomic `checkpoint_with_receipt`. |

Line references describe the observed working tree; concurrent later edits can move them. The previous `folder-permissions-20261011/local-acceptance-adapter.md` and maintained `docs/CODE_EXECUTION_COMPLETION_PLAN.md` were reused as direction/evidence, not treated as live proof.

## Next implementation wave

1. Bind one bounded verification plan to the **new** patch action before dispatch. The public plan must be immutable in the action/idempotency digest, admitted against the same task/workspace/generation and local exec policy, and validated before the first write. Preserve the structured argv/allowlist boundary. Native currently exposes canonical test/check command strings; do not forward arbitrary untrusted shell text. Start with one concrete supported test invocation rather than a generic verification framework.
2. In `controlPlaneApprovedPatch`, pass the admitted verification/test/check plan in the existing initial `agent_workflow` call. Preserve the exact patch envelope, deterministic route and context derivation. Expose the resulting proof ids/status and exact RUN/WAVE in a bounded receipt; distinguish patch effect from test outcome. A failed/timed-out test after a write must keep its effect receipt and failure/REPLAN evidence, never become a reason to replay the patch.
3. Exercise existing `task_control action=accept` through the real lifecycle-attested native ChatWeb connector for that NEW RUN/WAVE. It must preserve controller identity and active fencing/lease. Electron remains a relay/executor and must never change its own headers to chatweb, use the missing-identity compatibility path, submit forged proof ids, or auto-accept.
4. Observe the native checkpoint, then update central status from verified native evidence. Keep central owner verdict and native acceptance distinct until an authenticated exact correlation is demonstrated.

Expected adapter files: `control-plane/control_plane/mcp_facade.py` (schema/normalization/status), `control-plane/control_plane/store.py` (immutable intent/digest/action dispatch), `control-plane/control_plane/node_agent.py` (exact verification dispatch/result validation), `electron/services/controlPlaneApprovedPatchBridge.js` (admission/result allowlists), `electron/services/runtimeOrchestrator.js` (initial request and bounded receipt). Extend only the corresponding recovery/result serializer if its existing exact allowlist is crossed. Native `workflow_tools.py`, `context_tools.py`, `proof_ledger.py`, `acceptance_receipts.py`, and `coordination.py` should remain unchanged for this proposal.

## Acceptance authority and current limit

An authenticated Control Plane owner/service currently does **not** acquire native controller authority merely by being authenticated centrally. No examined current handoff/reattach path grants it that authority. The connector attestation helper signs caller labels and the exact native lifecycle with a local secret; it is not proof of a central principal delegation. Minting a chatweb label from the Electron bridge would be an authority change, not ordinary receipt forwarding.

The preferred next acceptance test is therefore the existing actual attested native ChatWeb controller action. If that transport is unavailable, report the precise missing authority/transport boundary and retain local pending state. A separate explicit, narrowly bound principal-to-controller handoff design is then necessary; this report does not assume it exists or authorize it.

## Exact proof identity and reuse

`task_control accept` does not trust a caller-provided digest. It reads proofs from the canonical ledger for the exact current RUN/WAVE. `acceptance_receipts.py:121`, `passed_proof_fingerprint`, computes SHA-256 of sorted unique `proof_id:input_fingerprint` pairs for passed proofs joined with `|`; empty passed proof set yields the empty string and fails mutation acceptance.

Modern passed proof must bind current HEAD, contract fingerprint, canonical covered paths and exact current path fingerprint (`acceptance_receipts.py:135`). Covered paths must include accepted mutation paths. Mixed legacy and modern source-bound passed proofs are rejected. New remote adapter evidence must require modern binding and never rely on the all-legacy compatibility fallback.

Reuse only a passed proof whose **entire existing cache identity** matches: stage id/version, base HEAD, worktree fingerprint, contract, covered path fingerprint, command/config/workdir/limits and upstream proof ids (`proof_ledger.py:40`). A reused proof from another wave is materialized as a new target-wave proof with source lineage and `executed=false` (`proof_ledger.py:131`). A same-byte patch result, a separate central exec success, or a manually copied hash is not an equivalent proof.

## Focused validation for the next wave

- `tests/control-plane-approved-patch-runtime.test.js`: initial request carries the admitted plan, patch/check happen once, exact RUN/WAVE retained, bridge remains pending; duplicate idempotent observation does not execute again; post-effect proof failure is explicit and never replays patch.
- `control-plane/tests/test_mcp_approved_patch_http_node_e2e.py`: caller/action/task/generation/plan correlation, wrong/expired local exec policy rejected pre-write, output status separates effect/proof/acceptance.
- `resources/coding-tools-mcp/tests/test_acceptance_file_attestation.py`: exact source-bound passed proof allows the genuine controller checkpoint; missing/wrong-wave proof, changed path bytes/HEAD/contract and stale controller are rejected. Use existing tests where unchanged instead of rewriting their assertions.
- `resources/coding-tools-mcp/tests/test_proof_cache_source_binding.py`: exact cache hit records target-wave lineage; source/config/command drift prevents reuse.
- Live acceptance is one NEW approved task/patch with one bounded admitted check, observed native proof and controller checkpoint. Existing pending RUN/WAVE and quarantine must remain unchanged.

No tests were run for this read-only report. Final investigation state: production source untouched, no newly launched Job, dirty `main @ 2c554f59`; the only new artifact is this report. Root should finish r10 activation proof before starting this source wave.
