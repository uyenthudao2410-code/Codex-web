# P2/P3 Orchestration & Resource Control — Phân tích vấn đề và phương án xử lý triệt để

**Dự án:** `E:\Github\Tools-Codex-web`  
**Ngày phân tích:** 2026-08-16  
**Phạm vi:** EOCL / Coding MCP / Codex App Server / Cargo-Rust / rust-analyzer / WebCodex Connector / live semantic proof  
**Mục tiêu:** Loại bỏ tình trạng chạy kéo dài, máy lag, process còn sống sau khi wave đã `REPLAN/STOP`, build/test chồng lấn, và semantic localization gây tải toàn workspace không cần thiết.

---

## 1. Tóm tắt điều hành

Vấn đề hiện tại không phải một lỗi đơn lẻ của Rust, Cargo hay `rust-analyzer`. Đây là một lỗi kiến trúc điều phối gồm ba lớp chưa được đồng bộ hoàn toàn:

1. **Control plane — EOCL** quản lý `RUN/WAVE`, trạng thái `PREFLIGHT → EXECUTING → PROVING → ACCEPTING`, write lease và acceptance.
2. **Execution plane — Coding MCP / Codex app-server** thực sự sinh các command như `pytest`, `cargo test`, `cargo build`, `rustc`, WebCodex Connector và LSP.
3. **OS process/resource plane — Windows** chịu tải CPU/RAM/I/O và quyết định process nào vẫn còn sống.

EOCL hiện kiểm soát khá tốt tính hợp lệ của workflow, nhưng chưa nắm chặt **ownership và lifecycle của toàn bộ process tree**. Vì vậy có thể xuất hiện trạng thái:

```text
EOCL: REPLAN / không có active lane
               |
               X  ownership không đồng bộ đầy đủ
               |
ChatGPT.exe
  └─ codex.exe app-server
       └─ pwsh.exe
            └─ cargo.exe
                 ├─ rustc.exe
                 └─ rustc.exe
```

Điều này giải thích trực tiếp hiện tượng người dùng quan sát: UI/workflow trông như đã dừng hoặc đang chờ model nhưng máy vẫn nóng, RAM vẫn tăng, disk vẫn hoạt động và delay vẫn lớn.

**Khuyến nghị trọng tâm:** Không giải quyết bằng cách mở thêm agent/worker. Cần bổ sung một **Global Execution & Resource Governor** giữa EOCL và OS, đồng thời gắn mọi command nặng vào một **managed process group/Windows Job Object theo RUN/WAVE**. Khi wave chuyển `REPLAN`, `ABORTED`, `STOPPED` hoặc bị supersede, toàn bộ descendant process của wave phải được teardown có kiểm soát trước khi wave mới được phép chạy.

---

## 2. Các triệu chứng đã quan sát

### 2.1 Máy lag mạnh khi live semantic proof và verification chạy nối tiếp

Trong quá trình P3, `rust-analyzer` từng phải index project lớn và working set đạt nhiều GB. Cùng thời điểm đó còn có các workload khác như full Python suite, Cargo compile/test và command inspection.

Hậu quả:

- CPU contention;
- memory pressure và paging;
- filesystem/page-cache contention;
- command nhẹ như process inspection cũng bắt đầu delay;
- polling MCP bị transport delay;
- wrapper timeout khiến state khó phân biệt giữa "test fail" và "host quá tải".

### 2.2 Process vẫn chạy sau khi orchestration đã chuyển trạng thái

Snapshot hiện trường cho thấy EOCL đang ở `REPLAN`, không có coordinated lane đang đăng ký, nhưng process tree vẫn có:

```text
ChatGPT.exe
  └─ codex.exe app-server
       └─ pwsh.exe
            └─ cargo test -p webcodex ...
                 └─ rustc.exe
```

Tại một lần đo, hai `rustc.exe` dùng xấp xỉ:

```text
~1.0 GiB working set
~1.56 GiB working set
```

