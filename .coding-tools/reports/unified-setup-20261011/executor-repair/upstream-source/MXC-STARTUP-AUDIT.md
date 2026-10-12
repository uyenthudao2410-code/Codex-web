# Pinned MXC startup audit

Observed 2026-10-11. Read-only product audit; no Sandbox execution, replay, test, service change, authority change, or product edit was performed by this audit.

## Source identity

Official repository: `https://github.com/microsoft/mxc`.
Exported checkout: `mxc/` at commit `cbe1774364ea2ec846f56ab744e43a416f751420`; exported files match that checkout. Clone Git metadata is outside `.coding-tools`, under the task's Temp audit directory. No nested Git repository is present in the evidence export. Export contains 2,105 public source files, 17,473,317 bytes. No exported files are ignored by the parent repository.

The runtime provenance declares a local patch SHA `85a0991dd4473b31574ad6c71d2c489389e6719a3e6ef9116f5f9156a7b7c8df`, but `scripts/patches/mxc-windows-sandbox-c-drive-share.patch` is absent. This audit establishes the unpatched upstream source identity; it cannot establish parity between that source and the patched binary from provenance alone.

## Start failure discrimination

[Pinned lifecycle source](https://github.com/microsoft/mxc/blob/cbe1774364ea2ec846f56ab744e43a416f751420/src/backends/windows_sandbox/lifecycle/src/state_aware.rs) defines start-ready 420 seconds, transition lock 600 seconds, IPC connect 5 seconds and IPC I/O 10 seconds. A daemon exit becomes `backend_error`, except exit 75 which represents VM slot contention. Thus elapsed time near 127 seconds cannot identify the cause from this source alone. Root's ongoing reproduction must retain the numeric timeout from the actual error envelope before cleanup.

[Pinned VM source](https://github.com/microsoft/mxc/blob/cbe1774364ea2ec846f56ab744e43a416f751420/src/backends/windows_sandbox/lifecycle/src/vm.rs) waits for the trusted System32 WindowsSandbox launcher process. A nonzero launcher exit is retained in its causal error chain as a signed process status. Ownership proof is captured only after launcher success; VM teardown checks process disappearance for 30 seconds and then waits 5 seconds for backend release. A native status is required before asserting a Windows platform cause.

## Safe capture before deprovision

Pinned token validation is exactly `wsb:[0-9a-f]{8}`. Derive paths from the adapter's trusted child environment, never from free-form messages:

`Path(manager._environment()["TMP"]) / "wxc-wsb" / "state-aware" / token / "daemon.log"`

`control_plane.rs:351,397` defines this layout; `state_aware.rs:475` adds `daemon.log`. Windows Rust temporary-directory resolution uses the child temporary environment. Deprovision removes the per-sandbox directory, including this log. Capture must therefore occur before cleanup. Prefer a pre-start byte offset; otherwise a fresh sandbox directory plus invocation time must establish the evidence window. Bound reads, require resolved containment, reject symlinks/reparse points, and retain only a fixed field set. Never export paths, sandbox token, nonce, endpoint, arbitrary messages or raw log lines.

Finite classifier inputs:

| Required evidence | Safe result |
| --- | --- |
| Exact backend message `daemon did not become ready within Ns`, bounded integer N | `daemon_ready_timeout`, `backend_timeout_seconds` |
| Backend daemon-exit message with bounded signed status | `daemon_exit`, `daemon_exit_code` |
| Latest causal `Error: launch VM` plus anchored `WindowsSandbox.exe exited with N`, signed 32-bit N | `vm_launch_exit`, `vm_launch_exit_code`, unsigned hexadecimal status |
| Exact causal rendezvous failure with bounded timeout | `rendezvous_timeout` |
| Exact guest-connect/Ready/preamble error context | A fixed connect, ready or protocol category |
| Exact foreign-VM refusal message | `foreign_vm_active` |

A formatted hexadecimal process status is not automatically an HRESULT interpretation. Unknown or mixed logs stay unclassified. Generic `backend_error` does not prove absence of effects.

## Boot markers and current causal gap

The daemon's fixed rendezvous and configuration directories are `wxc-wsb-stateaware-rendezvous` and `wxc-wsb-stateaware-config` beneath its temporary directory. Before boot it clears the previous rendezvous endpoint and writes a fresh nonce. The guest consumes and deletes the nonce, pre-authorizes its firewall, publishes a listener endpoint, accepts four authenticated roles, locks down networking, and emits Ready.

For the root reproduction, finite booleans can identify the last completed stage: launch requested, rendezvous seen, four channels established, protocol accepted, Ready received. A contemporaneous bootstrap log can add guest-started, nonce-loaded, firewall-authorized, listener-advertised, host-connected and firewall-locked markers. An older bootstrap log is stale and must not influence diagnosis.

There is no source-backed reason yet to raise a timeout or replay the original action. The first successful cold boot followed by repeated failures needs the current attempt's timeout and last stage. Preserve this gap rather than claiming a restart-residue, firewall or endpoint diagnosis from elapsed time.

## Focused regression checks proposed

1. Known cause returns only allowlisted code, phase, bounded numeric timeout/status and fixed stage fields; injected secrets, paths and nonce text are absent.
2. Invalid sandbox token, reparse escape, oversized/missing log, old byte range or old bootstrap timestamp produces no derived cause.
3. Original ToolFailure survives successful and failed cleanup; failed teardown remains uncertain.
4. Generic daemon failure remains UNKNOWN unless authenticated exact Job evidence proves a terminal before-process outcome.
5. If live capture proves a backend deadline mismatch, restore source reproducibility first, then test the exact corrected binary's cold boot, warm execution and teardown sequence.
