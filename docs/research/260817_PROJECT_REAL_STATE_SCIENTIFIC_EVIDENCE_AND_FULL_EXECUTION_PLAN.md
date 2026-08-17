# Coding Web — Thực Trạng Thực Tế, Phân Tích Số Liệu, Phương Pháp Luận Khoa Học Và Kế Hoạch Xử Lý Toàn Bộ

## Evidence-led assessment of accepted engineering outcome, server-first compute, routing economics, recovery/release closure và Solution Economics

**Ngày đánh giá:** 2026-08-17
**Giờ chốt số liệu:** khoảng 20:21 ICT (Asia/Bangkok)
**Repository:** `uyenthudao2410-code/Tools-Codex-web`
**Workspace vận hành lịch sử:** `E:\DEV\Tools-Codex-web` / `E:\Github\Tools-Codex-web`
**Remote `main` HEAD quan sát mới nhất:** `4fa7d6591dcce0fd76e62508ac4b58c3149c3f36`
**Source release-candidate HEAD đã được full code/test gate accept:** `1516f0e5ebcf4086376bb5d144c5e70bbfcf383b`
**Product:** `web-mcp-assistant 0.3.4`
**Canonical causal audit:** `.coding-tools/orchestration/ledger.sqlite3`
**Current performance projection:** `.coding-tools/performance.json` schema v5
**Loại tài liệu:** current-state scientific audit / quantitative assessment / causal methodology / remediation & rollout plan
**Tài liệu này supersede cho quyết định hiện tại:** các snapshot cũ vẫn giữ giá trị lịch sử, nhưng không được dùng thay source/evidence mới hơn.

---

# 0. Executive verdict

## 0.1 Kết luận ngắn nhất

Coding Web hiện **không còn ở giai đoạn xây nền tảng execution/orchestration**. Các phần khó về authority, EOCL, Recovery, exact-source packaging, managed-process ownership, LSP resource governance và server-first source identity đã đi rất xa.

Điểm nghẽn chính đã chuyển từ **code gate** sang **evidence/economics gate**:

> **Hệ thống đã có nhiều primitive để làm đúng việc, nhưng chưa có đủ paired causal evidence để chứng minh rằng các policy mới thực sự tạo accepted code nhanh hơn, rẻ hơn và ít rework hơn.**

Nói cách khác:

```text
Architecture readiness        HIGH
Authority / safety            HIGH
Recovery / release proof      HIGH, còn final closure
Measurement infrastructure    MEDIUM-HIGH
Measurement completeness      MEDIUM-LOW
Paired causal evidence        VERY LOW
Server-first ROI evidence     VERY LOW
Adaptive model-routing proof  VERY LOW
Solution Economics runtime    RESEARCH / NOT YET
```

Không nên hiểu các mức trên như phần trăm completion. Đây là maturity classification dựa trên loại bằng chứng đã tồn tại.

## 0.2 North Star không thay đổi

Mục tiêu chính thức:

> **Coding Web tự động phối hợp trí tuệ của ChatWeb với toàn bộ tài nguyên compute sẵn có để tạo accepted code nhanh nhất và rẻ nhất, trong khi máy người dùng chỉ chịu những workload thực sự cần chạy tại đó.**

Đích tối ưu là:

```text
accepted engineering outcome
```

không phải:

```text
model call rẻ nhất
CPU utilization cao nhất
cache hit nhiều nhất
LOC ít nhất
worker nhiều nhất
build nhanh nhất
server offload ratio cao nhất
```

## 0.3 Ba kết luận định lượng quan trọng nhất

### Kết luận A — Rework vẫn là leverage lớn nhất

Cohort ngày 2026-08-16 gồm 188 accepted ChatWeb+MCP organic runs cho thấy:

- first-pass accepted: `130/188 = 69.15%`;
- repaired accepted: `58/188 = 30.85%`;
- first-pass TTA p50: `36.357 s`;
- repaired TTA p50: `192.319 s`;
- repaired median penalty: **5.29x**.

Một cohort hậu activation khác, snapshot ngày 2026-08-17, có 122 organic accepted runs:

- first-pass: `73/122 = 59.8%`;
- repaired: `49/122 = 40.2%`.

Hai cohort **không đồng nhất về thời gian, task mix và inclusion rule**, nên không được kết luận causal regression. Tuy nhiên, chúng cùng chỉ ra một vấn đề chắc chắn:

> **Repair/replan đủ lớn để mọi optimization giảm vài giây execution trở thành thứ yếu nếu nó làm tăng xác suất phải sửa lại.**

### Kết luận B — Wait/orchestration vẫn lớn hơn compute thuần

Projection mới nhất trên `main`:

- `local_execution_ms = 27,341,654` ≈ **7.59 giờ**;
- `estimated_wait_ms = 89,805,578` ≈ **24.95 giờ**;
- wait/local-execution ratio ≈ **3.28x**.

Điều này không chứng minh toàn bộ 24.95 giờ là model latency. `estimated_wait_ms` là projection tổng hợp và phải giữ provenance. Nhưng nó đủ để bác bỏ giả thuyết đơn giản:

> “Muốn nhanh hơn thì chỉ cần máy server mạnh hơn.”

Nếu queue/round-trip/context/review/replan chi phối critical path, tăng CPU có thể không thay TTAR đáng kể.

### Kết luận C — Adaptive model routing chưa có dữ liệu production đủ dùng

Projection mới nhất:

```text
route_resolved_counts:
  deterministic = 1796
  mini          = 1
  luna          = 4
  terra         = 3
  sol_xhigh     = 4
```

Tổng route-resolved sample trong projection: 1,808.

- deterministic share ≈ **99.34%**;
- các non-deterministic route cộng lại chỉ 12 sample.

Execution modes:

```text
mcp_only           = 2913
bounded_candidate  = 5
deep_single_lane   = 13
auto               = 7
```

`mcp_only` ≈ **99.15%** số execution-mode observations.

Do đó, việc `execution_route=auto` vẫn fail-closed về deterministic là **đúng về khoa học**, không phải thiếu tính năng.

---

# 1. Evidence boundary và độ tin cậy

## 1.1 Thứ tự nguồn sự thật

Tài liệu này áp dụng thứ tự:

1. **Source implementation + exact tests + live/runtime evidence cho cùng fingerprint**.
2. **EOCL ledger và generated run/wave reports**.
3. `.coding-tools/performance.json`, `.coding-tools/task-state.json` và các projection khác.
4. `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`.
5. Dated research documents.
6. External papers/projects chỉ dùng để định hình phương pháp, không thay project evidence.

## 1.2 Giới hạn live evidence tại thời điểm viết

Trong phiên đánh giá hiện tại, ChatWeb gọi trực tiếp Coding MCP:

```text
workspace_context
```

và nhận:

```text
UNKNOWN
ExceptionGroup: unhandled errors in a TaskGroup
```

Điều này là **một live operational observation mới**, chưa được root-cause trong source và chưa được phép suy diễn thành regression của toàn Runtime.

Hệ quả phương pháp luận:

- không dùng Coding MCP hiện tại để giả vờ có live workspace snapshot;
- dùng latest pushed `main`, committed EOCL reports/projections và direct session observation;
- mọi claim “đang chạy live tốt” sau thời điểm lỗi trên phải được re-verify khi MCP truth plane trở lại;
- lỗi này trở thành P0 remediation trước wave triển khai lớn tiếp theo.

