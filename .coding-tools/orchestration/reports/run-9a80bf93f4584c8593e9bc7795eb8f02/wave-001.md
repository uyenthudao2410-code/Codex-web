# Orchestration Wave 1

- Run: `9a80bf93f4584c8593e9bc7795eb8f02`
- Wave: `73f62216416e4037a0923efcb9ce145c`
- Objective: Execute the already-prepared WAVE 1c1580a02cc84d78a06fd366fa28726f of RUN 21a41bfdbfc44192a82bc10c25e7eefe from the exact current dirty bytes. Preserve all unrelated dirty work and accidental dist artifacts. Close only these causal gaps: (1) make evidence_completeness.py the single Python host-observation schema authority with CURRENT_HOST_OBSERVATION_SCHEMA_VERSION=6 and LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS={1,2,3,4,5}; evaluation_report.py must import/reuse those constants, not redefine them; current v6 only enters current percentiles/correlation and v1-v5 remain legacy; update evaluation/evidence fixtures accordingly with legacy v1-v5 plus a separate v6 current event. (2) In chatEvaluationJournal.js remove generic Object.values and arbitrary array/object traversal; inspect only an explicit minimal response-envelope allowlist needed for response.completed/response shapes and never descend into message/messages/output/content/input/prompt/instructions/reasoning/chain-of-thought text or unknown keys; persist only numeric usage/correlation metadata; preserve stable dedupe; prevent JSON.parse/Response.json wrapper stacking and restore exact originals on dispose; add hostile nested-usage, double-install/dedupe and dispose-restoration JS tests. (3) Electron controllerUsage metadata must carry exact run_id and wave_id with turn_id/trace_id and preserve authenticated ChatWeb bridge. (4) usage_events controller-report validation must accept paired run_id/wave_id, require bounded text when supplied, reject booleans/negative/non-integer/token counts above JavaScript Number.MAX_SAFE_INTEGER, preserve unknown-not-zero and canonical duplicate semantics. (5) controller_usage_ingress must reject implicit_default and partial_headers provenance before ledger mutation; allow only explicit_headers or attested_transport with client_type=chatweb and role=controller; when authoritative RUN/WAVE exists, report must contain exact matching run_id/wave_id and exact authoritative turn_id/trace_id; CHECKPOINTED post-turn ingress must require exact current wave and the same existing controller lease still active/unexpired, without renewing/claiming an expired or missing lease before validation; active-run ingress may use supported controller authorization only after provenance/identity prevalidation. Preserve first-agent-workflow deferred usage compatibility only when no RUN/WAVE authority exists before prevalidation; after run creation bind exact resulting RUN/WAVE before recording. Add focused tests for implicit/partial/spoofed identity, run/wave mismatch, turn/trace mismatch, unsafe integers, duplicate conflict, exact idempotent duplicate, CHECKPOINTED same-wave active lease success, expired lease rejection, wave mismatch rejection. Keep current smart-v3 public contract at exactly 8 tools. Do not modify mcp_http_handler.py, server.py, orchestration_ledger.py, http_hub_identity.py or any path outside this 10-file packet. Do not run npm test, npm run dist, build/package/clean/restore/reset/commit/push/tag/publish/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `ff2e6f84643d07ecb99d3885ab43d65e13f144faca268eeb4992b3a844cb0b12`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `753839c6ce2254b680f3440b0e6ab8143dd0735633ca8b86f31b93e887b11779`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36822 | 2026-09-03T09:06:04.868Z | run_started |  | PREFLIGHT |  |
| 36823 | 2026-09-03T09:06:05.233Z | observation_span_recorded |  |  |  |
| 36824 | 2026-09-03T09:06:28.408Z | state_transition | PREFLIGHT | ABORTED | reason=Accidental RUN auto-minted by agent_workflow workflow=resume/phase=resume instead of reattaching archived RUN 21a. It failed at SOLUTION_SHADOW_REQUIRED before any write lease/source mutation. Abort this accidental RUN only; preserve workspace bytes, accidental dist artifacts, and runtime services. |
| 36825 | 2026-09-03T09:06:28.858Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Chain head: `cb086d3deec61b0c781dbcd0deebe7d61c105fcf0b7a57e81715001a1eeade30`
