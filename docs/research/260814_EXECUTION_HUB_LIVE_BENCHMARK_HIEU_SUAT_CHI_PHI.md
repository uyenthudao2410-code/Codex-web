# 260814 — Execution Hub + ChatWeb + Codex Desktop: Benchmark live hiệu suất, chi phí và phương án điều phối

**Ngày thực hiện:** 2026-08-14  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**Base HEAD:** `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`  
**Mục tiêu:** kiểm chứng Execution Hub đã hoạt động live với đường Codex Desktop MCP, đo chi phí/thời gian của các route, đo lợi ích continuation/cache, đánh giá orchestration overhead và chốt phương án phối hợp vận hành tiếp theo.  
**Phạm vi:** benchmark + tài liệu; không thay đổi routing threshold production, không bật auto-handoff, không commit/push/release/deploy/restart trong đợt benchmark này.

---

## 1. Kết luận điều hành

Execution Hub **đã hoạt động ở mức functional live** cho mục tiêu cốt lõi đã đặt ra:

```text
ChatWeb ─────────────┐
                     │
                     ▼
             ONE Coding Tools Runtime
                     ▲
                     │
Codex Desktop ─ thin proxy ─ Electron gateway
```

Các bằng chứng live quan trọng nhất:

- Codex Desktop Windows AppX đã được xác nhận cài đặt: `OpenAI.Codex 26.803.10989.0`.
- `~/.codex/config.toml` đã được cấu hình `mcp_servers.coding-tools` theo thin-proxy, không chứa MCP bearer.
- Native Codex process đã từng được quan sát spawn đúng `py.exe -3 -m coding_tools_mcp.hub_proxy_stdio`; parent process là `codex.exe`.
- Thin-proxy qua descriptor live trả được `tools/list` với đúng 8 tool `smart-v3` của **shared Runtime**.
- ChatWeb ghi handoff capsule và đọc lại nguyên vẹn qua đường `codex-desktop → thin proxy → Electron gateway → same MCP Runtime`.
- Capsule round-trip live giữ nguyên ID, SHA-256, payload và durable state.

Điểm cần nói chính xác: benchmark chứng minh **adapter path của Codex Desktop và shared execution truth hoạt động**. ChatWeb không có authority để chiếm hoặc quan sát tùy ý một arbitrary live native Codex Desktop UI turn, nên tài liệu này không tuyên bố điều đó.

Về model economics, kết quả live củng cố mạnh định hướng đã nghiên cứu trước đây:

- **Mini** rất hiệu quả cho localized strong-oracle leaf khi packet/path đúng và cache tốt.
- **Luna** đắt hơn Mini nhưng ổn định hơn trong các leaf khó vừa và ít nhạy với cache hơn trong sample này.
- **Sol xhigh deep-code** không nên dùng cho trivial leaf: cùng bài toán đầu tiên, Sol chạm deadline 30 giây, tiêu `0.94885` credits nhưng không sinh accepted candidate.
- **Same-thread continuation** tiếp tục cho lợi ích rất lớn: cùng prompt A2, warm Mini lane rẻ hơn fresh Mini lane khoảng **75.6%**, nhanh hơn khoảng **16.3%**, cache tăng **79.41 điểm phần trăm**.
- Hiệu quả hệ thống không chỉ phụ thuộc tier model. Một lỗi packet/path hoặc proof working-directory có thể làm Mini từ rẻ hơn thành **đắt hơn Luna** dù model hiểu bài đúng.

Do sample accepted hiện mới là Mini `n=2` first-pass và Luna `n=3` first-pass, **không thay đổi production routing threshold** ở thời điểm này. Đây là bằng chứng khởi đầu hợp lệ cho P2 calibration, chưa phải calibration hoàn tất.

---

## 2. Phân loại bằng chứng

Để tránh trộn benchmark giả lập với đo production-style, toàn bộ kết luận trong tài liệu này được chia thành bốn lớp:

| Lớp | Ý nghĩa | Có trong đợt này |
|---|---|---|
| Live system evidence | Process/config/RPC/capsule thực trên máy hiện tại | Có |
| Accepted-result benchmark | Model candidate → MCP apply → deterministic proof → ChatWeb Sol accept | Có |
| Continuation A/B | Cùng model/cùng prompt, warm thread so với fresh thread | Có |
| Scenario simulation | 100-task giả lập từ assumptions + router thật | Có, nhưng không dùng như production A/B |

