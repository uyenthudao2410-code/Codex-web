# P2/P3 Remaining Operational Hardening — Kế hoạch triển khai đã hiệu chỉnh theo trạng thái thực tế

**Dự án:** `E:\Github\Tools-Codex-web`  
**Ngày lập kế hoạch:** 2026-08-16  
**Cập nhật theo live audit:** 2026-08-16 16:38 +07:00  
**Baseline source tại thời điểm audit:** `main`, `HEAD == origin/main == 415cb658f43cbd1d2456f65bf5649ed52b87ab25`  

**Post-closure planning audit:** 2026-08-16 18:14:53 +07:00, `HEAD == origin/main == cf6cb6ddbf29d90515d003ce72490ffda985c37f`

**R1/R2/R5 implementation audit:** 2026-08-16 19:18 +07:00, source vẫn ở `cf6cb6ddbf29d90515d003ce72490ffda985c37f`; worktree có implementation chưa commit và concurrent changes ngoài scope được giữ nguyên.

**Cách sử dụng tài liệu:** Sections 1–25 là kế hoạch/lịch sử closure đã thực hiện; Section 26 là kế hoạch authoritative cho phần production evidence và race-hardening còn lại.

**Runtime quan sát:** Coding Tools MCP `0.4.3`, `smart-v3`, public tool count `8`  
**Tài liệu nền:** `docs/research/260816_P2-P3-orchestration-resource-analysis.md`  
**Mục tiêu:** hoàn thiện phần operational hardening còn lại của P2/P3 bằng cách tận dụng tối đa implementation hiện đã có, chỉ bổ sung các gap thực sự còn mở, tránh viết lại LSP lifecycle/resource governor/EOCL đã tồn tại, và chứng minh kết quả bằng operational soak có thể lặp lại.

---

# 1. Executive summary

Sau khi đối chiếu trực tiếp implementation plan cũ với source/runtime thực tế của repository, hướng kiến trúc tổng thể vẫn đúng nhưng một số giả định đã lỗi thời.

Điểm quan trọng nhất là: **không nên triển khai nguyên xi plan cũ**.

Một số capability mà tài liệu trước coi là “chưa có” thực tế đã tồn tại:

- `LspSupervisor` đã có `idle_ttl`.
- `LspSupervisor` đã có background idle reaper.
- idle cleanup đã kiểm tra `pending_count() == 0` trước khi drain.
- `ServerInstance` đã cập nhật `last_used` tại request start/completion.
- LSP child đã được quản lý bằng `webcodex_process::ManagedChild`.
- Windows backend đã dùng private Job Object với `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
- LSP shutdown đã terminate/reap đúng owned tree.
- Coding MCP đã có `LIGHT/MEDIUM/HEAVY` classification.
- Coding MCP đã có unique HEAVY admission per checkout.
- Coding MCP đã có host-memory gate, foreign-heavy detection và quiescence checks.
- semantic single-file scope đã dùng `document_symbols`.
- workspace semantic đã có cold concurrency `1`, warm concurrency bounded.
- Connector đã có `semantic_lsp_warm` state cơ bản.

Do đó phần còn thiếu thực sự tập trung vào bốn nhóm:

1. **Chứng minh idle teardown hiện có hoạt động đúng trong topology live**, thay vì viết lại lifecycle.
2. **Bổ sung working-set/process telemetry và memory-pressure policy cho persistent LSP**.
3. **Nối native semantic admission với resource governor hiện có để chặn Cargo/full-test ↔ cold LSP HEAVY overlap theo cả hai chiều**.
4. **Chạy authoritative soak cold → warm → idle → stopped → cold restart + conflict/fallback**, rồi chỉ bổ sung durable persistent ownership nếu soak/restart chứng minh thật sự cần.

Thứ tự triển khai đã hiệu chỉnh:

```text
Recovery Phase 3B accepted/checkpointed
        ↓
Wave 1 — Prove existing LSP idle lifecycle
        ↓
Wave 2 — LSP process/memory telemetry + pressure policy
        ↓
Wave 3 — Native semantic ↔ HEAVY governor integration
        ↓
Wave 4 — Ownership/restart proof
        ↓
        ├─ nếu existing ownership đủ → không thêm schema
        └─ nếu không đủ → bổ sung CONNECTOR_PROFILE ownership tối thiểu
        ↓
Wave 5 — Authoritative operational soak
        ↓
Wave 6 — Disk/cache hygiene
        ↓
Wave 7 — Final operational baseline + EOCL delivery
```

---

# 2. Trạng thái thực tế của repository tại thời điểm audit

## 2.1. Git/source baseline

Tại thời điểm đối chiếu:

```text
branch      = main
HEAD        = 415cb658f43cbd1d2456f65bf5649ed52b87ab25
origin/main = 415cb658f43cbd1d2456f65bf5649ed52b87ab25
ahead       = 0
behind      = 0
```

Repository không clean vì Recovery Phase 3B và runtime evidence vẫn đang thay đổi.

Các source/worktree path Recovery nổi bật đang dirty/untracked gồm:

```text
docs/RECOVERY_HOST.md
electron/main.js
electron/services/componentRevision.js
electron/services/config.js
electron/services/recoveryHost.js
electron/services/runtimePaths.js
package.json

electron/services/recoveryPlaneService.js
resources/recovery-mcp/recovery_mcp.py
resources/recovery-supervisor/recovery-supervisor.ps1
tests/recovery-plane.test.js
tests/recovery-supervisor.test.js
```

Ngoài ra `.coding-tools` tiếp tục có volatile evidence, đặc biệt:

```text
.coding-tools/orchestration/ledger.sqlite3
.coding-tools/performance.json
.coding-tools/task-state.json
.coding-tools/task-history.json
.coding-tools/evaluation/...
```

**Policy dự án hiện hành:** `.coding-tools/orchestration/ledger.sqlite3` là canonical runtime evidence nhưng không phải source-code input. Phải giữ nguyên, đọc làm bằng chứng và ghi observation window/checksum cần thiết vào report; không selective-stage hoặc commit SQLite/WAL/SHM cùng source delivery.

## 2.2. Runtime baseline

Live runtime đã xác nhận:

```text
runtime_version      = 0.4.3
profile              = smart-v3
public tool count    = 8
semantic provider    = webcodex_native_lsp
semantic read_only   = true
heavy concurrency    = 1 per checkout
```

Coding Tools MCP hiện đã expose/thi hành:

- managed process jobs;
- HEAVY checkout admission;
- host pressure check;
- foreign-heavy detection;
- quiescence reconciliation;
- EOCL RUN/WAVE state;
- proof/acceptance gate.

## 2.3. Recovery Phase 3B vẫn là hard blocker

Trong evidence window gần nhất, Recovery implementation đã có nhiều proof xanh nhưng run vẫn từng bị ChatWeb reject vì canonical acceptance receipt/modified-file scope chưa đủ rõ cho Recovery MCP Python và sau đó chuyển `REPLAN`.

Vì vậy **không được mở P2/P3 resource write wave trên authoritative checkout cho tới khi Recovery Phase 3B có accepted successor checkpoint hoặc explicit terminal isolation**.

Điều kiện vào Wave 1:

```text
Recovery run = CHECKPOINTED
OR explicit terminal ABORTED/isolated handoff
AND no active Recovery write lease
AND no active managed HEAVY job
AND no Recovery mutation wave đang EXECUTING/PROVING/ACCEPTING
```

---

# 3. Đối chiếu plan cũ với implementation thật

| Hạng mục plan cũ | Trạng thái thực tế | Hành động mới |
|---|---|---|
| LSP chưa có idle teardown | Đã có `idle_ttl`, background reaper, pending guard, owned-tree shutdown | Không viết lại; audit + live proof |
| LSP chưa có process-tree ownership | Đã dùng `ManagedChild`; Windows có Job Object | Không viết lại process ownership |
| Global HEAVY governor chưa có | Đã có classification, unique slot, host pressure, foreign heavy, quiescence | Chỉ mở rộng admission signal cho native semantic |
| Single-file semantic còn global | Đã dùng `document_symbols` | Closed |
| Workspace cold/warm concurrency chưa có | Đã có cold `1`, warm bounded | Closed, chỉ regression |
| LSP memory soft/hard policy | Chưa thấy working-set policy trực tiếp trong supervisor | Gap thật — triển khai |
| Persistent profile ownership durable | Chưa có model rõ như `CONNECTOR_PROFILE` trong EOCL ledger | Chỉ triển khai nếu ownership proof thất bại |
| Cargo↔LSP conflict | Cargo-side đã nhìn foreign rust-analyzer; semantic-side chưa gate đủ trước native start | Gap thật — triển khai hai chiều |
| Soak cold/warm/idle/restart | Chưa có authoritative matrix khép kín | Gap thật — bắt buộc |
| Disk/cache lifecycle | Chủ yếu guidance | Làm sau RAM/process lifecycle |

---

# 4. Protected invariants

## 4.1. Correctness

- Text fallback phải tiếp tục hoạt động khi native LSP unavailable, denied hoặc draining.
- Một lỗi native semantic không được làm context localization toàn task fail nếu text path vẫn đủ.
- Single-file request không được quay lại `workspace_symbols`.
- Workspace query order phải được giữ.
- Project-relative path only.
- Không làm suy yếu semantic result sanitation.

## 4.2. Security

- Không log credential contents hoặc bearer token.
- Không expose credential-file path trong durable telemetry.
- Wrong token vẫn reject.
- Workspace mismatch vẫn fail closed.
- Absolute path/traversal vẫn reject theo contract hiện tại.
- Không dùng global process-name kill.

## 4.3. Orchestration

- Mutation chỉ xảy ra trong EOCL wave có write authority hợp lệ.
- Không mở writer mới khi wave khác còn `ACCEPTING`.
- `REPLAN` phải thay strategy/evidence/scope.
- Không sửa SQLite ledger trực tiếp ngoài control plane.
- Proof reuse chỉ trên exact fingerprint tương ứng.

## 4.4. Public compatibility

- `smart-v3` public tool count phải vẫn là `8`.
- Không thêm public MCP tool chỉ để expose LSP resource internals.
- Resource telemetry phải là internal/operator-facing state.

## 4.5. Git/worktree

- Không trộn Recovery Phase 3B source với P2/P3 LSP hardening trong cùng implementation wave.
- Không reset/restore unrelated work.
- Final delivery selective stage.
- Không stage `.coding-tools` runtime projections; source delivery chỉ record evidence window, fingerprint và checksum của report cần thiết.

---

# 5. Kiến trúc hiện hữu cần tái sử dụng

## 5.1. Existing LSP lifecycle

`crates/webcodex-runner/src/webcodex_runner/lsp/supervisor.rs` đã có cấu trúc:

```text
LspSupervisorConfig
  request_timeout
  initialize_timeout
  shutdown_timeout
  idle_ttl
  background_reaper
