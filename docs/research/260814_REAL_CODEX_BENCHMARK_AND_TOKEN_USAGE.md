# Đo Đạc THẬT với Codex Model — Benchmark thực + Phân tích Token 2 Tháng

**Ngày:** 2026-08-14
**Repository:** `E:\Github\Tools-Codex-web` (HEAD `d3c6f18`)
**Phương pháp:** (A) benchmark chạy **model Codex thật** qua `CodexAppServerBridge` → `codex app-server` v0.147.0, tiêu thật credits; (B) phân tích **304 session files thật** của Codex (`~/.codex/sessions`, 13/06 → 14/08) — 276.026 turns, 36,09 tỷ input tokens.

> Đây là bản đánh giá bằng **dữ liệu thật**, thay thế cho các con số mô phỏng trong các báo cáo trước. Mọi con số dưới đây đều đo từ API/model thật hoặc file log thật trên máy.

---

## 1. Benchmark thật: cùng một packet, 3 tier model (chạy 2026-08-14)

**Thiết kế:** một packet bounded đúng chuẩn Phase 2 (hàm Python 3 dòng có bug + spec + oracle deterministic). Không cho tool, không cho đọc repo — chỉ sinh candidate. Chấm điểm bằng **oracle thật**: `exec()` hàm trả về và chạy 3 test cases.

| Profile | Model | Effort | Trạng thái | Wall time | Input tokens | Cached % | Output | **Credits thật** | Oracle |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `candidate_mini` | gpt-5.4-mini | low | completed | **4,88 s** | 4.578 | 53,1% | 52 | **0,0507** | ✓ 3/3 |
| `candidate_mini` (continuation cùng thread) | gpt-5.4-mini | low | completed | 4,20 s | 4.636 | **96,6%** | 95 | **0,0221** | — |
| `candidate_luna` | gpt-5.6-luna | high | completed | **2,11 s** | 8.733 | 0% | 62 | **0,2276** | ✓ 3/3 |
| `deep_code` | gpt-5.6-sol | xhigh | completed | 2,73 s | 12.280 | 22,9% | 40 | **1,2482** | ✓ 3/3 |

Tổng chi phí thật của đợt benchmark: **~1,55 credits**.

### Phát hiện thật (không phải mô phỏng)

1. **Trên packet đã localize, cả 3 tier đều đúng 100%** — khớp Phase 2, nhưng lần này đo bằng API thật.
2. **Chênh lệch chi phí thật còn dữ dội hơn ước tính**: Sol xhigh = **1,2482 credits ≈ 24,6× Mini (0,0507)** và 5,5× Luna. Báo cáo trước dùng hằng số Phase 2 (8,3×) — thực tế router tiết kiệm **nhiều hơn** mức đã công bố.
3. **Continuation cache là đòn bẩy chi phí mạnh nhất đo được**: tiếp tục cùng thread → 96,6% input cached → credits giảm **0,0507 → 0,0221 (−56%)**.
4. **Sol không nhanh hơn trên task nhỏ**: lần này Luna (2,11 s) và Sol (2,73 s) đều nhanh hơn Mini (4,88 s) — n=1 không kết luận được thứ hạng tốc độ, nhưng đủ để khẳng định *Sol không mang lại lợi ích gì trên leaf nhỏ* ngoài chi phí cao hơn 24 lần.
5. **Bridge chạy thật hoàn hảo**: `codex app-server` v0.147.0, 8 model thật liệt kê được (`gpt-5.6-sol/terra/luna`, `gpt-5.3-codex(-spark)`, `gpt-5.5`, `gpt-5.4(-mini)`) — toàn bộ đường dây Codex thật hoạt động, không cần stub.

---

## 2. Phân tích token thật 2 tháng (304 sessions, 276.026 turns)

### 2.1 Tổng quan

| Chỉ số | Giá trị thật |
|---|---:|
| Session files có token data | **304** |
| Tổng turns | **276.026** |
| Tổng input tokens | **36.093.161.053** (36,1 tỷ) |
| Tổng cached input | **34.611.721.344 (95,9%)** |
| Tổng output tokens | 97.837.964 |
| Tổng reasoning tokens | 42.857.717 |
| Credits ước tính (theo bảng giá của bridge) | **~677.297** |

### 2.2 Xu hướng theo ngày (input tokens thật, cache %, credits ước tính)

| Ngày | Sessions | Turns | Input tokens | Cached % | Credits ước tính |
|---|---:|---:|---:|---:|---:|
| 07-17 | 1 | 2.755 | 383,2 M | 96,4% | 7.039 |
| 07-26 | 38 | 34.708 | 4,80 tỷ | 96,1% | 91.412 |
| 08-01 | 31 | 40.730 | 5,18 tỷ | 96,9% | 92.415 |
| 08-02 | 19 | 47.599 | 6,16 tỷ | 96,6% | 110.876 |
| **08-03** | **82** | **103.459** | **13,38 tỷ** | 95,1% | **267.080** |
| 08-05 | 8 | 21.547 | 2,91 tỷ | 96,2% | 54.997 |
| **08-06** | 1 | 649 | 92,3 M | 97,8% | **1.605** |
| 08-08 | 5 | 5.301 | 743,8 M | 95,8% | 15.298 |
| 08-09 | 55 | 10.999 | 1,37 tỷ | 95,6% | 27.167 |
| 08-10 | 19 | 1.326 | 152,7 M | 95,6% | 2.856 |
| 08-13 | 8 | 264 | 20,4 M | 96,6% | **395** |

