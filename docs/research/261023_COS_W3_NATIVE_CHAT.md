# W3 (lát cắt đầu) — Chat native trong Codex-web qua Codex App Server

- Ngày: 2026-10-23 (Asia/Saigon). Phạm vi: snapshot VM `~/workspace/projects/Codex-web` — **không commit/push, không restart, không packaged**.
- Hướng (chỉ đạo user 19:03 23/10): **kết hợp logic tính năng CoS vào Codex-web** — chat phải chạy native trong Codex-web, **không** cài/chạy app CoS. CoS chỉ là nguồn tham chiếu (MIT) trong thư mục nghiên cứu. Tài liệu này là phần W3-B của kế hoạch gốc (Codex App Server trong cùng giao diện) theo ranh giới §5.3 của W2; W3-A (companion) đã bị hạ xuống cầu tham chiếu tùy chọn ở W1, W3-C ở mục 6.
- Tiền lệ đã đọc: `AGENTS.md` (repo + package MCP), W1 (`261023_COS_W1_ADAPTER.md`), W2 (`261023_COS_W2_UI_PORT.md` §5.3).

## 1. Kiểm toán contract `codex_bridge.py` (1.533 dòng, đã đọc toàn bộ)

`CodexAppServerBridge` là sidecar độc lập: nó spawn `codex app-server --listen stdio://` (JSON-RPC qua stdio), **chia sẻ CODEX_HOME** (auth, skills, config, lịch sử đã persist) với Codex Desktop nhưng **không bao giờ claim lượt đang chạy trong bộ nhớ của Desktop**. Discovery binary theo thứ tự: env `CODING_TOOLS_MCP_CODEX_BIN` → `CODEX_BIN` → `which("codex")` → `%LOCALAPPDATA%\OpenAI\Codex\bin\*\codex.exe` (đã kiểm chứng trong `discover_codex_binary`). Các MCP server đã cấu hình trong Codex home bị tắt trong sidecar (cô lập).

### 1.1 Primitive thật (`handle()`, 8 action)

| Action | Việc thật | Giới hạn quyết định cho chat |
|---|---|---|
| `status` | Trạng thái sidecar: connected, pid, binary, codex version/home, workspace, safety, profile defaults, capacity cooldowns | **Tự spawn sidecar** (`_ensure_connected`) — không có probe "không chạm"; lỗi `CODEX_NOT_FOUND` (retryable) khi không có binary |
| `models` | `model/list` của App Server | Đủ cho selector model sau này; lát cắt này chưa dùng |
| `threads` | `thread/list`, lọc theo workspace hiện tại, trả summary (id, name, preview, cwd, created/updated, status, forkedFrom) | **Chỉ summary** — không có action đọc turns/nội dung của thread đã persist; thread Desktop là *inspect/fork only* |
| `run` | `thread/start` (hoặc `thread/fork` khi có `source_thread_id` + profile `history`) rồi `turn/start` với prompt; thread thành *bridge-owned* | Thread **chỉ được tạo cùng prompt đầu tiên** — không có create-empty; prompt ≤ 20.000 ký tự; `wait_ms`/`deadline_ms` tùy chọn (deadline hết hạn thì interrupt) |
| `continue` | Thêm một turn vào thread bridge-owned (`turn/start`) | **Chỉ thread do chính tiến trình sidecar hiện tại sở hữu** (`THREAD_NOT_OWNED`); sidecar/MCP restart là mất quyền tiếp tục — resume bền chỉ có qua lane *persistent* nội bộ (`restore_persistent_thread`/`resume_persistent_thread`, không expose qua `handle()`, đang do machinery Goal/continuation dùng) |
| `observe` | Poll theo cursor: `agent_text` tích lũy (delta `item/agentMessage/delta` + `item/completed`), events có ý nghĩa (turn started/completed, item khác user/agent message, server request), token usage, economics; có `history_gap` khi cursor bị evict khỏi ring 400 events | Đây là "streaming" duy nhất: **poll**, không có kênh stream tới caller; `agent_text` bị cắt 65.536 ký tự |
| `interrupt` | `turn/interrupt` cho turn bridge-owned | — |
| `close` | Tắt cây tiến trình sidecar | Xóa sạch owned threads/turn states |

### 1.2 Tính chất mọi turn (không đổi theo profile)