Credits trong benchmark là **estimated credits** theo `codex_rate_card_observed_2026-08-12`; đây không phải hóa đơn tiền thật từ OpenAI.

---

## 3. Trạng thái live Codex Desktop MCP

### 3.1 Cấu hình

Config đã được thêm vào `C:\Users\Admin\.codex\config.toml` theo dạng:

```toml
[mcp_servers.coding-tools]
command = 'py.exe'
args = [
  '-3',
  '-m',
  'coding_tools_mcp.hub_proxy_stdio',
  '--descriptor',
  'C:\Users\Admin\AppData\Roaming\web-mcp-assistant\execution-hub-proxy.json'
]
env = {
  PYTHONPATH = 'E:\DEV\Tools-Codex-web\resources\coding-tools-mcp\python_vendor;E:\DEV\Tools-Codex-web\resources\coding-tools-mcp'
}
```

Backup trước khi sửa:

```text
C:\Users\Admin\.codex\config.toml.bak-execution-hub-20260814
```

Security invariant được giữ:

```text
Codex config
    có gateway descriptor
    KHÔNG có real MCP bearer

Electron SecretStore
    giữ real MCP bearer
```

### 3.2 Process proof

Native Codex activation đã được quan sát với chuỗi parent/child:

```text
codex.exe
  └─ py.exe -3 -m coding_tools_mcp.hub_proxy_stdio ...
       └─ python.exe ...hub_proxy_stdio...
```

Điều này chứng minh Codex Desktop đã parse config MCP mới và tự spawn đúng adapter, không phải một manual test process được giả làm Desktop.

### 3.3 RPC proof

Canary qua exact thin-proxy path trả `tools/list` thành công và thấy đúng public surface:

```text
workspace_context
agent_workflow
task_control
command_control
document_workflow
exec_command
request_permissions
view_image
```

Runtime contract vẫn là:

```text
profile        smart-v3
schema_version 1
tool_count     8
sha256         4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
```

Kết luận: **Codex Desktop MCP path hoạt động.**

---

## 4. Cross-client continuity canary

Đây là test quan trọng nhất cho mục tiêu “1 Hub — 2 mặt trận”.

### 4.1 ChatWeb ghi capsule

ChatWeb ghi handoff capsule:

```text
capsule_id = c2a7c0403133426ab142fc939aded6c6
bytes      = 1438
sha256     = b993fee1d9eab010cbcaa616bfdd9cfa0ed17fa77aed90ee425fabb1da1e114b
```

Payload có marker:

```text
benchmark = execution-hub-live-20260814
purpose   = cross-client continuity canary
```

### 4.2 Đọc lại qua đường Codex Desktop thin-proxy

Sau đó request được gửi qua:

```text
hub_proxy_stdio
    ↓
Electron HubProxyGateway
    ↓
shared Coding Tools Runtime
    ↓
task_control(handoff=get)
```

Kết quả trả về **cùng capsule ID, cùng SHA-256, cùng payload**.

Cold one-shot elapsed cho request này khoảng `1.226s`; số này bao gồm Python process/module startup nên không phải steady-state gateway RTT.

### 4.3 Ý nghĩa

Test này chứng minh live:

```text
ChatWeb durable state
       ==
Codex Desktop adapter durable state
```

Không cần copy transcript để hai mặt trận thấy cùng task checkpoint.

---

## 5. Benchmark transport/Hub overhead

Đợt này chưa có một timer chuyên dụng nằm bên trong resident native Codex proxy, nên không được gọi các số dưới đây là “pure network latency”. Ta chỉ có cold-process operational measurements.

### 5.1 Cold thin-proxy ping

5 lần one-shot:

```text
Python process
→ import hub_proxy_stdio
→ read descriptor
→ Electron loopback gateway
→ MCP ping
→ response
```

Tổng: `2598 ms`  
Trung bình: khoảng **519.6 ms/call**.

### 5.2 Startup baseline

5 lần `py.exe -3 --version`:

```text
304 ms total ≈ 60.8 ms/process
```

5 lần load module `hub_proxy_stdio --help`:

