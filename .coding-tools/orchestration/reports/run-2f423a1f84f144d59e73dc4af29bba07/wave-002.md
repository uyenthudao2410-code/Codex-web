# Orchestration Wave 2

- Run: `2f423a1f84f144d59e73dc4af29bba07`
- Wave: `9afe5ec5e6cd4958a1f4ec3063113687`
- Objective: Prove staged TG1-TG12 V4 application packet exact bytes before final acceptance
- Objective revision: `2`
- Objective SHA-256: `3f2d2237c9024ff10380eb186cfce79f794a9f354b5a07762bbef6f24dcb2524`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `9a9114af87fabb22bdb388af4b201cabde995d56603d51af54c96f14c8db4750`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35999 | 2026-09-03T04:25:02.041Z | wave_replanned |  | PREFLIGHT | reason=Query-only canonical-ledger reconciliation proves the prior unknown key stopped at operator ACK preflight before wave creation, command execution, proof, or mutation; use a new key for exact read-only proof |
| 36000 | 2026-09-03T04:25:02.284Z | observation_span_recorded |  |  |  |
| 36001 | 2026-09-03T04:25:03.282Z | observation_span_recorded |  |  |  |
| 36002 | 2026-09-03T04:25:03.486Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36003 | 2026-09-03T04:25:03.654Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 36004 | 2026-09-03T04:25:03.876Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36005 | 2026-09-03T04:25:04.084Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36006 | 2026-09-03T04:25:04.328Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 36007 | 2026-09-03T04:25:04.528Z | state_transition | READY | ROUTED | reason=route_selected |
| 36008 | 2026-09-03T04:25:04.759Z | observation_span_recorded |  |  |  |
| 36009 | 2026-09-03T04:25:05.711Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b08e2d41896f4f71989b15f894f04315 |
| 36010 | 2026-09-03T04:25:05.901Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36011 | 2026-09-03T04:25:06.836Z | observation_span_recorded |  |  |  |
| 36012 | 2026-09-03T04:25:07.133Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b08e2d41896f4f71989b15f894f04315 |
| 36013 | 2026-09-03T04:25:07.328Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36014 | 2026-09-03T04:25:08.107Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f07dd8d360880b34; input_fingerprint=a61ecd00745803b70102832b774b018f5a728a353ba6b80a7949592b3acf9d04 |
| 36015 | 2026-09-03T04:25:08.566Z | managed_process_admitted |  |  | owner=default |
| 36016 | 2026-09-03T04:25:08.875Z | managed_process_started |  |  | owner=default |
| 36017 | 2026-09-03T04:25:09.581Z | managed_process_terminal |  |  | owner=default |
| 36018 | 2026-09-03T04:25:09.943Z | proof_recorded |  |  | stage_id=check:f07dd8d360880b34; status=passed; cache_hit=False; input_fingerprint=a61ecd00745803b70102832b774b018f5a728a353ba6b80a7949592b3acf9d04 |
| 36019 | 2026-09-03T04:25:10.150Z | observation_span_recorded |  |  |  |
| 36020 | 2026-09-03T04:25:10.429Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 36021 | 2026-09-03T04:26:23.879Z | quality_outcome_recorded |  |  |  |
| 36022 | 2026-09-03T04:26:24.082Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 36023 | 2026-09-03T04:26:24.381Z | observation_span_recorded |  |  |  |
| 36024 | 2026-09-03T04:26:24.647Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f07dd8d360880b34 | passed | a61ecd00745803b70102832b774b018f5a728a353ba6b80a7949592b3acf9d04 | False | 1414 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 70cd7bc0bfe94e008a22958c2dba2855 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 3d4b6ebc9b13ec81b90734527f8ab1387ac79b8f55ae5120da4cc69326fca9a6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `16b476035b8b6af28d3d95c77bed2b5cca67f94f016d290fe730a948cc1eb20f`