Tức riêng compiler đã vượt khoảng 2.5 GiB, chưa tính Cargo, ChatGPT, Codex, Python, cache và các process hệ thống.

### 2.3 `rust-analyzer` bị yêu cầu làm việc cấp workspace dù caller có scope nhỏ

Luồng semantic hiện tại nhận `path`, nhưng `semantic_bridge.rs` vẫn gọi `workspace_symbols` rồi mới lọc symbol theo `path` sau khi LSP trả kết quả.

Mô hình hiện tại:

```text
caller path=src/some_file.rs
        |
        v
workspace/symbol toàn project
        |
        v
rust-analyzer index/search rộng
        |
        v
filter path sau cùng
```

Đây là anti-pattern đối với repo lớn: scope đã biết nhưng không được dùng để giảm workload upstream.

### 2.4 Timeout được sửa nhưng resource behavior vẫn chưa tối ưu

P3 trước đó đã sửa một defect thật:

- Python native semantic HTTP timeout: `5s → 35s`;
- Rust semantic query fan-out: sequential → concurrent.

Điều này sửa mismatch deadline, nhưng trong trạng thái LSP cold, nhiều query `workspace_symbols` chạy đồng thời có thể làm **burst tải lớn hơn**. Tức correctness tốt hơn nhưng resource scheduling chưa đủ thông minh.

### 2.5 Full verification bị dùng trong lúc host chưa quiescent

Có thời điểm full Python suite được chạy trong khi semantic/LSP đang warm hoặc host vẫn chịu tải. Đây là orchestration sequencing chưa hợp lý: hai workload độc lập nhưng đều nặng lại cạnh tranh cùng CPU/RAM/I/O.

---

## 3. Evidence kỹ thuật quan trọng

### 3.1 EOCL và process tree không phản ánh cùng một thực tại

EOCL snapshot:

```text
orchestration_state = REPLAN
execution_mode      = mcp_only
write_owner         = empty
write_lease_id      = empty
lane list           = []
```

Nhưng OS snapshot đồng thời vẫn có Cargo/Rustc do Codex app-server sinh ra.

Đây là bằng chứng mạnh cho thấy hiện còn khoảng trống giữa:

```text
logical workflow lifecycle
        vs
OS process lifecycle
```

### 3.2 Process không phải process ngẫu nhiên ngoài hệ thống

Parent chain đã xác định:

```text
explorer.exe
  └─ ChatGPT.exe
       └─ codex.exe app-server
            └─ pwsh.exe
                 └─ cargo.exe
                      └─ rustc.exe
```

Do đó process nặng vẫn thuộc execution ecosystem của ChatGPT/Codex, không phải một Cargo terminal hoàn toàn không liên quan.

### 3.3 `target/` tăng lớn là hệ quả bình thường của repeated Rust builds

`target/` đã được đo khoảng **7 GiB+**, chủ yếu:

```text
target/debug/incremental  ~3.0 GiB
target/debug/deps         ~2.38 GiB
target/debug/build        ~0.33 GiB
target/release/deps       ~0.86 GiB
target/release/build      ~0.19 GiB
```

Repeated `cargo test/build` làm tăng:

- incremental compilation cache;
- dependency artifacts;
- test executables;
- debug symbols;
- build-script outputs.

`.coding-tools` chỉ lưu orchestration/history/proof; nó **không thay thế** `target/` vì không chứa compiled artifacts.

---

## 4. Root cause theo tầng

## 4.1 Root cause A — Process ownership chưa phải first-class EOCL concept

EOCL có write lease và state transition, nhưng command/process descendants chưa được bắt buộc gắn đầy đủ với:

```text
RUN_ID
WAVE_ID
OWNER
COMMAND_ID
PROCESS_GROUP_ID / JOB_ID
RESOURCE_CLASS
```

Nếu command được spawn qua một execution surface khác nhưng không được đăng ký đầy đủ, EOCL không thể đảm bảo teardown khi wave chết.

### Hệ quả

