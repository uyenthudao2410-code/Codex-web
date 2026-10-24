# Đường "não ChatGPT web" → tool Coding Tools Hub local — kiểm toán 23-10-2026 (chưa commit)

Yêu cầu của user (23:59 23/10): não là **model trên ChatGPT web** (chat tại chatgpt.com,
model ở đó trả lời), gọi xuống tool của Coding Tools Hub trên máy local — để khi Codex
Desktop/CLI hết hạn mức Codex thì vẫn làm việc qua hạn mức chat riêng.
Tài liệu này ghi kiến trúc thật trong code, trạng thái live đã kiểm chứng tối 23/10,
và các bước còn lại phía tài khoản ChatGPT của user.

## 1. Kiến trúc thật (đã kiểm chứng trong code, cây converged)

Có HAI đường ChatGPT → hub, chọn bằng `executionRole` trong settings của app:

### 1.1 Đường đang dùng: `central_executor` (qua Ubuntu Control Plane)

```
ChatGPT web (app "Ubuntu Control Plane", Developer Mode)
  → OpenAI Secure MCP Tunnel
  → Ubuntu Control Plane (svhome): MCP ingress riêng 127.0.0.1:8766, chỉ POST /mcp
     (control-plane/control_plane/mcp_facade.py; listener operator/API 8765 không có /mcp)
  → dispatch tới node đã enroll (Windows) qua connected node-agent
     (control-plane/control_plane/node_agent.py + các bridge controlPlane*Bridge.js)
  → Coding Tools MCP local (127.0.0.1:18766, HTTP /mcp, profile smart-v3, 8 tool)
```

- ChatGPT **không** gọi thẳng vào máy Windows. Dịch vụ trung gian là Control Plane tự
  vận hành trên svhome (origin `https://svhome.tail0e4032.ts.net`, Tailnet). Windows chỉ
  là *executor node*: giữ file/Git/process/quyền OS; Ubuntu xác thực, route, ghi receipt.
- Auth phía MCP có 3 mode (`legacy_context_grant` / `oauth_introspection` /
  `private_tunnel_service`). Kết nối cá nhân Plus đang dùng là private tunnel service:
  tunnel inject grant của service principal từ file owner-private; "không account linked"
  trong ChatGPT là **đúng thiết kế**, không phải lỗi.
- Bằng chứng lịch sử trong repo: 27-09-2026 kết nối Plus cá nhân đã trả `inventory` và
  `task_list` qua đúng đường này (control-plane/README.md, docs/CURRENT_STATE.md).

### 1.2 Đường dự phòng: `direct_legacy` (Tunnel thẳng xuống máy local)

App đóng gói sẵn `tunnel-client.exe` (OpenAI Tunnel). Luồng theo guide trong app
(renderer/index.html, trang "Hướng dẫn Kết nối"): tạo Tunnel trên OpenAI Platform →
tạo Runtime API Key → app chạy local MCP tại `http://127.0.0.1:18766/mcp` →
tạo Custom Connector trong ChatGPT chọn Tunnel đó. Tunnel client inject header
chứng thực HMAC `X-Coding-Tools-Connector-Attestation`
(electron/services/connectorAttestation.js) để hub phân biệt traffic ChatGPT thật
với caller loopback thường.

## 2. `CHANGED_NEEDS_DISCOVERY` nghĩa là gì, tự khỏi bằng gì

- "Tool contract" = SHA-256 chính xác của tools/list (smart-v3). Mỗi lần MCP process
  nhận **discovery** từ client `chatweb` qua transport đã chứng thực, nó ghi một
  discovery receipt {contract_sha256, process_instance_id, server_instance_id, epoch}
  (resources/coding-tools-mcp/.../runtime_activity.py `_record_tool_discovery`).
- Khi contract hiện tại khác SHA đã được operator **acknowledge** (persist trong app
  state) và chưa có discovery receipt cho SHA mới ở process hiện tại →
  `CHANGED_NEEDS_DISCOVERY`, `refreshRequired=true`
  (electron/services/runtimeOrchestrator.js `connectorContractStatus`).
  Nguyên nhân điển hình: bản build mới đổi schema tool (r19 vừa đổi — thêm profile
  `chat` vào enum của `codex_bridge`, thêm `job_input`...).
