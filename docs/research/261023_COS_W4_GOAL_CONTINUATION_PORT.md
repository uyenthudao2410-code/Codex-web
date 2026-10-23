# W4 (kéo sớm) — Port LOGIC Goal + Compact & Resume của CoS vào Codex-web

- Ngày: 2026-10-23 (Asia/Saigon). Thực thi: VM-first, trên snapshot `~/workspace/projects/Codex-web` (không .git — không commit/push/restart/packaged).
- Chỉ đạo mới của user (19:03 23/10/2026): **kết hợp logic tính năng của CoS vào trong Codex-web** — sản phẩm cuối không cài thêm, không chạy thêm app CoS. Bản source CoS trên VM chỉ là tài liệu tham chiếu để port (MIT, `366404c1`, v2.1.45).
- Phạm vi lượt này: Python MCP (`resources/coding-tools-mcp`) + test + tài liệu. Không sửa `renderer/work-hub*` / `electron/services/workHub*` (agent W2 phụ trách UI).

## 1. Đối chiếu logic CoS ↔ Codex-web

### 1.1 Continuation / Compact & Resume

Nguồn CoS: `src/main/session/continuation.ts` (1.946 dòng). Mô hình giao dịch phiên của CoS:
`awaiting-summary → awaiting-chat → claimed → committing → committed | aborted`, kèm một
**checkpoint gửi 4 vị trí bền vững** cho mỗi prompt/effect (`ContinuationSendState`):

| CoS (wire) | Ý nghĩa (theo comment gốc của CoS) | Codex-web trước lượt này |
|---|---|---|
| `not-attempted` | Chưa bắt đầu gửi | Không có khái niệm tương đương ở tầng capsule |
| `attempted-unresolved` | Đã bắt đầu nhưng checkpoint được ghi **trước khi** đụng nút Send → chứng minh *chưa có gì được gửi* → được phép trao cho chat khác gõ lại | Không có |
| `dispatched-unresolved` | Đã ghi **trước cú click** → có thể đã tới nơi, không gì ở local phân biệt được → **không bao giờ phát lại** | Có *hành vi* tương đương rải rác ở driver: `DISPATCH_UNKNOWN` / `PROOF_OUTCOME_UNKNOWN` + fail-closed pause (`continuation_driver.py`) — nhưng là trạng thái vận hành tức thời, **không phải contract bền vững gắn trên handoff/capsule**, và không phân biệt được "đã bắt đầu nhưng chắc chắn chưa gửi" với "có thể đã gửi" |
| `sent` | Đã xác nhận gửi (có server message id) | Không có ở tầng capsule |

Codex-web đã có sẵn, tương đương hoặc mạnh hơn CoS (không port lại): capsule handoff bền vững
(`OrchestrationLedger.record_handoff_capsule`/`latest_handoff_capsule`, có hash + giới hạn kích thước),
controller lease/fencing + reattach (`controller_reattach.py`, `controller_continuity.py`),
claim một-lần qua `next_action_seq`/`consumed_event_seq` + `pending_action_id`, TTL/lease cho continuation
(`RUN_CONTINUATION_LEASE_SECONDS`), commit intent bền vững cho Goal episode
(`goal_continuations` + `run_continuations`).

**Khoảng trống thật đã xác minh:** thiếu taxonomy 4 mức send/effect như một *contract có tên, bền vững,
kiểm chứng được* trên handoff capsule — thứ quyết định "được phát lại / phải reconcile / đã xong"
khi chat A → chat B tiếp quản, độc lập với trạng thái tức thời của driver.

### 1.2 Goal

Nguồn CoS: `src/main/goal.ts` (3.145 dòng) + `src/shared/goal.ts`. Cơ chế cốt lõi của CoS là một
**model judge bên ngoài** (OpenRouter, key riêng của user; mặc định `z-ai/glm-5.3`): sau mỗi lượt,
model được hỏi "toàn bộ yêu cầu đã xong chưa", trả lời hoặc một chỉ thị tiếp tục, hoặc `NO_REPLY`
(= đã hoàn thành). Chống lặp của CoS: mỗi draft gắn `turnId` + token ack một-lần
(`ackGoalDraft(conversationId, token, clientId)` + tombstone bền vững `GOAL_REPLIES_STATE`),
draft đã ack thì không bao giờ được gõ lại; một draft/conversation tại một thời điểm.

