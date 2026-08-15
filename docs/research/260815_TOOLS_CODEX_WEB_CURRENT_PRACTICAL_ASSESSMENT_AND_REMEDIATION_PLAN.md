# Tools-Codex-web — Đánh giá thực tiễn hiện tại và kế hoạch xử lý tồn đọng

**Ngày đánh giá:** 2026-08-15  
**Workspace quan sát:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**HEAD quan sát:** `dff81e251836666fc825c40bf86e4167afd29c39`  
**Upstream:** `origin/main`, ahead `0`, behind `0`  
**App:** `web-mcp-assistant 0.3.4`  
**Coding Tools MCP runtime:** `0.4.3`  
**PerformanceTrace:** v5  
**Smart profile:** `smart-v3` — **8 public tools**  
**Smart contract SHA-256:** `8fbee29c8de9788bedb09caf1b2fc4317f26ba7ab85ef35ebc4a7288558940d4`  
**Loại tài liệu:** practical engineering assessment / remediation plan / review checklist  

Tài liệu này là **bản đánh giá current-state để ra quyết định triển khai tiếp**, không thay thế audit lịch sử. Các snapshot cũ vẫn giữ vai trò evidence tại thời điểm chúng được ghi nhận.

---

# 0. Kết luận điều hành

## 0.1 Hệ thống hiện ở giai đoạn nào?

Tools-Codex-web hiện đã qua giai đoạn prototype và cũng đã qua phần lớn giai đoạn “build capability nền”. Core harness hiện có đủ các đặc điểm của một **coding execution/control plane nghiêm túc**:

- public tool surface nhỏ và ổn định;
- one-runtime desktop mutation authority;
- EOCL/write lease/final acceptance rõ ràng;
- durable run/wave/ledger state;
- idempotency có policy epoch và fault proof;
- retry/reconnect không mặc định tái phát side effect;
- source/runtime identity và PerformanceTrace đã materialize;
- stale/orphan authority được phát hiện và reconcile/terminalize;
- release provenance và Windows artifact proof đã có source implementation;
- large-result continuation đã được source-fence và fail-closed;
- semantic bridge và Code Mode đều giữ fail-closed khi prerequisite chưa đủ.

Đánh giá tổng thể:

```text
Core engineering architecture          mạnh / gần production-grade
Operational dogfood readiness          mạnh
Scientific / causal evidence           trung bình-khá
Release reproducibility                chưa đóng hoàn toàn
Semantic acceleration                  source-ready, live chưa active
Routing automation                     intentionally conservative
Arbitrary generated-code execution     chưa có security boundary đủ chuẩn
```

Nếu quy đổi thành maturity aid, không phải KPI:

| Trục | Điểm hiện tại | Nhận định |
|---|---:|---|
| Core coding/runtime | **8.7/10** | Đủ mạnh để dogfood thường xuyên. |
| Safety / fail-closed | **9.2/10** | Một trong các phần tốt nhất của hệ thống. |
| EOCL / authority / continuity | **9.1/10** | State, lease, replan, acceptance khá chặt. |
| Tool-surface discipline | **9.5/10** | Smart-v3 vẫn đúng 8 public tools. |
| Idempotency / replay safety | **9.1/10** | `task_epoch_v1`, current-policy gate đã đạt 100% trong observation gần nhất. |
| Observability / auditability | **8.7/10** | Trace v5, ledger, identity, policy epoch, provenance. |
| Release-proof maturity | **6.5/10** | Local proof mạnh nhưng exact-SHA independent CI chưa green và worktree còn dirty. |
| Semantic live maturity | **5.0/10** | Boundary source tốt; live provider vẫn chưa configured. |
| Routing causal maturity | **5.5/10** | Safety tốt; representative paired cohorts chưa đủ. |
| Code Mode execution maturity | **4.0/10** | Binding proxy tốt, worker isolation thật chưa có. |

### Phán quyết ngắn

> **Tiêu chí kiến trúc cốt lõi đã đạt phần lớn. Khoảng cách lớn nhất còn lại không phải thiếu tool/capability, mà là clean release truth, live activation truth và representative production evidence.**

---

# 1. Tiêu chí xây dựng và mức độ đáp ứng

## 1.1 “Ít tool nhưng tool mạnh” — ĐẠT

Live contract hiện giữ:

```text
smart-v3
tool_count = 8
```

Continuation, semantic localization, routing evaluator, Code Mode bindings, proof reuse và recovery đều được internalize, không tạo tool thứ 9.

**Đánh giá:** đạt đúng mục tiêu giảm schema/context burden và tránh tool-selection entropy.

**Hard rule tiếp tục giữ:** không tăng public tool count nếu chưa có independent evidence review chứng minh tool mới tạo accepted-work value lớn hơn cost của schema/selection complexity.

---

## 1.2 “Một mutation authority rõ ràng” — ĐẠT

Desktop hot path:

```text
Electron supervisor
    -> one Python Coding Tools MCP runtime
    -> Smart-v3 / EOCL / write lease
    -> deterministic proof
    -> Sol final acceptance
```

Rust không được phép âm thầm trở thành mutation authority thứ hai. Native semantic bridge là read-only accelerator.

**Đánh giá:** kiến trúc authority rõ, phù hợp mục tiêu tránh dual-control-plane.

---

## 1.3 “Retry phải semantic-safe, không gây duplicate mutation” — ĐẠT

Current policy epoch:

```text
task_epoch_v1
```

Observation gần nhất trước tài liệu này:

```text
required calls under current policy   43
required keyed                        43
coverage                           100%
target                              95%
```

Historical aggregate được giữ riêng và không dùng làm current gate.

Fault-proof hiện bao phủ các invariant quan trọng:

- exact duplicate => replay/at-most-once;
- same key + different semantic request => `IDEMPOTENCY_CONFLICT`;
- previous-process unknown outcome => `IDEMPOTENCY_OUTCOME_UNKNOWN`, không tự replay side effect;
- accept/reject authority path đi qua durable idempotency layer.

**Đánh giá:** tiêu chí này đã chuyển từ “cần xây” sang “cần tiếp tục quan sát policy epoch khi operation semantics thay đổi”.

---

## 1.4 “Fail closed, không fake capability” — ĐẠT RẤT TỐT

### Semantic provider

Live runtime hiện:

```text
available = false
reason = NATIVE_LSP_BINDING_NOT_CONFIGURED
```

Không có real Connector URL/project credential thì hệ thống không tự gắn nhãn native semantic active.

### Routing

Automatic activation/dispatch vẫn không được promote từ benchmark/synthetic evidence.

### Code Mode

Source đã có host-binding proxy nhưng worker isolation vẫn blocked. Hệ thống không gọi Job Object hoặc current Landlock là “secure sandbox”.

**Đánh giá:** đây là behavior đúng cho một harness có tham vọng long-running production use.

---

## 1.5 “Không tối ưu khi chưa có causal/evidence value” — ĐẠT

Proof-cache observation:

```text
eligible                  ~96
observed hits               1
saved ms                  999
```

Result-tail continuation observation:

```text
samples                     7
truncated calls             0
```

Do đó:

- proof-cache optimization tiếp tục HOLD;
- continuation implementation giữ lại vì source boundary/correctness tốt nhưng chưa claim production ROI;
- không tạo synthetic corpus chỉ để làm counters đẹp;
- Call Hierarchy không lên trước live semantic evidence;
- Terra không auto-promote từ tiny cohort.

**Đánh giá:** phù hợp thesis “optimize accepted work, not implementation existence”.

---

## 1.6 “State/audit phải truthful” — ĐẠT

Live recovery snapshot hiện tại:

```text
stale_orchestration_runs              0
unresolved_stale_orchestration_runs   0
reconciled_stale_orchestration_runs   2
orphaned_background_operations        0
orphaned_idempotency_records          0
agent_lanes_waiting_after_restart     0
```

Historical runs được terminalize bằng `ABORTED` có reason thay vì bị xóa.

**Đánh giá:** operational state hiện green về authority hygiene.

---

# 2. Phân loại maturity đúng cách

Mỗi capability phải được gắn một trong các lớp sau:

```text
SOURCE-COMPLETE     source có implementation
TESTED              focused/integration proof pass
LIVE-ACTIVE         process hiện tại đang dùng capability
EVIDENCE-PROVEN     representative accepted-work evidence chứng minh value
BLOCKED-EXTERNAL    prerequisite nằm ngoài source/runtime authority hiện tại
HOLD                cố ý chưa promote vì evidence/security chưa đủ
```

Current classification:

