# 260814 — Trạng thái triển khai Execution Hub ChatWeb ⇄ Codex Desktop

**Ngày:** 2026-08-14  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Thiết kế nguồn:** `docs/research/260814_EXECUTION_HUB_CHATWEB_CODEX_DESKTOP_TONG_THE.md`  
**Trạng thái:** **SOURCE IMPLEMENTED / FOCUSED PROOFS PASS / LIVE ACTIVATION PENDING**  
**Public MCP contract:** giữ `smart-v3`, 8 top-level tools; không thêm tool công khai chỉ để phục vụ Hub.  
**Operations trong đợt triển khai này:** chưa commit, chưa push, chưa release, chưa restart Electron/runtime sau các thay đổi Hub.

---

## 1. Kết luận triển khai

Kiến trúc đã chuyển từ ý tưởng “hai MCP process cùng dùng một ledger” sang mô hình mục tiêu:

```text
ChatWeb ── tunnel / MCP ───────┐
                                │
                                ▼
                     ONE Coding Tools Runtime
                     ONE durable execution truth
                     ONE write authority
                                ▲
                                │
Codex Desktop ─ stdio proxy ───┘

Electron = supervisor + Execution Control Center + secret owner
```

Codex Desktop thin proxy không mở workspace, không mở SQLite ledger và không tạo `Runtime` thứ hai. Bearer thật của Coding Tools MCP chỉ nằm trong Electron `SecretStore`; Codex config chỉ nhận đường dẫn tới một descriptor local chứa gateway-scoped token ngắn hạn của process Electron.

Execution Hub hiện có các lớp chính:

- durable Hub client registry;
- per-client monotonic event cursors;
- semantic controller lease có TTL + monotonic fencing token;
- repository write lease vẫn độc lập với semantic controller;
- manual controller transfer có fencing;
- authenticated internal Hub control endpoint;
- snapshot v2 cho operator UI;
- bounded resume packet, không copy transcript;
- `SAFE TO ROTATE CHATWEB` fail-closed;
- Codex Desktop idle heartbeat;
- Electron-owned loopback gateway + Python stdio proxy;
- Execution Control Center hiển thị clients, controller, writer, cursors, continuity và resume;
- config onboarding an toàn cho Codex Desktop;
- fault/reconnect E2E regression tests.

---

## 2. Work packages đã accept

### WP-A — Durable multi-client Hub state

Accepted run: `afebf5d70dd443eaa4054ddbc5380084`

Kết quả:

- schema orchestration ledger lên version 5;
- thêm `hub_clients`, `hub_client_cursors`, `controller_leases`;
- client cursor chỉ tăng, không rewind;
- controller lease có fencing token tăng đơn điệu;
- competing owner không thể cướp lease đang sống;
- transfer chỉ tới client đang online;
- FK + explicit validation tránh orphan cursor/authority rows.

Focused proof cuối: `10 passed`.

### WP-B — Server/runtime Hub integration

Accepted run: `7d99d8f4341b46f09eac8e58c89c4c5d`

Kết quả:

- HTTP MCP request được gắn logical client identity;
- ChatWeb mặc định có thể claim controller khi run chưa có controller sống;
- Desktop heartbeat/call không được steal controller;
- `task_control events` ghi cursor theo event thực sự trả cho client, không tin arbitrary future `after_seq`;
- HTTP `accept/reject` bị controller lease fence;
- `/__control/hub` hỗ trợ heartbeat + operator transfer;
- `/__control/orchestration` nâng lên snapshot schema v2 nhưng giữ các key cũ;
- thêm `clients`, `authority`, `cursors`, `continuity`, `resume_packet`;
- context pressure hiển thị `unknown` khi host không expose, không tự bịa phần trăm;
- capsule freshness dựa trên durable execution/proof events, không dựa generic task timestamp.

Focused proof cuối: `13 passed`.

### WP-C — Single-runtime Codex Desktop thin proxy

Accepted run: `71d36f5168d24591868f7297a39c889d`

```text
Codex Desktop stdio
      ↓
coding_tools_mcp.hub_proxy_stdio
      ↓ gateway-scoped token
Electron HubProxyGateway (127.0.0.1)
      ↓ real MCP bearer from SecretStore
ONE Coding Tools Runtime
```

Security invariants:

- real MCP bearer không xuất hiện trong descriptor;
- descriptor token rotate theo Electron process;
- descriptor nằm ở app `userData`;
- gateway bind loopback;
- proxy không mở Runtime/ledger/workspace;
- MCP session/protocol được forward đúng;
- descriptor rotation reset stale upstream session;
- descriptor mất/hỏng trả typed JSON-RPC unavailable thay vì crash stdio.

