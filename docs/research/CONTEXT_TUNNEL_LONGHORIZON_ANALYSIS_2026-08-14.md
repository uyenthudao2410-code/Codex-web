# Phân tích: Context 1M token, Điều phối dài hạn và Độ tin cậy Tunnel

**Ngày:** 2026-08-14
**Repository:** `E:\Github\Tools-Codex-web` (nhánh `main`, HEAD `d3c6f18`)
**Đối tượng:** 3 vấn đề vận hành thực tế — (1) ChatGPT web lag/lỗi khi gần đạt 1M token, (2) điều phối & làm việc dự án dài hơi, (3) tunnel lỗi / giám sát từ điện thoại-web không truyền đầy đủ nội dung hoặc bị tạo lại.
**Phương pháp:** đọc trực tiếp code production (`server.py`, `transport_http.py`, `protocol.py`, `runtimeOrchestrator.js`, `tunnelService.js`, `chatViewController.js`), phân tích log thật trên máy (`tunnel.log` 4.980 dòng, `mcp.log` 1,6 MB, `assistant.log`), ledger SQLite (42 runs/48 waves/504 events), `performance.json` (968 tool calls), và chạy toàn bộ test suite (131 python + 51 node = **182/182 pass**).

---

## 1. Kết luận điều hành

| Vấn đề người dùng | Nguyên nhân gốc (bằng chứng) | Hệ thống đã có gì | Còn thiếu gì |
|---|---|---|---|
| ChatGPT web lag/lỗi gần 1M token | Context window là hành vi **sản phẩm của ChatGPT** (phiên được nhúng trong app qua `persist:chatgpt-session`); app chỉ kiểm soát được những gì nó đưa vào | Mọi tool result bị chặn (2.000 dòng/50 KB), `output_ref` đọc tiếp, gate Mini ≤24 KB / Luna ≤60 KB, **handoff capsule 8 KB** + event replay để xoay chat mới | Capsule **chưa từng được dùng** (0 bản ghi trong ledger) — lối thoát đã thiết kế nhưng không được vận hành |
| Làm việc dài hơi | Kiến trúc durable (runs/waves/events/proofs/checkpoints/background ops) hoạt động đúng: 14 runs accepted, median 90,3 s; 6 waves replanned an toàn | Resume qua `task_control`, event replay phân trang, checkpoint theo Git HEAD + proof fingerprint | 28 runs bỏ ngỏ `active` không bao giờ đóng; `idempotency_records` = 0 → retry sau khi tunnel rớt có thể chạy lại lệnh 2 lần |
| Tunnel lỗi / nội dung thiếu / tạo lại | **12 lần tunnel client tạo lại trong 5 ngày** (08-08 → 13-08); control-plane poll failed/timeout; 12 lần `ConnectionAbortedError WinError 10053` **ngắt giữa chừng khi MCP đang ghi response** | Session alias (mọi session mới đều trỏ về 1 Runtime), stateless protocol 2026-07-28, supervisor tự phục hồi **chỉ tunnel** + backoff 2 s→60 s, 51 test node xanh | Không retry tự động cho tool call bị ngắt giữa chừng; không surface trạng thái tunnel cho người dùng; health UI chỉ ở localhost (không giám sát được từ điện thoại) |

**Phán quyết:** cả 3 vấn đề đều có lời giải hoặc lời giải một nửa **đã tồn tại trong codebase**, nhưng phần vận hành (capsule, idempotency, tunnel observability) chưa được dùng đến trong thực tế. Đây là bài toán **khoảng cách giữa thiết kế và vận hành**, không phải bài toán thiếu kiến trúc.

---

## 2. Vấn đề 1 — ChatGPT web gần 1M token: lag, không xử lý dài hạn được

### 2.1 Kiến trúc thực tế

Desktop app nhúng ChatGPT web trong chính nó (`electron/chatViewController.js`):

```text
CHAT_PARTITION = 'persist:chatgpt-session'   // phiên ChatGPT sống trong app
CHAT_HOME = 'https://chatgpt.com/'
```

Tức là "ChatGPT web" mà người dùng thấy là view nhúng, và giới hạn ~1M token + hiện tượng chậm khi gần đầy là **hành vi sản phẩm phía ChatGPT** — không code nào trong repo này thay đổi được. Điều repo kiểm soát được là **tốc độ nạp context vào phiên đó**.

