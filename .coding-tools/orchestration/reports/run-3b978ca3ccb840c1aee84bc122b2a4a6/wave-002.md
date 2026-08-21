# Orchestration Wave 2

- Run: `3b978ca3ccb840c1aee84bc122b2a4a6`
- Wave: `765f375570f842f28ae5403d1f643378`
- Objective: S2 final proof-only preflight. Locate the exact focused existing tests and source symbols needed to prove: provider_result artifact_ref wiring, orchestration_proof artifact_ref, handoff_capsule artifact_ref, build_artifact artifact_ref, bounded read_project_artifact offset/length/default/max behavior, and native image retrieval MIME plus SHA-256 integrity. The command_output lineage wave is already accepted and should be reused, not rerun. No writes, no docs, no S3. Return exact test names/commands and relevant symbols with minimal context.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `ac0b969589034b068376451202c12961a81726dbdc2e12be3a52d37d8731eba8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24595 | 2026-08-20T23:56:02.265Z | wave_replanned |  | PREFLIGHT | reason=The previous wave failed before exercising behavior because the Python tests were invoked from the repository root and could not import coding_tools_mcp. The strategy changes the command working directory to resources/coding-tools-mcp and points Rust checks at the root Cargo.toml; test scope and S2 semantics are otherwise unchanged. |
| 24596 | 2026-08-20T23:56:02.442Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24597 | 2026-08-20T23:56:02.581Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24598 | 2026-08-20T23:56:02.790Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 24599 | 2026-08-20T23:56:02.981Z | state_transition | READY | ROUTED | reason=route_selected |
| 24600 | 2026-08-20T23:56:03.414Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=48498b1ca1424da0821e022ae8d2d132 |
| 24601 | 2026-08-20T23:56:03.614Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24602 | 2026-08-20T23:56:04.031Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=48498b1ca1424da0821e022ae8d2d132 |
| 24603 | 2026-08-20T23:56:04.247Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24604 | 2026-08-20T23:56:04.632Z | proof_cache_miss |  |  | reason=cold; stage_id=check:078aed4fde130528; input_fingerprint=0a9d1b57275a7c4f695beee836409185cfda9763869251d479fd76bcbfc24dfa |
| 24605 | 2026-08-20T23:56:04.998Z | managed_process_admitted |  |  | owner=default |
| 24606 | 2026-08-20T23:56:05.408Z | managed_process_started |  |  | owner=default |
| 24607 | 2026-08-20T23:56:05.847Z | managed_process_terminal |  |  | owner=default |
| 24608 | 2026-08-20T23:56:06.232Z | proof_recorded |  |  | stage_id=check:078aed4fde130528; status=passed; cache_hit=False; input_fingerprint=0a9d1b57275a7c4f695beee836409185cfda9763869251d479fd76bcbfc24dfa |
| 24609 | 2026-08-20T23:56:06.531Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8d212fae366d9dc9; input_fingerprint=ca0bee046b98a88fac47c347732ed08c03c5dff4e28420ebfe6d6675cffc195c |
| 24610 | 2026-08-20T23:56:07.048Z | managed_process_admitted |  |  | owner=default |
| 24611 | 2026-08-20T23:56:07.398Z | managed_process_started |  |  | owner=default |
| 24612 | 2026-08-20T23:56:07.899Z | managed_process_terminal |  |  | owner=default |
| 24613 | 2026-08-20T23:56:08.211Z | proof_recorded |  |  | stage_id=check:8d212fae366d9dc9; status=passed; cache_hit=False; input_fingerprint=ca0bee046b98a88fac47c347732ed08c03c5dff4e28420ebfe6d6675cffc195c |
| 24614 | 2026-08-20T23:56:08.411Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d206604053763eb1; input_fingerprint=37749cfc624d693789e3dcd435337fe8465b21ff5df90036230952edc6555a7d |
| 24615 | 2026-08-20T23:56:08.831Z | managed_process_admitted |  |  | owner=default |
| 24616 | 2026-08-20T23:56:09.232Z | managed_process_started |  |  | owner=default |
| 24617 | 2026-08-20T23:56:09.800Z | managed_process_terminal |  |  | owner=default |
| 24618 | 2026-08-20T23:56:10.194Z | proof_recorded |  |  | stage_id=check:d206604053763eb1; status=passed; cache_hit=False; input_fingerprint=37749cfc624d693789e3dcd435337fe8465b21ff5df90036230952edc6555a7d |
| 24619 | 2026-08-20T23:56:10.397Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f63e540ba3bbba9c; input_fingerprint=44c595a6acd7133f8d285849d1352756aa1ce346354d17db34bf783b0d3e4202 |
| 24620 | 2026-08-20T23:56:10.831Z | managed_process_admitted |  |  | owner=default |
| 24621 | 2026-08-20T23:56:11.194Z | managed_process_started |  |  | owner=default |
| 24622 | 2026-08-20T23:56:12.348Z | managed_process_terminal |  |  | owner=default |
| 24623 | 2026-08-20T23:56:12.831Z | proof_recorded |  |  | stage_id=check:f63e540ba3bbba9c; status=passed; cache_hit=False; input_fingerprint=44c595a6acd7133f8d285849d1352756aa1ce346354d17db34bf783b0d3e4202 |
| 24624 | 2026-08-20T23:56:13.149Z | proof_cache_miss |  |  | reason=cold; stage_id=check:77904ac5ff7a7650; input_fingerprint=67720e063f30669aeae27ed171e2b54bb47fbd9bf008313c4cbd86c1586ab260 |
| 24625 | 2026-08-20T23:56:13.898Z | managed_process_admitted |  |  | owner=default |
| 24626 | 2026-08-20T23:56:14.224Z | managed_process_started |  |  | owner=default |
| 24627 | 2026-08-20T23:56:14.823Z | managed_process_terminal |  |  | owner=default |
| 24628 | 2026-08-20T23:56:15.165Z | proof_recorded |  |  | stage_id=check:77904ac5ff7a7650; status=passed; cache_hit=False; input_fingerprint=67720e063f30669aeae27ed171e2b54bb47fbd9bf008313c4cbd86c1586ab260 |
| 24629 | 2026-08-20T23:56:15.365Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cd113d18fb3a0638; input_fingerprint=d47d4a004fb2bb134440349f43d35f071d47e0e8c3db96224322b48983a33c28 |
| 24630 | 2026-08-20T23:56:15.823Z | managed_process_admitted |  |  | owner=default |
| 24631 | 2026-08-20T23:56:16.148Z | managed_process_started |  |  | owner=default |
| 24632 | 2026-08-20T23:56:16.831Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24633 | 2026-08-20T23:56:17.166Z | proof_recorded |  |  | stage_id=check:cd113d18fb3a0638; status=passed; cache_hit=False; input_fingerprint=d47d4a004fb2bb134440349f43d35f071d47e0e8c3db96224322b48983a33c28 |
| 24634 | 2026-08-20T23:56:17.381Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 24635 | 2026-08-20T23:56:33.880Z | quality_outcome_recorded |  |  |  |
| 24636 | 2026-08-20T23:56:34.081Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 24637 | 2026-08-20T23:56:34.440Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:078aed4fde130528 | passed | 0a9d1b57275a7c4f695beee836409185cfda9763869251d479fd76bcbfc24dfa | False | 1217 | 0 |
| check:8d212fae366d9dc9 | passed | ca0bee046b98a88fac47c347732ed08c03c5dff4e28420ebfe6d6675cffc195c | False | 1219 | 0 |
| check:d206604053763eb1 | passed | 37749cfc624d693789e3dcd435337fe8465b21ff5df90036230952edc6555a7d | False | 1377 | 0 |
| check:f63e540ba3bbba9c | passed | 44c595a6acd7133f8d285849d1352756aa1ce346354d17db34bf783b0d3e4202 | False | 1968 | 0 |
| check:77904ac5ff7a7650 | passed | 67720e063f30669aeae27ed171e2b54bb47fbd9bf008313c4cbd86c1586ab260 | False | 1457 | 0 |
| check:cd113d18fb3a0638 | passed | d47d4a004fb2bb134440349f43d35f071d47e0e8c3db96224322b48983a33c28 | False | 1308 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e4f333c16d3e4f6e860a3980a255403e | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 8428b6bd89b1e3474a39e8acf19fe9b0ca13672c984b7713cae501ea21df47de | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `99`
- Chain head: `5390ad5c46e8f2b721c12ae13fcbd904760924da26af1508dba28683191b8c51`