Base proof: Node gateway PASS; Python proxy `3 passed`; Node syntax PASS.

### WP-D — Execution Control Center + Desktop liveness

Accepted run: `759c74c7229a4282b13bd429b5381cbf`

UI mới giữ task/run/events/proofs/delegations và bổ sung:

- ChatWeb online/offline + cursor/lag;
- Codex Desktop online/offline + cursor/lag;
- semantic controller owner/status/fencing token;
- write authority + fencing token;
- `SAFE TO ROTATE CHATWEB: YES/NO`;
- reason codes tiếng Việt;
- truthful context-pressure state;
- bounded resume summary;
- manual `Control → ChatWeb` / `Control → Codex` với explicit confirm.

Hardening:

- panel Pause/Resume/Stop không còn ghi trực tiếp task JSON; đi qua MCP `task_control` để không bypass EOCL;
- panel handoff có identity `electron-panel`, không bị nhận nhầm là ChatWeb;
- Desktop proxy gửi heartbeat ngay khi attach và mỗi 15 giây trong khi stdio còn sống;
- Hub freshness window là 45 giây;
- heartbeat đi `gateway token → Electron → real bearer → /__control/hub`, Python proxy không biết bearer thật;
- heartbeat không tạo JSON-RPC output và không steal controller;
- auto-handoff vẫn OFF.

Combined proof cuối: Node panel/gateway PASS; Python Hub/proxy/server/ledger `16 passed`.

### WP-E — Safe Codex Desktop onboarding

Accepted run: `ee25d78e1b234c1eb22a26a004778eb2`

Execution Control Center có nút **Copy Codex MCP config**. Electron dùng Python đã verify + bundled `resources/coding-tools-mcp` + stable gateway descriptor path để sinh TOML thin-proxy.

Config không chứa:

- MCP bearer;
- `--workspace`;
- `--permission-mode`;
- direct full-runtime `coding_tools_mcp --stdio` path.

App **không tự sửa** `~/.codex/config.toml`; operator phải paste/replace block sau khi review.

Focused Node config/panel/gateway proof PASS.

### WP-F — Fault/reconnect release gates

Accepted run: `fd693ed40c41493283b83ece23bb4eb6`

Fault suite chứng minh:

1. ChatWeb và Codex Desktop logical clients thấy cùng task/run trên cùng shared Runtime.
2. HTTP session manager chỉ báo `shared_runtimes = 1`.
3. Client cursors độc lập; ChatWeb catch-up không kéo cursor Desktop theo.
4. Desktop không steal live ChatWeb controller.
5. Manual controller transfer tăng fencing token.
6. Stale ChatWeb owner bị chặn semantic acceptance sau transfer.
7. Durable task/run/capsule sống qua Runtime/server recreation trên cùng workspace.
8. Old authenticated `Mcp-Session-Id` được dùng làm alias để reconnect sang Runtime mới và response trả session id mới.
9. Một defect thật được tìm thấy và sửa: alias tới Runtime mới trước đây vẫn `initialized=false` và trả `Server not initialized`; handler giờ compatibly initializes fresh alias-target Runtime trước dispatch, vẫn giữ bearer auth + protocol-version check.

Focused Hub backend/proxy/fault proof cuối: `18 passed`.

Lưu ý evidence: pytest recreation chạy hai Runtime/server object nối tiếp trong cùng một Python OS process, nên `process_instance_id` theo thiết kế giữ nguyên trong test và `server_instance_id` đổi. Việc OS-process restart làm đổi process/server instance id đã có live P1.5 restart canary trước đó; activation Hub sau Electron restart vẫn cần một live canary riêng.

---

## 3. Invariant hiện đã được code hóa

### Một execution truth

- Desktop không có ledger riêng.
- Desktop proxy không tạo `Runtime`.
- Cả ChatWeb và Desktop đi về Runtime do Electron sở hữu.

### Controller ≠ writer

```text
semantic controller lease
        ≠
repository write lease
```

Controller có thể đổi ChatWeb ⇄ Desktop qua explicit operator action. Repository mutation vẫn theo EOCL/write-fence của MCP.

### Conversation ≠ execution

Resume state được dựng từ durable run/wave, task projection, event sequence, proof refs, capsule ref/hash, controller và pending coordination messages. Không copy transcript giữa ChatWeb và Codex Desktop.

### Context limit được xử lý bằng continuity

Hub chỉ báo `SAFE TO ROTATE CHATWEB = YES` khi active execution có đủ điều kiện tối thiểu:

- ledger integrity OK;
- task runnable;
- Desktop online;
- capsule current;
- controller đã transfer sang Desktop.

Nếu ChatGPT host không expose context usage thì UI hiển thị `unknown`, không suy đoán giả.

---

## 4. Những thứ cố ý chưa bật

- **Auto-handoff:** OFF; chờ representative real-task A/B evidence.
- **Routing threshold mới:** không đổi; P2 vẫn cần accepted Mini/Luna/Sol cohorts đại diện.
- **Arbitrary live Codex Desktop thread takeover:** không claim; bridge không chiếm native Desktop turn.
- **Tự động sửa `~/.codex/config.toml`:** không làm; operator copy/paste sau review.
- **Transcript synchronization:** không làm; continuity dựa durable state/capsule/evidence.

---

## 5. Live activation còn phải làm

Source đã implement nhưng Electron đang chạy phải được **khởi động lại toàn bộ process Electron** để nạp gateway, preload/UI/config-copy và new Python runtime source. Chỉ restart MCP/Tunnel không đủ để reload Electron JavaScript nếu process Electron cũ vẫn sống.

Sau full Electron restart:

1. mở **Execution Control Center**;
2. xác nhận snapshot schema v2 load được;
3. xác nhận `smart-v3` vẫn 8 tools và contract hash phù hợp;
4. bấm **Copy Codex MCP config**;
5. review/paste block vào `~/.codex/config.toml`, thay direct `coding_tools_mcp --stdio` block cũ nếu còn;
6. restart/mở session mới Codex Desktop;
7. xác nhận Codex Desktop thành `online` trong Hub;
8. xác nhận ChatWeb và Desktop thấy cùng run/capsule;
9. ghi capsule current;
10. transfer controller thủ công sang Codex Desktop;
11. xác nhận `SAFE TO ROTATE CHATWEB: YES`;
12. thử đổi ChatWeb conversation/reconnect rồi quan sát cursor/resume state;
13. transfer controller lại ChatWeb trước final semantic acceptance nếu policy của task yêu cầu.

Public tool input schema không được thay đổi bởi Hub work packages, nên về nguyên tắc không cần Refresh ChatGPT MCP connector chỉ vì Hub; live activation canary vẫn phải xác nhận contract hash trước khi kết luận.

---

## 6. Release/acceptance matrix

| Gate | Source/focused proof |
|---|---|
| Durable clients | PASS |
| Independent cursors | PASS |
| Controller fencing | PASS |
| Online-only transfer | PASS |
| Same shared Runtime | PASS |
| Thin proxy no ledger | PASS |
| Real bearer isolated in Electron | PASS |
| Descriptor rotation/session reset | PASS |
| Desktop idle heartbeat | PASS |
| Panel task controls through EOCL | PASS |
| Snapshot v2 | PASS |
| Resume packet bounded | PASS |
| SAFE_TO_ROTATE fail-closed | PASS |
| Old MCP session alias reconnect | PASS after real defect fix |
| Durable run/capsule across Runtime recreation | PASS |
| Full live Electron activation | **PENDING** |
| Live real Codex Desktop connection through proxy | **PENDING** |
| Live ChatWeb ⇄ Desktop controller handoff | **PENDING** |
| Auto-handoff | OFF / evidence pending |
| P2 route calibration | evidence pending |

---

## 7. Final source audit command set

```text
node --test tests/codex-desktop-config.test.js tests/control-panel.test.js tests/hub-proxy-gateway.test.js tests/runtime-lifecycle.test.js
node --check electron/main.js
node --check electron/services/hubProxyGateway.js
node --check electron/services/codexDesktopConfig.js

cd resources/coding-tools-mcp
python -m pytest tests/test_coordination_state.py tests/test_execution_hub.py tests/test_hub_proxy_stdio.py tests/test_execution_hub_faults.py -q

cd ../..
git diff --check
```

Có thể bổ sung transport regression subset của `test_system_capability_suite.py` nếu final audit thấy HTTP session handler bị ảnh hưởng ngoài Hub.

---

## 8. Kết luận

Execution Hub hiện không còn là một kiến trúc trên giấy. Backend, single-runtime proxy, controller/cursor semantics, operator dashboard, onboarding và fault/reconnect behavior đã được implement và focused-proven trên source hiện tại.

Mốc còn thiếu để gọi **FULL LIVE PASS** không phải thêm kiến trúc mới mà là **activation vận hành**: restart full Electron process, chuyển Codex Desktop sang thin-proxy config, sau đó chạy live two-client canary. Auto-handoff và P2 routing calibration vẫn cố ý đứng sau evidence gates, không được bật chỉ để “hoàn thành checklist”.
