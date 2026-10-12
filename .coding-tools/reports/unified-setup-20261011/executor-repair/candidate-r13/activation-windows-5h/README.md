# r13 Windows transition under approved five-hour authority

Root-operated packet for profile `web-mcp-assistant`, device `DaoChienThang`, exact root `E:\Github\Tools-Codex-web`. Human approval: `call_a60e931056bd402b997c6c10b0796d81`. Preparation has no runtime or server effects. Earlier same-window packets and receipts remain intact.

Reuse candidate `source-fingerprint-1012-r13`, source freeze SHA `e9351a360eaa7c016514015a27ea06c762604e12c2a5ca436a550abbf09f29ff` and 17-file parity SHA `7c2c60851359f619472bbfafb649529b3eaae90ee6a4626a724c401b91323b88`; packaged smoke already passed. No rebuild or repeated source tests are required for this authority-only packet.

## Authority and policy

Root first uses the separate `candidate-r13/authority-5h` close → renew operation exactly once. The immutable renewal receipt must show phase `r13_5h_authority_renewed`, actual approval ID, `duration_ms=18000000`, new context and pilot, requested time anchored once, and `expires_at_ms = requested_at_ms + 18000000`. Each fresh server observation uses phase `r13_5h_read_only_observation`, `next_operation=owner_approved_r13_initial_verification_5h`, marker `authority_renewed`, admission `recovery`, and zero current target work. Its current and `next_` context/pilot/window fields must match the pinned renewal. Both receipts prove the preserved service grant covers the complete window. The actual public receipts omit marker-only operation/approved-duration metadata; those absent fields are not invented or required. The old 03:42 window cannot be reused or retroactively extended.

Old runtime observation may show expired route, absent old agent and incomplete admission. Those are recorded as observed; activation still requires exact old process identity, no active work/VM, unchanged historical pending records and pinned policies. This does not claim the expired r12 runtime is READY.

The `policy` phase uses the existing packaged `installReadOnlyPolicyAssignment` path for the newly assigned expiry. ReadOnly schema deliberately contains no context ID; context linkage is verified in server assignment receipts. Only its expiry may change. FileRead/ApprovedPatch/Exec already have current facade contracts and standing authority; their values and file hashes must stay unchanged, and they are not reinstalled. No sandbox probe runs.

## Root sequence

Choose new attempt ID `r13-5h-<8 or more unique characters>`. Observe and freeze old runtime immediately before activation; the pin must be under this packet's exact attempt directory.

1. `observe --attempt=ATTEMPT` records current r12 identity without effects.
2. `freeze --attempt=ATTEMPT --pin=ABS_OLD_PIN --expected-old-pid=ACTUAL --expected-old-token=ACTUAL --expected-old-epoch=ACTUAL` writes a new exclusive old-runtime pin.
3. `activate`, `policy`, `agent`, `refresh`, then optional `finalize` each use the common flags below and a fresh server observation under 60 seconds old. Refresh happens once; never replay an intent after uncertain effects.
4. `status --attempt=ATTEMPT` observes that exact transition. `proof` uses common receipt flags and requires exact READY, current route/policy, bounded agent heartbeat and matching server native echo.
5. Root reopens the scoped pilot through the separate server packet once, then may repeat the read-only proof against a fresh `intake_reopened`/`scoped_pilot` observation. Trial follows through its distinct canary namespace.

Common effect flags:

```text
--attempt=ATTEMPT
--operator-approved-r13-5h
--approval-id=call_a60e931056bd402b997c6c10b0796d81
--manifest-sha256=ACTUAL_MANIFEST_HASH
--server=ABS_FRESH_SERVER_OBSERVATION --server-sha256=ACTUAL_SERVER_HASH
--renewal=ABS_IMMUTABLE_5H_RENEWAL --renewal-sha256=ACTUAL_RENEWAL_HASH
--pin=ABS_OLD_PIN --pin-sha256=ACTUAL_PIN_HASH
```

The `--renewal` file is the new five-hour effect receipt, not old r12 or previous same-window evidence. At least twelve minutes must remain before each effect boundary. Agent `max_iterations` is bounded by remaining authority at 15-second interval, capped at 1200 and never zero. The existing agent permits this count. Iteration/backoff timing is not a hard wall-clock expiry guarantee; server context/pilot/action expiry remains authoritative.

No Ubuntu deployment/restart, Windows reboot, durable supervisor, semantic acceptance or Sandbox execution occurs in this Windows packet. Failed or uncertain phases retain their exclusive intents and keep server intake closed for reconciliation.