- wave `REPLAN` nhưng compile vẫn chạy;
- wave mới có thể cạnh tranh tài nguyên với wave cũ;
- operator tưởng workflow đã dừng nhưng OS chưa dừng;
- stale resource pressure làm các proof sau sai lệch về latency.

---

## 4.2 Root cause B — Không có global heavy-work admission control

Hiện chưa có một semaphore toàn host/check-out bắt buộc ngăn các workload nặng chạy đồng thời.

Các workload cần được xem là **HEAVY**:

- `cargo build` / `cargo test` khi compile xảy ra;
- `rustc`;
- cold `rust-analyzer` initialization/indexing;
- full Python suite;
- npm/electron packaging;
- full release build.

Nếu hai workload HEAVY chạy cùng lúc, hiệu quả thường thấp hơn chạy tuần tự vì memory pressure và I/O contention.

---

## 4.3 Root cause C — REPLAN chưa có quiescence barrier

`REPLAN` hiện chủ yếu là trạng thái logic. Nó cần thêm invariant:

```text
REPLAN_READY_TO_EXECUTE_NEXT_WAVE =
    no_active_write_lease
    AND no_managed_command_running
    AND no_managed_process_descendant_running
    AND no_foreign_heavy_process_on_same_checkout
```

Không đạt điều kiện này thì wave mới phải ở trạng thái chờ teardown/quiescence thay vì bắt đầu proof/build mới.

---

## 4.4 Root cause D — Semantic scope được lọc quá muộn

Khi đã biết một file cụ thể, `workspace_symbols` là công cụ quá rộng. Nên sử dụng `document_symbols` cho file đó.

Hiện trạng:

```text
file scope → workspace_symbols → filter
```

Mục tiêu:

```text
file scope → document_symbols → query/filter hierarchical symbols
workspace/dir scope → bounded workspace_symbols
```

---

## 4.5 Root cause E — Concurrency policy không phân biệt cold và warm LSP

`join_all` có lợi khi LSP đã warm, nhưng khi cold:

- mỗi request có thể kích hoạt/đợi initialization;
- global symbol requests làm nhiều work;
- burst request làm working set tăng nhanh;
- response latency không còn tỷ lệ thuận với concurrency.

Cần phân biệt:

```text
LSP_COLD  → concurrency = 1
LSP_WARM  → concurrency = bounded N, ví dụ 2-4
```

Không nên fan-out 8 query global ngay khi chưa có readiness proof.

---

## 4.6 Root cause F — Verification chưa được resource-aware

Progressive verification đúng về mặt logic nhưng cần thêm resource gate.

Sai lầm cần tránh:

```text
full pytest
+ rust-analyzer cold indexing
+ cargo compile
+ process probes
```

trên cùng host tại cùng thời điểm.

---

## 5. Kiến trúc mục tiêu

Đề xuất thêm tầng điều phối bắt buộc:

```text
User / ChatWeb Sol
        |
        v
+--------------------------+
| EOCL Control Plane       |
| RUN / WAVE / ACCEPTANCE  |
+--------------------------+
        |
        v
+-----------------------------------+
| Global Execution Resource Governor|
| - admission control               |
| - owner validation                |
| - heavy semaphore                 |
| - resource budgets                |
| - quiescence barrier              |
+-----------------------------------+
        |
        v
+------------------------------+
| Managed Process Job per Wave |
| Windows Job Object           |
| RUN_ID/WAVE_ID/JOB_ID        |
+------------------------------+
        |
        +------ cargo/rustc
        +------ pytest/python
        +------ rust-analyzer
        +------ webcodex
        +------ npm/electron
```

Mọi execution surface — MCP deterministic, Codex app-server, coordinated lane — phải đi qua cùng governor nếu thao tác trên authoritative checkout.

---

## 6. Giải pháp 1 — Managed Process Group / Windows Job Object

### 6.1 Mục tiêu

Một wave phải sở hữu toàn bộ process tree do nó spawn.

### 6.2 Metadata tối thiểu

