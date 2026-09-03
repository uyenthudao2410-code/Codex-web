# Orchestration Wave 2

- Run: `1bfeefca31874860bc218d9f3041cca3`
- Wave: `493ed8d7fbfb454d9351328b06350d08`
- Objective: Repair the stateless exact-RUN recovery control-plane defect blocking Token W4. Exact task_control with requested run_id and omitted task_context_id must recover the original registered context from exact archived task history when the current compact projection is safely terminal, while failing closed on active conflicts, pending operator reports, ambiguous contexts, workspace mismatch, or foreign controller ownership. Canonical orchestration ledger remains immutable authority. Preserve unrelated dirty bytes and the smart-v3 8-tool contract. No W4 implementation, restart, commit, push, release, or deploy in this wave.
- Objective revision: `2`
- Objective SHA-256: `d812bac70ceebd6109022c173d95d65f9f46f1552a2a17e75cc15c44bb163814`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `cd9fdac8b4ee50cfe307293d1356ef0f974776cd285d00e4dd4355cdb040bbad`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34127 | 2026-09-01T02:15:37.384Z | wave_replanned |  | PREFLIGHT | reason=The prior proof failure was an oracle/workdir error before any source mutation; the first corrective patch attempt was then rejected at preflight because one projection-rebuild hunk was ambiguous. This attempt changes patch addressing by splitting files and using unique function/branch context while retaining the same fail-closed design and corrected package-root oracle. |
| 34128 | 2026-09-01T02:15:37.637Z | observation_span_recorded |  |  |  |
| 34129 | 2026-09-01T02:16:12.935Z | observation_span_recorded |  |  |  |
| 34130 | 2026-09-01T02:16:13.193Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 34131 | 2026-09-01T02:16:13.392Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34132 | 2026-09-01T02:16:13.587Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34133 | 2026-09-01T02:16:13.880Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 34134 | 2026-09-01T02:16:14.099Z | state_transition | READY | ROUTED | reason=route_selected |
| 34135 | 2026-09-01T02:16:14.314Z | observation_span_recorded |  |  |  |
| 34136 | 2026-09-01T02:16:15.230Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e721f6d3e481420f96198f4943815147 |
| 34137 | 2026-09-01T02:16:15.385Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34138 | 2026-09-01T02:16:16.220Z | patch_surface_observed |  |  |  |
| 34139 | 2026-09-01T02:16:16.558Z | patch_surface_observed |  |  |  |
| 34140 | 2026-09-01T02:16:16.842Z | patch_surface_observed |  |  |  |
| 34141 | 2026-09-01T02:16:17.123Z | patch_surface_observed |  |  |  |
| 34142 | 2026-09-01T02:16:17.350Z | patch_surface_observed |  |  |  |
| 34143 | 2026-09-01T02:16:17.519Z | observation_span_recorded |  |  |  |
| 34144 | 2026-09-01T02:16:17.822Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e721f6d3e481420f96198f4943815147 |
| 34145 | 2026-09-01T02:16:17.982Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34146 | 2026-09-01T02:16:18.707Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b9422b6ec1ff4791b8e20333708bdce16b7b0e43b6704695ad39c2e482b3e14f |
| 34147 | 2026-09-01T02:16:19.341Z | managed_process_admitted |  |  | owner=default |
| 34148 | 2026-09-01T02:16:19.674Z | managed_process_started |  |  | owner=default |
| 34149 | 2026-09-01T02:16:42.588Z | managed_process_terminal |  |  | owner=default |
| 34150 | 2026-09-01T02:16:44.218Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b9422b6ec1ff4791b8e20333708bdce16b7b0e43b6704695ad39c2e482b3e14f |
| 34151 | 2026-09-01T02:16:45.091Z | observation_span_recorded |  |  |  |
| 34152 | 2026-09-01T02:16:45.318Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34153 | 2026-09-01T02:26:44.673Z | managed_process_admitted |  |  | owner=default |
| 34154 | 2026-09-01T02:26:45.024Z | managed_process_started |  |  | owner=default |
| 34155 | 2026-09-01T02:26:45.522Z | managed_process_terminal |  |  | owner=default |
| 34156 | 2026-09-01T02:27:05.647Z | quality_outcome_recorded |  |  |  |
| 34157 | 2026-09-01T02:27:05.838Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 34158 | 2026-09-01T02:27:06.098Z | observation_span_recorded |  |  |  |
| 34159 | 2026-09-01T02:27:06.333Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | b9422b6ec1ff4791b8e20333708bdce16b7b0e43b6704695ad39c2e482b3e14f | False | 24733 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 44ce31aa6f5e463bbac4da347289f4c7 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 3664beb6afc65ecfd0ae227b85564055e8a68e9c5d621e107eca9f64ed500251 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `45404375dadcd7d7b5171d52eec0c8c67c79027a92d0128082ff23bf96e0fb9d`
