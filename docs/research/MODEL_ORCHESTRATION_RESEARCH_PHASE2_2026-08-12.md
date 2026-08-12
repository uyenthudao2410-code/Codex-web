# Model Orchestration Research Phase 2 — ChatWeb Sol, Codex Sol xhigh, Mini, Luna, Terra, Max, Ultra

**Ngày nghiên cứu:** 2026-08-12  
**Repository:** `E:\DEV\Tools-Codex-web`  
**Trạng thái:** Decision document / proposal — **chưa thay đổi production routing/skill dựa trên Phase 2**  
**Mục tiêu:** xác định cách phối hợp ChatWeb, Coding Tools MCP, Codex App Server, Codex Desktop và các tier/effort GPT-5.6 để tối ưu **quality → time-to-accepted-result → total expected cost**, thay vì tối ưu token hoặc model riêng lẻ.

---

## 1. Kết luận điều hành

### 1.1 Kết luận chính

Dữ liệu hiện tại ủng hộ kiến trúc **asymmetric orchestration**:

```text
USER
  |
  v
CHATWEB GPT-5.6 SOL
semantic/control plane + final acceptance
  |
  v
CODING TOOLS MCP
collect evidence once + deterministic execution/proof
  |
  +------------------------+--------------------------+
  |                        |                          |
  v                        v                          v
MCP ONLY             PATCH CANDIDATE             DEEP CODE LANE
known change          no-tools                    Codex Desktop/App Server
strong oracle         bounded packet              Sol xhigh
  |                        |                          |
  |                  Mini low first                  |
  |                  Luna high when needed           |
  |                  Sol xhigh only if hard          |
  |                        |                          |
  +------------------------+--------------------------+
                           |
                           v
                 deterministic oracle
                           |
                           v
                    CHATWEB SOL ACCEPT
```

**Không dùng `Ultra` làm mặc định.**  
**Không dùng autonomous Codex shell-loop cho leaf nhỏ làm mặc định.**  
**Không dùng ladder tuần tự `Mini -> Luna -> Terra -> Sol -> Ultra`.**

Phương án hiệu quả nhất theo bằng chứng hiện có là:

1. **ChatWeb Sol** giữ user intent, requirement, architecture, shared semantics, risk classification, integration và final acceptance.
2. **Coding Tools MCP** là evidence/execution gateway: localize, diff, tests, compiler, exact patch apply, telemetry và route ledger.
3. Với leaf đã localize tốt, nếu cần model tạo candidate patch thì dùng **GPT-5.4-Mini low / no-tools** trước; **Luna high / no-tools** khi packet khó hơn hoặc Mini blocked/uncertain.
4. **Codex Sol xhigh** là default **deep Codex escalation**, không phải default leaf executor.
5. **Codex Desktop** nên được coi là persistent deep-work lane. Nếu Desktop chỉ dành cho việc khó/dài, có thể để **Sol xhigh làm default của Desktop** — đây là phương án “Sol xhigh-only” hợp lý nhất.
6. **Terra high/xhigh** vẫn có vai trò tiềm năng cho bounded cross-file implementation, nhưng chưa nên auto-route trong runtime hiện tại vì capacity + autonomous-loop evidence chưa đủ.
7. **Sol max** chỉ khi xhigh chưa đủ cho consequential reasoning.
8. **Sol ultra** chỉ khi task thật sự có các workstream độc lập có thể chạy song song và budget rõ ràng. Ultra là topology multi-agent, không nên hiểu đơn giản là “xhigh tốt hơn”.

### 1.2 Hai khái niệm Sol phải tách biệt

- **ChatWeb Sol**: GPT-5.6 Sol của phiên ChatGPT hiện tại. Nó có conversation context, user intent, web research và MCP. Effort nội bộ **không được expose**, nên không được gọi nó là `xhigh`, `max` hay `ultra`.
- **Codex Sol xhigh/max/ultra**: `gpt-5.6-sol` trong Codex/App Server với effort được request và quan sát qua runtime metadata.

Hai route dùng cùng capability family nhưng **khác harness, context, tool topology, session lifecycle và cost surface**. Vì vậy benchmark phải đánh giá **system route**, không chỉ tên model.

---

## 2. Vì sao Phase 2 cần thiết

Phase 1 đã so sánh:

- ChatWeb Sol -> MCP;
- Codex Luna autonomous low;
- Codex Terra autonomous medium.

Phase 1 không đo:

- Codex Sol xhigh;
- Sol max;
- Sol ultra;
- Luna high;
- Terra high;
- topology `patch-only/no-tools`.

Do đó Phase 1 chỉ đủ để nói:

> `Luna-low autonomous` và `Terra-medium autonomous` không nên được promote cho class localized strong-oracle đã test.

Nó **không đủ** để kết luận Luna/Terra nói chung kém, và cũng không trả lời câu hỏi “có nên chỉ dùng Sol xhigh không?”.

Phase 2 được thiết kế để tách ba biến:

```text
MODEL CAPABILITY
    !=
REASONING EFFORT
    !=
AGENT TOPOLOGY
```

Đây là distinction quan trọng nhất của toàn bộ nghiên cứu.

---

## 3. Evidence hierarchy

Tài liệu dùng ba loại evidence và không trộn độ tin cậy:

### A. Measured local evidence

Dữ liệu chạy trên chính `Tools-Codex-web`, Codex App Server và MCP hiện tại. Đây là evidence mạnh nhất cho policy local, nhưng sample còn nhỏ.

### B. Official / scientific evidence

- OpenAI official model/effort behavior and pricing.
- Google Research controlled multi-agent experiments.
- ACL/EACL routing/tool-use papers.
- Independent patch-verification research.
- SWE-bench correctness studies.

### C. Field reports / discussions

GitHub issues và community discussions dùng như **operational warning**, không được coi là controlled benchmark hay official guarantee.

---

## 4. External research synthesis

## 4.1 OpenAI GPT-5.6: model tier và Ultra

OpenAI mô tả GPT-5.6 gồm ba durable capability tier:

- Sol: flagship;
- Terra: lower-cost balanced tier;
- Luna: fastest / most affordable tier.

OpenAI công bố `ultra` là highest-capability setting **coordinating multiple agents across parallel workstreams**. Đây là điểm rất quan trọng: Ultra không chỉ là “thêm vài token reasoning” mà làm thay đổi topology thực thi.

Official coding results cũng cho thấy khoảng cách capability giữa các tier không tỷ lệ tuyến tính với giá. Ví dụ trên launch page:

- Coding Agent Index: Sol 80, Terra 77.4, Luna 74.6;
- SWE-Bench Pro: Sol 64.6%, Terra 63.4%, Luna 62.7%;
- DeepSWE: Sol 72.7%, Terra 69.6%, Luna 67.2%;
- Terminal-Bench 2.1: Sol 88.8%, Sol Ultra 91.9%, Terra 87.4%, Luna 84.7%.

Trong Big Finance Bench, gap rộng hơn: Sol 53%, Terra 51%, Luna 36%. Điều này củng cố việc không route financial meaning xuống Luna chỉ vì diff nhỏ.