### 2.2 Những gì hệ thống đang làm đúng để giảm tốc độ phình context

| Cơ chế | Nơi code | Hiệu lực |
|---|---|---|
| Mọi kết quả tool bị chặn mặc định 2.000 dòng / 50 KB, kèm cờ `truncated` + chỉ dẫn thu hẹp | `textutils.py:7,37` · `tool_results.py` | Mỗi tool call trung bình chỉ **10,6 KB** response (đo từ `performance.json`: 10,3 MB / 968 calls) |
| Command dài: chỉ trả tail, đọc tiếp qua `command_control` với `output_ref` — không nạp lại cả output | `processes.py:692-709` (head/tail buffer) · `tool_results.py:213` | Tránh nạp build/test log nhiều MB vào context |
| `agent_workflow` prepare đóng gói context: giới hạn file (`selected_paths`), bytes (24 KB cho lane Mini, 60 KB cho Luna) | `server.py:2793-2809` | Router *từ chối* lane rẻ khi context rộng |
| Workspace context là projection compact (không phải dump toàn bộ repo) | `project_context.py:59-120` | Giảm chi phí "nhìn quanh workspace" |
| Smart mode 8 tool — schema nhỏ | `server.py` + invariant T09 | Theo ToolScope (ACL 2026), bớt tool làm tăng độ chính xác chọn tool 8,38–38,6% → ít vòng gọi sai → ít token chết |

**Bằng chứng đo được:** tổng request bytes của 968 tool calls chỉ **915 KB** (0,95 KB/call) — phía MCP không phải là nguồn phình context. Nguồn phình là bản thân hội thoại ChatGPT (reasoning + tool results tích lũy + transcript dài ngày).

### 2.3 Lối thoát đã thiết kế nhưng chưa vận hành: handoff capsule

Hệ thống đã có đầy đủ cơ chế "xoay chat mới" đúng chuẩn:

```text
task_control action=handoff handoff_action=record  →  capsule ≤ 8 KB (HANDOFF_CAPSULE_MAX_BYTES = 8_192)
                                                    →  "Open a fresh ChatWeb conversation, fetch this capsule, then poll pending messages."
task_control action=handoff handoff_action=get     →  "Resume from this capsule; do not replay the previous ChatWeb transcript."
task_control action=events after_seq=N             →  replay audit events phân trang (≤500/lần) — không cần copy transcript
```

Capsule chứa đúng những thứ cần thiết (task_id, objective, base_head, worktree_fp, contract_fp, active lane ids, pending message ids) và **cấm** nhồi transcript/source/command output (`server.py:8942`). Thiết kế này trùng khớp với bài học field `openai/codex#32533` (session lớn bị chặn đến khi compaction) mà repo đã ghi nhận trong postmortem, và với quy tắc vận hành trong blueprint:

> **85% context**: không nhận thêm task dài; chuẩn bị chat mới (`260813_CODEX_WEB_ORCHESTRATION_BLUEPRINT.md:129`)

**Nhưng — bằng chứng quan trọng nhất:**

```text
ledger.handoff_capsules   = 0 rows   ← chưa từng ghi một capsule nào
ledger.coordination_messages = 0 rows
```

Khoảng trống này giải thích trực tiếp triệu chứng của người dùng: **chat bị kéo đến gần 1M token, lag, không xử lý được dài hạn — trong khi lối thoát (ghi capsule → chat mới → resume từ capsule + event replay) nằm sẵn trong code nhưng không bao giờ được kích hoạt.** Không có quy tắc nào trong smart-mode prompt/UI tự động nhắc người dùng xoay chat khi đạt ngưỡng.

### 2.4 Kết luận phần 1

- **Không phải lỗi kiến trúc:** phía MCP đã kỷ luật context rất tốt (10,6 KB/call).
- **Là lỗi vận hành:** capsule handoff = 0, ngưỡng 85% chỉ nằm trong tài liệu, không có trigger trong product (không cảnh báo, không tự nhắc, không hiển thị % context).
- **Khuyến nghị:** (i) thêm nhắc nhở/ngưỡng trong app khi phiên dài (đếm lượt tool call hoặc ước lượng token của hội thoại qua UI), (ii) dùng `task_control action=handoff` như bước chuẩn khi kết thúc mỗi task lớn, (iii) để Sol ghi capsule trước mỗi wave thay vì chỉ khi có sự cố.

