# 260814 — Execution Hub Multi-Provider Orchestration + 9-Node Live Router UI

**Ngày:** 2026-08-14  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**Base HEAD:** `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`  
**Trạng thái:** kiến trúc mục tiêu + UI router đã triển khai ở source và qua focused proof; chưa thay production routing threshold, chưa restart Electron trong wave này.

> **Completion update:** xem `docs/research/260814_NON_UI_TECHNICAL_COMPLETION_STATUS.md` cho trạng thái authoritative sau các wave Measurement Truth, exact OpenCode telemetry, read-only Provider Adapter và shadow routing. Các phần “target/future” bên dưới được giữ lại để bảo toàn lịch sử thiết kế.

---

## 1. Kết luận kiến trúc

Bài toán đúng không phải là “model nào tốt nhất”, cũng không phải một chuỗi fallback cố định kiểu:

```text
Flash -> Pro -> Terra -> Sol
```

Bài toán đúng là **điều phối nhiều provider theo task class, authority, risk, evidence, latency và total cost/accepted task**.

Phân tách provider phải rõ:

- **Codex provider plane**: Mini, Luna, GPT-5.6 Terra, GPT-5.6 Sol.
- **OpenCode Go provider plane**: DeepSeek V4 Flash, DeepSeek V4 Pro.
- **ChatWeb**: semantic controller và final acceptance trong topology hiện tại.
- **Coding Tools Runtime / MCP**: canonical execution state, write authority, proof, idempotency, task/run/wave ledger.
- **Electron**: runtime supervisor, local credential boundary, Control Center.

North-star:

```text
                         +-------------------+
                         |      ChatWeb      |
                         | semantic control  |
                         +---------+---------+
                                   |
                            OpenAI tunnel
                                   |
+----------------+          +------v-------+          +----------------+
| Codex Desktop  |--stdio-->|              |<--stdio--|    OpenCode    |
| Codex frontend |  proxy   | Execution Hub|  proxy   |  Go frontend   |
+----------------+          | ONE authority |          +----------------+
                            +------+-------+
                                   |
                    +--------------+--------------+
                    |                             |
             +------v------+               +------v-------+
             | Codex plane |               | OpenCode Go  |
             | Mini/Luna   |               | DeepSeek     |
             | Terra/Sol   |               | Flash/Pro    |
             +------+------+               +------+-------+
                    |                             |
                    +--------------+--------------+
                                   |
                            +------v-------+
                            | MCP writer   |
                            | proof/fence  |
                            +------+-------+
                                   |
                               workspace
```

Điểm quan trọng nhất:

> **Có nhiều compute provider nhưng chỉ có một execution truth.**

Không provider/model nào được tự trở thành canonical writer, proof owner hay final semantic authority chỉ vì model đó mạnh hơn.

---

## 2. “9 router” nên hiểu là 9-node Router Fabric, không phải 9 controller

UI mới dùng 9 node vì nó giúp quan sát hệ thống trực quan, nhưng về semantics các node không ngang quyền.

### 2.1 Chín node

1. **ChatWeb** — semantic controller / final acceptance.
2. **Codex Desktop** — deep-code frontend.
3. **OpenCode** — OpenCode Go frontend.
4. **Execution Hub** — một runtime authority.
5. **MCP Writer / Proof** — mutation + proof + fencing.
6. **Codex Fast** — Mini / Luna.
7. **Codex Deep** — Terra.
8. **Codex Critical** — Sol.
9. **OpenCode Go** — DeepSeek V4 Flash / Pro.

### 2.2 Authority không chia đều

| Node | Controller | Writer | Worker | Observer / UI |
|---|---:|---:|---:|---:|
| ChatWeb | Có, mặc định | Không | Có thể yêu cầu work | Có |
| Codex Desktop | Có thể nhận handoff controller | Không trực tiếp | Có | Có |
| OpenCode | Không ở phase hiện tại | Không trực tiếp | Có | Có |
| Execution Hub | Control-plane authority | Điều phối | N/A | Có |
| MCP Writer/Proof | Không | **Có** | N/A | Có |
| Mini/Luna | Không | Không | Có | N/A |
| Terra | Không | Không | Có | N/A |
| Sol | Không | Không | Có | N/A |
| DeepSeek Flash/Pro | Không | Không | Có | N/A |

Không có controller-transfer button cho OpenCode trong UI hiện tại. Đây là chủ ý, không phải thiếu UI.

Lý do: continuity/handoff semantics giữa ChatWeb và Codex Desktop đã có durable controller/fence model; OpenCode mới chỉ chứng minh frontend + MCP semantic tool-use, chưa chứng minh full controller continuity.

---

## 3. Current state vs target state

### 3.1 Current state đã có

- Electron-owned local loopback gateway.
- Thin stdio proxy cho Codex Desktop.
- Thin stdio proxy cho OpenCode.
- OpenCode semantic tool result compatibility (`structuredContent` canonical + text mirror cho OpenCode).
- Hub client registry.
- ChatWeb controller lease/fencing.
- Codex Desktop worker identity.
- OpenCode worker identity.
- MCP write lease/proof authority.
- Delegation/lane telemetry cho Codex-side routes.
- 9-node live router UI lấy state từ Hub/runtime.