**Nguồn:** OpenAI, “GPT-5.6: Frontier intelligence that scales with your ambition”, 2026-07-09.  
https://openai.com/index/gpt-5-6/

OpenAI preview cũng mô tả `max` là tăng deep-reasoning time cho Sol, trong khi `ultra` vượt single-agent bằng subagents.

**Nguồn:** OpenAI, “Previewing GPT-5.6 Sol: a next-generation model”, 2026-06-26.  
https://openai.com/index/previewing-gpt-5-6-sol/

### Implication

- `xhigh` là candidate hợp lý cho routine deep lane.
- `max` là escalation reasoning.
- `ultra` chỉ có expected value khi **parallelism thực sự tồn tại**.

Không được dùng `ultra` để chữa một packet bị localize kém hoặc một task tuần tự.

---

## 4.2 Multi-agent chỉ tốt khi task shape phù hợp

Google Research đánh giá **180 agent configurations** và tìm thấy:

- multi-agent coordination có thể tăng rất mạnh trên parallelizable tasks;
- centralized architecture tăng khoảng 80.9% trên Finance-Agent so với single-agent baseline;
- trên sequential planning, multi-agent variants giảm 39–70%;
- independent multi-agent có thể amplify error tới 17.2x, trong khi centralized orchestration giới hạn amplification tốt hơn;
- predictive architecture selection chọn đúng optimal architecture cho 87% unseen task configurations.

**Nguồn:** Google Research, “Towards a science of scaling agent systems: When and why agent systems work”, 2026-01-28.  
https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

### Implication cho hệ thống này

Ultra/multi-agent chỉ nên mở khi:

```text
PARALLELIZABLE = true
WRITE_OWNERSHIP_DISJOINT = true
SHARED_INTERFACES_SETTLED = true
REVIEW_CAPACITY >= WORKER_OUTPUT_RATE
EXPECTED_PARALLEL_GAIN > coordination + review + merge cost
```

Nếu task là:

```text
fail -> inspect -> decide -> edit -> rerun -> decide
```

thì đó là sequential agent loop; thêm workers thường chỉ thêm communication/tool tax.

---

## 4.3 Model routing: fewer switches tốt hơn cascade dài

MTRouter nghiên cứu cost-aware multi-turn routing và báo cáo:

- giảm tổng cost 58.7% trên ScienceWorld so với GPT-5 trong setup của paper;
- giảm 43.4% trên HLE trong khi giữ competitive accuracy;
- router hiệu quả có xu hướng **ít model switches hơn**;
- model specialization xuất hiện theo task/history.

**Nguồn:** Zhang et al., “MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings”, ACL 2026.  
DOI: 10.18653/v1/2026.acl-long.2045  
https://aclanthology.org/2026.acl-long.2045/

Phase 1 local data cũng khớp với điều này:

- Luna -> Sol serial fallback: mean penalty khoảng +22.8 s/task;
- Terra -> Sol serial fallback: mean penalty khoảng +10.7 s/task.

### Implication

Router của chúng ta phải là **classification**, không phải cascade.

Sai:

```text
Mini fails -> Luna -> Terra -> Sol -> Ultra
```

Đúng:

```text
classify packet once
-> choose cheapest competent route
-> one fallback maximum only when new evidence changes classification
```

---

## 4.4 Router đơn giản dựa trên lịch sử có thể đủ tốt

ContextualRouter cho thấy retrieval/kNN trên past similar tasks có thể cạnh tranh hoặc tốt hơn router phức tạp và generalize với rất ít historical data trong benchmark của paper.

**Nguồn:** Varangot-Reille et al., “Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient”, EACL 2026.  
DOI: 10.18653/v1/2026.eacl-srw.22  
https://aclanthology.org/2026.eacl-srw.22/

LLMRouterBench (>400K instances, 21 datasets, 33 models) cũng kết luận nhiều sophisticated routers không reliably beat simple baseline; larger ensembles có diminishing returns và careful model curation quan trọng hơn.

**Nguồn:** Li et al., “LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing”, Findings of ACL 2026.  
DOI: 10.18653/v1/2026.findings-acl.1881  
https://aclanthology.org/2026.findings-acl.1881/

### Implication

Không cần ML router phức tạp ngay.

Production router v1 nên dùng:

```text
TASK_CLASS
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
TOOL_DENSITY
RISK
PACKET_QUALITY
CACHE_STATE
CAPACITY_STATE
recent similar accepted routes
```

và nearest-similar-task ledger trước.

---

## 4.5 Tool surface nhỏ là lợi thế, không phải limitation

ToolScope chỉ ra redundant/large toolsets làm giảm tool selection; context-aware filtering/merging tăng tool-selection accuracy khoảng 8.38–38.6% trong evaluations của paper.

**Nguồn:** Liu et al., “ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering”, ACL 2026.  
DOI: 10.18653/v1/2026.acl-long.1573  
https://aclanthology.org/2026.acl-long.1573/

### Implication

Giữ **8-tool smart surface** của Coding Tools MCP là đúng hướng.

Không expose thêm Mini/Luna/Terra/Sol như nhiều model-facing tools. Routing phải nằm **bên trong MCP / skill policy**, không làm tool schema phình ra.

---

## 4.6 Independent verification tốt hơn homogeneous self-review

RETRACE dùng independent forward/backward reconstruction để verify patch thay vì chỉ yêu cầu cùng agent “review lại chính mình”. Trên SWE-bench Verified, paper báo cáo Pass@1 tăng 7.0 điểm với GPT-5-mini và 3.6 điểm với MiniMax-2.5; ablations cho thấy independent verification stages tạo giá trị thật.

**Nguồn:** Li et al., “Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework”, arXiv:2608.08950, 2026-08-09.  
https://arxiv.org/abs/2608.08950

### Implication

Review plane nên:

- blind/evidence-only;
- không nhận reasoning narrative của primary executor;
- một reviewer độc lập là đủ cho một distinct question;
- deterministic oracle vẫn là authority khi có.

Không dùng nhiều homogeneous Sol agents debate cùng một interpretation nếu không có independent evidence.

---

## 4.7 Test xanh chưa đủ cho high-risk acceptance

Một empirical study về SWE-bench cho thấy một số patch được benchmark tính là solved vẫn không khớp developer expectations; paper báo cáo các mức false plausibility đáng kể khi kiểm tra bằng broader tests/differential behavior.

**Nguồn:** Wang, Pradel & Liu, “Are ‘Solved Issues’ in SWE-bench Really Solved Correctly? An Empirical Study”, arXiv:2503.15223.  
https://arxiv.org/abs/2503.15223

### Implication

Strong oracle giúp route xuống model rẻ hơn, nhưng với:

- auth;
- privacy/tenant boundary;
- finance semantics;
- destructive migration;
- public compatibility contract;

Sol vẫn phải kiểm tra invariant/adjacent risk, không chỉ nhìn một focused unit test.

---

## 4.8 Diversity có thể giá trị hơn nhiều homogeneous agents

Research về heterogeneous multi-agent systems cho thấy gains có thể đến từ **diverse effective channels**, không phải agent count; một paper 2026 báo cáo 2 diverse agents có thể match/exceed 16 homogeneous agents trong setup của họ.

