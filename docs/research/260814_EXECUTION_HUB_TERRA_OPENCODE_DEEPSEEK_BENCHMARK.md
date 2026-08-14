# 260814 — Execution Hub: Terra vs Sol + OpenCode Go + DeepSeek V4 Flash/Pro

**Ngày:** 2026-08-14  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**Base HEAD:** `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`  
**Trạng thái:** benchmark live + tích hợp OpenCode Go đã qua proof/canary; chưa thay production routing threshold.  

---

## 1. Mục tiêu

Đợt này mở rộng benchmark Execution Hub theo hai hướng:

1. So sánh **GPT-5.6 Terra** với **GPT-5.6 Sol** ở workload cross-file/deep, bao gồm đúng tổ hợp người dùng quan tâm: **Terra xhigh + deep_code** so với **Sol high + deep_code**.
2. Kết nối **OpenCode Go** vào cùng Execution Hub và kiểm thử live **DeepSeek V4 Flash** cùng **DeepSeek V4 Pro**.
3. Tách riêng ba lớp số liệu để tránh kết luận sai:
   - **official public pricing/capability**;
   - **model/evidence-packet measurement**;
   - **end-to-end frontend + MCP + Hub measurement**.
4. Xác định vị trí vận hành phù hợp của Mini, Luna, Flash, Pro, Terra và Sol mà không tạo serial fallback ladder đắt đỏ.

Không thực hiện commit, push, release, deploy, restart runtime hoặc thay routing threshold trong đợt này.

---

## 2. Kết luận ngắn

### 2.1 Terra vs Sol

- **Terra xhigh** đã cho chất lượng đúng đầy đủ trên các evidence packet sâu, với chi phí thấp hơn Sol rõ rệt.
- **Sol high** nhanh hơn Terra xhigh trên cùng `deep_code` packet, nhưng tốn credits cao hơn.
- **Sol xhigh** nhanh nhất ở fixed packet xhigh cùng chất lượng, nhưng chi phí cao nhất.
- Trong autonomous repo exploration 30 giây, cả Terra xhigh và Sol xhigh đều chạm deadline; Terra tiêu ít credits hơn rất nhiều. Điều này cho thấy vấn đề không chỉ là model mạnh/yếu mà còn là **topology + packet localization**.
- Chưa đủ mẫu để auto-promote Terra thành production route mặc định.

### 2.2 DeepSeek V4 Flash vs Pro

- Cả Flash và Pro đều kết nối thật qua OpenCode Go và gọi cùng Coding Tools MCP/Execution Hub.
- Cả hai đều đọc được structured Hub result sau compatibility fix.
- Fixed evidence packet: cả hai trả đúng yêu cầu, confidence high.
- Pro nhanh hơn nhẹ trong model-event packet, nhưng chi phí quan sát cao hơn Flash khoảng 6.15× trong sample đó.
- Giá public hiện tại của Pro cao hơn Flash khoảng 3.11× ở cache-miss input/output; Flash có concurrency public cao hơn và OpenCode Go ước lượng request allowance lớn hơn nhiều.
- Flash phù hợp high-volume/parallel/bounded investigation; Pro phù hợp escalation cho open-model task khó hơn.

### 2.3 Kiến trúc điều phối

Không nên dùng ladder:

```text
Mini -> Luna -> Flash -> Pro -> Terra -> Sol
```

Nên route trực tiếp theo task class/evidence:

```text
                         ChatWeb Sol
                semantic control + final accept
                              |
                              v
                       EXECUTION HUB
             durable task/run/write/proof truth
                /        |         |        \
               /         |         |         \
      deterministic   Codex lanes  OpenCode   proof
                       /   |   \      Go
                    Mini Luna Terra/Sol  \
                                      Flash/Pro
```

---

## 3. Evidence classes

### 3.1 Live local measurement

Các số thời gian/credits/lane/proof trong tài liệu này là số đo thực trên workspace hiện tại, trừ nơi ghi rõ là official public pricing.

### 3.2 Official public pricing/capability

Nguồn chính thức được kiểm tra trong ngày 2026-08-14:

