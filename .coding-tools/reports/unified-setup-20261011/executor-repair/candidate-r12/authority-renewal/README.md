# r12 authority renewal — local preparation only

Prepared for root-owned r12 activation and one new edit → test → proof trial.
This packet has no live approval or effect receipt. Root must bind the future
explicit approval to the exact r12 package/profile, this renewal and one canary.
The deployed Ubuntu release is kept; this packet cannot deploy or restart it.

## Target and retained evidence

| Item | Exact value |
| --- | --- |
| Server | `svhome@100.116.112.22` |
| Service | existing user `codex-control-plane.service` |
| Windows profile | `web-mcp-assistant` on `DaoChienThang` |
| Root | `E:\Github\Tools-Codex-web` |
| Binding | `bind_3e05bf64cb3e4bab93d930ae1692bebb` |
| Device | `72ceec2d-e3f2-472f-8e3c-99fffe053035` |
| Workspace | `workspace_dda1d78e9a21402aa6213f72af64f788` |
| Generation | `generation_c2f13e8d02344cf6a38a3f42ecfa59b6` |
| New owner directory | `/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m` |
| New trial directory | the owner directory's empty `canary` child |
| Duration | one new `3600000` ms window, read/edit/sandboxed exec |

`r11_common.py` is copied unchanged, SHA256
`c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f`.
It validates the existing release revision/package/schema, exact registration,
grant and protected action/task history with no active central target work.
Root must independently prove zero native Job/VM/work before authority effects.
Central quiescence is not proof of Windows quiescence.

The immediately preceding r11 owner marker remains read-only at
`.../owner-operations/r11-initial-verification-next-60m/authority-renewal-public.json`,
SHA256 `e3d29f73b0395dd47ff46dd9bbb62831afce0a14183d23c2cd0ca88c5ceaf34c`,
phase `intake_reopened`, requested `1791735729910`, expires `1791739329910`.
All old markers/intents/action/task/RUN/WAVE records remain history. A new approval
identity must differ from `call_flEpmLChKJPZsbnlAAXR5byS`.

The frozen SSH STAGE/INVOKE/parser is read from
`candidate-r11/activation-server/root-ssh.py`, SHA256
`d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba`.
Its existing staging path family is `incoming/r11-approved-<UTC>`; the new r12
helpers use a new exclusive path in that family and a distinct r12 owner namespace.
Only two manifest-pinned Python helpers are transferred; `archives` is empty.

## Exact root phase sequence

