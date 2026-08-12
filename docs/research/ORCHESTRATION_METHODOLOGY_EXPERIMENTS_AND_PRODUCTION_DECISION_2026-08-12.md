# Phương pháp luận, thử nghiệm và quyết định production cho phối hợp ChatWeb – Coding Tools MCP – Codex

**Ngày chốt tài liệu:** 2026-08-12  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Branch:** `main`  
**Loại tài liệu:** Final engineering decision record / methodology / experiment log  
**Phạm vi:** ChatWeb GPT-5.6 Sol, Coding Tools MCP, Codex App Server/Desktop, GPT-5.4-Mini, GPT-5.6 Luna, Terra, Sol xhigh/max/ultra, Skill `sol-lean-codex`, review plane, execution plane, cost/latency/quality policy  
**Trạng thái:** Kiến trúc adaptive routing đã được triển khai vào Coding Tools MCP; tài liệu này tổng hợp đầy đủ quá trình đi tới quyết định đó.

---

## 0. Mục đích của tài liệu này

Hai báo cáo trước đã trả lời các câu hỏi riêng lẻ:

1. `EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md` đo Phase 1: ChatWeb Sol -> MCP so với Luna-low và Terra-medium autonomous executor.
2. `MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md` tách model capability khỏi effort và agent topology, bổ sung Mini/Luna patch-only, Sol xhigh/max/ultra, Terra-high và nghiên cứu khoa học bên ngoài.

Tài liệu hiện tại làm việc khác: **xây lại toàn bộ chuỗi lập luận từ câu hỏi ban đầu tới production architecture cuối cùng**, bao gồm cả các thí nghiệm thất bại, false starts, instrumentation bugs, capacity failures, packet-localization failures, cost traps, triển khai router, regression fixes và live acceptance.

Mục tiêu là để một kỹ sư khác có thể đọc duy nhất file này và hiểu:

- vấn đề ban đầu là gì;
- vì sao không thể chỉ chọn “model mạnh nhất”;
- vì sao benchmark đầu tiên chưa đủ;
- vì sao một số thí nghiệm bị loại;
- số liệu nào thực sự thay đổi quyết định;
- vai trò cuối cùng của từng model/tier;
- Skill, ChatWeb, MCP và Codex Desktop phải phối hợp thế nào;
- khi nào được dùng Mini/Luna/Terra/Sol xhigh/max/ultra;
- khi nào phải ở single-lane;
- tại sao không dùng serial cascade;
- cách tối ưu **quality -> time-to-accepted-result -> total expected cost**;
- những gate nào phải giữ trước khi thay đổi policy trong tương lai.

---

# 1. Kết luận điều hành

## 1.1 Kiến trúc được chọn

```text
USER
  |
  v
CHATWEB GPT-5.6 SOL
control plane / user intent / semantics / architecture / final acceptance
  |
  v
CODING TOOLS MCP
localize evidence once / deterministic tools / writer / proof / telemetry
  |
  +----------------------+----------------------+-----------------------+
  |                      |                      |                       |
  v                      v                      v                       v
DETERMINISTIC       CHEAP CANDIDATE       HARDER LEAF            DEEP CODE
MCP only            Mini low/no-tools      Luna high/no-tools      Codex Sol xhigh
  |                      |                      |                       |
  +----------------------+----------------------+-----------------------+
                         |
                         v
               MCP scope validation
               deterministic apply
               focused/full proof
                         |
                         v
                 CHATWEB SOL ACCEPT

EXPLICIT/GATED ONLY:
  Terra high      -> cross-file experiment
  Sol max         -> consequential escalation
  Sol ultra       -> true parallel-extreme escalation
```

Đây là kiến trúc **asymmetric orchestration**. Các thành phần không làm cùng một việc:

- ChatWeb Sol giữ semantic/control plane.
- MCP giữ evidence/execution/proof plane.
- Mini/Luna là candidate generators giá thấp khi packet đã đủ tốt.
- Codex Sol xhigh là deep-code lane thường trực cao nhất.
- Terra không còn là default autonomous worker; nó là cross-file experiment có gate.
- Max và Ultra không được auto-select.
- Final acceptance không giao cho child model.

## 1.2 Quy tắc production hiện tại

```text
if deterministic / no fresh judgment:
    Coding Tools MCP

elif localized bug/test
     and strong failing oracle
     and <= 2 selected paths
     and <= 24 KB decision context:
    Mini low / candidate-only

elif bounded leaf
     and <= 4 selected paths
     and <= 60 KB decision context:
    Luna high / candidate-only

else:
    Codex Sol xhigh / deep-code candidate lane

Terra high:
    explicit experiment only

Sol max:
    explicit + high-cost acknowledgement only

Sol ultra:
    explicit + high-cost acknowledgement
    + true parallelizable workstreams only

always:
    MCP validates/apply/proves
    ChatWeb Sol owns final acceptance
```

## 1.3 Những gì bị bác bỏ

Không dùng các topology sau làm mặc định:

```text
Luna autonomous -> Terra autonomous -> Sol
```

```text
Mini -> fail -> Luna -> fail -> Terra -> fail -> Sol -> max -> ultra
```

```text
Sol xhigh autonomous shell loop cho mọi leaf nhỏ
```

```text
Ultra chỉ vì task "khó"
```

```text
nhiều model cùng write authoritative checkout
```

Lý do không phải là lower-tier models “kém” tuyệt đối. Lý do là **expected accepted-result economics và topology**.

---

# 2. Vấn đề ban đầu

Hệ thống có bốn lớp có thể cùng tham gia xử lý coding task:

1. **ChatWeb GPT-5.6 Sol**: có hội thoại, user intent, web research, reasoning cấp cao và MCP.
2. **Coding Tools MCP**: repository tools, deterministic commands, tests, patch apply, task state.
3. **Codex App Server / Codex Desktop**: coding-agent runtime có model/effort rõ ràng và persistent session.
4. **Skill `sol-lean-codex`**: policy tầng cao quyết định khi nào giữ việc ở Sol, khi nào delegate, cách review, proof và recovery.

Câu hỏi ban đầu không đơn giản là “model nào tốt nhất”, mà là:

> Làm thế nào phân phối công việc giữa các lớp này để giữ chất lượng, giảm time-to-green/time-to-accepted, tránh tool duplication, tận dụng model rẻ khi phù hợp và không trả chi phí multi-agent/cascade vô ích?

Một phương án ngây thơ là luôn dùng model mạnh nhất. Một phương án ngược lại là luôn thử model rẻ rồi escalate. Cả hai đều có vấn đề:

- model mạnh có thể lãng phí chi phí trên leaf đã localize tốt;
- model rẻ autonomous có thể tốn nhiều tool-loop, fail/capacity, rồi cuối cùng vẫn phải trả Sol;
- cascade nhiều tier làm critical path dài;
- multi-agent có thể làm task sequential chậm hơn;
- review nếu lặp lại cùng reasoning không tạo independent evidence;
- model được quyền shell/write rộng dễ tạo blast radius lớn hơn lợi ích.

Do đó mục tiêu được định nghĩa lại thành:

```text
1. CORRECTNESS / SAFETY / COMPATIBILITY / TRUTHFUL PROOF
2. TIME TO ACCEPTED RESULT
3. TOTAL EXPECTED COST INCLUDING FAILURES + REWORK + REVIEW
4. MAINTAINABILITY / EXTENSION QUALITY WHEN RELEVANT
5. SIMPLICITY WHEN MATERIAL RESULTS ARE TIED
```

---

# 3. Thuật ngữ và metric

## 3.1 ChatWeb Sol và Codex Sol không phải cùng route

**ChatWeb Sol** là GPT-5.6 Sol của phiên ChatGPT. Nó sở hữu conversation context, user intent và MCP state. Effort nội bộ không expose; không được gọi nó là xhigh/max/ultra.

**Codex Sol xhigh/max/ultra** là `gpt-5.6-sol` qua Codex/App Server với effort request được quan sát qua runtime metadata.

Cùng model family nhưng khác:

- prompt/context;
- tool topology;
- sandbox;
- thread lifetime;
- cache;
- orchestration overhead;
- acceptance authority.

Vì vậy nghiên cứu đo **system route**, không đo tên model đơn lẻ.

## 3.2 Strong oracle

Strong oracle là một check khách quan có thể từ chối kết quả sai với chi phí thấp, ví dụ:

- deterministic unit/integration test;
- compiler/type checker;
- schema validator;
- exact invariant;
- reproducible runtime check.

