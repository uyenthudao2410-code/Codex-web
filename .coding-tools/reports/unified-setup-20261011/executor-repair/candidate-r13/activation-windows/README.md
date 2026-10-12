# r13 Windows transition packet

Prepared for root operation only. Preparation has not activated a runtime or changed server authority. Future explicit approval for `source-fingerprint-1012-r13` on profile `web-mcp-assistant` and the exact pilot rotation is required; each effect requires `--operator-approved-r13`, `--approval-id=r13-same-window-transition` and the frozen manifest hash. The approval ID is a stable operation marker. Root must retain the actual human approval separately before using this gate.

The exact target remains `E:\Github\Tools-Codex-web` on the existing device, workspace generation, binding, profile and Ubuntu service. This packet transitions current packaged r12 to r13. Package/source proof requires all 17 frozen payload files; imported lifecycle JS dependencies retain their verified hashes.

Preserve the original r12 renewal evidence and reuse its context `ctx_d7a539dd85264a62951fddad0ffa2f23`, requested `1791747735200`, expires `1791751335200`, and four installed policy hashes. Recovery admission unconditionally revokes the old pilot `pilot_98c0b502568a4f888b3106838004c117`; it cannot be reused after pause. Root must first reconcile and close the failed r12 canary, then execute the separately reviewed `candidate-r13/intake-transition` pause-and-rotate operation exactly once. That operation creates one replacement pilot under the existing context and expiry before Windows activation. Do not pause again after creating that pilot.

The new immutable rotation receipt is passed as `--renewal`; the old r12 receipt is rejected by these helpers. Both the rotation receipt and each fresh server observation must identify operation `owner_approved_r13_same_window_pilot_rotation`, approval marker `r13-same-window-transition`, the exact revoked predecessor and the live replacement pilot. During activation, server admission must be `recovery` and the marker phase `authority_rotated_in_recovery`. At least twelve minutes must remain at each effect boundary, with exact target/window and zero queued/accepted actions, open tasks/writers and unsettled target actions. No context, policy or expiry extension is part of this packet.

Root pins each receipt with an absolute path and SHA256; server observations must be under 60 seconds old. Use a new `--attempt=r13-<unique-id>` directory. Never remove/reuse intent files or repeat a failed phase automatically. Keep intake closed on failure and reconcile the exact attempt.

## Phase sequence

1. `observe` reads current r12 identity, census and unchanged historical pending rows. `freeze` additionally writes the pinned fresh old-runtime receipt, with `--pin`, `--expected-old-pid`, `--expected-old-token`, and `--expected-old-epoch`.
2. `activate` retires only pinned old agent/UI/native/Host identities, then launches/adopts the r13 Host via the supported WMI helper. It requires fresh old pin, zero VM/backend and canonical quiescence.
3. `policy` verifies the existing policy files and original hashes unchanged. It installs no policy, grants no permissions and starts no Sandbox probe.
4. `agent` starts one bounded registered r13 connected agent before READY. WMI provenance, exact process identity and launching PowerShell exit are checked.
5. `refresh` requests exactly one supported `full_clean_refresh` with preserved historical pending acceptance. Never issue another refresh to recover a transient VERIFYING state.
6. `status` observes the transition. `finalize` can complete that exact epoch when appropriate and does no additional refresh.
7. `proof` requires READY, fresh authenticated central route, same policy hashes, fresh native heartbeat echo, zero live work/VM and exited launch tools. It performs no semantic acceptance.

All effect phases require `--operator-approved-r13`, `--approval-id=r13-same-window-transition`, `--manifest-sha256`, `--server`/`--server-sha256`, `--renewal`/`--renewal-sha256`, plus the same attempt ID. `activate` and `policy` additionally need `--pin`/`--pin-sha256`. After local exact READY proof, root uses the reviewed server reopen phase once. A final server receipt may show `scoped_pilot` with marker `intake_reopened`; it must retain the same replacement pilot/context/window and echo current native identity.

No Ubuntu deployment/restart, Windows reboot, supervisor installation, semantic acceptance or Sandbox execution is part of this Windows packet. Server pilot rotation and reopen are effects of the separately reviewed intake-transition packet and require the same explicit r13 approval.
