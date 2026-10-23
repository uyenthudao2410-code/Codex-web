# W1 — CoS Companion Adapter (read-only pilot)

- Ngày: 2026-10-23 (Asia/Saigon). Phạm vi: bản snapshot VM `~/workspace/projects/Codex-web` — **không commit/push, không restart, không packaged**. Nối tiếp W0: `docs/research/261023_COS_WEBCODEX_W0_AUDIT.md`.
- Nguyên tắc giữ nguyên: CoS API-first, adapter mỏng ở Electron main, **không** authority/ledger thứ hai, **không** UI-làm-proof.

## 1. Contract đã chốt

### 1.1 Discovery & auth (theo source CoS đã xác minh ở W0)

- CoS Local Control API: HTTP `127.0.0.1`, **cổng ephemeral** — không hardcode port.
- Discovery qua thư mục userData của CoS: `<userData>/control-api/endpoint.json` (`{protocol, port, pid, appVersion, startedAt}`, protocol phải = **1**) và `<userData>/control-api/token` (Bearer, CoS xoay mỗi lần khởi động listener).
- Adapter **đọc lại cả hai file ở mỗi request** — CoS restart làm endpoint/token đổi, adapter tự theo, không cần khởi động lại Codex-web.
- Token chỉ tồn tại trong tiến trình main (biến cục bộ của request + header `Authorization`). Không method nào trả token ra ngoài; mọi body phản hồi còn được **scrub** đối chiếu token trước khi rời adapter. Token không vào IPC, không vào log, không ghi file.

### 1.2 Đường dẫn userData của CoS (thứ tự ưu tiên)

1. Setting `cosCompanionUserDataDir` (Codex-web Settings, lưu qua `settings:save`).
2. Env `COS_USERDATA_DIR` (hoặc `COS_COMPANION_USERDATA_DIR`) — dùng cho test/tự động hoá.
3. Mặc định theo nền tảng (Electron userData của app CoS, productName "Chat On Steroids", appId `com.chatonsteroids.app`):
   - Windows: `%APPDATA%\Chat On Steroids`
   - macOS: `~/Library/Application Support/Chat On Steroids`
   - Linux: `$XDG_CONFIG_HOME/Chat On Steroids` (hoặc `~/.config/Chat On Steroids`)

Thư mục adapter đọc là `<userData>/control-api/` bên trong các đường dẫn trên.

### 1.3 Trạng thái kết nối

| Trạng thái | Khi nào |
|---|---|
| `DISCONNECTED` | Flag tắt, hoặc không có `endpoint.json` (CoS chưa chạy/chưa bật Control API), hoặc chưa từng kết nối được |
| `CONNECTED_READ_ONLY` | `GET /v1/health` OK, protocol 1, CoS `actions.enabled=false` |
| `ACTIONS_AUTHORIZED` | Health OK **và CoS tự báo** `actions.enabled=true`. Adapter chỉ *báo cáo* — nó không có bất kỳ code path POST nào và không bao giờ tự bật phía CoS |
| `STALE` | Đã từng kết nối, request mới nhất thất bại (mất kết nối/timeout/HTTP error/auth sau khi đã OK) |
| `UNKNOWN` | Peer trả lời nhưng dữ liệu không tin được: protocol ≠ 1 hoặc JSON malformed |

Lỗi được mã hoá: `COS_DISABLED`, `COS_NOT_RUNNING`, `COS_ENDPOINT_INVALID`, `COS_PROTOCOL_MISMATCH`, `COS_AUTH`, `COS_RATE_LIMITED` (tôn trọng 429 của server, không retry dồn), `COS_TIMEOUT` (mặc định 5000ms/request), `COS_UNREACHABLE`, `COS_HTTP_ERROR`, `COS_MALFORMED`, `COS_BAD_REQUEST`. Mọi method **resolve bằng result object, không throw** — CoS chết/hỏng không làm chết main process hay MCP.

### 1.4 Methods (chỉ GET)

