# Orchestration Wave 2

- Run: `b433f3b24cd049a4a10b3ebe90e50bf3`
- Wave: `72a6785de167435892393e0d9215843b`
- Objective: Continue the same secondary-ledger forensic run after the URI permission false-positive. NEW EVIDENCE: a separate local SQLite query-only comparison proved resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 is schema-only and contains zero runs, zero waves, zero events, zero proofs, zero checkpoints, zero P5 epochs/enrollment/assignments/outcomes; canonical root ledger contains all durable history. This wave must ONLY localize the exact creation path and define the smallest prevention fix. Read the relevant OrchestrationLedger constructor/path-resolution code and all production/script/test call sites that can instantiate it from a workspace/CWD. Determine which path created a component-root ledger and whether a git-root/noncanonical-workspace guard would break legitimate temp/non-git test workspaces. Do not mutate source or databases yet; do not delete the nested DB; do not commit/push/restart or change P5 state. Return exact files/symbols and a minimal patch/test plan.
- Objective revision: `2`
- Objective SHA-256: `325398355d90d3219f574d0136fbc968ada81b761d833dcb5766c086044b8aa7`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0`
- Worktree fingerprint: `3f772125e2ee9ee0241440aa9afbe1fe02c393b08d367e8b1634999b9fc3b755`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27161 | 2026-08-22T13:53:00.445Z | wave_replanned |  | PREFLIGHT | reason=The prior wave's SQLite file-URI command was falsely classified as network and failed before execution. New evidence was obtained through a local SQLite query-only read using stdin: the nested ledger has zero durable rows and no unique project history. The strategy now changes to source-only localization of the creation path before any deletion or mutation. |
| 27162 | 2026-08-22T13:53:00.599Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27163 | 2026-08-22T13:53:00.775Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27164 | 2026-08-22T13:53:00.929Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 27165 | 2026-08-22T13:53:01.104Z | state_transition | READY | ROUTED | reason=route_selected |
| 27166 | 2026-08-22T13:53:01.824Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b6d0e26545ea49679f73003ee8bc9f68 |
| 27167 | 2026-08-22T13:53:01.980Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27168 | 2026-08-22T13:53:02.115Z | failure_observed | EXECUTING | EXECUTING | failure_class=INVALID_ARGUMENT |
| 27169 | 2026-08-22T13:53:02.434Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=b6d0e26545ea49679f73003ee8bc9f68 |
| 27170 | 2026-08-22T13:53:02.612Z | state_transition | EXECUTING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 27171 | 2026-08-22T13:53:02.849Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `44`
- Chain head: `59aee1fe0789a7a2822109b3793c353ec84e7de10a0520299ba2f96ff6e60572`