```

Slot state hiện tại:

```text
Starting
Running(ServerInstance)
Failed(LspError)
```

Idle cleanup hiện đã tương đương:

```text
if Running
and pending_count() == 0
and now - last_used >= idle_ttl:
    remove slot
    shutdown owned process tree
```

Background reaper cũng đã tự start theo demand và dùng `Weak` reference để không pin supervisor vô hạn.

## 5.2. Existing process ownership

`webcodex-process` đã định nghĩa `ManagedChild` ownership cho toàn descendant tree.

Windows backend:

```text
private Job Object
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
TerminateJobObject
wait/reap owned tree
```

Do đó không được tạo thêm một Windows process-tree mechanism thứ hai cho LSP.

## 5.3. Existing semantic cold/warm behavior

Connector hiện có:

```text
semantic_lsp_warm: AtomicBool
```

File scope:

```text
existing file → document_symbols
```

Workspace scope:

```text
cold  → concurrency = 1
warm  → bounded concurrency
```

LSP failure hạ state warm về false.

## 5.4. Existing Coding MCP governor

`resources/coding-tools-mcp/coding_tools_mcp/execution_resources.py` đã có:

```text
RESOURCE_CLASSES = LIGHT | MEDIUM | HEAVY
managed_process_jobs
checkout-wide HEAVY admission
host pressure check
foreign heavy process detection
rust-analyzer classification
wave quiescence assertion
```

Vì vậy không xây “Global Resource Governor v2”. Chỉ mở rộng existing governor để native semantic có thể hỏi admission state trước khi tạo tải LSP nặng.

---

# 6. Design correction — không triển khai state machine LSP thứ hai

Plan cũ đề xuất:

```text
STOPPED → STARTING → COLD_READY → WARM → IDLE → DRAINING → STOPPED
```

Không nên persist/duplicate toàn bộ state machine này vì source đã có các state tương đương ở nhiều lớp.

Thay vào đó giữ state hiện hữu và thêm **resource state trực giao**:

```text
pressure_state = NORMAL | SOFT | HARD | UNKNOWN

process_instance_id
working_set_bytes
peak_working_set_bytes
pending_request_count
last_used_age_ms
restart_count
drain_count
last_pressure_reason
```

Derived state có thể tính:

```text
STOPPED  = no live slot/process
STARTING = SlotState::Starting
RUNNING  = SlotState::Running
FAILED   = SlotState::Failed
IDLE     = pending_count == 0 && last_used_age >= threshold
WARM     = Connector semantic_lsp_warm == true
```

`DRAINING` có thể là transient implementation detail, không cần durable public state nếu không có consumer thật sự cần.

---

# 7. Gate 0 — Close Recovery Phase 3B trước khi P2/P3 tiếp tục

## 7.1. Mục tiêu

Tạo authoritative source/runtime boundary để resource hardening không trộn với Recovery implementation.

## 7.2. Bắt buộc

- Recovery successor wave đạt acceptance hoặc terminal explicit isolation.
- Canonical modified-file receipt phải chứa đúng Recovery source thực tế.
- Recovery proof phù hợp fingerprint cuối.
- Không còn Recovery writer.
- Không còn managed HEAVY job liên quan.
- Không sửa P2/P3 LSP files trong Recovery wave.

## 7.3. Exit criteria

```text
Recovery source ownership = settled
Recovery EOCL = CHECKPOINTED hoặc explicit terminal isolation
active write lease = 0 trên P2/P3 target surface
active managed HEAVY = 0
```

---

# 8. Wave 1 — Prove existing LSP idle lifecycle

## 8.1. Mục tiêu

Không implement idle teardown mới. Chứng minh implementation hiện có thật sự chạy đúng trong topology Connector `p3-live`/equivalent.

## 8.2. Kiểm tra source trước proof

Xác minh:

- exact `DEFAULT_IDLE_TTL` hiện tại;
- config path nào có thể override TTL trong test/live profile;
- background reaper thực sự enabled ở production Runner config;
- Connector artifact đang chạy được build từ source chứa reaper hiện tại.

Không hardcode TTL vào tài liệu trước khi đọc đúng constant/config.

## 8.3. Operational scenario

```text
1. ensure target LSP instance absent/STOPPED
2. issue one single-file semantic request
3. prove native document_symbols handled
4. record LSP PID/process identity
5. issue warm request
6. stop semantic traffic
7. wait configured test idle TTL
8. verify LSP owned tree is gone
9. verify Connector process/profile remains alive
10. issue a new single-file semantic request
11. verify new LSP instance identity
12. verify native semantic handled again
```

## 8.4. Acceptance

Pass nếu:

```text
idle LSP exits
Connector remains alive
no orphan descendants
new request cold-starts new LSP successfully
text fallback remains available during transition
```

## 8.5. Decision after Wave 1

### Nếu PASS

Đóng toàn bộ “Packet A — implement idle lifecycle” trong plan cũ.

Không sửa supervisor lifecycle chỉ để đổi tên state.

### Nếu FAIL

Chỉ patch đúng defect được chứng minh, ví dụ:

- reaper không start trong live topology;
- production TTL bị vô hiệu hóa;
- `last_used` không được cập nhật cho một request path;
- process shutdown không release tree;
- new request không cold restart.

---

# 9. Wave 2 — LSP process telemetry + memory-pressure policy

Đây là implementation gap quan trọng nhất còn mở.

## 9.1. Mục tiêu

Cho supervisor biết process working set và có policy soft/hard pressure mà không kill active request giữa chừng.

## 9.2. Process telemetry tối thiểu

Thêm một bounded internal snapshot:

```text
lsp_process_snapshot {
  process_instance_id,
  pid_or_opaque_identity,
  server_kind,
  project_identity,
  working_set_bytes,
  peak_working_set_bytes,
  pending_request_count,
  last_used_age_ms,
  lifecycle_usable,
  pressure_state,
  restart_count,
  drain_count
}
```

Không lưu:

- raw source;
- raw semantic query;
- credentials;
- unrestricted stderr.

## 9.3. Cross-platform abstraction

Không đưa Windows API trực tiếp vào LSP policy.

Ưu tiên abstraction ở process layer:

```text
ManagedChild::resource_snapshot()
```

hoặc tương đương internal API.

Windows implementation đọc working set/process identity.

Các platform khác có thể:

```text
supported metrics → numeric snapshot
unsupported      → pressure_state=UNKNOWN / metric unavailable
```

Không được biến unsupported thành `0 bytes`.

## 9.4. Soft/hard thresholds

Internal config:

```text
lsp_memory_soft_limit_bytes
lsp_memory_hard_limit_bytes
```

Yêu cầu:

- test có thể override threshold thấp deterministic;
- production default không được suy ra trực tiếp từ một snapshot lịch sử ~4.2 GiB;
- hard limit > soft limit;
- invalid config fail closed hoặc disable pressure action rõ ràng.

## 9.5. Soft pressure behavior

```text
if working_set >= soft_limit:
    pressure_state = SOFT
```

Behavior:

- không kill request đang active;
- broad workspace native request mới có thể bị deny/fallback;
- single-file native request chỉ được admit khi global governor không conflict và policy cho phép;
- khi pending requests về `0`, server trở thành eligible cho early drain.

## 9.6. Hard pressure behavior

```text
if working_set >= hard_limit:
    pressure_state = HARD
```

Behavior:

- không admit native request mới;
- active request đang chạy được phép hoàn thành theo timeout bình thường;
- khi pending count về `0`, drain exact owned LSP tree;
- next request chỉ cold-start sau khi admission state cho phép.

Không `taskkill /IM rust-analyzer.exe`.

## 9.7. UNKNOWN metrics

Nếu working-set measurement unavailable:

```text
pressure_state = UNKNOWN
```

Policy:

- không giả định memory = 0;
- LIGHT/read-only status vẫn allow;
- broad semantic khi đang có HEAVY conflict vẫn fail closed/fallback;
- no automatic blind kill.

## 9.8. Tests

Bắt buộc dùng injectable/synthetic metrics thay vì thật sự cấp phát nhiều GiB RAM.

Tests:

- below soft → NORMAL;
- >= soft → SOFT;
- >= hard → HARD;
- soft không kill pending request;
- hard không kill pending request giữa chừng;
- hard + pending=0 → owned tree drain;
- UNKNOWN không trở thành zero;
- cold restart sau hard drain;
- process identity thay đổi sau restart;
- descendants của managed tree gone sau drain.

---

# 10. Wave 3 — Native semantic admission ↔ existing HEAVY governor

## 10.1. Mục tiêu

Chặn conflict theo cả hai chiều:

```text
Cargo/full pytest HEAVY active
    ↓
broad/cold native semantic must not start competing HEAVY LSP work
```

và:

```text
cold/high-pressure rust-analyzer active
    ↓
