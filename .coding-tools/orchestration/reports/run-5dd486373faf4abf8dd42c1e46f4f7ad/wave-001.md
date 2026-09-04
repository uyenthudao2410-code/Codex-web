# Orchestration Wave 1

- Run: `5dd486373faf4abf8dd42c1e46f4f7ad`
- Wave: `648bbf0262e74ca084f990d66e9f15f5`
- Objective: G4 read-only semantic-then-text-fallback measurement only. Localize the three exact-text identifiers terminateExactProcessTree, captureSpawnedProcessIdentity, serviceSupervisorRestartRequest. No regex. Keep localization/materialization bounded to at most 5 files, at most 120000 total source bytes, and at most 10 matches per query. Do not mutate files, do not create or execute an EOCL RUN/WAVE, do not run proofs/tests/builds, do not create Problems/outcomes. Return observed semantic-localization attempt/handling/fallback engine and timing/read/materialization/truncation metadata when available; missing metrics remain unknown.
- Objective revision: `1`
- Objective SHA-256: `f7dd3e0c3769f9b1166b7ea26c16f3ae4c1fbc602ed489610c72dd490b5bafb9`
- Objective source: `run_initial_objective`
- Mode: `auto`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `8a39eb38e7f881a5ba3d8d531313501cd03c76a7e11611a944f489a590c67be4`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38814 | 2026-09-03T21:05:14.931Z | run_started |  | PREFLIGHT |  |
| 38815 | 2026-09-03T21:05:15.331Z | observation_span_recorded |  |  |  |
| 38816 | 2026-09-03T21:05:20.932Z | observation_span_recorded |  |  |  |
| 38817 | 2026-09-03T21:05:21.131Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38818 | 2026-09-03T21:08:50.772Z | state_transition | PREFLIGHT | ABORTED | reason=G4_RECONCILE_READ_ONLY_PREPARE_SIDE_EFFECT |
| 38819 | 2026-09-03T21:08:51.348Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `6`
- Chain head: `02778b1032fbcb5ee7715895c8c1c540605ca4fa92d98c464ebf275e919493ba`
