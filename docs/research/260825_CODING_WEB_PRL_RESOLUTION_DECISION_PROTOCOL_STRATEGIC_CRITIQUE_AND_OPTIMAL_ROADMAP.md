# Tools-Codex-web: hoàn thiện PRL, đo chất lượng quyết định và thử nghiệm Resolution Decision Protocol

**Strategic critique, authority-safe design và optimal roadmap**

Ngày lập báo cáo gốc: 2026-08-25
Ngày cập nhật chiến lược: 2026-08-25
Phạm vi triển khai: repository Tools-Codex-web
Phạm vi học thuật: các nguồn bên ngoài chỉ làm căn cứ giới hạn cho thiết kế đánh giá; cohort, dữ liệu, implementation và mọi kết luận vận hành đều chỉ thuộc Tools-Codex-web
Trạng thái tài liệu: **master roadmap / research protocol; chưa phải implementation receipt**

---

## 0. Delta cập nhật và quy tắc đọc tài liệu

Bản cập nhật này giữ lại toàn bộ quyết định đúng của bản trước nhưng sửa năm điểm chiến lược:

1. PRL v11 và RDP không được coi là “sản phẩm trí tuệ cuối cùng”; chúng là **scientific instrument + experimental apparatus** để đo problem-level outcome và decision-state continuity.
2. Giả thuyết trung tâm được nâng từ “RDP có giảm rework không?” thành một câu hỏi có thể bác bỏ: **một phần đáng kể rework trong long-horizon coding agents có xuất phát từ decision-state discontinuity và failure to incorporate counterevidence, thay vì implementation incapability đơn thuần hay không?**
3. P4 hiện có được dùng như **initial-decision observation**, RDP-Shadow dùng như **post-failure decision-update observation**. Không tạo thêm first-attempt decision subsystem.
4. C5 vẫn chỉ là shadow/measurement. **C6 bắt buộc là một behavior-changing intervention cụ thể**, không được gọi RDP-Shadow là treatment causal.
5. User confirmation time không mặc nhiên được gọi là exact resolution time. Với problem đã technical-full-pass trước khi user xác nhận, true resolution time có thể chỉ biết nằm trong một khoảng; reporter phải tách technical full-pass, observed confirmation và interval-censored resolution.

### 0.1 Current workspace identity và baseline snapshot identity là hai bằng chứng khác nhau

Current workspace được quan sát trong lượt cập nhật tài liệu này:

| Thuộc tính | Giá trị |
|---|---|
| Workspace | `E:\Github\Tools-Codex-web` |
| Branch | `main` |
| Current HEAD quan sát | `d254ac067fac87fa9a7a1861620f8af701112fca` |
| Upstream | `origin/main` |
| Source-code dirty | Không thấy file source-code nào bị sửa; đây là delivery documentation-only |
| Git worktree dirty | Có: `.coding-tools/orchestration/ledger.sqlite3` runtime drift và chính báo cáo này |
| Runtime version | Không claim runtime-loaded version trong báo cáo này |
| Public tool count | 8 theo source/maintained contract; không suy ra connector live chỉ từ số đó |

Bản immutable evidence receipt ở Mục 4 vẫn được pin tại:

`d8dd423b79316d0475e770085d534075ad51ec0f`

Do đó các con số `923 RUN`, `1.430 WAVE`, `656 failure_observed` và PRL v10 population trong báo cáo là **historical immutable snapshot evidence**, không được diễn giải như live/current counts tại `d254ac0...`.

Trước implementation Gate 0/C1, phải có một **S0 current-source delta reconciliation** rất hẹp trên các PRL/EOCL/P4/handoff surfaces liên quan. S0 không phải workstream nghiên cứu mới; nó chỉ trả lời liệu các source assumptions của snapshot `d8dd423...` còn đúng ở current HEAD hay đã bị code mới thay đổi.

### 0.2 Corpus tư vấn đã chuẩn hóa

Năm attachment mới có đúng **ba nội dung duy nhất**. Hai nhóm đầu là byte-for-byte duplicate, nên chỉ được tính một lần trong claim matrix; không nhân đôi trọng số tư vấn.

| Nhóm | Attachment | SHA-256 | Size / dòng | Vai trò đã dùng |
|---|---|---|---:|---|
| A | `2be72e6d…`, `f51a242e…` | `e5115329598a46a8e55c5a9e9164f6bc519363ca38a67bfbcfc1e1744ae9f284` | 22.498 B / 667 | PRL revision-safe closure |
| B | `b8336f78…`, `0a3b893b…` | `08a6b5760e0ede301b47a2f7832bf47a4fc9afc0d9c8fa7b7f9881bd5783` | 16.885 B / 746 | phản biện history → policy / Resolution Compiler |
| C | `16c61b82…` | `9c9a3c876cf4682a1a45cbdddadebfdae7c050fa148af3713ef63e5731121cc7` | 14.964 B / 618 | protocol mỏng, chống over-build |

Tài liệu tư vấn trước đó (`b24be826…`, SHA-256 `02e08e0744c8ca25aca2c46a6c59724616f4ec43bc253c90ea7ec60c564a1ff6`, 23.492 B / 692 dòng) chỉ là context lịch sử; nó không phải tài liệu thứ tư trong đánh giá này.

---

# 1. Kết luận điều hành

Hướng tối ưu là:

> **Hoàn thiện PRL thành measurement/authority foundation đúng semantics, dùng primitives hiện có để đo chuỗi quyết định của một problem revision, sau đó thử một continuity intervention nhỏ có đối chứng. Không xây Resolution Compiler như brain, planner, policy engine, memory platform hoặc subsystem mới.**

Điểm quan trọng hơn cả architecture là **research thesis**:

> **Long-horizon software-agent failure có khả năng là một sequential decision problem dưới partial observability và evolving intent, không chỉ là implementation-capability problem. Một phần rework có thể đến từ mất problem state, không carry forward counterevidence, chọn sai bước tiếp theo, oracle yếu hoặc reinterpret requirement sau restart/handoff.**

Đây là **hypothesis**, không phải kết luận đã chứng minh.

Bằng chứng hiện có cho phép:

- sửa deterministic mechanics và hard invariants;
- phát hiện loop/failure candidates;
- thu hẹp hypothesis space;
- thiết kế prospective cohort và causal intervention.

Bằng chứng hiện có **không cho phép**:

- suy causal resolution policy từ historical telemetry;
- gọi process-mined path là optimal strategy;
- tự động promote playbook/routing;
- tuyên bố RDP sẽ giảm rework trước controlled evidence.

Roadmap chính thức:

~~~text
S0 current-source delta reconciliation
    ↓
Gate 0 connector truth
    ↓
C1a authority correctness
    ↓
C1b immutable revision + problem identity mechanics
    ↓
C1c outcome/timestamp/reporter correctness
    ↓
C2 exact capture / work-origin / pinned binding
    ↓
C3 conditional EOCL → problem-outcome bridge
    ↓
C4 Tools-only natural canary + schema/codebook freeze
    ↓
C5 Decision Observation Cohort
   P4 initial-decision prior
   + RDP-Shadow post-failure update
    ↓
C6 one preregistered continuity intervention
    ↓
PROMOTE / REJECT / RETIRE
    ↓
Tools-only stopping point; no external replication in this roadmap
~~~

Trước C4 chỉ được claim mechanics/instrument validity.
Một natural problem qua restart/handoff/reopen chỉ chứng minh adaptive integration.
C5 chỉ chứng minh observability/reliability/burden.
Chỉ C6 mới có quyền tạo internal efficacy claim.
Mọi khẳng định vượt Tools-Codex-web đều ngoài phạm vi báo cáo này.

---

# 2. Quyết định chiến lược: chấp nhận, sửa, bác bỏ và hold

| Đề xuất | Quyết định | Lý do |
|---|---|---|
| PRL closure là nền bắt buộc | **Chấp nhận** | Thiếu identity/contract/outcome boundary thì mọi problem-level metric không đáng tin |
| Problem Revision là object bất biến | **Chấp nhận** | `thread.current_revision` không đủ làm historical authority |
| Reopen tự tạo revision mới | **Bác bỏ** | Same-requirement failure phải giữ nguyên revision |
| Accepted RUN tự provisional-resolve problem | **Bác bỏ** | Technical attempt có thể chỉ là progress hoặc không phủ acceptance contract |
| `resolution_claim` V1 chỉ `none/full_problem` | **Chấp nhận** | Giảm representation overlap; action semantics đo ở decision plane |
| Durable semantic contract capsule | **Chấp nhận có privacy gate** | Hash-only không khôi phục semantics qua restart/compaction |
| Resolution Compiler là authoritative brain | **Bác bỏ** | Tạo authority song song và solution-first bias |
| RDP mỏng | **Chấp nhận ở shadow** | Đo decision continuity mà không tạo planner mới |
| P4 = initial decision observation | **Chấp nhận** | Primitive đã có; tránh tạo instrument mới cho attempt đầu |
| RDP = post-failure decision update | **Chấp nhận** | Phù hợp WAVE/replan boundary hiện tại |
| Numeric Expected Information Gain | **Bác bỏ** | Không có calibrated belief model |
| Ordinal “information gain score” làm gate | **Bác bỏ ở V1** | Dễ gaming, semantic khó machine-verify |
| Runtime-verified `observed_delta_refs` | **Chấp nhận** | Chứng minh có new observation mà không giả causal meaning |
| Hai lần patch rồi bắt đổi strategy | **Bác bỏ** | Hard N không phân biệt causal failure với capacity/flaky proof |
| History → production policy ngay | **Bác bỏ** | Observational telemetry có confounding và selection bias |
| History → hypothesis/candidate playbook | **Chấp nhận** | Hợp lệ cho discovery/offline mining |
| Process mining | **Giữ ở discovery plane** | Path frequency không phải causal effect |
| Vector DB/autonomous retrieval injection | **Hold** | Chưa có applicability/negative-transfer ground truth |
| Learned router / auto model policy | **Hold** | Chưa có problem-level outcome transfer evidence |
| Multi-agent manager / DB thứ hai / tool thứ chín | **Bác bỏ** | Không giải current scientific bottleneck |
| RDP-Shadow là treatment | **Bác bỏ** | Shadow không đổi behavior nên không có treatment contrast |
| C6 continuity gate nhỏ | **Chấp nhận nếu C5 valid** | Có thể tạo causal contrast mà vẫn deterministic/fail-closed |
| HR là Tools V1 completion gate | **Bác bỏ** | Scope hiện khóa Tools-only |
| HR/benchmark là replication trong roadmap này | **Bác bỏ / ngoài phạm vi** | Scope khóa Tools-Codex-web; cần proposal và authority mới nếu sau này mở rộng |

