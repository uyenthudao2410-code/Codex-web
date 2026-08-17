# 260817 — Đánh Giá Tình Trạng Hiện Tại Và Các Vấn Đề Tồn Đọng

> **Ngày đánh giá:** 2026-08-17
> **Workspace:** `E:\DEV\Tools-Codex-web`
> **Observed Git HEAD:** `3a3abaff`
> **Loại tài liệu:** snapshot đánh giá dựa trên evidence trực tiếp (ledger, code, tests, docs); không phải tuyên bố release.
> **Quy tắc bằng chứng:** áp dụng đúng thứ tự ưu tiên trong `AGENTS.md` — ledger là canonical causal source; code/tests là sự thật hiện tại; docs chỉ là projection có thời điểm.

---

## 1. Phương pháp và nguồn bằng chứng

Các kết luận dưới đây được kiểm chứng lại trực tiếp trong phiên đánh giá (không dựa vào report cũ):

| Nguồn | Cách dùng |
| --- | --- |
| `.coding-tools/orchestration/ledger.sqlite3` | Truy vấn trực tiếp: runs, pairs, controller telemetry, quality outcomes, observation spans |
| Source `resources/coding-tools-mcp/` + `crates/` | Đọc code, chạy test thực tế |
| `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, `docs/research/260816_*` | Đối chiếu kế hoạch |
| GitHub (gh CLI) | CI runs, billing block, PRs mở |
| Test thực thi | Python pytest + unittest discover; cargo test các crate liên quan |

---

## 2. Snapshot hệ thống hiện tại

### 2.1 Git / worktree

- HEAD: `3a3abaff` ("up"), trước đó `e576af9f` (sync state), `55a00cf0` (server-first compute orchestration).
- **Worktree dirty: 25 modified + 13 untracked**, gồm:
  - Phần refactor server.py + lint polish (chưa commit: `server.py`, 17 module `coding_tools_mcp/*`, `mcp_http_handler.py`...);
  - Fix flaky Rust test (`job_manager_tests.rs`);
  - `ci.yml` (chuyển workflow_dispatch), `AGENTS.md`, `scripts/check_module_size.py`;
  - Các file runtime của session song song (`.coding-tools/*`, `tmp/p1-release-shared-0cf/`, `tmp/dev-python-fail.log`).
- **PRs mở:** #14 "P1 exact-source Windows Desktop release boundary" (DRAFT), #13 "ignore-local-coding-tools-state" (OPEN), 3 dependabot PRs (anyhow, pyside6, mypy) — tất cả chưa merge.

### 2.2 Ledger (canonical evidence)

| Chỉ số | Giá trị | Nhận xét |
| --- | ---: | --- |
| Tổng run | 471 | |
| Accepted | 272 | |
| Pair-tagged run (`evaluation.pair_id`) | **0** | Chương trình paired evaluation chưa bắt đầu |
| Run có `controller.started_at` | **0** | ChatWeb controller measurement vẫn trống |
| Run có `controller.monetary_cost` | **0** | |
| Sự kiện `quality_outcome_recorded` | **0** | Quality floor chưa quan sát được |
| Sự kiện `observation_span_recorded` | 11 | Mới bắt đầu thu |
| Host observations (`.coding-tools/evaluation/*.jsonl`) | 131 records | **Chưa bind vào ledger run** (0 host-binding event) |
| Organic accepted hậu activation (≥ 2026-08-15T05:58Z) | 122 | first-pass 73 (59.8%), repaired 49 (40.2%) |
| Phân bố workflow organic | feature 43, diagnose 22, bugfix 27, test_failure 10, build_release 9, custom 10, refactor 1 | Đủ để phân tầng task class |

### 2.3 Trạng thái test (thực thi trong phiên đánh giá)

| Suite | Lệnh | Kết quả |
| --- | --- | --- |
| Python MCP (pytest) | `python -m pytest tests/` | **371 passed, 1 skipped, 25 subtests** |
| Python MCP (đúng lệnh CI) | `python -m unittest discover -s resources/coding-tools-mcp/tests -p "test_*.py"` | **369 OK (skipped=1)** |
| Ruff lint toàn package | `ruff check` | **All checks passed** |
| Module-size guard | `check_module_size.py` | pass |
| Rust runner (toàn bộ bin) | `cargo test -p webcodex-runner --bin webcodex-runner` | **542 passed, 0 failed, 1 ignored** |
| Rust compute placement | `cargo test -p webcodex-core compute_placement` | 11/11 |
| Rust SSH | `cargo test -p webcodex-runner ssh` | pass |
| Rust job_manager | `cargo test -p webcodex-runner job_manager` | 34/34 × 3 lần liên tiếp (sau fix flaky) |

---

## 3. Tiến độ theo từng kế hoạch đã đề ra

### 3.1 ROADMAP.md (P1/P2/P3 chính thức)

| Giai đoạn | Trạng thái | Bằng chứng |
| --- | --- | --- |
| P1 — exact-source activation & release boundaries | ✅ Xong | Recovery Host/Supervisor/independent MCP-Tunnel (`CURRENT_STATE.md` §6); chuỗi commit `a8588b47 → cb26a54f` |
| P2 — LSP resource hardening | ✅ Xong | `cf6cb6dd`: 10-cycle acceptance window, p95 LSP < 30 MiB |
| P2 — representative routing economics | 🟡 Hạ tầng xong, **bằng chứng = 0** | `64ac538a` chỉ đóng engineering; ledger 0 pairs |
| P3 — operationalize evidence | ✅ Xong | `5d3968ec`, `cf6cb6dd`, docs `415cb658` |

### 3.2 Chương trình routing-economics (P0–P4, phân tích 260815)

| Hạng mục | Trạng thái |
| --- | --- |
| P0 code-side: evaluation schema (pair_id/policy/task_class/oracle/provenance/controller + topology/router/worker/review/cache_stratum/trace/turn), server-derived `pair_fingerprint`, `identity_mismatch_reasons`, `quality_outcome` + `observation_span` schema, rename `external_candidate_credit_delta` | ✅ Xong |
| P0 client-side: ChatWeb gửi controller timing/usage/cost | ❌ **Chưa — vẫn là blocker số 1** |
| P1 evaluation plane: `evaluation_replay.py` (451 dòng, isolated worktree, đủ identity fields), `record_observation_span`, `critical_path_analysis` (DAG longest path), `evaluation_report.py` | 🟡 Gần xong; **thiếu routing regret** |
| P2 fixed-route evidence (C0/C1/Mini/Luna) | ❌ Chưa bắt đầu (0 pairs) |
| P3/P4 (adaptive, shadow/canary) | ⏸️ Chặn bởi P2 |

### 3.3 Refactor server.py (đề xuất & thực hiện trong phiên này)

✅ **Hoàn thành:** 12.584 → **2.922 dòng** (−77%); 16 module mới (leaf modules + 10 mixin + `mcp_http_handler.py`); ruff sạch; guard module-size trong CI; public namespace giữ nguyên. Rủi ro còn lại: **chưa trải qua thời gian soak production dài** — cần theo dõi 1–2 tuần trên Execution Hub đang live.

### 3.4 Server-first compute orchestration

🟡 Source hoàn chỉnh, bằng chứng chưa có:
- `ComputeSourceMode` (CleanHead | SourceSnapshot) + `supports_source_snapshot_validation`; placement tests 11/11 pass.
- Runner source-snapshot lifecycle (`source_snapshot.rs`, `main.rs`), job_manager tests (+349), test-support crate (+529).
- **Thiếu:** accepted-result economics cho server-first; paired evaluation local-first vs server-first. Auto-placement vẫn OFF (fail-closed `LocalOnly`) — đúng như research doc 260816 yêu cầu.

### 3.5 SSH Session resources (WebCodex core)

✅ Hoàn chỉnh phía Runner: OpenSSH multiplex pool (`ssh.rs` ~1.600 dòng), config `[ssh.resources.<name>]` không chứa auth material, dispatch run_shell/run_job → SSH, capability `ssh_shell` chỉ advertise khi có OpenSSH. Test pass. Giới hạn có chủ đích: không persistent shell/PTY, không structured validation trên SSH, **không hỗ trợ Windows Runner**. Đây là feature Linux-Runner; desktop Windows không dùng. "SSH break-glass" trong recovery roadmap vẫn là tương lai.

---

## 4. Các vấn đề tồn đọng (inventory chi tiết)

### A. Bị chặn bởi bằng chứng (evidence gates) — không phải code

1. **ChatWeb controller measurement chưa đóng** (P0 client-side): 0 run có controller timing/usage/cost. 131 host observations đã thu được (monotonic clock, turn_id/trace_id) nhưng **chưa bind vào ledger run**. Khoảng trống lớn nhất của toàn bộ chương trình đo lường.
2. **0 cặp paired evaluation** dù hạ tầng `evaluation_replay.py` đã sẵn sàng và organic cohort 122 accepted là nguồn task thật dồi dào.
3. **0 quality outcome** được ghi — không có quality floor để chặn promotion (schema + `task_control` action đã có).
4. **Routing regret chưa được implement** — router không có metric phản hồi offline.
5. **Rework vẫn cao và chưa được chứng minh giảm:** organic first-pass 59.8% (thấp hơn baseline lịch sử 66%). Không phải paired comparison nên chưa kết luận regression hay cohort khó hơn, nhưng hiệu quả của remediation (patch preflight, workdir fix) **vẫn chưa có bằng chứng định lượng**.
6. Server-first economics + paired evaluation chưa có (auto-placement đúng là không được bật).

### B. Kỹ thuật / chất lượng

7. **Đã phát hiện và sửa:** flaky test `structured_process_job_handoff_observation_does_not_reset_the_original_total_timeout` (race timing dưới tải song song — sẽ làm CI Linux flake ngẫu nhiên). Fix: timeout 1s→2s, grace + poll thay vì sleep cố định + assert; 3 lần chạy liên tiếp xanh. **Chưa commit.**
8. `orchestration_ledger.py` 4.197 dòng — module lớn nhất còn lại (budget 5.000); là ứng viên split tiếp theo khi workload ổn định.
9. Worktree có 38 entry chưa commit, trong đó phần refactor/lint/fix là của phiên đánh giá — cần commit sớm để tránh xung đột với session song song (đã quan sát thấy 2 session sửa đồng thời server.py hôm 15/8).
10. Warning dead-code trong webcodex-runner tests (14 warnings, không phải lỗi) — nên dọn sau.

### C. CI / phát hành

11. **GitHub Actions bị chặn vì billing:** tất cả run gần đây fail 2–4 giây với thông báo "recent account payments have failed or your spending limit needs to be increased". Repo đang private → tốn minutes Free (2.000/tháng).
12. Đã quyết định: **CI chỉ chạy thủ công khi release** (`ci.yml` → `workflow_dispatch`). Hệ quả: cây hiện tại không được CI cross-platform kiểm tra liên tục; trước khi release phải trigger tay và nhớ chạy đủ (Linux job chứa coverage Landlock mà máy Windows không có).
13. PR #14 (P1 release boundary workflow) còn DRAFT — khi merge sẽ tạo workflow thứ hai; cần quyết định trigger cho nó (nên cùng chính sách workflow_dispatch).
14. 3 dependabot PRs (anyhow, pyside6, mypy) chưa review.

### D. Rủi ro ngoài kiểm soát

15. **Model capacity flapping phía OpenAI** (quan sát 15/8: gpt-5.6-sol/luna ultra bị "at capacity" xen kẽ thành công) — sẽ gây nhiễu cho paired evaluation; hạ tầng `cache_stratum`/`order_index` đã sẵn để kiểm soát, chỉ cần dùng.
16. Billing GitHub nếu không xử lý, mọi release-time CI đều không chạy được.

---

## 5. Khuyến nghị thứ tự ưu tiên

1. **Commit chốt công việc hiện tại** (refactor lint polish, flaky-test fix, ci.yml, AGENTS.md, guard) — tránh mất work và xung đột session song song.
2. **Xử lý billing GitHub** (hoặc chấp nhận workflow_dispatch-only như đã quyết định).
3. **Bind 131 host observations vào ledger runs** (đóng một nửa measurement boundary; hạ tầng đã có).
4. **Chạy 10–20 cặp replay đầu tiên** bằng `evaluation_replay.py` trên organic cohort 122 accepted — bắt đầu thu P2 evidence thật.
5. **Ghi `quality_outcome`** cho các accepted run mới (kèm observation window cho delayed outcome).
6. **Implement routing regret** trong `evaluation_report.py`.
7. Review 3 dependabot PRs + quyết trigger cho workflow PR #14.
8. Sau khi workload ổn: split `orchestration_ledger.py`.
9. Dọn warning dead-code trong webcodex-runner tests.

---

## 6. Kết luận ngắn gọn

- **Đúng như dự đoán từ đầu phiên:** mọi thứ dừng đúng ở **evidence gate, không phải code gate**. Hạ tầng đo lường (pairing, replay, quality, observation, critical path) đã hoàn chỉnh; cái thiếu là **thu thập bằng chứng cặp thực** và **đóng ChatWeb controller measurement**.
- **Chất lượng kỹ thuật tốt:** 371 Python tests + 542 Rust runner tests + ruff sạch + guard chống tái phát; refactor server.py −77% không đổi hành vi.
- **Điểm yếu thực tế nhất hiện tại:** worktree 38 entry chưa commit (rủi ro mất/xung đột work), CI billing-blocked, và rework rate 40.2% chưa có lời giải thích định lượng.

*Tài liệu này là snapshot đánh giá tại HEAD `3a3abaff` ngày 2026-08-17; các con số ledger có thể trôi tiếp vì runtime đang live.*
