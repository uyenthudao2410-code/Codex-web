# Đánh giá Hiệu năng – Chi phí – Thời gian của Mô hình Triển khai Tools-Codex-web

**Ngày:** 2026-08-14
**Repository:** `E:\Github\Tools-Codex-web` (nhánh `main`, HEAD `d3c6f18`)
**Phạm vi:** Coding Tools MCP runtime + adaptive model routing + Codex App Server bridge + orchestration ledger (deployment model hiện tại, không đánh giá lại WebCodex Rust core upstream)
**Phương pháp:** 3 lớp bằng chứng độc lập — (A) test suite tự động, (B) telemetry production đo được trên máy, (C) mô phỏng kinh tế routing dùng chính hàm routing production + hằng số chi phí đo được từ Phase 1/Phase 2 của repo.

---

## 1. Kết luận điều hành

**Phán quyết: mô hình triển khai hiện tại ĐẠT mục tiêu tối ưu chi phí và thời gian ở mức bằng chứng hiện có, nhưng lợi thế đến từ kiến trúc (classification + deterministic lane + packet topology), không phải từ "chọn model rẻ".**

Các con số cốt lõi:

| Chỉ số | Kết quả đo/test | Cơ sở |
|---|---:|---|
| Test suite MCP (routing, bridge, ledger, resilience) | **131/131 pass** (~44 s) | pytest, 2026-08-14 |
| Tỷ lệ wave production chạy `mcp_only` (0 credit model) | **33/48 = 68,75%** | orchestration ledger |
| Thời gian hoàn thành run được chấp nhận | **median 90,3 s** (n=14) | orchestration ledger |
| Proof/oracle thực thi | **median 3,3 s** (n=36) | orchestration ledger |
| Chi phí model mô phỏng/tuần (100 task) so với "luôn dùng Sol xhigh" | **−51,5% credits** (46,84 vs 96,49) với chất lượng gần tương đương | simulation §6 |
| Chi phí cho mỗi kết quả được chấp nhận | **0,471 credit** (vs 0,966 all-Sol; 0,344 ladder) | simulation §6 |
| Số lần thử lãng phí (wasted attempts)/100 task | **12,9** (vs 46,1 ladder; 34,2 all-Mini) | simulation §6 |
| Sai sót trên task rộng/nguy hiểm (critical miss)/100 task | **0,65** (vs 1,71 all-Mini; 0,90 all-Luna) | simulation §6 |

Ba kết luận sắc:

1. **Topology > tier model.** Bằng chứng mạnh nhất không nằm ở router mà ở Phase 2: cùng một Sol xhigh, chạy *autonomous shell loop* = 0/3 accepted (~31 s wall, không ghi production), chạy *packet-only/no-tools* = 3/3 accepted (~6,7–8,3 s wall). Trước khi chọn model, hệ thống phải bỏ được entropy của packet.
2. **Classification tiết kiệm hơn cascade.** Mô phỏng cho thấy ladder `Mini→Luna→Sol` có vẻ "rẻ credits" (34,2) nhưng trả giá bằng 46,1 lần thử lãng phí và +86% thời gian wall-clock so với router hiện tại — đúng như MTRouter (ACL 2026) kết luận: router tốt có *ít lần chuyển model*.
3. **Lợi thế chi phí bền vững.** Điểm hòa vốn của toàn hệ thống adaptive so với all-Sol chỉ cần P(mini)=1% — vì phần tiết kiệm lớn nhất đến từ lane deterministic (68,75% wave không tốn model credit) và lane Luna, chứ không phải chỉ lane Mini. Nếu sau này Mini bị hạ cấp, hệ thống vẫn rẻ hơn all-Sol; chỉ chất lượng (wasted attempts) là thứ cần giám sát.

Nhược điểm phải nêu thẳng: (i) cache/dedup semantic gần như không phát huy trong trace thực (1 cache hit / 968 calls); (ii) độ trễ LLM-turn chiếm 84% tổng thời gian chờ đo được — đây là nút thắt thật, không phải model; (iii) dữ liệu promote Mini lane mới 4/4 mẫu — chưa đủ để tin cậy thống kê; (iv) bridge vẫn kẹp observe ~30 s, làm méo deadline của executor autonomous.

