# Orchestration Wave 1

- Run: `bd3fa859b53c47978b6a2d973b76fa49`
- Wave: `bc78c25c92764977b7066eef5379d4ad`
- Objective: P1 activation repair 3: make host-visible turn measurement causally gated by a post-injection user send intent, so page reload/hydration/current in-progress turns can never create a span. Do not read prompt/response content. Detect composer intent only structurally via composer form submit, data-testid send-button click, or unmodified Enter on textarea/contenteditable; ignore IME composition. After intent, accept only the newest structurally visible tail user turn, then the newest tail assistant turn, with stable conversation-turn ordinal monotonicity when available. Keep the baseline priming as an additional guard. Bump current host evidence to schema v4 so v1-v3 smoke artifacts are preserved but excluded. Preserve all clock-domain and no-proximity-correlation rules; no routing/benchmark/promotion changes.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `e886a6c6f02650e3ae09274f0fe44e491f14c91e6ee19b78c3fa51a9b1140ec7`
- Contract fingerprint: `32c4f0eacfa2743afdb556337483e758a57a666e4c4b3b0f56dde9b6f521362c`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5020 | 2026-08-15T08:46:20.001Z | run_started |  | PREFLIGHT |  |
| 5021 | 2026-08-15T08:46:20.700Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 5022 | 2026-08-15T08:46:20.880Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5023 | 2026-08-15T08:46:21.123Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5024 | 2026-08-15T08:46:21.548Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5025 | 2026-08-15T08:46:21.822Z | state_transition | READY | ROUTED | reason=route_selected |
| 5026 | 2026-08-15T08:46:22.648Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d8540f4f94ed49198ecc8615268d302d |
| 5027 | 2026-08-15T08:46:22.855Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5028 | 2026-08-15T08:46:23.904Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d8540f4f94ed49198ecc8615268d302d |
| 5029 | 2026-08-15T08:46:24.106Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5030 | 2026-08-15T08:46:24.631Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1fb9970002b47283; input_fingerprint=161119431864f4361d407e222350bb98d9fa46b56bd42dfd361d5cb8a482dbab |
| 5031 | 2026-08-15T08:46:25.455Z | proof_recorded |  |  | stage_id=check:1fb9970002b47283; status=passed; cache_hit=False; input_fingerprint=161119431864f4361d407e222350bb98d9fa46b56bd42dfd361d5cb8a482dbab |
| 5032 | 2026-08-15T08:46:25.648Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6f0ee46d5e4c9471; input_fingerprint=01245fbf6b44112be1f2b08beb231ebcb02c4983fc8deb19f1e3583795399aad |
| 5033 | 2026-08-15T08:46:27.819Z | proof_recorded |  |  | stage_id=check:6f0ee46d5e4c9471; status=passed; cache_hit=False; input_fingerprint=01245fbf6b44112be1f2b08beb231ebcb02c4983fc8deb19f1e3583795399aad |
| 5034 | 2026-08-15T08:46:28.146Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1e5c4bf71d1ffc35; input_fingerprint=8117bb1f7c019adcd654024fa6eb47f810911b504364a8299569540eab9b9679 |
| 5035 | 2026-08-15T08:46:28.722Z | proof_recorded |  |  | stage_id=check:1e5c4bf71d1ffc35; status=passed; cache_hit=False; input_fingerprint=8117bb1f7c019adcd654024fa6eb47f810911b504364a8299569540eab9b9679 |
| 5036 | 2026-08-15T08:46:29.450Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5037 | 2026-08-15T08:50:38.773Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1fb9970002b47283 | passed | 161119431864f4361d407e222350bb98d9fa46b56bd42dfd361d5cb8a482dbab | False | 357 | 0 |
| check:6f0ee46d5e4c9471 | passed | 01245fbf6b44112be1f2b08beb231ebcb02c4983fc8deb19f1e3583795399aad | False | 1748 | 0 |
| check:1e5c4bf71d1ffc35 | passed | 8117bb1f7c019adcd654024fa6eb47f810911b504364a8299569540eab9b9679 | False | 132 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6bdd0e55d73440fb98959228066e064c | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | e5e284e2038ba3dd1b4f6b03ee8cf2a13f5555a75033b195fd963ae8414ea72b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `122aed87cadc5206ba8d055976400cf00dbd9cd3780463208711ad4707c166c7`
