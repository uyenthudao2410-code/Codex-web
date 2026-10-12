# r13 transition: replace one pilot within the existing window

Prepared read-only against preserved deployed revision
`9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c`.
No external effect was performed by this lane. Root may operate the prepared
packet only after the user's explicit r13 runtime transition and pilot rotation
approval, recorded under the stable marker `r13-same-window-transition`.

Keep context `ctx_d7a539dd85264a62951fddad0ffa2f23`, requested time
`1791747735200`, and expiry `1791751335200` unchanged. Replace only old pilot
`pilot_98c0b502568a4f888b3106838004c117` through the supported API.

## Concrete conflict

Deployed `Store.set_admission_mode`, lines 1623–1658, accepts only `open`,
`recovery`, and `scoped_pilot`. Selecting `recovery` unconditionally revokes every
unrevoked pilot, even when admission is already `recovery`. The HTTP route
`POST /v1/maintenance/admission`, lines 1693–1697, forwards only `mode` and has no
preserve flag. Selecting `scoped_pilot` again leaves intake open. Therefore the
requested server pause/reopen cannot preserve the exact pilot through this API.

`prove-supported-admission.py` executes the exact AST method from the preserved
artifact against an isolated in-memory SQLite fixture. It proves recovery
revocation from both starting modes, no pause from repeating `scoped_pilot`, and
rejection of `paused` and `suspended`. It does not import/start a service or access
credentials, runtime, authority, or live databases.

## Prepared sequence

Keep consumed r12 intents and its original marker unchanged. New remote evidence
is confined to `/home/svhome/.local/state/codex-control-plane/owner-operations/r13-same-window-transition`.
Its new canary directory is `canary-r13`; r12 evidence is never replayed.

1. Root runs read-only `observe` after the exact r12 rejected receipt is settled,
   task closed and writer released. Common guards require zero target unsettled
   actions, writers and tasks while preserving quarantined historical families.
2. After r13 approval, root runs `pause-rotate` once using that fresh receipt.
   Recovery revokes only the exact old pilot, after a guard rejects any unrelated
   unrevoked pilot. Then create exactly one replacement pilot in recovery with
   the same context and expiry. No new context or policy is created.
3. Root runs `observe` immediately before each Windows effect; the receipt must
   be younger than 60 seconds. The immutable rotation receipt is the Windows
   renewal/authority pin; observations are the fresh server pins.
4. Windows owner performs the explicitly approved r13 transition and proves its
   exact live node identity. Root observes again, then runs `reopen` once with
   those exact node fields. Only admission changes to scoped pilot.
5. Observe once to verify scoped intake, replacement lineage and unchanged
   history. A future canary is separately prepared in its new namespace.

Every operation requires at least 12 minutes remaining. The helper never extends
or reanchors the window. It contains no stage, deploy, service restart, context
create or policy write path. Do not select recovery again after the replacement
pilot is created, because that would revoke it.

## Root commands

Use one exact Python executable path already resolved by root, rather than an
array from `Get-Command`. These are individual commands; no orchestration wrapper.

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r13/intake-transition/root-intake-ssh.py observe

python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r13/intake-transition/root-intake-ssh.py pause-rotate
  --execute --operator-approved --approval-id r13-same-window-transition
  --server ABSOLUTE_FRESH_OBSERVATION --server-sha256 ACTUAL_SHA256

python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r13/intake-transition/root-intake-ssh.py reopen
  --execute --operator-approved --approval-id r13-same-window-transition
  --server ABSOLUTE_FRESH_OBSERVATION --server-sha256 ACTUAL_SHA256
  --activation-epoch EXACT_NEW_EPOCH --runtime-instance-id EXACT_NEW_RUNTIME
  --mcp-server-instance-id EXACT_NEW_MCP --contract-version EXACT_NEW_CONTRACT
```

Transport streams the hash-pinned helper to memory over SSH and uses frozen
protected environment/receipt helpers. It saves exclusive local effect intents;
remote phase/intents also forbid retry. Partial outcomes require exact read-only
observation. Never delete an intent or retry an ambiguous mutation.

## Receipt contract

Rotation/fresh recovery receipts expose `next_phase=authority_rotated_in_recovery`,
`approval_id=r13-same-window-transition`, exact context/requested/expiry,
new `pilot_id`, `old_pilot_id`, positive `old_pilot_revoked_at_ms`,
`replacement_pilot_live=true`, `old_pilot` and `replacement_pilot` summaries,
immutable `prior_marker_sha256` and current `next_marker_sha256`, target,
`policy_assignment`, service/release/state/node pins. Reopen advances only the new
marker to `intake_reopened` and adds exact node identity fields. The rotation
receipt remains immutable for Windows authority lineage.

## Validation

Preserved deployed AST contract proof passes. Three offline tests cover the full
mocked supported API sequence, exclusive replay refusal, exact old/new pilot and
context history guards, and the 12-minute boundary. Syntax checks pass. Mock
Windows tests emulate Linux file flags only inside their fixture.

Git remains dirty `main @ 2c554f59…`. This lane changed only new files under
`candidate-r13/intake-transition`; no commit, push, deploy, restart, or API effect.
