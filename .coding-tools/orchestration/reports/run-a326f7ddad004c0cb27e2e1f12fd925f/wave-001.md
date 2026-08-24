# Orchestration Wave 1

- Run: `a326f7ddad004c0cb27e2e1f12fd925f`
- Wave: `ed66e86f2f044480ad87c8de2e5e0311`
- Objective: RUN-MW-CLOSURE: prove the corrected stateless-background context propagation, multi-workspace isolation, durable context, and scoped control on the current Codex-web worktree.
- Objective revision: `1`
- Objective SHA-256: `df2a1dc35a6178a976099b503b4616d020c7064fc73af546d2341df3d89c60d8`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `4d77edd521658d14d6f5125b1e8ff3498e80a77f`
- Worktree fingerprint: `d606fbfd9ddbb35bfa28b2891069399eee79f3a456242accc11cb2344673c2b9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28880 | 2026-08-24T12:08:02.257Z | run_started |  | PREFLIGHT |  |
| 28881 | 2026-08-24T12:08:02.625Z | observation_span_recorded |  |  |  |
| 28882 | 2026-08-24T12:08:02.791Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28883 | 2026-08-24T12:08:02.937Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28884 | 2026-08-24T12:08:03.102Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28885 | 2026-08-24T12:08:03.281Z | state_transition | READY | ROUTED | reason=route_selected |
| 28886 | 2026-08-24T12:08:03.455Z | observation_span_recorded |  |  |  |
| 28887 | 2026-08-24T12:08:04.347Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7b035be8ee884701ab155244312e9966 |
| 28888 | 2026-08-24T12:08:04.495Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28889 | 2026-08-24T12:08:05.313Z | observation_span_recorded |  |  |  |
| 28890 | 2026-08-24T12:08:05.581Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7b035be8ee884701ab155244312e9966 |
| 28891 | 2026-08-24T12:08:05.719Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28892 | 2026-08-24T12:08:06.443Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a5804220fb15a344; input_fingerprint=7ddff0345e850a9e5f5f52caf44da2890ae993778a1368fc7b43b8010ef51b7f |
| 28893 | 2026-08-24T12:08:06.804Z | managed_process_admitted |  |  | owner=default |
| 28894 | 2026-08-24T12:08:07.094Z | managed_process_started |  |  | owner=default |
| 28895 | 2026-08-24T12:08:34.168Z | managed_process_terminal |  |  | owner=default |
| 28896 | 2026-08-24T12:08:34.538Z | proof_recorded |  |  | stage_id=check:a5804220fb15a344; status=passed; cache_hit=False; input_fingerprint=7ddff0345e850a9e5f5f52caf44da2890ae993778a1368fc7b43b8010ef51b7f |
| 28897 | 2026-08-24T12:08:34.717Z | observation_span_recorded |  |  |  |
| 28898 | 2026-08-24T12:08:34.883Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 28899 | 2026-08-24T12:12:33.280Z | quality_outcome_recorded |  |  |  |
| 28900 | 2026-08-24T12:12:33.444Z | observation_span_recorded |  |  |  |
| 28901 | 2026-08-24T12:12:33.582Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 28902 | 2026-08-24T12:12:33.954Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a5804220fb15a344 | passed | 7ddff0345e850a9e5f5f52caf44da2890ae993778a1368fc7b43b8010ef51b7f | False | 27747 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 29b82eea32274a2fac37a54c80c021e3 | accepted | 4d77edd521658d14d6f5125b1e8ff3498e80a77f | 1738680f673afad831c07c5fe777d5991891afefc239e00680a2946eb291ec03 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `0da5901e3b2feb49bb77a44311824b549dc4992286def687f1ee9b1521af0bac`