- Chuỗi tự khỏi: ChatGPT **fetch lại tools/list** (discovery mới, attested, đúng
  process hiện tại) → `CHANGED_DISCOVERED_NEEDS_ACK` → operator bấm acknowledge
  trong app Electron (hàm `acknowledgeExactConnectorDiscovery`, qua Recovery Host)
  → `CURRENT_ACKNOWLEDGED`. Có thêm đường compatibility cho SHA tiền nhiệm đã khai
  báo tương thích + có tools/call `workspace_context` hiện hành
  (`CHANGED_COMPATIBLE_NEEDS_ACK`).
- **Quan trọng cho đường central**: theo code `node_agent.runtime_readiness`, node ở
  vai `central_executor` chỉ cần `central_connected=true` + `authority_ready=true`
  là `ready` ("strict_central_route"); cổng rediscovery nghiêm ngặt chỉ áp cho đường
  direct. Nên `connector_ready=false` do NEEDS_DISCOVERY **không chặn** dispatch
  central — khớp ghi chú cũ của chương trình parity, nay đã kiểm chứng lại trong code.

## 3. Trạng thái live tối 23/10/2026 (bằng chứng trực tiếp)

| Thành phần | Trạng thái | Bằng chứng |
|---|---|---|
| Control Plane (svhome) | **SỐNG** | GET qua Tailnet proxy: `https://svhome.tail0e4032.ts.net/` → 200 và `http://100.116.112.22:8765/` → 200 (operator console HTML) lúc ~00:0x 24/10 +07 |
| App Windows (settings) | `executionRole=central_executor`, CP URL `https://svhome.tail0e4032.ts.net`, workspace `E:\DEV\Codex-web` | `%APPDATA%\web-mcp-assistant\settings.json` |
| Node enrollment | `approved`, credential_generation 1 | `control-plane-node.json` |
| Connected agent (Windows) | **Đang chạy nhưng degraded** | pid 14268 (node_agent.py run-connected-agent, bản r19); `control-plane-connected-agent-status.json`: iteration 531, `last_error_code=CONTROL_PLANE_BRIDGE_FAILED` (heartbeat) |
| Heartbeat tốt gần nhất | **ready lúc 23:58:46 +07** | `control-plane-route-evidence.json`: `runtime_readiness=ready`, `policy_state=enabled`, server_last_seen cùng thời điểm |
| Runtime local (Electron + Recovery Host + MCP :18766/:18082) | **ĐANG DỪNG** | Không process Coding Tools, không listener 18766/18082/18767/18083; `logs/mcp.log` ghi tới 23:58:59 +07 rồi ngừng; recovery-supervisor-status: `state=uninstalled, supervisor_pid=null` |

Kết luận live: phía Ubuntu/central **sẵn sàng**; phía Windows **executor đang tắt**
(agent còn chạy nhưng bridge vào runtime local thất bại vì runtime đã dừng ~23:59).
Ngay trước khi dừng, toàn chuỗi vẫn ready — đây là sự cố "runtime bị tắt", không phải
hỏng connector.

### Việc agent đã tự làm để chuẩn bị (và kết quả)

- Thử mở lại app đóng gói r19 qua Interactive scheduled task (2 cách: Start-Process
  trực tiếp và qua explorer, kèm WorkingDirectory) — **đều thất bại**: process thoát
  ngay, `win-unpacked\debug.log` ghi 3 lần
  `ERROR:base\i18n\icu_util.cc:232] Invalid file descriptor to ICU data received.`
  (00:06:38 / 00:09:35 / 00:10:01 +07). Ảnh desktop lúc thử:
  `~/workspace/research/cos-webcodex/chatgpt-web/prep-after-relaunch.png`.
  Nhận định: ở bản r19, việc khởi động stack phải đi qua đường Recovery Host/bootstrap
  của chính app (launch có truyền descriptor/FD), mở thẳng file exe không phải đường
  được hỗ trợ. Agent **không** chạy các script recovery khác khi chưa được duyệt riêng.
- Đã dọn 2 scheduled task tạm do agent tạo (PrepRelaunchHub, PrepRelaunchHub2).
- Không thay đổi settings/config/credential nào; không đụng tài khoản ChatGPT.

## 4. Các bước còn lại (đúng thứ tự)