`probe()`/`getHealth()` → `/v1/health`; `getStatus()` → `/v1/status` (projection rút gọn: connection state/detail, bridge running/paired, tool calls đang chạy); `listSessions({limit≤50, cursor})` → `/v1/sessions`; `getSession(id, {live})` → `/v1/sessions/{id}`; `getSessionEvents(id, {from, limit≤200, kinds})` → `/v1/sessions/{id}/events`.

Projection giữ **nguyên** `sessionId`/`conversationId`/`projectId` của CoS, cắt text sự kiện ở 20.000 ký tự, và gắn nhãn `observation: 'OBSERVED'` cho mọi phiên/sự kiện. Không suy ra `run_id`/`job_id`/`proof_id`, không ghi ledger.

## 2. Cách bật

1. Phía CoS: bật `controlApi.enabled=true` (giữ `allowActions=false` cho pilot đọc) và để CoS chạy — listener tự ghi `endpoint.json`/`token`.
2. Phía Codex-web: `settings.save({ cosCompanionEnabled: true })` (đã thêm vào allowlist của `settings:save`). Nếu CoS cài ở vị trí lạ: `cosCompanionUserDataDir: '<đường dẫn userData CoS>'`.
3. Mở Work Hub → nhóm "Công việc, kiến thức & tích hợp" → panel **ChatGPT companion (CoS)**: trạng thái kết nối, danh sách phiên (tiêu đề, thời gian, nhãn OBSERVED), bấm "Xem sự kiện" để đọc events của phiên đã chọn. Không có nút gửi/dừng/tiếp tục nào.

Tắt flag → adapter không khởi động hành vi nào (mọi IPC trả `COS_DISABLED`/`DISCONNECTED`), Work Hub trở lại nguyên trạng.

## 3. Files đã tạo/sửa

| File | Thay đổi |
|---|---|
| `electron/services/cosCompanionAdapter.js` | **Mới** — adapter + discovery + projection + scrub token |
| `electron/services/config.js` | Thêm `cosCompanionEnabled: false`, `cosCompanionUserDataDir: ''` vào DEFAULTS + normalize |
| `electron/main.js` | Require adapter; 3 handler `workhub:cos-status` / `workhub:cos-sessions` / `workhub:cos-session-events` (bám pattern `secureHandle` + `invokeSafely` của workhub); thêm 2 key vào allowlist `settings:save` |
| `electron/preload.js` | Expose `workhubCosStatus`, `workhubCosSessions`, `workhubCosSessionEvents` — hàm cụ thể, không expose token/fetch tổng quát |
| `renderer/index.html` | Panel companion trong Work Hub |
| `renderer/work-hub.js` | `renderCosCompanion()` + `openCosSession()` — render bằng `textContent`/`el()` (không innerHTML với dữ liệu CoS), scope-guard theo project (`requestScope`), dọn panel khi đổi project; gọi trong `refresh()`; nút "Làm mới companion" |
| `tests/cos-companion-adapter.test.js` | **Mới** — fake CoS server HTTP thật trên loopback |

## 4. Test đã chạy (VM, Node 24)

- `node --test tests/cos-companion-adapter.test.js` → **12/12 PASS**. Bao phủ đúng các ca yêu cầu: (a) token sai → `COS_AUTH`, không rò token (kể cả token sai); (b) protocol mismatch ở endpoint.json **và** ở health → `COS_PROTOCOL_MISMATCH` + `UNKNOWN`; (c) server tắt giữa chừng → `STALE` (`COS_UNREACHABLE`), gọi tiếp vẫn fail-soft; CoS chưa chạy → `DISCONNECTED`; (d) JSON malformed → `COS_MALFORMED` + `UNKNOWN`; (e) token không xuất hiện trong bất kỳ object nào adapter trả (probe/status/sessions/session/events/connection view); (f) flag tắt → `COS_DISABLED`, không kết nối; cộng happy-path OBSERVED, `ACTIONS_AUTHORIZED` chỉ khi CoS tự bật, settings default/normalize, thứ tự discovery.
  - Trong lúc test đã bắt và sửa 1 bug thật: nhánh flag-tắt của `_get` trả sai shape khiến lỗi bị báo thành `COS_MALFORMED` thay vì `COS_DISABLED`.
