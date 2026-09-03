# Orchestration Wave 3

- Run: `03fd5fbb0cc34177972b6065150c8f73`
- Wave: `26734c18978f4c99b0766be318f1252a`
- Objective: W2 repair after the no-mutation broad-suite failure. Implement exact cross-wave idempotency for ChatWeb controller usage within one RUN. Controller economic usage_id must be derived from RUN + turn_id, independent of wave_id, while controller delegation_id remains wave-bound attribution. The ledger must treat wave_id/delegation_id as non-economic attribution only when comparing duplicate controller events, preserving the first stored attribution event. Same exact controller receipt replayed in a later wave must deduplicate; changed economic evidence for the same RUN+turn must fail closed. Generic/provider build_usage_event identity and provider dedupe semantics must remain unchanged. Add a focused unit oracle covering cross-wave controller duplicate, first-attribution preservation, conflict rejection, and provider wave-bound identity. Preserve unknown_not_zero and unrelated dirty work. No commit/push/restart/package/release/deploy.
- Objective revision: `3`
- Objective SHA-256: `5bef1134618a0a467731ef9d8a708af8f400d7b1a53906479bbb5cb7c1b949bb`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `808eed8f72b06394accf31267b8bb5211e6dca404551be197fd575a9030acbfc`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33630 | 2026-08-31T19:01:11.442Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 failed only because the model-free run performed broad npm run test before any source mutation. Changed strategy: apply an explicit three-file causal patch and replace the non-discriminating full-suite gate with a focused unittest that directly exercises the missing cross-wave invariant plus provider regression semantics. |
| 33631 | 2026-08-31T19:01:11.707Z | observation_span_recorded |  |  |  |
| 33636 | 2026-08-31T19:03:29.257Z | state_transition | PREFLIGHT | ABORTED | reason=Terminalize the original W2 lineage because stateless task-context drift made the live task projection non-rebindable after Wave 3 was created. Wave 3 remained PREFLIGHT-only with no write lease, source mutation, or proof. Preserve all prior rejected/failed audit history; replacement work must start from exact current source and must not reuse stale proof. |
| 33637 | 2026-08-31T19:03:29.828Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `66`
- Chain head: `68eebbb3d4ed53474a066a82e2b7ed4159dd304a63399378475eb04de5050a26`
