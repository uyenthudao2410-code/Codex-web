# Orchestration Wave 1

- Run: `8f7bc98ea0df455b8c3f9632e445fb10`
- Wave: `370248c95bc548f893a742e872d28db9`
- Objective: Fix the proof-integrity false positive where a managed proof command whose execution-resource lifecycle has already been reconciled to quiesced can still be reduced to PASS solely because the root payload reports status=exited and exit_code=0. Preserve current Rust test-only worktree changes. Add an exact lifecycle lookup to ExecutionResourceGovernor; in ContextToolsMixin._run_continuous_check, after the terminal command payload is obtained but before TaskState/proof reduction, read the managed job lifecycle from execution_owner.job_id. If a known managed lifecycle is anything other than exited, fail closed by making the terminal payload non-success (quiesced/terminated/timeout/spawn_failed/etc. must never become PASS). Do not parse stdout text for FAILED. Add deterministic regression tests for exit_code=0 plus quiesced lifecycle and for normal exited lifecycle remaining PASS. Keep behavior for unmanaged/no-job payloads unchanged.
- Objective revision: `1`
- Objective SHA-256: `0ab933e2ea19eff32cb0439d61c58921f68afa71bb3974872ec1964b5c368080`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e150020a0c0829a988ffea527d5c8d82132ed65`
- Worktree fingerprint: `7b54aa5ab96a3b29ba50523d4283c0e0553d039c6634fd3c18da1cfeab1344ff`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28597 | 2026-08-23T04:51:35.903Z | run_started |  | PREFLIGHT |  |
| 28609 | 2026-08-23T04:51:48.868Z | solution_shadow_recommended |  |  |  |
| 28851 | 2026-08-24T10:51:53.453Z | state_transition | PREFLIGHT | ABORTED | reason=Exact stale reconciliation: threshold exceeded with no live controller lease or write fence. |
| 28852 | 2026-08-24T10:51:53.839Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `4`
- Chain head: `2f1c66f1eeb89d761f3857ed0bcfefa844b6eddd5db095401540afc4c040c25a`
