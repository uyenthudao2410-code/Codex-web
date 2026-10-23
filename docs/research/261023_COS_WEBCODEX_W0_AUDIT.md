# W0 Audit — Tích hợp Chat On Steroids (CoS) + WebCodex vào Codex-web

- Ngày: 2026-10-23 (Asia/Saigon). Thực thi: VM-first, nghiên cứu cô lập. **Không sửa code production Codex-web, không commit/push/restart/packaged.**
- Phê duyệt của user: 18:42 23/10/2026 — "Đồng ý cho bạn xử lý đi": Muse tự xử lý chương trình theo kế hoạch, không hỏi từng bước trong phạm vi **W0 / W0.2 / W1 read-only pilot**. Các cổng riêng vẫn giữ: **KHÔNG bật `allowActions`, KHÔNG dùng worker CoS sửa source thật, KHÔNG push/package/restart production** (cổng W6).
- Thư mục nghiên cứu: `~/workspace/research/cos-webcodex/` (logs: `npm-ci.log`, `typecheck.log`, `build.log`, `control-api-tests.log`).

## 1. Ghim phiên bản nguồn (đã xác minh)

| Nguồn | SHA đã ghim | Xác minh | Ngày commit | License (đọc file thật) |
|---|---|---|---|---|
| Chat On Steroids (`totec448-spec/chat-on-steroids`, public) | `366404c1002038f055d61311f137d9701ff83b96` | GitHub API commit object + tarball codeload tại đúng SHA | 2026-10-23T06:32:33Z, merge PR #1795, tác giả Maxim | **MIT** — `LICENSE`: "Copyright (c) 2026 Chat On Steroids contributors" |
| Codex-web (`uyenthudao2410-code/Codex-web`) GitHub main | `d5f0bec6d1b0b48e0e65443228cabe957be446c8` | GitHub API `commits/main` | 2026-10-23T10:26:04Z | Repo `LICENSE` (Apache-2.0, 11.358 byte trong snapshot VM) + package `coding-tools-mcp` khai MIT — hai lớp khác nhau, giữ nguyên khi port |
| Codex-web mốc trong kế hoạch gốc | `89a164c0` | Đã cũ — là snapshot nghiệm thu r18, **không** phải main hiện tại | — | — |
| WebCodex trong kế hoạch gốc | `f2d610c9` | **Không xác minh được**: SHA này không tồn tại trong repo Codex-web (API trả lỗi), và kế hoạch không ghi owner/repo riêng cho WebCodex. Trong Codex-web, mã WebCodex là subsystem vendored (`src/`, `src/tool_runtime/`, `crates/*`) — xem mục 5. Cần chốt lại nguồn WebCodex upstream nếu muốn đối chiếu độc lập. | — | — |

### Cách lấy CoS về VM (ghi rõ theo yêu cầu)

1. `git clone https://github.com/totec448-spec/chat-on-steroids.git` — **THẤT BẠI**: `fetch-pack: unexpected disconnect while reading sideband packet` sau ~120s (đường truyền/proxy VM), không tạo được thư mục.
2. Tarball codeload tại SHA ghim — **THÀNH CÔNG**: `https://codeload.github.com/totec448-spec/chat-on-steroids/tar.gz/366404c1002038f055d61311f137d9701ff83b96` (68 MB gzip), giải nén vào `~/workspace/research/cos-webcodex/chat-on-steroids` với `--strip-components=1`. Hệ quả: **không có `.git`/history** trong bản nghiên cứu (chấp nhận được cho W0 audit; nếu W1 cần history thì clone lại trên Windows/svhome nơi mạng ổn định hơn).

### CoS snapshot — số liệu thật

