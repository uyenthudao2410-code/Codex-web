# W7 — Hoàn thiện toàn bộ tồn đọng CoS/WebCodex (handoff/fork/resume, input_id lên wire, Git Review UI, FAILED dính)

- Ngày: 2026-10-24 (Asia/Saigon). Chỉ đạo user 06:39 24/10: "chạy hoàn thiện, đảm bảo đầy đủ xong các vấn đề".
- Cây làm việc: `~/workspace/projects/Codex-web-converged/` (bản hội tụ của GitHub main tại thời điểm W6 + delta chương trình). **Mức SOURCE + TEST** — không commit/push, không đóng gói, không restart production, không chạm Windows/svhome. Khâu phát hành do parent điều phối (checklist ở mục 6).
- Tồn đọng xử lý: W3 §7 mục 2–4 + §6 (W3-C), W5 §1 (giới hạn wire của `input_id`) + §2 (Git Review chưa nối IPC/UI), W6 §8 mục 1–3.
- Tổ chức: 3 cụm độc lập theo file — A (W3-C) và B (input_id) song song; C (UI wiring + FAILED) chạy sau A vì cùng đụng `electron/main.js`/`preload.js`/`renderer/work-hub.js`. Điều phối viên tự kiểm chứng chéo cuối lượt (mục 5).

## 1. Cụm A — W3-C: handoff / fork / resume / selector

### 1.1 Handoff nối đầy đủ — ĐÃ LÀM

- `workHubCodexChat.handoffToTask(root, payload)` + handler `workhub:codex-chat-handoff` + preload + nút "Chuyển thành việc điều hành" trong panel chat (kèm dòng receipt `#whCodexChatHandoffInfo`).
- Điều kiện chạy: phiên có nội dung (`CHAT_HANDOFF_NO_CONTENT`), không có lượt đang chạy (`CHAT_HANDOFF_TURN_ACTIVE`), kênh `task_control` đã nối (`CHAT_HANDOFF_NOT_WIRED`).
- Đã có RUN liên kết: đọc capsule hiện tại qua đúng bề mặt `task_control action=handoff, handoff_action=get` (cùng đường `workhub:handoff-get`), lấy `send_replay_directive` + `recommended_next_action` (semantics W4 trong `continuation_wiring.py`/`coordination.py` — tái dùng, **không tạo cơ chế handoff thứ hai**). Directive `RECONCILE_BEFORE_REPLAY` hoặc `ALREADY_CONFIRMED` → trả `HANDOFF_DIRECTIVE_BLOCKED`, lưu trạng thái blocked kèm directive vào view, **không tạo task, không ghi capsule, không replay**.
- Chưa có RUN: tạo việc qua đường tạo task hiện có `task_control action=start` qua `callMcpTool` (như các handler khác); lấy `task_id`/`orchestration.run_id` thật từ kết quả để cập nhật liên kết.
- Capsule dựng từ phiên: objective, summary (assistant text gần nhất), `recent_turns` (6 lượt cuối, cắt 500 ký tự/lượt), `thread_ref` (thread/session/profile/forked_from), `chat_link`, `send_checkpoint={state:'not_attempted'}`; ghi qua `handoff_action=record` vào đúng ledger capsule. Liên kết hai chiều chat session ↔ run/task được lưu vào registry phiên (mục 1.3) và hiển thị ở panel.
- **Lease — giới hạn trung thực:** ledger có `acquire_controller_lease` nội bộ nhưng bề mặt panel **không có API ghi lease** (chỉ đọc qua `workHubCoordination.runDetail`). Service tiêm `readLease` (main nối = `workHubCoordination.runDetail(root, runId).lease` — holder + status + expiry) và ghi giới hạn này ngay trong capsule (`lease_note`); không bịa API ghi mới. Nếu task tạo ra chưa có RUN: capsule được giữ ở `handoff.pendingCapsule` trong registry kèm lý do, vì capsule/lease đều khóa theo `run_id`.

### 1.2 Fork từ lịch sử Desktop — ĐÃ LÀM