| Khái niệm CoS | Codex-web tương đương | Kết luận |
|---|---|---|
| Judge "chưa hoàn thành" bằng model ngoài | Tín hiệu xác định từ bằng chứng: `_goal_criterion_coverage` (mỗi criterion: `UNRESOLVED`/`PROVEN`/`SATISFIED_NON_CODE`) + verdict inline trong `goal_pursuit_live_summary` (`completion.exact_coverage_status` COMPLETE/PARTIAL/NONE, `resolution_status`, `stop.legitimate_stop`) | Đã có — nhưng verdict nằm *inline trong một projection nặng* (bắt buộc exact RUN binding + fact window), **không có hàm tín hiệu thuần, tái dùng được** cho tầng continuation |
| Chống gửi lặp (ack token + tombstone) | Idempotency mạnh hơn: `goal_continuation_observations` theo `observation_id` + `GOAL_CONTINUATION_OBSERVATION_CONFLICT`, grant/materialize idempotent theo content hash, action seq một-lần | Đã tương đương/mạnh hơn — **không port** |
| Trần continuation / chống lặp vô hạn | Ngân sách bền vững: `remaining_decision_turns`, `remaining_patch_attempts`, `no_progress_count` với trần `max_no_progress` (mặc định `GOAL_CONTINUATION_MAX_NO_PROGRESS = 2`) → tự pause `GOAL_CONTINUATION_NO_PROGRESS` (`run_continuation_ledger.py`) | Đã có — **không port** |
| Prompt/draft do model judge viết | Dispatch qua EOCL + grant hiện tại, proposal qua `continuation_proposal` profile | Khác triết lý — **không port** (xem §3) |

**Khoảng trống thật đã xác minh cho Goal:** thiếu một hàm tín hiệu hoàn thành *thuần, xác định,
dùng chung được* (coverage + ngân sách episode → complete / lý do chưa xong / may_continue),
để tầng continuation và các consumer nhẹ không phải chạy toàn bộ live projection mới biết
Goal đã xong hay chưa và vì sao.

## 2. Logic đã port (lượt này)

Module leaf mới: `resources/coding-tools-mcp/coding_tools_mcp/continuation_send_state.py` (233 dòng,
chỉ import stdlib/typing — đúng quy tắc module của package: leaf không import `server.py`).

| Hàm / hằng | Hành vi |
|---|---|
| `SEND_STATE_NOT_ATTEMPTED` / `SEND_STATE_STARTED_UNKNOWN` / `SEND_STATE_POSSIBLY_SENT` / `SEND_STATE_CONFIRMED`, `SEND_STATES` | Taxonomy 4 mức canonical: `not_attempted` / `started_unknown` / `possibly_sent` / `confirmed` (ánh xạ 1-1 với 4 tên wire của CoS theo bảng §1.1) |
| `normalize_send_state(value)` | Chuẩn hoá cả tên canonical lẫn tên CoS (`not-attempted`, `attempted-unresolved`, `dispatched-unresolved`, `sent`); tên lạ → `ValueError` |
| `advance_send_state(current, next)` | Chuyển trạng thái **đơn điệu**: bằng nhau = idempotent, tiến (kể cả nhảy cóc khi bằng chứng xác nhận đến muộn) = OK, **lùi = `ValueError`** — một effect `possibly_sent`/`confirmed` không bao giờ bị viết lại thành trạng thái được-phát-lại; `confirmed` là terminal |
| `send_may_be_replayed(state)` | Chỉ `True` cho `not_attempted` + `started_unknown` (đúng hàm `sendUnattempted` của CoS: cả hai đều được ghi trước dispatch nên chứng minh chưa gửi gì) |
| `send_requires_reconciliation(state)` | Chỉ `True` cho `possibly_sent` — **unknown thì không gửi lại, phải reconcile** |
| `normalize_send_checkpoint(value)` | Chuẩn hoá checkpoint `{state, message_id}` (chấp nhận cả `messageId` kiểu CoS), bỏ key lạ, giới hạn độ dài |
| `handoff_resume_directive(checkpoint)` | Lệnh resume cho người đọc handoff: `REPLAY_SAFE` / `RECONCILE_BEFORE_REPLAY` / `ALREADY_CONFIRMED` + cờ `may_replay`, `requires_reconciliation`. Chỉ *nêu quyết định*, không tự cấp quyền gửi — quyền vẫn qua EOCL/grant |
| `goal_completion_signal(coverage, *, no_progress_count, max_no_progress, remaining_decision_turns, remaining_patch_attempts)` | Tín hiệu Goal xác định: `complete` chỉ khi có ≥1 criterion và tất cả đều `PROVEN`/`SATISFIED_NON_CODE`; `incomplete_reasons` (`UNRESOLVED_CRITERIA`, `CRITERIA_UNAVAILABLE`, `NO_PROGRESS_LIMIT_REACHED`, `DECISION_TURNS_EXHAUSTED`, `PATCH_ATTEMPTS_EXHAUSTED`); `may_continue` sai khi đã complete hoặc chạm hard-stop; `signal_source = DETERMINISTIC_CRITERION_COVERAGE` |