| Capability | Source | Tested | Live | Representative value | Current state |
|---|---|---|---|---|---|
| Smart-v3 8-tool contract | yes | yes | yes | yes | **KEEP CORE** |
| EOCL / write lease / ledger | yes | yes | yes | strong operational | **KEEP CORE** |
| Current-policy idempotency | yes | yes | yes | 100% observed coverage | **PASS** |
| Source-fenced continuation | yes | yes | available | workload not yet exercising it | **KEEP / MEASURE** |
| Exact-source Windows provenance | yes | yes | release path only | independent CI pending | **SOURCE-READY** |
| Native semantic bridge | yes | focused proof | no | none live | **BLOCKED PREREQUISITE** |
| Call Hierarchy | no/partial upstream concept | n/a | no | none | **HOLD** |
| Routing-v2 promotion | yes | safety tested | shadow/explicit | insufficient causal cohort | **HOLD** |
| Code Mode host bindings | yes | yes | not exposed as Code Mode | n/a | **PREREQUISITE READY** |
| Code Mode worker execution | no qualifying backend | no | no | none | **SECURITY HOLD** |
| Proof-cache accelerator | yes | yes | yes | negligible observed ROI | **HOLD OPTIMIZATION** |

---

# 3. Điểm mạnh thực tiễn hiện tại

## 3.1 Coding task execution path đã đủ khỏe để dogfood

Các phần đang có confidence cao:

```text
workspace inspection
search/localization fallback
code/file mutation
command lifecycle
background command tracking
task continuity
run/wave state machine
write authority
replan semantics
proof lineage
idempotent replay control
stale-state reconciliation
runtime/source identity
bounded result shaping
local regression suites
```

Full Python MCP regression gần nhất:

```text
274 passed
1 skipped
16 subtests passed
```

Root Node/Electron baseline gần nhất:

```text
99 / 99 PASS
```

Focused Windows Rust semantic-identity package check đã PASS.

Đây là mức bằng chứng vượt xa prototype smoke test.

---

## 3.2 Safety posture tốt hơn feature breadth

Hệ thống hiện chủ động từ chối một số trạng thái chưa đủ chuẩn thay vì “best effort enable”:

- native semantic không configured => text fallback;
- Code Mode thiếu real isolation => OFF;
- unknown mutation outcome => fail closed;
- routing evidence non-representative => no promotion;
- exact-source release truth chưa có => không gọi release green;
- proof cache miss => chạy proof thật, không reuse lỏng fingerprint.

Đây là nền tảng tốt để mở rộng sau này mà không tích lũy silent correctness debt.

---

# 4. Những vấn đề tồn đọng thực sự

## 4.1 P0 — Worktree chưa phải clean reproducible release revision

### Hiện trạng

`main` đang đồng bộ `origin/main`, nhưng worktree dirty với nhiều lớp thay đổi:

1. accepted source work;
2. volatile `.coding-tools/*` runtime evidence;
3. CI/release documentation/scripts;
4. semantic/Code Mode changes;
5. concurrent Operator Control Panel/UI work.

Do đó hệ thống đang được đánh giá thực tế là:

```text
HEAD dff81e...
+ accepted worktree source changes
+ live runtime state
```

chứ chưa phải một immutable Git revision có thể checkout lại và tái tạo toàn bộ behavior.

### Rủi ro

- không thể bind independent CI tới exact candidate source;
- provenance manifest không đại diện một clean candidate;
- khó tách accepted wave khỏi concurrent UI work khi commit;
- runtime evidence tiếp tục làm Git noise nếu không được phân lớp đúng.

### Phương án xử lý

**Wave R0 — Worktree classification + candidate freeze**

1. Chụp HEAD + upstream + worktree fingerprint.
2. Phân tất cả dirty paths thành:
   - `CANDIDATE_SOURCE`;
   - `CONCURRENT_UNRELATED`;
   - `VOLATILE_RUNTIME_EVIDENCE`;
   - `DOCUMENTATION/REPORT`.
3. Không `git add .`.
4. Review candidate diff theo subsystem.
5. Chạy exact-worktree regression.
6. Chỉ khi user cho phép commit: commit explicit path list.
7. Sau commit, verify clean/known-dirty candidate state và exact SHA.

### Acceptance

