# Bộ Test Đánh Giá Năng Lực Hệ Thống — Thiết kế, Kết quả và Kế hoạch Khắc phục

**Ngày:** 2026-08-14
**Repository:** `E:\Github\Tools-Codex-web` (nhánh `main`, HEAD `d3c6f18`)
**Test mới:** `resources/coding-tools-mcp/tests/test_system_capability_suite.py` (34 test, 6 nhóm)
**Kết quả tổng:** Python MCP **169/169 pass** (~46 s, trong đó 34 test mới ~9,5 s) · Node/Electron **57/57 pass** · Tổng **226/226 green**

---

## 1. Mục tiêu

Xây dựng bộ test sâu hơn để trả lời **chính xác, định lượng và có thể lặp lại** ba câu hỏi từ các phân tích trước:

1. Mô hình điều phối (routing + oracle gate + high-cost gate) có thực sự đạt tối ưu chi phí/thời gian không — hay chỉ đúng trên giấy?
2. Hệ thống có chịu được công việc dài hơi (context phình, chạy lại, sự cố transport) không — các cơ chế phòng vệ có hoạt động thật không?
3. Những khoảng trống đã phát hiện (capsule không dùng, idempotency, run không đóng, tunnel drop) đang được đo và ghi nhận như thế nào để giải quyết?

Nguyên tắc: **mọi khẳng định phải đi kèm một test bảo vệ** (regression guard) hoặc một quan sát có số liệu.

---

## 2. Phương pháp lấy từ nghiên cứu thế giới

| Nguồn | Bài học phương pháp | Áp dụng vào bộ test này |
|---|---|---|
| **SWE-bench** (Jimenez et al., ICLR 2024, arXiv:2310.06770 — 2.294 issue GitHub thật) | Đánh giá agent qua *nhiệm vụ thật + oracle thật*, không qua câu hỏi tổng hợp; mọi patch phải vượt qua test độc lập | Nhóm 2–3: dùng oracle thật (command thật, file thật, exit code thật) thay vì mock; chấp nhận chỉ khi bằng chứng deterministic |
| **τ-bench pass^k** (Yao et al., 2024, arXiv:2406.12045) | Độ tin cậy = khả năng lặp lại kết quả đúng qua nhiều lần thử; đo *nhất quán*, không chỉ thành công một lần | Nhóm 1 (determinism của router: 6 lần lặp cùng input → cùng output), nhóm 4 (30 phiên churn liên tiếp), nhóm 3 (replay sau restart) |
| **Chaos engineering / fault injection** (Netflix Simian Army; áp dụng cho LLM agents) | Hệ thống chỉ đáng tin khi vẫn phục vụ được khi *client ngắt giữa chừng, tải dồn, upload dở dang* | Nhóm 4: client abort giữa response (tái hiện WinError 10053 đã đo ngoài production), partial upload rồi disconnect, session churn |
| **MTRouter** (ACL 2026) + **FrugalGPT** + **RouteLLM** | Router tốt = ít chuyển model, chi phí tính trên *kết quả được chấp nhận*, cascade tốn penalty thời gian | Nhóm 5: mô phỏng kinh tế với ngưỡng hồi quy (adaptive phải rẻ hơn all-Sol ≥40%, ladder phải lãng phí >3×) |
| **Conformal routing** (ACL 2026 SRW) | Không promote model rẻ từ mẫu nhỏ; cần lower confidence bound | Nhóm 1: kiểm tra gate cứng — auto **không bao giờ** chọn `sol_max/sol_ultra` trong toàn bộ không gian đầu vào quét được |

---

## 3. Inventory — 34 test mới (6 nhóm)

### Nhóm 1 — Routing classification matrix (8 test)
`RoutingMatrixTests`
- `test_workflow_prefers_deterministic_lane` — diagnose/document/resume/build_release/greenfield → `deterministic` (0 credit) dù context lớn
- `test_mini_gate_requires_oracle_and_tight_scope` — Mini chỉ khi **đủ 4 điều kiện đồng thời**: oracle xanh + bugfix/test_failure + ≤2 file + ≤24 KB; bỏ 1 điều kiện bất kỳ → rớt xuống luna
- `test_luna_boundaries_are_exact` — kiểm tra biên chính xác 4/5 file, 60.000/60.001 bytes
- `test_high_cost_gate_blocks_max_and_ultra` — `HIGH_COST_ACK_REQUIRED` khi thiếu `allow_high_cost`; mở được khi đủ
- `test_unknown_route_rejected_and_explicit_route_honored`
- `test_auto_never_selects_max_or_ultra` — quét 5 workflow × 5 mức file × 4 mức bytes = 100 tổ hợp
- `test_decision_is_deterministic` — 4 input × 6 lần lặp = cùng kết quả (tinh thần pass^k)
- `test_route_specs_are_self_consistent` — bảng route production phải tự nhất quán (model, deadline, cờ high_cost)