new Cargo/full-test HEAVY must not start concurrently
```

Nửa thứ hai phần lớn đã có qua foreign-heavy/governor detection. Gap chính là semantic-side admission.

## 10.2. Không biến persistent LSP thành fake EOCL wave job

LSP vẫn thuộc Connector/Runner `ManagedChild` lifecycle.

Coding MCP governor chỉ cung cấp **admission decision**.

Không ghi một fake `managed_process_jobs` row để giả LSP là command của wave nếu ownership không đúng semantic.

## 10.3. Admission API nội bộ

Thêm helper có output deterministic, ví dụ:

```text
semantic_native_admission {
  allowed,
  mode,
  reason_code,
  active_heavy_count,
  host_pressured,
  foreign_heavy_present
}
```

Reason code reuse existing vocabulary khi có thể:

```text
HEAVY_SLOT_BUSY
HOST_MEMORY_PRESSURE
FOREIGN_HEAVY_PRESENT
RESOURCE_OWNER_REQUIRED
```

Chỉ thêm code mới khi semantic policy thực sự cần phân biệt:

```text
LSP_MEMORY_PRESSURE
LSP_MEMORY_HARD_LIMIT
```

## 10.4. Admission placement

Quan trọng: gate phải xảy ra **trước native provider call** khi request có nguy cơ cold/broad HEAVY.

Không làm:

```text
start/index rust-analyzer
→ rồi mới hỏi governor
```

Mục tiêu:

```text
context localization request
    ↓
classify native semantic cost
    ↓
ask resource admission
    ├─ allow → native provider
    └─ deny  → text fallback
```

## 10.5. Request classification

Initial policy tối giản:

```text
single-file document semantic + warm/normal LSP → MEDIUM
workspace semantic + cold LSP                → HEAVY
workspace semantic + hard/soft pressure      → deny/fallback
single-file + active Cargo HEAVY              → policy-defined; default prefer fallback
```

Không cần autoscheduler phức tạp ở wave này.

## 10.6. Acceptance matrix

| Existing workload | New semantic/workload | Expected |
|---|---|---|
| none | cold workspace semantic | allow nếu host pressure thấp |
| Cargo HEAVY | cold/broad semantic | native deny, text fallback |
| full pytest HEAVY | broad semantic | native deny, text fallback |
| LSP cold/high pressure | Cargo HEAVY | Cargo defer/reject |
| warm normal LSP | focused Cargo HEAVY | governor policy quyết định theo pressure; không blind kill |
| LIGHT command | any HEAVY active | LIGHT status vẫn allow |

## 10.7. Tests

- active Cargo HEAVY → native broad semantic không được gọi;
- text fallback vẫn trả usable context;
- after Cargo completes → native semantic lại được admit;
- high-pressure LSP → new managed HEAVY bị chặn;
- LIGHT status vẫn chạy;
- unknown ownership không làm governor tự kill process;
- reason code deterministic.

---

# 11. Wave 4 — Ownership/restart proof trước khi thêm durable profile schema

## 11.1. Mục tiêu

Xác định liệu existing natural process ownership có đủ hay không.

Current natural topology:

```text
Connector / Runner
    └─ LspSupervisor
         └─ ManagedChild
              └─ rust-analyzer tree
```

EOCL command ownership là topology riêng:

```text
RUN/WAVE
    └─ managed_process_jobs
         └─ cargo/python/npm/etc.
```

Không trộn hai topology nếu chưa có evidence cần thiết.

## 11.2. Proof matrix

Bắt buộc chứng minh:

1. terminal wave cleanup không kill persistent Connector profile;
2. idle LSP teardown chỉ kill LSP child tree, không kill Connector parent;
3. Connector/profile shutdown kill đúng descendant LSP;
4. MCP/runtime restart không làm wave cleanup nhận nhầm profile LSP;
5. PID reuse/process identity mismatch không bị coi là owned;
6. unknown resource identity không bị auto-kill.

## 11.3. Decision gate

### Nếu tất cả PASS

Không thêm `CONNECTOR_PROFILE` table/schema.

Document ownership contract và dừng ở đây.

### Nếu FAIL vì không reconcile persistent process identity sau restart

Bổ sung durable record **tối thiểu**:

```text
persistent_resource {
  owner_type = CONNECTOR_PROFILE,
  owner_id,
  checkout_id,
  runtime_instance_id,
  process_identity,
  lifecycle_state,
  updated_at
}
```

Chỉ persist event quan trọng:

- registered;
- process identity changed;
- pressure entered;
- drained/restarted;
- unknown/orphaned;
- reconciled after restart.

Không ghi từng LSP request.

## 11.4. Fail-closed ownership rule

```text
identity exact match → can manage/reconcile
identity uncertain   → UNKNOWN
UNKNOWN              → do not kill blindly
UNKNOWN + collision risk → block/defer new HEAVY
```

---

# 12. Wave 5 — Authoritative operational soak

Đây là proof quyết định để đóng defect resource-lifecycle ban đầu.

## 12.1. Test environment

- stable Connector profile riêng hoặc `p3-live` khi không có conflict;
- không chạy cùng Recovery/feature mutation wave;
- host không có unrelated compile/test do system quản lý;
- record exact Git HEAD/runtime/tool contract.

## 12.2. Scenario A — Cold single-file semantic

```text
LSP absent
→ single-file semantic
→ document_symbols
→ semantic_handled > 0
→ fallback = 0
```

Record:

- cold latency;
- process instance;
- initial working set;
- peak during startup.

## 12.3. Scenario B — Warm repeated single-file semantic

Pass khi:

- reuse same LSP instance;
- handled ổn định;
- no extra server instance;
- working set growth bounded;
- no workspace_symbols regression.

## 12.4. Scenario C — Warm workspace semantic

Pass khi:

- bounded concurrency;
- query order preserved;
- no unbounded process growth;
- result remains sanitized/project-relative.

## 12.5. Scenario D — Idle teardown

```text
stop traffic
→ wait test TTL
→ LSP tree gone
→ Connector alive
→ memory reclaimed by process exit
```

Acceptance dựa trên process termination, không dựa duy nhất vào một MB threshold.

## 12.6. Scenario E — Cold restart after idle

```text
new semantic request
→ new process identity
→ native handled > 0
```

## 12.7. Scenario F — Memory soft pressure

Synthetic/controlled threshold:

```text
working_set >= soft
→ pressure=SOFT
→ no active request killed
→ broad native request denied/fallback as policy
→ pending=0 permits drain
```

## 12.8. Scenario G — Memory hard pressure

```text
working_set >= hard
→ new native request denied
→ current request completes/timeout normally
→ pending=0
→ exact owned LSP tree drained
→ later request cold-starts new instance
```

## 12.9. Scenario H — Cargo/LSP conflict

```text
start managed Cargo HEAVY
→ request broad semantic
```

Expected:

```text
native LSP HEAVY not admitted
text fallback used
HEAVY overlap count remains 0
```

Sau Cargo terminal:

```text
semantic request → native admission restored
```

## 12.10. Scenario I — Reverse conflict

```text
cold/high-pressure LSP exists
→ request Cargo/full-test HEAVY
```

Expected:

- Cargo deferred/rejected by governor;
- no blind kill of LSP if active;
- if LSP idle and policy says drain, drain exact owned tree first;
- Cargo only admitted after safe state.

## 12.11. Scenario J — REPLAN/terminal cleanup

Controlled wave-owned process tree:

```text
spawn managed descendant
→ terminal/replan path
→ descendants exit
→ Connector-profile process unaffected
```

## 12.12. Metrics

Record content-free metrics:

```text
cold_semantic_latency_ms
warm_semantic_latency_ms
workspace_semantic_latency_ms
lsp_working_set_bytes
lsp_peak_working_set_bytes
lsp_idle_teardown_count
lsp_restart_count
lsp_soft_pressure_count
lsp_hard_pressure_count
native_semantic_attempted
native_semantic_handled
text_fallback_count
heavy_admission_allowed_count
heavy_admission_rejected_count
heavy_overlap_detected_count
orphan_process_count
unknown_owner_count
```

## 12.13. Hard acceptance

```text
orphan_process_count = 0
heavy_overlap_detected_count = 0
idle LSP teardown = proven
cold restart = proven
single-file document_symbols = proven
text fallback under deliberate denial = proven
active request not killed by ordinary idle policy
active request not killed mid-flight by soft/hard memory policy
Smart-v3 public tool count = 8
```

Nếu các điều kiện trên pass, defect resource-lifecycle gây host lag có thể coi là closed về kỹ thuật.

---

# 13. Wave 6 — Disk/cache lifecycle

Chỉ triển khai sau khi RAM/process lifecycle đã đạt soak acceptance.

## 13.1. Mục tiêu

Quan sát và dọn build cache/artifact an toàn mà không làm mất incremental performance vô ích.

## 13.2. Telemetry

```text
target_total_bytes
debug_incremental_bytes
release_artifact_bytes
temporary_worktree_target_bytes
last_soft_cleanup_at
last_hard_cleanup_at
```

## 13.3. Soft cleanup

Ưu tiên:

- old temporary worktree target dirs;
- obsolete dedicated hardening target dirs;
- disposable temporary artifacts có owner/path rõ.

Guard:

```text
no active build owner
path belongs to allowed cleanup roots
artifact not used by active Connector/profile
```

## 13.4. Hard cleanup

`cargo clean` vẫn là manual/operator policy.

Không dùng `cargo clean` làm automatic response cho RAM pressure.

---

# 14. Wave 7 — Final operational baseline + EOCL delivery

## 14.1. Final fingerprint

Chốt:

```text
Git HEAD
origin/main HEAD
runtime version
resource policy version
tool contract SHA
smart-v3 tool count
Connector artifact identity
LSP policy/config identity
```

## 14.2. Final baseline

Record:

```text
LSP cold peak working set
LSP warm working set
idle teardown behavior
cold restart behavior
soft/hard pressure behavior
Cargo/LSP conflict behavior
native/fallback counts
orphan count
unknown-owner count
stale orchestration count
```

Không biến measurement trên một máy thành universal guarantee.

## 14.3. Verification ladder

Ở final source fingerprint:

1. scoped static/diff checks;
2. LSP supervisor/resource unit tests;
3. process-tree tests;
4. governor focused tests;
5. connector semantic tests;
6. operational soak;
7. affected subsystem Python/Rust suites;
8. broad authority run một lần nếu change surface thực sự cross-cutting.

Không full-build/full-suite sau mọi patch.

## 14.4. EOCL closure

Material implementation run phải đạt:

```text
PREFLIGHT
→ READY
→ ROUTED
→ EXECUTING
→ PROVING
→ ACCEPTING
→ CHECKPOINTED
```

Không để source “xong” nhưng final run còn `REPLAN`.

## 14.5. Git delivery

Trước commit:

```text
review full status
separate Recovery/P2-P3 scopes
selective stage intended source/tests/docs
exclude .coding-tools/orchestration/ledger.sqlite3, WAL/SHM and other volatile projections
record accepted source fingerprint + report checksum in maintained docs
git diff --cached --check
secret scan staged diff
```

Sau commit:

```text
push main only when explicitly authorized
verify local SHA == origin/main SHA
verify commit contains intended files
verify no volatile `.coding-tools` evidence was staged
```

Không force-push.

---

# 15. Revised implementation packets

## Packet A — Existing idle lifecycle proof

**Scope:** no production feature by default.  
**Outcome:** chứng minh idle reaper hiện có thực sự teardown và cold restart.  
**Write:** chỉ khi proof expose defect.  
**Proof:** cold → warm → idle → process gone → new cold instance.

## Packet B — Process/memory telemetry

**Scope:** `ManagedChild` resource snapshot + LSP supervisor counters/pressure state.  
**Outcome:** working set/peak/pressure observable.  
**Proof:** synthetic deterministic metrics + process identity tests.

## Packet C — LSP soft/hard memory pressure

**Scope:** supervisor admission/drain behavior.  
**Outcome:** no new native work under hard pressure; safe drain only after pending=0.  
**Proof:** no mid-flight kill + restart regression.

## Packet D — Native semantic resource admission

**Scope:** existing Coding MCP governor + context/native semantic decision point.  
**Outcome:** Cargo/full-test ↔ cold LSP HEAVY overlap = 0.  
**Proof:** deliberate deny/fallback + post-completion native recovery.

## Packet E — Ownership/restart proof

**Scope:** evidence first.  
**Outcome:** determine if natural Connector/ManagedChild ownership is sufficient.  
**Write:** durable profile owner only if proof fails.

## Packet F — Soak harness

**Scope:** integration/proof only unless defect discovered.  
**Outcome:** repeatable resource lifecycle evidence.

## Packet G — Disk/cache hygiene

**Scope:** telemetry + safe soft cleanup guards.  
**Outcome:** observable disk growth without destructive automatic cleaning.

---

# 16. Candidate file map đã hiệu chỉnh

## 16.1. Primary Rust surfaces

```text
crates/webcodex-runner/src/webcodex_runner/lsp/supervisor.rs
crates/webcodex-runner/src/webcodex_runner/lsp/tests.rs
crates/webcodex-runner/src/webcodex_runner/lsp/navigation_tests.rs
crates/webcodex-process/src/lib.rs
crates/webcodex-process/src/windows.rs
src/connector_runtime/semantic_bridge.rs
src/connector_runtime/mod.rs
```

### Nguyên tắc

- `supervisor.rs`: telemetry + pressure policy; không rewrite idle lifecycle.
- `webcodex-process`: chỉ expose process metrics/identity abstraction nếu cần.
- `semantic_bridge.rs`: giữ document/workspace scope và cold/warm policy; chỉ thêm pressure/admission semantics nếu interface cần.

## 16.2. Primary Python governor surfaces

```text
resources/coding-tools-mcp/coding_tools_mcp/execution_resources.py
resources/coding-tools-mcp/coding_tools_mcp/context_tools.py
resources/coding-tools-mcp/tests/test_execution_resources.py
```

Có thể cần thêm affected focused tests tùy localization thật.

## 16.3. Conditional surfaces — chỉ dùng nếu evidence bắt buộc

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/coordination.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py
crates/webcodex-core/src/lsp_bridge.rs
```

