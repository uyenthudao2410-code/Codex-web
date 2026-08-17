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

### 1.2.1 Current verification update — khoảng 21:00 ICT, 2026-08-17

Phần trên được giữ nguyên như **chronology tại thời điểm report được tạo**. Sau đó trong cùng ngày, P0.1 đã re-verify lại trực tiếp trên Coding MCP truth plane hiện tại và lỗi `ExceptionGroup: unhandled errors in a TaskGroup` **không còn tái hiện**:

- `workspace_context(detail=full)` PASS trên current runtime;
- `document_workflow inspect` PASS trên chính tài liệu này;
- `agent_workflow prepare` PASS ở cả initial wave và deterministic replan wave;
- current runtime không có stale/orphaned orchestration/background-operation residue theo live truth snapshot;
- public `smart-v3` contract vẫn đúng 8 tools, không đổi schema để né lỗi.

Vì không còn retained child-exception provenance đủ mạnh để reconstruct chính xác lỗi lịch sử, P0.1 **không gán một source fix giả định**. Kết luận causal hiện tại được ghi chi tiết tại checkpoint P0.1 ở Phase P0 bên dưới.

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

**P1.3 update:** canonical coverage reporting for these fields is now closed with explicit experimental enrollment (`pair_id + policy + provenance`), trusted source attribution and fail-closed promotion economics. Current eligible experimental population is still zero, so live coverage rates correctly remain `null` rather than `0%`.

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

### P0.1 execution checkpoint — 2026-08-17, khoảng 21:00 ICT

**P0.1 DECISION: `ACCEPTED`.** Acceptance này là quyết định kỹ thuật của controller dựa trên acceptance criteria bên trên; wave ghi tài liệu này vẫn tuân theo EOCL checkpoint riêng.

#### WHAT CHANGED

- Không sửa production source cho P0.1 vì current failure không tái hiện và không có bằng chứng đủ để biện minh cho một speculative fix.
- Giữ nguyên historical observation ở §1.2; bổ sung current verification để không biến dated research thành lịch sử giả.
- Root-cause classification được hạ đúng mức bằng chứng thay vì coi generic `UNKNOWN/ExceptionGroup` là một diagnosed server defect.

#### CURRENT STATE

```text
workspace_context                 PASS
document_workflow inspect         PASS
agent_workflow prepare            PASS
stale/orphaned operations         0 observed in live truth snapshot
runtime identity                  KNOWN
smart-v3 public tool count        8
public contract                   UNCHANGED
historical TaskGroup symptom      NOT REPRODUCIBLE
production source change          NONE
```

Một lỗi hiện tại khác, `SEMANTIC_PROVIDER_CALL_FAILED`, được semantic-first localization trả về theo typed/fallback path và text fallback vẫn chạy. Đây là nhánh LSP semantic-value/P4, **không phải** bằng chứng P0.1 còn lỗi TaskGroup.

#### SOURCE / RUN / WAVE ID

```text
source HEAD                       db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
P0.1 run_id                       809f62e686934d9583250dda67a7954d
initial wave_id                   3280b15f45cb45fa8a2e9d82bf7c2c8c
deterministic replan wave_id      8e82874fd14d49cb9bbc99e7bff5c237
runtime process_instance_id       BJ4zrld3FvC5f19g
runtime server_instance_id        HXHbpMFeobFjEWdk
smart-v3 contract SHA-256         4ddfa6bb982f46f02bdd448975ca64b3235a59379b379ec651bcc44000ac9aca
```

Initial `sol_xhigh` execution wave đi tới replan vì `PROMPT_TOO_LARGE` sau khi focused oracle đã PASS. Đây là candidate evidence-packet failure, không phải reproduction của TaskGroup bug. Wave được replan sang `deterministic / mcp_only` thay vì retry unchanged.

#### PROOF ACTUALLY RUN

1. Live `workspace_context(detail=full)` PASS và trả exact Git/runtime/contract identity; stale/orphan counters đều sạch ở snapshot dùng để accept P0.1.
2. `document_workflow inspect` PASS trên file kế hoạch này, chứng minh document plane không còn symptom cùng family tại thời điểm closure.
3. `agent_workflow prepare` PASS; deterministic replan prepare cũng PASS.
4. Focused oracle đã chạy và PASS ở exact source HEAD trước documentation-only mutation:

   ```text
   python -m unittest tests.test_task_state_and_build tests.test_stateless_http_2026 tests.test_mcp_sdk_smoke
   exit_code = 0
   ```

5. Current source inspection cho thấy:
   - background worker bắt `Exception` và materialize typed `BACKGROUND_OPERATION_FAILED` thay vì để exception thoát khỏi operation state;
   - HTTP `handle_rpc` luôn convert server-side exception thành JSON-RPC error response;
   - reconnect path reconcile task projection từ durable ledger;
   - expired tunnel session có compatibility recreation path;
   - search current source không tìm thấy implementation literal `TaskGroup`/`ExceptionGroup`; các hit nằm trong chính research document.
6. Git lineage kiểm tra hai hardening có vẻ liên quan nhất:

   ```text
   a051897449827e4753b16def1b693d867fad76e9  2026-08-13  process-scoped background operations
   f64abe25a85e6abaa9fe9eeacd3665eb29a82515  2026-08-15  expired tunnel-session recreation
   ```

   Cả hai **đều có trước** observation ngày 2026-08-17, vì vậy không được dùng để claim rằng một trong hai chính là causal fix của incident này.

#### CAUSAL CLASSIFICATION

Strongest defensible statement:

> Historical symptom được quan sát ở caller boundary dưới dạng async `TaskGroup/ExceptionGroup` wrapper; current server truth plane không tái hiện và retained evidence không còn child exception đủ chi tiết để xác định chính xác sub-cause.

Classification hiện tại:

```text
likely boundary family     connector / transport / session asynchronous wrapper
server defect proven       NO
exact child exception      UNKNOWN DUE TO MISSING HISTORICAL PROVENANCE
boundary confidence        MEDIUM
exact-cause confidence     LOW
speculative source fix     REJECTED
```

Điểm quan trọng: `UNKNOWN DUE TO MISSING HISTORICAL PROVENANCE` ở đây là **epistemic status của postmortem**, không phải permission để giữ một current runtime error class `UNKNOWN`. Nếu symptom tái xuất hiện, phải capture child exception/log/trace tại thời điểm xảy ra rồi mới sửa typed boundary tương ứng.

#### ACCEPTED OR NOT

`ACCEPTED` — toàn bộ acceptance criteria của P0.1 đã được chứng minh trên current runtime. Không còn stop-rule blocker cho bước kế tiếp.

#### WHAT REMAINS