---

## 3. Vấn đề 2 — Điều phối & làm việc dự án dài hơi

### 3.1 Kiến trúc durable hiện có (đã đúng hướng)

```text
runs (42) → waves (48) → events (504, append-only, hash-chained)
   └── proofs (36: command_hash + input_fingerprint + duration_ms + cache_hit)
   └── checkpoints (14: git_head + proof_fingerprint, accepted_by="ChatWeb Sol")
   └── background_operations (7)   ← workflow dài hand-off, không mất khi chat kết thúc
   └── write_fences (1)            ← khóa workspace, tránh 2 writer đè nhau
   └── handoff_capsules (0) / coordination_messages (0) / agent_lanes (0)
```

**Bằng chứng hoạt động thật (12–13/08):**
- 14 runs accepted, median **90,3 s** từ start đến khi được ChatWeb Sol chấp nhận; proof median **3,3 s**;
- 33/48 waves (68,75%) chạy `mcp_only` — bằng chứng deterministic;
- 6 waves `replanned` + 19 events `failure_observed` — control loop **có phản ứng** với lỗi thật;
- Wave-based ledger lưu `base_head` + `worktree_fp` + `contract_fp` → resume không nhầm base (bảo vệ chống "sửa nhầm thế hệ code").

### 3.2 Điểm yếu thật, có số liệu

**W1 — 28/42 runs vẫn `active`, không bao giờ đóng.** Run chỉ đóng khi accepted, không có cơ chế đóng run bị bỏ dở/đổi hướng. Hậu quả: (a) `task_control` resume sẽ liệt kê hàng loạt run "đang chạy" thật ra đã chết; (b) ledger tăng vô hạn; (c) không phân biệt được "đang chờ" và "bị bỏ quên".

**W2 — `idempotency_records` = 0 rows; `performance.json` ghi `deduplicated_calls: 0`.** Bảng dedup tồn tại (schema có sẵn) nhưng không có một request nào được ghi. Hệ quả trực tiếp với tunnel: khi ChatGPT **retry** một tool call sau khi kết nối rớt giữa chừng (vì nó không nhận được response), server chạy lại lệnh — build/test có thể chạy 2 lần, thời gian chờ nhân đôi. Đây chính là chi phí ẩn của "bị tạo lại" mà người dùng cảm nhận.

**W3 — Deep lane chưa được dùng (`agent_lanes` = 0).** Mọi delegation thật sự (2 lần) đều `blocked` đúng quy tắc (packet thiếu scope), nhưng nghĩa là các tính năng lane song song/coordination chưa có bằng chứng vận hành thật.

### 3.3 Kết luận phần 2

Điều phối dài hạn **đúng kiến trúc** (durable, hash-chained, checkpoint, replan) và **đã chạy thật** với kết quả chấp nhận được, nhưng thiếu 3 thứ để chịu được "dự án dài hơi thật sự": đóng run lifecycle (W1), idempotency hoạt động (W2), và kích hoạt capsule/lane trong vận hành thường nhật. Test suite đã xác nhận các cơ chế này *hoạt động đúng khi được gọi* (131 python + 51 node pass) — vấn đề là **không ai gọi chúng**.

---

## 4. Vấn đề 3 — Tunnel: lỗi, nội dung thiếu, bị tạo lại

### 4.1 Kiến trúc

```text
ChatGPT (web nhúng + điện thoại) ⇄ OpenAI Tunnel (control plane của OpenAI)
   ⇄ tunnel-client.exe (app chạy, tunnel ID cố định tunnel_6a76a8...)
   ⇄ MCP local 127.0.0.1:18766/mcp (Authorization Bearer)
```

- **URL tunnel ổn định** (cùng `tunnel_id` suốt 5 ngày) — "bị tạo lại" không phải URL đổi, mà là **session MCP bên trong bị tạo lại** mỗi khi tunnel client restart/control-plane rớt.
- App đã lường trước hành vi này: `transport_http.py:22` ghi thẳng — *"Tunnel clients may create a fresh MCP session for nearly every command"* → mọi session id chỉ là alias của 1 Runtime process-global (TTL 1h, cap 512 aliases), và stateless protocol `2026-07-28` cho phép mỗi request tự mang `_meta` đầy đủ, không phụ thuộc session trước đó.

