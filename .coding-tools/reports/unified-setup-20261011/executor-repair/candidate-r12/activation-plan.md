# r12 activation and one new edit → test → proof trial

Prepared on 12 October 2026 (+07). Root owns all live effects and final go/no-go.
This document is preparation, not an activation receipt or permission grant.
The repository remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
Concurrent source changes and all historical evidence remain preserved.

## 1. Exact target and immutable candidate

| Item | Pin |
| --- | --- |
| Windows device | `DaoChienThang` |
| Profile | `C:\Users\daoth\AppData\Roaming\web-mcp-assistant` |
| Repository | `E:\Github\Tools-Codex-web` |
| Binding | `bind_3e05bf64cb3e4bab93d930ae1692bebb` |
| Device ID | `72ceec2d-e3f2-472f-8e3c-99fffe053035` |
| Workspace | `workspace_dda1d78e9a21402aa6213f72af64f788` |
| Generation | `generation_c2f13e8d02344cf6a38a3f42ecfa59b6` |
| Candidate | `policy-contract-1012-r12` |
| Package root | `E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-policy-contract-1012-r12\win-unpacked` |
| `resources\app.asar` SHA256 | `2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1` |
| `Coding Tools MCP.exe` SHA256 | `797d4d00d855c05da17117471816ebafc7e2b3397d09c738eea49cf7368bfbb8` |
| Packaged `resources\resources\native-python\python.exe` SHA256 | `4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a` |
| `source-freeze.json` SHA256 | `dcdeaf4a8c49b5451dea2a239e4f512854edb3ba9b0117d021c5cbc15d2d6069` |
| `candidate-parity-20261011T172955204Z.json` SHA256 | `048a983e472ea5c322f939bf67a1cf88f43125861337bdbf2191d0a59074b86d` |
| `packaged-smoke-receipt.json` SHA256 | `8ea704d1491359c8fdd3ca397b6a6fc4bd784d528179a5203cff810d6560ea44` |

The [parity receipt](candidate-parity-20261011T172955204Z.json) proves 15/15
relevant packaged payloads match the frozen source. The
[isolated packaged smoke receipt](packaged-smoke-receipt.json) proves healthy
test-owned Recovery Host/MCP, exact resources and adapter, eight `smart-v3`
tools, fail-closed supervisor checks, cleanup and unchanged production descriptor.
The [source proof](../policy-contract-recurrence-20261012/source-proof.json)
records 33 JavaScript and three Python tests, syntax and scoped whitespace checks.
These are local package/source results; production READY and a live canary are
still unproven.

Ubuntu remains the existing destination `svhome@100.116.112.22`, user service
`codex-control-plane.service`. Last verified source revision was
`9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c`
with schema 29 and instance `cp_339c7a19bc2443eeab35583addfef543`.
Reobserve those values; they are expectations, not reusable current receipts.
This packet includes no Ubuntu deployment, service restart, Windows reboot or
persistent task/service installation.

## 2. Scope and old state that must remain intact

Root must obtain one new explicit authorization covering this r12 profile
activation and the same exact repository read/edit/exec scope for 60 minutes,
including context/policy/scoped-pilot renewal, controlled intake close/reopen,
local policy installation and one new canary. Record its actual approval identity
in a new immutable operation packet. Old r11 authorization expired at
`1791739329910` (12 October 00:22:09.910 +07); it cannot authorize any new effect.

Protect these historical acceptance-pending records throughout activation and
canary cleanup:

- RUN `95e909f0040a448faa9f1f3257e2ee2c`, row SHA256
  `a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590`.
- WAVE `c101beadfc6d4f2fbc13845052c84693`, row SHA256
  `59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce`.
- Existing canary fixture/checker preimages, frozen action/intent/owner markers,
  previous contexts/pilots and rejected or unfinished trial receipts.

Do not reuse or rewrite a frozen r11 helper, marker, approval, deadline,
idempotency key or action. Derive distinct r12 operation directories and helpers,
pin their hashes, and retain the old packets byte-for-byte. A fresh observation
must establish whether any old work remains unfinished; reconcile the exact
unfinished work before changing authority or replacing its runtime.

The prepared server lane names its new owner directory
`/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m`
and separate `canary` child. Pin their actual absence/current marker state before
creation; an exclusive directory/marker receipt must establish ownership. These
paths in this plan do not assert that any server directory has been created.

## 3. Why agent bootstrap precedes final READY

The source supports two different gates:

1. **Bootstrap gate:** the registered same-user agent may publish a conservative
   authenticated heartbeat while the exact activation epoch is admission-closed.
   This supplies fresh central connectivity and local-policy evidence.
2. **Execution gate:** final activation and each code action still require exact
   native identity, current epoch/source/runtime and action-specific authority.

Source basis:

- `control-plane/control_plane/node_agent.py:6012` publishes runtime heartbeat
  even when aggregate readiness is degraded/blocked. At that point it reports
  `unreported` native identities; it does not invent a READY identity.
- `node_agent.py:2246` validates the authenticated server echo for the same
  device/endpoint/credential generation/readiness and exact policy observation,
  then writes credential-free `control-plane-route-evidence.json` atomically.
- `electron/services/controlPlaneRouteEvidence.js:98` allows a fresh authenticated
  route observation to be connected when its runtime readiness is degraded or
  blocked. `authorityReady` requires enabled, unexpired observed local policy.
  Evidence older than 60 seconds, a wrong device or malformed values are rejected.
- `node_agent.py:7770` runs heartbeat before effect-lane admission/polling.
  Missing/disabled lanes are skipped; enabling the loop grants no capability.
- `electron/services/fullCleanActivation.js:2680` independently requires fresh
  `CENTRAL_ROUTE_READY` for central final census while admission is still CLOSED.
  All native/component/epoch/source gates remain required before commitReady.
- `resources/recovery-supervisor/recovery-supervisor.ps1:297` also invokes the
  connected agent before host-health work. Its normal unbounded argv is not the
  bounded trial launcher described here.

Therefore a bootstrap launcher must not require `fullyReady=true`, final epoch
READY, `identity_current=true` or a READY heartbeat before launching the agent.
Starting the agent alone does not prove any of those final predicates.
There is no supported `ControlPlaneEnrollmentService.startConnectedAgent`
method; use the shipped `run-connected-agent` CLI.

## 4. Root-owned sequential operations

### A. Pin and close intake under the new approved packet

1. Recheck candidate bytes and 15/15 source parity immediately before effects.
   If source or package drifted, stop and produce a new freeze/proof; do not
   silently activate a different candidate.
2. Observe sanitized profile descriptor, exact PID/start token/executable/user,
   UI/native/Recovery MCP/agent identities, activation epoch/admission, current
   source revisions, local policies, registration and canonical work census.
   Freeze one new observation and its digest. Do not assume the previously seen
   r11 Host PID20400 is still current.
3. Obtain a central observation less than 60 seconds old: actual service
   instance/revision, exact binding/node/workspace/generation, relevant authority
   rows, intake and zero target queued/accepted actions, tasks and writers.
   Preserve unrelated pilots and history. Close intake through the reviewed
   authority helper using fresh service/state/grant/prior/new-marker pins.
4. Require the independent local canonical census to show no active commands,
   starting commands, tool calls, agent lanes, managed processes, unexplained
   work or resource residue. Prove zero VM through supported ownership-aware
   cleanup if necessary. Never kill a VM, process or tree by name.

### B. Controlled Windows package transition

1. The new `activation-windows` helper must record each effect intent before
   performing it, recheck exact old process identities and quiescence at every
   boundary, and preserve historical acceptance-pending hashes.
2. Retire only the observed exact quiescent old agent if one exists; suppress
   and stop the exact UI, stop native through authenticated Recovery IPC, then
   retire the exact old Host as permitted by the frozen operation.
3. Launch one r12 Host for the authorized profile. Reconcile its actual
   PID/start token/executable/user/descriptor/authenticated IPC after the launch
   session returns. Do not create a second Host on timeout or missing receipt.
4. If using the diagnosed native Windows PowerShell WMI pattern, explicitly
   use native WindowsPS module paths, import CimCmdlets and use .NET archive
   hashing. A generic refusal does not prove Create ran. Record the failing
   stage and `create_invoked/create_returned` separately.
5. `IsProcessInJob=true` alone is not a failed launch or permission to kill it.
   Prove exact identity, health and survival after the launcher exits. If Job
   ownership/durable supervision is unknown, report that limitation; a bounded
   trial does not establish service-grade supervision.

### C. Anchor one new 60-minute window and install exact local policies

1. Prepare Windows transition before anchoring the authority clock where safe.
   New `renew` anchors `requested_at_ms` once immediately before creating the
   exact new context/pilot; require `expires_at_ms=requested_at_ms+3600000`.
   Do not reanchor an existing or expired marker or expand the service grant.
