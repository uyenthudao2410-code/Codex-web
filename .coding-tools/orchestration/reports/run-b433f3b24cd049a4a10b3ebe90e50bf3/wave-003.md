# Orchestration Wave 3

- Run: `b433f3b24cd049a4a10b3ebe90e50bf3`
- Wave: `88a6b259099a40898792f7a97f012ead`
- Objective: Continue the same secondary-ledger forensic run after the URI permission false-positive. NEW EVIDENCE: a separate local SQLite query-only comparison proved resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 is schema-only and contains zero runs, zero waves, zero events, zero proofs, zero checkpoints, zero P5 epochs/enrollment/assignments/outcomes; canonical root ledger contains all durable history. This wave must ONLY localize the exact creation path and define the smallest prevention fix. Read the relevant OrchestrationLedger constructor/path-resolution code and all production/script/test call sites that can instantiate it from a workspace/CWD. Determine which path can create a component-root ledger and whether a git-root/noncanonical-workspace guard would break legitimate temp/non-git test workspaces. Do not mutate source or databases yet; do not delete the nested DB; do not commit/push/restart or change P5 state. Return exact files/symbols and a minimal patch/test plan.
- Objective revision: `3`
- Objective SHA-256: `c8b7127f735513c61fb9c6cc21b685eb28b71a869dca0fbc3e9afaa47f3c1fcb`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0`
- Worktree fingerprint: `3f772125e2ee9ee0241440aa9afbe1fe02c393b08d367e8b1634999b9fc3b755`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27172 | 2026-08-22T13:53:18.248Z | wave_replanned |  | PREFLIGHT | reason=The prior wave's SQLite file-URI command was falsely classified as network and failed before execution. New evidence was obtained through a local SQLite query-only read using stdin: the nested ledger has zero durable rows and no unique project history. The strategy now changes to source-only localization of the creation path before any deletion or mutation. |
| 27173 | 2026-08-22T13:53:19.289Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 27174 | 2026-08-22T13:53:19.424Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 27175 | 2026-08-22T13:53:19.574Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27176 | 2026-08-22T13:53:19.715Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27177 | 2026-08-22T13:53:19.865Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 27178 | 2026-08-22T13:53:20.033Z | state_transition | READY | ROUTED | reason=route_selected |
| 27179 | 2026-08-22T13:53:21.139Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=098e83eb33d94302974eb895f22789e5 |
| 27180 | 2026-08-22T13:53:21.305Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27181 | 2026-08-22T13:53:22.075Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=098e83eb33d94302974eb895f22789e5 |
| 27182 | 2026-08-22T13:53:22.232Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27183 | 2026-08-22T13:53:22.915Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=d3be2922792140ae4512148d195f4a04509cf2f0113ac2cc0d99b918acbc2a30 |
| 27184 | 2026-08-22T13:53:23.305Z | managed_process_admitted |  |  | owner=default |
| 27185 | 2026-08-22T13:53:23.566Z | managed_process_started |  |  | owner=default |
| 27186 | 2026-08-22T13:53:24.758Z | managed_process_terminal |  |  | owner=default |
| 27187 | 2026-08-22T13:53:25.089Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=d3be2922792140ae4512148d195f4a04509cf2f0113ac2cc0d99b918acbc2a30 |
| 27188 | 2026-08-22T13:53:25.267Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 27189 | 2026-08-22T13:54:20.437Z | quality_outcome_recorded |  |  |  |
| 27190 | 2026-08-22T13:54:20.573Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 27191 | 2026-08-22T13:54:20.915Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | d3be2922792140ae4512148d195f4a04509cf2f0113ac2cc0d99b918acbc2a30 | False | 1783 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| cb6920206568475f8c76073b7635c997 | accepted | 6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0 | 471951c4eaacbfc5371f1b9006b2ad6e189025e08375148854c1f76f7cf34107 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `59aee1fe0789a7a2822109b3793c353ec84e7de10a0520299ba2f96ff6e60572`