### 3.2 Target state chưa nên tuyên bố đã có

Hub **chưa có một OpenCode Provider Adapter hoàn chỉnh** để tự dispatch:

```text
Hub -> OpenCode Go -> DeepSeek Flash/Pro
```

và nhận lại đầy đủ:

- provider/model identity,
- run/session identity,
- status,
- usage/cost,
- tool-call boundary,
- proof relationship,
- parent run/wave,
- terminal outcome.

Hiện OpenCode là một frontend kết nối vào Hub; người dùng hoặc OpenCode process chọn model.

Do đó không được nói rằng production router hiện đã tự route DeepSeek giống như Codex App Server lane.

---

## 4. Rủi ro lớn nhất khi biến OpenCode thành auto-dispatched provider

OpenCode có hệ tool riêng ngoài MCP. Nếu một Hub-side adapter chỉ chạy:

```text
opencode run -m opencode-go/deepseek-v4-flash ...
```

nhưng để model dùng edit/bash/write native của OpenCode, nó có thể thay workspace mà không đi qua MCP write lease/proof.

Điều đó phá invariant:

```text
ONE canonical writer per workspace
```

Vì vậy OpenCode auto-provider chỉ được promote khi thỏa một trong hai topology:

### Phương án A — read-only delegated agent

- OpenCode native write/edit/bash side effects bị disable hoặc fail-closed.
- DeepSeek chỉ được đọc evidence / reasoning / review.
- Mọi mutation do MCP apply/proof thực hiện sau khi Hub nhận change proposal.

Đây là phương án nên dùng trước.

### Phương án B — all mutations proxied through MCP

OpenCode agent có thể đề xuất mutation nhưng tool surface chỉ expose MCP mutation path có write fence.

Phương án này mạnh hơn nhưng cần adapter/plugin integration sâu hơn.

### Không chấp nhận

```text
Hub dispatch DeepSeek
        +
OpenCode native edit/bash enabled
        +
MCP cũng có writer
```

vì khi đó có hai side-effect planes không cùng fencing domain.

---

## 5. Router phải chọn provider trước, model sau

Không nên xem toàn bộ model như một danh sách phẳng.

Router đúng có hai tầng:

```text
Task
  |
  v
Provider / execution-plane choice
  |-- deterministic MCP
  |-- Codex plane
  `-- OpenCode Go plane
          |
          v
Model choice inside eligible provider
```

Ví dụ:

```text
localized patch + strong oracle
  -> Codex plane
     -> Mini, sau đó Luna nếu task class thực sự khó hơn

wide read-only repository exploration
  -> OpenCode Go plane
     -> DeepSeek Flash

hard long-context independent review
  -> OpenCode Go plane
     -> DeepSeek Pro

evidence-localized cross-file architecture
  -> Codex plane
     -> Terra xhigh

deep task cần latency tốt
  -> Codex plane
     -> Sol high

broad + ambiguous + high consequence
  -> Codex plane
     -> Sol xhigh
```

---

## 6. Hard gates trước scoring

Router không nên chọn model chỉ bằng một score liên tục. Trước tiên cần các hard gate.

### Gate 1 — authority

- Có active controller hợp lệ không?
- Có writer khác đang giữ lease không?
- Client có đúng role không?
- Fencing token có hợp lệ không?

Fail => không dispatch mutation.

### Gate 2 — side-effect class

Task được phân thành:

- read-only,
- proposed-change,
- deterministic mutation,
- consequential mutation.

OpenCode phase đầu chỉ nên auto-dispatch read-only/proposed-change.

### Gate 3 — provider readiness

- provider connected?
- adapter healthy?
- model available?
- credentials held đúng boundary?
- no stale session/descriptor?

### Gate 4 — evidence quality

- packet đã localize đủ chưa?
- model có cần repo exploration không?
- oracle có rõ không?

Nếu evidence đã rất localized, dùng model quá mạnh thường chỉ tăng chi phí.

### Gate 5 — risk

- security/auth/permission?
- release/build infrastructure?
- cross-process lifecycle?
- destructive side effect?
- uncertain external system?

Risk cao có thể bắt buộc Sol/reviewer hoặc independent second opinion.

---

## 7. Scoring chỉ áp dụng sau hard gates

Khi nhiều route đều eligible, có thể dùng conceptual utility:

```text
route_utility =
    expected_acceptance_value
  - alpha * expected_total_cost
  - beta  * expected_latency
  - gamma * repair_probability
  - delta * authority_or_side_effect_risk
  - eta   * duplicate_work_penalty