## 1.3 Các số liệu có mốc thời gian khác nhau

Ba lớp số liệu phải tách:

### A. Current committed projection

`.coding-tools/performance.json` tại remote `main`, đã tích lũy tới release-closure sequence ngày 2026-08-17.

### B. Latest detailed ledger audit snapshot

`docs/research/260817_PROJECT_STATE_AND_REMAINING_ISSUES_ASSESSMENT.md` tại HEAD `3a3abaff` ghi:

- total runs: 471;
- accepted: 272;
- pair-tagged: 0;
- controller `started_at`: 0;
- controller monetary cost: 0;
- quality outcome events: 0;
- observation span events: 11;
- organic post-activation accepted: 122.

Sau HEAD đó, project đã có thêm nhiều accepted/release runs. Vì live ledger hiện không truy vấn được qua Coding MCP, **471/272 không được trình bày như current final count**; nó là latest exact ledger count đã audit được trong committed report.

### C. Current release-task projection

`.coding-tools/task-state.json` trên latest `main` đang giữ run:

```text
run_id: 59b40e0a67694ad59385227f6dcfc4d4
wave_id: 930e152321ca4d19b89d0c300a9cb6b0
orchestration_state: ACCEPTING
execution_mode: mcp_only
route_requested: deterministic
route_resolved: deterministic
base_head: 1516f0e5ebcf4086376bb5d144c5e70bbfcf383b
```

Đây là bằng chứng rằng final Windows artifact build đã xanh nhưng EOCL projection được commit khi còn **Awaiting acceptance**.

---

# 2. Current architecture: phần nào thực sự đã đóng

## 2.1 Authority và control plane

Đã có và nên coi là settled architecture:

- ChatWeb/Sol = semantic controller + final acceptance trong coordinated topology;
- one Coding Tools Runtime = deterministic workspace writer/oracle;
- Electron/Recovery Host = lifecycle + secret owner;
- Codex Desktop = thin client/proxy vào cùng authority, không phải peer writer;
- Codex App Server/OpenCode = secondary candidate/review/read-only lanes;
- controller ownership khác write lease;
- EOCL RUN/WAVE state machine;
- explicit REPLAN/BLOCKED/ABORTED;
- proof fingerprint + acceptance checkpoint;
- process ownership/quiescence/fencing.

Không có bằng chứng hiện tại biện minh cho việc thiết kế lại các primitive này.

## 2.2 Smart-v3 tool surface

Contract production vẫn là 8 public tools:

```text
workspace_context
agent_workflow
task_control
document_workflow
exec_command
command_control
request_permissions
view_image
```

Không nên thêm tool thứ 9 chỉ để expose server/model/node lựa chọn. Placement/routing phải là internal control concern.

## 2.3 LSP/resource hardening

P2/P3 resource hardening đã đóng kỹ thuật:

- process identity;
- current/peak working set;
- pressure states;
- cold restart identity;
- reaper/drain/restart counters;
- managed HEAVY admission;
- live Connector/Runner/rust-analyzer soak;
- 10-cycle acceptance;
- host-scoped p95 LSP peak dưới ~30 MiB trong acceptance window;
- giữ soft/hard defaults 2 GiB/3 GiB.

Điều quan trọng:

> **Resource stability đã đóng không đồng nghĩa semantic localization efficiency đã tốt.**

Đây là hai research questions khác nhau.

## 2.4 Recovery

Đã có:

- headless Recovery Host;
- Windows Recovery Supervisor;
- independent Recovery MCP;
- independent Recovery Tunnel khi configured;
- bounded recovery actions;
- device-aware identity;
- exact-source packaged Recovery lane;
- installed current-session Recovery Supervisor acceptance;
- rollback evidence.

Current-session installed acceptance đã được checkpoint.

Không được suy diễn thành reboot/logon persistence nếu boundary đó chưa được test đúng nghĩa.

## 2.5 Server-first source contract

Commit `55a00cf04726298c787b18be36c1764408bf9b39` đã đưa server-first vượt khỏi nghiên cứu thuần:

- `ComputeSourceMode::CleanHead`;
- `ComputeSourceMode::SourceSnapshot`;
- explicit `server_compute` opt-in;
- capability `source_snapshot_validation`;
- exact base Git HEAD;
- bounded snapshot SHA-256 + entry count;
- snapshot-vs-clean-head mutual semantics;
- old Runner defaults fail-closed;
- source mismatch/drift reason codes;
- tests cho selection/fallback/mismatch.

Điều chưa có là **production ROI evidence**.

---

# 3. Release / packaging thực tế

## 3.1 Recovery packaging blocker đã được phát hiện bằng installed test

Một điểm tích cực về phương pháp: project không chỉ chạy unit test rồi claim release.

Installed acceptance từng phát hiện:

- source Recovery Supervisor SHA-256 khác packaged copy;
- packaged copy thiếu UTF-8 path handling mới;
- Scheduled Task runtime fail dù manifest/executable path nhìn bề ngoài đúng.

Đây là ví dụ tốt cho nguyên tắc:

```text
source proof != package proof != installed runtime proof
```

Sau đó remediation thêm clean-dist + exact packaged resource identity.

## 3.2 Exact-source packaging remediation đã checkpoint

Accepted wave ghi nhận:

- `npm run test:recovery:packaged` exit 0;
- packaged smoke `ok=true`;
- focused build/supervisor tests 13/13;
- 249 allowed resources exact source/package identity;
- `git diff --check` pass;
- ChatWeb checkpoint accepted.

## 3.3 Full release-candidate gate đã accepted

Một final RC proof-only run đã kiểm tra:

- `git diff --check`;
- full Python MCP suite;
- real Recovery process E2E;
- production dependency audit;
- complete root `npm test` suite;
- source-root cleanliness;
- exact fingerprint policy.

Run này đã được ChatWeb accepted tại HEAD `1516f0e5...`.

## 3.4 Final Windows NSIS artifact đã build thành công nhưng projection còn ACCEPTING

Current committed task-state:

```text
objective: build final Windows NSIS release artifact
base_head: 1516f0e5...
state: ACCEPTING
current_step: Awaiting acceptance
```

Build result:

```text
npm run dist
status: passed
exit_code: 0
duration: 79,110 ms
```

Artifact chính:

```text
path: dist/web-mcp-assistant-setup-0.3.4.exe
size: 128,679,189 bytes ≈ 122.72 MiB
SHA-256: 36E51E2EFDC060B540B35D29975BA0D9E34867AAFED5E5C4C56AA854CFF2F38D
```

Supporting artifacts:

```text
dist/latest.yml
  size: 363 bytes
  SHA-256: CF79AD7B0900922B0F7C0BBBE826338E82860390622FAAAB82A75482454CB782

dist/web-mcp-assistant-setup-0.3.4.exe.blockmap
  size: 135,713 bytes
  SHA-256: CC06BCA08066FF20C8C6A80798A7FADB4D35AF9376F1AAF03DB8BE7807505AB5
```

### Release verdict

```text
SOURCE RC              ACCEPTED
FULL CODE/TEST GATE     ACCEPTED
PACKAGE BUILD           PASS
ARTIFACT HASH           RECORDED
EOCL FINAL CHECKPOINT   NOT SHOWN IN COMMITTED TASK STATE
PUBLICATION/UPLOAD      NOT CLAIMED
```

Do đó release closure là P0 immediate action, nhưng không còn là “feature development”.