2. Obtain fresh principal-specific facade authority for the exact target and
   save its schema/profile/hash triple. Do not use the historical facade triple
   or the separate native tool-contract digest as substitutes.
3. Install the metadata assignment and existing standing file-read,
   approved-patch and exec policies with the supported packaged installers.
   Preserve target, owner/device/endpoint, roots/path scope, limits, allowlist,
   authority mode and sandbox gates; change only the newly authorized expiry
   and exact fresh facade contract needed by this renewal.
4. Reinspect installed policies and compare their triples with an authenticated
   authority observation less than 60 seconds old. Confirm the exact canary
   argv below is already admitted. A missing argv permission is a typed blocker,
   not justification for broadening the allowlist implicitly.

### D. Bootstrap one bounded registered connected agent

Perform this before final central READY. Gate the launch on exact r12 package
and profile, valid enrolled config, registered workspace/generation and the
approved unexpired policy/window. Intake remains closed and the canonical
effect census remains quiescent. No final native READY identity is required by
this bootstrap gate.

Use one supported packaged CLI invocation with absolute verified paths:

```text
<r12>/resources/resources/native-python/python.exe -B -I -u
  <r12>/resources/resources/control-plane/node_agent.py run-connected-agent
  --config C:/Users/daoth/AppData/Roaming/web-mcp-assistant/control-plane-node.json
  --workspace-registry C:/Users/daoth/AppData/Roaming/web-mcp-assistant/control-plane-workspaces.json
  --project-root <r12>
  --node <r12>/Coding Tools MCP.exe
  --runtime-mode packaged
  --interval-seconds 15 --max-backoff-seconds 60
  --max-iterations <frozen explicit positive count>
```

Here `<r12>` is the exact package root from section 1. Set working directory to
that root, use sanitized enrollment environment and hidden execution. Save
stdout/stderr as local evidence without printing tokens, config contents or raw
sensitive output. Pin the count before launch; it must be positive and bounded
by the remaining approved window's planned 15-second attempts. `max_iterations`
bounds attempts, not wall-clock duration: transport/runtime delays and backoff
can extend loop lifetime. Expiry still gates every capability action; do not
claim the loop stops exactly at the authority deadline.

Before launching, inspect the config's connected-agent lock and actual status
PID/start identity. The CLI owns exclusive-lock validation and only reclaims a
definitely dead lock. If an exact agent is already live, observe/adopt its
recorded launch rather than spawn another. A launch timeout is an unknown
outcome requiring status/lock/identity reconciliation before any next effect.

Confirm credential-free status reports the launched PID/agent instance, a fresh
successful heartbeat and no unexplained error. Confirm route evidence belongs
to the exact device/endpoint and current policy digest/expiry, is less than
60 seconds old, and evaluates `connected=true`, `authorityReady=true`,
`reason=CENTRAL_ROUTE_READY`. A conservative degraded/blocked runtime heartbeat
at this stage is expected and must not be relabeled READY.

### E. Supported full refresh, final identities, then scoped reopen

1. With bootstrap running and route evidence fresh, issue one supported
   `full_clean_refresh` under the frozen new operation, `sourceCheckpoint:null`
   and `allowAcceptancePending:true`. Observe the same HANDOFF/operation to
   completion. Do not repeat refresh or use `runtime.start` to create native
   under a terminal prior READY/READY_COMMITTED/FAILED epoch.
2. If a new refresh was already issued before bootstrap under this operation,
   observe that same in-flight handoff; do not create another epoch merely to
   change the ordering. After bootstrap route evidence is fresh, the supported
   `runtime.complete_activation_epoch(existing_epoch_id)` may finish that exact
   VERIFYING epoch if background completion has not finished. Recovery Host
   routes this through `fullCleanActivation.finalize(id, finalCensus(id))`;
   native/component/source/admission gates are still enforced. A different or
   terminal epoch is not authority to bypass the census.
3. Require final exact r12 Host/UI/native/Recovery MCP identities and the same
   new epoch, current running/disk revisions, validated workspace/device/source,
   READY with admission open and `updateIncomplete=false`. Authenticated native
   observation must have `mcp_ready=true`, `identity_current=true`, exact current
   epoch/process/server identities and its own tool-contract digest.
4. Wait for the same agent's post-READY heartbeat to publish those exact native
   identities, central node readiness READY and fresh policy telemetry. Use an
   actual observation less than 60 seconds old for native and central pins.
