# Tools-Codex-web — Phân tích hoạt động hệ thống, phối hợp tự động, hiệu năng và chi phí

**Ngày thu thập:** 2026-08-15 (cửa sổ quan sát ~03:33–05:00 UTC)  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main` — **HEAD quan sát:** `dff81e251836666fc825c40bf86e4167afd29c39`  
**App:** web-mcp-assistant 0.3.4 · **MCP runtime:** 0.4.3 · **PerformanceTrace:** v5 · **Smart-v3:** 8 tools  
**Nguồn bằng chứng:** `.coding-tools/orchestration/ledger.sqlite3` (canonical), `.coding-tools/performance.json`, `.coding-tools/task-history.json`  
**Cảnh báo phương pháp:** tất cả số liệu là snapshot tại thời điểm capture; window 08-15 là ngày chưa kết thúc nên số thấp là bình thường. Credits CODEX là **ước tính nội bộ** theo rate card quan sát 2026-08-12, không phải hóa đơn provider. Chi phí opencode là **provider-reported (đo thực)**.

---

# 1. Trả lời trực tiếp câu hỏi: "Chỉ có chatweb hoạt động?"

**Nhận định của bạn gần đúng, nhưng có sắc thái quan trọng.**

## 1.1 Chatweb là bộ não + đôi tay chính

```text
waves theo execution_mode:
  mcp_only           87.4%   (38 + 234 + 52 = 324 / 373 waves)
  deep_single_lane    5.6%   (21)
  auto                4.6%   (17)
  bounded_candidate   3.2%   (12)
```

`mcp_only` nghĩa là: **mô hình của chatweb tự thực thi công việc trực tiếp qua 8 tool MCP**, không đi qua lane/delegation nào. Hơn 87% waves được xử lý kiểu này. Vì vậy cảm giác "chỉ có chatweb làm việc" là **chính xác về mặt phân công thực thi**.

## 1.2 Nhưng codex và opencode không "không chạy" — chúng chạy ở vai khác

| Client | Vai | Kết nối | Lần thấy gần nhất | Hoạt động thực tế |
|---|---|---|---|---|
| `chatweb` (openai-mcp) | **controller** | 08-14 05:50 | 08-15 03:53 | Liên tục; tự thực thi 87% waves; tạo mọi lane, delegation, capsule |
| `codex-desktop` | worker | 08-14 05:54 | 08-15 02:13 | Nhận 27 delegation đề xuất ứng viên; 6 chấp nhận, 21 bị chặn; 13 lane benchmark đã chạy rồi đóng |
| `opencode` | worker | 08-14 12:50 | 08-15 03:53 (vẫn đang chạy) | Provider adapter hoạt động end-to-end; **17 delegation hôm nay, 16 completed, chi phí đo thực**; đang chạy chính phiên hiện tại |
| `electron-panel` | supervisor | 08-14 12:49 | 08-14 12:50 | Canary kiểm tra execution-hub provider |

Kết luận: **codex có chạy** — nó được gọi làm "candidate proposer" và "benchmark reviewer" — nhưng **gần như chưa tạo accepted work**: 0 delegation nào được trao quyền ghi (`authoritative_write=false` ở toàn bộ 28 bản ghi). **opencode mới là worker đang tăng trưởng thật sự**: từ 08-14 chỉ 1 call đọc flash, đến hôm nay 16 call deepseek-v4-pro completed với chi phí đo thực — phiên làm việc này chính là opencode.

---

# 2. Tiến trình phối hợp tự động (coordination) — đang ở đâu?

## 2.1 Những gì đã HOẠT ĐỘNG THẬT (không phải benchmark)

```text
run_started                    258   (08-13: 50, 08-14: 180, 08-15: 37)
waves                          373   (56 / 263 / 54)
state_transition             1,556
write_lease acquired/revoked   274   (mỗi chiều)
proof_recorded                 289   — proofs: 253 PASSED, 48 FAILED
idempotency_records            603   — current-policy 44/44 = 100% keyed
wave_replanned                 103
run_stale_reconciled            39 + wave_lifecycle_reconciled 40
background_operations          309   (308 completed, 1 timed_out)
handoff_capsules                 5   (active, có sha256)
controller_transferred           4   (2 vòng chatweb -> codex-desktop -> chatweb, fencing token hợp lệ)
```

Đây là bằng chứng một **control plane hoạt động thật**: lease được cấp và thu hồi đầy đủ, proof có pass/fail thật, replan xảy ra khi failure, stale run được reconcile, idempotency current-policy đạt 100% trên 44 call required.

## 2.2 Delegation tới codex: cơ chế chạy, nhưng đầu ra còn mỏng

```text
28 delegation (28 lần dispatch model):
  blocked               21
  accepted_candidate     6   (mini 4, luna 3... tổng 7 dòng đã dispatch)
  completed (opencode)  16 + 1 active (hôm nay, đang tăng)