---

# 3. Câu hỏi học thuật thật sự của chương trình

## 3.1 Scientific thesis

Luận đề trung tâm cần kiểm nghiệm:

> **A material share of long-horizon coding-agent rework is caused by decision-state discontinuity and failure to incorporate counterevidence, rather than implementation incapability alone.**

Tiếng Việt:

> **Một phần đáng kể rework của coding agent dài hạn có thể bắt nguồn từ việc không duy trì đúng trạng thái quyết định — mất problem contract, không carry previous outcome, không cập nhật theo counterevidence, hoặc đổi/giữ strategy sai thời điểm — chứ không chỉ vì model không biết viết code.**

Luận đề này phải cho phép bị bác bỏ. Nếu C6 cho thấy continuity intervention không làm giảm rework sau khi quality/burden được kiểm soát, hypothesis phải bị hạ hoặc bác bỏ; không được mở thêm framework để “cứu” hypothesis.

## 3.2 Research questions

### RQ1 — Failure decomposition

Bao nhiêu rework/reopen có thể quy về:

- implementation defect;
- wrong target/workspace/source state;
- weak/mismatched oracle;
- problem/requirement continuity loss;
- failure to incorporate counterevidence;
- transient environment/capacity;
- legitimate requirement evolution;
- unknown.

RQ1 là descriptive/mechanism-discovery question; historical logs có thể hỗ trợ candidate taxonomy nhưng không được causal-backfill semantic truth.

### RQ2 — Goal continuity

Immutable problem revision + exact attempt binding có giảm:

- wrong-target correction;
- requirement-loss correction;
- historical reinterpretation;
- false closure;

so với legacy behavior hay không?

Phần mechanics của RQ2 có deterministic proof; effect lên user outcome cần prospective evidence.

### RQ3 — Decision adaptation after counterevidence

Khi một attempt technical-accepted nhưng problem bị authoritative reopen, lần quyết định tiếp theo có thực sự:

- carry previous outcome/proof;
- dùng fresh observation;
- thay đổi causal framing/oracle/scope/action khi cần;
- tránh exact ineffective mutation replay;

hay không?

### RQ4 — Continuity intervention efficacy

Một bounded gate chỉ yêu cầu carry previous exact outcome + fresh observed delta và chặn exact failed mutation replay có giảm rework/low-information replacement waves mà không làm giảm quality hoặc tăng burden/TTPR quá ngưỡng không?

Đây là câu hỏi causal chính của C6.

### RQ5 — Experience reuse

Target-bound experience/playbook có giúp decision quality hơn no-history/raw-history trong SWE hay gây negative transfer?

RQ5 **không nằm trong C0–C6**. Chỉ mở sau khi có trusted prospective problem-outcome data và C6 đã terminal.

## 3.3 Falsification criteria

Chương trình phải cho phép các kết luận sau:

- `H_CONTINUITY_SUPPORTED`: continuity intervention giảm primary rework outcome và không vi phạm floors.
- `H_CONTINUITY_REJECTED`: không có material improvement hoặc có harm/burden lớn hơn benefit.
- `H_INCONCLUSIVE`: instrumentation/denominator/power chưa đủ; không được đổi taxonomy giữa cohort chỉ để tìm effect.
- `MECHANISM_SHIFT`: dữ liệu cho thấy implementation/oracle/model capability mới là dominant bottleneck; roadmap phải chuyển theo evidence.

---

# 4. Immutable baseline evidence receipt ngày 2026-08-25

## 4.1 Current-source reconciliation snapshot (`d254ac0…`)

Đây là snapshot mới phục vụ delivery tài liệu này, tách biệt với baseline lịch sử bên dưới. Nó dùng read-only connection, `PRAGMA query_only=ON`, explicit read transaction và SQLite Backup API vào `TemporaryDirectory` ngoài repository; sau đó chỉ query copy với `immutable=1`. Không khởi tạo writer, migration, runtime, schema change hay direct SQL mutation.

| Thuộc tính | Giá trị |
|---|---|
| Git HEAD tại capture | `d254ac067fac87fa9a7a1861620f8af701112fca` |
| Capture UTC / Asia-Saigon | `2026-08-24T19:51:50.137Z` / `2026-08-25T02:51:50.137+07:00` |
| Hoàn tất UTC | `2026-08-24T19:51:50.756Z` |
| SHA-256 của Backup-API copy | `6568d95ae3c85c85a3b6023e00d8240dd593a1cde6a81196be2b3122093ab83e` |
| Size snapshot | 64.696.320 byte |
| SQLite user_version | 10 |
| `integrity_check` / `foreign_key_check` | `ok` / 0 violation |
| Writer/runtime instantiated | không |

Filters và queries của current snapshot: toàn bộ row của `runs`, `checkpoints`, `waves`, `events`, `problem_threads`, `problem_events`; **không** time window, accepted-only population filter hay deduplication. Ngoại lệ duy nhất là cross-check `failure_observed` join RUN có current `status='accepted'`. Các aggregation dùng `GROUP BY status` và các điều kiện exact sau:

~~~sql
events.event_type = 'wave_replanned' | 'failure_observed'
problem_events.link_status = 'EXACT'
  AND link_role = 'PRIMARY'
  AND relation_type IN ('LINK', 'ENGINEERING_ATTEMPT_BOUND')
  AND run_id <> ''
~~~

| Current snapshot population | Count |
|---|---:|
| RUN total; accepted / aborted / stale / completed / active / failed | 923; 505 / 317 / 83 / 12 / 5 / 1 |
| Checkpoint total / accepted | 508 / 508 |
| WAVE total; accepted / replanned / aborted / completed / active | 1.430; 505 / 511 / 402 / 7 / 5 |
| `wave_replanned` / `failure_observed` / accepted-RUN `failure_observed` | 513 / 656 / 436 |
| `problem_threads` / `problem_events` | 0 / 1 |
| `ENGINEERING_ATTEMPT_BOUND`, `UNLINKED`, policy-ineligible | 1 / 1 / 1 |
| Exact primary RUN binding | 0 |

**Censoring/missingness:** không có `problem_thread`, vì vậy PRL risk set, terminal outcome, confirmation, TTPR và right-censored unresolved-thread population đều **not estimable** (`n=0`), không phải 0 successful resolution. `RESOLVED_UNCONFIRMED`, `SUPERSEDED`, `ABANDONED`, silence hoặc cross-clock event không được count as success trong mọi reporter v11 đề xuất.

## 4.2 Historical baseline snapshot identity (`d8dd423…`)

Bảng này là **historical immutable receipt**, không phải live current-source claim.

| Thuộc tính | Giá trị |
|---|---|
| Git HEAD của snapshot | `d8dd423b79316d0475e770085d534075ad51ec0f` |
| Capture UTC | `2026-08-24T19:05:01.249Z` |
| Capture Asia/Saigon | `2026-08-25T02:05:01.249+07:00` |
| Hoàn tất UTC | `2026-08-24T19:05:02.859Z` |
| Snapshot SHA-256 | `25e513468b68e2593c25b4a9afbfdd6efddc991f1e82f9c53ec96c465784f468` |
| Snapshot size | 64.696.320 byte |
| SQLite user_version | 10 |
| Read mode | query_only, immutable Backup-API copy |
| integrity_check | ok |
| foreign_key_check | 0 violation |
| Canonical writer/runtime/governor instantiated trong capture | không |

Snapshot implementation mở source read-only, bắt đầu explicit read transaction, dùng SQLite backup và chỉ đọc bản sao; baseline anchors từng được kiểm tại `ledger_analysis.py` và `lifecycle_census.py`. Vì current HEAD đã khác, line anchors cũ phải được revalidate ở S0 trước implementation.

Một lifecycle capture độc lập lúc `2026-08-24T19:05:47.506Z` tạo lại đúng physical snapshot SHA-256 ở trên và báo logical SHA-256 `ce5805d9776647b3659817a980ac29fd9560b3dba06777a1bb1cd9241da7eec2`. Đây là companion consistency receipt trên một Backup-API copy khác.

## 4.3 Historical population và filters

Không có time-window, accepted-only filter hoặc deduplication, trừ subset failure trong accepted RUN được ghi rõ.