- Service `fork(root, {sourceThreadId, text, model?, effort?})`: gọi bridge `run` với `source_thread_id` + profile `history` + `lifetime:'persistent'` và prompt đầu do user nhập (bridge không tạo thread rỗng — thiếu prompt/source bị từ chối cục bộ). Thread mới bridge-owned, continuable bằng `continue`, view mang `forkedFrom`; `listHistory` trả thêm `forkedFrom` + `forkable:true` (vẫn `continuable:false` cho thread gốc).
- UI: nút "Fork thành chat mới" cạnh mỗi mục lịch sử. **Giới hạn ghi thẳng trong UI:** panel không đọc được nội dung lượt cũ của thread Desktop (bridge chỉ trả summary; trong cây không có `codex_sessions.py` — không bịa đường đọc), fork kế thừa bối cảnh qua `thread/fork` của App Server, không qua panel.

### 1.3 Resume bền qua restart — ĐÃ LÀM

- **Registry bền (Electron):** service nhận `stateFile` tiêm vào; main nối `path.join(runtimePaths.dataRoot(), 'workhub-codex-chat-sessions.json')` (cạnh `settings.json`/`runtime-state.json`); ghi atomic (file tạm + `renameSync`, mẫu `workHubCoordination.writeOutbox`). Registry lưu: thread_id, session_id, workspace, profile, title, createdAt, link RUN, forkedFrom, route, handoff, lastState. Chat mới tạo với `lifetime:'persistent'` (trước đây ephemeral).
- **Bridge:** thêm action `resume` vào `handle()` của `codex_bridge.py` → `resume_registered_thread()` bọc trên machinery sẵn có `restore_persistent_thread` (thread/read → kiểm workspace + **session_id phải khớp registry** → thread/resume); chỉ re-own, không launch turn, trả route rút gọn (không lộ base instructions). `THREAD_NOT_OWNED` cho thread Desktop tùy ý **không bị nới**. Hệ quả bắt buộc: enum action của tool nội bộ `codex_bridge` trong `tool_schema.py` thêm `resume` + arg `session_id` (nếu không, `validate_arguments` với `additionalProperties:false` chặn action mới — đúng tiền lệ W3 §3; smart-v3 vẫn đúng 8 public tool).
- **Service:** `probe()` nạp registry và tự thử resume cho session restored; `send()` resume trước `continue` khi restored, và khi `continue` trả `THREAD_NOT_OWNED` thì thử resume **một lần** rồi retry — `OWNERSHIP_LOST` chỉ kết luận khi resume thất bại thật (kèm bằng chứng lỗi resume trong view `ownership.note`). Có thêm method/handler/preload `resume` để thử lại thủ công.
- **Giới hạn trung thực:** resume phụ thuộc App Server còn giữ thread trong CODEX_HOME (thread mất → `PERSISTENT_THREAD_NOT_FOUND` → OWNERSHIP_LOST thật); **timeline panel không persist** — sau restart chỉ ownership + link + route quay lại, messages trống.

### 1.4 Selector model/effort — ĐÃ LÀM (không defer)

Đã kiểm chứng bridge `run`/`continue` nhận `model`/`effort` override và profile `chat` không bị `locked_route` (chỉ `continuation_proposal` khóa); override không đụng bất biến `approvalPolicy=never`/read-only/no-network (có test Python khẳng định). Service thêm `listModels` (bridge `action=models`, handler/preload `workhub:codex-chat-models`) + validate effort cục bộ (`CHAT_EFFORT_INVALID`, không gọi bridge khi sai); `send`/`fork` chuyển tiếp override. UI: dropdown model (để trống = mặc định gpt-5.6-terra/medium của profile `chat`) + dropdown effort theo profile defaults, kèm chú thích bất biến không đổi.

## 2. Cụm B — `input_id` lên wire

