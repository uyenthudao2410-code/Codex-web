# 9router → Tools-Codex-web
# Phân tích tham khảo toàn diện và Blueprint nâng cấp Execution Hub

**Ngày đánh giá:** 2026-08-14  
**Dự án đích:** `Tools-Codex-web` / `web-mcp-assistant`  
**Dự án tham khảo:** `decolua/9router`  
**Mục tiêu:** phân tích có hệ thống các ý tưởng đáng học từ 9router về dashboard, live routing animation, telemetry usage/token, quota/rate-limit, capacity/fallback và control plane; sau đó chuyển hóa thành kiến trúc phù hợp với Execution Hub hiện tại mà không phá EOCL, authority, proof, Smart-v3 hay mô hình accepted-result cost.

> **Nguyên tắc trung tâm:** không “port 9router”. Học cách 9router biến **observability → capacity state → routing action → operator feedback** thành một vòng điều khiển, rồi tích hợp vòng đó vào kiến trúc Execution Hub hiện có.

---

## 0. Executive summary

9router là một dự án tham khảo tốt cho Tools-Codex-web ở ba mặt:

1. **AI traffic observability**: usage/token/cached-token, request history, provider/account breakdown, realtime active requests.
2. **Provider capacity operations**: quota/reset/depleted state, refresh cadence, fallback/capacity pool, account/provider availability.
3. **Live topology UX**: router ở trung tâm, provider node xung quanh, edge active có directional particle/electric effect, trạng thái idle/active/last/error trực quan.

Tuy nhiên, Tools-Codex-web không phải một proxy router thuần. Nó là một **execution control plane cho coding agent**, đã có:

- ChatWeb/Codex Desktop/OpenCode frontends;
- một Runtime authority;
- task/run/wave;
- EOCL;
- controller lease/fencing;
- repository write authority;
- model delegation;
- deterministic proof;
- persistent task/handoff;
- adaptive route Mini/Luna/Terra/Sol;
- bounded candidate packet;
- token/cache/estimated-credit evidence từ Codex bridge;
- per-principal command quota và job concurrency primitives.

Vì vậy kiến trúc tối ưu không phải:

```text
Tools-Codex-web
    ↓
biến thành 9router
```

mà là:

```text
9router ideas
    ↓
Usage / Quota / Topology / Capacity patterns
    ↓
chuẩn hóa theo semantics của Execution Hub
    ↓
Traffic & Usage Control Plane
    ↓
EOCL + adaptive routing + proof vẫn giữ authority
```

Kết luận đề xuất:

```text
Execution Hub hiện tại
  + Canonical Usage Meter
  + Quota / Cooldown Registry
  + Traffic Governor
  + Reservation Ledger
  + Traffic Queue
  + Event-driven Topology Projector
  + Live Execution Fabric animation
  + Traffic & Usage operator page
```

Không tăng public MCP surface. `smart-v3` tiếp tục giữ đúng 8 tool.

---

# 1. Phạm vi và phương pháp đánh giá

## 1.1 Phạm vi 9router được xem xét

Các nhóm source chính được dùng làm bằng chứng kiến trúc:

```text
README.md
src/app/(dashboard)/dashboard/usage/page.js
src/shared/components/UsageStats.js
src/app/(dashboard)/dashboard/usage/components/UsageTable.js
src/app/(dashboard)/dashboard/usage/components/ProviderTopology.js
src/app/(dashboard)/dashboard/usage/components/ProviderLimits/index.js
src/app/(dashboard)/dashboard/quota/page.js
src/app/api/usage/stats/route.js
src/app/api/usage/history/route.js
src/app/api/usage/stream/route.js
src/lib/db/repos/usageRepo.js
open-sse/utils/usageTracking.js
open-sse/services/capacityAdapter.js
open-sse/services/combo.js
open-sse/handlers/chatCore/streamingHandler.js
open-sse/handlers/chatCore/requestDetail.js
```

Các search result trong đợt đánh giá 2026-08-14 resolve nhiều file về snapshot commit:

```text
15223724c3e1ad898e84ef6e0cc1686cbafc8290
```

Một số file trọng yếu cũng được đọc qua default branch tại thời điểm phân tích. Đây là **point-in-time evidence**, không phải cam kết rằng upstream 9router sẽ giữ nguyên implementation về sau.

## 1.2 Phạm vi Tools-Codex-web được đối chiếu

```text
renderer/index.html
renderer/control-center.js
renderer/control-center.css
renderer/dashboard.js
renderer/dashboard.css
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py
README.md
docs/research/260814_TOOLS_CODEX_WEB_OPTIMAL_PERFORMANCE_COST_UPGRADE_METHODOLOGY.md
```

Audit hiện tại xác nhận app đã có các primitives rất quan trọng:

- topology 9 node;
- state `offline | connected | waiting | blocked | active`;
- delegation-based route truth;
- OpenCode connectivity không bị đánh đồng với DeepSeek activity;
- writer state dựa trên write authority;
- model-visible byte accounting;
- phân biệt `MEASURED`, `ESTIMATED`, `SCENARIO` ở dashboard;
- token economics đo được từ delegation khi có provider/model usage;
- cache token evidence;
- capacity cooldown trong Codex bridge;
- hidden-page polling suppression;
- `prefers-reduced-motion` support.

Do đó bài toán là **evolve**, không greenfield.

---

# 2. 9router thực chất giải bài toán gì?

9router về bản chất là một lớp trung gian đứng giữa client và nhiều AI provider/model/account.

Một mô hình giản lược:

```text
Client / IDE / App
        │
        ▼
      9router
   ┌────┼────┐
   ▼    ▼    ▼
 OpenAI Claude Gemini ...
   │    │    │
 account pools / quotas
```

Các bài toán cốt lõi của nó:

- chuẩn hóa request/response nhiều provider;
- theo dõi usage;
- biết request nào đang active;
- route/fallback theo provider/model/account;
- hiểu capability như vision/pdf/audio/video;
- theo dõi quota/reset;
- tránh provider/account đã cạn hoặc không phù hợp;
- hiển thị trực quan cho operator.

Đó là lý do các ý tưởng của 9router đặc biệt hữu ích cho **traffic plane**, nhưng không thể thay thế **execution authority plane** của Tools-Codex-web.

---

# 3. Điểm mạnh thứ nhất: Usage/Token observability

## 3.1 9router không giữ raw usage theo từng provider một cách rời rạc

`open-sse/utils/usageTracking.js` cho thấy một chiến lược quan trọng: parse nhiều provider format nhưng quy về convention chung.

Các nguồn được xử lý gồm các shape tương ứng với:

- OpenAI Chat Completions;
- OpenAI Responses;
- Claude/Anthropic;
- Gemini;
- DeepSeek-compatible usage;
- Ollama.

Canonical shape về cơ bản xoay quanh:

```text
prompt_tokens
completion_tokens
total_tokens
cached_tokens
cache_creation_input_tokens
reasoning_tokens
```

Điều đáng học không phải tên field cụ thể mà là:

> **Provider-specific parsing phải kết thúc ở một canonical storage/economics convention.**

Nếu không có canonical layer, dashboard, cost calculator và router sẽ mỗi nơi hiểu cache token một kiểu.

## 3.2 Cache token được coi là first-class signal

Đây là điểm rất phù hợp với benchmark của Tools-Codex-web.

Hai request cùng 50k input token có economics rất khác:

