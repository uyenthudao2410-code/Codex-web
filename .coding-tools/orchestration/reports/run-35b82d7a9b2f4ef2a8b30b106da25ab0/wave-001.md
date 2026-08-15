# Orchestration Wave 1

- Run: `35b82d7a9b2f4ef2a8b30b106da25ab0`
- Wave: `b8401e1666a142dcb14130dd01801fd4`
- Objective: P1 organic ChatWeb canary after controlled Electron/runtime activation. Create one exact EOCL run for this user turn, exercise only read-only evaluation-plane reporting, and preserve fail-closed behavior: do not modify source, do not restart, do not ACK coordination messages, do not route models, do not synthesize or manually assign host turn identity, and do not infer correlation by timestamp. The acceptance oracle is that the exact run is explicitly linked to the organic host turn by stable content-free identity and the evaluation reporter can prove explicit_host_run_identity_present.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `d0ce0b96930bdb8f1b9051db849800e33b6a28f8ed6da10fda317c29caecd95d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5150 | 2026-08-15T09:54:10.250Z | run_started |  | PREFLIGHT |  |
| 5151 | 2026-08-15T09:54:11.293Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 5152 | 2026-08-15T09:54:11.469Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 5153 | 2026-08-15T09:54:11.647Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5154 | 2026-08-15T09:54:11.816Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5155 | 2026-08-15T09:54:12.035Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 5156 | 2026-08-15T09:54:12.238Z | state_transition | READY | ROUTED | reason=route_selected |
| 5157 | 2026-08-15T09:54:13.176Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0cb3bcbaadda4d5c9c5b4d89ae61e73e |
| 5158 | 2026-08-15T09:54:13.349Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5159 | 2026-08-15T09:54:14.297Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0cb3bcbaadda4d5c9c5b4d89ae61e73e |
| 5160 | 2026-08-15T09:54:14.556Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5161 | 2026-08-15T09:54:15.347Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:facf17b308bc2dcd; input_fingerprint=bf1839de66c34608b5bb2f402ed26604913af0e56f4f549d04dd92e6d1968754 |
| 5162 | 2026-08-15T09:54:16.106Z | proof_recorded |  |  | stage_id=check:facf17b308bc2dcd; status=passed; cache_hit=False; input_fingerprint=bf1839de66c34608b5bb2f402ed26604913af0e56f4f549d04dd92e6d1968754 |
| 5163 | 2026-08-15T09:54:16.290Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5164 | 2026-08-15T09:56:01.808Z | observation_span_recorded |  |  |  |
| 5165 | 2026-08-15T09:56:50.456Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:facf17b308bc2dcd | passed | bf1839de66c34608b5bb2f402ed26604913af0e56f4f549d04dd92e6d1968754 | False | 336 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f8d2cbdd07344ac8a214846ae5893d5a | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 8f2077f60b4591fa38a66a7e97da438e312ecd681a22c212f6e86a639367574b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `16`
- Chain head: `ddf1edef67a98e8e252d8d1d2f88bff786b7f4f7da2132207e2ff5a575bce4b1`