- Kích thước sau giải nén: **109 MB, 1.575 file** (chưa gồm `node_modules`).
- `package.json`: name `chat-on-steroids`, **version 2.1.45**, license MIT, `main: out/main/index.js`.
- Scripts chính: `dev`/`build` = `electron-vite`, `typecheck` = `tsc --noEmit`, `test` = `vitest run`, `verify:ci` = rg + privacy + notices + typecheck + vitest (loại trừ rồi chạy riêng `computer`/`mcp-shutdown`).
- Dependencies runtime đáng chú ý: **CodeMirror 6** (`codemirror`, `@codemirror/state 6.7.6`, `@codemirror/merge 6.12.2`, `@codemirror/language(-data)`, `@lezer/highlight`), `@xterm/xterm 6.0.0` + `node-pty`, `@modelcontextprotocol/{client,node,server} ^2`, `marked 18`, `katex`, `pdfjs-dist ^6`, `tree-sitter 0.25.1`, `quickjs-emscripten`, `sharp`, `koffi` (FFI native), `ws`, `zod ^4`.
- DevDependencies: **Electron 44.3.0** (Codex-web đang dùng 43.2.0 — lệch major, cần lưu ý khi port), `electron-vite ^5`, **Vite ^7.3.6**, `typescript ^7.0.2`, `vitest ^5`.
- `THIRD-PARTY-NOTICES.txt` ~10,5 MB — khi port bất kỳ module nào phải mang theo notice tương ứng.

## 2. Kết quả build/chạy thử trên VM Linux

| Bước | Lệnh | Kết quả |
|---|---|---|
| Cài deps | `npm ci --no-audit --no-fund` (TMPDIR chuyển khỏi `/tmp` 512 MB) | **PASS** — 534 packages, ~69s, exit 0 |
| Typecheck | `npm run typecheck` (`tsc --noEmit`) | **PASS** — exit 0 |
| Build | `npm run build` (`electron-vite build`) | **PASS** — `out/{main,preload,renderer}` sinh đầy đủ, build ~18s, exit 0 |
| Test Control API | `vitest run` 5 file `test/control-api*.test.ts` | **PASS — 155/155 tests, 5/5 files**, ~20s |

Giới hạn trung thực:

- **Chưa chạy Electron GUI / extension trên VM** (VM headless, không có Chrome/ChatGPT session) — đúng giới hạn kế hoạch dự kiến; phần này thuộc W0.2 trên Windows.
- Tuy nhiên 155 test trên **là receipt giao thức thật ở mức headless**: `test/control-api.test.ts` mock Electron tối thiểu, khởi động listener thật qua loopback HTTP (`startControlApi()`), đọc `endpoint.json` + `token` từ userData tạm và gọi `GET /v1/health` cùng các route khác bằng HTTP thật. Như vậy *listener + auth + routing + projection* đã được chứng minh chạy được ngoài GUI; thứ chưa chứng minh là *dữ liệu phiên thật* do app CoS đầy đủ ghi ra (cần app + extension + ChatGPT).
- Chưa chạy toàn bộ test suite CoS (chỉ chạy focused 5 file Control API — đúng nguyên tắc validate-chỉ-phần-liên-quan của AGENTS.md).

## 3. Control API — đã xác minh từ source (không phải từ kế hoạch)

Nguồn: `src/shared/control-api.ts` (401 dòng, wire contract), `src/main/control-api.ts` (549 dòng, listener), `src/main/control-reads.ts` (566), `src/main/control-actions.ts` (277), `src/main/control-workers.ts` (120), `src/main/control-stream.ts`, `src/main/config.ts`.

### Cơ chế bật / auth / transport

- **Mặc định TẮT cả hai công tắc**: `DEFAULT_CONTROL_API = { enabled: false, allowActions: false }` (`config.ts:295`). Bật listener cần `controlApi.enabled=true`; hành động cần thêm `controlApi.allowActions=true` (và transform ép `allowActions=false` nếu `enabled=false`).
- Listener: HTTP trên **`127.0.0.1`, cổng ephemeral** (`listen(0)`) — **không có cổng cố định**. Discovery qua file `userData/control-api/endpoint.json` (`{protocol, port, pid, appVersion, startedAt}`, protocol = **1**); token tại `userData/control-api/token`.
- **Token**: random 32 byte base64url, sinh mới mỗi lần khởi động listener, ghi file mode `0600`, **không bao giờ được cấp qua HTTP** — caller phải đọc được userData của chính user đó. Kiểm tra bằng `Authorization: Bearer <token>` + `timingSafeEqual`.
- Chống lạm dụng từ trình duyệt: request có header `Origin` → 403; `Host` phải đúng `127.0.0.1:<port>`/`localhost:<port>` (chống DNS rebinding); rate limit đọc 600/phút, action 30/phút (tính **sau** auth); GET có body → 413; tối đa 8 read chưa xong, 4 action chờ, deadline đọc 15s, deadline action 20s.
- Mọi response là **allowlist projection** từ owner có sẵn; các trường chứa secret (MCP path token, tunnel id, plugin source/config) bị loại theo thiết kế và có test bảo vệ.