```text
Request A
input   50k
cached  45k

Request B
input   50k
cached   2k
```

Vì vậy chỉ theo dõi `input_tokens` là chưa đủ.

Tools-Codex-web hiện đã có cache evidence trong Codex bridge và benchmark warm-thread cho thấy cache có thể thay đổi chi phí cực mạnh. Do đó 9router củng cố thêm quyết định rằng dashboard tương lai cần đưa:

```text
input
cached input
cache-write
output
reasoning
cache ratio
```

lên thành metrics chính thức.

## 3.3 Estimate là fallback, không phải source of truth

9router có heuristic ước tính khi provider không trả usage. Ý tưởng đúng là:

```text
provider-reported usage available
    → use measured

provider-reported usage unavailable
    → estimate
```

Không nên:

```text
transport bytes
    → mặc định coi là provider token
```

Tools-Codex-web hiện đã cải thiện đúng hướng: `model_visible_bytes` được đo, rồi byte/token chỉ là conversion `ESTIMATED`; delegation economics có thể override thành `MEASURED`.

Đề xuất tiếp tục chuẩn hóa thành provenance rõ ràng:

```text
measurement = provider_reported
measurement = model_visible_estimate
measurement = unknown
```

---

# 4. Điểm mạnh thứ hai: Historical snapshot + realtime delta

Một pattern tốt của 9router là tách dữ liệu thành hai đường:

```text
REST / database
    → historical/full snapshot

SSE stream
    → live mutable state
```

Các route như:

```text
/api/usage/stats
/api/usage/history
/api/usage/stream
```

cho phép frontend không cần reload toàn bộ historical data khi chỉ có active request thay đổi.

Đây là pattern phù hợp để thay polling nặng trong Execution Hub.

## 4.1 Target cho Tools-Codex-web

Có thể hình thành control API nội bộ:

```text
GET /__control/usage?period=24h
GET /__control/traffic
GET /__control/quotas
GET /__control/requests?cursor=...

SSE /__control/traffic/stream
```

Hoặc Electron IPC equivalents nếu không muốn public thêm HTTP route.

Realtime delta chỉ cần chứa:

```json
{
  "active": 3,
  "queued": 2,
  "rpm": 18,
  "tpm": 41220,
  "route_changes": [],
  "quota_changes": [],
  "topology_events": []
}
```

Không stream lại hàng MB event history.

---

# 5. Điểm mạnh thứ ba: Provider Limits / Quota UX

9router có một lớp UI riêng cho provider/account limits thay vì coi quota là một error message 429.

Các khái niệm đáng học:

- quota remaining;
- reset time;
- depleted state;
- refresh quota;
- auto refresh;
- sort/filter account;
- bulk action cho account depleted/available;
- refresh cadence khác nhau giữa provider;
- tránh polling vô nghĩa khi tab không visible.

## 5.1 Ý nghĩa kiến trúc

Quota không nên chỉ xuất hiện sau khi request fail.

Nó phải trở thành input cho scheduler/router:

```text
quota state
   ↓
route eligibility
   ↓
queue / dispatch / pause / fallback
```

## 5.2 Nhưng Tools-Codex-web không nên copy “disable account” trực tiếp

Trong 9router, account pool là tài nguyên proxy tương đối đồng nhất.

Trong Tools-Codex-web, semantics tốt hơn là:

```text
quota exhausted
    ↓
route/account eligibility = paused_by_quota
```

Credential/account object không bị xoá hoặc thay đổi quyền.

Khi quota reset:

```text
paused_by_quota
    ↓
available
```

Operator actions nên là:

```text
Pause exhausted
Resume available
Drain route
Refresh quota
```

`Drain` nghĩa là không nhận request mới nhưng cho request đang chạy hoàn tất.

---

# 6. Điểm mạnh thứ tư: Capacity Adapter và fallback pool

`open-sse/services/capacityAdapter.js` thể hiện pattern:

- capability pools;
- model list theo capability;
- fallback hoặc round-robin strategy;
- chỉ đưa adapter model lên trước khi original model list không đáp ứng hard capability;
- tránh override một combo vốn đã có model phù hợp.

Các hard capability được xem xét bao gồm nhóm như:

```text
vision
pdf
audioInput
videoInput
```

## 6.1 Ý tưởng có thể port

**Eligibility trước scoring.**

```text
hard requirement
    ↓
filter eligible candidates
    ↓
capacity/cost/latency scoring
```

Đây chính là nguyên tắc Tools-Codex-web cần áp dụng cho model quality class:

```text
semantic requirement
    ↓
eligible route class
    ↓
Traffic Governor
    ↓
best available eligible route
```

Không được đảo thứ tự.

## 6.2 Round-robin chỉ hợp lý trong semantic equivalence class

Có thể round-robin/least-loaded giữa:

```text
Mini endpoint A
Mini endpoint B
Mini-equivalent account C
```

hoặc một pool mà router đã chứng minh cùng đáp ứng yêu cầu.

Không được coi:

```text
Mini
Terra
Sol
```

là ba node tương đương để round-robin.

Model quality/authority constraint phải loại route không đủ năng lực **trước** khi load-balancing.

---

# 7. Context-window adaptation của 9router

Capacity adapter có logic cắt lịch sử để vừa context window của fallback model. Implementation dùng rough estimate theo character/token và giữ:

- system/developer instructions;
- một phần head;
- current tail;
- bỏ middle history trước.

Ý tưởng tốt:

> **Fallback model phải tương thích context budget.**

Nhưng implementation này không nên copy nguyên vào Tools-Codex-web.

Tools-Codex-web đã có:

- task ledger;
- proof ledger;
- handoff capsule;
- bounded resume packet;
- candidate packet;
- context projection.

Vì vậy target tốt hơn:

```text
context pressure
    ↓
model-free projection / capsule
    ↓
bounded packet
    ↓
new/fallback route
```

thay vì âm thầm drop middle transcript.

---

# 8. Điểm mạnh thứ năm: Live Provider Topology

Đây là phần UI nổi bật nhất và rất phù hợp để tham khảo.

`ProviderTopology.js` của 9router dùng `@xyflow/react` để dựng graph.

## 8.1 Node model

Có hai node class chính:

```text
ProviderNode
RouterNode
```

Provider node có:

- provider icon;
- provider color;
- name;
- active border;
- glow;
- ping dot khi active.

Router node ở trung tâm:

- pulse/glow khi có activity;
- badge active count;
- nhiều handles để edge nối theo hướng hợp lý.

## 8.2 Dynamic radial/ellipse layout

Provider được rải đều trên ellipse quanh router.

Bán kính không hard-code hoàn toàn mà tăng theo node count để đảm bảo khoảng cách.

Pattern này hợp lý với 9router vì các provider có vai trò tương đối đồng cấp.

## 8.3 Edge semantics

9router phân biệt:

```text
idle
active
last
error
```

Ví dụ visual semantics:

```text
idle   → line mờ
active → bright/electric
last   → amber
error  → red
```

Đây là điểm rất đáng học: animation không tồn tại độc lập, nó phản ánh request state.

---

# 9. Phân tích kỹ electric/particle animation của 9router

Active edge không chỉ là `stroke-dasharray` chạy.

Nó được cấu thành từ nhiều layer SVG:

```text
outer halo
   +
mid plasma
   +
hot white core
   +
moving energy orbs
   +
electric sparks
```

## 9.1 Electric distortion

SVG filter dùng các primitive kiểu:

```text
feTurbulence
feDisplacementMap
```

để edge có cảm giác điện/plasma thay vì một đường thẳng tĩnh.

## 9.2 Directional particles

Particle dùng motion dọc edge path.

Đây là phần có giá trị nhất cho Tools-Codex-web vì **direction có semantic meaning**:

```text
client → hub       request inbound
hub → model        dispatch
model → hub        response
hub → writer       mutation authority/use
writer → proof     validation
```

## 9.3 Không dùng built-in animated edge một cách mù quáng

Source 9router có comment rằng built-in animated dash style có thể CPU-heavy và họ ưu tiên particle beam custom.

Bài học đúng cho Electron:

> animation phải có budget và dừng khi không còn state active.

## 9.4 Frontend stuck-state guard

9router có frontend active timeout để không giữ animation mãi nếu provider state bị stuck.

Đây là defensive UX tốt, nhưng Tools-Codex-web nên tốt hơn bằng cách phân biệt:

```text
source event freshness
state lease / heartbeat
render timeout
```

Renderer timeout chỉ là safety net, không được thay runtime truth.

## 9.5 Resize/fit behavior

Topology refit khi container resize/node count thay đổi.

Đây là chi tiết UX nhỏ nhưng cần thiết nếu topology dynamic.

---

# 10. Điều gì không nên copy nguyên từ Live Topology của 9router?

## 10.1 Không cần React Flow chỉ để có animation

Tools-Codex-web renderer hiện là Electron HTML/CSS/JavaScript với SVG topology sẵn có.

Nếu đưa `@xyflow/react` chỉ vì muốn particle edge, chi phí sẽ gồm:

- thêm React runtime/renderer integration;
- build/bundling complexity;
- lifecycle bridge với Electron page hiện tại;
- duplicate state rendering;
- migration/test cost;
- có thể phá IDs/bindings cũ.

ROI thấp.

**Khuyến nghị:** giữ SVG/DOM hiện tại.

Nâng:

```text
<line>
```

thành:

```text
<path>
```

với:

```text
Bezier path
SVG defs/filter
2–4 directional particles
CSS/SVG state classes
```

Như vậy học được 80–90% visual value mà không migration framework.

## 10.2 Không copy “gaming RGB” y nguyên

9router intentionally dùng hiệu ứng khá mạnh:

- cyan halo;
- green plasma;
- white core;
- yellow/cyan sparks.

Execution Hub phù hợp hơn với visual language:

```text
operations console
+ network fabric
+ restrained sci-fi
```

Mục tiêu là operator hiểu state nhanh, không phải tối đa hiệu ứng.

---

# 11. Baseline Live Routing hiện tại của Tools-Codex-web

Checkout hiện tại đã có 9-node topology:

```text
ChatWeb
Codex Desktop
OpenCode
Codex Fast (Mini/Luna)
Execution Hub
OpenCode Go / DeepSeek
Codex Deep / Terra
MCP Writer
Codex Critical / Sol
```

`control-center.js` đã làm đúng một invariant rất quan trọng:

```text
OpenCode online
≠
DeepSeek model active
```

DeepSeek lane chỉ active khi có delegation evidence.

Tương tự, model lanes lấy state từ delegation status thay vì đoán từ frontend connectivity.

## 11.1 Current visual state

Hiện có:

```text
offline
connected
waiting
blocked
active
```

Active edge dùng dash animation.

Active node pulse.

Waiting/blocked dùng color/dashed distinction.

## 11.2 Current polling discipline

Control Center:

- poll khoảng vài giây;
- không poll khi document hidden;
- chỉ poll các page operator liên quan.

Dashboard cũng đã có visibility gating.

Đây là nền tốt để nâng sang stream/delta về sau.

## 11.3 Reduced motion

CSS đã disable active animation khi:

```text
prefers-reduced-motion: reduce
```

Phải giữ invariant này sau khi thêm particle/electric effect.

---

# 12. Baseline token/cost dashboard hiện tại

Một cải tiến quan trọng đã có trong checkout hiện tại là đổi semantics từ “token thật” sang evidence rõ hơn.

Dashboard hiện mô tả:

```text
MEASURED
ESTIMATED
SCENARIO
```

và không còn coi transport request/response byte là billing token truth.

`model_visible_bytes` là measurement thật của text projection, nhưng conversion byte/token vẫn là estimate.

Khi delegation metadata có economics:

```text
input_tokens
output_tokens
cached_input_tokens
```

thì lane có thể được đánh dấu `MEASURED`.

Đây là đúng hướng và phải được giữ khi tham khảo 9router.

---

# 13. Gap matrix: 9router vs Tools-Codex-web

| Capability | 9router | Tools-Codex-web hiện tại | Quyết định |
|---|---|---|---|
| Usage normalization đa provider | Mạnh | Partial theo delegation/model-visible telemetry | Chuẩn hóa thành canonical UsageEvent |
| Cached token | Có | Có evidence trong Codex bridge/dashboard | Nâng thành KPI first-class |
| Realtime active request stream | Có | Poll orchestration/perf | Chuyển dần sang delta stream |
| Historical usage store | Có | Performance trace + ledger, coverage khác nhau | Xây bounded aggregation/read model |
| Provider quota UI | Có | Chưa có control plane chung | Nên thêm |
| Quota reset/depleted semantics | Có | Capacity cooldown rời rạc | Hợp nhất Quota/Cooldown Registry |
| Rate governor RPM/TPM | Router-oriented | Chưa có unified governor | Nên thêm |
| Local concurrency | Có theo service logic | Có job/session concurrency primitives | Không trộn với provider quota |
| Capacity fallback | Có | Có route/capacity cooldown và replan | Hợp nhất nhưng giữ semantic eligibility |
| Round-robin | Có ở adapter strategy | Không generic | Chỉ trong equivalence class |
| Context fallback trimming | Có | Có bounded packets/capsule | Không copy silent trimming |
| Live topology | React Flow + particles | SVG 9-node topology | Nâng SVG hiện tại |
| Directional flow | Có visually | Chưa rõ chiều trên edge | Nên thêm |
| Error/last state | Có | blocked/active/waiting | Mở rộng typed visual states |
| Proof/write semantics | Không phải trọng tâm | Rất mạnh | Giữ và đưa vào animation |
| Controller/write authority | Không tương đương | Có | Không cho UI/provider layer vượt authority |
| Flight-recorder replay | Không phải core pattern | Có ledger đủ nền | Nên làm sau live topology |

---

# 14. Target architecture: Traffic & Usage Control Plane

Kiến trúc đề xuất:

```text
                         OPERATOR
                            │
                            ▼
                   Execution Control Center
                 ┌──────────┼───────────┐
                 │          │           │
              Routing    Traffic     Proof/Task
                 │          │           │
                 └─────┬────┴─────┬─────┘
                       ▼          ▼
                    EOCL      Traffic Governor
                       │          │
                       │     ┌────┴─────────────┐
                       │     │ Usage Meter      │
                       │     │ Quota Registry   │
                       │     │ Cooldown Registry│
                       │     │ Reservation      │
                       │     │ Traffic Queue    │
                       │     └────┬─────────────┘
                       │          │
                       └────┬─────┘
                            ▼
                      Adaptive Router
                            │
                eligible provider/model route
                            │
                            ▼
                         Executor
                            │
                  usage / latency / outcome
                            │
                            └──── feedback ────┐
                                               │
                                               └─→ Usage Meter
```