```text
1085 ms total ≈ 217 ms/process + module load
```

Lấy cold full ping trừ module-start baseline cho một ước lượng thô:

```text
519.6 - 217 ≈ 302.6 ms
```

Khoảng `~303 ms` này bao gồm descriptor read + gateway + loopback HTTP + upstream MCP + JSON processing + measurement noise.

**Không được hiểu nó là steady-state native Desktop RTT.** Resident proxy được thiết kế để sống lâu và heartbeat mỗi 15 giây; cần instrument trực tiếp để có p50/p90 steady-state thật ở phase sau.

### 5.3 Đánh giá

So với model wall-time trong benchmark leaf khoảng `4.8–8.6s`, cold Hub adapter tax nằm ở cấp vài trăm mili-giây. Về order-of-magnitude, Hub không làm mất lợi ích model routing.

Tuy nhiên việc spawn proxy mới cho từng request sẽ là sai topology. Production phải giữ resident proxy/session như thiết kế hiện tại.

---

## 6. Paired benchmark #1 — clamp/normalize leaf

### 6.1 Oracle

Ba fixture Mini/Luna/Sol giống nhau. Code sai có hai return boundary bị đảo. Deterministic oracle kiểm:

```text
normalize_score(-5)  == 0
normalize_score(50)  == 50
normalize_score(120) == 100
```

Cả ba fixture đều RED trước khi tiêu model credits.

### 6.2 Kết quả

| Route | Outcome | Model wall | Credits | Cache | Proof | Accepted |
|---|---:|---:|---:|---:|---:|---:|
| Mini low | PASS first-pass | 7.281s | 0.178478 | 14.59% | 105ms PASS | Có |
| Luna high | PASS first-pass | 8.625s | 0.297000 | 0% | 109ms PASS | Có |
| Sol xhigh deep_code | Deadline | 30.015s | 0.948850 | 80.99% | Không có | Không |

Mini run:

```text
run   9c97e07fc63647cda4320dfce9b0afa8
wave  ae8ace7f814c4cd08159be383df9da4b
proof 6d31b522d4ff4c50ab71bd9a6e32650a
```

Luna run:

```text
run   2bdad163116a43fc8b85701257f99235
wave  e8d7104c64ec411890473fc2a34e658f
proof bff6774cfd284ba7a396fbdc6e6a0e2a
```

Sol run:

```text
run  7ac656c66c064c58a6349f90c1a49987
wave 8858c189ac194b84a82cd549fc499705
final state ABORTED after preserving deadline evidence
```

### 6.3 So sánh

Mini so với Luna trên cùng task:

```text
credits: 0.178478 vs 0.297
Mini rẻ hơn ≈ 39.9%

model wall: 7.281s vs 8.625s
Mini nhanh hơn ≈ 15.6%
```

Sol xhigh so với Mini:

```text
credits ratio ≈ 5.32x
model wall ratio ≈ 4.12x
accepted result = NO
```

Sol xhigh so với Luna:

```text
credits ratio ≈ 3.19x
model wall ratio = 3.48x
accepted result = NO
```

Finding quan trọng: Sol có cache `80.99%` nhưng vẫn chạm deadline. Đây là bằng chứng rằng **cache tốt không cứu được một topology sai cho task class**.

---

## 7. Paired benchmark #2 — remaining capacity

Bài toán:

```python
def remaining_capacity(limit, used):
    return min(limit - used, 0)
```

Ý định đúng:

```text
remaining = max(limit - used, 0)
```

### 7.1 Luna

Luna được chạy với full workspace-relative path ngay từ đầu:

```text
wall    4.875s
credits 0.281800
cache   0%
proof   105ms PASS
outcome first-pass accepted
```

Run:

```text
11ddc1dafef442f6a54c83a44568eb3a
```

### 7.2 Mini và orchestration failure

Mini lần đầu:

```text
model hiểu đúng semantic fix
wall    3.827s
credits 0.174897
status  CANDIDATE_TARGET_MISSING
```

Candidate không được apply vì packet sử dụng short relative target trong sub-project.

Replan giữ nguyên model/spec/oracle nhưng dùng workspace-relative path đầy đủ:

```text
wall    4.952s
credits 0.173118
candidate applied correctly
```