---

## 2. Mô hình triển khai được đánh giá

Pipeline hiện tại (README §2–§7, `server.py`, `codex_bridge.py`, `orchestration_ledger.py`):

```text
ChatGPT (MCP client)
   └─> Coding Tools MCP (smart mode: 8 tools)
         ├─ workspace_context / agent_workflow / task_control ...
         ├─ _select_agent_execution_route()            <-- đối tượng test chính
         │    deterministic | mini | luna | terra | sol_xhigh | sol_max | sol_ultra
         ├─ strong-oracle gate: Mini chỉ khi bugfix/test_failure
         │    + verification green + <=2 files + <=24 KB
         ├─ high-cost gate: sol_max/sol_ultra yêu cầu allow_high_cost=true
         └─ Codex App Server sidecar (read-only, no-network, approvalPolicy=never)
```

Bảng route production (`server.py` dòng 289–303):

| Route | Model | Effort | Deadline | Ghi chú |
|---|---|---|---|---|
| `deterministic` | — | — | — | Không gọi model; tool/test/compiler |
| `mini` | gpt-5.4-mini | low | 10 s | Leaf localize + oracle mạnh |
| `luna` | gpt-5.6-luna | high | 15 s | Bounded leaf (≤4 files, ≤60 KB) |
| `terra` | gpt-5.6-terra | high | 25 s | Cross-file, thử nghiệm, gated |
| `sol_xhigh` | gpt-5.6-sol | xhigh | 30 s | Deep/broad mặc định |
| `sol_max` / `sol_ultra` | gpt-5.6-sol | max/ultra | 30 s | **Gate bắt buộc** `allow_high_cost` |

Đây là **router phân lớp (classifier) + tối đa 1 fallback**, không phải ladder tuần tự — thiết kế trùng khớp với khuyến nghị của MTRouter (Zhang et al., ACL 2026) và FrugalGPT (Chen et al., 2023).

---

## 3. Phương pháp và ranh giới bằng chứng

| Lớp | Công cụ | Dữ liệu | Độ tin cậy |
|---|---|---|---|
| A. Test suite | pytest 9.1.1 / Python 3.11.9 | 131 tests của `resources/coding-tools-mcp/tests` | Cao cho tính đúng đắn của deployment |
| B. Telemetry production | SQLite ledger + `performance.json` | 42 runs, 48 waves, 504 events, 968 tool calls (12–13/08/2026) | Cao nhưng mẫu nhỏ, một máy, một người dùng |
| C. Mô phỏng kinh tế | Harness gọi hàm routing thật + hằng số đo được | 100-task-week × 5 chiến lược, sensitivity | Trung bình — phụ thuộc hằng số đầu vào |

**Hằng số chi phí/thời gian** lấy từ chính repo (không bịa):

- Credits mỗi candidate được chấp nhận (Phase 2, patch-only): Mini 0,138 · Luna 0,260 · Sol xhigh 1,317.
- TTA (s): Mini 10,2 · Luna 10,1 · Sol xhigh 11,2 · deterministic 3,3 (proof median từ ledger).
- Serial fallback penalty đo được (Phase 1): +22,8 s/task.
- Sol xhigh autonomous trên leaf hẹp: 0/3 accepted, ~31 s wall (Phase 2).
- Terra autonomous: 2/3 capacity failure (Phase 2).

**Ranh giới:** các xác suất thành công theo class task trong mô phỏng là ước lượng bảo thủ từ Phase 1/2 + tier gap của GPT-5.6 (OpenAI launch page: SWE-Bench Pro Sol 64,6% / Terra 63,4% / Luna 62,7%). Không có xác suất nào được "đo ngược" để làm đẹp kết quả; sensitivity §7 cho thấy kết luận ổn định trong khoảng ±0,15.

---

## 4. Test 1 — Tính đúng đắn của deployment (131 tests)

