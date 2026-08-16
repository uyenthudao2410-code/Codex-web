# Kế hoạch Tích hợp Codex Desktop ⇄ ChatWeb MCP — "1 ledger, 2 mặt trận"

**Ngày:** 2026-08-14
**Trạng thái:** ĐÃ NỐI CẤU HÌNH (config phía Codex Desktop đã thêm), cần khởi động lại Codex Desktop để có hiệu lực
**Vấn đề gốc:** dùng riêng ChatWeb MCP thì mất context dài + phải chuyển task thủ công sang Desktop; dùng riêng Desktop thì mọi việc trả giá Sol xhigh (đo thật: 24,6× Mini) và token không giảm.

---

## 1. Ý tưởng: không chọn 1 trong 2 — để 2 bên dùng chung một bộ não vận hành

Thay vì "hoặc ChatWeb, hoặc Desktop", cả hai trở thành **2 client của cùng một backplane**:

```text
                    ┌────────────────────────────────────────────┐
                    │        CODING TOOLS MCP (đã có sẵn)        │
                    │  smart 8-tool · adaptive router (mini/luna/│
                    │  sol) · orchestration ledger · proof ledger│
                    │  task state · handoff capsule · idempotency│
                    └───────────────┬────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
   CHATWEB (qua OpenAI tunnel)                    CODEX DESKTOP (stdio, mới nối)
   - web research, acceptance                      - deep lane, context dài
   - user conversation                            - subagent khi cần
   - route xuống mini/luna qua MCP                - gọi agent_workflow → tự route
                                                   - đọc/ghi cùng ledger + capsule
```

- **Mỗi bên làm đúng việc mình giỏi**, nhưng **không phải chuyển task thủ công**: trạng thái nhiệm vụ nằm ở ledger + task-state + capsule — bên nào mở lên cũng thấy cùng một run/wave.
- **Router vẫn nằm trong MCP** → ngay cả khi làm việc trong Desktop, gọi `agent_workflow` cho leaf đã localize thì MCP tự route xuống mini/luna (0,05–0,23 credits thật) thay vì Sol xhigh (1,25 credits thật) — đây chính là đòn bẩy làm token **giảm ngay trong Desktop**.

## 2. Đã nối những gì (hôm nay)

### 2.1 Đăng ký Coding Tools MCP vào Codex Desktop

`~/.codex/config.toml` (đã backup `config.toml.before-coding-tools-mcp`):

```toml
[mcp_servers.coding-tools]
command = 'C:\Users\daoth\AppData\Local\Programs\Python\Python311\python.exe'
args = ['-m', 'coding_tools_mcp', '--stdio', '--permission-mode', 'trusted']
env = { CODING_TOOLS_MCP_TOOL_MODE = 'smart', PYTHONPATH = 'E:\Github\Tools-Codex-web\resources\coding-tools-mcp' }
```

- Stdio = **không cần tunnel, không cần token** — Desktop spawn trực tiếp process MCP.
- `--workspace` mặc định lấy **cwd của phiên Codex** → mỗi project tự có workspace + ledger riêng tại `<project>/.coding-tools/`. Mở Desktop ở `E:\Github\Tools-Codex-web` = dùng chung đúng ledger với app Electron.
- Smoke test đã chạy: initialize + tools/list trả đúng 8 tool smart.

### 2.2 Chiều ngược lại (đã có từ trước, đã benchmark thật)

MCP → Codex models qua `codex app-server` bridge: 8 profile (candidate_mini/luna, deep_code, packet, scoped, critical, consequential, parallel_extreme, history) — đo thật hôm nay: mini 0,05 credits, luna 0,23, sol xhigh 1,25 trên cùng packet đúng 3/3. Bridge tự tắt MCP lồng nhau khi chạy app-server (không lo đệ quy).

## 3. Quy tắc vận hành "thông nhau"

| Việc | Làm ở đâu | Vì sao |
|---|---|---|
| Leaf đã localize + có oracle (bugfix/test_failure) | ChatWeb hoặc Desktop đều được — **gọi `agent_workflow`** | Router tự chọn mini/luna (0,05–0,23 credits thật) |
| Deep work, refactor lớn, cross-file | **Codex Desktop** (Sol xhigh mặc định sẵn) | Context dài + persistent lane — đúng vai deep lane |
| Web research, yêu cầu người dùng, final acceptance | ChatWeb | Conversation context + web |
| Theo dõi trạng thái từ bên kia | `workspace_context` / `task_control action=events` | Cùng ledger, không cần kể lại |
| Xoay chat mới / đổi bên làm | **Ghi capsule handoff** (nút trên bảng điều khiển hoặc `task_control`) | Bên kia mở capsule + poll pending messages là tiếp tục được ngay |
| Task dài không ai trực | Background operation + poll | Durable qua restart |

## 4. Rủi ro kỹ thuật và cách phòng

1. **Hai writer một workspace** (Desktop tự sửa file + MCP apply_patch): chạy **một lane tại một thời điểm**; ledger lưu `base_head` + `worktree_fp` để phát hiện lệch base; `write_fences` đã có (blueprint ghi nhận còn PARTIAL — nếu va chạm thật thì nâng cấp sau khi gặp lần đầu).
2. **Hai process MCP cùng mở ledger SQLite**: SQLite khóa WAL + `task-state.json` ghi atomic — an toàn cho đọc/ghi đan xen.
3. **Desktop session mở MCP mà Python/PYTHONPATH sai** → MCP fail lớn trong session: đã smoke-test với đúng python + path; nếu đổi máy phải sửa 2 dòng này.
4. **Phiên Desktop ở project không có ledger** → MCP vẫn chạy bình thường, ledger tự tạo mới trong `.coding-tools/`.

## 5. Kiểm chứng sau khi khởi động lại Desktop

1. Mở Codex Desktop → session mới → hỏi: *"list các tool MCP coding-tools đang có"* → phải thấy 8 tool smart.
2. Chạy thử: *"dùng task_control xem trạng thái task hiện tại"* → phải trả đúng task-state đang chạy (nếu app Electron đang chạy cùng project).
3. Ghi capsule từ ChatWeb → mở Desktop hỏi `task_control action=handoff handoff_action=get` → phải đọc được capsule đó.
4. Sau 1 tuần, chạy lại phân tích `~/.codex/sessions` — nếu tuân thủ rule §3, tỷ lệ session sol sẽ giảm, mini/luna xuất hiện, credits/ngày giảm so với baseline 03/08.

## 6. Nguồn tham khảo

- Blueprint bidirectional: `docs/research/260813_CODEX_WEB_BIDIRECTIONAL_RESILIENT_ORCHESTRATION.md` (§2.1–2.7: ledger, lane registry, coordination storage, capsule — toàn bộ nền móng đã có sẵn trong code)
- Số liệu thật: `docs/research/2026-08-14_REAL_CODEX_BENCHMARK_AND_TOKEN_USAGE.md`
- Skill `sol-lean-codex` trong `~/.codex/skills` — chính sách phân vai model, dùng chung cho cả hai bên.