Model confidence, prose fluency hoặc self-review không phải strong oracle.

## 3.3 Integration width

Integration width là lượng state khác loại phải tổng hợp cùng lúc để phán đoán đúng:

- contracts;
- subsystems;
- callers;
- data flows;
- public compatibility;
- security/finance/privacy semantics.

File count chỉ là weak proxy. Một file có thể có high integration width; nhiều file mechanical có thể low integration width.

## 3.4 First-pass acceptance

Một route accepted first-pass khi outer attempt đầu tiên tạo kết quả qua focused gate và full affected-boundary gate mà không sửa tests để lách oracle.

## 3.5 Availability-adjusted acceptance

Dùng để tách model capability khỏi service capacity:

```text
accepted / attempts where model was actually available
```

Metric này không thay thế overall acceptance vì capacity vẫn là production cost thật.

## 3.6 TTA

TTA trong benchmark là observed **time to accepted result** dưới orchestration hiện tại:

```text
executor/model wall
+ independent focused grading
+ full package/boundary grading
```

Phase 1/2 không có timestamp hoàn hảo của “first instant when code became green”; đó là một telemetry gap được ghi riêng.

## 3.7 Accepted-at-deadline

Turn có thể bị interrupt do deadline nhưng candidate/patch trên disk đã đúng và external grading xanh. Đây là một insight quan trọng: **turn completion status không đồng nghĩa patch correctness**.

---

# 4. Nguyên tắc phương pháp luận

## 4.1 Đo production topology, không benchmark toy IQ

Không dùng toy arithmetic/code snippets làm evidence chính. Regression được inject vào source MCP thật và grading bằng tests hiện có.

## 4.2 Oracle phải được preflight trước model spend

Một benchmark model là vô nghĩa nếu regression không thực sự làm oracle đỏ. Vì vậy mọi mutation phải chứng minh red trước khi dispatch model.

## 4.3 Một thay đổi biến tại một thời điểm

Phase 1 chủ yếu thay executor model/topology. Phase 2 cố ý tách:

```text
MODEL CAPABILITY
!= REASONING EFFORT
!= AGENT TOPOLOGY
!= PACKET QUALITY
```

## 4.4 Không retry unchanged failure

Capacity/deadline/failure không được retry cùng packet cùng route chỉ để hy vọng may mắn. Retry phải thêm evidence, đổi topology, narrow scope hoặc chuyển policy class.

## 4.5 Không dùng mean đơn độc

Tail latency của ChatWeb tool roundtrips và capacity failures có thể làm mean sai lệch. Phân tích dùng:

- median;
- per-task paired comparison;
- accepted-only vs all-attempt;
- availability-adjusted acceptance;
- lower-bound accepted-result credits.

## 4.6 Không coi cheapest model call là cheapest solution

Expected cost phải gồm:

```text
GENERATION
+ EVIDENCE COLLECTION
+ VALIDATION
+ REVIEW
+ P(failure) * REPAIR/ESCALATION
+ LATENCY PENALTY
+ INTEGRATION COST
```

---

# 5. Chronology: từ câu hỏi ban đầu tới production router

## 5.1 Bước 1 — Giữ model-facing MCP surface cố định

Một constraint quan trọng xuất hiện sớm: không được làm ChatWeb client phải discover thêm hàng loạt model tools.

Kiến trúc bridge được đưa vào dưới `agent_workflow`, trong khi smart model-facing surface vẫn cố định 8 tools. `codex_bridge` tồn tại như hidden compatibility/internal service, không phải tool thứ 9 trong smart mode.

Lợi ích:

- không phụ thuộc client schema refresh để thêm mỗi model;
- giảm tool-selection entropy;
- routing là server policy, không phải user/model phải chọn giữa hàng chục tools;
- giữ Sol làm coordinator duy nhất.

## 5.2 Bước 2 — Tạo review router trước implementation router

Bridge đầu tiên được dùng để external review với các profile:

```text
PACKET   -> Mini low, no tools, ~8 s
SCOPED   -> Luna low, read-only
CRITICAL -> Terra medium, read-only
HISTORY  -> explicit persisted Desktop fork
```

Review plane có các guard:

- network off;
- approval never;
- child environment scrub credentials;
- no blind cascade;
- external review không thay đổi `execution.ok`;
- Sol vẫn final acceptance.

Kinh nghiệm này tạo nền cho implementation routing: **model nên trả evidence/candidate, MCP giữ mutation authority**.

## 5.3 Bước 3 — Câu hỏi về autonomous implementation

Sau review integration, câu hỏi chuyển thành:

> Có nên để Luna/Terra tự inspect repo, shell, edit và test thay cho ChatWeb Sol -> MCP không?

Đó là Phase 1.

---

# 6. Phase 1 — Executor Routing Benchmark

## 6.1 Thiết kế

30 official observations:

```text
10 real mutation tasks
x 3 system routes
= 30 observations
```

Routes:

1. ChatWeb Sol -> MCP patch.
2. Codex Luna autonomous (`gpt-5.6-luna`, effort low).
3. Codex Terra autonomous (`gpt-5.6-terra`, effort medium).

Mỗi task:

1. copy pristine `resources/coding-tools-mcp` snapshot;
2. inject đúng một regression;
3. `git init` fixture;
4. xác nhận focused oracle đỏ;
5. dispatch route;
6. không cho sửa test oracle;
7. chạy focused grading;
8. chạy full Python package gate;
9. accepted chỉ khi cả hai xanh.

Pristine gate: **38/38 Python tests pass**.  
Preflight mutations: **10/10 focused oracles red**.

## 6.2 10 task/invariant

| ID | Class | Regression | Width |
|---|---|---|---|
| T01 | security_env_isolation | child env không strip `WEBCODEX_*` | Low |
| T02 | routing_effort_control | packet effort `low -> ultra` | Low |
| T03 | tool_surface_isolation | packet reviewer được bật shell | Low |
| T04 | app_server_protocol | invalid `deferGoalContinuation` trong ephemeral fork | Medium |
| T05 | cost_accounting | cached tokens bị tính như uncached | Low |
| T06 | capacity_resilience | capacity failure không mở cooldown | Medium |
| T07 | session_ownership | continuation bỏ owned-thread guard | Medium |
| T08 | api_validation | public `INVALID_ACTION` code bị đổi sai | Low |
| T09 | client_tool_compatibility | smart surface 8 -> 9 tools | Medium |
| T10 | dirty_worktree_isolation | diff scope quay lại whole worktree | Medium |

## 6.3 Aggregate result

| Metric | ChatWeb Sol -> MCP | Luna autonomous | Terra autonomous |
|---|---:|---:|---:|
| Accepted | **10/10 (100%)** | **2/10 (20%)** | **6/10 (60%)** |
| Accepted when available | 100% | 2/6 = 33.3% | 6/8 = 75% |
| Capacity failures | 0 | 4 | 2 |
| Deadline failures | 0 | 4 | 2 |
| Accepted despite interrupt | 0 | 1 | 5 |
| Integration defects focused-green/full-red | **0** | **0** | **0** |
| Tests modified | 0 | 0 | 0 |
| Median executor wall | 39.2 s | 43.4 s | 45.8 s |
| Median observed TTA | **42.5 s** | 47.3 s | 48.9 s |
| Median model/tool events | **2** | 3 | 4 |

## 6.4 Per-task result

| Task | Sol | Luna | Terra |
|---|---:|---:|---:|
| T01 | PASS 30.2s | CAP 33.9s / 0.183cr | CAP 8.6s |
| T02 | PASS 146.7s | DL 54.4s / 0.144cr | DL 50.3s / 0.371cr |
| T03 | PASS 30.0s | CAP 10.3s | PASS 49.7s / 0.200cr |
| T04 | PASS 45.8s | PASS 44.3s / 0.065cr | PASS 49.1s / 0.199cr |
| T05 | PASS 40.7s | CAP 15.9s / 0.257cr | PASS 48.6s / 0.264cr |
| T06 | PASS 100.3s | PASS 51.9s / 0.091cr | PASS 43.6s / 0.208cr |
| T07 | PASS 38.3s | DL 51.8s / 0.103cr | DL 48.6s / 0.433cr |
| T08 | PASS 44.3s | DL 50.3s / 0.285cr | CAP 21.5s / 0.206cr |
| T09 | PASS 58.4s | CAP 9.0s | PASS 50.0s / 0.317cr |
| T10 | PASS 37.3s | DL 52.6s / 0.077cr | PASS 49.2s / 0.199cr |

