# Closed schema29 recovery preparation

This is an **offline emergency observation/receipt recovery artifact**, derived from frozen Store395. It is not the r11 release or a generic production replacement. No deployment, SSH, grant renewal, service operation, Windows activation, database restore, commit, or push occurred in this lane.

## Identity

| Artifact | SHA256 / identity |
| --- | --- |
| Baseline Store395 source | `395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5` |
| Recovery source revision (content hash, not Git commit) | `81303f7cf4d006c5e6e2eeaffb578b57446b9dbd6730c9f34b2a7bec98b8c0cb` |
| Recovery package | `sha256:a3cdac42954c17199888bb85c32631ada4da55682cb62d57101999da1989bf8a` |
| Archive | `7059225a0c7663b0a28899afc3d8603d496af85fb3d32789a5b8a9a2d055b3fc` |
| Release manifest | `0b9bbc26d22f46dc4004be4b8150fdb72a06f870941a8b680344f5bd9d11ddd2` |

Only `control-plane/control_plane/store.py` differs from Store395. The other 37 payload files, deployment helpers, and maintained payload documentation are byte-identical to that baseline. The immutable release verifier passes all 38 payload files and schema29. Preparation refuses to overwrite an existing receipt/release.

## Supported state and boundaries

- Existing database: `PRAGMA user_version = 29`, persisted `admission_mode = recovery`, and nullable `verification_json TEXT` in the three migrated intent/permission tables.
- Startup performs read checks only. It returns before the old initializer and never runs migration/DDL, lowers `user_version`, clears verification, or restores a snapshot.
- All polling returns an empty list, independent of later admission drift. No action is allocated or redelivered and no new delivery attempt is created.
- New admission, admission changes, pilot creation/renewal, context/work-request creation, MCP grant creation/renewal, and semantic acceptance are rejected at their Store entry points. Public/HTTP routes resolve to those same methods.
- Existing action observations and exact receipt replay remain available. Legacy status serializers are not a new initial-verification oracle; retain/read the original receipt payload and use a schema29-capable forward release for final semantic acceptance.
- Missing/fresh databases, older/newer schemas, missing verification columns, and open/scoped-pilot intake are unsupported and fail closed.

## Focused proof

`prove-recovery.py` uses frozen Store395 to create schema28 legacy patch/receipt history, frozen r11 to migrate it and add exact-verification permission/intents/receipts, and this recovery artifact to reopen the closed database. No real file patch or command is executed. Local fixture credentials are generated test data and are neither printed nor retained; temporary SQLite databases are removed by the temporary-directory fixture.

`proof-receipt.json` records **7 passed invariants**:

1. All existing schema28 rows survive schema29 migration unchanged.
2. Recovery opening preserves every row, schema declaration, column, user version, action, and receipt/history record exactly.
3. All three `verification_json` columns and populated plans remain intact.
4. All dispatch lanes return no actions; queued verification stays queued; existing completed receipt replay is idempotent.
5. Intake/authority/grant/pilot/context/work-request/legacy acceptance refusal adds no rows or history.
6. Direct external admission drift cannot enable intake, dispatch, or recovery restart.
7. Fresh, older, newer, or open databases are refused without migration or restore.

The preserved fixture contains 3 actions, 2 delivery attempts, 2 receipts, 2 approved-patch intents, 1 standing-verification intent, and 22 events. Python import caches created during the proof were retained under `proof-runtime-cache/`; `proof-runtime-cache-receipt.json` records their original locations and exact moved-byte hashes. They are outside the frozen release payloads. Invoke future local proof with `python -B` to avoid creating caches in payload directories. The existing immutable proof receipt must be preserved; a new proof run needs a separately named receipt.

## Recovery use — requires a separate authorized live operation

1. Keep the known-good Store395 release and a verified transactionally consistent preactivation backup. Never restore that backup over any postmigration task/action history as an automatic rollback.
2. Using the currently served schema29-capable release, close intake into recovery mode and verify the persisted mode. Reconcile/stop active local work and preserve its receipt/proof state before changing the service.
3. Verify archive, release manifest, live schema29, exact service target, and closed-intake state. Take a new consistent backup of the current database. Preserve the r11 archive and packet as immutable evidence.
4. Activate this emergency artifact only through the separately approved server/service procedure, against the same current schema29 database. Do not deploy its legacy node-agent payload to Windows or renew any authority.
5. Use observation/exact receipt recovery only. Keep intake closed. Do not resume queued verification, submit a new patch/command, or record semantic acceptance under legacy code.
6. Prepare and verify a schema29-capable forward fix; preserve every postmigration row and proof. Reopening intake and activating another release are separate explicit live operations.

Current lane state: local packet and focused proof complete; live recovery deployment not performed. Parent/root retains rollout and final acceptance authority. Git remains dirty `main` at `2c554f59cb7b8ffc86ce5e0e28076c792777642f`, with unrelated/concurrent work preserved. No live RUN/WAVE/Job was created or queried by this lane.