| Population | Count |
|---|---:|
| RUN tổng | 923 |
| RUN accepted / aborted / stale | 505 / 317 / 83 |
| RUN completed / active / failed | 12 / 5 / 1 |
| Checkpoint tổng / accepted | 508 / 508 |
| WAVE tổng | 1.430 |
| WAVE accepted / replanned / aborted | 505 / 511 / 402 |
| WAVE completed / active | 7 / 5 |
| `wave_replanned` events | 513 |
| `failure_observed` events | 656 |
| `failure_observed` trong RUN hiện accepted | 436 |

Các số là row counts, không giả định 1:1 giữa RUN/checkpoint/WAVE/event.

## 4.4 PRL v10 tại historical snapshot

| Population | Count |
|---|---:|
| problem_threads | 0 |
| problem_events | 1 |
| ENGINEERING_ATTEMPT_BOUND | 1 |
| UNLINKED | 1 |
| policy-eligible / ineligible | 0 / 1 |
| exact primary RUN binding | 0 |

Event duy nhất có caller field `event_time=2026-08-24T03:32:15.969Z`. Không có problem-thread state, confirmed outcome, TTPR hoặc correction denominator.

PRL-D companion report là `DESCRIPTIVE_ONLY`: exact/ambiguous/unlinked = `0/0/1`, observed terminal threads = `0`, TTPR/restricted-TTPR = `null`. `right_censored_threads=0` vì không có thread nào trong risk set, không phải vì problem đã được giải quyết.

## 4.5 Diễn giải đúng

- 923 RUN **không phải** 923 problems.
- 505 accepted RUN **không phải** 505 resolutions.
- 656 failure events **không phải** 656 causal failures độc lập.
- Một UNLINKED PRL event **không chứng minh** capture rate bằng 0 trên một denominator đã định nghĩa; nó chứng minh natural PRL denominator chưa tồn tại.

Historical ledger đủ để tìm mechanics defect, process motifs và candidate hypotheses. Nó chưa đủ để biến history thành causal policy.

---

# 5. Source-truth baseline và S0 current-source reconciliation

## 5.1 Baseline source gaps đã được xác minh ở snapshot `d8dd423...`

| Gap baseline | Sự thật mạnh nhất tại snapshot | Priority |
|---|---|---|
| Caller khai provenance/eligibility | `eligible_for_policy` là public input; provenance/evidence có caller-controlled enums | P0-A |
| Shadow feedback có thể mutate state | state derivation không chặn shadow provenance / false eligibility | P0-A |
| HOST_OBSERVED chỉ bind identity | pending turn/trace được kiểm, semantic label không được host attest | P0-A |
| Caller time đi vào TTPR | event hash giữ timestamp đã ghi nhưng không chứng minh clock authority | P0-A |
| Revision chỉ ở thread | không có immutable `problem_revisions` authority | P0-A |
| Reopen tự tăng revision | same-requirement failure có thể thành false contract revision | P0-A |
| Handoff đọc current revision | attempt cũ có thể bị reinterpret theo revision mới | P0-A |
| Disposition bị tính như resolution | unconfirmed/superseded/abandoned có nguy cơ đi vào closure semantics sai | P0-A |
| Criteria chưa map vào exact proof | proof/contract identity có nhưng criterion-level structural coverage chưa có | P0-B |
| Replan reason là free text | WAVE boundary có nhưng chưa có observed decision delta | P1 |
| P4/handoff primitives đã có | có bounded capsule, allowlist/idempotency/pre-write pattern/proof refs | REUSE |

### Source anchors và Claim matrix (rechecked at `d254ac0…`)

Các anchors dưới đây là source/test evidence cho **gap hoặc primitive**, không phải claim rằng runtime/package hiện đang chạy bytes đó.

| Claim | Loại bằng chứng / source anchor | Kết luận được phép |
|---|---|---|
| PRL hiện vẫn schema v10 | `problem_lineage.py:19`, migration `:307–380`; focused fixtures `tests/test_problem_lineage.py:35–51` | V11 chưa source-present; v9/v10→v11 là work C1 |
| Caller có thể đưa provenance, eligibility, state và event time | normalize allowlist `problem_lineage.py:172–249`; hash v1 `:285–293`; persisted event `:464–466` | Authority/timestamp/eligibility phải chuyển vào runtime ở V11 |
| Feedback/reopen/resolution hiện có thể chọn state từ input | `problem_lineage.py:218–224`, canonical mutation `:427–474` | V11 phải tách observation khỏi explicit authorized transition |
| Reopen đang nâng revision; handoff đọc `current_revision` | `problem_lineage.py:444`, `:542–557` | Same-problem reopen và historical handoff cần revision object bất biến |
| HOST_OBSERVED chỉ verify identity | `problem_lineage_control.py:39–44` | Turn/trace exactness không chứng minh semantic label đúng |
| Existing exact-link primitive không bịa problem lineage | `workflow_tools.py:55–105` | C2 có thể reuse auto-binding/missingness primitive, nhưng phải pin revision trước durable RUN write |
| Handoff field reserved và runtime-derived | `coordination.py:1139–1162` | RDP dùng projection/handoff hiện có, caller không được spoof authority fields |
| EOCL acceptance có proof/checkpoint primitives nhưng chưa criterion attribution | `coordination.py:1287–1368` | C3 bổ sung bridge/manifest thay vì dựng acceptance subsystem mới |
| Read-only snapshot path tồn tại | `ledger_analysis.py:318–378`; PRL-D script | Snapshot trong Mục 4 là reproducible evidence receipt, không writer/migration proof |
| Current product/source policy | `docs/CURRENT_STATE.md:1–35, 80–115` | Chỉ tám public smart-v3 tools; `auto` vẫn fail-closed deterministic |

| Khẳng định quan trọng | Phân loại | Quyết định / giới hạn |
|---|---|---|
| Không có problem-level outcome denominator hiện tại | observed — current immutable snapshot | Chỉ làm mechanics/capture, không suy efficacy/routing/playbook |
| v10 có authority, revision, clock và disposition gaps | observed — current source | C1 V11 là P0 bắt buộc trước policy/natural efficacy claim |
| `problem_revisions` + capsule + criterion attribution sẽ giảm reopen | proposal/hypothesis | Có deterministic mechanics proof; effect chỉ đo sau C4/C6 |
| RDP-Shadow làm giảm rework | hypothesis | C5 chỉ observe; không hard-block hay claim causal effect |
| Resolution Compiler/history thành policy | rejected design at current evidence | Không có outcome/causal/applicability proof; giữ candidate playbook offline |

## 5.2 P0-A và P0-B phải tách

### P0-A — Scientific integrity / valid lineage

Phải sửa trước natural cohort:

- shadow/unknown không mutate canonical state;
- caller không self-qualify policy eligibility;
- trusted timestamp semantics;
- immutable revision identity;
- reopen/revise correctness;
- pinned historical handoff;
- resolution ≠ administrative disposition.

### P0-B — Trusted-resolution rigor

Cần trước claim `trusted_resolution`:

- `work_origin`;
- immutable `resolution_claim`;
- criterion-to-proof structural manifest;
- engineering floor;
- conditional EOCL outcome bridge.

Tách hai nhóm này để không biến C1 thành một “siêu tranche” ngăn hệ thống bắt đầu thu valid lineage unnecessarily lâu.

## 5.3 S0 current-source delta reconciliation

Vì current HEAD đã là `d254ac0...`, trước code change phải kiểm đúng các surfaces:

- `problem_lineage.py`;
- `problem_lineage_control.py`;
- `problem_resolution_economics.py`;
- `tool_schema.py`;
- `coordination.py` / orchestration control/ledger;
- P4 solution recommendation surfaces;
- handoff capsule projection;
- tests liên quan PRL/proof/replan/handoff.

S0 exit:

- `UNCHANGED_ASSUMPTIONS`: baseline gap matrix còn đúng → tiếp Gate 0/C1;
- `PARTIALLY_FIXED`: current source đã sửa một số gap → roadmap tự thu hẹp, không reimplement;
- `SEMANTIC_DRIFT`: current source thay semantics materially → cập nhật authority/measurement spec trước write.

S0 không tạo roadmap mới và không được reanalyze toàn dự án.

---

# 6. Authority model: ba lớp phải tách

1. **Identity provenance**: event gắn đúng turn/trace/RUN/WAVE/workspace/problem revision nào?
2. **Transition authority**: actor/operation có quyền đổi canonical problem state hay không?
3. **Policy eligibility**: observation có đủ quality/provenance để vào cohort/promotion analysis hay không?

Exact identity không tạo semantic truth.
Semantic authority không tạo technical proof.
Technical proof không tự tạo user outcome.
Policy eligibility không được caller tự cấp.

## 6.1 Transition-authority matrix V11

Trong V11, generic `observe_feedback` chỉ append observation; nó không mutate state. Adapter/runtime phải chuyển structured explicit-user feedback hoặc authorized human annotation thành explicit transition operation.

