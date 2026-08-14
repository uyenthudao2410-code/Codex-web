# Tools-Codex-web — Trợ lý Web MCP cho Coding

> Bộ công cụ desktop Windows giúp kết nối ChatGPT với máy lập trình của bạn qua MCP, quản lý workspace, chạy lệnh/test/build, thao tác Git, xử lý tài liệu và điều phối Codex theo mức độ khó của công việc.

**Phiên bản desktop hiện tại:** `web-mcp-assistant 0.3.4`  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Nền tảng chính:** Windows + Electron  
**MCP runtime chính:** `Coding Tools MCP`

---

## 1. Công cụ này dùng để làm gì?

`Tools-Codex-web` biến ChatGPT thành một trợ lý coding có thể làm việc trực tiếp với repository trên máy của bạn thay vì chỉ trả lời bằng văn bản.

Khi được kết nối qua MCP, ChatGPT có thể:

- xem cấu trúc project và trạng thái Git;
- đọc, tìm kiếm và sửa code trong workspace được cho phép;
- chạy command, test, build và các bước verification;
- theo dõi tiến trình command chạy lâu;
- lưu trạng thái task để tiếp tục qua nhiều lượt chat;
- tạo/đọc tài liệu Word, PDF, Markdown và text theo workflow chuyên dụng;
- xem ảnh nằm trong workspace;
- điều phối model phù hợp với độ khó của tác vụ;
- dùng Codex App Server như một reviewer/worker độc lập ở chế độ chỉ đọc;
- giữ các thao tác nguy hiểm trong ranh giới workspace và policy đã cấu hình.

Đây là bản tùy biến phát triển từ WebCodex, nhưng trọng tâm hiện tại của desktop app là **Execution Hub + Coding Tools MCP + ChatGPT/Codex Desktop + adaptive model routing**.

---

## 2. Kiến trúc hiện tại

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
│                                              │
│  - quản lý workspace                        │
│  - quản lý MCP runtime                      │
│  - quản lý tunnel                           │
│  - hiển thị trạng thái task / command       │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│              Coding Tools MCP                │
│                                              │
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

Desktop có thể đổi workspace mà không cần khởi động lại toàn bộ MCP + tunnel khi runtime cho phép.

### Execution Hub — một Runtime, hai client

Kiến trúc multi-client hiện tại không cho ChatWeb và Codex Desktop tự spawn hai Coding Tools Runtime ngang hàng cùng ghi một ledger. Electron giữ **một Runtime authority**; ChatWeb đi qua tunnel, còn Codex Desktop dùng một stdio proxy mỏng đi qua loopback gateway của Electron:

```text
ChatWeb ── Tunnel/MCP ───────┐
                             ▼
                      ONE Coding Tools Runtime ──> Repository
                             ▲
Codex Desktop ─ stdio proxy ─┘

Electron = supervisor + secret owner + Execution Control Center
```

Runtime giữ durable client registry, per-client event cursor, controller lease/fencing, task/run/proof/capsule và repository write authority. Controller semantic và write lease là hai khái niệm riêng; chuyển controller không tự trao quyền mutation checkout.

Không đồng bộ transcript giữa ChatWeb và Desktop. Continuity được rebuild từ ledger/task/proof/capsule + bounded resume packet.

---

## 3. Smart Mode — 8 công cụ chính

Chế độ `smart` cố ý giữ tool surface nhỏ để ChatGPT chọn công cụ ổn định hơn và giảm số vòng gọi tool không cần thiết.

Profile contract hiện tại là **`smart-v3`** và chỉ public đúng **8 tool**:

| Tool | Mục đích |
|---|---|
| `workspace_context` | Xem nhanh workspace, project, thư mục gốc, Git, task hiện tại và diagnostics runtime khi dùng `detail=full`. |
| `agent_workflow` | Công cụ chính cho công việc coding end-to-end: phân tích, sửa code, test, build, release verification và resume. |
| `task_control` | Quản lý task/EOCL, background operation, audit/acceptance, coordination lane, handoff và restart runtime có xác nhận. |
| `exec_command` | Chạy một command tập trung khi high-level workflow không phù hợp. |
| `command_control` | Poll, gửi stdin, đọc thêm output hoặc dừng command session đang chạy. |
| `document_workflow` | Đọc/tạo/chuyển đổi PDF, DOCX, Markdown và text bằng workflow chuyên dụng. |
| `request_permissions` | Báo trạng thái yêu cầu quyền theo scope; không bao giờ tự biến host không hỗ trợ elicitation thành một permission grant. |
| `view_image` | Trả ảnh trong workspace về MCP client để model có thể xem. |