**Nguồn:** Yang et al., “Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity”, arXiv:2602.03794.  
https://arxiv.org/abs/2602.03794

### Implication

Nếu cần second opinion:

```text
Sol primary + Mini/Luna/Terra independent verifier
```

có thể tạo evidence diversity tốt hơn:

```text
Sol + Sol + Sol cùng rationale
```

nhưng chỉ khi reviewer có distinct evidence role.

---

## 4.9 Safety-aware routing

Conformal routing research 2026 đề xuất calibrate route threshold theo acceptable violation rate thay vì promote model rẻ chỉ từ raw success percentage.

**Nguồn:** “Conformal LLM Routing with Distribution-Free Safety Guarantees”, ACL 2026 Student Research Workshop.  
https://aclanthology.org/2026.acl-srw.70/

### Implication

`4/4` Mini patch-only trong Phase 2 là promising, **không đủ để declare global-safe auto-route**. Promotion cần nhiều representative observations và conservative lower confidence bound.

---

## 4.10 Field evidence: chọn effort/model hiện vẫn là operational problem

Các open feature requests trong official `openai/codex` repository đề nghị:

- Smart Mode tự chọn model + effort;
- per-thread Auto routing;
- model-callable reasoning gearbox;
- mode-specific default model/effort.

Điều này không phải benchmark, nhưng là field signal rằng một fixed global effort không phù hợp với workload biến thiên.

Examples:

- openai/codex #34388 — Smart Mode for automatic model/reasoning selection;
- #34278 — per-thread Auto routing model + effort;
- #20855 — reasoning gearbox;
- #8649 — dynamic reasoning tiering.

Một GitHub issue #35177 báo cáo `Sol ultra` tạo 20+ subagent sessions và tiêu 250–600 credits trong một số read-only workloads, trong khi xhigh thấp hơn rất nhiều. Đây là **user report chưa được OpenAI xác nhận như behavior guarantee**, nên chỉ dùng như cost-risk warning.

**Field source:**  
https://github.com/openai/codex/issues/35177

### Implication

Không bật Ultra chỉ vì “task khó”. Ultra phải cần explicit topology/budget gate.

---

# 5. Phase 1 baseline — tóm tắt

Phase 1 đã chạy 10 mutation tasks × 3 routes = 30 official observations.

| Route | First-pass accepted | Availability-adjusted | Median observed TTA |
|---|---:|---:|---:|
| ChatWeb Sol -> MCP | **10/10 (100%)** | 100% | **42.5 s** |
| Luna low autonomous | 2/10 (20%) | 2/6 = 33.3% | 47.3 s |
| Terra medium autonomous | 6/10 (60%) | 6/8 = 75% | 48.9 s |

Phase 1 conclusions retained:

- do not auto-promote Luna-low autonomous;
- do not auto-promote Terra-medium autonomous globally;
- do not use serial fallback ladder;
- capacity is a real production routing input;
- autonomous tool-loop overhead can dominate token-price advantage.

Phase 1 report:

`docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`

---

# 6. Phase 2 methodology

## 6.1 Research questions

Phase 2 trả lời:

1. `Codex Sol xhigh` có nên thay ChatWeb/MCP hoặc lower tiers làm default executor không?
2. Model nào thắng khi **localization/tool loop bị loại khỏi worker** và worker chỉ tạo candidate patch?
3. `xhigh`, `max`, `ultra` khác nhau thế nào trên cùng evidence packet?
4. Có nên dùng một policy “Sol xhigh-only” để giảm routing complexity không?
5. Vai trò thực tế của Mini/Luna/Terra còn lại là gì?

## 6.2 Task suite

Sử dụng 6 regression invariants đã có deterministic existing tests:

| ID | Class | Broken invariant |
|---|---|---|
| T02 | routing_effort_control | packet effort `low -> ultra` |
| T04 | app_server_protocol | invalid `deferGoalContinuation` on ephemeral fork |
| T06 | capacity_resilience | capacity circuit-breaker guard disabled |
| T07 | session_ownership | bridge-owned thread guard removed |
| T09 | client_tool_compatibility | smart surface 8 -> 9 tools |
| T10 | dirty_worktree_isolation | diff scope falls back to whole worktree |

Correct preflight used system Python 3.11.7 with fixture `PYTHONPATH` and verified **6/6 focused tests red**.

An earlier preflight with the embedded native Python imported production source instead of the fixture and returned false-green. That run was invalidated before model benchmarking; no model conclusions use it.

## 6.3 Two topologies

### Autonomous executor

```text
objective + focused test
-> model can inspect repo
-> shell/tool loop
-> model edits isolated worktree
-> model runs focused test
-> external focused/full grading
```

### Patch-only / no-tools

```text
ChatWeb/MCP-style localization
-> objective + failing oracle + bounded source snippet
-> model returns structured exact replacement
-> deterministic apply
-> focused oracle
-> full gate
```

The second topology isolates **model patch reasoning** from agentic localization/tool-loop cost.

## 6.4 Acceptance

Accepted only when:

- focused oracle passes;
- full Python package gate passes;
- production code changed appropriately;
- tests are not modified.

## 6.5 Important instrumentation limitation

The current bridge `observe()` bounds individual wait to ~30 seconds. Therefore Phase 2 autonomous executor calls requested at 45s were effectively interrupted around 31–32s.

Do **not** compare Phase 2 autonomous wall time directly against Phase 1 true ~45s runner as if deadline were identical.

This itself is a production finding: executor instrumentation needs a true deadline loop plus `time_to_first_write` and `time_to_first_green` before cross-file promotion.

---

# 7. Phase 2 measured results

## 7.1 Codex Sol xhigh autonomous executor

Official pre-stop observations:

| Task | Result | Model wall | TTA | Est. credits | Production write |
|---|---|---:|---:|---:|---|
| T02 | FAIL / interrupted | 31.154 s | 37.034 s | 0.3765 | none |
| T04 | FAIL / interrupted | 31.145 s | 36.926 s | 0.2674 | none |
| T06 | FAIL / interrupted | 31.147 s | 37.673 s | 0.3544 | none |

**Accepted: 0/3.**

Batch was intentionally stopped after the same failure pattern to avoid spending additional credits. Supplemental child/lifecycle outputs later appeared for the remaining cases, also without successful production writes; they are not used in the primary score because the parent batch had already been terminated.

### Interpretation

This does **not** prove Sol xhigh lacks coding capability.

It proves:

> For narrow strong-oracle repairs, giving Sol xhigh an autonomous shell/localization loop under the current bridge is worse than giving it a compact, correctly localized packet.

---

## 7.2 Sol xhigh patch-only/no-tools

Valid localized cases:

| Task | Accepted | Model wall | TTA | Est. credits |
|---|---:|---:|---:|---:|
| T02 | yes | 6.681 s | 10.563 s | 1.288875 |
| T04 | yes | 7.545 s | 11.477 s | 1.323875 |
| T06 | yes | 8.263 s | 11.648 s | 1.339000 |

**3/3 accepted.**

