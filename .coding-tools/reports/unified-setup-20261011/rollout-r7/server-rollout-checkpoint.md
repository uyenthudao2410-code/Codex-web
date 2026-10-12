# Frozen Console rollout checkpoint

11 October 2026, 17:19 +07. Local repository remains dirty `main` at observed
HEAD `2c554f59cb7b8ffc86ce5e0e28076c792777642f`; no commit or push occurred.

## Outcome and scope

The approved user service `codex-control-plane.service` on
`svhome@100.116.112.22` now runs the immutable Console snapshot
`5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f`.
This is a **content-addressed source snapshot**, not a claimed Git commit.
Its canonical identity and original Git release provenance are documented in
`snapshot-provenance.json`. Package source fingerprint:
`sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566`.

Exactly one of 38 payload files changed:
`control-plane/control_plane/web_ui.py`, frozen SHA-256
`03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b`.
All 37 other payload files are byte-identical to the retained
`beaa9d5ade4926ef231e3ec9d0a517fe93830e90` release. Only the derived release
manifest and protected deployment identity configuration changed in addition.
Schema remains 28. No broad dirty-checkout deployment occurred.

## Validation and service state

- Local and remote release integrity verifiers passed, 38 payload files.
- Frozen Python source syntax passed.
- Health reports the exact new package and expected package fingerprint.
- Fresh service instance `cp_d203277517b747e4b056ec0184d09709`, PID `806340`,
  started at `1791713953816`.
- HTTP HTML matches expected SHA
  `aa4e9bae769406dc789fdddd9df6e40d897221fa5aab64f0fa126a515b24a21c`.
- HTTP `/assets/control-plane-ui.js` matches expected SHA
  `0b9521f4b7afea5d4a34cfa89809506552b6733cf592543cdcbd49f3c80fdcef`.
- Intake remains **recovery**, closure observed at `1791713952634` in
  `server-intake-closed.json`.
- Queue, accepted actions, open writer leases and open tasks are zero.
- Actions 32, tasks 6, acceptances 1 are unchanged.
- Historical unresolved family remains 12 quarantined UNKNOWN reads and one
  explicitly fenced historical unobserved dispatch; family digest remains
  `825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed`.

## Resolved validation failure

The first attempt switched successfully, then its new postflight helper
incorrectly called `.encode()` on UI constants that are already bytes. The
guarded deployment rolled back to the original healthy release and retained
recovery intake. Original failure and rollback are preserved in
`server-deployment.jsonl`, with fresh observation `server-after-rollback.json`.

`ubuntu-console-reapply.py` fixes only this verification oracle, rechecks the
retained baseline/config/backup, verifies the already-extracted candidate and
reapplies the exact approved source snapshot. It does not overwrite/remove the
retained release or backups. Reapply passed; evidence is `server-reapply.jsonl`.

## Recovery and remaining work

Protected configuration and a verified SQLite snapshot remain only on Ubuntu:
`/home/svhome/.local/state/codex-control-plane/deployment-backups/unified-setup-r7-5ce5c51fc9758450`.
Snapshot SHA is
`bbcb2101512bb4a1d5c475134ae8e2fbe3f63390277d7372ea0744fcd7ca2e75`.
Original immutable release is retained for guarded rollback. No SQLite restore,
authority renewal, new grant, credential change, action replay, Windows reboot
or Windows activation was performed by this server worker.

## Same-scope renewal after confirmed Windows switch

Parent confirmed the Windows r7 initial host switch and issued the renewal
go-ahead. The prepared helper then completed the approved exact
Tools-Codex-web scope for **60 minutes**, from **17:20:33.341 +07** to
**18:20:33.341 +07** today (`1791714033341` to `1791717633341`).

- Binding: `bind_3e05bf64cb3e4bab93d930ae1692bebb`.
- Device: `72ceec2d-e3f2-472f-8e3c-99fffe053035`.
- Workspace: `workspace_dda1d78e9a21402aa6213f72af64f788`.
- Generation: `generation_c2f13e8d02344cf6a38a3f42ecfa59b6`.
- Context: `ctx_01ca575dd5fa46cc95432e8f5aa56848`.
- Pilot: `pilot_39a7fb99d6f7475db1e553383c3f3e2e`.

Existing service grant `mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd`, its
credential and scopes were preserved. The new private marker fixes the expiry
once and cannot extend it on retry. Only expired exact contexts were closed
through owner APIs. Intake reopened as `scoped_pilot` under that exact decision.

`server-authority-renewal.json` holds completion evidence.
`server-renewal-fresh-observation.json`, observed at `1791714058254`, confirms
healthy exact source snapshot, one matching context/pilot, zero queue/accepted
actions/open writers/open tasks, unchanged action/task/acceptance counts and
unchanged historical family digest. This worker still has not installed any
Windows policy or run a code canary.

Next action: parent synchronizes the matching Windows local policy, refreshes
runtime and verifies setup/readiness before the approved execution checks.

## Final read-only census after execution failure cleanup

`server-final-census.json`, observed **17:33:17.904 +07**
(`1791714797904`), confirms the immutable snapshot/service are still healthy.
MCP metadata operations `inventory` and `task_list` return the exact binding:
`online`, `ready`, `dispatchable`, policy `enabled`, registered capabilities
`read/write/exec=true`. Heartbeat age is 13 seconds. This readiness observation
does not prove successful command execution.

The live execution canary **failed** before a code process started. One attempt
for action `act_2673b93c5bb3483889742dfe3055fd3d` initially produced UNKNOWN at
approximately 128 seconds with `CONTROL_PLANE_EXEC_MCP_REJECTED`. Its sealed
command timeout is 300 seconds and server action TTL is 600 seconds, so the
UNKNOWN occurred before action or approved authority expiration. Native
terminal proof reported `SANDBOX_STATE_PHASE_FAILED` / `spawn_failed` with root
PID zero. Parent reconciled through the supported node receipt route; no
execution replay was performed.

The action is now `settled` with failed receipt
`rcpt_97a6b0ffb80149fd8f87c5d6b70e3182`, code
`CONTROL_PLANE_EXEC_SANDBOX_START_FAILED_BEFORE_PROCESS`, and no exit code.
Original UNKNOWN receipt `rcpt_420d659f8dac4aa1941b4c126acf7784` and its digest
remain intact. Exactly one delivery attempt remains. Task
`task_8982097843784d44bcc4bb0440c35141` is closed and its writer lease released.

Final counts are actions 35, tasks 7, acceptances 1; zero queued/accepted
actions, open tasks and open writers. Only the original 13 fenced historical
unresolved rows remain; family digest is unchanged. The exact approved
context/pilot expiry remains **18:20:33.341 +07**, with no further renewal.

No actions, receipts, tasks, policies, authority, deployment or services were
mutated by this worker after the authorized renewal. Final census is read-only.
Remaining blocker: Windows Sandbox startup failure. Next action belongs to
parent: fix and prove the local startup boundary before claiming exec works.