```text
candidate source set explicit
unrelated changes excluded or separately classified
no unresolved conflict
full required local proof PASS
candidate exact SHA exists
```

### Stop condition

Dừng nếu bất kỳ dirty file nào không xác định được owner/scope hoặc có concurrent source write mới trong lúc freeze.

---

## 4.2 P0 — Exact-SHA independent CI chưa green

### Hiện trạng

Known GitHub run `31852696347` cho baseline SHA không chạy test steps; Linux/Windows jobs đều failure pre-run với empty steps/runner allocation issue.

Điều được phép kết luận:

```text
NO independent green CI proof
```

Điều không được phép kết luận:

```text
source regression
```

### Phương án xử lý

**Wave R1 — CI truth**

Prerequisite ngoài source: GitHub account/billing/spending limit phải được unblock.

Sau đó:

1. Push/trigger exact candidate SHA khi được user authorize.
2. Verify jobs bind đúng SHA.
3. Verify jobs thật sự acquire runner.
4. Verify required Linux + Windows steps execute.
5. Classify failures thành infra/test/package/release.
6. Capture canonical proof run ID và artifact hashes.

### Acceptance

```text
runner allocated
required steps non-empty
Linux gate PASS
Windows gate PASS
candidate SHA exact match
release/provenance artifacts bind same SHA
```

### Rollback

Không “rebuild cùng version” sau proof. Nếu source thay đổi, tạo SHA/candidate mới và prove lại.

---

## 4.3 P1 — Native semantic chưa active live

### Hiện trạng

Source boundary đã có:

```text
loopback-only endpoint policy
project credential
project/workspace binding
read-only action allowlist
bounded request/response
no proxy / no redirect
fail-closed validation
```

