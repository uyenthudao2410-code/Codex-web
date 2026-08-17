# Orchestration Wave 1

- Run: `4755a66728bf42ed92e2692d15212391`
- Wave: `0f2ce962fa8b4dcdbb1e1087cfcad7e7`
- Objective: Close P0.1 repository/runtime-evidence hygiene. Add exact .gitignore rules for the one-shot host correlation pending/binding files and SQLite ledger WAL/SHM sidecars. Preserve the tracked canonical .coding-tools/orchestration/ledger.sqlite3. The accidentally tracked pending-turn file is already deleted in the worktree; keep that deletion so it leaves source control on the next commit. Do not delete or modify any current live chatweb-host-turn-binding.json file; it must simply become ignored. Do not alter other runtime evidence or source. Prove the exact ignore behavior, expected tracked/deleted state, canonical ledger tracking, source-root cleanliness, and diff hygiene.
- Mode: `mcp_only`
- Base HEAD: `3059b218989fda8ebf217d121cd6e8f74a71587d`
- Worktree fingerprint: `35004ce4fb8844014c1b3aaef091924a303ff431ed63a0a0f38f13132aa854a2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12122 | 2026-08-17T07:47:27.586Z | run_started |  | PREFLIGHT |  |
| 12123 | 2026-08-17T07:47:28.020Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12124 | 2026-08-17T07:47:28.131Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12125 | 2026-08-17T07:47:28.291Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12126 | 2026-08-17T07:47:28.460Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 12127 | 2026-08-17T07:47:28.647Z | state_transition | READY | ROUTED | reason=route_selected |
| 12128 | 2026-08-17T07:47:29.118Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f31064f2de26422ca77b5158be4c0f81 |
| 12129 | 2026-08-17T07:47:29.294Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12130 | 2026-08-17T07:47:29.867Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f31064f2de26422ca77b5158be4c0f81 |
| 12131 | 2026-08-17T07:47:30.020Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12132 | 2026-08-17T07:47:30.347Z | proof_cache_miss |  |  | reason=cold; stage_id=check:65fcb8a67ecb5c11; input_fingerprint=b0b72c9d1b83b130622866688a400ecaf6e36ba7cd14065e45a544a3dd9d495d |
| 12133 | 2026-08-17T07:47:30.707Z | managed_process_admitted |  |  | owner=default |
| 12134 | 2026-08-17T07:47:30.994Z | managed_process_started |  |  | owner=default |
| 12135 | 2026-08-17T07:47:31.411Z | managed_process_terminal |  |  | owner=default |
| 12136 | 2026-08-17T07:47:31.744Z | proof_recorded |  |  | stage_id=check:65fcb8a67ecb5c11; status=passed; cache_hit=False; input_fingerprint=b0b72c9d1b83b130622866688a400ecaf6e36ba7cd14065e45a544a3dd9d495d |
| 12137 | 2026-08-17T07:47:31.901Z | proof_cache_miss |  |  | reason=cold; stage_id=check:22472cf448f1454d; input_fingerprint=46923b20606d2baa4f91afabc7b1c3d9887a0339c1a81847d6df23077d86047b |
| 12138 | 2026-08-17T07:47:32.223Z | managed_process_admitted |  |  | owner=default |
| 12139 | 2026-08-17T07:47:32.515Z | managed_process_started |  |  | owner=default |
| 12140 | 2026-08-17T07:47:32.927Z | managed_process_terminal |  |  | owner=default |
| 12141 | 2026-08-17T07:47:33.238Z | proof_recorded |  |  | stage_id=check:22472cf448f1454d; status=passed; cache_hit=False; input_fingerprint=46923b20606d2baa4f91afabc7b1c3d9887a0339c1a81847d6df23077d86047b |
| 12142 | 2026-08-17T07:47:33.417Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6e062d85e5743450; input_fingerprint=da792c1da3161a442a31c89a720f750ba2edb48fa85922be10b5dbb4347757af |
| 12143 | 2026-08-17T07:47:33.742Z | managed_process_admitted |  |  | owner=default |
| 12144 | 2026-08-17T07:47:34.036Z | managed_process_started |  |  | owner=default |
| 12145 | 2026-08-17T07:47:34.460Z | managed_process_terminal |  |  | owner=default |
| 12146 | 2026-08-17T07:47:34.776Z | proof_recorded |  |  | stage_id=check:6e062d85e5743450; status=passed; cache_hit=False; input_fingerprint=da792c1da3161a442a31c89a720f750ba2edb48fa85922be10b5dbb4347757af |
| 12147 | 2026-08-17T07:47:34.948Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5d2bd3e0ac5171d0; input_fingerprint=6c2330a8c31e5532da7d60a14c1dfbd84efd5ad9170fc986ce8b2cff38725b7d |
| 12148 | 2026-08-17T07:47:35.318Z | managed_process_admitted |  |  | owner=default |
| 12149 | 2026-08-17T07:47:35.602Z | managed_process_started |  |  | owner=default |
| 12150 | 2026-08-17T07:47:36.086Z | managed_process_terminal |  |  | owner=default |
| 12151 | 2026-08-17T07:47:36.417Z | proof_recorded |  |  | stage_id=check:5d2bd3e0ac5171d0; status=passed; cache_hit=False; input_fingerprint=6c2330a8c31e5532da7d60a14c1dfbd84efd5ad9170fc986ce8b2cff38725b7d |
| 12152 | 2026-08-17T07:47:36.614Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e95d8ff96949c991; input_fingerprint=1fc70ed789af92d87e526430385f562a3bd5238f4486a1a91069eaffd00328ef |
| 12153 | 2026-08-17T07:47:36.958Z | managed_process_admitted |  |  | owner=default |
| 12154 | 2026-08-17T07:47:37.261Z | managed_process_started |  |  | owner=default |
| 12155 | 2026-08-17T07:47:37.736Z | managed_process_terminal |  |  | owner=default |
| 12156 | 2026-08-17T07:47:38.061Z | proof_recorded |  |  | stage_id=check:e95d8ff96949c991; status=passed; cache_hit=False; input_fingerprint=1fc70ed789af92d87e526430385f562a3bd5238f4486a1a91069eaffd00328ef |
| 12157 | 2026-08-17T07:47:38.516Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12158 | 2026-08-17T07:47:47.609Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12159 | 2026-08-17T07:47:47.925Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:65fcb8a67ecb5c11 | passed | b0b72c9d1b83b130622866688a400ecaf6e36ba7cd14065e45a544a3dd9d495d | False | 1059 | 0 |
| check:22472cf448f1454d | passed | 46923b20606d2baa4f91afabc7b1c3d9887a0339c1a81847d6df23077d86047b | False | 1034 | 0 |
| check:6e062d85e5743450 | passed | da792c1da3161a442a31c89a720f750ba2edb48fa85922be10b5dbb4347757af | False | 1076 | 0 |
| check:5d2bd3e0ac5171d0 | passed | 6c2330a8c31e5532da7d60a14c1dfbd84efd5ad9170fc986ce8b2cff38725b7d | False | 1136 | 0 |
| check:e95d8ff96949c991 | passed | 1fc70ed789af92d87e526430385f562a3bd5238f4486a1a91069eaffd00328ef | False | 1089 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| cdbb2c6c67f04db6a7317c0201d90c9c | accepted | 3059b218989fda8ebf217d121cd6e8f74a71587d | fe414a7833a3e9c6e02a14e876c16b3192c17015cb0eaa2081de7489f6b9b217 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `feafadc51a3bff0bfae65c4fe299d3011b7a566b6abfc5c662f1b142b68e8bad`