```

**Nguyên nhân 21 lần bị chặn (codex):**

| Lý do | Số lần | Diễn giải |
|---|---:|---|
| `candidate_model_not_completed` | 9 | Timeout 25–30s khi gọi model qua codex app server bridge (chủ yếu sol/terra) |
| `PROMPT_TOO_LARGE` | 6 | Prompt vượt giới hạn khi đóng gói scope cho candidate |
| `candidate_scope_missing` | 3 | Không đóng gói được scope candidate (gọi auto/sol mà không có scope) |
| `candidate_reported_blocked` | 2 | Model candidate tự báo blocked |
| `CANDIDATE_TARGET_MISSING` | 1 | Thiếu target patch |

Điểm đáng chú ý: **các lần bị chặn hầu như không tốn chi phí model** (economics null ở hầu hết lần blocked muộn — chỉ các lần timeout là có chi phí ước tính vì đã dispatch thật).

## 2.3 Kênh messaging giữa chatweb ↔ codex: TẠO RA NHƯNG CHƯA AI DÙNG

```text
coordination_messages: 38 bản ghi — 14 chatweb_to_codex, 12 codex_to_chatweb, 12 system
status: TẤT CẢ = pending (acknowledged = 0)
```

Toàn bộ kênh nhắn tin bền vững (coordination messages) chưa có một tin nào được tiêu thụ. Liên lạc thực tế đi qua **lane state + capsule + bridge status** chứ không qua message queue. Đây là dấu hiệu: infrastructure đi trước, workflow thật đi sau.

## 2.4 Handoff (bàn giao giữa agent): 5 capsule, mang tính thử nghiệm

- Capsule P1 handoff shadow (08-14 02:22) — probe resume fresh lane, có acceptance rõ.
- Capsule execution-hub continuity canary (08-14 06:11) — kiểm tra đọc capsule qua thin-proxy codex-desktop.
- Capsule "new-machine-live" (08-14 12:00) — chấp nhận chuyển controller sang máy mới, kèm bằng chứng controller_transferred.

Tất cả còn là **probe/canary** — chưa có workload dài nào thực sự dựa vào handoff để resume. 13 agent lane đều `closed` (không còn lane active tồn đọng — tốt về hygiene).

## 2.5 Chấm điểm trưởng thành phối hợp

| Trục | Trạng thái | Đánh giá |
|---|---|---|
| Controller-centric execution (EOCL) | **LIVE** | 87% waves, lease/proof/accept đầy đủ |
| Delegation tới codex app server | **HỎNG MỘT NỬA ĐƯỜNG** | Cơ chế lane/bridge chạy; 75% delegation bị chặn; 0 quyền ghi |
| Provider adapter (opencode) | **LIVE & ĐO ĐƯỢC** | Đang là con đường delegation khỏe nhất, read-only enforced, cost đo thực |
| Coordination messaging | **CHẾT (chưa khai tử)** | 38/38 pending |
| Handoff/capsule | **PROBE** | Đúng mechanic, chưa có workload chứng minh ROI |
| Routing tự động | **HOLD cố ý** | `automatic_activation=false`; auto chỉ 4.6% waves |

**Kết luận trung thực:** phối hợp tự động mới ở mức **"controller + durable state machine + delegation thí điểm"**. Nó chưa phải multi-agent orchestration thật sự: chưa có vòng lặp chatweb giao việc → codex làm → chatweb nghiệm thu đều đặn. Điều này **khớp đúng thiết kế thận trọng** trong tài liệu đánh giá trước (routing HOLD, candidate-only, fail-closed) — nhưng cũng nghĩa là phối hợp tự động hiện là **điểm yếu nhất về giá trị thực dụng**, không phải về an toàn.

---

# 3. Hiệu năng / hiệu suất

Số liệu `performance.json` v5, tổng tích lũy qua 3015 tool call:

```text
tool_calls                3,015
errors                      239   (~7.9%)
local_execution_ms   6,172,921   ≈ 1.71 giờ chạy cục bộ
estimated_wait_ms   54,434,307   ≈ 15.12 giờ chờ model (wait ước tính)
request_bytes        4,410,877   ≈ 4.4 MB
response_bytes      92,664,183   ≈ 92.7 MB (trước khi cắt gọn)
model_visible_bytes  8,022,740   ≈ 8.0 MB thực sự đưa vào context
```

## 3.1 Phân bổ thời gian

```text
phase_timing (50 samples):  workspace 11.4s | localization 64.5s | materialization 0.7s
```

- **Tỷ lệ wait/exec ≈ 8.8 : 1** — thời gian mất đi nằm ở việc model chờ kết quả tool, không phải tool chạy chậm.
- 64.5s localization cho 50 samples là pha tốn thời gian nhất của harness (không tính model).

## 3.2 Semantic localization: chưa từng chạy LSP

```text
localization_queries      275
fallback_search_queries   275   (100% text fallback)
lsp_attempted_queries       0
lsp_handled_queries         0
```

Khớp với trạng thái `NATIVE_LSP_BINDING_NOT_CONFIGURED`. Mọi navigation đang đi qua tìm kiếm text — đúng fail-closed, nhưng đây là **chi phí hiệu năng thực**: localization chiếm phần lớn 64.5s/pha.

## 3.3 Error rate và proof

```text
errors 239 / 3015 calls ≈ 7.9%
phân lớp: VALIDATION 34 | RUNTIME 9 | AUTHORITY_DENIED 8 | UNKNOWN 4 | IDEMPOTENCY 1 (56 đã phân lớp, còn lại ~183 thuộc lớp client/timeout không nằm bucket này)
proofs: 253 passed / 48 failed
```

7.9% error là cao cần chú ý nhưng phần lớn nằm ở chu kỳ phát triển/kiểm thử của chính dự án (nhiều run là thử nghiệm), không phải lỗi production steady-state.

## 3.4 Cache & tăng tốc

```text
proof_cache: 96 eligible | 1 hit | 999 ms saved        -> HOLD (đúng quyết định)
result_tail:  7 samples | 0 truncation                 -> chưa có workload dùng continuation
idempotency:  current-policy 44/44 = 100% keyed | optional keyed 26/459
```

---

# 4. Chi phí

## 4.1 Chi phí ĐO THỰC (provider-reported) — opencode

```text
opencode-go/deepseek-v4-flash:  $0.00034   (1 call, 4,753 in / 56 out)
opencode-go/deepseek-v4-pro:    ~$0.057    (19 usage_event, call lớn nhất $0.0408 cho 85,606 in / 402 out / 3,592 reasoning)
tổng đo thực ≈ $0.058 (và đang tăng vì phiên hiện tại vẫn chạy)
```

Đây là **một trong những bằng chứng chi phí tốt nhất hệ thống có**: mỗi model call qua opencode được ghi usage_event với tokens, cache hit và cost do provider báo — không ước tính.

## 4.2 Chi phí ƯỚC TÍNH nội bộ (không phải hóa đơn) — codex

```text
13 lần dispatch model thật qua codex (rate card quan sát 2026-08-12):
  tổng ≈ 4.21 estimated credits
  gpt-5.6-sol  1.96 | gpt-5.4-mini 0.97 | gpt-5.6-luna 0.88 | gpt-5.6-terra 0.41