- Không cố reconstruct quá khứ bằng suy đoán. Nếu TaskGroup symptom xuất hiện lại, capture connector/client stack, server/Recovery logs, request/session identity và child exception trong cùng incident window.
- `SEMANTIC_PROVIDER_CALL_FAILED` vẫn cần xử lý ở P4 theo đúng scope riêng.
- Formal release provenance reconciliation của P0.2 vẫn phải được ghi đầy đủ dù prior release run đã được checkpoint để giải phóng EOCL boundary trước P0.1.

#### NEXT CRITICAL ACTION

**P0.2 — Reconcile final artifact run:** đối chiếu exact RC/source fingerprint, installer/blockmap/latest.yml SHA, EOCL checkpoint/quiescence và release-control documentation; không rebuild nếu proof cho thấy artifact hiện tại đã exact và không drift.

## P0.2 Reconcile final artifact run

**P0.2 DECISION: `CLOSED / ACCEPTED`.** Corrective release-provenance closure đã được ChatWeb/controller accept và EOCL checkpoint tại `2026-08-17T14:39:27Z` (khoảng 21:39 ICT). **P0.3 chưa được bắt đầu trong wave này.**

### Vì sao cần corrective provenance build

Run release cũ được dùng làm điểm reconcile ban đầu:

```text
59b40e0a67694ad59385227f6dcfc4d4
```

Run này có build evidence lịch sử, nhưng exact final artifact bytes của nó **không còn được retained trong `dist/`**. Đối chiếu byte đã xác nhận `dist/` bị drift sang một bộ artifact khác. Vì vậy không được phép chỉ sửa projection hoặc ghi lại old SHA rồi coi như artifact cũ vẫn tồn tại; P0.2 cần một corrective build có provenance mới.

### Root cause phát hiện trong corrective attempt đầu tiên

Corrective build đầu tiên dừng ở test gate và phát hiện một bug thật tại Recovery Host legacy pinned-revision bridge:

```text
Git/index text bytes       LF
Windows working-tree bytes CRLF
legacy bridge behavior     SHA-256 raw working-tree bytes
result                     false tamper / revision mismatch
```

Source Git vẫn clean, nhưng cùng logical text có EOL khác nhau trên Windows checkout nên pinned legacy proof bị sai.

Fix được giới hạn đúng boundary:

- `electron/services/componentRevision.js`: canonicalize duy nhất `CRLF -> LF` trước khi hash **legacy pinned text proof**;
- normal component revision vẫn giữ **raw-byte semantics**;
- `tests/component-revision.test.js`: thêm regression coverage cho CRLF acceptance, tamper rejection sau normalization và raw-byte semantics của revision thông thường.

Focused checkpoint trước final build:

```text
run_id      10147ddcac554c2ba3be22c7bd70f59f
focused     23/23 PASS
```

Không cập nhật expected digest một cách cơ học để làm test xanh; fix nằm ở canonicalization boundary gây false mismatch.

### Canonical corrective final-build identity

```text
run_id                cdc2344c2d8b477e8599730d59746268
wave_id               14a232a585b445d6a2c44f3cac28f7b4
base HEAD             db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
worktree fingerprint  417975e837be9f200efd44c02b03fc9bd7a571dc89f6d036df0cef043670ed31
```

### PROOF ACTUALLY RUN

Canonical audit của run trên có integrity sạch và required proofs xanh:

```text
precheck proof  53c1ae48d18d458c8eddba3b9903eda1  exit 0
precheck proof  d152160a8c8b487fba7134a361b0572d  exit 0
final proof     39399b3d83384ce4b3cd954536ec85d7  PASS
command         npm run dist
exit_code       0
```

Post-build source-scope check xác nhận:

```text
HEAD unchanged                  db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
product/test modified scope     electron/services/componentRevision.js
                                tests/component-revision.test.js
git diff --check               PASS
unexpected product/package drift NONE OBSERVED
```

Build job đã terminal-exit sạch; không khởi chạy một build thứ hai sau proof PASS.

### Final content-addressed artifacts

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| `dist/web-mcp-assistant-setup-0.3.4.exe` | 128,679,337 | `CF8555C381F3B45989236BFD1BD4ADB3AAB2A3181ED2313E736F380BCEB35D57` |
| `dist/web-mcp-assistant-setup-0.3.4.exe.blockmap` | 135,846 | `B02910158B0CD88772DE05FAC65FD58CD62DB8BEB5B312CE8B4ADEA6749CD11F` |
| `dist/latest.yml` | 363 | `0016A7E6F14AFE07DB33D29ECBFBC3CDA2BAD6165C75ECCDA76F9A01309C72C5` |
| `dist/win-unpacked/resources/app.asar` | 5,273,224 | `59FEC580356ACA2285BCDD2054DA2239FCED872906716231A90C460F51372FF5` |

### EOCL closure

```text
final orchestration state  CHECKPOINTED
accepted_at                2026-08-17T14:39:27Z
integrity                  CLEAN
mixed-fingerprint proof    NONE OBSERVED
hidden second build        NO
publication/upload         NOT PERFORMED
install/restart            NOT PERFORMED
stash/reset/clean          NOT PERFORMED
P0.3 work                  NOT STARTED IN THIS WAVE
```

Một lookup sau successful build trước đó trả `ORCHESTRATION_RUN_NOT_FOUND` vì dùng **wrong/stale run lookup**, không phải vì build proof biến mất. Canonical run `cdc2344...` sau đó được reconcile và audit trực tiếp ở trạng thái `ACCEPTING`, đủ 3/3 proof PASS; vì vậy không duplicate rebuild. Run được accept chính thức và chuyển sang `CHECKPOINTED`.

### Acceptance

```text
CHECKPOINTED                 PASS
artifact SHA recorded        PASS
source base recorded         PASS
worktree fingerprint         RECORDED
no mixed-fingerprint proof   PASS
no hidden second build       PASS
```

#### WHAT CHANGED

- Corrected the Windows CRLF/LF false-tamper boundary in the Recovery legacy pinned revision bridge with regression coverage.
- Rebuilt the final NSIS artifact only because previously accepted final bytes were no longer retained and current `dist/` had drifted.
- Bound the new installer, blockmap, `latest.yml` and packaged `app.asar` to one canonical corrective run and accepted/checkpointed that run.

#### CURRENT STATE

P0.2 is closed against its stated acceptance criteria. This is a release-provenance closure, **not** a claim that P0.3 logon/reboot/fault-matrix/publication boundaries have already passed.

#### ACCEPTED OR NOT

`ACCEPTED / CHECKPOINTED`.

#### WHAT REMAINS

Only the next explicit release-contract decision in **P0.3** remains inside Phase P0: decide whether fresh-logon persistence, reboot persistence, production Recovery fault matrix and publication/upload are required boundaries for v0.3.4. Those requirements must be recorded before any additional release action.

#### NEXT CRITICAL ACTION

