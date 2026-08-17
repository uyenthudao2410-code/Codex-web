# Orchestration Wave 1

- Run: `9d0750fc4b1f46359440985375798cb7`
- Wave: `f6175d70a0e344caac5303353462881d`
- Objective: Continue P0.2 provenance reconciliation after the accepted negative byte-gate finding. Identify which build/run most likely produced the CURRENT dist artifacts (installer SHA256 ac923d818794213203794342d03bfd66d85707f73c93f9a624c91f5362df1, installer size 128662237, blockmap SHA256 fada63ccc8a00eeb601ceeb5373e1a79cccdeb9096550b586fe8de593a8af341, latest.yml SHA256 649badfe4ccf8c4c2495697e15c5376e9fa90f4fcad3870117c643525eb5cd9f, releaseDate 2026-08-17T02:51:15.475Z). Search durable orchestration/task history and release documents for that artifact identity, size, timestamp, or the dist/build command that produced it. Determine whether current dist is an older valid artifact overwritten into place, a later unrelated package build, or unexplained drift. Do not mutate, rebuild, publish, or start P0.3. Return the smallest scientifically defensible remediation path for P0.2.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `a66fcbd249744d211a29486393c6edaea09b58ef041a720131fa437d983832dd`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14146 | 2026-08-17T14:10:50.505Z | run_started |  | PREFLIGHT |  |
| 14147 | 2026-08-17T14:10:55.636Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14148 | 2026-08-17T14:13:16.561Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14149 | 2026-08-17T14:13:16.686Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14150 | 2026-08-17T14:13:16.803Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 14151 | 2026-08-17T14:13:16.928Z | state_transition | READY | ROUTED | reason=route_selected |
| 14152 | 2026-08-17T14:13:17.488Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6d39f7c170cf49e1a0a024b63afcab4f |
| 14153 | 2026-08-17T14:13:17.627Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14154 | 2026-08-17T14:13:18.179Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6d39f7c170cf49e1a0a024b63afcab4f |
| 14155 | 2026-08-17T14:13:18.295Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14156 | 2026-08-17T14:13:18.785Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f434cb44fc3eccec; input_fingerprint=5264f230bfda9cf40ceec528546e97adc46ee007997d18896beeafc85e5708f4 |
| 14157 | 2026-08-17T14:13:19.028Z | managed_process_admitted |  |  | owner=default |
| 14158 | 2026-08-17T14:13:19.297Z | managed_process_started |  |  | owner=default |
| 14159 | 2026-08-17T14:13:19.651Z | managed_process_terminal |  |  | owner=default |
| 14160 | 2026-08-17T14:13:19.916Z | proof_recorded |  |  | stage_id=check:f434cb44fc3eccec; status=passed; cache_hit=False; input_fingerprint=5264f230bfda9cf40ceec528546e97adc46ee007997d18896beeafc85e5708f4 |
| 14161 | 2026-08-17T14:13:20.026Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0a0c5364ef2b05f0; input_fingerprint=62f8b261eee671b71b1ae778eb552ed23567a6c208c58930371715b066abb593 |
| 14162 | 2026-08-17T14:13:20.268Z | managed_process_admitted |  |  | owner=default |
| 14163 | 2026-08-17T14:13:20.488Z | managed_process_started |  |  | owner=default |
| 14164 | 2026-08-17T14:13:20.925Z | managed_process_terminal |  |  | owner=default |
| 14165 | 2026-08-17T14:13:21.196Z | proof_recorded |  |  | stage_id=check:0a0c5364ef2b05f0; status=passed; cache_hit=False; input_fingerprint=62f8b261eee671b71b1ae778eb552ed23567a6c208c58930371715b066abb593 |
| 14166 | 2026-08-17T14:13:21.320Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ef2c41710016bba8; input_fingerprint=1bd10ab766cb972b2028d3a3263ab9a31d0c8f84224d69bad6dc88b410693022 |
| 14167 | 2026-08-17T14:13:21.544Z | managed_process_admitted |  |  | owner=default |
| 14168 | 2026-08-17T14:13:21.760Z | managed_process_started |  |  | owner=default |
| 14169 | 2026-08-17T14:13:43.901Z | managed_process_terminal |  |  | owner=default |
| 14170 | 2026-08-17T14:13:44.135Z | proof_recorded |  |  | stage_id=check:ef2c41710016bba8; status=passed; cache_hit=False; input_fingerprint=1bd10ab766cb972b2028d3a3263ab9a31d0c8f84224d69bad6dc88b410693022 |
| 14171 | 2026-08-17T14:13:44.248Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8d7d2cb826b62636; input_fingerprint=4f499d932a6ece60f7819c08b56442e79c6d4ee8cfa10cff2783588be5bf1247 |
| 14172 | 2026-08-17T14:13:44.518Z | managed_process_admitted |  |  | owner=default |
| 14173 | 2026-08-17T14:13:44.844Z | managed_process_started |  |  | owner=default |
| 14174 | 2026-08-17T14:13:49.810Z | managed_process_terminal |  |  | owner=default |
| 14175 | 2026-08-17T14:13:50.090Z | proof_recorded |  |  | stage_id=check:8d7d2cb826b62636; status=passed; cache_hit=False; input_fingerprint=4f499d932a6ece60f7819c08b56442e79c6d4ee8cfa10cff2783588be5bf1247 |
| 14176 | 2026-08-17T14:13:50.221Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8944c08024cd307d; input_fingerprint=21d66411e7bab1d78b99c5791fe1c547a9858f607d4fc954723220082ad004ea |
| 14177 | 2026-08-17T14:13:50.465Z | managed_process_admitted |  |  | owner=default |
| 14178 | 2026-08-17T14:13:50.691Z | managed_process_started |  |  | owner=default |
| 14179 | 2026-08-17T14:13:51.051Z | managed_process_terminal |  |  | owner=default |
| 14180 | 2026-08-17T14:13:51.351Z | proof_recorded |  |  | stage_id=check:8944c08024cd307d; status=passed; cache_hit=False; input_fingerprint=21d66411e7bab1d78b99c5791fe1c547a9858f607d4fc954723220082ad004ea |
| 14181 | 2026-08-17T14:13:51.462Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ccaa9c9c633bcaae; input_fingerprint=ab8b5f343f7f9515270cc741d1adcc26fa6270d26416aaec0ace75d75fbb193c |
| 14182 | 2026-08-17T14:13:51.701Z | managed_process_admitted |  |  | owner=default |
| 14183 | 2026-08-17T14:13:51.935Z | managed_process_started |  |  | owner=default |
| 14184 | 2026-08-17T14:13:52.285Z | managed_process_terminal |  |  | owner=default |
| 14185 | 2026-08-17T14:13:52.553Z | proof_recorded |  |  | stage_id=check:ccaa9c9c633bcaae; status=passed; cache_hit=False; input_fingerprint=ab8b5f343f7f9515270cc741d1adcc26fa6270d26416aaec0ace75d75fbb193c |
| 14186 | 2026-08-17T14:13:52.721Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14187 | 2026-08-17T14:14:39.123Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14188 | 2026-08-17T14:14:39.386Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f434cb44fc3eccec | passed | 5264f230bfda9cf40ceec528546e97adc46ee007997d18896beeafc85e5708f4 | False | 870 | 0 |
| check:0a0c5364ef2b05f0 | passed | 62f8b261eee671b71b1ae778eb552ed23567a6c208c58930371715b066abb593 | False | 919 | 0 |
| check:ef2c41710016bba8 | passed | 1bd10ab766cb972b2028d3a3263ab9a31d0c8f84224d69bad6dc88b410693022 | False | 22597 | 0 |
| check:8d7d2cb826b62636 | passed | 4f499d932a6ece60f7819c08b56442e79c6d4ee8cfa10cff2783588be5bf1247 | False | 5581 | 0 |
| check:8944c08024cd307d | passed | 21d66411e7bab1d78b99c5791fe1c547a9858f607d4fc954723220082ad004ea | False | 869 | 0 |
| check:ccaa9c9c633bcaae | passed | ab8b5f343f7f9515270cc741d1adcc26fa6270d26416aaec0ace75d75fbb193c | False | 837 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| afc1b9547dec4e969f9f5d60532a4aef | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 826653e628bba8fd6fd0c73f266220d3e867446bc13a8b673ccc7290aec49aa4 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `31a56cba10e984db4f3a424cc385458ed79d5c97c33b6eef555efc90471fb464`