```text
process_job {
  job_id,
  run_id,
  wave_id,
  command_id,
  owner,
  checkout_id,
  resource_class,
  root_pid,
  started_at,
  lifecycle_state
}
```

### 6.3 Windows implementation

Dùng **Windows Job Object** với semantics tương đương:

```text
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
```

Khi root command spawn child process (`cargo → rustc`, Python → subprocess...), child process phải nằm trong Job Object của wave.

### 6.4 State transition behavior

Khi wave chuyển:

```text
REPLAN
ABORTED
STOPPED
SUPERSEDED
```

runtime thực hiện:

1. gửi graceful termination;
2. chờ bounded grace period;
3. terminate Job Object nếu descendants còn sống;
4. xác nhận process count = 0;
5. ghi `wave_processes_quiesced` vào ledger;
6. mới cho phép wave kế tiếp acquire heavy slot/write lease.

### 6.5 Acceptance criteria

- Không còn `cargo/rustc/python/rust-analyzer/webcodex` của wave sau teardown deadline.
- Không kill process của wave khác hoặc process người dùng ngoài managed job.
- Restart MCP không làm mất ability reconcile process ownership record.

---

## 7. Giải pháp 2 — Global Resource Governor

## 7.1 Phân loại workload

### LIGHT

- `rg`/search source;
- small file reads;
- `git diff --check`;
- metadata inspection;
- small status queries.

Có thể chạy song song có giới hạn.

### MEDIUM

- focused Python single-file tests;
- `rustfmt --check`;
- small deterministic scripts.

Có thể chạy nếu không có host pressure.

### HEAVY

- Cargo compile/test;
- release build;
- full pytest;
- cold rust-analyzer;
- npm/electron packaging.

Mặc định **global concurrency = 1** trên authoritative checkout.

## 7.2 Admission rule

Trước khi start HEAVY job:

```text
if active_heavy_job exists:
    wait / queue
elif host_memory_pressure > threshold:
    defer
elif prior_wave_not_quiescent:
    reject start
else:
    acquire heavy slot
```

### 7.3 Host pressure signal

Không cần hệ thống autoscaling phức tạp. Một bộ signal đơn giản đủ hiệu quả:

- available RAM;
- total working set của managed heavy processes;
- CPU utilization rolling window;
- disk queue/IO pressure nếu có;
- number of active `rustc`;
- LSP state cold/warm.

### 7.4 Cargo-specific defaults

Với focused regression trên máy dev:

```text
CARGO_BUILD_JOBS=1 hoặc cargo -j 1
```

khi host đang pressure hoặc khi proof chỉ cần một target.

Không áp `-j 1` cứng cho mọi release build; governor có thể cho phép mức cao hơn khi host rảnh.

---

## 8. Giải pháp 3 — Quiescence Gate bắt buộc trước wave mới

Thêm một phase logic:

```text
REPLAN
  ↓
QUIESCING
  ↓
READY
```

Hoặc giữ state machine hiện tại nhưng thêm invariant `quiescent=true` trước `READY/EXECUTING`.

### Check tối thiểu

```text
active_command_count(run/wave) == 0
managed_descendant_count(run/wave) == 0
active_write_lease == none
heavy_slot_owner == none or this wave
foreign_heavy_same_checkout == none
```

Nếu phát hiện process thuộc ChatGPT/Codex nhưng không có EOCL owner record, đánh dấu:

```text
UNOWNED_EXECUTION_PROCESS
```

và fail closed cho workload nặng tiếp theo.

---

## 9. Giải pháp 4 — Sửa semantic localization theo scope thật

## 9.1 Single-file scope

Nếu `prepare_coding_context` nhận đúng một requested source file tồn tại và extension được LSP hỗ trợ:

```text
.rs  → rust-analyzer document_symbols
.py  → pyright document_symbols
.ts  → TypeScript document_symbols
...
```

Connector chỉ cần **một** `document_symbols` request cho file rồi lọc hierarchical symbols cho từng semantic query.

