# Orchestration Wave 5

- Run: `0e7268b8bc324ebd972ac00819df82fa`
- Wave: `790a9591a02449e59549dc77ae110ff0`
- Objective: Audit whether the local checkout actually contains and proves the claimed PR #17 recovery/runtime identity fixes. Verify: main/HEAD and ancestry for f6018a5420c28b5da3e6effc456ee07da25a14ed, a1c664c2, 75169953; dev installation_id derived from canonical running checkout root without persisting raw path; dev A->B takeover with authenticated exact owner_pid+instance_id and descriptor TOCTOU rejection RECOVERY_DESCRIPTOR_CHANGED; legacy missing installation_id stale/bootstrap behavior; packaged fail-closed across installation identities; development startWithWindows forced false and stale dev supervisor suppression via stop.request; runtimeIdentity.js included in Recovery Host fingerprint; workspace settings passed as --workspace and not reused to infer checkout source; authorizedRoots/canonical alias behavior; .coding-tools untouched by the claimed merge. Locate the exact regression tests and authoritative commands. Do not modify files.
- Mode: `mcp_only`
- Base HEAD: `f6018a5420c28b5da3e6effc456ee07da25a14ed`
- Worktree fingerprint: `d490feb92469e93c4d8879e5f97114fc8d4b39775fb363079110b356e4920310`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16643 | 2026-08-18T08:46:01.584Z | wave_replanned |  | PREFLIGHT | reason=Final status after the green npm test revealed the nested ledger is tracked repository evidence, so deleting it would violate the repository's .coding-tools retention invariant. The strategy changes from deletion to exact binary relocation: preserve the same Git blob under root .coding-tools (which is the authorized evidence tree) while keeping the nested source-package runtime-state path absent. |
| 16644 | 2026-08-18T08:46:01.981Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16645 | 2026-08-18T08:46:02.374Z | managed_process_admitted |  |  | owner=default |
| 16646 | 2026-08-18T08:46:02.922Z | managed_process_started |  |  | owner=default |
| 16647 | 2026-08-18T08:46:03.652Z | managed_process_terminal |  |  | owner=default |
| 16648 | 2026-08-18T08:46:03.964Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 16649 | 2026-08-18T08:46:04.120Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16650 | 2026-08-18T08:46:04.343Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16651 | 2026-08-18T08:46:04.528Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 16652 | 2026-08-18T08:46:04.677Z | state_transition | READY | ROUTED | reason=route_selected |
| 16653 | 2026-08-18T08:46:05.360Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e63f767569004c1d986f665ad92a1109 |
| 16654 | 2026-08-18T08:46:05.576Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16655 | 2026-08-18T08:46:06.058Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e63f767569004c1d986f665ad92a1109 |
| 16656 | 2026-08-18T08:46:06.208Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16657 | 2026-08-18T08:46:06.659Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0540f4ae1ee6c540; input_fingerprint=8e0f150848f8ab4f4893868f170352547a3d31fc408dedce041aa477fd7deddf |
| 16658 | 2026-08-18T08:46:06.940Z | managed_process_admitted |  |  | owner=default |
| 16659 | 2026-08-18T08:46:07.253Z | managed_process_started |  |  | owner=default |
| 16660 | 2026-08-18T08:46:07.606Z | managed_process_terminal |  |  | owner=default |
| 16661 | 2026-08-18T08:46:08.314Z | proof_recorded |  |  | stage_id=check:0540f4ae1ee6c540; status=passed; cache_hit=False; input_fingerprint=8e0f150848f8ab4f4893868f170352547a3d31fc408dedce041aa477fd7deddf |
| 16662 | 2026-08-18T08:46:08.475Z | proof_cache_miss |  |  | reason=cold; stage_id=check:703fce19a99c60e9; input_fingerprint=bccd48087e9b3d48013e733c732aa23b64000327421de288217b5a05245b4508 |
| 16663 | 2026-08-18T08:46:08.792Z | managed_process_admitted |  |  | owner=default |
| 16664 | 2026-08-18T08:46:09.040Z | managed_process_started |  |  | owner=default |
| 16665 | 2026-08-18T08:46:10.940Z | managed_process_terminal |  |  | owner=default |
| 16666 | 2026-08-18T08:46:11.294Z | proof_recorded |  |  | stage_id=check:703fce19a99c60e9; status=passed; cache_hit=False; input_fingerprint=bccd48087e9b3d48013e733c732aa23b64000327421de288217b5a05245b4508 |
| 16667 | 2026-08-18T08:46:11.425Z | proof_cache_miss |  |  | reason=cold; stage_id=check:94f5f48ffe8d75f9; input_fingerprint=0259d47606088dc31e5182a63f34e6e7ea7af65a890177826e0a24222cf012f6 |
| 16668 | 2026-08-18T08:46:11.803Z | managed_process_admitted |  |  | owner=default |
| 16669 | 2026-08-18T08:46:12.214Z | managed_process_started |  |  | owner=default |
| 16670 | 2026-08-18T08:46:13.827Z | managed_process_terminal |  |  | owner=default |
| 16671 | 2026-08-18T08:46:14.159Z | proof_recorded |  |  | stage_id=check:94f5f48ffe8d75f9; status=passed; cache_hit=False; input_fingerprint=0259d47606088dc31e5182a63f34e6e7ea7af65a890177826e0a24222cf012f6 |
| 16672 | 2026-08-18T08:46:14.360Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fb80fe7271b5055c; input_fingerprint=9671c8916e19f16a8f7d792e036202331ca00be15dda01cd259b1ddafde31735 |
| 16673 | 2026-08-18T08:46:14.808Z | managed_process_admitted |  |  | owner=default |
| 16674 | 2026-08-18T08:46:15.131Z | managed_process_started |  |  | owner=default |
| 16675 | 2026-08-18T08:46:15.546Z | managed_process_terminal |  |  | owner=default |
| 16676 | 2026-08-18T08:46:15.910Z | proof_recorded |  |  | stage_id=check:fb80fe7271b5055c; status=passed; cache_hit=False; input_fingerprint=9671c8916e19f16a8f7d792e036202331ca00be15dda01cd259b1ddafde31735 |
| 16677 | 2026-08-18T08:46:16.111Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0d4a4ffcba0b92fdd0e4d4be0e474d37561538c9eff75b303160db799fdc2ff3 |
| 16678 | 2026-08-18T08:46:16.466Z | managed_process_admitted |  |  | owner=default |
| 16679 | 2026-08-18T08:46:16.721Z | managed_process_started |  |  | owner=default |
| 16680 | 2026-08-18T08:46:17.486Z | managed_process_terminal |  |  | owner=default |
| 16681 | 2026-08-18T08:46:17.824Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0d4a4ffcba0b92fdd0e4d4be0e474d37561538c9eff75b303160db799fdc2ff3 |
| 16682 | 2026-08-18T08:46:17.988Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16683 | 2026-08-18T08:47:04.272Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 16684 | 2026-08-18T08:47:04.702Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:0540f4ae1ee6c540 | passed | 8e0f150848f8ab4f4893868f170352547a3d31fc408dedce041aa477fd7deddf | False | 1394 | 0 |
| check:703fce19a99c60e9 | passed | bccd48087e9b3d48013e733c732aa23b64000327421de288217b5a05245b4508 | False | 2485 | 0 |
| check:94f5f48ffe8d75f9 | passed | 0259d47606088dc31e5182a63f34e6e7ea7af65a890177826e0a24222cf012f6 | False | 2395 | 0 |
| check:fb80fe7271b5055c | passed | 9671c8916e19f16a8f7d792e036202331ca00be15dda01cd259b1ddafde31735 | False | 1156 | 0 |
| verify:tests | passed | 0d4a4ffcba0b92fdd0e4d4be0e474d37561538c9eff75b303160db799fdc2ff3 | False | 1344 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fe1b38d65eb8470da3e471356459e388 | accepted | f6018a5420c28b5da3e6effc456ee07da25a14ed | 20ff1f0c68a7a2b2737ae415dca3c6619b9011b68eba5029e7c55f7f1d6d8330 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `060ca0a6268d2b3334e7829b2ea9b22a4448f65faa6dd34c3ef57e625695bb94`
