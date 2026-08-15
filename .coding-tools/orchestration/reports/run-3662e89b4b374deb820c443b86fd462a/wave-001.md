# Orchestration Wave 1

- Run: `3662e89b4b374deb820c443b86fd462a`
- Wave: `1c84ac481fa04988960d32fb47e52b4f`
- Objective: Expose provider cost attribution status in the compact session/evidence projection so operator and research consumers cannot mistake measured-but-uncorrelated provider cost for task-attributed cost. No provider calls, no routing changes.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `d61ea8a600242a01499b16b36dcbcb11764934af41d9bc694996fe9008784570`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4400 | 2026-08-15T05:07:58.253Z | run_started |  | PREFLIGHT |  |
| 4401 | 2026-08-15T05:07:58.433Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4402 | 2026-08-15T05:07:58.589Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4403 | 2026-08-15T05:07:58.784Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4404 | 2026-08-15T05:07:58.936Z | state_transition | READY | ROUTED | reason=route_selected |
| 4405 | 2026-08-15T05:07:59.753Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6def46adeeda47709000548fa5a5ea4f |
| 4406 | 2026-08-15T05:07:59.949Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4407 | 2026-08-15T05:08:00.802Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6def46adeeda47709000548fa5a5ea4f |
| 4408 | 2026-08-15T05:08:01.024Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4409 | 2026-08-15T05:08:01.553Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=e84aa016ce35e022f55d046fba9b9add634f78209075b6c8fcb947cb213446df |
| 4410 | 2026-08-15T05:08:02.408Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=e84aa016ce35e022f55d046fba9b9add634f78209075b6c8fcb947cb213446df |
| 4411 | 2026-08-15T05:08:02.624Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a955de749fd9bc6be252b549955251a27c6e28bb0f588a01f8c255614003e3d8 |
| 4412 | 2026-08-15T05:08:13.046Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a955de749fd9bc6be252b549955251a27c6e28bb0f588a01f8c255614003e3d8 |
| 4413 | 2026-08-15T05:08:13.776Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4414 | 2026-08-15T05:08:25.704Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | e84aa016ce35e022f55d046fba9b9add634f78209075b6c8fcb947cb213446df | False | 490 | 0 |
| verify:tests | passed | a955de749fd9bc6be252b549955251a27c6e28bb0f588a01f8c255614003e3d8 | False | 9500 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 73319f43cf2046b1b9f54e751f78dc56 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | c55be5548c9d5b4a60a5586eb31f945432a399cda163c5c90688846cebade28a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `a17f092031265174d773a20a67c86a3208c5c9bab4b72817aee247b97f29d6be`