- OpenCode Go: `https://opencode.ai/docs/go/`
- OpenCode Zen pricing/model endpoints: `https://opencode.ai/docs/zen/`
- DeepSeek Models & Pricing: `https://api-docs.deepseek.com/quick_start/pricing/`

Pricing public có thể thay đổi; không dùng bảng này làm accounting cố định lâu dài nếu chưa refresh nguồn.

### 3.3 Không trộn billing plane

**Không so trực tiếp số `credits` của Codex App Server với USD/cost event của OpenCode Go.**

Có thể so:

- Terra vs Sol trong cùng Codex billing/estimation plane;
- Flash vs Pro trong cùng OpenCode Go event/billing plane;
- official price ratios trong cùng bảng public.

Không được nói `0.9 Codex credits` đắt/rẻ hơn `$0.009 OpenCode` như một phép so trực tiếp.

---

# PHẦN A — GPT-5.6 TERRA VS GPT-5.6 SOL

## 4. Public price hiện tại qua OpenCode Zen

Giá per 1M tokens theo bảng OpenCode Zen hiện tại:

| Model | Context tier | Input | Output | Cached read | Cached write |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 Sol | <=272K | $5.00 | $30.00 | $0.50 | $6.25 |
| GPT-5.6 Terra | <=272K | $2.00 | $12.00 | $0.20 | $2.50 |
| GPT-5.6 Sol | >272K | $10.00 | $45.00 | $1.00 | $12.50 |
| GPT-5.6 Terra | >272K | $4.00 | $18.00 | $0.40 | $5.00 |

Theo bảng này, Terra đang bằng **40% giá Sol** ở cả bốn dimension trên, tức thấp hơn khoảng **60%**.

Đây là public list pricing qua OpenCode Zen, không phải conversion của internal Codex credits.

---

## 5. Benchmark A1 — autonomous cross-file exploration, xhigh

### 5.1 Bài toán

Cùng prompt read-only yêu cầu model tự inspect bốn file thật:

- `electron/services/codexDesktopConfig.js`
- `resources/coding-tools-mcp/coding_tools_mcp/hub_proxy_stdio.py`
- `electron/services/hubProxyGateway.js`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`

Yêu cầu tái dựng end-to-end Codex Desktop -> Execution Hub -> Runtime, bearer ownership, hai fail-closed behaviors và một restart/race inference.

Deadline: **30s** cho cả hai.

### 5.2 Kết quả

| Metric | Terra xhigh | Sol xhigh |
|---|---:|---:|
| Model | `gpt-5.6-terra` | `gpt-5.6-sol` |
| Profile | `cross_file` | `deep_code` |
| Wall | 30.062s | 30.062s |
| Deadline | HIT | HIT |
| Terminal answer | Không | Không |
| Estimated credits | **0.336800** | **1.376575** |
| Input tokens | 13,634 | 21,887 |
| Cached input | 11,008 | 13,056 |
| Cache ratio | **80.74%** | 59.65% |
| Output tokens | 277 | 146 |
| Reasoning tokens | 52 | 30 |

### 5.3 Diễn giải

- Cả hai đều không hoàn thành trong 30s nên **không có cơ sở nói Terra tốt hơn Sol về correctness** ở sample này.
- Sol tiêu khoảng **4.09× credits** của Terra.
- Terra thấp hơn khoảng **75.5% credits** trong sample.
- Cache mix khác nhau nên không coi đây là pure model benchmark.
- Finding quan trọng nhất: autonomous repo exploration có thể làm cả model mạnh chạm deadline. Localize evidence trước khi dùng deep model thường hiệu quả hơn.

---

## 6. Benchmark A2 — fixed evidence packet, Terra xhigh vs Sol xhigh

### 6.1 Mục đích

Tách khả năng reasoning khỏi repo exploration overhead.

Hai model nhận **cùng một evidence packet**, không tool, không network, cùng câu hỏi 4 mục:

1. trust chain;
2. real bearer ownership;
3. strongest fail-closed property;
4. restart/race inference.

### 6.2 Kết quả

| Metric | Terra xhigh | Sol xhigh |
|---|---:|---:|
| Profile | `packet` | `packet` |
| Correctness | 4/4 | 4/4 |
| Confidence | high | high |
| Wall | 13.812s | **11.437s** |
| Estimated credits | **0.907188** | 1.737125 |
| Input tokens | 11,131 | 11,131 |
| Cached | 0 | 0 |
| Output tokens | 564 | 461 |
| Reasoning tokens | 350 | 287 |

### 6.3 Chênh lệch

- Sol xhigh nhanh hơn khoảng **17.2%**.
- Terra xhigh rẻ hơn khoảng **47.8%** theo internal estimated credits.
- Sol xhigh tốn khoảng **1.915× credits** của Terra.
- Correctness sample này ngang nhau.

### 6.4 Ý nghĩa

Khi evidence đã được localize tốt, Terra xhigh có profile economics hấp dẫn cho:

- cross-file review;
- architecture review;
- risk analysis;
- implementation planning;
- second-pass challenge/reviewer.

Sol xhigh vẫn hợp lý khi:

- scope thực sự rộng/ambiguous;
- autonomous integration khó;
- cần model mạnh nhất cho unresolved deep issue;
- cost/latency secondary so với defect risk.

---

## 7. Benchmark A3 — đúng yêu cầu Terra xhigh/deep_code vs Sol high/deep_code

### 7.1 Bài toán

Cùng fixed architecture evidence packet, cùng `deep_code` profile.

Yêu cầu:

- strongest invariant;
- 5-step restart-safe state machine;
- exactly 3 ranked failure modes + mitigation;
- vị trí đúng của OpenCode compatibility layer.

Không tool/network.

### 7.2 Kết quả

| Metric | Terra xhigh + deep | Sol high + deep |
|---|---:|---:|
| Model | `gpt-5.6-terra` | `gpt-5.6-sol` |
| Effort | **xhigh** | **high** |
| Profile | `deep_code` | `deep_code` |
| Correctness | đầy đủ | đầy đủ |
| Confidence | high | high |
| Wall | 28.360s | **19.061s** |
| Estimated credits | **1.259625** | 2.133750 |
| Input | 11,616 | 11,616 |
| Cached | 0 | 0 |
| Output | 1,423 | 909 |
| Reasoning | 1,034 | 516 |

### 7.3 Chênh lệch

- Sol high nhanh hơn khoảng **32.8%**.
- Terra xhigh rẻ hơn khoảng **41.0%**.
- Sol high tốn khoảng **1.69× credits** Terra xhigh.
- Terra dùng nhiều output/reasoning token hơn; đây chỉ là observation, **không đồng nghĩa reasoning token nhiều hơn = chất lượng tốt hơn**.
- Cả hai đều tìm đúng kiến trúc: compatibility phải ở stdio proxy, không làm bẩn gateway hoặc canonical runtime.

### 7.4 Chọn route thế nào

**Terra xhigh/deep** nếu ưu tiên:

- cost-efficient deep review;
- cần suy luận dài nhưng evidence đã tương đối rõ;
- architecture/risk/design work có thể chấp nhận latency thêm;
- muốn tránh Sol xhigh cho mọi deep task.

**Sol high/deep** nếu ưu tiên:

- latency tốt hơn trong deep packet;
- task có deadline tương tác;
- cần câu trả lời ngắn/gọn hơn nhưng vẫn sâu;
- cost cao hơn chấp nhận được.

**Sol xhigh/deep** giữ cho:

- broad integration;
- ambiguity cao;
- multi-subsystem root cause;
- consequential change;
- Terra/Sol-high vẫn chưa giải quyết được evidence gap.

---

## 8. Tạm xếp Terra trong router

Chưa bật auto-route, nhưng vị trí experimental hợp lý là:

```text
localized strong oracle        -> Mini
harder bounded leaf            -> Luna
cross-file evidence/reviewer   -> Terra high/xhigh [experimental]
deep time-sensitive design     -> Sol high
deep broad/ambiguous           -> Sol xhigh
```

Không serial cascade tất cả tier.

---

# PHẦN B — OPENCODE GO + DEEPSEEK V4

## 9. Environment live

Local machine đã xác nhận:

- OpenCode version: **1.18.18**
- OpenCode Go credential: có trong OpenCode credential store
- Live model catalog:
  - `opencode-go/deepseek-v4-flash`
  - `opencode-go/deepseek-v4-pro`

Credential value không được lưu vào repo.

---

## 10. Kiến trúc tích hợp OpenCode với Execution Hub

### 10.1 Project config

Tạo project-local `opencode.json`.

MCP frontend:

```text
OpenCode
  -> py.exe -3 resources/coding-tools-mcp/coding_tools_mcp/hub_proxy_stdio.py
     --structured-content-as-text
  -> Electron Execution Hub gateway
  -> same Coding Tools Runtime