Sau đó proof lại fail vì `python test_case.py` bị chạy từ repo root thay vì subdirectory mong muốn.

Không tiêu model lần ba. Replan proof-only deterministic:

```text
python tmp/execution-hub-benchmark/capacity-mini/test_case.py
111ms
PASS
```

Run cuối:

```text
d974b3df5bf04734aebdc743977bbcf4
proof 994eea31f33c42b0b2f774efcf8e8454
```

Tổng candidate spend Mini để có accepted result:

```text
credits = 0.174897 + 0.173118 = 0.348015
model wall = 3.827s + 4.952s = 8.779s
```

So với Luna first-pass:

```text
Mini system-level candidate cost cao hơn ≈ 23.5%
Mini model wall tổng cao hơn ≈ 80.1%
```

Nếu chỉ nhìn candidate thứ hai, Mini vẫn rẻ hơn Luna. Nhưng nếu nhìn **accepted result end-to-end**, rework làm mất lợi thế.

Đây là finding quan trọng nhất của benchmark:

> **Tối ưu tier model mà bỏ qua packet construction và proof path sẽ tối ưu sai mục tiêu.**

---

## 8. Paired benchmark #3 — timeout/default semantics

Bài toán yêu cầu:

```text
None      → default 30
0         → default 30
negative  → default 30
positive  → giữ nguyên
```

Cả hai route dùng full workspace-relative path từ đầu.

| Route | Outcome | Wall | Credits | Cache | Proof |
|---|---:|---:|---:|---:|---:|
| Mini | first-pass accepted | 4.766s | 0.055640 | 91.57% | 114ms PASS |
| Luna | first-pass accepted | 7.265s | 0.300400 | 0% | 111ms PASS |

Mini run:

```text
647aa0c622cf4eedae32d9a87c337df8
```

Luna run:

```text
ad3ca357adb84a4d979e91dfcdb67e58
```

So sánh:

```text
Mini rẻ hơn ≈ 81.5%
Mini nhanh hơn ≈ 34.4%
```

Nguyên nhân lớn trong sample này là cache: Mini hit `91.57%`, Luna `0%`.

Điều này củng cố policy: **không route dựa trên model label đơn thuần; cache/thread health phải là input economics.**

---

## 9. Exact paired aggregate — Mini vs Luna

Để tránh so cohort không đồng nhất, chỉ gộp hai task mà Mini và Luna đều chạy sạch cùng spec/oracle: normalize + timeout.

### 9.1 Credits

```text
Mini total = 0.178478 + 0.055640 = 0.234118
Luna total = 0.297000 + 0.300400 = 0.597400
```

Mini rẻ hơn trên hai exact paired tasks khoảng **60.8%**.

### 9.2 Model wall-time

```text
Mini total = 7.281 + 4.766 = 12.047s
Luna total = 8.625 + 7.265 = 15.890s
```

Mini nhanh hơn khoảng **24.2%** trong hai paired tasks này.

### 9.3 Quality

```text
Mini: 2/2 first-pass accepted
Luna: 2/2 first-pass accepted
```

Nhưng capacity case cho thấy Mini có thể mất lợi thế vì control-plane path defects. Vì vậy chưa được suy ra “Mini luôn tốt hơn Luna”.

---

## 10. Same-thread continuation A/B

Đây là test cùng model và **cùng exact second prompt A2**.

### 10.1 Warm lane continuation

Lane:

```text
DBuF245JV-p30j2w
```

A2 continuation:

```text
model        gpt-5.4-mini low
wall         4.484s
credits      0.041760
cache ratio  94.32%
```

### 10.2 Fresh lane control

Lane:

```text
D5OCzKk-is0YyqHe
```

Exact A2 fresh:

```text
wall         5.360s
credits      0.171395
cache ratio  14.91%
```

### 10.3 Hiệu quả

```text
credit saving ≈ 75.6%
wall saving   ≈ 16.3%
cache gain    +79.41 percentage points
```

Kết quả này còn mạnh hơn seed A/B trước đó, nơi same-thread Mini rẻ hơn khoảng 62%.

Policy được củng cố:

> **Nếu semantic continuity còn đúng và thread healthy, reuse lane nên là default. Fresh lane chỉ nên dùng cho blind review, semantic reset hoặc recovery khỏi drift.**