- `tool_schema.py`: thêm property `input_id` OPTIONAL (string, `maxLength: 128`, mô tả semantics dedupe/no-replay) vào schema `command_control` (cho action `write`) và tool nội bộ `write_stdin`. Vẫn `additionalProperties:false` cho mọi property khác; không thêm/bớt tool; không đổi `required`; smart-v3 vẫn 8 tool.
- `server.py`: dispatch của `command_control` chuyển tiếp `input_id` cho action `write` xuống `session_control.write_stdin` → `JobInputLedger` (W5). Đường `write_stdin` đi qua handler tool nội bộ tới cùng `write_stdin` đã nối ledger từ W5. Không có `input_id` → hành vi legacy nguyên vẹn 100%.
- **Quyết định phạm vi (ghi trong header của `tests/test_job_input_wire.py`):** `exec_command` **không** có `input_id` — `stdin` của nó là payload ban đầu của lệnh mới (ghi một lần lúc khởi tạo), không phải lần ghi tiếp vào session đang chạy; semantics dedupe/receipt thuộc về các đường ghi tiếp (`command_control write`, `write_stdin`).
- **Contract/attestation:** bộ test `test_connector_attestation` PASS với schema mới (attestation mang `contract_sha256` được HMAC-ký trên contract hiện hành). Hệ quả thiết kế phải ghi rõ: **đổi schema = đổi contract hash** → sau phát hành, connector ChatGPT sẽ cần discovery/ack lại (Refresh phía user + acknowledge của operator nếu app nhắc) — đây là kỳ vọng, không phải lỗi (xem checklist mục 6).
- Test tầng wire mới `tests/test_job_input_wire.py` (gọi qua đúng đường dispatch + `validate_arguments` như MCP caller thật): (a) gửi kèm `input_id` → ghi đúng 1 lần, `input_receipt.outcome=delivered`; (b) gửi lại cùng `(session_id, input_id)` → không ghi lần 2, receipt `duplicate=true`; (c) ghi lỗi giữa chừng → `unknown`, gửi lại vẫn `unknown` và không ghi lại (không tự replay); (d) `input_id` không hợp lệ bị schema từ chối; (e) không có `input_id` → legacy nguyên vẹn.
- Baseline hồi quy (số đã đính chính của worker): bộ 45 test liên quan (job_input/attestation/execution/wave) **OK (skipped=1) trước và sau thay đổi** — khớp 1-1, cùng số test, cùng 1 skip.

## 3. Cụm C — Git Review UI + sửa FAILED dính

### 3.1 Nối `workHubGitReview` vào IPC/UI — ĐÃ LÀM

- `electron/main.js`: `require('./services/workHubGitReview')` + handler `workhub:git-review` đặt **sau** `workhub:check-url` (ngoài đoạn fixture của scope test, cạnh block W3/W3-C), đúng khuôn `secureHandle + invokeSafely + scopedWorkHubRoot(payload?.expectedWorkspace)`, truyền `{from, to}` cho `gitRangeReview`. `electron/preload.js`: hàm cụ thể `workhubGitReview(payload)` (không expose transport tổng quát).
- Renderer (panel Thay đổi, sau khối diff/patch-approval): mục "Rà soát thay đổi theo range" — hai ô base/head (trống = `HEAD~1`/`HEAD`, service tự dựng range), nút chạy, meta `#whGitReviewMeta`, danh sách `#whGitReview`. Render bằng `el()/textContent`, scope-guard `requestScope('gitreview')`, dọn state khi đổi project: số commit (tối đa 20 dòng), file theo nhóm subsystem (rename `origPath → path`, `+/−` dòng, binary ghi rõ "binary (không tính dòng)"), totals, fingerprint rút gọn 12 ký tự; lỗi validate rev hiển thị **nguyên văn** mã/thông điệp của service.
- **STALE:** lúc chạy review bắt HEAD hiện tại (qua `workhubGitHead`, fallback `toHash`) lưu vào `ui.gitReviewHead`; đường refresh gọi lại `renderGitReviewMeta()` — HEAD workspace đã khác HEAD đã bắt thì meta thêm nhãn STALE. Diễn giải đã khóa: STALE xét theo HEAD workspace di chuyển *sau lúc rà soát*, nên rà soát một `to` cũ tường minh không bị gắn STALE ngay chỉ vì `toHash ≠ HEAD`.

### 3.2 FAILED dính ở panel chat — ĐÃ SỬA Ở GỐC

- **Đính chính root cause so với W6 §8.3:** trong code hiện tại (hậu Cụm A), `listHistory`/`listModels` **không** ghi state (catch trả `{ok:false, state: session.state}` — đã mô phỏng xác minh: history fail giữ nguyên state/error). Đường ghi FAILED thật là `fail()` do `probe()` gọi: lỗi bridge lúc khởi động không khớp pattern phân loại nào (`CODEX_NOT_FOUND`, `MCP chưa sẵn sàng/ECONNREFUSED/…`, `THREAD_NOT_OWNED`, …) rơi xuống `BRIDGE_ERROR → FAILED`. Và `probe()` thành công chỉ chuyển `UNKNOWN/PROVIDER_UNAVAILABLE/MCP_UNAVAILABLE → READY` — **không đụng FAILED** → FAILED dính vô hạn dù availability/version đã hiện.
- **Sửa (nhỏ nhất, trong `probe()` của `workHubCodexChat.js`):** mở rộng điều kiện về READY thêm `(state === FAILED && !session.turnId)`. `turnId` rỗng phân biệt FAILED khởi động (chưa từng có turn chạy) với FAILED của một turn thật (luôn có `turnId`, do `poll` ghi terminal) — loại sau giữ nguyên FAILED. Không nới lỏng phân loại `PROVIDER_UNAVAILABLE/MCP_UNAVAILABLE/OWNERSHIP_LOST`; `prepareTurn` vốn không chặn FAILED nên lượt gửi mới không bị nhuộm (nay khóa bằng test).
- Test hồi quy mới trong `tests/work-hub-codex-chat.test.js`: (o) history fail không ghi state → probe fail generic ra FAILED → probe ok → `READY`, error `null`, version hiện; history fail sau đó vẫn giữ READY. (p) send ngay sau FAILED khởi động chạy tới `COMPLETED`. (q) probe thành công **không** xóa FAILED của turn lỗi thật (có `turnId`).