---

# 4. Quantitative performance projection — số liệu mới nhất

## 4.1 Aggregate counters

Current `.coding-tools/performance.json` schema v5:

| Metric | Current value |
|---|---:|
| Tool calls | 4,154 |
| Errors | 425 |
| Cache hits | 14 |
| Deduplicated calls | 1 |
| Idempotency eligible calls | 2,355 |
| Idempotency key calls | 1,376 |
| Required idempotency calls | 490 |
| Required keyed | 486 |
| Proof-cache eligible | 563 |
| Proof-cache hits | 1 |
| Proof-cache misses | 562 |
| Proof-cache saved time | 996 ms |
| Local execution | 27,341,654 ms |
| Estimated wait | 89,805,578 ms |
| Request bytes | 5,345,614 |
| Raw response bytes | 271,220,412 |
| Model-visible bytes | 7,446,928 |
| Phase timing samples | 389 |
| Localization samples | 290 |
| Localization queries | 1,770 |
| LSP attempted queries | 963 |
| LSP handled queries | 5 |
| Fallback search queries | 1,765 |

## 4.2 Derived metrics

### Aggregate tool error observation rate

```text
425 / 4154 = 10.23%
```

Không được gọi đây là “task failure rate”. Nhiều `VALIDATION`, `AUTHORITY_DENIED`, `USER_BLOCKED` là expected fail-closed behavior.

Error class distribution trong 425 error observations:

| Class | Count | Share of errors |
|---|---:|---:|
| RUNTIME | 163 | 38.35% |
| VALIDATION | 152 | 35.76% |
| UNKNOWN | 43 | 10.12% |
| USER_BLOCKED | 31 | 7.29% |
| AUTHORITY_DENIED | 29 | 6.82% |
| IDEMPOTENCY | 7 | 1.65% |

### Interpretation

Hai nhóm lớn nhất là Runtime + Validation ≈ 74% error observations.

Không nên đặt objective “error_count → 0”, vì validation rejection là safety signal. Nên tách:

```text
expected_guardrail_rejection
recoverable_environment_failure
preventable_runtime_failure
unknown_failure
```

**`UNKNOWN = 43` mới là class cần ưu tiên giảm mạnh** vì nó phá causal diagnosis và recovery routing.

## 4.3 Idempotency compliance

Required calls:

```text
486 keyed / 490 required = 99.18%
```

4 missing được projection ghi là `task_control:accept` với `missing_run`.

Đây là một chỉ số kỹ thuật mạnh: mutation/control path gần như đã tuân thủ current idempotency policy.

Không nên đầu tư architecture lớn hơn ở idempotency trước khi xử lý 4 missing-run path và đo duplicate-side-effect evidence.

## 4.4 Wait vs execution

```text
local execution ≈ 7.59 h
estimated wait  ≈ 24.95 h
ratio           ≈ 3.28x
```

So với snapshot 2026-08-16 (~4.05x), ratio aggregate đã thấp hơn. Nhưng đây **không phải causal improvement claim** vì:

- cumulative window khác;
- task mix khác;
- release/build workloads tăng execution time;
- wait là estimated, không phải homogeneous measured controller latency.

Correct scientific statement:

> **Wait/orchestration overhead vẫn material và lớn hơn local execution aggregate; exact effect theo task class cần paired/critical-path attribution.**

## 4.5 Phase timing

389 phase samples:

```text
workspace_ms       = 158,719
localization_ms    = 1,136,867
materialization_ms = 3,934
total_ms           = 1,910,260
```

Shares trên measured phase total:

- localization ≈ **59.5%**;
- workspace ≈ **8.3%**;
- materialization ≈ **0.2%**.

Remaining measured phase time nằm ở các phase khác/overhead.

Localization vẫn là subsystem đáng tối ưu.

## 4.6 Semantic LSP usefulness vs resource stability

Current counts:

```text
LSP attempted  = 963
LSP handled    = 5
handled rate   ≈ 0.52%
```

Across localization queries:

```text
fallback search = 1765 / 1770 ≈ 99.72%
```

Snapshot ngày 16/08 từng có:

```text
LSP attempted = 161
LSP handled   = 5
```

Tức handled count vẫn là 5 trong khi attempt count tăng mạnh.

Đây là một finding cần tách khỏi P2/P3 memory hardening:

> **LSP đã ổn về lifecycle/resource không có nghĩa nó đang đóng góp đáng kể vào semantic localization throughput.**

Các khả năng cần kiểm định:

1. query mix không phù hợp LSP;
2. provider capability coverage hẹp;
3. adapter fail/unsupported rồi fallback đúng;
4. telemetry counting semantics không phản ánh actual semantic value;
5. LSP warm-state chưa được sử dụng ở task classes cần nó.

Không nên “sửa” bằng cách tăng concurrency trước khi biết nguyên nhân.

## 4.7 Result shaping / context economy

```text
raw response bytes    = 271,220,412
model-visible bytes   =   7,446,928
raw/model-visible     ≈ 36.42x
model-visible/raw     ≈ 2.75%
```

Điều này cho thấy bounded evidence shaping đang làm việc: model không bị nhận toàn bộ raw terminal/tool output.

Nhưng raw plane vẫn phải tạo/xử lý hơn 271 MB. Hai câu hỏi tách biệt:

- model context economy: tương đối tốt;
- tool/runtime serialization/processing economy: còn có thể tối ưu nếu raw generation nằm trên critical path.

## 4.8 Proof cache

```text
eligible = 563
hits     = 1
hit rate ≈ 0.18%
saved    = 996 ms
```

Miss reasons:

```text
input_fingerprint_changed = 288
cold                      = 274
```

Kết luận:

> **Generic proof-cache ROI hiện gần như bằng 0.**

Không nên xây cache subsystem phức tạp hơn chỉ để tăng “hit rate”.

Remote proof portability là problem khác: nếu exact server proof giúp tránh chạy lại local proof, nó phải được đánh giá bằng paired saved TTAR/local burden, không bằng generic cache count.

---

# 5. Rework economics — phân tích sâu

## 5.1 Cohort 188 accepted runs

Cohort định nghĩa trong research 16/08:

- scan 200 recent accepted;
- loại 12 explicit model-route runs;
- còn 188 model-free ChatWeb+MCP accepted.

| Metric | Value |
|---|---:|
| Accepted | 188 |
| First-pass | 130 |
| First-pass rate | 69.15% |
| Repaired | 58 |
| Repaired rate | 30.85% |
| Replan events in repaired | 92 |
| First-pass TTA p50 | 36.357 s |
| First-pass TTA p90 | 212.636 s |
| Repaired TTA p50 | 192.319 s |
| Repaired TTA p90 | 427.723 s |
| p50 multiplier | 5.29x |
| p90 multiplier | 2.01x |

## 5.2 Post-activation organic cohort 122

Snapshot 17/08 tại HEAD `3a3abaff`:

```text
organic accepted >= 2026-08-15T05:58Z = 122
first-pass = 73 (59.8%)
repaired   = 49 (40.2%)
```

Task mix:

```text
feature       43
diagnose      22
bugfix        27
test_failure  10
build_release  9
custom        10
refactor       1
```

## 5.3 Tại sao không được kết luận regression 9.35 pp

Numerically:

```text
59.8% - 69.15% = -9.35 percentage points
```

Nhưng causal claim bị chặn bởi:

- cohort time windows khác;
- workflow distribution khác;
- acceptance selection khác;
- task difficulty chưa normalized;
- source/runtime versions khác;
- cache/order/model capacity khác;
- cohort chỉ chứa accepted runs → survivor selection;
- post-activation cohort có thể chứa release/recovery/concurrency tasks khó hơn.

Do đó đúng về khoa học là:

> **Observed first-pass rate trong cohort mới thấp hơn; cần stratified paired evaluation để phân biệt regression thật với workload-mix shift.**

## 5.4 Why rework remains the central objective

Giả sử một optimization giảm execution stage 20% nhưng làm repair probability tăng.

Vì repaired median TTA ≈ 5.29x first-pass, expected TTAR có thể xấu hơn dù từng build nhanh hơn.

Do đó mọi policy mới phải report:

```text
first_pass_acceptance
repair_probability
repair_cost
TTAR
```

không chỉ:

```text
execution_ms
```

---

# 6. Routing economics thực tế

## 6.1 Tình trạng kỹ thuật

Runtime đã có explicit routes:

```text
deterministic
mini
luna
terra
sol_xhigh
sol_max
sol_ultra
```

`auto` hiện fail-closed về deterministic trong ROI-measurement epoch.

Đây là policy hợp lý vì sample hiện tại quá lệch.

## 6.2 Không thể học router từ current route distribution

Non-deterministic samples trong projection mới nhất:

```text
Mini      1
Luna      4
Terra     3
Sol xhigh 4
```

Ngay cả khi tất cả đều thành công, n quá nhỏ để ước lượng:

- acceptance probability;
- TTAR distribution;
- failure modes;
- cost distribution;
- task-class interaction;
- capacity sensitivity.

## 6.3 Latest exact ledger audit: paired program chưa thực sự chạy

Tại snapshot `3a3abaff`:

```text
pair-tagged runs = 0
controller.started_at = 0
controller.monetary_cost = 0
quality_outcome_recorded = 0
```

Sau snapshot này, host observation binding đã được cải thiện; current JSONL đã có `run_id`/`wave_id` trên một số `assistant_response_first_visible` và `host_turn_span` records.

Điều đó chứng minh **binding mechanism bắt đầu hoạt động**, nhưng không chứng minh paired economics đã đủ sample.

## 6.4 Measurement gaps còn lại

Cần phân biệt:

### Đã có

- pair schema;
- policy/task_class/oracle/provenance fields;
- environment/topology/router identifiers;
- trace/turn IDs;
- host observed spans;
- quality-outcome schema/action;
- replay/evaluation infrastructure;
- critical-path analysis primitives.

### Chưa được chứng minh đủ population

- representative paired runs;
- controller token/cost population;
- quality outcomes population;
- route regret population;
- server/local paired economics;
- lower-tier model cohorts.

---

# 7. Server-first compute — current scientific status

## 7.1 Code status

Server-first không còn là architecture proposal đơn thuần.

Source đã có:

- compute intent;
- resource class;
- placement policy;
- server opt-in;
- runner health/capability data;
- exact clean-head validation;
- source snapshot validation;
- source mismatch/drift guards;
- snapshot identity persisted into job validation metadata;
- read-only/validation-oriented remote selection;
- backward-compatible fail-closed capability defaults.

## 7.2 Điều chưa được phép claim

Chưa có đủ evidence để nói:

- server-first giảm TTAR x%;
- server-first giảm local CPU x%;
- server-first giảm CAR x%;
- remote proof reuse an toàn trên representative workload;
- placement predictor tốt hơn local heuristic;
- automatic server-first nên bật rộng.

## 7.3 Scientific question đúng

Không hỏi:

> “Server chạy cargo được chưa?”

Phải hỏi:

> **Trên task classes đủ điều kiện, server-first có làm giảm expected time/cost to accepted result và local burden mà không làm tăng repair/quality risk không?**

## 7.4 Treatment definition

Baseline:

```text
LOCAL_FIRST_V1
```

Treatment:

```text
SERVER_FIRST_DETERMINISTIC_V1
```

Giữ giống nhau:

- source snapshot;
- task semantics;
- oracle;
- proof policy;
- controller;
- tool contract;
- environment requirements;
- cache stratum label.

Thay đổi duy nhất cần attribution:

```text
compute placement
```

---

# 8. Solution Economics / Ponytail-derived methodology — current status

## 8.1 Research status

Tài liệu `260816_ACCEPTED_ENGINEERING_OUTCOME_SOLUTION_ECONOMICS_METHODOLOGY_AND_IMPLEMENTATION_PLAN.md` đã hoàn chỉnh methodology.

Nhưng hiện chưa có evidence rằng `agent_workflow` production đã áp dụng một `SolutionEconomicsAssessment` như policy bắt buộc.

Do đó trạng thái đúng:

```text
research synthesis      DONE
methodology             DONE
runtime policy          NOT YET
shadow telemetry        NOT YET PROVEN
paired evaluation       NOT YET
production promotion    NOT YET
```

## 8.2 Tại sao cần layer này

Current optimization pipeline thường bắt đầu từ workload đã tồn tại:

```text
workload
-> model route
-> compute placement
-> proof
```

Solution Economics hỏi trước:

```text
workload này có cần tồn tại không?
```

Candidate strategy taxonomy:

```text
NO_CHANGE
REUSE_EXISTING
STDLIB
NATIVE_PLATFORM
EXISTING_DEPENDENCY
SMALL_CUSTOM
STRUCTURED_EXTENSION
ARCHITECTURAL_CHANGE
```

## 8.3 Không được biến thành LOC optimizer

Objective không phải:

```text
minimize lines of code
```

Mà là:

```text
minimize total engineering work
subject to correctness/security/robustness/compatibility/extension-quality floors
```

Vì repaired runs đắt, một patch ngắn nhưng under-defended có thể làm TTAR xấu hơn.

---

# 9. Hàm mục tiêu khoa học thống nhất

## 9.1 Accepted outcome as hard constraint

Một run chỉ accepted nếu:

```text
requested outcome satisfied
+ exact source identity
+ authority valid
+ proof adequate
+ no unresolved hard blocker
+ local-affinity gates passed where required
+ final acceptance recorded
```

## 9.2 TTAR

Định nghĩa:

TTAR = T_context + T_queue + T_transfer + T_execution + T_proof + T_review + T_repair + T_handoff

## 9.3 CAR

CAR = C_controller + C_candidate + C_remote_compute + C_local_opportunity + C_transfer + C_retry + C_review

Không biến unknown cost thành zero.

## 9.4 Local burden

Track ít nhất:

```text
local_cpu_minutes
local_heavy_minutes
local_peak_working_set
memory_pressure_events
disk_busy_windows
interactive_slowdown_events
```

## 9.5 Long-horizon maintenance burden

Solution policy cần thêm:

```text
change_surface
new_public_contracts
new_dependencies
new_configs
new_persistent_state
new_process_boundaries
hotspot_change_frequency
```

## 9.6 Unified objective

Với plan `p`:

J(p) = E[TTAR_p] + lambda_c E[CAR_p] + lambda_l E[LocalBurden_p] + lambda_m E[MaintenanceBurden_p] + lambda_r E[Risk_p]

Nhưng đây là **scoring layer sau hard filters**.

Không score qua:

- security boundary;
- write lease;
- secret locality;
- exact source mismatch;
- incompatible platform;
- destructive-action policy;
- acceptance authority.