Không sửa các file này chỉ vì plan cũ liệt kê.

## 16.4. Explicitly out of P2/P3 waves

Recovery source không được đụng trong resource hardening wave:

```text
electron/services/recoveryPlaneService.js
resources/recovery-mcp/recovery_mcp.py
resources/recovery-supervisor/recovery-supervisor.ps1
Recovery-specific tests/docs
```

trừ khi user mở riêng Recovery task.

---

# 17. Error/reason taxonomy

Reuse existing governor codes trước:

```text
HEAVY_SLOT_BUSY
HOST_MEMORY_PRESSURE
FOREIGN_HEAVY_PRESENT
UNOWNED_EXECUTION_PROCESS
RESOURCE_OWNER_REQUIRED
```

Chỉ thêm LSP-specific internal codes nếu cần:

```text
LSP_MEMORY_PRESSURE
LSP_MEMORY_HARD_LIMIT
LSP_METRICS_UNAVAILABLE
LSP_RESTART_REQUIRED
LSP_OWNER_UNCERTAIN
RESOURCE_IDENTITY_MISMATCH
```

Không bắt buộc expose thành public MCP API.

---

# 18. Telemetry contract

## 18.1. Allowed

- numeric working set/peak;
- process instance hash/opaque identity;
- lifecycle/pressure transition;
- owner/profile identity đã sanitize;
- admission reason;
- teardown/restart counters;
- semantic handled/fallback counters.

## 18.2. Forbidden/unnecessary

- raw source file content;
- raw prompt;
- private chain-of-thought;
- credentials;
- Authorization header;
- full unbounded stdout/stderr;
- machine-local secret path.

---

# 19. Rollback strategy

## 19.1. Idle proof fails

- không viết lại toàn LSP stack;
- identify exact reaper/config/lifecycle defect;
- patch minimal surface;
- text fallback remains enabled.

## 19.2. Memory metric unreliable

- retain metric observation as `UNKNOWN`;
- disable automatic memory-driven drain;
- keep idle teardown;
- do not invent zero value.

## 19.3. Soft/hard pressure causes semantic instability

- keep telemetry;
- disable memory-triggered automatic drain via internal flag;
- preserve native/text fallback logic;
- debug restart/admission separately.

## 19.4. Persistent ownership cannot be reconciled

- mark UNKNOWN;
- no blind kill;
- block unsafe HEAVY collision;
- only then add minimal durable `CONNECTOR_PROFILE` record.

## 19.5. Soak finds correctness regression

- reject current EOCL wave;
- reuse exact prior proof where fingerprint still matches;
- replan only failing invariant;
- no broad suite loop until focused defect fixed.

---

# 20. Definition of Done

## 20.1. Process lifecycle

```text
orphan managed process = 0
wave cleanup kills only wave-owned descendants
idle LSP teardown works
Connector survives LSP idle teardown
profile shutdown kills correct LSP descendants
cold restart works
PID/process identity mismatch fail closed
```

## 20.2. Memory/resource policy

```text
LSP working set observable or explicitly UNKNOWN
soft pressure does not kill active request
hard pressure blocks new native request
hard drain only after pending=0
no blind process-name kill
```

## 20.3. Scheduling

```text
conflicting HEAVY overlap = 0
Cargo/full pytest considers LSP conflict
cold/broad semantic considers active Cargo/full-test conflict
LIGHT inspection still allowed
foreign/unknown heavy process not killed blindly
```

## 20.4. Semantic behavior

```text
single-file → document_symbols
workspace → bounded cold/warm behavior
native semantic recovers after idle/hard drain
text fallback works during native deny/failure
project-relative sanitized results preserved
```

## 20.5. Security/public contract

```text
wrong token rejected
workspace mismatch rejected
absolute/traversal path rejected
credential not leaked
smart-v3 public tool count = 8
```

## 20.6. Operational proof

```text
cold → warm → idle → stopped → cold restart proven
soft pressure proven
hard pressure proven
Cargo/LSP conflict fallback proven
orphan count = 0
HEAVY overlap count = 0
stale orchestration count = 0 at final evidence window
active write fences = 0 at final acceptance
active managed HEAVY = 0 after proof
```

## 20.7. Delivery

```text
EOCL CHECKPOINTED
selective intended source commit
runtime ledger preserved outside the source commit; accepted report checksum recorded
push main successful only when explicitly authorized
local SHA == origin/main SHA
no force-push
```

---

# 21. Recommended execution order — authoritative version

Không đổi thứ tự trừ khi live evidence chứng minh dependency khác.

```text
0. Finish/checkpoint Recovery Phase 3B.
1. Establish quiescent P2/P3 baseline.
2. Prove existing LSP idle reaper/cold restart.
3. Implement process/memory telemetry.
4. Implement soft/hard LSP memory policy.
5. Integrate native semantic admission with existing HEAVY governor.
6. Run ownership/restart proof.
7. Add durable CONNECTOR_PROFILE ownership only if Step 6 proves necessary.
8. Run authoritative cold/warm/idle/restart/conflict soak.
9. Implement disk/cache hygiene.
10. Final EOCL acceptance + selective source commit; preserve ledger as runtime evidence and push only with explicit authorization.
```

---

# 22. Priority thực tế

## P0 — Blocker

1. Đóng Recovery Phase 3B.
2. Không trộn Recovery source với LSP/resource hardening.

## P1 — Core technical closure

1. Prove existing idle reaper.
2. Add LSP process/memory telemetry.
3. Add soft/hard memory policy.
4. Gate native semantic against existing HEAVY governor.
5. Authoritative operational soak.

## P2 — Conditional hardening

1. Persistent `CONNECTOR_PROFILE` ownership chỉ nếu restart/ownership proof không đủ.
2. Additional telemetry/reporting nếu có consumer cụ thể.

## P3 — Operational hygiene

1. Disk/cache telemetry.
2. Safe soft cleanup.
3. Performance tuning sau khi correctness/resource safety đã proven.

---

# 23. Những việc không được làm