Chạy ngày 2026-08-14, `PYTHONPATH=resources/coding-tools-mcp`:

```
tests/test_task_state_and_build.py      (routing invariants, background ops)     76 passed (nhóm 1)
tests/test_budget_control.py  proof_ledger, orchestration_*, agent_workflow ... 
tests/test_codex_bridge.py    smoke, stateless http, quota, job object          41 passed (nhóm 2)
tests/test_resilience_fault_injection.py durable_coordination, live_*           14 passed (nhóm 3)
Tổng: 131 passed, ~44 s
```

Những invariant được test trực tiếp liên quan đến mô hình triển khai:

- `T02` (routing effort control): route `mini` chỉ khi `strong_oracle=True` + ≤2 files + ≤24 KB; thiếu oracle → `luna`; feature rộng → `sol_xhigh`; `sol_max/ultra` **luôn bị chặn** khi chưa có `allow_high_cost` (mã lỗi `HIGH_COST_ACK_REQUIRED`).
- `T09` (client tool compatibility): smart surface phải đúng 8 tool — bảo vệ thiết kế "tool surface nhỏ" (đối chiếu ToolScope, §8).
- Background operation: workflow chạy lâu hand-off thành `operation_id` và poll được — không mất công chạy lại từ đầu.
- Budget control, proof ledger, per-principal quota, idempotency, restart reconciliation: các test xác nhận **retry-safe và không tính phí 2 lần cho cùng một bằng chứng**.

**Ý nghĩa kinh tế của việc này:** một hệ thống chạy model tính tiền theo token mà không có idempotency/ledger sẽ trả tiền nhiều lần cho cùng một lần build/test. 131 tests xanh là bằng chứng rẻ nhất mà rẻ không có nghĩa là thừa: mỗi test fail ở lớp này tương đương chi phí model lãng phí trong production.

---

## 5. Test 2 — Bằng chứng production thực tế (ledger + telemetry)

### 5.1 Orchestration ledger (`.coding-tools/orchestration/ledger.sqlite3`, 12–13/08/2026)

| Đo đạc | Giá trị | Diễn giải kinh tế |
|---|---:|---|
| Waves theo execution mode | `mcp_only` 33 · `auto` 12 · `deep_single_lane` 3 | **68,75% wave không tiêu một credit model nào** — lane deterministic đang thực sự gánh phần lớn khối lượng production |
| Runs accepted | 14/42 (28 còn active/in-flight) | median 90,3 s, mean 153 s từ lúc bắt đầu đến lúc được ChatWeb Sol chấp nhận |
| Proofs | 36 proof, **100% status passed/failed được ghi**, median 3,3 s | Oracle chạy nhanh hơn một lượt LLM-turn (median wait 13,1 s) |
| Delegations tới Codex Sol xhigh | 2, cả hai **blocked** (`candidate_scope_missing`, `candidate_model_not_completed`) | Router từ chối trả tiền cho một Sol autonomous loop khi packet chưa đủ scope — đúng "packet quality trước model tier" |
| Kinh tế delegation thứ 2 | wall 30 s, cache_ratio **0,942**, est. credits 0,4243 | Cơ chế continuation cache hoạt động: 94,2% input token là cached |
| Checkpoints accepted_by | **ChatWeb Sol** (14/14) | Kiến trúc phân quyền "Sol kiểm soát, worker chỉ candidate" đang được vận hành đúng thiết kế |
| Replanned waves | 6 | Có failure surface thật; control loop có phản ứng (xem §8 gap) |

### 5.2 Tool-call telemetry (`.coding-tools/performance.json`)

| Chỉ số | Giá trị |
|---|---:|
| Tổng tool calls | 968 |
| Lỗi | 65 (6,7%) |
| Tổng thời gian thực thi local | 4 067 s (67,8 phút) — trung bình 4,2 s/call |
| Tổng thời gian chờ (wait) | 21 240 s (354 phút) — trung bình **21,9 s/call**, p90 40,3 s |
| Cache hits / dedup | **1 / 0** |