```

Custom commands:

- `hub-flash` -> `opencode-go/deepseek-v4-flash`
- `hub-pro` -> `opencode-go/deepseek-v4-pro`

Không có API key trong file.

### 10.2 Descriptor resolution

Proxy giờ hỗ trợ:

1. explicit `--descriptor`;
2. `CODING_TOOLS_MCP_PROXY_DESCRIPTOR`;
3. fallback `%APPDATA%/web-mcp-assistant/execution-hub-proxy.json`.

Codex Desktop explicit path behavior không đổi.

### 10.3 Tại sao cần APPDATA fallback

Canary đầu tiên dùng JSON env substitution cho Windows path bị `InvalidEscapeCharacter`, vì backslash được chèn vào JSONC trước parse.

Fallback trong Python proxy loại bỏ machine-specific path khỏi `opencode.json` và tránh escape hazard.

### 10.4 Proof

Accepted integration run:

- run: `0f77cd3b2e5046b398f84465bac2a0f2`
- final accepted proof: `7e7776a77670419e8766dc67e13a20a5`
- proof fingerprint: `63372d8010d7805ee8490288d5124a456beb1cbe3ee715d764466cb3c7d09140`
- focused tests: `5 passed`

Live:

```text
opencode mcp list
coding-tools connected
```

---

## 11. structuredContent compatibility gap và fix

### 11.1 Gap thật

OpenCode 1.18.18 gọi Coding Tools MCP thành công nhưng model-facing tool result ban đầu chỉ chứa text summary kiểu:

```text
workspace_context: completed.
```

Canonical `structuredContent` có trong MCP response nhưng model không thấy dữ liệu chi tiết.

Cả Flash và Pro đã **đúng khi từ chối bịa field**.

### 11.2 Fix thử 1 — move structuredContent sang text

Unit test pass nhưng live canary fail:

```text
MCP -32600:
Tool workspace_context has an output schema but did not return structured content
```

Nguyên nhân: OpenCode SDK dùng `structuredContent` để validate `outputSchema` trước khi model thấy result.

Wave này bị reject, không accept chỉ vì unit test xanh.

### 11.3 Fix cuối — preserve + mirror

OpenCode-only compatibility mode:

- **giữ nguyên canonical `structuredContent`** để schema validation đúng;
- mirror JSON của structured payload vào text content block cho model;
- preserve non-text content;
- preserve `isError`;
- outbound response vẫn bị size-bound/fail-closed;
- default mode cho Codex Desktop không đổi.

### 11.4 Final proof

EOCL run:

- run: `31b80d1d320541cf908e586864d43979`
- accepted wave: `1b0bbed1448d4ed3a64574c3e8174ef2`
- proof ID: `c9f8c5cd8a1d4d9386727042117f23ec`
- proof fingerprint: `bd6cf8de9707b4abb06bd6728f2e6b0830e6d6f3f5cde5ed7de063194c937caf`
- focused oracle: `8 passed in 4.32s`
- final state: `CHECKPOINTED`

### 11.5 Semantic live canary

Sau fix, **Flash và Pro đều gọi `workspace_context(detail=full)` đúng một lần và đọc được chính xác**:

```text
project: web-mcp-assistant
branch: main
tool_mode: smart
process_instance_id: J1wGYtML6Bh50vb5
stale_orchestration_runs: 1
```

Đây là semantic PASS, không chỉ transport PASS.

---

## 12. DeepSeek V4 official capability

Theo DeepSeek official pricing/model docs hiện tại:

| Capability | V4 Flash | V4 Pro |
|---|---:|---:|
| Context length | 1M | 1M |
| Max output | 384K | 384K |
| Thinking | yes, default | yes, default |
| Non-thinking | yes | yes |
| JSON Output | yes | yes |
| Tool Calls | yes | yes |
| Anthropic API | yes | yes |
| Responses API | yes | official page hiện ghi chưa cho Pro |
| Public concurrency limit | **2500** | 500 |

OpenCode Go dùng OpenAI-compatible Chat Completions endpoint cho cả hai, nên Responses API difference không cản integration hiện tại.

---

## 13. DeepSeek public price hiện tại

### 13.1 Direct DeepSeek / OpenCode Go listed model price

| Price / 1M | V4 Flash | V4 Pro | Pro / Flash |
|---|---:|---:|---:|
| Cache-hit input | $0.0028 | $0.003625 | ~1.29× |
| Cache-miss input | $0.14 | $0.435 | ~3.11× |
| Output | $0.28 | $0.87 | ~3.11× |

### 13.2 OpenCode Go allowance estimate

Official Go table hiện ước tính theo typical request pattern:

| Window | V4 Flash | V4 Pro |
|---|---:|---:|
| 5 hours | **31,650** | 3,450 |
| week | **79,050** | 8,550 |
| month | **158,150** | 17,150 |

Flash vì rẻ hơn nên có request allowance ước tính lớn hơn khoảng 9× theo bảng hiện tại.

Go hiện có subscription $5 tháng đầu, sau đó $10/tháng; usage limits được quy đổi theo dollar value và có thể thay đổi.

---

## 14. Benchmark B1 — fixed packet Flash vs Pro

### 14.1 Bài toán

Cùng trust-chain evidence packet như Terra/Sol; không tool, không network.

Yêu cầu 4 finding + confidence.

### 14.2 Kết quả model-event

| Metric | DeepSeek V4 Flash | DeepSeek V4 Pro |
|---|---:|---:|
| Correctness | đạt yêu cầu | đạt yêu cầu |
| Confidence | high | high |
| Model-event wall | ~12.175s | **~11.490s** |
| OpenCode reported cost | **$0.0015172** | $0.00933565 |
| Input tokens | 19,333 | 20,489 |
| Output tokens | 282 | 267 |
| Reasoning tokens | 872 | 217 |
| Cache read | 1,664 | 512 |

### 14.3 Diễn giải

- Pro nhanh hơn khoảng **5.6%** trong model-event sample.
- Pro tốn khoảng **6.15× reported cost** trong sample này.
- Flash rẻ hơn khoảng **83.8%** theo OpenCode event cost quan sát.
- Cache/token mix khác nhau, vì vậy 6.15× là **sample observation**, không thay thế public list-price ratio ~3.11×.
- Cả hai đều đủ tốt cho packet này.
- Pro wording thận trọng hơn ở fail-closed property; Flash có một câu diễn đạt hơi quá mạnh về khả năng misuse gateway token, dù conclusion chính vẫn đúng.

---

## 15. Benchmark B2 — live Hub semantic tool use

### 15.1 Mục đích

Chứng minh model không chỉ “có MCP”, mà thật sự đọc structured state của Execution Hub.

### 15.2 Flash full canary

- tool: `coding-tools_workspace_context`
- detail: `full`
- tool call: completed
- model trả đúng cả 5 field
- CLI wall: ~26.15s
- model-event from first step start to final step finish: ~7.48s
- reported cost của hai model steps cộng lại: ~`$0.0005922`
- sample có cache cao; không dùng làm fair Flash/Pro cost A/B.

### 15.3 Pro full canary

- cùng tool/prompt/fields
- tool call: completed
- model trả đúng cả 5 field
- model-event from first step start to final step finish: ~10.81s
- reported cost hai model steps: ~`$0.0069915`
- cache mix khác Flash; không dùng sample này để nói Pro chậm/rẻ hơn về intrinsic model.

### 15.4 Kết luận canary

**OpenCode Go + Flash/Pro + Execution Hub semantic path = LIVE PASS.**

---

# PHẦN C — SO SÁNH VẬN HÀNH TỔNG THỂ

## 16. Ma trận model theo vai trò

| Route | Điểm mạnh thực dụng | Điểm yếu/rủi ro | Vị trí khuyến nghị |
|---|---|---|---|
| Deterministic | rẻ, proof rõ | không reasoning | inspect/apply/test/proof trước |
| Mini | cực hiệu quả cho localized strong-oracle | nhạy packet/path/orchestration | leaf bug/test |
| Luna | ổn định hơn Mini cho bounded harder leaf | đắt hơn Mini | harder bounded leaf |
| DS V4 Flash | cực rẻ, high-volume, tool-capable, 1M context | hard task có thể kém Pro; output cần proof | parallel investigation/reviewer, cheap first pass |
| DS V4 Pro | open model mạnh hơn cho harder task | giá public ~3.11× Flash input/output | escalation trong OpenCode plane |
| Terra xhigh | deep reasoning economics tốt, public Zen 40% giá Sol | có thể chậm; autonomous 30s sample timeout | cross-file/deep reviewer/planner experimental |
| Sol high | deep packet nhanh, concise | credits cao | time-sensitive deep design |
| Sol xhigh | strongest reserve lane cho broad/ambiguous | đắt, dễ overkill | broad/deep/high-risk integration |

---

## 17. Không dùng serial ladder

### Sai

```text
Mini fail
 -> Luna
 -> Flash
 -> Pro
 -> Terra
 -> Sol high
 -> Sol xhigh