Quy tắc authority:

```text
Traffic Governor có thể làm route KHÔNG khả dụng.
Traffic Governor không được làm route KHÔNG đủ năng lực trở thành khả dụng.
```

---

# 15. Canonical UsageEvent

Đề xuất contract:

```text
UsageEvent
  schema_version
  event_id
  timestamp

  task_id
  run_id
  wave_id
  delegation_id
  request_id

  principal
    chatweb
    codex_desktop
    opencode
    supervisor

  route
    deterministic
    mini
    luna
    terra
    sol_xhigh
    sol_max
    sol_ultra

  provider
  model
  account_ref

  operation
  tool_name

  usage
    input_tokens
    cached_input_tokens
    cache_creation_tokens
    output_tokens
    reasoning_tokens
    total_tokens

  measurement
    provider_reported
    model_visible_estimate
    unknown

  reservation
    estimated_input_tokens
    reserved_output_tokens
    reserved_total_tokens

  economics
    estimated_credits
    estimated_usd
    pricing_revision

  timing
    queue_ms
    dispatch_transport_ms
    provider_ms
    first_token_ms
    total_ms

  outcome
    success
    failure
    rate_limited
    capacity
    deadline
    cancelled

  retry_after_ms
  cooldown_until
```

## 15.1 Không cộng measurement planes sai cách

Không được:

```text
provider token
+
MCP transport byte estimate
=
“total token”
```

Cần hierarchy:

```text
provider_reported
    >
model_visible_estimate
    >
unknown
```

Một request chỉ chọn source phù hợp nhất cho cùng metric.

---

# 16. QuotaState contract

```text
QuotaState
  provider
  account_ref
  model_or_pool

  source
    provider_api
    provider_header
    inferred
    operator
    unknown

  windows[]
    kind
      rolling
      daily
      weekly
      credits
      request
      token

    limit
    used
    remaining
    remaining_ratio
    reset_at

  fetched_at
  stale_after
  status
    available
    low
    exhausted
    unknown
    error
```

Invariant:

> `unknown` không được render thành `100% remaining`.

---

# 17. Cooldown Registry

Codex bridge hiện đã có capacity cooldown. Không tạo một cooldown subsystem khác cho dashboard.

Nâng thành registry chung:

```text
CooldownState
  scope
    provider
    account
    model
    route

  reason
    rate_limit
    quota_exhausted
    capacity
    provider_unavailable
    auth
    deadline
    model_unavailable

  started_at
  retry_after_ms
  cooldown_until

  source
    provider_header
    provider_error
    runtime_policy
    operator

  confidence
```

Router hỏi registry thay vì tự parse mỗi nơi:

```text
isEligible(route, now)?
```

---

# 18. Traffic Governor

Nên dùng hierarchical admission control:

```text
GLOBAL
  │
  └── PROVIDER
       │
       └── ROUTE / MODEL
            │
            └── PRINCIPAL
                 │
                 └── TASK
```

Ví dụ:

```text
global concurrency      6
provider concurrency    4
sol_xhigh concurrency   1
chatweb concurrency     3
task concurrency        1
```

Tất cả gate phải pass trước dispatch.

---

# 19. RPM và TPM

## 19.1 RPM

Token bucket đơn giản:

```text
capacity = configured RPM
refill_rate = RPM / 60 per second
request_cost = 1
```

## 19.2 TPM

Bucket khác:

```text
capacity = configured TPM
refill_rate = TPM / 60 tokens/second
```

Nhưng TPM có vấn đề: output token chưa biết trước.

Vì vậy cần reservation.

---

# 20. Reservation Ledger

Trước dispatch:

```text
reservation_id
provider
route
request_id
estimated_input
max_output
reserved_total
created_at
expires_at
state
```

Ví dụ:

```text
estimated input    24k
max output          8k
──────────────────────
reserve             32k
```

Sau response:

```text
actual input        23k
actual output       3.2k
──────────────────────
actual              26.2k
refund               5.8k
```

Nếu provider chưa nhận request:

```text
release full reservation
```

Nếu delivery/outcome unknown:

```text
hold bounded reconciliation window
```

Reservation phải có idempotency identity để reconnect/retry không double-reserve.

---

# 21. Queue thay vì blind retry

Anti-pattern:

```text
Sol call
 → 429
 → retry
 → 429
 → fallback Terra
 → semantic mismatch
 → retry Sol
```

Target:

```text
route = Sol
    ↓
Governor sees TPM near hard limit
    ↓
queue
    ↓
bucket refill / quota reset
    ↓
one dispatch
```

Nếu queue deadline vượt giới hạn:

```text
Is there semantic-equivalent route?
    ├─ yes → reroute
    └─ no  → BLOCKED / typed REPLAN
```

Không dùng serial ladder vô điều kiện.

---

# 22. Routing semantics sau khi thêm traffic plane

Thứ tự bắt buộc:

```text
Task semantics
    ↓
EOCL / safety / authority
    ↓
Router builds eligible route set
    ↓
Traffic Governor removes unavailable members
    ↓
Scorer ranks remaining candidates
    ↓
Reservation
    ↓
Dispatch
    ↓
Proof
    ↓
Final acceptance
```

Không được:

```text
route nào rảnh nhất
    ↓
route đó làm task
```

---

# 23. Route scoring

Sau semantic filtering, scoring deterministic có thể là:

```text
score(route) =
    quality_fit
  + capacity_headroom
  + cache_benefit
  - expected_accepted_cost
  - queue_penalty
  - cooldown_penalty
  - recent_failure_penalty
```

Không cần ML router ở giai đoạn đầu.

Một route không đủ quality/authority bị **eliminate**, không chỉ bị trừ điểm.

---

# 24. Target UI: tách Traffic & Usage thành page riêng

Command Center hiện khá dày. Nếu thêm quota/RPM/TPM vào cùng page sẽ làm mất hierarchy.

Nav đề xuất:

```text
Command Center
Live Routing
Traffic & Usage       ← mới
Tasks & Proof
Connections
Workspace
System
```

`Traffic & Usage` gồm:

```text
Overview
Live Traffic
Models & Routes
Quotas
Requests
Policy
```

---

# 25. Command Center sau khi giảm tải

Chỉ giữ snapshot vận hành:

```text
AI traffic
42k TPM · 18 RPM

Cost today / trace
$4.27

Capacity
3 active · 2 queued

Warnings
Sol low quota · reset 41m
```

và một mini chart.

Toàn bộ bảng model, quota cards, request details, policy editor chuyển sang `Traffic & Usage`.

---

# 26. Live Traffic page

KPI:

```text
Active calls
Queued calls
RPM
TPM
p50 latency
p95 latency
429 rate
capacity error rate
```

Chart theo phút:

```text
input tokens
output tokens
cached tokens
requests
```

Policy thresholds:

```text
TPM soft threshold
TPM hard threshold
```

Mục tiêu operator:

> Nhìn trong 3 giây biết hệ thống đang healthy, queued hay throttled.

---

# 27. Models & Routes page

Bảng đề xuất:

| Route | Model | Active | Queue | RPM | TPM | Cache | p95 | Cost | Capacity | State |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Mini | candidate | 2 | 0 | 12 | 18k | 42% | 2.1s | low | 81% | Healthy |
| Luna | bounded | 0 | 1 | 4 | 9k | 51% | 4.8s | medium | 63% | Healthy |
| Terra | deep | 1 | 0 | 3 | 21k | 36% | 11s | higher | 44% | Busy |
| Sol | critical | 0 | 1 | 1 | 28k | 70% | 19s | high | 8% | Throttled |