Một số tool cũ vẫn được giữ dưới lớp **compatibility** để client cache cũ không bị gãy, nhưng agent mới không nên chủ động tìm hoặc gọi các tên legacy này.

### Tool contract fingerprint và connector refresh

Runtime tính một SHA-256 deterministic từ đúng tool contract đang expose và công bố cùng:

```text
schema_version
profile = smart-v3
sha256
tool_count = 8
```

Electron so fingerprint hiện tại với fingerprint mà operator đã xác nhận cho ChatGPT. Khi contract thay đổi, app hiện cảnh báo cần **Refresh actions / làm mới MCP app trong ChatGPT**. Sau khi đã refresh thành công, operator bấm **“Tôi đã làm mới ChatGPT MCP”** để ghi nhận hash hiện tại.

Cơ chế này là **stale-schema detection**, không giả định ChatGPT sẽ tự động nhận schema mới. Việc refresh/re-publish phía ChatGPT vẫn phụ thuộc khả năng của workspace/host.

### Vì sao chỉ giữ 8 tool?

Thay vì để model tự ghép hàng chục thao tác thấp cấp, bản hiện tại gom các bước thường dùng vào workflow lớn hơn:

```text
workspace_context
      ↓
agent_workflow
      ↓
localize → change → test/build → diff → task state
```

Cách này giảm round-trip, giảm thao tác lặp, hạn chế context dư thừa và làm kết quả dễ kiểm chứng hơn.

---

## 4. `agent_workflow` — trung tâm của Coding Tools MCP

`agent_workflow` là tool nên dùng mặc định cho hầu hết tác vụ coding thực tế.

### Nhóm workflow hỗ trợ

- `bugfix` — sửa lỗi;
- `feature` — phát triển tính năng;
- `greenfield` — tạo project/file mới;
- `refactor` — tái cấu trúc;
- `test_failure` — chẩn đoán và sửa test fail;
- `build_release` — kiểm tra build/release;
- `diagnose` — điều tra read-only;
- `document` — luồng tài liệu;
- `resume` — tiếp tục task đã lưu;
- `custom` — workflow tùy chỉnh.

### Các phase

| Phase | Ý nghĩa |
|---|---|
| `prepare` | Thu thập context, search, đọc file liên quan và chuẩn bị bằng chứng. |
| `execute` | Áp dụng change set đã xác định và verification. |
| `run` | Prepare + execute trong một workflow liên tục. |
| `resume` | Khôi phục task/context trước đó rồi tiếp tục. |

### Một workflow có thể gom trong một lần gọi

- context và project instructions;
- file cần tạo hoặc patch cần áp dụng;
- command chuẩn bị;
- test command;
- build command;
- artifact verification;
- Git diff;
- task state;
- model routing;
- external review khi có giá trị.

### Bounded candidate packet

Khi Mini/Luna được dùng như candidate lane, MCP vẫn là writer/oracle owner. Candidate chỉ nhận bounded evidence packet. Với file lớn, packet hiện ưu tiên thêm các snippet quanh exact search matches để symbol nằm sâu trong file không bị mất chỉ vì phần đầu file đã chạm giới hạn đọc.

Các invariant hiện tại:

- tổng source evidence vẫn nằm trong budget candidate hiện có;
- tối đa 4 query-centered deep snippets;
- snippet chỉ đọc từ path nằm trong allowed candidate scope;
- candidate không có quyền tự mutation checkout chính;
- proof cuối vẫn do MCP chạy và ChatWeb/Sol quyết định acceptance.

---

## 5. Adaptive Model Routing

Bản hiện tại có router để chọn lane xử lý theo độ khó, phạm vi code và chất lượng oracle/verification.

### Các route đang được cấu hình