### Phía máy local — cần làm trước (agent làm được khi được duyệt, hoặc user tự mở)

1. Khởi động lại stack r19 bằng đường chính thống của app (Recovery Host full-clean
   refresh như các đợt activation trước), xác nhận: có listener 18766/18082,
   connected-agent hết `CONTROL_PLANE_BRIDGE_FAILED`, heartbeat mới có
   `runtime_readiness=ready`.
2. Mở app → trang Kết nối/Hướng dẫn: nếu hiện cảnh báo "Tool contract đã thay đổi"
   (NEEDS_DISCOVERY/NEEDS_ACK), để sẵn — việc acknowledge chỉ bấm được **sau** khi
   ChatGPT đã discovery lại (bước 4 dưới đây), app sẽ tự chuyển trạng thái.

### Phía tài khoản ChatGPT — BẮT BUỘC USER (agent không đăng nhập/không bấm thay)

3. Trên chatgpt.com (tài khoản Plus cá nhân đã có app): **Settings → Apps/Plugins →
   app "Ubuntu Control Plane" → Refresh** để ChatGPT fetch lại tools/list mới.
   (Developer Mode đã bật từ trước; app đã cài ở dạng developer mode,
   "Authorization: None / no account linked" là đúng thiết kế private_tunnel_service.)
4. Mở **chat mới**, bấm **+ → Developer mode/Apps → chọn "Ubuntu Control Plane"**,
   gửi câu kiểm tra chỉ-đọc, ví dụ đúng câu guide trong app:
   "Hãy liệt kê các tệp ở tầng đầu tiên của thư mục làm việc hiện tại, và cho tôi
   biết đây là dự án gì. Không được sửa đổi bất kỳ tệp nào."
   hoặc gọi `workspace_context` với operation `inventory`.
5. Quay lại app Electron bấm acknowledge contract (nút "Kiểm tra lại trạng thái"/
   xác nhận trong cảnh báo contract ở trang Hướng dẫn) nếu app yêu cầu → trạng thái
   về `CURRENT_ACKNOWLEDGED`.

## 5. Dấu hiệu thành công (cả hai phía)

- ChatGPT web: app trả kết quả thật từ máy local (inventory đúng node
  DESKTOP-63643J4 / workspace E:\DEV\Codex-web) trong chat mới; model trả lời là
  model ChatGPT web — không tốn hạn mức Codex.
- Windows: `control-plane-route-evidence.json` có heartbeat mới `runtime_readiness=ready`;
  agent status hết lỗi bridge; app hiện connector `CURRENT_ACKNOWLEDGED`
  (hoặc ít nhất central_connected=true + authority ready — đủ cho dispatch central).
- Control Plane: task được tạo từ ChatGPT có receipt dispatch xuống đúng binding/node.

## 6. Giới hạn trung thực

- Chưa kiểm chứng được một lượt gọi ChatGPT-web → tool hoàn chỉnh **trong tối 23/10**
  vì runtime local đang dừng; lần cuối toàn chuỗi ready là 23:58:46 +07 (heartbeat),
  và bằng chứng gọi thật gần nhất trong repo là 27-09-2026 (inventory, task_list).
- Trạng thái contract ack hiện tại chưa đọc được từ file state (các trường
  `chatgptToolContract*` không nằm trong runtime-state.json/activation-epoch.json);
  phải xem trong health snapshot của app sau khi runtime chạy lại.

## 7. Kết quả sau Refresh — kiểm chứng 06:34–06:41 +07, 24/10/2026 (chưa commit)

User báo 06:33 24/10: đã bấm **Refresh** app "Ubuntu Control Plane" trong ChatGPT
và xác nhận GUI r19 OK. Runtime lúc kiểm chứng: epoch
`activation-mvl8uyob-1808c2f2772c25250e9bc766445b876b` (kích hoạt 00:29:24 +07),
connected-agent pid 33312 heartbeat `succeeded` liên tục (iteration >1016,
`last_error_code=null`), route evidence `runtime_readiness=ready`,
`policy_state=enabled`, `central_connected` qua heartbeat CP mỗi ~22 giây.

### 7.1 Trạng thái contract: trước và sau Refresh

- **Trước Refresh (mốc kích hoạt 00:29:24 +07):** census trong
  `activation-epoch.json` ghi `connectorContractState = CHANGED_NEEDS_DISCOVERY`
  (giá trị duy nhất trong toàn bộ file).