T02/T06 là Sol latency outliers do orchestration/tool plumbing, không phải pure semantic difficulty. Chúng được giữ vì benchmark đo system route thật.

## 6.5 Accepted-result credit economics

Observed credits của Luna/Terra không nên chỉ tính accepted calls.

- Luna observed total credits: ~1.20487 trên các attempts có telemetry; 2 accepted.
- Lower-bound observed policy credits per accepted outcome: **~0.6024** và còn missing-credit rows.
- Terra observed total credits: ~2.396638; 6 accepted.
- Lower-bound observed policy credits per accepted outcome: **~0.3994** và còn một missing-credit row.

Nghịch lý quan trọng:

> Luna có unit rate rẻ hơn Terra nhưng failure/capacity làm observed policy cost per accepted outcome tệ hơn Terra.

## 6.6 Serial cascade economics

Sol-only:

- total observed TTA: 572.016 s / 10 tasks;
- mean: 57.20 s;
- median: 42.52 s.

Naive Luna-first then Sol fallback:

- mean ~80.02 s;
- penalty ~+22.82 s/task, khoảng +39.9%.

Naive Terra-first then Sol fallback:

- mean ~67.86 s;
- penalty ~+10.66 s/task, khoảng +18.6%.

Kết luận Phase 1:

```text
REJECT serial lower-tier cascade
REJECT Luna-low autonomous default
REJECT Terra-medium autonomous global default
KEEP ChatWeb Sol -> MCP for localized strong-oracle work
```

## 6.7 Insight deadline

5/6 accepted Terra runs được external grading xanh dù turn bị deadline interrupt. Do đó future executor không được coi:

```text
turn interrupted == patch failed
```

Policy tốt hơn:

```text
interrupt
-> freeze candidate/diff
-> external oracle
-> accept or revert
```

---

# 7. Gap sau Phase 1: vì sao chưa được chốt model strategy

Phase 1 chưa đo:

- Sol xhigh;
- Sol max;
- Sol ultra;
- Luna high;
- Terra high/xhigh;
- Mini;
- patch-only/no-tools topology.

Quan trọng hơn, Phase 1 đã trộn hai yếu tố:

```text
MODEL QUALITY
+
AUTONOMOUS AGENT LOOP QUALITY
```

Luna/Terra vừa phải reason, vừa phải localize, shell, inspect, edit, test và kết thúc turn. Nếu thất bại, không biết phần nào gây ra.

Câu hỏi mới được đặt ra:

> Nếu ChatWeb/MCP làm localization và oracle, model chỉ trả bounded patch candidate thì lower-tier có còn kém không?

Đồng thời user đặt câu hỏi cụ thể về **Sol Ultra** và phương án chỉ dùng **Sol xhigh**. Đây là trigger của Phase 2.

---

# 8. Nghiên cứu khoa học và field evidence dùng để thiết kế Phase 2

Phase 2 không chỉ chạy local benchmark. Nó đối chiếu các kết quả bên ngoài để tránh overfit vào 10 mutation tasks.

## 8.1 OpenAI GPT-5.6 / Sol Ultra

Phase 2 ghi nhận từ OpenAI rằng Sol/Terra/Luna là các capability tiers khác nhau và `ultra` là highest-capability setting có multi-agent/parallel-workstream semantics, không chỉ “xhigh nhiều token hơn”.

Sources được lưu trong Phase 2:

- https://openai.com/index/gpt-5-6/
- https://openai.com/index/previewing-gpt-5-6-sol/

Implication:

- xhigh là candidate deep single-lane default;
- max là deeper consequential reasoning;
- ultra là topology escalation và cần task parallelizable.

## 8.2 Google Research: khi multi-agent giúp/hại

Phase 2 dẫn nghiên cứu Google trên 180 agent configurations:

- parallelizable task có thể hưởng lợi mạnh;
- sequential planning có thể giảm đáng kể;
- error amplification phụ thuộc architecture;
- centralized orchestration tốt hơn independent swarm trong nhiều setting.

Source:

- https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

Implication:

```text
parallelism is a task property, not a model-tier reward
```

## 8.3 MTRouter: ít model switches hơn

MTRouter cho thấy cost-aware multi-turn routing có thể giảm chi phí và các router hiệu quả có xu hướng giảm model switches.

Source:

- https://aclanthology.org/2026.acl-long.2045/

Điều này khớp local Phase 1: serial Luna/Terra fallback làm critical path tệ hơn Sol-only.

## 8.4 ContextualRouter và LLMRouterBench

Các nghiên cứu này hỗ trợ việc bắt đầu bằng simple routing/nearest-similar historical performance trước khi xây ML router phức tạp.

Sources:

- https://aclanthology.org/2026.eacl-srw.22/
- https://aclanthology.org/2026.findings-acl.1881/

## 8.5 ToolScope

ToolScope cho thấy toolset lớn/redundant có thể giảm tool selection; context-aware filtering cải thiện đáng kể trong benchmark của paper.

Source:

- https://aclanthology.org/2026.acl-long.1573/

Implication local: giữ **compact 8-tool smart surface**, không expose mỗi model thành một tool.

## 8.6 Independent patch verification

RETRACE nhấn mạnh giá trị của independent verification hơn là cùng một agent tự review reasoning của chính nó.

Source:

- https://arxiv.org/abs/2608.08950

Implication:

- external reviewer nhận evidence/diff/proof;
- không nhận narrative rationale của executor nếu mục tiêu là independent check;
- deterministic oracle có authority cao hơn model debate.

## 8.7 SWE-bench correctness caveat

Research về false plausibility của benchmark “solved” nhắc rằng focused test xanh không đủ cho high-risk semantics.

Source:

- https://arxiv.org/abs/2503.15223

Do đó auth/privacy/finance/destructive migration/public contract vẫn cần Sol kiểm tra invariant và adjacent risk.

## 8.8 Diversity và conformal routing

Phase 2 cũng ghi nhận:

- heterogeneous evidence channels có thể giá trị hơn nhiều homogeneous agents;
- cheap-route promotion cần conservative safety bound, không dựa vào 3–4 successes.

Sources:

- https://arxiv.org/abs/2602.03794
- https://aclanthology.org/2026.acl-srw.70/

## 8.9 Codex field reports

Open issues về auto model/effort routing trong `openai/codex` cho thấy fixed global effort là operational pain point. Issue #35177 được dùng **chỉ như field warning**, không như controlled evidence, về khả năng Ultra fan-out và tiêu credits cao.

- https://github.com/openai/codex/issues/35177

---

# 9. Phase 2 — Tách model khỏi topology

## 9.1 Research questions

1. Sol xhigh autonomous có nên thay ChatWeb/MCP làm default executor?
2. Khi bỏ tool/localization loop, Mini/Luna/Sol xhigh khác nhau thế nào?
3. xhigh/max/ultra có quality gain trên cùng packet không?
4. Terra high có đủ ổn định để auto-promote không?
5. Phương án “Sol xhigh-only” có đáng đơn giản hóa hệ thống không?

## 9.2 Suite

6 regression invariants:

| ID | Class | Broken invariant |
|---|---|---|
| T02 | routing_effort_control | packet `low -> ultra` |
| T04 | app_server_protocol | invalid ephemeral-fork field |
| T06 | capacity_resilience | circuit-breaker guard disabled |
| T07 | session_ownership | owned-thread guard removed |
| T09 | client_tool_compatibility | 8 -> 9 smart tools |
| T10 | dirty_worktree_isolation | broad diff scope |

## 9.3 False-green preflight incident

Một preflight ban đầu dùng embedded native Python đã import production source thay vì isolated fixture, làm **6 mutations trông như green**.

Đây là một methodology failure, không phải model success.

Quy trình đã xử lý đúng:

1. dừng benchmark trước khi tiêu model credits;
2. trace import path/test discovery;
3. chuyển sang system Python 3.11.7 + fixture `PYTHONPATH` đúng;
4. xác nhận **6/6 mutations red**;
5. chỉ sau đó mới benchmark model.

Lesson:

> Oracle environment identity phải là một phần của benchmark provenance. “Test pass” không có giá trị nếu test đang chạy nhầm source.

## 9.4 Hai topology

### Autonomous executor

```text
objective + oracle
-> model inspect repo
-> shell/tool loop
-> edit isolated worktree
-> model runs checks
-> external grade
```

### Patch-only/no-tools