**P0.3 — Final release boundary decision.** Determine and record the release contract first; do not invent a reboot/logon/publication requirement after the fact and do not perform publication implicitly.

## P0.3 Final release boundary decision

**P0.3 DECISION: `CLOSED / ACCEPTED`.** Release contract cho v0.3.4 đã được quyết định và EOCL checkpoint tại `2026-08-17T14:48:01Z` (khoảng 21:48 ICT). Closure này là **contract decision + evidence checkpoint**, không phải thực hiện các lifecycle action không thuộc current release contract.

### SOURCE / RUN / WAVE ID

```text
source HEAD             db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
run_id                  c675125eb066465282e6aeedeb7351d4
final wave_id           e827a6a286cd414698b10b1cf2a45c5d
worktree fingerprint    0e162adbf73707c084a32bece907ac22d7e742db984196e35a8f1ca930ed867f
proof_id                278374c65eb247908fae8e85905611dc
proof fingerprint       6c486d257e40ec8f97b40cac6447cb60471b36fc4c041f3283622f2727fbe802
final state             CHECKPOINTED
integrity               CLEAN
```

### Release contract được chốt

| Boundary | Quyết định v0.3.4 | Cơ sở |
|---|---|---|
| Installed current-session smoke | **REQUIRED / ALREADY EVIDENCED** | Packaged + installed current-session Recovery acceptance đã có từ các wave trước. |
| Fresh login/logon persistence | **CONDITIONAL — không phải base-release blocker** | `startWithWindows` mặc định `false`; Windows login-item là opt-in từ persisted setting; Recovery Supervisor install là operator action riêng. Trước khi claim đường opt-in này hoạt động qua fresh logon, phải chạy installed fresh-logon/session smoke. |
| Reboot persistence | **NOT REQUIRED cho current contract** | Maintained release guidance không định nghĩa reboot là gate mặc định; kiến trúc hiện tại là same-user session/logon, không phải Windows service/LocalSystem contract. Chỉ trở thành required khi có release claim tường minh về reboot survival. |
| Production Recovery fault matrix | **CONDITIONAL** | Packaged/isolation acceptance đã cover packaged Supervisor healthy ping, live-owner fail-closed và executable-hash fail-closed. Chỉ các production-only scenario được nêu cụ thể và không thể test an toàn trong isolation mới trở thành gate của thay đổi/release tương ứng. |
| Publication/upload | **SEPARATE AUTHORIZED ACTION — NOT PERFORMED** | Publication không phải closure mặc định; phải có yêu cầu + destination tường minh. User chưa yêu cầu publish/upload trong bước này. |

Điểm phân biệt bắt buộc:

> Base artifact v0.3.4 có thể đóng release boundary hiện tại mà không cần tự ý logoff/reboot. Điều này **không** đồng nghĩa opt-in startup/Supervisor persistence đã được chứng minh qua fresh logon hoặc reboot; nếu sau này release/support claim boundary đó, exact installed acceptance tương ứng phải chạy trước claim.

### PROOF ACTUALLY RUN

Evidence bundle của run đọc maintained release/recovery guidance và current implementation. Final deterministic proof:

```text
git grep -n "startWithWindows: false" -- electron/services/config.js renderer/app.js
exit_code = 0
status    = PASS
```

Proof này xác nhận current source/default/UI preview đều không bật Windows startup mặc định.

Hai replan trong chronology của run không phải product regression:

1. execute read-only đầu tiên bị workflow validation chặn vì không có check command;
2. check `node -e` kế tiếp bị safe-mode chặn `INLINE_SCRIPT_PERMISSION_REQUIRED`;
3. không nâng quyền/trusted mode; replan sang read-only `git grep`, PASS.

### WHAT CHANGED

- Không thay đổi production source.
- Không thay đổi installer/artifact đã khóa ở P0.2.
- Ghi rõ boundary nào là current gate, boundary nào conditional, và publication là action tách biệt.
- Không biến một optional feature thành release blocker chỉ vì nó tồn tại trong kiến trúc.

### CURRENT STATE

```text
P0 truth plane                  CLOSED for current acceptance scope
P0.2 artifact provenance       CHECKPOINTED
P0.3 release contract          CHECKPOINTED
installed current-session      EVIDENCED
fresh-logon claim              NOT MADE; CONDITIONAL PROOF REQUIRED IF CLAIMED
reboot-survival claim          NOT PART OF CURRENT CONTRACT
unspecified prod fault matrix  NOT A BLOCKER
publication/upload             NOT REQUESTED / NOT PERFORMED
```

### ACCEPTED OR NOT

`ACCEPTED / CHECKPOINTED` — P0.3 đã hoàn tất theo đúng mục tiêu là **quyết định release boundary trước khi hành động**, không phải chạy thêm lifecycle tests không có contract requirement.

### WHAT REMAINS

- Nếu sau này user/release contract bật hoặc quảng bá `startWithWindows`/installed Recovery Supervisor qua fresh logon, chạy installed fresh-logon smoke trước khi accept claim đó.
- Nếu sau này có explicit “survives reboot” promise, thêm reboot acceptance đúng boundary.
- Nếu có named production-only Recovery fault scenario không thể test an toàn trong isolation, chạy scenario đó như release gate của thay đổi liên quan.
- Publication/upload vẫn chờ một yêu cầu riêng có destination rõ ràng.

### NEXT CRITICAL ACTION

**P1.1 — Re-run current ledger baseline after MCP recovery.** P0 đã đóng theo acceptance scope hiện tại; bước tiếp theo là tạo fresh canonical baseline từ current ledger/current HEAD/runtime instance thay vì tiếp tục dựa vào snapshot 16/08 hoặc HEAD `3a3abaff`.

---

# 15. Phase P1 — Measurement integrity closure

## P1.1 Re-run current ledger baseline after MCP recovery

**P1.1 DECISION: `CLOSED / ACCEPTED`.** Fresh canonical baseline đã được sinh trực tiếp từ current ledger tại `2026-08-17T14:59:54.529034Z` (~21:59 ICT) và được ghi thành `docs/research/260817_CURRENT_LEDGER_BASELINE.md`. Snapshot này thay thế các count cũ ở HEAD `3a3abaff`/16-Aug cho quyết định ongoing, nhưng giữ các snapshot cũ làm chronology.

### WHAT CHANGED

P1.1 phát hiện repository đã có hai authority đúng nhưng tách rời:

```text
report_rework_baseline.py   -> organic accepted-result rework / TTAR
report_evaluation_plane.py  -> host-visible observation plane
```

Chưa có một canonical aggregate duy nhất cho run population/status, REPLAN/failure classes, route decisions, pair coverage, quality coverage, controller coverage và host binding. Vì vậy đã thêm **reporting adapter mỏng**, không tạo analytics database thứ hai và không thay runtime behavior:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
  + OrchestrationLedger.current_baseline_summary()

