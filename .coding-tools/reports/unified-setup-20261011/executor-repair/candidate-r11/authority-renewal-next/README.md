# r11 follow-up authority — local preparation only

Root executes this packet under the NEW explicit approval
`call_flEpmLChKJPZsbnlAAXR5byS` for the same Tools-Codex-web/DaoChienThang
scope for one additional 60-minute window. This lane did not invoke SSH,
API, deployment, restart, policy installation, execution or acceptance.

## Preserved old operation

The frozen common helper remains byte-identical SHA
`c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f`.
Its protected old owner marker is read, hashed and never rewritten. Actual old
phase is `authority_renewed`: the previous intake reopen failed. The old window
was `1791730996302` → `1791734596302` (22:03:16 → 23:03:16 Vietnam time).
Its context `ctx_9f4989c869534b9d9667a57b9095878e` and pilot
`pilot_779ba01094a04453819c5585f0b73769` remain history.

The new protected server directory is
`/home/svhome/.local/state/codex-control-plane/owner-operations/r11-initial-verification-next-60m`.
It is created only by explicit root `close --execute` with the new approval ID,
duration 3600000, fresh service/state/grant pins and old/new marker SHA pins.
It never reanchors the old marker or an expired new window.

## Root phases

`root-ssh-next.py` reuses the exact frozen STAGE/INVOKE and public-receipt parser
from `activation-server/root-ssh.py`, SHA
`d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba`.
It stages only two pinned Python helpers in a fresh protected
`incoming/r11-approved-<UTC>` directory; there are no release archives.

```text
root-ssh-next.py stage
root-ssh-next.py observe --remote-dir <returned exact directory>
root-ssh-next.py close --remote-dir <directory> --execute --operator-approved --approval-id call_flEpmLChKJPZsbnlAAXR5byS --approved-duration-ms 3600000 <fresh six pin flags>
root-ssh-next.py observe --remote-dir <directory>
root-ssh-next.py renew --remote-dir <directory> --execute --operator-approved --approval-id call_flEpmLChKJPZsbnlAAXR5byS --approved-duration-ms 3600000 <fresh six pin flags>
```

The six flags come from an observe receipt younger than 60 seconds:
`--expected-service-instance`, `--expected-state-sha256`,
`--expected-grant-sha256`, `--observed-at-ms`,
`--expected-prior-marker-sha256`, `--expected-next-marker-sha256`.
For the first close, the next-marker pin is the literal `absent`.

Before any authority operation, the frozen common guard requires all target
actions/tasks/writers quiescent and unchanged historical action families.
Reconcile an unfinished canary before renewal. `close` moves intake to recovery
and terminalizes only expired exact-target contexts/pilot through supported API.
It blocks if recovery's global revocation would alter any unrelated pilot.
It creates the new marker without starting its clock.

Root may finish Windows runtime preparation before `renew`. `renew` anchors its
new exact 60 minutes once immediately before new context/pilot creation. The
unchanged service grant must cover the full window. A retry can adopt one exact
already-created row, but an uncertain missing creation outcome blocks replay.
It emits `policy_assignment` for root's separate exact-profile policy step.

After policy installation and a fresh current ready node observation, root uses
another observe and invokes `reopen` with the same six pins and:
`--expected-activation-epoch`, `--expected-runtime-instance`,
`--expected-mcp-instance`, `--expected-contract-version`.
Reopen verifies exact context/pilot identity and 60-minute expiry. Node standing
policy telemetry has a separate 60-second heartbeat TTL: it must be an integer,
strictly later than overview observation and at most last-seen + 60000.
It opens only scoped pilot; no deployment, restart or grant scope change occurs.

SSH uses BatchMode, strict host-key checks, connect timeout 15 seconds and
keepalive. Overall timeout is 600 seconds. A timeout/missing public receipt saves
an exclusive content-free unknown-outcome receipt and requires read-only marker
inspection, never automatic retry. Stderr and partial raw stdout are not saved.

## Proof

`python -B test-renewal-next.py`: 9 offline cases pass. Cases cover delayed single
anchor/no duplicate/no grant change, unrelated-pilot denial before recovery,
uncertain creation no replay, lost-response row adoption, unrelated authority
history mutation, actual previous `authority_renewed` phase, expired standing TTL
and wrong context denial, strict binary two-helper transport, and timeout receipt.
Fixtures use mocked API/SSH, not the live server or Windows runtime.

Git is dirty `main @ 2c554f59…`; all concurrent work and previous reports remain.
No commit/push/release and no live RUN/WAVE/Job or external effect was performed.
Root owns the live receipts, policy installation, intake reopen and acceptance.