### Ưu điểm

- tránh global `workspace/symbol`;
- giảm request count;
- giảm pressure khi LSP cold;
- giữ kết quả read-only;
- giữ auth/workspace binding hiện tại;
- không thêm public tool.

## 9.2 Directory/workspace scope

Giữ `workspace_symbols`, nhưng:

- batch bounded;
- concurrency bounded;
- cold/warm aware;
- giới hạn max results upstream;
- text fallback vẫn hoạt động nếu LSP không xử lý được.

## 9.3 Matching document symbols

Cần flatten cây symbol một cách bounded:

```text
DocumentSymbol[]
  → DFS/BFS bounded
  → normalized project-relative rows
  → query match
  → max_results
```

Không leak absolute path hoặc `file://` URI.

---

## 10. Giải pháp 5 — Cold/Warm LSP State Machine

Runtime nên theo dõi trạng thái:

```text
STOPPED
STARTING
COLD_READY
WARM
FAILED
```

### COLD_READY

Server đã initialize nhưng chưa có evidence rằng workspace indexing đủ ổn định cho global symbol burst.

Policy:

```text
semantic concurrency = 1
prefer document scope
avoid broad workspace symbol batch
```

### WARM

Sau một request thành công hoặc readiness probe phù hợp:

```text
semantic concurrency = min(query_count, configured_limit)
```

Khuyến nghị default ban đầu: `2`, chỉ tăng khi telemetry chứng minh có lợi.

---

## 11. Giải pháp 6 — Progressive Verification có resource gate

Thứ tự đề xuất:

### Stage A — Static / zero-compile

```text
rustfmt --check scoped-file
git diff --check
Python syntax/static nếu cần
```

### Stage B — Focused unit/regression

Chỉ test đúng behavior vừa sửa.

Ví dụ:

```text
pytest test_single_file_scope_forwarding
cargo test -p webcodex native_semantic_bridge_document_scope -- -j 1
```

### Stage C — Affected subsystem

Chạy package/subsystem suite sau khi focused proof pass.

### Stage D — Live runtime proof

Build artifact cần thiết → restart có kiểm soát → live semantic proof.

### Stage E — Broad authority

Full Python suite/full release build chỉ chạy **một lần** ở fingerprint cuối, khi:

- không có LSP cold indexing;
- không có Cargo khác;
- host quiescent;
- source fingerprint ổn định.

### Proof reuse

Nếu fingerprint không đổi, không rerun proof đã pass chỉ vì một bước sau timeout.

---

## 12. Giải pháp 7 — Execution-plane registration bắt buộc

Codex app-server, Coding MCP và bất kỳ coordinated execution lane nào phải đăng ký command trước khi spawn.

### Spawn contract

```text
spawn_managed_command(
  run_id,
  wave_id,
  checkout_id,
  owner,
  resource_class,
  executable,
  argv
)
```

Nếu thiếu `run_id/wave_id` với workload HEAVY trên authoritative checkout:

```text
reject: EXECUTION_OWNERSHIP_REQUIRED
```

### Ngoại lệ

Các command người dùng chạy ngoài hệ thống không được tự ý kill. Governor chỉ nhận diện chúng là `foreign heavy process` và có thể chặn workload mới để tránh contention.

---

## 13. Giải pháp 8 — Tách Connector lifecycle khỏi MCP restart

WebCodex Connector từng biến mất sau restart MCP/Electron. Cần định nghĩa rõ ownership:

- Connector có phải child của MCP runtime không?
- hay persistent service theo profile?

Nếu mục tiêu live semantic yêu cầu Connector sống qua MCP restart, nên có một supervisor riêng hoặc persistent job lifecycle:

```text
connector_profile = p3-live
lifecycle = persistent_across_mcp_restart
```

Restart MCP không được vô tình kill Connector; ngược lại, khi test kết thúc phải có explicit stop/cleanup policy.

---

## 14. Giải pháp 9 — Disk usage policy cho `target/`