T10 with Sol xhigh patch-only did not finish before the 20s bound in one observation. T07 was invalid as a model test because packet localization selected the wrong code neighborhood; Sol correctly returned `BLOCKED` rather than inventing a patch. T07 is excluded from model scoring.

### Interpretation

`Sol xhigh` is highly useful when the system has already done:

```text
localization
+ evidence selection
+ scope reduction
+ oracle specification
```

The expensive part is often **not model intelligence**; it is autonomous discovery/tool looping.

---

## 7.3 Luna high patch-only/no-tools

| Task | Accepted | Model wall | TTA | Est. credits |
|---|---:|---:|---:|---:|
| T02 | yes | 4.615 s | 7.717 s | 0.255100 |
| T04 | yes | 5.304 s | 8.259 s | 0.266150 |
| T06 | yes | 4.644 s | 7.689 s | 0.257775 |
| T10 | yes | 12.199 s | 16.729 s | 0.313850 |

**4/4 accepted.**

Mean TTA trên 4 cases: ~10.10 s.  
Mean estimated credits: ~0.2732.

---

## 7.4 GPT-5.4-Mini low patch-only/no-tools

| Task | Accepted | Model wall | TTA | Est. credits |
|---|---:|---:|---:|---:|
| T02 | yes | 3.888 s | 6.934 s | 0.140337 |
| T04 | yes | 7.089 s | 10.176 s | 0.159342 |
| T06 | yes | 6.819 s | 10.210 s | 0.175723 |
| T10 | yes | 9.211 s | 13.478 s | 0.076414* |

`*` T10 had high cache reuse in this observation, so do not generalize its unusually low credit figure as cold cost.

**4/4 accepted.**

Mean TTA: ~10.20 s.  
Mean estimated credits: ~0.1380.

### Interpretation

For **well-localized strong-oracle candidate generation**, Mini is not merely a reviewer candidate; it can generate valid minimal patches in this small Phase 2 suite.

Sample size is too small to auto-promote globally, but it changes the most promising research direction.

---

# 8. Direct common-task comparison

T02/T04/T06 are common valid packet-only tasks across Mini/Luna/Sol-xhigh.

| Route | Accepted | Mean TTA | Mean est. credits |
|---|---:|---:|---:|
| Mini low patch-only | **3/3** | 9.107 s | **0.158467** |
| Luna high patch-only | **3/3** | **7.888 s** | 0.259675 |
| Sol xhigh patch-only | **3/3** | 11.229 s | 1.317250 |

On these three samples:

- Sol xhigh costs about **5.1x Luna high** per accepted patch candidate;
- Sol xhigh costs about **8.3x Mini low**;
- Sol xhigh is also slower on mean TTA than both lower tiers;
- all three meet the same external focused + full gate.

This is the strongest empirical reason **not** to use Sol xhigh-only for every bounded leaf.

It is not evidence that Mini/Luna have equal general capability to Sol. It is evidence that **when packet entropy is already removed, expensive capability is often unused**.

---

# 9. Sol xhigh vs max vs ultra — controlled effort calibration

Same T06 packet, same no-tools topology:

| Sol effort | Accepted | Model wall | TTA | Est. credits | Output / reasoning tokens |
|---|---:|---:|---:|---:|---:|
| xhigh | yes | 8.263 s | 11.648 s | 1.339000 | 124 / 56 |
| max | yes | 5.540 s | 9.304 s | 1.351125 | 139 / 80 |
| ultra | yes | 6.640 s | 9.799 s | 1.383625 | 180 / 113 |

### Correct interpretation

- n=1 per effort: do not claim max is inherently faster than xhigh.
- quality is identical on this bounded task.
- credits rise modestly with effort in this packet.
- no observed quality gain justifies Ultra here.

### Critical caveat about Ultra

This test used the **packet/no-tools constrained profile**. It is **not equivalent to native Ultra multi-agent behavior** described by OpenAI.

Therefore the only valid conclusion is:

> Under a tightly constrained evidence-only packet, escalating xhigh -> max -> ultra did not improve acceptance on T06.

It does **not** benchmark a full Ultra swarm. Running native Ultra merely to benchmark a one-invariant leaf would violate the objective of this study because task shape is not parallelizable and potential spend is high.

---

# 10. Terra high Phase 2 result

Autonomous Terra high on medium-width tasks:

| Task | Result | Model wall | TTA | Est. credits |
|---|---|---:|---:|---:|
| T04 | interrupted / no write | 31.941 s | 34.772 s | 0.237175 |
| T06 | capacity failure | 11.103 s | 14.921 s | 0.663375 |
| T10 | capacity failure | 4.476 s | 9.050 s | no accounting |

**0/3 accepted in this Phase 2 topology.**

This is not sufficient evidence to reject Terra high capability. It is sufficient evidence **not to auto-promote Terra-high autonomous execution in the current runtime**.

Phase 1 Terra-medium had 6/10 accepted at a different true 45s runner. Combined evidence suggests Terra is potentially competent but current availability/tool-loop topology is unstable.

Terra therefore remains a **gated experimental cross-file worker**, not production default.

---

# 11. The most important experimental result: topology > tier on bounded work

Compare same Sol xhigh family:

```text
AUTONOMOUS SHELL LOOP
T02/T04/T06: 0/3 accepted
~31 s model wall each
no production write

PATCH-ONLY / NO-TOOLS
T02/T04/T06: 3/3 accepted
~6.7–8.3 s model wall
all full gates green
```

This difference is too large to attribute to a small reasoning-effort nuance.

The system should therefore optimize in this order:

1. reduce uncertainty/context;
2. localize causality;
3. bind scope;
4. specify oracle;
5. then choose model tier;
6. only then increase effort.

Using a more expensive model before fixing packet/topology is the wrong optimization order.

---

# 12. Evaluation of the “Sol xhigh-only” strategy

There are two different versions of “xhigh-only”.

## 12.1 Bad version: every Codex call uses Sol xhigh

```text
ChatWeb Sol
  -> every external review/candidate/execution
       -> Codex Sol xhigh
```

### Advantages

- simplest model-routing policy;
- no wrong-tier classification between Mini/Luna/Terra;
- high capability ceiling;
- easier audit trail.

### Disadvantages measured locally

For the common T02/T04/T06 patch-only cases:

- xhigh: ~1.3173 credits/accepted candidate;
- Luna high: ~0.2597;
- Mini low: ~0.1585.

So xhigh-only spends ~5.1x Luna or ~8.3x Mini for the same accepted results in this narrow class.

It was also slower in these cases.

### Decision

**Do not use Sol xhigh for every internal Codex call.**

---

## 12.2 Good version: Codex Desktop is an xhigh-only deep lane

A much better simplification is:

```text
ROUTINE / LOCALIZED
ChatWeb Sol + MCP
+ internal Mini/Luna packet candidates/review when useful

DEEP LONG-RUNNING CODE WORK
Codex Desktop = Sol xhigh by default
```

This has strong operational properties:

- Desktop is only opened/used when work already passed the “deep lane” gate;
- therefore a single xhigh default is reasonable;
- no need for users to constantly switch Desktop between Luna/Terra/Sol;
- routine cost remains low because routine work never enters Desktop;
- ChatWeb Sol remains architecture/integration authority.