### 4.2 Bằng chứng log thật trên máy (08-08 → 13-08)

**Tunnel client bị tạo lại 12 lần trong 5 ngày:**

| Thời điểm restart | Số lần |
|---|---|
| 08-08: 22:41, 22:49 | 2 |
| 08-09: 07:48, 09:09, 12:48, 14:17, 21:39, 22:57 | 6 |
| 08-10: 19:51 | 1 |
| 08-12: 21:21 | 1 |
| 08-13: 22:56, 23:09 | 2 |

Mỗi lần restart = `client_instance_id` mới = **mọi request đang bay bị mất session**. Lỗi lặp lại trong `tunnel.log` (18 WARN, 1 ERROR / 4.980 dòng):

- `WARN poll failed; backing off` / `poll timed out; backing off` — control plane OpenAI không với tới được (mạng/proxy);
- `WARN OAuth discovery failed` — lặp lại ở **mọi** lần khởi động (cảnh báo nền, không tự chết);
- `WARN response already fulfilled or unknown request` — response về sau khi người gọi đã bỏ cuộc;
- `ERROR dispatcher received unsupported channel` + `WARN failed to process polled command` — lệnh từ control plane bị bỏ.

**Phía MCP (`mcp.log`):** 12 lần traceback:

```text
File "...\server.py", line 6342, in handle_metadata_request
    self.send_json({...})
File "...\server.py", line 6991, in send_json
    self.wfile.write(body)
ConnectionAbortedError: [WinError 10053] An established connection was aborted
    by the software in your host machine
```

Đây là **bằng chứng trực tiếp của "không truyền được đầy đủ nội dung"**: server đang ghi response thì phía client (tunnel) ngắt kết nối giữa chừng → ChatGPT chỉ nhận được một phần hoặc không nhận gì → nó hiểu là lỗi → **retry/recreate** → vòng lặp mà người dùng mô tả.

### 4.3 Những gì app ĐÃ làm đúng (và test xanh chứng minh)

- Supervisor phân biệt đúng loại lỗi: `mcpRunning=true + tunnel chết` → **chỉ khởi động lại tunnel, không đụng MCP** (test: "live supervisor recovers only the tunnel and never kills a healthy MCP");
- Yêu cầu 3 lần fail liên tiếp cùng loại trước khi phục hồi (chống giật); backoff luỹ thừa 2 s → tối đa 60 s;
- MCP còn sống nhưng health check không trả lời → **hoãn restart** tối đa 6 chu kỳ để không cắt tool call đang chạy;
- Session alias + stateless protocol chống việc "session mới = mất hết state";
- Log rotate, health check riêng cho tunnel (healthPort), taskkill cả cây tiến trình.

### 4.4 Giới hạn không thể sửa từ phía app — và cần nói thẳng

1. **Hạ tầng tunnel của OpenAI** (control-plane poll, OAuth discovery) nằm ngoài app. Khi mạng/proxy của máy dao động (log cho thấy poll failed nhiều đợt), app chỉ có thể restart lại — không thể làm tunnel ổn định hơn.
2. **Giám sát từ điện thoại:** health UI của app ở `http://127.0.0.1:<healthPort>/ui` — chỉ localhost, **không có thiết kế nào** cho giám sát từ điện thoại. Những gì điện thoại thấy là ChatGPT mobile kết nối qua cùng tunnel — và nó chịu chung mọi lỗi rớt kết nối ở trên. Muốn giám sát từ xa phải có kênh riêng (ví dụ expose trạng thái qua capsule/status endpoint có xác thực) — hiện chưa có.
3. **Tool call bị ngắt giữa chừng không được tự retry:** supervisor phục hồi *kết nối*, nhưng *lượt gọi đang bay* thì mất — và vì `idempotency_records` = 0, khi ChatGPT retry thì lệnh chạy lại từ đầu (W2 ở §3.2).

### 4.5 Kết luận phần 3

