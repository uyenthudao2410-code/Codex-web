# Guarded Windows r11 transition

Root owns all runtime and server effects. This packet is local preparation only until root executes a mutation phase. Frozen r10 helpers and product sources are unchanged.

## Pins

- Repository `E:\Github\Tools-Codex-web`, profile `web-mcp-assistant`, HEAD `2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
- Candidate `initial-proof-1011-r11`; app.asar `2071c0c242bc4b24ebfc22ea21b5c4d066e018505061ebe299cd666c6d2e8a91`.
- Immutable parity receipt `cefbb4daaeda869629594ed311e685de10049ef07445766b73ae4a5113bc0666`; source freeze `3bd561909abf56126ae2a15cc65932181251a48a1a9d47779b506e1b6c359c63`; all 12 payloads rechecked before each mutation.
- Current r10 app.asar `c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9`; executable `6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f`.
- Binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`; device `72ceec2d-e3f2-472f-8e3c-99fffe053035`; workspace `workspace_dda1d78e9a21402aa6213f72af64f788` / `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`.
- Pending RUN `95e909f0040a448faa9f1f3257e2ee2c` SHA `a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590`; WAVE `c101beadfc6d4f2fbc13845052c84693` SHA `59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce`.

## Sequential root operations

Use absolute paths in production invocation. No phase automatically retries effects or rolls back server history.

1. `node transition-r11.cjs observe`: query-only sanitized descriptor/process/readiness/config/allowlist/canonical census/pending records and VM observation. Nonzero VM is reported as an activation blocker.
2. `node transition-r11.cjs freeze`: same observation plus one immutable `r10-observation-pin.json`. Existing pin is not overwritten. Save its SHA256 for every mutation invocation.
3. Close Ubuntu intake and obtain a fresh recovery receipt. Run `node_modules/electron/dist/electron.exe --user-data-dir=C:\Users\daoth\AppData\Roaming\web-mcp-assistant owned-cleanup-electron.cjs` with the shared flags below. This credential-only entrypoint creates no BrowserWindow or production mutex. Its userData and sessionData use the authorized profile's existing Windows crypto key; no key/Local State copy is made. It uses existing Electron SecretStore safeStorage and native supervisor control only. The token stays in memory. Boolean found/valid/unavailable/recovered/token-present diagnostics are emitted without payload. Existing `prepareCodeActivation` and `FullCleanActivation._prepareFence` start/observe one exact owned cleanup operation with a fixed deadline and require its confirmation before independent zero-VM proof. The cleanup phase alone accepts either exact Store395 or approved9cae recovery receipt. Reinvocation observes the same unexpired operation; it never starts a different cleanup attempt automatically.
4. Deploy approved Ubuntu9cae and obtain its pinned recovery receipt. Renew exact scope for 60 minutes and save the pinned renewal receipt.
5. `node transition-r11.cjs activate` with shared flags: retire the exact quiescent old agent if still live, suppress/stop the exact UI, IPC-stop native, then retire exact host under an exclusive canonical census and spawn r11. No arbitrary VM/HCS termination. Every effect rechecks process identities, canonical idle state, original pending records and zero VM. The old connected agent has no supported graceful stop command; exact PID/start-token retirement is used only when its last iteration is completed and all work counts are zero.
6. `node transition-r11.cjs policy` with shared flags and renewal flags: install metadata policy assignment with the exact renewed expiry. It does not install standing read/edit/exec policies.
7. `node transition-r11.cjs refresh` with shared and renewal flags: supported `full_clean_refresh`, `allowAcceptancePending:true`, no source checkpoint or semantic acceptance. Observe the same handoff via `status`; do not repeat refresh.
8. `node transition-r11.cjs agent` with shared and renewal flags: one bounded agent, 15-second interval, maximum iterations bounded by remaining authorized time (backoff can delay loop completion but cannot extend server action authority).
9. Root reopens scoped intake after server native heartbeat gates pass. `node transition-r11.cjs status`, then `proof`: prove genuine READY/admission, exact replacement identities, current revisions, heartbeat and original pending records. This transition proof precedes the new canary; it deliberately accepts only the original pending RUN set. Use a separate final census after the canary adds a new RUN/WAVE.

Shared mutation flags:

```text
--operator-approved-r11
--pin-sha256=<SHA256 of r10-observation-pin.json>
--server=<absolute fresh recovery receipt JSON>
--server-sha256=<SHA256 of that receipt>
```

Policy/refresh/agent also require:

```text
--renewal=<absolute exact renewal receipt JSON>
--renewal-sha256=<SHA256 of that receipt>
```

Recovery receipt: `ok:true`, `host:100.116.112.22`, `service:codex-control-plane.service`, exact source revision and binding, `admission:recovery`, fresh `observed_at_ms` (<10 minutes); `state` must have zero `queued_actions`, `accepted_actions`, `open_writers`, `open_tasks`, `target_unsettled_actions`.

Renewal receipt: same source/binding/service identity and recovery admission; exact root/profile; `expires_at_ms=requested_at_ms+3600000`, unexpired; flat or nested `policy_assignment` exact device/workspace/generation. The server assignment is authoritative. Local canary argv admission is reported explicitly; if not allowed, root must use an exact authorized policy delta before the canary.

## Evidence and verification

The helper appends content-free `transition.jsonl`; agent stdout/stderr are local evidence and must not be dumped without sanitization. Query/freeze may save nonzero VM evidence but cannot activate through it. The source module exports only cleanup, paths and sanitized error reporting for the isolated Electron entrypoint. Syntax checks passed for both CJS files. No live runtime, service, agent, VM, authority, acceptance, commit or push operation was performed by this preparation agent.

### Isolated Electron archive-read correction

Root's first cleanup launch at `2026-10-11T14:52:11.640Z` returned `ENOENT` before `r10_owned_cleanup_started`; no prepare operation was begun. The root-controlled diagnostic retry pinned the failure to Electron's ASAR filesystem redirection while hashing the complete archive (`sha` → `verifyCandidate` → `mutationGuard` → `ownedCleanup`). Sanitized diagnostics contain only syscall, numeric errno, basename, and stack basename/line/column; Error.message, first stack line, subprocess arguments and private output are excluded.

`owned-cleanup-electron.cjs` now sets `process.noAsar=true` before loading `transition-r11.cjs`. This affects archive-byte reads in the isolated helper only; it does not alter any production process or candidate bytes. Root owns the next launch after checking the newly recorded helper hashes. The preserved journal retains both earlier pre-effect failures.

At `2026-10-11T14:55:47.212Z` the same operation was pinned while independent VM observations were already zero. Preparation returned `COMPONENT_STOPPED` with no fence because the helper's new crypto profile could not read the live native credential. This is classified as a helper credential-context failure, not evidence the native process stopped. The worker now requires the explicit authorized `--user-data-dir` at launch and sets userData/sessionData to that same profile without a UI or mutex. It retains the exact original cleanup operation/deadline and the fence confirmation gate. [Electron43.2.0 source](https://raw.githubusercontent.com/electron/electron/v43.2.0/shell/browser/browser_process_impl.cc) binds Windows DPAPIKeyProvider to Local State loaded from DIR_SESSION_DATA; this supports the context diagnosis.