### Recommendation

**This is the recommended interpretation of “Sol xhigh-only”.**

Use Codex Desktop as a dedicated xhigh workstation, not as the universal backend for every MCP packet.

---

# 13. Recommended system architecture

```text
┌───────────────────────────────────────────────────────────────┐
│ USER                                                          │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│ CHATWEB GPT-5.6 SOL                                           │
│ - requirements/user intent                                    │
│ - architecture/shared semantics                               │
│ - risk + integration-width classification                     │
│ - web/current research                                        │
│ - final acceptance                                             │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               v
┌───────────────────────────────────────────────────────────────┐
│ CODING TOOLS MCP — compact 8-tool surface                     │
│ - deterministic evidence collection                           │
│ - symbol/delta localization                                   │
│ - tests/compiler/runtime oracle                               │
│ - patch application                                            │
│ - bounded internal routing                                    │
│ - cache/capacity/route telemetry                              │
└───────────────┬──────────────────────┬────────────────────────┘
                │                      │
      known deterministic       candidate needed?
                │                      │
                v                      v
          MCP APPLY/VERIFY      PACKET-ONLY GENERATION
                               Mini low
                               Luna high when harder
                               Sol xhigh if semantics require
                                      │
                                      v
                              deterministic apply/oracle
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                         v                         v
                accepted local lane       deep/long/shared work
                                                  │
                                                  v
                                      CODEX DESKTOP / APP SERVER
                                      SOL xhigh persistent lane
                                      isolated worktree
                                                  │
                                                  v
                                       checkpoints/diff/proof
                                                  │
                                                  v
                                      CHATWEB SOL INTEGRATES
```

---

# 14. Responsibilities by component

## 14.1 `sol-lean-codex` Skill

Skill phải là **policy layer**, không phải một agent khác.

Nó quyết định:

- finish line;
- oracle strength;
- risk/integration width;
- whether delegation has positive expected value;
- executor shape;
- reviewer topology;
- effort ceiling;
- stop/escalation rules.

Skill không nên ép workers chỉ vì workers tồn tại.

### Proposed future skill change after review

Current rule:

```text
narrow strong oracle -> Luna
otherwise -> Terra
Sol for shared/critical
```

Nên refinement thành:

```text
if deterministic known action:
    MCP
elif localized candidate generation and strong oracle:
    Mini-low PATCH_ONLY
elif localized but higher semantic uncertainty:
    Luna-high PATCH_ONLY
elif bounded cross-file and route ledger proves Terra useful:
    Terra-high isolated executor
elif high integration/shared semantics:
    ChatWeb Sol
elif deep bounded independent implementation is valuable:
    Codex Sol-xhigh
max/ultra only explicit escalation
```

Đây mới là proposal; chưa cập nhật skill production trong Phase 2.

---

## 14.2 Coding Tools MCP

MCP nên làm “context compiler” hơn là chỉ shell gateway.

### Keep

- compact 8-tool surface;
- affected-file diff scoping;
- circuit breaker;
- read-only bridge default;
- bounded deadlines;
- token/cache/credit telemetry;
- hidden/internal Codex bridge.

### Add after approval

1. **Symbol-aware packet builder**
   - failing test/frame;
   - exact symbol;
   - exact changed block;
   - nearby caller/contract only when relevant.

T07 Phase 2 chứng minh packet localization là hard prerequisite: model đúng đã trả BLOCKED vì packet sai neighborhood.

2. **`candidate_patch` internal profile**
   - no tools;
   - structured replacements;
   - multi-edit schema only when exact files/symbols known;
   - deterministic apply outside model.

3. **True executor deadline instrumentation**
   - remove accidental ~30s observe clamp from end-to-end deadline semantics;
   - `time_to_first_write`;
   - `time_to_first_focused_green`;
   - `time_to_last_useful_evidence`.

4. **Route ledger**

```text
TASK_CLASS
PACKET_FINGERPRINT
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
MODEL
EFFORT
PROFILE
CACHE_STATE
CAPACITY_STATE
FIRST_PASS_ACCEPTED
TTA
CREDITS
SOL_REPAIR_TURNS
CRITICAL_DEFECTS
```

5. **Nearest-similar-task routing** before ML router.

6. **One fallback maximum** and only after new evidence changes route value.

---

## 14.3 ChatWeb Sol

ChatWeb should remain control plane because it naturally owns:

- user conversation;
- changing requirements;
- public/current research;
- architecture decisions;
- cross-workstream synthesis;
- acceptance.

ChatWeb should **not** duplicate Codex repository scanning if MCP has already collected evidence.

Preferred loop:

```text
question
-> cheapest discriminating MCP evidence
-> settle semantics
-> candidate generation only if needed
-> deterministic proof
-> accept
```

For many bugfixes, ChatWeb can construct the patch directly and skip child-model generation entirely.

---

## 14.4 Codex Desktop

Codex Desktop should not be treated as “another reviewer window”.

Best use:

- long coherent implementation lane;
- persistent local code context;
- repeated follow-ups in same semantic workstream;
- substantial refactor/feature where a dedicated code agent session saves ChatWeb context/tool turns;
- user wants direct visibility/control of long code activity.

### Recommended Desktop default

If Desktop is reserved for deep work:

```text
MODEL  = GPT-5.6 Sol
EFFORT = xhigh
```

This is a **simple and defensible default**.

Use `max` manually for consequential hard reasoning.  
Use `ultra` only for explicitly parallelizable large work with budget approval.

### Do not use Desktop history as routine context transfer

Bad:

```text
ChatWeb needs one fact
-> fork entire Desktop history
```

Prior local calibration showed a full history fork can consume ~233K input tokens and ~29 credits for a trivial inherited-context answer.

Prefer:

```text
Desktop lane
-> compact state capsule / selected evidence
-> ChatWeb/MCP
```

`HISTORY` remains manual/exceptional.

---

# 15. Execution policy by task class

| Task class | Primary route | Candidate worker | Deep escalation | Review |
|---|---|---|---|---|
| Search/status/exact transform | MCP only | none | none | none |
| Local bug + known causal patch + strong test | ChatWeb Sol -> MCP | none | none | none |
| Local bug + candidate needed | MCP localize | Mini low patch-only | Luna high; Sol xhigh only if semantic | deterministic oracle |
| Bounded medium semantic leaf | ChatWeb/MCP | Luna high patch-only | Sol xhigh | Mini/Luna blind review only if proof gap |
| Cross-file settled-interface implementation | ChatWeb Sol owns contract | Terra high **gated** or Desktop Sol xhigh | Sol xhigh | deterministic affected-boundary gate |
| High integration / architecture | ChatWeb Sol | no cheap writer by default | Desktop Sol xhigh | optional independent Terra critical review |
| Finance/auth/privacy/data boundary | ChatWeb Sol | no Luna ownership | Sol xhigh/max | independent bounded review + invariant proof |
| Long coherent project lane | ChatWeb Sol checkpoints | Codex Desktop Sol xhigh | max if needed | Sol integration |
| Truly parallel independent workstreams | Sol centralized orchestrator | bounded heterogeneous lanes | Ultra only when justified | centralized merge/proof |