| Route | Model cấu hình | Effort | Deadline gợi ý | Ghi chú |
|---|---|---:|---:|---|
| `deterministic` | Không cần model phụ | — | — | Ưu tiên tool/test/compiler khi không cần phán đoán model. |
| `mini` | `gpt-5.4-mini` | `low` | 10s | Leaf nhỏ, rõ, rẻ, có oracle mạnh. |
| `luna` | `gpt-5.6-luna` | `high` | 15s | Tác vụ hẹp nhưng cần reasoning tốt hơn. |
| `terra` | `gpt-5.6-terra` | `high` | 25s | Cross-file hoặc implementation reasoning. |
| `sol_xhigh` | `gpt-5.6-sol` | `xhigh` | 30s | Tích hợp rộng, semantic phức tạp. |
| `sol_max` | `gpt-5.6-sol` | `max` | 30s | Tác vụ hệ quả cao; yêu cầu xác nhận high-cost. |
| `sol_ultra` | `gpt-5.6-sol` | `ultra` | 30s | Chỉ dùng khi được yêu cầu rõ; high-cost và có thể dùng parallel reasoning. |

> Đây là route cấu hình của repository hiện tại. Model thực tế còn phụ thuộc khả năng mà Codex runtime tại máy cung cấp.

### Strong oracle

Router không gửi bug nhỏ xuống Mini chỉ vì ít file.

Với bug/test-failure cục bộ, Mini chỉ được ưu tiên tự động khi có **strong oracle**, ví dụ:

- `verification=tests`;
- `verification=build`;
- `verification=all`;
- hoặc có `test_command` / `build_command` cụ thể.

Nếu phạm vi nhỏ nhưng không có oracle đủ mạnh, router có thể nâng lên Luna thay vì tối ưu chi phí quá sớm.

### High-cost gate

`sol_max` và `sol_ultra` bị chặn mặc định. Muốn gọi trực tiếp phải truyền xác nhận `allow_high_cost=true`.

Điều này tránh việc một tác vụ bình thường vô tình chạy route đắt nhất.

### Production routing calibration

Router có telemetry/cohort support, nhưng production threshold **không nên được mở rộng chỉ từ vài sample nhỏ hoặc scenario simulation**. Calibration phải dựa trên các real accepted task cùng class với route, first-pass/repair status, cost, TTA và defect evidence đủ đại diện.

---

## 6. Codex App Server Bridge

Repository hiện có `codex_bridge.py` để kết nối Coding Tools MCP với một **Codex App Server sidecar độc lập**.

Trong `smart` mode, `codex_bridge` không được public như một tool thứ 9. Nó được dùng nội bộ bởi workflow và vẫn tồn tại cho compatibility khi cần.

### Nguyên tắc an toàn của bridge

Codex sidecar:

- dùng Codex Desktop/CLI auth và persisted history trên máy;
- không chiếm hoặc điều khiển turn đang chạy trong Codex Desktop;
- chỉ làm việc trong workspace hiện tại;
- `approvalPolicy=never`;
- sandbox `read-only`;
- tắt network;
- không tự sửa file;
- không dùng MCP server lồng nhau từ Codex config;
- chỉ trả về candidate/review để Coding Tools MCP kiểm tra và áp dụng theo đường chính.

### Profile bridge hiện có

- `candidate_mini`;
- `candidate_luna`;
- `cross_file`;
- `deep_code`;
- `consequential`;
- `parallel_extreme`;
- `packet`;
- `scoped`;
- `critical`;
- `history`.

Bridge còn theo dõi token usage, cache ratio, estimated credits, thời gian chạy và capacity cooldown để router có thêm tín hiệu vận hành.

---

## 7. Review plane

Không phải thay đổi nào cũng cần một model thứ hai review.

Workflow hiện ưu tiên:

```text
Deterministic proof trước
        ↓
Nếu bằng chứng đã đủ → không gọi review ngoài
        ↓
Nếu cần review độc lập → packet/scoped/critical tùy rủi ro
```

Ví dụ, một bug cục bộ đã có test mạnh và verification pass có thể bỏ qua external review. Một feature rộng hơn có thể dùng packet review độc lập.

Mục tiêu là **độ tin cậy của kết quả**, không phải gọi càng nhiều model càng tốt.

---

## 8. Task state, EOCL và công việc chạy lâu

Coding Tools MCP có persistent task state theo workspace và một enforced orchestration control loop (EOCL) cho các workflow có mutation/proof.

Task có thể lưu:

- objective;
- bước hiện tại;
- bước tiếp theo;
- command đang chạy;
- test/build result;
- file đã sửa;
- lỗi;
- lịch sử task.

`task_control` hiện hỗ trợ các nhóm action:

- task lifecycle: `get`, `start`, `update`, `pause`, `stop`, `resume`, `clear`, `history`;
- background operation: `operation`;
- EOCL: `audit`, `accept`, `reject`;
- coordination: `lane`, `events`, `messages`, `ack`;
- durable state transfer: `handoff`;
- runtime control: `restart_runtime`.

EOCL bình thường đi qua:

```text
PREFLIGHT → READY → ROUTED → EXECUTING → PROVING → ACCEPTING → CHECKPOINTED
```

`REPLAN`, `BLOCKED` và `ABORTED` là các nhánh fail-closed. Một wave ở `ACCEPTING` phải được ChatWeb/Sol accept hoặc reject thay vì tự coi test xanh là final acceptance.

### Long-running workflow

`agent_workflow` có thể hand-off thành background operation nếu chạy lâu. Agent nhận `operation_id` rồi tiếp tục poll bằng `task_control` mà không phải chạy lại từ đầu.

### Durable handoff capsule

`task_control(handoff)` có thể ghi/đọc capsule bounded để chuyển sang chat/window mới mà không cần replay toàn transcript. Capsule dùng cho rollover/recovery; auto-handoff không nên bật chỉ từ một vài sample nhỏ.

### Production-safe runtime restart

`task_control(action="restart_runtime")` là control-plane operation, không phải `taskkill` trực tiếp từ MCP.

Yêu cầu:

```text
confirm_restart = true
```

Flow:

```text
ChatGPT / MCP call
      ↓
MCP kiểm tra explicit confirmation + runtime idle
      ↓
ghi delayed, short-lived, workspace-bound one-shot ticket
      ↓
trả response với expected_disconnect=true
      ↓
Electron supervisor consume ticket
      ↓
RuntimeOrchestrator.restart()
      ↓
reconnect → workspace_context(full) → xác minh instance id mới
```

Ticket hiện được collapse khi có concurrent request, hết hạn nhanh và không được replay từ JSON backup. Electron là owner của service lifecycle; MCP không tự kill process phục vụ chính request của nó.

### Command session

Command dài được quản lý bằng session riêng:

```text
exec_command
    ↓
command_id / output_ref
    ↓
command_control
    ├─ poll
    ├─ read
    ├─ write stdin
    └─ kill
```

Nhờ vậy một build hoặc test dài không cần bị hủy chỉ vì một lượt chat đã kết thúc.

---

## 9. Document Workflow

`document_workflow` là đường chính cho các tác vụ tài liệu.

Hỗ trợ:

- inspect PDF;
- inspect DOCX;
- inspect Markdown/text;
- tạo DOCX;
- tạo Markdown;
- tạo text;
- chuyển đổi tài liệu sang DOCX;
- trả metadata verification như kích thước, số dòng, SHA-256 và preview khi tạo file.

Nguyên tắc của workflow:

```text
inspect nguồn một lần
        ↓
model xử lý nội dung
        ↓
create output hoàn chỉnh một lần
```

Không nên dùng shell hoặc nhiều patch nhỏ để dựng tài liệu nếu `document_workflow` đã xử lý được trực tiếp.

---

## 10. Permission Mode của Coding Tools MCP

Coding Tools MCP hiện có ba permission mode ở runtime Python:

| Mode | Network | Shell expansion / inline script | Secret env filter | Landlock trên Linux | Mức sử dụng |
|---|---|---|---|---|---|
| `safe` | Tắt mặc định | Chặn | Bật | Bật khi host hỗ trợ | Mặc định an toàn. |
| `trusted` | Cho phép | Cho phép | Bật | Bật khi host hỗ trợ | Máy/dev workspace tin cậy. |
| `dangerous` | Cho phép | Cho phép | Tắt | Tắt | Bỏ qua phần lớn permission gate; chỉ dùng khi hiểu rõ rủi ro. |

Ngoài permission mode, runtime còn có:

- workspace boundary;
- authorized roots;
- symlink escape protection;
- lọc biến môi trường nhạy cảm;
- command policy;
- destructive-command detection;
- runtime HOME/TMP/CACHE riêng;
- giới hạn output/session;
- kiểm tra path trước khi đọc/ghi.

### Khi MCP host không hỗ trợ permission elicitation

`request_permissions` là **status-reporting tool**, không phải cơ chế bypass server policy.

Nếu client/host hiện tại không hỗ trợ interactive elicitation, runtime trả một kết quả thành công ở cấp MCP với semantics:

```text
status = unsupported
grant_id = null
error.code = ELICITATION_UNSUPPORTED
fallback.mode = server_policy
fallback.granted = false
fallback.fail_closed = true
```

Điều này có nghĩa: tool đã báo trạng thái thành công, **permission vẫn không được cấp**. Client không nên retry y hệt vô hạn và server không được biến `ELICITATION_UNSUPPORTED` thành implicit grant.

> Landlock chỉ có ý nghĩa trên Linux khi kernel/host hỗ trợ. Trên Windows, runtime vẫn áp dụng các policy/path guard tương ứng nhưng không có Linux Landlock sandbox.

---

## 11. Tool Mode

Ngoài `smart`, server còn có các tool mode khác:

| Mode | Mục đích |
|---|---|
| `smart` | Surface nhỏ 8 tool (`smart-v3`), khuyến nghị cho ChatGPT hiện tại. |
| `readonly` | Chỉ inspection/Git/read tools. |
| `coding` | Đọc + sửa code + command + build verification. |
| `build` | Tập trung inspection/command/build, không expose patch write như coding mode. |
| `full` | Expose toàn bộ tool registry; chủ yếu phục vụ debug/compatibility/advanced use. |

Khuyến nghị: **dùng `smart` cho luồng agent bình thường**.

---

## 12. Cách chạy desktop app từ source

### Yêu cầu

- Windows;
- Node.js + npm;
- Git;
- Codex Desktop/CLI nếu muốn dùng adaptive Codex bridge;
- các toolchain riêng của project mà bạn định làm việc với ChatGPT.

### Cài dependency

```powershell
cd E:\DEV\Tools-Codex-web
npm install
```

### Chạy desktop app

```powershell
npm start
```

Script hiện tại chạy:

```text
electron .
```

Trên thanh công cụ có nút **Bảng điều khiển** để mở **Execution Control Center** ngay bên cạnh ChatGPT. Panel hiển thị theo thời gian thực:

- trạng thái nhiệm vụ (objective, bước hiện tại, tiến độ, command đang chạy kèm thời gian);
- trình tự điều phối (run/wave, execution mode, base HEAD, số sự kiện/wave/checkpoint);
- luồng sự kiện audit mới nhất, bằng chứng (proofs), ủy quyền model (delegations);
- trạng thái MCP + Tunnel và cảnh báo khi đang tự khôi phục;
- ChatWeb/Codex Desktop online state, per-client cursor/lag, controller lease/fencing và write authority;
- `SAFE TO ROTATE CHATWEB: YES/NO` cùng reason codes; context pressure chỉ hiện khi có nguồn thật, nếu host không expose thì ghi `unknown`;
- bounded resume summary;
- điều khiển: tạm dừng / tiếp tục / dừng nhiệm vụ qua MCP/EOCL, **Ghi capsule handoff** (≤8 KB), và manual controller transfer có xác nhận;
- **Copy Codex MCP config** để lấy cấu hình thin-proxy không chứa bearer.

Dữ liệu panel lấy từ endpoint `GET /__control/orchestration` của Coding Tools MCP (yêu cầu Bearer token).

### Kết nối Codex Desktop vào cùng Execution Hub

Không khuyến nghị cấu hình Codex Desktop chạy trực tiếp `python -m coding_tools_mcp --stdio` trên cùng workspace, vì cách đó tạo một Runtime authority thứ hai.

Luồng khuyến nghị:

1. chạy Electron app để Execution Hub/gateway sẵn sàng;
2. mở **Execution Control Center** và bấm **Copy Codex MCP config**;
3. review đoạn TOML vừa copy rồi tự paste/replace block `[mcp_servers.coding-tools]` trong cấu hình Codex Desktop;
4. restart/mở session Codex Desktop mới;
5. kiểm tra card **Codex Desktop** chuyển thành `online` trong Hub.

Config được sinh từ Python mà Electron đã verify, bundled `resources/coding-tools-mcp` và descriptor trong app `userData`. Descriptor chỉ có loopback port + gateway-scoped token của process Electron; **real MCP bearer vẫn nằm trong Electron SecretStore**. App không tự sửa `~/.codex/config.toml`.

Desktop proxy gửi heartbeat định kỳ khi stdio còn attach, nhưng không mở workspace/ledger và không tự claim controller khi ChatWeb đang giữ lease. Chuyển controller vẫn là thao tác manual có xác nhận; auto-handoff hiện OFF.

