# 261023 — Codex Desktop dùng tool của Coding Tools MCP Hub (Codex-web)

**Ngày:** 2026-10-23 (tối, sau W6/r19) · **Máy:** DESKTOP-63643J4 (Windows, Admin) · **Trạng thái: ĐÃ ÁP DỤNG + KIỂM CHỨNG GUI ĐẦU-CUỐI PASS**
**Cửa sổ bằng chứng:** 23/10/2026 22:26–22:44 (+07). **Trạng thái repo quan sát được:** GitHub main `a554b5df`; checkout Windows `E:\DEV\Codex-web` ở nhánh `main`, đồng bộ `origin/main` (chip trên app: `main @ a554b5`; chính câu trả lời của lượt kiểm chứng cũng xác nhận ahead/behind 0).

Mục tiêu trải nghiệm: mở Codex Desktop (app ChatGPT/Codex trên Windows) → chọn model →
chat → trợ lý trong Desktop gọi được các tool của Coding Tools MCP Hub trong lúc chat.

---

## 1. Nghiên cứu mẫu GitHub / tài liệu công khai

| # | Nguồn | Cơ chế họ dùng | Điểm áp dụng cho mình |
|---|-------|----------------|------------------------|
| 1 | OpenAI — Docs MCP (developers.openai.com/learn/docs-mcp) | `codex mcp add <name> --url …` hoặc ghi trực tiếp `[mcp_servers.*]` vào `~/.codex/config.toml`; cấu hình **dùng chung** giữa CLI và IDE extension, kiểm chứng bằng `codex mcp list` | Khẳng định đường chính thống: một file `~/.codex/config.toml` cho mọi bề mặt Codex (CLI, IDE, Desktop app) |
| 2 | Matagi — "Codex MCP Setup: Add MCP Servers to OpenAI Codex (CLI + Desktop)" (matagi.ai) | Desktop app: Settings → Integrations → MCP servers → Add server, có tab **STDIO** cho server nội bộ và Streamable HTTP cho server từ xa | Desktop đọc cùng `config.toml`; server stdio nội bộ là mẫu hình đúng cho hub chạy trên cùng máy |
| 3 | Context7 — kiểm chứng thực tế với Codex CLI 0.160.0 (octomind.run/blog/context7-mcp) | `codex mcp add` ghi `[mcp_servers.context7] command/args` vào `~/.codex/config.toml`; CLI, desktop app và IDE extension dùng chung; tên khóa hiện hành là `startup_timeout_sec` (tài liệu cũ ghi `startup_timeout_ms`), timeout khởi động mặc định 10 giây | Bằng chứng thực địa ở phiên bản gần với bản đang dùng (0.164.0); lưu ý drift tên khóa giữa các phiên bản |
| 4 | SonarSource — "How to use OpenAI Codex CLI with SonarQube MCP Server" (sonarsource.com) | Server stdio qua Docker khai trong `config.toml` (`command/args/env`), kiểm chứng trong phiên bằng `/mcp` | Mẫu stdio + env inline giống hệt dạng generator của repo sinh ra |
| 5 | cexll/codex-mcp-server ("Codex MCP Tool", GitHub) | Dự án cộng đồng bọc **Codex CLI thành MCP server** để client khác (Claude, Cursor) gọi Codex như một tool | Chiều ngược lại với nhu cầu của mình (mình cần Desktop làm MCP *client* của hub), nhưng chứng minh hệ sinh thái đều chuẩn hoá trên stdio MCP + file cấu hình của host |
| 6 | TeaBranch/agentic-developer-mcp ("Codex Wrapper MCP Server", mcpservers.org) | Bọc Codex CLI thành MCP server qua Node Express + open-responses-server | Tương tự #5: hướng wrapper-Codex; không cần cho mình vì hub đã là MCP server thật |
| 7 | wiztechnoz / groundtruth — ghi chú phát hành OpenAI 24/08/2026 | **`codex mcp-server` bị deprecated**, thay bằng **Codex app-server** (JSON-RPC riêng) | Rủi ro cần tránh: không xây gì trên `codex mcp-server`. Hướng của mình không đụng tới nó: Desktop là MCP client → stdio proxy → hub; còn chat native trong Codex-web đi qua app-server (đúng khuyến nghị) |