- Không viết lại `LspSupervisor` state machine chỉ vì plan cũ đề xuất nhiều state hơn.
- Không tạo Resource Governor thứ hai.
- Không biến persistent LSP thành fake wave-owned command nếu semantic ownership không đúng.
- Không thêm persistent ownership schema trước khi proof chứng minh cần.
- Không hardcode memory threshold từ snapshot lịch sử ~4.2 GiB.
- Không test hard pressure bằng cách cố allocate nhiều GiB RAM trong CI.
- Không `taskkill /IM rust-analyzer.exe`.
- Không chạy Cargo/full pytest song song với cold LSP chỉ để “test tải”.
- Không rerun broad suite sau mọi patch.
- Không `cargo clean` trong active proof wave.
- Không thay đổi public tool count để expose telemetry nội bộ.
- Không manually edit, stage hoặc commit `.coding-tools/orchestration/ledger.sqlite3`, WAL/SHM hay runtime projections để làm source delivery trông sạch hơn.

---

# 24. Kết luận

Correctness foundation của P2/P3 đã đi xa hơn plan cũ mô tả.

Các capability quan trọng — process-tree ownership, idle TTL/reaper, semantic file scope, cold/warm concurrency, HEAVY governor và quiescence — đã tồn tại. Vì vậy mục tiêu còn lại không phải xây thêm framework mà là **nối các capability hiện hữu thành một operational resource contract khép kín và chứng minh bằng live soak**.

Kiến trúc mục tiêu sau hiệu chỉnh:

```text
LSP requested
    ↓
existing LspSupervisor starts owned ManagedChild
    ↓
semantic cold/warm policy bounds request fan-out
    ↓
process metrics expose working set/pressure
    ↓
existing Coding MCP governor coordinates HEAVY admission
    ↓
normal/warm → reuse
soft pressure → restrict broad native work, drain when safe
hard pressure → deny new native work, drain after pending=0
idle → existing reaper tears down
next request → safe cold restart
    ↓
text fallback preserves correctness whenever native path is denied/unavailable
```

Definition of success không phải “rust-analyzer luôn sống” mà là:

```text
khi cần      → start đúng owner
khi warm     → reuse bounded
khi idle     → release process/memory
khi pressure → defer/drain/fallback
khi conflict → không HEAVY overlap
khi quay lại → cold restart an toàn
khi cleanup  → chỉ kill đúng owned tree
```

Khi Wave 1–5 pass với `orphan_process_count = 0` và `heavy_overlap_detected_count = 0`, defect resource-lifecycle gây lag trước đây có thể coi là đóng về kỹ thuật. Các bước disk/cache sau đó là operational hygiene, không còn là blocker correctness/resource safety.

---

# 25. Implementation closure — 2026-08-16

## 25.1. Trạng thái các wave

| Gate/Wave | Kết quả | Bằng chứng chốt |
|---|---|---|
| Gate 0 — Recovery boundary | PASS | Recovery delivery đã được tách tại `cb26a54f`; evidence cuối không có write fence hoặc managed HEAVY job. |
| Wave 1 — existing idle lifecycle | PASS | Background reaper dọn exact owned LSP tree và cho phép cold restart. |
| Wave 2 — process/memory policy | PASS | Cross-platform process snapshot, `NORMAL/SOFT/HARD/UNKNOWN`, safe drain và restart counters đã có test deterministic. |
| Wave 3 — semantic/governor admission | PASS | Native provider bị gate trước call; Cargo/pytest HEAVY chuyển semantic sang text fallback; native phục hồi sau terminal. Directory/unsupported scope giữ HEAVY semantics. |
| Wave 4 — ownership/restart | PASS | `ManagedChild`/Connector ownership đủ; PID/start-token và owned-tree proof không cho thấy nhu cầu thêm schema `CONNECTOR_PROFILE`. |
| Wave 5 — operational soak | PASS | Ma trận real-process + synthetic-pressure equivalent pass 28 focused tests/checks. |
| Wave 6 — disk/cache hygiene | PASS | Snapshot và fail-closed soft-clean guard đã triển khai; không chạy cleanup trên primary `target`. |
| Wave 7 — baseline/delivery | PASS | Implementation gốc đã lên `main` tại `5d3968ec`; follow-up closure và record này đã lên `main` tại `cf6cb6dd`. |

## 25.2. Final proof fingerprint

Evidence window cuối:

```text
started_at  = 2026-08-16T11:09:18.211Z
finished_at = 2026-08-16T11:09:38.055Z
base HEAD   = 5d3968ec2dead0d47859e32028e167bc53d28e1f
source SHA  = 22b73a14c103fdc00e061e5114ce34d555d24f26f68f2f07b7182678cd633e03
mode        = real_process_and_synthetic_pressure_equivalent
runtime     = Coding Tools MCP 0.4.3 / smart-v3 / 8 public tools
policy      = p2-p3-operational-hardening-v1
```

`source SHA` là SHA-256 tổng hợp theo `path + NUL + file_sha256 + LF` của 17 source/test file được harness liệt kê. Nó khóa cả các file uncommitted tại thời điểm proof, vì vậy không suy diễn proof chỉ từ base HEAD.

Verification matrix cuối:

```text
managed process snapshot             1/1 PASS
owned process-tree termination       1/1 PASS
background idle teardown             1/1 PASS
LSP memory-pressure matrix           4/4 PASS
governor + semantic fallback        12/12 PASS
smart-v3 public contract             1/1 PASS
resource-hygiene guards              2/2 PASS
native semantic bridge               6/6 PASS
total                               28/28 PASS
```

Ledger health tại cuối evidence window:

```text
active_managed_heavy_count     = 0
active_write_fence_count       = 0
orphan_process_count           = 0
heavy_overlap_detected_count   = 0
stale_orchestration_run_count  = 0
active_run_count               = 1
```

`active_run_count = 1` là một ChatWeb controller có live lease, không có write fence/job/HEAVY owner; vì vậy không phải stale hay conflicting owner. Hard gate dùng đúng invariant của kế hoạch là stale run/fence/job/orphan bằng `0`, không biến mọi read-only/live controller thành lỗi giả.

## 25.3. Disk baseline và cleanup decision

```text
target_total_bytes                  = 14,178,286,735
debug_incremental_bytes             =  7,961,953,346
release_artifact_bytes              =  1,550,436,025
temporary_worktree_target_bytes     =              0
last_soft_cleanup_at                = null
last_hard_cleanup_at                = null
```

Không chạy `cargo clean` và không chạy soft cleanup. Primary `target` vẫn là cache incremental hữu ích; policy hard cleanup tiếp tục là manual-only. Soft cleanup chỉ nhận explicit non-primary `target`, yêu cầu confirmation, chặn primary/nested-primary target, và fail closed nếu không quan sát được process ownership hoặc còn managed HEAVY/build/Connector reference.

## 25.4. Kết luận triển khai

P2/P3 operational hardening đã đóng về kỹ thuật theo scope của kế hoạch. Persistent profile schema không được thêm vì ownership proof đã pass. Giới hạn còn lại được ghi rõ: pressure thresholds được chứng minh bằng synthetic metrics để không cấp phát nhiều GiB trong CI; process teardown/cold restart vẫn dùng real managed child, và native semantic bridge chạy qua integration tests của repository. Không có release, deployment hoặc service restart trong delivery này.

---

# 26. Post-closure completion plan — production evidence và atomic admission

Section này supersede Sections 21–22 cho mọi implementation tiếp theo. Mục tiêu không phải mở lại các wave đã PASS, mà là đóng ba khoảng trống còn lại giữa “focused implementation proven” và “production operational contract proven under concurrency”.

## 26.1. Evidence baseline và gap classification

Live observation tại `2026-08-16T18:14:52.984+07:00`:

```text
branch                         = main
HEAD                           = cf6cb6ddbf29d90515d003ce72490ffda985c37f
origin/main                    = cf6cb6ddbf29d90515d003ce72490ffda985c37f
active_managed_heavy_count     = 0
active_write_fence_count       = 0
orphan_process_count           = 0
heavy_overlap_detected_count   = 0
stale_orchestration_run_count  = 0
active_run_count               = 2
```

Hai active run là observation point-in-time, không tự động là blocker vì không có write fence, managed HEAVY hoặc stale owner. Worktree đang có một đợt documentation reorganization concurrent với nhiều staged deletion/modification ngoài scope; implementation source wave tiếp theo phải chờ ownership của đợt này được settle hoặc dùng isolated worktree.

| Gap | Evidence trong source hiện tại | Phân loại | Quyết định |
|---|---|---|---|
| Semantic admission chưa atomic với managed HEAVY admission | `semantic_native_admission()` chỉ đọc state và không reserve slot; native provider được gọi sau decision | Race chưa được chứng minh xảy ra, nhưng hard guarantee `overlap = 0` dưới simultaneous start chưa đủ | Bổ sung checkout-scoped scheduling claim dùng chung cho semantic HEAVY và managed HEAVY |
| Cold single-file chưa có warm/pressure handshake trước classification | Python phân loại supported file là `MEDIUM`, trong khi request đầu có thể cold-start LSP | Policy ambiguity thật | Status `STOPPED/UNKNOWN` phải làm cold single-file nhận HEAVY semantics; chỉ warm + normal focused request mới là MEDIUM |
| Process snapshot chưa có production consumer | `project_process_snapshot()` hiện chỉ được dùng trong supervisor tests | Observability gap | Expose một bounded resource projection qua existing internal/operator status, không thêm MCP tool mới |
| Soak chưa phải long-running live Connector soak | Harness tự khai báo `real_process_and_synthetic_pressure_equivalent` | Evidence gap, không phải code defect | Thêm live mode với real Connector/Runner + rust-analyzer và nhiều cold/warm/idle cycles |
| Default 2 GiB/3 GiB chưa được field-calibrate trên live profile | Threshold deterministic tests PASS nhưng không có representative live measurement series | Tuning gap | Giữ defaults cho tới khi live evidence chứng minh cần đổi; không auto-tune |
| Disk hygiene | Snapshot + guarded soft cleanup đã PASS; temporary target hiện bằng `0` trong closure evidence | Closed | Không thêm scheduler/automatic `cargo clean`; chỉ re-open khi có target owner/retention use case thật |
| Persistent kill ownership | ManagedChild/Connector ownership proof PASS | Closed | Không thêm `CONNECTOR_PROFILE` kill-ownership schema |