```

Đây là **mô hình thiết kế**, chưa phải production formula hiện tại.

Metric tối ưu phải là:

```text
total cost / accepted task
```

không phải:

```text
cost / model call
```

Vì end-to-end còn gồm:

- controller reasoning,
- packet preparation,
- candidate worker,
- provider startup,
- cache state,
- retry/replan,
- MCP proof,
- final acceptance.

---

## 8. Task-class routing matrix đề xuất

| Task class | Primary route | Optional reviewer | Lý do |
|---|---|---|---|
| deterministic inspect/apply/test | MCP deterministic | none | không cần model tax |
| localized bug + strong oracle | Codex Mini | Luna nếu scope thực sự tăng | rẻ, nhanh, bounded |
| bounded leaf khó | Codex Luna | Terra khi cross-file thật | tránh Sol tax |
| broad read-only scan | DeepSeek Flash | none | cheap breadth / long context |
| broad scan cần stronger reasoning | DeepSeek Pro | Terra nếu cần independent synthesis | không dùng Pro mặc định |
| cross-file architecture, evidence đã localize | Terra xhigh | none / Sol high nếu latency/risk yêu cầu | deep economics |
| deep design, latency quan trọng | Sol high | Terra read-only reviewer nếu consequential | fast deep lane |
| broad ambiguous root cause | Sol xhigh | DeepSeek Pro independent reviewer khi đáng giá | breadth + depth |
| auth/security/consequential mutation | Sol xhigh hoặc Sol high tùy risk | independent Pro/Terra review | correctness > token cost |
| repetitive review nhiều module | Flash parallel read-only slices | Terra synthesis | breadth rẻ + deep synthesis |

---

## 9. Phối hợp Flash + Terra là một pattern có giá trị

Thay vì chạy Flash rồi fail mới chạy Terra, có thể dùng hai model với **vai trò khác nhau**.

### Pattern

```text
DeepSeek Flash
  -> broad read-only evidence mining
  -> compact findings + references

Terra
  -> synthesize cross-file invariant
  -> reason over localized packet

MCP
  -> deterministic apply + proof

ChatWeb
  -> accept/reject
```

Đây không phải fallback waterfall.

Flash làm breadth; Terra làm synthesis.

Pattern này đáng test vì benchmark hiện tại cho thấy:

- broad repo exploration có thể tốn rất nhiều orchestration/time nếu giao thẳng cho deep model;
- Terra có economics tốt khi evidence được localize;
- Flash có chi phí rất thấp cho independent read-only reasoning.

---

## 10. Phối hợp Pro + Sol chỉ nên dùng có điều kiện

Pro và Sol đều có thể giải bài reasoning khó. Chạy cả hai cho mọi task là duplicate-work tax.

Chỉ đáng dùng khi cần **independent evidence**, ví dụ:

- security boundary,
- auth/permission semantics,
- concurrency/race,
- migration/destructive change,
- release-critical decision,
- hai giải pháp kiến trúc có trade-off lớn.

Pattern:

```text
Sol
  -> primary deep solution

DeepSeek Pro
  -> independent adversarial review
  -> không đọc chain-of-thought của Sol
  -> chỉ đọc problem/evidence/proposed diff

ChatWeb
  -> reconcile disagreement

MCP
  -> proof final chosen change
