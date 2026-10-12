# r10 recovery intake: same expiry, supported replacement pilot

Prepared helper: `ubuntu-r10-same-expiry-recovery-intake.py`

Frozen SHA256: `8f260b9c43da8facda48d2a73c60b3ec298f104890e8ba9e181c1751fa482744`.

Stage alongside frozen `ubuntu-r10-store-authority-v3-local-proof.py`, SHA256
`a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec`.
The helper imports that sibling's pinned source/package/service/schema and
read-only retained-state inspection. It never writes the original v3 marker.

## Exact operation

Supported `maintenance/admission` recovery closes intake and revokes live pilot
decisions. A revoked decision cannot be reopened. The helper therefore creates a
replacement through the existing scoped-pilot API with the original scope and
expiry, then opens scoped-pilot admission. It does not renew or reanchor authority.

Window remains `1791722898491`–`1791726498491` ms
(2026-10-11 19:48:18.491–20:48:18.491 +07).
Original pilot: `pilot_25fa8c634f7f40e282c30a303b51bfd0`.
Context: `ctx_9e58c758a20249479b6ec806970f68ca`.
Binding: `bind_3e05bf64cb3e4bab93d930ae1692bebb`.
Service instance: `cp_6766892f5ada47d1862a0d24334f1116`.

The helper pins 38 actions, 10 tasks and 1 patch acceptance, retained historical
family and patch-acceptance digests, and the exact settled cold command/receipt/
task/context cleanup. Reopen requires a fresh recovered activation epoch, exact
native process/server/contract identities, ready node, enabled unexpired policy
and heartbeat newer than 60 seconds. A sole replacement matching the exact
reason and scope may be reobserved after response loss. No command is replayed.

## Root-owned execution

First obtain the observation, then use its exact hashes:

```text
python3 -B <helper>
python3 -B <helper> close --execute --operator-approved --expected-service-instance cp_6766892f5ada47d1862a0d24334f1116 --expected-state-sha256 <observation> --expected-authority-marker-sha256 <observation>
python3 -B <helper> reopen --execute --operator-approved --expected-service-instance cp_6766892f5ada47d1862a0d24334f1116 --expected-state-sha256 <observation> --expected-authority-marker-sha256 <observation> --expected-activation-epoch <recovered epoch> --expected-process-instance <native process> --expected-server-instance <native server> --expected-native-contract bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
```

Its own protected marker is
`/home/svhome/.local/state/codex-control-plane/owner-operations/r10-same-expiry-recovery-v1/intake-recovery-public.json`.
Stop on a refusal; leave intake closed until recovery evidence is complete.

## Receipt contract

Phases are `r10_same_window_intake_observation`,
`r10_same_window_intake_closed`, `r10_same_window_intake_reopened`.
Successful close/reopen receipts include:

- `observed_at_ms`: fresh final overview observation.
- `source_revision`: `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5`.
- `package_source_sha256`: `sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419`.
- `service_grant_preserved`: `mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd`.
- Exact service, binding, context, requested/expiry timestamps, retained state and
  its digest, original authority-marker digest and cold-family digest.
- `pilot_id` and `original_pilot_id`: original pilot for correlation.
- `newpilot_id`: null after close; exact replacement after reopen. Warm
  acceptance must pin this replacement while retaining original correlation.
- `activation_epoch`: recovered epoch after reopen.
- `authority_renewed`, `original_marker_modified`, `service_grant_changed`,
  `command_replayed`, `pending_acceptance_changed`: all false.

## Prepared proof and operation state

Original pure guard proof passed syntax, 2 positive and 7 negative cases. The
final helper adds receipt fields only; AST proof verifies their exact expressions
and frozen v3 identity without rerunning unchanged guard cases. See
`r10-same-expiry-recovery-final-proof.json` and final manifest.

This preparation performed no live SSH/API/service/runtime/authority operation,
source edit, commit, push or deployment. Root owns execution and live proof.
