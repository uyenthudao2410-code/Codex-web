# Orchestration Wave 2

- Run: `f423d1ffaedd4c1d81dac0eb63af489c`
- Wave: `16ee3b32894d463fbb93ebcc8d383464`
- Objective: Continue the existing baseline roll-forward recovery under the canonical RUN only. Open a provenance-only corrective wave after the acknowledged rejected report, adopt exact current bytes for the two pre-existing dirty acceptance paths lacking durable provenance, perform no source content mutation, and run no verification in this adoption transaction.
- Objective revision: `2`
- Objective SHA-256: `641a2ccad631fa88793036ceca60828009fdcf3584d10d8c939e0e018a16934d`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `cd9fdac8b4ee50cfe307293d1356ef0f974776cd285d00e4dd4355cdb040bbad`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34112 | 2026-09-01T02:12:31.476Z | wave_replanned |  | PREFLIGHT | reason=ACCEPTANCE_FILE_ATTESTATION_REQUIRED after acknowledged completion report 2ca7ab3aef5fb2e89fd6d3b9386b07fcaa742414807304e649f8d3cfd30536be. The pre-ACK idempotency attempt was deterministically reconciled NOT_STARTED; create only a new provenance-only WAVE under the same canonical RUN f423d1ffaedd4c1d81dac0eb63af489c and adopt the two exact current dirty files without editing bytes. |
| 34113 | 2026-09-01T02:12:31.752Z | observation_span_recorded |  |  |  |
| 34114 | 2026-09-01T02:12:31.946Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34115 | 2026-09-01T02:12:32.163Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34116 | 2026-09-01T02:12:32.365Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 34117 | 2026-09-01T02:12:32.574Z | state_transition | READY | ROUTED | reason=route_selected |
| 34118 | 2026-09-01T02:12:32.841Z | observation_span_recorded |  |  |  |
| 34119 | 2026-09-01T02:12:33.684Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2a8a4ac5c6154b76a905bd50490261c6 |
| 34120 | 2026-09-01T02:12:33.915Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34121 | 2026-09-01T02:12:34.670Z | existing_file_adoption_observed |  |  |  |
| 34122 | 2026-09-01T02:12:34.882Z | observation_span_recorded |  |  |  |
| 34123 | 2026-09-01T02:12:35.226Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2a8a4ac5c6154b76a905bd50490261c6 |
| 34124 | 2026-09-01T02:12:35.434Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34125 | 2026-09-01T02:12:36.485Z | observation_span_recorded |  |  |  |
| 34126 | 2026-09-01T02:12:36.698Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34160 | 2026-09-01T02:32:06.883Z | observation_span_recorded |  |  |  |
| 34161 | 2026-09-01T02:32:07.087Z | failure_observed | ACCEPTING | ACCEPTING | reason=ACCEPTANCE_PROOF_REQUIRED: provenance-only adoption succeeded, but proof lineage was not materialized in the adoption wave.; failure_class=SOL_REJECTED |
| 34162 | 2026-09-01T02:32:07.316Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 34163 | 2026-09-01T02:32:07.523Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `204`
- Chain head: `855850803062800611e9d45e3c4ddd2517e83caefea8b866fb59ecf9ff4bddbf`
