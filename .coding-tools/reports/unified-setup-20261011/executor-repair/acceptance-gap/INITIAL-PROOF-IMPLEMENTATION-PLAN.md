# Initial proof: focused implementation plan

Source investigation on 2026-10-11; dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`. This additive plan reuses `INITIAL-PROOF-ADAPTER.md`. It is not implementation, test, runtime or acceptance proof. Existing pending RUN/WAVE and quarantine are untouched. Root should finish r10 rollout evidence first.

## One bounded initial check

For the first NEW exact approved patch, carry one immutable structured plan:

```json
{
  "verification": {
    "argv": ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"],
    "cwd": "",
    "timeout_ms": 60000,
    "max_output_bytes": 131072
  }
}
```

This is the first supported invocation, subject to the existing local exec allowlist and permission window. The fixture used for live acceptance must change behavior that this check actually verifies; success from an unrelated test is insufficient. Bound the plan to action, task, writer generation, workspace/generation, exact patch pre/postimages, policy/contract and idempotency digest before dispatch. Reject an absent exec grant, expired/wrong policy, unsupported invocation or mismatched plan before any write. Do not infer exec authority from patch authority.

### Concrete native limitation discovered

`context_tools.py:_run_continuous_check` currently calls `exec_command` with `cmd` text. `exec_tools.py:exec_command` sets `popen_shell = structured_argv is None`; the Windows MXC path is selected only when argv is structured. Existing canonical `checks`/`test_command` strings therefore cannot carry the current Windows structured execution boundary. Merely changing `verification: 'none'` to tests/check strings is incomplete.

Preserve the native ProofLedger and acceptance state machine, but add the smallest initial-proof argv adapter. Do not spoof the exec bridge identity or set `_continuation_internal` to reuse an unrelated grant.

## Edit sequence and exact responsibility

| Boundary | Files and symbols | Focused change |
| --- | --- | --- |
| Public intent | `control-plane/control_plane/mcp_facade.py`: `_approved_patch_input_schema`, `_request_patch_permission`, `_request_standing_patch`, `_request_approved_patch`; `store.py`: `_mcp_approved_patch_envelope`, `request_mcp_approved_patch`, `request_mcp_standing_patch` | Exact optional plan schema; normalize once and bind it into immutable permission/intent/action/idempotency hashes. No server-selected test fallback. |
| Node dispatch | `node_agent.py`: `_admit_approved_patch_policy_request`, `_approved_patch_bridge_request`, `_safe_approved_patch_bridge_result`, `recovery_approved_patch_bridge`, `_poll_approved_patch_once` | Preserve plan identity and bounded results; require both patch and exec policy admission. Extend only `recovery_approved_patch_bridge.cjs` exact serializer fields that are crossed. |
| Local admission | `electron/services/controlPlaneApprovedPatchBridge.js`: request/admission normalization; `controlPlaneExecBridge.js`: `loadExecBridgePolicy`, `resolveRegisteredWorkspaceRoot`, `admitExecBridgeRequest` | Reuse existing structured argv/target/allowlist/limit validation before write. A synthetic exec admission may be used solely for validation; its exec actor/result must not be dispatched or substituted for approved-patch identity. |
| Initial workflow | `runtimeOrchestrator.js:controlPlaneApprovedPatch` | Bind plan + exec policy digest to the existing local request/context/idempotency identity, then send one initial custom/execute/mcp_only/deterministic workflow. Preserve existing exact patch and postimage verification. Use current workflow observation/recovery lifecycle for a slow check, not a separate central exec context. |
| Native argv transport | `workflow_tools.py:_agent_workflow_impl`; `context_tools.py:apply_changes_and_verify`, `_run_continuous_check`; `exec_tools.py:exec_command` | Carry one admitted structured verification argv into the existing source-bound check stage. Validate its attested approved-patch caller and workflow-owned internal execution marker before patch; native public input must not accept a caller-forged marker. Execute through the existing structured argv/MXC path with real RUN/WAVE ownership. Fingerprint exact argv, cwd, limits and coverage in the existing ProofLedger. |
| Durable effect/result | `workflow_tools.py:_agent_idempotency_summary`; `controlPlaneApprovedPatchBridge.js:normaliseApprovedPatchWorkflowResult`, `normaliseApprovedPatchResult`; node journal recovery helpers | Persist a bounded exact patch-effect summary independent of proof outcome so crash/dedup after a failed check remains observable. Require canonical RUN/WAVE, one exact update and validated postimage; keep plan/hash/proof status. Do not replay patch or unchanged check to repair a missing response. |
| Operator status | `mcp_facade.py:_approved_patch_status`, `_completed_approved_patch_relay`; `store.py:mcp_approved_patch_action_observation` | Project effect, proof and native acceptance separately from the existing durable receipt. Central owner verdict remains distinct. |

Add one exact field to native `agent_workflow` schema at its current registry definition when required; verify the registry location before editing. `ProofLedger`, receipt fingerprint rules, controller fencing and `task_control accept` semantics remain unchanged. Do not create a prove-existing-wave endpoint or a second proof framework.

## Result and retry contract

- Passed check: `patch_applied=true`, exact file receipt, modern source-bound proof ids/fingerprint, `proof_status=passed`, canonical RUN/WAVE and `local_semantic_acceptance=pending`; native state ACCEPTING.
- Failed or timed-out check after write: retain the same effect receipt and RUN/WAVE; `proof_status=failed` or `timed_out`, native REPLAN and its existing failure code. This is a completed effect with failed proof, not a pre-write failure or a fresh dispatch candidate.
- Pre-write admission denial: no patch effect, no command, exact actionable denial code.
- Unknown post-effect outcome: observe native idempotency/report and existing node journal. Never automatic patch/check replay. Dedup must carry sufficient bounded evidence to reconstruct the original effect and proof result.

## Native acceptance gate

The final step is the genuine lifecycle-attested native ChatWeb controller calling existing `task_control action=accept` for the NEW current RUN/WAVE. Require modern passed proof covering the mutated path and current source/HEAD/contract, plus the matching controller lease/fence. Verify the resulting native checkpoint receipt before projecting completed central status. Authenticated Control Plane owner/service and Electron remain insufficient to claim ChatWeb controller authority. If this transport is missing, retain pending state and report that exact boundary; do not fabricate the client identity, proof or acceptance.

## Smallest focused validation

1. `tests/control-plane-approved-patch-runtime.test.js`, `tests/control-plane-approved-patch-bridge.test.js`: plan admitted before write; exact initial request; one patch/one check; modern proof projection; post-effect failure and dedup/crash observation never replay; actor unchanged.
2. `control-plane/tests/test_approved_patch_node_agent.py`, `recovery_approved_patch_bridge.test.cjs`, `test_mcp_approved_patch_http_node_e2e.py`: plan/task/generation/action correlation and hash drift; missing/expired/wrong exec policy rejected pre-write; exact effect/proof/acceptance projection and journal recovery.
3. Native focused checks alongside existing workflow/idempotency tests: argv stays an array into MXC, `shell=False`, approved-patch attestation/internal origin required; public forged marker, wrong actor, arbitrary argv and shell tokens denied before write; modern proof retains exact RUN/WAVE/coverage. Failed/timeout paths preserve the exact applied patch and durable bounded summary.
4. Reuse existing `test_acceptance_file_attestation.py`, `test_proof_cache_source_binding.py`, `test_agent_workflow_idempotency.py`, `test_orchestration_workflow.py` for unchanged ledger/accept semantics. Run only affected cases, plus genuine controller wrong-wave/source/controller rejection if the adapter crosses that boundary.
5. One live NEW approved patch task, one admitted check through the supported structured executor, source-bound proof in its own RUN/WAVE, then genuine native ChatWeb accept and observed checkpoint. Old pending/quarantine hashes remain identical. Packaged/source parity and controlled rollout require separate root evidence.

No tests or jobs were launched for this document. Production source, runtime and authority were not changed in this lane; no commit, push, release, SSH or service operation occurred here.