Tunnel là **mắt xích yếu nhất và nằm phần lớn ngoài tầm kiểm soát**. Phần app kiểm soát được (phân loại lỗi, phục hồi chỉ-tunnel, backoff, session alias, stateless protocol) đã làm đúng và có test. Phần còn thiếu: (a) idempotency thực sự hoạt động để retry không chạy lệnh 2 lần, (b) báo trạng thái tunnel + số lần restart lên UI để người dùng biết khi nào nên đổi mạng/proxy, (c) kênh giám sát từ xa có xác thực.

---

## 5. Bảng nguyên nhân → giải pháp (xếp theo giá trị)

| # | Nguyên nhân (đã xác minh) | Giải pháp | Nơi thay đổi | Độ phức tạp |
|---|---|---|---|---|
| 1 | Handoff capsule = 0 → chat phình tới 1M token | Kích hoạt vận hành: ghi capsule sau mỗi task lớn; nhắc xoay chat ở ~85%; thêm chỉ báo "phiên dài" vào UI | prompt/skill + renderer | Thấp |
| 2 | Idempotency 0 → retry sau tunnel-drop chạy lệnh 2 lần | Ghi `idempotency_records` cho mọi `exec_command`/`agent_workflow` (key = request hash), trả kết quả cached khi trùng | `server.py` call path | Trung bình |
| 3 | WinError 10053 cắt giữa response | Bắt `ConnectionAbortedError` có chủ đích, ghi log đầy đủ (tool, request_id), đếm metric `aborted_responses`; kết hợp #2 để retry an toàn | `server.py:send_json/handle_metadata_request` | Thấp |
| 4 | 28 runs `active` không đóng | Lifecycle: đóng run sau N giờ không hoạt động với trạng thái `stale`/`superseded`; resume chỉ liệt kê run thực sự sống | `orchestration_ledger.py` | Thấp |
| 5 | Không có giám sát từ xa | Endpoint status có xác thực (token) trả trạng thái tunnel/MCP + restart count, mở qua tunnel health port hoặc một kênh riêng | `electron` + MCP control API | Trung bình |
| 6 | Không thấy trạng thái tunnel trong app | UI hiển thị: tunnel uptime, số lần restart, lần lỗi cuối, mẹo đổi proxy khi poll failed | renderer | Thấp |
| 7 | OAuth discovery failed mọi lần | Báo cáo OpenAI (hoặc bỏ qua an toàn — đã là WARN nền) + ghi lại nếu gây mất tính năng | theo dõi | Thấp |

---

## 6. Bằng chứng test (chạy lại ngày 2026-08-14)

```text
Python MCP suite:  131 passed (~44 s)  — routing/gate/budget/ledger/stateless/resilience
Node Electron suite: 51 passed (~2,7 s) — supervisor tunnel-only recovery, deferred restart,
                                          session alias, stateless HTTP, source-clean
Tổng: 182/182 green
```

Các test xác nhận **cơ chế** đúng (supervisor không giết MCP khỏe, 3-fail threshold, alias session, capsule ≤ 8 KB, gate high-cost). Các log production xác nhận **vận hành** còn hở (capsule 0, idempotency 0, runs không đóng, 12 tunnel restart). Khoảng cách giữa hai vế này chính là kết luận của báo cáo.

---

## 7. Tài liệu tham khảo

1. Nội bộ: `docs/research/260813_CODEX_WEB_BIDIRECTIONAL_RESILIENT_ORCHESTRATION.md` (ngưỡng 85% context, capsule policy).
2. Nội bộ: `docs/research/PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md` (§28.2 — field case `openai/codex#32533`: session lớn bị chặn đến khi compaction; chiến lược compact state capsule).
3. Nội bộ: `docs/research/DEPLOYMENT_PERFORMANCE_COST_EVALUATION_2026-08-14.md` (bộ số cost/latency dùng chung).
4. Liu et al., *ToolScope*, ACL 2026 (DOI 10.18653/v1/2026.acl-long.1573) — cơ sở cho 8-tool surface.
5. Log thật: `%APPDATA%\web-mcp-assistant\logs\tunnel.log` (12 restarts, 18 WARN, 1 ERROR), `mcp.log` (12 × WinError 10053), `assistant.log` (2 đợt tự khôi phục).
6. Ledger production: `.coding-tools/orchestration/ledger.sqlite3` (runs 42, waves 48, events 504, proofs 36, capsules 0, idempotency 0).