### Endpoint thật

Đọc (GET — chỉ cần `enabled`):

| Method + path | Ghi chú xác minh |
|---|---|
| `GET /v1/health` | Trả `protocol`, toàn bộ `routes`, `actions.enabled` + action routes, pid, version, uptime |
| `GET /v1/status` | Connection/bridge/plugins/update/toolCalls — projection có redact |
| `GET /v1/sessions` | Phân trang bằng `cursor`, kèm `activeId` |
| `GET /v1/sessions/{id}` | Chi tiết; `?live=1` mới kèm khối `live` (turn đang chạy, goal/loop, recovery, job Compact&Resume) |
| `GET /v1/sessions/{id}/events` | Phân trang theo `position`/`from` (`seq`), lọc `kinds` |
| `GET /v1/sessions/{id}/events/stream` | SSE, tối đa 4 stream, heartbeat 15s, sống tối đa 30 phút, resume bằng `Last-Event-ID` |
| `GET /v1/inputs` | Outbox: mỗi dòng có `delivery ∈ {sent, not_sent, unconfirmed, pending}` — bằng chứng gửi, không suy từ thời gian |
| `GET /v1/agents` | Trạng thái swarm (prime/worker) dạng projection |
| `GET /v1/log` | Ring log hoạt động đã redact |
| `GET /v1/models` | Catalog model ChatGPT đã đọc từ picker (chỉ đọc bản đã lưu, không mở trang) |

Action (POST — cần `enabled && allowActions`, nếu không mọi action route trả cùng một 403 `actions_disabled` trước khi đọc body):

| Method + path | Ghi chú |
|---|---|
| `POST /v1/inputs` | Gửi tin nhắn; `id` do caller cấp (UUID lowercase) chính là outbox id — gửi lặp cùng id trả lại dòng cũ (`replayed: true`), không gửi hai lần. Không có `sessionId` = mở chat mới. Body zod strict, text ≤ 64.000 ký tự |
| `POST /v1/inputs/{id}/cancel` | Chỉ hủy được khi delivery proof còn là `pending`; đã có thể đã gửi → 409, không báo "đã hủy" giả |
| `POST /v1/sessions/{id}/stop` | Bắt buộc `turnId` khớp `live.activeTurnId`; 202 = *đã yêu cầu* stop, proof là `turn_end` được ghi sau đó |
| `POST /v1/workers/{ownerId}/spawn` · `/message` · `/ack` | Qua broker worker hiện hữu; spawn tối đa 8 worker/lần; cần thêm `multiAgent.enabled` và capability command+create+edit |

Worker read — **ngoại lệ quan trọng** (xem sai lệch S1):

| Method + path | Điều kiện thật |
|---|---|
| `GET /v1/workers/{ownerId}` | Trạng thái worker theo owner (UUID) |
| `GET /v1/workers/{ownerId}/reports` | Báo cáo worker; phải ack bằng action route mới coi là đã nhận |

Cả hai route GET worker đều đi qua `enabled()` trong `control-workers.ts`, hàm này **ném 403 `actions_disabled` nếu `allowActions` đang tắt** (và 403 `workers_disabled` nếu multiAgent tắt) — dù là GET.

## 4. Ma trận module CoS — reuse / adapt / port / defer