### Khởi động lại dịch vụ

Trong desktop app, dùng nút **“Khởi động lại toàn bộ dịch vụ”** để Electron restart MCP và Tunnel theo đúng ownership/order.

Nếu MCP tool contract thay đổi, sau restart app có thể hiện cảnh báo connector stale. Khi đó refresh/recreate MCP app phía ChatGPT theo khả năng workspace, mở chat mới nếu cần, xác minh schema mới rồi mới xác nhận contract trong desktop app.

### Chạy test của desktop app

```powershell
npm test
```

### Chạy test Coding Tools MCP từ repository root

```powershell
npm run test:mcp
```

Script này tự chuyển vào `resources/coding-tools-mcp` trước khi chạy pytest để import path ổn định. Có thể chạy cả hai suite chính bằng:

```powershell
npm run test:all
```

### Build installer Windows

```powershell
npm run dist
```

Output của Electron Builder nằm trong:

```text
dist\
```

Có thể build dạng thư mục chưa đóng gói bằng:

```powershell
npm run dist:dir
```

---

## 13. Cấu trúc thư mục quan trọng

```text
Tools-Codex-web/
├─ electron/                         # main process và runtime orchestrator
├─ renderer/                         # giao diện desktop
├─ resources/
│  ├─ coding-tools-mcp/              # Coding Tools MCP Python runtime
│  │  ├─ coding_tools_mcp/
│  │  │  ├─ server.py               # tool registry, schemas, workflow, policy
│  │  │  ├─ codex_bridge.py         # Codex App Server sidecar
│  │  │  └─ ...
│  │  └─ tests/
│  ├─ native-python/                 # Python runtime đóng gói cho desktop
│  └─ tools/                         # helper/tunnel binaries
├─ tests/                            # stability/source tests cho desktop
├─ docs/
│  ├─ agent/                         # kiến trúc, authority, session decisions
│  └─ research/                      # benchmark/research model routing
├─ scripts/
├─ package.json
└─ README.md
```

Repo vẫn chứa nhiều thành phần WebCodex upstream như Rust crates, server/deployment docs và các thành phần liên quan. Desktop app hiện đóng gói phần `electron`, `renderer` và `resources` làm sản phẩm chạy trực tiếp trên Windows.

---

## 14. Ví dụ dùng với ChatGPT

### Kiểm tra project

```text
Kiểm tra workspace hiện tại, Git status và cho tôi biết file nào đang thay đổi.
```

Agent nên bắt đầu bằng `workspace_context`.

### Sửa bug và test

```text
Tìm nguyên nhân test đăng nhập đang fail, sửa đúng nguyên nhân và chạy lại test liên quan.
```

Agent nên dùng `agent_workflow` với workflow `bugfix` hoặc `test_failure`.

### Làm feature

```text
Thêm tính năng X, chỉ sửa các file cần thiết, chạy test và build trước khi kết luận.
```

`agent_workflow` sẽ gom context, change set và verification vào một luồng.

### Theo dõi build dài

```text
Build project và báo tiến độ cho tôi cho đến khi hoàn tất.
```

Command dài sẽ được quản lý qua `exec_command` + `command_control` hoặc background operation của `agent_workflow`.

### Làm tài liệu

```text
Đọc file PDF yêu cầu, tóm tắt và tạo report.docx trong workspace.
```

Agent nên dùng `document_workflow`, không tự ghép shell/Python nếu không cần.

---

## 15. Git workflow khuyến nghị

Coding Tools MCP có thể kiểm tra Git và hỗ trợ chuẩn bị commit, nhưng trước khi push nên luôn đảm bảo:

1. workspace đúng;
2. không có file tạm/tooling vô tình bị stage;
3. test/build liên quan đã pass;
4. `git diff` đúng phạm vi;
5. không force-push nếu chưa xác định rõ lịch sử remote;
6. chỉ push khi task của người dùng thực sự yêu cầu push.

Với repository này, `main` là nhánh đang dùng cho bản Tools-Codex-web hiện tại.

---

## 16. Phân biệt permission của Coding Tools MCP và authority của WebCodex core

Repository có hai lớp khái niệm khác nhau, không nên trộn lẫn:

### Coding Tools MCP Python runtime

Dùng:

```text
safe | trusted | dangerous
```

Đây là policy trực tiếp cho command/network/sandbox của runtime MCP desktop.

### WebCodex core/server