- `approvalPolicy=never`, sandbox **read-only**, **không mạng**; request phê duyệt từ App Server bị bridge *decline* tự động, request host khác bị trả method-not-supported — bridge **không phục vụ tương tác phê duyệt**.
- 11 profile có sẵn đều là *review lane* (candidate/cross-file/deep-code/consequential/parallel/packet/scoped/critical/history/continuation): base instructions bắt model làm reviewer/candidate-generator, không phải hội thoại. **Đây là khoảng trống contract duy nhất cần mở cho chat** — xem mục 3.
- Model capacity có circuit breaker 30s (`MODEL_CAPACITY_COOLDOWN`); route khóa cứng cho `continuation_proposal`.

**Kết luận kiểm toán:** chat tương tác native làm được ngay ở mức: tạo thread bằng prompt đầu → gửi tiếp bằng `continue` → nhận trả lời bằng poll `observe`. Không bị chặn ở bridge; hai giới hạn thật là (i) instructions của profile (đã xử lý ở mục 3) và (ii) quyền sở hữu thread chỉ sống theo tiến trình sidecar (UI phải nói rõ, xem mục 4). Không được gọi đây là phiên ChatGPT Web — đây là phiên **Codex App Server**.

## 2. Trạng thái provider — tách bạch VM / Windows

- **VM (snapshot này): không có provider của user.** Gateway 9 account chết từ 22/10; `codex` thấy trên VM là của môi trường agent, không phải provider sản phẩm — không dùng để lấy live proof.
- **Windows: provider ĐÃ LIVE (tối 23/10, thông tin từ phiên làm việc khác, đã vào MEMORY.md).** Codex CLI cài qua npm vào profile Admin, `auth.json` sẵn có xác thực được, probe `codex exec` trả `PROVIDER_OK`; bridge trên Windows trỏ bằng env `CODING_TOOLS_MCP_CODEX_BIN=%APPDATA%\npm\codex.cmd` — đúng khóa env đầu tiên mà `discover_codex_binary` đọc. Natural Goal E2E pilot cùng tối đã chạy qua production bridge thật (gpt-5.6-sol/xhigh).
- Hệ quả: phần implement + test của lát cắt này làm trên VM bằng **fake bridge**; **live smoke khả thi ngay ở bước tiếp theo trên Windows** (mục 7), không còn là "chờ provider vô định".

## 3. Thay đổi ở bridge: profile `chat` (tối thiểu, có chủ đích)

- Thêm đúng một profile vào `_PROFILE_SPECS` trong `codex_bridge.py`: `chat` — model `gpt-5.6-terra`, effort `medium`, `shell_tool=True` (đọc workspace), còn lại giữ `_REVIEW_FEATURES` (multi_agent/apps/browser/computer/plugins… đều tắt). Base instructions là **hội thoại** (trợ lý chat của Work Hub, trả lời + đọc workspace read-only) và nói thẳng trong instructions: chat không sửa tệp/không mạng, thay đổi chỉ qua Job/duyệt.
- Thêm `"chat"` vào enum `profile` của tool `codex_bridge` trong `tool_schema.py` (chỉ tool đó; enum của persistent-lane ở dòng 618 không đổi).
- **Không đổi public MCP surface smart-v3** (vẫn đúng 8 tool công khai). Đường Work Hub dùng là tool nội bộ `codex_bridge` đã đăng ký sẵn (`tool_contract.py`: read_only, card "agent") qua kênh panel hiện hữu — cùng cách `workhub:job-run` gọi `exec_command` và `workhub:handoff-get` gọi `task_control`. Không thêm tool, không thêm route.
- Module size: `codex_bridge.py` 1.533 → 1.554 dòng, trong ngân sách 1.600 (`scripts/check_module_size.py` PASS).

## 4. Lát cắt native đã làm (Work Hub)