Nhưng live runtime:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
```

### Tác động thực tế

Không làm coding correctness mất nền tảng vì text fallback vẫn hoạt động, nhưng giảm:

- symbol navigation precision;
- definition/reference localization;
- cross-file context efficiency;
- semantic telemetry;
- khả năng đánh giá Call Hierarchy;
- evidence cho semantic ROI.

### Phương án xử lý

**Wave S0 — Real semantic activation**

Chỉ bắt đầu khi có:

```text
real Rust Connector instance
real project-scoped credential/grant
explicit local endpoint configuration
operational permission to reload/restart runtime
```

Steps:

1. Start/identify intended Rust Connector instance.
2. Bind credential file + loopback URL qua existing intended configuration path.
3. Restart/fresh-load Python runtime khi được authorize.
4. Verify runtime source identity.
5. Smoke symbol/definition/reference path.
6. Negative tests: bad credential, workspace mismatch, invalid action/path.
7. Verify provider unavailable still falls back deterministically.
8. Collect live semantic metrics on real tasks.

### Acceptance

```text
semantic available > 0
semantic attempted > 0
semantic handled > 0
workspace escape succeeds = 0
unauthenticated request succeeds = 0
mutation through semantic path = 0
fallback failure = 0
public tool count remains 8
```

### Stop condition

Dừng ngay nếu activation đòi generic Rust tool passthrough, credential fabrication, second mutation authority hoặc non-loopback endpoint không được policy cho phép.

---

## 4.4 P1 — Code Mode còn thiếu security backend thật

### Đã đạt

Internal host-binding proxy source-ready:

```text
read_text
list_files
search_text
semantic_search
```

Các fence đã có:

- primary workspace only;
- absolute/drive/UNC/home/`..` denied;
- symlink escape denied;
- NTFS ADS denied;
- Windows reserved device names denied;
- request/response byte caps;
- exact operation/argument allowlist;
- semantic-return path revalidation.

### Chưa đạt

Không có qualifying worker isolation backend.

Các primitive hiện hữu không đủ:

```text
Windows Job Object  -> process lifecycle control only
Linux Landlock      -> current policy primarily write confinement
Python subprocess   -> not a security sandbox
Node worker/VM      -> same-process capability exposure risk
```

### Security contract bắt buộc

Backend tương lai phải chứng minh cùng lúc:

```text
no_direct_filesystem
no_network
no_inherited_environment_secrets
no_unrestricted_subprocess
bounded_framed_host_binding_only_ipc
```

### Khuyến nghị kiến trúc

Ưu tiên evaluate một capability-oriented isolated runtime, ví dụ WASM/WASI runtime có explicit host imports hoặc OS sandbox thật sự. Không tự dựng pseudo-sandbox từ Job Object + env clearing rồi tuyên bố secure.

### Phương án xử lý

**Wave C0 — Backend feasibility spike, không activation**

1. Chọn tối đa 2 backend candidate.
2. Threat-model filesystem/network/env/process/IPC escape.
3. Prototype outside production activation path.
4. Attack-oriented tests trước performance benchmark.
5. Chỉ sau security acceptance mới tích hợp binding protocol hiện hữu.

### Acceptance trước khi merge backend

```text
all five guarantees proven
escape tests PASS
worker cannot call arbitrary Runtime tools
worker cannot inspect raw environment
worker cannot spawn unrestricted child process
only framed host binding protocol reachable
resource/time/output limits enforced
Code Mode default remains OFF until separate promotion
```

---

## 4.5 P1/P2 — Routing-v2 vẫn thiếu causal production evidence

### Hiện trạng

Routing implementation/safety đã mạnh:

- route requested/resolved telemetry;
- provenance filters;
- promotion readiness;
- synthetic/benchmark exclusion;
- `automatic_activation=false`;
- Terra explicit/shadow.

Nhưng selection bias vẫn tồn tại nếu chỉ nhìn observational route cohorts.

### Phương án xử lý

**Wave E0 — Paired accepted-task experiment**

Task pair phải giữ:

```text
same task
same base SHA
same environment
same acceptance criteria
actual route A
actual route B
```

Minimum report per class:

```text
n
first-pass acceptance
TTA paired delta
repair/replan delta
provider cost / accepted
model-visible bytes / accepted
critical defect escape
```

### Promotion gate đề xuất

Không auto-promote khi thiếu bất kỳ điều nào:

```text
representative n
multiple task classes
quality non-regression
critical defect evidence
provider cost completeness
TTA completeness
```

Terra tiếp tục shadow/explicit cho tới một decision riêng.

---

## 4.6 P2 — Call Hierarchy chưa phải priority

Call Hierarchy có concept fit tốt nhưng hiện dependency chưa thỏa.

Correct order:

```text
activate semantic provider
-> collect live semantic attempts/handled
-> identify cross-file impact workloads
-> bounded Call Hierarchy experiment
```

Không port thêm Rust code trước khi semantic live path chứng minh nó được gọi và có bottleneck thực.

---

## 4.7 P2 — Proof cache không đáng tối ưu thêm lúc này

Observed:

```text
1 hit
~999 ms saved
~96 eligible observations
```

Kết luận:

- exact fingerprint semantics phải giữ;
- không broaden fingerprint để chase hit-rate;
- không dành P0/P1 engineering capacity cho cache optimization.

Revisit chỉ khi representative opportunity window chứng minh cumulative saved TTA đủ lớn.

---

## 4.8 P2 — Continuation đã implement nhưng ROI chưa được workload xác nhận

Source-fenced continuation đã giải quyết correctness boundary, nhưng current observed result-tail samples chưa có truncation thật.

Do đó trạng thái đúng là:

```text
implementation: KEEP
correctness boundary: PROVEN
production ROI: UNPROVEN
```

Không cần thêm framework. Chỉ tiếp tục thu telemetry tự nhiên trên large-diff/large-evidence tasks.

---

# 5. Risk register hiện tại

| ID | Risk | Severity | Likelihood | Hiện trạng | Mitigation |
|---|---|---:|---:|---|---|
| R1 | Dirty worktree không map được về immutable release candidate | **High** | High | Open | Candidate classification + explicit commit boundary |
| R2 | Exact-SHA CI không chạy vì external account/runner gate | **High** | High | External blocker | Unblock account, rerun exact candidate |
| R3 | Source/runtime mismatch khi source thay đổi nhưng process chưa reload | Medium | Medium | Known | Runtime/source identity + explicit activation proof |
| R4 | Semantic feature được gọi “active” khi binding chưa configured | Medium | Medium | Controlled | Keep fail-closed status + activation checklist |
| R5 | Routing promoted từ tiny/synthetic cohort | High | Medium | Prevented by source | Keep automatic activation OFF |
| R6 | Code Mode bật trên pseudo-sandbox | **Critical** | Medium nếu feature pressure tăng | Prevented | Security backend contract + attack tests |
| R7 | Proof-cache fingerprint bị nới để tăng hit-rate | High correctness risk | Low | HOLD | Exact fingerprint hard invariant |
| R8 | Rust/Python ownership drift tạo mutation plane thứ hai | High | Low-Med | Role contract exists | Preserve explicit subsystem ownership |
| R9 | Runtime evidence files bị nhầm thành source/release state | Medium | Medium | Controlled | Keep volatile evidence classification |
| R10 | Concurrent UI/source work bị trộn vào commit của reliability waves | High | Medium | Open while dirty | Explicit path staging, no `git add .` |

---

# 6. Dependency graph xử lý

```text
[CURRENT WORKTREE]
       |
       v