| Module (đường dẫn thật, số dòng) | Chiến lược | Lý do (đối chiếu đề xuất của user) |
|---|---|---|
| Control API (`main/control-api.ts` + `shared/control-api.ts` + reads/stream) | **Reuse qua adapter** (W1) | Đúng đề xuất. Giao thức đã hoàn chỉnh, có 155 test; chỉ viết client mỏng phía Codex-web |
| `renderer/unified-diff.ts` (66 dòng) | **Port chọn lọc** | Đúng đề xuất. Nhỏ, cô lập; phụ thuộc CodeMirror merge/state + lezer — mang theo deps đó, không kéo cả file panel |
| `renderer/file-panel.ts` (1.728 dòng) | **Port giao diện, giữ backend Codex-web** | Đúng đề xuất. UI phụ thuộc `shared/project-files`/`project-git` của CoS — phải map sang `electron/services/workHubFiles.js`, không port backend file của CoS |
| `renderer/agent-panel.ts` (279) + `agent-activity.ts` (133) + `agent-plan.ts` (81) | **Port giao diện + activity projection** | Đúng đề xuất. Nhỏ và tách bạch; dữ liệu thật lấy từ EOCL/`workHubCoordination.js`, nhãn phân biệt worker CoS / Codex / EOCL |
| `renderer/chat.ts` (9.291 dòng, 522 KB, 72 import) | **Defer — tách thành phần khi W2.3** | Đúng đề xuất "không copy nguyên". Phụ thuộc recorder/extension/i18n/skills/terminal…; chỉ tách shell/timeline/composer theo adapter |
| `main/goal.ts` (3.145 dòng) | **Adapt ý tưởng, không chạy engine** | Đúng đề xuất. Cơ chế đáng học: helper model đánh giá "chưa hoàn tất" + 1 draft/chat chống gửi trùng. Lưu ý: bản CoS gọi **OpenRouter** bằng API key riêng — không đưa key/cơ chế này vào Codex-web; dispatch vẫn qua EOCL + `goal_pursuit.py`/`goal_continuation_ledger.py` |
| `main/agents.ts` (5.754 dòng) | **Defer (chỉ tham khảo contract)** | Broker worker của CoS có quyền command/edit/create riêng — chạy song song sẽ tạo authority thứ hai. Chỉ dùng Worker Board UI + read model |
| `main/session/continuation.ts` (1.946 dòng) | **Adapt state/logic** | Đúng đề xuất và là phần đáng học nhất: transaction open→summary→claim→commit/abort, commit 3 pha (preflight/durable/publish), trạng thái gửi `not-attempted / attempted-unresolved / dispatched-unresolved / sent` khớp gần 1-1 với delivery proof của Control API — map sang capsule/receipt của Codex-web ở W4 |
| `extension/` (MV3, ~30.000 dòng JS; `content.js` 14.532 dòng, `background.js` 5.938) | **Defer — thử độc lập ở W0.2/W3-A** | Đúng đề xuất. Permissions thật (mục 6) rộng và dựa DOM ChatGPT — rủi ro ToS/độ ổn định, không phải phụ thuộc bắt buộc |

## 5. Phía WebCodex trong Codex-web — kiểm tra tồn tại thật

Đã kiểm tra snapshot VM `~/workspace/projects/Codex-web` tại `src/tool_runtime/` và `crates/webcodex-core/src/`:

