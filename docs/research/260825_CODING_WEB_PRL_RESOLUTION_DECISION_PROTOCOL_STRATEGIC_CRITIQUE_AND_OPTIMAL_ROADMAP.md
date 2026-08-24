# Tools-Codex-web: hoàn thiện PRL và thử nghiệm Resolution Decision Protocol

**Strategic critique, authority-safe design và optimal roadmap**

Ngày lập báo cáo: 2026-08-25

Phạm vi: chỉ repository Tools-Codex-web

Source identity được quan sát: main @ d8dd423b79316d0475e770085d534075ad51ec0f

Trạng thái tài liệu: quyết định kiến trúc và kế hoạch triển khai; chưa phải implementation receipt

## 1. Kết luận điều hành

Hướng tối ưu là hoàn thiện Problem Resolution Lineage (PRL) thành tranche nền bắt buộc, sau đó thử một Resolution Decision Protocol (RDP) mỏng ở chế độ shadow. Không xây “Resolution Compiler” như brain, planner, policy engine, memory platform hoặc subsystem mới.

Quyết định này giữ lại phần có giá trị nhất của ba tư vấn:

1. Đơn vị cần tối ưu là một problem revision đi tới trusted resolution, không phải một RUN đơn lẻ.
2. Problem contract phải tồn tại bền vững, bất biến theo revision và được pin chính xác vào từng attempt.
3. Một replan có khả năng ghi phải chỉ ra điều gì đã thay đổi trong evidence, hypothesis, oracle, scope, contract, authority hoặc môi trường.
4. Outcome thực phải quay lại điều chỉnh lần quyết định sau.

Nhưng báo cáo bác bỏ bước nhảy từ history sang policy ở trạng thái hiện tại. Snapshot mới có 923 RUN và 1.430 WAVE nhưng PRL chỉ có một event UNLINKED, không có problem thread và không có natural outcome denominator. Dữ liệu đó đủ để tìm lỗi mechanics, loop candidates và hard invariants đã có oracle; nó chưa đủ để học causal resolution policy.

Thứ tự đúng là:

~~~text
Gate 0 connector truth
    ↓
C1 authority-safe PRL v11
    ↓
C2 exact capture/origin/binding
    ↓
C3 conditional EOCL outcome bridge
    ↓
C4 Tools-only natural canary + schema freeze
    ↓
C5 RDP-Shadow trên replan có khả năng ghi
    ↓
C6 prospective/control evaluation
    ↓
chỉ khi có bằng chứng: semantic-repeat gate hoặc playbook promotion
~~~

Trước C4, hệ thống chỉ được tuyên bố đã đúng về mechanics. Một natural case qua restart/handoff/reopen chỉ chứng minh adaptive integration. Chỉ một cohort prospective hoặc controlled mới có thể chứng minh efficacy.

## 2. Quyết định chấp nhận, sửa và giữ lại

| Đề xuất | Quyết định | Lý do |
|---|---|---|
| PRL closure là nền bắt buộc | Chấp nhận | Đây là identity, contract, outcome và measurement boundary còn thiếu |
| Problem Revision là object bất biến | Chấp nhận | Integer trên thread/event không đủ bảo toàn semantic contract |
| Accepted RUN tự động provisional-resolve | Bác bỏ | RUN có thể chỉ diagnose hoặc hoàn thành một phần |
| Resolution claim có điều kiện | Chấp nhận, thu taxonomy | V1 chỉ cần none hoặc full_problem; work origin giải quyết phần còn lại |
| Resolution Compiler là “não hệ thống” | Bác bỏ | Tạo authority song song, abstraction và policy chưa có ground truth |
| Resolution Decision Protocol mỏng | Chấp nhận ở shadow | Tận dụng WAVE, replan, proof, P4 và handoff hiện có |
| Numeric expected information gain | Bác bỏ | Chưa có probability model được hiệu chuẩn |
| Hard limit hai attempt | Bác bỏ | Failure do capacity/flaky proof khác causal failure |
| Không lặp mutation nếu không có information gain | Sửa | Trong shadow chỉ yêu cầu runtime-verified observed delta; chưa hard-block |
| Process mining lịch sử | Giữ ở P2/offline | Hữu ích để sinh candidate, không chứng minh causality |
| History tự động thành policy/playbook | Hold | Chỉ hard invariant có deterministic oracle mới enforce ngay |
| Vector DB, retrieval injection, autonomous strategy/routing | Hold | Chưa có outcome quality, applicability và negative-transfer evidence |
| Multi-agent manager hoặc database thứ hai | Bác bỏ | Không có current need; tăng coordination và consistency cost |

## 3. Phạm vi, phương pháp và giới hạn claim

### 3.1 Phạm vi

Báo cáo chỉ đánh giá Tools-Codex-web. Mọi ví dụ HR trong attachment chỉ được xem là minh họa; HR không phải completion gate, không phải nguồn denominator và không nằm trong roadmap triển khai này.

Báo cáo dùng thứ tự authority của repository:

1. implementation, focused tests và live contract hiện tại;
2. docs/CURRENT_STATE.md;
3. maintained product docs;
4. component docs;
5. dated research snapshots;
6. attachment và external research.

Source presence, focused proof, controlled activation và packaged/released state là bốn claim khác nhau. Báo cáo không nâng claim vượt bằng chứng.

### 3.2 Chuẩn hóa attachment

Năm attachment mới chỉ có ba nội dung duy nhất. Hai cặp là bản sao byte-for-byte:

| Nhóm | Attachment | SHA-256 | Kích thước | Dòng | Vai trò |
|---|---|---|---:|---:|---|
| A | 2be72e6d… và f51a242e… | e5115329598a46a8e55c5a9e9164f6bc519363ca38a67bfbcfc1e1744ae9f284 | 22.498 B | 667 | PRL revision-safe closure |
| B | b8336f78… và 0a3b893b… | 08a6b5760e0ede301b47a2f7832bf47a4fc9af95afc0d9c8fa7b7f9881bd5783 | 16.885 B | 746 | Resolution Compiler/history→policy |
| C | 16c61b82… | 9c9a3c876cf4682a1a45cbdddadebfdae7c050fa148af3713ef63e5731121cc7 | 14.964 B | 618 | Phản biện compiler và đề xuất protocol mỏng |

Tài liệu tư vấn trước đó có SHA-256 02e08e0744c8ca25aca2c46a6c59724616f4ec43bc253c90ea7ec60c564a1ff6; nó là context lịch sử, không được tính như tài liệu thứ tư trong claim matrix mới.

### 3.3 Phương pháp

- Đối chiếu từng claim quan trọng với source và focused test hiện tại.
- Chụp ledger bằng SQLite Backup API trong temporary directory ngoài repository.
- Tách measured facts, derived interpretations, design proposals và hypotheses cần thử.
- Chỉ dùng nguồn khoa học làm support cho phạm vi mà thiết kế nghiên cứu của nguồn cho phép.
- Không dùng performance.json để suy ra problem economics vì chưa có workspace attribution phù hợp và internal credits không phải provider billing.

## 4. Immutable evidence receipt ngày 2026-08-25

### 4.1 Snapshot identity

| Thuộc tính | Giá trị |
|---|---|
| Git HEAD | d8dd423b79316d0475e770085d534075ad51ec0f |
| Capture UTC | 2026-08-24T19:05:01.249Z |
| Capture Asia/Saigon | 2026-08-25T02:05:01.249+07:00 |
| Hoàn tất UTC | 2026-08-24T19:05:02.859Z |
| Snapshot SHA-256 | 25e513468b68e2593c25b4a9afbfdd6efddc991f1e82f9c53ec96c465784f468 |
| Snapshot size | 64.696.320 byte |
| SQLite user_version | 10 |
| Read mode | query_only, immutable Backup-API copy |
| integrity_check | ok |
| foreign_key_check | 0 violation |
| Canonical writer/runtime/governor instantiated | không |

