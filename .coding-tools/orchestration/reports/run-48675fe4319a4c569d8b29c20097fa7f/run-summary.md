# Orchestration Run Summary

- Run: `48675fe4319a4c569d8b29c20097fa7f`
- Task: `8201a44ade2640858f53879322e2922b`
- Objective: Tiếp tục run EOCL hiện tại và triển khai source closure cho các gap đã audit, bảo toàn toàn bộ dirty/concurrent work hiện có. Thay đổi nhỏ, trực tiếp, không rewrite framework, không đổi Smart-v3 8 public tools, không đổi routing thresholds, không bật Routing-v2/deep escalation/auto-handoff/OpenCode writes. Cụ thể:

1) Idempotency truth/coverage: nâng PerformanceTrace theo kiểu additive/versioned (không reinterpret historical counters). Tách policy none/optional/required; required chỉ khi runtime có semantic identity đủ ổn định để replay-protect, optional cho side-effect calls mà exact repeat có thể là chủ ý (exec_command, stdin/write/kill, restart, handoff record, document create/convert, generic destructive/open-world nếu không có identity bền). Tự derive durable key chỉ cho các operation an toàn: agent_workflow phase=execute khi current durable run_id+wave_id tồn tại, key dựa trên run_id+wave_id+canonical request hash; và task_control accept/reject khi durable run/wave xác định. Không auto-key phase=run, exec commands, stdin, kill, restart, handoff, document writes. Explicit idempotency_key vẫn hoạt động như trước. Telemetry phải ghi effective key, policy, source explicit/derived; thêm clean v5 required/optional counters, auto-key count và coverage source-of-truth, giữ legacy fields tương thích nhưng không dùng chúng để quảng cáo gate mới. Duplicate exact execute trong cùng wave phải dedup; changed request hoặc new wave không được dedup sai.

2) Error attribution: thêm deterministic bounded error taxonomy cho PerformanceTrace theo methodology (ít nhất CONTROL_PATH, CONTROL_CWD, CONTROL_SCHEMA, CONTROL_CONNECTOR, CAPACITY, DEADLINE, PROMPT_SIZE, MODEL_CANDIDATE_INVALID, BASE_DRIFT, PATCH_AMBIGUOUS, PROOF_INFRA, PROOF_CODE_FAILURE, AUTHORITY_DENIED, USER_BLOCKED, PROVIDER, IDEMPOTENCY, VALIDATION, RUNTIME, UNKNOWN). Chỉ classify từ code/category đã quan sát, không suy diễn message/secret. Aggregate top-level + per-run và giữ UNKNOWN share đo được.

3) Phase timing: mở rộng PerformanceTrace phase whitelist để nhận các measured keys như preflight_ms, localization_ms, packet_build_ms, queue_ms, dispatch_transport_ms/transport_ms, model_wall_ms/provider_ms, candidate_validate_ms, apply_ms, proof_ms, accept_wait_ms, replan_ms, handoff_ms, total_ms/total_tta_ms cùng các composite-read keys hiện có. Chỉ nhận non-negative measured values và provenance; không biến EOCL EXECUTING dwell thành model latency. Runtime extractor vẫn bỏ cached/unmeasured samples. OrchestrationLedger.run_phase_timing phải trả tta_ms (nếu terminal), observed_ms, unattributed_ms, tta_coverage, coverage floor 0.90/target 0.95 + booleans, methodology windows hiện có. accepted_result_economics giữ EOCL coverage non-overlapping và bổ sung provider timing components (queue/provider/total) dưới một field overlapping/provenance riêng, không cộng chồng vào observed_ms/coverage.

4) Resident Hub latency: instrument đúng seam electron/services/hubProxyGateway.js bằng bounded rolling samples dùng monotonic/high-resolution clock, tách mcp/heartbeat/telemetry, chỉ lưu duration/status/size-class hoặc kind, không body/header/token. Expose metrics() với n,p50,p90,p99/max và sample cap; đo request-to-upstream-response resident gateway latency, không gọi nó là network/model latency. Không thêm push transport hay unauthenticated endpoint. Bổ sung Node test deterministic cho metrics. Nếu cần đưa vào Electron heartbeat/status thì chỉ projection non-secret nhỏ, không ghi descriptor token file lại theo mỗi request.

5) Python/Rust metadata seam: không full rewrite. Thêm vocabulary/ownership contract nhỏ ở Python ToolSpec/server metadata dùng đúng risk labels Rust hiện có (read_only, project_write, job_run, account_manage, unknown) và mô tả canonical ownership: Python owns MCP public annotation/projection; Rust ToolMetadata/ToolRisk owns native execution risk; EOCL/permission/write lease owns authority. Chỉ annotate các tool rõ semantics; mixed control tool giữ unknown thay vì gán sai....
- Status: **active**
- Started: `2026-08-14T16:06:48.345Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3a320698f38944faba0c90ddc6c15e74` | `deep_single_lane` | `62ff046711503260b079e53a85c66e5b9af01e32` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2646 | `sol_xhigh` | `sol_xhigh` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2652 | `PROMPT_TOO_LARGE` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `ae9cf027920929a7c15b1909d5f7abcbcb29b044d3640fdbe350ccefcf12d967`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