resources/coding-tools-mcp/coding_tools_mcp/evaluation_report.py
  + host_binding_summary()
  + current_ledger_baseline_report()

resources/coding-tools-mcp/scripts/report_current_ledger_baseline.py
  + canonical JSON CLI

resources/coding-tools-mcp/tests/test_evaluation_report.py
  + regression coverage
```

Không đổi database schema, public MCP tool schema, routing policy, runtime lifecycle hay release artifacts.

### SOURCE / RUN / WAVE ID

```text
source HEAD                         db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
runtime version                     0.4.3
runtime process_instance_id         BJ4zrld3FvC5f19g
runtime server_instance_id          HXHbpMFeobFjEWdk
loaded behavior fingerprint         63cacbecb33383823780c7f7ad384c1a6236169df58f6d11e721ef51ac2d50a4
smart-v3 contract SHA-256           4ddfa6bb982f46f02bdd448975ca64b3235a59379b379ec651bcc44000ac9aca
P1.1 implementation run_id          967bb4c9007f4f8aac4f14eaf16ed521
P1.1 implementation wave_id         3d1671ab31ed4924baf2f53d52cea8e6
implementation proof_id             8e526630ba97470ca3e587e783e72c1d
implementation proof fingerprint    c622ed5b93fbe13653f2004ae0a3ebb4fe7b1cecd717a2d5cb96e6042870b2a6
implementation final state          CHECKPOINTED
baseline capture command_id         SYtpm2rRDc2bpOCisuL4CAFz
baseline report SHA-256             0c60b551db5c13e8be652791de0eb92a28cfeccf4632d2e1725f866b254ef80f
```

Baseline command được chạy **ngoài EOCL run** sau khi implementation run đã checkpoint, nên current population không bị tự chèn một measurement run `active`.

### PROOF ACTUALLY RUN

Implementation proof:

```text
python -m unittest tests.test_evaluation_report
PASS
```

Additional repository guardrails:

```text
python scripts/check_module_size.py
module-size budgets ok

git diff --check -- coding_tools_mcp/orchestration_ledger.py coding_tools_mcp/evaluation_report.py tests/test_evaluation_report.py scripts/report_current_ledger_baseline.py
PASS
```

Fresh canonical capture:

```text
python resources/coding-tools-mcp/scripts/report_current_ledger_baseline.py --workspace .
exit_code = 0
captured_at = 2026-08-17T14:59:54.529034Z
```

### CURRENT STATE — fresh canonical numbers

#### Ledger population

```text
total runs = 559
accepted   = 333
aborted    = 170
stale      = 49
completed  = 7
```

#### Organic/model-free accepted-result cohort

```text
accepted scanned             = 333
explicit model-route excluded = 16
organic accepted              = 317
first-pass accepted           = 201 (63.4069%)
repaired accepted             = 116 (36.5931%)
replan count                  = 213
first-pass TTAR p50           = 49,320 ms
first-pass TTAR p90           = 339,099 ms
repaired TTAR p50             = 246,091 ms
repaired TTAR p90             = 1,042,600 ms
p50 repair multiplier         = 4.98968x
p90 repair multiplier         = 3.074618x
```

Rework vẫn là leverage lớn: repaired median gần **5x** first-pass median.

#### Canonical replan/failure events

```text
REPLAN transitions      = 381
failure_observed events = 381
```

Largest event classes:

```text
CHECK_FAILED               106
SOL_REJECTED                49
PATCH_AMBIGUOUS             48
BUILD_VERIFICATION_FAILED   46
BASE_DRIFT                  36
```

Đây là **event counts**, không phải independent task failure rates.

Preflight-avoided no-write patch failures hiện là 68:

```text
PATCH_CONTEXT_AMBIGUOUS = 44
PATCH_CONTEXT_NOT_FOUND = 24
```

#### Route-selected population

```text
route_selected events = 687

deterministic = 654
sol_xhigh     = 17
mini          = 7
luna          = 6
terra         = 3
```

Non-deterministic evidence vẫn quá nhỏ/heterogeneous để justify broad auto-routing promotion.

#### Pair / quality / controller coverage

```text
pair-tagged runs          = 0
unique pair ids           = 0
quality outcome events    = 0
quality run coverage      = 0 / 559 = 0%
controller observed       = 0 / 559 = 0%
controller started_at     = 0 / 559 = 0%
controller token usage    = 0 / 559 = 0%
controller monetary cost  = 0 / 559 = 0%
```

`0% coverage` **không có nghĩa cost = 0**; đây là measurement absence và unknown vẫn phải giữ unknown.

#### Host-visible / binding

```text
current schema-v5 host turn spans   = 46
spans with run+wave binding         = 17
host binding rate                   = 36.9565%
spans with trace+turn identity      = 17
exact ledger correlations           = 17
exact correlated run count          = 17
```

Host-visible timing:

```text
p50 = 339,908.2 ms
p90 = 2,128,839.1 ms
```

Đây là Electron DOM `user turn visible -> first assistant visible`, **không phải model/provider latency**.

P1.1 cố ý **không** tính:

```text
eligible_runs_with_host_span
eligible_run_host_coverage
```

vì P1.2 phải định nghĩa controlled eligible-run denominator trước; không được nhìn dữ liệu rồi sửa denominator để làm coverage đẹp hơn.

### ACCEPTED OR NOT

`ACCEPTED / CLOSED` — P1.1 đã đạt mục tiêu tạo một fresh canonical current-ledger baseline có provenance rõ, dùng ledger làm causal source và không tạo một analytics plane mới.

Detailed report:

```text
docs/research/260817_CURRENT_LEDGER_BASELINE.md
SHA-256 0c60b551db5c13e8be652791de0eb92a28cfeccf4632d2e1725f866b254ef80f
```

### WHAT REMAINS

P1.1 không giải quyết thay cho các measurement steps kế tiếp:

- P1.2: định nghĩa controlled eligible-run denominator và tính exact host binding coverage;
- P1.3: populate controller `started_at` / token usage / monetary cost nơi thực sự observable;
- P1.4: bắt đầu quality-outcome population trên new experimental runs;
- P1.5: giảm `UNKNOWN` bằng typed causal taxonomy.

### NEXT CRITICAL ACTION

**P1.2 — Host binding coverage metric.** Định nghĩa denominator trước khi measurement, sau đó report `host_spans_total`, `host_spans_with_run_binding`, `host_binding_rate`, `eligible_runs_with_host_span`, `eligible_run_host_coverage` bằng explicit identity; tuyệt đối không timestamp-proximity matching.

## P1.2 Host binding coverage metric

**P1.2 DECISION: `CLOSED / ACCEPTED`.** P1.2 defines the denominator before evaluating coverage and closes the measurement-contract gap without timestamp-proximity inference. **P1.3 remains `NOT STARTED`.**

### WHAT CHANGED

The runtime source now writes a durable eligibility marker only when a newly created run actually claims the pending organic Electron host identity:

```text
host_correlation.schema_version = 1
host_correlation.source         = electron_pending_host_turn
host_correlation.eligible       = true
```

Controlled calls that merely supply `trace_id`/`turn_id` do not receive this marker. The reporter uses this marker as the causal denominator and does not reinterpret old runs after observing their timestamps.

Reporter output now includes:

```text
host_spans_total
host_spans_with_run_binding
host_binding_rate
eligible_runs_total
eligible_runs_with_host_span
eligible_run_host_coverage
eligible_run_coverage_status
eligible_run_coverage_basis
historical_eligible_run_coverage_status
timestamp_proximity_inference_forbidden
```

### CURRENT STATE

Fresh closure verification:

```text
host_spans_total                    46
host_spans_with_run_binding         17
host_binding_rate                   36.9565%
host_spans_with_trace_turn_identity 17
exact_ledger_correlations           17
exact_correlated_run_count          17