```text
MCP/ChatWeb localize
-> bounded evidence packet
-> model returns structured exact edit
-> MCP validates path/scope
-> MCP applies
-> external deterministic grade
```

Đây là experiment quan trọng nhất của Phase 2.

---

# 10. Phase 2 results

## 10.1 Sol xhigh autonomous

Official pre-stop observations:

| Task | Result | Model wall | TTA | Credits | Production write |
|---|---|---:|---:|---:|---|
| T02 | interrupted/fail | 31.154s | 37.034s | 0.3765 | none |
| T04 | interrupted/fail | 31.145s | 36.926s | 0.2674 | none |
| T06 | interrupted/fail | 31.147s | 37.673s | 0.3544 | none |

**0/3 accepted.** Batch được stop vì cùng failure pattern, tránh blind spend.

Kết luận đúng không phải “Sol xhigh yếu”. Kết luận là:

> Autonomous localization/shell loop dưới bridge hiện tại không có expected value cho narrow strong-oracle repairs.

## 10.2 Instrumentation bug: ~30s observe clamp

Phase 2 runner request 45s nhưng bridge `observe()` bound từng wait khoảng 30s, nên autonomous turns bị interrupt ~31–32s.

Do đó:

- không so trực tiếp Phase 2 autonomous latency với Phase 1 45s như deadline giống nhau;
- cần telemetry `time_to_first_write`, `time_to_first_green`, `time_to_last_useful_evidence` trước khi promote cross-file executor.

Đây là evidence về system instrumentation, không phải model intelligence.

## 10.3 Sol xhigh patch-only/no-tools

| Task | Accepted | Model wall | TTA | Credits |
|---|---:|---:|---:|---:|
| T02 | yes | 6.681s | 10.563s | 1.288875 |
| T04 | yes | 7.545s | 11.477s | 1.323875 |
| T06 | yes | 8.263s | 11.648s | 1.339000 |

**3/3 accepted.**

Cùng model Sol xhigh:

```text
AUTONOMOUS: 0/3
PATCH-ONLY: 3/3
```

Đây là evidence mạnh nhất cho luận điểm:

> Trên bounded work, packet quality và topology có thể ảnh hưởng nhiều hơn model tier.

## 10.4 Luna high patch-only

| Task | Accepted | Model wall | TTA | Credits |
|---|---:|---:|---:|---:|
| T02 | yes | 4.615s | 7.717s | 0.255100 |
| T04 | yes | 5.304s | 8.259s | 0.266150 |
| T06 | yes | 4.644s | 7.689s | 0.257775 |
| T10 | yes | 12.199s | 16.729s | 0.313850 |

**4/4 accepted.** Mean TTA ~10.10s; mean observed credits ~0.2732.

## 10.5 Mini low patch-only

| Task | Accepted | Model wall | TTA | Credits |
|---|---:|---:|---:|---:|
| T02 | yes | 3.888s | 6.934s | 0.140337 |
| T04 | yes | 7.089s | 10.176s | 0.159342 |
| T06 | yes | 6.819s | 10.210s | 0.175723 |
| T10 | yes | 9.211s | 13.478s | 0.076414* |

`*` T10 có cache reuse cao, không dùng con số này như cold-price prior.

**4/4 accepted.** Mean TTA ~10.20s; mean observed credits ~0.1380.

## 10.6 Common-task comparison

T02/T04/T06:

| Route | Accepted | Mean TTA | Mean credits |
|---|---:|---:|---:|
| Mini low patch-only | **3/3** | 9.107s | **0.158467** |
| Luna high patch-only | **3/3** | **7.888s** | 0.259675 |
| Sol xhigh patch-only | **3/3** | 11.229s | 1.317250 |

Trên samples này:

- Sol xhigh ~5.1x Luna credits;
- Sol xhigh ~8.3x Mini credits;
- không có quality gain vì external gates giống nhau;
- expensive capability không được dùng hết khi packet entropy đã bị remove.

## 10.7 Sol xhigh vs max vs ultra calibration

Cùng T06 packet-only:

| Effort | Accepted | Model wall | TTA | Credits | Output/reasoning tokens |
|---|---:|---:|---:|---:|---:|
| xhigh | yes | 8.263s | 11.648s | 1.339000 | 124 / 56 |
| max | yes | 5.540s | 9.304s | 1.351125 | 139 / 80 |
| ultra | yes | 6.640s | 9.799s | 1.383625 | 180 / 113 |

n=1/effort nên không được kết luận max inherently nhanh hơn xhigh.

Valid conclusion:

- quality giống nhau trên packet này;
- không có evidence để dùng Ultra cho leaf;
- constrained packet Ultra không phải native multi-agent Ultra benchmark.

## 10.8 Terra high autonomous

| Task | Result | Model wall | TTA | Credits |
|---|---|---:|---:|---:|
| T04 | interrupt/no write | 31.941s | 34.772s | 0.237175 |
| T06 | capacity | 11.103s | 14.921s | 0.663375 |
| T10 | capacity | 4.476s | 9.050s | unavailable |

**0/3 accepted trong Phase 2 topology.**

Combined with Phase 1:

- Terra có capability signal tốt hơn Luna autonomous;
- nhưng current runtime availability + tool-loop topology chưa đủ để auto-promote;
- Terra giữ explicit cross-file experiment.

## 10.9 T07 packet-localization failure

Một T07 patch-only run bị invalid vì packet builder chọn sai code neighborhood. Sol xhigh trả `BLOCKED` thay vì invent patch.

Đây là model behavior đúng và benchmark harness behavior sai.

Lesson:

```text
packet builder phải symbol-aware
không chỉ first textual match / broad snippet
```

Và worker cần được phép `BLOCKED / INSUFFICIENT_PACKET` mà không bị tính như semantic hallucination.

---

# 11. Kết luận cốt lõi từ hai phase

## 11.1 Topology > tier trên bounded work

Phase 1 nói autonomous Luna/Terra không tốt trên class đã test. Phase 2 sửa cách hiểu:

> Vấn đề lớn không chỉ là model tier; autonomous discovery/tool-loop tax là biến chính.

Khi localization/proof được tách ra:

- Mini low 4/4;
- Luna high 4/4;
- Sol xhigh 3/3 trên common valid leaf packets.

Do đó lower-tier không nên bị loại; **vai trò của chúng phải đổi**.

## 11.2 Packet quality là economic switch

Low packet quality:

```text
lower-tier call
-> wrong localization / more tool loops / failure
-> escalation
-> expensive accepted result
```

High packet quality:

```text
MCP localize + strong oracle
-> cheap bounded model
-> exact candidate
-> deterministic apply/proof
-> cheap accepted result
```

## 11.3 Sol xhigh là deep default, không phải universal default

Sol xhigh có giá trị khi:

- context broad/long;
- semantics khó;
- integration width cao;
- dedicated deep code lane giảm tải ChatWeb;
- cross-file coherent work cần single strong lane.

Nhưng dùng Sol xhigh cho leaf đã localize tốt lãng phí 5–8x credits trong common Phase 2 samples.

## 11.4 Ultra là topology decision

Ultra chỉ có lý khi:

- workstreams độc lập;
- write ownership disjoint/isolated;
- interface đã settle;
- merge/review capacity tồn tại;
- expected parallel gain lớn hơn coordination + review + cost.

Không dùng Ultra để sửa poor localization, sequential debugging hoặc “just to be safe”.

---

# 12. Ba chiến lược đã được cân nhắc

## 12.1 Strategy A — ChatWeb/MCP + Sol xhigh-only deep lane

```text
ChatWeb Sol + MCP cho routine
Codex Desktop Sol xhigh cho deep work
không auto Mini/Luna/Terra implementation
```

Ưu:

- đơn giản;
- ít classifier mistakes;
- quality ceiling cao;
- dễ vận hành Desktop.

Nhược:

- bounded candidate generation trả quá nhiều credits;
- bỏ phí Phase 2 evidence về Mini/Luna;
- throughput kém khi nhiều small leaves.

**Verdict:** safe/simple nhưng không cost-optimal.

## 12.2 Strategy B — Adaptive bounded router

```text
ChatWeb Sol control
-> MCP evidence/localization
   -> deterministic if possible
   -> Mini low candidate for tiny strong-oracle leaf
   -> Luna high candidate for harder bounded leaf
   -> Sol xhigh for broad/deep work
-> MCP apply/proof
-> ChatWeb Sol accept
```

Terra/Max/Ultra explicit-gated.

