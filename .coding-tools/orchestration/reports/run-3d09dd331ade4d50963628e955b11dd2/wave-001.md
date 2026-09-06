# Orchestration Wave 1

- Run: `3d09dd331ade4d50963628e955b11dd2`
- Wave: `7a28674f1efd472f8201294da6da5f5b`
- Objective: Explicit continuation correction after predecessor checkpoint e5673e0ded354257a7c3309dfc1691b0 exposed DEV_UI_CHECKPOINT_NOT_ACTIVATABLE from the unnecessary package.json test alias. Apply only the smallest correction: remove test:recovery:installed from package.json and remove only the exact corresponding package-script assertion from tests/build-verification.test.js. Retain scripts/installed-recovery-smoke.js unchanged and retain CODEX_PACKAGED_APP_ROOT support in scripts/packaged-recovery-smoke.js unchanged. Validate the direct harness remains repeatable and npm run dev:status has no Electron UI revision mismatch attributable to this packet. Do not bypass activation; do not touch docs/research/260905*, unrelated source/evidence, Git delivery, release/deploy, experiments, stale-run reconciliation, or ACK report cf5cefca8d2f505e507929f1c8e44143c4a94c2e744c39efa1141bc448eae70c.
- Objective revision: `1`
- Objective SHA-256: `55a365fb8bc9b007690ed206af38a6b34348f4ad71b5034d095549d4eab8f1e0`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `ef5aa3b74f91b5f5167f002b27a04e43c895180f`
- Worktree fingerprint: `76ccaeec1f14fd1a27221ced37386f8b495dfc6743ae9b5fd01f104c5f39ca72`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42151 | 2026-09-06T10:01:22.694Z | run_started |  | PREFLIGHT |  |
| 42152 | 2026-09-06T10:01:23.116Z | observation_span_recorded |  |  |  |
| 42153 | 2026-09-06T10:01:24.196Z | observation_span_recorded |  |  |  |
| 42154 | 2026-09-06T10:01:24.391Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42155 | 2026-09-06T10:01:24.583Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42156 | 2026-09-06T10:01:24.766Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42157 | 2026-09-06T10:01:24.976Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 42158 | 2026-09-06T10:01:25.199Z | state_transition | READY | ROUTED | reason=route_selected |
| 42159 | 2026-09-06T10:01:25.407Z | observation_span_recorded |  |  |  |
| 42160 | 2026-09-06T10:01:26.599Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=649569cdee9a4282a50c1106884b943d |
| 42161 | 2026-09-06T10:01:26.811Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42162 | 2026-09-06T10:01:28.108Z | existing_file_adoption_observed |  |  |  |
| 42163 | 2026-09-06T10:01:28.365Z | patch_surface_observed |  |  |  |
| 42164 | 2026-09-06T10:01:28.597Z | observation_span_recorded |  |  |  |
| 42165 | 2026-09-06T10:01:28.936Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=649569cdee9a4282a50c1106884b943d |
| 42166 | 2026-09-06T10:01:29.078Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42167 | 2026-09-06T10:01:30.055Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:719395034be5a3ca; input_fingerprint=58b8f8072721d3838fa397de19bfadc0a31b42bb9c2d6da694bf3383ed893889 |
| 42168 | 2026-09-06T10:01:30.463Z | managed_process_admitted |  |  | owner=default |
| 42169 | 2026-09-06T10:01:30.911Z | managed_process_started |  |  | owner=default |
| 42170 | 2026-09-06T10:01:31.360Z | managed_process_terminal |  |  | owner=default |
| 42171 | 2026-09-06T10:01:31.721Z | proof_recorded |  |  | stage_id=check:719395034be5a3ca; status=passed; cache_hit=False; input_fingerprint=58b8f8072721d3838fa397de19bfadc0a31b42bb9c2d6da694bf3383ed893889 |
| 42172 | 2026-09-06T10:01:31.957Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:89c42cc96b3eb71c; input_fingerprint=34bf5208a3e609e17f73da7a3ba7145b91534b86ec757e60fcb6459633b5a792 |
| 42173 | 2026-09-06T10:01:32.411Z | managed_process_admitted |  |  | owner=default |
| 42174 | 2026-09-06T10:01:32.692Z | managed_process_started |  |  | owner=default |
| 42175 | 2026-09-06T10:01:33.283Z | managed_process_terminal |  |  | owner=default |
| 42176 | 2026-09-06T10:01:33.629Z | proof_recorded |  |  | stage_id=check:89c42cc96b3eb71c; status=passed; cache_hit=False; input_fingerprint=34bf5208a3e609e17f73da7a3ba7145b91534b86ec757e60fcb6459633b5a792 |
| 42177 | 2026-09-06T10:01:33.823Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bdda12fe7067ef68; input_fingerprint=cbbc26e506ba82d7a9bad2242394b11ba9f924545274f3bb0202ea7739dbdd86 |
| 42178 | 2026-09-06T10:01:34.213Z | managed_process_admitted |  |  | owner=default |
| 42179 | 2026-09-06T10:01:34.534Z | managed_process_started |  |  | owner=default |
| 42180 | 2026-09-06T10:01:34.995Z | managed_process_terminal |  |  | owner=default |
| 42181 | 2026-09-06T10:01:35.307Z | proof_recorded |  |  | stage_id=check:bdda12fe7067ef68; status=passed; cache_hit=False; input_fingerprint=cbbc26e506ba82d7a9bad2242394b11ba9f924545274f3bb0202ea7739dbdd86 |
| 42182 | 2026-09-06T10:01:35.504Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:c258b46a1eabc99b; input_fingerprint=eca46e40230e3213744277666467f7cccfae00d1ae53001e73d9453c006e3050 |
| 42183 | 2026-09-06T10:01:36.023Z | managed_process_admitted |  |  | owner=default |
| 42184 | 2026-09-06T10:01:36.419Z | managed_process_started |  |  | owner=default |
| 42185 | 2026-09-06T10:01:36.870Z | managed_process_terminal |  |  | owner=default |
| 42186 | 2026-09-06T10:01:37.201Z | proof_recorded |  |  | stage_id=check:c258b46a1eabc99b; status=passed; cache_hit=False; input_fingerprint=eca46e40230e3213744277666467f7cccfae00d1ae53001e73d9453c006e3050 |
| 42187 | 2026-09-06T10:01:37.418Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bda80ff0a48cc0e7; input_fingerprint=0d9179ba53ec0382ddb4520332fc40a3783169096e66f58e98357f888c4a7d47 |
| 42188 | 2026-09-06T10:01:37.772Z | managed_process_admitted |  |  | owner=default |
| 42189 | 2026-09-06T10:01:38.260Z | managed_process_started |  |  | owner=default |
| 42190 | 2026-09-06T10:02:03.444Z | managed_process_terminal |  |  | owner=default |
| 42191 | 2026-09-06T10:02:03.776Z | proof_recorded |  |  | stage_id=check:bda80ff0a48cc0e7; status=passed; cache_hit=False; input_fingerprint=0d9179ba53ec0382ddb4520332fc40a3783169096e66f58e98357f888c4a7d47 |
| 42192 | 2026-09-06T10:02:03.943Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:385f51573288f6e6; input_fingerprint=fc0143b66f7657bff94f7ad95b4eb9f30fcfd5ed984c3ba4e6ae99476df54bfd |
| 42193 | 2026-09-06T10:02:04.391Z | managed_process_admitted |  |  | owner=default |
| 42194 | 2026-09-06T10:02:04.748Z | managed_process_started |  |  | owner=default |
| 42195 | 2026-09-06T10:02:05.527Z | managed_process_terminal |  |  | owner=default |
| 42196 | 2026-09-06T10:02:05.851Z | proof_recorded |  |  | stage_id=check:385f51573288f6e6; status=passed; cache_hit=False; input_fingerprint=fc0143b66f7657bff94f7ad95b4eb9f30fcfd5ed984c3ba4e6ae99476df54bfd |
| 42197 | 2026-09-06T10:02:07.006Z | observation_span_recorded |  |  |  |
| 42198 | 2026-09-06T10:02:07.221Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42199 | 2026-09-06T10:02:36.383Z | managed_process_admitted |  |  | owner=default |
| 42200 | 2026-09-06T10:02:36.678Z | managed_process_started |  |  | owner=default |
| 42201 | 2026-09-06T10:02:37.287Z | managed_process_terminal |  |  | owner=default |
| 42202 | 2026-09-06T10:02:48.142Z | quality_outcome_recorded |  |  |  |
| 42203 | 2026-09-06T10:02:48.332Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42204 | 2026-09-06T10:02:48.634Z | observation_span_recorded |  |  |  |
| 42205 | 2026-09-06T10:02:48.829Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:719395034be5a3ca | passed | 58b8f8072721d3838fa397de19bfadc0a31b42bb9c2d6da694bf3383ed893889 | False | 1299 | 0 |
| check:89c42cc96b3eb71c | passed | 34bf5208a3e609e17f73da7a3ba7145b91534b86ec757e60fcb6459633b5a792 | False | 1298 | 0 |
| check:bdda12fe7067ef68 | passed | cbbc26e506ba82d7a9bad2242394b11ba9f924545274f3bb0202ea7739dbdd86 | False | 1214 | 0 |
| check:c258b46a1eabc99b | passed | eca46e40230e3213744277666467f7cccfae00d1ae53001e73d9453c006e3050 | False | 1325 | 0 |
| check:bda80ff0a48cc0e7 | passed | 0d9179ba53ec0382ddb4520332fc40a3783169096e66f58e98357f888c4a7d47 | False | 26036 | 0 |
| check:385f51573288f6e6 | passed | fc0143b66f7657bff94f7ad95b4eb9f30fcfd5ed984c3ba4e6ae99476df54bfd | False | 1525 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 84b65096ab0c4a4e98bcf07362f94540 | accepted | ef5aa3b74f91b5f5167f002b27a04e43c895180f | 2b9b7a3c974b27e143a0a31502db6c2c94f9cf8a964f773ccba5d9e1875660e6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `dafffa8a3e962298e6a8f45fe373fd0b145612ca03f6551f1878088fb34063f6`
