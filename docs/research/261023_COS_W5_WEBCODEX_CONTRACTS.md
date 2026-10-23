# W5 — Port contract WebCodex chọn lọc (§8) vào Codex-web

- Ngày: 2026-10-23 (Asia/Saigon). Cây làm việc: `~/workspace/projects/Codex-web-converged/` (đã hội tụ lên GitHub main `e52ed53b`). Không commit/push, không chạm Windows/svhome.
- Nguyên tắc (kế hoạch §8 + W0 audit): cả 5 path upstream (`job_input.rs`, `git_review.rs`, `browser_tools.rs`, `computer_tools/`, `skills.rs`) **không tồn tại** trong Codex-web — W5 là **port contract**, không chép file Rust. Với mỗi mục: kiểm toán hiện trạng trước, chỉ implement khoảng trống thật, nhỏ nhất, có test. Hướng hiện hành của user (19:03): hợp logic tính năng **native vào Codex-web**, sản phẩm không phụ thuộc app CoS.

## 1. Interactive Job input — ĐÃ PORT (lớp nội bộ Python MCP)

**Hiện trạng trước W5:** gửi input vào Job đang chạy đi qua `command_control` (action `write`) và tool nội bộ `write_stdin`, cả hai đều tới `SessionControlMixin.write_stdin` → `ExecSession.write_input`. **Không có** `input_id`, không receipt, không dedupe: mất ACK thì caller không biết input đã vào hay chưa, gửi lại là gửi trùng. Lớp idempotency sẵn có của server (`idempotency_key`) áp cho operation-level của các facade, không bao phủ từng lần ghi stdin.

**Đã port:**
- Module mới `resources/coding-tools-mcp/coding_tools_mcp/job_input.py` — `JobInputLedger`: mỗi input có `input_id` do caller cấp (≤128 ký tự), receipt typed `{input_id, session_id, outcome, duplicate, bytes, sha256, recorded_at}` với 3 outcome: `delivered` (ghi xong), `unknown` (ghi lỗi giữa chừng — byte có thể đã vào một phần; tra lại cùng `input_id` vẫn trả `unknown`, **không bao giờ tự gửi lại**), `rejected` (chắc chắn chưa ghi). Dedupe theo `(session_id, input_id)`, có khóa luồng, bounded 512 record (FIFO — record bị evict thì dedupe không còn đảm bảo, đã ghi trong docstring). `receipt_for()` là đường reconcile sau khi mất ACK: chỉ tra, không ghi.
- Nối dây `session_control.py::write_stdin`: có `input_id` thì ghi qua ledger và trả `input_receipt` trong payload; outcome `unknown` → `ToolFailure JOB_INPUT_OUTCOME_UNKNOWN` kèm receipt trong `details`; lệnh đã đóng + có `input_id` → ghi receipt `rejected` (reason `COMMAND_CLOSED`) rồi giữ nguyên lỗi `COMMAND_CLOSED` cũ. Không có `input_id` → hành vi cũ nguyên vẹn. `server.py::command_control` chuyển tiếp `input_id` cho action `write`.
- **Giới hạn ghi rõ:** public smart-v3 giữ nguyên 8 tool và schema facade **không đổi** — validator (`validate_arguments`, additionalProperties=false) sẽ từ chối `input_id` trên wire cho tới khi schema + attestation/contract-golden được cập nhật ở một đợt riêng (bài học CI: đổi schema làm lệch golden hash). Hiện tại contract dùng được cho caller Python nội bộ (driver/continuation/recipe console nội bộ) và là nền để mở wire sau.

**Test:** `tests/test_job_input.py` — 10 test (ledger: delivered/dedupe/unknown-không-replay/rejected/session độc lập/input_id sai; write_stdin: receipt + ghi đúng 1 lần, legacy không đổi, write lỗi → `JOB_INPUT_OUTCOME_UNKNOWN` + receipt tra được, lệnh đóng → receipt `rejected`).

## 2. Git review (committed range) — ĐÃ PORT (service Electron)