| Hạng mục kế hoạch §8 kỳ vọng | Tồn tại tại đường dẫn nêu? | Thực tế trong Codex-web |
|---|---|---|
| `src/tool_runtime/job_input.rs` | **KHÔNG** | Không có file này ở cả `src/tool_runtime/` lẫn `crates/webcodex-core/src/`. Tương đương gần nhất: `src/tool_runtime/jobs.rs` (2.636 dòng) + `job_tools.rs` + `registry/input_schemas/jobs.rs` (`run_job_input_schema`). Contract `input_id` + typed receipt + outcome-unknown cho **interactive job input chưa có** — đây đúng là việc phải port ở W5, không phải đã sẵn |
| `crates/webcodex-core/src/job_input.rs` | **KHÔNG** | `crates/webcodex-core/src/` chỉ có 10 file (lib, source_snapshot, shell_protocol, lsp_bridge, validation_bridge, artifact_policy, sensitive_paths, compute_placement, apply_edits_shared, build_info) |
| `src/tool_runtime/git_review.rs` | **KHÔNG** | Tương đương: `src/tool_runtime/git.rs` (3.014 dòng) + `git_tools.rs` (69 dòng, lớp tool mỏng). Phân tích committed-range/rename/subsystem theo kiểu WebCodex upstream **chưa tách thành module review riêng** |
| `src/tool_runtime/browser_tools.rs` | **KHÔNG** | Không có browser tool nào trong Rust `tool_runtime`. Năng lực browser hiện ở JS: `electron/services/workHubBrowserQa.js` + `renderer/browser.js` (Browser QA) — khác hẳn mô hình CDP session/profile/element-generation của upstream |
| `src/tool_runtime/computer_tools/` | **KHÔNG** | Không tồn tại thư mục/file computer-use nào trong toàn repo (ngoài docs). M3.2 Windows UIA vẫn là hạng mục chưa làm — khớp MEMORY |
| `src/tool_runtime/skills.rs` | **KHÔNG** | Không có `skills.rs`. "Skills" hiện chỉ xuất hiện rời rạc phía Python MCP (`codex_bridge.py` có nhắc) — chưa có resolver/consumer lifecycle trong Rust |

Kết luận mục 5: cả 5 đường dẫn trong kế hoạch §8 đều là **đường dẫn của repo WebCodex upstream riêng**, không phải của Codex-web hiện tại. W5 vì vậy là *port contract* thật sự (sang Python MCP hoặc Rust subsystem hiện có), không phải "kích hoạt lại file đã có". Đồng thời các điểm neo W3 của kế hoạch đã kiểm chứng **có thật**: `electron/services/codexDesktopConfig.js`, `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py`, `hub_proxy_stdio.py`, `goal_pursuit.py`, `goal_continuation_ledger.py`, và các đích port W1/W2 `electron/services/workHubFiles.js`, `workHubCoordination.js`, `renderer/work-hub.js`, `renderer/work-hub-store.js` đều tồn tại.

## 6. Extension — permissions thật (từ `extension/manifest.json`)

- Manifest V3, version 2.1.45, `minimum_chrome_version 125`.
- `permissions`: `storage`, `scripting`, `alarms`, **`debugger`**, `tabs`, `tabGroups`; `optional_permissions`: `cookies`.
- `host_permissions`: `http://*/*`, `https://*/*` (rất rộng), cộng `chatgpt.com`/`chat.openai.com` và dải localhost bridge `8765–8769 / 18765–18769 / 38765–38769`.
- Content scripts chạy trên `chatgpt.com` + `chat.openai.com`, gồm script ở **MAIN world** (`fiber.js` đọc React fiber, `usage.js` từ `document_start`).
- Đánh giá: đúng như kế hoạch cảnh báo — quyền rộng + bám DOM/fiber của ChatGPT. Chỉ thử trên profile Chrome/Edge tách riêng, không cài vào profile production ở W0.2 nếu user chưa đồng ý cụ thể cho việc cài extension.

## 7. Sai lệch so với kế hoạch gốc (phải ghi rõ)

