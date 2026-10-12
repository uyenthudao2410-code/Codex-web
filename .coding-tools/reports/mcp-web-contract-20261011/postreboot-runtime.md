# Windows post-reboot runtime checkpoint

Observed 2026-10-11 at 16:01 Asia/Saigon. Primary remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`; unrelated edits and pending acceptance are preserved. No commit or push performed.

The owner reported completing reboot. A fresh `Win32_OperatingSystem.LastBootUpTime` observation confirms boot at `2026-10-11T08:42:38.500Z` (15:42:38.500 +07). The previous rollout helper's `windows_restarted:false` belongs to its earlier observation; it has not been rewritten. This continuation uses `postreboot-runtime.jsonl` with a new boot observation and `windows_restarted:true`.

## Completed and proof

- Exact r4 candidate executable, app archive and bundled node-agent hashes matched the prepared receipt. Persisted old Host 6388 and Coding MCP 28604 were absent after reboot.
- Supported stopped census passed in 16.3 seconds, with no canonical-ledger mutation, no active execution resources, and pending RUN `95e909f0040a448faa9f1f3257e2ee2c` preserved. The same candidate was launched; no alternate runtime or gate bypass was used.
- Supported full-clean refresh progressed through HANDOFF and VERIFYING. Components, projection, workspace, device and revision checks passed while the central route awaited heartbeat.
- No connected-agent Python process existed after reboot. Supported packaged r4 agent started with the profile-derived root and no data-root override. Exact agent PID 15044/start token `134361827972487370` is live; heartbeat succeeded.
- Epoch `activation-mv3lbekh-30cb2a711387e84898df6da3b1a6fad1` reached READY at 16:00:21.258 +07. Fresh proof at 16:00:33.876 +07 and a later proof confirm admission open; fully, local, components, central and authority readiness all true; update incomplete false.
- Host 14880, UI 3716 and Coding MCP 2600 have matching process identities. Running/disk Coding MCP revision `63b08970ce899e7e950b2acb444369048921057234c8ef55f0719108c6922390` agrees across 148 files.

## Scope and remaining work

No server authority renewal, exec-policy installation, Sandbox launch, deployment or additional reboot was performed by this worker. Exact standing read/write policies were checked before agent start. Context/pilot expiry remains 16:26:24.008 +07; the agent is bounded to 200 iterations at 15 seconds and authority remains enforced by server/local policy.

The parent controller now owns Sandbox readiness proof, supported local exec-policy installation and one bounded command/test verification. This runtime checkpoint proves READY plus heartbeat; it does not itself prove command execution. Pending RUN acceptance remains pending. No source implementation files were changed.

Evidence: `postreboot-runtime.cjs`, `postreboot-runtime.jsonl`, and bounded connected-agent stdout/stderr files in this directory. The helper permits only this continuation's runtime/readiness/agent phases and verifies exact spawned-agent identity plus a succeeded heartbeat within 90 seconds before final proof.

## Exact exec follow-up at 16:11 +07

The first central command attempt, action `act_0dbe0e6b68a34afea0e93ca5e55e4b34`, attempt `try_b165ade7805f44249af6efe4f3b0321e`, entered UNKNOWN after the r4 exec bridge timed out. Its original node journal retains `CONTROL_PLANE_EXEC_TIMEOUT`; it captured no command/job handle and remains unchanged.

Read-only native-ledger observation independently found the exact request-derived idempotency key `cpex_448df604842b976cee7f2f66215209fca87d89cfb2a51cad955abde9`, command `lpEXvw0QYM4KAWZD0EAhw5nm`, job `a389ace9d0b04ee5888a80929e817966`. The job reached terminal `spawn_failed` at 16:04:14.358 +07 with `root_pid=0` and no process token; the idempotency record ended UNKNOWN with `SANDBOX_STATE_PHASE_FAILED` at 16:04:14.758 +07. The later native failure occurred after the bridge timeout. Fresh observations found zero active managed jobs and no WXC or Windows Sandbox host processes. The source plus focused performance trace imply phase `start` (`retryable=true`); the backend error code was not retained and remains unproven.

After the parent controller reviewed the exact evidence and authorized terminalization, `postreboot-runtime.exec-reconcile.py --submit` used the supported packaged node-agent receipt API to append a truthful terminal failed receipt. At 16:11:15.426 +07 the server acknowledged `rcpt_01ff7fded14b46b7bf72eacba5903391` with `failed`, `settled`, `replayed=false`. The code is `CONTROL_PLANE_EXEC_SANDBOX_START_FAILED_BEFORE_PROCESS`; no exit code or output success was invented. The original unknown journal byte hash `502d41b3422411a05c93dad38ec24d554262fade88a02d26d3d92757f9a3e0ce` is preserved. No command replay, writer release, task close, process kill or runtime restart occurred in this reconciliation wave.

The parent has prepared an r5 cold-start fix. `postreboot-runtime.r5-activation.cjs` is prepared and syntax/preflight checked only: r5 candidate/archive/node hashes match `exec-coldstart-candidate.json`, while exact r4 Host 14880 and Coding MCP 2600 remain live. No r5 activation occurred. Its future switch retires the exact old connected agent only at a completed iteration, then uses supported UI/runtime stop, guarded canonical census and candidate launch with pending acceptance preserved. Operator approval for the separately named r5 activation is still required by the parent's authority decision. Scope expiry remains 16:26:24.008 +07.

## Authorized r5 activation checkpoint at 16:16 +07

The owner subsequently authorized activating r5 and testing within the unchanged scope/deadline. The parent reviewed the helper's guards before execution.

- At 16:14:19, the first switch preflight refused `R4_CONNECTED_AGENT_NOT_QUIESCENT` while the agent was polling; no mutation occurred. A fresh observation showed completed iteration 48. The next switch retired exact r4 agent PID 15044/start token `134361827972487370` at 16:14:42 through the lifecycle identity API.
- Supported UI and manual runtime stop preceded the exclusive canonical census. At 16:14:54 it passed with all active execution/resource counts zero, no canonical-ledger mutation, and pending RUN `95e909f0040a448faa9f1f3257e2ee2c` preserved. The approved candidate spawned at 16:14:55.
- Supported full-clean refresh returned HANDOFF at 16:15:16.953. Epoch `activation-mv3lxw05-c20b330cb58f3edea4f421b9a65b0743` reached READY; fresh final proof at 16:16:02.189 confirms admission open, update incomplete false, and all local/components/central/authority/full readiness flags true.
- Exact r5 installation `f9558a082121b56759553627fc60ee93cf624a94e8a1082c32e65b92b153bd86` owns Host 1936, UI 852 and Coding MCP 9632 with verified process identities. The archive hash is `4e9c51c4952b5cc491f42a40859d0e78911356453643023ab740ec06343e6f62`; bundled node-agent hash `7ac20204eb742719db1665651e97d52add481b691ba1cfcca907f35fdfd9ff40` matches the tested candidate.
- New bound agent PID 10336/start token `134361837362242930` runs the exact r5 packaged Python/node-agent path with the profile-derived project root, no data-root override and 200-iteration bound. Iteration 2 completed with successful heartbeat at 16:15:53.757.

No policy or server authority change, Ubuntu deployment, additional reboot, command replay, primary commit or push occurred in this activation wave. The parent owns the distinct second command/test proof; r5 READY is not a test-pass claim. Exact authority still expires 16:26:24.008 +07. The prepared r5 helper and all activation/agent observations are retained in `postreboot-runtime.r5-activation.cjs`, `postreboot-runtime.r5-activation.jsonl` and its bounded agent log files.

## Final independent native observation at 16:19 +07

The parent controller reported the distinct r5 central test completed successfully with 4 PASS, 0 FAIL and exit 0, and the central task was closed. This worker then performed one focused read-only local verification; no command, Sandbox probe, runtime or policy mutation was repeated.

At 16:19:30.872 +07, exact action `act_2de8172636ef4cdba9e388c203855f6b`, attempt `try_432aaf41ae244fafb7ccb0f01e9555a0`, has local journal state/receipt `completed` and receipt submitted. The journal supplies exact command `FSp5DLd4i9tjmeFnBFTWTQzS` and job `21eeffeec3b1411daed1219ebaa5778e`. Read-only SQLite (`mode=ro`, `query_only=ON`) confirms that exact managed job belongs to `control-plane-exec-bridge`, lifecycle `exited`, metadata exit code 0 and finished timestamp 16:16:59.212 +07. Active managed-job count is zero. Payload output is 1,070 bytes; stdout SHA-256 `640e5dc0aad76b8144b243cefb2f901508a77e27923bfda2a7025664a1dba15a`, stderr is empty, and response digest is `3cd791a0e214943b08599adfab8e547e44d9529ed123f73fe315cb6947e16405`. Raw output was not copied into this checkpoint.

Fresh r5 identity/readiness proof at 16:18:48.695 +07 continues to confirm READY with admission open and unchanged Host 1936, UI 852, Coding MCP 9632 and agent 10336 identities. Agent iteration 9 completed; its heartbeat succeeded at 16:18:31.940 +07. The preserved pending RUN is still separate from this successful command receipt. This observation does not claim a full project suite or a new live write test.

Content-free evidence is retained by `postreboot-runtime.final-native.py` and the final records of `postreboot-runtime.r5-activation.jsonl`. No replay, acceptance action, process kill, service restart, authority renewal, commit or push occurred in this final observation.