**Hiện trạng trước W5:** `workHubFiles.js` có status (porcelain -z, có rename ở working tree), log, show, blame, diff theo tệp (W2 đã thêm head + fingerprint cho diff working-tree). **Thiếu:** phân tích một committed range — danh sách commit của range, thay đổi theo tệp với rename detection, cộng/trừ dòng, nhóm subsystem, fingerprint của range.

**Đã port:** service mới `electron/services/workHubGitReview.js` — `gitRangeReview(root, {from, to})`:
- Rev được validate (`REV_PATTERN`, cấm `..` — range luôn do service dựng từ 2 rev riêng) và resolve thành hash đầy đủ ở hai đầu.
- Commits của range (≤200), files từ `git diff --name-status -M -z` (rename có `origPath`), số dòng từ `git diff --numstat -z` (định dạng rename 3-field đã kiểm chứng thực nghiệm trên git 2.43; binary → `additions/deletions = null`), nhóm theo **subsystem** = segment đầu của path (`(root)` cho file ở gốc), totals gồm số rename.
- **Source fingerprint:** sha256 trên `fromHash + toHash + danh sách thay đổi canonical` — đổi đầu range hoặc nội dung range là fingerprint đổi; cùng range thì ổn định.

**Chưa làm (ghi rõ):** chưa expose IPC/preload và chưa thêm khối hiển thị vào Work Hub — service đứng độc lập có test; nối UI thuộc đợt tích hợp W6 để tránh thay đổi layout chưa được nghiệm thu riêng. **Test:** `tests/work-hub-git-review.test.js` — 4 test trên repo git thật (validate rev, subsystem, rename + grouping + fingerprint ổn định, fingerprint đổi khi range đổi).

## 3. Browser/CDP identity — ĐÃ PORT element generation (workHubBrowserQa)

**Hiện trạng trước W5:** Browser QA (M3.1) là capture một lần: mỗi lần tạo cửa sổ offscreen mới, chụp xong hủy; **không có session/profile bền, không có khái niệm phần tử** — nên cũng chưa có rủi ro stale-ref, nhưng thiếu hẳn identity để tham chiếu phần tử giữa các bước.

**Đã port** trong `electron/services/workHubBrowserQa.js` (giữ nguyên `capture` cũ, tương thích ngược — record cũ có `sessionId: null, generation: null, elements: []`):
- `openSession / captureInSession / closeSession / listSessions`: session có `id` riêng; mỗi lần capture trong session là một lần điều hướng → **generation tăng**.
- `extractElements(dom, sessionId, generation)`: trích tối đa 50 phần tử tương tác (a/button/input/select/textarea/label/h1–h6) từ DOM, mỗi phần tử mang ref `{sessionId, generation, ordinal}` + tag/id/name/text.
- `resolveElementRef(sessionId, ref)`: từ chối `BROWSER_ELEMENT_STALE` khi generation của ref khác generation hiện tại của session, `BROWSER_SESSION_NOT_FOUND` cho ref của session khác/đã đóng, `BROWSER_ELEMENT_NOT_FOUND` cho ordinal không còn. Đây là điều kiện an toàn bắt buộc trước khi bất kỳ thao tác click/gõ nào (việc của adapter tương lai) được phép dùng ref.

**Test:** `tests/work-hub-browser-qa-session.test.js` — 3 test mới (ref binding, stale sau điều hướng, session lạ bị từ chối, capture thường tương thích ngược) + suite cũ `work-hub-browser-qa` giữ nguyên PASS.

## 4. Skills + Remote Runner — KIỂM TOÁN, không implement thêm