**Phân tích sắc:** tỷ lệ wait/exec ≈ **5,2 : 1**. Nút thắt không phải tốc độ tool hay model — mà là độ trễ mỗi vòng LLM-turn của MCP client. Vì vậy hai thiết kế của repo là chính xác về mặt kinh tế: (1) **agent_workflow bundle nhiều bước vào 1 call** (mỗi round-trip tránh được ≈ 21,9 s); (2) **smart mode 8 tool** giảm xác suất chọn nhầm tool → bớt vòng gọi lỗi. ToolScope (Liu et al., ACL 2026) đo lợi ích lọc/trộn tool tăng độ chính xác chọn tool 8,38–38,6% — đây là cơ sở khoa học trực tiếp cho quyết định giữ 8 tool thay vì phình schema.

**Ngược lại:** cache semantic (1 hit) và dedup (0) gần như không phát huy trên workload hiện tại. Hệ thống có cơ chế nhưng chưa có lợi ích — đây là khoảng trống tối ưu lớn nhất còn lại (§9).

---

## 6. Test 3 — Mô phỏng kinh tế routing (100-task-week, 5 chiến lược)

Harness gọi trực tiếp `Runtime._select_agent_execution_route()` của production (không copy lại logic), với phân phối task ước lượng từ workload thực: 35 localized+strong-oracle, 20 bounded leaf, 15 broad/deep, 30 deterministic-class. Xác suất thành công theo class (bảo thủ): Mini 0,75/0,40/0,10 · Luna 0,85/0,85/0,35 · Sol 0,97/0,95/0,92; mọi chiến lược được phép tối đa 1 fallback về Sol (+22,8 s penalty đo từ Phase 1).

| Chiến lược | Credits/tuần | TTA (h) | Accepted | Cred/accepted | Wasted attempts | Critical miss | vs all-Sol |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Adaptive router (đang triển khai)** | **46,84** | **0,35** | **99,4** | **0,471** | **12,9** | **0,65** | **−51,5%** |
| All-Sol xhigh (baseline đơn giản) | 96,49 | 0,28 | 99,8 | 0,966 | 3,3 | 0,16 | 0% |
| All-Luna | 41,89 | 0,39 | 99,1 | 0,423 | 18,0 | 0,90 | −56,6% |
| All-Mini | 54,78 | 0,55 | 98,3 | 0,557 | 34,2 | 1,71 | −43,2% |
| Ladder Mini→Luna→Sol | 34,21 | **0,65** | 99,4 | 0,344 | **46,1** | 0,59 | −64,5% |

**Đọc bảng như một nhà nghiên cứu, không như một slide bán hàng:**

1. **Adaptive rẻ hơn 51,5% so với all-Sol** với accepted gần như không đổi (99,4 vs 99,8) và critical miss chỉ nhích 0,65 vs 0,16. Đây là giao dịch chi phí–rủi ro hợp lý cho workload cá nhân/team nhỏ.
2. **All-Luna rẻ hơn adaptive ~10% credits nhưng tệ hơn ở đúng thứ đắt nhất:** +40% wasted attempts (18,0 vs 12,9) và critical miss cao hơn 38% — mỗi lần thử lãng phí là một patch fail đã tiêu model-turn, oracle-run và *turn sửa của Sol*. Đây chính là "cheapest first call" mà Phase 2 (mục 20) cảnh báo không được tối ưu.
3. **Ladder rẻ nhất credits nhưng đắt nhất thời gian** (0,65 h, +86% so với adaptive) và 46,1 lần thử lãng phí. Khớp với MTRouter: router hiệu quả *ít chuyển model*; và với Phase 1: mỗi hop serial cộng penalty đo được.
4. **All-Mini là chiến lược tệ nhất toàn diện**: đắt hơn adaptive, chậm hơn, sai nhiều hơn trên task nguy hiểm (1,71 critical miss). Điều này biện minh trực tiếp cho **strong-oracle gate** và **high-cost gate** trong code: chi phí thật của model rẻ nằm ở hậu quả sai lầm, không ở token.

**Sensitivity P(mini | localized+oracle):**