Lane benchmark (last turn): sol xhigh tới 2.13, terra tới 1.26 credits/turn
```

Phần lớn tiền codex đã "bay" vào các lần **dispatch bị timeout** (9 lần `candidate_model_not_completed` sau 25–30s vẫn có economics) và benchmark — tức là chi phí đã chi mà **không ra accepted work**.

## 4.3 Điểm mù chi phí lớn nhất: CHÍNH CHATWEB

Chatweb là tác nhân thực thi 87% waves và mọi run điều phối, nhưng **không có một usage_event nào cho model của chatweb**. Toàn bộ token mà "công nhân chính" tiêu thụ **không được đo trong ledger**. Nghĩa là con số chi phí thực của dự án có thể gấp nhiều lần ~$0.06 + ~4.21 credits — và hệ thống hiện không có cách nào biết chính xác.

---

# 5. So sánh 3 hệ thống: ai thực sự tạo ra giá trị?

| Hệ thống | Số lượng công việc | Chất lượng đóng góp | Chi phí | Nhận xét |
|---|---|---|---|---|
| **chatweb** | 87% waves, 258 run điều phối | Tạo toàn bộ accepted work, commit hàng ngày | **KHÔNG ĐO ĐƯỢC** | Là hệ thống duy nhất tạo ra sản phẩm thật |
| **codex** | 28 delegation + 13 lane | 6 accepted_candidate; 0 accepted work có quyền ghi | ~4.2 credits ước tính, phần lớn vào timeout | Cơ chế tốt nhưng đang là "consultant bị chặn" |
| **opencode** | 17 delegation hôm nay (đang tăng) | Đang thực thi phiên hiện tại, read-only + write qua controller | ~$0.06 đo thực | Worker tích hợp khỏe nhất về đo lường |

---

# 6. Vấn đề cần giải quyết (theo mức độ)

## P0 — Codex delegation chết 75%

Ba nhóm nguyên nhân:
1. **Timeout 25–30s** trên codex app server bridge cho sol/terra/xhigh (9/28) — cần điều tra bridge latency/queue, hoặc tăng deadline có kiểm soát, hoặc giảm workload cho candidate.
2. **PROMPT_TOO_LARGE** (6/28) — budget đóng gói scope candidate quá nhỏ so với scope thực; cần làm scope packing đúng mức hoặc cắt bớt context đóng gói.
3. **candidate_scope_missing** (3/28) — lỗi bên gọi: route auto/sol được yêu cầu mà không có scope kèm theo.

Khuyến nghị: fix theo thứ tự 3 → 2 → 1 (rẻ nhất trước). Sau mỗi fix, đo lại tỷ lệ accepted_candidate trên delegation thật (không phải benchmark).

## P1 — Kênh coordination_messages: dùng hoặc xóa

38 tin pending vĩnh viễn. Hoặc nối vào workflow handoff thật, hoặc demote/remove để giảm "state chết" trong kiến trúc. Không giữ machinery không ai tiêu thụ.

## P1 — Đo chi phí chatweb

Chatweb nên được ghi usage tương tự opencode (ít nhất là ước tính từ provider dashboard nếu không lấy được API usage). Đây là điều kiện để mọi quyết định kinh tế về routing (giữ chatweb tự làm hay thuê codex/opencode) có cơ sở.

## P2 — Semantic live

275/275 localization query phải dùng text fallback. Kích hoạt Rust Connector (theo đúng checklist trong tài liệu đánh giá P1 wave S0) là con đường cắt 64.5s localization/pha.

## P2 — Error 7.9%

Phân lớp nốt ~183 error không nằm trong bucket để biết bao nhiêu là do thử nghiệm vs. lỗi thật.

---

# 7. Kết luận ngắn

1. **Cảm giác của bạn là có cơ sở:** chatweb thực thi 87% công việc và là nguồn accepted work duy nhất. Codex chỉ đóng vai candidate/benchmark, 75% delegation bị chặn, chưa bao giờ được trao quyền ghi. Opencode đang là worker phụ hoạt động thật và đo lường tốt nhất.
2. **Phối hợp tự động đã có bộ xương hoàn chỉnh** (EOCL, lease, proof, idempotency 100%, replan, reconcile, handoff capsule, controller transfer) nhưng **chưa có "vòng lặp sản xuất"**: delegation → accepted work còn gần bằng 0 ngoài chatweb.
3. **Hiệu năng:** wait/exec 8.8:1; bottleneck lớn nhất là model wait và semantic fallback (0 query LSP).
4. **Chi phí:** đo thực opencode ~$0.06; ước tính codex ~4.2 credits (phần lớn vào timeout vô ích); **chi phí chatweb hoàn toàn không đo được** — đây là điểm mù quan trọng nhất.
5. **Khuyến nghị ưu tiên:** sửa 3 lỗi chặn delegation codex → nối hoặc xóa coordination_messages → đo usage chatweb → kích hoạt semantic. Không cần thêm tính năng mới.

> Dữ liệu đầy đủ (bảng events theo ngày, delegation chi tiết, lane economics, usage_event) nằm trong `.coding-tools/orchestration/ledger.sqlite3` — có thể tái lập toàn bộ phân tích trên bằng các truy vấn đính kèm.

## Appendix — Các số liệu nền

```text
runs:   08-13: 50 (15 accepted, 35 stale) | 08-14: 180 (106 accepted, 48 active, 17 aborted, 9 stale) | 08-15: 37 (19 accepted, 9 active, 10 aborted)
events: 08-13: 570 | 08-14: 2,994 | 08-15: 708
delegations: 08-13: 2 blocked | 08-14: 17 blocked + 6 accepted + 1 completed | 08-15: 2 blocked + 16 completed + 1 active
proofs: 253 passed / 48 failed
idempotency: 603 records | required 44/44 keyed (100%) | optional 26/459 keyed
background ops: 308 completed / 1 timed_out
lanes: 13 (all closed) | capsules: 5 active | coord messages: 38 (all pending)
execution_mode (performance.json): mcp_only 1,307 | deep_single_lane 90 | bounded_candidate 25 | auto 37
route_resolved: deterministic 930 | sol_xhigh 37 | luna 12 | mini 11 | terra 8
```
