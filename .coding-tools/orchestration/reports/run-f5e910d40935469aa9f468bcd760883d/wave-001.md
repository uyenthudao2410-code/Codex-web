# Orchestration Wave 1

- Run: `f5e910d40935469aa9f468bcd760883d`
- Wave: `6053bb07f27949cb9c21c14017142799`
- Objective: Investigate Project Finance -> Project detail -> Overview in the HR app. Identify every overview KPI/card/table value that is currently hardcoded, mocked, placeholder, seeded only for UI, or falls back to fake numbers. Trace the real data contracts and calculation sources available in the current finance frontend/BFF/backend. Do not mutate files yet. Financial invariant: displayed monetary/percentage/status values must be derived from the selected project's real persisted/read-model data and must not fabricate a value when source data is missing; missing data should be represented truthfully. Return the smallest coherent implementation scope and authoritative focused verification commands.
- Mode: `mcp_only`
- Base HEAD: `06854413b465b17749346ecfd7ce51731b6a4789`
- Worktree fingerprint: `dabfe19bd747b107a65e8fd92dd57a34228f4507731c272bc732edb29ecf3017`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19234 | 2026-08-19T04:28:36.901Z | run_started |  | PREFLIGHT |  |
| 19235 | 2026-08-19T04:29:09.672Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19236 | 2026-08-19T04:29:22.911Z | managed_process_admitted |  |  | owner=chatweb |
| 19237 | 2026-08-19T04:29:23.268Z | managed_process_started |  |  | owner=chatweb |
| 19238 | 2026-08-19T04:29:23.694Z | managed_process_terminal |  |  | owner=chatweb |
| 19239 | 2026-08-19T04:29:33.566Z | managed_process_admitted |  |  | owner=chatweb |
| 19240 | 2026-08-19T04:29:33.870Z | managed_process_started |  |  | owner=chatweb |
| 19241 | 2026-08-19T04:29:34.316Z | managed_process_terminal |  |  | owner=chatweb |
| 19242 | 2026-08-19T04:29:42.720Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19243 | 2026-08-19T04:29:53.062Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 19244 | 2026-08-19T04:29:53.234Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 19245 | 2026-08-19T04:29:53.438Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `197`
- Chain head: `b7269eb4089c09255400b81b4981a53bcbe1a4a2fccfe75cabcc724afe37087e`