Phần WebCodex core trong repo có authority model riêng:

```text
WEBCODEX_AUTHORITY_MODE=trusted_agent|restricted
```

`trusted_agent` là chế độ tự thực thi sau hard-safety checks; `restricted` yêu cầu luồng authorization phù hợp. Legacy `WEBCODEX_PERMISSION_MODE` đã bị loại bỏ trong contract WebCodex core và không nên được dùng làm alias.

Nếu bạn chỉ chạy desktop Coding Tools MCP hiện tại thì phần cần quan tâm trực tiếp nhất vẫn là permission mode của Coding Tools MCP.

---

## 17. Bảo mật

Công cụ này có khả năng sửa file và chạy command thật trên máy.

Hãy coi một MCP client đã kết nối như một coding agent có quyền thực thi trong phạm vi được cấu hình.

Khuyến nghị:

- chỉ chọn workspace thật sự cần thiết;
- không đưa token/API key/credential vào Git;
- không dùng `dangerous` cho repository hoặc command không tin cậy;
- giữ source trong Git để có thể rollback;
- kiểm tra diff trước commit/push;
- không mở tunnel public lâu hơn cần thiết;
- không chia sẻ endpoint/token của MCP cho người không có quyền;
- giữ Codex bridge ở read-only như thiết kế hiện tại;
- với thao tác release/deploy/delete dữ liệu, luôn yêu cầu scope và target rõ ràng.

Xem thêm: [`SECURITY.md`](SECURITY.md).

---

## 18. Tài liệu kỹ thuật trong repository

Các tài liệu hữu ích cho kiến trúc hiện tại:

- [`docs/agent/architecture-decisions.md`](docs/agent/architecture-decisions.md) — quyết định kiến trúc bền vững;
- [`docs/agent/permission-model.md`](docs/agent/permission-model.md) — authority/safety model của WebCodex core;
- [`docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`](docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md) — benchmark executor routing;
- [`docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`](docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md) — nghiên cứu orchestration/model routing;
- [`docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md`](docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md) — trạng thái proof-cache, handoff, runtime activation và routing evidence hiện tại;
- [`AGENTS.md`](AGENTS.md) — hướng dẫn cho coding agent trong repository.

---

## 19. Nguyên tắc phát triển của bản hiện tại

Bản Tools-Codex-web này ưu tiên:

1. **High-level workflow trước low-level tool.**
2. **Test/compiler/deterministic evidence trước model debate.**
3. **Model rẻ chỉ dùng khi đủ chắc chắn.**
4. **Sol giữ phần semantic/integration quan trọng.**
5. **Không tạo nhiều worker nếu công việc thực chất là tuần tự.**
6. **Không lặp lại inspection/test đã có bằng chứng hợp lệ.**
7. **Không ghi đè workspace ngoài scope.**
8. **Không để Codex sidecar tự mutation repository.**
9. **Không force-push chỉ để giải quyết lịch sử Git bị lệch.**
10. **Kết luận dựa trên verification đã thực sự chạy.**

---

## 20. Nguồn gốc và ghi nhận

Project này kế thừa nhiều thành phần và ý tưởng từ **WebCodex** upstream, sau đó được tùy biến cho workflow desktop cá nhân, Coding Tools MCP và model orchestration.

Upstream WebCodex:

```text
https://github.com/yyjeqhc/webcodex
```

Repository tùy biến hiện tại:

```text
https://github.com/uyenthudao2410-code/Tools-Codex-web
```

Cảm ơn các dự án MCP, WebCodex, Codex và cộng đồng mã nguồn mở đã tạo nền tảng cho bộ công cụ này.

---

## 21. License

Xem file [`LICENSE`](LICENSE) và [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) trong repository để biết điều khoản áp dụng cho source và các thành phần bên thứ ba.

---

### Tóm tắt

Nếu chỉ cần nhớ bốn điểm về bản hiện tại:

> **1. `smart-v3` chỉ public 8 tool và có contract fingerprint để phát hiện connector stale.**
> **2. `agent_workflow` là đường chính cho coding; MCP giữ mutation/proof, route rẻ chỉ được dùng khi evidence đủ mạnh.**
> **3. `task_control` quản lý EOCL/handoff và có production-safe `restart_runtime` qua Electron supervisor.**
> **4. `request_permissions` fail-closed: host không hỗ trợ elicitation không bao giờ đồng nghĩa permission được cấp.**