---

# 10. Phương pháp luận thực nghiệm chuẩn hóa

## 10.1 Research questions

### RQ1 — Rework

Policy mới có làm tăng first-pass acceptance và giảm expected repair cost không?

### RQ2 — Server-first

Server-first deterministic placement có giảm TTAR/CAR/local burden trên eligible tasks không?

### RQ3 — Solution Economics

Pre-routing minimization có giảm engineering work mà không làm giảm correctness/security/robustness không?

### RQ4 — Model routing

Lower-cost candidate routes có giảm cost per accepted result trên task classes nào?

### RQ5 — Context/localization

Semantic/context plan nào giảm localization/turn cost mà không giảm root-cause accuracy?

### RQ6 — Proof economy

Proof plan nào là cheapest sufficient proof cho từng risk/task class?

## 10.2 Unit of analysis

Primary unit phải là:

```text
one task assignment / one experimental replicate
```

không phải:

```text
one tool call
one wave event
one test assertion
```

Tool-call counters dùng diagnostics, không dùng làm independent samples.

## 10.3 Experimental assignment

Mỗi pair cần cùng:

```text
pair_id
task semantics
source snapshot
oracle_id
environment_id
controller class
risk policy
cache stratum
```

Và khác đúng treatment dimension.

Ví dụ server placement:

```text
A = local-first
B = server-first
```

Ví dụ Solution Economics:

```text
A = current solution policy
B = lean-solution-v1
```

Ví dụ model routing:

```text
A = ChatWeb + deterministic MCP
B = bounded Mini candidate + MCP proof
```

Không thay hai biến cùng lúc rồi attribution cho một biến.

## 10.4 Randomization và order effects

Nếu A và B chạy sequentially:

- randomize A→B / B→A;
- record `order_index`;
- stratify cold/warm cache;
- reset isolated worktree;
- preserve identical task prompt/acceptance oracle;
- record provider capacity failure separately.

## 10.5 Intention-to-treat

Primary analysis phải giữ mọi assigned run:

```text
accepted
failed
blocked
capacity-failed
activation-failed
```

Không chỉ phân tích accepted rows.

Nếu chỉ dùng accepted runs để đánh giá policy, ta tạo survivor bias.

## 10.6 Quality floor trước efficiency

Primary gate order:

1. correctness/security/authority non-inferior;
2. robustness/compatibility non-inferior;
3. first-pass acceptance non-inferior hoặc tốt hơn;
4. sau đó mới TTAR/CAR/local burden.

Một treatment nhanh hơn nhưng làm quality xấu không được promote.

## 10.7 Non-inferiority margins

Không hardcode margin từ paper khác.

Pilot có thể bắt đầu với provisional governance targets:

```text
functional correctness: <= 3 percentage-point degradation
security exploit regression: 0 tolerated
robustness: <= 5 pp degradation
```

Nhưng trước confirmatory study phải calibrate margins theo:

- baseline variance;
- user-visible consequence;
- task class;
- sample size/power.

High-risk auth/security/data-loss tasks dùng stricter gate.

## 10.8 Primary estimands

### Binary quality

```text
Delta_accept = P(accepted|B) - P(accepted|A)
Delta_first_pass = P(first_pass|B) - P(first_pass|A)
Delta_repair = P(repair|B) - P(repair|A)
```

### TTAR

Use within-task log ratio:

```text
D_t = log(TTAR_B,t) - log(TTAR_A,t)
```

Geometric mean ratio dễ diễn giải hơn raw mean khi latency heavy-tailed.

### Cost

Tương tự dùng paired log-ratio khi cost observed. Unknown run phải giữ missingness state, không được đổi thành zero.

## 10.9 Statistical model

### Pilot

10–20 pairs đầu dùng để:

- kiểm tra instrumentation;
- estimate variance;
- estimate failure mix;
- estimate effect order;
- làm power calculation.

Không dùng 10 pairs làm proof production chỉ vì threshold code đang là 10.

### Confirmatory

Tùy dataset:

- paired bootstrap cluster theo task;
- mixed-effects model với random intercept `task_id`;
- logistic mixed model cho accepted/first-pass;
- robust CI cho heavy-tailed TTAR;
- McNemar cho paired binary outcome nếu thiết kế phù hợp.

### Multiple comparisons

Primary family:

- Holm correction.

Exploratory task-class breakdown:

- Benjamini-Hochberg FDR.

Không chọn metric thắng đẹp nhất rồi đưa lên headline.

## 10.10 Power analysis

Final n không ấn định cảm tính.

Procedure:

1. chạy instrumentation pilot;
2. estimate paired log-TTAR SD và binary discordance rate;
3. chọn minimum economically meaningful effect;
4. tính n cho 80–90% power;
5. freeze analysis trước confirmatory run.

## 10.11 Preregistration nội bộ

Trước paid/expensive cohort, commit một experiment manifest:

```yaml
experiment_id:
hypotheses:
primary_metrics:
quality_margins:
task_sampling_frame:
strata:
assignment:
cache_policy:
missing_data_policy:
analysis_script_sha:
promotion_gate:
stop_rule:
```

Điều này chống hindsight tuning và p-hacking.

---

# 11. Causal confounders bắt buộc kiểm soát

## 11.1 Task difficulty

Stratify ít nhất:

```text
localized strong-oracle bug
weak-oracle bug
cross-file semantic change
build/test failure
UI/runtime
recovery/process
security/trust boundary
large-file localization
release/build
```

## 11.2 Cache state

Cold vs warm:

```text
repo mirror
semantic index
dependency cache
compiler cache
model context/cache
```

Không trộn rồi báo một median.

## 11.3 Provider capacity

Capacity flapping là deployed-system effect nhưng cũng là capability confounder.

Report hai view:

```text
capability-conditional quality
real deployed TTAR including capacity
```

## 11.4 Human intervention

Record:

```text
human steering count
manual replan
manual correction
manual retry
```

Không bỏ khỏi cost model.

## 11.5 Policy/harness contamination

Fingerprint:

```text
source
AGENTS/repo instructions
routing policy
solution policy
review policy
tool contract
active hooks/plugins
runtime behavior fingerprint
environment
oracle
```

Một pair mismatch ở non-treatment fingerprint không đủ chuẩn confirmatory.

---

# 12. Measurement plane cần đóng những gì

## 12.1 Host visible latency

Current JSONL đã có các span với `run_id`/`wave_id` ở một số turns.

Cần đưa thành stable ledger population:

```text
user visible start
assistant first visible
bound run/wave
clock domain
navigation epoch
trace_id
turn_id
measurement provenance
```

Không match bằng timestamp proximity.

## 12.2 Controller timing

Cần populate:

```text
controller.started_at
controller visible response end or bound host span
```

Tách:

- observed host-visible latency;
- derived orchestration gaps;
- provider-reported model latency.

## 12.3 Controller usage/cost

Nếu client/provider expose:

```text
input_tokens
cached_input_tokens
output_tokens
reasoning_output_tokens
monetary_cost
source=client_reported|provider_reported
```

Không có thì `unknown`.

## 12.4 Quality outcome

Mỗi accepted experimental run cần:

```text
immediate acceptance outcome
first_pass / repaired
critical defect flag
post-accept observation window
quality_outcome source
```

Delayed production defect phải link lại run nếu có exact provenance.

## 12.5 Routing/placement regret

Sau outcome:

```text
predicted policy score
actual TTAR/CAR/quality
best observed comparable action
regret estimate
```

Chỉ dùng comparable strata; không giả counterfactual từ task khác.

---

# 13. Scientific assessment của từng subsystem

## 13.1 EOCL/authority

**Decision: KEEP.**

Evidence:

- accepted/checkpointed runs;
- explicit replan on base drift;
- exact proof identity;
- process quiescence;
- idempotency compliance cao.

Next work chỉ harden observed failures, không redesign.

## 13.2 Recovery

**Decision: KEEP / CLOSE release boundary.**

Evidence mạnh từ packaged + installed acceptance.

Remaining work chỉ boundary thật:

- reboot/logon nếu release contract yêu cầu;
- production-only fault matrix nếu không thể cover isolation;
- final release provenance.

## 13.3 LSP resource governor

**Decision: KEEP.**

Resource stability proven.

## 13.4 LSP semantic localization benefit

**Decision: REVISE / INVESTIGATE.**

Reason:

```text
5 handled / 963 attempted
```

Không được kết luận provider vô dụng cho mọi case; cần instrumentation audit + task-class analysis.

## 13.5 Generic proof cache

**Decision: HOLD.**

0.18% hit rate, 996 ms saved aggregate hiện không biện minh subsystem expansion.

## 13.6 Server-first exact snapshot contract

**Decision: KEEP / ACTIVATE EXPERIMENTALLY.**

Implementation đã đủ để bắt đầu live paired canary, chưa đủ để broad promote.

## 13.7 Automatic model routing

**Decision: HOLD.**

Non-deterministic sample quá nhỏ, pair population chưa đủ.

## 13.8 Solution Economics

**Decision: SHADOW FIRST.**

Không inject always-on persona. Thu solution-strategy decisions + change surface trước, sau đó A/B.

---

# 14. Full remediation and implementation plan

## Phase P0 — Restore truth plane và đóng release hiện tại

### P0.1 Root-cause Coding MCP TaskGroup failure

**Problem:** current ChatWeb call `workspace_context` trả `ExceptionGroup`.

### Actions

1. Inspect Runtime/Recovery Host logs without restarting blindly.
2. Determine whether failure is:
   - connector session/schema;
   - server TaskGroup lifecycle;
   - stale command/task projection;
   - tunnel/transport;
   - one child operation throwing unhandled exception.
3. Reproduce with smallest read-only tool.
4. Add typed error class; remove `UNKNOWN` wrapper if root cause known.
5. Focused test + live call.

### Acceptance

```text
workspace_context PASS
agent_workflow prepare PASS
no stale/orphaned operation
runtime instance identity known
8-tool contract unchanged
```

### Stop rule

Do not start a new mutation wave while Runtime truth cannot be read reliably.

## P0.2 Reconcile final artifact run

Current run:

```text
59b40e0a67694ad59385227f6dcfc4d4
state = ACCEPTING
```

### Actions

- inspect accepted RC fingerprint;
- verify artifact paths/hash match task-state;
- verify no source drift after build;
- accept or reject explicitly;
- checkpoint EOCL;
- verify quiescence;
- update release control doc.

### Acceptance

```text
CHECKPOINTED
artifact SHA recorded
source base recorded
no mixed-fingerprint proof
no hidden second build required
```

## P0.3 Final release boundary decision

Explicitly decide whether v0.3.4 requires:

```text
installed current-session smoke      already evidenced
fresh login/logon persistence        decision required
reboot persistence                    decision required
production Recovery fault matrix     decision required
publication/upload                    separate action
```

Do not invent requirements after build; record release contract.

---

# 15. Phase P1 — Measurement integrity closure

## P1.1 Re-run current ledger baseline after MCP recovery

Generate one canonical report from **current** ledger:

```text
total runs
accepted/rejected/aborted
first-pass/repaired
TTAR p50/p90
replan counts
failure classes
route counts
pair counts
quality outcomes
controller timing/cost coverage
host-bound span coverage
```

This replaces reliance on 3a3/16-Aug snapshots for ongoing decisions.

## P1.2 Host binding coverage metric

Add/report:

```text
host_spans_total
host_spans_with_run_binding
host_binding_rate
eligible_runs_with_host_span
eligible_run_host_coverage
```

Acceptance for scientific use should target near-complete coverage in controlled experiments, not organic all-history perfection.

## P1.3 Controller usage coverage

Report:

```text
eligible experimental runs
with started_at
with token usage
with monetary cost
```

No promotion economics if cost coverage is materially incomplete.

## P1.4 Quality-outcome population

Start recording on new experimental runs immediately.

For past organic tasks, backfill only when evidence exists; do not infer quality from “accepted” alone.

## P1.5 Error taxonomy cleanup

Target `UNKNOWN`:

```text
43 current aggregate unknown error observations
```

Goal is not zero total errors; goal is typed causal errors.

---

# 16. Phase P2 — Rework diagnosis before adding more routing complexity

## P2.1 Stratified rework report

Use workflow strata from organic cohort:

- feature;
- diagnose;
- bugfix;
- test_failure;
- build_release;
- custom;
- refactor.

For each:

```text
n
first-pass rate
repair rate
replan count
TTAR p50/p90
failure class
scope size
oracle strength
```

## P2.2 Root-cause categories

Classify repair reason:

```text
patch_context_ambiguity
source/base drift
wrong root cause
oracle weakness
environment/workdir
runtime/tool failure
missing requirement
provider/capacity
proof timeout
acceptance correction
```

## P2.3 Countermeasure evaluation

Evaluate existing interventions:

- patch preflight;
- workdir resolution;
- semantic localization;
- exact source;
- recovery fencing;
- solution minimization later.

Each gets baseline/intervention/fresh rerun.

### Promotion criterion

Do not call a remediation effective without a measured reduction in appropriate rework class or TTAR.

---

# 17. Phase P3 — Server-first paired experiment

## P3.1 Scope first cohort

Only tasks with:

```text
read-only or deterministic validation
portable environment
no GUI/device/secret affinity
strong oracle
exact source snapshot
```

Prefer HEAVY tasks where remote benefit can exceed transfer/setup cost.

## P3.2 Metrics

Primary:

```text
accepted rate
first-pass rate
TTAR
```

Secondary:

```text
queue_ms
transfer_ms
execution_ms
proof_ms
local_cpu_minutes
local_heavy_minutes
remote_compute_minutes
fallback rate
placement regret
```

## P3.3 Pilot

10–20 representative pairs.

Use pilot only cho:

- instrumentation validation;
- variance;
- break-even estimate;
- power planning.

## P3.4 Promotion

Auto-placement for a task class only if:

```text
quality non-inferior
TTAR or CAR materially better
or local burden materially lower with acceptable TTAR
fallback safe
source/proof identity exact
sample diversity sufficient
```

Keep class-specific promotion; do not flip global server-first switch.

---

# 18. Phase P4 — LSP semantic-value investigation

## P4.1 Audit 963 attempted vs 5 handled

Sample actual query types and reason codes:

```text
unsupported_query
provider_unavailable
admission_denied
symbol_not_found
protocol_error
fallback_by_design
```

## P4.2 Define usefulness metric

Not `LSP call count`.

Use:

```text
localization TTAR
search/tool hops
context bytes
root-cause accuracy
first-pass acceptance
```

## P4.3 A/B

On symbol-heavy task strata:

```text
A = bounded text fallback
B = semantic-first LSP
```

If B does not improve accepted-result economics, keep LSP as niche capability rather than forcing wider use.

---

# 19. Phase P5 — Solution Economics shadow mode

## P5.1 Do not change implementation behavior yet

At `agent_workflow.prepare`, derive/log:

```yaml
solution_economics:
  solution_class:
  reuse_candidates:
  native_candidates:
  dependency_candidates:
  causal_scope:
  protected_invariants:
  expected_change_surface:
  lean_pressure:
  uncertainty:
```

No public tool.

## P5.2 Change-surface metrics

Record:

```text
files_touched
lines_delta
new_dependency
new_config
new_public_interface
new_persistent_state
new_process
new_protocol_surface
```

LOC remains diagnostic only.

## P5.3 Causal Fix Gate

For bugfix:

- identify touched shared symbol;
- inspect relevant callers when shared-root-cause plausible;
- fix demonstrated root cause;
- avoid per-symptom guards when one shared correction is valid.

## P5.4 Shadow evaluation

Compare recommendation vs actual implementation after acceptance:

```text
predicted solution class
actual change surface
repair outcome
TTAR
```

Use this to tune policy before treatment A/B.

---

# 20. Phase P6 — Solution Economics controlled A/B

## P6.1 Treatment

```text
A = current policy
B = lean-solution-v1
```

## P6.2 Task strata

Must include:

```text
overbuild-opportunity
irreducible
minimal-is-wrong / robustness probes
security-sensitive
brownfield cross-file
recovery/concurrency
input/parser edge cases
UI/native opportunity
```

## P6.3 Primary quality gates

- correctness non-inferiority;
- security zero exploit regression;
- robustness non-inferiority;
- first-pass acceptance.

## P6.4 Efficiency outcomes

Only after no-harm:

```text
TTAR
CAR
model calls
context bytes
proof time
change surface
local/remote compute burden
```

Do not promote from LOC/token reduction alone.

---

# 21. Phase P7 — Model-routing paired cohorts

## P7.1 Baseline

```text
ChatWeb Sol semantic control
+ deterministic MCP writer/oracle
```

## P7.2 Candidate lanes

Evaluate separately:

```text
Mini bounded candidate
Luna bounded candidate
Terra explicit cross-file experiment
Sol xhigh deep lane
```

Do not create serial cascade Mini→Luna→Terra→Sol as default.

## P7.3 Suitable task classes

Mini/Luna only when:

- localized/bounded;
- strong oracle;
- settled semantics;
- small evidence packet;
- candidate-only authority.

## P7.4 Economics

Need provider/controller cost coverage before cost claims.

Primary:

```text
cost per accepted result
TTAR
first-pass
repair
```

## P7.5 Promotion

Class-specific and confidence-gated.

`auto` remains deterministic until evidence gate truly passes.

---

# 22. Phase P8 — Joint model + compute + proof optimization

Chỉ sau P3/P6/P7 có data.

## P8.1 Hierarchical router

Không brute-force all combinations.

```text
1. understand/solution economics
2. semantic route
3. compute placement
4. context plan
5. proof plan
```

## P8.2 Contextual learning

Context candidates:

```text
task_class
integration_width
oracle_strength
risk
solution_class
change_surface estimate
resource profile
cache state
node health
local interactive state
historical route quality
```

Action:

```text
semantic route
compute node class
proof policy
```

Reward:

```text
R = w_a Accepted - w_t log(1+TTAR) - w_c CAR - w_l LocalBurden - w_h HumanIntervention
```

Safety constraints are not reward terms; they remain hard filters.

## P8.3 Learning algorithm

Start simpler than RL:

- empirical class policy;
- nearest comparable cohort;
- UCB/Thompson Sampling only in low-risk strata if exploration needed.

No exploration on auth/security/destructive/data-loss paths.

---

# 23. Phase P9 — Optional scale extensions

Only if actual evidence demands:

```text
CAS/REAPI
multi-server fairness / DRF
distributed compiler cache
GPU/local-model lanes
rich fleet management
cross-runner migration
```

Do not build because architecture is interesting.

Each requires a measured bottleneck.

---

# 24. Immediate ordered backlog

## P0 — phải xử lý trước

1. Root-cause current Coding MCP `TaskGroup/ExceptionGroup` read failure.
2. Restore reliable `workspace_context`/truth plane.
3. Reconcile run `59b40e...` and checkpoint/reject final NSIS artifact.
4. Bind release provenance: source HEAD, artifact SHA, proof fingerprint.
5. Decide installed-logon/reboot/fault-matrix release boundary explicitly.

## P1 — measurement

6. Re-run current ledger baseline after MCP recovery.
7. Compute host-binding coverage current.
8. Populate controller timing/usage/cost where observable.
9. Start quality-outcome capture.
10. Add routing/placement regret reporting.
11. Reduce `UNKNOWN` error class with typed causes.

## P2 — causal baseline

12. Stratify rework by workflow/oracle/risk.
13. Explain 59.8% post-activation first-pass vs earlier cohort without causal shortcut.
14. Quantify intervention-specific rework reduction.

## P3 — server-first

15. Run 10–20 instrumentation pairs.
16. Power-size confirmatory cohort.
17. Promote only proven task classes.

## P4 — semantic localization

18. Explain 5/963 LSP handled result.
19. Run text-vs-LSP task-class A/B.

## P5/P6 — Solution Economics

20. Shadow structured Solution Economics assessment.
21. Record change surface.
22. A/B no-harm + TTAR/CAR.

## P7 — model routing

23. Produce actual Mini/Luna/Terra/Sol paired cohorts.
24. Keep automatic routing off until promotion gate passes.

## P8 — adaptive joint router

25. Only then consider learned model+compute+proof policy.

---

# 25. Quantitative acceptance gates đề xuất

Các số dưới đây là governance starting points, không phải luật thống kê; confirmatory threshold phải được power-calibrated.

## 25.1 Measurement integrity

```text
pair identity mismatch: 0 confirmatory pairs
oracle mismatch: 0
unknown cost represented as zero: 0
unbound controlled host span: target ~0
mixed source fingerprint proof: 0
```

## 25.2 Server-first pilot

No promotion unless:

```text
quality floor passes
no authority/source/proof regression
median paired TTAR direction favorable OR local burden materially lower
p90 not catastrophically worse
fallback success demonstrated
```

## 25.3 Model route

No auto promotion on sample counts like current 1/4/3/4.

Require:

- powered representative cohort;
- >= several task classes if route is broad;
- no critical quality regression;
- cost coverage sufficient.

## 25.4 Solution Economics

No promotion if:

```text
correctness lower beyond margin
security exploit regression > 0
robustness materially worse
repair rate rises enough to erase TTAR gain
```

---

# 26. What NOT to build now

Do not:

- add public tools for nodes/models;
- create second analytics database;
- make server a second authoritative writer;
- turn `server-first` into `remote-all`;
- add Kubernetes-like scheduler;
- implement full REAPI before transfer/cache bottleneck exists;
- optimize generic proof cache with 0.18% current hit rate;
- widen LSP concurrency before understanding 5/963 handled;
- auto-enable Mini/Luna/Terra based on tiny samples;
- add always-on Ponytail persona;
- optimize LOC as North Star;
- open multi-agent fanout by default;
- use synthetic no-op volume as production routing proof;
- interpret test count as project completion.

---