## 4. Danh sách file thay đổi

| File | Cụm | Thay đổi |
|---|---|---|
| `electron/services/workHubCodexChat.js` | A, C | Registry bền + resume/fork/handoff/listModels/route override (A); sửa chuyển state FAILED→READY trong `probe()` (C) |
| `electron/main.js` | A, C | Tiêm `callTool`/`readLease`/`stateFile`; handler `workhub:codex-chat-handoff|resume|models` (A) và `workhub:git-review` (C) — tất cả sau `workhub:check-url` |
| `electron/preload.js` | A, C | `workhubCodexChatHandoff/Resume/Models` (A); `workhubGitReview` (C) |
| `renderer/index.html` | A, C | Nút handoff + dòng directive, selector model/effort (A); mục "Rà soát thay đổi theo range" (C) |
| `renderer/work-hub.js` | A, C | Render handoff/fork/selector (A); `renderGitReview*` + STALE (C) |
| `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py` | A | Action `resume` + `resume_registered_thread()` (1.593 dòng, trong ngân sách 1.600) |
| `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py` | A, B | Enum `resume` + arg `session_id` cho tool nội bộ `codex_bridge` (A); property `input_id` cho `command_control` + `write_stdin` (B) |
| `resources/coding-tools-mcp/coding_tools_mcp/server.py` | B | Chuyển tiếp `input_id` ở dispatch `command_control` action `write` |
| `tests/work-hub-codex-chat.test.js` | A, C | +8 test (A: fork/resume/handoff/selector) → 18; +3 test hồi quy FAILED (C) → 21 |
| `tests/work-hub-git-review.test.js` | C | +1 test wiring (vị trí handler/preload/id HTML/nhãn STALE) → 5 |
| `tests/work-hub-ui.test.js` | C | +2 test UI (render range review + STALE + lỗi nguyên văn) → 17 |
| `resources/coding-tools-mcp/tests/test_codex_bridge.py` | A | +3 test (resume qua handle, session mismatch, override + persistent) → 26 |
| `resources/coding-tools-mcp/tests/test_job_input_wire.py` | B | Mới — test tầng wire cho `input_id` |
| `docs/research/261024_W7_COMPLETION.md` | — | Tài liệu này |

`electron/services/workHubCoordination.js` chỉ đọc (lease/ledger), không sửa. `electron/services/workHubGitReview.js` không sửa (service đã đủ từ W5).

## 5. Kết quả test

Theo cụm (worker chạy): A — Node `work-hub-codex-chat` 18/18, hồi quy Node liên quan 45/45 + 31/31; Python `test_codex_bridge` 26/26, continuation 69/69; `check_module_size.py` ok. C — git-review 5/5, codex-chat 21/21, scope 6/6, ui 17/17, files 20/20, diff-view 4/4, coordination 6/6, store 25/25, render-scope 6/6.

Điều phối viên chạy lại trên cây đã hợp nhất (kiểm chứng chéo A∩B trong cùng `tool_schema.py`: enum `resume` của A và property `input_id` của B cùng tồn tại, không ghi đè):

| Lệnh | Kết quả |
|---|---|
| `node --test tests/work-hub-*.test.js tests/cos-companion-adapter.test.js tests/codex-desktop-config.test.js` (từng suite) | **154 pass / 4 fail / 1 skipped** — 4 fail đều ở `work-hub-lsp` (xem dưới) |
| `PYTHONPATH=python_vendor:. python3 -m unittest` (11 suite: job_input, job_input_wire, connector_attestation, codex_bridge, continuation_send_state, continuation_goal_wiring, run_continuation, coordination_state, goal_pursuit, execution_hub, wave_a_runtime) | **172 test OK (skipped=1)** |
| `python3 scripts/check_module_size.py` | **ok** |
| `node --check` các file JS đã sửa | OK |