**Verdict:** được chọn.

## 12.3 Strategy C — Full autonomous ladder

```text
Mini/Luna -> Terra -> Sol -> max -> ultra
```

**Verdict:** reject.

Reasons:

- Phase 1 cascade penalties;
- repeated discovery;
- capacity/deadline tax;
- model-switching critical path;
- Ultra topology risk;
- weak expected accepted-result economics.

---

# 13. Production router implementation

Current source encodes:

```text
mini      = gpt-5.4-mini / low   / candidate_mini / 10s
luna      = gpt-5.6-luna / high  / candidate_luna / 15s
terra     = gpt-5.6-terra / high / cross_file     / 25s
sol_xhigh = gpt-5.6-sol / xhigh  / deep_code      / 30s
sol_max   = gpt-5.6-sol / max    / consequential  / 30s / high-cost
sol_ultra = gpt-5.6-sol / ultra  / parallel_extreme / 30s / high-cost
```

Auto classifier:

```text
workflow in diagnose/document/resume/build_release/greenfield
    -> deterministic

bugfix/test_failure
+ strong oracle
+ 1-2 selected paths
+ <= 24 KB context
    -> mini

1-4 selected paths
+ <= 60 KB context
    -> luna

otherwise
    -> sol_xhigh
```

Terra không được auto-select.  
Max/Ultra yêu cầu explicit `allow_high_cost=true`.

---

# 14. Vì sao Mini phải gate bằng strong oracle

Implementation đầu tiên của adaptive router có risk:

```text
small bug + tiny context -> Mini
```

nhưng “tiny” không đủ. Nếu không có strong verification thì một cheap wrong patch có thể trở thành latent defect.

Commit `b802b597` sửa policy thành:

```text
small + bug/test + strong_oracle -> Mini
small without strong oracle -> Luna or higher
```

Đây là production lesson:

> Routing xuống tier rẻ phải được mua bằng objective verification, không chỉ bằng file count.

---

# 15. Candidate patch contract và newline regression

Candidate models không trả arbitrary shell script. Output structured gồm:

- status `ready|blocked`;
- summary;
- exact replacements;
- bounded new files;
- proof hints;
- confidence.

MCP:

1. normalize candidate path;
2. enforce allowed paths;
3. require unique exact match;
4. convert candidate to patch;
5. apply itself;
6. verify itself.

Trong deployment xuất hiện một Windows newline mismatch: model packet có CRLF nhưng fixture/file có LF. Exact match fail dù semantic replacement đúng.

Commit `0fffe4be` thêm newline normalization trước unique-match validation.

Lesson:

> Candidate protocol phải deterministic nhưng không được brittle với representation differences không mang semantic meaning.

Guard vẫn giữ `count == 1`; normalization không làm broad fuzzy replacement.

---

# 16. Execution plane và Review plane phải tách nhau

## 16.1 Execution plane

```text
DETERMINISTIC MCP
MINI CANDIDATE
LUNA CANDIDATE
SOL XHIGH DEEP
TERRA EXPERIMENT
SOL MAX CONSEQUENTIONAL
SOL ULTRA PARALLEL EXTREME
```

## 16.2 Review plane

```text
NONE
PACKET  -> Mini low
SCOPED  -> Luna
CRITICAL -> Terra
SOL_LOCAL -> existing ChatWeb Sol
HISTORY -> explicit only
```

Không có quan hệ bắt buộc:

```text
executor tier == reviewer tier
```

Examples:

- Mini candidate + deterministic tests -> review NONE.
- Sol xhigh deep implementation + finance invariant -> Terra independent CRITICAL review có thể hữu ích.
- ChatWeb Sol architecture + strong deterministic proof -> không cần external review.

Review phải có independent information value, không phải ceremony.

---

# 17. Vai trò cuối cùng của từng thành phần

## 17.1 ChatWeb GPT-5.6 Sol — CONTROL

Sở hữu:

- user intent;
- requirement changes;
- architecture;
- public/current research;
- risk classification;
- shared semantics;
- interface ownership;
- conflict resolution;
- cross-workstream synthesis;
- final acceptance.

Không nên:

- duplicate toàn bộ repository scanning nếu MCP đã localize;
- mở nhiều child agents chỉ để “có thêm confidence”;
- tự gọi history fork lớn cho một fact nhỏ.

Preferred loop:

```text
finish line
-> cheapest discriminating evidence
-> settle semantics
-> dispatch only if positive expected value
-> deterministic proof
-> accept
```

## 17.2 Coding Tools MCP — DETERMINISTIC AUTHORITY

Sở hữu:

- context collection;
- grep/search/read;
- exact deterministic commands;
- test/build;
- candidate packet assembly;
- path/scope validation;
- authoritative workspace writes;
- diff/proof;
- task state;
- route telemetry;
- hidden bridge.

MCP không nên expose hàng loạt model-specific tools.

## 17.3 Mini low — CHEAP PATCH CANDIDATE

Dùng khi:

- localized;
- strong failing oracle;
- tiny packet;
- reversible;
- low integration width.

Topology:

```text
TOOLS = none
NETWORK = none
WRITE = none
OUTPUT = structured candidate
```

Không sở hữu auth/privacy/finance/public contract semantics.

## 17.4 Luna high — HARDER LEAF

Dùng cho:

- bounded leaf khó hơn Mini;
- settled semantics;
- packet nhỏ/vừa;
- MCP vẫn writer/oracle.

Default vẫn no-tools candidate. Chỉ mở repository inspection nếu evidence tương lai chứng minh expected value.

## 17.5 Codex Sol xhigh — DEEP CODE

Đây là highest routine Codex lane.

Dùng cho:

- broad context;
- long coherent code work;
- high integration width;
- hard debugging;
- dedicated deep workstream;
- substantial feature/refactor khi dedicated coding session đáng giá.

Không phải universal leaf executor.

## 17.6 Terra high — CROSS-FILE EXPERIMENT

Terra có competency signal nhưng availability/autonomous evidence chưa đủ để auto-promote.

Use only when:

- explicit experiment;
- settled interfaces;
- isolated worktree/candidate scope;
- external proof;
- class-specific telemetry đang được thu.

## 17.7 Sol max — CONSEQUENTIAL ESCALATION

Use only when:

- xhigh còn under-proven;
- question consequential;
- added reasoning có thể đổi acceptance;
- budget justified.

## 17.8 Sol ultra — TRUE PARALLEL EXTREME

Use only when:

```text
TRUE_PARALLEL_WORKSTREAMS = yes
INTERFACES_SETTLED = yes
WRITE_OWNERSHIP_DISJOINT = yes
REVIEW_CAPACITY = enough
EXPLICIT_BUDGET = yes
EXPECTED_PARALLEL_GAIN > orchestration cost
```

Không auto-select.

---

# 18. Codex Desktop policy

Codex Desktop không nên được coi là “review window thứ hai”.

Best use:

- long coherent implementation lane;
- repeated follow-up trong cùng semantic workstream;
- persistent local environment/context;
- substantial feature/refactor;
- user cần direct visibility vào deep coding activity.

Nếu Desktop được dành cho deep work, default hợp lý:

```text
MODEL  = GPT-5.6 Sol
EFFORT = xhigh
```

Manual escalation:

```text
max   -> consequential hard reasoning
ultra -> explicit parallel-extreme only
```

## 18.1 History fork warning

History không phải free context. Calibration trước đó cho thấy full Desktop history fork có thể cực lớn (~233K input tokens, ~29 credits trong một trivial inherited-context case).

Prefer:

```text
Desktop
-> compact state capsule
-> ChatWeb/MCP
```

State capsule:

```text
GOAL
ACCEPT
BASE
INVARIANTS
SETTLED_DECISIONS
CHANGED_PATHS
LATEST_PROOF
OPEN_UNCERTAINTY
NEXT_ACTION
```

---

# 19. Skill `sol-lean-codex` policy

Skill phải phản ánh production router, không giữ taxonomy cũ “Luna leaf / Terra default / Sol high”.

Current policy:

```text
CONTROL                  ChatWeb Sol
DETERMINISTIC            Coding Tools MCP
CHEAP PATCH              Mini low/no-tools
HARDER LEAF              Luna high/no-tools
DEEP CODE                Codex Sol xhigh
CROSS-FILE EXPERIMENT    Terra high
CONSEQUENTIAL            Sol max
PARALLEL EXTREME         Sol ultra
FINAL ACCEPTANCE         ChatWeb Sol + deterministic evidence
```