eligible_runs_total                 0
eligible_runs_with_host_span        0
eligible_run_host_coverage          null
eligible_run_coverage_status        no_instrumented_eligible_runs
eligible_run_coverage_basis         server_owned_host_correlation_marker_v1
historical_eligible_run_coverage    not_reconstructable_without_durable_eligibility_marker
timestamp_proximity_inference       FORBIDDEN
```

The `0` eligible-run population is a typed “no instrumented eligible runs yet” state, **not** a 0% coverage result. The live MCP process has not been restarted/activated onto the new source, and P1.2 did not require an implicit restart.

### SOURCE / RUN / WAVE ID

Implementation:

```text
source HEAD         db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
run_id              18f59868b4164dc0a42e9600a3b5a37b
wave_id             87f0749155104aab8c3e609ea481a27b
proof_id            f395b8ea29424d759391fa34164256d0
proof fingerprint   dd6537ba39f9ed963c723f45dd12631fa7e492991d18041929b8e1b43e15847c
checkpoint_id       919f3da563434786847f76524beaca9f
final state         CHECKPOINTED
```

Fresh closure verification:

```text
run_id              2d5264fdc2dc4f0fb20516008be2be98
wave_id             0c17f716a2374c80809fc49ee6dc6397
proof fingerprint   41af6a3e4b50454546752e11424d6dc5aac1e43257951db4320e64f7dffca063
final state         CHECKPOINTED
```

### PROOF ACTUALLY RUN

```text
python -m unittest tests.test_evaluation_report                     9/9 PASS
python scripts/check_module_size.py                                 PASS
python scripts/report_current_ledger_baseline.py --workspace ../.. PASS
scoped git diff --check on P1.2 source/test surface                 PASS
ledger integrity                                                     PASS
```

Regression coverage explicitly checks:

- eligible marker + matching host span => coverage 1.0;
- eligible marker without host span => coverage 0.0;
- timestamp proximity is never used;
- an organic newly-created run claims exact pending host identity and gets the durable marker;
- a controlled run with caller-supplied identity takes precedence and gets no marker;
- an existing run does not later claim a pending host identity.

### ACCEPTED OR NOT

`ACCEPTED / CHECKPOINTED`.

Acceptance is for the **scientific measurement contract and implementation**:

- denominator defined causally before measurement;
- explicit server-owned eligibility marker implemented;
- controlled-identity leakage regression-covered;
- history left non-reconstructable where evidence cannot support backfill;
- fresh canonical reporter verified.

Near-complete coverage remains the target for future **controlled experiments** once instrumented runs exist; organic all-history perfection is not required and cannot be manufactured retroactively.

### WHAT REMAINS

P1.2 itself has no remaining implementation blocker.

A runtime restart/activation to begin producing new durable markers is a separate lifecycle action and was **not performed implicitly**. If explicitly authorized later, a post-activation organic turn can validate that the live process starts populating `eligible_runs_total`.

P1.3 is intentionally not implemented in this wave.

### NEXT CRITICAL ACTION

After this P1.2 documentation closure, proceed to **P1.3 Controller Usage Coverage** only as a separate wave. Its contract is to populate/measure `controller.started_at`, token usage and monetary cost where genuinely observable, preserving missing values as unknown.

## P1.3 Controller usage coverage

**P1.3 DECISION: `CLOSED / ACCEPTED / CHECKPOINTED`.** The controller timing/usage/cost measurement contract is now explicit, causal and fail-closed. This closure does **not** claim that a paired experimental population already exists. **P1.4 was not started in this wave.**

### WHAT CHANGED

P1.3 reuses the existing `agent_workflow.evaluation.controller` schema and canonical orchestration ledger; it does not add a public MCP tool or a second analytics store.

The canonical controller-coverage denominator is now:

```text
explicit_evaluation_enrollment_v1
```

A run enters the experimental denominator only when all enrollment identity is explicit:

```text
pair_id       nonempty
policy        nonempty
provenance    representative | benchmark | synthetic
status        independent / intention-to-treat
```

Organic `trace_id`/`turn_id` identity alone does not make a run eligible for controller economics.

Controller telemetry semantics are now explicit:

```text
started_at                 counts only when timestamp is parseable
token usage                counts when >=1 token field is explicitly observed
complete token usage       counts when all four token fields are explicitly observed
monetary cost              counts when an explicit nonnegative numeric value exists
source                     client_reported | provider_reported
```

`monetary_cost=0` is an observed zero. Missing cost is unknown. Missing token fields are unknown rather than silently converted to zero.

Canonical reporting now includes:

```text
eligible_experimental_runs
runs_observed
runs_with_started_at
runs_with_token_usage
runs_with_complete_token_usage
runs_with_monetary_cost
runs_with_source
source_counts
observed_rate
started_at_rate
token_usage_rate
complete_token_usage_rate
monetary_cost_rate
source_rate
unknown_is_not_zero
promotion_economics
```

Promotion economics is held when there is no eligible experimental population or when controller monetary-cost coverage is incomplete. P1.3 itself does not authorize automatic routing promotion.

### CURRENT STATE

Fresh canonical measurement after implementation acceptance:

```text
captured_at                       2026-08-17T16:35:47.073719Z (~23:35 ICT)
denominator                       explicit_evaluation_enrollment_v1
pair_tagged_runs                  0
unique_pair_ids                   0
eligible_experimental_runs        0
runs_observed                     0
runs_with_started_at              0
runs_with_token_usage             0
runs_with_complete_token_usage    0
runs_with_monetary_cost           0
runs_with_source                  0
source_counts                     {}
observed_rate                     null
started_at_rate                   null
token_usage_rate                  null
complete_token_usage_rate         null
monetary_cost_rate                null
source_rate                       null
unknown_is_not_zero               true
promotion_economics.status        hold
promotion_economics.hold_reasons  [no_eligible_experimental_runs]
automatic_promotion               false
```

The `0` denominator means there is currently no explicitly enrolled paired experiment in the ledger. Therefore the coverage rates are correctly `null`, **not 0%**. This is measurement absence, not a zero-cost or zero-token result.

When enrolled experimental runs exist, materially incomplete cost coverage keeps economics on hold via:

```text
controller_cost_coverage_incomplete
```

### SOURCE / RUN / WAVE ID

```text
source HEAD         db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
run_id              16ab815de8fa4976bd92ff35e21a4d6f
wave_id             72524477cded4457858d1ae2e8426e12
worktree fingerprint b4557a1b5fa4280fbf3c1c7f9a6ba92c485b37a76bad91cfb4333b152db50991
proof fingerprint   a3a0cb55374bf6b062f11ccc93676ffee6928280ebda60ded68c45d32921950f
final state         CHECKPOINTED
accepted_at         2026-08-17T16:28:52.248Z
```

Implementation surface:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/tests/test_evaluation_report.py
```