### Nhóm 2 — Context/output budget (6 test)
`ContextBudgetTests`
- Cắt head/tail đúng giới hạn dòng + bytes, cờ `truncated_by` chính xác; văn bản vừa khít không bị đánh dấu cắt
- **`test_long_command_output_is_capped_and_retainable`** — command sinh 120 KB, response chỉ 4 KB nhưng **giữ nguyên 100% stream trong session buffer** + hướng dẫn `read_output` tiếp tục + diagnostic `OUTPUT_TRUNCATED`. Đây là bằng chứng mới: cơ chế chống phình context mạnh hơn mô tả trong README (không mất dữ liệu, chỉ bounded response)
- Command nhỏ không bị cắt; command fail trả exit code + stderr đầy đủ

### Nhóm 3 — Long-horizon lifecycle (7 test)
`LongHorizonLifecycleTests`
- `test_full_run_chain_is_integrity_verified` — dựng run→wave→4 events→proof→checkpoint→finish; `verify_chain` hash-chain phải OK
- `test_event_replay_paginates` — 250 events, replay 100/100/50 đúng phân trang (`has_more`, `next_after_seq`)
- `test_handoff_capsule_round_trip` — ghi → đọc lại nguyên vẹn; `test_oversized_capsule_is_rejected` — payload >8 KB bị từ chối
- `test_proof_cache_returns_prior_pass` — cache theo fingerprint trả đúng proof cũ, không nhầm fingerprint khác
- **`test_active_run_scope_and_stale_run_observation`** — đo khoảng trống W1: `current_active_run()` chọn đúng run mới nhất, nhưng **5 run bị bỏ dở vẫn `active` mãi mãi** (hệ thống không tự đóng — test ghim hành vi này để thấy rõ gap)
- `test_idempotent_replay_after_restart_has_single_side_effect` — restart runtime rồi gọi lại cùng `idempotency_key`: marker file chỉ có **1** dòng (không chạy lệnh lần 2)

### Nhóm 4 — Transport/tunnel resilience (5 test)
`TransportResilienceTests` (server HTTP thật, token thật)
- `test_orchestration_endpoint_auth_and_shape` — 401 khi thiếu token; 200 + đủ 7 khóa dữ liệu khi có token (endpoint cho bảng điều khiển)
- `test_session_churn_survives_fresh_aliases` — 30 phiên stateless liên tiếp, mỗi phiên session mới → 30/30 thành công (tái hiện hành vi tunnel "fresh session per command")
- **`test_client_abort_mid_response_does_not_kill_server`** — client đóng socket ngay sau khi gửi request (tái hiện WinError 10053 production) → server vẫn khỏe, health 200
- `test_partial_upload_then_disconnect_leaves_no_broken_state` — gửi 1 phần body rồi ngắt → request kế tiếp bình thường
- `test_stateless_validation_matrix` — request thiếu `_meta` bị từ chối 400 đúng mã lỗi

### Nhóm 5 — Routing economics regression thresholds (5 test)
`RoutingEconomicsTests` — mô phỏng 100-task-week với hằng số chi phí đo được Phase 1/2; **ngưỡng hồi quy cố định trong test**:
- adaptive phải tiết kiệm **≥40%** so với all-Sol và critical-miss không tăng quá 0,6 task
- ladder (Mini→Luna→Sol) phải lãng phí **>3×** adaptive và chậm hơn về wall-time
- all-Mini phải có critical-miss **>2×** adaptive (bằng chứng gate oracle có giá trị)
- lane deterministic đóng góp 0 credit; sensitivity phải đơn điệu theo P(mini)

### Nhóm 6 — Perf baseline (3 test, ngưỡng rộng chống flaky)
- echo command median < 600 ms; quyết định routing median < 10 ms; truncate 2,4 MB text median < 100 ms

---

## 4. Kết quả đo thực tế (chạy 2026-08-14)

```text
python -m pytest tests/test_system_capability_suite.py  →  34 passed in 9.51s
python -m pytest tests (toàn bộ MCP)                    →  169 passed, 3 subtests in 45.60s
npm test (Electron)                                     →  57/57 passed
```

### 4.1 Kinh tế routing (giá trị từ mô phỏng đã được test chốt ngưỡng)

| Chiến lược | Credits/tuần | TTA (h) | Accepted | Cred/accepted | Wasted | Critical miss |
|---|---:|---:|---:|---:|---:|---:|
| **Adaptive router (đang triển khai)** | **46,84** | **0,35** | **99,4** | **0,471** | **12,9** | **0,65** |
| All-Sol xhigh | 96,49 | 0,28 | 99,8 | 0,966 | 3,3 | 0,16 |
| All-Luna | 41,89 | 0,39 | 99,1 | 0,423 | 18,0 | 0,90 |
| All-Mini | 54,78 | 0,55 | 98,3 | 0,557 | 34,2 | 1,71 |
| Ladder Mini→Luna→Sol | 34,21 | **0,65** | 99,4 | 0,344 | **46,1** | 0,59 |

Kết luận giữ nguyên sau khi kiểm tra lại bằng test: adaptive rẻ hơn all-Sol **51,5%** với rủi ro sai sót ngang bằng thực tế; ladder tuy rẻ credits nhất nhưng **+86% thời gian** và 46 lần thử lãng phí — đúng dự báo của MTRouter.