## 26.2. Revised finish line

Production completion chỉ đạt khi tất cả điều kiện sau được chứng minh trên cùng source fingerprint:

```text
1. simultaneous semantic HEAVY và managed HEAVY không thể cùng acquire checkout claim
2. cold single-file được phân loại HEAVY cho tới khi Connector chứng minh warm + normal
3. warm + normal focused semantic vẫn có MEDIUM fast path
4. status/resource projection không start LSP và không lộ path/source/query/credential
5. active semantic request không bị kill bởi idle/soft/hard cleanup
6. crash/timeout luôn release claim bằng finally hoặc lease expiry
7. real Connector soak chứng minh cold → warm → idle → stopped → cold restart nhiều cycle
8. public smart-v3 tool count vẫn bằng 8
9. orphan, overlap, stale orchestration, active write fence và terminal managed HEAVY đều bằng 0 ở final window
```

Không dùng một test tuần tự để chứng minh atomicity. Phải có barrier/concurrent-start oracle làm cả hai phía cố acquire cùng lúc.

## 26.3. Architecture decision — scheduling claim, không phải process ownership

Giữ hai khái niệm tách biệt:

```text
Process ownership
  Connector / Runner → LspSupervisor → ManagedChild → exact LSP tree
  quyền terminate chỉ đi theo exact owned handle/tree

Scheduling claim
  checkout + resource_class → một active claimant tại một thời điểm
  chỉ quyết định admit/defer/fallback
  không tự mang quyền kill process
```

Data flow mục tiêu:

```text
semantic request
  ↓
read bounded Connector LSP resource status
  ↓
classify focused/workspace + stopped/warm + pressure
  ↓
atomic checkout resource claim
  ├─ denied → text fallback
  └─ acquired → native provider call → release in finally

managed Cargo/full-test HEAVY
  ↓
same atomic checkout resource claim
  ├─ denied → HEAVY_SLOT_BUSY / retry
  └─ acquired → managed_process_job lifecycle → release on terminal/replan/reconcile
```

Nếu ledger-backed claim là cần thiết để đồng bộ nhiều Runtime process, schema tối thiểu nên là một scheduling table riêng, ví dụ:

```text
checkout_resource_claims
  claim_id
  checkout_id
  resource_class
  owner_type          = MANAGED_JOB | NATIVE_SEMANTIC
  owner_id_hash       = opaque, content-free
  lifecycle_state     = active | released | expired
  acquired_at
  expires_at
  updated_at
```

Invariant:

```text
at most one active HEAVY claim per checkout
expired claim reconciled before new insert
claim acquisition and conflict decision happen in one BEGIN IMMEDIATE transaction
managed job row and its claim are created/terminalized consistently
semantic claim never creates a fake managed_process_jobs row
claim owner never implies process terminate authority
```

Không tạo generic scheduler framework. Table này chỉ được triển khai khi concurrent-start test trước patch chứng minh oracle có thể quan sát cửa sổ race hoặc khi cross-runtime atomic guarantee được giữ làm acceptance bắt buộc.

## 26.4. Wave R0 — Reconcile authority và freeze acceptance

### Mục tiêu

Tạo base sạch cho implementation mà không đụng documentation reorganization hiện tại.

### Hành động

1. Xác nhận root/branch/HEAD/origin và owner của staged documentation deletions.
2. Chọn một trong hai:
   - đợi documentation wave checkpoint/commit; hoặc
   - tạo isolated worktree từ exact accepted `origin/main`.
3. Xác nhận không có active write fence trên các surface:

```text
crates/webcodex-core/src/lsp_bridge.rs
crates/webcodex-runner/src/webcodex_runner/lsp/
src/connector_runtime/semantic_bridge.rs
resources/coding-tools-mcp/coding_tools_mcp/
resources/coding-tools-mcp/tests/
```

4. Pin acceptance matrix và source fingerprint trước write.

### Exit criteria

```text
base HEAD verified
target source paths clean hoặc isolated
conflicting write fence = 0
managed HEAVY = 0
concurrent docs changes không tham gia source fingerprint
```

## 26.5. Wave R1 — Bounded LSP resource-status handshake

### Mục tiêu

Biến telemetry hiện có thành input thật cho semantic classification và operator diagnosis.

### Projection tối thiểu

```text
lsp_resource
  lifecycle_state       = STOPPED | STARTING | RUNNING | FAILED
  warm                  = true | false | unknown
  pressure_state        = NORMAL | SOFT | HARD | UNKNOWN
  process_instance_id   = opaque
  working_set_bytes     = number | null
  peak_working_set_bytes= number | null
  pending_request_count
  restart_count
  drain_count
  observed_at
```

Không expose raw PID nếu consumer không cần. Không expose executable path, project absolute path, query, source, stderr hoặc credential-file path.

### Candidate surfaces

```text
crates/webcodex-core/src/lsp_bridge.rs
crates/webcodex-runner/src/webcodex_runner/lsp/navigation.rs
crates/webcodex-runner/src/webcodex_runner/lsp/navigation_tests.rs
src/connector_runtime/semantic_bridge.rs
resources/coding-tools-mcp/coding_tools_mcp/semantic_localization.py
```

Ưu tiên optional resource block trong existing status/internal contract. Không thêm public MCP tool và không làm status call start LSP.

### Classification contract

| Scope | Lifecycle/warm/pressure | Resource class/action |
|---|---|---|
| focused file | warm + NORMAL | MEDIUM, native allowed nếu không có policy conflict |
| focused file | STOPPED/STARTING/UNKNOWN | HEAVY claim trước native call |
| workspace/directory | any usable state | HEAVY claim |
| any | HARD | native deny/fallback; safe drain after pending=0 |
| workspace | SOFT | native deny/fallback; eligible early drain |
| status only | any | LIGHT, no server start |

### Tests

- status on absent server returns `STOPPED` without process spawn;
- running server returns content-free instance/pressure snapshot;
- unsupported metrics stay `null/UNKNOWN`;
- serialization backward-compatible với optional field;
- credential/path/query không xuất hiện trong JSON;
- cold focused classification = HEAVY;
- warm normal focused classification = MEDIUM.

### Exit criteria

```text
one bounded status contract
one demonstrated scheduling consumer
no public tool-count change
status read has zero process side effect
```

## 26.6. Wave R2 — Atomic checkout resource claim

### Mục tiêu

Đóng check-then-call window giữa semantic admission và managed HEAVY admission trên nhiều Runtime process.

### Implementation rules

1. Acquire claim trong một SQLite transaction có write serialization.
2. Managed HEAVY và semantic HEAVY dùng cùng conflict key.
3. Semantic giữ claim qua toàn bộ native provider call và release trong `finally`.
4. Managed HEAVY giữ claim tới terminal/replan/reconcile.
5. Runtime crash được phục hồi bằng bounded expiry + process/runtime identity reconciliation.
6. Không release claim của owner khác dựa chỉ trên PID.
7. LIGHT inspection vẫn chạy khi HEAVY claim bận.
8. MEDIUM focused semantic không chiếm HEAVY claim sau khi warm + normal đã được chứng minh.

