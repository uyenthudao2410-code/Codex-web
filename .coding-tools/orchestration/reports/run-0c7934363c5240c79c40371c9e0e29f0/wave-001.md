# Orchestration Wave 1

- Run: `0c7934363c5240c79c40371c9e0e29f0`
- Wave: `3cc1e2b5ab764b4e8d08fdb20e243997`
- Objective: Validate accepted-run cohort telemetry v2 against the current durable production ledger. Run the canonical runtime activation benchmark after the accepted schema-v2 benchmark change. Capture cohort coverage and the homogeneous cohort breakdown. Do not compare raw global TTA across mixed workloads. Do not modify source files, commit, push, restart, or deploy.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `f9ef66869c97c3dc55390ae3b5d24364459b174155f309046afb5bff9ee663b5`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 712 | 2026-08-14T02:27:19.803Z | run_started |  | PREFLIGHT |  |
| 713 | 2026-08-14T02:27:20.257Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 714 | 2026-08-14T02:27:20.403Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 715 | 2026-08-14T02:27:20.634Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 716 | 2026-08-14T02:27:20.854Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 717 | 2026-08-14T02:27:21.159Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 718 | 2026-08-14T02:27:21.445Z | state_transition | READY | ROUTED | reason=route_selected |
| 719 | 2026-08-14T02:27:22.344Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a6fba31debbf432f8258f084eb463f16 |
| 720 | 2026-08-14T02:27:22.545Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 721 | 2026-08-14T02:27:23.055Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a6fba31debbf432f8258f084eb463f16 |
| 722 | 2026-08-14T02:27:23.213Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 723 | 2026-08-14T02:27:24.979Z | proof_recorded |  |  | stage_id=check:d97ff2ecbaa79b27; status=passed; cache_hit=False; input_fingerprint=995c4376eeb7ce7cd419db5e8412d54280a73b5d82c448cd13e76b4abab68839 |
| 724 | 2026-08-14T02:27:25.145Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 725 | 2026-08-14T02:27:51.110Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d97ff2ecbaa79b27 | passed | 995c4376eeb7ce7cd419db5e8412d54280a73b5d82c448cd13e76b4abab68839 | False | 1106 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 83c39088c9ea4f5bbf0b3bb63011f652 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 9152b6bbb84c561ba986d9b26f27ddee35fe59e631219d84ce0e2efb0a6f4226 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `231d4aa29e7e7254dc8af4540b09905fa7e01c48418e0f13987c56f0c619b975`
