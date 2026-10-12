# Exact approved r13 authority: one new 5-hour window

Human approval `call_a60e931056bd402b997c6c10b0796d81` includes r13 activation,
pause/reopen, one MCP trial and a 5-hour duration. Root alone executes effects.
This new packet preserves the unexecuted same-window r13 packet and all r12
history. It contains no deployment, service restart, reboot or grant expansion.

Deployed revision `9cae1044…` supports the duration: context creation requires a
future absolute expiry; pilot creation allows up to 24 hours. The helper requires
the unchanged service grant to cover all `18,000,000 ms`; insufficient coverage
is a typed refusal, never an implicit grant extension.

Old r12 marker is immutable SHA `a3c5c2ee239644a3937fa5f81c7fc14b89544bfde82c4bea56a928ddda408487`.
Its exact rejected action/task/lease cleanup is required before authority effects.
Only expired contexts for the exact binding may close and only the old r12 pilot
may revoke. Supported recovery revokes old pilot once; no unrelated unrevoked
pilot is permitted. New context/pilot share one new expiry, anchored once just
before context creation. Retries cannot reanchor or duplicate creation.

New remote namespace:
`/home/svhome/.local/state/codex-control-plane/owner-operations/r13-initial-verification-5h`.
Marker `authority-renewal-public.json`; canary child `canary`. Original marker,
grant, scope, source/release, action/task history remain pinned. The copied common
helper changes only renewed-authority duration validation from 1 hour to 5 hours.

## Root sequence

Resolve one exact Python executable. Let `C` be this directory. Individual commands:

```text
python -B C/root-ssh-r13-5h.py stage --execute --operator-approved
  --approval-id call_a60e931056bd402b997c6c10b0796d81 --approved-duration-ms 18000000
python -B C/root-ssh-r13-5h.py observe --remote-dir EXACT_RETURNED_DIRECTORY
```

Stage transfers only two hash-pinned helper files to a fresh protected incoming
directory; no server source/deploy artifact is transferred. For each effect use
the immediately preceding observation, younger than 60 seconds:

```text
python -B C/root-ssh-r13-5h.py close --remote-dir EXACT_DIRECTORY --execute --operator-approved
  --approval-id call_a60e931056bd402b997c6c10b0796d81 --approved-duration-ms 18000000
  --expected-service-instance S --expected-state-sha256 STATE --expected-grant-sha256 GRANT
  --observed-at-ms OBSERVED --expected-prior-marker-sha256 PRIOR --expected-next-marker-sha256 NEXT

python -B C/root-ssh-r13-5h.py renew [SAME_FLAGS_FROM_NEW_OBSERVATION]
```

`close` leaves recovery intake and closes only expired target authority. `renew`
starts the 5 hours once and creates exactly one context/pilot while recovery.
Save its immutable `r13_5h_authority_renewed` receipt for the Windows policy and
authority pin. Root observes before every Windows transition effect. After the
approved Windows r13 activation proves exact READY identity:

```text
python -B C/root-ssh-r13-5h.py reopen [SAME_FLAGS_FROM_NEW_OBSERVATION]
  --expected-activation-epoch EPOCH --expected-runtime-instance RUNTIME
  --expected-mcp-instance MCP --expected-contract-version CONTRACT
```

Observe again and prepare the separate `canary-5h` trial from the actual reopened
receipt. Never run recovery again after new pilot creation. Effect intents are
exclusive and consumed; ambiguous outcomes require read-only inspection.

## Receipt contract and validation

Operation `owner_approved_r13_initial_verification_5h`; effect phases
`r13_5h_intake_closed`, `r13_5h_authority_renewed`, `r13_5h_intake_reopened`.
Observation phase `r13_5h_read_only_observation`, `next_phase` mirrors marker.
Scope/host/service/revision, exact approval, `duration_ms=18000000`, dynamically
anchored `requested_at_ms`/`expires_at_ms`, new `context_id`/`pilot_id`, prior/new
marker digests, state/grant pins and `policy_assignment` match the tested r12
receipt shape. Context/pilot must differ from expired r12 IDs. No retroactive
start time or future IDs are invented.

16 focused offline tests cover 5-hour anchor once, full grant coverage denial,
unchanged history, unrelated authority refusal, lost-response no replay/adoption,
fresh telemetry, 12-minute canary margin and transport/exclusive intents. Syntax
checks pass. No live effect by this lane; dirty `main @ 2c554f59…`; no commit/push.
