# Orchestration Run Summary

- Run: `10d905a41d3b433687346b50e4a180b5`
- Task: `501a8a4bf4fc48dba38d6984a209a3b3`
- Objective: Kiểm tra hệ thống chỉ số ở màn hình 'Tổng quan vận hành' xem đã bắt token thực từ provider/runtime hay chưa, vì dashboard hiện cập nhật chậm và có dấu hiệu sai số. Đối chiếu các KPI Tổng token, Token đầu vào, Token đầu ra, Chi phí, phân bổ token theo mô hình/công cụ và chuỗi thu thập telemetry -> lưu trữ -> aggregate/query -> UI. Tìm nguồn dữ liệu thực tế, các fallback/ước lượng, cache/polling/window thời gian, độ trễ ghi dữ liệu, khả năng double-count/missing events, và giải thích các bất nhất nhìn thấy trên ảnh: Tổng token 138K trong khi input 96K + output 12K = 108K; donut phân bổ theo mô hình chỉ khoảng 28K; chi phí $0.015. Chỉ chẩn đoán, chưa sửa code. Trả về file/symbol liên quan, root cause có bằng chứng, mức độ tin cậy, và đề xuất cách xác minh bằng log/DB/test.
- Status: **aborted**
- Started: `2026-08-19T08:04:44.570Z`
- Finished: `2026-08-19T08:06:27.350Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a76b0c8e3d4a4f73bab15defd038942d` | `auto` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `5`
- Chain head: `e69e7e3b6b219c0282e5baef0c6a1e41b20b9d5c301871cf6d144d5ed59ae336`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