- **Fail môi trường, tiền tồn, không liên quan W7:** `tests/work-hub-lsp.test.js` 4 test fail trên VM vì TypeScript language server không khả dụng trong môi trường này (provider báo `unavailable`, fallback `text-search`; test pyright tự skip với ghi chú "pyright-langserver not installed"). Không cụm nào đụng LSP; suite này cũng không nằm trong bộ hồi quy phát hành 133 test của W6 trên Windows.
- **Tiền tồn đã biết, không sửa theo chỉ đạo:** `tests/chat-ui-compact.test.js` fail 1/6 (kỳ vọng chuỗi trong `renderer/app.js`).
- Mọi bằng chứng W7 là mức **test** (fake bridge / fake task_control / fake app-server / fixture DOM / repo git tạm). **Không có live proof** cho fork/resume/handoff/git-review-UI/input_id-wire — live smoke thuộc khâu phát hành.

## 6. Checklist phát hành (cho parent)

1. Đồng bộ delta W7 sang checkout Windows, chạy nghi thức delivery (`npm run stage:coding-tools-delivery` → `npm run check:coding-tools-delivery`), xem full `git diff --cached`, commit bằng pathspec, push, đồng bộ 3 máy (như W6).
2. Chạy bộ test trên Windows trước commit: Node (gồm `settings` và `work-hub-lsp` — trên Windows có TS server, kỳ vọng 4 fail môi trường của VM biến mất) + Python với `PYTHONPATH=python_vendor;.`.
3. Build tag mới (kế tiếp r19), dừng stack bằng đường hỗ trợ, kích hoạt full-clean qua Recovery Host IPC; giữ r19 làm vị trí rollback. Sau khi đổi bản đóng gói, **sinh lại config Codex Desktop** (nút copy-config trong app) vì config hiện trỏ thư mục build r19.
4. Live smoke trên bản đóng gói: (a) mở app lạnh — panel chat probe ra READY, không còn FAILED dính; (b) fork một thread từ lịch sử Desktop và chat tiếp; (c) restart MCP/app → phiên chat resume được, không OWNERSHIP_LOST oan; (d) nút "Chuyển thành việc điều hành" tạo task + capsule (đường REPLAY_SAFE) và hiển thị chặn đúng khi directive là RECONCILE/ALREADY_CONFIRMED; (e) mục Git Review chạy một range thật, commit thêm rồi thấy nhãn STALE; (f) qua wire: gửi `command_control write` hai lần cùng `input_id` → chỉ ghi 1 lần, lần 2 trả receipt `duplicate=true`.
5. Connector ChatGPT: contract hash đã đổi (thêm `input_id` + action `resume`) → sau phát hành, user Refresh lại app "Ubuntu Control Plane" trong ChatGPT và operator acknowledge nếu app nhắc; nhân dịp này gửi 1 câu test từ ChatGPT để đóng luôn bằng chứng đầu-cuối của Đường A (việc còn mở từ 06:41 24/10).
6. Lưu ý vận hành: lần chạy đầu sau phát hành, app tạo file registry `workhub-codex-chat-sessions.json` trong thư mục data của app; file này là state phiên chat (không chứa credential).

## 7. Giới hạn còn lại (trung thực)

- Fork/resume phụ thuộc khả năng thật của Codex App Server + CODEX_HOME: panel không đọc được turns của thread Desktop (chỉ summary + fork qua `thread/fork`); thread bị xóa khỏi CODEX_HOME thì resume trả OWNERSHIP_LOST thật.
- Timeline chat không persist qua restart — chỉ ownership/link/route được khôi phục từ registry.
- Lease controller chỉ đọc được từ panel; ghi lease vẫn là đường nội bộ của ledger — handoff ghi nhận qua capsule + `lease_note`, chưa có API ghi lease cho panel (cần đợt riêng nếu muốn panel trực tiếp acquire/release lease).
- Capsule handoff chỉ ghi vào ledger khi đã có RUN thật; task chưa có RUN thì capsule nằm ở `pendingCapsule` trong registry phiên.
- Chưa có live INTERRUPTED evidence và chưa kiểm chứng GUI bằng UIA (giới hạn đã biết từ W6, không đổi).