| Operation | Canonical effect | Allowed authority | Bắt buộc | Bị cấm |
|---|---|---|---|---|
| `open` | tạo thread + revision 1 ở OPEN | explicit user/controller hoặc reviewed annotation | exact workspace + sanitized capsule | shadow/inferred tự tạo policy-eligible thread |
| `observe_feedback` | không đổi state | mọi provenance được ghi rõ | exact receipt nếu claim host-observed | state mutation |
| `provisional_resolve` | revision → PROVISIONALLY_RESOLVED | deterministic EOCL bridge | `full_problem`, exact revision, complete structural coverage, engineering floor, accepted checkpoint | model/shadow feedback tự đóng |
| `confirm` | revision → RESOLVED_CONFIRMED | structured explicit-user feedback hoặc reviewed annotation | exact revision + authority receipt | silence/inference/HOST identity đơn độc |
| `reopen` | giữ revision, state → REOPENED | structured explicit-user feedback hoặc reviewed annotation | same-problem semantics + exact revision | tự tăng revision |
| `revise` | CAS current revision/fingerprint, tạo N+1 OPEN | explicit contract revision transaction | exact expected revision + new sanitized capsule | suy revision chỉ từ feedback label/fingerprint mismatch |
| `block` | state → BLOCKED | runtime deterministic guard hoặc authorized user/operator | typed reason + next evidence/action | generic free text |
| `abandon` | administrative disposition | explicit user/operator authority | typed reason/provenance | timeout/silence tự động |

`eligible_for_policy` phải là runtime-derived output từ binding, authority, timestamp, capsule validity, proof/coverage và cohort rules. Public caller input phải bị loại bỏ hoặc reject.

---

# 7. Timestamp authority và outcome-time semantics

## 7.1 Event clocks V11

| Field | Owner | Semantics | Dùng cho analysis |
|---|---|---|---|
| `event_seq` | SQLite writer transaction | total durable append order | ordering/tie-break only |
| `recorded_at` | runtime ledger writer | lúc durable append | ingest/audit latency; không thay event occurrence |
| `occurred_at` | optional trusted adapter | external event occurrence | wall-clock estimator nếu attested |
| `occurred_at_source` | runtime/adapter enum | clock source | bắt buộc nếu có occurred_at |
| `clock_authority` | runtime-derived | trust/domain | bắt buộc nếu có occurred_at |
| `legacy_event_time` | caller legacy projection | v10 compatibility only | không dùng policy/TTPR |

Hash-material v2 canonical-encode event schema version + clock fields; legacy v1 hash vẫn verify theo material cũ, migration không rewrite history.

Caller-supplied timestamp chưa được attest không được dùng cho policy eligibility, ordering hay bất kỳ TTPR estimator nào. `recorded_at` chỉ chứng minh ingest/order tại ledger, không thay thế real-world occurrence.

## 7.2 Không gọi confirmation timestamp là exact resolution time

Nếu technical full-pass/provisional xảy ra lúc `t_p` và explicit confirmation được quan sát lúc `t_c`, true real-world resolution có thể đã xảy ra bất kỳ lúc nào trong khoảng đó nếu không có contradictory event/mutation.

Do đó reporter phải tách:

1. **TTFP — Time To Technical Full Pass / valid provisional**;
2. **TTOC — Time To Observed Confirmation**;
3. **Resolution interval**: `[t_p, t_c]` khi assumptions cho phép;
4. **Administrative disposition time**: supersede/abandon/block, không phải success.

Nếu event occurrence chỉ biết nằm trong khoảng, đó là interval-censored outcome, không được ép thành exact event ở confirmation time. Đây là cùng lớp statistical issue với interval-censored time-to-event data: thời điểm thực nằm giữa lần cuối chưa quan sát event và lần đầu quan sát event.

## 7.3 Censoring và competing dispositions

- silence/unconfirmed: right-censored hoặc unknown tùy observation model;
- supersede/abandon: competing disposition, không success;
- user silence có thể informative, nên Kaplan–Meier chỉ là một descriptive view kèm sensitivity/competing-risk reporting;
- cross-clock/missing clock: UNKNOWN, không thay bằng 0;
- không tính population percentiles khi `n` nhỏ; báo exact values/CI phù hợp.

---

# 8. Immutable Problem Revision V11

V11 thêm `problem_revisions` trong **cùng canonical SQLite**:

~~~text
problem_threads
  problem_id PK
  current_revision
  compatibility projections

problem_revisions
  problem_id
  revision
  contract_fingerprint
  criteria_fingerprint
  typed_contract_capsule
  task_class
  engineering_floor
  created_event_seq
  created_at
  creation_authority
  PRIMARY KEY(problem_id, revision)

problem_events
  event_seq PK
  problem_id NULL
  problem_revision NULL
  ...
  FOREIGN KEY(problem_id, problem_revision)
    REFERENCES problem_revisions(problem_id, revision)
~~~

Rules:

- EXACT events: composite `(problem_id, revision)` bắt buộc;
- AMBIGUOUS/UNLINKED: cả hai NULL;
- CHECK constraint enforce pair semantics; không dùng sentinel revision 0;
- `problem_threads.current_revision` chỉ là projection/read optimization;
- authority thuộc revision row;
- reopen giữ revision;
- revise dùng CAS và tạo immutable revision mới;
- fingerprint là integrity/concurrency guard, không phải semantic oracle.

Migration v9/v10 → v11 additive:

- không semantic-backfill user intent/revision/criteria/trusted timestamp;
- legacy UNLINKED event giữ legacy/ineligible;
- old event hash không rewrite;
- rollback bằng disable new writers/readers, không delete/rewrite history.

---

# 9. Problem Identity Codebook — construct bắt buộc trước C4

Problem identity là construct khó nhất của program. Nếu split/merge không ổn định, mọi First Revision Resolution Rate có thể bị thay đổi chỉ bởi annotation choice.

Codebook dùng stable user-level intended outcome + acceptance contract + target/domain + causal continuity để phân loại.

| Label | Khi dùng | Không dùng khi |
|---|---|---|
| `SAME_PROBLEM` | outcome cũ vẫn là mục tiêu; symptom/evidence mới nhưng contract không đổi | user thêm/đổi acceptance outcome materially |
| `REVISION` | cùng thread nhưng contract/constraint/target outcome thay đổi có authority | chỉ vì attempt trước thất bại |
| `CHILD_DEPENDENCY` | problem mới phải giải để unblock parent nhưng có acceptance contract riêng | chỉ là một implementation step nội bộ không có user/product outcome riêng |
| `NEW_PROBLEM` | user-level intended outcome độc lập | symptom mới vẫn nằm trong original contract |
| `AMBIGUOUS` | evidence không đủ phân biệt | không ép SAME/NEW để làm metric đẹp |

### 9.1 Examples

- “Vẫn không lưu được dự án” sau một accepted attempt → `SAME_PROBLEM`, same revision nếu contract không đổi.
- “Lưu được rồi nhưng thêm Chủ đầu tư vào acceptance” → `REVISION` nếu đây là requirement extension của cùng user objective.
- “Dự án lưu được nhưng Finance sync bị lỗi” → có thể `SAME_PROBLEM`, `CHILD_DEPENDENCY` hoặc `NEW_PROBLEM` tùy acceptance contract ban đầu; codebook + review phải quyết định, không heuristic duy nhất.

### 9.2 Reliability

C4 phải independent-double-annotate một sample cho problem identity và báo:

- raw agreement;
- class prevalence;
- Cohen’s kappa hoặc Krippendorff’s alpha phù hợp;
- disagreement table;
- ambiguous rate.

Agreement cao không tự chứng minh construct validity, nhưng agreement thấp là bằng chứng taxonomy chưa đủ operational.

---

# 10. Semantic contract capsule và privacy threat model

Capsule V11 typed, immutable, canonical-encoded, tối đa 8 KiB, chỉ gồm:

1. sanitized `objective_summary`;
2. `acceptance_criteria[]` với stable criterion IDs;
3. `protected_invariants[]`;
4. `constraints[]`;
5. `unresolved_conditions[]`.

Không lưu raw prompt, transcript, command output, source content, stack dump đầy đủ, private chain-of-thought hoặc arbitrary JSON. Reuse canonical encoding, hashing và sanitization primitives hiện có; không dùng generic run-scoped handoff capsule làm contract authority.

Chỉ `problem_revisions` giữ authoritative capsule copy. Event/RUN/WAVE/handoff giữ opaque reference + fingerprint do runtime resolve.

Capsule missing/hash mismatch → `BLOCKED_MISSING_PROBLEM_CONTEXT`; fingerprint không khôi phục semantics.

Privacy threats cần fail closed trước durable write:

| Threat | Guard |
|---|---|
| secret/API key ingestion | deterministic secret scan + reject + remediation/rotation if already written |
| PII/customer data | detect + reject durable write; yêu cầu abstract/authorized opaque reference, không âm thầm retain |
| source/log exfiltration | strict allowlist/type/size validation |
| transcript/CoT retention | schema không có field; arbitrary keys rejected |
| encoded secret laundering | normalize/decode limits + entropy/pattern scan |
| revision amplification | content-addressed safe capsule/opaque ref; no raw duplication |
| handoff authority injection | runtime owns reserved projection; caller values stripped/rejected |

`.coding-tools` evidence có khả năng đi vào version control, vì vậy không được coi ledger là private scratchpad.

---

# 11. Capture, work origin, resolution claim và criterion-level proof

## 11.1 Work origin

| `work_origin` | Semantics | Binding | Denominator |
|---|---|---|---|
| `problem` | work nhằm giải exact problem revision | exact revision bắt buộc | problem capture/resolution analysis |
| `non_problem` | maintenance/release/read-only chores/other work | không fake lineage | loại khỏi problem denominator |
| `unknown` | legacy/shadow chưa phân loại | ineligible | missingness riêng |

C2 shadow-capture trước; sau canary/review mới bắt buộc cho write-capable RUN.

## 11.2 Resolution claim

V1 chỉ:

- `none`
- `full_problem`