Hai benchmark lane đã được đóng sau khi thu số liệu.

---

## 11. Durable production-style cohort sau benchmark

Final activation snapshot:

```text
resources/coding-tools-mcp/benchmarks/reports/
runtime-activation-snapshot-20260814-131940.json
```

Key metrics:

```text
accepted runs                 47
accepted cohort coverage      47/47 = 100%
accepted TTA p50              57.870s
accepted TTA p90              265.667s
proof records                 86
handoff capsules              2
proof cache hits              1
proof cache saved             999ms
```

Accepted non-deterministic cohorts lần đầu đã có dữ liệu thực:

```text
Mini / test_failure / first_pass
n = 2
p50 TTA = 23.177s
p90 TTA = 26.238s

Luna / test_failure / first_pass
n = 3
p50 TTA = 30.868s
p90 TTA = 97.945s
```

Cảnh báo khi đọc TTA:

- TTA durable đo từ run lifecycle, không phải model latency.
- Nó bao gồm control-plane processing và khoảng chờ ChatWeb Sol final acceptance.
- Luna p90 bị ảnh hưởng rõ bởi một run bị giữ ở acceptance trong lúc benchmark controller làm việc khác.
- Vì vậy model wall + proof time là metric phù hợp hơn cho pure route latency; durable TTA phù hợp cho operator/service-level behavior.

Runtime telemetry cuối:

```text
tool_calls                    610
route_resolved deterministic  186
route_resolved mini             8
route_resolved luna             6
route_resolved sol_xhigh         2
bounded_candidate calls         14
```

Ledger hygiene vẫn cho thấy:

```text
active historical runs 52
stale runs              1
```

Đây là backlog/hygiene signal cần quan sát riêng; không được tự mass-clean khi chưa có provenance.

---

## 12. Routing economics simulation 100 task

Report:

```text
resources/coding-tools-mcp/benchmarks/reports/
routing-economics-20260814-061351.json
```

**Evidence class:** `scenario_simulation_not_production_ab`.

Scenario mix:

```text
30 deterministic
35 localized strong-oracle → Mini
20 bounded leaf            → Luna
15 broad/deep              → Sol xhigh
```

Kết quả giả lập:

| Strategy | Credits | Expected accepted | Credits/accepted | Aggregate TTA |
|---|---:|---:|---:|---:|
| Adaptive | 45.2597 | 98.3875 | 0.4600 | 0.3404h |
| All-Sol for model tasks | 92.1900 | 96.7500 | 0.9529 | 0.2453h |

Theo assumptions của simulation:

```text
credit saving adaptive vs all-Sol = 50.91%
```

Nhưng adaptive aggregate TTA cao hơn vì có modeled fallback penalty:

```text
0.3404h ≈ 20.42 min
0.2453h ≈ 14.72 min
```

Đây là trade-off quan trọng:

> Adaptive routing tối ưu **credits per accepted result**, nhưng nếu fallback xảy ra nhiều thì có thể chậm hơn all-Sol ở aggregate latency.

Do đó production policy phải ưu tiên **first-pass route confidence**, không dùng cascade Mini→Luna→Sol trên mọi task.

---

## 13. Phương án tổ chức phối hợp được khuyến nghị

Mô hình vận hành nên giữ asymmetric authority:

```text
                    USER
                     │
                     ▼
             ChatWeb / Sol
       semantic controller + acceptor
                     │
                     ▼
            EXECUTION HUB
     state / router / writer / proof
          │          │          │
          │          │          └─ deterministic tools
          │          │
          │          ├─ Mini: localized strong-oracle leaf
          │          ├─ Luna: harder bounded leaf
          │          └─ Sol xhigh: broad/deep integration work
          │
          └─ Codex Desktop: persistent deep-code frontend/lane
```

### 13.1 ChatWeb

Dùng cho:

- hiểu intent người dùng;
- research/web;
- settle architecture/contracts;
- chọn route/mode;
- review conflict/integration;
- final acceptance;
- quyết định khi nào handoff/rotate context.

Không dùng ChatWeb để “ngồi chờ” build/test/model lane nhiều phút hoặc nhiều giờ.

### 13.2 Execution Hub

