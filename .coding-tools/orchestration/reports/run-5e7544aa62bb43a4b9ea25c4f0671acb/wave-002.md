# Orchestration Wave 2

- Run: `5e7544aa62bb43a4b9ea25c4f0671acb`
- Wave: `d539d830be174302bc9ec10d14bf6de0`
- Objective: Preflight exactly the six currently reported unresolved stale orchestration RUN IDs using the repository-supported read-only exact-ID maintenance CLI. Capture immutable snapshot/logical hashes and blocker classifications only. Do not reconcile, do not pass runtime-stopped, do not modify source/Git/ledger except ordinary current RUN evidence, and do not inspect any other historical RUN.
- Objective revision: `1`
- Objective SHA-256: `38c7a4112d68fc383ae6c4420a66cc6357b668a505e297b775117fee5f263da2`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `1f8ce07b6442346931cfcd2610c20047b7c341224ac9a059f7e79152adc73886`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42637 | 2026-09-07T02:31:22.127Z | wave_replanned |  | PREFLIGHT | reason=The previous wave failed before any preflight because the source checkout has no python_vendor executable at that path. Use the Python interpreter available to the active Coding MCP runtime instead; keep all exact RUN IDs and read-only semantics unchanged. |
| 42638 | 2026-09-07T02:31:22.342Z | observation_span_recorded |  |  |  |
| 42639 | 2026-09-07T02:31:22.862Z | observation_span_recorded |  |  |  |
| 42640 | 2026-09-07T02:31:23.072Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42641 | 2026-09-07T02:31:23.275Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42642 | 2026-09-07T02:31:23.504Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42643 | 2026-09-07T02:31:23.684Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42644 | 2026-09-07T02:31:23.882Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42645 | 2026-09-07T02:31:24.080Z | state_transition | READY | ROUTED | reason=route_selected |
| 42646 | 2026-09-07T02:31:24.312Z | observation_span_recorded |  |  |  |
| 42647 | 2026-09-07T02:31:24.817Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ebd69a9743df485f9182b5c19dce2330 |
| 42648 | 2026-09-07T02:31:24.991Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42649 | 2026-09-07T02:31:25.377Z | observation_span_recorded |  |  |  |
| 42650 | 2026-09-07T02:31:25.660Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ebd69a9743df485f9182b5c19dce2330 |
| 42651 | 2026-09-07T02:31:25.817Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42652 | 2026-09-07T02:31:26.217Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6d456d5145e1708d; input_fingerprint=786c12d5216db767b2085317b94c4732178449d239ac7fa62e8425a9871a52cb |
| 42653 | 2026-09-07T02:31:26.580Z | managed_process_admitted |  |  | owner=default |
| 42654 | 2026-09-07T02:31:26.930Z | managed_process_started |  |  | owner=default |
| 42655 | 2026-09-07T02:31:31.219Z | managed_process_terminal |  |  | owner=default |
| 42656 | 2026-09-07T02:31:31.624Z | proof_recorded |  |  | stage_id=check:6d456d5145e1708d; status=failed; cache_hit=False; input_fingerprint=786c12d5216db767b2085317b94c4732178449d239ac7fa62e8425a9871a52cb |
| 42657 | 2026-09-07T02:31:31.819Z | observation_span_recorded |  |  |  |
| 42658 | 2026-09-07T02:31:31.999Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42659 | 2026-09-07T02:31:32.208Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42660 | 2026-09-07T02:31:32.395Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6d456d5145e1708d | failed | 786c12d5216db767b2085317b94c4732178449d239ac7fa62e8425a9871a52cb | False | 5025 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `74`
- Chain head: `675c0f0af65252c437cd3e7955b11cc12bed2eb4fd0915cd07645de3ff109f9c`
