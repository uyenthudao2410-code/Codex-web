# Orchestration Wave 2

- Run: `214411ecb15d4d3a9f24f2be976d40a0`
- Wave: `a33cd14ce4754d8f9990b2d64c2e731f`
- Objective: Complete the S2 W0/W2 closeout without additional semantic source changes. Reuse the already accepted W1 proof and W2A proof. Verify the pre-existing authenticated bounded artifact read/resource path and upload abort/finalization invariants with exact focused tests; record the evidence-backed W0 decision that W2 export/resource is already present and richer artifact provenance is deferred to W9 because artifact_refs already supplies content-free owner/source/hash locators and no current P0 consumer requires a second registry. Preserve the accepted W2A dirty source.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `352112c812fed31ede3785ed31d32c08a36434415561d258be0a270bd105b139`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24317 | 2026-08-20T15:45:08.513Z | wave_replanned |  | PREFLIGHT | reason=Previous wave used --lib for the binary-only webcodex-runner package and failed before any test ran. Correct the Cargo target selection; scope and source remain unchanged. |
| 24318 | 2026-08-20T15:45:08.671Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24319 | 2026-08-20T15:45:08.838Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24320 | 2026-08-20T15:45:08.988Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 24321 | 2026-08-20T15:45:09.139Z | state_transition | READY | ROUTED | reason=route_selected |
| 24322 | 2026-08-20T15:45:09.639Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c4c252a799994ecd98c64f1d894f07ed |
| 24323 | 2026-08-20T15:45:09.839Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24324 | 2026-08-20T15:45:10.357Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c4c252a799994ecd98c64f1d894f07ed |
| 24325 | 2026-08-20T15:45:10.498Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24326 | 2026-08-20T15:45:10.904Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9605d74b303f511c; input_fingerprint=8d89b35ec863104951eb2250fd18e81de3e33099a9b78117d5a4a08757326ae3 |
| 24327 | 2026-08-20T15:45:11.331Z | managed_process_admitted |  |  | owner=default |
| 24328 | 2026-08-20T15:45:11.739Z | managed_process_started |  |  | owner=default |
| 24329 | 2026-08-20T15:46:10.407Z | managed_process_terminal |  |  | owner=default |
| 24330 | 2026-08-20T15:46:11.437Z | proof_recorded |  |  | stage_id=check:9605d74b303f511c; status=passed; cache_hit=False; input_fingerprint=8d89b35ec863104951eb2250fd18e81de3e33099a9b78117d5a4a08757326ae3 |
| 24331 | 2026-08-20T15:46:11.479Z | proof_cache_miss |  |  | reason=cold; stage_id=check:09f7d01d3fd152fc; input_fingerprint=b561b1ef7bcb3c96e2c367b10f7c221de75a50458cd688f97e8ac27ca5e56fee |
| 24332 | 2026-08-20T15:46:11.888Z | managed_process_admitted |  |  | owner=default |
| 24333 | 2026-08-20T15:46:12.803Z | managed_process_started |  |  | owner=default |
| 24334 | 2026-08-20T15:46:13.754Z | managed_process_terminal |  |  | owner=default |
| 24335 | 2026-08-20T15:46:14.123Z | proof_recorded |  |  | stage_id=check:09f7d01d3fd152fc; status=passed; cache_hit=False; input_fingerprint=b561b1ef7bcb3c96e2c367b10f7c221de75a50458cd688f97e8ac27ca5e56fee |
| 24336 | 2026-08-20T15:46:14.287Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=35b2fea5d54df6a8f6417870071d9f4007328ffaa2ac99c0249520f27978dd5d |
| 24337 | 2026-08-20T15:46:15.243Z | managed_process_admitted |  |  | owner=default |
| 24338 | 2026-08-20T15:46:15.564Z | managed_process_started |  |  | owner=default |
| 24339 | 2026-08-20T15:49:20.231Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24340 | 2026-08-20T15:49:21.047Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=35b2fea5d54df6a8f6417870071d9f4007328ffaa2ac99c0249520f27978dd5d |
| 24341 | 2026-08-20T15:49:21.441Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 24342 | 2026-08-20T15:49:22.063Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 24343 | 2026-08-20T15:49:22.497Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9605d74b303f511c | passed | 8d89b35ec863104951eb2250fd18e81de3e33099a9b78117d5a4a08757326ae3 | False | 59983 | 0 |
| check:09f7d01d3fd152fc | passed | b561b1ef7bcb3c96e2c367b10f7c221de75a50458cd688f97e8ac27ca5e56fee | False | 2290 | 0 |
| verify:tests | failed | 35b2fea5d54df6a8f6417870071d9f4007328ffaa2ac99c0249520f27978dd5d | False | 185750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `164`
- Chain head: `bc77171a11aab920f2f04bc810a4a98b96268bfb7b2116e23949f189ab5dfd4f`