| File | Thay đổi |
|---|---|
| `electron/services/workHubCodexChat.js` | **Mới** — service ở main process, transport tiêm vào (`callBridge`). Quản phiên chat theo workspace: `probe` (bridge status → trạng thái + định danh provider), `listHistory` (threads Desktop, gắn `continuable:false`), `send` (thread chưa có → `run` profile `chat`; đã có → `continue`), `poll` (observe theo cursor, cập nhật text assistant + events, chốt trạng thái terminal), `interrupt`, `reset`, `getView`. Mọi method resolve result object `{ok, state, error?, data}`, không throw |
| `electron/main.js` | Require service; 6 handler `workhub:codex-chat-probe|history|send|poll|interrupt|reset` qua `secureHandle` + `invokeSafely`, keyed bằng `scopedWorkHubRoot(payload.expectedWorkspace)`; transport = `callMcpTool('codex_bridge', args, timeout)` sẵn có |
| `electron/preload.js` | Expose 6 hàm `workhubCodexChat*` cụ thể (không expose fetch/transport tổng quát) |
| `renderer/index.html` | Panel **"Chat Codex (native)"** ngay sau panel companion: state, timeline (`whCodexChatLog`), events gần nhất, composer, nút Gửi/Làm mới lượt/Dừng lượt/Chat mới, dòng liên kết RUN, danh sách lịch sử |
| `renderer/work-hub.js` | `renderCodexChat/paintCodexChat/sendCodexChat/pollCodexChatTurn` + polling 1,5s khi RUNNING (scope-guard theo project như các panel khác, dừng khi đổi project/terminal); render bằng `textContent`/`el()`; gọi trong `refresh()`; dọn panel khi đổi project; liên kết RUN lấy từ `ui.taskPayload.state.orchestration.run_id` **tại lúc tạo chat** |
| `renderer/work-hub.css` | Style `.wh-chat-log/.wh-chat-msg/.wh-chat-head/.wh-chat-body` theo biến màu sẵn có |
| `tests/work-hub-codex-chat.test.js` | **Mới** — fake bridge scripted |
| `resources/coding-tools-mcp/tests/test_codex_bridge.py` | Thêm test profile `chat` |

### 4.1 Ngữ nghĩa trung thực đã khóa trong UI/service

- **Trạng thái lấy từ bridge**, không bịa: `UNKNOWN → READY` (status OK) / `RUNNING` / `COMPLETED` / `FAILED` / `INTERRUPTED` / `PROVIDER_UNAVAILABLE` (không binary — phân loại từ message lỗi của bridge, tập trung ở `classifyBridgeError`) / `MCP_UNAVAILABLE` / `OWNERSHIP_LOST` (khi `continue` trả `THREAD_NOT_OWNED` — UI ghi rõ "MCP/App Server đã khởi động lại, tạo chat mới"; timeline cũ vẫn giữ nguyên để đọc).
- **Composer khóa đúng lý do**: nút Gửi bị disable + state line nêu lý do khi provider/MCP chưa sẵn sàng, khi đang chạy lượt, hoặc khi mất ownership. Không có nút nào giả vờ gửi được khi bridge không cho.
- **Timeline** = đúng các tin user đã gửi qua panel + `agent_text` của bridge theo từng turn; events hiển thị là events bridge trả về (method/item type/status), không trang trí thêm.
- **Liên kết thread ↔ RUN**: chỉ khi renderer có `run_id` thật trong task state lúc tạo chat; service ghi `link {runId, taskId}` cạnh thread và UI in nguyên văn. Không có RUN → ghi "Chưa liên kết RUN". Không bao giờ suy diễn từ nội dung chat.
- **Lịch sử Desktop**: hiển thị summary với nhãn chỉ-xem + ghi rõ muốn dùng phải fork (bước sau) — không có nút "tiếp tục" giả.

## 5. Test đã chạy

- Python: `python3 -m unittest tests.test_codex_bridge` trong `resources/coding-tools-mcp` → **23/23 OK** (gồm test mới: profile `chat` resolve terra/medium + shell_tool, base instructions hội thoại, turn vẫn `approvalPolicy=never` + `sandboxPolicy readOnly/no-network`, thread thành bridge-owned). (Môi trường VM không có `pytest`; file test là unittest-style nên chạy bằng unittest — kết quả tương đương cho file này.) `scripts/check_module_size.py` → ok.
- Node: `node --test tests/work-hub-codex-chat.test.js` → **10/10 PASS**: probe READY/định danh provider; probe thiếu binary → `PROVIDER_UNAVAILABLE` và send từ chối **không gọi run**; send đầu → `run` đúng profile + link chỉ khi được cấp; poll theo cursor → text tăng dần → `COMPLETED`; send hai → `continue` đúng thread; `THREAD_NOT_OWNED` → `OWNERSHIP_LOST` + reset → chat mới; chặn gửi chồng/rỗng/kết quả malformed; history inspect-only; interrupt; phân loại MCP-down khác provider-missing.
- Không hồi quy vùng liên quan: 14 suite (work-hub ui/store/scope/render-scope/coordination/files/diff-view/jobs/browser-qa/lsp/ssh + cos-companion-adapter + work-hub-codex-chat + settings) → **146 PASS, 0 fail** (147 test, 1 skipped có sẵn). Trong quá trình này đã bắt và sửa 1 hồi quy thật do chính lát cắt gây ra: fixture của `work-hub-scope.test.js` đánh giá đoạn main.js từ `workHubRoot` tới handler `workhub:check-url`, block handler chat ban đầu nằm trong đoạn đó và sandbox của fixture không có `createWorkHubCodexChat` → 5 test fail; đã chuyển block handler chat ra sau `workhub:check-url`, scope test trở lại 6/6.
- Lỗi có sẵn từ trước, không liên quan W3: `tests/chat-ui-compact.test.js` fail 1/6 (kỳ vọng chuỗi trong `renderer/app.js`, đã ghi nhận ở W1/W2).
- `node --check` đạt cho 4 file JS đã sửa/tạo.