### Candidate surfaces

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/execution_resources.py
resources/coding-tools-mcp/coding_tools_mcp/context_tools.py
resources/coding-tools-mcp/tests/test_execution_resources.py
resources/coding-tools-mcp/tests/test_task_state_and_build.py
```

### Deterministic concurrency oracle

Tạo barrier test với hai Runtime instance trỏ cùng checkout/ledger:

```text
lane A: acquire semantic HEAVY claim
lane B: acquire managed HEAVY claim
barrier: release both attempts simultaneously
assert: exactly one acquired
assert: loser reason = HEAVY_SLOT_BUSY
assert: active HEAVY claim count never > 1
assert: winner terminal/release → loser retry succeeds
```

Chạy ít nhất 100 iterations bằng synthetic provider/process để tăng khả năng phát hiện race mà không tạo tải Rust thật. Đây là concurrency proof, không phải performance benchmark.

### Negative/repair tests

- provider exception release claim trong `finally`;
- process spawn failure không để claim active;
- expired semantic claim được reconcile;
- stale runtime không release current claim;
- REPLAN terminalizes managed claim nhưng không đụng Connector process;
- restart giữa acquire/release fail closed;
- repeated release idempotent;
- public snapshot redacts owner identity.

### Exit criteria

```text
100/100 barrier iterations: active HEAVY claims <= 1
sequential fallback/recovery tests still PASS
no fake managed job for LSP
no process kill added to claim reconciliation
```

## 26.7. Wave R3 — Live Connector/Runner soak

### Mục tiêu

Nâng evidence từ `real_process_and_synthetic_pressure_equivalent` lên một live profile run có real Connector/Runner artifact và real rust-analyzer.

### Environment

- Windows host hiện tại là primary acceptance host;
- exact Connector/Runner artifact identity được record;
- exact Git HEAD/source fingerprint được record;
- rust-analyzer availability/version được record nhưng không log executable path;
- test profile có bounded idle TTL thấp để không chờ production TTL 15 phút;
- không có unrelated Cargo/full-test HEAVY;
- no Recovery/documentation writer trên source surface.

### Scenario matrix

1. Cold focused file: claim HEAVY, native `document_symbols`, process snapshot numeric hoặc explicit UNKNOWN.
2. Warm focused file: same process instance, MEDIUM path, stable result.
3. Warm workspace: HEAVY claim, bounded concurrency, ordered/sanitized result.
4. Idle: stop traffic, exact LSP tree exits, Connector sống.
5. Cold restart: new process instance, native handled.
6. Managed Cargo conflict: simultaneous barrier, exactly one HEAVY claimant.
7. Semantic exception/timeout: claim released, text fallback usable.
8. Soft/hard synthetic threshold override against real process: no mid-flight kill, safe drain.
9. Connector shutdown: correct descendant tree gone.
10. Repeat cold/warm/idle/restart tối thiểu 10 cycles.

### Metrics

```text
cold_semantic_latency_ms[]
warm_semantic_latency_ms[]
workspace_semantic_latency_ms[]
lsp_working_set_bytes[]
lsp_peak_working_set_bytes[]
claim_wait_ms[]
semantic_claim_allowed/rejected
managed_claim_allowed/rejected
idle_teardown_count
restart_count
drain_count
fallback_count
orphan_count
overlap_count
unknown_owner_count
```

Record sample size và distribution (`min/median/p95/max`) thay vì chỉ một snapshot.

### Hard acceptance

```text
10/10 lifecycle cycles PASS
overlap_count = 0
orphan_count = 0
unknown_owner auto-kill = 0
active request mid-flight kill = 0
fallback under denial/exception PASS
final active claim = 0
final active managed HEAVY = 0
final write fence = 0
```

## 26.8. Wave R4 — Threshold calibration decision

### Mục tiêu

Quyết định giữ hay đổi production defaults 2 GiB/3 GiB dựa trên live series, không dựa trên cảm giác hoặc một peak đơn lẻ.

### Decision rule

Giữ defaults nếu:

```text
normal live p95 < soft limit
no false soft/hard drain trong 10-cycle soak
host vẫn giữ quiescence margin hợp lý
```

Chỉ đề xuất đổi nếu data cho thấy một trong các trường hợp:

- normal operation thường xuyên vượt soft limit;
- hard limit không ngăn được host pressure trước khi fallback/drain;
- platform metric semantics khác nhau rõ rệt.

Mọi thay đổi threshold phải:

- giữ `hard > soft > 0`;
- có deterministic override test;
- document host/sample scope;
- không biến measurement máy này thành universal guarantee;
- không thêm auto-tuning loop ở phase này.

### Exit criteria

Một decision record rõ ràng: `KEEP_DEFAULTS` hoặc `CHANGE_TO(...)`, kèm evidence window/sample size và rollback.

## 26.9. Wave R5 — Operationalization và delivery

### Documentation

Sau khi documentation reorganization hiện tại được settle, cập nhật đúng các canonical docs còn tồn tại:

```text
docs/CURRENT_STATE.md
docs/LSP_NAVIGATION.md
docs/ARCHITECTURE.md
docs/research/260816_P2-P3-remaining-operational-hardening-implementation-plan.md
```

Không tự restore các docs đang bị xóa bởi wave khác. Nếu canonical docs thay đổi, resolve destination từ trạng thái repository mới thay vì dùng danh sách cũ như hardcoded authority.

### Final verification ladder

1. scoped diff/static/schema check;
2. status/classification focused tests;
3. atomic claim unit + 100-iteration barrier test;
4. process/LSP memory regression tests;
5. native semantic auth/scope/sanitation tests;
6. live Connector soak 10 cycles;
7. smart-v3 public tool contract test;
8. final ledger/job/claim/fence health snapshot.

Không rerun full workspace suite nếu các affected boundaries trên đã đủ và không có cross-cutting compile failure. Nếu public `lsp_status` schema đổi, chạy representative consumer tests ở `webcodex-core`, Runner và tool runtime.

### Git/EOCL delivery

```text
source wave CHECKPOINTED
selective stage only intended source/tests/docs
do not include concurrent documentation deletions by accident
preserve canonical ledger as volatile runtime evidence; do not stage it
git diff --cached --check
staged secret-pattern scan
commit without amend/reset/rebase
push only when delivery authorization includes push
verify local HEAD == origin/main after push
```

## 26.10. Priority và execution order

| Priority | Hạng mục | Lý do |
|---|---|---|
| P0 | R0 authority/worktree reconciliation | Worktree hiện có concurrent staged documentation changes; không được mở overlapping writer |
| P1 | R1 bounded status handshake | Là dependency để phân biệt cold single-file với warm focused request |
| P1 | R2 atomic checkout claim | Đóng hard concurrency guarantee còn thiếu |
| P1 | R3 live Connector soak | Chuyển equivalent proof thành live operational evidence |
| P2 | R4 threshold decision | Chỉ tuning sau khi có series thật |
| P2 | R5 docs/delivery | Đồng bộ operator contract và accepted source |
| P3 | Trend/retention automation | Chỉ mở khi có consumer và retention requirement thật |

Authoritative order:

```text
R0 reconcile/isolate
  → R1 resource-status handshake
  → R2 atomic scheduling claim
  → focused concurrency proof
  → R3 live soak
  → R4 keep/change threshold decision
  → R5 docs + EOCL + selective delivery
```

Không chạy R1/R2 song song vì status contract quyết định semantic resource classification. R3 chỉ bắt đầu sau khi barrier oracle của R2 đã xanh.

## 26.11. Definition of Done — remaining completion

```text
[x] concurrent HEAVY admission is atomic across Runtime instances
[x] cold focused semantic cannot bypass HEAVY claim
[x] warm normal focused semantic retains MEDIUM fast path
[x] status projection is bounded, content-free and side-effect-free
[x] semantic/provider failure cannot leak an active claim
[x] managed terminal/replan/reconcile releases only its own claim
[x] 100/100 simultaneous barrier iterations keep active HEAVY <= 1
[x] 10/10 real Connector lifecycle cycles PASS
[x] live working-set/latency sample series recorded
[x] explicit KEEP_DEFAULTS or threshold-change decision recorded
[x] smart-v3 public tool count remains 8
[x] final overlap/orphan/stale/fence/claim counts are 0
[x] no CONNECTOR_PROFILE kill-ownership schema added without new failure evidence
[x] no automatic cargo clean or global process-name kill added
[x] unrelated documentation reorganization preserved
[x] bounded governor snapshot always keeps active managed jobs visible ahead of terminal history
[ ] accepted source selectively committed; push/readback only when authorized
```

Các mục kỹ thuật/vận hành của checklist đã đạt **production operational closure with atomic admission and live soak evidence** trong worktree hiện tại. Mục selective commit/push vẫn là delivery boundary riêng và chỉ thực hiện khi có authorization.

## 26.12. Implementation/evidence record — 2026-08-16 20:59 +07:00

### Trạng thái wave

| Wave | Trạng thái | Evidence/decision |
|---|---|---|
| R0 — authority/worktree | PASS có điều kiện | Root/branch/HEAD được xác minh là repository được user chỉ định, `main` tại `cf6cb6dd`; chỉ sửa source/test/doc thuộc hardening. Concurrent documentation/source changes ngoài scope không bị restore, stage, reset hoặc overwrite. |
| R1 — status handshake/classification | IMPLEMENTED + FOCUSED PASS | `lsp_status` có bounded content-free resource projection; internal semantic status route không model-advertised; `STOPPED/UNKNOWN` focused là HEAVY; chỉ `RUNNING + warm=true + NORMAL` focused là MEDIUM; warm-only request không được cold-start server. |
| R2 — atomic claim | IMPLEMENTED + PASS | Ledger schema v7 có checkout-scoped partial unique HEAVY claim dùng chung cho managed job và native semantic. Barrier semantic↔managed đạt 100/100, đúng một winner, loser `HEAVY_SLOT_BUSY`, claim trở về 0 mỗi vòng. |
| R3 — live Connector soak | LIVE PASS 10/10 | Profile cô lập `p3-live` dùng Runner TTL 5 giây; real Connector/Runner/rust-analyzer hoàn tất 10 cold/warm/workspace/idle/restart cycles, mỗi restart có opaque process identity mới; final LSP `STOPPED`; barrier có đúng một winner và loser `HEAVY_SLOT_BUSY`. |
| R4 — threshold decision | `KEEP_DEFAULTS` | Giữ soft/hard defaults 2 GiB/3 GiB. Live sample n=10 có working-set p95 `14,573,568` bytes, peak p95 `29,593,600` bytes, `drain_count=0`; không có evidence để hạ/tăng production defaults. Đây chỉ là host-scoped calibration. |
| R5 — operationalization | SOURCE/HARNESS/DOC COMPLETE, DELIVERY PENDING | Harness ghi structured blocker, bounded workspace-index warm-up, exact artifact/source identity và final ledger health. Canonical docs đã được đồng bộ. Chưa commit/push vì worktree có concurrent unrelated changes và không có authorization delivery. |

### Implementation đã hoàn tất

1. Core/Runner:
   - thêm `DocumentSymbolsExisting` và resource status projection;
   - document sync + symbol request nằm trong cùng owned operation;
   - warm-only admission giữ map/operation guard để đóng idle-reaper race;
   - scheduling claim không có quyền kill process và không tạo fake `managed_process_jobs` cho LSP.
   - thêm Agent profile override `lsp_idle_ttl_seconds` có bound `1..=86400`, mặc định omission vẫn dùng 15 phút và thay đổi cần Runner restart; live profile dùng 5 giây, không đổi production default.
2. Connector/tool runtime:
   - thêm exact internal route `/api/connector/internal/semantic/status` với project-credential/workspace validation;
   - MEDIUM file request bắt buộc existing server; HEAVY được dùng cho cold/unknown/workspace;
   - public model surface không tăng tool.
3. Coding Tools MCP:
   - schema v7 thêm `checkout_resource_claims` và một partial unique index cho active checkout HEAVY;
   - managed HEAVY job + claim được insert atomically; terminal/quiesced chỉ release claim của chính owner;
   - semantic lease release bằng owner hash trong `finally`, kể cả provider exception/expiry race;
   - mọi native path đã biết (`prepare_coding_context` và Code Mode semantic binding) đều đi qua status classification + claim;
   - cross-runtime reconciliation chỉ mutate row khi cùng process hoặc cùng logical runtime; runtime đồng thời khác chỉ observe scheduling state.
   - claim `MANAGED_JOB` do schema mới backfill được release khi chính managed Job tương ứng đã terminal; không mutate Job/process của runtime khác và không release owner không xác định.
4. Operational harness:
   - `run_resource_hardening_soak.py` tiếp tục tự nhận diện mode là `real_process_and_synthetic_pressure_equivalent`;
   - thêm `run_live_connector_resource_soak.py`, chỉ dùng binding máy/env hiện hữu, yêu cầu exact artifact IDs, file/query ổn định và tối thiểu 10 cycles;
   - live report ghi source fingerprint, rust-analyzer version, cold/warm/workspace latency distribution, working-set/peak, claim wait, opaque process identity, conflict, lifecycle và final ledger health;
   - thiếu binding/status/artifact trả structured `blocked`, không fallback sang fake production binding.
   - provider failure giữa cycle cũng trả structured `LIVE_NATIVE_CALL_FAILED`; workspace symbol index có bounded retry trong cùng HEAVY claim để phân biệt warm-up với capability failure.

### Verification đã quan sát

```text
Python focused matrix:
  35 passed, 1 skipped, 60 deselected, 5 subtests passed