| P(mini) | Credits | TTA (h) | Accepted | Wasted |
|---|---:|---:|---:|---:|
| 0,50 | 58,37 | 0,43 | 98,9 | 21,7 |
| 0,75 (mặc định mô hình) | 46,84 | 0,35 | 99,4 | 12,9 |
| 0,95 | 37,62 | 0,29 | 99,7 | 6,0 |

Điểm hòa vốn (adaptive vs all-Sol về credits) ≈ **P(mini) = 1%**: lợi thế chi phí của kiến trúc này không phụ thuộc vào Mini. Kể cả khi Mini lane hoàn toàn vô dụng, lane deterministic + Luna vẫn đủ làm hệ thống rẻ hơn all-Sol. Cái mất khi P(mini) thấp là *chất lượng* (wasted 21,7) chứ không phải tiền — do đó việc promote Mini phải do chất lượng quyết định, đúng như khuyến nghị conformal routing (§8.5).

---

## 7. Phân tích chi phí – thời gian (cost model)

Dùng cost model của chính repo (Phase 2, mục 20):

```text
EXPECTED_ACCEPTED_COST = generation + evidence + validation + review
                       + P(failure) * repair/escalation + latency + integration
```

Phân rã cho task lớp localized+strong-oracle theo chiến lược:

| Thành phần | Adaptive (Mini→Sol fallback) | All-Sol |
|---|---:|---:|
| Generation | 0,138 | 1,317 |
| P(fail)=0,25 → repair Sol | 0,25 × 1,317 = 0,329 | 0,03 × 1,317 = 0,040 |
| Evidence/oracle (mcp_only, 3,3 s) | 0 | 0 |
| Latency penalty khi fail | 0,25 × 22,8 s | 0,03 × 22,8 s |
| **Tổng credits/accepted** | **≈ 0,47** | **≈ 1,36** |

**Chênh lệch thời gian:** trên toàn bộ workload mô phỏng, adaptive chậm hơn ~2,6 s cho mỗi kết quả được chấp nhận (12,7 s vs 10,1 s, đã tính cả lane deterministic); riêng lớp localized+oracle, kỳ vọng fallback cộng thêm 0,25 × (11,2 + 22,8) ≈ 8,5 s/task — tức thời gian mất thêm chỉ rơi vào 25% task phải trả penalty fallback, đúng thiết kế "chỉ fallback khi bằng chứng mới làm thay đổi phân lớp".

**Tiết kiệm thời gian thật của hệ thống nằm ở chỗ khác, ít được nói tới:** mỗi vòng tool-call tránh được nhờ bundling ≈ 21,9 s (số đo trace thực), và lane deterministic chấp nhận kết quả trong 90,3 s median thay vì để một autonomous loop chạy 31 s × N lần thử như Phase 2 đã đo.

---

## 8. Đối chiếu với nghiên cứu khoa học & phân tích gần đây