**Kết luận khả thi:** khả thi bằng cơ chế chính thống, không cần dự án mẫu bên ngoài —
Codex Desktop nạp MCP server từ `~/.codex/config.toml` (`[mcp_servers.<name>]`, stdio),
và repo Codex-web **đã có sẵn đường thiết kế cho đúng việc này** (xem §2).

**Rủi ro đã ghi nhận:**
- Desktop chỉ nạp cấu hình MCP **khi khởi động** → sửa config xong phải khởi động lại app (đã kiểm chứng thực tế, §4).
- Schema config trôi theo phiên bản Codex (ví dụ `rmcp_client`/`experimental_use_rmcp_client` ở bản cũ, `startup_timeout_ms` → `startup_timeout_sec`); phải đối chiếu bằng chính CLI đang cài (`codex mcp list/get`) thay vì tin tài liệu cũ.
- Timeout khởi động MCP mặc định ~10 giây: proxy Python phải lên nhanh (đo thực tế 0,6 giây — đạt).
- **Mã hoá stdout trên Windows:** proxy ghi JSON qua stdout text-mode của Python; trên máy locale Việt Nam, output bị mã hoá theo ANSI codepage → hỏng UTF-8 → client MCP không parse được. Phải chạy Python với `-X utf8` (xem §3).

## 2. Đối chiếu cơ chế đã có trong repo Codex-web

- `electron/services/codexDesktopConfig.js` — `buildCodexDesktopMcpConfig()` sinh đúng khối
  TOML `[mcp_servers.coding-tools]` (command = Python, args chứa `-m coding_tools_mcp.hub_proxy_stdio
  --descriptor <…>`, `env = { PYTHONPATH = … }`), không chứa bearer/token (`containsBearer: false`),
  có test `tests/codex-desktop-config.test.js` (kể cả mẫu `prefixArgs: ["-X", "utf8"]`).
- `electron/main.js` (IPC `panel:copy-codex-config`) — app tự sinh cấu hình này bằng
  `pythonStatus()` + `resourcesRoot()` + `hubProxyDescriptorFile()` rồi copy vào clipboard:
  đây là đường thiết kế sẵn của sản phẩm.
- `resources/coding-tools-mcp/coding_tools_mcp/hub_proxy_stdio.py` — proxy stdio mỏng:
  đọc descriptor `%APPDATA%\web-mcp-assistant\execution-hub-proxy.json` (host/port/token của
  gateway nội bộ, token **chỉ** nằm trong descriptor, không vào config.toml), forward JSON-RPC
  tới hub qua HTTP với danh tính client allowlist `codex-desktop`/`codex_desktop`, có heartbeat.
  Proxy đọc lại descriptor ở mỗi lời gọi nên hub đổi port khi khởi động lại vẫn theo được.

→ Áp dụng = sinh khối TOML bằng chính generator của repo với các tham số đúng như bản đóng gói
r19 đang chạy dùng, và append vào `~/.codex/config.toml`. Không tự chế định dạng.

## 3. Đã áp dụng trên Windows

**Hiện trạng trước (22:2x 23/10):** `C:\Users\Admin\.codex\config.toml` (4.425 byte,
SHA-256 `B9D22C5C…E64F0774`) có sẵn `[mcp_servers.node_repl]`, `[mcp_servers.autocad-mcp]`
(cùng các server do plugin cấp: canvas-authoring, codex_app, cua_repl) — **chưa có** mục nào
trỏ vào hub (`coding-tools`/`hub_proxy_stdio` đều vắng). Hub r19 đang chạy (descriptor hợp lệ:
127.0.0.1:64485, version 1).

**Sao lưu:** `C:\Users\Admin\.codex\config.toml.bak-20261023-desktop-hub` — hash của bản sao
khớp 100% hash gốc trước khi sửa.