---

# 16. Review plane must remain separate from execution plane

Recommended review ladder remains:

```text
NONE
  |
  +-> PACKET Mini low
  |
  +-> SCOPED Luna when repo inspection is necessary
  |
  +-> CRITICAL Terra for distinct consequential ambiguity
  |
  +-> SOL_LOCAL = existing ChatWeb Sol
  |
  +-> HISTORY explicit only
```

This is **not a mandatory sequence**.

Examples:

- Mini generated patch + deterministic tests may need no model review.
- Desktop Sol xhigh implementation may receive Terra independent review for a financial invariant.
- ChatWeb Sol architecture decision may need no external review when deterministic evidence already proves it.

Do not spawn second external Sol reviewer by default. Homogeneous duplication has low information diversity and high cost.

---

# 17. Parallelism policy

## Stay single-lane when

- one mutation surface;
- high seriality;
- every tool result changes next decision;
- shared interfaces unsettled;
- writers overlap;
- oracle weak;
- integration/review is already bottleneck.

## Parallelize when

- workstreams are genuinely independent;
- write ownership is disjoint or isolated worktrees exist;
- base/interfaces pinned;
- each worker has objective proof;
- Sol can review outputs without becoming bottleneck.

Recommended initial concurrency:

```text
1 primary lane
+ at most 1 independent reviewer/evidence lane
```

Increase only after recent packets are accepted cleanly.

Do not invoke Ultra simply to obtain parallelism when ordinary two-lane orchestration is sufficient.

---

# 18. Cache and session strategy

Local prior calibration showed direct continuation can be dramatically cheaper when semantic continuity is real: a Mini continuation previously reached ~95% cached input and ~0.026 estimated credits.

Therefore:

### Reuse thread when

- same task;
- same invariant;
- same repo/base;
- direct correction/follow-up;
- no independent-review requirement.

### New thread when

- distinct blind review;
- changed base/interface;
- stale assumptions;
- unrelated task.

### Stable prefix

Keep stable:

- safety instructions;
- output schema;
- profile rules;
- invariant format.

Send only evidence delta on continuation.

Do not keep stale context just to save cache cost.

---

# 19. Capacity policy

Observed locally:

- Luna/Terra have returned `serverOverloaded` multiple times;
- Phase 2 Terra high had 2 capacity failures in 3 autonomous attempts.

Production rule:

```text
capacity error
-> record model cooldown
-> do not retry unchanged
-> if exactly one alternative route has positive expected value, use it
-> otherwise return to ChatWeb Sol
```

Capacity is operational reality and must affect router choice even though it is not intrinsic model intelligence.

---

# 20. Cost model

Optimize:

```text
EXPECTED_ACCEPTED_COST =
    generation_cost
  + evidence_collection_cost
  + validation_cost
  + review_cost
  + P(failure) * repair/escalation_cost
  + latency_penalty
  + integration_cost
```

Do not optimize:

```text
cheapest first model call
```

Phase 1 already showed cheap failed calls can make Luna policy cost worse than Terra per accepted result.

Phase 2 shows the complementary result:

> Once packet quality is high enough, lower-cost models can match Sol on bounded leaves and become genuinely cheaper accepted-result routes.

Thus **packet quality is the variable that flips the economics**.

---

# 21. Comparing three production strategies

## Strategy A — Simple deep-lane xhigh

```text
ChatWeb Sol + MCP for almost everything
Codex Desktop Sol xhigh only for deep work
No automatic Mini/Luna/Terra implementation
Mini allowed only as reviewer if desired
```

### Pros

- operationally simple;
- high quality ceiling;
- minimal routing mistakes;
- Desktop config easy to understand;
- low orchestration complexity.

### Cons

- leaves that require candidate generation pay excessive Sol cost;
- wastes evidence that Mini/Luna can solve bounded packets cheaply;
- less throughput when many small tasks arrive.

### When to choose

- volume of delegated candidate generation is low;
- engineering simplicity matters more than model credits;
- workload is mostly high-risk/high-integration;
- team does not want a dynamic internal model router yet.

### Verdict

**Safe/simple option; not cost-optimal.**

---

## Strategy B — Adaptive bounded router (recommended)

```text
ChatWeb Sol control
  |
MCP deterministic
  |
  +-> known patch: apply/test
  |
  +-> bounded candidate:
       Mini low patch-only
       Luna high when packet harder
       Sol xhigh when semantics/risk justify
  |
Desktop Sol xhigh for long/deep lane
  |
Sol acceptance
```

### Pros

- best fit with Phase 2 evidence;
- low leaf cost;
- preserves Sol quality where needed;
- avoids autonomous agent-loop tax;
- keeps Ultra out of routine path;
- compatible with compact MCP surface.

### Cons

- requires good packet builder;
- requires route ledger/telemetry;
- needs abstain/blocked behavior, not forced answer;
- more implementation complexity than xhigh-only.

### Verdict

**Recommended target architecture.**

---

## Strategy C — Full model ladder / autonomous workers

```text
Luna -> Terra -> Sol -> max -> Ultra
```

### Verdict

**Reject.**

Reasons:

- Phase 1 cascade latency penalties;
- MTRouter favors fewer model switches;
- Google research shows coordination tax on sequential tasks;
- current Terra capacity volatility;
- Ultra changes topology and may multiply cost;
- same discovery is repeated across models.

---

# 22. Recommended route pseudocode

```text
finish = define_acceptance_and_invariants()
proof = cheapest_authoritative_oracle(finish)
evidence = MCP.localize_once(proof)

if no_fresh_model_judgment_needed(evidence):
    MCP.execute_and_prove()
    return SOL_ACCEPT

risk = classify_risk(evidence)
width = integration_width(evidence)
seriality = task_seriality(evidence)
packet = build_bounded_packet(evidence)

if packet.quality < REQUIRED:
    return CHATWEB_SOL   # fix localization, not model tier

if localized(packet) and strong_oracle(proof) and cheap_revert:
    if route_ledger.supports("mini-low-patch-only", task_class):
        candidate = MINI_LOW_PATCH_ONLY(packet)
    else:
        candidate = CHATWEB_SOL_OR_LUNA_EXPERIMENT(packet)

    if candidate.blocked_or_uncertain and one_fallback_has_positive_value:
        candidate = LUNA_HIGH_PATCH_ONLY(packet_with_delta)

    if candidate.blocked_because_semantics_are_hard:
        return CHATWEB_SOL_OR_CODEX_SOL_XHIGH

    MCP.apply(candidate)
    if proof.green and adjacent_risk_ok:
        return SOL_ACCEPT
    return SOL_REPAIR

if width == MEDIUM and interfaces_settled:
    if terra_class_ledger_is_promoted and capacity_ok:
        isolated = TERRA_HIGH_WORKTREE(packet)
        grade_external(isolated)
    else:
        return CHATWEB_SOL_OR_DESKTOP_SOL_XHIGH

if width == HIGH or risk == CRITICAL or semantics_unsettled:
    CHATWEB_SOL_OWNS_DECISION()
    if deep_independent_code_lane_has_positive_value:
        CODEX_DESKTOP_SOL_XHIGH()

if xhigh_is_underproven_for_consequential_question:
    SOL_MAX()

if task_has_true_parallel_workstreams and explicit_budget and ultra_expected_value_positive:
    SOL_ULTRA()
```

