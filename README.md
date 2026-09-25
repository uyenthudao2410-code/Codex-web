# Tools-Codex-web — Coding Tools MCP Execution Hub

> Desktop app Windows quản lý máy chạy Coding Tools MCP: workspace, quyền đọc/sửa/chạy lệnh, tiến trình và evidence. ChatGPT kết nối qua MCP/Tunnel được hỗ trợ trong trình duyệt hoặc ứng dụng chính thức; Execution Hub không nhúng hay quan sát trang, DOM, nội dung hoặc session đăng nhập ChatGPT.

> **Nguồn trạng thái hiện tại:** [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md). File có ngày dưới `docs/research/` là evidence/plan lịch sử, không dùng để ghi đè source, test hoặc trạng thái vận hành mới hơn.

| | |
|---|---|
| **Phiên bản desktop** | `coding-tools-mcp 1.0.7` |
| **Repository** | `uyenthudao2410-code/Tools-Codex-web` |
| **Nền tảng** | Windows + Electron |
| **MCP runtime** | `Coding Tools MCP` (Python, `resources/coding-tools-mcp`) |
| **Tool profile** | `smart-v3` — 8 tool public |

---

## Mục lục

1. [App dùng để làm gì?](#1-app-dùng-để-làm-gì)
2. [Bản đồ tính năng](#2-bản-đồ-tính-năng)
3. [Kiến trúc](#3-kiến-trúc)
4. [Smart Mode — 8 công cụ](#4-smart-mode--8-công-cụ)
5. [`agent_workflow`](#5-agent_workflow--trung-tâm-coding)
6. [Adaptive Model Routing](#6-adaptive-model-routing)
7. [Codex App Server Bridge & Review plane](#7-codex-app-server-bridge--review-plane)
8. [Task state, EOCL, command session](#8-task-state-eocl-command-session)
9. [Document Workflow](#9-document-workflow)
10. [Mở ChatGPT và chuyển tệp có kiểm soát](#10-mở-chatgpt-và-chuyển-tệp-có-kiểm-soát)
11. [Ledger evidence & archival](#11-ledger-evidence--archival)
12. [Permission & Tool Mode](#12-permission--tool-mode)
13. [Cài đặt, chạy, test, build](#13-cài-đặt-chạy-test-build)
14. [Cấu trúc thư mục](#14-cấu-trúc-thư-mục)
15. [Ví dụ dùng với ChatGPT](#15-ví-dụ-dùng-với-chatgpt)
16. [Git workflow & delivery guard](#16-git-workflow--delivery-guard)
17. [Bảo mật](#17-bảo-mật)
18. [Tài liệu kỹ thuật](#18-tài-liệu-kỹ-thuật)
19. [Nguyên tắc phát triển](#19-nguyên-tắc-phát-triển)
20. [Nguồn gốc & License](#20-nguồn-gốc--license)

---

## 1. App dùng để làm gì?

Khi kết nối qua MCP, ChatGPT có thể:

- xem cấu trúc project và trạng thái Git;
- đọc, tìm kiếm, sửa code trong workspace được cho phép;
- chạy command, test, build và verification;
- theo dõi command chạy lâu (poll / đọc thêm output / gửi stdin / kill);
- lưu trạng thái task để tiếp tục qua nhiều lượt chat (kể cả sang cửa sổ chat mới qua handoff capsule);
- tạo/đọc tài liệu Word, PDF, Markdown, text theo workflow chuyên dụng;
- xem ảnh trong workspace;
- quản lý file qua hộp thoại workspace local; không tự kéo attachment từ trang ChatGPT;
- điều phối model phù hợp độ khó tác vụ (Mini/Luna/Terra/Sol, fail-closed về deterministic);
- dùng Codex App Server như reviewer/worker độc lập ở chế độ chỉ đọc;
- giữ mọi thao tác trong ranh giới workspace và policy đã cấu hình.

Đây là bản tùy biến phát triển từ WebCodex; trọng tâm desktop hiện tại là **Execution Hub + Coding Tools MCP + các MCP client được hỗ trợ + evidence-gated model routing**.

---

## 2. Bản đồ tính năng

### Giao diện desktop (Electron + renderer)

| Màn hình | File | Chức năng |
|---|---|---|
| Trang chính / onboarding | `renderer/index.html` + `app.js` | Chọn workspace, cấu hình OpenAI Tunnel (Tunnel ID + Runtime Key), triển khai dịch vụ, checklist hướng dẫn 5 bước, thẻ trạng thái (workspace/MCP/tunnel), quản lý thư mục ủy quyền bổ sung |
| Executor Hub | `renderer/browser.html` + `browser.js` | Trạng thái runtime, route, task và workspace; mở trang thiết lập connector trong trình duyệt hệ thống theo thao tác người dùng |
| Execution Control Center | `renderer/panel.html`, `token-dashboard.html`, `control-center.js` | Realtime: objective/tiến độ/command đang chạy, run/wave/mode/base HEAD, event audit, proofs, delegations, MCP+Tunnel health, ChatWeb/Codex online + cursor/lag, controller lease/fencing/write authority, `SAFE TO ROTATE CHATWEB`, resume summary; điều khiển pause/resume/stop, **Ghi capsule handoff (≤8 KB)**, manual controller transfer có xác nhận, **Copy Codex MCP config** |
| Styles/theme | `styles.css`, `dashboard.css`, `panel.css`, `control-center.css`, day/night background | Giao diện sáng/tối, font Plus Jakarta Sans |

Dữ liệu Control Center lấy từ endpoint `GET /__control/orchestration` của Coding Tools MCP (yêu cầu Bearer token).

### Backend Electron (`electron/`)

| Service | Chức năng |
|---|---|
| `main.js`, `browserPreload.js` | Vòng đời Execution Hub, Control Center và IPC allowlist; không tạo phiên WebView ChatGPT |
| `services/recoveryHost.js`, `fullCleanActivation.js`, `recoveryHostLauncher.js` | Recovery Host supervisor, full-clean activation/restart, activation epoch + connector ACK |
| `services/tunnelService.js`, `proxyService.js`, `hubProxyGateway.js` | OpenAI Tunnel lifecycle, loopback gateway cho Codex Desktop stdio proxy |
| `services/secretStore.js`, `settingsStore.js`, `config.js`, `deviceIdentity.js` | Secrets (Electron SecretStore, real MCP bearer không rời app), settings, device identity |
| `services/codexDesktopConfig.js` | Sinh TOML thin-proxy cho Codex Desktop (chỉ loopback port + gateway token, không chứa bearer) |
| `services/runtimeOrchestrator.js`, `nativeService.js`, `commandRunner.js` | Điều phối MCP runtime (Python bundled), native runtime, chạy command |
| `services/healthService.js`, `mcpSemanticHealth.js`, `connectorAttestation.js` | Health check, attestation managed-tunnel, stale-schema detection |
| `services/tokenMeasurement.js`, `uiPerformanceMetrics.js` | Token theo nguồn usage có provenance; số đo thiếu hiển thị unknown |

### Coding Tools MCP (`resources/coding-tools-mcp/`)

8 tool `smart-v3` (xem §4), `agent_workflow` đa workflow (bugfix/feature/greenfield/refactor/test_failure/build_release/diagnose/document/resume/custom), EOCL + task state bền vững, Codex bridge read-only, model routing, permission `safe|trusted|dangerous`, ledger audit SQLite + archival tự động (xem §11).

---

## 3. Kiến trúc

```text
┌──────────────────────────┐
│        ChatGPT           │
│   MCP client / agent     │
└────────────┬─────────────┘
             │ HTTPS / MCP
             ▼
┌──────────────────────────┐
│  Tunnel / MCP endpoint   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│            Desktop Electron App              │
│  workspace · MCP runtime · tunnel · task UI  │
│  downloads · Control Center · recovery host  │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│              Coding Tools MCP                │
│  workspace · files · Git · commands          │
│  tests · builds · documents · task state     │
│  adaptive agent_workflow                     │
└────────────┬───────────────────────┬─────────┘
             │                       │
             │                       ▼
             │          ┌────────────────────────┐
             │          │ Codex App Server       │
             │          │ independent sidecar    │
             │          │ read-only / no-network │
             │          └────────────────────────┘
             ▼
┌──────────────────────────┐
│ Repository / Workspace   │
│ trên máy của bạn         │
└──────────────────────────┘
```

### Một Runtime, hai client

Không cho ChatWeb và Codex Desktop tự spawn hai Runtime ngang hàng cùng ghi một ledger. Electron giữ **một Runtime authority**: ChatWeb qua tunnel, Codex Desktop qua stdio proxy mỏng tới loopback gateway của Electron. Không đồng bộ transcript giữa hai client; continuity rebuild từ ledger/task/proof/capsule + bounded resume packet. Desktop đổi workspace không cần restart toàn bộ MCP + tunnel khi runtime cho phép.

### Kết nối Codex Desktop vào cùng Execution Hub

Không chạy trực tiếp `python -m coding_tools_mcp --stdio` trên cùng workspace (tạo Runtime authority thứ hai). Luồng đúng: chạy Electron app → mở Execution Control Center → **Copy Codex MCP config** → review rồi paste block `[mcp_servers.coding-tools]` vào config Codex Desktop → mở session mới → card Codex Desktop hiện `online`. App không tự sửa `~/.codex/config.toml`. Proxy heartbeat khi stdio còn attach, không tự claim controller khi ChatWeb giữ lease; chuyển controller là thao tác manual, auto-handoff OFF.

---

## 4. Smart Mode — 8 công cụ

Chế độ `smart` giữ tool surface nhỏ để model chọn tool ổn định, ít round-trip.

| Tool | Mục đích |
|---|---|
| `workspace_context` | Tổng quan workspace/project/Git/task; `detail=full` kèm diagnostics runtime |
| `agent_workflow` | Coding end-to-end: phân tích → sửa → test/build → verify → resume |
| `task_control` | Task lifecycle, background operation, EOCL audit/accept/reject, lane/events/messages/ack, handoff, `restart_runtime` |
| `exec_command` | Chạy một command khi high-level workflow không phù hợp |
| `command_control` | Poll / đọc thêm output / gửi stdin / kill command session |
| `document_workflow` | PDF/DOCX/Markdown/text: inspect, tạo mới, chuyển đổi + metadata verification |
| `request_permissions` | Báo trạng thái yêu cầu quyền (status-only, fail-closed — xem §12) |
| `view_image` | Trả ảnh trong workspace cho model xem |

Tool cũ giữ lớp **compatibility** cho client cache cũ; agent mới không chủ động gọi tên legacy.

### Contract fingerprint & stale-schema detection

Runtime công bố SHA-256 của đúng contract đang expose (`profile = smart-v3`, `tool_count = 8`). Electron so với fingerprint connector đã discover; khi lệch, app yêu cầu refresh/recreate MCP app phía ChatGPT. Nút **“Kiểm tra lại trạng thái”** chỉ poll bằng chứng. Recovery Host guarded-ACK khi nhận `tools/list`/`server/discover` attested đúng epoch/process/server/contract SHA (nhánh strict), hoặc `workspace_context` bootstrap attested khi admission đóng (nhánh tương thích, giữ `connector_rediscovered=false`). Generic `tools/call` hay xác nhận thủ công không thay thế receipt hợp lệ. Đây là fail-closed: repo không có API ép ChatGPT rescan.

---

## 5. `agent_workflow` — trung tâm coding

Workflow: `bugfix`, `feature`, `greenfield`, `refactor`, `test_failure`, `build_release`, `diagnose`, `document`, `resume`, `custom`. Phase: `prepare` (context + evidence) → `execute` (change + verify) → `run` (gộp) → `resume` (khôi phục task cũ). Một lần gọi có thể gom: context, patch, command chuẩn bị/test/build, artifact verification, Git diff, task state, model routing, external review khi đáng giá.

Candidate lane (Mini/Luna) chỉ nhận bounded evidence packet (tối đa 4 query-centered deep snippets, đúng allowed scope), không mutation checkout chính; proof cuối do MCP chạy, ChatWeb/Sol quyết định acceptance.

---

## 6. Adaptive Model Routing

Production policy **fail-closed**: `execution_route=auto` resolve về `deterministic` cho tới khi đủ representative accepted paired evidence.

| Route | Model | Effort | Deadline | Dùng khi |
|---|---|---:|---:|---|
| `deterministic` | — | — | — | Ưu tiên tool/test/compiler, không cần model phụ |
| `mini` | `gpt-5.4-mini` | `low` | 10s | Leaf nhỏ, rõ, oracle mạnh |
| `luna` | `gpt-5.6-luna` | `high` | 15s | Hẹp nhưng cần reasoning tốt hơn |
| `terra` | `gpt-5.6-terra` | `high` | 25s | Cross-file / implementation reasoning |
| `sol_xhigh` | `gpt-5.6-sol` | `xhigh` | 30s | Tích hợp rộng, semantic phức tạp |
| `sol_max` / `sol_ultra` | `gpt-5.6-sol` | `max`/`ultra` | 30s | Hệ quả cao; **chặn mặc định, cần `allow_high_cost=true`** |

Strong oracle (`tests`/`build`/`all` hoặc command cụ thể) là tín hiệu quan trọng nhưng **không vượt ROI evidence gate**. Calibration threshold phải dựa trên real accepted task cùng class (first-pass/repair, cost, TTA, defect) — không mở rộng từ vài sample hay simulation.

---

## 7. Codex App Server Bridge & Review plane

`codex_bridge` không public ở smart mode; workflow dùng nội bộ. Sidecar an toàn: auth Codex Desktop/CLI của máy, không chiếm turn Codex đang chạy, đúng workspace hiện tại, `approvalPolicy=never`, sandbox read-only, tắt network, không sửa file, không MCP lồng nhau — chỉ trả candidate/review để MCP kiểm tra. Profile: `candidate_mini`, `candidate_luna`, `cross_file`, `deep_code`, `consequential`, `parallel_extreme`, `packet`, `scoped`, `critical`, `history`. Bridge theo dõi token usage, cache ratio, estimated credits, thời gian chạy, capacity cooldown.

Review plane: deterministic proof trước; đủ bằng chứng thì bỏ qua review ngoài; cần độc lập thì `packet`/`scoped`/`critical` theo rủi ro. Mục tiêu là độ tin cậy, không phải gọi nhiều model.

---

## 8. Task state, EOCL, command session

Task bền vững theo workspace: objective, bước hiện tại/tiếp theo, command đang chạy, kết quả test/build, file đã sửa, lỗi, lịch sử. `task_control`: lifecycle (`get/start/update/pause/stop/resume/clear/history`), `operation` (background), EOCL (`audit/accept/reject`), coordination (`lane/events/messages/ack`), `handoff` (capsule ≤8 KB chuyển chat mới không replay transcript), `restart_runtime`.

EOCL: `PREFLIGHT → READY → ROUTED → EXECUTING → PROVING → ACCEPTING → CHECKPOINTED`; `REPLAN/BLOCKED/ABORTED` fail-closed. Wave ở `ACCEPTING` phải được ChatWeb/Sol accept/reject — test xanh không phải final acceptance. Workflow lâu hand-off thành background operation (`operation_id`, poll bằng `task_control`).

**Restart production-safe** (`task_control` + `confirm_restart=true`, hoặc nút **“Khởi động lại toàn bộ dịch vụ”**): kiểm tra idle → ghi one-shot ticket bound workspace/process/server + fence → Recovery Host supervisor consume ticket (journal `.processing` để resume sau crash) → resolve exact accepted checkpoint → `FullCleanActivation` thay toàn bộ process cùng `activation_epoch_id` → final census + connector ACK → READY. Không `taskkill` từ MCP; ticket hết hạn nhanh, không replay; watchdog chỉ `soft_recovery` cục bộ.

**Command session:** `exec_command` → `command_id/output_ref` → `command_control` (`poll/read/write-stdin/kill`). Build/test dài không bị hủy khi chat kết thúc.

---

## 9. Document Workflow

`document_workflow`: inspect PDF/DOCX/Markdown/text, tạo DOCX/Markdown/text, convert sang DOCX, kèm metadata verification (size, số dòng, SHA-256, preview). Nguyên tắc: inspect nguồn một lần → model xử lý → create output hoàn chỉnh một lần. Không dùng shell/patch nhỏ lẻ khi workflow đã xử lý được.

---

## 10. Mở ChatGPT và chuyển tệp có kiểm soát

Execution Hub mở trang thiết lập connector ChatGPT trong trình duyệt mặc định khi bạn nhấn nút. Hội thoại, đăng nhập, cookie và tải tệp diễn ra trong trình duyệt hoặc ứng dụng chính thức; Coding Tools MCP chỉ nhận lời gọi MCP và dữ liệu cần cho đúng thao tác được yêu cầu.

Tệp muốn đưa vào repository được chọn qua hộp thoại hoặc thao tác của hệ điều hành vào workspace đã cấp quyền. App không tự tải, đồng bộ toàn hội thoại, hay tự lưu attachment từ phiên ChatGPT vào thư mục dự án. Hãy rà soát file và quyền trước khi yêu cầu MCP đọc hoặc sửa.

Khi tool trả nội dung file, đó là kết quả của một lời gọi MCP có phạm vi, không phải app đọc ngược trang ChatGPT. Nội dung nhạy cảm tiếp tục bị chặn bởi chính sách local.

## 11. Ledger evidence & archival

Mọi vận hành (run/wave/event/proof/delegation/task) được ghi vào audit ledger SQLite:

```text
.coding-tools/orchestration/ledger.sqlite3          # canonical — bắt buộc có trong Git
.coding-tools/orchestration/archives/               # shard archive + manifest.json
.coding-tools/delivery-snapshot.json                # receipt snapshot giao hàng
```

### Retention policy (tóm tắt cho operator)

- Mọi file dưới `.coding-tools/` đều là evidence phải version-control, **ngoại trừ đúng 2 sidecar tạm**: `ledger.sqlite3-shm`, `ledger.sqlite3-wal`.
- Trước **mỗi commit/push**: `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery`. Script stage snapshot canonical bằng Backup API (WAL-safe) + ghi receipt bound đúng blob/hash/size.
- **GitHub chặn cứng file >100MB.** Ledger tăng vô hạn nên repo có cơ chế archive tự động bên dưới — không xóa history, không dùng Git LFS (pointer LFS làm vỡ guard SQLite integrity).

### Archive tự động (`scripts/archive-ledger.py`)

Archive theo **run hoàn chỉnh** (chain hash là per-run nên không bao giờ gãy verify), chỉ lấy runs đã `finished` và quá cutoff, luôn giữ runs bị FK RESTRICT trỏ tới (ví dụ runs p5):

```powershell
# Dry-run read-only: mô phỏng trên bản copy, in số shard/size dự kiến
npm run archive:ledger -- --older-than 2026-09-01T00:00:00.000Z

# Thực thi (yêu cầu dừng runtime + xác nhận đúng digest đã kiểm tra)
python scripts/archive-ledger.py --older-than 2026-09-01T00:00:00.000Z --apply --runtime-stopped --expected-sha256 <digest>
```

Ngưỡng: canonical mục tiêu ≤90MB, mỗi shard ≤95MB (tự chia nhiều shard khi ước lượng >80MB/shard), fail-closed khi reconcile `archive + canonical == source` lệch, integrity/FK/active-lease vi phạm, hoặc live DB đổi giữa chừng. Shard ở DELETE journal-mode (không sidecar), manifest ghi SHA-256 + time-range + danh sách run. Backup pre-archive giữ **ngoài repo** (thư mục temp).

### Tra cứu liên shard (`scripts/query-ledger-history.py`)

Máy khác chỉ cần clone/pull là có đủ history:

```powershell
npm run ledger:history                                        # liệt kê shard + time-range
python scripts/query-ledger-history.py counts                 # đếm theo bảng
python scripts/query-ledger-history.py locate <run_id>        # run nằm ở shard nào
python scripts/query-ledger-history.py sql --table events --where "run_id='<id>'" --limit 20
```

Bảng query được: `runs, waves, events, proofs, checkpoints, delegations, idempotency_records, managed_process_jobs, background_operations, controller_leases, handoff_capsules, coordination_messages` (read-only, mỗi row gắn `_source_file`).

---

## 12. Permission & Tool Mode

### Permission mode (Coding Tools MCP runtime)

| Mode | Network | Shell expansion/inline script | Secret env filter | Dùng khi |
|---|---|---|---|---|
| `safe` | Tắt | Chặn | Bật | Mặc định an toàn |
| `trusted` | Cho phép | Cho phép | Bật | Máy/workspace tin cậy |
| `dangerous` | Cho phép | Cho phép | Tắt (+tắt Landlock) | Chỉ khi hiểu rõ rủi ro |

Kèm theo: workspace boundary, authorized roots, symlink-escape protection, command policy, destructive-command detection, runtime HOME/TMP/CACHE riêng, giới hạn output/session, pre-check path. Landlock chỉ có hiệu lực trên Linux có hỗ trợ; Windows áp dụng policy/path guard tương ứng.

`request_permissions` là **status-reporting tool**, không phải bypass. Host không hỗ trợ elicitation → trả `status=unsupported`, `ELICITATION_UNSUPPORTED`, `fail_closed=true` — **permission vẫn không được cấp**, client không retry vô hạn, server không biến thành implicit grant.

### Tool mode

| Mode | Dùng khi |
|---|---|
| `smart` | Mặc định cho ChatGPT (8 tool `smart-v3`) |
| `readonly` | Chỉ inspection/Git/read |
| `coding` | Đọc + sửa + command + build verify |
| `build` | Inspection/command/build, không patch write |
| `full` | Toàn registry — debug/compatibility/advanced |

### Authority WebCodex core (phân biệt rõ)

Đừng trộn với permission MCP ở trên. WebCodex core/server có authority riêng: `WEBCODEX_AUTHORITY_MODE=trusted_agent|restricted` (`trusted_agent` tự thực thi sau hard-safety checks; `restricted` cần authorization flow). `WEBCODEX_PERMISSION_MODE` legacy đã bỏ, không dùng làm alias. Chạy desktop MCP hiện tại thì chỉ cần quan tâm bảng permission ở trên.

---

## 13. Cài đặt, chạy, test, build

### Yêu cầu

Windows, Node.js + npm, Git; Codex Desktop/CLI nếu dùng Codex bridge; toolchain của project bạn làm việc cùng ChatGPT.

### Cài & chạy

```powershell
Set-Location <path-to-Tools-Codex-web>
npm install
npm start            # = npm run dev: start/focus lifecycle (start UI MISSING, activate STALE, focus CURRENT)
```

Các lệnh vòng đời UI: `npm run dev:status`, `npm run dev:control-center`, `npm run dev:stop` (chỉ đóng UI, giữ service nền), `npm run dev:replace`, `npm run dev:refresh` (`full_clean_refresh`: thay toàn bộ process cùng epoch, **không xóa** ledger/task/settings/secrets/identity; fail-closed `UPDATE_INCOMPLETE` khi postflight không chứng minh được).

### npm scripts hay dùng

| Lệnh | Mục đích |
|---|---|
| `npm start` / `dev` | Chạy desktop app |
| `npm test` | Test desktop (`tests/*.test.js` + check source-root + secret scan) |
| `npm run test:mcp` | pytest Coding Tools MCP |
| `npm run test:all` | Cả hai suite |
| `npm run stage:coding-tools-delivery` | Stage evidence + snapshot ledger + receipt (trước mọi commit/push) |
| `npm run check:coding-tools-delivery` | Guard giao hàng (secret + stage + history `--require-staged`) |
| `npm run check:coding-tools-history` | Guard policy evidence `.coding-tools` |
| `npm run archive:ledger` | Dry-run archive ledger (xem §11) |
| `npm run ledger:history` | Liệt kê shard ledger |
| `npm run dist` | Build installer Windows (`dist\`, `coding-tools-mcp-setup-<version>.exe`) |
| `npm run dist:dir` | Build dạng thư mục chưa đóng gói |
| `npm run report:ui-performance` | Báo cáo hiệu năng UI |
| `npm run check:repository-secrets` | Quét secret bị track |

### Chuyển máy / restart Windows

PID lưu trong runtime state có thể bị OS cấp lại cho app khác. Census đối chiếu PID **kèm OS process-start token**; token khác = tiến trình cũ đã mất. Không xóa `.coding-tools`/ledger, không kill app khác để vượt lỗi. Completion của CLI và admission của connector là hai mốc riêng: refresh có thể exit 0 (`DEV_UI REFRESHED`) trong khi epoch vẫn `VERIFYING/admission=closed` chờ connector ACK — đây không phải lỗi.

---

## 14. Cấu trúc thư mục

```text
Tools-Codex-web/
├─ electron/                     # main process, orchestrator
│  ├─ main.js, browserPreload.js, panelPreload.js
│  └─ services/                  # recovery-host, tunnel, secrets,
│                                # health, token-measure, codex-config, ...
├─ renderer/                     # UI: index, executor hub, panel,
│                                # token-dashboard, control-center
├─ resources/
│  ├─ coding-tools-mcp/          # Python MCP runtime (server.py + mixins) + tests
│  ├─ native-python/             # Python bundled cho desktop
│  └─ tools/                     # helper / tunnel binaries
├─ scripts/                      # archive-ledger.py, query-ledger-history.py,
│                                # stage/check-coding-tools-*, dev lifecycle, dist
├─ tests/                        # test desktop
├─ tasks/                        # todo/lessons vận hành
├─ docs/
│  ├─ CURRENT_STATE.md           # snapshot vận hành (nguồn sự thật số 1 sau code)
│  ├─ ARCHITECTURE.md  RECOVERY_HOST.md  ...
│  ├─ agent/                     # architecture-decisions, permission-model, ...
│  └─ research/                  # evidence/benchmark theo ngày (bất biến)
├─ .coding-tools/                # evidence vận hành (ledger, archives, reports, ...)
├─ AGENTS.md                     # luật cho coding agent trong repo
├─ SECURITY.md  LICENSE  THIRD_PARTY_NOTICES.md
├─ package.json
└─ README.md
```

Repo còn chứa thành phần WebCodex upstream (Rust crates, server, deploy docs). Desktop app đóng gói `electron` + `renderer` + `resources` để chạy trực tiếp trên Windows.

---

## 15. Ví dụ dùng với ChatGPT

```text
Kiểm tra workspace hiện tại, Git status và cho tôi biết file nào đang thay đổi.
→ agent bắt đầu bằng workspace_context

Tìm nguyên nhân test đăng nhập đang fail, sửa đúng nguyên nhân và chạy lại test liên quan.
→ agent_workflow, workflow bugfix hoặc test_failure

Thêm tính năng X, chỉ sửa file cần thiết, chạy test và build trước khi kết luận.
→ agent_workflow gom context + change + verification

Build project và báo tiến độ cho đến khi hoàn tất.
→ exec_command + command_control (hoặc background operation)

Đọc file PDF yêu cầu, tóm tắt và tạo report.docx trong workspace.
→ document_workflow (đừng tự ghép shell/Python)
```

---

## 16. Git workflow & delivery guard

Agent có thể hỗ trợ commit, nhưng trước push luôn đảm bảo: đúng workspace, không stage file tạm, test/build liên quan pass, `git diff` đúng phạm vi, không force-push khi chưa rõ remote, chỉ push khi task yêu cầu. Nhánh chính: `main`.

Riêng repo này, trước **mọi commit/push** phải chạy (policy trong `AGENTS.md`):

```powershell
npm run stage:coding-tools-delivery
npm run check:coding-tools-delivery
```

Guard sẽ fail khi: thiếu receipt mới, evidence chưa stage hết, sidecar lạ bị track, nested Git dưới `.coding-tools`, hoặc blob staged không phải SQLite hợp lệ.

---

## 17. Bảo mật

MCP client đã kết nối = coding agent có quyền thực thi thật trong scope cấu hình:

- chỉ chọn workspace thật sự cần; dùng thư mục ủy quyền bổ sung thay vì mở rộng workspace chính;
- không đưa token/API key/credential vào Git (`npm run check:repository-secrets`);
- không dùng `dangerous` cho repo/command không tin cậy;
- giữ source trong Git để rollback; review diff trước commit/push;
- không mở tunnel public lâu hơn cần thiết; không chia sẻ endpoint/token;
- giữ Codex bridge read-only; release/deploy/xóa dữ liệu cần scope + target rõ ràng;
- file đính kèm tải về nằm trong workspace — đưa vào `.gitignore` nếu không muốn commit.

Xem thêm [`SECURITY.md`](SECURITY.md).

---

## 18. Tài liệu kỹ thuật

- [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) — snapshot vận hành, thứ tự ưu tiên tài liệu
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — kiến trúc desktop + WebCodex core subsystem
- [`docs/RECOVERY_HOST.md`](docs/RECOVERY_HOST.md) — Recovery Host, Supervisor, Recovery MCP/Tunnel
- [`docs/agent/architecture-decisions.md`](docs/agent/architecture-decisions.md) — quyết định kiến trúc
- [`docs/agent/permission-model.md`](docs/agent/permission-model.md) — authority/safety WebCodex core
- [`docs/research/`](docs/research/) — benchmark/model-routing theo ngày (bất biến; không dùng để ghi đè hiện tại)
- [`AGENTS.md`](AGENTS.md) — luật cho coding agent (ưu tiên: implementation/tests hiện tại → CURRENT_STATE → docs sản phẩm → agent docs → research)

---

## 19. Nguyên tắc phát triển

1. High-level workflow trước low-level tool.
2. Test/compiler/deterministic evidence trước model debate.
3. Model rẻ chỉ khi đủ chắc chắn; Sol giữ phần semantic/integration quan trọng.
4. Không tạo nhiều worker cho việc thực chất tuần tự; không lặp inspection/test đã có bằng chứng.
5. Không ghi đè workspace ngoài scope; Codex sidecar không tự mutation repo.
6. Không force-push để chữa lệch history; kết luận dựa trên verification đã thực chạy.

---

## 20. Nguồn gốc & License

Kế thừa nhiều thành phần/ý tưởng từ **WebCodex** upstream (`https://github.com/yyjeqhc/webcodex`), tùy biến cho workflow desktop cá nhân, Coding Tools MCP và model orchestration. Cảm ơn các dự án MCP, WebCodex, Codex và cộng đồng open-source.

- Repo hiện tại: `https://github.com/uyenthudao2410-code/Tools-Codex-web`
- License: [`LICENSE`](LICENSE), third-party: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

---

### Tóm tắt (4 điểm)

> **1. `smart-v3` public đúng 8 tool, có contract fingerprint phát hiện connector stale.**
> **2. `agent_workflow` là đường coding chính; `auto` fail-closed về deterministic.**
> **3. `task_control` quản lý EOCL/handoff + `restart_runtime` an toàn qua supervisor; file tải từ ChatGPT tự lưu vào workspace kèm SHA-256.**
> **4. Ledger là evidence bắt buộc trong Git, archive theo shard + manifest để không bao giờ vượt giới hạn 100MB của GitHub.**