Claim phải pin trước first mutation và bất biến trong WAVE. Nâng `none → full_problem` tạo WAVE mới để tránh post-hoc denominator selection.

Action semantics như diagnose/localize/intervene được đo ở decision plane, không nhét vào resolution taxonomy.

## 11.3 Criterion-to-proof manifest

`full_problem` acceptance nộp bounded manifest:

~~~text
criterion_id -> [passed_proof_id, ...]
~~~

Runtime verify:

- exact complete criterion set;
- no duplicate/extra/missing criterion;
- proof PASS, same RUN/WAVE/revision/contract;
- proof pre-dates acceptance và chưa invalidated;
- exact accepted checkpoint;
- thread still points expected revision/fingerprint.

Manifest chỉ chứng minh **structural completeness + provenance**, không tự chứng minh oracle semantic adequacy. Reopen/correction outcome phải là guard chống “coverage hình thức”.

## 11.4 Engineering floor

| Floor | Gate |
|---|---|
| `REQUIRED` | accepted checkpoint + complete valid criterion/proof attribution |
| `NOT_APPLICABLE` | authorized non-code path + complete criterion disposition |
| `UNKNOWN` | không policy-eligible provisional closure |

User confirmation và engineering trust là hai axes độc lập. Confirmation không accept RUN, không tạo proof và không override failed technical floor.

---

# 12. Conditional EOCL → problem outcome bridge

EOCL vẫn là độc quyền execution/proof/technical acceptance authority.

~~~text
EOCL CHECKPOINTED
      ↓
if work_origin=problem
   + resolution_claim=full_problem
   + exact revision/contract
   + complete criterion/proof manifest
   + engineering floor satisfied
      ↓
idempotent PROVISIONALLY_RESOLVED event
      ↓
explicit user/human outcome
  confirm / reopen / revise / block
~~~

Nếu EOCL checkpoint thành công nhưng append PRL bridge event crash, không được unaccept RUN. Recovery phải reconcile missing bridge event bằng deterministic/idempotent identity trên exact accepted checkpoint + revision + claim + manifest.

Changed-bytes reuse phải conflict; same-ID/same-bytes phải idempotent.

---

# 13. Decision observation architecture: P4 + RDP, không tạo compiler

## 13.1 Tại sao phải đo attempt đầu lẫn post-failure update

Nếu chỉ enroll RDP ở attempt 2+, dataset conditioned on prior failure. Nó học recovery decision nhưng không phân biệt:

- bad initial framing;
- weak first oracle;
- premature intervention;
- good initial decision nhưng implementation defect;
- good first decision + poor adaptation after counterevidence.

Không tạo subsystem mới. Reuse primitives:

~~~text
Problem Revision
   ↓
P4 Shadow = initial-decision prior
   ↓
Attempt 1
   ↓
Outcome / proof / user feedback
   ↓
RDP-Shadow = post-failure decision update
   ↓
Attempt 2+
   ↓
Outcome
~~~

P4 không được promote thành router. RDP không được trở thành brain. Cả hai là measurement plane cho decision trajectory.

## 13.2 Decision trajectory dataset

Không lưu chain-of-thought. Chỉ structured fields:

- `decision_id`;
- exact `problem_id/revision`;
- exact WAVE/source identity;
- initial P4 recommendation ref nếu có;
- `action_kind`;
- hypothesis/oracle/scope/strategy fingerprints;
- observed evidence refs;
- previous outcome/proof refs;
- whether decision materially changed after counterevidence;
- next proof/outcome;
- reopen/correction/disposition.

Dataset mục tiêu:

> **Decision → Evidence → Update → Outcome**

không phải transcript → reconstructed reasoning.

---

# 14. RDP-Shadow: continuity contract, không phải compiler

RDP thuộc existing WAVE/replan event plane. Không DB/tool/state machine mới.

Enrollment C5:

- second or later write-capable attempt;
- same exact problem revision;
- problem/full-resolution work;
- read-only/simple/non-problem work không bị ép card.

Record tối thiểu:

- `exact_previous_wave_id`;
- `action_kind`: `clarify|diagnose|localize|intervene|verify`;
- runtime-verified `observed_delta_refs`;
- `delta_kind`: USER_EVIDENCE, TECHNICAL_EVIDENCE, HYPOTHESIS, ORACLE, SCOPE, CONTRACT, TRANSIENT_ENVIRONMENT, AUTHORITY;
- strategy/hypothesis/oracle/scope fingerprints;
- discriminator/oracle ref;
- P4 recommendation ref nếu có;
- immutable resolution claim ref;
- stop condition code;
- bounded `semantic_delta_claim` của Sol, advisory only.

Runtime owns predecessor/problem/revision/workspace/base/worktree/tool-contract identity.

### 14.1 Safe no-repeat semantics trong C5

C5 **không hard-block semantic repeats**.

Theo dõi:

- causal/mutation failure: replacement write cần material decision delta;
- same strategy + no fresh observed ref;
- exact same mutation request after causal failure;
- capacity/timeout/flaky proof: bounded retry chỉ khi có fresh transient observation;
- operator-authorized repeat với authority receipt riêng;
- idempotent replay/Job continuation: không thuộc semantic retry gate;
- unsafe ambiguous replay: không tự replay.

Không dùng numeric/ordinal EIG làm gate. Nếu không còn discriminator, oracle hoặc authority hợp lệ, runtime phải ghi `BLOCKED` với typed reason và exact next evidence/action required. Hard-reject exact duplicate mutation chỉ là candidate C6 sau khi C5 chứng minh false-block rate nằm trong preregistered bound.

### 14.2 Carry-forward

Qua restart/compaction/handoff phải giữ:

- exact revision/capsule ref;
- previous decision/WAVE;
- passed/failed proof refs + invalidation;
- authoritative reopen/correction;
- latest stop condition;
- unresolved evidence gap dạng typed/ref fields.

Historical attempt không bao giờ đọc `thread.current_revision` để reinterpret lineage.

---

# 15. Candidate causal intervention C6: `RDP_CONTINUITY_GATE_V1`

## 15.1 C5 shadow không phải treatment

Một shadow record không thay hành vi. Vì vậy:

~~~text
RDP-Shadow ≠ causal treatment
~~~

C5 chỉ đo:

- coverage;
- label reliability;
- overhead;
- false delta/gaming;
- decision-update patterns;
- candidate intervention eligibility.

## 15.2 Treatment đầu tiên phải nhỏ và deterministic

Không test semantic “information gain” đầu tiên.

Candidate treatment:

> **Trước replacement write-capable WAVE của cùng problem revision sau causal/mutation failure hoặc authoritative reopen, runtime yêu cầu exact previous outcome/proof refs và ít nhất một fresh runtime-verifiable observed delta hoặc explicit authorized exception. Exact failed mutation request không được replay nếu không thuộc idempotent/transient/authority exception.**

Tên working protocol:

`RDP_CONTINUITY_GATE_V1`

Nó không quyết định model, strategy hay hypothesis. Nó chỉ enforce **continuity of evidence and failure state**.

### 15.3 Control và treatment

**Control:** PRL v11 + EOCL bình thường, RDP instrumentation/shadow nhưng không continuity enforcement.

**Treatment:** cùng stack + `RDP_CONTINUITY_GATE_V1` với preregistered exception set.

Không dùng historical accepted-only tail làm control effect estimate.

### 15.4 Tại sao intervention này có giá trị học thuật

Nếu gate nhỏ, deterministic này giảm rework mà không giảm quality:

> một phần failure không cần model “thông minh hơn”; nó đến từ failure-state discontinuity / không incorporate counterevidence vào next mutation.

Nếu không có effect:

> hypothesis continuity phải bị hạ; tìm bottleneck khác thay vì mở rộng gate semantic.

---

# 16. Action-kind taxonomy và reliability

`clarify|diagnose|localize|intervene|verify` không mặc nhiên mutually exclusive về semantics. Một SQL query có thể vừa diagnose vừa localize.

V1 cần codebook với **primary action intent**:

| Action | Primary intent |
|---|---|
| `clarify` | acquire missing user/contract information |
| `diagnose` | discriminate causal hypotheses |
| `localize` | narrow target/scope without yet changing target behavior |
| `intervene` | change system behavior/state to address causal mechanism |
| `verify` | test whether acceptance/oracle is satisfied |

Nếu một operation có nhiều chức năng, annotation chọn primary decision intent và có optional secondary tag ở offline analysis; runtime schema không cần taxonomy phình to.

C5 reliability study phải thêm `action_kind` vào independent double annotation. Nếu agreement thấp, không dùng action-kind effect estimate cho causal claim.

---

# 17. Goodhart và gaming register

| Gaming vector | Cách game | Guard | Metric |
|---|---|---|---|
| Strategy rename | đổi tên nhưng same mutation footprint | fingerprint/ref comparison | duplicate-mutation review |
| Hypothesis paraphrase | đổi câu chữ không new discriminator | only observed refs count | no-evidence replan rate |
| Useless probe | tạo evidence vô nghĩa | observation quality sampling | probe burden / false gain |
| False problem split | mở thread mới tránh reopen | identity codebook + review | false-split rate |
| False revision | revise để reset attempts | CAS + explicit authority + review | revision-reversal rate |
| False merge | gắn problem khác vào old thread | explicit SAME/REVISION/NEW/AMBIGUOUS review | false-merge rate |
| No-claim avoidance | luôn `none` | no-claim coverage audit | no-claim rate |
| Work-origin laundering | fix thật khai non_problem | shadow classifier/review | origin override |
| Clarification abuse | hỏi lại để né decision | burden guardrail | clarification turns/problem |
| Abandonment abuse | abandon để làm TTPR đẹp | competing disposition | abandonment rate |
| Timestamp laundering | caller backdate | attested clocks only | unattested-time rate |
| Provenance laundering | caller chọn HOST/USER | runtime-derived authority | rejected attestation rate |