Skill giữ nguyên các nguyên tắc:

- quality-first;
- no blind cascade;
- one fallback max khi evidence thay đổi route value;
- compact packet;
- tests as oracle, not ritual;
- no nested/unbounded orchestration;
- report only observed routes/evidence.

## 19.1 Skill deployment incident

Bản v4 được validate/package thành 13-file `skill.zip`.

Quá trình cài global Windows gặp hai safety issues đáng ghi lại:

1. safe-mode MCP ban đầu chặn write ra `C:\Users\Admin\.codex` bằng filesystem boundary; không lách sandbox.
2. khi user explicit yêu cầu cài, ZIP được transfer theo chunks; lần đầu hash mismatch vì chunk đầu bị giới hạn/truncate. Integrity gate phát hiện và **không cài bundle sai**.
3. retransmit binary-safe, SHA khớp source bundle.
4. extract staging;
5. comparator tests 10/10 trước swap;
6. backup v3;
7. atomic promote;
8. comparator tests 10/10 sau cài.

Installed path:

`C:\Users\Admin\.codex\skills\sol-lean-codex`

Backup:

`C:\Users\Admin\.codex\skills\sol-lean-codex.backup-20260812-202137`

Lesson:

> Skill deployment cũng cần artifact integrity + staging + rollback, giống code deployment.

## 19.2 ChatWeb refresh behavior

Ngay sau local install, current ChatWeb session vẫn đọc v3 do skill metadata/resource cache. Không được claim hot-update thành công.

Ở một conversation/session boundary sau đó, ChatWeb resource discovery đã trả policy v4 mới. Lesson:

> Skill update có thể cần session/resource rediscovery; runtime MCP server policy không nên phụ thuộc vào skill hot-refresh để đảm bảo safety.

---

# 20. Fixed 8-tool MCP surface

Một quyết định kiến trúc quan trọng là giữ smart model-facing surface compact.

`codex_bridge` không trở thành public smart tool thứ 9. Model-facing ChatWeb dùng `agent_workflow`; routing nội bộ dispatch hidden bridge.

Lợi ích:

- schema ổn định;
- ít tool-selection entropy;
- client cũ vẫn dùng auto server policy;
- model tiers có thể thay đổi mà không thêm tool names;
- hidden compatibility/service layer vẫn testable.

---

# 21. Client schema cache incident

Sau production reload, server đã support `execution_route`, nhưng ChatWeb wrapper trong active conversation vẫn hiển thị schema cũ không có field mới.

Điều này **không ngăn auto router**, vì `auto` logic chạy server-side.

Live deterministic smoke trả:

```text
execution_route.selected = deterministic
reason = workflow_prefers_local_tools
```

Lesson:

> Server-side safe default phải hoạt động cả khi client schema lag. Manual new options có thể chờ rediscovery; production safety không được phụ thuộc client refresh ngay lập tức.

---

# 22. Live Mini auto-route acceptance

Sau native MCP reload, một isolated single-file smoke fixture được tạo:

```text
VALUE = 1
```

Objective:

```text
change VALUE from 1 to 2, nothing else
```

Focused oracle:

```text
find exact `VALUE = 2`
```

Preflight oracle đỏ. Auto router quan sát:

- bugfix;
- one selected path;
- tiny context;
- strong test command.

Route:

```text
selected = mini
profile  = candidate_mini
model    = gpt-5.4-mini
effort   = low
```

Observed:

- candidate status: ready;
- confidence: high;
- model wall: ~5.078s;
- estimated credits: ~0.143558;
- MCP applied one exact update;
- final focused verification: PASS;
- fixture removed afterward.

Đây là end-to-end proof của production topology:

```text
ChatWeb
-> agent_workflow
-> server auto classifier
-> hidden Codex Mini candidate
-> MCP candidate scope validation
-> MCP write
-> deterministic proof
-> ChatWeb result
```

---

# 23. Final acceptance trước deployment

Trên source router trước final reload:

- Python Coding Tools MCP tests: **44/44 PASS**;
- Node stability tests: **5/5 PASS**;
- `git diff --check`: PASS;
- smart tool surface regression: PASS;
- route gating tests: PASS;
- candidate newline normalization test: PASS;
- candidate scope violation checks: PASS.

Router implementation được đưa lên Git history qua các commits chính:

- `c20f1e22` — `feat: add adaptive Codex routing and orchestration research`;
- `0fffe4be` — `fix: normalize candidate patch newlines`;
- `b802b597` — `fix: gate mini routing on strong verification`;
- các merge/sync/chore commits sau đó đưa `main` về clean state.

---

# 24. Security và mutation boundaries

## 24.1 Authoritative checkout

MCP là writer chính. Candidate models không được arbitrary write authoritative checkout.

## 24.2 Candidate scope

Candidate output chỉ được chạm allowed paths; path normalization reject:

- absolute paths;
- drive paths;
- `..` traversal;
- ambiguous/invalid components.

Exact replacement phải unique.

## 24.3 Child runtime

Review/candidate lanes:

- approval `never`;
- network false;
- credentials scrubbed;
- unrelated Desktop MCP servers disabled;
- no delegation except explicit Ultra parallel-extreme profile.

## 24.4 Writable external executor

Nếu future Terra/Sol worktree executor được bật:

- isolated worktree;
- pinned base;
- exact ownership;
- one attempt;
- deadline;
- freeze diff;
- external proof;
- no merge/rebase/reset/clean authority;
- Sol accepts/rejects.

---

# 25. Parallelism policy

## 25.1 Stay single-lane when

- sequential causality;
- each tool result changes next decision;
- one mutable surface;
- interfaces unsettled;
- overlapping writes;
- weak oracle;
- review/integration bottleneck.

Preferred:

```text
localize -> change -> validate
```

## 25.2 Parallelize when

- independent workstreams;
- disjoint ownership;
- isolated worktrees if writes;
- base/interfaces frozen;
- each leaf có objective proof;
- Sol integration bandwidth đủ.

Recommended starting concurrency:

```text
1 primary lane
+ at most 1 independent evidence/review lane
```

Fan-out thêm chỉ khi telemetry chứng minh positive expected value.

## 25.3 Nested swarm guard

Không chạy outer Mini/Luna/Terra/Sol workers đồng thời với native Ultra swarm trên cùng mutable surface. Nếu Ultra được chọn, nó là explicit topology owner của parallel subwork trong scope đó.

---

# 26. Capacity policy

Capacity errors là production input, không chỉ benchmark nuisance.

Observed:

- Phase 1 Luna capacity failures 4/10;
- Phase 1 Terra 2/10;
- Phase 2 Terra-high 2/3 autonomous attempts capacity.

Policy:

```text
capacity error
-> record cooldown
-> no unchanged retry
-> if exactly one alternative route has positive expected value, use it
-> otherwise return to ChatWeb Sol
```

Không silently downgrade high-risk task xuống model dưới quality floor.

---

# 27. Cache/session economics

Warm continuation có thể làm tier cao hơn rẻ hơn cold lower-tier trong một số context.

Prior calibration:

- Mini packet cold ~5.2s, ~0.131 credits;
- same packet continuation ~1.9s, ~95% cache ratio, ~0.026 credits;
- Luna scoped cold ~4.8s, ~0.261 credits.

Do đó router nên record:

```text
CACHE_STATE
UNCACHED_INPUT
CACHED_INPUT
OUTPUT
WALL
```

Reuse thread khi:

- same task;
- same invariant;
- same base;
- direct correction/follow-up.

New thread khi:

- blind independent review;
- changed interface/base;
- stale context;
- unrelated task.

Không giữ stale context chỉ vì cache rẻ.

---

# 28. Cost model và rate-card provenance

Benchmark bridge dùng snapshot `codex_rate_card_observed_2026-08-12`.

Historical benchmark basis per 1M input/cached/output credits:

| Model | Input | Cached | Output |
|---|---:|---:|---:|
| Sol | 125 | 12.5 | 750 |
| Terra | 62.5 | 6.25 | 375 |
| Luna | 25 | 2.5 | 150 |
| GPT-5.4-Mini | 18.75 | 1.875 | 113 |

Đây là **date-stamped benchmark basis**, không phải lời hứa về future pricing.

Decision metric:

```text
EXPECTED_ACCEPTED_COST =
  generation
+ localization/evidence
+ verification
+ review
+ failure_probability * rework/escalation
+ latency penalty
+ integration burden
```