Hub là source of execution truth:

- task/run/wave;
- events;
- client cursors;
- controller lease;
- write fencing;
- candidate packet;
- proof;
- idempotency;
- handoff capsule;
- resume state.

### 13.3 Codex Desktop

Desktop nên là persistent coding/deep-work surface, nhưng **không phải runtime authority thứ hai**.

Dùng Desktop/deep Sol cho:

- high integration width;
- repository exploration sâu;
- multi-file refactor cần giữ context coding lâu;
- deep implementation thread mà continuation cache có giá trị.

### 13.4 Mini/Luna

Mini:

```text
localized
strong oracle
settled semantics
small packet
low write ambiguity
```

Luna:

```text
bounded nhưng khó hơn
ít certainty hơn Mini
cần reasoning vừa phải
vẫn không sở hữu architecture/final acceptance
```

### 13.5 Không serial cascade mặc định

Không dùng:

```text
Mini fail → Luna fail → Sol fail → ...
```

Dùng:

```text
route một lần với evidence tốt
↓
fail typed
↓
ChatWeb Sol phân loại nguyên nhân
↓
proof-only / packet repair / direct Sol tùy nguyên nhân
```

Capacity benchmark chứng minh vì sao: lỗi target/path không phải lý do tăng tier model.

---

## 14. Phân rã thời gian

Một accepted localized task hiện có các thành phần:

```text
T_total
 = preflight/oracle
 + packet construction
 + model wall
 + validation/apply
 + deterministic proof
 + final acceptance wait
```

Các số đo điển hình đợt này:

```text
proof Python nhỏ ≈ 105–114 ms
model Mini        ≈ 4.8–7.3s khi first-pass
model Luna        ≈ 4.9–8.6s khi first-pass
cold proxy ping   ≈ 0.52s gồm process startup
```

Như vậy ở localized leaf, model vẫn là phần latency lớn nhất; proof gần như không đáng kể. Hub transport không phải bottleneck chính ở order-of-magnitude hiện tại.

Tuy nhiên **replan/control waits** có thể lớn hơn cả model. Đây là lý do time-to-accepted-result phải được tối ưu ở orchestration layer, không chỉ chọn model nhanh.

---

## 15. Phân tích chi phí

### 15.1 Khi mọi thứ first-pass

Exact paired normalize + timeout:

```text
Mini credits = 0.234118
Luna credits = 0.597400
Mini saving  ≈ 60.8%
```

### 15.2 Khi orchestration bị lỗi

Capacity:

```text
Mini candidate spend = 0.348015
Luna first-pass       = 0.281800
```

Mini trở thành đắt hơn khoảng **23.5%**, không phải vì Mini reasoning tệ mà vì hai control-plane/path problems.

### 15.3 Sol misuse cost

Trivial normalize leaf:

```text
Sol xhigh failed attempt = 0.948850 credits
Mini accepted            = 0.178478 credits
```

Một Sol deep-code attempt thất bại đã tiêu khoảng **5.32 lần** Mini accepted candidate cost.

### 15.4 Thread reuse

Exact Mini A2:

```text
fresh = 0.171395
warm  = 0.041760
```

Tiết kiệm khoảng **75.6%** cho chính cùng request.

---

## 16. Hiệu quả tổng thể của Execution Hub

### 16.1 Những gì đã được chứng minh

Execution Hub đang tạo giá trị thật ở bốn điểm:

1. **Continuity:** ChatWeb và Codex adapter đọc cùng capsule/run state.
2. **Cost control:** localized leaf có thể xuống Mini/Luna thay vì giữ mọi work ở Sol.
3. **Long-running separation:** model/thread execution không phụ thuộc lifetime của ChatWeb conversation.
4. **Authority separation:** model candidate không đồng nghĩa writer/final acceptor.

### 16.2 Hub overhead có chấp nhận được không?

Với số đo cold hiện tại, có. Cold one-shot full proxy ping khoảng `0.52s` trong khi model leaf thường `~5–9s`.

Nhưng phase tiếp theo nên instrument resident proxy p50/p90 để tránh dùng cold startup làm proxy cho production latency.

### 16.3 Chi phí coordination có chấp nhận được không?

Ở first-pass: có.