### Điểm nối vào contract hiện hữu (không tạo controller/ledger thứ hai)

1. **Handoff capsule** (`coding_tools_mcp/coordination.py`, nhánh `task_control action=handoff`):
   - `handoff_action=record`: nếu payload có `send_checkpoint`, nó được `normalize_send_checkpoint`
     chuẩn hoá trước khi ghi capsule; checkpoint sai → `ToolFailure("HANDOFF_SEND_CHECKPOINT_INVALID")`.
     Payload không có checkpoint → hành vi cũ, tương thích ngược hoàn toàn.
   - `handoff_action=get`: nếu capsule có `send_checkpoint`, response kèm `send_replay_directive`
     và `recommended_next_action` đổi theo directive — đặc biệt `possibly_sent` trả lệnh
     *"Do not replay… Reconcile the destination first"* thay cho lời khuyên resume chung chung.
2. **Goal live summary** (`coding_tools_mcp/goal_pursuit.py`, `goal_pursuit_live_summary`):
   trường cộng thêm `completion.criterion_signal = goal_completion_signal(coverage)` tính từ
   chính coverage map mà projection đã dựng (None khi fact window unavailable, khớp các count None
   hiện hữu). Không đổi bất kỳ trường/verdict hiện có nào.

### 2.1 Nối dây vào driver (lượt sau — hoàn tất phần "Còn lại" của §5 cũ)

Module mixin mới `coding_tools_mcp/continuation_wiring.py` (`ContinuationWiringMixin`,
`ContinuationDriverMixin` kế thừa — tách module vì ngân sách 1.600 dòng của
`continuation_driver.py` theo AGENTS.md của package; driver còn 1.467 dòng, wiring 196 dòng):

1. **Driver → send_checkpoint khi dispatch unknown** (`_run_continuation_record_dispatch_unknown_checkpoint`):
   mọi nhánh `DISPATCH_UNKNOWN` của `_run_continuation_observe_driver` (mất identity dispatch,
   bridge không còn own thread sau restart, bridge observe lỗi) và của
   `_run_continuation_reconcile_driver`, cộng nhánh tương đương `PROOF_OUTCOME_UNKNOWN`
   (proof Job không chứng minh được terminal), đều ghi checkpoint
   `{state: possibly_sent}` lên capsule của đúng RUN đó qua
   `OrchestrationLedger.record_handoff_capsule` — cùng store/cơ chế record mà coordination
   handoff dùng. Payload capsule trước được giữ nguyên và cộng thêm checkpoint + marker
   `continuation_dispatch_unknown {action_id, reason}`; nếu cộng dồn vượt giới hạn kích thước
   capsule thì ghi capsule tối thiểu chỉ chứa contract checkpoint. Ghi là **đơn điệu**: capsule
   đã ở `possibly_sent`/`confirmed` thì không ghi lại (không bao giờ hạ cấp một effect đã
   confirmed), và là best-effort không-raising — ghi lỗi không đổi kết quả fail-closed của
   driver. Kết quả driver trả thêm trường `send_checkpoint {state, recorded}`. Lượt resume sau
   đọc capsule qua coordination `handoff get` sẽ nhận directive `RECONCILE_BEFORE_REPLAY`
   như §2 đã chốt.