Schema/codebook freeze ở C4: semantic change tăng version/cohort; chỉ privacy/integrity/measurement defect mới hotfix trong cohort.

---

# 18. History và playbook governance

| Authority tier | Nguồn | Online effect | Promotion | Demotion |
|---|---|---|---|---|
| Hard invariant | deterministic product/safety contract | enforce | code review + deterministic proof | contract revision |
| Candidate mechanism/playbook | historical process motif | advisory/offline | preregister prospective hypothesis | any material counterevidence |
| Confirmed playbook | trusted prospective applicability cases | bounded advisory first | applicability + rebinding + invalidation + verification + negative history | reopen/negative transfer/drift/kill switch |

Historical telemetry dùng cho:

~~~text
process motifs
→ candidate mechanisms
→ falsifiable hypotheses
→ prospective intervention
→ causal evidence
→ only then policy/playbook promotion
~~~

Không dùng:

~~~text
historical path frequency
→ production policy
~~~

Process mining được phép sinh:

- loop candidates;
- failure-pattern candidates;
- candidate strategy families;
- experiment eligibility strata.

Không được tự sinh authoritative policy.

Playbook phải có version, applicability, rebinding, invalidation, verification, negative/reopen history, explicit revocation và kill switch. Reopen hoặc counterevidence material phải demote playbook; không có promotion P5/routing, automatic retrieval injection hay autonomous strategy selection trong roadmap này.

Process mining chỉ chạy offline trên immutable Tools ledger và mở rộng reporter hiện có để sinh loop/failure/playbook **candidate**. Nó không tạo platform mới, causal policy hay online controller.

---

# 19. Đối chiếu khoa học

Các nguồn dưới đây chỉ hỗ trợ đúng phạm vi thiết kế nghiên cứu của chúng; không nguồn nào chứng minh PRL/RDP cụ thể là tối ưu cho Tools-Codex-web.

