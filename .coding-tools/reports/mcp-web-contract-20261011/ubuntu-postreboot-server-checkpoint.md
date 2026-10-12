# Ubuntu read-only post-reboot checkpoint — 2026-10-11

## Initial authority and health observation

At 15:57:12.769 +07 (`1791709032769`), `svhome@100.116.112.22` still ran the authorized revision `beaa9d5ade4926ef231e3ec9d0a517fe93830e90`, package fingerprint `sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835`, schema 28, and service PID 794023. Immutable release verification passed for all 38 files. No deployment or restart occurred during this observation.

The exact binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`, standing context `ctx_80a102323c14412fa539a396a1edd034`, scoped pilot `pilot_4723468161ec46269ea73e93e854f52a`, device/workspace/generation, registered read/write/exec capabilities and existing service grant were preserved. The approved authority window still ended at 16:26:24.008 +07 (`1791710784008`); no renewal occurred.

At that time the Windows node's cached `ready`/`enabled` values were stale: heartbeat age was 925,112 ms and the advertised short policy heartbeat window had expired. This was not proof of current runtime readiness after reboot. The central service remained healthy.

Actions/tasks/acceptances: 30/4/1. Queued actions, accepted actions, open writer leases and open tasks: all zero. Thirteen historical unresolved action families were unchanged, with digest `825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed`.

Evidence: `ubuntu-postreboot-server-initial.jsonl`, `ubuntu-postreboot-observe-tail.py`.

## New exec action observation

The root controller submitted the actual post-reboot test action. This observer did not submit or replay it. At 16:05:14.430 +07 (`1791709514430`), the one new exec action `act_0dbe0e6b68a34afea0e93ca5e55e4b34`, linked to task `task_80f4e34defce4c139bc8c6a0ffa2984b`, was `reconcile_required` with one UNKNOWN receipt. Its single attempt was dispatched at 16:02:00.749; the receipt arrived at 16:02:21.179, 20,430 ms later.

Receipt diagnostics were `CONTROL_PLANE_EXEC_EFFECT_UNKNOWN` and `CONTROL_PLANE_EXEC_TIMEOUT`. The server receipt had no local handle, command ID or job ID. No server reconciliation or dispatch disposition was present. The sealed command matched the expected focused Node test; sealed argv digest matched the private exec intent, cwd was empty, and the output byte bound matched. Raw sealed arguments, argv, receipt messages and credential material were not emitted. The first observer had an assumed 120,000 ms timeout comparison that was false; this is not evidence of sealed-intent corruption. The helper was corrected to compare the sealed timeout directly with the private intent on its next use.

Node heartbeat was now fresh (15,062 ms), readiness was `ready`, policy was `enabled`, and activation epoch was `activation-mv3lbekh-30cb2a711387e84898df6da3b1a6fad1`. This does not prove the test completed. The local durable command must be inspected before any result adoption, reconciliation or retry.

Global state was 31 actions, 5 tasks and 1 acceptance. Fourteen actions were unresolved: the thirteen historical families plus this one new exec UNKNOWN. Queued and accepted actions remained zero. One task remained open and one unreleased writer lease remained recorded; the lease expiry was 16:02:57.493 +07, already elapsed. Historical evidence digest remained unchanged.

The historical-family helper query excluded only this exact new action while global counts still covered every action. No expected-quiescence assertion was used for the new UNKNOWN boundary. No authority operation, restart, deployment, action replay, task mutation, writer mutation or direct database write was performed by this workstream. Git HEAD and existing work were preserved; observer files and sanitized receipts are new local evidence.

Evidence: `ubuntu-postreboot-exec-unknown-observation.jsonl`, `ubuntu-postreboot-unknown-observe-tail.py`.

## Final observation after the authorized r5 test

The root controller resolved the original action using exact local job evidence and a failed-before-process receipt, then the user authorized r5 activation and a repeat test inside the same scope and deadline. This observer did not perform those mutations. At 16:17:36.644 +07 (`1791710256644`), the final read-only inventory/task list/action observation succeeded.

- MCP inventory reported `online`, `ready`, `dispatchable`, and policy `enabled` for the exact binding. The current contract remained schema 32, profile `control-plane-private-tunnel-service-v1`, SHA-256 `274af168c29bc7a10eb35e2314632badddabe456c2c645cda7a7767480fc2e32`.
- New r5 action `act_2de8172636ef4cdba9e388c203855f6b` was settled with one completed receipt, exit code 0 and one delivery attempt. Local handle, command ID and job ID were present in its receipt. Its task `task_9cfe9f74f92e476982085da7165ea0d8` was closed and writer lease released. The root controller separately verified four passing test cases, zero failures and bounded output.
- Original r4 action `act_0dbe0e6b68a34afea0e93ca5e55e4b34` was settled failed. The added receipt `rcpt_01ff7fded14b46b7bf72eacba5903391` reported `CONTROL_PLANE_EXEC_SANDBOX_START_FAILED_BEFORE_PROCESS` and `SANDBOX_STATE_PHASE_FAILED`, digest `e9ab79ec88547566c407ed9c8a8d5b389e4583f4c685d798215e3d12f389ffb0`. The original UNKNOWN receipt and sealed-argument hash remained unchanged. Its task was also closed and writer released.
- Global action/task/acceptance counts were 32/6/1. Queued actions, accepted actions, open writers and open tasks were all zero. No nonhistorical unresolved action remained. The thirteen historical unresolved families retained their exact digest.
- The standing context and pilot retained exact expiry 16:26:24.008 +07. Remaining authority was 527,364 ms (8 minutes 47 seconds). No renewal occurred. The node heartbeat was fresh (4,425 ms), with r5 activation epoch `activation-mv3lxw05-c20b330cb58f3edea4f421b9a65b0743`.
- Ubuntu remained on the exact authorized `beaa9d5a` revision, verified 38-file package, schema 28 and original service PID 794023. No server deployment or service operation occurred during these observations.

Final evidence: `ubuntu-postreboot-server-final.jsonl`, `ubuntu-postreboot-final-observe-tail.py`. The observer performed only MCP metadata `inventory`/`task_list`, operator GET requests and SQLite read-only queries. The historical-family query excluded only the exact two new test action IDs; global state counts still covered the whole database.

## Completed state and next action

Server-side post-reboot verification is complete: current inventory is ready, the authorized repeat test has a completed receipt with exit code 0, and no active task/writer/action from this wave remains. The root controller owns final local runtime checks and the combined operator report. The authority deadline is unchanged; further operations after that deadline require an authorized renewal. Git HEAD and existing work remain preserved, with new sanitized observer evidence only; this workstream performed no commit or push.