[R0 classify + freeze candidate]
       |
       v
[clean exact candidate SHA]
       |
       +--------------------+
       |                    |
       v                    v
[R1 exact-SHA CI]     [release provenance]
       |                    |
       +---------+----------+
                 |
                 v
          [RELEASE-READY CORE]
                 |
       +---------+----------+
       |                    |
       v                    v
[S0 semantic live]   [E0 routing cohorts]
       |                    |
       v                    |
[semantic evidence]         |
       |                    |
       v                    |
[Call Hierarchy exp]        |
       +----------+---------+
                  |
                  v
          [KEEP / DEMOTE / REMOVE]

Parallel long-horizon track:
[C0 Code Mode security backend feasibility]
    -> no dependency on release promotion
    -> must not block core release
```

Critical path tới một release candidate mạnh **không cần** Call Hierarchy, Terra promotion hay Code Mode.

---

# 7. Kế hoạch triển khai chi tiết theo wave

## Wave 0 — Candidate truth / worktree normalization

**Goal:** biến current accepted work thành một candidate có boundary rõ.

Actions:

1. Capture `HEAD`, upstream, worktree fingerprint.
2. Generate file classification manifest.
3. Separate runtime evidence from source.
4. Separate concurrent UI/operator-panel work from P0/P1/P5 source.
5. Review only candidate diff.
6. Run `git diff --check` + full Python + root Node + required Rust focused checks.
7. Present explicit commit set for approval.

Exit criteria:

```text
all dirty source files classified
no conflict
no unknown owner
candidate regression green
```

No commit/push without explicit user authorization.

---

## Wave 1 — Immutable candidate + exact-source proof

**Goal:** tạo exact SHA đại diện đúng behavior đã proof.

Actions after authorization:

1. Explicit-path commit candidate source only.
2. Verify commit contains intended paths and excludes volatile `.coding-tools/*` unless explicitly desired.
3. Verify `HEAD == intended candidate SHA`.
4. Verify upstream relation before push.
5. Push only if explicitly authorized.
6. Record candidate SHA in release/provenance workflow.

Exit:

```text
candidate SHA immutable
local proof bound to that candidate/worktree
release manifest can reference exact source
```

---

## Wave 2 — Independent CI truth

**Prerequisite:** GitHub runner/account gate resolved.

Actions:

1. Trigger exact candidate workflow.
2. Confirm jobs acquire runners.
3. Linux full/canonical gates.
4. Windows selected Rust + Node/Python/package gates.
5. Inspect exact-source artifact/provenance.
6. Record run/job/proof IDs.

Exit:

```text
CI GREEN for exact candidate SHA
artifacts/provenance bind same SHA
```

---

## Wave 3 — Native semantic activation

**Prerequisite:** real project-bound Rust Connector configuration + permission to restart/reload.

Actions:

1. Configure loopback endpoint and credential-file binding.
2. Fresh-load runtime.
3. Verify source/runtime identity match.
4. Positive semantic smoke.
5. Negative authorization/workspace/path tests.
6. Fallback test.
7. Real-task observation window.

Exit:

```text
semantic_attempted > 0
semantic_handled > 0
security negative tests = 0 unauthorized success
fallback healthy
```

---

## Wave 4 — Evidence accumulation, not feature building

### Routing

Collect paired real tasks until promotion-readiness has representative samples.

### Continuation

Wait for natural truncation/large-result tasks; capture re-read/TTA impact.

### Proof cache

Continue passive opportunity study.

### Handoff

Measure resume success / work avoided; do not expand unless long-task evidence supports it.

Exit is **decision quality**, not code volume.

---

## Wave 5 — Bounded experiments

Only after prerequisites:

- Call Hierarchy on qualified cross-file tasks;
- route A/B paired trials;
- optionally Terra cross-file experiment if representative evidence justifies cost.

Every experiment must define keep/kill rule before execution.

---

## Wave 6 — Simplification

For each accelerator:

```text
KEEP
KEEP BUT DEMOTE PERFORMANCE CLAIM
FIX
REMOVE
DEFER
```

This wave is mandatory: evidence program must be allowed to delete complexity, not only justify more complexity.

---

# 8. Acceptance criteria tổng thể

Không gọi hệ thống “release-ready strong” cho tới khi các gate sau đúng:

## Core correctness

- full required local regression PASS;
- no unresolved merge conflict;
- Smart-v3 tool count = 8;
- write-without-lease = 0 known violations;
- required idempotency current-policy coverage >= target with sample count;
- no known duplicate required side effect.

## Runtime truth

- runtime/source identity visible;
- source-loaded runtime relation understood;
- no unexplained stale/orphan authority;
- volatile runtime evidence not confused with source revision.

## Release truth

- exact candidate SHA exists;
- CI jobs actually execute;
- Linux/Windows required gates pass;
- exact-source provenance manifest produced;
- candidate bytes smoked are the bytes published/distributed;
- raw runtime/benchmark snapshots excluded from product package.

## Semantic truth

Do not call semantic “active” until:

- provider availability observed live;
- nonzero attempts/handled queries;
- negative auth/workspace tests pass;
- deterministic fallback proven.

## Routing truth

Do not auto-promote until:

- representative paired cohort;
- quality non-regression;
- critical defect evidence complete;
- TTA/cost evidence complete;
- provenance trusted.

## Code Mode truth

Do not enable until a real worker backend proves all five security guarantees and attack tests pass.

---

# 9. Stop / rollback rules

## General

Any correctness, security, source-consistency or proof-truth violation overrides performance gain.

## Semantic

Disable binding and return to text fallback if:

- credential scope ambiguous;
- workspace mismatch can succeed;
- response unbounded;
- bridge exposes mutation/generic tool dispatch.

## Routing

Keep deterministic-first / shadow if:

- cohorts too small;
- selection bias unresolved;
- defect/repair rate regresses;
- cost data incomplete.

## Code Mode

No partial-security activation. If backend cannot prove one of five guarantees, status remains blocked.

## Release

If source changes after proof, prior artifact proof does not carry forward. New SHA => new proof.

---

# 10. Việc KHÔNG nên làm tiếp lúc này

Không nên ưu tiên:

```text
thêm public tool
merge upstream WebCodex wholesale
mở Terra auto-routing
Call Hierarchy trước semantic live activation
nới proof-cache fingerprint
xây framework continuation mới
rewrite Rust/Python chỉ vì có overlap
bật Code Mode bằng subprocess/VM không phải sandbox
coi local PASS là CI green
coi benchmark/synthetic routing là production evidence
```

Các hành động trên hoặc không giải bottleneck hiện tại, hoặc làm tăng risk/complexity trước evidence.

---

# 11. Ưu tiên thực thi đề xuất

## NOW — P0

```text
1. Worktree classification / candidate freeze
2. Exact candidate local proof
3. Explicit candidate commit boundary (chỉ khi được authorize)
4. Unblock GitHub CI account/runner
5. Exact-SHA independent CI + provenance
```

## NEXT — P1

```text
6. Real Rust Connector + semantic binding
7. Authorized runtime activation/restart
8. Live semantic workload measurement
9. Paired routing cohort accumulation
```

## LATER — P2

```text
10. Call Hierarchy experiment
11. Routing promotion decision
12. Code Mode security-backend feasibility/integration
```

## HOLD

```text
proof-cache optimization
Terra automatic routing
additional public tools
upstream convenience features without demand evidence
```

---

# 12. Definition of Done theo ba cấp

## Level A — Strong dogfood core

**Hiện tại: gần đạt / thực tế đã dùng được.**

Require:

- core tests green;
- authority/recovery healthy;
- deterministic fallback intact;
- no known critical correctness issue.

## Level B — Clean release-ready core

**Hiện tại: chưa đạt hoàn toàn.**

Require thêm:

- clean immutable candidate SHA;
- exact-SHA independent CI green;
- provenance exact candidate;
- package sanitation verified;
- no unexplained concurrent/uncommitted candidate source.

## Level C — Evidence-driven autonomous accelerator stack

**Hiện tại: chưa đạt và không nên giả đạt.**

Require thêm:

- semantic live proven;
- routing representative paired evidence;
- Code Mode real isolation nếu muốn arbitrary code execution;
- accelerators chứng minh accepted-work ROI.

---

# 13. Review checklist cho chủ dự án

Khi kiểm tài liệu/roadmap này, cần quyết định rõ các câu sau:

- [ ] Có đồng ý coi **clean release candidate + exact-SHA CI** là blocker P0 lớn nhất hiện tại không?
- [ ] Có đồng ý tiếp tục giữ `smart-v3 = 8 tools` làm hard invariant không?
- [ ] Có đồng ý semantic activation phải dùng **real Rust Connector + real credential**, không mock production binding không?
- [ ] Có đồng ý Call Hierarchy chỉ bắt đầu sau khi semantic live có nonzero workload không?
- [ ] Có đồng ý Routing-v2/Terra tiếp tục shadow/explicit cho tới representative paired evidence không?
- [ ] Có đồng ý Code Mode không được bật bằng Job Object/current Landlock/subprocess-only pseudo-sandbox không?
- [ ] Có muốn đầu tư một security-backend spike riêng cho Code Mode, hay tiếp tục defer?
- [ ] Có muốn tách concurrent Operator Control Panel/UI changes thành commit riêng trước candidate reliability commit không?
- [ ] Sau khi review, có authorize commit/push candidate source hiện tại hay chưa?
- [ ] GitHub account/billing/runner prerequisite có thể được xử lý để lấy exact-SHA CI không?

---

# 14. Kết luận cuối

Kiến trúc hiện tại đang đi đúng tiêu chí ban đầu: **lean, controlled, evidence-driven và fail-closed**. Phần đáng lo nhất không còn là thiếu capability nền. Phần cần xử lý tiếp là làm cho source, runtime, CI và artifact trở thành **một chuỗi bằng chứng khép kín**.

North-star tiếp theo nên là:

```text
DIRTY ACCEPTED WORKTREE
        ->
CLEAN EXACT CANDIDATE SHA
        ->
INDEPENDENT EXACT-SHA PROOF
        ->
LIVE SEMANTIC ACTIVATION
        ->
REPRESENTATIVE ACCEPTED-WORK EVIDENCE
        ->
PROMOTE / KEEP / REMOVE BASED ON CAUSAL VALUE
```

Không nên quay lại mode “thêm capability vì capability trông hữu ích”.

> **Core system is strong enough to operate. The next maturity jump comes from release truth, live activation truth, and causal evidence — not from increasing tool count or feature breadth.**

---

## Appendix A — Current live snapshot used by this document

```text
workspace                         E:\DEV\Tools-Codex-web
branch                            main
HEAD                              dff81e251836666fc825c40bf86e4167afd29c39
upstream                          origin/main
ahead / behind                    0 / 0
worktree                          dirty
runtime version                   0.4.3
PerformanceTrace                  v5
idempotency epoch                 task_epoch_v1
Smart-v3 tools                    8
Smart contract SHA                8fbee29c8de9788bedb09caf1b2fc4317f26ba7ab85ef35ebc4a7288558940d4
semantic live                     false
semantic reason                   NATIVE_LSP_BINDING_NOT_CONFIGURED
stale runs                        0
unresolved stale runs             0
orphan background operations      0
orphan idempotency records        0
```

### Source/runtime caveat

Latest source contains newer Code Mode readiness metadata than the currently loaded process reports. Therefore Code Mode source status and live metadata must remain distinguished until an authorized runtime reload/restart occurs.

## Appendix B — Evidence references inside repository

```text
docs/research/260815_TOOLS_CODEX_WEB_PRACTICAL_FIT_AUDIT_OF_ADVISORY_RECOMMENDATIONS.md
docs/research/260815_TOOLS_CODEX_WEB_CURRENT_IMPLEMENTATION_DELTA.md
docs/RUST_PYTHON_PRODUCT_ROLES.md
.coding-tools/orchestration/ledger.sqlite3
.coding-tools/performance.json
.coding-tools/task-history.json
.coding-tools/task-state.json
```

Volatile `.coding-tools/*` files are runtime evidence, not source-release inputs.