No database schema, public MCP schema, routing policy, runtime lifecycle or release artifact was changed. No runtime restart was performed.

### PROOF ACTUALLY RUN

```text
proof 78c33310b75342b3b1fb7b9660e82ddf
python scripts/check_module_size.py
PASS

proof 4368aca06cf9461c8d0b5ae2f9460945
git diff --check -- coding_tools_mcp/orchestration_ledger.py tests/test_evaluation_report.py
PASS

proof 8498a36382d942188f838ac083665b17
python -m unittest tests.test_evaluation_report
PASS / exit 0

python resources/coding-tools-mcp/scripts/report_current_ledger_baseline.py --workspace .
PASS / exit 0
captured_at = 2026-08-17T16:35:47.073719Z
```

Regression coverage proves:

- `pair_id + policy + provenance` enrollment is required;
- status is not used to survivor-filter the denominator;
- organic host trace/turn identity alone is excluded;
- missing controller telemetry remains unknown;
- partial token telemetry remains visibly partial;
- explicit zero monetary cost is observed rather than treated as missing;
- controller source provenance is restricted to declared trusted sources;
- promotion economics stays on hold when monetary-cost coverage is incomplete.

One duplicate implementation attempt hit `PATCH_CONTEXT_NOT_FOUND` after the intended source change had already been applied. The rejection happened at preflight/context matching, created no second mutation, and is not a product regression.

### ACCEPTED OR NOT

`ACCEPTED / CHECKPOINTED`.

P1.3 is closed as a **measurement-integrity and reporting contract**. Current paired/controller population remains absent; no data was fabricated or backfilled to force a non-null coverage number.

### WHAT REMAINS

- Real representative/benchmark/synthetic experiments must explicitly enroll with `pair_id + policy + provenance` before they enter this denominator.
- A trusted client/provider must populate `controller.started_at`, token fields and `monetary_cost` where actually observable.
- Economics stays fail-closed until cost coverage is complete enough for the intended analysis.
- P1.4 quality-outcome population remains separate and was not implemented here.

### NEXT CRITICAL ACTION

**P1.4 — Quality-outcome population.** Begin recording explicit quality outcomes on new experimental runs and preserve historical unknowns where no post-accept evidence exists. Do not infer quality from `accepted` state alone.

## P1.4 Quality-outcome population

**P1.4 DECISION: `CLOSED / ACCEPTED / CHECKPOINTED`.** Quality-outcome reporting is now explicit and fail-closed. Lifecycle `accepted` is never substituted for quality evidence; historical backfill requires exact evidence; the experimental denominator is `explicit_evaluation_enrollment_v1` (`pair_id + policy + provenance`, status-independent).

### CURRENT STATE

Fresh root-canonical capture after acceptance:

```text
captured_at                      2026-08-17T17:03:21.070238Z
run_count                        567
eligible_experimental_runs       0
quality_outcome_events           0
experimental_runs_with_outcome   0
experimental_coverage_rate       null
experimental_coverage_status     no_eligible_experimental_runs
promotion_quality.status         hold
promotion_quality.hold_reasons   [no_eligible_experimental_runs]
automatic_promotion              false
unknown_is_not_good              true
```

The null experimental coverage is measurement absence, **not** 0% quality. The all-history explicit-event coverage remains 0 because no exact historical quality events exist and P1.4 correctly refused to infer them from acceptance state.

### SOURCE / RUN / WAVE ID

```text
source HEAD      db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
run_id           73f933ec87be4a36849fe8d4770a22d9
final wave_id    d723ac8823a54982a6e8d742ac7f9c6c
proof_id         21799528cd3d479da35147cabf0b3e8c
final state      CHECKPOINTED
integrity        261 / 261 OK
```

### PROOF ACTUALLY RUN

```text
python -m unittest tests.test_evaluation_report                    PASS
python scripts/check_module_size.py                                PASS
scoped git diff --check                                            PASS
python resources/coding-tools-mcp/scripts/report_current_ledger_baseline.py --workspace .
                                                                   PASS / exit 0
```

### ACCEPTED OR NOT

`ACCEPTED / CHECKPOINTED`.

### WHAT REMAINS

Representative experimental population is still absent. New controlled experiments must explicitly enroll and record quality outcomes; old unknown quality remains unknown unless exact provenance exists.

### NEXT CRITICAL ACTION

**P1.5 — Error Taxonomy Cleanup.** Target causal classification coverage of `UNKNOWN`; do not optimize total error count and do not invent historical causes.

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
8. **DONE P1.3:** define/report controller timing/usage/cost coverage with explicit experimental enrollment and unknown-preserving semantics; current eligible population remains 0.
9. **DONE P1.4:** explicit quality-outcome coverage + fail-closed promotion-quality contract; current eligible experimental population remains 0 and experimental coverage remains null.
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
| Host observation binding | causal denominator defined; current 17/46 span binding | P1.2 CLOSED / instrumented live population pending activation | P1.3 closed; live activation only if explicitly authorized |
| Controller usage/cost | explicit enrollment/report contract closed; eligible experimental runs = 0, rates = null | P1.3 CLOSED / economics HOLD | populate trusted telemetry on future enrolled runs; P1.4 next |
| Quality outcomes | explicit quality contract/reporting closed; current enrolled population = 0 and coverage = null | P1.4 CLOSED / promotion HOLD | populate exact outcomes on future enrolled experiments; do not backfill from accepted state |
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

- `docs/research/260817_CURRENT_LEDGER_BASELINE.md`
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

P1.1 đã tạo fresh measured baseline report từ current ledger/current runtime:

```text
docs/research/260817_CURRENT_LEDGER_BASELINE.md
```

Report hiện đã cover:

