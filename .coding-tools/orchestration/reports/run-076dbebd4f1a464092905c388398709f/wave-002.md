# Orchestration Wave 2

- Run: `076dbebd4f1a464092905c388398709f`
- Wave: `6b4021b6bf4b445480257788f2143ab7`
- Objective: Resolve the exact consent failure: a bounded continuation challenge can be displayed, then POST fails with 'This controller endpoint is fenced from the durable Goal'. Preserve fail-closed authority, one-shot consent, exact Problem rev2, and controller-gated acceptance. Implement the smallest safe behavior: immutable controller/RUN/WAVE drift terminalizes the reviewed challenge; transient finalization failures remain retryable; the local approval UI must not re-enable a terminal stale challenge and must require a freshly issued challenge. No restart/commit/push/package/release and no unrelated source changes.
- Objective revision: `2`
- Objective SHA-256: `3fd0bff1dac8e86d06424e23887327bcdd14c137b905e3305993fa24cd885819`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `50993da4aaaf75219274db5f7d577b30281b165b`
- Worktree fingerprint: `18a72397cdb257c44d7725e61f2f39351a4d79e56a2bbf69bfa3bfebbcd8b4f2`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59634 | 2026-09-15T11:03:46.755Z | wave_replanned |  | PREFLIGHT | reason=The previous wave was fail-closed before mutation because concurrent unrelated work changed the repository after preflight. The two intended consent source/test files were verified clean immediately before that drift. Replan the same RUN on current workspace bytes, restrict writes to those two files, and apply the already-derived stale-challenge lifecycle fix without touching concurrent lanes. |
| 59635 | 2026-09-15T11:03:47.056Z | observation_span_recorded |  |  |  |
| 59637 | 2026-09-15T11:04:24.732Z | observation_span_recorded |  |  |  |
| 59638 | 2026-09-15T11:04:25.419Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59639 | 2026-09-15T11:16:23.204Z | managed_process_admitted |  |  | owner=default |
| 59640 | 2026-09-15T11:16:23.501Z | managed_process_started |  |  | owner=default |
| 59641 | 2026-09-15T11:16:23.928Z | managed_process_terminal |  |  | owner=default |
| 59642 | 2026-09-15T11:17:03.774Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 59643 | 2026-09-15T11:17:03.966Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 59644 | 2026-09-15T11:17:04.217Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `77`
- Chain head: `a71a08b45f4fe76c4d755ed9d4dcd6fbf96e77f722b8b2cbfa8983a1199fab03`