- **Sau Refresh (06:34–06:41 +07): vẫn `CHANGED_NEEDS_DISCOVERY`** — không chuyển
  sang `CHANGED_DISCOVERED_NEEDS_ACK`, vì:
  - `runtime-state.json` hiện tại **không có** bất kỳ trường
    `chatgptToolContractSha256 / AcknowledgedAt / RediscoveredAt` nào → chưa từng
    có acknowledge hay rediscovery được persist ở process/epoch này.
  - Discovery receipt phía local chỉ tồn tại **trong bộ nhớ** của MCP process
    (khởi động 00:28:58 +07) và chỉ tính khi client `chatweb` qua
    attested transport; không có contact nào như vậy kể từ khi process khởi động
    (bridge journal phía Windows đứng yên từ 20:14–20:15 23/10; CP không dispatch
    action nào kể từ 20:13 23/10).
  - Refresh của ChatGPT fetch tools/list tại **CP facade trên svhome**, và facade
    phục vụ tools/list theo kiểu stateless/cacheable (`_stateless_result` trong
    `mcp_facade.py`) → theo thiết kế **không tạo** discovery receipt phía local
    và không ghi DB. Đây là hành vi đúng kiến trúc central, không phải Refresh hỏng.
- **Hệ quả:** ở vai `central_executor`, trạng thái này **không chặn** dispatch
  (đã kiểm chứng lại trong code: cổng `connectorReady` trả null cho central;
  khối auto-acknowledge khi activation chỉ chạy khi `!centralExecutor`).
  Chuỗi `DISCOVERED_NEEDS_ACK → CURRENT_ACKNOWLEDGED` chỉ là cổng của đường
  direct_legacy, không áp dụng cho đường đang dùng.

### 7.2 Acknowledge: không thực hiện — vì không có gì để acknowledge

- Điều kiện acknowledge (`CHANGED_DISCOVERED_NEEDS_ACK`) **không** xuất hiện,
  nên không có thao tác acknowledge nào được bấm (cả GUI lẫn IPC).
- Ảnh chụp app lúc 06:38 +07 (`~/workspace/research/cos-webcodex/chatgpt-web/postrefresh-app.png`):
  trang Cài đặt hiện thẻ "Chưa xác minh được inventory workspace / cần tải lại"
  (nút "Tải lại Inventory") — đây là receipt kiểm tra inventory CP còn sót từ
  cửa sổ downtime 23:59, **không phải** cảnh báo contract/acknowledge. Không bấm
  nút này trong lượt kiểm chứng (user đang thao tác trực tiếp trên máy qua
  TeamViewer; nút là thao tác tải lại chỉ-đọc, user/parent bấm lúc nào cũng được).

### 7.3 Có lời gọi ChatGPT → tool sau Refresh chưa? — CHƯA

Bằng chứng CP (sqlite `/home/svhome/.local/state/codex-control-plane/control-plane.sqlite3`),
cửa sổ 06:30 → 06:41 +07 ngày 24/10:

- `events`: chỉ 21+ bản ghi `node_heartbeat` (readiness=ready), không event nào khác.
- `work_requests` / `actions` / `receipts` / `mcp_task_sessions` /
  `mcp_exec_intents` / `mcp_read_only_intents` sau mốc 06:30: **0**. Action gần
  nhất vẫn là 20:13 +07 23/10 (đợt test Desktop).
- Kết luận: user đã Refresh (phía ChatGPT, không để lại dấu vết theo thiết kế)
  nhưng **chưa gửi câu test nào trong ChatGPT** — chưa có bằng chứng đầu-cuối mới
  cho đường não-web ở epoch này.

### 7.4 Còn thiếu đúng một bước phía user

Mở **chat mới** trong ChatGPT → **+ → Developer mode/Apps → chọn "Ubuntu Control Plane"**
→ gửi câu kiểm tra chỉ-đọc (vd câu guide: liệt kê tệp tầng đầu của thư mục làm việc,
không sửa gì). Khi đó CP sẽ xuất hiện work_request/action mới và Windows có
bridge journal mới — đó là bằng chứng đầu-cuối còn thiếu. Không cần acknowledge,
không cần Refresh thêm.