Click route mở drawer:

```text
WHY CURRENT STATE?

quota source
retry-after
last failures
queue depth
current concurrency
recent accepted-result rate
cache ratio
route-selection reason
```

---

# 28. Quotas page

Provider/account card:

```text
OpenAI / account A
──────────────────────────
5h window         68% left
weekly            42% left
credits                  3
reset                2h14m

state             AVAILABLE
last refresh            14s
source            provider

[Pause] [Drain] [Refresh]
```

Nếu không có API quota:

```text
Quota        UNKNOWN
Rate state   HEALTHY
Usage seen   measured
```

Không fabricate percentage.

---

# 29. Requests page

Tools-Codex-web có advantage lớn nhờ task/run/wave/delegation ledger.

Một request row nên có:

```text
15:31:22
Task 7ab3
agent_workflow
sol_xhigh
model/provider

Queue          1.8s
Provider      17.4s
Input         31.2k
Cached        18.6k
Output         4.8k
Credits       estimate
Result        accepted
```

Click mở trace:

```text
ChatWeb
   ↓
agent_workflow
   ↓
ROUTED → sol_xhigh
   ↓
queued
   ↓
provider execution
   ↓
MCP writer / proof
   ↓
ACCEPTING
   ↓
accepted
```

Đây là nơi Execution Hub có thể vượt xa dashboard proxy thông thường.

---

# 30. Policy page

Đừng bắt operator chỉnh 20 biến ngay từ đầu.

Top-level profiles:

```text
Cost Saver
Balanced
Performance
Custom
```

Advanced:

```text
max concurrency
provider concurrency
route concurrency
RPM
TPM
max queue wait
daily token budget
task credit limit
soft threshold
hard threshold
fallback policy
max reroutes
```

Mọi mutation policy nên có audit identity:

```text
policy_version
changed_at
changed_by
previous_hash
new_hash
```

---

# 31. Live Routing → Live Execution Fabric

Đây là phần nên học animation của 9router mạnh nhất.

Layout của Tools-Codex-web không nên radial hoàn toàn vì node có role khác nhau.

Semantic layout đề xuất:

```text
                    FRONTENDS

          ChatWeb   Desktop   OpenCode
              \       |       /
               \      |      /
                EXECUTION HUB
               /      |       \
              /       |        \
        Fast lane   Deep lane   Critical
        Mini/Luna     Terra       Sol
              \       |        /
               \      |       /
                 MCP WRITER
                     |
                 Repository
```

Operator học layout một lần và không phải tìm node mỗi lần provider list đổi.

---

# 32. Animation semantics: không animate “online” như “executing”

Nguyên tắc:

```text
connected ≠ active
```

Ví dụ:

```text
OpenCode heartbeat online
```

chỉ render node `connected`.

Chỉ khi có:

```text
delegation_started
provider_call_started
```

mới animate compute edge.

Tương tự:

```text
MCP Writer connected
≠
mutation active
```

Chỉ write lease/mutation evidence mới tạo mutation animation.

---

# 33. Animation scenario 1: Client request inbound

Khi ChatWeb phát request:

```text
ChatWeb  ●━━●━━●━━▶ Execution Hub
```

Visual:

- 2–3 particles;
- inbound cyan/blue;
- Hub pulse một lần;
- không sáng model lane trước khi có route evidence.

---

# 34. Animation scenario 2: Model delegation

Ví dụ chọn Luna:

```text
Hub ═══●══●══▶ Fast / Luna
```

Chỉ lane tương ứng active.

Mini/Terra/Sol còn lại giữ idle/available state.

Tooltip:

```text
route=luna
effort=high
status=executing
```

---

# 35. Animation scenario 3: Streaming/response

Direction đảo:

```text
Luna ●━━●━━●━━▶ Hub
```

Có thể dùng cùng color family nhưng particle chạy inward.

`dispatch` và `response` trở thành hai visual phases khác nhau mà không cần thêm nhiều text.

---

# 36. Animation scenario 4: Write authority

Candidate/model response không làm Writer active.

Chỉ khi runtime có write authority/use:

```text
Hub ═════▶ MCP Writer
              │
              ▼
          Workspace
```

Writer badge:

```text
LEASED
fence #N
```

Điểm này giúp operator phân biệt:

```text
model reasoning
```

với:

```text
repository mutation
```

---

# 37. Animation scenario 5: Proof

Khi EOCL vào `PROVING`:

```text
Workspace / Writer
        │
        └━━●━━●━━▶ Proof/Hub
```

Visual state:

```text
PROVING
```

Khi proof pass:

```text
✓ PROOF
```

pulse ngắn, không loop vô hạn.

---

# 38. Animation scenario 6: ACCEPTING

Sau proof, compute lanes có thể idle.

Semantic controller/ChatWeb node được highlight:

```text
ACCEPTING
```

Điều này thể hiện đúng rằng test xanh chưa tự động là final acceptance.

---

# 39. Animation scenario 7: Queue

Queued không phải active.

Visual:

```text
Hub ─ ─ ─ ─ ─▶ Terra
              Q2
```

- amber;
- dashed/static hoặc particle rất chậm;
- badge queue depth;
- optional wait time.

Không dùng electric active beam cho queued request.

---

# 40. Animation scenario 8: Cooldown / throttled

Ví dụ Sol:

```text
Codex Critical
SOL
COOLDOWN · 37s
```

Edge:

```text
Hub ───────╳────── Sol
```

Node có countdown ring hoặc compact timer.

Khi cooldown kết thúc:

```text
COOLDOWN → AVAILABLE
```

chỉ flash một transition rồi về idle.

---

# 41. Animation scenario 9: Typed failures

Không gom mọi failure thành đỏ.

Visual mapping đề xuất:

```text
rate_limited   → amber + 429/retry badge
capacity       → orange + CAP badge
blocked        → red dashed + lock
error          → red pulse x2 rồi static
cancelled      → gray fade
proof_failed   → red proof state, không gán lỗi cho provider nếu provider call đã thành công
control_error  → highlight Hub/control edge, không highlight model sai
```

Điều này phù hợp với error taxonomy mà project đang hướng tới.

---

# 42. TopologyProjector: renderer không tự suy đoán

Đề xuất architecture:

```text
Runtime events
    ↓
TopologyProjector
    ↓
VisualSnapshot / VisualDelta
    ↓
SVG renderer
```

Renderer không parse EOCL business semantics rải rác.

Ví dụ mapping:

```text
delegation_started(route=luna)
    → edge hub→fast
      state=dispatch
      direction=outbound

provider_response_streaming(route=luna)
    → edge fast→hub
      state=stream
      direction=inbound

write_lease_acquired
    → hub→writer
      state=mutation_authorized

proof_started
    → writer→proof/hub
      state=proof
```

---

# 43. VisualState contract

Node:

```text
NodeState
  offline
  idle
  connected
  queued
  dispatching
  active
  streaming
  writing
  proving
  accepting
  cooldown
  blocked
  error
  success
```

Edge:

```text
EdgeState
  idle
  connected
  queued
  dispatch
  stream
  mutation
  proof
  handoff
  cooldown
  blocked
  error
```

Direction:

```text
inbound
outbound
bidirectional
none
```

Renderer chỉ cần visual contract này.

---

# 44. SVG implementation recommendation