---

# 23. Proposed reasoning-effort policy

## Mini

- `low` for packet review/candidate generation.
- Do not increase effort by default; if Mini struggles, classifier should usually change tier rather than inflate effort.

## Luna

- `high` for narrow candidate generation after Phase 2 evidence.
- Not owner of finance/auth/privacy/public-contract semantics.

## Terra

- `high` for future scoped cross-file experiment.
- `xhigh` only when class-specific data shows quality gain.
- Current runtime evidence is insufficient for promotion.

## Sol

### `xhigh`

**Recommended default deep Codex tier.**

Use for:

- difficult bounded implementation;
- long coherent Desktop lane;
- high-integration reasoning support;
- complex debugging where ChatWeb needs a separate deep code lane.

### `max`

Use only when:

- consequential decision;
- xhigh answer remains materially under-proven;
- added reasoning can change acceptance.

### `ultra`

Use only when:

- explicit parallel decomposition;
- multiple independent workstreams;
- merge/review capacity exists;
- budget explicitly allows it;
- ordinary centralized 1–2 lane orchestration is insufficient.

Do not use Ultra for:

- one-file repair;
- routine review;
- sequential debug loop;
- poor packet localization;
- “just to be safe”.

---

# 24. Why Sol xhigh is the right deep default, not Ultra

The case is cumulative:

1. Official OpenAI: Ultra is multi-agent/parallel workstream mode.
2. Google Research: multi-agent gains depend strongly on task parallelizability; sequential workflows can degrade heavily.
3. Local Phase 2: bounded leaf quality is already saturated by Mini/Luna/Sol-xhigh after localization.
4. Local effort calibration: xhigh/max/ultra all accepted T06; no quality evidence favored Ultra.
5. Field issue #35177 reports extreme Ultra spend in some Codex workloads; anecdotal but relevant operational warning.
6. Sol xhigh keeps a single coherent reasoning lane and avoids nested swarm risk.

Therefore:

> `Sol xhigh` should be the highest **routine** Codex effort in the proposed system.

Max and Ultra are exception modes.

---

# 25. Security and mutation boundaries

## ChatWeb/MCP

- MCP remains authoritative filesystem gateway.
- Deterministic patch apply preferred.
- Existing dirty worktree changes never overwritten/reset.

## Internal reviewers

- read-only;
- network disabled;
- approval never;
- no repository tools for packet profile.

## Candidate generation

- candidate text only by default;
- deterministic MCP applies replacement;
- model does not get arbitrary shell/write unless explicit isolated executor lane.

## Writable external executor

Only when:

- isolated worktree;
- exact write ownership;
- base fingerprint pinned;
- one attempt;
- deadline;
- external grading;
- no merge/rebase/reset/clean authority.

---

# 26. Codex Desktop session policy

Use Desktop persistent lane by **semantic continuity**, not worker identity.

Keep session when:

- same feature/refactor;
- same interfaces;
- follow-up probability high;
- reusable environment/context substantial.

Roll over when:

- base changed materially;
- interface assumptions changed;
- repeated stale-context corrections;
- workstream finished;
- new task is independent.

Before rollover, externalize compact state:

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

Do not replay full Desktop transcript through MCP unless historical reasoning itself is required evidence.

---

# 27. Promotion gates

No route is promoted globally from 3–4 successes.

A cheaper route needs class-specific paired evaluation with:

1. same quality floor as Sol;
2. strong external oracle;
3. enough representative samples to establish a conservative lower success bound;
4. no critical invariant miss;
5. accepted-result TTA improvement, not just first-token speed;
6. expected credits including failed attempts lower than current route;
7. no increase in Sol repair/integration workload;
8. acceptable capacity behavior;
9. stable result after runtime/model release change.

### Immediate status

- Mini-low patch-only: **PROMISING / experimental**.
- Luna-high patch-only: **PROMISING / experimental**.
- Sol-xhigh patch-only: **VALID deep escalation**, expensive for routine leaves.
- Terra-high autonomous: **NOT PROMOTED**.
- Sol-xhigh autonomous narrow-task loop: **NOT PROMOTED**.
- Sol-max: **exception only**.
- Sol-ultra: **explicit parallel exception only**.

---

# 28. What should be implemented next — only after approval

## P0 — packet quality

Build symbol-aware localization and an `INSUFFICIENT_PACKET` state.

A worker must be able to abstain without penalty when required source is not in packet.

## P1 — internal candidate profile

Add hidden internal `candidate_patch` capability:

```text
PROFILE = patch_only
TOOLS = none
WRITE = none
OUTPUT = structured exact edit(s)
DEFAULT = Mini low
```

MCP applies and grades candidate.

## P2 — candidate escalation

```text
Mini low
  -> only if blocked/uncertain due reasoning, one fallback:
Luna high
  -> if shared/high-risk semantics exposed:
return to ChatWeb Sol
  -> optional Codex Sol xhigh deep lane when independently useful
```

No Terra hop in this leaf path.

## P3 — fix executor telemetry

- true deadline semantics beyond 30s observe bound;
- time-to-first-write;
- time-to-first-green;
- per-command timestamps;
- candidate diff fingerprint.

## P4 — route ledger

Use nearest recent similar task before any learned router.

## P5 — Desktop xhigh deep-lane convention

Document that Desktop is a deep persistent lane, default Sol xhigh, not universal routine executor.

## P6 — separate Terra cross-file study

Run 6–10 genuinely cross-file tasks with 2–3 repetitions after deadline instrumentation is fixed.

Do not use localized one-line mutations to decide Terra’s long-context value.

## P7 — only then update `sol-lean-codex`

Skill changes should encode **demonstrated** routing, not aspirational model hierarchy.

---

# 29. Proposed final operating modes

## Mode 1 — FAST / routine

```text
ChatWeb Sol
+ deterministic MCP
REVIEW=NONE unless proof gap
```

## Mode 2 — CHEAP CANDIDATE

```text
MCP localizes
-> Mini low patch-only
-> MCP proof
-> Sol accepts
```

## Mode 3 — HARDER LEAF

```text
MCP localizes
-> Luna high patch-only
-> MCP proof
-> Sol accepts
```

## Mode 4 — DEEP

```text
ChatWeb Sol controls semantics
-> Codex Desktop/App Server Sol xhigh
-> isolated/coherent code lane
-> MCP/proof
-> Sol integrates
```

## Mode 5 — CRITICAL

```text
ChatWeb Sol owns decision
-> Sol xhigh deep support
-> max only if xhigh under-proven
-> independent review only if distinct evidence value
```

## Mode 6 — PARALLEL EXTREME

```text
Ultra only when task decomposition is genuinely parallel
+ explicit cost budget
+ centralized Sol acceptance
```

---

# 30. Decision matrix