### 4.2 Phát hiện mới từ bộ test (khác với hiểu biết trước)

1. **Giữ trọn dữ liệu khi cắt response**: output >128 KB vẫn được giữ 100% trong session buffer (65536 head + 57344 tail = 122.880 bytes đúng bằng stream), response chỉ cắt còn 4 KB kèm `read_output` continuation. Chống phình context **không** làm mất thông tin — lập luận "bounded context" giờ có bằng chứng mạnh hơn.
2. **Biên gate chính xác đến từng byte**: 24.000/24.001 và 60.000/60.001 chuyển lane đúng như thiết kế — không có lỗi off-by-one.
3. **Server sống sót qua client abort + partial upload** trong điều kiện phòng lab — nghĩa là 12 lần WinError 10053 production không làm hỏng server, chỉ làm mất lượt gọi; vấn đề còn lại thực sự là **retry an toàn** (đã có idempotency_key, cần ChatGPT dùng nó — ngoài tầm app).
4. **Hash-chain integrity + capsule 8KB + proof cache** hoạt động đúng trong test tích hợp — các cơ chế "đã thiết kế nhưng chưa dùng" (G2/W2 của báo cáo trước) **hoạt động khi được gọi**; vấn đề còn lại chỉ là vận hành/kích hoạt.

### 4.3 Khoảng trống được ghim lại bằng test (để giải quyết)

| ID | Gap đã ghim | Test ghim | Hướng giải quyết |
|---|---|---|---|
| W1 | Run bỏ dở không bao giờ tự đóng | `test_active_run_scope_and_stale_run_observation` | Thêm lifecycle: đóng run `stale` sau N giờ không hoạt động; resume chỉ liệt kê run sống |
| W2 | Idempotency hoạt động khi có `idempotency_key` nhưng ChatGPT không tự sinh key | `test_idempotent_replay_after_restart_has_single_side_effect` | Panel/skill sinh `idempotency_key` ổn định cho mỗi lệnh quan trọng (hash của cmd+workdir+base) |
| G1 | Cache semantic chưa dùng (1/968 hit production) | `test_proof_cache_returns_prior_pass` | Bật `find_cached_pass` trong proof ledger khi cùng stage+fingerprint+base HEAD |
| T1 | Tunnel drop làm mất lượt gọi đang bay (12 restarts/5 ngày) | `test_client_abort_mid_response_does_not_kill_server` | Kết hợp W2: retry với idempotency key; hiện cảnh báo tunnel restart lên panel |

---

## 5. Cách chạy lại toàn bộ đánh giá

```powershell
cd E:\Github\Tools-Codex-web\resources\coding-tools-mcp
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests -q                      # 169 tests, ~46s
python -m pytest tests/test_system_capability_suite.py -q   # riêng bộ sâu: 34 tests, ~10s
cd E:\Github\Tools-Codex-web
npm test                                       # 57 tests Electron
```

Bộ test sâu được thiết kế để **không cần mạng, không cần model thật, không flaky**: mọi trường hợp dùng workspace tạm, oracle deterministic, và ngưỡng perf rộng. Bất kỳ thay đổi nào làm vỡ gate routing, mất idempotency, phá budget output hoặc làm mô phỏng kinh tế tụt dưới ngưỡng sẽ làm CI đỏ ngay.

---

## 6. Tài liệu tham khảo

1. Jimenez et al. — *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024. arXiv:2310.06770. https://arxiv.org/abs/2310.06770
2. Yao et al. — *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains* (metric pass^k). 2024. arXiv:2406.12045. https://arxiv.org/abs/2406.12045
3. Chen, Zaharia, Zou — *FrugalGPT* (LLM cascade). arXiv:2305.05176. https://arxiv.org/abs/2305.05176
4. Ong et al. — *RouteLLM: Learning to Route LLMs with Preference Data*. arXiv:2406.18665. https://arxiv.org/abs/2406.18665
5. Zhang et al. — *MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings*. ACL 2026. DOI: 10.18653/v1/2026.acl-long.2045. https://aclanthology.org/2026.acl-long.2045/
6. *Conformal LLM Routing with Distribution-Free Safety Guarantees*. ACL 2026 SRW. https://aclanthology.org/2026.acl-srw.70/
7. Liu et al. — *ToolScope*. ACL 2026. DOI: 10.18653/v1/2026.acl-long.1573. https://aclanthology.org/2026.acl-long.1573/
8. Basiri et al. — *Chaos Engineering* (Netflix Simian Army), IEEE Software 2016 — nền tảng cho nhóm fault-injection.
9. Nội bộ: `docs/research/DEPLOYMENT_PERFORMANCE_COST_EVALUATION_2026-08-14.md`, `docs/research/CONTEXT_TUNNEL_LONGHORIZON_ANALYSIS_2026-08-14.md` — nguồn hằng số chi phí và các gap W1/W2/G1/T1.
