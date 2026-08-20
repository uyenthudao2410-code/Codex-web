# Orchestration Wave 1

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Wave: `6659d288b4a749c391a3593b47d6c299`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Mode: `mcp_only`
- Base HEAD: `66c2d17b68969c3a413b867cc7281f80fbaf4b45`
- Worktree fingerprint: `49df1bd45be44847a81ecf6f72ac256ef772a2548b2ee066fa371120889e626c`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23880 | 2026-08-20T11:22:48.133Z | run_started |  | PREFLIGHT |  |
| 23881 | 2026-08-20T11:22:59.090Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23882 | 2026-08-20T11:23:46.460Z | managed_process_admitted |  |  | owner=default |
| 23883 | 2026-08-20T11:23:46.722Z | managed_process_started |  |  | owner=default |
| 23884 | 2026-08-20T11:23:47.522Z | managed_process_terminal |  |  | owner=default |
| 23885 | 2026-08-20T11:24:16.822Z | managed_process_admitted |  |  | owner=default |
| 23886 | 2026-08-20T11:24:17.071Z | managed_process_started |  |  | owner=default |
| 23887 | 2026-08-20T11:24:17.891Z | managed_process_terminal |  |  | owner=default |
| 23888 | 2026-08-20T11:24:29.564Z | managed_process_admitted |  |  | owner=default |
| 23889 | 2026-08-20T11:24:29.797Z | managed_process_started |  |  | owner=default |
| 23890 | 2026-08-20T11:24:30.599Z | managed_process_terminal |  |  | owner=default |
| 23891 | 2026-08-20T11:25:19.210Z | managed_process_admitted |  |  | owner=default |
| 23892 | 2026-08-20T11:25:19.571Z | managed_process_started |  |  | owner=default |
| 23893 | 2026-08-20T11:25:20.132Z | managed_process_terminal |  |  | owner=default |
| 23894 | 2026-08-20T11:26:00.650Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23895 | 2026-08-20T11:26:01.350Z | managed_process_admitted |  |  | owner=default |
| 23896 | 2026-08-20T11:26:01.655Z | managed_process_started |  |  | owner=default |
| 23897 | 2026-08-20T11:26:02.763Z | managed_process_terminal |  |  | owner=default |
| 23898 | 2026-08-20T11:26:03.090Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 23899 | 2026-08-20T11:26:03.298Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23900 | 2026-08-20T11:26:03.525Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23901 | 2026-08-20T11:26:03.692Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 23902 | 2026-08-20T11:26:03.944Z | state_transition | READY | ROUTED | reason=route_selected |
| 23903 | 2026-08-20T11:26:04.482Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a1d17f66154f4f7ebaa60eff094ab19c |
| 23904 | 2026-08-20T11:26:04.713Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23905 | 2026-08-20T11:26:05.176Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a1d17f66154f4f7ebaa60eff094ab19c |
| 23906 | 2026-08-20T11:26:05.391Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23907 | 2026-08-20T11:26:05.966Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:796009f75ffcdfa8; input_fingerprint=45108c4827b84e443239caa166c9926db9472002bc65605bff9d718591bce41c |
| 23908 | 2026-08-20T11:26:06.363Z | managed_process_admitted |  |  | owner=default |
| 23909 | 2026-08-20T11:26:06.719Z | managed_process_started |  |  | owner=default |
| 23910 | 2026-08-20T11:26:10.128Z | managed_process_terminal |  |  | owner=default |
| 23911 | 2026-08-20T11:26:10.575Z | proof_recorded |  |  | stage_id=check:796009f75ffcdfa8; status=passed; cache_hit=False; input_fingerprint=45108c4827b84e443239caa166c9926db9472002bc65605bff9d718591bce41c |
| 23912 | 2026-08-20T11:26:10.801Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=0554059a2d8c6938e55235c8146fcb1aa71ef76310b3f88f665cbbeb4b4d31cf |
| 23913 | 2026-08-20T11:26:11.210Z | managed_process_admitted |  |  | owner=default |
| 23914 | 2026-08-20T11:26:11.563Z | managed_process_started |  |  | owner=default |
| 23915 | 2026-08-20T11:26:12.798Z | managed_process_terminal |  |  | owner=default |
| 23916 | 2026-08-20T11:26:13.153Z | proof_recorded |  |  | stage_id=verify:all; status=failed; cache_hit=False; input_fingerprint=0554059a2d8c6938e55235c8146fcb1aa71ef76310b3f88f665cbbeb4b4d31cf |
| 23917 | 2026-08-20T11:26:13.358Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 23918 | 2026-08-20T11:26:13.519Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 23919 | 2026-08-20T11:26:13.736Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:796009f75ffcdfa8 | passed | 45108c4827b84e443239caa166c9926db9472002bc65605bff9d718591bce41c | False | 4225 | 0 |
| verify:all | failed | 0554059a2d8c6938e55235c8146fcb1aa71ef76310b3f88f665cbbeb4b4d31cf | False | 2015 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `86ff6f220ed633371c16f8c9d708dbab4535a3695e2f74d603db51e9f0749d54`