Ở repaired path: chưa tối ưu. Capacity Mini cho thấy packet/path/proof bugs có thể tăng spend và TTA đủ lớn để đảo thứ tự economics giữa Mini và Luna.

---

## 17. Hai defect/gap được benchmark phát hiện

### P1.7-A — Candidate target normalization

Triệu chứng:

```text
CANDIDATE_TARGET_MISSING
```

Khi workflow chạy trong sub-project và candidate target được trả ở dạng short path (`case.py`), validation có thể không resolve về workspace-relative path đã được packet scope cho phép.

Impact:

- model call đã tiêu credits nhưng candidate không được apply;
- replan cần model call thứ hai;
- accepted-result cost tăng mạnh.

Yêu cầu fix:

- candidate packet phải canonicalize target path;
- output validator phải map path tương đối theo candidate packet base, không suy đoán cwd khác;
- regression test cho nested path.

### P1.7-B — Verification workdir/path consistency

Triệu chứng:

Workflow đã chỉ subdirectory workdir nhưng proof `python test_case.py` được thực thi từ repo root trong một replan path.

Impact:

- patch đúng nhưng proof fail giả;
- thêm EOCL wave;
- tăng TTA;
- có thể kéo agent lên tier đắt nếu recovery policy không phân loại đúng.

Yêu cầu fix:

- oracle command phải có canonical workdir rõ ràng;
- run report phải ghi resolved cwd;
- test matrix root path vs nested path;
- proof failure `FILE_NOT_FOUND` do cwd phải được typed riêng với code/test failure.

**Hai gap này nên được sửa trước khi tăng production Mini traffic.**

---

## 18. Routing decision sau benchmark

### 18.1 Không thay threshold ngay

Final accepted cohort:

```text
Mini first-pass n=2
Luna first-pass n=3
```

Đây là bước tiến lớn so với trạng thái trước benchmark `n=0`, nhưng vẫn quá nhỏ để tune production route distribution.

### 18.2 Calibration window khuyến nghị

Không dùng một con số sample cứng như chân lý. Initial gate thực dụng:

```text
ít nhất khoảng 10–20 accepted real tasks / route / task-class chính
+
first-pass rate ổn định
+
zero critical defect
+
repair cost được đo
+
credits/accepted advantage còn tồn tại sau rework
+
TTA không xấu đi ngoài budget
```

Khi đủ dữ liệu, dùng confidence interval / defect evidence chứ không chỉ mean.

### 18.3 Auto-handoff

Vẫn **OFF**.

Mechanics và live cross-client capsule đã pass, nhưng auto-handoff cần thêm:

- real long-running tasks;
- client disconnect/reconnect observations;
- controller-transfer operator ergonomics;
- thread health criteria;
- false-handoff rate;
- recovery rate.

---

## 19. Kế hoạch triển khai tiếp theo

### Phase A — sửa orchestration tax vừa phát hiện

Ưu tiên ngay:

```text
candidate target canonicalization
verification cwd/path contract
nested-workspace regression tests
typed path/proof failures
```

Mục tiêu: Mini không được mất credits chỉ vì Hub không resolve đúng target đã có trong packet.

### Phase B — đo resident Hub RTT

Thêm telemetry trực tiếp ở:

```text
Codex stdio receive
→ Hub gateway receive
→ MCP upstream response
→ stdio response
```

Cần p50/p90/p99 và payload-size buckets.

### Phase C — tích lũy real accepted cohorts

Trong task production thật:

- localized strong-oracle → Mini;
- harder bounded → Luna;
- broad/deep → Sol xhigh;
- ghi first-pass/repair/defect/credits/TTA/cache.

Không tạo benchmark giả chỉ để đủ `n`.

### Phase D — policy calibration

Khi cohort đủ đại diện:

- tune Mini/Luna confidence gates;
- điều chỉnh max one fallback policy;
- incorporate warm-cache state;
- so credits/accepted và TTA/accepted;
- đánh giá auto-handoff riêng, không gộp với routing.

---

## 20. Phương án vận hành đề xuất

Cho workflow thực tế hiện tại:

```text
1. ChatWeb nhận yêu cầu, settle semantics.
2. Hub preflight oracle + localize packet.
3. Nếu deterministic đủ → không gọi model.
4. Localized strong oracle → Mini.
5. Harder bounded leaf → Luna.
6. Broad/high integration width → persistent Sol deep lane / Codex Desktop.
7. MCP là writer + proof owner.
8. ChatWeb Sol final accept/reject.
9. Nếu ChatWeb context pressure tăng → record capsule.
10. Khi Desktop/client healthy → controller handoff manual nếu cần.
11. Resume từ durable state, không copy transcript.
12. Reuse thread khi semantic continuity còn đúng.
```

Đây là mô hình cân bằng tốt nhất giữa:

```text
quality
cost
latency
continuity
operator control
```

---

## 21. Các artifact/evidence chính

### Live benchmark snapshots

```text
resources/coding-tools-mcp/benchmarks/reports/
runtime-activation-snapshot-20260814-131240.json

resources/coding-tools-mcp/benchmarks/reports/
runtime-activation-snapshot-20260814-131940.json

resources/coding-tools-mcp/benchmarks/reports/
routing-economics-20260814-061351.json
```

### Key runs

```text
Mini normalize accepted
9c97e07fc63647cda4320dfce9b0afa8

Luna normalize accepted
2bdad163116a43fc8b85701257f99235

Sol normalize deadline/aborted
7ac656c66c064c58a6349f90c1a49987

Mini capacity repaired/accepted
d974b3df5bf04734aebdc743977bbcf4

Luna capacity first-pass
11ddc1dafef442f6a54c83a44568eb3a

Mini timeout first-pass
647aa0c622cf4eedae32d9a87c337df8

Luna timeout first-pass
ad3ca357adb84a4d979e91dfcdb67e58
```

### Continuation lanes

```text
warm  DBuF245JV-p30j2w
fresh D5OCzKk-is0YyqHe
```

Cả hai đã được đóng sau benchmark.

### Cross-client capsule

```text
capsule_id c2a7c0403133426ab142fc939aded6c6
sha256     b993fee1d9eab010cbcaa616bfdd9cfa0ed17fa77aed90ee425fabb1da1e114b
bytes      1438
```

---

## 22. Quyết định đề xuất

**GO** cho tiếp tục sử dụng kiến trúc Execution Hub + Codex Desktop thin-proxy.

**GO** cho Mini/Luna ở chế độ bounded/evidence-gated hiện tại.

**NO-GO** cho mở rộng tỷ lệ Mini production trước khi sửa path/cwd gaps P1.7-A/B.

**NO-GO** cho dùng Sol xhigh deep-code trên trivial/localized leaf chỉ vì Sol mạnh hơn.

**NO-GO** cho serial cascade mặc định.

**NO-GO** cho auto-handoff ở thời điểm này.

**KEEP** same-thread reuse như ưu tiên khi semantic continuity và thread health còn tốt.

**KEEP** ChatWeb Sol làm semantic controller/final acceptance; Hub làm execution truth/writer/proof authority; Codex Desktop là persistent deep-code frontend chứ không phải Runtime authority thứ hai.

---

## 23. Kết luận cuối

Đợt benchmark này xác nhận hướng kiến trúc đã chọn **không chỉ hoạt động về cơ chế mà đã bắt đầu cho hiệu quả kinh tế đo được**.

Phần thắng lớn nhất không phải “Mini rẻ” mà là:

```text
Hub có thể chọn đúng compute cho đúng leaf
+
reuse đúng thread để tận dụng cache
+
giữ writer/proof/continuity bên ngoài conversation
```

Nhưng benchmark cũng chỉ ra giới hạn rất thực tế:

> **Orchestration quality là một phần của model economics.**

Một lỗi target path hoặc proof cwd đủ để xóa lợi ích tier rẻ. Vì vậy bước tiếp theo không phải mở router mạnh hơn mà là **sửa packet/path/proof invariants, instrument steady-state Hub RTT, rồi tích lũy real accepted cohorts**.

Nếu ba bước này được đóng, kiến trúc hiện tại có cơ sở tốt để tiến tới mục tiêu ban đầu: ChatWeb ngắn hạn làm controller, Codex Desktop giữ deep persistent work, Mini/Luna xử lý leaf hợp lý, còn Execution Hub duy trì một execution truth bền vững với chi phí thấp hơn mà không đánh đổi final acceptance authority.