| Dimension | Mini low | Luna high | Terra high | Sol xhigh | Sol max | Sol ultra |
|---|---|---|---|---|---|---|
| Local bounded candidate | **Best cost candidate** | strong fallback | unnecessary | overkill usually | no | no |
| Local autonomous shell loop | not target | avoid | avoid | avoid | avoid | avoid |
| Cross-file implementation | no | limited | experimental | **deep safe candidate** | exception | only if parallel |
| Architecture/shared semantics | no | no | reviewer/support | **yes** | yes if hard | only if parallel |
| Finance/auth/privacy ownership | no | no | independent review | **yes** | yes | rarely |
| Blind packet review | good | good if harder | critical review | expensive duplicate | no | no |
| Long persistent Desktop lane | no | no | possible worker | **recommended** | occasional | explicit only |
| Cost sensitivity | best | good | medium | expensive | expensive | potentially very expensive |
| Current local Phase-2 patch evidence | 4/4 | 4/4 | n/a | 3/3 common; T10 timeout | 1/1 T06 | 1/1 constrained T06 |

---

# 31. Decision confidence

## High confidence

- keep ChatWeb Sol as authority;
- keep compact MCP surface;
- avoid serial model ladder;
- avoid Ultra as default;
- packet quality/localization is critical;
- narrow autonomous shell loops are poor topology in current bridge;
- xhigh is a better routine deep ceiling than Ultra.

## Medium confidence

- Mini-low patch-only should become experimental first candidate;
- Luna-high patch-only is a useful fallback/stronger leaf.

Needs larger paired suite before auto promotion.

## Low / unresolved confidence

- Terra-high/xhigh exact cross-file sweet spot;
- Sol xhigh vs max quality delta on truly hard tasks;
- native Ultra value/cost on this repository’s genuinely parallel workloads.

These require different task classes, not more repetitions of one-line mutations.

---

# 32. Final recommendation before production change

### Recommended architecture to approve

```text
CONTROL / ACCEPTANCE
    ChatWeb GPT-5.6 Sol

DETERMINISTIC PLANE
    Coding Tools MCP

LOCAL CANDIDATE PLANE
    Mini low patch-only first
    Luna high patch-only when harder

DEEP CODE PLANE
    Codex Desktop / App Server GPT-5.6 Sol xhigh

CROSS-FILE EXPERIMENT
    Terra high only when class-specific telemetry supports it

REASONING ESCALATION
    Sol max only after xhigh is materially under-proven

MULTI-AGENT EXTREME
    Sol ultra explicit-only, parallelizable workstreams, budget gate

FINAL ACCEPTANCE
    ChatWeb Sol + deterministic evidence
```

### Recommended “simple configuration” if operational simplicity is preferred

```text
ChatWeb Sol + MCP for routine work
Codex Desktop always Sol xhigh for deep work
No automatic Terra/Luna autonomous executors
Mini/Luna only hidden packet candidates/reviewers
```

This retains almost all architectural safety while avoiding the cost of making Sol xhigh handle every tiny candidate packet.

### Do not approve

```text
all Codex calls = Sol xhigh
```

because local Phase 2 shows leaf candidate cost can be ~5x Luna and ~8x Mini with no acceptance gain on the common tested packets.

### Do not approve

```text
Luna -> Terra -> Sol -> Ultra cascade
```

because both local Phase 1 and external routing research indicate model-switching/coordination overhead can erase theoretical savings.

---

# 33. What would change after approval

If this document is approved, the next implementation should be intentionally narrow:

1. add symbol-aware packet builder;
2. add hidden patch-only candidate profile;
3. start with Mini low **experimental, telemetry-only promotion gate**;
4. Luna high as one fallback only for model-reasoning insufficiency;
5. keep Sol xhigh as deep Desktop/App Server lane;
6. keep Terra autonomous disabled by default;
7. keep max/ultra manual/explicit;
8. add route ledger + first-write/first-green telemetry;
9. update `sol-lean-codex` only after the runtime contract is proven;
10. run a separate cross-file study before Terra promotion.

No production routing change should be made solely because a model has a better public benchmark score. Local route evidence and task topology remain the deciding signals.

---

# 34. References

## Official OpenAI

1. OpenAI. **GPT-5.6: Frontier intelligence that scales with your ambition.** 2026-07-09.  
   https://openai.com/index/gpt-5-6/

2. OpenAI. **Previewing GPT-5.6 Sol: a next-generation model.** 2026-06-26.  
   https://openai.com/index/previewing-gpt-5-6-sol/

3. OpenAI Codex rate card / current GPT-5.6 pricing as observed 2026-08-12. Pricing must be re-checked before future cost-policy changes.

## Scientific / peer-reviewed / preprint

4. Kim, Y. et al. **Towards a Science of Scaling Agent Systems: When and Why Agent Systems Work.** Google Research, 2026.  
   https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

5. Zhang, Y. et al. **MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings.** ACL 2026. DOI 10.18653/v1/2026.acl-long.2045.  
   https://aclanthology.org/2026.acl-long.2045/

6. Varangot-Reille, C. et al. **Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient.** EACL 2026. DOI 10.18653/v1/2026.eacl-srw.22.  
   https://aclanthology.org/2026.eacl-srw.22/

7. Li, H. et al. **LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing.** Findings ACL 2026. DOI 10.18653/v1/2026.findings-acl.1881.  
   https://aclanthology.org/2026.findings-acl.1881/

8. Liu, M. M. et al. **ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering.** ACL 2026. DOI 10.18653/v1/2026.acl-long.1573.  
   https://aclanthology.org/2026.acl-long.1573/

9. Li, C. et al. **Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework (RETRACE).** arXiv:2608.08950, 2026.  
   https://arxiv.org/abs/2608.08950

10. Wang, Y.; Pradel, M.; Liu, Z. **Are ‘Solved Issues’ in SWE-bench Really Solved Correctly? An Empirical Study.** arXiv:2503.15223.  
    https://arxiv.org/abs/2503.15223

11. Yang, Y. et al. **Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity.** arXiv:2602.03794, 2026.  
    https://arxiv.org/abs/2602.03794

12. Uddin & Bauer. **Conformal LLM Routing with Distribution-Free Safety Guarantees.** ACL 2026 SRW.  
    https://aclanthology.org/2026.acl-srw.70/

## Field / operational discussions — anecdotal, not controlled evidence

13. openai/codex #34388 — Smart Mode for model/reasoning-effort selection.  
    https://github.com/openai/codex/issues/34388

14. openai/codex #34278 — per-thread Auto routing model + effort.  
    https://github.com/openai/codex/issues/34278

15. openai/codex #20855 — Reasoning Gearbox.  
    https://github.com/openai/codex/issues/20855

16. openai/codex #8649 — Auto reasoning effort.  
    https://github.com/openai/codex/issues/8649

17. openai/codex #35177 — user-reported Ultra subagent/cost behavior; **treat as unverified field report**.  
    https://github.com/openai/codex/issues/35177

---

# 35. One-sentence policy

> **Use ChatWeb Sol to decide, MCP to localize/execute/prove, Mini/Luna to cheaply generate or independently verify bounded packets, Codex Sol xhigh as the routine deep-work ceiling, and Max/Ultra only when new evidence proves their additional reasoning or parallel topology has positive expected value.**
