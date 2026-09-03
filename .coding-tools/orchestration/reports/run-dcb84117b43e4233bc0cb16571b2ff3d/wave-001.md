# Orchestration Wave 1

- Run: `dcb84117b43e4233bc0cb16571b2ff3d`
- Wave: `322d3f7db62e4d5a9a5153c5a8033d06`
- Objective: Prepare the smallest exact patch for RUN 21a. Read current source and callsites only. Determine: (1) the minimal single Python authority for host-observation schema v6 without circular imports; (2) the exact response envelope keys actually needed to discover response.completed/response while never traversing message/output/content or arbitrary arrays/objects; (3) the actual HTTP identity/provenance fields used before controller usage ledger mutation; (4) the authoritative current RUN/WAVE and host/evaluation turn/trace correlation surfaces; (5) how _require_hub_controller proves the same controller lease is active and how to test expiry/mismatch. Preserve first-call compatibility only where there is genuinely no RUN/WAVE authority; once authority exists, incomplete or mismatched provenance must fail closed. Do not mutate or run verification in prepare.
- Objective revision: `1`
- Objective SHA-256: `e4b89b15b2714ab7b6276df13b13b18054b86c3f94ae34549b23dedaf86ff154`
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
| 36915 | 2026-09-03T09:14:09.726Z | run_started |  | PREFLIGHT |  |
| 36916 | 2026-09-03T09:14:10.038Z | observation_span_recorded |  |  |  |
| 36917 | 2026-09-03T09:14:23.789Z | state_transition | PREFLIGHT | ABORTED | reason=Accidental RUN auto-minted while attempting to execute exact archived RUN 21a wave 19f. It failed at SOLUTION_SHADOW_REQUIRED before write lease/source mutation. Operator forbids replacement RUNs. Abort only this accidental RUN; preserve all workspace bytes, accidental dist artifacts and runtime services. |
| 36918 | 2026-09-03T09:14:24.183Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Chain head: `914f294eb4726ba47df2385a74b33593e65544ff58d3f2e17f37b5c2bbb162cc`