| Hạng mục | Đã có (bằng chứng) | Thiếu / quyết định |
|---|---|---|
| Skills resolver/consumer | Work Hub F34 (M4): `renderer/work-hub-store.js` — skill có `sha256`, `revision` (tăng khi content đổi + reset sha), `lastUsedAt/lastUsedProject` (consumer evidence), bật/tắt theo từng project (`setSkillForProject`, `skillsForProject`), UI hiện `rev + sha256 rút gọn + đã dùng ở đâu` (`renderer/work-hub.js` khối F34); test `work-hub-store` có case F34 per-project | Chưa có resolver từ thư mục skill trên đĩa kiểu upstream `skills.rs` (skill hiện do user tạo trong Hub). **Defer:** chưa có nhu cầu nguồn skill thứ hai; khi có, resolver phải nạp vào đúng store hiện hữu, không tạo registry song song |
| Remote Runner / chọn máy | Control Plane đã có enrollment + bridges theo máy (`electron/services/controlPlaneEnrollment.js`, `controlPlaneExecBridge.js`, `controlPlaneReadOnlyBridge.js`, `controlPlanePolicyStore.js`...), chọn máy đích CP đã làm ở D5; SSH có host-key pinning SHA256 kiểu TOFU có chủ đích (`workHubSsh.js`, M4) | Chưa có "runner registry" kiểu WebCodex. **Defer:** tạo registry thứ hai sẽ trùng authority với Control Plane — vi phạm nguyên tắc không hai hệ điều phối. Nhu cầu chọn máy thật đã được CP đáp ứng |

## 5. Windows Computer Use (UIA) — DEFER có chủ đích

- **Không implement ở W5** (đúng chỉ định + quyết định từ chương trình parity: M3.2 là adapter riêng, ngoài phạm vi).
- Khoảng trống hiện tại: không có UIA adapter, không window identity, không input/screenshot theo cửa sổ trong Codex-web (Browser QA chỉ chụp trang web trong cửa sổ Electron của chính app).
- Điều kiện mở khi làm: (1) quyền riêng theo **từng cửa sổ đích + từng loại thao tác** (đọc screenshot ≠ click ≠ gõ phím); (2) window identity phải gắn với tiến trình/HWND tại thời điểm thao tác và hết hạn khi cửa sổ đổi; (3) mọi thao tác phải qua Job/receipt của EOCL như các đường thực thi khác; (4) quyết định sản phẩm riêng của user cho M3.2.

## 6. Kết quả test

| Lệnh | Kết quả |
|---|---|
| `node --test tests/work-hub-git-review.test.js` | **4/4 PASS** |
| `node --test tests/work-hub-browser-qa-session.test.js tests/work-hub-browser-qa.test.js` | **7/7 PASS** (3 mới + 4 cũ) |
| `node --test` work-hub-files + git-review + browser-qa + browser-qa-session + work-hub-ui + work-hub-store + work-hub-scope + work-hub-jobs + work-hub-coordination | **94/94 PASS** |
| `PYTHONPATH=python_vendor:. python3 -m unittest tests.test_job_input` | **10/10 OK** |
| `PYTHONPATH=python_vendor:. python3 -m unittest tests.test_job_input tests.test_execution_hub tests.test_wave_a_runtime` | **40 tests OK (skipped=1)** |
| `python3 scripts/check_module_size.py` | **ok** (module mới `job_input.py` nhỏ; `session_control.py` vẫn dưới ngân sách 1.600) |

Fail có sẵn, không liên quan W5: `chat-ui-compact.test.js` 1/6 (đã ghi nhận từ W1/hội tụ — kỳ vọng chuỗi trong `renderer/app.js`, W5 không đụng file đó, không chạy lại ở lượt này).

## 7. Tóm tắt files W5 (cây converged)

- Mới: `resources/coding-tools-mcp/coding_tools_mcp/job_input.py`, `resources/coding-tools-mcp/tests/test_job_input.py`, `electron/services/workHubGitReview.js`, `tests/work-hub-git-review.test.js`, `tests/work-hub-browser-qa-session.test.js`, tài liệu này.
- Sửa: `resources/coding-tools-mcp/coding_tools_mcp/session_control.py` (nối ledger vào `write_stdin` + `job_input_receipt`), `resources/coding-tools-mcp/coding_tools_mcp/server.py` (chuyển tiếp `input_id` trong `command_control`), `electron/services/workHubBrowserQa.js` (session + element generation, tương thích ngược).
- Không đổi: public smart-v3 (8 tool + schema facade), layout Work Hub, cây snapshot gốc (chỉ nhận bản sao tài liệu này).