```

Điểm giá trị là **independence**, không phải “hai model mạnh hơn một”.

---

## 11. Terra và Sol trong Codex plane

### Terra xhigh — Deep Economics Lane

Nên ưu tiên khi:

- cross-file reasoning,
- evidence đã được localize,
- architecture/risk review,
- không cần shortest latency,
- muốn deep reasoning nhưng không muốn Sol xhigh economics.

Observed cùng deep packet:

- Terra xhigh: 28.360s, 1.259625 credits.
- Sol high: 19.061s, 2.133750 credits.

Terra rẻ hơn đáng kể nhưng chậm hơn.

### Sol high — Deep Fast Lane

Nên ưu tiên khi:

- task deep nhưng scope đủ rõ,
- latency quan trọng,
- cần solution concise nhanh.

### Sol xhigh — Critical Ambiguity Lane

Nên giữ cho:

- broad root cause,
- ambiguous multi-system integration,
- security/consequential design,
- high-value task nơi repair cost cao hơn model cost.

Không nên dùng Sol xhigh chỉ vì task “khó”.

---

## 12. Flash và Pro trong OpenCode plane

### DeepSeek V4 Flash — Breadth / Volume Lane

Nên ưu tiên khi:

- read-only scan,
- context lớn,
- nhiều independent hypotheses,
- review lặp lại,
- parallel evidence mining,
- cần economics tốt.

### DeepSeek V4 Pro — Strong OpenCode Review Lane

Nên dùng khi:

- Flash evidence không đủ chắc,
- long-context reasoning khó hơn,
- independent review của Codex proposal,
- cần một provider-family khác để giảm correlated error.

Không nên dùng Pro làm default chỉ vì tên “Pro”.

---

## 13. Không dùng fixed fallback waterfall

Sai:

```text
Mini fail -> Luna -> Flash -> Pro -> Terra -> Sol
```

Vì mỗi lần fail có thể do nguyên nhân khác nhau:

- transport,
- deadline,
- thiếu evidence,
- packet quá rộng,
- wrong task class,
- tool incompatibility,
- model capability,
- proof failure.

Route sau chỉ được đổi khi có **typed REPLAN reason**.

Ví dụ:

```text
Terra deadline, no change-set
```

Nếu scope đã localize đủ thì route đúng có thể là deterministic MCP patch/proof, không phải tự động lên Sol.

Đây chính là điều đã xảy ra trong UI implementation wave ngày 2026-08-14.

---

## 14. Failure taxonomy cho router

### `TRANSPORT_FAILURE`

- retry cùng route nếu operation idempotent và provider session chưa ambiguous;
- nếu descriptor/session đổi, reinitialize trước retry.

### `DEADLINE_WITH_NO_PROPOSAL`

- kiểm tra packet/evidence size;
- nếu scope đã deterministic thì chuyển về MCP;
- chỉ nâng model nếu ambiguity/capability thật sự là bottleneck.

### `INSUFFICIENT_EVIDENCE`

- thêm investigator/breadth route;
- Flash là ứng viên tốt cho read-only evidence expansion.

### `LOW_CONFIDENCE_REASONING`

- same-family upgrade có thể hợp lý: Flash -> Pro;
- hoặc cross-provider reviewer nếu risk cao.

### `PROOF_FAILURE`

- không đổi model ngay;
- sửa implementation/change-set dựa trên oracle failure.

### `AUTHORITY_OR_FENCE_FAILURE`

- không model nào được bypass;
- repair control plane trước.

---

## 15. Concurrency policy

### Luật cơ bản

```text
semantic controller: 1
workspace writer:    1
proof authority:     MCP
read-only workers:   có thể >1, bounded
```

### Parallelization tốt

- Flash scan module A/B/C read-only.
- Mini/Luna investigate independent localized tests.
- Pro independent review của một proposal.

### Parallelization xấu

- Terra và Sol cùng sửa workspace.
- OpenCode native edit song song MCP writer.
- hai provider cùng giải nguyên packet chỉ để “xem ai tốt hơn” trong production path.

### Admission rule đề xuất

Parallel worker chỉ được mở nếu:

```text
expected_information_gain > duplicate_work_cost
```

và không tạo write-authority conflict.

---

## 16. Provider-aware synthesis

Một task phức tạp có thể gồm nhiều stage, mỗi stage một route khác nhau.

Ví dụ migration lớn:

```text
1. Flash
   broad inventory / read-only search

2. Terra
   derive migration invariant + sequencing

3. Mini/Luna
   implement localized leaves one-by-one

4. MCP
   tests/proofs each wave

5. Pro
   independent regression/risk review nếu migration consequential

6. ChatWeb
   final semantic acceptance
```

Đây là orchestration theo **work decomposition**, không theo “model ranking”.

---

## 17. Router UI phải phản ánh truth, không phản ánh ý định

UI mới có 4 trạng thái chính:

### Offline

- client không heartbeat,
- provider lane không có evidence active.

### Connected

- client có heartbeat / runtime online,
- không nhất thiết có model đang chạy.

### Waiting

- lane/delegation queued, pending, idle-waiting.

### Active

- có evidence task/delegation/write đang thực sự active.

### Blocked

- failed/replanned/interrupted state có evidence.

Animation chỉ chạy với `active`.

Nếu user bật reduced-motion, animation bị tắt bằng:

```css
@media (prefers-reduced-motion: reduce)
```

---

## 18. Ý nghĩa animation

Animation không phải decoration.

Một edge chuyển động phải có nghĩa:

```text
source node currently participates in an observed active execution path
```

Ví dụ:

```text
ChatWeb ----animated----> Execution Hub
```

chỉ khi ChatWeb là active controller hoặc có execution evidence tương ứng.

```text
Codex Deep / Terra ----animated----> Execution Hub
```

chỉ khi delegation model/route xác định Terra và status active/running.

```text
OpenCode Go / DeepSeek ----animated----> Execution Hub
```

chỉ khi Hub có model/delegation metadata xác định DeepSeek active.

Không được bật animation DeepSeek chỉ vì OpenCode frontend đang connected.

---

## 19. OpenCode identity bug đã được xử lý

Trước wave này, gateway local hard-code mọi stdio proxy thành:

```text
client_id   = codex-desktop
client_type = codex_desktop
```

Do đó nếu chỉ thêm OpenCode card, UI sẽ báo sai.

Fix hiện tại dùng dedicated local headers:

```text
X-Coding-Tools-Proxy-Client-Id
X-Coding-Tools-Proxy-Client-Type
```

Allowlist:

```text
codex-desktop | codex_desktop
opencode      | opencode
```

Gateway mới canonicalize thành upstream Hub identity.

Không cho frontend tự spoof:

```text
chatweb | chatweb
```

qua local proxy.

Canonical client headers do frontend tự gửi không được tin để nâng quyền.

---

## 20. OpenCode là worker-only ở phase hiện tại

Server role mapping:

```text
chatweb        -> controller
codex_desktop  -> worker
opencode       -> worker
electron       -> supervisor
```

Test đảm bảo heartbeat/request của OpenCode không làm đổi:

- ChatWeb controller owner,
- controller fencing token.

UI không có:

```text
transferController('opencode')
```

Đây là invariant nên giữ cho tới khi OpenCode continuity contract được thiết kế riêng.

---

## 21. Exact Flash vs Pro live telemetry là gap còn lại

Hiện Hub có thể biết chắc:

```text
OpenCode frontend connected
```

nhưng không phải mọi MCP request đều mang thông tin:

```text
model = deepseek-v4-flash
```

hay:

```text
model = deepseek-v4-pro
```

Do đó UI không được đoán model.

### Target telemetry

Một OpenCode Provider Adapter tương lai nên đăng ký mỗi run:

```json
{
  "provider": "opencode_go",
  "frontend_client_id": "opencode",
  "model": "deepseek-v4-flash",
  "run_id": "...",
  "wave_id": "...",
  "provider_session_id": "...",
  "status": "running",
  "side_effect_class": "read_only",
  "usage": {
    "input_tokens": 0,
    "cached_tokens": 0,
    "output_tokens": 0,
    "estimated_cost": 0
  }
}
```

Không cần thêm top-level MCP tool thứ 9.

Metadata có thể đi qua existing coordination/delegation/control plane.

---

## 22. Target OpenCode Provider Adapter

Nên là thin execution adapter, không phải runtime authority thứ hai.

```text
Execution Hub
    |
    | dispatch bounded packet
    v