Phase 1: low first-call price không cứu được failure-heavy Luna autonomous.  
Phase 2: high packet quality làm Mini/Luna thực sự rẻ hơn Sol trên bounded leaves.

---

# 29. Recommended operational playbook

## 29.1 Exact/mechanical task

Examples:

- rename known symbol mechanically;
- run formatter;
- exact config update đã biết;
- collect status/build/test evidence.

Route:

```text
MCP only
```

Không gọi child model.

## 29.2 Local bug + known causal patch

```text
ChatWeb Sol understands cause
-> MCP apply exact patch
-> focused test
-> affected boundary gate
-> accept
```

Không gọi Mini chỉ vì Mini rẻ nếu Sol đã biết exact change.

## 29.3 Local bug cần candidate

Requirements:

- strong failing oracle;
- localized 1–2 paths;
- low integration width;
- reversible.

Route:

```text
MCP packet
-> Mini low candidate
-> MCP apply/prove
-> Sol accept
```

Nếu Mini `BLOCKED` do packet thiếu evidence: **fix packet**, không blind retry.

Nếu blocked vì semantic uncertainty: reclassify to Luna/Sol.

## 29.4 Harder bounded leaf

```text
MCP localize
-> Luna high candidate
-> deterministic apply/proof
-> Sol accept
```

## 29.5 Broad/deep implementation

```text
ChatWeb Sol settles contract
-> Codex Sol xhigh deep lane
-> bounded candidate/diff or isolated worktree
-> MCP proof
-> Sol integration/accept
```

## 29.6 Cross-file experiment

```text
explicit Terra high
-> isolated/read-only candidate workflow
-> external proof
-> record route ledger
-> no auto promotion from one success
```

## 29.7 Auth/privacy/finance/data boundary

```text
ChatWeb Sol owns semantics
-> deterministic evidence
-> Sol xhigh/max only if deep work adds value
-> independent bounded review if distinct question exists
-> invariant + adjacent-risk proof
-> Sol final accept
```

Mini/Luna không sở hữu semantic decision.

## 29.8 True parallel project

```text
Sol centralized controller
-> freeze interfaces/base
-> disjoint leaves/worktrees
-> ordinary bounded parallel lanes first
-> Ultra only if ordinary parallelism insufficient and budget explicit
-> centralized merge/proof
```

---

# 30. One-fallback rule

Không có general cascade. Chỉ cho tối đa một fallback và phải có **new evidence**.

Valid example:

```text
Mini reports packet ambiguity
-> MCP adds exact symbol context
-> Luna once
```

Invalid:

```text
Mini timeout
-> same packet Luna
-> same packet Terra
-> same packet Sol
```

Một failure phải làm thay đổi:

- evidence;
- scope;
- route class;
- strategy;
- hoặc return blocker.

---

# 31. Route ledger / telemetry cần duy trì

Recommended fields:

```text
TASK_CLASS
PACKET_FINGERPRINT
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
TOOL_DENSITY
RISK_CLASS
ROUTE_REQUESTED
ROUTE_RESOLVED
MODEL
EFFORT
PROFILE
CACHE_STATE
CAPACITY_STATE
TIME_TO_FIRST_DISPATCH
TIME_TO_FIRST_WRITE
TIME_TO_FIRST_ORACLE_GREEN
MODEL_WALL
TTA
INPUT_TOKENS
CACHED_TOKENS
OUTPUT_TOKENS
REASONING_TOKENS
ESTIMATED_CREDITS
FIRST_PASS_ACCEPTED
DEADLINE_HIT
CAPACITY_FAILURE
INTEGRATION_DEFECT
SOL_REPAIR_TURNS
CRITICAL_DEFECTS
```

Router v1 nên dùng simple class rules + recent similar accepted tasks. Chưa cần learned ML router.

---

# 32. Promotion gates

Không promote route từ 3–4 successes.

Một route rẻ hơn chỉ được production-promote cho task class khi:

1. quality floor gần/không thấp hơn Sol control;
2. representative paired sample đủ lớn;
3. strong external oracle;
4. conservative lower confidence bound đạt target;
5. zero critical-invariant miss trong evaluation set;
6. TTA accepted-result tốt hơn, không chỉ first-token;
7. total credits tính cả failures thấp hơn;
8. Sol repair/integration burden không tăng;
9. capacity ổn định;
10. result lặp lại sau model/runtime release.

Current interpretation:

| Route | Status |
|---|---|
| Mini-low patch-only | production auto only under narrow strong-oracle gate; continue telemetry |
| Luna-high patch-only | production bounded fallback/class route |
| Sol-xhigh deep-code | routine deep default |
| Terra-high cross-file | explicit experimental |
| Sol-max | explicit consequential exception |
| Sol-ultra | explicit parallel-extreme exception |

---

# 33. Known limitations của evidence

## 33.1 Phase 1

- 10 tasks;
- one official run/route/task;
- mostly localized Python MCP regressions;
- ChatWeb Sol had accumulated repo context;
- service capacity sampled one point in time;
- ChatWeb token/credit telemetry unavailable;
- full gate là Python package boundary, không full Electron/Rust repo.

## 33.2 Phase 2

- patch-only success sample nhỏ;
- effort calibration n=1;
- autonomous deadline bị ~30s observe clamp;
- Terra capacity volatility lớn;
- T07 packet invalidated do localization bug;
- native Ultra swarm chưa được benchmark trên proper parallel task;
- mutations vẫn thiên về regressions hơn full features/refactors.

## 33.3 Production live smoke

- Mini end-to-end smoke là one-file invariant, chứng minh wiring/safety nhưng không chứng minh global quality.

Kết luận được phép:

- đủ bằng chứng để **không** dùng bad topology;
- đủ để deploy guarded adaptive router;
- chưa đủ để broad-promote Terra/Ultra hoặc bỏ các gate.

---

# 34. Future experiment plan

## 34.1 Cross-file representative suite

Tối thiểu 20 paired tasks:

- cross-file bug;
- small feature;
- adapter/API change;
- UI/data-flow change;
- refactor;
- CI/env diagnosis;
- compatibility change;
- long-context debugging.

Selected tasks lặp >=3 lần để estimate capacity variance.

Routes:

1. ChatWeb Sol -> MCP control.
2. Mini patch-only qualified classes.
3. Luna high patch-only.
4. Sol xhigh deep candidate.
5. Terra high scoped/isolated executor.

Max/Ultra chỉ trên task class xứng đáng.

## 34.2 Ultra-specific suite

Không dùng one-line mutation.

Task cần:

- >=3 independent workstreams;
- interfaces pinned;
- disjoint ownership;
- merge cost đo được;
- single-lane Sol xhigh baseline;
- ordinary 2-lane baseline;
- native Ultra comparison.

Measure:

```text
parallel speedup
credits
subagent count
merge/review cost
stale-work rate
integration defects
Sol acceptance burden
```

## 34.3 Packet-quality benchmark

Vary packet quality giữ model cố định:

```text
raw objective only
vs file-localized
vs symbol-localized
vs symbol + failing oracle
vs symbol + oracle + adjacent contract
```

Mục tiêu là định lượng value của localization thay vì chỉ model tier.

---

# 35. Decision pseudocode cuối cùng

```text
finish = define_finish_line()
oracle = establish_authoritative_proof(finish)
evidence = MCP.localize_once(oracle)

if environment_or_oracle_invalid:
    fix_environment_first()
    STOP_MODEL_SPEND

if deterministic_change_known:
    MCP.apply_and_prove()
    return CHATWEB_SOL_ACCEPT

risk = classify_risk(evidence)
width = integration_width(evidence)
packet = build_bounded_packet(evidence)

if packet_quality_insufficient:
    improve_localization()
    return CHATWEB_SOL

if localized_bug_or_test
   and strong_oracle
   and paths <= 2
   and context <= 24KB
   and risk_not_critical:
    candidate = MINI_LOW_NO_TOOLS(packet)
    MCP.validate_apply_prove(candidate)
    return CHATWEB_SOL_ACCEPT_OR_REPAIR

if bounded_leaf
   and paths <= 4
   and context <= 60KB
   and semantics_settled:
    candidate = LUNA_HIGH_NO_TOOLS(packet)
    MCP.validate_apply_prove(candidate)
    return CHATWEB_SOL_ACCEPT_OR_REPAIR

if deep_or_broad:
    CHATWEB_SOL_SETTLES_SHARED_SEMANTICS()
    candidate = CODEX_SOL_XHIGH_DEEP(packet)
    MCP.validate_apply_prove(candidate)
    return CHATWEB_SOL_ACCEPT

if explicit_cross_file_experiment:
    TERRA_HIGH_ISOLATED(packet)
    external_grade()
    CHATWEB_SOL_ACCEPT_OR_REJECT()

if consequential_and_xhigh_underproven:
    require_high_cost_ack()
    SOL_MAX()

if truly_parallel_extreme
   and explicit_budget
   and expected_parallel_value_positive:
    require_high_cost_ack()
    SOL_ULTRA()

never:
    blind_serial_cascade()
    nested_unbounded_swarm()
    child_model_final_acceptance()
```