2. **Episode machinery → tiêu thụ `goal_completion_signal`** (`_run_continuation_episode_goal_signal`
   + `_run_continuation_episode_stop`): tại ba điểm driver sắp tạo dispatch mới cho một
   RUN con của Goal episode — (a) nhánh READ của observe driver trước `_run_continuation_dispatch_next`,
   (b) nhánh BLOCKED (model xin dừng) trước technical replan/dispatch repair,
   (c) nhánh proof-fail của `_run_continuation_complete_proof` trước technical replan/dispatch repair
   (sau xử lý `goal_observation.stopped` hiện hữu) — driver tính tín hiệu từ **cùng facts mà
   goal_pursuit đã dựng**: coverage lấy từ `goal_pursuit_live_summary().completion.criterion_signal`
   (tái dựng map trạng thái từ chính signal đó: id unresolved giữ nguyên, criterion đã proven
   tính theo số lượng — đủ cho verdict complete/unresolved/counts), ngân sách lấy từ hàng
   `goal_continuations` của episode cha (`no_progress_count` — ưu tiên số tươi từ
   `goal_observation` khi có, `policy.max_no_progress`, `remaining_decision_turns`,
   `remaining_patch_attempts` — các remaining này được ledger trừ authoritative khi reserve/consume).
   Quyết định: `complete` → dừng hẳn, trả `GOAL_COMPLETE / CRITERIA_COMPLETE`, không dispatch thêm;
   `may_continue=false` vì hard-stop → dừng đúng lý do (`PAUSED` + `stop_reason` của signal,
   riêng `NO_PROGRESS_LIMIT_REACHED` ánh xạ về mã hiện hữu `GOAL_CONTINUATION_NO_PROGRESS`);
   còn lại → `None`, luồng cũ quyết định như trước. RUN không thuộc episode nào → `None`,
   hành vi không đổi. Tín hiệu chỉ là đầu vào quyết định: nó không tự dispatch, không cấp
   quyền — mọi dispatch vẫn qua EOCL/grant như cũ.

## 3. Logic cố ý KHÔNG port + lý do

| Phần của CoS | Lý do không port |
|---|---|
| Model judge qua OpenRouter (key riêng, `z-ai/glm-5.3`, prompt hệ thống Goal/Loop trong `shared/goal.ts`) | Gọi model ngoài là phụ thuộc runtime mới + credential mới; Codex-web đã có tín hiệu xác định từ proof/coverage và dispatch qua EOCL — port judge sẽ tạo một authority quyết định "xong/chưa" thứ hai, trái nguyên tắc chương trình |
| Goal draft + ack-token tombstone của CoS | Codex-web đã có idempotency tương đương/mạnh hơn ở tầng ledger (`observation_id` + conflict, content-addressed grant, action seq) — port thêm một cơ chế ack song song là nhân đôi |
| Engine Goal/Loop tự lái (tự soạn prompt, tự gõ vào composer, `GOAL_HOLD_TOOLS`, decision chat) | Đó là một controller thứ hai chạy song song EOCL; kế hoạch §7 đã chốt: chỉ học state/logic, quyết định dispatch vẫn qua EOCL + grant hiện tại |
| Transaction open→claim→commit/abort của `continuation.ts` (bản thân state machine + WAL/`CONTINUATIONS_STATE`, single-instance lock, TTL theo model Pro/thường) | Codex-web đã có capsule bền vững + controller lease/fencing/reattach + continuation ledger với claim một-lần; phần đáng học (taxonomy send 4 mức + quy tắc không-phát-lại) đã được port ở §2, phần khung giao dịch còn lại là trùng lặp hạ tầng |
| Extension/DOM ChatGPT, composer automation | Ngoài phạm vi hướng mới: sản phẩm không phụ thuộc app/trang CoS nữa |

## 4. Test

