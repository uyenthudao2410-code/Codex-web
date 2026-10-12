# Prepared helper packet and observed host quiescence

Observed Git: dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`, preserved. No commit or push. Native lifecycle source remains frozen to the hashes in `SOURCE-PROOF.md`; this continuation edited only helper/evidence files.

## Live read-only proof

Two independent default observer invocations completed successfully on 2026-10-11:

| Observation | Local time (+07) | Sandbox process count | Daemon record | Canonical census |
| --- | --- | --- | --- | --- |
| First | 19:16:26 | 0 | absent, never opened | passed |
| Second | 19:16:58 | 0 | absent, never opened | passed |

The process observation covers all names beginning `WindowsSandbox` and the exact `vmmemWindowsSandbox` name. The daemon path is `temp_dir()/wxc-wsb/state-aware/daemon.json`, as defined by the retained MXC lifecycle source. Its existence alone was checked; its private IPC nonce was never read.

Both canonical censuses used the current `fullCleanActivation.js` hash `881ffbdc57d4332ec1d6316199d2876d58821447b30cc861eade4c2c3d31baf1`, with all other source, package, descriptor, process identity, node heartbeat, pending acceptance, quarantine and authority guards retained from the reviewed r9 observer. Active/starting commands and Jobs were zero. Server state remained 37 actions, 9 tasks, 1 acceptance, and 13 historical unsettled/quarantined actions; the exact original families and pending acceptance records were preserved.

This proves two observed periods of host/daemon absence. It does not establish which earlier operation caused cleanup, does not expose an r9 cleanup confirmation API, and does not authorize a runtime transition.

Evidence:

- `host-read-only-observation.jsonl`: observation hash `d147bfc2e543ea888396307aba715d0e72352d12fcc8de718f2cf75c84154259`.
- `census-2026-10-11T12-16-26-063Z.json`: SHA256 `d4335fe7963c5685f3887c95dff4b4326a311af6e299ade67eeb2ca369a8f36c`.
- `host-read-only-observation-2.jsonl`: observation hash `06fd17621f6eb1012425171c5d0861efe3d86a135b9ed28f679293d0f0556222`.
- `census-2026-10-11T12-16-58-725Z.json`: SHA256 `0deec647504945f4631501909c6035daa4bb832d1189bc43cc0149095dace602`.

## Prepared timeout alternative: not executed

`r9-timeout-canary.py` prepares one distinct central `exec_run` using the approved test argv, timeout 5000 ms and output limit 32768 bytes. Default only observes. Execution requires the root flag, fresh run nonce, reviewed server-state digest and fresh native-observation digest. It never stops, cancels, deprovisions, replays or writes SQL. Observation is bounded to 240 seconds. Unknown outcomes retain the action for root reconciliation. A natural completion is preserved without retry or a VM-cleanup claim.

The fixed authority window expires at 19:19:16.518 (+07). The execution guard requires more than five minutes remaining; this prepared attempt therefore cannot be started after 19:14:16.518. Do not change the expiry or reuse it under a new authorization. Prepare and review a fresh packet for the newly authorized window if this alternative becomes necessary.

The default observer can independently establish host absence without the timeout alternative. When an exact new timeout action is available, its action/task mode verifies the submitted node receipt, native idempotency result and exact durable timeout Job before two host snapshots. The existing read-only census has a separately guarded `--after-canary` expectation of 38 actions and 10 tasks.

## Static validation and hashes

`verify-helper-static.py` passed 9 pure-function cases, Python and Node syntax checks, the embedded authority-helper digest, corrected task idempotency table/principal guard, the 240-second bound and safe nonce/error output checks. Neither live helper main was invoked by that proof.

| File | SHA256 |
| --- | --- |
| `r9-timeout-canary.py` | `8104fb3bca074c8605fedf1ff2b9f5d3a397087194b3351b5bb9a7d92a170a98` |
| `r9-timeout-native-observer.py` | `0bf532858baa253d370783ab45de80b9a28ad73ec052233f438dae7777ecc9eb` |
| `observe-r9-current.cjs` | `0ca287de959f503ddb675c47015ef2788363bd18c15cde3211a9af305ff95742` |
| Embedded reviewed authority helper | `c86ff98e315651225a9f125132ce4ac4c84fe64a537d3021971d5333c9abf869` |

## Safe root invocation

Run from `E:\Github\Tools-Codex-web` after reviewing the hashes. Default is read-only; it writes only new observation evidence in this directory.

```powershell
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/graceful-executor-cleanup/r9-timeout-native-observer.py
```

Do not call the timeout helper with `--root-execute` in the expired bounded-attempt window. Do not infer r10 activation acceptance from these read-only r9 observations.

## Completed state and next action

No new native command, action, task, cancellation, VM operation, authority change, service operation, deploy, activation, reboot, commit or push occurred. The root controller now has two real host/daemon absence observations and preserved canonical state. Next action: reconcile this proof with r10's frozen package and activation authorization; keep the timeout alternative prepared unless new evidence demonstrates a need.