Giữ current DOM topology nhưng đổi đường:

```text
<line>
```

thành paths có semantic IDs:

```text
<path id="edge-chatweb-hub" ... />
<path id="edge-hub-fast" ... />
<path id="edge-hub-terra" ... />
<path id="edge-hub-sol" ... />
<path id="edge-hub-writer" ... />
```

Cho active edge:

```text
halo path
core path
motion particles
```

Chỉ inject particle DOM khi state cần animation.

Khi state kết thúc:

```text
remove particles
remove filter animation
```

Không chỉ `opacity: 0` nhưng vẫn để animation chạy nền.

---

# 45. Animation performance budget

Electron UI phải có explicit budget.

Đề xuất:

```text
idle topology
  0 continuous animation

1 active edge
  2–4 particles

2–4 active edges
  2 particles/edge

>4 active edges
  reduce particle count
  disable sparks

window hidden
  pause animation updates

prefers-reduced-motion
  no particle motion
  static highlight only
```

Không chạy 6 particles + 5 sparks trên mọi edge cùng lúc như một bản sao trực tiếp của 9router.

---

# 46. Traffic intensity animation

P2 có thể map TPM/RPM vào velocity/density nhưng chỉ theo normalized scale.

Không 1:1.

Ví dụ:

```text
normalized = log1p(current_tpm) / log1p(reference_tpm)
```

sau đó clamp:

```text
particle_count = 1..4
speed = bounded range
```

Mục tiêu chỉ cho operator thấy relative intensity.

---

# 47. Flight Recorder Replay

Đây là điểm Tools-Codex-web có thể vượt 9router nhờ orchestration ledger.

Một task cũ có thể replay:

```text
00:00 ChatWeb → Hub
00:01 Hub → Luna
00:05 Luna → Hub
00:06 Hub → Writer
00:08 Writer → Proof
00:11 Proof pass
00:12 ACCEPTING
00:13 ACCEPTED
```

Use cases:

- debug routing;
- postmortem;
- hiểu tail latency;
- xem vì sao fallback/replan xảy ra;
- demo system behavior;
- so sánh accepted-result economics.

Replay phải từ durable events, không lưu screen recording.

---

# 48. Data refresh cadence

Không dùng một timer cho tất cả.

Đề xuất:

```text
live runtime/traffic delta
  ~0.5–2s hoặc event stream

aggregated usage
  ~5–15s

provider quota API
  ~30–300s tuỳ provider

historical charts
  refresh theo user/time bucket
```

Khi tab hidden:

- renderer animation pause;
- UI aggregation polling pause;
- runtime traffic control vẫn hoạt động;
- quota refresh server-side chỉ chạy khi thật sự cần cho routing, không phụ thuộc UI.

---

# 49. Provider adapters nên nằm dưới runtime

Không để renderer biết chi tiết provider API.

Target:

```text
adapters/
  usage/
  quota/
  errors/
  capability/
```

Canonical interfaces:

```text
UsageAdapter.parse(response)
QuotaAdapter.refresh(account)
ErrorAdapter.classify(error)
CapabilityAdapter.describe(model)
```

UI chỉ nhận canonical DTO.

---

# 50. Suggested internal module map

Nếu triển khai trên Coding Tools MCP Python trước:

```text
coding_tools_mcp/
  traffic/
    usage_schema.py
    usage_meter.py
    aggregation.py
    quota_registry.py
    cooldown_registry.py
    token_bucket.py
    reservation_ledger.py
    traffic_queue.py
    governor.py
    topology_projection.py
    policy.py
    adapters/
      codex.py
      opencode.py
      provider_common.py
```

Không bắt buộc tạo toàn bộ ngay Wave 1.

Rule của repo vẫn áp dụng:

> Chỉ extract abstraction khi có concrete second use case.

Do đó có thể bắt đầu bằng vài module nhỏ rồi tách dần.

---

# 51. Public MCP contract

**Không thêm public tool mới.**

Giữ:

```text
smart-v3
8 tools
```

Traffic/quota là operator/runtime concern.

Exposure phù hợp:

- Electron IPC;
- internal control endpoints;
- orchestration snapshot extension;
- diagnostics trong `workspace_context(detail=full)` nếu thật sự cần model thấy một bounded summary.

Không tạo:

```text
traffic_control
quota_manager
provider_router
```

thành public tool thứ 9/10/11 chỉ để UI thuận tiện.

---

# 52. Authority invariants

Traffic plane tuyệt đối không được:

- cấp controller lease;
- cấp write lease;
- bỏ qua EOCL;
- tự hạ Sol-required task xuống Mini;
- bỏ high-cost gate;
- coi provider availability là proof;
- coi animation state là execution evidence;
- mutation repository trực tiếp;
- biến quota unknown thành available;
- tự retry unsafe side effect.

Một câu chốt:

> **Presentation scope != traffic eligibility != semantic authority != repository write authority.**

---

# 53. Accepted-result economics vẫn là objective

Không tối ưu:

```text
model call rẻ nhất
```

Mà tối ưu:

```text
ExpectedAcceptedCost =
  (model
   + context
   + tool
   + queue
   + proof
   + review
   + repair
   + integration
   + ops)
  / P(accepted)
```

Traffic Governor giúp giảm:

- retry do 429;
- capacity false starts;
- queue tail không quan sát được;
- duplicate reservation/retry;
- model call vào route đang cooldown.

Nhưng không được làm giảm `P(accepted)` bằng cách chọn model dưới chuẩn.

---

# 54. Ưu tiên ROI

## P0 — Measurement truth

Trước mọi fancy dashboard:

- canonical UsageEvent;
- source provenance;
- measured vs estimated;
- cached/reasoning token;
- queue/provider/total timing;
- typed error classification.

Gate:

```text
không mix billing plane
không fake quota
không fake model activity
```

## P1 — Event-driven Live Execution Fabric

Nâng current topology:

- Bezier SVG paths;
- directional particles;
- node state badges;
- queue/cooldown/blocked distinction;
- writer/proof phases;
- reduced motion;
- no animation without evidence.

Đây là phần có UX impact lớn nhưng risk runtime thấp nếu chỉ projection.

## P2 — Unified cooldown + basic traffic state

- đưa Codex capacity cooldown vào shared registry;
- expose route availability;
- queue depth;
- active count;
- per-route concurrency state.

## P3 — Traffic Governor

- concurrency admission;
- queue;
- RPM bucket;
- TPM bucket;
- reservation/reconciliation.

## P4 — Traffic & Usage page

- overview;
- live traffic;
- models/routes;
- requests;
- policy.

## P5 — Provider quota adapters

Chỉ adapter provider có nguồn đủ tin cậy.

- remaining;
- reset_at;
- freshness;
- source;
- unknown semantics.

## P6 — Capacity-aware routing

Trong semantic equivalence class:

- least-loaded;
- quota-aware;
- cache-aware;
- expected accepted-result cost.

## P7 — Flight recorder replay

Dùng existing ledger để replay visual timeline.

---

# 55. Tại sao animation nên được làm tương đối sớm?

Animation là UI-only nếu làm đúng projection architecture.

Nó có ba lợi ích sớm:

1. ép team chuẩn hóa state semantics;
2. làm lộ ngay chỗ runtime đang thiếu event/typed state;
3. giúp operator kiểm chứng routing/authority trực quan trước khi thêm governor tự động.

Nó không nên chỉ là cosmetic task.