### 14.1 Không commit `target/`

`target/` là build artifact/cache, đã Git-ignore và có thể rebuild.

### 14.2 Không `cargo clean` giữa quá trình proof

Clean giữa P3 làm mất incremental cache và khiến build kế tiếp chậm hơn rất nhiều.

### 14.3 Cleanup sau acceptance

Sau khi P2/P3:

```text
CHECKPOINTED
+ live proof pass
+ commit/push verified
```

mới chạy policy cleanup.

Có thể có hai mode:

```text
soft cleanup:
  remove old temporary worktree target dirs
  optionally prune old incremental cache

hard cleanup:
  cargo clean
```

Hard cleanup chỉ khi thực sự cần reclaim toàn bộ disk.

---

## 15. Kế hoạch triển khai đề xuất

## Phase 0 — Stabilize ngay trước khi tiếp tục P3

1. Không start thêm workload HEAVY.
2. Xác định process tree hiện hữu trên authoritative checkout.
3. Phân loại owned/unowned.
4. Dừng managed/stale jobs không còn hợp lệ.
5. Xác nhận `cargo/rustc/rust-analyzer/pytest` quiescent.
6. Chỉ sau đó mới resume EOCL P3.

**Exit criterion:** host quiescent và không có compiler/LSP job vô chủ.

---

## Phase 1 — Process ownership & teardown

Implement:

- managed process record;
- Windows Job Object per wave;
- descendant teardown;
- ledger events;
- restart reconciliation.

Regression bắt buộc:

1. wave spawn command có child;
2. chuyển `REPLAN`;
3. toàn bộ descendants exit;
4. process của wave khác không bị ảnh hưởng.

---

## Phase 2 — Resource governor

Implement:

- resource class `LIGHT/MEDIUM/HEAVY`;
- global heavy semaphore;
- checkout-aware admission;
- memory/CPU pressure check;
- quiescence gate.

Regression:

- hai HEAVY commands không compile song song;
- LIGHT command vẫn chạy khi an toàn;
- stale/unowned heavy process chặn heavy admission mới.

---

## Phase 3 — Semantic scope optimization

Implement:

- caller forwards single requested existing file;
- Connector chooses `document_symbols` for supported file;
- bounded flatten/filter;
- fallback to workspace symbols for broader scopes;
- cold concurrency limit.

Regression:

- single file không gọi `workspace_symbols`;
- directory scope vẫn gọi workspace path;
- result order giữ nguyên;
- absolute paths không leak;
- auth/workspace binding giữ nguyên;
- public smart-v3 tool count vẫn = 8.

---

## Phase 4 — Live P3 acceptance

1. Focused tests pass.
2. Scoped rustfmt pass.
3. Affected Rust package test pass.
4. Build đúng Connector artifact.
5. Start Connector managed lifecycle.
6. Restart MCP controlled.
7. Verify instance change/reconnect.
8. Live semantic probe:

```text
semantic_attempted > 0
semantic_handled   > 0
```

9. Wrong-token/fake-token rejection proof.
10. Stale orchestration = 0.

---

## Phase 5 — Final broad verification & delivery

Khi host quiescent:

1. full Python suite;
2. release build authority;
3. `git diff --check`;
4. scoped/global format policy;
5. secret scan/staged diff review;
6. restore temporary Git config;
7. selective staging;
8. commit;
9. push;
10. verify local SHA == `origin/main` SHA.

---

## 16. Acceptance criteria tổng thể

P2/P3 chỉ được coi là hoàn tất khi đồng thời đạt:

### Orchestration

- `stale_orchestration_run_count = 0`;
- không active write lease vô chủ;
- không active managed process của terminal wave;
- restart reconstruct được acceptance/projection từ ledger.

### Resource lifecycle

- `REPLAN/ABORTED/STOP` terminalizes descendant process tree;
- không có Cargo/Rustc orphan thuộc ChatGPT/Codex execution plane;
- heavy workload concurrency tuân policy.