OpenCode Provider Adapter
    |
    | selects exact OpenCode Go model
    v
DeepSeek Flash / Pro
    |
    | read-only findings / proposal / usage events
    v
Execution Hub ledger
```

Adapter chịu trách nhiệm:

- exact model identity,
- process/session lifecycle,
- bounded prompt packet,
- timeout,
- output normalization,
- usage/cost capture,
- run/wave correlation,
- cancellation,
- fail-closed side-effect policy.

Adapter **không** giữ canonical task state riêng.

---

## 23. OpenCode Adapter phase đầu nên read-only

Đây là lựa chọn an toàn và có giá trị ngay.

Allowed:

- investigate,
- explain,
- review,
- compare,
- produce patch proposal text,
- produce file/line evidence references.

Disallowed:

- edit source trực tiếp,
- shell command có side effect,
- package install,
- git mutation,
- process restart,
- deploy.

MCP sau đó quyết định deterministic mutation.

---

## 24. Control Center nên hiển thị thêm provider telemetry ở phase sau

Mỗi compute node nên có:

- provider,
- exact model,
- state,
- current run/wave,
- elapsed,
- input/cached/output,
- estimated cost,
- task class,
- read-only vs mutation intent,
- confidence,
- last proof relationship.

Ví dụ:

```text
OPEN CODE GO
DeepSeek V4 Flash
ACTIVE · read-only investigator
12.4s · $0.0016
run 7c... / wave 02
```

Hoặc:

```text
CODEX DEEP
GPT-5.6 Terra · xhigh
WAITING
packet localized · cache 81%
```

---

## 25. UI không nên chỉ có “model đang chạy”

Một Control Center hữu ích cần tách:

### Frontend state

- ChatWeb connected?
- Codex Desktop connected?
- OpenCode connected?

### Authority state

- controller owner?
- fencing token?
- writer active?

### Compute state

- provider/model nào active?
- task class?
- status?

### Economic state

- cost current task?
- cache ratio?
- orchestration tax?

### Proof state

- last proof?
- accepted/rejected/replan?

Như vậy user nhìn UI có thể trả lời ngay:

> Ai đang điều khiển? Ai đang suy luận? Ai được phép ghi? Task nào đang chạy? Chi phí ở đâu? Có proof chưa?

---

## 26. “Chạy cái nào kết nối cái đấy” — semantic cụ thể

Yêu cầu UI này nên được định nghĩa như sau:

### Nếu chỉ OpenCode app mở

```text
OpenCode node: connected
DeepSeek node: idle
```

Không animate DeepSeek.

### Nếu OpenCode Adapter dispatch Flash

```text
OpenCode node: connected
DeepSeek node: active
edge DeepSeek -> Hub: animated
label: Flash
```

### Nếu Terra lane active

```text
Codex Desktop có thể connected hoặc không tùy topology
Codex Deep/Terra: active
edge Terra -> Hub: animated
```

### Nếu MCP đang apply/test

```text
MCP Writer: active
edge Writer -> Hub: animated
```

### Nếu chỉ runtime alive

```text
Hub: connected
compute lanes: idle
no animated compute edges
```

Đây là behavior đáng tin hơn một dashboard luôn chuyển động.

---

## 27. Routing telemetry cần lưu theo accepted task

Mỗi accepted task nên ghi:

```text
task_class
primary_provider
primary_model
review_provider
review_model
packet_size
cache_ratio
worker_cost
controller_cost
proof_cost
wall_time
time_to_accept
repair_count
proof_fail_count
accepted_first_pass
critical_defect_after_accept
```

Metric tổng:

```text
TOTAL_CREDITS_PER_ACCEPTED_TASK
TTA
FIRST_PASS_RATE
REPAIR_RATE
CRITICAL_DEFECT_RATE
```

Không promote model chỉ từ một microbenchmark.

---

## 28. Evidence gate trước production auto-routing

Đề xuất tối thiểu cho mỗi route candidate:

```text
>= 10 accepted useful tasks
>= 3 representative task classes
```

Và phải có:

- first-pass rate,
- median/P90 TTA,
- cost/accepted,
- repair rate,
- proof failure rate,
- critical defect count.

Terra/Flash/Pro hiện vẫn chưa có cohort production đủ lớn để auto-promote threshold.

---

## 29. Recommended routing policy theo giai đoạn

### Phase 0 — hiện tại

- ChatWeb controller.
- MCP writer/proof.
- Codex routes dùng theo explicit/evidence-gated policy.
- OpenCode là worker frontend.
- UI quan sát 9-node fabric.

### Phase 1 — OpenCode read-only provider adapter

- Flash/Pro dispatch được từ Hub.
- direct write disabled.
- exact model/run telemetry.
- cost capture.

### Phase 2 — shadow router

Router tính recommendation nhưng chưa tự dispatch:

```text
recommended_primary = flash
recommended_reason  = broad_read_only_scan
```

So recommendation với route con người chọn.

### Phase 3 — bounded auto-route

Chỉ auto:

- deterministic,
- Mini localized,
- Flash read-only.

Terra/Pro explicit hoặc evidence-gated.

### Phase 4 — deep auto-route

Chỉ sau cohort đủ:

- Terra deep-economics,
- Sol high latency lane,
- Pro independent reviewer.

Sol xhigh vẫn consequence-gated.

---

## 30. Suggested primary route algorithm

Pseudo-policy:

```text
classify(task)
validate_authority()
classify_side_effects()
measure_evidence_localization()
measure_scope_and_ambiguity()
measure_risk()
check_provider_readiness()