From the repository, the driver is:

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r12/authority-renewal/root-ssh-r12.py
```

Append one action and flags. `<NEW_APPROVAL_ID>` is the actual future approval,
not a newly invented grant. Every mutation, including staging, requires:

```text
--execute --operator-approved --approval-id <NEW_APPROVAL_ID> --approved-duration-ms 3600000
```

1. `stage <approval flags>`: transfer only pinned helpers and retain the returned
   exact `remote_dir`. This does not open intake or create authority.
2. `observe --remote-dir <remote_dir>`: read-only observation.
3. `close --remote-dir <remote_dir> <approval flags> <six fresh pins>`:
   close intake to recovery, terminalize only expired exact-target contexts and
   the old exact pilot. Reject unrelated unrevoked pilots, live contexts, wrong
   targets and changed history. Create the r12 marker and empty private `canary`
   child; the new authority clock has not started.
4. Finish local read-only observation, source/package freeze and transition
   preparation. Windows activation requires the renewed server receipt; do not
   invoke the Windows transition before renewal.
5. Fresh `observe`, then `renew --remote-dir <remote_dir> <approval flags>
   <six fresh pins>`: anchor the new 60 minutes once, then create one exact context
   and pilot. The unchanged service grant must cover the entire new window.
6. Fresh `observe`: supply its complete authority receipt and the server renewal
   receipt with `policy_assignment` to the Windows helper. Activate the exact r12
   runtime, install exact local policies, bootstrap the bounded heartbeat agent
   while intake is closed, then finalize the same native activation epoch READY.
   Refresh or finalize the same existing VERIFYING epoch once, then obtain its
   current READY identity and authenticated server echo younger than 60 seconds.
   Follow `../activation-plan.md` and `../activation-windows/README.md`.
7. Fresh `observe`, then `reopen --remote-dir <remote_dir> <approval flags>
   <six fresh pins> <four current native pins>`: require the exact new context,
   pilot, READY identities and standing-policy telemetry before scoped intake.
8. Root's separate canary packet obtains fresh principal-specific facade/schema
   and authority observations before one new dispatch. The native contract digest
   and principal-specific facade contract are separate values.

The six pins come from an `observe` receipt younger than 60 seconds:

```text
--expected-service-instance <service_instance_id>
--expected-state-sha256 <state_sha256>
--expected-grant-sha256 <service_grant_sha256>
--observed-at-ms <observed_at_ms>
--expected-prior-marker-sha256 <prior_marker_sha256>
--expected-next-marker-sha256 <next_marker_sha256>
```

For first close, the exact `next_marker_sha256` is `absent`. Refresh all six
after each mutation; do not reuse stale state digests. Reopen also requires:

```text
--expected-activation-epoch <current node activation_epoch>
--expected-runtime-instance <current node runtime_instance_id>
--expected-mcp-instance <current node mcp_server_instance_id>
--expected-contract-version <current node contract_version>
```

Standing-policy heartbeat expiry must be later than the server observation and
at most node `last_seen_at_ms + 60000`. Its short telemetry TTL is distinct from
the 60-minute authorization expiry.

## Receipt contract and remaining-window gate

The transport retains credential-free receipts under `remote-receipts/`; the
server receipt is `public_receipts[0]`. After renewal, a fresh read-only `observe`
contains these top-level fields for Windows policy installation:

```text
host, service, observed_at_ms, service_instance_id, binding_id, device_id, workspace_id,
workspace_generation, root, profile, requested_at_ms, expires_at_ms,
context_id, pilot_id, capabilities={read:true,write:true,exec:true},
canary_directory, minimum_canary_remaining_ms=720000, admission,
next_marker_sha256, state_sha256, service_grant_sha256
```

Before renewal, the new window/context/pilot fields are null. Those receipts do
not authorize policy installation. Root must verify `next_phase=authority_renewed`
or `intake_reopened`, exact scope and fresh IDs before using a post-renewal receipt.

Reopen requires at least **720000 ms** left according to the actual server clock:
the existing standing-patch action/context/request TTL is **600000 ms**, with
**120000 ms** margin. The canary must independently recheck this gate immediately
before dispatch, even when reopen passed. A short or expired window blocks;
helpers never extend/reanchor it or widen the grant to make a trial pass.

The canary child is created only if absent, mode `0700`, under the private owner
directory. Existing empty safe child is accepted; unsafe paths, symlinks or
existing trial evidence block. Nothing is deleted or overwritten.

## Unknown outcomes and proof

Each transport mutation first writes exclusive `transport-intent-<action>.json`.
Do not rerun a mutation after its intent exists. SSH is BatchMode with strict
host-key checks, bounded connection/keepalive and overall timeout 120 seconds.
Timeout or missing/unsafe receipt produces a public unknown-outcome receipt,
preserves all evidence, and requires read-only exact marker/state reconciliation.
No raw stdout/stderr, protected configuration or token is disclosed.

Server creation intents also block duplicate context/pilot creation. Reconciliation
may recognize one already-created exact row after a lost response; the root driver
does not automatically replay that mutation. A new reviewed reconciliation step
must follow the actual observed outcome; never delete an intent to force a retry.

`test-authority-r12.py` is offline: mocked API/SSH and temporary local fixtures.
Its proof includes exact scope/history, once-only anchor and intents, missing
creation no replay, one exact lost-response row, strict two-file binary staging,
safe unknown outcomes, bootstrap child, full-window gate and serialization of
fresh observation fields without effects. The initial `local-proof-receipt.json`
and `README-pre-order-review.md` remain chronology. Use the final receipt when
present at `local-proof-receipt-final.json`; it binds the corrected phase order,
host/service receipt fields and current helper/README/manifest hashes.

Git remains dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f` with concurrent
work preserved. This lane changed only this new folder. No SSH/API, native Job/VM,
authority/runtime effect, commit, push, release, deployment or service restart
was performed. Root owns the future approval and all live receipts.
