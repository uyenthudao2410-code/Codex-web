# Orchestration Wave 2

- Run: `07459502d5c84ee99ae1652df0032473`
- Wave: `6a4d741d56924e83a2c0a91dec353b95`
- Objective: Implement the prepared Natural HR Problem Lineage activation fix. Requirements: (1) problem_lineage_activation.py must be retry-idempotent when a guarded stopped-runtime retry sees schema already at v12, while still enforcing exact snapshot/logical hashes and full postflight checks; (2) introduce an exact typed maintenance reason problem_lineage_schema_v12 and a generalized workspace-maintenance predicate in Python restart-ticket/coordination code so an authorized target workspace is preserved only for exact-stale or PRL-v12 maintenance, with malformed prefix variants rejected; (3) mirror that reason/target validation in runtimeOrchestrator.js without weakening ordinary restart checkpoint semantics; (4) in fullCleanActivation.js run the existing scripts/activate_problem_lineage.py preflight and activation only after the old canonical runtime is stopped, derive fresh exact snapshot and logical hashes from preflight, pass them into --activate --runtime-stopped, validate schema 12/postflight receipt, record bounded verification evidence, and make Recovery Host retry safe; (5) preserve existing exact-stale maintenance and all unrelated dirty work; (6) do not manually edit SQLite, do not backfill historical Problems/outcomes, do not add a public tool. Add focused Python and Node tests for exact PRL maintenance target propagation, malformed-reason rejection, already-v12 retry, and stopped-runtime activation sequencing/receipt.
- Objective revision: `1`
- Objective SHA-256: `5ec82a14a1f60a7a60b616334723ad6941382b1bee73184b1fb8ed829c596ba7`
- Objective source: `replan_request`
- Mode: `deep_single_lane`
- Base HEAD: `58dfd3093d7a05f6999fe93e15c94050aa51d204`
- Worktree fingerprint: `68bdcb9633783e0d14ae05d48d3290218fa240fb2921081e6baea6a1592791cc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43454 | 2026-09-07T10:45:36.217Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 made no source changes and failed only because proof commands ran from the repository root. This wave corrects proof execution to the package-relative workdir and uses a Sol deep-code route appropriate to the coherent Python+Electron cross-subsystem change. |
| 43455 | 2026-09-07T10:45:36.388Z | observation_span_recorded |  |  |  |
| 43456 | 2026-09-07T10:45:36.662Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=COMPLETION_READINESS_BLOCKED |
| 43457 | 2026-09-07T10:45:36.854Z | state_transition | PREFLIGHT | REPLAN | reason=COMPLETION_READINESS_BLOCKED; failure_class=COMPLETION_READINESS_BLOCKED |
| 43458 | 2026-09-07T10:45:37.046Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `83`
- Chain head: `31e650dafcc0a85a59b6e441ea67f0f1a504166c56464f75bf72edbf00015f59`
