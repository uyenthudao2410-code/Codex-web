# Orchestration Wave 1

- Run: `10eb561f23f24f73a596ec03b4978d5b`
- Wave: `e6fe71150f5748acb8d2860b5c343727`
- Objective: G5 real ChatWeb observability turn 2; inspect controller-usage ingress without source mutation.
- Objective revision: `1`
- Objective SHA-256: `2222cf3f33eed6f337a3f24955a67bf50088ff0aa2e5336c132c92989f788f40`
- Objective source: `run_initial_objective`
- Mode: `auto`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `0faee146ff3a9e8a33b0a40103a781345f93fff61603576e2b500f2beed90bbf`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38898 | 2026-09-03T22:22:25.257Z | run_started |  | PREFLIGHT |  |
| 38899 | 2026-09-03T22:22:25.655Z | observation_span_recorded |  |  |  |
| 38900 | 2026-09-03T22:22:31.078Z | observation_span_recorded |  |  |  |
| 38901 | 2026-09-03T22:22:31.323Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38902 | 2026-09-03T22:25:27.234Z | state_transition | PREFLIGHT | ABORTED | reason=G5 turn 2 measurement complete; terminalize only this exact turn-2 PREFLIGHT RUN before creating the separate real turn-3 attribution RUN. |
| 38903 | 2026-09-03T22:25:27.753Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Chain head: `0948c188f6423acc4e5375b91917c3a694dd1965ca1b4b3c2c942e21200f861e`