5. Reobserve authority/service state and reopen only the exact scoped pilot
   using the new context/pilot/marker and current activation/runtime/MCP/contract
   pins. Do not open a wider intake to work around a failed readiness gate.
6. Save transition proof and a quiescent census before adding the new canary
   RUN/WAVE. Historical pending records must still match their protected hashes.

## 5. One new canary with a 12-minute dispatch gate

Prepare a separate immutable r12 trial after transition proof. Adapt the prior
canary helper into a new operation directory, with new task/patch/action intent
and idempotency keys bound to current source/package/runtime/service/authority
pins. Preserve the prior rejected canary and its internal contexts as history.
Do not dispatch until the r12 helper actually enforces this stronger gate:

```text
expires_at_ms - current_server_time_ms >= 720000
```

This is the internal action-context lifetime of 600000ms plus a 120000ms margin.
The old helper's 120-second gate is insufficient. If less than 12 minutes remain,
do not dispatch; prepare a separately authorized fresh trial window.

Before the single dispatch require:

- Current native receipt and central heartbeat less than 60 seconds old; exact
  epoch/process/server/native contract and principal-specific facade pins.
- Exact fixture/checker preimages and proof plan, unchanged protected old
  RUN/WAVE rows, zero active canonical work/VM and exact target authority.
- Exact command `argv=["node","--test","tests/fixtures/initial-proof-canary-check.cjs"]`,
  `cwd=""`, timeout `60000` and output bound `32768`, admitted by existing exec
  policy. Keep the Sandbox gate and its ownership-aware resource handling.
- Fresh immutable task/patch/action intent and the exact current authority marker.

Use prepare → stage → preflight → **one dispatch** → read-only observe → settled
cleanup. Unknown dispatch outcome requires causal receipt/intent reconciliation;
never replay it automatically. Any exemption for the new action's own internal
context must prove its exact request/owner/full target/action and 600000ms
lifespan, with no unrelated action/request. Unrelated live authority still blocks.

On durable Job completion, immediately read retained output through supported
`command_control action=read`. Capture complete bounded stdout/stderr within
300 seconds of completion, before ExecSession retention expires. Keep output
receipts local and report only allowed summary/digests. Prove:

- Durable Job terminal exit 0 **and actual TAP 4 pass / 0 fail**, rather than
  inferring test count from exit status.
- Exact central task/action, native command/Job, ProofLedger initial verification,
  new RUN/WAVE, source pre/postimage/checker/plan, input and aggregate fingerprints,
  current native runtime identities and submitted node receipt agree causally.
- Settled exact central task and writer cleanup, zero active Job/VM/unexplained
  work and unchanged historical acceptance-pending rows.

Preserve new native semantic acceptance pending. A central MCP service trial is
not a genuine native ChatWeb call and cannot prove or perform native ChatWeb final
acceptance. Do not fabricate headers/attestation, use a Console verdict as a
substitute, or self-accept historical/new RUNs.

## 6. Stop conditions and final checkpoint

Stop the next effect and save a content-free reconciliation receipt for any
wrong target, source/package/helper drift, unknown launch/dispatch outcome,
changed PID/start identity, unexpected live owner/agent/VM/work, expired authority,
unrelated pilot/context mutation risk, policy/contract mismatch, stale heartbeat,
incomplete final epoch census or insufficient 12-minute dispatch margin.
Leave intake closed when the next safe step is unresolved; report its exact
state and blocker. Do not weaken a gate, erase evidence or repeat an unchanged
failed plan to obtain READY.

Every material phase ends with an operator-visible checkpoint: completed work,
Git and external/runtime state, strongest proof, typed blocker, remaining work
and exact next action. Final reporting must distinguish source tests, isolated
packaged smoke, controlled production READY, live edit/test/proof and native
ChatWeb acceptance. State active Jobs/agents/VMs and any supervision uncertainty.

### Outstanding packet fields before root execution

- Actual new r12 approval identity and immutable authority operation directory.
- Fresh profile/process/epoch/service/state/grant/registration observations;
  old/next-marker digests and approved 60-minute window/context/pilot identities.
- Reviewed/hash-pinned r12 transition/renewal/canary derivatives, including
  bootstrap-first admission and the enforced 720000ms canary gate.
- Fresh principal-specific facade authority and separate native tool-contract
  identity. Historical contract values are insufficient.

This plan performed no IPC/SSH mutation, authority change, runtime launch,
service operation, deployment, acceptance, commit, push or release.