Atomic governor file (bao gồm barrier 100 vòng và cross-version claim reconciliation):
  15 passed

webcodex-core lsp_bridge tests:
  7 passed

webcodex-runner navigation tests:
  35 passed, 1 ignored

Equivalent operational soak (--skip-root-semantic):
  7/7 checks PASS
  final fingerprinted rerun 7/7 checks PASS; hard gate was point-in-time busy
  because another managed Cargo owner started concurrently
  active_heavy_claim_count = 0
  heavy_overlap_detected_count = 0
  orphan_process_count = 0
  active_write_fence_count = 0
  stale_orchestration_run_count = 0
  source_fingerprint = 4d8e15a625643c34558cd1b1f6efe668b3803beb29a11f3f72579ceff59c3968

Smart-v3 contract:
  exact public tools = 8

Formatting/module budget:
  cargo fmt --all -- --check = PASS
  check_module_size.py = PASS

Live Connector/Runner/rust-analyzer acceptance:
  artifact window = 2026-08-16T13:53:50.219Z..13:57:44.451Z
  cycles = 10/10 PASS
  Connector SHA-256 = c4306afe77ed17a4e281fdaad40cb79bfb18f946d55777e60106041e7515557d
  Runner SHA-256 = 7d6c4a013016d717cacd71d678a1a34b59ca0d7ab3f7c88d531cf2f64029b0a7
  launcher SHA-256 = 18d552e0c290ecd79117bfa75b182b398234eede444dabf26071e1e4dd01053a
  rust-analyzer = 1.92.0 (ded5c06c 2025-12-08)
  source fingerprint = 629dfd66b50e58c396dd89c93882159df053e0e85ea000ffeed2c7c2deee13c2 (34 files)
  cold latency p95 = 905 ms
  warm latency p95 = 813 ms
  workspace latency p95 = 8,860 ms
  claim wait p95 = 1,968 ms
  LSP working-set p95 = 14,573,568 bytes
  LSP peak working-set p95 = 29,593,600 bytes
  final claim/overlap/orphan/fence/stale = 0/0/0/0/0
  report = .coding-tools/orchestration/p3-live-connector-resource-soak.json
  report SHA-256 = 77090a28309eb44bc3d76f86592badfb27325d9f64cff8240e0883e3a225adc7
```

Health timeline cần đọc theo causal ledger thay vì lấy một snapshot đơn lẻ:

- run đầu tại `2026-08-16T12:17:55Z` PASS toàn bộ hard acceptance với claim/overlap/orphan/fence/stale đều `0`;
- fingerprinted rerun tại `2026-08-16T12:24:46Z` vẫn có 7/7 checks PASS, nhưng một owner khác đã bắt đầu managed Cargo HEAVY lúc `12:24:21Z`, nên `active_heavy_claim_count=1` và overall report fail-closed;
- row này là `running`, có live owned process tree (`cmd → cargo → rustc`), không phải orphan/stale/leak; không được kill hoặc sửa ledger từ wave này.
- owner tự kết thúc trước `2026-08-16 19:34:46 +07:00`; final read-only health snapshot trở lại `active_heavy_claim_count=0`, overlap/orphan/fence/stale đều `0`. `active_run_count=4` là projection point-in-time và không vi phạm hard gate khi không có stale run/fence/job/claim.
- live rerun quan sát một managed Job của runtime cũ terminalize sau khi schema v7 đã backfill claim; Job đã `exited` nhưng claim còn active. Reconcile mới chỉ release claim khi owner hash khớp đúng một terminal Job, không kill/mutate process và không đụng owner chưa xác định; focused governor file tăng từ 14 lên 15 tests và PASS.
- final fingerprint-complete live run tại `13:53:50Z..13:57:44Z` PASS 10/10 với exact Connector/Runner hashes, final LSP `STOPPED`, claim/overlap/orphan/fence/stale đều `0`. Sau Ctrl-C, Connector Server, Runner, rust-analyzer, Cargo và rustc đều không còn process.

Root `webcodex` Connector/tool-runtime test binary đã vượt blocker `E0063` cũ và đi vào link, nhưng focused command `cargo test -p webcodex -j 1 connector_runtime::semantic_bridge::tests` được dừng graceful trước test execution khi riêng Cargo/rustc đạt khoảng 5.1 GiB working-set và host chỉ còn 10.25% RAM trống. Sau Ctrl-C đúng owned job, Cargo/rustc trở về 0 và free RAM phục hồi 41.37%. Không tuyên bố test này PASS; production bin build, Core/Runner focused tests và real Connector route 10-cycle soak là evidence acceptance hiện có. Không đánh đổi host safety để chạy một root test binary quá rộng.

### Lệnh live acceptance đã thực thi

```powershell
python resources/coding-tools-mcp/scripts/run_live_connector_resource_soak.py `
  --repository E:\Github\Tools-Codex-web `
  --file src/connector_runtime/semantic_bridge.rs `
  --query semantic_resource_status `
  --connector-artifact-id sha256:c4306afe77ed17a4e281fdaad40cb79bfb18f946d55777e60106041e7515557d `
  --runner-artifact-id sha256:7d6c4a013016d717cacd71d678a1a34b59ca0d7ab3f7c88d531cf2f64029b0a7 `
  --cycles 10 `
  --output .coding-tools/orchestration/p3-live-connector-resource-soak.json
```

Harness không nhận raw credential trên command line; nó chỉ dùng native-LSP binding đã được cấu hình qua contract hiện hữu. Final report có `passed=true`, đủ 10 cycles và đầy đủ working-set/latency series, nên hai checklist R3 đã được đóng.

### Delivery state

Không commit, push, release, deploy, restart service, kill process theo tên hoặc chạy automatic `cargo clean`. Worktree vẫn dirty bởi cả implementation này và các thay đổi concurrent ngoài scope; selective delivery còn chờ authorization riêng.

## 26.13. EOCL/operator observability continuation — 2026-08-16 21:18 +07:00

Đánh giá delivery tiếp theo phát hiện một gap nội bộ độc lập với live soak: `ExecutionResourceGovernor.snapshot(limit=N)` tính đúng `active_command_count`, nhưng trước đây lấy trực tiếp `N` row mới nhất nên một active Job cũ có thể biến mất khỏi bounded `jobs` khi terminal history mới hơn đủ lớn.

Implementation đã được thu hẹp đúng hai file governor/test:

- bounded `jobs` ưu tiên active lifecycle trước, sau đó mới dùng terminal/history để lấp phần limit còn lại;
- mỗi nhóm vẫn giữ deterministic order hiện hữu và chỉ chọn các row mới nhất nếu chính nhóm đó vượt limit;
- counts và sanitized public row fields không đổi; không expose command text, argv, environment, secret hoặc schema field mới;
- regression tạo một active Job cũ cùng năm terminal Job mới hơn với `limit=3`, rồi chứng minh active Job vẫn đứng đầu và hai terminal row mới nhất vẫn giữ thứ tự.

Verification:

```text
python -m py_compile coding_tools_mcp/execution_resources.py = PASS
focused snapshot regression = 1 passed, 19 deselected
test_execution_resources.py = 20 passed
check_module_size.py = PASS
```

Proof lineage sau live soak được record tách bạch:

```text
live base fingerprint       = 629dfd66b50e58c396dd89c93882159df053e0e85ea000ffeed2c7c2deee13c2
post-observability fingerprint = b516e25578765b114c21df369ca9a2f4f3a1735227a051e5092b06de04639960
fingerprinted files         = 34
delta from live base        = execution_resources.py + test_execution_resources.py only
```

Không gán artifact live cũ cho byte-for-byte source mới. Live 10-cycle evidence vẫn là base proof; delta chỉ đổi bounded selection của sanitized operator snapshot, không đổi admission, claim, process lifecycle, Connector route hoặc LSP provider. Vì vậy full governor file 20/20 và focused regression là sufficient changed-behavior proof; không restart topology/rerun live soak chỉ để làm nghi thức.

Projection quan sát lúc `2026-08-16 21:18 +07:00`, `run_id=ae9ac4714f3748008b2cb5830c2efd68` ở `REPLAN`, là run chẩn đoán observability này, không phải P2/P3 soak. Check cũ dùng selector `-k "snapshot or active"` khi chưa có test mang tên tương ứng nên pytest trả exit `5` với `19 deselected`; run đó không ghi source (`modified_files=[]`). Continuation hiện tại đã triển khai và prove objective, nhưng không manually edit ledger/task-state hoặc giả lập `ACCEPTING/CHECKPOINTED` cho historical run. `.coding-tools/task-state.json` là volatile projection và đã chuyển sang run concurrent khác sau observation này; causal history phải đọc từ ledger.

Delivery policy cũng được reconcile theo `AGENTS.md`: SQLite ledger là first-class volatile runtime evidence, không phải source để commit. Selective source delivery phải loại `.coding-tools/orchestration/ledger.sqlite3`, WAL/SHM và projections, đồng thời giữ source fingerprint/report checksum trong maintained documentation. Commit/push vẫn chờ authorization riêng.
