# Orchestration Wave 1

- Run: `bba5a6782a66499babfb12e548e8982a`
- Wave: `165fcc9628434970a653055c65414f29`
- Objective: Fix the demonstrated workspace checkpoint restore validation fail-open for Git C-quoted diff paths. Current changed_paths_from_diff only understands unquoted `diff --git a/... b/...` and `+++ b/...` / `--- a/...`; a quoted sensitive path can therefore produce zero extracted paths and bypass validate_checkpoint_diff before git apply. Preserve legitimate non-ASCII paths: do not solve this by blanket-rejecting all quoted paths if a small correct decoder/extractor is practical. Find the smallest causal implementation, preferably in crates/webcodex-workspace/src/workspace_checkpoint.rs with focused unit tests in the same file. Reuse an existing Git quoted-path decoder/helper if one already exists; otherwise implement only the C-style path decoding needed for Git patch headers, fail closed on malformed/undecodable quoted paths, and keep ordinary path behavior unchanged. Validate both: a quoted sensitive path is rejected, and a legitimate quoted non-ASCII path is extracted/accepted. Do not touch current dirty paths, commit, push, restart, or open P5.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `ee5413e1b1f02542ed4266856fb712d31d3000851741559d423a14e387e388b3`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18280 | 2026-08-18T21:49:09.491Z | run_started |  | PREFLIGHT |  |
| 18281 | 2026-08-18T21:49:14.843Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18282 | 2026-08-18T21:51:21.867Z | solution_shadow_recommended |  |  |  |
| 18283 | 2026-08-18T21:53:00.945Z | managed_process_admitted |  |  | owner=default |
| 18284 | 2026-08-18T21:53:01.294Z | managed_process_started |  |  | owner=default |
| 18285 | 2026-08-18T21:53:01.729Z | managed_process_terminal |  |  | owner=default |
| 18286 | 2026-08-18T21:53:12.323Z | managed_process_admitted |  |  | owner=default |
| 18287 | 2026-08-18T21:53:12.544Z | managed_process_started |  |  | owner=default |
| 18288 | 2026-08-18T21:53:12.906Z | managed_process_terminal |  |  | owner=default |
| 18289 | 2026-08-18T21:53:34.069Z | managed_process_admitted |  |  | owner=default |
| 18290 | 2026-08-18T21:53:34.322Z | managed_process_started |  |  | owner=default |
| 18291 | 2026-08-18T21:53:34.739Z | managed_process_terminal |  |  | owner=default |
| 18292 | 2026-08-18T21:54:06.488Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 18293 | 2026-08-18T21:54:06.681Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 18294 | 2026-08-18T21:54:06.827Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 18295 | 2026-08-18T21:54:06.938Z | state_transition | READY | ROUTED | reason=route_selected |
| 18296 | 2026-08-18T21:54:07.362Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8fb3aaa316e3418683b18827a2b8c5df |
| 18297 | 2026-08-18T21:54:07.514Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 18298 | 2026-08-18T21:54:07.977Z | solution_shadow_patch_surface_observed |  |  |  |
| 18299 | 2026-08-18T21:54:08.147Z | solution_shadow_patch_surface_observed |  |  |  |
| 18300 | 2026-08-18T21:54:08.299Z | solution_shadow_patch_surface_observed |  |  |  |
| 18301 | 2026-08-18T21:54:08.489Z | solution_shadow_patch_surface_observed |  |  |  |
| 18302 | 2026-08-18T21:54:08.697Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8fb3aaa316e3418683b18827a2b8c5df |
| 18303 | 2026-08-18T21:54:08.816Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 18304 | 2026-08-18T21:54:09.193Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bde650d74cca7cd9; input_fingerprint=8ef68f3b5b8a72d07f80d9aea416313c52e2cdb4052fa8a2fbe7fe7acf09cece |
| 18305 | 2026-08-18T21:54:09.608Z | managed_process_admitted |  |  | owner=default |
| 18306 | 2026-08-18T21:54:09.839Z | managed_process_started |  |  | owner=default |
| 18307 | 2026-08-18T21:54:10.544Z | managed_process_terminal |  |  | owner=default |
| 18308 | 2026-08-18T21:54:10.881Z | proof_recorded |  |  | stage_id=check:bde650d74cca7cd9; status=failed; cache_hit=False; input_fingerprint=8ef68f3b5b8a72d07f80d9aea416313c52e2cdb4052fa8a2fbe7fe7acf09cece |
| 18309 | 2026-08-18T21:54:11.055Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 18310 | 2026-08-18T21:54:11.247Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 18311 | 2026-08-18T21:54:11.466Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:bde650d74cca7cd9 | failed | 8ef68f3b5b8a72d07f80d9aea416313c52e2cdb4052fa8a2fbe7fe7acf09cece | False | 1240 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `d27dee9c17d6884cb618c1c10b55c1e49218133bf4b27bf9191ae4a761366628`