- **S1 — Worker read KHÔNG phải read-only thuần.** Kế hoạch §3 bước 0.2 và bảng §5 ngầm định `GET /v1/workers/{ownerId}` xem được khi chỉ bật đọc. Source thật: cả GET worker và GET reports đều qua gate `allowActions && multiAgent.enabled` (`control-workers.ts`). Hệ quả cho W1: ở chế độ read-only thuần, Work Hub **không** xem được worker qua Control API; muốn xem phải bật `allowActions` (mở luôn cả POST inputs/spawn) — cần quyết định riêng, hoặc W1 chỉ hiển thị worker từ EOCL như kế hoạch W2.2 vốn đã định. Đề xuất: giữ read-only thuần ở P0, worker CoS để defer.
- **S2 — Không có cổng cố định.** Kế hoạch không nói port; thực tế port là ephemeral và phải discover qua `endpoint.json`. Adapter W1 phải đọc endpoint file (hoặc cấu hình thư mục userData của CoS), không hardcode port.
- **S3 — Kế hoạch thiếu 4 route đọc đã có sẵn**: `GET /v1/inputs` (outbox + delivery proof — rất quan trọng cho reconcile W3-A bước 5), `GET /v1/agents`, `GET /v1/log`, `GET /v1/models`. Tin tốt: kho contract đầy đủ hơn kế hoạch mô tả.
- **S4 — Action surface đầy đủ hơn bảng §3**: ngoài `POST /v1/inputs` còn có cancel, stop (theo `turnId`), và 3 worker action. Vẫn giữ OFF toàn bộ ở P0 theo cổng phê duyệt.
- **S5 — SHA WebCodex `f2d610c9` không kiểm chứng được** trong repo Codex-web và kế hoạch không ghi repo chứa nó (mục 1). Mọi tham chiếu "WebCodex upstream" ở W5 cần chốt lại repo + SHA trước khi port.
- **S6 — Lệch phiên bản nền**: CoS dùng Electron 44 / TypeScript 7 / Vite 7; Codex-web dùng Electron 43.2. Port UI phải kiểm tra tương thích, không giả định copy thẳng chạy ngay.
- Khớp với kế hoạch (không sai lệch): API mặc định tắt; `allowActions` là công tắc thứ hai riêng; endpoint health/status/sessions/events/stream tồn tại đúng như mô tả; nguyên tắc không fork-nguyên, không hai authority/ledger được source xác nhận là khả thi (Control API tự nó "owns no fact", chỉ projection).

## 8. Điều kiện hoàn tất W0 — còn thiếu gì

Đã đạt: ghim SHA + license + deps cả hai phía; ma trận module có lý do; build upstream **PASS** (ci + typecheck + build); Control API contract xác minh từ source + 155 test headless PASS (gồm HTTP thật tới `/v1/health`).

Còn thiếu (thuộc W0.2, không phải thiếu sót của W0):

1. **Receipt đọc phiên thật**: chạy app CoS đầy đủ + extension trên máy thật, bật `controlApi.enabled` (chỉ đọc), đọc `sessions`/`events` của một phiên và lưu receipt. Trên VM không làm được (không GUI/Chrome/ChatGPT session).
2. Chốt repo + SHA cho WebCodex upstream (S5) nếu W5 cần đối chiếu ngoài phần đã vendored.
3. Quyết định về S1 (worker read) — đề xuất đã nêu, chốt ở W1 kickoff.

## 9. Đề xuất W0.2 cụ thể

- **Chạy ở đâu**: Windows (máy có GUI + Chrome/Edge thật), trong profile trình duyệt thử nghiệm tách riêng; CoS chạy từ bản build tại SHA `366404c1` này (hoặc bản phát hành chính thức đúng version 2.1.45 — ghi rõ dùng bản nào khi chạy).
- **Các bước**: (1) bật duy nhất `controlApi.enabled=true`, giữ `allowActions=false`; (2) tạo một **hội thoại TEST tự tạo** (được phê duyệt 18:42 cho phép dùng phiên test tự tạo, không cần dữ liệu thật của user) và thực hiện `GET /v1/health` → `/v1/status` → `/v1/sessions` → `/v1/sessions/{id}/events` bằng token trong `endpoint.json`/`token`; (3) lưu receipt (request/response đã redact token) vào thư mục nghiên cứu; (4) thử ngắt CoS giữa chừng để xác nhận hành vi stale/disconnect phía client.
- **Cần user chỉ định riêng**: một hội thoại **ChatGPT thật** của user để liên kết thử (phiên test tự tạo không thay thế được mốc P0). Việc cài extension vào profile chứa tài khoản thật cũng cần user xác nhận tại thời điểm làm, dù phê duyệt 18:42 đã bao phủ phạm vi read-only pilot nói chung.
- **Không làm ở W0.2**: không bật `allowActions`, không POST input, không spawn worker CoS, không đụng runtime production Codex-web.