Nếu implementation buộc phải hỏi:

```text
“edge này đang chạy vì sao?”
```

mà runtime không trả lời được bằng evidence, đó là signal về observability gap.

---

# 56. Acceptance criteria cho Live Execution Fabric

## Truthfulness

- OpenCode online không animate DeepSeek nếu không có delegation.
- Model lane active chỉ từ delegation/provider-call evidence.
- Writer active chỉ từ write-authority/mutation evidence.
- Proof state chỉ từ actual proof event.
- Queue/cooldown không render thành active.

## Direction

- inbound request có direction rõ;
- dispatch outward;
- response inward;
- write/proof là path khác compute.

## Lifecycle

- animation stop khi state terminal;
- stale frontend state có timeout/freshness guard;
- hidden window không tốn animation CPU đáng kể.

## Accessibility

- reduced motion static state vẫn đầy đủ thông tin;
- color không là signal duy nhất;
- badge/text state vẫn tồn tại.

## Performance

- idle gần như zero animation work;
- bounded particle DOM count;
- không full topology rerender mỗi tick nếu state không đổi.

---

# 57. Acceptance criteria cho Usage/Traffic plane

- provider-reported usage không bị cộng trùng estimate;
- cached token preserved;
- unknown quota không thành 100%;
- reservation idempotent;
- queue không tạo duplicate dispatch;
- 429/capacity/deadline phân loại riêng;
- policy mutation audited;
- Traffic Governor không thay semantic route requirement;
- high-cost gate vẫn enforce;
- provider state không được dùng như proof;
- historical aggregation bounded;
- live stream delta không chứa secrets/raw prompts.

---

# 58. Test strategy

## Unit

```text
usage canonicalization
quota freshness
cooldown expiry
RPM bucket
TPM reservation/refund
idempotent reservation
route eligibility
visual event projection
```

## Renderer

```text
no false animation from connectivity
active delegation → correct edge
queue → waiting visual
cooldown → cooldown visual
writer lease → writer edge only
reduced motion → no moving particles
```

## Integration

```text
request → route → usage event
429 → cooldown → queue/no blind retry
quota reset → route eligible
proof lifecycle → topology states
```

## Fault injection

```text
lost stream
stale event
provider response without usage
provider usage malformed
quota adapter error
reservation outcome unknown
runtime reconnect
client cursor lag
```

---

# 59. No-go list

Không nên:

1. port toàn bộ 9router architecture;
2. biến Tools-Codex-web thành generic AI proxy;
3. đưa React Flow vào chỉ vì animation;
4. copy code/assets khi chưa kiểm tra license/attribution obligations;
5. thêm public MCP tools chỉ cho dashboard;
6. round-robin Mini/Terra/Sol như node đồng cấp;
7. tự fallback xuống model yếu hơn khi semantic requirement không cho phép;
8. coi request/response bytes là provider billing token;
9. hiển thị quota unknown như healthy/full;
10. silent trim middle conversation mặc định;
11. retry serial ladder sau 429/capacity;
12. animate connectivity như execution;
13. dùng animation làm source of truth;
14. cho UI thay authority;
15. chạy particle/spark vô hạn khi edge đã idle;
16. làm provider-specific API logic trong renderer;
17. mass rewrite dashboard trước khi canonical telemetry ổn định;
18. tối ưu throughput bằng tăng agents nếu task thực tế serial;
19. làm ML router trước deterministic governor;
20. weaken proof/EOCL để đạt latency đẹp hơn.

---

# 60. Adopt / Adapt / Reject matrix

## Adopt gần như trực tiếp về nguyên lý

```text
canonical usage normalization
cached-token visibility
historical + realtime split
quota/reset state as operator data
provider-specific refresh cadence
pause UI polling when hidden
active topology state
node glow + directional particles
stale active frontend guard
```

## Adapt theo Execution Hub

```text
provider pool
    → semantic route pool

account disable
    → route/account eligibility pause

round-robin
    → weighted least-loaded inside equivalence class

provider topology
    → execution fabric

active provider
    → typed execution phase

quota UI
    → quota + traffic + authority-aware operations

history request log
    → task/run/wave/delegation trace
```

## Reject cho production mặc định

```text
generic model round-robin
silent context middle-drop
UI-side provider authority
framework migration chỉ vì graph
unbounded decorative animation
```

---

# 61. Recommended final topology UX

Một màn hình lý tưởng:

```text
┌──────────────────────────────────────────────────────────────┐
│ LIVE EXECUTION FABRIC                              ● LIVE    │
│ 3 clients · 1 route · 1 writer · 0 blocked                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│        ChatWeb ●          Desktop ○        OpenCode ○         │
│            │                                                 │
│            │ ● ● ●                                           │
│            ▼                                                 │
│        ┌────────────────┐                                    │
│        │ Execution Hub  │                                    │
│        │ ROUTED         │                                    │
│        └────────────────┘                                    │
│            │                                                 │
│            ├════●══●════▶ Fast / Luna ● ACTIVE              │
│            │                                                 │
│            ├───────────── Terra ○ IDLE                       │
│            │                                                 │
│            └──────╳────── Sol ◔ COOLDOWN 31s                │
│                                                              │
│                    ▼                                         │
│               MCP Writer ○ idle                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ACTIVE REQUEST                                               │
│ agent_workflow → Luna                                        │
│ input 18.4k · cached 9.2k · output 2.1k · queue 0.4s        │
└──────────────────────────────────────────────────────────────┘
```

Điểm quan trọng là mọi animation đều có evidence path.

---

# 62. Recommended final data/control UX

```text
┌──────────────────────────────────────────────────────────────┐
│ TRAFFIC & USAGE                                             │
├──────────────────────────────────────────────────────────────┤
│ Active 3   Queue 2   RPM 18   TPM 41k   429 0.8%           │
│ Cache 63%  p95 4.2s  Estimated accepted cost ...            │
├──────────────────────────────────────────────────────────────┤
│ Live Traffic chart                                           │
├──────────────────────────────────────────────────────────────┤
│ Route        State       Queue     Quota      Cache           │
│ Mini/Luna    Healthy       0       81%         42%            │
│ Terra        Busy          0       unknown     36%            │
│ Sol          Cooldown      1        8%         70%            │
├──────────────────────────────────────────────────────────────┤
│ Warnings                                                     │
│ Sol provider capacity · retry in 31s                         │
└──────────────────────────────────────────────────────────────┘
```

---

# 63. Thứ tự implementation tối ưu

Nếu bắt đầu triển khai ngay, thứ tự nên là:

```text
1. Visual/event state contract
2. Live Execution Fabric SVG upgrade
3. Canonical UsageEvent
4. Unified Cooldown Registry
5. TrafficSnapshot/read model
6. Traffic & Usage page
7. Queue + concurrency governor
8. RPM/TPM + reservation
9. Provider quota adapters
10. Capacity-aware route scorer
11. Replay/flight recorder
```

Lý do animation đứng sớm:

- phần lớn read-only/projection;
- tạo giá trị operator ngay;
- ép chuẩn hóa event semantics;
- ít rủi ro hơn governor tự động;
- giúp debug các bước governor sau.

Lý do provider quota đứng sau:

- provider APIs không đồng nhất;
- freshness và auth complexity;
- không nên block architecture vào API quota cụ thể.

---

# 64. Implementation files có khả năng bị tác động

## UI

```text
renderer/index.html
renderer/control-center.js
renderer/control-center.css
renderer/dashboard.js
renderer/dashboard.css
```