**Chưa phải live proof:** tất cả kết quả trên là fake-bridge/fake-App-Server ở tầng test. Chưa có lượt chat thật nào chạy qua panel này.

## 6. W3-C — handoff ChatWeb ⇄ Codex Desktop ⇄ Work Hub (mức đã xác minh)

Các mảnh ghép đều có thật và đã có đường dây một phần:

- **Codex Desktop → Hub**: `electron/services/codexDesktopConfig.js` (36 dòng) sinh config TOML cho Codex Desktop trỏ MCP server `coding-tools` vào `python -m coding_tools_mcp.hub_proxy_stdio --descriptor <hubProxyDescriptorFile>` — mode `single_runtime_proxy`, **không chứa bearer** trong config.
- **Proxy**: `resources/coding-tools-mcp/coding_tools_mcp/hub_proxy_stdio.py` (295 dòng) — proxy stdio: nạp descriptor của Execution Hub, validate client identity (`validate_proxy_identity`), forward JSON-RPC, có heartbeat. Panel main đã có handler `panel:copy-codex-config` dùng config này.
- **Capsule/lease**: handoff capsule nằm trong orchestration ledger; đọc qua `task_control` action `handoff` (get) — panel đã nối (`workhub:handoff-get`, A8). Từ W4, capsule mang `send_checkpoint` chuẩn hóa và `handoff get` trả `send_replay_directive` + `recommended_next_action` (directive REPLAY_SAFE / RECONCILE_BEFORE_REPLAY / ALREADY_CONFIRMED) — đó là semantics "không gửi lại effect chưa biết" mà W3-C cần khi chuyển controller.
- **Controller lease** đọc từ ledger qua `workHubCoordination` (bảng điều phối RUN đã hiển thị lease owner + hết hạn).

Thiết kế bước tiếp theo cho W3-C (chưa làm ở lát cắt này): (1) từ panel chat native, khi user bấm "chuyển phiên", đọc capsule của RUN đã liên kết (đúng `run_id` trong `link`) và hiển thị directive; (2) chỉ cho phép phía nhận *tiếp tục* khi directive = REPLAY_SAFE hoặc đã reconcile; (3) mọi chuyển quyền ghi nhận bằng đúng capsule/lease của ledger — không tạo cơ chế handoff thứ hai. Điều kiện nghiệm thu W3 của kế hoạch (ba client cùng quan sát một RUN, một controller, một writer lease) được kiểm ở bước đó + W6 (T04).

## 7. Việc còn lại (theo thứ tự)

1. **Live smoke trên Windows** (khả thi ngay): đồng bộ các file của lát cắt này sang checkout Windows, chạy bản dev/packaged tương ứng, bật MCP với `CODING_TOOLS_MCP_CODEX_BIN=%APPDATA%\npm\codex.cmd`, mở Work Hub → panel Chat Codex: probe phải ra READY + version; gửi một câu hỏi test về workspace; nhận trả lời qua poll; thử Dừng lượt; lưu receipt (không kèm nội dung nhạy cảm). Đây là live proof đầu tiên của W3 — thuộc bước Windows/packaged, không làm trên VM.
2. **Fork từ lịch sử Desktop**: dùng `run` với `source_thread_id` + profile `history` để bắt đầu chat mới từ một thread Desktop đã chọn (hiện panel mới liệt kê lịch sử ở chế độ chỉ-xem).
3. **Thread bền qua restart MCP** (tùy chọn, cân nhắc sau): expose đường restore/resume lane persistent cho chat hoặc chấp nhận semantics OWNERSHIP_LOST hiện tại (đã trung thực trong UI).
4. **Selector model/effort** từ `action=models` + `profile_defaults` (hiện cố định terra/medium của profile `chat`).
5. **W3-C handoff** theo mục 6 và nghiệm thu T03/T04 ở W6; nhánh ChatGPT-over-MCP (ChatGPT gọi Coding Tools MCP) giữ nguyên đường vận hành hiện hữu, không nằm trong lát cắt chat native này.