---

# 36. Decision matrix nhanh

| Situation | Route |
|---|---|
| Known deterministic action | MCP |
| Local bug, exact patch already known | ChatWeb Sol -> MCP |
| Tiny localized bug + failing strong oracle | Mini low candidate |
| Harder bounded leaf | Luna high candidate |
| Broad/deep implementation | Sol xhigh |
| Cross-file route under experiment | Terra high explicit |
| Consequential unresolved after xhigh | Sol max explicit |
| Truly parallel extreme task | Sol ultra explicit |
| Final acceptance | ChatWeb Sol |
| Evidence review complete/proof strong | NONE |
| Cheap independent packet review | Mini |
| Scoped read-only review | Luna |
| Critical distinct review | Terra |
| Persisted-history evidence genuinely required | HISTORY explicit |

---

# 37. Những sai lầm cần tránh trong tương lai

1. **False-green oracle:** test nhầm source rồi benchmark model.
2. **Conflate model and topology:** kết luận model yếu vì shell/localization loop yếu.
3. **Blind retry:** cùng packet/cùng failure nhiều lần.
4. **Serial tier ladder:** trả startup/tool tax ở mọi tier.
5. **Use Ultra as safety blanket:** fan-out task tuần tự.
6. **Use file count as risk:** bỏ qua integration width.
7. **Let candidate write directly:** mất deterministic mutation boundary.
8. **Treat interrupt as failure:** không external-grade candidate state.
9. **Promote from 4/4:** sample quá nhỏ.
10. **Ignore capacity:** capability benchmark không đủ cho production.
11. **Ignore cache:** cold/warm economics khác nhau.
12. **Duplicate repository discovery:** ChatWeb và Codex cùng scan lại mọi thứ.
13. **Homogeneous self-review:** nhiều agent cùng rationale không tạo evidence mới.
14. **Trust client schema freshness:** server policy phải safe khi wrapper cache cũ.
15. **Deploy skill/artifact without hash gate:** transfer/truncation có thể tạo silent corruption.

---

# 38. Reproduction/provenance

Primary research files:

- `docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`
- `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`

Key implementation files:

- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py`
- `resources/coding-tools-mcp/tests/test_codex_bridge.py`
- `resources/coding-tools-mcp/tests/test_task_state_and_build.py`
- `tests/stability-source.test.js`

Key commits:

- `c20f1e220d050be67143a6f8751d7ad87b695f81` — adaptive routing + research.
- `0fffe4be58d7eba755e8701ad0f97e0f2ec144c6` — newline normalization for exact candidate replacement.
- `b802b59756b0a9c92c004fad7860aca9e14dc107` — require strong verification before auto Mini routing.

Phase 1 base at study time:

- HEAD `1df45d48a661f336703f8b1c95fb3df74359dc60` plus then-uncommitted bridge change-set.

Runtime observed during research:

- `codex-cli 0.147.0-alpha.6.6`;
- grading Python 3.11.7.

Historical Phase 1 report SHA at creation:

- `5511A490DAB189E1C00244B8BB1AD46D13D7342572EACB893630FCF7B59A197A`.

Phase 2 report at creation:

- 1,821 lines;
- 58,815 bytes.

Skill v4 package used for final policy synchronization:

- 13 files;
- comparator tests 10/10;
- ZIP SHA-256 observed during deployment: `8D0260C813B906BE53AE08DB5FF0703430CE634D7D1B680C3FBA5A2D0981B6BA`.

---

# 39. Final decision record

## Decision

Adopt **adaptive bounded orchestration**:

```text
ChatWeb Sol = control + semantics + final acceptance
Coding Tools MCP = deterministic evidence + writer + proof
Mini low = cheapest tiny strong-oracle candidate
Luna high = harder bounded candidate
Codex Sol xhigh = routine deep-code lane
Terra high = explicit cross-file experiment
Sol max = consequential exception
Sol ultra = explicit true-parallel extreme exception
```

## Why

1. ChatWeb Sol control route đạt 10/10 trong Phase 1.
2. Luna/Terra autonomous routes không đạt quality/availability floor và cascade làm latency tệ hơn.
3. Phase 2 chứng minh same Sol xhigh 0/3 autonomous nhưng 3/3 patch-only: topology là major causal variable.
4. Mini/Luna patch-only đạt 4/4 trên small suite với cost thấp hơn nhiều Sol xhigh.
5. Sol max/ultra không tạo quality gain trên bounded calibration case.
6. Terra-high current autonomous evidence bị deadline/capacity instability.
7. External research ủng hộ task-shape-aware parallelism, fewer model switches, compact tool surfaces và independent verification.
8. Production implementation giữ mutation/proof authority ở MCP và final acceptance ở ChatWeb Sol.
9. Live Mini auto-route smoke chứng minh full server-side wiring hoạt động.
10. Guardrails đã được regression-test và deployment issues đã dẫn tới fixes cụ thể.

## What this decision does not claim

- Không claim Mini/Luna ngang capability Sol nói chung.
- Không claim Terra yếu nói chung.
- Không claim Ultra không hữu ích.
- Không claim current thresholds 2 paths/24KB và 4 paths/60KB là universally optimal.
- Không claim benchmark rates/pricing vĩnh viễn đúng.

Nó chỉ claim:

> Với evidence hiện có trên hệ thống này, adaptive bounded routing có expected value tốt nhất: đưa entropy/tool work về MCP, dùng model rẻ khi objective oracle giới hạn risk, giữ Sol xhigh cho deep work, và chỉ mở Terra/Max/Ultra khi task topology/risk thật sự biện minh.

---

# 40. Operational acceptance checklist

Trước mỗi delegated coding task:

```text
[ ] Finish line rõ
[ ] Protected invariants rõ
[ ] Base/worktree identity rõ
[ ] Oracle đã preflight
[ ] Context/localization đúng source
[ ] Integration width được đánh giá
[ ] Risk class không bị suy từ file count đơn thuần
[ ] Chỉ một primary execution lane
[ ] Candidate models không có authoritative write
[ ] Allowed paths explicit
[ ] Deadline explicit
[ ] External proof độc lập với model confidence
[ ] Không unchanged retry
[ ] Không blind cascade
[ ] Final acceptance bởi ChatWeb Sol
```

Nếu dùng Terra/Max/Ultra:

```text
[ ] Explicit route reason
[ ] Cost/latency expected value positive
[ ] Required budget acknowledgement
[ ] Isolation/parallel ownership correct
[ ] Route ledger sẽ ghi result
```

---

# 41. Kết luận cuối

Bài học lớn nhất của toàn bộ quá trình không phải “Mini rẻ”, “Sol mạnh”, hay “Ultra đắt”. Bài học là:

> **Hiệu suất của coding-agent system được quyết định bởi cách chia semantic authority, evidence collection, mutation authority, oracle và model reasoning.**

Một model mạnh trong topology sai có thể chậm và đắt hơn model rẻ trong packet đúng. Một model rẻ không có oracle có thể tạo expected accepted-result cost cao hơn model mạnh. Nhiều agents không tự động tạo parallelism. Test xanh không tự động giải quyết high-risk semantics. Và router tốt không phải là ladder nhiều model; nó là một classifier đơn giản, evidence-calibrated, biết abstain và biết khi nào không delegate.

Kiến trúc cuối cùng vì vậy cố ý giữ ba authority tách biệt:

```text
SEMANTIC AUTHORITY  = ChatWeb Sol
MUTATION/PROOF AUTHORITY = Coding Tools MCP
BOUNDED REASONING CAPACITY = Mini/Luna/Sol/Terra/Max/Ultra theo task shape
```

Đây là cơ sở để hệ thống tiếp tục tối ưu theo dữ liệu mới mà không phải thay đổi triết lý nền: **quality first, accepted-result economics second, orchestration only where it earns its cost.**