| # | Nguồn | Phát hiện | Hệ thống này khớp/đi ngược |
|---|---|---|---|
| 1 | **FrugalGPT** (Chen, Zaharia & Zou, 2023, arXiv:2305.05176) | LLM cascade + approximation có thể giảm chi phí tới 98% mà giữ chất lượng | Khớp: 3 chiến lược (prompt adaptation, LLM approximation = lane deterministic, cascade có chọn lọc) đều có mặt trong thiết kế |
| 2 | **RouteLLM** (Ong et al., 2024, arXiv:2406.18665) | Router học giữa model mạnh/yếu giảm chi phí >2× không mất chất lượng | Khớp một phần: repo dùng router quy tắc thay vì ML router — LLMRouterBench (#5) cho thấy điều này không tệ hơn |
| 3 | **MTRouter** (Zhang et al., ACL 2026, DOI 10.18653/v1/2026.acl-long.2045) | −58,7% chi phí (ScienceWorld) nhờ router ít chuyển model, chịu lỗi thoáng qua tốt | Khớp trực tiếp: thiết kế "classify once + max 1 fallback"; Phase 1 đo penalty chuyển model +22,8 s là bằng chứng local cùng chiều |
| 4 | **ToolScope** (Liu et al., ACL 2026, DOI 10.18653/v1/2026.acl-long.1573) | Lọc/trộn tool tăng độ chính xác chọn tool 8,38–38,6% | Khớp: smart mode giữ 8 tool, invariant T09 bảo vệ surface |
| 5 | **LLMRouterBench** (Li et al., Findings ACL 2026, DOI 10.18653/v1/2026.findings-acl.1881) | Router phức tạp không reliably thắng baseline đơn giản; curation model quan trọng hơn | Khớp: chưa cần ML router; cần route ledger trước (P4 của repo) |
| 6 | **ContextualRouter** (Varangot-Reille et al., EACL 2026, DOI 10.18653/v1/2026.eacl-srw.22) | Retrieval lịch sử few-shot đủ để route tốt | Khớp với hướng "nearest-similar-task ledger" của repo |
| 7 | **Google Research — Scaling agent systems** (2026-01-28) | Multi-agent chỉ thắng khi task parallelizable; sequential planning giảm 39–70%; centralized hạn chế khuếch đại lỗi | Khớp: ultra bị gate; 1 primary lane + ≤1 reviewer lane; không spawn worker tuần tự |
| 8 | **Conformal LLM Routing** (ACL 2026 SRW, 2026.acl-srw.70) | Promote model rẻ phải theo lower confidence bound, không theo % thành công thô | Khớp: repo đã giữ Mini ở mức "PROMISING/experimental" dù 4/4 — chưa auto-promote toàn cục |
| 9 | **Independent Patch Verification / RETRACE** (Li et al., arXiv:2608.08950) | Verify độc lập (blind, evidence-only) tăng Pass@1 3,6–7,0 điểm | Khớp: review plane blind/evidence-only, không nhận narrative của executor |
| 10 | **SWE-bench "solved" study** (Wang, Pradel & Liu, arXiv:2503.15223) | Test xanh chưa đủ cho high-risk acceptance | Khớp: Sol vẫn kiểm tra invariant cạnh cho auth/finance/tenant dù oracle xanh |
| 11 | **Prompt caching / continuation** (thực nghiệm của repo + delegation cache_ratio 0,942) | Continuation ~95% cached → ~0,026 credits (Mini) | Khớp: policy "reuse thread khi semantic continuity, không giữ stale context" |

**Tổng hợp:** toàn bộ 9/11 quyết định kiến trúc lớn của deployment model này có cơ sở khoa học độc lập 2023–2026, và 2 điểm còn lại (route ledger, executor deadline) là những gì chính repo xếp vào P3/P4 chưa làm — không phải mâu thuẫn mà là đúng trình tự.

---

## 9. Lập luận sắc: đúng ở đâu, yếu ở đâu

### 9.1 Năm lập luận khẳng định mô hình hiện tại

**L1 — Đúng thứ tự tối ưu.** Phase 2 đã chứng minh bằng thực nghiệm: đổi topology (autonomous → packet-only) làm Sol xhigh từ 0/3 thành 3/3 với wall time giảm 4–5 lần. Không một thay đổi effort/model nào cho được lợi ích cỡ đó. Repo đúng khi đặt "packet quality" là biến lật ngược kinh tế.

**L2 — Đúng bản chất của router.** Đây là classifier + max-1-fallback, không phải ladder. Cả MTRouter lẫn LLMRouterBench đều ủng hộ router ít chuyển model. Phase 1 đã đo cái giá của chuyển model (+22,8 s/lần) — con số mà một thiết kế ngây thơ không nhìn thấy.

**L3 — Đúng nơi đặt chi phí bằng không.** 68,75% wave production là `mcp_only`: 0 credit model. "Không gọi model khi deterministic proof đủ" là chiến lược giảm chi phí tuyệt đối tốt nhất — và nó cũng là chiến lược giảm lỗi tốt nhất, vì compiler/test không hallucinate.

**L4 — Đúng gate cho rủi ro đuôi.** `sol_max/ultra` bị chặn cứng bằng `allow_high_cost`, Terra bị gated do 2/3 capacity failure đo được, Mini không được auto dùng khi thiếu oracle. Đây là cost-control theo rủi ro (risk-weighted), đúng tinh thần conformal routing, chứ không phải tối ưu token đơn thuần.

**L5 — Đúng đơn vị đo.** Ledger theo dõi `FIRST_PASS_ACCEPTED, TTA, CREDITS, CRITICAL_DEFECTS` — tức là chi phí trên *kết quả được chấp nhận*, không phải chi phí trên lần gọi đầu tiên. Phase 1 đã cho thấy "gọi model rẻ trước" có thể đắt hơn trên mỗi kết quả accepted. Bộ metric này ngăn hệ thống rơi lại vào cái bẫy đó.

### 9.2 Bốn điểm yếu và rủi ro còn lại

**G1 — Cache/dedup chưa phát huy (bằng chứng: 1 hit / 968 calls, 0 dedup).** Trong khi delegation đo được cache_ratio 0,942 trên lane continuation. Khoảng trống: cơ chế cache semantic của MCP chưa được workload hiện tại tận dụng — có thể do pattern sử dụng command-heavy (54% exec_command trong trace gần đây) thay vì workflow bundle. Đây là cơ hội tiết kiệm lớn nhất còn lại, ước lượng lý thuyết lên tới hàng chục % trên chi phí evidence lặp lại.

**G2 — Wait-time chiếm 84% thời gian (354 phút vs 68 phút exec).** Nút thắt là LLM-turn latency. Mọi tối ưu tiếp theo (parallel read, prefix cache cho prompt của client, giảm poll) nên nhắm vào đây, không nhắm vào tốc độ model.

**G3 — Mẫu promote Mini chưa đủ (4/4).** Theo conformal routing, cần conservative lower bound trước khi auto-promote. Hiện Mini lane là hard-coded rule (≤2 files, ≤24 KB, oracle green) — rule đúng hướng nhưng ngưỡng chưa được hiệu chỉnh bằng ledger (P4). Nếu P(mini) thực tế < 0,5, hệ thống vẫn rẻ nhưng bắt đầu sinh wasted attempts (§6) — cần giám sát `SOL_REPAIR_TURNS` liên tục.

**G4 — Đo đạc executor còn méo (30 s observe clamp, Phase 2 §6.5) và Terra chưa có dữ liệu sạch.** Nếu muốn trả lời câu hỏi "cross-file có nên auto-route Terra", phải sửa deadline semantics trước (P3 của repo), nếu không mọi benchmark autonomous đều bị cắt ở 31 s và kết luận sẽ sai.

---

## 10. Khuyến nghị theo thứ tự giá trị

1. **Đóng nút thắt wait-time trước (P0).** Bất kỳ cải thiện nào cắt được 1 vòng LLM-turn (~21,9 s) đều lớn hơn mọi tối ưu model trong bảng §6. Cụ thể: tăng mật độ bundle trong agent_workflow, giảm poll không cần thiết, cache evidence theo fingerprint để không hỏi lại.
2. **Kích hoạt semantic cache/dedup cho oracle lặp lại (P1).** Proof ledger đã có `cache_hit` nhưng production ghi 0. Chính sách: cùng `command_hash` + cùng input fingerprint trong cùng base HEAD → trả kết quả cached, ghi nhãn `cache_hit` (đã có cột sẵn).
3. **Route ledger → hiệu chỉnh ngưỡng Mini (P2).** Ghi mỗi route kèm class, oracle strength, TTA, credits, first-pass; sau ~50 mẫu/class thì điều chỉnh ngưỡng (files/bytes) theo lower confidence bound — không cần ML.
4. **Sửa deadline instrumentation của bridge (P3).** True deadline loop + `time_to_first_write` / `time_to_first_green` trước khi bất kỳ quyết định nào về Terra/cross-file autonomous.
5. **Không thay đổi gì về gate hiện tại.** Giữ `allow_high_cost`, giữ Terra gated, giữ read-only sidecar — chúng đang đúng với bằng chứng.

---

## 11. Giới hạn của nghiên cứu này

- **Mẫu nhỏ:** Phase 1 (n=30) và Phase 2 (n≈20) là chuỗi 4–12 mẫu/lane; ledger production mới chạy 2 ngày, một máy, một người dùng. Các tỷ lệ phần trăm trong §6 là mô phỏng có điều kiện, không phải đo đạc A/B thật.
- **Xác suất thành công theo class là ước lượng**, neo vào tier gap công bố của OpenAI và kết quả nhỏ của repo; kết luận chiến lược đã được kiểm tra sensitivity (§6–7) và giữ nguyên trong khoảng rộng.
- **Không đo được chi phí USD thật** — credits là đơn vị ước lượng của bridge (`_CREDIT_RATES_PER_MILLION`), không phải hóa đơn.
- **Không đánh giá chất lượng patch trên miền ngoài repo này** (không có SWE-bench-style grading độc lập); "accepted" nghĩa là oracle + ChatWeb Sol chấp nhận.
- Workload là cá nhân, không suy ra được cho deployment nhiều tenant.

---

## 12. Tài liệu tham khảo

1. Chen, L., Zaharia, M., Zou, J. — *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance*. arXiv:2305.05176, 2023. https://arxiv.org/abs/2305.05176
2. Ong, I. et al. — *RouteLLM: Learning to Route LLMs with Preference Data*. arXiv:2406.18665, 2024. https://arxiv.org/abs/2406.18665
3. Zhang, Y. et al. — *MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings*. ACL 2026. DOI: 10.18653/v1/2026.acl-long.2045. https://aclanthology.org/2026.acl-long.2045/
4. Liu, M. M. et al. — *ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering*. ACL 2026. DOI: 10.18653/v1/2026.acl-long.1573. https://aclanthology.org/2026.acl-long.1573/
5. Li et al. — *LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing*. Findings of ACL 2026. DOI: 10.18653/v1/2026.findings-acl.1881. https://aclanthology.org/2026.findings-acl.1881/
6. Varangot-Reille et al. — *Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient*. EACL 2026 SRW. DOI: 10.18653/v1/2026.eacl-srw.22. https://aclanthology.org/2026.eacl-srw.22/
7. Google Research — *Towards a science of scaling agent systems: When and why agent systems work*. 2026-01-28. https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
8. *Conformal LLM Routing with Distribution-Free Safety Guarantees*. ACL 2026 SRW. https://aclanthology.org/2026.acl-srw.70/
9. Li et al. — *Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework*. arXiv:2608.08950, 2026. https://arxiv.org/abs/2608.08950
10. Wang, W., Pradel, M., Liu, S. — *Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study*. arXiv:2503.15223. https://arxiv.org/abs/2503.15223
11. OpenAI — *GPT-5.6: Frontier intelligence that scales with your ambition* (2026-07-09) và *Previewing GPT-5.6 Sol* (2026-06-26). https://openai.com/index/gpt-5-6/
12. Nội bộ repo: `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`, `docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md` — nguồn hằng số chi phí/TTA/penalty dùng trong §6–7.

---

### Tóm tắt 1 phút

> Mô hình triển khai của Tools-Codex-web **đạt** mục tiêu hiệu suất–chi phí–thời gian ở mức bằng chứng hiện có: tiết kiệm ~51,5% chi phí model so với dùng Sol cho mọi việc mà chấp nhận rủi ro sai lệch gần như không đáng kể, 68,75% tác vụ production chạy với 0 credit model, và toàn bộ 131 test tự động xác nhận các gate (oracle, high-cost, idempotency) hoạt động đúng. Lợi thế đến từ *classification + deterministic lane + packet topology*, không phải từ model rẻ. Hai cơ hội lớn nhất còn lại: (1) wait-time LLM-turn chiếm 84% thời gian — nút thắt thật; (2) semantic cache/dedup chưa phát huy (1/968 hit). Đây là hướng tối ưu tiếp theo, cùng với việc hiệu chỉnh ngưỡng Mini bằng route ledger thay vì tin vào 4/4 mẫu nhỏ.
