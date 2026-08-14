# Orchestration Wave 3

- Run: `ff4a12a96ce549d4871195fc9d77428f`
- Wave: `6388754e57ce43d7bb17cf0cbcea2912`
- Objective: Complete the remaining non-UI technical roadmap for Tools-Codex-web without changing the Smart-v3 public 8-tool contract. Implement a canonical measured UsageEvent contract/projection with provenance, measured-vs-estimated identity, cached/reasoning token counters, queue/provider/total timing and typed provider error classification; integrate existing OpenCode telemetry into that contract. Implement a Hub-side OpenCode read-only Provider Adapter that can dispatch an explicitly selected allowlisted OpenCode Go model (Flash/Pro) with a bounded prompt packet, timeout/cancel lifecycle, exact run/wave/session/model correlation, usage/cost capture, and fail-closed no-native-write semantics. Implement shadow provider routing as recommendation/evidence only (no automatic mutation or controller transfer), with durable accepted-task route/economics fields sufficient for later cohort calibration. Preserve current controller/write fencing, current routing thresholds, OpenCode worker-only role, existing concurrent UI work, and existing exact telemetry semantics. Do not touch renderer/UI files, do not restart Electron/runtime, do not change permission settings, do not run paid/provider inference solely for proof, and do not commit/push/release/deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `b948aa04e3a5fde60552498f4e3614ddb830b3ce3cbf8d4add55342925c9b5bb`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1748 | 2026-08-14T09:39:23.674Z | wave_replanned |  | PREFLIGHT | reason=The focused new test exposed that the existing secret sanitizer intentionally redacts a generic parent key named 'tokens'. Do not weaken that security boundary. Materially adjust the new UsageEvent representation to use a non-sensitive 'usage' container while preserving allowlisted numeric token leaf keys. |
| 1749 | 2026-08-14T09:39:23.854Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1750 | 2026-08-14T09:39:24.068Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1751 | 2026-08-14T09:39:24.251Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1752 | 2026-08-14T09:39:24.511Z | state_transition | READY | ROUTED | reason=route_selected |
| 1753 | 2026-08-14T09:39:25.045Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0e737f33dc154839b326dd972871b748 |
| 1754 | 2026-08-14T09:39:25.201Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1755 | 2026-08-14T09:39:26.026Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0e737f33dc154839b326dd972871b748 |
| 1756 | 2026-08-14T09:39:26.200Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1757 | 2026-08-14T09:39:27.116Z | proof_recorded |  |  | stage_id=check:9ec7b67d368443f8; status=passed; cache_hit=False; input_fingerprint=ffc543b29d7ab25561eb17989caa3a33686a077ef9f2814ed1ba615f24d35c68 |
| 1758 | 2026-08-14T09:39:27.809Z | proof_recorded |  |  | stage_id=check:cc2f1f958275bce8; status=passed; cache_hit=False; input_fingerprint=545f84904edbc1e8e930404cae2f0d4b30450837fa1de68474f0a7f7c55a78cf |
| 1759 | 2026-08-14T09:39:32.584Z | proof_recorded |  |  | stage_id=check:d68f99d3d141b6d7; status=passed; cache_hit=False; input_fingerprint=2005a4c7d196b1736116575182bfd013009f197f2e448483e3e5eaa4e585143c |
| 1760 | 2026-08-14T09:39:33.884Z | proof_recorded |  |  | stage_id=check:27d05452881c31de; status=passed; cache_hit=False; input_fingerprint=03a606f9b50bbef6eadcfd1c48800b9c53c69b0b582265625c43cd2cc386adc7 |
| 1761 | 2026-08-14T09:39:36.442Z | proof_recorded |  |  | stage_id=check:6b5eb56c39e969bc; status=passed; cache_hit=False; input_fingerprint=31c34b0bb2bf99aff05326f34f849f42cafad10bdaf6da6be917ba941d836c0a |
| 1762 | 2026-08-14T09:39:37.134Z | proof_recorded |  |  | stage_id=check:619de2c276141ae3; status=passed; cache_hit=False; input_fingerprint=8d9287c0e7c3575f66b8e76196c9039ba8ddb184dada5a209011296b4a070f2d |
| 1763 | 2026-08-14T09:39:47.664Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1764 | 2026-08-14T09:40:04.431Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9ec7b67d368443f8 | passed | ffc543b29d7ab25561eb17989caa3a33686a077ef9f2814ed1ba615f24d35c68 | False | 284 | 0 |
| check:cc2f1f958275bce8 | passed | 545f84904edbc1e8e930404cae2f0d4b30450837fa1de68474f0a7f7c55a78cf | False | 336 | 0 |
| check:d68f99d3d141b6d7 | passed | 2005a4c7d196b1736116575182bfd013009f197f2e448483e3e5eaa4e585143c | False | 4423 | 0 |
| check:27d05452881c31de | passed | 03a606f9b50bbef6eadcfd1c48800b9c53c69b0b582265625c43cd2cc386adc7 | False | 954 | 0 |
| check:6b5eb56c39e969bc | passed | 31c34b0bb2bf99aff05326f34f849f42cafad10bdaf6da6be917ba941d836c0a | False | 2183 | 0 |
| check:619de2c276141ae3 | passed | 8d9287c0e7c3575f66b8e76196c9039ba8ddb184dada5a209011296b4a070f2d | False | 360 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 47188a3ceb59414897f4e2bfc87a5243 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | 945c3e1acd98b1971f065b6488b7421c144bddd08d0d54b395b2359d2a1e622a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `98be1f371f0f6a3a76beb00d30c943e7e27fef27d4e71efeb254dab6e4fa67ed`
