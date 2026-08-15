# Orchestration Run Summary

- Run: `e9276d396e8548f8bf55b804eb30066d`
- Task: `49817a91be1a4e5a82bc499a9151911a`
- Objective: Chẩn đoán chính xác vì sao Operator Control Panel giữ nguyên trạng thái mặc định dù MCP/Tunnel health xanh. Bằng chứng UI cho thấy refreshOrchestration chưa render thành công (rotationLine vẫn là chuỗi mặc định 'Đang đánh giá khả năng xoay ChatWeb…', các client và Execution Hub vẫn default OFFLINE), trong khi refreshHealth đã chạy. Hãy tái hiện riêng đường panel:orchestration -> GET /__control/orchestration trên workspace/runtime hiện tại nếu có thể mà không in bearer/token; xác định request có lỗi HTTP/auth, endpoint có exception theo dữ liệu ledger hiện tại, hay vượt timeout 2500ms. Đo thời gian snapshot/endpoint nếu phù hợp. Chỉ chẩn đoán, không sửa source, không restart runtime, không thay đổi secrets. Báo root cause với bằng chứng và change set tối thiểu nếu cần.
- Status: **active**
- Started: `2026-08-15T02:10:36.489Z`
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
| 1 | `925144b668264b78bc63059b8956e0fc` | `bounded_candidate` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3681 | `luna` | `luna` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3687 | `PROMPT_TOO_LARGE` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `d17d511bb43d8b10aa3d261ab2db1ad39639419adad26c8f435e7ca80aba2267`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
