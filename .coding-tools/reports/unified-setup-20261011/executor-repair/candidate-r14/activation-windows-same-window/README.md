# r14 transition within existing authority window

Prepared executable Windows packet for DaoChienThang / `web-mcp-assistant` / `E:\Github\Tools-Codex-web`. Root operates it after separate explicit r14 approval. Preparation has not activated r14, stopped a process, changed a policy, restarted Ubuntu, accepted a RUN or extended authority.

## Exact scope

- Candidate: `workflow-timeout-1012-r14`; app.asar SHA `f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324`; executable SHA `8270535a8149b54527172f9b774ea1fd6ed975fde44e4bb91022bdde31dea154`.
- Reuse existing context `ctx_1e7e2fec6f0e43018db7a51c6980e5c2`, requested time `1791758571067` and expiry `1791776571067` (12 October 2026 10:42:51.067 Vietnam time).
- Existing pilot `pilot_b1cb26c319fb489aae24d3b746318447` is revoked when central intake enters recovery. The server has no supported pause that preserves it. Create exactly one replacement for the same existing private service principal, binding and expiry; retain the existing context and grant.
- Preserve both pending RUN/WAVE families and every row hash captured by read-only SQLite query. No semantic acceptance occurs.
- All four existing local policy files remain byte-identical. The `policy` phase only checks their hashes and scope. No policy install, Sandbox probe, reboot, Ubuntu deployment or service restart occurs.

## Current evidence and cleanup

`observation-20261011T231645777Z.json` proves exact r13 host 11476, agent 10396, two awaiting-acceptance RUNs and zero active managed Jobs. It records three Sandbox host processes and one backend process; activation preflight was blocked. The observation is not a zero-VM activation pin.

The active Sandbox is owned by the native Runtime's manager in memory. `native.stop()` alone cannot prove teardown on Windows. The supported cleanup path is native activation prepare inside r13 `full_clean_refresh`: it fences admission and invokes the existing manager's exact `close()`/sandbox ID deprovision, then pins cleanup confirmation before replacing the native process. Recovery IPC does not expose a standalone native prepare action. r14 cannot own the old in-memory manager after stopping r13. Therefore this packet performs one supported r13 refresh first, then the r14 transition. It never stops processes by name or broadly terminates VMs.

Root must finish exact central task cleanup before intake closure; all server counters must be zero.

## Approval and receipts

Root creates a new immutable approval receipt after the human approves r14. Old r13 approval IDs are rejected. Required fields: `approved=true`, `source=human_user_response`, actual `approval_id`, `approved_at_ms`, `operation=owner_approved_r14_same_window_activation`, `candidate_tag=workflow-timeout-1012-r14`, exact exported `target`, current `context_id`, existing `expires_at_ms`, `r13_owned_executor_cleanup_refresh=true`, `pilot_replacement_same_principal_binding_expiry=true`, `new_approved_patch_verification_canary=true`, and `authority_extension`, `ubuntu_deploy_or_restart`, `windows_reboot`, `semantic_acceptance` all false. The packet contains no actual future approval.

The authority receipt is the immutable existing r13 five-hour renewal, `candidate-r13/authority-5h/remote-receipts/renew-20261011T224251426341Z.json`, not a new grant. The server observation must be under 60 seconds old and report `phase=r14_same_window_read_only_observation`, `next_operation=owner_approved_r14_same_window_activation`, existing context/window, unchanged service instance, zero current work and exact target. With recovery admission, `next_phase=intake_closed` requires `pilot_id=null` and `prior_pilot_revoked=true`; after replacement, `next_phase=pilot_replaced` includes the new pilot ID and explicit same-principal/binding/expiry assertions. Final scoped-pilot proof uses `next_phase=intake_reopened` with those same assertions.

## Root execution sequence

Use a unique `--attempt=r14-same-window-UNIQUE_ID`. All phases are explicit. Intent files use exclusive creation; uncertain mutation phases are reconciled and never automatically replayed.

1. Obtain r14 approval, record/pin it, and use a separate server operation to set recovery once, revoking the existing pilot. Do not create an intermediate pilot or renew context/grant.
2. Run `observe-r14.cjs observe` immediately before cleanup; pin the fresh observation as `--cleanup-pin` and its hash. It verifies original exact r13 host/agent, native/UI identities, both row hashes, policy hashes and zero Jobs; VM presence is recorded.
3. Run `transition-r14.cjs cleanup` with the common effect flags below. It performs one supported r13 `full_clean_refresh` under a fixed operation ID and existing expiry. Use `cleanup-status` to observe the exact supported host handoff. If the epoch awaits completion, run `cleanup-finalize` once with a fresh server receipt, then `cleanup-status`. Completion requires READY, same native identity/epoch, zero Jobs and zero Sandbox/backend processes.
4. Run `observe`, then `freeze` with `--pin=ABS_PIN`, actual `--expected-old-pid`, `--expected-old-token`, `--expected-old-epoch`. The post-cleanup pin is exclusive and must be under this attempt directory. Activation requires it under 60 seconds old.
5. Run `activate`, `policy`, `agent`, `refresh`, optional `finalize`, then `proof`. The old exact agent/UI/native/host are retired in that order with guards between effects. r14 host/agent are launched with exact WMI receipts; the agent is bounded to remaining existing authority. `refresh` performs one r14 supported full-clean refresh. New pending history hashes must remain identical at every boundary.
6. After exact r14 READY proof while intake is closed, create one same-principal/binding/expiry replacement pilot through the separate server operation and open scoped pilot. Run `proof` again against its fresh server echo. Only then run the one newly approved edit→test→proof canary in a distinct idempotency namespace. Root selects and pins the exact file pre/post state after activation; capture stdout/TAP immediately through supported output before its retention expires. Leave semantic acceptance pending for the real authorized controller. Never reset or replay the old POST/action/Job family.

Common effect flags:

```text
--attempt=r14-same-window-UNIQUE_ID
--operator-approved-r14-same-window
--approval-id=ACTUAL_NEW_R14_APPROVAL_ID
--manifest-sha256=ACTUAL_MANIFEST_SHA256
--approval=ABS_NEW_APPROVAL_RECEIPT --approval-sha256=ACTUAL_SHA256
--authority=ABS_EXISTING_RENEWAL_RECEIPT --authority-sha256=ACTUAL_SHA256
--server=ABS_FRESH_SERVER_OBSERVATION --server-sha256=ACTUAL_SHA256
--cleanup-pin=ABS_FRESH_PRE_CLEANUP_OBSERVATION --cleanup-pin-sha256=ACTUAL_SHA256
--pin=ABS_POST_CLEANUP_PIN --pin-sha256=ACTUAL_SHA256
```

Omit `--pin` only before it exists (cleanup/status/finalize). `cleanup-status` needs the authority/server and cleanup-pin pins but performs no mutation. All effect boundaries require at least twelve minutes left in the existing authority window. Failure leaves intake closed, exclusive intent evidence retained and no automatic retry.

The base-generation scripts are retained as preparation evidence. The final reviewed transition contains the explicit supported cleanup amendments; do not regenerate or overwrite it. Manifest pins the final helpers, tests and this operator guidance. Build, package parity, source tests and packaged smoke already passed; this packet's offline checks validate only its changed guards.
