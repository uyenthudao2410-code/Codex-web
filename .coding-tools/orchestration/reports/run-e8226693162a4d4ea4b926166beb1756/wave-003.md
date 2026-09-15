# Orchestration Wave 3

- Run: `e8226693162a4d4ea4b926166beb1756`
- Wave: `2888058ee5774ccb940d9412327c1636`
- Objective: Diagnose the failed official Recovery Supervisor Install without retrying it. Verify whether the newly registered supervisor is actually alive/healthy despite installer timeout, and test the suspected current-source defect in Get-OptionalProperty where an existing property appears to return the default value. Bind findings to the failed Install command and current installed/source hashes. Read-only only; no source or lifecycle mutation in this wave.
- Objective revision: `2`
- Objective SHA-256: `167778966a0799e3cc3a67153391c0aa3da0556e103e62eeae33fc5b3029b5de`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `b7325226698fe70dc2b1460c2078bed2f064bdb513d1c77b938e0f5983bcb4b4`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57773 | 2026-09-15T07:34:42.929Z | wave_replanned |  | PREFLIGHT | reason=Official Install failed again with exact readiness timeout after forensic stop-writers quiesced. New source evidence materially changes the hypothesis: Get-OptionalProperty returns the default when the requested property exists, while Wait-InstalledSupervisorReady uses it for all readiness fields. Diagnose actual post-install state and helper behavior instead of retrying Install. |
| 57774 | 2026-09-15T07:34:43.583Z | observation_span_recorded |  |  |  |
| 57775 | 2026-09-15T07:34:44.169Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57776 | 2026-09-15T07:34:44.467Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57777 | 2026-09-15T07:34:44.763Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57778 | 2026-09-15T07:34:45.205Z | state_transition | READY | ROUTED | reason=route_selected |
| 57779 | 2026-09-15T07:34:45.630Z | observation_span_recorded |  |  |  |
| 57780 | 2026-09-15T07:34:46.563Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2ea8074f1f364523992a3fb13a10ebbf |
| 57781 | 2026-09-15T07:34:47.007Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57782 | 2026-09-15T07:34:47.758Z | observation_span_recorded |  |  |  |
| 57783 | 2026-09-15T07:34:48.635Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2ea8074f1f364523992a3fb13a10ebbf |
| 57784 | 2026-09-15T07:34:49.051Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57785 | 2026-09-15T07:34:49.990Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ac8aab2c4cdcb426; input_fingerprint=0c1e5562337fb0715cc8ce4c7c937c10d7f0f155b0fc051c244ba44d79a6487f |
| 57786 | 2026-09-15T07:34:50.972Z | managed_process_admitted |  |  | owner=default |
| 57787 | 2026-09-15T07:34:51.656Z | managed_process_started |  |  | owner=default |
| 57788 | 2026-09-15T07:34:54.272Z | managed_process_terminal |  |  | owner=default |
| 57789 | 2026-09-15T07:34:55.058Z | proof_recorded |  |  | stage_id=check:ac8aab2c4cdcb426; status=passed; cache_hit=False; input_fingerprint=0c1e5562337fb0715cc8ce4c7c937c10d7f0f155b0fc051c244ba44d79a6487f |
| 57790 | 2026-09-15T07:34:55.410Z | proof_cache_miss |  |  | reason=cold; stage_id=check:20bd5c87423dc402; input_fingerprint=2ee3b3bdd149ecc3b491e55256faaa27ea052d2a80fd80ccf449ee631bead129 |
| 57791 | 2026-09-15T07:34:56.097Z | managed_process_admitted |  |  | owner=default |
| 57792 | 2026-09-15T07:34:56.773Z | managed_process_started |  |  | owner=default |
| 57793 | 2026-09-15T07:34:57.484Z | managed_process_terminal |  |  | owner=default |
| 57794 | 2026-09-15T07:34:58.335Z | proof_recorded |  |  | stage_id=check:20bd5c87423dc402; status=passed; cache_hit=False; input_fingerprint=2ee3b3bdd149ecc3b491e55256faaa27ea052d2a80fd80ccf449ee631bead129 |
| 57795 | 2026-09-15T07:34:58.711Z | proof_cache_miss |  |  | reason=cold; stage_id=check:52bfd585cc63e2b4; input_fingerprint=a993afae8d0c4326a47f8518853a29b7ea1518114d03adf6b627fa97bd0d4d6a |
| 57796 | 2026-09-15T07:34:59.242Z | managed_process_admitted |  |  | owner=default |
| 57797 | 2026-09-15T07:35:00.221Z | managed_process_started |  |  | owner=default |
| 57798 | 2026-09-15T07:35:01.496Z | managed_process_terminal |  |  | owner=default |
| 57799 | 2026-09-15T07:35:02.222Z | proof_recorded |  |  | stage_id=check:52bfd585cc63e2b4; status=passed; cache_hit=False; input_fingerprint=a993afae8d0c4326a47f8518853a29b7ea1518114d03adf6b627fa97bd0d4d6a |
| 57800 | 2026-09-15T07:35:02.885Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7b8e7811f67a196c; input_fingerprint=06e73c1c667ad6a5a4356f13641a889ac3a588c4307c4b07c4ccdf0661fe8ac1 |
| 57801 | 2026-09-15T07:35:03.733Z | managed_process_admitted |  |  | owner=default |
| 57802 | 2026-09-15T07:35:04.432Z | managed_process_started |  |  | owner=default |
| 57803 | 2026-09-15T07:35:05.672Z | managed_process_terminal |  |  | owner=default |
| 57804 | 2026-09-15T07:35:06.535Z | proof_recorded |  |  | stage_id=check:7b8e7811f67a196c; status=passed; cache_hit=False; input_fingerprint=06e73c1c667ad6a5a4356f13641a889ac3a588c4307c4b07c4ccdf0661fe8ac1 |
| 57805 | 2026-09-15T07:35:07.229Z | observation_span_recorded |  |  |  |
| 57806 | 2026-09-15T07:35:07.369Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 57807 | 2026-09-15T07:35:07.960Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 57825 | 2026-09-15T07:36:06.385Z | quality_outcome_recorded |  |  |  |
| 57826 | 2026-09-15T07:36:06.975Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 57828 | 2026-09-15T07:36:10.264Z | observation_span_recorded |  |  |  |
| 57830 | 2026-09-15T07:36:13.020Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 57831 | 2026-09-15T07:36:13.701Z | observation_span_recorded |  |  |  |
| 57832 | 2026-09-15T07:36:14.488Z | observation_span_recorded |  |  |  |
| 57833 | 2026-09-15T07:36:15.155Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ac8aab2c4cdcb426 | passed | 0c1e5562337fb0715cc8ce4c7c937c10d7f0f155b0fc051c244ba44d79a6487f | False | 4396 | 0 |
| check:20bd5c87423dc402 | passed | 2ee3b3bdd149ecc3b491e55256faaa27ea052d2a80fd80ccf449ee631bead129 | False | 2080 | 0 |
| check:52bfd585cc63e2b4 | passed | a993afae8d0c4326a47f8518853a29b7ea1518114d03adf6b627fa97bd0d4d6a | False | 2982 | 0 |
| check:7b8e7811f67a196c | passed | 06e73c1c667ad6a5a4356f13641a889ac3a588c4307c4b07c4ccdf0661fe8ac1 | False | 2859 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 7979e6c5438e47588be68509ca75f6a3 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 75dcb8ec45db23386909aaa03c4763b53fbc721c6c0509459089346c55bf61cc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `584f0f00b53d2d5ac73c72846455021db8c9444075e84d99891a8fc93529adf0`