| Nguồn | Hỗ trợ | Không chứng minh |
|---|---|---|
| [SWE-Interact](https://arxiv.org/abs/2606.30573) | multi-turn/user-driven SWE làm lộ requirement/interaction/rework failure | schema PRL/RDP này tối ưu |
| [LongCLI-Bench](https://aclanthology.org/2026.findings-acl.1497/) | long-horizon CLI tasks cần sequential planning; stall phổ biến; interactive guidance có thể hữu ích | self-correction luôn vô ích hoặc continuity gate chắc chắn tốt |
| [Context as a Tool](https://aclanthology.org/2026.findings-acl.1032/) | long-horizon SWE bị context explosion/semantic drift; stable task semantics + condensed context có thể hữu ích | immutable problem revision tự gây efficacy hoặc cần thêm context-manager service |
| [COMPASS](https://aclanthology.org/2026.acl-long.152/) | long-horizon failure có thể đến từ mất critical evidence/context coherence và replan failure | multi-agent topology của COMPASS transfer sang SWE/Tools |
| [RoadmapBench](https://arxiv.org/abs/2605.15846) | version drift/long-horizon change làm continuity khó | PRL revision mechanism đủ giải problem |
| [SlopCodeBench v2](https://arxiv.org/abs/2603.24755) | iterative degradation/rework cần được đo ngoài checkpoint pass | no-repeat gate chắc chắn giảm degradation |
| [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/) | routing phải benchmark đa chiều; complex router không mặc nhiên hơn simple baseline | learned routing vô ích trong mọi domain |
| [xRouteBench](https://arxiv.org/abs/2608.06867) | learned/user-conditioned routing có thể tốt trong cohort/budget cụ thể | effect transfer sang Tools problem outcomes |
| [QCR / Beyond Retrieval](https://arxiv.org/abs/2608.12847) | trajectory reuse cần target-bound bindings/applicability/verification | universal memory/playbook schema |
| [Beyond Final Scores](https://arxiv.org/abs/2608.13417) | final score che process bottleneck; experience reuse có thể giúp hoặc gây negative transfer | accepted history đủ làm trusted policy |
| [Process-mining study](https://arxiv.org/abs/2607.04948) | event logs có thể sinh workflow/agent candidates | mined workflow là causal optimum |
| [W3C PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | provenance entity/activity/agent separation | identity provenance = semantic truth |
| [SPACE](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/) | productivity đa chiều | một scalar TTPR đại diện toàn quality |
| [DevEx](https://doi.org/10.1145/3610285) | feedback loops/cognitive load/flow liên quan burden | telemetry tự suy ra user experience |
| [Reopened bugs study](https://www.microsoft.com/en-us/research/publication/characterizing-and-predicting-which-bugs-get-reopened/) | reopen có nhiều nguyên nhân khác nhau | mọi reopen là avoidable agent error |
| [Interval censoring overview](https://pmc.ncbi.nlm.nih.gov/articles/PMC3684949/) | true event time có thể chỉ biết nằm trong một interval giữa observations | một estimator cụ thể mặc nhiên đúng cho Tools |
| [Kaplan–Meier](https://doi.org/10.1080/01621459.1958.10501452) | right-censored time-to-event | competing disposition là success |
| [Cohen’s kappa](https://doi.org/10.1177/001316446002000104) / [Krippendorff’s alpha](https://doi.org/10.1111/j.1468-2958.2004.tb00738.x) | agreement với chance/missingness correction | agreement cao = construct validity |
| [Controlled online experiments](https://ai.stanford.edu/~ronnyk/2007GuideControlledExperiments.pdf) | treatment/control + guardrails cho causal product claim | một natural case = efficacy |

Kết luận khoa học phải khiêm tốn: literature hỗ trợ problem-level evaluation, state/context continuity, bounded experience reuse, negative-transfer guards và prospective/controlled comparison. Không nguồn nào cấp authority để biến history hiện tại thành policy.

---

# 20. Roadmap triển khai và nghiên cứu

## S0 — Current-source delta reconciliation

Mục tiêu: xác nhận roadmap assumptions từ snapshot `d8dd423...` ở current `d254ac0...`.

Exit: `UNCHANGED_ASSUMPTIONS | PARTIALLY_FIXED | SEMANTIC_DRIFT`.

Không source mutation.

## Gate 0 — Connector truth

Mục tiêu: phân biệt source schema, serialized contract và real target-client receipt.

Deliverables:

1. current source/component/contract/process identity vs maintained receipt;
2. regression serialized stdio **và** HTTP `tools/list`: đúng một `action` enum, có cả `problem`/`p5`, không dùng `allOf` intersection;
3. sau authorized connector rediscovery, gọi read-only logical `problem.get` qua `task_control(action="problem", problem_event={operation:"get", problem_id:<nonexistent>})`; expected error là `PRL_PROBLEM_NOT_FOUND`;
4. chỉ recertify real-client khi boundary/identity thực sự trigger;
5. chỉ sửa projection/cache/deployment nếu lỗi tái hiện ở current target client.

Không gọi source contract hiện tại defective chỉ vì receipt cũ hoặc stale client cache.

## C1a — Authority correctness

Deliverables:

- observation-only generic feedback;
- explicit transition authority operations;
- runtime-derived eligibility;
- caller provenance/timestamp không tự cấp authority;
- `recorded_at` runtime-owned; `occurred_at` optional và luôn có source/clock authority;
- event/hash schema v2 với legacy hash compatibility.

Exit:

- shadow/unknown không mutate;
- caller eligibility rejected/ignored;
- caller timestamp không ảnh hưởng policy/TTPR;
- authority receipt deterministic.

## C1b — Immutable revision + identity mechanics

Deliverables:

- `problem_revisions`;
- typed immutable capsule;
- composite nullable exact refs;
- reopen same revision;
- revise CAS;
- pinned handoff/revision;
- migration v9/v10→v11 additive;
- projection consistency checks.

Exit:

- old attempt không reinterpret;
- FK/CHECK/chain/integrity PASS;
- legacy event preserved/ineligible.

## C1c — Reporter/outcome correctness

Deliverables:

- resolution ≠ administrative disposition;
- TTFP / TTOC / resolution interval / disposition time;
- wall vs active clocks;
- censoring/competing-disposition semantics;
- no fake zero on missing clocks.

Exit: metrics mechanically valid, chưa claim efficacy.

## C2 — Exact capture/origin/binding

Deliverables:

- auto-fill pending host turn/trace khi caller omit; explicit mismatch fail closed;
- mismatch fail closed;
- open/observe/confirm/reopen/revise/new-problem instructions;
- exact revision pin trước durable problem RUN write;
- work_origin shadow capture;
- identity codebook/review workflow;
- handoff pinned old revision.

Exit:

- exact binding denominator;
- false split/merge reviewable;
- origin override reviewable;
- concurrency CAS proof.

## C3 — Conditional outcome bridge

Deliverables:

- immutable `resolution_claim`;
- complete criterion/proof manifest;
- engineering floor semantics;
- idempotent provisional event;
- valid recovery/reconciliation;
- explicit confirm/reopen/revise/block.

`resolution_claim=none` và `work_origin=non_problem` chỉ ghi progress/observation; chúng không tạo provisional closure. Recovery chỉ reconcile bridge claim v11 hợp lệ, never recreate closure from inferred/shadow state.

Exit: trusted technical-to-problem bridge mechanically correct.

## C4 — Tools-only natural canary + freeze

30–50 events chỉ là mechanics calibration range, không efficacy law.

Freeze:

- schema;
- identity codebook;
- action-kind codebook;
- transition semantics;
- estimators;
- cohort rules.

Chỉ hotfix privacy, integrity hoặc measurement defect trong cohort. Semantic change phải tăng schema/codebook version và bắt đầu cohort mới hoặc stratify rõ ràng.

Review sample:

- problem identity;
- exact link;
- work origin;
- transition authority;
- capsule privacy;
- criterion/proof attribution;
- action kind;
- timestamp authority.

Exit dựa trên preregistered critical-defect/error bounds, không raw N.

Canary report bắt buộc event-chain/FK/integrity, privacy, exact binding, structural criterion coverage, false merge/split, authoritative confirmation và confidence intervals; `30–50` là mechanics calibration, không efficacy threshold.

## C5 — Decision Observation Cohort

### C5a Initial decision prior

Reuse P4 recommendation/ref as initial-decision observation. Không thay routing.

### C5b Post-failure update

RDP-Shadow chỉ trên replacement WAVE thứ hai hoặc sau đó, có write capability, cùng exact problem revision và làm `full_problem`; không bắt read-only/simple/non-problem task lập decision card. Runtime carry previous decision/proof, user reopen/correction và invalidation qua restart/compaction/handoff. Đây là comparison shadow với hành vi thực; không hard-block và không tự chọn strategy.

Measure:

- previous evidence carried forward?;
- fresh observed delta present?;
- action/hypothesis/oracle/scope materially changed?;
- exact failed mutation replay?;
- overhead/probe/clarification burden?;
- annotation reliability?;

Exit:

- instrumentation coverage đủ;
- runtime refs valid;
- action-kind/problem-identity reliability acceptable cho intended analysis;
- burden dưới guardrail;
- không shadow side effect;
- candidate C6 eligibility rõ.

Focused RDP proof phải bao phủ: đúng một record cho mỗi replacement WAVE; record trước first write; same-ID/same-bytes idempotent; changed bytes conflict; runtime bind predecessor/problem/revision; caller không spoof reserved handoff projection; stale/cross-revision refs bị reject; shadow không đổi route/state/mutation/policy; restart/handoff giữ projection và invalidation.

## C6 — Controlled continuity evaluation

Unit: `problem_revision`.

Treatment: `RDP_CONTINUITY_GATE_V1` hoặc một bounded intervention khác được preregister trước cohort.

Primary candidate mechanism:

~~~text
accepted/failed attempt or authoritative reopen
   → replacement write-capable WAVE
   → exact prior outcome/proof must be referenced
   → fresh runtime-observed delta OR typed authorized exception
   → exact failed mutation request cannot silently replay
~~~

Control: same PRL v11 stack without behavior-changing gate.

Focused fixture bắt buộc ở cấp `problem_revision`: accepted technical attempt → explicit same-problem reopen → next write-capable attempt phải reference exact prior outcome **và** một fresh discriminator/observed-evidence reference. Evaluation so sánh control/RDP về correctness, repeated low-information waves, reopen/rework, `TTPR_wall`, `TTPR_active`, protocol overhead, clarification burden và false blocks.

Measure:

- primary rework outcome;
- trusted resolution;
- correctness/security/authority floors;
- TTFP/TTOC/active time;
- clarification/probe/protocol burden;
- false block/override;
- contamination/compliance.

Terminal decision:

- `PROMOTE_BOUNDED`;
- `REJECT`;
- `RETIRE_HYPOTHESIS_FOR_EPOCH`;
- `INCONCLUSIVE_MEASUREMENT` only nếu preregistered validity gate thực sự fail.

Không mở framework mới chỉ vì effect ≈ 0.

## Out of scope — replication / external validity

HR, independent benchmark và repository khác không phải cohort, completion gate hay replication task của roadmap này. C6 chỉ có thể tạo claim nội bộ cho Tools-Codex-web; bất cứ quyết định mở scope nào sau đó cần một proposal/authority riêng, không được ngầm kéo vào delivery này.

---

# 21. Metrics

## 21.1 Primary problem outcomes

Mọi user-outcome rate dùng preregistered follow-up horizon `H`; immature revision không đi vào fixed-horizon denominator.

| Metric | Definition |
|---|---|
| First Revision Resolution Rate @ H | revision đạt trạng thái resolution được định nghĩa trước ở first eligible full attempt trước H / eligible mature revisions; luôn báo riêng provisional, confirmed và trusted |
| First Revision Trusted Resolution Rate @ H | revision trusted-resolved ở first full attempt trước H / eligible mature revisions |
| Authoritative Confirmed Resolution Rate @ H | exact explicit-user/human confirmed revisions / eligible mature revisions |
| Technical Full-Pass Rate | full claims đạt floor + complete structural coverage / eligible full claims |
| Trusted Resolution Rate | exact revision có cả engineering trust + authoritative confirmation / eligible revisions |
| Reopen Rate @ H | authoritative same-revision reopen / mature provisionally or confirmed revisions |
| Avoidable Correction Rate | reviewed avoidable corrections / eligible correction events |
| Attempts per Trusted Resolution | exact primary attempts / trusted-resolved revisions |
| `time_to_provisional` / TTFP | authoritative start → first valid technical full-pass + deterministic provisional event |
| `time_to_confirmed_resolution` / TTOC | authoritative start → observed explicit confirmation; không tự nhận là real-world resolution time |
| `time_to_administrative_disposition` | authoritative start → supersede, abandon hoặc block; competing disposition, không success |
| `TTPR_wall` | authoritative start → resolution end chỉ khi start/end `occurred_at` cùng attested clock authority; khác clock/missing clock = UNKNOWN, không 0 |
| Resolution Interval Width | confirmation time − full-pass time khi interval assumptions hợp lệ |
| `TTPR_restricted` / `TTPR_active` | union active engineering intervals trên compatible clock domain; excludes user/external/wait spans |

## 21.2 Decision/rework metrics

- low-information replacement WAVE rate;
- exact failed mutation replay rate;
- previous-outcome carry-forward coverage;
- fresh-observed-delta coverage;
- strategy/hypothesis/oracle/scope change rates sau counterevidence;
- initial P4 recommendation vs eventual outcome strata;
- post-failure RDP adaptation vs next outcome;
- duplicate mutation replan rate.

## 21.3 Mechanics/burden metrics

- exact revision binding coverage;
- problem-capture coverage by work_origin;
- criterion-to-proof structural coverage;
- outcome observation coverage;
- authoritative timestamp coverage;
- chain/FK/projection integrity;
- no-claim rate;
- false split/merge;
- origin/transition override;
- RDP coverage;
- bytes/latency/authoring burden;
- clarification turns/problem;
- probes/problem;
- false-stop/false-block;
- protocol compliance.

Mỗi report ghi snapshot/cohort, HEAD, schema version, filters, missingness, censoring, sample size. Internal credits không được gọi là provider billing.

---

# 22. Reliability và annotation protocol

Independent double annotation cần cho ít nhất:

- problem identity;
- work origin;
- transition intent/authority;
- action kind;
- criterion/proof semantic adequacy sample;
- avoidable correction mechanism sample.

Báo:

- raw agreement;
- prevalence;
- Cohen’s kappa hoặc Krippendorff’s alpha phù hợp;
- disagreement matrix;
- ambiguous/unknown rate.

Low agreement là measurement finding, không được giải quyết bằng cách tự động ép classifier output thành truth.

---

# 23. Preregistered evaluation skeleton C6

Trước treatment phải khóa:

1. population/exclusions;
2. exact treatment semantics và exception set;
3. primary outcome duy nhất hoặc multiplicity handling;
4. correctness/security/authority non-inferiority floors;
5. minimum detectable effect + power/sample assumptions;
6. follow-up horizon;
7. censoring/interval/competing-disposition handling;
8. randomization/allocation mechanism nếu khả thi;
9. stratification: task class, oracle strength, source epoch, initial P4 risk/scope;
10. contamination/compliance handling;
11. protocol/user burden guardrails;
12. false-block ceiling;
13. stop/harm rules;
14. schema/codebook version;
15. analysis plan trước outcome reveal.

Nếu randomization không khả thi và chỉ có observational comparison, claim phải hạ từ causal efficacy xuống association/quasi-experimental evidence tương ứng.

---

# 24. Causal-analysis discipline

Historical và prospective observational data có confounding theo:

- task difficulty;
- model/route;
- tool/runtime version;
- source epoch;
- oracle strength;
- user involvement;
- workspace/context width;
- failure type;
- prior attempts;
- time-of-day/host availability/capacity.

Do đó:

~~~text
observed path X → success
không cho phép suy
forcing path X → higher success
~~~

mà không controlled/credible causal design.

C5 dùng để discover/measure mechanisms. C6 mới được dùng để estimate treatment effect.

Phân tích phải báo effect heterogeneity thay vì chỉ pooled average khi task classes khác nhau rõ rệt.

---

# 25. Definition of Done bốn tầng

## Tầng 1 — Mechanics

- v11 authority/revision/timestamp/idempotency đúng;
- privacy gate fail closed;
- chain/FK/projection integrity PASS;
- reporter tách technical/confirmation/disposition;
- legacy history không bị semantic rewrite.

## Tầng 2 — Adaptive integration

Fixture reopen bắt replacement decision carry exact previous outcome/proof + fresh observed delta/valid exception; restart/compaction/handoff không mất revision/invalidation.

## Tầng 3 — Natural-system demonstration

Một real Tools problem đi qua:

~~~text
open
→ exact revision
→ full attempt
→ EOCL proof/checkpoint
→ provisional
→ authoritative reopen
→ replacement decision carrying prior evidence
→ trusted resolution OR typed blocker
~~~

qua restart/handoff mà không dựng lại transcript.

Đây chỉ là integration demonstration.

## Tầng 4 — Internal efficacy

Prospective/control C6 cho credible evidence rằng bounded continuity intervention giảm preregistered rework outcome mà không làm giảm quality/security/authority hoặc tăng TTPR/burden vượt floors.

---

# 26. Stop conditions và kill switches

Dừng rollout/demote protocol khi:

- secret/privacy material vào durable capsule;
- shadow/unknown authority mutate canonical state;
- unattested timestamp vào policy/outcome estimator;
- false split/merge vượt threshold;
- protocol tăng false block/clarification/probe burden/TTPR quá guardrail;
- negative transfer/reopen tăng materially;
- schema/codebook drift trong cohort không version;
- current connector truth khác source regression chưa localize projection/cache/deployment;
- treatment contamination làm effect không interpretable;
- primary outcome null/harm sau đủ power và floors → **REJECT/RETIRE**, không mở semantic compiler để cứu hypothesis.

BLOCKED record phải có typed reason + exact next evidence/action. “Không đủ thông tin” không đủ cụ thể.

---

# 27. Những việc cố ý không làm

- Không tool MCP thứ chín.
- Không Resolution Compiler service/brain/planner/policy engine.
- Không second database/vector DB/knowledge graph.
- Không autonomous retrieval injection.
- Không auto-route Mini/Luna/Terra/Sol từ RDP.
- Không semantic-backfill historical problem outcomes.
- Không process-mined path → production policy.
- Không hard semantic information-gain gate trước evidence.
- Không hard “hai attempts”.
- Không dùng HR làm C0–C6 completion gate.
- Không dùng 30–50/100 như scientific law.
- Không tối ưu một scalar “expected remaining work” làm authority.
- Không tuyên bố eventual convergence.
- Không mở thêm P6/P7/P8 chỉ vì natural evidence chưa đủ.

---

# 28. Implementation work packages dự kiến

| Tranche | Primary surfaces | Test/validation surfaces | Dependency |
|---|---|---|---|
| S0 | read-only current-source delta | source diff / focused read | none |
| Gate 0 | tool schema / serialized transport nếu lỗi current tái hiện | stdio+HTTP tools-list + real-client receipt khi trigger | S0 |
| C1a | problem lineage authority/control/schema | lineage/authority/timestamp focused tests | Gate 0 |
| C1b | revision/capsule/migration/handoff | lineage + migration + FK/chain/handoff | C1a |
| C1c | economics/reporter clocks/disposition | reporter + censoring fixtures | C1b |
| C2 | capture/binding/origin/instructions | host-turn + lineage + handoff | C1 |
| C3 | claim/proof manifest/outcome bridge | proof + acceptance + recovery/idempotency | C2 |
| C4 | reporter/codebook/reliability docs; source only for measurement defects | immutable cohort receipts + annotation | C3 |
| C5 | P4 analytical join + RDP event/handoff projection | replan/RDP/reliability/burden | C4 |
| C6 | bounded continuity gate + experiment reporter | allocation/compliance/effect fixtures | C5 |

Mỗi tranche là smallest coherent change, focused proof trước, checkpoint rõ, không re-open accepted architecture chỉ vì sample pending.

---

# 29. Rủi ro còn lại và giới hạn khoa học

1. Problem identity vẫn là semantic construct, không hoàn toàn machine-verifiable.
2. Action-kind có thể low agreement nếu task operations multiplex nhiều intents.
3. Criterion-to-proof map structural không chứng minh oracle semantic adequacy.
4. User confirmation có selection bias; silence có thể informative.
5. True resolution time thường interval-censored, không exact.
6. RDP có thể tăng cognitive/protocol burden hơn benefit.
7. Historical logs có confounding theo task/model/source/runtime maturity.
8. C6 continuity gate có thể chỉ giảm duplicate mutation nhưng không tăng trusted resolution.
9. Playbook có thể negative-transfer giữa superficially similar revisions.
10. Current source đã drift từ baseline snapshot; S0 bắt buộc để tránh implement stale assumptions.
11. Nếu schema quá giàu, bounded structured record có thể biến thành planning prose dạng JSON.
12. External validity không được đánh giá trong roadmap này; không được generalize cohort Tools sang product/benchmark khác.

---

# 30. Final recommendation

Cho phép triển khai **S0 → Gate 0 → C1a/b/c → C2 → C3 → C4** như một closure tranche duy nhất của scientific instrument PRL v11.

Sau khi mechanics + natural capture valid:

- bật **C5 Decision Observation Cohort**;
- dùng **P4** như initial-decision prior;
- dùng **RDP-Shadow** như post-failure decision update;
- không hard-block, không route, không promote policy.

Chỉ khi C5 cho thấy instrumentation reliable và burden hợp lý mới preregister **C6 `RDP_CONTINUITY_GATE_V1`** hoặc một bounded behavior-changing intervention tương đương.

Câu hỏi C6 phải là:

> **Việc buộc replacement mutation carry exact prior outcome/failure evidence và fresh observed delta có giảm avoidable rework mà không làm giảm trusted resolution hoặc tăng burden quá ngưỡng không?**

Nếu **có**, ta có một finding quan trọng:

> một phần long-horizon coding rework đến từ decision-state continuity failure, không chỉ model coding capability.

Nếu **không**, hypothesis phải được reject/retire cho epoch và program chuyển sang mechanism khác theo evidence.

Không được cứu hypothesis bằng việc xây Resolution Compiler lớn hơn.

## 30.1 Điểm dừng sản phẩm Tools V1

Tools-Codex-web giữ được:

- exact immutable problem contract;
- pinned revision cho từng attempt;
- authority-safe state transitions;
- conditional technical→problem outcome bridge;
- explicit confirm/reopen/revise;
- resolution tách administrative disposition;
- exact prior outcome/evidence carry-forward qua restart/handoff;
- decision observation không cần reconstruct transcript.

Đây là **Problem Resolution Measurement/Continuity V1**.

## 30.2 Điểm dừng học thuật

Không phải “RDP đã được build”.

Mà là:

> **một preregistered causal test đã PROMOTE/REJECT một hypothesis cụ thể về decision-state continuity, với quality/burden floors và measurement validity đủ rõ để người khác có thể phản biện hoặc replicate.**

---

# 31. Validation và claim discipline cho bản cập nhật này

### Baseline validation receipt được giữ như historical evidence

Bản gốc đã ghi:

- immutable ledger snapshot ở `d8dd423...`;
- external link/local anchor checks tại thời điểm lập;
- no source/runtime/migration/restart/commit/push/release/deploy trong documentation task;
- Git diff/whitespace checks tại thời điểm đó.

### Update receipt hiện tại

Bản cập nhật này quan sát current workspace `main @ d254ac0...` và tạo **một Backup-API immutable census mới** trong Mục 4.1. Vì vậy:

- Mục 4.1 là current-source point-in-time receipt; Mục 4.2–4.5 giữ baseline lịch sử `d8dd423...` để chronology không bị rewrite;
- row count lặp lại giữa hai snapshot không biến các population thành live, causal hay outcome denominators;
- source gap matrix được recheck có chủ đích tại các anchors liệt kê ở Mục 5.1; S0 vẫn là pre-implementation sign-off, không phải lý do tự động mutation;
- không claim current C1/C2/C3 implementation state chỉ từ historical source anchors;
- không claim current live connector defect nếu chưa có current target-client reproduction;
- không claim C5/C6 efficacy trước prospective evidence.

### Kiểm tra delivery của báo cáo này

- Corpus attachment được hash/deduplicate trước khi tổng hợp (Mục 0.2).
- Source anchors trong Mục 5.1 được kiểm local: file tồn tại và line range được nêu có mặt ở `d254ac0…`.
- Citation check: 14/20 title/standard pages mở trực tiếp qua browser; PMC interval-censoring và Stanford experiment guide trả HTTP 200 qua direct check; bốn DOI resolver endpoints trả 403 cho client kiểm tra và một DOI trả redirect 302. Đây là access-control/redirect outcome, không phải claim rằng DOI sai; URL DOI nguyên gốc được giữ, không thay bằng mirror không kiểm chứng.
- Tất cả fence Markdown trong file đã được pair-checked; `git diff --check` PASS.
- Final worktree còn `.coding-tools/orchestration/ledger.sqlite3` drift (đã tồn tại/tiếp tục là runtime evidence) và báo cáo này. Không source/runtime/migration/restart/connector call/commit/push/release/deploy nào được thực hiện.

### Research claim ladder

~~~text
SOURCE PRESENT
≠ FOCUSED PROOF
≠ CONTROLLED ACTIVATION
≠ NATURAL INTEGRATION
≠ INTERNAL EFFICACY
≠ EXTERNAL VALIDITY
≠ RELEASE / PRODUCTION
~~~

Tài liệu này chỉ authorize roadmap và research design. Mọi bước triển khai sau phải báo đúng tầng bằng chứng thực tế.