```

Đây là cách tối đa hóa wasted attempts.

### Đúng

Route theo evidence:

```text
if deterministic/proof-only:
    MCP only
elif localized + strong oracle:
    Mini
elif bounded leaf nhưng khó hơn:
    Luna
elif cheap independent investigation / parallel review:
    DeepSeek V4 Flash
elif open-model task harder và Flash evidence không đủ:
    DeepSeek V4 Pro
elif cross-file evidence-heavy review/planning:
    Terra high/xhigh experimental
elif deep design cần latency/quality cao:
    Sol high
elif broad, ambiguous, consequential deep integration:
    Sol xhigh
```

Sau model output:

```text
MCP apply/prove
 -> ChatWeb Sol final semantic acceptance
```

---

## 18. Phương án phối hợp nhiều frontend

### 18.1 ChatWeb Sol

Vai trò:

- hiểu intent người dùng;
- phân loại task;
- chọn route;
- đọc proof/critical evidence;
- final acceptance/reject/replan.

Không cần giữ một conversation vô hạn để làm execution state.

### 18.2 Execution Hub

Vai trò:

- durable task/run state;
- write lease;
- idempotency;
- proof;
- handoff;
- client-neutral execution truth.

### 18.3 Codex Desktop

Vai trò:

- persistent OpenAI/Codex coding frontend;
- long-lived context;
- deep interactive implementation lane.

### 18.4 OpenCode Go

Vai trò:

- thêm open-model execution/review plane;
- V4 Flash cho throughput/cost;
- V4 Pro cho harder open-model tasks;
- cùng MCP Hub, không tạo execution truth riêng.

---

## 19. Routing proposal sau benchmark

### Tier 0 — deterministic

Luôn ưu tiên nếu bài toán đã deterministic.

### Tier 1 — Mini

Localized, strong oracle, patch nhỏ.

### Tier 2 — Luna

Bounded leaf nhưng Mini confidence thấp hoặc task có branching khó hơn.

### Side lane F — DeepSeek V4 Flash

Không phải tier “sau Luna”. Dùng song song/độc lập cho:

- read-only research trên repo;
- code review bounded;
- issue hypothesis;
- cheap candidate explanation;
- parallel challenger;
- large-context but straightforward synthesis.

### Side lane P — DeepSeek V4 Pro

Escalate từ Flash **chỉ khi có lý do**:

- failure evidence cho thấy reasoning gap;
- cross-file interaction khó;
- tool-plan phức tạp;
- Flash output không đủ confidence/proofability.

### Tier T — Terra experimental

Dùng cho:

- cross-file architecture review;
- deep evidence packet;
- migration/implementation planning;
- risk/permission/restart analysis;
- reviewer trước Sol.

### Tier S — Sol

`Sol high`:

- deep design cần latency tốt;
- architecture packet đã localize.

`Sol xhigh`:

- broad autonomous integration;
- ambiguity lớn;
- deep root cause;
- consequential/high-risk change;
- final deep route khi cheaper route không đủ.

---

# PHẦN D — TEST PLAN TIẾP THEO

## 20. Mục tiêu test phase tiếp theo

Không còn mục tiêu “model nào trả lời hay hơn trong một prompt”.

Mục tiêu phải là:

> **accepted useful result / time / total cost / defect risk**

trên cùng task class và cùng deterministic oracle.

---

## 21. Task classes đề xuất

### T1 — Localized bug + strong oracle

Mục tiêu:

- baseline Mini/Luna;
- Flash candidate reviewer;
- không dùng Sol/Terra nếu không cần.

### T2 — Cross-file diagnose

4–8 file, không mutation ở vòng đầu.

So:

- Flash
- Pro
- Terra xhigh
- Sol high

Oracle: known root cause + required evidence locations.

### T3 — Cross-file implementation

2–5 file mutation, focused test.

So:

- Pro
- Terra xhigh
- Sol high

MCP vẫn apply/prove; model không trực tiếp làm writer ngoài contract.

### T4 — Deep architecture/restart/recovery

So đúng:

- Terra xhigh + deep_code
- Sol high + deep_code
- Sol xhigh + deep_code

Oracle chấm:

- invariant completeness;
- restart semantics;
- idempotency/replay safety;
- critical defect count.

### T5 — Large-context synthesis

Dùng packet/file set lớn nhưng read-only.

So:

- Flash
- Pro
- Terra xhigh
- Sol high

Đo cache reuse và continuation economics.

### T6 — Recovery after typed failure

Cố ý tạo các failure class hợp lệ:

- target localization error;
- proof path mismatch;
- model timeout;
- stale descriptor/reconnect;
- ambiguous in-flight write.

Đo model/router có **replan đúng loại** hay chỉ nâng tier vô ích.

---

## 22. Metrics bắt buộc

Cho mỗi accepted task:

```text
route
model
model effort/profile
task class
first-pass | repaired
model wall time
end-to-end TTA
input/output/reasoning/cache
model/provider cost
orchestration retry count
MCP tool-call count
proof duration
proof pass/fail
critical defect count
final acceptance status
```

Thêm hai metric quan trọng:

### 22.1 Total cost per accepted result

Không chỉ model-call cost.

```text
sum(all attempts + repair + proof overhead attributable to task)
/
accepted result
```

### 22.2 Orchestration tax

```text
end-to-end TTA - useful model wall - deterministic proof wall
```

và:

```text
wasted model cost caused by packet/path/protocol/replay defects
```

---

## 23. Suggested evidence gate

Đây là **đề xuất test gate**, chưa phải production policy:

- ít nhất 10 accepted useful tasks cho mỗi route muốn promote;
- tối thiểu 3 task classes;
- không chỉ synthetic no-op;
- critical defects = 0 trong promotion sample;
- cohort metadata coverage = 100%;
- compare homogeneous class, không compare global p50 lẫn lộn;
- report first-pass và repaired tách riêng;
- auto-route chỉ sau khi cost/accepted + TTA + defect rate đều có lợi thế rõ.

---

## 24. Terra promotion gate đề xuất

Terra có thể tiến từ experimental sang recommended cross-file route nếu:

1. >=10 accepted representative tasks;
2. ít nhất 5 cross-file diagnose/review tasks;
3. >=90% first-pass ở strong-evidence cohort hoặc chứng minh cost/accepted tốt hơn Sol-high đáng kể;
4. không tăng critical defect rate;
5. p90 không bị deadline pathology quá cao;
6. autonomous timeout rate được đo riêng khỏi packet-localized rate.

Không promote chỉ vì Terra rẻ hơn trong 2–3 packet.

---

## 25. DeepSeek Flash promotion gate đề xuất

Flash có thể trở thành default cheap read-only/parallel reviewer nếu:

1. semantic MCP tool-use success >=99% trong controlled suite;
2. structuredContent mirror không gây schema/size regression;
3. >=10 representative tasks;
4. accepted/correct rate đủ cao ở simple/moderate class;
5. total cost/accepted tốt hơn Pro rõ rệt;
6. hard-task fallback được typed, không serial retry mù.

---

## 26. DeepSeek Pro promotion gate đề xuất

Pro chỉ cần rộng hơn Flash nếu nó chứng minh:

- giảm repaired-task rate trên hard cohort;
- tăng first-pass accepted rate đủ bù ~3.11× public input/output price;
- hoặc rút ngắn TTA đáng kể ở task quan trọng.

Nếu correctness ngang Flash trên simple task, không có lý do dùng Pro mặc định.

---

# PHẦN E — SECURITY / OPERATIONS

## 27. Credential handling

Trong quá trình kiểm tra OpenCode, lệnh debug config của CLI đã hiển thị credential values trong tool output.

**Không lặp lại các giá trị đó trong tài liệu này.**

Khuyến nghị vận hành:

- rotate các provider credentials đã xuất hiện trong debug output;
- không lưu credential vào `opencode.json`;
- tiếp tục dùng OpenCode credential store;
- không đưa real MCP bearer vào frontend config;
- không đưa bearer vào docs/log/report.

---

## 28. Contract safety

OpenCode integration không thay public MCP tool count.

Expected contract vẫn:

```text
profile: smart-v3
tool_count: 8
sha256: 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
```

OpenCode compatibility nằm ở stdio presentation boundary, không đổi canonical Runtime tool schema.

---

## 29. Remaining known state

- historical `stale_orchestration_runs = 1` vẫn tồn tại;
- không mass-clean khi chưa kiểm provenance;
- không có lý do restart runtime cho OpenCode config/proxy source vì OpenCode spawn proxy process mới theo project config;
- Codex Desktop default proxy mode không đổi.

---

# PHẦN F — DECISION

## 30. Quyết định hiện tại

| Hạng mục | Quyết định |
|---|---|
| Execution Hub multi-frontend | **GO** |
| Codex Desktop frontend | **GO** |
| OpenCode frontend | **GO — LIVE semantic PASS** |
| DeepSeek V4 Flash | **GO cho bounded/high-volume/read-only + evidence gathering** |
| DeepSeek V4 Pro | **GO cho harder open-model tasks, không default** |
| Terra xhigh packet/deep | **GO experimental** |
| Terra auto-route production | **HOLD — cần cohort lớn hơn** |
| Sol high/deep | **GO cho latency-sensitive deep design** |
| Sol xhigh/deep | **GO reserve cho broad/ambiguous/high-risk** |
| Serial multi-model cascade | **NO-GO** |
| Auto-handoff | giữ **OFF** cho tới khi có đủ representative A/B |
| Routing threshold change ngay | **NO** |

---

## 31. Recommended operating policy

```text
1. ChatWeb Sol phân loại task và acceptance contract.
2. Execution Hub giữ durable truth.
3. Deterministic trước khi gọi model nếu có thể.
4. Mini/Luna cho bounded implementation leaves.
5. Flash là cheap parallel/open-model investigator.
6. Pro là evidence-driven escalation trong OpenCode plane.
7. Terra xhigh là experimental deep/cross-file reviewer/planner.
8. Sol high cho deep task cần latency tốt.
9. Sol xhigh chỉ cho broad/ambiguous/consequential deep task.
10. MCP apply/prove; ChatWeb Sol accept/reject/replan.
```

---

## 32. Bottom line

**Terra không thay Sol theo nghĩa tuyệt đối.** Trong các sample hiện tại, Terra xhigh cho quality ngang ở fixed deep packets với economics tốt hơn, nhưng chậm hơn Sol high/xhigh; autonomous exploration vẫn có thể timeout. Vị trí tốt nhất hiện tại là một **cost-efficient deep/cross-file lane trước Sol**.

**DeepSeek V4 Flash không phải bản Pro rẻ hơn đơn thuần.** Flash có economics và throughput rất mạnh, đủ chất lượng cho simple/moderate agent/review tasks; Pro nên được trả thêm tiền khi harder cohort chứng minh gain về first-pass/correctness/TTA.

**OpenCode Go đã trở thành frontend thứ ba dùng cùng Execution Hub**, không tạo một execution silo mới. Đây là phần quan trọng nhất về tổ chức phối hợp: model/provider có thể thay đổi, nhưng write/proof/task truth vẫn tập trung ở Hub.