# 27. Reporting contract từ nay về sau

Mọi material wave phải kết thúc bằng report chứa:

```text
WHAT CHANGED
CURRENT STATE
SOURCE / RUN / WAVE ID
PROOF ACTUALLY RUN
ACCEPTED OR NOT
WHAT REMAINS
NEXT CRITICAL ACTION
```

Không được dừng ở “tool finished” hoặc “tests green”.

Mỗi optimization report phải thêm:

```text
HYPOTHESIS
BASELINE
TREATMENT
SAMPLE / STRATA
QUALITY FLOOR
TTAR/CAR/LOCAL BURDEN
EFFECT SIZE + UNCERTAINTY
KEEP / REVISE / REMOVE
```

---

# 28. Scientific verdict theo từng vấn đề

| Problem | Current evidence | Scientific verdict | Next action |
|---|---|---|---|
| Authority/EOCL | Strong source + accepted runs | KEEP | no redesign |
| Recovery architecture | Packaged + installed evidence | KEEP / close release | exact remaining release boundary |
| Release RC | Full gate accepted; installer built | NEAR CLOSED | final EOCL acceptance/provenance |
| Current MCP live availability | TaskGroup exception observed | OPEN P0 | root-cause before next mutation wave |
| Rework | 30.85–40.2% observed across non-identical cohorts | HIGH PRIORITY | stratified paired diagnosis |
| Wait overhead | 3.28x local execution aggregate | MATERIAL | critical-path attribution |
| LSP resource stability | Closed | KEEP | no resource redesign |
| LSP semantic usefulness | 5/963 handled | UNPROVEN / likely underutilized | query reason audit + A/B |
| Proof cache | 1/563 hit | LOW ROI | hold expansion |
| Server-first source | Implemented | READY FOR EXPERIMENT | paired live canary |
| Server-first economics | none sufficient | UNPROVEN | local-vs-server pairs |
| Model auto-routing | tiny non-det sample | NOT READY | paired cohorts |
| Host observation binding | mechanism now observed | PARTIALLY CLOSED | coverage metric + ledger population |
| Controller cost | latest exact audit had 0 coverage | OPEN | provider/client measurement |
| Quality outcomes | latest exact audit had 0 | OPEN | record from new experiments |
| Solution Economics | research only | READY FOR SHADOW | structured assessment + A/B |
| Learned joint router | no causal dataset | HOLD | after P3/P6/P7 |

---

# 29. Core methodological lessons from project evidence

## 29.1 A test-green system can still be release-wrong

Packaged Recovery source drift proved this directly.

Therefore exact artifact/source identity is not ceremony; it prevented false acceptance.

## 29.2 A fast execution can still be an expensive accepted outcome

5.29x repaired median penalty proves execution speed alone is insufficient.

## 29.3 A stable subsystem can still have low economic usefulness

LSP resource lifecycle can be healthy while only handling 5/963 attempted semantic queries.

## 29.4 A feature can be implemented but scientifically unproven

Server-first source code exists; ROI does not.

## 29.5 An architecture can expose multiple models while production behavior remains deterministic

This is desirable until evidence exists.

## 29.6 Observability must not become fiction

`estimated_wait`, host-visible spans, provider cost và model latency are different measurements.

Do not relabel one as another.

---

# 30. Final project assessment

## 30.1 Where the project actually stands

Coding Web has crossed the main architecture threshold:

```text
prototype execution tool
        ↓
reliable authority/recovery harness
        ↓
accepted-result orchestration platform
        ↓
NOW: evidence-driven optimization platform
```

The next large gain is unlikely to come from adding another subsystem.

It should come from:

1. closing live/release truth;
2. measuring causal accepted-result economics;
3. reducing rework;
4. proving server-first by task class;
5. proving Solution Economics without robustness loss;
6. proving model routing before automation;
7. only then learning a joint policy.

## 30.2 Main thesis for the next development era

> **Do less unnecessary engineering work, route only the work that remains, place deterministic compute where end-to-end economics are best, preserve one authority, prove the smallest sufficient result, and learn only from representative accepted outcomes.**

That is the scientifically defensible path from current Coding Web to the intended system:

> **ChatWeb semantic brain + deterministic execution/proof fabric + server-first compute + local-affinity edge + evidence-gated adaptive optimization.**

---

# 31. Evidence map

## Current product truth

- `docs/CURRENT_STATE.md`
- `docs/ROADMAP.md`
- `.coding-tools/performance.json`
- `.coding-tools/task-state.json`
- `.coding-tools/orchestration/ledger.sqlite3`
- `.coding-tools/evaluation/chatweb-host-observations.jsonl`

## Current/recent audits

- `docs/research/260817_PROJECT_STATE_AND_REMAINING_ISSUES_ASSESSMENT.md`
- `docs/research/260816_CHATWEB_SERVER_FIRST_COMPUTE_ORCHESTRATION_RESEARCH.md`
- `docs/research/260816_ACCEPTED_ENGINEERING_OUTCOME_SOLUTION_ECONOMICS_METHODOLOGY_AND_IMPLEMENTATION_PLAN.md`
- `docs/research/260816_P2-P3-orchestration-resource-analysis.md`
- `docs/research/260816_P2-P3-remaining-operational-hardening-implementation-plan.md`
- `docs/research/260816_TOOLS_CODEX_RECOVERY_ARCHITECTURE_ROADMAP.md`

## Key delivery commits

- `cf6cb6dd` — close P3 operational hardening gaps
- `55a00cf0` — complete server-first compute orchestration source contract
- `24825cd8` — preserve organic host correlation
- `bae11481` — close runtime evidence hygiene
- `d5d4bbb5` — enforce exact-source packaged resources
- `acaa3582` — normalize Recovery Supervisor persisted state
- `885260b4` — close P0.2 installed Recovery acceptance
- `1516f0e5` — accepted RC/delivery sequence
- `4fa7d659` — latest pushed evidence/report state observed during this assessment

## Current direct live observation

- Coding MCP `workspace_context` failed in this ChatWeb session with `ExceptionGroup: unhandled errors in a TaskGroup`.
- `document_workflow` also failed with the same TaskGroup family while attempting to write this report into the live repository.
- This is recorded here as an **unresolved P0 operational observation**, not as a proven source regression.

---

# 32. Required next report

Sau khi P0 truth plane được phục hồi, báo cáo tiếp theo không nên là một research essay mới. Nó nên là một **fresh measured baseline report** generated từ current ledger với exact current HEAD/runtime instance:

```text
CURRENT_LEDGER_BASELINE_YYYYMMDD

- run population
- accepted/first-pass/repaired
- TTAR distributions
- controller/host binding coverage
- quality-outcome coverage
- route/model cohorts
- server/local placement cohorts
- error taxonomy
- LSP usefulness by task class
- proof reuse
- current release checkpoint
```

Từ đó mọi P3/P6/P7 experiment dùng cùng baseline authority.

---

# 33. Artifact note

Tài liệu này được tạo dưới dạng artifact ngoài workspace vì current Coding MCP truth/document plane đang lỗi `ExceptionGroup/TaskGroup`. Không commit trực tiếp GitHub để tránh bypass one-Runtime/write-authority policy. Khi MCP được khôi phục, file này nên được đặt vào:

```text
docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md
```

và sau đó được cập nhật bằng fresh current-ledger baseline trước khi dùng làm production rollout authority.

---

**End of current scientific assessment.**