Snapshot implementation mở source read-only, bắt đầu explicit read transaction, dùng SQLite backup và chỉ đọc bản sao; xem [ledger_analysis.py](../../resources/coding-tools-mcp/coding_tools_mcp/ledger_analysis.py#L95) và [lifecycle_census.py](../../resources/coding-tools-mcp/coding_tools_mcp/lifecycle_census.py#L135).

Một lifecycle capture độc lập lúc 2026-08-24T19:05:47.506Z tạo lại đúng physical snapshot SHA-256 ở trên và báo logical SHA-256 ce5805d9776647b3659817a980ac29fd9560b3dba06777a1bb1cd9241da7eec2. Đây là companion consistency receipt trên một Backup-API copy khác, không phải cùng temporary snapshot object.

### 4.2 Population và filters

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
| wave_replanned events | 513 |
| failure_observed events | 656 |
| failure_observed trong RUN hiện accepted | 436 |

Các con số là row counts; không giả định quan hệ 1:1 giữa RUN, checkpoint, WAVE hoặc event.

Các filters chính:

~~~sql
SELECT status, COUNT(*) FROM runs GROUP BY status;
SELECT status, COUNT(*) FROM checkpoints GROUP BY status;
SELECT status, COUNT(*) FROM waves GROUP BY status;
SELECT COUNT(*) FROM events WHERE event_type='wave_replanned';
SELECT COUNT(*) FROM events WHERE event_type='failure_observed';
SELECT COUNT(*)
FROM events e JOIN runs r ON r.run_id=e.run_id
WHERE e.event_type='failure_observed' AND r.status='accepted';
~~~

### 4.3 PRL v10 tại snapshot

| Population | Count |
|---|---:|
| problem_threads | 0 |
| problem_events | 1 |
| ENGINEERING_ATTEMPT_BOUND | 1 |
| UNLINKED | 1 |
| policy-eligible / ineligible | 0 / 1 |
| exact primary RUN binding | 0 |

Event duy nhất có caller field event_time bằng 2026-08-24T03:32:15.969Z. Không có problem-thread state, confirmed outcome, TTPR hoặc correction denominator.

PRL-D companion report trả DESCRIPTIVE_ONLY: exact/ambiguous/unlinked bằng 0/0/1, observed terminal threads bằng 0 và TTPR/restricted-TTPR đều null. right_censored_threads bằng 0 vì không có thread nào để đưa vào risk set, không phải vì mọi problem đã kết thúc.

Do ledger là runtime evidence sống, các count trên chỉ đúng tại snapshot. Main database trước/sau capture giữ nguyên size và mtime trong cửa sổ 1,61 giây; WAL bằng 0, SHM vẫn do runtime chạm. Không dùng live-file hash làm transactional receipt.

Lifecycle companion capture lúc 19:05:47Z phân loại cả 5 ordinary active rows là THRESHOLD_SENSITIVE_STALE_CANDIDATE dưới ngưỡng stale 24 giờ và không có live ownership; nó cũng thấy một unbound running background-operation residue. Đây là point-in-time operator evidence, không phải quyền để stop/reconcile trong một documentation-only task.

### 4.4 Diễn giải đúng

923 RUN không phải 923 problem. 505 accepted RUN không phải 505 resolution. 656 failure events không phải 656 causal failures độc lập. Một PRL event UNLINKED không chứng minh capture rate bằng 0 trên một population đã định nghĩa; nó chứng minh natural PRL denominator hiện chưa tồn tại.

Đây là bằng chứng mạnh cho việc hoàn thiện measurement/authority foundation trước policy, không phải bằng chứng ủng hộ một brain tự học.

## 5. Claim matrix của ba tài liệu mới

| Claim | A: PRL closure | B: Compiler | C: Protocol | Source/science verdict | Quyết định |
|---|---|---|---|---|---|
| Problem revision phải bất biến | Mạnh | Kế thừa | Mạnh | Source xác nhận event/RUN chưa pin revision | Adopt P0 |
| Reopen không đồng nghĩa revise | Mạnh | Kế thừa | Kế thừa | Source đang tăng revision khi reopen | Adopt P0 |
| Accepted RUN không tự là resolution | Mạnh | Có full program | Đồng ý | Một proof pass chưa phủ toàn contract | Adopt P0 |
| Durable semantic contract cần thiết | Có | Có | Có | Cần continuity nhưng tạo privacy risk | Adopt với strict capsule |
| Connector hiện defective | Khẳng định | Kế thừa | Kế thừa | Source/test hiện có problem/p5; live claim chỉ đang thiếu fresh receipt | Sửa thành Gate 0 truth |
| History phải ảnh hưởng next decision | Hàm ý | Trung tâm | Trung tâm | Hợp lý như hypothesis cần prospective test | Adopt shadow |
| History hiện đủ để tạo policy | Không | Khẳng định | Bác bớt | Không có natural PRL outcome denominator | Reject |
| Compiler là brain | Không | Khẳng định | Bác bỏ | Trùng authority với Sol/EOCL, tăng subsystem | Reject |
| EIG có thể tối ưu online | Không | Khẳng định | Hạ thành ordinal | Chưa có calibrated probability model | Reject numeric |
| Hai attempt rồi phải đổi strategy | Không | Khẳng định | Bác hard N | Failure modes khác nhau | Reject hard limit |
| Process mining tạo playbook | Sau | Có | Candidate-only | Correlation/path discovery, không causal proof | Hold P2 advisory |
| Natural case chứng minh breakthrough | Vertical loop | DoD | Integration test | Một case không ước lượng effect | Integration only |
| Multi-workspace/HR là closure gate | Có | Ví dụ HR | Ví dụ HR | Ngoài phạm vi đã khóa | Exclude |

### Phản biện tổng hợp

Tài liệu A đúng về data model và conditional outcome bridge, nhưng taxonomy DIAGNOSTIC/PARTIAL/FULL/NON_PROBLEM tạo hai representation chồng nhau. V1 đơn giản hơn khi dùng work_origin để phân biệt problem/non-problem và resolution_claim chỉ gồm none/full_problem.

Tài liệu B phát hiện đúng gap continuity giữa các replans. Sai lầm của nó là nâng một protocol ghi quyết định thành authoritative compiler, suy policy từ execution telemetry và coi process mining như nguồn tri thức causal. Đây là overreach lớn nhất.

Tài liệu C sửa đúng overreach đó, nhưng ordinal information gain vẫn có thể bị game và không machine-verifiable. Thiết kế cuối cùng không dùng score NONE/LOW/MATERIAL/DECISIVE làm gate. Runtime chỉ kiểm observed_delta_refs; semantic_delta_claim của Sol là advisory.

## 6. Source-truth: gap thực sự của v10

| Gap | Source anchors | Sự thật mạnh nhất | P |
|---|---|---|---|
| Caller khai provenance/eligibility | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L200), [tool_schema.py](../../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py#L484) | eligible_for_policy là public input; provenance/evidence là caller enum | P0 |
| Shadow feedback có thể mutate state | [state derivation](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L221), [transition application](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L427), [thread update](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L474) | State derivation không bị chặn bởi shadow provenance hoặc false eligibility | P0 |
| HOST_OBSERVED chỉ bind identity | [problem_lineage_control.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py#L39) | Pending turn/trace được kiểm; semantic label không được host attest | P0 |
| Caller time đi vào TTPR | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L226), [problem_resolution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_economics.py#L141) | Hash bảo toàn timestamp đã ghi, không chứng minh clock đúng | P0 |
| Revision chỉ ở thread | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L309) | Không có immutable problem_revisions authority | P0 |
| Reopen tự tăng revision | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L444) | Same-requirement failure có thể bị diễn giải như contract revision | P0 |
| Handoff đọc current revision | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py#L542) | Attempt cũ có thể bị reinterpret theo revision mới | P0 |
| Criteria không map vào proof | [proof_ledger.py](../../resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py#L19), [coordination.py](../../resources/coding-tools-mcp/coding_tools_mcp/coordination.py#L1313), [problem_resolution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_economics.py#L201) | Có contract/proof identity, chưa có criterion-level attribution | P0 |
| Disposition được tính như resolution | [problem_resolution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_economics.py#L24) | closed set gồm unconfirmed, superseded và abandoned | P0 |
| Replan reason là free text | [orchestration_control.py](../../resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py#L744) | Có WAVE boundary, chưa có observed decision delta | P1 |
| Handoff và P4 primitives đã có | [orchestration_ledger.py](../../resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py#L2814), [solution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/solution_economics.py#L102) | Có 8 KiB capsule, allowlist/idempotency/pre-write patterns và proof refs | Reuse |

Một nuance quan trọng: current source schema có action problem và p5 trong một enum ở [tool_schema.py](../../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py#L362), và focused test kiểm problem hiện diện ở [test_problem_lineage.py](../../resources/coding-tools-mcp/tests/test_problem_lineage.py#L190). Do đó không được gọi source contract hiện tại là defective chỉ vì một connector snapshot cũ từng có allOf/intersection. [CURRENT_STATE operational recency override](../CURRENT_STATE.md#L18) giữ một process-bound connector LIVE_PASS; receipt này chỉ phải tái chứng nhận sau component/contract/process boundary tương ứng. Delivery tài liệu hiện tại không quan sát live connector mới hơn và không hạ receipt đó thành blocker.

### 6.1 Delta tối thiểu, không xây lại primitive

| Plane v10 hiện có | Giữ nguyên | Delta v11 nhỏ nhất | Không làm |
|---|---|---|---|
| PRL problem_threads + problem_events | canonical ledger, event chain, link identity | immutable problem_revisions, explicit authority, timestamp v2, composite ref | database/tool/state machine thứ hai |
| EOCL RUN/WAVE/proof/checkpoint | execution, mutation, proof và acceptance authority | work_origin/claim binding + conditional idempotent outcome bridge | PRL tự accept RUN hoặc chạy proof |
| P4 solution recommendation | allowlist, idempotency, pre-write pattern, scope/oracle refs | RDP chỉ trỏ recommendation_id khi có | copy P4 payload hoặc promote routing |
| Replan/new WAVE | quiescence, predecessor, base/worktree/contract/objective identity, reason | one typed RDP-Shadow record trên enrolled replacement WAVE | planner/strategy engine |
| Handoff capsule | bounded/sanitized transport và runtime-reserved projection | chỉ thêm exact PRL/RDP refs + invalidation do runtime derive | copy contract semantics hoặc caller-supplied authority |

## 7. Thiết kế P0: PRL v11 authority-safe

### 7.1 Ba lớp authority phải tách

1. Identity provenance trả lời: event gắn đúng turn, trace, RUN, WAVE, workspace và revision nào?
2. Transition authority trả lời: actor/operation này có quyền đổi canonical state hay không?
3. Policy eligibility trả lời: observation có đủ chất lượng và provenance để vào cohort hoặc promotion analysis hay không?

Exact identity không tự tạo semantic authority. Semantic authority không tự tạo technical proof. Policy eligibility không được là quyền caller tự cấp.

### 7.2 Transition-authority matrix

Trong v11, operation feedback chỉ append observation. Nó không đổi canonical state. Adapter/runtime phải chuyển structured explicit-user feedback thành một explicit operation riêng sau khi identity và authority được xác minh.

| Explicit operation | Canonical effect | Allowed authority | Bắt buộc | Bị cấm |
|---|---|---|---|---|
| open | Tạo thread + revision 1 ở OPEN | explicit user/controller hoặc human-reviewed annotation | exact workspace; accepted sanitized capsule | shadow/inferred tự mở policy-eligible thread |
| observe_feedback | Không đổi state | mọi provenance được ghi rõ | exact turn/trace nếu claim host-observed | mọi state mutation |
| provisional_resolve | Revision → PROVISIONALLY_RESOLVED | deterministic EOCL acceptance bridge | full_problem; exact revision; current contract; structurally complete criterion-to-passed-proof attribution; engineering-floor path; accepted checkpoint | model/shadow feedback; caller eligibility |
| confirm | Revision → RESOLVED_CONFIRMED | structured explicit-user feedback hoặc human-reviewed annotation | exact same revision; recorded authority; confirmation event | HOST_OBSERVED identity đơn độc; inferred silence |
| reopen | Giữ revision, state → REOPENED | structured explicit-user feedback hoặc human-reviewed annotation | same-problem semantics; exact revision | tự tăng revision |
| revise | CAS current revision/fingerprint; tạo revision N+1 OPEN | explicit contract revision transaction | exact expected current revision + fingerprint; new sanitized capsule | suy revision chỉ từ fingerprint mismatch hoặc feedback label |
| block | State → BLOCKED | runtime deterministic guard hoặc authorized operator/user | typed reason; exact next evidence/action | generic free-text stop |
| abandon | Administrative ABANDONED | explicit user/operator authority theo contract | typed reason và provenance | timeout/silence tự động |

Nếu hệ thống cần REVISED như canonical event/state label, nó phải chỉ xuất hiện trong revise transaction. Old revision được đóng bằng administrative supersession; new revision bắt đầu OPEN. Reporter không được tính transaction đó như successful resolution.

eligible_for_policy là output do runtime derive từ exact binding, authority, timestamp, capsule validity, proof/coverage và cohort rules. Public input v11 phải bị loại bỏ hoặc bị reject nếu caller gửi.

Closed reason-code set ban đầu nên nhỏ và operational: BLOCKED_MISSING_PROBLEM_CONTEXT, BLOCKED_MISSING_EVIDENCE, BLOCKED_MISSING_ORACLE, BLOCKED_AUTHORITY_REQUIRED, BLOCKED_EXTERNAL_DEPENDENCY, BLOCKED_UNSAFE_REPLAY, ABANDONED_EXPLICIT_USER và ABANDONED_AUTHORIZED_OPERATOR. Mọi BLOCKED record phải có exact next_evidence_ref hoặc next_action_code; không mở free-text taxonomy song song.

### 7.3 Timestamp authority

Mỗi event v11 luôn có:

| Field | Owner | Semantics | Dùng cho ordering/TTPR |
|---|---|---|---|
| event_seq | SQLite writer transaction | canonical total append order | Có cho ordering; không phải duration |
| recorded_at | runtime ledger writer | thời điểm durable append theo runtime clock | Có cho ingest/audit timing, không thay event occurrence |
| occurred_at | optional trusted adapter | thời điểm sự kiện ngoài runtime thật sự xảy ra | Chỉ khi attested |
| occurred_at_source | runtime/host adapter enum | nguồn clock | Bắt buộc nếu occurred_at có |
| clock_authority | runtime-derived enum | mức tin cậy và domain | Bắt buộc nếu occurred_at có |
| legacy_event_time | legacy projection | caller-supplied v10 | Không policy, ordering hoặc TTPR |

Hash-material v2 phải canonical-encode event schema version, recorded_at, occurred_at nullable, occurred_at_source và clock_authority. Legacy hash v1 vẫn được verify bằng đúng material cũ; migration không rewrite hashes.

TTPR_wall chỉ dùng occurred_at khi start/end cùng compatible attested wall-clock domain. Nếu thiếu cặp timestamp đó, TTPR_wall là UNKNOWN/right-censored theo preregistered observation rule; recorded_at chỉ cho một metric riêng như ledger-observed capture-to-capture latency, không được đổi tên thành user-wall TTPR. event_seq xác định total order/tie-break, không được biến thành duration. Không trộn hai clock domain trong cùng estimator.

### 7.4 Immutable Problem Revision

V11 thêm problem_revisions trong cùng canonical SQLite:

~~~text
problem_threads
  problem_id PK
  current_revision
  compatibility projection fields

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
  PRIMARY KEY (problem_id, revision)

problem_events
  event_seq PK
  problem_id NULL
  problem_revision NULL
  ...
  FOREIGN KEY (problem_id, problem_revision)
    REFERENCES problem_revisions(problem_id, revision)
~~~

Exact events phải có composite revision reference. AMBIGUOUS và UNLINKED events dùng NULL cho cả problem_id/revision; không dùng sentinel 0, unknown revision hoặc empty synthetic problem. Composite FK cần đi cùng CHECK constraint để enforce hai cột cùng có giá trị khi link_status=EXACT và cùng NULL khi AMBIGUOUS/UNLINKED; chỉ dựa vào nullable SQLite FK là chưa đủ.

Các field current_revision, task_class, engineering_floor và criteria projection ở problem_threads được giữ để compatibility/read speed, nhưng authority thuộc revision row. Reporter phải kiểm projection khớp revision authority.

Reopen giữ nguyên revision. Revise dùng compare-and-swap trên exact current revision và contract fingerprint, sau đó tạo immutable row mới. Fingerprint là integrity/concurrency guard; nó không tự hiểu rằng semantic requirement đã đổi.

### 7.5 Schema và flow

~~~mermaid
flowchart TD
    U[Structured user/human authority] --> O[Explicit PRL operation]
    H[Host turn/trace receipt] --> B[Runtime exact binder]
    C[Sanitized typed contract capsule] --> R[(problem_revisions)]
    O --> B
    B --> E[(problem_events v11)]
    R --> B
    E --> T[(problem_threads projection)]

    R --> W[EOCL RUN / WAVE pinned to exact revision]
    W --> P[Passed proofs on exact WAVE]
    P --> M[Structural criterion-to-proof manifest]
    M --> A{full_problem + floor + checkpoint?}
    A -- no --> G[Progress observation only]
    A -- yes --> V[Idempotent PROVISIONALLY_RESOLVED event]
    V --> F{Explicit outcome}
    F -- confirm --> X[RESOLVED_CONFIRMED]
    F -- same problem fails --> Y[REOPENED, same revision]
    F -- contract changed --> Z[revise CAS, new revision]
    F -- no authority/evidence --> K[BLOCKED with typed next action]
~~~

### 7.6 Additive migration v9/v10 → v11

- Tạo tables/columns/indexes và event/hash schema version mới.
- Không semantic-backfill problem revision, user intent, criteria coverage hoặc trusted timestamps.
- V10 threads nếu có chỉ được materialize revision row khi contract capsule và authority hiện hữu, không dựa vào đoán.
- Current Tools event UNLINKED giữ nguyên legacy/ineligible.
- Verification gồm integrity_check, foreign_key_check, v1/v2 chain verification, projection consistency và idempotent rerun.
- Rollback là ngừng v11 writers/readers mới và giữ additive objects; không rewrite/delete lịch sử.

## 8. Semantic contract capsule và privacy threat model

### 8.1 Capsule tối thiểu

Capsule là typed, immutable, canonical-encoded và tối đa 8 KiB, gồm đúng:

1. objective_summary đã khử dữ liệu nhạy cảm;
2. acceptance_criteria với stable criterion IDs;
3. protected_invariants;
4. constraints;
5. unresolved_conditions.

Không lưu raw prompt, transcript, command output, source content, stack dump đầy đủ, chain-of-thought hoặc arbitrary JSON. Generic run-scoped handoff capsule không phải contract authority; v11 chỉ reuse canonical encoding, hashing, bounded storage và sanitization primitives.

Chỉ problem_revisions giữ một authoritative capsule copy. Event, RUN/WAVE và handoff chỉ giữ opaque contract_ref + fingerprint đã được runtime resolve; không nhân bản semantic text sang các evidence surfaces khác.

Capsule thiếu, hash mismatch hoặc không verify được dẫn tới BLOCKED_MISSING_PROBLEM_CONTEXT. Runtime không được tiếp tục chỉ dựa vào fingerprint vì hash không khôi phục semantics.

### 8.2 Tại sao đây là P0 privacy

Theo retention invariant, gần như mọi file dưới .coding-tools là evidence phải được version-control và có thể commit/push. Vì vậy “local ledger” không phải private scratchpad. Secret/privacy gate phải chạy trước durable write, không phải chỉ trước delivery.

| Threat | Ví dụ | Hậu quả | Guard bắt buộc |
|---|---|---|---|
| Secret ingestion | token/API key trong objective | credential được giữ và phát hành vĩnh viễn | deterministic secret scan; reject; rotate/remediate nếu đã ghi |
| PII/customer data | tên, email, hồ sơ trong criterion | privacy breach qua Git history | redact/abstract; allow opaque authorized reference |
| Source/output exfiltration | paste code/log vào capsule | repo evidence chứa proprietary content | strict allowlist và size/type validation |
| Prompt/CoT retention | raw conversation hoặc reasoning | vượt mục đích, khó xóa | schema không có field tương ứng; reject arbitrary keys |
| Hash-only amnesia | capsule bị mất nhưng fingerprint còn | attempt tiếp tục sai contract | fail closed với missing-context blocker |
| Sanitizer bypass | base64/encoded secret hoặc nested text | laundering vào ledger | normalize/canonical decode limits; entropy/pattern scan; review lane |
| Revision amplification | cùng sensitive payload nhân nhiều revision | tăng blast radius | content-addressed safe capsule hoặc opaque ref; no raw duplication |
| Handoff injection | caller ghi reserved problem/RDP projection | giả authority sau restart | runtime owns reserved keys; strip/reject caller values |

Secret detection không được xử lý bằng cách âm thầm bỏ file khỏi .coding-tools. Phải reject write và yêu cầu objective abstract hoặc opaque reference; nếu secret đã tồn tại, dừng delivery và xử lý/rotate theo retention policy.

## 9. Capture, work origin, full claim và criterion-level proof

### 9.1 Work origin

RUN metadata v11 có:

| work_origin | Semantics | Binding | Denominator |
|---|---|---|---|
| problem | Work nhằm giải một problem revision | exact revision bắt buộc | problem-capture và resolution analysis |
| non_problem | maintenance, read-only analysis, release chores hoặc work không gắn problem | không tạo fake lineage | loại khỏi problem-capture denominator |
| unknown | legacy/shadow chưa phân loại | không policy-eligible | báo missingness riêng |

Trong C2, work_origin chỉ shadow-capture. Sau canary và false-classification review mới bắt buộc cho write-capable RUN.

### 9.2 Resolution claim

V1 chỉ có none hoặc full_problem. Claim phải được ghi trước first mutation, bất biến trong WAVE; nâng từ none lên full_problem phải tạo WAVE mới. Điều này tránh post-hoc chọn denominator sau khi biết kết quả.

none hoặc non_problem chỉ ghi progress/outcome observation; không tạo provisional resolution.

### 9.3 Coverage manifest

Khi full_problem đi vào acceptance, caller/controller phải nộp bounded manifest:

~~~text
criterion_id -> [passed_proof_id, ...]
~~~

Runtime phải xác minh:

- criterion IDs bằng đúng complete set trong immutable revision;
- không có criterion thừa/thiếu/trùng;
- mọi proof tồn tại, PASS, thuộc exact RUN/WAVE và đúng contract/revision identity;
- proof được tạo trước acceptance và chưa invalidated;
- checkpoint là accepted EOCL checkpoint của exact WAVE;
- current thread vẫn trỏ revision/fingerprint dự kiến.

Manifest chứng minh structural completeness và proof provenance. Nó không tự chứng minh semantic adequacy của từng oracle. Semantic controller/human vẫn chịu trách nhiệm chọn criterion và oracle; efficacy evaluation phải đo reopen/correction để phát hiện coverage hình thức.

### 9.4 Engineering floor

| engineering_floor | Provisional gate |
|---|---|
| REQUIRED | accepted EOCL checkpoint + structurally complete criterion-to-passed-proof attribution |
| NOT_APPLICABLE | đúng authority path và complete criterion disposition; không ép code proof |
| UNKNOWN | không policy-eligible provisional closure |

User confirmation và technical trust là hai trục độc lập:

| User confirmation | Engineering trust | Canonical interpretation |
|---|---|---|
| không | không/unknown | unresolved hoặc progress |
| có | không/unknown | confirmation observation có authority, nhưng trusted_resolution=false và RUN không tự accepted |
| không | có | technical full-pass/provisional; confirmation censored |
| có | có | trusted resolution nếu cùng exact revision |

Confirmation không tạo proof, không accept RUN và không override failed engineering floor.

## 10. Reporter v11: resolution không phải disposition

PRL-D phải báo ba clocks:

1. time_to_provisional: authoritative problem start → first valid provisional event;
2. time_to_confirmed_resolution: authoritative start → explicit confirmed resolution;
3. time_to_administrative_disposition: authoritative start → supersede/abandon/other administrative terminal state.

RESOLVED_UNCONFIRMED, SUPERSEDED và ABANDONED không vào successful-resolution numerator và không làm confirmed TTPR ngắn hơn. Silence/unconfirmed là right-censored. Supersede/abandon là competing dispositions.

Wall và active/restricted time phải tách:

- TTPR_wall: elapsed trong một attested compatible wall-clock domain;
- TTPR_active: union của active engineering intervals, không cộng user/external wait;
- missing clock, cross-clock hoặc ambiguous binding được báo UNKNOWN, không thay bằng 0.

Với censoring, mô tả time-to-event có thể dùng risk sets/Kaplan–Meier cho confirmed resolution nhưng phải kiểm và công bố giả định censoring độc lập/non-informative. User silence có thể informative, nên luôn báo outcome table, sensitivity và competing dispositions; competing-risk analysis hoặc cause-specific reporting dùng cho abandonment/supersession. Không tính percentile population khi n nhỏ; báo ordered exact values và confidence interval phù hợp.

## 11. RDP-Shadow: continuity contract, không phải compiler

### 11.1 Vị trí kiến trúc

RDP thuộc WAVE/replan plane hiện có. Nó không là PRL state, không có database riêng, không thêm top-level MCP tool và không overload P4.

Record được tạo cho replacement WAVE sau reopen/failure và trước first write-capable action. Read-only discrimination có thể xảy ra trước record. Runtime bind các authority fields; caller không khai lại problem_id, revision, workspace, base HEAD, worktree fingerprint hoặc tool-contract identity.

### 11.2 Bounded record

RDP-Shadow mang:

- exact_previous_wave_id;
- action_kind: clarify, diagnose, localize, intervene hoặc verify;
- observed_delta_refs do runtime kiểm;
- strategy_fingerprint, hypothesis_fingerprint, oracle_fingerprint, scope_fingerprint;
- discriminator_ref hoặc oracle_ref;
- P4 recommendation_ref khi có;
- resolution_claim_ref trỏ immutable claim của WAVE;
- stop_condition_code;
- delta_kind có type;
- semantic_delta_claim advisory của Sol.

Runtime reuse objective provenance, P4 recommendation, scope/oracle-strength, proof IDs, event identities và replan reason. Không copy các object đó thành representation song song.

Một event/record trên existing orchestration event plane, cùng same-ID/same-bytes idempotency và different-bytes conflict, là đủ. Handoff chỉ chứa runtime-derived projection của exact WAVE decision và invalidation state.

| Field | Authority | Runtime validation |
|---|---|---|
| exact_previous_wave_id | runtime-derived | predecessor tồn tại, cùng RUN/revision và đã quiescent |
| action_kind | caller proposal trong closed enum | clarify, diagnose, localize, intervene hoặc verify |
| observed_delta_refs | runtime-resolved | ref tồn tại, thuộc allowed evidence plane và đúng temporal/revision boundary |
| delta_kind | caller claim trong closed enum | USER_EVIDENCE, TECHNICAL_EVIDENCE, HYPOTHESIS, ORACLE, SCOPE, CONTRACT, TRANSIENT_ENVIRONMENT hoặc AUTHORITY |
| strategy/hypothesis/oracle/scope fingerprints | canonical encoder | integrity/dedup signal, không là semantic truth |
| discriminator_ref/oracle_ref | runtime-resolved | ref tồn tại; applicability vẫn advisory nếu không có deterministic oracle |
| recommendation_ref | runtime-resolved | trỏ P4 hiện hữu, không copy P4 payload |
| resolution_claim_ref | runtime-resolved | trỏ immutable exact-WAVE claim; không copy hoặc nâng trong cùng WAVE |
| stop_condition_code | closed enum | đủ cụ thể để reporter phân loại; blocker phải có next evidence/action |
| semantic_delta_claim | Sol advisory | lưu bounded/sanitized; không dùng làm hard gate |

### 11.3 Safe no-repeat semantics

Trong shadow, một write-capable replan phải dẫn chiếu ít nhất một observed delta:

| Tình huống | Điều kiện retry/replan | Semantic gate |
|---|---|---|
| Causal/mutation failure | material decision delta | theo dõi; chưa hard-block |
| Capacity/timeout/flaky proof | fresh observation và bounded retry | không cần đổi causal hypothesis |
| Job observation/continuation | exact durable Job identity | ngoài gate |
| Idempotent replay | same request/idempotency proof | ngoài gate |
| Operator-requested repeat | explicit operator authority | ghi authority riêng |
| Unsafe/ambiguous mutation | không replay tự động | BLOCKED |
| Không còn discriminator/oracle/authority | typed reason + next exact action/evidence | BLOCKED |

Không dùng numeric EIG, scalar optimizer hoặc hard “hai attempts”. Chỉ sau khi shadow đo false-block/override đủ tốt mới cân nhắc hard-reject exact duplicate mutation replan.

### 11.4 Carry-forward

Qua restart, compaction và handoff, runtime phải mang:

- exact revision capsule/ref;
- previous WAVE decision;
- passed/failed proof refs và invalidation;
- explicit reopen/correction;
- latest stop condition;
- unresolved evidence gap dưới dạng sanitized typed/ref fields.

Handoff không được đọc thread.current_revision để reinterpret attempt cũ. Nó đọc exact composite binding đã pin.

## 12. Goodhart và gaming register

| Gaming vector | Cách game | Runtime signal | Guard | Canary metric |
|---|---|---|---|---|
| Strategy rename | đổi tên cùng hành vi | same scope/oracle/evidence + equivalent mutation footprint | fingerprint/ref comparison; semantic claim advisory | duplicate-mutation review rate |
| Hypothesis paraphrase | thay câu chữ, không thay discriminator | không có new observed ref | chỉ observed_delta_refs được tính | no-evidence replan rate |
| Useless probe | tạo evidence ID rỗng | probe không đổi observable/oracle | typed observation quality + sampled review | probe burden, false gain |
| False problem split | mở thread mới để tránh reopen | same user turn/target/contract overlap | split/merge review; stable problem authority | false-split rate |
| False revision | revise để reset attempt count | new capsule semantically tương đương | CAS + explicit authority + review sample | revision-reversal rate |
| Merge sai | gắn symptom khác vào old problem | corrections/new requirement mismatch | explicit new-problem/revise/reopen instruction | false-merge rate |
| No-claim avoidance | luôn chọn none để tránh denominator | write-capable problem work không full claim | no-claim coverage dashboard; sampled audit | no-claim rate |
| work_origin laundering | chọn non_problem cho fix thật | mutation/objective evidence conflict | runtime shadow classifier + review | origin override rate |
| Clarification abuse | hỏi lại để né quyết định | repeated clarify, no new user datum | burden cap/reporting; operator override | clarification turns/problem |
| Abandonment abuse | abandon để làm TTPR đẹp | disposition spike | competing disposition, excluded from success | abandonment rate |
| Timestamp laundering | backdate/future-date | untrusted clock/source | runtime recorded_at; attest occurred_at | unattested-time rate |
| Provenance laundering | caller chọn HOST/USER | không có adapter receipt | runtime-derived authority only | rejected attestation rate |

Schema freeze trong C4 là Goodhart guard: taxonomy/transition không được đổi giữa cohort để làm metric đẹp. Chỉ privacy, integrity hoặc measurement defect mới hotfix; semantic change tăng version và cohort mới hoặc stratification.

Canary tối thiểu phải báo no-claim coverage, false split/merge, override rate, probe burden, clarification burden, false-stop/false-block và authoritative timestamp/provenance coverage.

## 13. History và playbook governance

| Authority tier | Nguồn | Online effect | Promotion | Demotion |
|---|---|---|---|---|
| Hard invariant | product/safety contract có deterministic oracle | enforce | code review + focused deterministic test | contract revision |
| Candidate playbook | historical technical pattern | advisory/shadow | offline mining + prospective registration | bất kỳ counterevidence đáng kể |
| Confirmed playbook | một exact seed problem revision + nhiều trusted prospective applicability cases | bounded advisory trước | applicability, rebinding, invalidation, verification, negative/reopen history | reopen, negative transfer, drift hoặc kill switch |

Confirmed playbook phải versioned, revocable, có applicability predicate, rebinding rule, invalidation rule, verification oracle, negative history và kill switch. Không tự động inject retrieval vào prompt, không tự chọn strategy và không promote P5/routing.

Process mining chỉ chạy offline trên immutable Tools ledger bằng cách mở rộng reporter hiện có. Output hợp lệ là loop candidates, failure-pattern candidates và playbook candidates. Transition frequency không phải causal effect.

## 14. Đối chiếu khoa học và thực tiễn

Ngày truy cập/kiểm URL: 2026-08-25. LongCLI-Bench và LLMRouterBench dùng bản ACL Anthology; PROV-O là W3C Recommendation; các DOI/publication pages trỏ nguồn publisher/authoritative host. Các URL arXiv là preprint ở revision quan sát ngày truy cập, nên số liệu/version phải được pin lại nếu dùng cho quyết định triển khai sau này.

| Nguồn | Điều nguồn hỗ trợ | Điều nguồn không chứng minh |
|---|---|---|
| [SWE-Interact](https://arxiv.org/abs/2606.30573) | long-horizon SWE cần interaction/outcome qua nhiều turn | schema PRL/RDP cụ thể này tối ưu |
| [LongCLI-Bench](https://aclanthology.org/2026.findings-acl.1497/) | curated long-horizon CLI tasks cho thấy stall phổ biến và interactive guidance có thể hữu ích | self-correction không bao giờ giúp hoặc accepted RUN là resolution |
| [RoadmapBench](https://arxiv.org/abs/2605.15846) | version drift và long-horizon change làm identity/continuity quan trọng | immutable revision tự tăng efficacy |
| [SlopCodeBench v2](https://arxiv.org/abs/2603.24755) | iterative degradation/rework là failure mode cần đo | no-repeat gate chắc chắn giảm lỗi |
| [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/) | routing cần benchmark đa chiều và quality-aware | route availability đủ để bật auto routing |
| [xRouteBench](https://arxiv.org/abs/2608.06867) | learned/user-conditioned routers có thể hơn fixed baseline trong cohort và budget cụ thể | kết quả offline đó đã transfer sang accepted-work cohort của Tools |
| [Agent-system scaling study v3](https://arxiv.org/abs/2512.08296) | topology/coordination có task-dependent cost | thêm multi-agent manager luôn tốt |
| [Beyond Retrieval / QCR](https://arxiv.org/abs/2608.12847) | reuse trajectory cần target-bound bindings, applicability và verification | một universal memory schema hoặc autonomous policy |
| [Beyond Final Scores](https://arxiv.org/abs/2608.13417) | experience reuse có thể giúp và có negative transfer | lịch sử accepted đủ làm confirmed playbook |
| [Process-mining study](https://arxiv.org/abs/2607.04948) | event log có thể sinh workflow/agent candidates | mined path là causal production policy |
| [W3C PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | entity/activity/agent và provenance separation | semantic truth chỉ từ provenance identity |
| [SPACE framework](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/) | productivity là đa chiều; không tối ưu một scalar | một TTPR metric đại diện toàn bộ quality |
| [DevEx framework](https://doi.org/10.1145/3610285) | feedback loops, cognitive load và flow hỗ trợ đo protocol burden | telemetry đơn độc suy ra developer experience |
| [Microsoft study về reopened bugs](https://www.microsoft.com/en-us/research/publication/characterizing-and-predicting-which-bugs-get-reopened/) | survey 358 nhân viên và observational case study cho thấy reopen có nhiều nguyên nhân/factor | mọi reopen đều avoidable agent error hoặc một universal threshold |
| [Kaplan–Meier](https://doi.org/10.1080/01621459.1958.10501452) | time-to-event với right censoring | abandon/supersede là successful event |
| [Cohen’s kappa](https://doi.org/10.1177/001316446002000104) và [Krippendorff’s alpha](https://doi.org/10.1111/j.1468-2958.2004.tb00738.x) | agreement cần hiệu chỉnh chance/missingness phù hợp | agreement cao tự chứng minh construct validity |
| [Controlled online experiments](https://ai.stanford.edu/~ronnyk/2007GuideControlledExperiments.pdf) | control/treatment và guardrails cần cho causal product claim | một natural case chứng minh efficacy |

Kết luận khoa học có mức khiêm tốn: literature ủng hộ problem-level evaluation, provenance, bounded experience reuse, negative-transfer guards và prospective comparison. Không nguồn nào chứng minh Resolution Compiler như brain hoặc hard semantic-repeat gate sẽ cải thiện Tools-Codex-web.

Ba limitation đặc biệt chi phối roadmap: QCR tự mô tả target-bound note như một phép thử reuse hypothesis chứ không phải universal memory format; Beyond Final Scores khảo sát bảy frontier model trên 36 long-horizon AI R&D tasks và quan sát experience có thể giúp hoặc làm lệch quyết định; process-mining study mới là proof-of-concept trên một open-source project kèm exploratory user study. Cả ba đều có external-validity gap lớn so với canonical Tools ledger và không cấp authority cho production policy. Tương tự, LLMRouterBench cho thấy nhiều router không reliably hơn simple baseline trong fixed offline pool, còn xRouteBench là counterevidence rằng learned/user-conditioned routing có thể hữu ích dưới cohort/budget khác; kết luận đúng là “phải chứng minh transfer”, không phải “router không hoạt động”.

## 15. Lộ trình tối ưu Gate 0 và C1–C6

### Gate 0 — Connector truth

Mục tiêu: phân biệt source truth, serialized contract và real target client receipt.

Baseline được giữ theo maintained state là process-bound LIVE_PASS cho connector/process đã được quan sát. Không tự động làm mới receipt chỉ vì viết tài liệu. Tái chứng nhận chỉ khi source/component/contract liên quan đổi, có process boundary làm mất tính hiện hành của receipt, hoặc một authorized acceptance task yêu cầu current live proof.

Deliverables:

1. So current source/component/contract/process identities với exact maintained receipt để quyết định có recertification trigger hay không.
2. Regression serialized stdio tools/list và serialized HTTP tools/list.
3. Xác nhận task_control.action có đúng một enum chứa problem và p5; serialized schema không có allOf.
4. Khi recertification thực sự bị trigger, sau authorized real-client rediscovery gọi read-only problem.get với nonexistent exact ID và kỳ vọng PRL_PROBLEM_NOT_FOUND.
5. Chỉ sửa projection/cache/deployment nếu real target client tái hiện lỗi.

Exit:

- source/serialized regression PASS;
- reuse exact maintained receipt khi identity/boundary chưa đổi, hoặc fresh real-client receipt ở đúng current process khi recertification bị trigger;
- không gọi current source defective khi chỉ thiếu receipt.

Không thực hiện restart/rediscovery trong delivery tài liệu này.

### C1 — V11 authority-safe foundation

Deliverables:

- problem_revisions và typed revision capsule;
- composite nullable event reference;
- event/hash schema v2 + runtime recorded_at + trusted occurred_at;
- observation-only feedback;
- explicit transition-authority matrix;
- runtime-derived eligible_for_policy;
- additive migration và legacy v1 chain compatibility;
- reporter tách resolution/disposition.

Focused proof:

- shadow/unknown confirmation không mutate;
- caller eligibility bị reject/ignore;
- caller timestamp không đổi TTPR;
- v1/v2 chain verify;
- FK và projection consistency;
- unconfirmed/superseded/abandoned không vào confirmed TTPR.

Exit: mechanics deterministic; current legacy event còn nguyên và ineligible.

### C2 — Capture, origin và exact binding

Deliverables:

- auto-fill pending host turn/trace khi caller bỏ trống;
- mismatch fail closed;
- model instructions cho open/observe/confirm/reopen/revise/new-problem;
- resolve exact revision trước first durable RUN write;
- work_origin shadow field;
- handoff đọc pinned revision của attempt.

Focused proof:

- omitted IDs auto-bind exact receipt;
- wrong IDs fail closed;
- non_problem không tạo fake lineage;
- unknown không policy-eligible;
- revise/reopen concurrency dùng CAS;
- restart/handoff giữ old attempt revision.

Exit: exact-binding, false split/merge và origin override có reviewable denominator.

### C3 — Conditional outcome bridge

Deliverables:

- resolution_claim immutable trước mutation;
- full_problem structural criterion-to-passed-proof manifest;
- engineering-floor three-way semantics;
- deterministic/idempotent provisional event;
- recovery chỉ reconcile valid v11 claim;
- explicit confirm/reopen/revise/block nối outcome về exact revision.

Focused proof:

- none không provisional;
- proof từ WAVE/revision khác bị reject;
- thiếu criterion bị reject;
- NOT_APPLICABLE path không bị ép code proof;
- UNKNOWN không policy-eligible;
- confirmation không tạo proof/accept RUN;
- same bridge request không double-event, changed bytes conflict.

Exit: full problem bridge có structural coverage và đúng authority, nhưng chưa claim efficacy.

### C4 — Tools-only natural canary và schema freeze

30–50 events là mechanics calibration range, không phải efficacy threshold hoặc “đủ N là pass”.

Trong cohort:

- freeze schema, taxonomy, state semantics và estimator;
- hotfix chỉ privacy/integrity/measurement defect;
- semantic version change mở cohort mới hoặc stratify;
- dual review sample cho link, transition, capsule privacy và coverage;
- báo event-chain/FK/integrity, exact binding, authoritative confirmation, false merge/split, structural criterion attribution, timestamp authority và confidence interval.

Exit dựa vào preregistered error bounds/critical defects, không chỉ raw N. Zero denominator là UNKNOWN, không PASS.

### C5 — RDP-Shadow

Enrollment:

- second hoặc later write-capable attempt;
- cùng exact problem revision;
- full-resolution work;
- không bắt read-only/simple/non-problem tasks tạo card.

Deliverables:

- one bounded decision record per WAVE;
- runtime-verified observed_delta_refs;
- carry-forward/invalidation trong handoff;
- comparison giữa shadow decision delta và hành vi thực;
- không hard-block, route, chọn strategy hoặc mutate policy.

Focused proof:

- đúng một record cho mỗi enrolled replacement WAVE và phải có trước first write;
- same-ID/same-bytes replay idempotent; changed bytes conflict;
- predecessor, problem và revision do runtime bind;
- wrong, stale hoặc cross-revision observed refs bị reject;
- caller không spoof reserved handoff projection;
- shadow record không đổi route, PRL state, mutation authority hoặc policy;
- restart/handoff giữ exact projection và invalidation state.

Exit: instrumentation coverage tốt, overhead/burden có giới hạn, false-stop/override được review; schema giữ frozen trong cohort.

### C6 — Controlled convergence evaluation

Unit of analysis: problem_revision.

Adaptive fixture bắt buộc:

~~~text
accepted technical attempt
  → explicit same-problem reopen
  → replacement write-capable WAVE
  → exact prior outcome/proof referenced
  → at least one fresh observed discriminator/evidence reference
  → no exact failed mutation decision replay
~~~

Prospective/control comparison đo correctness, low-information WAVE, reopen/rework, wall/active TTPR, protocol overhead, clarification/probe burden và false block.

Chỉ sau kết quả này mới xem xét:

- hard-reject exact duplicate mutation replan;
- candidate → confirmed playbook;
- bất kỳ routing/P5 promotion nào.

## 16. Metrics và định nghĩa

### 16.1 Primary outcome metrics

Mọi rate phụ thuộc user outcome phải được định nghĩa tại follow-up horizon H đã preregister. Revision chưa đủ H được báo immature và không trộn vào denominator của fixed-horizon rate; song song, time-to-event giữ chúng trong risk set theo đúng censoring rule.

| Metric | Numerator | Denominator | Censoring/exclusion |
|---|---|---|---|
| First Revision Resolution Rate at H | revision trusted-resolved ở first full attempt trước H | eligible revisions đã mature tới H | revised/superseded báo riêng |
| Authoritative Confirmed Resolution Rate at H | exact explicit-user/human confirmed revisions trước H | eligible revisions đã mature tới H | silence/immature báo riêng |
| Technical Full-Pass Rate | full claim đạt floor + complete valid coverage | eligible full claims | N/A floor stratified |
| Trusted Resolution Rate | confirmed và technical trust cùng exact revision | eligible revisions | missing one axis không success |
| Reopen rate at H | same-revision authoritative reopen trước H | provisionally/confirmed revisions đã mature tới H | new requirement không là reopen |
| Avoidable correction rate | reviewed avoidable correction | eligible correction events | unknown giữ unknown |
| Attempts per resolved revision | exact primary problem attempts | trusted-resolved revisions | secondary allocation không double-count |
| TTPR_wall | attested elapsed to confirmed | confirmed + censored risk set | competing disposition riêng |
| TTPR_active | union active stage intervals | compatible clock-domain revisions | incomplete timing unknown |

### 16.2 Mechanics và burden metrics

- exact revision binding coverage;
- problem-capture coverage theo work_origin;
- structurally complete criterion-to-proof attribution rate;
- outcome-observation coverage;
- authoritative timestamp coverage;
- event-chain/FK/projection integrity;
- no-claim rate;
- false split/merge rate;
- origin/transition override rate;
- RDP instrumentation coverage;
- protocol bytes, latency và authoring burden;
- clarification turns/problem và probes/problem;
- false-stop/false-block rate;
- duplicate mutation replan rate.

Mọi metric phải ghi snapshot/cohort window, Git HEAD, schema version, filters, missingness, censoring và sample size. Internal cost estimates không được trình bày như provider billing.

### 16.3 Reliability

Link/origin/transition/coverage review cần codebook đóng băng, independent double annotation trên sample và agreement report. Dùng Cohen’s kappa cho hai rater/categorical complete data hoặc Krippendorff’s alpha khi nhiều rater/missing data; luôn kèm raw agreement và class prevalence. Agreement không thay thế construct validity.

## 17. Preregistered evaluation skeleton

Trước C4/C6 cần khóa:

- population và exclusion;
- primary outcome duy nhất hoặc multiplicity handling;
- quality/security/authority non-inferiority floors;
- minimum detectable effect và power assumptions;
- censoring/competing-disposition rules;
- analysis clock domains;
- protocol overhead và user-burden guardrails;
- false-block ceiling;
- schema/taxonomy version;
- stop/harm conditions;
- treatment allocation và contamination handling.

Control là PRL v11 không RDP enforcement; treatment là RDP-Shadow/selected bounded gate. Không dùng historical accepted-only tail làm control effect estimate.

## 18. Definition of Done bốn tầng

### Tầng 1 — Mechanics

- v11 schema/authority/timestamp/binding/idempotency đúng;
- capsule privacy gate fail closed;
- full claim coverage structurally complete;
- reporter tách provisional/confirmed/disposition;
- focused regressions, chain, FK và integrity PASS.

### Tầng 2 — Adaptive integration

Fixture reopen bắt replacement decision mang exact prior evidence/outcome và fresh observed delta; không replay exact failed mutation decision. Restart/compaction/handoff không làm mất revision hoặc invalidation.

### Tầng 3 — Natural-system demonstration

Một problem thật của Tools đi qua restart hoặc handoff, technical attempt, authoritative reopen và cuối cùng trusted resolution hoặc explicit typed blocker mà không dựng lại transcript. Đây chỉ là integration demonstration.

### Tầng 4 — Efficacy

Prospective/control evidence cho thấy giảm useless replan/rework mà không giảm correctness/quality/security/authority hoặc tăng TTPR/user burden vượt ngưỡng preregistered.

Một natural case không đạt tầng 4.

## 19. Stop conditions và kill switches

Dừng rollout hoặc demote RDP/playbook khi:

- secret/privacy material lọt vào durable capsule;
- state mutation xảy ra từ shadow/unknown authority;
- timestamp không attested đi vào TTPR/policy;
- false split/merge vượt threshold;
- protocol làm tăng false block, clarification burden hoặc TTPR quá guardrail;
- reopen/counterevidence cho thấy playbook gây negative transfer;
- schema/taxonomy drift trong cohort không được version;
- connector truth khác source regression mà chưa xác định projection/cache/deployment layer.

Khi BLOCKED, record phải có typed reason và exact next evidence/action. “Không đủ thông tin” không đủ cụ thể.

## 20. Những việc cố ý không làm

- Không tạo tool MCP thứ chín.
- Không tạo Resolution Compiler service, planner, brain hoặc policy engine.
- Không tạo second database, vector DB hoặc autonomous retrieval injection.
- Không auto-route Mini/Luna/Terra/Sol; execution_route=auto vẫn evidence-gated/fail-closed.
- Không sửa P4/P5/A2 để phục vụ RDP khi primitives hiện tại đủ.
- Không semantic-backfill lịch sử.
- Không dùng HR làm gate.
- Không xem 30–50 hoặc 100 là scientific law.
- Không tối ưu một scalar “expected remaining work”.
- Không tuyên bố eventual convergence.

## 21. Implementation work packages và thứ tự file-level dự kiến

Đây là kế hoạch cho các turn triển khai sau; delivery hiện tại không sửa các file này.

| Tranche | Primary surfaces dự kiến | Test surfaces | Dependency |
|---|---|---|---|
| Gate 0 | tool_schema.py, protocol/transport serialization nếu lỗi tái hiện | test_problem_lineage.py, stdio/HTTP tools-list tests | none |
| C1 schema/authority | problem_lineage.py, problem_lineage_control.py, tool_schema.py | test_problem_lineage.py, economics tests | Gate 0 |
| C1 reporter | problem_resolution_economics.py, reporter script | test_problem_resolution_economics.py | schema semantics |
| C2 capture/binding | server/control/coordination integration | lineage + host-turn + handoff tests | C1 |
| C3 bridge | orchestration control/ledger + proof integration | lineage, proof, acceptance/recovery tests | C2 |
| C4 canary | reporter/docs only trừ defects | immutable snapshot/reliability checks | C3 |
| C5 RDP-Shadow | existing WAVE metadata/event and handoff surfaces | orchestration/replan/handoff tests | C4 |
| C6 evaluation | offline reporter/research protocol | analysis fixtures | C5 |

Mỗi tranche phải là smallest coherent change, chạy focused tests trước và kết thúc bằng operator-visible checkpoint. Source, controlled runtime và released state phải báo riêng.

## 22. Rủi ro còn lại

1. Semantic adequacy vẫn không hoàn toàn machine-verifiable; stable criteria và proof mapping chỉ giảm ambiguity.
2. User confirmation có selection bias và silence censoring.
3. Problem split/merge là construct khó, cần review chứ không chỉ rule.
4. RDP có thể tăng cognitive/protocol burden lớn hơn benefit.
5. Historical workflow có confounding theo task difficulty, model, source state và tool maturity.
6. Một schema quá giàu sẽ trở thành planning prose dạng JSON; bounded allowlist và canary burden phải chặn điều này.
7. Playbook đúng ở một revision class có thể negative-transfer sang class gần giống.
8. Ledger tiếp tục drift; mọi nghiên cứu phải tạo snapshot receipt mới.

## 23. Final recommendation

Cho phép triển khai Gate 0 → C4 như closure tranche duy nhất của PRL v11. Sau khi mechanics và Tools-only natural capture đạt gate, cho phép C5 RDP-Shadow trên đúng second/write-capable/full-resolution attempts. Chưa cho phép hard semantic-repeat rejection, playbook promotion, process-mined policy, routing change hoặc Resolution Compiler subsystem.

Điểm dừng sản phẩm rõ ràng:

> Tools-Codex-web giữ được exact immutable problem contract, pin đúng revision vào từng attempt, chỉ provisional-resolve khi full claim có structurally complete criterion-to-passed-proof attribution và đúng engineering floor, nhận explicit confirmation/reopen/revise qua đúng authority, đo resolution tách khỏi administrative disposition, và buộc replan có khả năng ghi mang forward exact prior outcome cùng observed decision delta — qua restart/handoff mà không dựng lại transcript.

Sau điểm đó, câu hỏi không còn là “có xây thêm framework không”, mà là một câu hỏi thực nghiệm: RDP có giảm rework/low-information waves dưới quality và burden floors hay không.

## 24. Validation checklist cho delivery tài liệu này

- [x] Chuẩn hóa ba attachment duy nhất và xác minh hai cặp duplicate byte-for-byte.
- [x] Chụp immutable ledger snapshot mới với HEAD, UTC/local timestamp, SHA-256, filters và censoring.
- [x] Đối chiếu transition, timestamp, revision, proof, reporter, replan, P4 và handoff với source.
- [x] Có claim matrix, source anchors, authority matrix, schema/flow, privacy threat model, Goodhart register, staged roadmap, metrics và scientific limitations.
- [x] Kiểm tra external link reachability.
- [x] Kiểm tra local Markdown anchors.
- [x] git diff --check, final diff review và status.
- [x] Xác nhận không source/runtime/migration/restart/commit/push/release/deploy.

Validation receipt: 18 external targets được kiểm ngày 2026-08-25; 13 trả HTTP 200, bốn authoritative publisher/standard endpoints resolve rồi từ chối automated client bằng 403, và Cohen DOI resolve 302 tới SAGE trước khi Windows curl gặp TLS receive failure. Không target nào trả 404. Cả 23 local file/line anchors tồn tại. Tracked git diff --check PASS; no-index scan của file mới không có whitespace diagnostic, chỉ có Git for Windows LF→CRLF warning. Report có newline cuối file và zero trailing-whitespace match.
