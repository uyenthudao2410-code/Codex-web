# Orchestration Wave 2

- Run: `742eff5143bf45e6aa42febdd4e14018`
- Wave: `8c4c360ed7bb4e109cd438d52909efb5`
- Objective: Converge Recovery Host and Coding MCP component state by no-patch provenance adoption of the exact current bytes for the 26 unaccepted component files, with fresh deterministic proof and no source writes.
- Objective revision: `1`
- Objective SHA-256: `a20ad08e4ac6fe68112a7f6aa8a12bdb2de285e6f23c1b3f2c30785064a62679`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44158 | 2026-09-08T17:37:29.812Z | wave_replanned |  | PREFLIGHT | reason=The runtime contract permits adopt_existing_files only for paths that were already Git-dirty when the write lease was acquired. Preserve the exact 26-file convergence objective without writing source: no-patch adopt only the observed pre-existing dirty subset in this wave, run the unchanged full 26-file proof boundary from repository root, then use controller acceptance_files to hash and attest all 26 exact current bytes at checkpoint. |
| 44159 | 2026-09-08T17:37:30.144Z | observation_span_recorded |  |  |  |
| 44160 | 2026-09-08T17:37:30.323Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44161 | 2026-09-08T17:37:30.489Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44162 | 2026-09-08T17:37:30.671Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44163 | 2026-09-08T17:37:30.857Z | state_transition | READY | ROUTED | reason=route_selected |
| 44164 | 2026-09-08T17:37:31.056Z | observation_span_recorded |  |  |  |
| 44165 | 2026-09-08T17:37:31.739Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e6214742903b4fe1b4c229431e7d5bf3 |
| 44166 | 2026-09-08T17:37:31.925Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44167 | 2026-09-08T17:37:32.732Z | existing_file_adoption_observed |  |  |  |
| 44168 | 2026-09-08T17:37:32.945Z | observation_span_recorded |  |  |  |
| 44169 | 2026-09-08T17:37:33.238Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e6214742903b4fe1b4c229431e7d5bf3 |
| 44170 | 2026-09-08T17:37:33.373Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44171 | 2026-09-08T17:37:34.190Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a1ca22a027389477; input_fingerprint=06dc333501a26eadcbbc017dbb58b5d2f8118c8bad8aa7b1eba5ba9b782e0353 |
| 44172 | 2026-09-08T17:37:34.532Z | managed_process_admitted |  |  | owner=default |
| 44173 | 2026-09-08T17:37:34.875Z | managed_process_started |  |  | owner=default |
| 44174 | 2026-09-08T17:38:47.137Z | managed_process_terminal |  |  | owner=default |
| 44175 | 2026-09-08T17:38:47.611Z | proof_recorded |  |  | stage_id=check:a1ca22a027389477; status=passed; cache_hit=False; input_fingerprint=06dc333501a26eadcbbc017dbb58b5d2f8118c8bad8aa7b1eba5ba9b782e0353 |
| 44176 | 2026-09-08T17:38:47.806Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fea3ad3e8fb2d5f8; input_fingerprint=7a8f763548a69a2bfbf68ca6d3c75340600fbb2d2f0c688c7f4360e23d593250 |
| 44177 | 2026-09-08T17:38:48.211Z | managed_process_admitted |  |  | owner=default |
| 44178 | 2026-09-08T17:38:48.523Z | managed_process_started |  |  | owner=default |
| 44179 | 2026-09-08T17:38:53.637Z | managed_process_terminal |  |  | owner=default |
| 44180 | 2026-09-08T17:38:53.976Z | proof_recorded |  |  | stage_id=check:fea3ad3e8fb2d5f8; status=failed; cache_hit=False; input_fingerprint=7a8f763548a69a2bfbf68ca6d3c75340600fbb2d2f0c688c7f4360e23d593250 |
| 44181 | 2026-09-08T17:38:54.187Z | observation_span_recorded |  |  |  |
| 44182 | 2026-09-08T17:38:54.368Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 44183 | 2026-09-08T17:38:54.580Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 44184 | 2026-09-08T17:38:54.808Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 45589 | 2026-09-09T10:48:21.353Z | state_transition | REPLAN | ABORTED | reason=Terminalize this detached historical RUN as ABORTED. Canonical replay shows no accepted checkpoint: the first wave failed an existing-file adoption guard; the replanned wave recorded one passed proof and then a second proof FAILED exit 2 with CHECK_FAILED, followed by REPLAN and quiescence. Preserve all proof/failure/adoption evidence; do not accept stale partial proof. |
| 45590 | 2026-09-09T10:48:21.765Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a1ca22a027389477 | passed | 06dc333501a26eadcbbc017dbb58b5d2f8118c8bad8aa7b1eba5ba9b782e0353 | False | 73138 | 0 |
| check:fea3ad3e8fb2d5f8 | failed | 7a8f763548a69a2bfbf68ca6d3c75340600fbb2d2f0c688c7f4360e23d593250 | False | 5830 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `2979843ece71fbb63c7b0a818f2d0652aba5779575f33465b44d48759129569b`