if deterministic:
    MCP
elif localized && strong_oracle:
    Codex Mini/Luna
elif read_only && broad:
    DeepSeek Flash
elif read_only && broad && hard_reasoning:
    DeepSeek Pro
elif cross_file && evidence_localized && !latency_critical:
    Terra xhigh
elif deep && latency_critical:
    Sol high
elif broad && ambiguous && consequential:
    Sol xhigh
else:
    explicit controller decision
```

Reviewer selection là bước riêng, không trộn vào primary selection.

---

## 31. Reviewer algorithm

Chỉ thêm reviewer khi một trong các điều kiện đúng:

- risk high,
- uncertainty high,
- solution space có nhiều trade-off,
- mutation consequential,
- primary confidence thấp,
- provider-specific blind spot đáng lo.

Đề xuất:

```text
primary Codex -> reviewer OpenCode
primary OpenCode -> reviewer Terra/Sol
```

Cross-provider review có giá trị hơn same-provider duplicate ở nhiều case vì giảm correlated error.

---

## 32. Không nên dùng ChatWeb làm compute router cho mọi leaf

ChatWeb nên giữ:

- task interpretation,
- policy/authority,
- final acceptance,
- web/external research khi cần,
- reconciliation khi provider disagree.

Không nên tiêu ChatWeb Sol token để micro-manage từng file read nếu Hub/worker có thể xử lý deterministic.

Điều này giảm controller tax trong `total cost/accepted`.

---

## 33. Codex Desktop nên giữ vai trò gì

Codex Desktop phù hợp:

- deep interactive coding,
- long-lived code context,
- manual user-supervised deep sessions,
- Terra/Sol provider access,
- receive controller handoff khi ChatWeb rotation cần thiết.

Nó không nên trở thành runtime authority thứ hai.

---

## 34. OpenCode nên giữ vai trò gì

OpenCode phù hợp:

- alternative frontend,
- DeepSeek Go compute access,
- cheap read-only breadth,
- independent provider review,
- long-context parallel investigation.

Phase hiện tại:

```text
worker frontend
```

Target:

```text
worker frontend + Hub-dispatchable read-only provider adapter
```

Không cần biến nó thành controller để lấy giá trị.

---

## 35. Execution Hub là sản phẩm chính, không phải model switcher

Định vị sản phẩm tốt hơn:

> **Tools-Codex-web = local multi-provider execution control plane cho ChatWeb, Codex Desktop và OpenCode.**

Giá trị không nằm ở dropdown model.

Giá trị nằm ở:

- one execution truth,
- authority/fencing,
- provider-aware routing,
- proof,
- continuity,
- cost visibility,
- safe side-effect boundary,
- live topology.

---

## 36. Khi UI hoàn chỉnh hơn, user flow nên là

```text
User nêu mục tiêu ở ChatWeb / Desktop / OpenCode
                |
                v
Execution Hub classify + display recommendation
                |
                v
Primary compute node lights up
                |
                v
Optional reviewer lights up nếu policy yêu cầu
                |
                v
MCP Writer lights up khi mutation/proof bắt đầu
                |
                v
Final acceptance node/controller resolves
                |
                v