**Tham số generator (đúng bản r19 đang chạy):**
- resources root: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-r19-cos-integration\win-unpacked\resources\resources`
  (lưu ý layout đóng gói có thêm một tầng `resources\` bên trong)
- `pythonCommand`: `…\resources\resources\native-python\python.exe` (portable Python của bản đóng gói — đúng thứ `pythonStatus()` chọn đầu tiên)
- `pythonPath`: `…\resources\resources\coding-tools-mcp\python_vendor;…\resources\resources\coding-tools-mcp`
- `descriptorPath`: `C:\Users\Admin\AppData\Roaming\web-mcp-assistant\execution-hub-proxy.json`

**Khối đã append (dạng cuối, sau hash `B7D35FDF…B7356C96384F6C`, 5.082 byte):**

```toml
[mcp_servers.coding-tools]
command = "E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-r19-cos-integration\\win-unpacked\\resources\\resources\\native-python\\python.exe"
args = ["-X", "utf8", "-m", "coding_tools_mcp.hub_proxy_stdio", "--descriptor", "C:\\Users\\Admin\\AppData\\Roaming\\web-mcp-assistant\\execution-hub-proxy.json"]
env = { PYTHONPATH = "E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-r19-cos-integration\\win-unpacked\\resources\\resources\\coding-tools-mcp\\python_vendor;E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-r19-cos-integration\\win-unpacked\\resources\\resources\\coding-tools-mcp" }
```

**Lệch duy nhất so với lần sinh đầu tiên — và lý do:** lần sinh đầu dùng `prefixArgs: []`
(đúng như `pythonStatus()` của bản đóng gói trả về). Kiểm chứng tĩnh cho thấy khi đó phản hồi
initialize (32,5 KB, có ký tự ngoài ASCII) bị ghi ra stdout theo ANSI codepage của máy →
sai UTF-8 ở byte 4.303 (`0x97`) → client MCP chuẩn không đọc được. Thêm `-X utf8` qua chính
tham số `prefixArgs` của generator (dạng này có sẵn trong test của repo) thì initialize +
tools/list đều sạch UTF-8. Mọi mục cấu hình khác của user giữ nguyên byte-for-byte
(thao tác thực hiện: khôi phục từ .bak rồi append lại khối đúng, tránh trùng bảng).

**Giới hạn cần nhớ:** đường dẫn trỏ vào thư mục build `r19-cos-integration`. Khi cài bản
đóng gói mới (r20+…), phải sinh lại khối này theo resources của bản mới (nút copy-config
trong app làm đúng việc đó), nếu không Desktop sẽ trỏ vào thư mục build cũ.

## 4. Kiểm chứng

**Tĩnh (CLI, trước khi mở GUI):**
- `codex mcp list` (codex-cli 0.164.0): `coding-tools` xuất hiện, **enabled**;
  `codex mcp get coding-tools`: `enabled: true`, `transport: stdio`, command/args/env đúng như đã ghi.
- MCP client tối giản gọi đúng command trong config (spawn + `initialize` + `tools/list`):
  initialize **0,6 giây**, `protocolVersion 2025-11-25`, server `coding-tools-mcp` version 1.0.7;
  `tools/list` trả **đúng 8 tool smart-v3**: `workspace_context`, `agent_workflow`, `task_control`,
  `command_control`, `document_workflow`, `exec_command`, `request_permissions`, `view_image`.
  (Bản ghi: `E:\DEV\w6\desktop-hub-fromconfig-receipt.json`.)
- Ghi nhận tương thích giao thức: gateway của hub hỗ trợ MCP `2025-11-25 / 2025-06-18 / 2025-03-26`
  (bản nháp `2026-07-28` bị từ chối `-32602` — chỉ là ghi chú kiểm chứng, Desktop dùng bản được hỗ trợ).

**GUI (Codex Desktop, 22:33–22:42):**
1. Desktop lúc bắt đầu đã chạy từ 10:04 với app-server cũ (pid 42304). Chụp màn hình xác nhận
   không có lượt nào đang chạy dở (thread gần nhất hoàn tất 20:06, composer trống) → thoát hẳn
   bằng menu **Tệp → Thoát ChatGPT (Ctrl+Q)**. Lưu ý vận hành: nút đóng cửa sổ/Alt+F4 chỉ ẩn
   app xuống nền (mọi tiến trình vẫn sống) — muốn nạp lại config phải Thoát hẳn.
2. Mở lại app: tiến trình chính mới (pid 47088, 22:33:32), **app-server mới (codex pid 52084,
   22:33:38)** — bản này đọc config đã có `coding-tools`.
3. Thread mới "Kiểm tra trạng thái hub": đổi model trong bộ chọn từ mặc định **6.1 Sol** sang
   **5.6 Terra** (mức "Cực cao"), gửi câu: *"Dung tool workspace_context cua MCP server
   coding-tools de xem trang thai hub va control plane hien tai, roi tom tat ngan gon."*
4. Lượt chạy 4 phút 10 giây: UI hiện bước **"Accessing current Codex-web workspace context"**,
   kết thúc bằng trả lời *"Đã gọi `workspace_context` thành công."* + tóm tắt đúng dữ liệu sống
   của hub (endpoint bind vào `E:\DEV\Codex-web`; admission/gate `open`; task gần nhất
   `completed`/`ACCEPTED`, orchestration `CHECKPOINTED`; git `main` đồng bộ `origin/main`;
   18 stale runs; semantic localization `UNAVAILABLE`).
5. **Bằng chứng phía hub (độc lập với GUI):** ledger hiệu năng của hub
   (`E:\DEV\Codex-web\.coding-tools\performance.json`) ghi đúng một lời gọi trong cửa sổ lượt chạy:
   `workspace_context`, 22:41:15–22:41:16 (+07), `client_id: "codex-desktop"`,
   `client_type: "codex_desktop"`, outcome `ok`, response 531.020 byte,
   `orchestration_state: "CHECKPOINTED"` — danh tính này chỉ xuất hiện khi lời gọi đi qua
   `hub_proxy_stdio` (proxy gắn header danh tính allowlist). Bản ghi trích ra:
   `E:\DEV\w6\desktop-hub-evidence.json`.
   (Ảnh chụp các bước: `~/workspace/research/cos-webcodex/w6/desktop-*.png`, bản chốt:
   `desktop-hub-final.png` / `desktop-turn-poll3.png`.)

**Chưa/điểm còn thiếu:**
- Mới chứng minh một tool đọc (`workspace_context`). Các tool còn lại dùng chung một đường
  (cùng server, cùng tools/list) nhưng chưa gọi thử từng tool trong Desktop.
- Proxy do app-server quản lý theo phiên thread (không thấy tiến trình Python thường trực
  trong các lần kiểm tra điểm) — hành vi này bình thường với stdio MCP.
- Cấu hình gắn với thư mục build r19 (xem giới hạn ở §3).

## 5. Cách gỡ

1. Khôi phục nguyên trạng: copy `C:\Users\Admin\.codex\config.toml.bak-20261023-desktop-hub`
   đè lên `C:\Users\Admin\.codex\config.toml` (hoặc gọn hơn: `codex mcp remove coding-tools`).
2. Thoát hẳn Codex Desktop (Tệp → Thoát ChatGPT) rồi mở lại để app-server nạp config cũ.
3. Kiểm chứng: `codex mcp list` không còn `coding-tools`.

---

*Thực hiện bằng SSH (`win-ssh.sh`) + Interactive scheduled task/GUI automation, script tại
`~/workspace/research/cos-webcodex/w6/op47–op64`. Không commit/push thay đổi nào vào repo
trong đợt này ngoài tài liệu này; file cấu hình Desktop nằm ngoài repo (CODEX_HOME của user).*

---

**Bổ sung — đã sửa ở nguồn (23/10, cùng đợt commit với tài liệu này):** workaround `-X utf8`
áp dụng tay ở §3 đã thành mặc định trong mã nguồn. `buildCodexDesktopMcpConfig()`
(`electron/services/codexDesktopConfig.js`) nay tự chèn `-X`, `utf8` vào args trên Windows
khi caller chưa truyền (giữ nguyên vị trí các prefix args của launcher như `-3` của `py.exe`;
ngoài Windows không thay đổi), kèm test trong `tests/codex-desktop-config.test.js` khẳng định
trường hợp portable Python (prefixArgs rỗng — đúng đầu ra `pythonStatus()` của bản đóng gói).
Đối chiếu byte-level: block do generator đã sửa sinh ra với đúng tham số bản r19 **khớp hệt**
block đang chạy trong `~/.codex/config.toml`. Từ nay nút copy-config trong app sinh ra cấu
hình đúng ngay từ đầu; các bản đóng gói đã phát hành (r19) không đổi — config Desktop đang
live vốn đã có `-X utf8` do áp dụng tay.
