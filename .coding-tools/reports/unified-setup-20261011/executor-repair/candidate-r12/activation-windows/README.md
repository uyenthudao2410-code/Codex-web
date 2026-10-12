# r12 Windows activation packet — local preparation

Root owns every runtime/server/authority action. This packet has not activated
r12, launched an agent, renewed authority, accepted a RUN/WAVE, restarted Ubuntu,
or rebooted Windows. It adds only files under this evidence directory.

## Frozen target and gates

- Candidate `policy-contract-1012-r12`, profile `web-mcp-assistant`, root
  `E:\Github\Tools-Codex-web`, device `72ceec2d-e3f2-472f-8e3c-99fffe053035`.
- Source HEAD remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
- Exact r12 package/source/parity pins are checked before each effect. Imported
  lifecycle dependencies must match both current source and the frozen package.
- Every effect requires explicit future r12 approval, a manifest pin, a fresh
  server recovery receipt observed less than 60 seconds ago, and a new unexpired
  exact 60-minute renewal. Old context/pilot/attempt identities are refused.
- Ubuntu remains revision `9cae1044…`, schema29; no deployment or service restart.
- Fresh exact r11 descriptor/host/UI/native/agent identities and query-only
  canonical census are frozen before the first effect. The historical pending
  RUN/WAVE row hashes are checked at each boundary and never accepted.
- Old components retire through supported IPC/UI stop and exact PID/start token
  termination only. VM/backend presence blocks; no process-name or VM kills.
- `runtime.stop` stops native MCP/tunnel. Recovery-plane children may survive
  exact old Host retirement until the one supported full-clean refresh stops
  them using product ownership receipts. Freeze/status/final receipts include
  sanitized Recovery MCP/tunnel/candidate PID/start token/instance/epoch and OS
  identities. Activation does not claim all old children exited. The unchanged
  product final census retains Recovery-plane freshness and same-epoch gates.
- Recovery supervisor manifests were absent at preparation. An installed
  supervisor appearing before an effect requires reconciliation. This packet
  cannot install a scheduled task or supervisor.
- Host and bounded agent use the proven WMI launch transport with Windows
  PowerShell's native module environment and allowlisted child environment.
  Host argv remains supported packaged Recovery Host argv. Child adoption checks
  exact PID/start token, executable/user, WMI parent and authenticated Recovery
  IPC. Job membership is an observation; no outside-all-Jobs claim or gate.
- Final proof requires launching tool processes to have exited while exact
  host/agent identities persist. This proves the observed lifetime boundary,
  not independent durable supervision. Agent iterations are bounded; backoff
  means the iteration bound is not a hard wall-clock expiry. Server grants and
  each action still enforce authority; root reconciles the exact agent at trial
  completion/expiry.

## Root sequence

Use one new attempt name `r12-<unique-id>` throughout. No old attempt directory
or phase intent may be reused. `<SERVER>` is the latest read-only `observe`
receipt from `../authority-renewal`, unwrapped automatically from
`public_receipts[0]`. It must contain `next_phase=authority_renewed` (or
`intake_reopened` for final proof), exact capabilities and schema29 census.
`<RENEWAL>` is the actual successful new `renew` receipt and remains immutable.

Driver:

```text
node .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r12/activation-windows/transition-r12.cjs <PHASE>
```

Append `--attempt=r12-<unique-id>` to every phase. First run `observe`; it is
query-only and emits exact fresh old identities. Then `freeze`, adding:

```text
--pin=<absolute new attempt directory>/r11-observation-pin.json
--expected-old-pid=<fresh observed PID>
--expected-old-token=<fresh observed start token>
--expected-old-epoch=<fresh observed epoch>
```

The frozen receipt must be less than 60 seconds old at the first effect. All
effect phases require these explicit pinned flags:

```text
--operator-approved-r12
--manifest-sha256=<helper-manifest SHA256>
--server=<absolute fresh SERVER receipt> --server-sha256=<SERVER SHA256>
--renewal=<absolute immutable RENEWAL receipt> --renewal-sha256=<RENEWAL SHA256>
```

`activate` additionally requires `--pin=<frozen pin>` and
`--pin-sha256=<frozen pin SHA256>`. Root first closes intake and renews through
the authority packet, then freezes/activates this packet under that new window.

1. `activate`: retire pinned quiescent r11 components, reserve one intent, WMI
   launch exact r12 Host, reconcile its descriptor/IPC and exact child identity.
2. Fresh server `observe`, then `policy`: install renewed metadata policy and
   reconcile the three standing policy facade contracts through supported
   packaged installers. Their noncontract limits/scope/allowlists remain exact.
   No new Sandbox probe is run. A partial install stops for inspection.
3. Fresh server `observe`, then `agent`: launch exactly one bounded registered
   `run-connected-agent`. It may bootstrap while epoch/admission is incomplete.
   `mcp_ready`, `identity_current`, aggregate READY and reported native IDs are
   deliberately not preconditions for heartbeat bootstrap. Exact package,
   profile, authenticated Host, registration, renewal and local policies are.
4. `status` until fresh authenticated route evidence is `CENTRAL_ROUTE_READY`.
   The route digest must match the installed standing lane projection and its
   short telemetry expiry, independently of the metadata trial expiry.
5. Fresh server `observe`, then **one** `refresh`: supported
   `full_clean_refresh`, no source checkpoint, pending acceptance preserved.
   A phase intent prevents replay and any second refresh.
6. `status` reconciles exact supported Host handoff. If the same epoch still
   needs finalization, fresh `observe` then `finalize` invokes supported
   `runtime.complete_activation_epoch` on that exact epoch once. It retains all
   product final census/identity gates; no extra refresh is used.
7. Wait for a new successful agent heartbeat after READY; fresh server
   `observe` then `proof` verifies exact native/epoch/UI revisions and the
   server's node echo `runtime_instance_id/mcp_server_instance_id/activation_epoch/
   contract_version`, observed less than 60 seconds ago. `proof` needs the
   server/renewal pin flags but performs no runtime effects.
8. Root may reopen exact scoped intake using the separate authority packet.
   Canary edit → sandboxed test → source-bound proof and genuine native ChatWeb
   acceptance are separate work, not claimed by runtime/package proof.

Any uncertain launch/effect or helper refusal means inspect the recorded exact
intent/child/descriptor state with intake kept closed. Do not replay a creation,
overwrite an intent, start another host, accept old work or fabricate READY.

## Local verification

`offline-check.cjs` exercises synthetic destination/freshness/renewal, standing
contract-only replacement and canonical pending/work gates without live runtime
effects. Node syntax, Windows PowerShell parsing and Python compile-only checks
are recorded in `local-proof-receipt.json`; package proof remains the existing
15/15 parity and isolated packaged smoke in the parent candidate directory.