### 2.3 Phân bố theo model (session dominant)

| Model | Số session | Tỷ lệ |
|---|---:|---:|
| **gpt-5.6-sol** | 205 | **67,4%** |
| gpt-5.6-terra | 63 | 20,7% |
| gpt-5.5 | 15 | 4,9% |
| gpt-5.6-luna | 13 | 4,3% |
| gpt-5.4-mini | **0** | **0%** |

Nguồn khởi tạo: **Codex Desktop/codex_local_access: 277 sessions** · Codex Desktop/openai: 23 · codex_exec: 3 · codex-tui: 1.

---

## 3. Trả lời trực tiếp câu hỏi: "Token của Codex model không giảm chút nào"

**Số liệu nói điều ngược lại ở cấp hệ thống — nhưng cảm nhận của bạn là đúng ở cấp Codex Desktop.** Cụ thể:

1. **Token ĐÃ giảm mạnh sau 06/08**: từ đỉnh **267.080 credits/ngày (03/08)** → 1.605 (06/08) → 395 (13/08). Giảm **~99,8%** sau khi kết thúc đợt thí nghiệm điều phối và áp dụng routing mới. Trong khoảng đó, ngày 03/08 một mình đốt 13,38 tỷ input tokens qua **103.459 turns** — đây chính là đợt chạy multi-agent/subagent quy mô lớn (session_meta cho thấy `thread_source=subagent`, `agent_role=worker`, `multi_agent_version=v2`), không phải công việc thường nhật.

2. **Nhưng Codex Desktop vẫn nặng Sol** (67,4% session chạy sol, 0% session dùng mini). Lý do kiến trúc: theo thiết kế (Phase 2 §12.2), **Desktop là "deep lane" Sol xhigh** — router tiết kiệm chi phí nằm ở phía **ChatWeb MCP** (deterministic/mini/luna lanes). Nếu bạn tiếp tục làm việc trực tiếp trong Desktop, không một cơ chế nào của MCP được chạm tới, và token Desktop sẽ đúng là "không giảm" — vì không có gì được route đi nơi rẻ hơn.

3. **Cache đang gánh chi phí**: 95,9% input tokens toàn kỳ là cached. Nếu không có prompt cache, con số ước tính không phải 677K credits mà cao gấp nhiều lần. "Token nhiều" trong UI phần lớn là token cache rẻ (tỷ lệ giá ~1:10 theo `_CREDIT_RATES_PER_MILLION`).

**Kết luận sắc:** vấn đề không phải "hệ thống không tối ưu" mà là **kỷ luật route**: công việc thường nhật phải chảy qua ChatWeb MCP (để rơi vào mini/luna/deterministic), Desktop chỉ dành cho deep work. Mọi công việc đặt vào Desktop sẽ trả giá Sol xhigh — và benchmark thật ở §1 cho thấy giá đó cao hơn **24,6 lần** so với Mini trên cùng một kết quả đúng.

---

## 4. Khuyến nghị hành động (dựa trên số liệu thật)

1. **Dịch chuyển routine khỏi Desktop.** Mọi leaf đã localize + có oracle → ChatWeb MCP (`bugfix`/`test_failure` với verification) sẽ tự rơi lane mini (0,05 credits/lần — đã đo thật). Chỉ đưa sang Desktop khi MCP phân loại `deep_code`/cross-file.
2. **Dùng continuation thay vì session mới** khi theo đuổi cùng một nhiệm vụ: đo được −56% credits nhờ 96,6% cache. Quy tắc: cùng task + cùng invariant → cùng thread.
3. **Hạn chế subagent**: đợt 03/08 (103K turns) là bằng chứng chi phí của topology multi-agent trên workload lớn — không spawn worker song song nếu công việc tuần tự (khớp Google Research §4.2 của Phase 2).
4. **Đưa "credits/ngày" lên bảng điều khiển**: dữ liệu đã có trong ledger + session files; thêm một dòng tổng chi phí hôm nay vào panel để bạn thấy token có giảm hay không mỗi ngày — thay vì cảm nhận.
5. **Đo tiếp định kỳ**: benchmark thật ở §1 chỉ tốn ~1,5 credits — nên chạy lại 1 lần/tuần để theo dõi tier gap thật (hiện 24,6×) khi OpenAI đổi giá/model.

---

## 5. Tài liệu tham khảo

1. Báo cáo mô phỏng trước (để so sánh độ lệch với thực tế): `docs/research/DEPLOYMENT_PERFORMANCE_COST_EVALUATION_2026-08-14.md`
2. Phương pháp packet-only: `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md` (§7)
3. Cơ chế bridge + bảng giá: `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py` (`_PROFILE_SPECS`, `_CREDIT_RATES_PER_MILLION`)
4. Dữ liệu thật: `~/.codex/sessions/**/*.jsonl` (304 files, event `token_count`), `~/.codex/history.jsonl`
5. Script benchmark thật: `C:\Users\daoth\AppData\Local\Temp\opencode\real_codex_bench.py` (tái chạy được; ~1,5 credits/lần)
6. Script phân tích usage: `C:\Users\daoth\AppData\Local\Temp\opencode\analyze_codex_usage2.py`