Có thể thêm module JS riêng thay vì tiếp tục phình file:

```text
renderer/execution-fabric.js
renderer/traffic-usage.js
```

chỉ khi code thực tế đủ lớn để extraction có giá trị.

## Electron bridge

Các IPC/control bindings hiện có nên được mở rộng theo read-only snapshot/delta thay vì tạo runtime thứ hai.

## MCP runtime

```text
resources/coding-tools-mcp/coding_tools_mcp/
```

Nên thêm canonical traffic state ở đây hoặc ở một module control-plane dùng chung.

## Codex bridge

`codex_bridge.py` tiếp tục là adapter nguồn cho:

```text
model usage
cache ratio
estimated credits
capacity cooldown
```

Không để dashboard đọc bridge internals trực tiếp.

---

# 65. Risk register

## Risk 1 — đẹp nhưng sai

Animation chạy dựa trên inferred state.

Mitigation:

```text
TopologyProjector chỉ đọc typed events/snapshots
```

## Risk 2 — trộn token planes

Mitigation:

```text
measurement provenance bắt buộc
```

## Risk 3 — rate governor làm giảm chất lượng

Mitigation:

```text
semantic eligibility trước governor
```

## Risk 4 — UI CPU cao

Mitigation:

```text
bounded particles
hidden pause
reduced motion
no idle loop
```

## Risk 5 — provider quota stale

Mitigation:

```text
fetched_at
stale_after
source
unknown state
```

## Risk 6 — retry/reservation double spend

Mitigation:

```text
idempotency identity + reconciliation
```

## Risk 7 — server.py tiếp tục phình

Mitigation:

```text
extract concrete traffic modules khi có use case thực
```

---

# 66. KPI để chứng minh nâng cấp có giá trị

Không dùng “animation trông đẹp” làm acceptance duy nhất.

## Observability KPIs

```text
% model calls có usage provenance
% calls có phase timing
% rate/capacity failures typed
% route state explainable từ event
```

## Economics KPIs

```text
credits / accepted result
model-visible bytes / accepted result
cache ratio
retry spend
repair spend
```

## Traffic KPIs

```text
429 rate
capacity false-start rate
queue p50/p95
provider utilization
route cooldown frequency
```

## UX KPIs

```text
false-active topology incidents = 0
stuck-animation incidents = 0
operator can identify active route from topology
operator can identify write/proof phase
```

---

# 67. Strategic conclusion

9router là nguồn tham khảo rất tốt, nhưng giá trị lớn nhất không nằm ở việc “có nhiều provider” hay “có dashboard đẹp”.

Giá trị thật nằm ở pattern:

```text
observe
   ↓
normalize
   ↓
understand capacity
   ↓
control traffic
   ↓
route/fallback
   ↓
show operator why
   ↓
measure again
```

Tools-Codex-web đã có một control plane mạnh hơn ở mặt coding execution:

```text
EOCL
controller fencing
writer authority
proof
accepted result
```

Vì vậy kiến trúc kết hợp tốt nhất là:

```text
9router-style traffic intelligence
             +
Tools-Codex-web execution authority
             ↓
AI Execution Operations Console
```

Đích cuối không phải một router nhiều hiệu ứng, mà là một hệ thống nơi operator có thể nhìn thấy và trả lời ngay:

1. Ai đang điều khiển task?
2. Model nào thực sự đang chạy?
3. Request đang dispatch, stream, queue hay cooldown?
4. Bao nhiêu token là measured, bao nhiêu là estimated?
5. Cache có hiệu quả không?
6. Provider/route còn capacity/quota không?
7. Tại sao router chọn lane này?
8. Repository có đang bị ghi không?
9. Proof đang chạy hay đã pass?
10. Kết quả đã được final-accept hay chưa?
11. Chi phí của **accepted result** là bao nhiêu?
12. Nếu task chậm, bottleneck nằm ở queue, provider, proof hay control plane?

Nếu Execution Hub trả lời được 12 câu này bằng dữ liệu thật và animation chỉ là projection của dữ liệu đó, phần tham khảo từ 9router đã được áp dụng đúng.

---

# 68. Quyết định khuyến nghị cuối cùng

## Nên làm

```text
A. Nâng Live Routing hiện tại thành Live Execution Fabric
B. Giữ SVG/DOM; không migration React Flow
C. Directional particles + restrained electric glow
D. Event-driven visual states
E. Canonical UsageEvent
F. Unified Quota/Cooldown state
G. Queue + RPM/TPM governor theo từng wave
H. Tách Traffic & Usage thành operator page riêng
I. Flight recorder replay sau khi live state ổn định
```

## Không nên làm

```text
A. Port source 9router nguyên khối
B. Copy generic round-robin vào model tiers
C. Copy silent context trimming
D. Thêm public MCP tools cho UI
E. Cho animation suy đoán provider activity
F. Xây governor trước measurement truth
G. Tối ưu model-call price thay vì accepted-result economics
```

**Khuyến nghị rollout:** bắt đầu bằng **P0 measurement contract + P1 Live Execution Fabric**, sau đó hợp nhất cooldown/traffic state trước khi bật governor tự động. Đây là đường có tỷ lệ lợi ích/rủi ro tốt nhất và phù hợp với kiến trúc hiện tại của Tools-Codex-web.

---

## Appendix A — Source map 9router tham khảo

```text
Repository
  decolua/9router

Usage UI
  src/app/(dashboard)/dashboard/usage/page.js
  src/shared/components/UsageStats.js
  src/app/(dashboard)/dashboard/usage/components/UsageTable.js

Live topology
  src/app/(dashboard)/dashboard/usage/components/ProviderTopology.js

Quota / limits
  src/app/(dashboard)/dashboard/usage/components/ProviderLimits/index.js
  src/app/(dashboard)/dashboard/quota/page.js

Usage APIs
  src/app/api/usage/stats/route.js
  src/app/api/usage/history/route.js
  src/app/api/usage/stream/route.js

Usage persistence
  src/lib/db/repos/usageRepo.js

Token normalization
  open-sse/utils/usageTracking.js

Capacity/fallback
  open-sse/services/capacityAdapter.js
  open-sse/services/combo.js

Request/streaming path
  open-sse/handlers/chatCore/streamingHandler.js
  open-sse/handlers/chatCore/requestDetail.js
```

## Appendix B — Source map Tools-Codex-web hiện tại

```text
Live routing UI
  renderer/index.html
  renderer/control-center.js
  renderer/control-center.css

Usage/context/cost dashboard
  renderer/dashboard.js
  renderer/dashboard.css

Runtime / EOCL / tool surface
  resources/coding-tools-mcp/coding_tools_mcp/server.py

Codex usage/cache/capacity adapter
  resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py

Architecture/current behavior
  README.md
  docs/research/260814_TOOLS_CODEX_WEB_OPTIMAL_PERFORMANCE_COST_UPGRADE_METHODOLOGY.md
```

## Appendix C — Design mantra

```text
ANIMATE EVIDENCE, NOT ASSUMPTIONS.

CONTROL TRAFFIC, NOT AUTHORITY.

MEASURE PROVIDER USAGE WHEN AVAILABLE,
ESTIMATE ONLY WHEN NECESSARY.

OPTIMIZE THE COST OF A CORRECT ACCEPTED RESULT,
NOT THE PRICE OF AN INDIVIDUAL MODEL CALL.
```
