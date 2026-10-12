# Plan and approved unified setup rollout — final checkpoint

11 October 2026, Asia/Saigon. Repository remains dirty `main @
2c554f59cb7b8ffc86ce5e0e28076c792777642f`; existing unrelated changes preserved.

## Outcome

The code execution completion plan is saved in
`docs/CODE_EXECUTION_COMPLETION_PLAN.md`, linked from CURRENT_STATE and ROADMAP.
It prioritizes the reproduced execution startup failure, then one correlated
patch/test/proof/controller acceptance flow, daily exact-target authority,
diagnostics, managed agent lifecycle, recovery and supported installation.
An independently verified real code problem through ChatGPT is the finish line.

The approved r7/Console activation and exact-folder 60-minute renewal were
performed. **Execution acceptance did not pass**; no test success is claimed.

## Changed external resources and strongest proof

- Windows `web-mcp-assistant` on DaoChienThang runs the verified unpacked r7
  candidate. Full-clean activation reached READY at 17:24:03, exact host/UI/
  native/agent identities and fresh heartbeat. Pending local semantic acceptance
  RUN `95e909f0040a448faa9f1f3257e2ee2c` / WAVE
  `c101beadfc6d4f2fbc13845052c84693` remains unchanged.
- Ubuntu `svhome@100.116.112.22`, **user** `codex-control-plane.service`, runs the
  one-file Console snapshot `5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f`.
  Identity is a content-addressed source snapshot, **not a new Git commit**.
  Only frozen `web_ui.py` SHA `03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b`
  differs from base `beaa9d5a`; 37 other payloads are unchanged. Schema 28,
  38-file integrity, health and served HTML/JavaScript byte hashes passed.
- One exact context/pilot window is 17:20:33.341–18:20:33.341 +07 for
  `E:/Github/Tools-Codex-web`, binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`.
  Binding, device, generation, service grant/scopes/credential were preserved.
  Metadata assignment was synchronized; standing file/exec policies matched and
  needed no reinstall. Actual Sandbox prerequisite/child-process probe passed.
- Authenticated Ubuntu MCP inventory observed online/ready/dispatchable;
  wrong-contract feedback was structured/actionable. Fixture read (49 bytes)
  and bounded source read (1,366 bytes) completed with verified content hashes.

## Live exec failure and reconciliation

One attempt of `node --test tests/control-plane-approved-patch-runtime.test.js`
created action `act_2673b93c5bb3483889742dfe3055fd3d`, task
`task_8982097843784d44bcc4bb0440c35141`, native Job
`8f6df428efb4489aa310f6266cce054f` and command `WaJumSgZyYU90Yj_Mt7qu-Gp`.
The Job ended `spawn_failed`, root PID 0, before a test process. Native error is
`SANDBOX_STATE_PHASE_FAILED`; phase/backend cause was lost in the current error
projection, which reached the bridge as `CONTROL_PLANE_EXEC_MCP_REJECTED`.
This is not action/authority expiry or a 120-second Recovery client clamp.
No exit code or TAP output was produced. No native resource code changed from
r5, so no UI-causality claim is made.

At 17:31:51 exact request/idempotency/terminal Job evidence, zero managed jobs
and zero Sandbox processes allowed a supported authenticated failed receipt.
Server ACK `rcpt_97a6b0ffb80149fd8f87c5d6b70e3182` is failed/settled. The original
UNKNOWN journal/receipt was preserved. At 17:31:58 MCP writer release and task
close succeeded. There was no command replay or manual ledger/evidence edit.

Final local census at 17:32:19 has zero active commands, background operations,
managed processes and agent lanes. Its `RUNTIME_BUSY` classification is expected
because the serving native runtime is live; sole blocker is
`live_runtime_state_process`. Integrity is `ok`; the prior acceptance boundary
is unchanged. This does not certify test success.

Final Ubuntu census at 17:33:17.904 observes healthy exact snapshot and fresh
online/ready target. Counts: actions 35, tasks 7, acceptances 1; queue, accepted
actions, open tasks and writers all zero. Only the original 13 quarantined
historical unresolved families remain, digest
`825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed`.

## Validation, deviations and remaining work

Reused exact unchanged candidate proof (106 focused Node cases, eight Console
cases, isolated packaged smoke/source parity). New proof consists of immutable
snapshot verification, syntax, guarded activation/census, actual policy/Sandbox
probe, MCP reads, one failed live exec and terminal reconciliation/cleanup.
Documentation links, whitespace and conflict checks passed. No broad suite or
new product compilation was run for this planning turn.

The first Console postflight helper incorrectly encoded existing byte constants;
automatic rollback was healthy. Correcting only that verifier and guarded
reapplication succeeded. Failure/rollback evidence is retained. Private backup
and old immutable release remain on Ubuntu; no database restore occurred.
The one-file repack used truthful snapshot identity to avoid committing or
deploying unrelated dirty source. No primary staging/commit/push/tag/public
release or Windows reboot occurred.

Renderer continuation and actual ChatGPT connector proof remain open. The trial
poller is bounded to 200 iterations at 15 seconds; it is not a supported
persistent installation. Sandbox binaries still have the experimental release
gate. Standing private-service delegation and proof/acceptance linkage remain
planned source changes, not authority granted by this rollout.

**Exact next action:** retain allowlisted native code/phase/backend diagnostics
in the existing exec response/Job evidence; reproduce and repair Sandbox startup
after probe/relaunch, then validate one terminal exec before implementing the
patch/proof/acceptance adapter. Do not repeat the unchanged failed request or
extend authority silently.

Evidence: `server-final-census.json`, `windows-activation.jsonl`,
`live-read-verification.jsonl`, `live-exec-verification.jsonl`,
`canary-reconciliation.jsonl`, `failed-task-cleanup.jsonl`,
`R7-CANARY-DIAGNOSIS.md`, `server-rollout-checkpoint.md`.