```text
- run population
- accepted/first-pass/repaired
- TTAR distributions
- event-level failure/replan classes
- route population
- pair/quality/controller coverage
- host span binding
- current runtime/source provenance
```

P1.2 đã đóng causal eligible-run denominator và exact host-binding coverage contract. P1.3 đã đóng explicit experimental controller-coverage denominator, provenance semantics và fail-closed economics gate. P1.4 đã đóng explicit quality-outcome reporting + fail-closed promotion-quality contract; current eligible experimental population vẫn là `0`, vì vậy experimental coverage được giữ `null` và historical accepted state không bị suy thành quality evidence. **P1.5 là measurement-integrity action kế tiếp** để giảm diagnostic `UNKNOWN` bằng typed causal taxonomy trước khi P3/P6/P7 dùng baseline cho causal experiments.

---

# 33. Artifact note

Tài liệu này ban đầu được tạo dưới dạng artifact ngoài workspace khi current Coding MCP truth/document plane gặp `ExceptionGroup/TaskGroup`. Sau P0.1, truth/document plane đã được re-verify và tài liệu hiện được duy trì trực tiếp trong workspace qua Coding MCP authority.

Current authoritative path:

```text
docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md
```

---

**End of current scientific assessment.**

---

# Addendum — P1 Measurement Integrity & Evaluation Readiness Closure

**Current-state capture:** 2026-08-17T18:06:42.547322Z (~01:06 ICT, 2026-08-18)
**Purpose:** append-only closure update. The dated sections above remain historical evidence. For **current P1 status and next-action decisions**, this addendum supersedes older statements above that still describe P1.5/P1.6 as pending.

## A. Final P1 verdict

```text
P1 Measurement Integrity & Evaluation Readiness   CLOSED / CHECKPOINTED
P1.1 canonical current-ledger baseline            CLOSED
P1.2 causal host-binding denominator               CLOSED
P1.3 controller usage/cost coverage contract       CLOSED
P1.4 explicit quality-outcome contract             CLOSED
P1.5 prospective typed error taxonomy              CLOSED / CHECKPOINTED
P1.6 routing/placement regret reporting             CLOSED / CHECKPOINTED

Empirical policy efficacy                           NOT YET PROVEN
Automatic model/placement promotion                 HOLD
Automatic activation from P1 evidence               false
P2 work in this closure wave                        NOT STARTED
```

The key distinction is mandatory:

> **P1 is closed as a measurement-integrity and evaluation-readiness phase, not as proof that any candidate route, placement policy, or orchestration policy is already faster, cheaper, or higher quality.**

P1 now gives the project a causal measurement vocabulary and fail-closed reporting plane. It intentionally refuses to manufacture efficacy evidence where the representative experimental population is still absent.

## B. P1.1–P1.6 closure matrix

| Item | What is now closed | Fresh current evidence | Scientific interpretation |
|---|---|---|---|
| **P1.1** | Canonical current-ledger baseline/reporting adapter | Ledger is the causal source; current reporter completes successfully | One current measurement entry point exists without creating a second analytics database. |
| **P1.2** | Server-owned causal eligible-run denominator for organic host binding | `eligible_runs_total=1`, `eligible_runs_with_host_span=1`, coverage `1.0`; overall span binding `18/51 = 35.2941%` | The causal marker path is now observed live, but **n=1 is instrumentation evidence, not a mature coverage estimate**. Historical eligibility remains non-reconstructable. |
| **P1.3** | Explicit experimental controller timing/token/cost denominator and unknown-preserving semantics | `eligible_experimental_runs=0`; all controller coverage rates `null`; economics `HOLD` | Measurement contract is complete; economics evidence is absent. Missing cost/tokens are unknown, never zero. |
| **P1.4** | Explicit quality-outcome population/reporting and fail-closed quality gate | `eligible_experimental_runs=0`, quality events `0`, experimental coverage `null`, promotion quality `HOLD` | Lifecycle `accepted` is not treated as quality evidence. No historical quality is fabricated. |
| **P1.5** | Prospective typed causal taxonomy and epoch-aware reporting | Current taxonomy epoch has `0` samples; status `no_current_epoch_samples`. Supplemental cumulative projection still has `48/475` UNKNOWN and typed coverage `89.8947%` | Implementation is closed, but **no empirical post-epoch UNKNOWN reduction may yet be claimed**. Historical UNKNOWN is deliberately not backfilled. |
| **P1.6** | Representative-pair routing/placement regret methodology and canonical report | Mini: `pair_count=0`, Luna: `pair_count=0`; both `HOLD`; predicted policy score `null`; scalar regret `null` | Regret can now be measured when real comparable pairs exist. Current data cannot rank Mini/Luna against the baseline. |

## C. P1.5 durable closure — typed error taxonomy

```text
run_id      9b6b067d90244a71bf5835ba04b5543b
wave_id     eda8944c29944a03a310fcfc8b51fa2c
proof_id    55eedfd1e57347c287e89c84dca87953
state       CHECKPOINTED
```

P1.5 uses a prospective taxonomy epoch and normalizes typed causal families including `FILESYSTEM`, `POLICY`, `NOT_FOUND`, `INTERNAL`, and `CONFLICT`. It keeps causal orchestration-ledger evidence separate from the supplemental `.coding-tools/performance.json` projection.

Fresh P1 closure capture:

```text
cumulative supplemental projection samples     475
UNKNOWN                                          48
typed coverage                                  0.898947
current taxonomy epoch samples                   0
current epoch typed coverage                   null
current epoch UNKNOWN share                    null
current epoch status                           no_current_epoch_samples
historical_backfill                            false
historical_unknown_reclassification_forbidden  true
```

Therefore P1.5 closes the **taxonomy/instrumentation defect**, not the empirical outcome. No post-epoch reduction in UNKNOWN is claimed before current-epoch samples exist.

## D. P1.6 durable closure — routing / placement regret

```text
source HEAD  db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc
run_id       72616aa5d7a3409a83098d2243f48c48
wave_id      da847ca77d7a4d19bc4af6e1377b3e3d
proof_id     4ea919f98b544fb095457b2eac5da8b8
state        CHECKPOINTED
ledger       353 / 353 integrity records OK at acceptance
```

Accepted source/test receipts are bound to exactly four files:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/evaluation_report.py
resources/coding-tools-mcp/tests/test_orchestration_ledger.py
resources/coding-tools-mcp/tests/test_evaluation_report.py
```

Only **explicit, representative, identity-compatible paired runs** may enter regret analysis. Similar historical tasks and timestamp proximity are not accepted as counterfactuals.

Observed dimensions remain separate: quality is maximized; TTAR and total cost are minimized. A best observed action exists only when one action weakly Pareto-dominates the other on all observed dimensions and is strictly better on at least one. Typed outcomes preserve incomplete/trade-off/no-dominance states rather than forcing a winner.

Two fields deliberately remain unavailable today:

```text
predicted_policy_score = null  # unobserved_not_recorded
scalar_regret          = null  # unavailable_without_calibrated_utility_weights
```

No scalar utility is invented from arbitrary weights. Component/vector regret is reported only against a real observed Pareto-best comparable action.

Fresh current regret population:

```text
tagged_runs_scanned = 0

