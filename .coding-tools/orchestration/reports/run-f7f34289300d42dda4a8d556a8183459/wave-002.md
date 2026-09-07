# Orchestration Wave 2

- Run: `f7f34289300d42dda4a8d556a8183459`
- Wave: `9ae16cad015d409899cde342eece012f`
- Objective: Implement the user-authorized bounded exact-stale maintenance seam in Recovery Host full-clean replacement. Parse only a strict reserved reason prefix exact_stale_runs:<comma-separated 32-lowerhex-run-ids>, max 16 unique IDs. In continueReplacement, while the old canonical Coding MCP is already stopped and before orchestrator.start, sequentially run the existing reconcile_exact_stale_run.py through pythonStatus/execFile without shell: fresh preflight per ID, validate physical+logical HEX64 snapshot hashes, then reconcile with --runtime-stopped and exact expected hashes; require schema_version=1, reconciliation.chain_ok=true, and postflight target stale/RECONCILED_STALE/already_reconciled=true. Any malformed request, Python/script failure, receipt mismatch, or deadline expiry must fail the activation closed before MCP start. Ordinary restart reasons remain unchanged/no-op. Add focused tests proving sequential maintenance occurs before MCP start and malformed reserved reasons prevent start. Do not change public MCP tool schema/count, Python ledger logic, unrelated source, Git history, or external services.
- Objective revision: `1`
- Objective SHA-256: `bb863ff4cd2390b87937cb5c9bfa35cc3dd3cca0d821a04c8e4bfa934986cb9c`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `512b1aed166eb0ce7230a58de35bfb27068ccce670983fc8184791832652eebc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43010 | 2026-09-07T03:11:22.043Z | wave_replanned |  | PREFLIGHT | reason=The rejected wave established a narrower cause: only the two newly added exact-stale tests were reported to expire before reaching the maintenance seam. Replan to inspect and correct only their clock/deadline fixture, preserve the production maintenance implementation unchanged, then rerun the focused full-clean activation suite and diff check. |
| 43011 | 2026-09-07T03:11:22.331Z | observation_span_recorded |  |  |  |
| 43012 | 2026-09-07T03:11:32.480Z | observation_span_recorded |  |  |  |
| 43013 | 2026-09-07T03:11:32.681Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43014 | 2026-09-07T03:12:24.878Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43015 | 2026-09-07T03:12:25.148Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43016 | 2026-09-07T03:12:25.323Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43017 | 2026-09-07T03:12:25.480Z | state_transition | READY | ROUTED | reason=route_selected |
| 43018 | 2026-09-07T03:12:25.735Z | observation_span_recorded |  |  |  |
| 43019 | 2026-09-07T03:12:26.280Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6ace305d9a9b4ee2a984fde64b7d2ecf |
| 43020 | 2026-09-07T03:12:26.524Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43021 | 2026-09-07T03:12:27.147Z | patch_surface_observed |  |  |  |
| 43022 | 2026-09-07T03:12:27.363Z | observation_span_recorded |  |  |  |
| 43023 | 2026-09-07T03:12:27.630Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6ace305d9a9b4ee2a984fde64b7d2ecf |
| 43024 | 2026-09-07T03:12:27.846Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43025 | 2026-09-07T03:12:28.322Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fdd8d9bbdabfc13b; input_fingerprint=8f21a2538b50eff3deb30695a17e322360a4cdcc65592d4a7e8f59bb81978874 |
| 43026 | 2026-09-07T03:12:28.647Z | managed_process_admitted |  |  | owner=default |
| 43027 | 2026-09-07T03:12:28.956Z | managed_process_started |  |  | owner=default |
| 43028 | 2026-09-07T03:12:29.450Z | managed_process_terminal |  |  | owner=default |
| 43029 | 2026-09-07T03:12:29.805Z | proof_recorded |  |  | stage_id=check:fdd8d9bbdabfc13b; status=passed; cache_hit=False; input_fingerprint=8f21a2538b50eff3deb30695a17e322360a4cdcc65592d4a7e8f59bb81978874 |
| 43030 | 2026-09-07T03:12:30.030Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=064f41c558723405a0ac085d48c3965c02694d95777f514ce4fa2d83f073ed24 |
| 43031 | 2026-09-07T03:12:30.532Z | managed_process_admitted |  |  | owner=default |
| 43032 | 2026-09-07T03:12:30.795Z | managed_process_started |  |  | owner=default |
| 43033 | 2026-09-07T03:12:33.263Z | managed_process_terminal |  |  | owner=default |
| 43034 | 2026-09-07T03:12:35.069Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=064f41c558723405a0ac085d48c3965c02694d95777f514ce4fa2d83f073ed24 |
| 43035 | 2026-09-07T03:12:35.779Z | observation_span_recorded |  |  |  |
| 43036 | 2026-09-07T03:12:36.047Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43037 | 2026-09-07T03:14:24.303Z | managed_process_admitted |  |  | owner=default |
| 43038 | 2026-09-07T03:14:24.519Z | managed_process_started |  |  | owner=default |
| 43039 | 2026-09-07T03:14:25.161Z | managed_process_terminal |  |  | owner=default |
| 43040 | 2026-09-07T03:14:54.418Z | observation_span_recorded |  |  |  |
| 43041 | 2026-09-07T03:14:54.577Z | failure_observed | ACCEPTING | ACCEPTING | reason=Final acceptance failed closed with ACCEPTANCE_FILE_ATTESTATION_REQUIRED: one pre-existing dirty acceptance path (fullCleanActivation.js from the prior rejected wave) is not yet proven inside this wave's durable mutation surface. Code/test oracle is green; replan solely to exact-byte adopt current fullCleanActivation.js and test bytes into a fresh wave, rerun the same proofs, then accept.; failure_class=SOL_REJECTED |
| 43042 | 2026-09-07T03:14:54.727Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 43043 | 2026-09-07T03:14:54.903Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fdd8d9bbdabfc13b | passed | 8f21a2538b50eff3deb30695a17e322360a4cdcc65592d4a7e8f59bb81978874 | False | 1172 | 0 |
| verify:tests | passed | 064f41c558723405a0ac085d48c3965c02694d95777f514ce4fa2d83f073ed24 | False | 4640 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `100`
- Chain head: `d131d7d6fc7b04b21d22ab14c6e56caacc5eaa3ccda8de8ab8f99f6586968fad`
