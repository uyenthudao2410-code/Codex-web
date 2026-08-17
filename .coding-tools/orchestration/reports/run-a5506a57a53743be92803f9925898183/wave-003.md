# Orchestration Wave 3

- Run: `a5506a57a53743be92803f9925898183`
- Wave: `4637bfc074ad4be6b11ef6eaf49825e1`
- Objective: Map the P0.3 F1-F9 Recovery fault matrix on exact delivered HEAD 885260b404c2c64df1b1afa835963045ac55dbf6 before any new mutation. For each F1-F9 in docs/PRODUCTION_CLOSURE_ROLLOUT.md, identify exact existing test names/functions/scripts and whether they are deterministic/unit, current-process integration, or isolated packaged real-process evidence. Reuse exact current coverage where it already proves the required behavior. Identify the smallest genuine gaps only. Pay special attention to whether F2 Recovery Host crash + installed Supervisor restart is covered in a real installed/isolated process harness, and whether F3-F6 subordinate owned-process exits are covered with new PID, preserved unaffected peer, exact port/device identity and no duplicate listener. F7/F8/F9 may be deterministic if they fully prove ownership/backoff invariants. Never propose killing the active development Coding MCP/Recovery Host/Tunnels. Return a concrete matrix with exact commands to run and minimal files to change only if needed.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `5d82026f8a9bc78da6473002cd51239f92a30b235ad850d5c7c5f1f0d64709c5`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13192 | 2026-08-17T09:26:24.749Z | wave_replanned |  | PREFLIGHT | reason=Previous Terra candidate was blocked before source mutation. Prepare exact source context so the next execute wave can use a complete explicit patch rather than candidate-generated mutation. |
| 13193 | 2026-08-17T09:26:25.783Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13194 | 2026-08-17T09:27:44.034Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13195 | 2026-08-17T09:29:56.574Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=deep_single_lane; resolved=mcp_only |
| 13196 | 2026-08-17T09:29:56.765Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13197 | 2026-08-17T09:29:56.964Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13198 | 2026-08-17T09:29:57.157Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13199 | 2026-08-17T09:29:57.330Z | state_transition | READY | ROUTED | reason=route_selected |
| 13200 | 2026-08-17T09:29:57.954Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5399bdba3dfb421488303467233010ed |
| 13201 | 2026-08-17T09:29:58.148Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13202 | 2026-08-17T09:29:58.981Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5399bdba3dfb421488303467233010ed |
| 13203 | 2026-08-17T09:29:59.273Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13204 | 2026-08-17T09:29:59.814Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b918ef072cc2a2f26faf02b79be05fbda3dfa8745b6262f0f23565dcfba36dfb |
| 13205 | 2026-08-17T09:30:00.185Z | managed_process_admitted |  |  | owner=default |
| 13206 | 2026-08-17T09:30:00.595Z | managed_process_started |  |  | owner=default |
| 13207 | 2026-08-17T09:30:01.156Z | managed_process_terminal |  |  | owner=default |
| 13208 | 2026-08-17T09:30:02.543Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b918ef072cc2a2f26faf02b79be05fbda3dfa8745b6262f0f23565dcfba36dfb |
| 13209 | 2026-08-17T09:30:03.291Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13210 | 2026-08-17T09:31:02.138Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13211 | 2026-08-17T09:31:02.576Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | b918ef072cc2a2f26faf02b79be05fbda3dfa8745b6262f0f23565dcfba36dfb | False | 2219 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5efd555cbd3b4d3687b91f3097ba466d | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | bae592655d85cc95d332c5acea13a089ac17fcd23ea02d64cf81b322008bece5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `05b19844e5ace548d94c537611d1f18768f4cbb6596c4721e8b617683fff351d`