Task becomes CHECKPOINTED
```

User nhìn dashboard có thể hiểu cả quá trình mà không đọc log.

---

## 37. Animation đề xuất phase sau

Không thêm animation tùy hứng. Có thể nâng cấp theo semantic event:

### `dispatch`

Một pulse từ Hub tới compute lane.

### `working`

Edge compute -> Hub chạy dash animation.

### `proposal_ready`

Node compute chuyển active -> waiting review.

### `write_lease_acquired`

Writer node pulse mạnh một lần, sau đó active.

### `proof_pass`

Writer -> Hub pulse green/accepted indicator.

### `replan`

Edge hiện blocked/replan state, không chạy loop như active.

### `handoff`

Pulse giữa ChatWeb và Codex Desktop qua Hub, không vẽ frontend-to-frontend direct authority link.

---

## 38. UI layout 3x3 hiện tại có semantic hợp lý

```text
+----------------+----------------+----------------+
| ChatWeb        | Codex Desktop  | OpenCode       |
| controller     | frontend       | frontend       |
+----------------+----------------+----------------+
| Codex Fast     | Execution Hub  | OpenCode Go    |
| Mini/Luna      | authority      | Flash/Pro      |
+----------------+----------------+----------------+
| Codex Deep     | MCP Writer     | Codex Critical |
| Terra          | proof/fence    | Sol            |
+----------------+----------------+----------------+
```

Hub ở giữa giúp trực quan hóa invariant:

```text
mọi đường execution có quan sát/authority đều quy về Hub
```

---

## 39. Không nên vẽ direct edge Terra -> Sol hoặc Flash -> Pro

Vì điều đó tạo impression model tự fallback sang nhau.

Fallback/replan phải đi qua Hub:

```text
Terra -> Hub -> REPLAN -> Sol
```

không phải:

```text
Terra -> Sol
```

Tương tự:

```text
Flash -> Hub -> REPLAN -> Pro
```

Điều này giữ audit trail rõ.

---

## 40. Cost-aware but not cost-minimizing

Mục tiêu không phải luôn chọn model rẻ nhất.

Ví dụ một security migration:

- Flash có thể rẻ nhưng repair risk lớn hơn.
- Sol xhigh đắt nhưng nếu giảm critical defect, tổng business cost thấp hơn.

Vì vậy cost là constraint/penalty, không phải objective duy nhất.

---

## 41. Latency-aware but not fastest-model-wins

Sol high có thể nhanh hơn Terra trên deep packet.

Nhưng nếu task không latency-critical thì Terra economics có thể tốt hơn.

Router cần một task-level latency target:

```text
interactive
normal
batch
background-review
```

Ví dụ:

- interactive deep -> Sol high.
- batch architecture review -> Terra.
- background breadth -> Flash.

---

## 42. Cache-aware routing

Cache ratio ảnh hưởng economics rất mạnh.

Router telemetry nên phân biệt:

- cold provider call,
- same-thread continuation,
- packet reuse,
- model/provider cache.

Không so hai route nếu một route warm cache và route kia cold mà không ghi rõ điều kiện.

---

## 43. Context strategy

Không chia sẻ raw transcript giữa frontends.

Chia sẻ:

- task state,
- run/wave,
- accepted decisions,
- proof refs,
- compact handoff capsule,
- localized evidence packet.

Điều này vừa giảm token vừa tránh coupling ChatWeb/Codex/OpenCode conversation state.

---

## 44. Handoff và multi-provider là hai khái niệm khác nhau

### Handoff

Đổi semantic frontend/controller:

```text
ChatWeb -> Codex Desktop
```

### Provider routing

Đổi compute resource cho một work unit:

```text
Terra -> DeepSeek Pro reviewer
```

Không nên dùng cùng một API/state machine cho hai việc này nếu semantics khác nhau.

---

## 45. Controller lease tương lai

Nếu sau này OpenCode cần controller mode, phải thêm explicit contract:

- controller eligibility,
- fencing,
- handoff capsule compatibility,
- cursor/reconnect,
- final acceptance semantics.

Không promote chỉ bằng cách đổi role string từ worker thành controller.

---

## 46. Security boundary

Secrets:

- real MCP bearer chỉ Electron/gateway giữ.
- frontend thin proxies không nhận real bearer.
- OpenCode provider credentials ở OpenCode credential store.
- config repo không chứa secret.

Proxy identity:

- explicit allowlist,
- fail-closed invalid pair,
- no ChatWeb impersonation through local stdio.

---

## 47. Runtime boundary

Một workspace nên có:

```text
ONE Electron-owned Coding Tools Runtime
```

Không chạy:

```text
ChatWeb MCP runtime
+
Codex Desktop full MCP runtime
+
OpenCode full MCP runtime
```

cùng ghi chung ledger.

Thin proxies/frontends được phép nhiều; runtime authority chỉ một.

---

## 48. Proof boundary

Worker/model output không phải proof.

Proof phải đến từ:

- deterministic tests,
- build checks,
- focused oracles,
- ledger evidence,
- accepted diff state.

Một model nói “looks good” không đổi orchestration state thành accepted.

---

## 49. Final acceptance boundary

Trong topology hiện tại:

```text
ChatWeb Sol = final semantic acceptance
```

Nếu controller đã handoff hợp lệ sang Codex Desktop thì acceptance policy có thể theo existing controller contract.

OpenCode không tự accept production mutation ở phase này.

---

## 50. UI implementation wave — evidence

Accepted run:

```text
run  153e80bfb2b4449eb502cd340ade89c5
wave b56b0b4437fd41df93113ddbd3275357
```

Proof:

```text
b26318ec4f5d4de08f7f353bd738da7e
```

Proof fingerprint:

```text
22b83caef53066b1ce44b7b6957398c5ca45fefceb2553b529e866bd197c34b6
```

Final state:

```text
CHECKPOINTED
```

Focused verification command:

```text
node --test tests/control-panel.test.js tests/hub-proxy-gateway.test.js &&
cd resources/coding-tools-mcp &&
python -m pytest tests/test_hub_proxy_stdio.py tests/test_execution_hub.py
```

Result:

```text
exit 0
Python: 13 passed in 9.78s
combined duration ~11.6s
```

---

## 51. Terra candidate behavior trong cùng implementation task

Trước deterministic implementation, Terra xhigh cross-file candidate được thử trên scope này.

Observed:

```text
deadline: 25s
terminal change-set: none
estimated credits: 0.40765
cache ratio: 85.9%
```

Router không tự cascade lên Sol.

Sau khi scope được localize, deterministic MCP patch/proof hoàn thành.

Đây là một evidence thực tế ủng hộ policy:

> Fail một deep model không có nghĩa model kế tiếp trong bảng xếp hạng phải được gọi.

---

## 52. Phases tiếp theo nên làm theo thứ tự

### P-MP1 — OpenCode exact run/model telemetry

Mục tiêu:

- Hub biết Flash hay Pro thực sự chạy.
- UI node có exact label/cost/status.

### P-MP2 — OpenCode read-only Provider Adapter

Mục tiêu:

- Hub có thể dispatch bounded read-only work.
- direct write disabled.
- usage/cost registered.

### P-MP3 — Shadow provider router

Mục tiêu:

- recommendation only,
- compare với human route,
- chưa auto mutation.

### P-MP4 — Cohort collection

Mục tiêu:

- Flash/Pro/Terra homogeneous accepted cohorts.
- total cost/accepted + TTA + repair.

### P-MP5 — Bounded automatic routing

Mục tiêu:

- Flash read-only,
- Mini localized,
- deterministic MCP.

### P-MP6 — Deep route promotion

Mục tiêu:

- Terra/Sol-high/Pro theo evidence thresholds.
- Sol xhigh vẫn gated.

---

## 53. Những thứ chưa nên làm

- Không thêm tool thứ 9 chỉ để “OpenCode route”.
- Không cho OpenCode controller ngay.
- Không bật auto-handoff chỉ vì UI đã có OpenCode.
- Không dùng two-full-runtime topology.
- Không chạy all-model fanout mặc định.
- Không promote routing threshold từ vài benchmark samples.
- Không để OpenCode native write bypass MCP fence.
- Không animate model node khi chỉ biết frontend connected.

---

## 54. Product direction

Execution Hub nên tiến thành:

> **Multi-provider local execution operating layer**

với ba frontend chính:

```text
ChatWeb
Codex Desktop
OpenCode
```

và nhiều compute plane bên dưới.

Electron Control Center trở thành nơi user quan sát:

- active frontend,
- controller,
- provider/model route,
- writer/proof,
- cost,
- task progress,
- handoff,
- runtime health.

Đây là hướng mạnh hơn việc xây một “AI IDE khác” hay “model switcher”.

---

## 55. Quyết định đề xuất

### Giữ nguyên ngay bây giờ

- ChatWeb controller/final acceptance.
- MCP writer/proof.
- Codex Desktop + OpenCode là frontend/worker.
- Terra/Sol là Codex compute lanes.
- DeepSeek là OpenCode Go compute family.
- 9-node Router Fabric là live topology view.

### Tiếp theo nên đầu tư

1. exact OpenCode run/model telemetry;
2. read-only OpenCode Provider Adapter;
3. cost/accepted-task telemetry chuẩn hóa;
4. shadow router;
5. evidence-gated auto routing.

### Chưa nên làm

- fixed fallback ladder;
- direct OpenCode writes ngoài MCP;
- automatic Pro/Terra/Sol escalation;
- controller promotion cho OpenCode.

---

## 56. Final architecture principle

Hệ thống nên tối ưu theo nguyên tắc:

```text
Right work
-> right provider
-> right model
-> minimum necessary authority
-> one writer
-> deterministic proof
-> one accepted execution truth
```

Không tối ưu theo:

```text
strongest model everywhere
```

và cũng không tối ưu theo:

```text
cheapest model everywhere
```

Mục tiêu cuối là:

```text
highest accepted-task efficiency
subject to correctness, latency, security and authority constraints
```

Đó là bài toán phối hợp toàn diện phù hợp nhất với hướng phát triển hiện tại của Tools-Codex-web.