### Semantic

- native provider configured;
- live request có `semantic_attempted > 0`;
- live request có `semantic_handled > 0`;
- file-scoped request không cần global workspace symbol search;
- text fallback vẫn đúng khi provider không xử lý.

### Security

- credential không được in/log;
- wrong token bị từ chối;
- workspace binding fail closed;
- chỉ loopback origin hợp lệ;
- project-relative path only;
- read-only LSP semantics.

### Public contract

- smart-v3 public tool count vẫn là `8`;
- không thêm public tool chỉ để sửa orchestration nội bộ.

### Delivery

- tests/build cần thiết pass ở final fingerprint;
- intended source/test được stage;
- runtime/report junk không được stage;
- `.coding-tools/orchestration/ledger.sqlite3` được đưa vào commit theo policy dự án;
- remote SHA được xác minh sau push.

---

## 17. Priority đề xuất

### P0 — Làm ngay

1. Dọn/quiesce process hiện đang chạy.
2. Không cho HEAVY workload chồng nhau.
3. Hoàn thiện semantic file-scope để tránh global search không cần thiết.
4. Đóng P3 live proof.

### P1 — Ngay sau P3

1. Windows Job Object per wave.
2. Quiescence barrier.
3. Mandatory execution ownership registration.
4. Heavy-work global semaphore.

### P2 — Hardening

1. Cold/warm LSP state telemetry.
2. Adaptive concurrency.
3. Host resource pressure metrics.
4. Automatic post-wave process reconciliation.

### P3 — Optimization

1. Disk cache cleanup policy.
2. accepted-result latency/resource telemetry.
3. tuning Cargo parallelism theo host capacity.

---

## 18. Điều không nên làm

Không nên giải quyết tình trạng hiện tại bằng các cách sau:

- mở thêm nhiều agent cùng chạy build/test trên cùng checkout;
- tăng timeout liên tục mà không sửa scope/resource ownership;
- rerun full suite sau mỗi lỗi nhỏ;
- `taskkill /IM rustc.exe` hoặc kill toàn cục không biết ownership;
- `cargo clean` trước khi live acceptance hoàn tất;
- coi `REPLAN` logic đồng nghĩa OS đã quiescent;
- dùng `workspace_symbols` cho single-file scope rồi lọc hậu kỳ;
- cho một external execution plane tự chạy HEAVY command mà EOCL không có owner record.

---

## 19. Trạng thái triển khai và nghiệm thu P3

Phần dưới đây ghi nhận trạng thái thực thi, không phải giả định thiết kế. Evidence window: `2026-08-16T15:49:24+07:00`, workspace `E:\Github\Tools-Codex-web`, branch `main`, source HEAD tại thời điểm build/live proof `a8588b47c35d3fc009bebc131b0353dcdd7075b0`. Artifact runtime trong `.coding-tools/` được giữ nguyên như evidence volatile; không dùng nó làm source fingerprint.

### 19.1. Đã triển khai

- Execution ownership được đăng ký trước spawn cho MCP `exec_command`, OpenCode sidecar và Codex app-server sidecar; ledger schema đã nâng lên v6 với `managed_process_jobs`.
- Governor phân loại `LIGHT/MEDIUM/HEAVY`, áp dụng HEAVY semaphore theo checkout, gate memory/foreign-heavy, yêu cầu `run_id/wave_id` cho HEAVY và fail-closed khi ownership/PID identity không thể xác minh.
- Windows Job Object/process-group được gắn trước khi resume; terminal wave đóng descendant tree, restart reconciliation không kill PID không có handle ownership; `REPLAN/BLOCKED/ABORTED/CHECKPOINTED` yêu cầu quiescence trước wave thay thế.
- Semantic single-file scope forward đúng một file hiện hữu và dùng một `document_symbols` request; scope directory/workspace dùng `workspace_symbols` với cold concurrency `1`, warm concurrency tối đa `2`, giữ query order và project-relative paths. Absolute Windows/POSIX path và traversal bị từ chối.
- Connector giữ `semantic_lsp_warm` bằng `AtomicBool`; lỗi LSP hạ về cold. Smart-v3 public tool count vẫn là `8`.