Mini: pair_count=0, task_class_count=0, status=hold, pareto_status=indeterminate_no_pairs
Luna: pair_count=0, task_class_count=0, status=hold, pareto_status=indeterminate_no_pairs
```

The implementation exposes governance starting points `min_pairs=10` and `min_task_classes=3`; these are **not** production statistical proof thresholds. The earlier methodology in this document still governs: an initial 10–20 pair cohort is an instrumentation/variance pilot, followed by power sizing and confirmatory analysis.

## E. Fresh canonical P1 baseline after P1.6 checkpoint

```text
python resources/coding-tools-mcp/scripts/report_current_ledger_baseline.py --workspace .
exit_code   = 0
captured_at = 2026-08-17T18:06:42.547322Z
```

### E.1 Current orchestration population

```text
run_count = 571
accepted  = 342
aborted   = 172
stale     = 49
completed = 7
active    = 1

REPLAN transitions      = 387
failure_observed events = 387
```

Largest failure-event classes are `CHECK_FAILED=106`, `SOL_REJECTED=50`, `PATCH_AMBIGUOUS=48`, `BUILD_VERIFICATION_FAILED=47`, and `BASE_DRIFT=40`. These are event counts, not independent task failure probabilities.

### E.2 Organic/model-free accepted-result economics

```text
accepted runs scanned               342
explicit model-route excluded        16
organic/model-free accepted         326
first-pass accepted                 206  (63.1902%)
repaired accepted                   120  (36.8098%)
replan count in repair population   219
first-pass TTAR p50                  52,110 ms
first-pass TTAR p90                 427,103 ms
repaired TTAR p50                   250,672 ms
repaired TTAR p90                 1,067,959 ms
repaired/first-pass p50 multiplier  4.810439x
repaired/first-pass p90 multiplier  2.500472x
```

> **Rework remains a dominant observed economic penalty: repaired median TTAR is about 4.81x first-pass median in the current model-free accepted cohort.** This remains observational cohort evidence, not treatment-effect proof.

Preflight avoided 70 known no-write patch failures before run creation: `PATCH_CONTEXT_AMBIGUOUS=45`, `PATCH_CONTEXT_NOT_FOUND=25`.

### E.3 Current route-selected population

```text
route_selected events = 698
deterministic = 665
sol_xhigh     = 17
mini          = 7
luna          = 6
terra         = 3
```

These route events are operational history, **not** a valid paired-efficacy dataset. P1.6 correctly refuses to use them as regret counterfactuals.

### E.4 Host-visible and causal host binding

```text
host turn spans                        51
spans with run binding                 18
overall host span binding rate         35.2941%
exact ledger correlations              18
causally eligible runs                  1
eligible runs with exact host span       1
eligible-run host coverage              1.0
coverage basis                          server_owned_host_correlation_marker_v1
```

Host-visible duration is `user_turn_visible -> first_assistant_visible`: p50 `352,466.7 ms`, p90 `2,106,995.6 ms`. It is a DOM measurement, **not provider/model latency**. The fresh `1/1` causal eligible coverage proves the marker path has produced an observed sample; it does not establish mature production coverage.

### E.5 Experimental efficacy population remains absent

```text
pair-tagged runs                        0
unique pair ids                         0
eligible experimental runs              0
controller observed runs                0
controller monetary-cost coverage      null
controller token-usage coverage        null
promotion_economics                    HOLD
quality outcome events                  0
experimental quality coverage          null
promotion_quality                      HOLD
Mini comparable regret pairs            0
Luna comparable regret pairs            0
routing/placement automatic activation false
```

This is the central P1 closure result: the project no longer lacks the *definitions* required for causal economics; it lacks the *representative treatment population* needed to estimate them.

## F. Comprehensive scientific interpretation of P1

P1 now proves that causal denominators are explicit; missing controller cost/tokens/quality stay unknown; historical uncertainty is retained instead of backfilled; lifecycle acceptance is not quality evidence; routing regret requires real representative comparable pairs; multi-objective trade-offs remain visible; and measurement readiness never grants routing/placement authority automatically.

P1 does **not** prove that Mini, Luna, server-first, or any automatic routing policy is better or worse than its baseline. It does not establish cost per accepted result, candidate quality non-inferiority, or model latency from host-visible DOM spans. It also does not causally resolve the 48 legacy UNKNOWN observations.

Current maturity classification:

```text
measurement definitions / semantics         HIGH
causal identity / denominator integrity      HIGH
unknown-preserving reporting                 HIGH
host-binding instrumentation                 OBSERVED, VERY SMALL CAUSAL N
controller economics population              ABSENT
experimental quality population              ABSENT
representative paired routing population     ABSENT
empirical regret estimation                  HOLD
automatic promotion readiness                HOLD
```

The correct transition is therefore:

```text
P1: build trustworthy measurement contracts        DONE
        ↓
P2+: create and analyze representative evidence    NEXT
```

not `P1 complete -> candidate policies proven`.

## G. Current ordered boundary after P1 closure

For current decision-making, stale P1 backlog entries earlier in this dated document are superseded as follows:

```text
P1.1  DONE  canonical current-ledger baseline
P1.2  DONE  causal host-binding denominator
P1.3  DONE  controller usage/cost coverage contract
P1.4  DONE  explicit quality-outcome contract
P1.5  DONE  prospective typed error taxonomy
P1.6  DONE  routing/placement regret reporting

P2.1  NEXT  stratified rework diagnosis
```

**P2.1 was not started by the P1 closure wave documented here.** The immediate research question after the P1 checkpoint is which rework strata dominate accepted-result economics and which existing intervention demonstrably reduces each causal rework class before more routing complexity is added.

## H. P1 final evidence summary

```text
P1.5 run / wave / proof
  9b6b067d90244a71bf5835ba04b5543b
  eda8944c29944a03a310fcfc8b51fa2c
  55eedfd1e57347c287e89c84dca87953

P1.6 run / wave / proof
  72616aa5d7a3409a83098d2243f48c48
  da847ca77d7a4d19bc4af6e1377b3e3d
  4ea919f98b544fb095457b2eac5da8b8

P1.6 state = CHECKPOINTED
P1.6 ledger integrity at acceptance = 353 / 353 OK
fresh canonical reporter = PASS / exit 0
captured_at = 2026-08-17T18:06:42.547322Z
```

No P1 closure evidence authorizes an implicit runtime restart, release publication, public tool-schema change, automatic route promotion, or P2 implementation.

---

**End of P1 closure addendum.**