Môi trường VM không có `pytest` cho python hệ thống → chạy bằng `unittest` (các test đều viết kiểu
unittest, pytest trên Windows sẽ thu thập như thường). Lệnh (từ `resources/coding-tools-mcp`):

| Suite | Lệnh | Kết quả |
|---|---|---|
| Mới: send-state + checkpoint + goal signal + capsule round-trip | `python3 -m unittest tests.test_continuation_send_state` | **15/15 OK** |
| Liên quan: goal pursuit + run continuation + coordination state | `python3 -m unittest tests.test_goal_pursuit tests.test_run_continuation tests.test_coordination_state` | **74/74 OK** |
| Controller continuity | `python3 -m unittest tests.test_controller_continuity` | **9/9 OK** |
| Module-size guard (quy tắc package) | `python3 scripts/check_module_size.py` | **ok** (`continuation_send_state.py` 233 dòng; `coordination.py` 1.500 < 1.600; `goal_pursuit.py` 1.086 < 1.600) |

Test mới (`tests/test_continuation_send_state.py`, 15 test) bao phủ: chuẩn hoá tên canonical + CoS,
từ chối trạng thái lạ, chuyển đơn điệu/idempotent/nhảy cóc/cấm lùi/`confirmed` terminal,
bảng chân trị replay × reconcile × directive cho cả 4 mức (gồm quy tắc lõi: `possibly_sent`
không bao giờ `may_replay`), checkpoint camelCase + bỏ key lạ + từ chối shape sai,
round-trip capsule qua `OrchestrationLedger` giữ nguyên checkpoint, và tín hiệu Goal
(complete / unresolved còn tiếp tục được / trần no-progress / cạn ngân sách / coverage rỗng).
Không ghi nhận fail có sẵn nào trong các suite đã chạy.

## 5. Trạng thái W4

- ~~Gắn `send_checkpoint` vào producer thật trong driver~~ — **XONG** (§2.1 mục 1): mọi nhánh
  `DISPATCH_UNKNOWN` + `PROOF_OUTCOME_UNKNOWN` tự ghi `possibly_sent` lên capsule của RUN.
- ~~Cho driver/goal-continuation tiêu thụ `goal_completion_signal` khi quyết định continue/stop~~ —
  **XONG** (§2.1 mục 2): cổng tín hiệu tại 3 điểm dispatch (READ / BLOCKED / proof-fail).
- Test nối dây (từ `resources/coding-tools-mcp`, bằng `unittest` như các lượt trước):

  | Suite | Kết quả |
  |---|---|
  | Mới: `tests.test_continuation_goal_wiring` (driver ghi checkpoint khi unknown + không hạ cấp confirmed; episode dừng khi signal complete; episode dừng khi cạn ngân sách với đúng lý do) | **4/4 OK** |
  | Hồi quy: `test_continuation_send_state` + `test_goal_pursuit` + `test_run_continuation` + `test_coordination_state` + `test_controller_continuity` | **98/98 OK** |
  | Kề bên: `test_controller_reattach` + `test_continuation_consent_http` + `test_cross_session_continuity_report` | **39/39 OK** |
  | Module-size guard | **ok** (`continuation_driver.py` 1.467 < 1.600; `continuation_wiring.py` 196) |

  Lưu ý harness: `Runtime.orchestration_ledger` là compatibility view uỷ quyền cho primary
  ledger — stub precondition của controller phải cài trên `ledger._primary` mới tới được
  self-call bên trong ledger (đã ghi trong test).

**W4 phần logic = DONE.** Còn lại của chương trình không thuộc W4-logic: worker board/UI (W2),
chat native (W3), đóng gói + nghiệm thu (W6).

## 6. Hướng chương trình sau chỉ đạo 19:03

Logic CoS được **gộp native vào Codex-web** (module Python ở trên; các port UI/diff ở W2; chat native
qua Codex App Server + ChatGPT-over-MCP ở W3). App CoS không phải phụ thuộc runtime: không cần cài,
không cần chạy, không cần Control API của nó cho sản phẩm cuối. Adapter W1 giữ vai trò cầu tham chiếu
tùy chọn, không phải đường chính.