### 19.2. Proof cuối

- Python full suite: `335 passed, 1 skipped, 25 subtests passed`.
- Resource/orchestration/provider/activation focused suites đã pass theo các proof window trước; regression resource/Windows hiện tại pass `12` tests.
- Rust semantic bridge: `cargo test -p webcodex -j 1 native_semantic_bridge -- --test-threads=1` → `6 passed, 0 failed` (chỉ còn 3 warning có sẵn ngoài phạm vi).
- Scoped Rust format check: `rustfmt --edition 2021 --check src/connector_runtime/semantic_bridge.rs` → pass.
- Final release authority sau patch path: `cargo build --release -p webcodex -j 1` → pass (`Finished release profile` trong `10m 36s`).

### 19.3. Live acceptance

- `webcodex status --profile p3-live`: `agent=online`, `connection=connected`, `ready=true`.
- Native semantic probe trên `src/connector_runtime/semantic_bridge.rs`: HTTP `200`, provider `webcodex_native_lsp`, `read_only=true`, `lsp_state=COLD_READY`, `semantic_concurrency=1`; hai query đều handled.
- Thực thi `Runtime.prepare_coding_context` live với một file: `semantic_attempted=2`, `semantic_handled=2`, `text_fallback_queries=0`, cả hai kết quả dùng `semantic:webcodex_native_lsp`, selected path chỉ gồm file yêu cầu.
- Security matrix: fake token `401`; workspace mismatch `403/semantic_workspace_mismatch`; traversal, absolute Windows và absolute POSIX đều `400/invalid_arguments`; không response nào làm lộ credential path hoặc local state path.
- Smart-v3 runtime projection: `8` tools, không thêm public tool cho orchestration nội bộ.
- Ledger health tại cùng evidence window: `stale_run_candidates=0`, active write fences `0`, active controller leases `0`, active managed process jobs `0`. Connector tree còn sống theo profile `p3-live`; không còn `cargo`, `rustc` hay `pytest` chạy sau proof.

### 19.4. Delivery note

Concurrent commit `6299c052567852607ddcda30fabe48c859eef932` sau evidence window đã đưa cùng delta regression classifier/Windows timing và absolute-path validation lên `main`/`origin/main`; do đó source P3 đã đồng bộ ở HEAD hiện tại. Worktree chỉ còn tài liệu nghiệm thu này và các artifact/runtime thay đổi ngoài source P3, cần selective review riêng. Không chạy `cargo clean` trong evidence window.

---

## 20. Kết luận

Sự cố lag vừa rồi là một **orchestration/resource-lifecycle defect**, không chỉ là "máy yếu" hay "Rust compile lâu".

Correctness layer của P2/P3 đã tiến triển đáng kể: stale reconciliation, EOCL durability, timeout contract và concurrent semantic dispatch đều giải quyết các lỗi thật. Tuy nhiên chúng chưa đủ để bảo đảm **time-to-accepted-result** tốt nếu execution process vẫn có thể sống ngoài lifecycle của wave và nếu semantic localization tiếp tục kích hoạt global indexing/search không cần thiết.

Giải pháp triệt để là đưa **OS process ownership và resource scheduling trở thành một phần của orchestration contract**:

```text
EOCL state
  + managed process ownership
  + Windows Job Object
  + global heavy-work governor
  + quiescence barrier
  + scope-aware semantic localization
  + progressive resource-aware proof
```

Khi các lớp này được nối lại, một trạng thái như `REPLAN` sẽ không chỉ đúng trên ledger/UI mà còn đúng ở mức máy thật: không còn compiler/LSP job của wave cũ chạy ngầm, không có build chồng lấn vô chủ, và live semantic proof không cần làm cả workspace nóng lên chỉ để tìm symbol trong một file.