- Không hồi quy ở vùng liên quan: `node --test tests/work-hub-ui.test.js tests/work-hub-store.test.js tests/work-hub-scope.test.js tests/work-hub-render-scope.test.js tests/work-hub-coordination.test.js tests/work-hub-files.test.js` → **77/77 PASS**; `tests/settings.test.js` **15/15**, `tests/settings-redesign.test.js` **20/20**, `tests/codex-desktop-config.test.js` **2/2**, `tests/chat-page-retirement.test.js` **3/3**.
- Một lỗi **có sẵn từ trước, không liên quan W1**: `tests/chat-ui-compact.test.js` fail 1/6 — test kỳ vọng chuỗi `Show the settings shell immediately` trong `renderer/app.js`, nhưng file đó (sửa lần cuối 22/10, W1 không đụng) không chứa chuỗi này. Ghi nhận để xử lý riêng, không sửa trong W1.

## 5. Nghiệm thu W1 (đối chiếu kế hoạch §4)

| Tiêu chí | Mức đã chứng minh |
|---|---|
| Mở/đóng CoS không làm chết Coding Tools MCP | Ở mức test: fake server tắt giữa chừng → adapter fail-soft `STALE`, main không throw (mọi method resolve result object). Chưa chứng minh trên app đóng gói thật |
| Ngắt kết nối trả trạng thái stale | PASS ở test (c) |
| Đổi project không lẫn hội thoại | Renderer scope-guard (`requestScope('cos')`) + xoá panel khi đổi project; phiên CoS **không** có binding project nên UI ghi rõ "chưa liên kết với dự án/RUN hiện tại" thay vì tự suy diễn |
| Token không xuất hiện trong renderer/log | PASS ở test (e) — token không rời main; preload chỉ expose 3 hàm cụ thể |
| Work Hub đọc được sự kiện mà không tự gửi lệnh | PASS ở test: adapter chỉ có GET; renderer chỉ có nút làm mới/xem, không có nút gửi/Stop/Resume |

## 6. Giới hạn đã biết

- **Worker CoS không đọc được ở read-only** (sai lệch S1 của W0): `GET /v1/workers/{ownerId}` và `/reports` bị CoS khóa sau `allowActions && multiAgent.enabled`. Adapter vì vậy **không** gọi route worker; connection view trả `workersReadable: false` kèm ghi chú, và Work Hub chỉ hiển thị worker EOCL như trước. Muốn xem worker CoS phải có quyết định riêng về việc bật `allowActions` phía CoS (ngoài phạm vi W1).
- Chưa dùng SSE `/events/stream` — W1 poll theo thao tác người dùng (làm mới/chọn phiên). Stream để W2/W3 khi có nhu cầu live thật.
- Chưa có UI trong trang Settings để bật flag — bật qua `settings:save` (IPC sẵn có) hoặc sửa file settings; thêm công tắc Settings là việc nhỏ để W2/W0.2 Windows làm kèm khi cấp endpoint thật.
- Chưa liên kết phiên CoS ↔ RUN/Job: đúng thiết kế P0 — liên kết chỉ khi có hành động/receipt xác định (W3).

## 7. W0.2 (Windows) sẽ cấp endpoint thật như thế nào

1. Cài/chạy CoS 2.1.45 (SHA `366404c1`) trên Windows, bật `controlApi.enabled=true`, `allowActions=false`.
2. Codex-web trên Windows bật `cosCompanionEnabled=true`; nếu userData CoS không ở `%APPDATA%\Chat On Steroids` thì đặt `cosCompanionUserDataDir` trỏ đúng thư mục chứa `control-api/endpoint.json`.
3. Tạo một **hội thoại TEST tự tạo** trong CoS, mở Work Hub panel companion: kỳ vọng thấy `CONNECTED_READ_ONLY`, phiên test với nhãn OBSERVED, đọc được events; lưu receipt (đã redact token) vào thư mục nghiên cứu.
4. Thử tắt CoS giữa chừng → panel phải chuyển `STALE`/`DISCONNECTED` và Codex-web vẫn chạy bình thường — đó là receipt đóng W0.2 và mở đường W2.
