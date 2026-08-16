# Orchestration Wave 2

- Run: `c0e53aa707614fdc83e1a51a7e3e7d4a`
- Wave: `ef78b3ae7cad4f51b3df5d16fdcc6aaf`
- Objective: Design the final non-linker-heavy R2B behavior oracle on the current accepted implementation. Do not modify files or run commands in prepare. Inspect only the server-first compute placement adapter, Cargo validation dispatch wiring, existing server_first_* tests, webcodex-core placement policy/tests, and Cargo target layout. Determine whether the four required behaviors (distinct opted-in exact target dispatch; source runner never chosen as compute target; ineligible candidates fall back to source; offload excludes cargo_fmt/short/sandboxed validation) can be proven by an existing small package/target. If not, identify the smallest pure helper boundary that can be moved or exposed to webcodex-core for lightweight tests without changing runtime semantics. Preserve all unrelated WIP and do not propose the root monolithic test binary.
- Mode: `mcp_only`
- Base HEAD: `48e91a1cc12e9d6fe9c71f053404476132007468`
- Worktree fingerprint: `838e5fac71d8714c52edd8bf14a6f90d99ef6215d6def160e247cd66ff5a2a02`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8768 | 2026-08-16T14:38:43.612Z | wave_replanned |  | PREFLIGHT | reason=The prior wave mutated the intended two files and then stopped at the first proof because rustfmt requested only deterministic whitespace/line wrapping. This replacement wave changes only those exact formatting differences before rerunning the same bounded non-linking proof chain; no semantic retry is being attempted unchanged. |
| 8769 | 2026-08-16T14:38:43.737Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8770 | 2026-08-16T14:38:43.851Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8771 | 2026-08-16T14:38:43.953Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8772 | 2026-08-16T14:38:44.128Z | state_transition | READY | ROUTED | reason=route_selected |
| 8773 | 2026-08-16T14:38:44.550Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=fbf21f1940f54471990bd0e9300d740e |
| 8774 | 2026-08-16T14:38:44.653Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8775 | 2026-08-16T14:38:45.162Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=fbf21f1940f54471990bd0e9300d740e |
| 8776 | 2026-08-16T14:38:45.287Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8777 | 2026-08-16T14:38:45.705Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=823c4d2ed8fa81ebb853a4f675f1d35a9d795557f808a72f63ca75463adfdf3b |
| 8778 | 2026-08-16T14:38:45.953Z | managed_process_admitted |  |  | owner=default |
| 8779 | 2026-08-16T14:38:46.173Z | managed_process_started |  |  | owner=default |
| 8780 | 2026-08-16T14:38:51.819Z | managed_process_terminal |  |  | owner=default |
| 8781 | 2026-08-16T14:38:52.095Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=823c4d2ed8fa81ebb853a4f675f1d35a9d795557f808a72f63ca75463adfdf3b |
| 8782 | 2026-08-16T14:38:52.257Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c6e30766227ab9c6; input_fingerprint=9ad0d63f907bed6a5aec04d277feb9be18775fc96f1802ee4a3556721a30199a |
| 8783 | 2026-08-16T14:38:52.597Z | managed_process_admitted |  |  | owner=default |
| 8784 | 2026-08-16T14:38:52.878Z | managed_process_started |  |  | owner=default |
| 8785 | 2026-08-16T14:39:02.882Z | managed_process_terminal |  |  | owner=default |
| 8786 | 2026-08-16T14:39:03.138Z | proof_recorded |  |  | stage_id=check:c6e30766227ab9c6; status=passed; cache_hit=False; input_fingerprint=9ad0d63f907bed6a5aec04d277feb9be18775fc96f1802ee4a3556721a30199a |
| 8787 | 2026-08-16T14:39:03.272Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bcb9509776b8d535; input_fingerprint=3be29c01d58e96bb9a169afba5f2f0994953abf9aafca89ffa200ce61c154784 |
| 8788 | 2026-08-16T14:39:03.625Z | managed_process_admitted |  |  | owner=default |
| 8789 | 2026-08-16T14:39:03.858Z | managed_process_started |  |  | owner=default |
| 8790 | 2026-08-16T14:39:29.822Z | managed_process_terminal |  |  | owner=default |
| 8791 | 2026-08-16T14:39:30.052Z | proof_recorded |  |  | stage_id=check:bcb9509776b8d535; status=passed; cache_hit=False; input_fingerprint=3be29c01d58e96bb9a169afba5f2f0994953abf9aafca89ffa200ce61c154784 |
| 8792 | 2026-08-16T14:39:30.176Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:731a566acabcb042; input_fingerprint=af5b17d90fc4b2f5226e40b1db1e0ee183c0992752a20ac83c449d70f0e81057 |
| 8793 | 2026-08-16T14:39:30.692Z | managed_process_admitted |  |  | owner=default |
| 8794 | 2026-08-16T14:39:30.913Z | managed_process_started |  |  | owner=default |
| 8795 | 2026-08-16T14:40:02.133Z | managed_process_terminal |  |  | owner=default |
| 8796 | 2026-08-16T14:40:02.386Z | proof_recorded |  |  | stage_id=check:731a566acabcb042; status=passed; cache_hit=False; input_fingerprint=af5b17d90fc4b2f5226e40b1db1e0ee183c0992752a20ac83c449d70f0e81057 |
| 8797 | 2026-08-16T14:40:02.853Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8798 | 2026-08-16T14:40:17.848Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8799 | 2026-08-16T14:40:18.373Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | passed | 823c4d2ed8fa81ebb853a4f675f1d35a9d795557f808a72f63ca75463adfdf3b | False | 6109 | 0 |
| check:c6e30766227ab9c6 | passed | 9ad0d63f907bed6a5aec04d277feb9be18775fc96f1802ee4a3556721a30199a | False | 10616 | 0 |
| check:bcb9509776b8d535 | passed | 3be29c01d58e96bb9a169afba5f2f0994953abf9aafca89ffa200ce61c154784 | False | 26549 | 0 |
| check:731a566acabcb042 | passed | af5b17d90fc4b2f5226e40b1db1e0ee183c0992752a20ac83c449d70f0e81057 | False | 31956 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 4929a7339a1c4fb9956d3d6700827852 | accepted | 48e91a1cc12e9d6fe9c71f053404476132007468 | 12d569acf513b05218509a60a12b89779dc2724079a02c2e03cf5837edacabb9 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `24afe0f64236a2cc0eee21d43aa0e2eeb45f0f31649dfeba38e623a42816a5b0`
