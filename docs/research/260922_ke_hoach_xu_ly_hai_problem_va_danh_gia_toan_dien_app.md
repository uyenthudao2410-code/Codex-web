# Kế hoạch xử lý hai Problem và đánh giá toàn diện khả năng theo đuổi mục tiêu của app

Ngày lập: **22/09/2026 — Asia/Saigon (UTC+07)**. Repository: `E:\DEV\Codex-web`.

Trạng thái tài liệu: **RECOVERY REHEARSAL ACTIVE — người dùng đã cấp controlled recovery; backup/candidate cô lập đã tạo, canonical chưa thay, candidate chưa activation-eligible**.

> **Cập nhật mới nhất 22/09 khoảng 19:46 +07:** verifier đã có pointer-only projection plan và clone-only apply probe; candidate tail `317→320` an toàn về invariant nhưng `can_apply=false`, xem **16.24**. Canonical hash vẫn nguyên; candidate chưa activation-eligible; goal ACTIVE, chưa complete.

## 0. Kết luận điều hành

App có nền tảng thực thi, quyền, continuation, recovery và phân tích khá sâu, nhưng khoảng cách lớn nhất hiện nay nằm ở **tính liên tục của bằng chứng, sự thống nhất source–package–runtime, và kết quả sử dụng đầu-cuối**. Không đủ căn cứ nói app đã theo đuổi một Goal đến kết quả tin cậy mà người dùng không phải liên tục chuyển tin/nhắc tiếp tục.

Hướng được khuyến nghị là **hội tụ trên kiến trúc hiện có, ưu tiên đường central đã được sản phẩm lựa chọn**, không viết lại Goal Engine, không thêm database tri thức có quyền điều hành, không tăng routing tự động hoặc nới guard để làm xanh status. Cần đối chiếu contract của Problem boot cũ với role central trước khi dùng proof mới; không tự sửa tiêu chí để làm closure dễ hơn.

Thứ tự quyết định:

1. Khóa baseline và đối soát ba RUN/checkpoint còn trong report nhưng không có trong canonical hiện tại.
2. Chốt exact Problem Revision, mode sử dụng, owner, package và điều kiện nghiệm thu; giữ hai Problem riêng.
3. Sửa P1/P2 handoff và oracle; tận dụng các sửa đổi source/candidate đã có, tránh làm lại.
4. Đưa đúng package/runtime/epoch/central route về trạng thái dùng được bằng một activation được cấp quyền và có postflight đầy đủ.
5. Kiểm chứng continuation bằng worker/model thật trong cửa sổ không có controller can thiệp; giữ nguyên ngân sách, quyền và chốt nghiệm thu.
6. Chạy recovery/reboot/hai máy và natural-use, nối exact criterion coverage và independent outcome.
7. Sau một Problem tự nhiên, thu 5–10 Problem để hiệu chỉnh phương pháp; chỉ mở nghiên cứu P5 A/A rồi A/B khi dữ liệu và quyền đủ. Không dùng cohort nhỏ như bằng chứng thống kê xác nhận hiệu quả.

**Không công bố một phần trăm hoàn thiện chung.** Một số phần đã có source/test hoặc candidate package, nhưng còn thiếu live, outcome và lịch sử canonical. Gộp các mức này thành một điểm số sẽ che đúng các rủi ro cần giải quyết.

### 0.1. Phạm vi và giới hạn của lần đánh giá

- Đã đọc source/test/docs liên quan, dữ liệu canonical qua snapshot nhất quán và các projection. Đã đối chiếu trạng thái runtime trong phiên audit liền trước ngày 22/09; thời điểm từng nguồn được ghi riêng.
- Đánh giá toàn diện **theo mục tiêu sản phẩm và các ranh giới nghiệm thu**, không phải pentest, kiểm thử mọi dòng code, benchmark tải, kiểm toán nhà cung cấp hay UAT toàn bộ giao diện.
- Không sửa source, không mở RUN/Goal/experiment, không cấp consent, không accept/reconcile ledger, không restart/kill/reboot, không đổi IAM/credential/policy, không commit/push/install/deploy.
- Chỉ file Markdown này được tạo trong repository. Các kế hoạch, report lịch sử và dirty work của tác vụ khác không bị sửa.
- Số liệu thiếu là `UNKNOWN`; sự vắng mặt trong snapshot hiện tại không chứng minh sự kiện chưa từng xảy ra ở bất kỳ máy/ledger nào.

## 1. Nguồn chứng cứ và baseline

### 1.1. Hệ quy chiếu

| Mã | Nguồn | Cửa sổ/identity | Dùng để kết luận | Không dùng thay cho |
| --- | --- | --- | --- | --- |
| E01 | Git/source checkout | Quan sát 22/09 16:47, `main@77d73471dc896a1f1ac189b2df46529276481552`; worktree dirty | Source có gì, delta thuộc ai | Package hoặc loaded runtime |
| E02 | `.coding-tools/orchestration/ledger.sqlite3` qua SQLite Backup API | Snapshot 22/09 **16:38:44.074**; causal event cuối 15/09 **18:21:44.082** | Problem/Revision, RUN/WAVE, checkpoint, authority và lịch sử trong bản hiện có | Các report ngoài ledger hoặc state trên Ubuntu |
| E03 | `.coding-tools/performance.json` | Quan sát riêng, hash/cửa sổ ở mục 3 | Tool/error/cache/search/routing/timing projection | Billing, causal outcome hoặc full-history percentiles |
| E04 | `.coding-tools/task-history.json`, `task-state.json`, contextual projections | Dữ liệu rolling/archived có freshness riêng | Continuity và UI diagnostics | Canonical causal ordering |
| E05 | Official Recovery IPC, `dev:status`, Scheduled Task và OS process read | 22/09 **16:33–16:38** | Process, role, loaded/disk revision, epoch/readiness tại thời điểm đọc | Reboot acceptance, real-client task hoặc remote production |
| E06 | Generated run summaries và pre-reboot receipt | Embedded event time ngày 15/09, không phải filesystem mtime | Lịch sử report, exact ID cần đối soát | Acceptance canonical nếu row/chain không có |
| E07 | Maintained docs và candidate setup plan | Có checkpoint tới 22/09; mỗi checkpoint có fingerprint riêng | Tiến triển được tài liệu ghi nhận, tránh làm lại | Live proof độc lập của phiên này |
| E08 | Golden HR / EGRI research | Calibration lịch sử | Bài học, giả thuyết và thiết kế phép đo | Outcome mới, quyền HR hoặc causal ROI |

Snapshot E02 dùng để tái kiểm tra: `E:\Caches\Temp\codex-prl-readonly-audit-3vu2z_az\ledger.sqlite3`, kích thước `97,509,376` byte, schema `12`, mở `immutable=1`, `query_only=ON`.

- Physical SHA-256: `c894f57ebdb0c1c7995cb5dc315edbc39a317d6143afe2d1cda1184b9034f39a`.
- Logical SHA-256: `06351abf428ef9c854c2f0a8f8bf09b59e52632630eb8ab7dd9b603482db5ffb`.
- `integrity_check=ok`, foreign-key violations `0`; reporter chính thức ghi `mutated_canonical_ledger=false`.
- Snapshot tạm là vật chứng audit, không phải DB để thay canonical. Hash này không được dùng làm preflight cho một mutation tương lai.

SQLite Backup API cung cấp bản sao nhất quán trong khi nguồn có thể đang hoạt động. Điều đó bảo đảm tính nhất quán của **bản được chụp**, không chứng minh bản đó chứa mọi sự kiện từng phát sinh ở các nhánh lịch sử khác. Nguồn phương pháp: [SQLite Online Backup API](https://www.sqlite.org/backup.html).

Git đầu phiên: HEAD bằng `origin/main` **lưu cục bộ**, chưa fetch; 40 tracked changes và 25 untracked entries, không staged/unmerged. Không coi source root scanner PASS là Git clean. Dirty setup/UI/control-plane/icon/evidence phải được phân loại owner trước bất kỳ implementation/delivery nào.

### 1.2. Hai hợp đồng riêng

| Problem chính xác | Revision | Tiêu chí | Canonical state | RUN trong snapshot | Kết luận |
| --- | --- | ---: | --- | --- | --- |
| `prl-22e670302757c9b7663170e226ed7c26` | 1 | 12: C01–C12 | OPEN; `closed_at=null` | 63 = 44 accepted + 16 aborted + 3 active | Boot/host/recovery/reboot chưa closure |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` | 2 | 18: 4 continuity/telemetry + BG01–BG14 | OPEN; `closed_at=null` | 39 = 16 accepted + 10 aborted + 13 active | Durable Goal/no-manual-nudge chưa closure |

18 tiêu chí của revision 2 đã được đọc trực tiếp từ `problem_revisions.typed_contract_capsule`: **BG01–BG14 thực sự đã nằm trong canonical revision 2**, không còn chỉ là đề xuất trong file kế hoạch. Provisional resolution của revision 1 cũ không được kế thừa sang revision 2.

Trong metadata WAVE/checkpoint của hai current revision: số trường `coverage_manifest`, `criterion_dispositions`, `problem_outcome_claim` có nội dung đều **0**. Không có provisional/confirmed resolution event cho hai current revision. Đây là **thiếu proof linking**, không phải kết luận source làm được 0/30 tiêu chí.

### 1.3. Chênh lệch lịch sử cần xử lý trước closure

| Generated report | Checkpoint được ghi | Canonical snapshot hiện tại |
| --- | --- | --- |
| `run-dcb539e0e1694bc1bb29eed2b2e07f8b`: safe canary arming | `8d10f27638e2498cba80edf0bcbe77ce` | Không có RUN tương ứng |
| `run-d01a5dce50c846fc8e13673cdfc8b3b3`: packaged cold-start | `6fb3de41a26349f5995a6a2bd92d82f2` | Không có RUN/checkpoint tương ứng |
| `run-b194ab1e311e42efa1dd0614ca245037`: pre-reboot arming | `c8f32a66c7714204bcdd64162dc20ee1` | Không có RUN/checkpoint tương ứng |

Canonical `events` có 25,694 row, max seq `59694`, event cuối `2026-09-15T11:21:44.082Z`; checkpoint cuối `11:21:42.754Z`. Các report trên có event muộn hơn, gồm seq `59702/59734/59815`. Ba accepted report ngoài canonical khớp chênh lệch **63→66 RUN, 44→47 accepted** của báo cáo cũ. Đây không đơn thuần là thay đổi số đếm do runtime chạy tiếp.

Không phủ nhận packaged spawn lịch sử, nhưng không tái cấp authority từ report. Nguyên nhân khác biệt ledger chưa xác lập. Integrity/FK PASS không chứng minh lịch sử đầy đủ. Phải phân biệt: sai ledger target, snapshot cũ, branch/delivery divergence, archival omission, hoặc thiếu provenance khác; chưa gán nguyên nhân nào là fact.

### 1.4. Runtime và candidate

| Thành phần | E05 đã quan sát | Ý nghĩa |
| --- | --- | --- |
| Recovery Host | Healthy, PID 14300, `development`, đúng checkout | Host sống; không phải packaged acceptance host 1.0.0 trong report cũ |
| Role | `central_executor` | Không dùng local Tunnel xanh làm oracle duy nhất |
| MCP/native | Cả hai true; MCP running=disk `396e1692…` | MCP local sống và revision khớp tại thời điểm đọc |
| Recovery Host revision | Running `80f71aa1…`, disk `ec6c20ea…`, update pending | Toàn hệ thống chưa source-continuous |
| Epoch | `activation-mucbq2r3-51dffc08603d42b6c30e1413ec68862f`; durable FAILED, `ACTIVATION_REQUEST_EXPIRED` | Projection UPDATE_INCOMPLETE; admission đóng; không sửa record thành READY |
| Readiness | localReady/centralConnected/authorityReady/fullyReady đều false | Chưa usable đầu-cuối |
| Connector/local Tunnel | CHANGED_NEEDS_DISCOVERY; rediscovered false; Tunnel false | Cần oracle theo role; không tự kết luận local Tunnel hỏng trong central mode |
| Supervisor | Exact Scheduled Task không tồn tại | Không có current installed-autostart proof |
| Startup settings | `startWithWindows=false`, `autoStartServices=false` | Không được tự bật chỉ vì muốn auto-recovery PASS |

Source `runtimeReadiness()` tách `central_executor` và `direct_legacy`: central cần localReady + centralConnected + authorityReady, không giả local Tunnel. MCP revision khớp không loại trừ Host drift hoặc epoch hết hạn. Epoch expired là lỗi được quan sát; chưa chứng minh Host drift là nguyên nhân làm epoch đó expired.

Candidate setup đang có nhiều proof mới trong [kế hoạch thiết lập 22/09](../260922_SYSTEM_SETUP_SIMPLIFICATION_PLAN.md), gồm source/UI checks, candidate resource/smoke và Control Plane artifact portability. Đây là **documented candidate evidence**, có cả failed/rebuilt attempt; không gán tất cả vào một fingerprint, không dùng các tổng test 939/943/944 của những lượt khác nhau làm một mẫu tăng trưởng. Chưa cài candidate thay runtime hiện tại trong audit này. Tái dùng exact candidate còn khớp bytes; nếu drift thì chỉ chạy lại phần bị invalidated.

## 2. Mục tiêu app và tiêu chuẩn thành công

Mục tiêu vận hành rút từ [ROADMAP](../ROADMAP.md), [shared-account status](../SHARED_ACCOUNT_WORKSPACE_STATUS.md) và hai canonical capsule:

1. Người dùng chọn đúng workspace bằng binding; client cùng account điều khiển đúng node/workspace, không copy credential/context hoặc đổi target ngầm.
2. Một Goal được giao một lần, có scope/ngân sách; runtime thực sự gọi lượt worker tiếp theo khi hợp lệ, không biến người dùng thành người chuyển báo cáo.
3. Hệ thống thực thi an toàn qua lỗi/reconnect/restart được phép: không duplicate effect, không chạy sai revision/owner, không vượt Stop/revoke.
4. Kết quả được kiểm bằng oracle đúng tầng; technical acceptance và independent user outcome khác nhau.
5. Mỗi lần xử lý để lại bằng chứng có thể tái sử dụng, giúp giảm rework/TTAR/TTPR và công vận hành; không chỉ tăng lượng log hoặc số test.

| Mức đầy đủ | Điều kiện | Hiện trạng tổng hợp |
| --- | --- | --- |
| Kỹ thuật dùng được | Correct target, exact loaded bytes, hợp lệ epoch/route/policy, thực thi/read/write/stop/receipt đúng | Có source/focused/candidate proof; E05 chưa đủ live readiness |
| Hiệu quả công việc thực | Một Goal natural end-to-end, no unnecessary nudge/relay, independent outcome, sau đó cohort đại diện | Hai current revision chưa có coverage/outcome đủ; không suy từ accepted RUN |
| Sẵn sàng phát hành/vận hành | Frozen artifact, installed/reboot/multi-client/restore/retention/secret/OS proof, owner approval và destination cụ thể | Chưa đủ bằng chứng; không được dùng packaged smoke thay các gate còn lại |

North Star: **giảm tổn thất kinh tế để đạt kết quả được nghiệm thu dưới sàn chất lượng, quyền, bảo mật và đúng dữ liệu cố định**. Ưu tiên theo thứ tự: quality/safety → kết quả đúng ngay từ lần đầu → thời gian đến outcome → tài nguyên/chi phí có quan sát → công người vận hành → độ đơn giản. Không tối ưu số tool call, LOC hay tên model riêng lẻ.

## 3. Phân tích chỉ số và chất lượng dữ liệu

### 3.1. Population và cửa sổ: không join mù

E02 causal events thuộc `2026-08-22T07:01:58.223Z`–`2026-09-15T11:21:44.082Z`. Các bảng RUN/checkpoint có thể bao gồm lifecycle khởi tạo trước cửa sổ event hiện còn; không gán toàn bộ history app vào population này.

E03 performance version 6 được đọc và hash xác minh lại lúc **22/09 16:58**:

- SHA-256: `417c63ba0c8f57486eeb80cba30c8393cb09f0bbcb42bbd1b2dd0dcd5340659c`.
- `last_finished_at=2026-09-22T06:59:48.707Z` (13:59:48 +07).
- Run-metric timestamps quan sát được từ `2026-09-14T19:48:58.745Z` tới `2026-09-22T06:59:38.432Z`; đây **không chứng minh start time của toàn bộ cumulative counters**.
- `recent` chỉ 100 records, từ `2026-09-15T11:16:32.954Z` tới `2026-09-22T06:59:48.707Z`.
- Task-history timestamp mới nhất đọc được `2026-08-24T17:41:15.012Z`; task-state `2026-09-09T12:23:33.868Z`. Contextual projections có population riêng; root task-state không đại diện toàn workspace.

Performance có observation ngày 22/09 nhưng canonical causal events chỉ tới 15/09. Có thể có hoạt động ngoài RUN hoặc nguồn/window khác; **không suy từ đó rằng mọi tool call bị mất ledger**. Cần exact correlation để xác định phần nào thực sự thiếu. Tỷ lệ chỉ mô tả tập đã thấy, không phải SLO uptime hay tỷ lệ thành công toàn sản phẩm.

### 3.2. Tool/error, idempotency và output

| Chỉ số E03 | Giá trị | Diễn giải có thể bảo vệ | Hướng xử lý |
| --- | ---: | --- | --- |
| Tool calls / errors | 2,689 / 373 = **13.87%** | Tỷ lệ error envelope trong cumulative projection, không đồng nghĩa bug rate | Phân lỗi theo cause và work origin trước ưu tiên |
| Runtime errors | 137/373 = 36.73% | Nhóm lớn nhất, gồm gate/runtime conditions | Role-aware diagnosis, source/epoch continuity và actionable next step |
| Validation errors | 123/373 = 32.98% | Có thể gồm lỗi input/negative tests; chưa gán toàn bộ là defect | Nhóm top typed codes và input schema delta, thêm preflight hints |
| Authority denied | 61/373 = 16.35% | Có thể là guard hoạt động đúng | Cải thiện hướng dẫn authority; không hạ guard |
| Internal / not-found | 22/373 = 5.90%; 14/373 = 3.75% | Cần exact error/cause/source before fix | Ưu tiên internal tái hiện trong natural workload |
| User-blocked / idempotency / unknown | 11 / 4 / 1 | Lần lượt 2.95% / 1.07% / 0.27% trên errors | Giữ typed causes; unknown cần phân loại, không đổi verdict |
| RUN-bound calls | 1,407/2,689 = **52.36%** | Chỉ phần đó có run_metrics; unbound không tự là missing causal record | Ghi work_origin/non_problem/correlation để giải thích phần còn lại |
| RUN-bound errors | 240/373 = 64.34% | Cửa sổ/tập khác full tool population | Không chia 240 cho 2,689 để tạo task error KPI |
| Required idempotency key | 152/152 = **100%** trong policy epoch | Key presence đạt; không chứng minh exactly-once effect | Giữ; nghiệm thu lost-ACK/duplicate-delivery bằng journal |
| Eligible key presence | 559/1,021 = 54.75% | Includes optional cases, không phải compliance failure | Chỉ mở rộng automatic key khi semantics/idempotency proof cho phép |
| Deduplicated calls | 2 | Quan sát loại call lặp, không phải toàn bộ duplicate-effect metric | Tách call dedup và side-effect replay safety |
| Response / model-visible bytes | 145,894,909 / 5,227,254 | Visible chiếm **3.58%** response; hiệu ứng chiếu/output bound | Không quy ra token tiết kiệm/tiền hoặc chứng minh không mất evidence |
| Tail/pagination evidence | 7 samples; 0 truncated/offered/reads/stale trong bộ counter này | Mẫu ít, chưa stress overflow/follow-up | Kiểm boundary đúng case; không thêm pagination framework vì số 0 |

Runtime + validation + authority-denied là 321/373 = **86.06% error envelopes**. Đây là căn cứ ưu tiên **làm rõ precondition/role/source/authority và taxonomy**, không phải quyền bỏ validation/authority để giảm tỷ lệ lỗi.

### 3.3. Timing: đã thấy gì, chưa đo được gì

| Population | Chỉ số | Giá trị | Caveat |
| --- | --- | ---: | --- |
| Cumulative E03 | `local_execution_ms` | 9,094,340 ≈ 2.53 giờ | Tổng cộng tool durations, có thể overlap; không phải elapsed task time |
| Cumulative E03 | `estimated_wait_ms` | 26,070,284 ≈ 7.24 giờ | Inter-tool gaps; gồm user/thinking/approval/idle; không tự là thời gian lãng phí |
| Bounded tail n=100 | Duration nearest-rank p50/p95 | 890 / 13,203 ms | Chỉ tail, không phải toàn kỳ hay latency SLO |
| Bounded tail n=100 | Wait-before p50/p95 | 7,766 / 30,266 ms | Không gọi đây là provider latency |
| Phase sample n=123 | total/workspace/localization/materialization sums | 464,050 / 51,049 / 164,497 / 1,399 ms | Các phase không phải partition exhaustive; không ép cộng bằng total |

Tail gồm task_control 47, exec_command 23, workspace_context 18, agent_workflow 9, workspace_preheat 3; tail errors 15/100. Tool mix này khác một natural coding population, nên không dùng nó để kết luận người dùng viết feature mất trung bình bao lâu.

`estimated_wait_ms / (estimated_wait_ms + local_execution_ms) ≈ 74.14%` chỉ là tỷ trọng của **hai bộ đếm cộng dồn**, không phải “74% thời gian có thể tiết kiệm”. Chưa có phase join/censoring/operator-observation đủ để tính TTAR/TTPR hoặc avoidable wait cho hai current Problem.

Metric schema cần ghi temporality, start/end và reset epoch. Cumulative sum, delta và histogram có semantics khác; percentile cần population/histogram/distribution thích hợp. Không lấy mean/tổng suy ra p95. Nguồn phương pháp: [OpenTelemetry Metrics Data Model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/).

### 3.4. Cache, localization và route

| Surface | Đã đo | Nhận định | Quyết định |
| --- | --- | --- | --- |
| E03 proof cache | 117 eligible, 0 hit, 117 miss; cold 104 (88.89%), fingerprint changed 13 (11.11%) | Chưa có proof reuse trong window này; đa số miss là cold | Đầu tiên kiểm repeated-proof opportunity và 13 invalidations; không cache unsafe |
| E02 proofs | 942 = 813 passed + 129 failed; cache hit 5/miss 937 | Tỷ lệ pass 86.31%, hit 0.53% trên proof rows lịch sử | Không mâu thuẫn với 0/117 E03 vì khác window/eligibility; không gọi pass rate là outcome rate |
| Localization E03 | 55 samples; 262 attempted queries; handled 0; fallback 262; available samples 0 | Không có semantic success evidence trong tập này | Một provider-bound canary, record reason/lang/workspace/fingerprint; không bật LSP đại trà trước availability proof |
| Route E02 | 613 selections: deterministic→deterministic 585; auto→deterministic 9; sol_xhigh→sol_xhigh 15; luna 2; mini 2 | 9/9 auto fail-closed đúng; mỗi selection không phải unique task/paid inference | Giữ auto deterministic; không chọn winner từ n=2/15 không paired |
| Execution mode E03 | 1,407 mode records; 1,378 mcp_only, 22 auto, 7 deep_single_lane | Mode denominator khác route-resolved 894 records | Không nhập execution mode và model route thành cùng KPI |

Cache miss do input fingerprint thay đổi có thể hoàn toàn đúng. Chỉ sửa fingerprint nếu discriminator chứng minh thành phần không phải input causal đang làm invalidation (ví dụ telemetry volatile lọt vào source identity). Không tăng hit rate bằng bỏ source/toolchain/oracle/authority inputs. Semantic fallback phải giữ hoạt động đúng khi provider unavailable; tối ưu này không được chặn technical canary không cần LSP.

### 3.5. Tri thức, coverage và xác nhận kết quả

| E02 object/event | Số lượng | Ý nghĩa và giới hạn |
| --- | ---: | --- |
| Problem threads / revisions | 42 / 49 | 30 provisional, 7 open, 3 confirmed, 2 blocked; không lấy 30 provisional làm hoàn tất |
| Problem events | 304 = 286 EXACT + 18 UNLINKED | Exact-link 94.08%; event coverage, không phải criterion/outcome coverage |
| Accepted checkpoints | 270 | Chỉ technical checkpoints trong snapshot |
| Handoff capsules | 3, đều active | Ít capsule không chứng minh đủ context; active record không phải live worker |
| Knowledge checkpoints / ACK | 3 / 67 | 40 CURRENT, **27 MISSING = 40.30%** ACK records; không phải 40% task thất bại |
| Knowledge read observed | 21 events | 16 revision 0, 5 revision 1; phải phân biệt chưa có checkpoint với lỗi không đọc |
| Coordination messages | 22 pending | Durable queue trạng thái; chưa xác nhận delivery/liveness hiện tại |
| Quality outcome events | 272 | 270 (**99.26%**) là `accepted_proof_auto_v1`; 2 nguồn review/repeat khác, không phải 272 independent user outcomes |
| Explicit user outcome receipts | 3 | Controller-reported explicit user receipts ở Problem khác; không chứng minh external business oracle, không thuộc hai current revision |
| Continuity telemetry | 384 | 254 report_gate + 87 accepted_checkpoint + 42 continuation_failure + 1 manual_nudge |
| Provenance natural trong continuity | 3/384 = 0.78% | 2 report-gate + 1 accepted-checkpoint; 381 legacy_unknown; không phải 3 Goal success |
| Current target grants | goal_continuations=0; goal observations=0 | Không có sample trong snapshot để chứng minh source grant đã chạy tự nhiên |

Không có dedicated table mang tên lesson/solution-plan/framing/P4 trong inventory được đọc; các signals tương ứng nằm trong events/derived modules. Không được từ đó khẳng định “app không có tri thức”, cũng không mô tả các report như một knowledge authority database mới.

**Acceptance-throughput của hai Problem không phải completion-rate:** 44/63=69.84% và 16/39=41.03% RUN accepted chỉ phản ánh status mix trong lịch sử đã liên kết. Active/aborted/replanned không độc lập, không random, có missing tail, nên không so hai tỷ lệ để kết luận Problem nào dễ hơn hoặc model nào tốt hơn.

### 3.6. P4/P5: nhiều recommendation, chưa có hiệu quả được chứng minh

P4/event-derived:

- `oracle_preflight`: 207 events; strong_oracle true 4, false 203; verification none 151 (72.95%), tests 52, build 3, all 1.
- Classification hiện có: NOT_RUN 96, VERIFICATION_PASSED 22, ENVIRONMENT_UNAVAILABLE 2; **87 record thiếu field classification**. Thiếu field không tính là PASS/FAIL.
- `solution_shadow_recommended`: 207; toàn bộ shadow_only, automatic_policy_activation=false, production_behavior_changed=false; recommendation khai oracle_strength strong 199, moderate 8; root-cause confidence high 191, medium 16.

Sự khác biệt **4 preflight-strong so với 199 recommendation-strong** là tín hiệu cần đối chiếu definitions và exact run/wave/time. Hai field không mặc nhiên cùng semantics: một là preflight observation, một là structured recommendation. Chưa đủ kết luận 195 recommendation sai; cũng không dùng confidence cao tự khai để coi oracle đã mạnh. Packet cần join exact scope và so recommendation-before-write với observed proof/outcome, giữ unknown và không sửa label lịch sử.

P5: 6 epoch đều P5-A0 shadow A/A, 5 closed và 1 hard-stopped với `post_open_source_scope_drift`; enrollment/assignment/protocol-start/workflow-binding/assignment-outcome đều **0**. Vì denominator assigned=0, treatment effect, arm quality, SRM và causal ROI đều **UNESTIMABLE**, không phải hiệu quả 0% hay thí nghiệm PASS. Giữ hard-stop evidence; không reopen epoch cũ hoặc điền synthetic samples.

### 3.7. Tiền, token và economics

Ledger chỉ có **7 usage_event**: 6 interrupted và 1 completed. Các token fields có mặt 7/7 trong nhóm này; provider_cost/reported_cost đều **0/7 có giá trị**, derived_cost/pricing_revision **1/7**, provider_ms/queue_ms **0/7**. Performance projection không có provider-billing counter.

Do đó:

- Có một mẫu nhỏ provider token telemetry, chưa có coverage toàn task/RUN/Problem; không dùng 7/7 để gọi usage coverage app 100%.
- Một cost tính từ pricing table không phải invoice/provider bill. Không đưa ra tiền tiết kiệm hoặc ROI của cache/route/continuation.
- CAR tiền tệ, TTPR đến confirmed outcome của hai Problem, provider latency và manual operator time giữ UNKNOWN; không biến thiếu cost thành miễn phí.
- Bổ sung correlation/coverage và sources trước; pricing version chỉ cần khi thực sự tính derived cost, phải tách provider-reported/derived/scenario.

### 3.8. Ưu tiên suy ra từ dữ liệu

1. X0 history continuity + outcome/coverage là ưu tiên cao nhất: nhiều accepted proof không bù được exact lineage thiếu.
2. Hoàn thiện actionable setup/runtime/authority errors và source/epoch alignment: nhóm này chiếm phần lớn error envelopes, nhưng phải phân biệt refusal đúng với defect.
3. Chốt một oracle natural mạnh và zero-nudge measurement: không tăng recommendation volume khi feedback độc lập còn ít.
4. Knowledge-currentness và bounded case provenance: xử lý 27 MISSING ACK bằng nguyên nhân exact, không bulk auto-ACK.
5. Sau baseline usable: kiểm 13 cache invalidations và 262 semantic fallbacks bằng case có mục tiêu; không xây tầng mới từ raw counts.
6. Usage/P4/P5 chỉ promote khi đủ assigned population, source/runtime ổn định và independent outcome; tiếp tục shadow-only trong thời gian đó.

## 4. Dữ liệu tri thức: app đang có gì và còn thiếu gì?

### 4.1. Không đánh đồng lưu trữ với tri thức đã kiểm chứng

| Lớp dữ liệu | Thành phần hiện có | Giá trị | Ranh giới cần giữ |
| --- | --- | --- | --- |
| Lịch sử causal | PRL + orchestration ledger, acceptance/file receipts, effect journals | Truy ngược failure→attempt→proof→acceptance | Report rời/mtime không tự bù event thiếu |
| Current state | task-state/context, runtime snapshot, performance | Vận hành/UI và phát hiện drift | Phải có source/window/age; không thay lịch sử |
| Continuity memory | `controller_continuity.py`, knowledge ACK, handoff capsule | Controller tiếp nhận trạng thái có fingerprint và delta | ACK knowledge không phải accept code/outcome |
| Resolution Capsule | `problem_lineage.py::problem_handoff_for_run` | Exact Problem/Revision, contract, remaining criteria, events và frame shadow | Derived/advisory; không cấp mutation/closure authority |
| Phân tích | `problem_resolution_journey.py`, economics/P4/P5/rework reports | Chuyển fact sang chẩn đoán có denominator/missingness | Observation không chứng minh nhân quả |
| Case calibration | Golden HR 7 trường hợp, EGRI research | Phát hiện sai frame, oracle sai tầng, stale runtime, recurrence | Historical labels không phải current natural outcomes |

Resolution Capsule đã có giới hạn payload: outer handoff 8 KiB, embedded contract 4 KiB; nếu quá lớn phải trả omission reason/fingerprint và yêu cầu đọc exact revision, không cắt âm thầm. Frame shadow có `authority_side_effects=false`, `automatic_mutation_gate=false`. Nên **giữ** thiết kế bounded này, không đổi thành kho transcript vô hạn.

Golden HR calibration trong repository có 7 case, nhưng tài liệu tự ghi **không case nào đạt TRUSTED_RESOLUTION**, independent outcome còn unobserved/unconfirmed. GHR-03 cho thấy nghiệm thu kỹ thuật không cứu được oracle sai nghĩa dữ liệu; GHR-04 minh họa source đúng nhưng runtime stale. Đây là bài học để thiết kế phép thử, không phải tỷ lệ thất bại hay hiệu quả của app hiện tại. Không truy cập/sửa dự án HR trong công việc này.

### 4.2. Khoảng hở tri thức ưu tiên

1. **Provenance trước retrieval:** một case có nội dung đúng nhưng checkpoint không có trong canonical phải hiện `UNVERIFIED_PROVENANCE`, không được xếp như lời giải đã accepted.
2. **Outcome trước “best practice”:** accepted-proof-derived quality phải tách independent user/business confirmation; không tạo vòng tự xác nhận.
3. **Applicability trước reuse:** exact workspace/task class/role, source/contract/runtime envelope, oracle strength và failure mode; case không tương thích chỉ là counterexample/advisory.
4. **Giữ phản chứng:** failed attempts, REPLAN, reopened outcomes và lỗi báo cáo phải đi cùng case; không chỉ distill success summary.
5. **Tiến bộ phải đo được:** ghi case/evidence nào làm thay đổi quyết định, discriminator nào loại hypothesis, thời gian đọc và outcome. Retrieval hit không tự chứng minh hữu ích.
6. **Privacy:** chỉ lưu facts, decision labels, hashes, bounded summaries và references được cho phép; không raw credential, transcript, PII hoặc private reasoning.

### 4.3. Thiết kế cải tiến nhỏ nhất

Không tạo vector database/knowledge graph/universal memory mới ở giai đoạn này. Tận dụng các projection/readers hiện có và thêm **bản chiếu case có truy nguyên** khi một natural case thực sự cần:

```text
User contract → exact Problem Revision → bounded frame/discriminator
→ RUN/WAVE/effect/proof → controller acceptance → independent outcome/reopen
→ derived case + applicability + counterevidence → bounded reuse (tối đa 3 case)
```

Trường tối thiểu đề xuất: problem/revision, symptom, typed failure, proven cause hoặc missingness, relevant source/runtime fingerprint, attempted interventions kể cả thất bại, exact proof/checkpoint refs, independent outcome authority/time, applicability/exclusions, closure falsifier, freshness status, reuse decision/result. Đây là **schema đề xuất để map vào structures đang có**, không phải API/table mới được cấp quyền.

Bước đầu chỉ distill hai incident của tài liệu này và một natural product case có thật. Nếu chưa đủ outcome, lưu rõ `PROVISIONAL/UNKNOWN`, không gán “solved”. Sau 5–10 case mới quyết định có thực sự cần index rộng hơn; nếu retrieval không thay đổi quyết định hoặc làm tăng overhead thì giảm/bỏ.

## 5. Đánh giá các hướng giải quyết

| Hướng | Lợi ích | Chi phí/rủi ro | Quyết định đề xuất |
| --- | --- | --- | --- |
| A. Quay lại hoàn thiện direct legacy như đường sản phẩm chính | Ít thay đổi so với contract boot ban đầu; local Tunnel dễ đối chiếu | Xung đột hướng shared-account central; duy trì hai ingress/UX; không giải quyết authority/outcome/ledger gap | Chỉ dùng nếu owner chủ động giữ direct như target được hỗ trợ; không tự đổi role hiện tại |
| B. Hội tụ central account/workspace trên một local runtime + continuation hiện có | Tận dụng source/candidate gần đây, giảm thiết lập lặp; phù hợp account→binding→node | Cần remote exact package, approval/policy/route, role-aware boot oracle; phụ thuộc vận hành Ubuntu | **Khuyến nghị có điều kiện:** chốt contract/revision mapping và gate, không nới guard |
| C. Viết Goal Engine/scheduler/memory hoặc model gateway mới | Có vẻ linh hoạt/hấp dẫn về roadmap | Tăng state/authority/chi phí khi current natural outcome còn thiếu; khó phân biệt lỗi cũ/mới | **DEFER**; chỉ mở khi có yêu cầu chưa được current bounded driver đáp ứng và oracle rõ |
| D. Tối ưu model/cache trước để giảm giá/tool calls | Có thể giảm chi phí một số leaf | Thiếu paired evidence và provider usage; dễ tối ưu sai denominator, gây latent defect | Chỉ sửa deterministic defect đã chứng minh; chưa promote routing/treatment |

Đây là lựa chọn kỹ thuật dựa trên độ phù hợp hiện có, không phải benchmark hoặc phép tính ROI. Không chấm điểm trọng số số học khi dữ liệu chưa bảo vệ được các trọng số.

### 5.1. Ranh giới kiến trúc đích

**Xung đột mã nghiệm thu đã xác minh:** `SHARED_ACCOUNT_WORKSPACE_STATUS.md` tại checkpoint Wave 12 dùng T14 cho “model gateway, nếu bật”; `TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md` mục 7 dùng T14 cho “upgrade/rollback/restore”. T01–T16 của hai bảng cũng không cùng mapping. Trong tài liệu này, mọi mã T tham chiếu **TWAC §7 = ma trận mục 7 của TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md** (T01 same-account, T14 restore, T16 E2E/soak). Đây là namespace tham chiếu cho kế hoạch, không phán quyết authority cho các receipt cũ. X1 phải chốt matrix ID/version/fingerprint trước thực thi, mapping theo nghĩa từng case; không được bỏ restore vì thấy T14 ở bảng khác là N/A. Không rewrite các checkpoint chronology cũ.

```text
Client/account → central principal + binding/task pin → queue/receipt
                                                     ↓ exact node/target
                      Windows installed node → Recovery Host → Coding MCP
                                                     ↓
       explicit Goal grant → existing driver → App Server proposal lane
                                 ↓
                  MCP sole writer + proof + effect journal
                                 ↓
                   ACCEPTING → authorized controller
                                 ↓
                   independent outcome / truthful reopen
```

Central Control Plane DB và Windows canonical orchestration ledger có trách nhiệm khác nhau. Phải liên kết action/attempt/task/Problem qua references, không merge hai DB hoặc coi receipt delivery của central là acceptance kỹ thuật/Goal outcome. MCP tool relay không tự là model API. App Server proposal lane hiện có là lựa chọn mặc định của v1; chỉ đánh giá provider gateway riêng khi sản phẩm thật sự cần và có quyền sử dụng/chi phí cụ thể.

## 6. Điều kiện chung trước khi triển khai

### X0 — Đối soát provenance và freshness (ưu tiên P0)

**Owner:** controller + người giữ ledger/delivery; trước mọi closure hoặc activation dựa trên ba checkpoint thiếu.

1. Chụp lại canonical bằng Backup API; ghi HEAD, worktree relevant hashes, max seq/hash, schema, path/host và timestamp. Kiểm mỗi DB lịch sử trên bản sao/immutable; không mở migration writer.
2. Lập manifest ba missing RUN, checkpoint, report path/hash, event range, expected chain parents; tìm đúng receipt/ledger snapshot trong Git delivery history, backup và host có thẩm quyền. Không dùng “file mới hơn” làm tiêu chuẩn chọn.
3. Phân biệt bản thiếu tail với divergent histories: kiểm event IDs, hashes, parents, RUN/WAVE/problem binding và file attestations. Tìm nguyên nhân bằng đường delivery/restore/copy cụ thể; chưa có evidence thì ghi UNKNOWN.
4. Nếu tìm được lineage đầy đủ: chuẩn bị phục hồi/reconcile theo cơ chế canonical được hỗ trợ, dry-run trên bản cô lập, review và quyền riêng trước mutation. Nếu cơ chế hiện tại không hỗ trợ trường hợp này, mở bounded implementation packet sau khi contract được chốt; không ghép row SQLite thủ công.
5. Nếu không tìm được: giữ report như historical-unverified; không dựng acceptance giả. Owner quyết định proof mới được phép với attempt mới, ghi rõ original missingness. Không kill host chỉ để tăng số đếm.
6. Đối soát 16 active/expired lease theo exact ID; chỉ terminalize qua supported lifecycle preflight/authority. Không bulk cleanup, không biến expired lease thành quyền takeover, không chạm P5 anchors không liên quan.

**Exit X0:** mỗi missing reference có kết luận `VERIFIED_LINEAGE`, `ISOLATED_DIVERGENCE` hoặc `UNRECOVERED_HISTORY_GAP` cùng owner/next action; canonical integrity/chain được kiểm, không claim completeness giả. Những gate phụ thuộc proof chưa hồi phục phải còn mở. Một báo cáo gap hoàn chỉnh không tự đóng C10/BG11/BG13.

### X1 — Freeze contract, execution role và target

1. Read-back cả hai exact capsule/fingerprint; đọc criteria ở mục 8–9, đối chiếu no-manual-nudge dependencies, không mở Problem trùng hoặc chọn newest.
2. Với boot: giữ C01–C12 nếu semantics vẫn đáp ứng; nếu central làm thay đổi meaningful criterion (ví dụ per-device direct Tunnel), lập explicit revision/CAS + mapping carry-forward/reprove/not-applicable có approval. Không tự đặt N/A cho criterion cũ.
3. Với continuation: xác nhận contract thực sự là 4 criterion gốc + BG01–BG14. Không dùng riêng BG list như Problem mới và không carry provisional từ revision 1.
4. Freeze supported target: installed Windows central executor, central origin/service có owner, exact node/workspace binding, controller view, candidate manifest/hash, rollback artifact. Development UI vẫn là development; muốn thêm central-dev support phải là packet riêng.
5. Tách bốn quyền: read/binding; execution scope; model/continuation budget; lifecycle/deploy. Đăng ký Problem không tự cấp bất kỳ quyền nào còn thiếu.

**Exit X1:** target/role/criteria/oracle matrix không mâu thuẫn, acceptance owner và runtime authority rõ; không còn dùng PID/hash từ report ngày 15/09 như target sống.

### X2 — Measurement contract và evidence writer

- Dùng canonical writer hiện có cho events/receipts, reader/projection chỉ đọc. Mọi material wave có operator checkpoint, typed failure, exact source/proof identity, outcome hoặc explicit missingness.
- Thêm source-window/execution-origin/metric-schema vào **projection đang có nếu thiếu**, không một event store cạnh tranh. Ghi runtime/source/projection disagreement thành diagnostic; không tự reconcile từ UI.
- Trong phép thử autonomy, reader phải không dispatch. Không dùng `run_continuation.observe/start/resume/reconcile` từ controller trong cửa sổ đo rồi gọi kết quả là tự chạy.
- Ngân sách pilot dùng contract hiện tại tối đa 900s/12 decisions/3 patches; no-progress 2, driver lease 60s. Con số 60 phút/4 episodes/32 turns/8 patches trong kế hoạch cũ là đề xuất, **không phải quyền hoặc giới hạn đã được implementation hiện tại hỗ trợ**.

**Exit X2:** định nghĩa mẫu số, bắt đầu/kết thúc, synthetic/natural, abort/retry, censoring và privacy được review; data invalid thì dừng claim chứ không điều chỉnh số liệu.

## 7. Kế hoạch kỹ thuật Problem boot/recovery

Các mã A0–A5 là work packet của tài liệu này, không phải runtime states hay Problem mới.

### A0 — Sửa semantic stop refusal (P1)

**Scope dự kiến:** `electron/services/recoveryBootstrap.js`, hợp đồng lỗi tại `recoveryIpc.js` nếu cần, `tests/recovery-bootstrap.test.js`.

- Hiện tại catch tại khoảng dòng 906–921 gom semantic refusal và transport loss; sau đó exact identity có thể dẫn tới terminate tại dòng 949. Identity xác nhận đúng đối tượng, **không thay cho quyền bỏ qua semantic refusal**.
- Phân loại response/error theo contract thực của IPC. Auth/authority/busy/refusal phải kết thúc handoff, không terminate/spawn và không rollback bằng start khi stop chưa được chấp thuận.
- Transport loss giữ trạng thái effect uncertain; đọc lại authenticated exact host/child state trong deadline trước khi quyết định. Không coi mất response là stop thành công, cũng không coi owner đúng là đủ quyền terminate.
- Revalidate ở stop/terminate boundary để bắt UI/job/writer/supervision mới xuất hiện; giữ explicit refusal, không đổi thành generic retry.

**Oracle:** late-busy/refused/auth-denied → terminate=0, spawn=0; transport-loss đã stop thật có đường reconcile đúng; đổi PID/start-token/descriptor/owner → không touch replacement; timeout có typed terminal receipt. Fixtures cô lập trước, không thử bằng kill live host.

### A1 — Rollback giữ nguyên startup intent (P2)

**Scope dự kiến:** cùng module/test với A0; một writer, làm tuần tự.

- Chụp trạng thái ban đầu và intent qua nguồn authenticated đủ fresh trước stop. Giữ tri-state ON/OFF/UNKNOWN; không biến unknown thành on.
- Compensation chỉ khôi phục đúng dịch vụ đã chạy và có khả năng bị operation này dừng, khi exact old owner còn được chứng minh. Ban đầu idle/off → không start; semantic refusal → không start.
- Nếu không phân biệt được stop effect, giữ typed recovery-required và trình owner; không tự bật tất cả services.
- Failed/expired receipt bất biến; compensation thành công không sửa original failure thành success.

**Oracle:** initial off + later failure → start=0; initial on + proven child stop + exact owner → restore đúng; changed owner/manualStop/revoke/busy → no unsafe restore; duplicate rollback không double-start. Kiểm cả primary và recovery plane nếu operation thực sự chạm hai plane.

### A2 — Oracle role-aware và không false-green

**Scope dự kiến:** verifier/receipt hiện có, `scripts/packaged-recovery-smoke.js`, `scripts/dev-ui-lifecycle.js`, relevant tests; chỉ thêm một verifier nhỏ nếu chưa có nơi thích hợp.

Receipt mỗi sample phải bind Problem/revision, role, source/package/contract hash, boot time + boot mode, process start token/instance, epoch và operation, endpoint/workspace generation, startup intent, before/after state, error/retry sequence và observed client result.

- Direct legacy: Host/MCP/Tunnel và connector theo exact/compatible/breaking contract policy đã được duyệt.
- Central: Host/MCP/native + hợp lệ epoch, registered target, central route freshness, local policy/authority + real-client action trên bound workspace. Không ép local Tunnel=true.
- Cả hai: loaded revisions đúng, admission hợp lệ, fullyReady=true, không repeated manual repair; client discovery khi contract yêu cầu strict; `workspace_context` thật trả completed/workspace_accessed đúng, không tính pending handshake là workspace read.
- Các oracle phải thất bại khi chỉ PID/hash/health xanh nhưng primary task không dùng được. `CURRENT_COMPATIBLE_ACKNOWLEDGED` là continuity path được phép khi contract phù hợp, không được ghi là strict rediscovery.

**Exit:** positive + discriminating negative tests, receipt version/compatibility rõ; pre receipt cũ giữ nguyên lịch sử. Không sửa pre JSON ngày 15/09 để nó trông như đã kiểm các field mới.

### A3 — Frozen package và activation có kiểm soát

**Phụ thuộc:** X0/X1, A0–A2 source/technical acceptance; owner cấp lifecycle/deploy target riêng.

1. Review dirty source/candidate đang có, không build lại phần đã có exact proof nếu bytes còn khớp; không lấy failed EBUSY artifact làm candidate.
2. Freeze Windows + Control Plane package manifests. Verify OS-specific archive mode/LF, resources, fuse/RunAsNode, secret store/ACL và installed identity theo đúng lane.
3. Với central: verify exact remote package/service/schema và enrollment/credential/workspace/policy/route. `/healthz=200` chỉ là reachability. Không coi Ubuntu đã approved/deployed từ tài liệu lịch sử.
4. Tránh vòng phụ thuộc: enrollment/workspace/policy setup không yêu cầu fullyReady; nhưng execution admission phải yêu cầu đầy đủ identity/route/policy/epoch.
5. Khi đủ authority/census, tạo new controlled activation operation/epoch; giữ FAILED cũ và pending accepted work. Không nới UPDATE_INCOMPLETE hoặc hạ source revision guard.
6. Postflight từng component, epoch, source/package, bound target và client action; nếu sai thì dừng theo tầng, không lặp refresh mù.
7. Cài/enable đúng Supervisor và startup intent chỉ theo opt-in của owner, rồi xác minh manifest/task identity/readback. Supervisor alive khác primary services enabled.

**Exit:** exact installed/runtime receipt, một client task thật đúng workspace; thiếu central operator/deploy/máy B thì ghi BLOCKED_EXTERNAL tương ứng, không mở admission giả.

### A4 — Recovery/reboot matrix

Chạy isolated faults trước, sau đó live faults/reboot **chỉ khi được phép và jobs đã quiescent**. Ma trận chi tiết kế thừa [boot closure plan](../BOOT_HOST_TRANSITION_CLOSURE_PLAN.md), không tự giảm sample.

| Nhóm | Sample cần thực hiện | Oracle phân biệt |
| --- | --- | --- |
| Cold-start/logon | Entry point đúng target, không process cũ; Startup ON và intentional OFF phân biệt | Auto-ready đúng intent; OFF không bị tự bật |
| Reboot M02 | 3 reboot mỗi máy vật lý theo plan; ghi Restart/power-on/Fast Startup thực tế | Boot/start token/instance mới + readiness/client task, không chỉ PID khác |
| Host/network loss | Host-only loss, tunnel/central-route loss phù hợp role, reconnect | Không retry storm, duplicate child/epoch/effect |
| Busy/authority | Active writer/job, manualStop, lease/identity drift, revoked credential | Refusal đúng; không mất task/secret/history |
| Upgrade/skipped version | Same/compatible/unknown/breaking contract, stale installed bytes | Compatibility chỉ trong reviewed closure; strict discovery khi bắt buộc |
| Hai máy/cùng account | Client B/C chọn binding của A; đồng thời chọn binding khác cho task khác | Không retarget/failover mù; read/observe/stop/handoff đúng scope |
| Rollback/restore | Failed activation/partial effect, isolated restore drill | Giữ attempt lịch sử, unknown effect không được replay |

Mỗi sample giữ cả failure/retry. VM/temp process trên máy A không thay máy B. OS đã reboot trong đời thường nhưng không có exact before/after receipt không được backfill thành sample PASS.

### A5 — Natural-use và closure boot

- Canonical revision 1 hiện giữ **ít nhất 48 giờ sử dụng thực**, một phiên natural hoàn tất trên mỗi máy và independent confirmation theo plan. Đây không phải 48 giờ máy idle hoặc 48 giờ kể từ lúc bắt đầu viết code.
- Soak 24 giờ trong shared-account plan là gate khác; không tự dùng 24h thay 48h. Có thể dùng chung cửa sổ nếu đáp ứng cả hai bộ điều kiện và giữ mapping riêng.
- Thu số unnecessary repair/refresh/login/nudge, failures/reopens, bound task success, uptime samples và gaps. Không tạo công việc giả để đủ mẫu.
- Nối evidence tới từng C criterion bằng canonical coverage API/receipt hợp lệ; controller acceptance và outcome receipt khác authority. Thiếu sample → giữ criterion mở.

## 8. Ma trận C01–C12: khoảng trống, owner và acceptance

Mỗi dòng là một tiêu chí **canonical revision 1**. Cột “đã có” không phải dấu PASS: toàn bộ còn cần exact coverage/acceptance của revision đích; nếu X1 duyệt revision mới thì giữ mapping hai chiều, không ghi đè lịch sử này.

| Criterion | Nghĩa cần đạt | Đã có / thiếu hiện tại | Packet + oracle đóng |
| --- | --- | --- | --- |
| C01 | Đúng entry point cold-start khi process cũ mất, gồm reboot thật | Historical packaged spawn/pre receipt; chưa nối checkpoint canonical, không post-reboot proof | X0, A2–A4: fresh boot/start-token/package + real bound workspace task |
| C02 | Một epoch owner; không spawn dưới terminal READY; drain supervision trước handoff | Có idle/timeout/drain hardening; P1 late refusal còn trong source | A0/A2: late-busy, two-owner, READY/failed-epoch negative và one-operation process proof |
| C03 | Same-SHA ACK bootstrap được khi predecessor rỗng | Compatibility/bootstrap source và tests hiện có; chưa revalidate exact integrated path của target | A2/A3: Python→Electron admission-closed attested handshake; không giả workspace read |
| C04 | Skipped compatible releases; unknown/breaking phải discovery | Reviewed compatibility graph source hiện có | A2/A4: compatible positive + unknown/cycle/tamper negative; đúng discovery rule |
| C05 | Discovery/census/lock/cleanup hữu hạn, typed causes, không orphan | Existing timeout/lock/identity mechanisms; chưa current installed matrix | A0–A4: forced timeout/lock contention/cleanup, bounded terminal receipt và job census |
| C06 | Không vượt manualStop, write/job/lease, foreign identity/source drift | Guards có; A1 có nguy cơ bật dịch vụ ban đầu off | A0/A1/A4: idle-off, manual stop/revoke, live writer, PID reuse, source drift negative |
| C07 | Host-only restart rồi loss không retry loop | Recovery source/isolated smoke đã ghi nhận; live fault chưa closure | A4: đúng loss plane theo role, bounded retries/backoff, no duplicate host/epoch/effect |
| C08 | Session hợp lệ được giữ; missing/revoked đúng lớp | Durable session/device/credential separation; chưa installed two-machine outcome | A3–A5: không clear session vì runtime error; revoke/login/missing config phân loại đúng |
| C09 | Hai máy đúng endpoint/workspace/tunnel, không silent mutation failover | Central binding/task-pin candidate có; contract old-direct cần X1 mapping | X1/A4/A5: hai physical/client receipts và read thật; sai target/generation bị từ chối |
| C10 | Exact source/proof/acceptance/runtime/artifact và rollback/history | **Có gap ba canonical checkpoint/RUN** và Host drift | X0/A3/A4: complete ancestry/attestations, restore/replay negatives; missingness không tự PASS |
| C11 | Ca thành công không cần sửa source/xóa state/refresh tay | Chưa natural window; current runtime chưa ready | A4/A5: ghi intervention/event trail, zero unnecessary repair trong sample thành công |
| C12 | User xác nhận đúng Problem Revision, không mandatory blocker | Chưa independent current outcome; 48h/máy B còn mở | A5: canonical criterion coverage + explicit user/outcome receipt + closure falsifier |

## 9. Kế hoạch durable Goal continuation và ma trận 18 tiêu chí

### 9.1. Phần nên giữ và kiểm chứng, không xây lại

Các cơ chế đã thấy trong source:

- `goal_pursuit.py`: exact identity/revision, bounded candidate pagination, ambiguity fail-closed, criterion-gap projection; tests không cho passed proof thay accepted criterion claim.
- `continuation_contract.py`: immutable typed READ/PATCH/READY/BLOCKED proposal, evidence hash, exact scope/check hashes và bounded consent; v3 RUN/v1 Goal episode.
- `run_continuation.py`: parent goal record trong **cùng ledger**, one-active identity constraint, exact controller fence, child materialization, shared remaining decisions/patch attempts, atomic reservation/release, no-progress observation và revocation.
- `continuation_driver.py`: real bridge dispatch (`continue_thread`), effect backups/journal, all-approved-checks proof, technical replan, report-gate auto resume, execution rebind, pending-effect stop/reconcile và barrier ACCEPTING.
- `controller_continuity.py`, continuity telemetry: bounded knowledge checkpoint/ACK và provenance, không thay owner/acceptance.

Parent policy hiện được xây từ bounded RUN policy; source giới hạn tổng **900 giây / 12 quyết định / 3 lần patch**, no-progress **2**. Có khả năng materialize đúng child đã bind; **không suy ra source hiện tự tạo mọi RUN kế tiếp hoặc Goal dài vô hạn**. Child RUN khác chỉ khi có lý do/authority/lineage hợp lệ; ordinary REPLAN phải giữ RUN và dùng WAVE, không tăng số RUN để né ngân sách.

### B0 — Exact grant, runtime và inference lane readiness

**Phụ thuộc:** X0/X1/X2 và một runtime usable của A3. B0 source inspection/negative fixtures có thể làm song song với A0/A1.

1. Preflight current public schema/transport; xác minh exact endpoint/workspace/controller generation và Problem revision. Nếu central client chưa có đường attested host consent tương thích với driver hiện hữu, ghi integration gap cụ thể; không forge ChatWeb identity.
2. Thu explicit one-shot bounded user consent qua host/path thực sự hỗ trợ, kèm allowlist write/protected paths/checks/time/decisions/patches. Không dùng một câu “toàn quyền” cũ thay receipt.
3. Verify actual App Server lane, route requested/resolved, process/thread/turn identity, model availability và usage visibility. Ưu tiên lane hiện có; không cần gateway mới chỉ vì central đang relay tools.
4. Chạy content-free bounded dispatch canary có quyền trước mutation; strict typed parser vẫn cuối cùng, không extract JSON từ prose hoặc bỏ fields lỗi để hợp thức proposal.
5. Nếu không có authority tạo lượt inference tiếp theo sau client response end, dừng tại **thiếu host/provider dispatch authority**, không biến poll loop/cron/browser automation thành model turn giả.

**Exit:** grant thật → một dispatch thật có receipt → result được strict-parse trên đúng runtime; chưa phải natural outcome.

### B1 — Proof parent accounting và unknown-effect safety

**Scope:** existing contract/ledger/driver và tests; thêm regression chỉ cho gap tái hiện được.

- Hai wake đồng thời chỉ reserve/dispatch một action; duplicate ACK không debit budget lần hai; rejected pre-dispatch reservation chỉ refund qua exact no-effect proof.
- Parent remaining budgets/expiry giữ qua child bind/reconnect/restart được phép; không tự gia hạn, không reset khi đổi RUN/WAVE/controller.
- Crash tại trước effect, sau effect trước receipt, sau terminal trước ACK phải có verdict phân biệt. Unknown pending dispatch/effect → reconcile required, không dispatch lại để “thử xem”.
- Không viết vào protected oracle, `.coding-tools` qua model patch, hoặc path ngoài grant. Source/worktree/proof drift trước apply → no effect.
- No-progress phải dựa trên evidence/proof/criteria thay đổi có ý nghĩa, không dựa vào prose khác hoặc mỗi lần gọi tool đều coi là tiến bộ.

**Exit:** focused negative suite + isolated process fault proof bound exact source. Existing tests là tài sản tái sử dụng, không chạy full suite nếu leaf proof đã đủ.

### B2 — Tự tiếp tục sau report/reconnect và tiếp nhận đúng controller

1. Phân biệt triggers: ordinary proof failure→REPLAN cùng RUN, report ACK→eligible auto resume, reconnect→reattach/revalidate, controlled restart→exact successor activation receipt. Revoke/Stop/pause/budget exhausted không phải triggers để resume.
2. Kiểm exact environment/runtime behavior fingerprint và controller attachment ở mọi boundary; khác endpoint hoặc epoch không được dùng consent/lease cũ mù quáng.
3. Đưa review request và outcome về cùng controller view. Ghi `request_emitted`, `delivery_observed`, `controller_acknowledged` riêng; chỉ nhìn thấy code gửi message không chứng minh người dùng đã nhận.
4. ACCEPTING tiếp tục cần authorized accept/reject. Executor không tự accept để giảm manual interaction; approval hợp lệ được đếm riêng khỏi unnecessary nudge.
5. Kiểm các pending coordination message bằng delivery/provenance contract hiện có, không mark-delivered bulk. Knowledge CURRENT có nghĩa nhận đúng revision, không quyền execution mới.

**Exit:** actual automatic transition có consumed-event/action/turn IDs và controller delivery receipt; mọi stop boundary có typed reason và exact next action.

### B3 — Autonomy canary không bị phép đo can thiệp

**Thiết kế phép thử:** một task bounded có strong immutable oracle, một parent grant, một active child; fixed source/runtime/contract; technical fixture được gắn `synthetic/technical`, không natural.

1. Bắt đầu một lần sau consent; ghi thời điểm host response end/worker start được quan sát. Đóng view chỉ khi thao tác đó được cấp quyền và không mất authority đã được contract bảo đảm.
2. Trong cửa sổ, controller chỉ đọc immutable ledger hoặc proven passive projection. Cấm gọi public `observe/start/resume/reconcile` có thể dispatch/renew/apply.
3. Yêu cầu ít nhất một chuỗi tự động có evidence thực: result→oracle fail/read-needed→typed next proposal→actual next dispatch→proof→ACCEPTING; nếu task đã xong ngay thì không ép tạo lỗi để gọi đó natural case.
4. Kiểm Stop/revoke và unknown-effect bằng separate authorized fault samples. Legitimate user approval không bị báo là product failure.
5. Nếu controller phải nhắc/relay để tiếp tục, giữ sample failed/intervened, ghi cause; không bỏ khỏi denominator rồi báo zero-nudge.

**Exit:** canary technical autonomy PASS với thời gian/turn IDs; chưa BG10/BG14 natural resolution.

### B4 — Natural Goal, independent outcome và continuation closure

- Chọn một công việc **người dùng thực sự cần**, có reproduction, phạm vi, oracle độc lập và nguồn outcome rõ; không tự tạo việc sửa lỗi giả. Có thể là một defect app thật sau khi source fix được giao, nhưng người dùng/owner phải xác nhận nhu cầu và tiêu chí.
- Chốt trước window, max budget, allowed lifecycle, exit conditions và cách phân unnecessary nudge/manual relay với legitimate approval/outcome.
- Thu TTAR, TTPR, all attempts/aborts/replans, operator interventions và usage coverage. Outcome pending giữ right-censored, không bỏ các task chưa thành công khỏi phân tích.
- Controller technical acceptance trước, user/outcome authority sau; không natural success từ `REPORT_ACKNOWLEDGED` hoặc `CONTROLLER_ACCEPTED` telemetry.
- Nối exact 18 criterion evidence vào revision hiện hành; nếu scope meaningful đổi thì explicit revise, không carry acceptance tự động.

**Exit:** BG10/BG14 và bốn criterion gốc có exact coverage/outcome, không mandatory blocker; nếu failed thì truthful reopen của đúng revision và plan mới từ counterevidence.

### 9.2. Ma trận đủ 18 tiêu chí canonical revision 2

| Criterion ID | Yêu cầu rút gọn | Source/proof nền hiện có | Gate/packet còn phải chứng minh |
| --- | --- | --- | --- |
| continuity.auto_resume | Tự resume qua ordinary REPLAN/report/reconnect/accepted restart, không manual continue | `continuation_driver.py` auto_resume/rebind; test report-gate/successor epoch | B2/B3/B4: actual dispatch sau boundary, không controller pump |
| continuity.no_duplicate_effect | Retry/reconnect không lặp effect | effect journal/reservation/terminal replay | B1 + A4: fault trước/sau effect/ACK, duplicate wake, exact reconciliation |
| continuity.terminal_stop | Chỉ dừng tại terminal/blocker/safety thật với typed cause | driver terminal/blocked/revoked/expiry branches | B1/B2: exhaustive stop mapping; không lặng im ở transport timeout |
| telemetry.durable_events | Event durable qua restart, không transcript/private reasoning | continuity telemetry logical IDs, ledger writer | X0/X2/B1: durable restart/query-only replay, schema/privacy/dedup |
| BG01 | Một Goal exact Problem/Revision/workspace/endpoint/controller, không pursuit/RUN trùng | goal resolver; parent identity unique; controller fence | B0/B1: duplicate grant/current-revision ambiguity, no timestamp selection |
| BG02 | Có grant thì tiếp tục sau response end; stop/revoke vẫn dừng | worker driver + explicit consent path | B0/B3: real provider/host path sau response end, one-shot grant |
| BG03 | Oracle phân PASS/FAIL/UNKNOWN, model text không là proof | strict parser, all-approved-checks, proof pipeline | B1/B3: malformed/stale/evidence-missing/zero-test negatives |
| BG04 | Typed proposal được validate rồi dispatch thật, không chỉ lời nhắc copy | `continue_thread`, durable thread/turn/action cursor | B2/B3: next-turn ID + result + proof linkage, no manual relay |
| BG05 | Parent budget durable, atomic reservation, expiry, không auto extend | shared parent remaining counters; current cap 900/12/3 | B1: concurrent child/action, restart/refund, no budget reset |
| BG06 | Event/response/two-wake không double mutation; unknown reconcile | exact effect journal và pending-action checks | B1/B3: crash/lost ACK/conflicting terminal, stop without replay |
| BG07 | Resume revalidate revision/source/env/quyền, không đổi máy/scope ngầm | runtime behavior hash, controller rebind/successor receipt | B0/B2/A4: wrong endpoint/new epoch/no receipt must fail-closed |
| BG08 | No-progress/budget/oracle/authority/pause/stop/blocker không retry storm | no_progress=2; typed budget/revoke/expired branches | B1/B2: two identical evidence observations, genuine progress reset, bounded backoff |
| BG09 | Readiness/review cùng giao diện; ACCEPTING cần controller | continuity core/ACK + accepting barrier | B2: real delivery/readback and authorized accept/reject; no self-accept |
| BG10 | Natural case zero relay/zero unnecessary nudge, approval riêng | Chưa đủ natural sample trong snapshot | B4: predeclared uncontaminated window, intervention count và all-sample retention |
| BG11 | Failure→replan→dispatch→proof→budget/recovery→acceptance→outcome liên kết canonical | schema/events/journey hiện có; X0 history gap còn thật | X0/X2/B4: exact links/current revision, cả failed attempt, no orphan accepted report |
| BG12 | Dedup/privacy/natural-vs-synthetic/unknown/coverage; không ROI giả | telemetry/report schema và privacy gates | X2/B4: missingness report, origin provenance, duplicate logical ID tests |
| BG13 | Regression + isolated process faults + exact runtime acceptance; rollback giữ ledger | Nhiều focused tests hiện có, chưa current integrated/live closure | B1/B3/A3/A4: fingerprint-bound tests + process/runtime + non-destructive rollback |
| BG14 | Confirmed chỉ sau đúng user outcome/revision; technical pass chưa đủ | PRL provisional/confirmed guard | B4: accepted coverage + independent current outcome + absence mandatory blocker |

## 10. App còn cần bổ sung hoặc xử lý phần nào?

### 10.1. Bảng quyết định toàn sản phẩm

| Miền | Giữ/tận dụng | Cần MODIFY/ADD có giới hạn | Proof/gate và ưu tiên |
| --- | --- | --- | --- |
| Canonical persistence/delivery | Ledger append-only, receipts, Backup API, retention guard | History-gap diagnostic exact references, delivery-tail/restore provenance và report freshness | X0; P0 trước closure; không store thứ hai |
| Boot/recovery | Host, Supervisor, epoch, process identity và manualStop guards | P1/P2; role-aware oracle; installed startup intent | A0–A4; P0 safety/availability |
| Setup/UX | Candidate “Thiết lập hệ thống”, origin/binding selection | Finish review pending/stale/revoked/dev vs packaged, exact next action; tránh wizard loops | Reuse setup candidate G2/G3 evidence; installed user flow P1 |
| Central account/target | principal→binding→task pin, node enrollment, standing policy | Exact remote package, approval/rotation/registry/policy/route and actual two-client use | T01–T11; external authority riêng; P0 usable |
| Jobs/effects | Structured argv, poll/stop/cursor/terminal, journal | Verify large output/child process/stop offline/ACK loss thật, no silent redelivery | T12/T13 + B1; P0 safety |
| Goal/continuation | Parent grant, driver, App Server lane, accepting barrier | End-to-end supported host consent/delivery, autonomy after response, exact successor rebind | B0–B4; P0 product goal |
| Tri thức/context | Derived capsule/knowledge ACK/journey | Provenance status, applicability, counterevidence, outcome-linked bounded reuse | K0/K1 below; P1 after trustworthy baseline |
| Observability | Typed metrics/events/projection cache | Window/reset/source/denominator, unknown display, one status checkpoint per material wave | X2/K0; P0 truthful operation |
| Oracle/quality | Immutable approved checks, PRL coverage and outcome guard | Natural strong-oracle case; reconcile declarative-vs-observed strength | B1/B4/K1; P0 outcome |
| Cache/semantic speed | Existing proof cache and fallback search | Diagnose 13 fingerprint invalidations; one provider health canary | K2; P2 only when boundary usable |
| Security/credential/OS | DPAPI/SecretStore, local ACL, auth/generation fence | Installed rotation/revoke, wrong principal/target, artifact no-secret, supported OS matrix | T02/T04/T10/T15; P0 before multi-client live |
| Packaging/release | Existing builder/resource verifier/isolated smoke | Freeze exact archive/installed bytes; Windows+Linux lane compatibility; evidence manifest | R0 below; P1 delivery, separate authority |
| Backup/restore/operations | Central recovery runbook and admission recovery mode | Isolated drill plus node-side effect reconcile, retention/ACL/capacity/alerts; owner RPO/RTO | T14/T16; production gate, không /healthz substitute |
| Routing/EGRI/P5 | Source-gated shadow/experiment facilities | Data quality, natural cohort, A/A instrumentation before A/B | K3; DEFER automatic promotion/gateway/framework |

### 10.2. K0 — Làm trạng thái và tri thức đáng tin

Scope đề xuất: existing report/journey/knowledge projection, UI consumer tests; không sửa event lịch sử.

- Mỗi status card hiện observed_at/age/source/window và exact target; `pending`, `unknown`, `stale`, `failed`, `ready` không bị coerce thành nhau.
- Separate “source current”, “host current”, “MCP current”, “epoch admitted”, “route/policy ready”, “task worked”, “user outcome”. Một badge Ready không che component drift.
- Phân 27 MISSING knowledge ACK: chưa có checkpoint, wrong generation, not delivered, unobserved user read hoặc stale/source mismatch. Chỉ acknowledge qua real supported reader/owner, không auto-advance knowledge để hạ số đỏ.
- Nối case/report tới canonical reference, đánh dấu historical-unverified khi chain thiếu; UI không đề xuất restart từ một report stale.
- Triển khai lỗi hướng dẫn theo deterministic typed code nơi đã có contract; ưu tiên natural runtime/validation/authority errors, không catalog toàn bộ hypothetical errors.

**Acceptance:** negative tests cho stale/pending/missing telemetry, E2E đúng màn hình/target; không yêu cầu viết lại dashboard. Không đo outcome từ screenshot đẹp.

### 10.3. K1 — Một natural case và bounded knowledge reuse

Chọn case thật sau A3; bước trước mutation gồm: user outcome → frame hiện tại → 1–3 hypothesis → một discriminator → at most 3 historical cases có applicability → scope/oracle. Ghi structured decision labels, không private reasoning.

Sau task ghi actual cause hoặc unproven, intervention, exact code/proof/acceptance, outcome/reopen và reuse helpful/neutral/harmful. Historical case chỉ giúp đặt câu hỏi; không thay runtime readback. Hoàn tất một case rồi 5–10 case với task class, risk, source window, oracle và operator burden rõ. Không dùng cohort tự chọn toàn success để tuyên bố general benefit.

**Acceptance:** mỗi case có falsifier và provenance; case reuse gây sai frame phải được giữ như negative-transfer evidence. Knowledge precision/harmful-reuse được tính trên reviewed retrieval decisions, không trên tổng log.

### 10.4. K2 — Tối ưu nhỏ theo tín hiệu thực

1. Cache: lấy một repeated exact proof opportunity, phân cold/invalidation, kiểm relevant-input hash; đo proof_ms saved và validation quality giữ nguyên. No-op unrelated telemetry không invalidate source; changed oracle/toolchain phải invalidate. Không đặt target cache hit 80% khi workload chủ yếu cold.
2. Semantic: đúng workspace/language/provider; đo availability, handling/fallback reason, search-to-useful-evidence latency và accuracy; giữ deterministic fallback. Zero handling hiện tại là lý do probe availability, không bằng chứng cần thay engine.
3. Output: kiểm one bounded large-result flow và continuation correctness; 3.58% visible bytes có thể tiết kiệm output nhưng cần thấy missing evidence/truncation before optimizing further.

**Acceptance:** một discriminatory repro, một fix nhỏ nếu có lỗi, exact regression và no quality regression. Không thêm abstraction/framework trước use case thứ hai.

### 10.5. K3 — Economics/P5 sau dữ liệu natural

- Dùng read-only reporters hiện có; freeze source/manifest/analyzer và independent oracle. Giữ P4 passive; không đổi recommendation lịch sử để khớp proof hậu nghiệm.
- A/A xác minh assignment/funnel/dedup/ITT/source binding, không hiệu quả. Không chọn epoch closed/hard-stopped cũ để refill.
- A/B riêng sau A/A và approval, chỉ thay một micro-policy (ví dụ bounded case packet), giữ model/route/compute/proof/risk và task strata. Pre-register quality floor, restricted TTAR/resource-overhead/cost noninferiority khi cost đủ coverage.
- Report all-assigned, incomplete/censored, exclusions và source drift. Không suy effect từ 0 assignments, raw accepted count hoặc 5–10 calibration cases.
- KEEP/MODIFY/REMOVE khi outcome/economics đủ; không auto-promote vào production.

### 10.6. R0 — Handover/release/operations

Sau technical/natural gates, owner chọn có cần release/destination nào. Run isolated package/install/reboot/rotation/restore matrix exact artifact, kiểm outstanding jobs/effects/leases, operational support scope, rollback target và retention/ACL/backup schedule. Không công bố unsupported OS/client chỉ từ source test.

Trước mỗi commit/push theo repo policy: `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery`, exact staged receipt/index/ledger integrity và secret/history guards; giữ mọi `.coding-tools/**` trừ đúng hai sidecar canonical được phép. Việc lập tài liệu này không chạy staging commands hoặc cấp quyền publish.

## 11. Kế hoạch điều hành, phụ thuộc và ước lượng

### 11.1. Thứ tự và cách song song hóa

```text
X0 provenance + X1 contract + X2 measurement
                  ↓
          A0 → A1 → A2       B0/B1 source-level checks
                  ↓                    │
                 A3 usable baseline ←──┘
                  ↓
             A4 faults/reboot     B2/B3 real autonomy
                  └──────┬──────────────┘
                       A5 + B4 natural outcomes (mapping riêng)
                              ↓
                 K0/K1 → cohort → K2/K3 (evidence-gated)
                              ↓
                       R0 nếu có quyền release
```

K0 status truthfulness và document/metric contract có thể làm sớm khi scope không đụng A/B writer. Các packet chia sẻ `recoveryBootstrap.js` hoặc `run_continuation.py` phải tuần tự, một writer/lease. Canonical E02 không cấp current mutation authority. Workers read-only/candidate trước; controller giữ contract, trust boundary và acceptance. Không spawn mô hình nặng hơn chỉ vì task có nhiều file; model route trong repo và model chạy audit là hai fact khác nhau.

### 11.2. Bảng work packet

Ước lượng dưới đây là **planning range theo ngày công kỹ thuật**, không phải benchmark, cam kết SLA hoặc elapsed calendar. Không có nhân sự/phân phối lead-time đã đo; re-estimate sau X0/X1. Không cộng đơn giản các dòng chạy song song, không tính thời gian chờ owner/máy B/provider là đã hoàn tất.

| Packet | Owner chức năng | Depends | Output reviewable | Ước lượng đề xuất | Điểm dừng |
| --- | --- | --- | --- | --- | --- |
| X0 | Evidence/delivery owner + controller | Quyền đọc nguồn lịch sử | Missing-reference/chain comparison, cause verdict, supported recovery plan | 0.5–2 ngày; có thể chờ external | Không tìm lineage hoặc cần phục hồi thật → xin đúng authority |
| X1/X2 | Controller + product owner | Canonical readback | Contract/role mapping, grant terms, measurement manifest | 0.5–1 ngày | Meaningful contract conflict hoặc budget chưa duyệt |
| A0/A1 | Recovery writer | X1, reproduction | Two safety fixes + discriminating regression | 1–2 ngày | Refusal/rollback semantics chưa settle |
| A2 | Recovery/oracle owner | A0/A1 interface | Role-aware receipt/verifier + false-green negatives | 0.5–1.5 ngày | Oracle không đo được client/usefulness |
| B0/B1 | Continuation writer | X1/X2 | Reuse map, focused gaps/fault proof | 1–2 ngày | Host consent/provider authority hoặc effect unknown |
| A3 | Windows/Ubuntu operators + controller | Exact accepted source, X0 gate disposition | Frozen manifest, approved activation, live identity/route/task receipt | 0.5–1.5 ngày thao tác, ngoài thời gian chờ | Wrong target/epoch/remote package hoặc permission thiếu |
| A4 | Test/operator | A3 + maintenance authority | Matrix samples before/after, all failures/retries | 1–2 ngày, phụ thuộc hai máy | Busy job, revoke, unknown effect, failed sample |
| B2/B3 | Continuation/controller host owner | A3 + grant | Real dispatch/reconnect/review/autonomy canary | 0.5–1.5 ngày | Intervention contamination/unsafe resume |
| A5/B4 | User + independent outcome owner | Controlled gates đạt | ≥48h use + natural Goal outcome, exact coverage | ≥48h actual-use; nhu cầu thật quyết định lịch | Thiếu natural task/approval hoặc recurrence |
| K0/K1 | Observability/knowledge owner | X2, then natural case | Truthful status + provenance-bounded case | 1–2 ngày cho slice đầu | Không có evidence/outcome cho claim |
| K2 | Performance owner | Stable repeatable baseline | Một cache/semantic/output decision packet | 0.5–1 ngày/defect đã định vị | Chỉ raw count, không reproduction |
| K3/R0 | Experiment/release owner | Natural evidence + quyền riêng | Preregistered study hoặc release/ops acceptance | Lập sau sample/target, chưa ước lượng | Không đủ assignment/outcome/cost hoặc release authority |

Mỗi wave cần kết thúc bằng operator checkpoint: changed/completed, Git/source/runtime identity, proof level, failure/blocker classification, remaining criteria, exact next action. Không dùng tool card/log làm final-visible report. Không tạo RUN mới chỉ vì cũ REPLAN; không tự đóng RUN khác để làm census xanh.

### 11.3. Quyết định cần owner đúng thời điểm

1. Target release/use path là installed central executor hay tiếp tục hỗ trợ direct legacy song song? X1 lập mapping; file này khuyến nghị central, chưa thay canonical contract.
2. Ai giữ authority đối soát/phục hồi ledger và bản nào có lịch sử còn thiếu? Chỉ đọc không cần restore authority; mutation cần riêng.
3. Windows artifact/Ubuntu service nào được phép install/activate/deploy, maintenance window và rollback target nào?
4. Máy B/client account/test workspace nào được phép dùng; có quyền reboot/fault/rotation/revoke không?
5. Task natural và outcome owner nào, ngân sách continuation thực tế bao nhiêu? Chỉ bắt đầu sau consent thật; không tự cấp paid inference.
6. RPO/RTO/retention/SLO nào owner chấp nhận? Chưa có số đo hoặc yêu cầu để ghi 99.9%/zero-loss như cam kết hiện hữu.

## 12. KPI, tiêu chuẩn nghiệm thu và phản chứng

Các mục tiêu dưới đây là **đề xuất acceptance của packet**, không phải baseline app đã đạt. Ngưỡng cứng từ canonical (12/18 criteria, 48h) giữ riêng với target hiệu năng cần owner duyệt.

| KPI | Định nghĩa/mẫu số | Baseline hiện có | Gate đề xuất |
| --- | --- | --- | --- |
| Canonical reference completeness | Exact verified refs / required refs trong closure packet | Ba historical RUN thiếu; two current coverage manifests=0 | 100% refs được dùng để claim phải verify; missing refs không được tự PASS |
| Criterion coverage | Criterion có accepted exact evidence / 12 hoặc 18 | Chưa có accepted linking đủ; không đo bằng LOC | Đủ từng mandatory criterion, không chỉ tổng phần trăm |
| Ready-to-first-real-action | Từ start được phép đến action đúng bound workspace | UNKNOWN | Fresh epoch/role/task receipt; timeout target chốt X2 theo thực nghiệm |
| Recovery success | Samples phục hồi đúng intent/target, no duplicate / toàn bộ allowed samples | Chưa current installed matrix | Mọi mandatory sample A4/T matrix đạt; giữ failed/retry |
| Duplicate effect | Irreversible/already-recorded effects bị lặp | Chưa natural fault denominator | 0 trong controlled matrix và natural window; any critical miss dừng rollout |
| Unnecessary nudge/relay | User message chuyển tiếp/nhắc tiếp tục vì ordinary boundary trong eligible window | 1 manual_nudge history chưa đủ coverage | 0 trong BG10 sample; legitimate consent/acceptance/outcome tách riêng |
| Stop/revoke correctness | Authorized stop tạo safe terminal/unknown verdict trong deadline | Source proof nền | Không dispatch mới sau fence; pending stop không giả stopped |
| Budget conservation | Spent + reserved + remaining hợp lệ dưới grant cap, không reset | Parent source present, snapshot grant0 | Concurrency/restart/expiry/regrant negatives PASS |
| TTAR | Start eligible attempt → technical accepted checkpoint, chốt scope/time convention | Chưa fresh exact comparable cohort | Report all attempts + restricted/censored; không chỉ successful runs |
| TTPR | User Problem open/revision → confirmed outcome đúng revision | Hai current Problem OPEN | Chỉ tính outcome thật; unresolved right-censored |
| Knowledge evidence coverage | Retrieved/cited cases có provenance + applicability + outcome label | Derived structures có; natural reuse benefit UNKNOWN | 100% cited cases có label/refs; unverified không làm authority |
| Helpful/harmful reuse | Reviewed retrieval decisions thay đổi quyết định đúng/sai / all reviewed decisions | UNKNOWN | Theo dõi cả harmful/neutral; không gộp hit count thành helpful |
| Knowledge ACK freshness | ACK đúng checkpoint/generation observed / expected ACKs của sample | 40 CURRENT/67 records, 27 MISSING lịch sử | Resolve cause; không đặt 100% bằng auto-ACK |
| Cache benefit | Saved proof time trên exact safe reusable opportunities | 0/117 E03, mostly cold | Demonstrated benefit + no invalid reuse; không target arbitrary hit rate |
| Monetary CAR | Full observed accepted-result cost / accepted-result denominator được đăng ký | Provider costs thiếu, UNKNOWN | Chỉ available khi coverage theo reporter đủ; derived cost tách billing |
| P5 efficacy | Preregistered ITT outcome contrast, uncertainty + quality floor | Assignment0/outcome0 | A/A healthy trước A/B; chưa có efficacy claim |

Phản chứng đóng ngay claim tương ứng: sai workspace/generation; effect lặp; semantic refusal bị terminate; initial-off tự bật; pending read được báo completed; stale report cấp quyền; source/package/epoch mismatch; controller intervention không ghi; natural label do fixture; user counterevidence sau technical pass. Giữ evidence, stop unsafe action, REPLAN theo cause; không “sửa số liệu” để giữ PASS.

## 13. Rủi ro và chiến lược kiểm soát

| Rủi ro | Mức/khả năng hiện biết | Kiểm soát và phản ứng |
| --- | --- | --- |
| Canonical/report divergence chưa biết nguyên nhân | Cao về acceptance; đã có evidence | X0 exact lineage; không restore/merge DB mù |
| Source tiếp tục đổi khi build/activate | Đã quan sát Host drift/candidate rebuild history | Freeze relevant bytes, one writer, hash trước/after; invalidate đúng proof nodes |
| Hai contract direct/central lẫn nhau | Cao về false-green | X1 mapping/revision approval; role-aware oracle |
| Runtime deadlock/loss hoặc unsafe handoff | P1/P2 source gap đã định vị | A0/A1 negative tests trước live; no blind kill/restart |
| Auth/binding có vẻ ready nhưng task wrong-target | Chưa live multi-client proof | Opaque binding pin, generation/writer local policy, T01–T07/T11 |
| Goal tự chạy nhưng mất semantic review | Nguy cơ nếu bỏ ACCEPTING | Controller required; delivery receipt; acceptance !=outcome |
| Retry storm/unknown duplicate effect | Quan trọng dù tests xanh | Durable journal, one reservation, exact reconciliation, budget/Stop fence |
| Metrics gây quyết định sai | Window/coverage/provenance thiếu đã thấy | Metric dictionary/temporality, natural/synthetic, uncertainty, no ROI claim |
| Knowledge tự xác nhận và khuếch đại sai frame | 270/272 auto-derived quality; historical counterexamples | Independent outcome + applicability + counterevidence; bounded advisory |
| Windows candidate khác Ubuntu package/OS assumptions | Candidate portability work có; live chưa verify | Exact manifests, native platform lane, no /healthz-only release gate |
| Natural-use không có người/máy B | External schedule, chưa xác định | NOT_RUN/blocker rõ, không simulation thay người dùng/máy vật lý |
| Chi phí inference/ops ngoài scope | Usage/cost coverage yếu | Explicit grant/provider authority, caps và missing-cost label; không auto upsell route |

Ưu tiên là sửa/đo rủi ro có bằng chứng. Không mở broad refactor, pentest hay tối ưu UI toàn app chỉ vì bảng có nhiều miền; mỗi implementation packet phải có symptom/criterion/oracle cụ thể.

## 14. Evidence map và cách kiểm chứng lại

### 14.1. Source/test/reference map

| Ref | File/symbol cần dùng khi triển khai | Vì sao |
| --- | --- | --- |
| S01 | [recoveryBootstrap.js](../../electron/services/recoveryBootstrap.js), `bootstrapCurrentRecoveryHost`; [tests](../../tests/recovery-bootstrap.test.js) | Stop catch/terminate/rollback, exact identity, idle handoff và deadlines |
| S02 | [runtimeOrchestrator.js](../../electron/services/runtimeOrchestrator.js), `runtimeReadiness`; [recoveryHost.js](../../electron/services/recoveryHost.js) | Role-aware readiness, source/epoch, lifecycle authority |
| S03 | [dev-ui-lifecycle.js](../../scripts/dev-ui-lifecycle.js), `statusLifecycle`; [activationEpoch.js](../../electron/services/activationEpoch.js) | Official read-only runtime projection và durable failure |
| S04 | [Recovery Supervisor](../../resources/recovery-supervisor/recovery-supervisor.ps1); [tests](../../tests/recovery-supervisor.test.js) | Installed manifest/task, startup intent, fail-closed liveness |
| S05 | [continuation_contract.py](../../resources/coding-tools-mcp/coding_tools_mcp/continuation_contract.py), [run_continuation.py](../../resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py), [driver](../../resources/coding-tools-mcp/coding_tools_mcp/continuation_driver.py) | Existing parent grants/budgets/dispatch/effects; không xây lại |
| S06 | [continuation tests](../../resources/coding-tools-mcp/tests/test_run_continuation.py), [consent HTTP tests](../../resources/coding-tools-mcp/tests/test_continuation_consent_http.py) | Parent exact/shared budget/no-progress, lost claim, persistent lane, auto-resume và consent |
| S07 | [goal_pursuit.py](../../resources/coding-tools-mcp/coding_tools_mcp/goal_pursuit.py), [goal tests](../../resources/coding-tools-mcp/tests/test_goal_pursuit.py) | Exact Goal/pagination, không chọn newest, proof không tự cover criterion |
| S08 | [controller_continuity.py](../../resources/coding-tools-mcp/coding_tools_mcp/controller_continuity.py), [tests](../../resources/coding-tools-mcp/tests/test_controller_continuity.py) | Knowledge revision/ACK/fingerprint/delivery boundary |
| S09 | [problem_lineage.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py), [lineage tests](../../resources/coding-tools-mcp/tests/test_problem_lineage.py) | Exact coverage/checkpoint/outcome và bounded derived capsule |
| S10 | [problem_resolution_journey.py](../../resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_journey.py), [accepted-result economics](../../resources/coding-tools-mcp/coding_tools_mcp/accepted_result_economics_report.py) | Read-only descriptive metrics, cost/window/missingness |
| S11 | [egri_p5_continuity_readiness.py](../../resources/coding-tools-mcp/coding_tools_mcp/egri_p5_continuity_readiness.py), [solution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/solution_economics.py) | Baseline/preregistration/A-A gates; no production side effect |
| D01 | [Boot closure plan](../BOOT_HOST_TRANSITION_CLOSURE_PLAN.md) | C01–C12/M matrix/48h và mode boundaries |
| D02 | [Continuation closure plan](../CONTINUATION_CLOSURE_PLAN.md), [single-goal plan](../SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md) | Intra-goal scope, passive measurement, host consent và budgets |
| D03 | [Shared-account plan](../TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md), [status](../SHARED_ACCOUNT_WORKSPACE_STATUS.md) | Central principal/binding/task-pin và T01–T16; chronology không thay current source |
| D04 | [Setup simplification candidate](../260922_SYSTEM_SETUP_SIMPLIFICATION_PLAN.md) | Concurrent candidate/source/package proof và blockers cần reuse |
| D05 | [Control Plane recovery runbook](../CONTROL_PLANE_RECOVERY_RUNBOOK.md), [Windows exact runbook](../WINDOWS_EXACT_VALIDATION_RUNBOOK.md), [release checklist](../RELEASE_CHECKLIST.md) | External operations/restore/package authority boundaries |
| H01 | [Cold-start report](../../.coding-tools/orchestration/reports/run-d01a5dce50c846fc8e13673cdfc8b3b3/run-summary.md), [pre-reboot report](../../.coding-tools/orchestration/reports/run-b194ab1e311e42efa1dd0614ca245037/run-summary.md), [pre receipt](../../.coding-tools/reboot-acceptance/c01-m02-machine-a-restart-1-pre.json) | Historical report/receipt còn trên disk, không canonical-current acceptance |
| H02 | [Golden HR calibration](260831_CODING_WEB_GOLDEN_HR_RESOLUTION_CASES_CALIBRATION_V1.md), [EGRI implementation plan](260901_CODING_WEB_EVIDENCE_GROUNDED_RESOLUTION_INTELLIGENCE_DETAILED_IMPLEMENTATION_PLAN.md) | Advisory historical lessons, không quyền hoặc natural proof mới |

### 14.2. Truy vấn nền tái lập (chỉ trên snapshot)

Các câu SQL dưới đây là recipe **chỉ đọc**. Mở URI `mode=ro&immutable=1` trên bản Backup API đã chụp; `PRAGMA query_only=ON`. Không copy live SQLite bằng shell hoặc chạy constructor canonical writer để report.

```sql
SELECT p.problem_id,p.current_revision,p.resolution_state,p.closed_at,
       r.criteria_count,r.contract_fingerprint,r.criteria_fingerprint
FROM problem_threads p
JOIN problem_revisions r
  ON r.problem_id=p.problem_id AND r.revision=p.current_revision
WHERE p.problem_id IN (
  'prl-22e670302757c9b7663170e226ed7c26',
  'prl-e918c7d33e70c2d304d0797e11b05fcb'
);

SELECT e.problem_id,e.problem_revision,r.status,
       COUNT(DISTINCT e.run_id) AS run_count
FROM problem_events e JOIN runs r ON r.run_id=e.run_id
WHERE e.relation_type='ENGINEERING_ATTEMPT_BOUND'
  AND ((e.problem_id='prl-22e670302757c9b7663170e226ed7c26'
        AND e.problem_revision=1)
    OR (e.problem_id='prl-e918c7d33e70c2d304d0797e11b05fcb'
        AND e.problem_revision=2))
GROUP BY e.problem_id,e.problem_revision,r.status;

SELECT checkpoint_id,run_id,status,created_at FROM checkpoints
WHERE checkpoint_id IN (
  '6fb3de41a26349f5995a6a2bd92d82f2',
  'c8f32a66c7714204bcdd64162dc20ee1'
);

SELECT event_type,COUNT(*) FROM events
WHERE event_type IN ('oracle_preflight','solution_shadow_recommended',
                     'quality_outcome_recorded','usage_event','route_selected')
GROUP BY event_type;
```

Đếm run_id từ OPEN/REVISION/feedback có thể chứa chuỗi rỗng hợp lệ: loại `run_id=''` và dùng ENGINEERING_ATTEMPT_BOUND khi cần count RUN. Kiểm tra hiện tại **không thấy nonempty dangling run_id** ở problem_events của hai Problem; không biến blank identity của event không thuộc RUN thành một data-loss finding. Ba missing report RUN ở H01 là finding khác và đã query exact IDs.

Coverage kiểm bằng metadata JSON của exact linked waves/checkpoints, current revision, accepted proof/checkpoint authority; một nonempty field bất kỳ chưa đủ cho semantic coverage. Để tính richer journey/P4/P5 dùng existing read-only reporters ở `resources/coding-tools-mcp/scripts`, chốt argv/schema trước; chạy sequential heavy snapshot reports, không dựng Runtime để đọc.

### 14.3. Validation đã làm và đề xuất chưa chạy

Đã thực hiện trong chuỗi audit/lập tài liệu này:

- Git root/branch/HEAD/status/history và relevant diff inspection; không fetch.
- Backup-API/query-only snapshot; integrity/FK; exact Problem/current revision/capsule/count/coverage/lease/missing checkpoint queries; inventory/timing/provenance metrics đọc và tổng hợp.
- Official Recovery IPC/status, OS process và exact Scheduled Task read trong E05; không action runtime.
- Bốn focused Node handoff tests đã PASS trong lượt audit liền trước tại cùng HEAD và source liên quan không đổi: lost-stop-response, exact idle packaged handoff, bounded in-flight supervision wait, exact-owner rollback. Không rerun cùng test chỉ để lập Markdown. Bốn test đó **không phủ P1/P2 negatives**.
- Đọc source và tên/assertion test continuation/consent/Goal/knowledge; **không chạy lại full Node/MCP/Cargo, không gọi provider thật** trong lượt viết tài liệu.
- Kiểm tra Markdown, local links, đủ 12/18 criterion IDs và whitespace cho file mới trước bàn giao. Kết quả cuối được ghi ở mục 15.

Các lệnh test sau là **gợi ý proof cho implementation tương lai**, chưa thực thi trong lượt tài liệu; chỉ dùng nếu packet tương ứng được giao và fingerprint đúng:

```powershell
# Recovery leaf, sau khi bổ sung regression P1/P2:
node --test tests/recovery-bootstrap.test.js

# Từ resources/coding-tools-mcp, sau thay đổi bounded continuation:
python -m pytest tests/test_run_continuation.py tests/test_continuation_consent_http.py -q

# Criterion/knowledge leaf khi có thay đổi tương ứng:
python -m pytest tests/test_goal_pursuit.py tests/test_controller_continuity.py tests/test_problem_lineage.py -q
```

Full subsystem/real-process/package/live tests chỉ sau source settled và đúng gate; không chạy E2E/reboot/fault suite như kiểm tra tài liệu. `report`, `observe`, `status` cần xác minh semantics trước khi dùng làm passive probe; tên gọi không bảo đảm không có side effect.

## 15. Kết luận và checkpoint bàn giao tài liệu

**Chọn hướng B: hội tụ central execution trên runtime/continuation hiện có, kèm X0 provenance trước closure và mapping contract có quyền.** Phần phải làm ngay không phải “reboot thêm” hoặc “xây trí nhớ thông minh hơn”, mà là:

1. Hoàn tất đối soát bằng chứng và chốt exact contract/target.
2. Sửa hai invariant handoff cùng oracle.
3. Activate đúng bytes/epoch/route/policy rồi chứng minh một task dùng được.
4. Chứng minh background dispatch thật, review delivery, Stop/budget/idempotency.
5. Thu natural outcome và coverage của từng Problem; sau đó mới đánh giá economics/knowledge improvements có hiệu quả hay không.

Tài liệu giữ rõ hai trạng thái OPEN, ba mức đầy đủ, các source mechanisms đã có, safety gaps đã định vị, historical/candidate/live evidence, sample/denominator/missingness, quyền còn thiếu và hành động tiếp theo. Đây là kế hoạch để owner review và giao work packets; không có closure hoặc quyền triển khai được tạo bởi file này.

**Checkpoint QA ngày 22/09:** đã kiểm UTF-8, tên file `260922_...md`, 16 mục cấp hai, cân bằng code fences, toàn bộ liên kết local resolve được; ma trận có đủ **12/12 + 18/18 exact criterion IDs** đọc từ canonical capsule. Các phép tính tỷ lệ chính đã kiểm lại từ raw counters; performance SHA đã đối chiếu độc lập. Scoped `git diff --no-index --check` cho file mới không có whitespace error (Git chỉ cảnh báo LF→CRLF theo môi trường). Toàn worktree có hai cảnh báo EOF đã biết ở `tasks/todo.md`/`tests/icon-source.test.js`, ngoài scope và giữ nguyên. Không chạy lại suite sản phẩm để kiểm Markdown.

Git baseline vẫn là `main@77d7347`; file nghiên cứu này untracked, chưa stage/commit. Các query/test/read-only audit jobs đã hoàn tất, không có product RUN/Job mới do việc lập tài liệu. Mọi live/mutation/release gate nêu trên còn là công việc tương lai cần authority và fresh preflight. **Exact next action đề xuất cho owner:** review/chốt X1 target-role/criteria mapping và cho phép X0 đối soát nguồn lịch sử; sau đó giao A0/A1 cùng B0/B1 source-validation theo scope đã ghi, chưa reboot hoặc mở P5.

## 16. Nhật ký triển khai và trạng thái các packet

> Tiến độ mới nhất nằm ở mục 16.5 trở đi; blocker local source authority của lượt 16.4 đã được người dùng gỡ rõ ràng. Không giả một write lease/acceptance EOCL từ quyền local này.

### 16.1. Lượt bắt đầu — 22/09/2026, 17:13–17:20 +07

Người dùng đã yêu cầu triển khai từng mục và cập nhật thường xuyên vào chính file này. Cách cập nhật: sau mỗi material wave, test/failure/replan hoặc gặp authority boundary; không hứa giám sát nền sau khi lượt xử lý đã dừng và không tự tạo automation.

**Scope đang thực hiện:** X0 forensic/read-only; X1 đối chiếu contract; cập nhật tài liệu. Chưa sửa source/test hoặc thực hiện lifecycle operation.

Preflight:

- Root `E:/DEV/Codex-web`, `main@77d73471dc896a1f1ac189b2df46529276481552`; các dirty source/evidence có sẵn được bảo toàn, không stage/reset/rebase.
- Census mới `snapshot_at=2026-09-22T10:15:09.316Z`: physical/logical SHA vẫn đúng E02; integrity `ok`, FK `0`, `mutated_canonical_ledger=false`; 17 ordinary active RUN đều `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, 6 P5 anchors, managed jobs rỗng, unbound live/stale background residue `0`.
- Tool inventory của phiên hiện tại không expose `workspace_context`, `agent_workflow`, `task_control`; không có khả năng xin write lease/record EOCL acceptance bằng public Coding Tools path từ phiên này. Không tạo “lease” hoặc “accepted” trong JSON/SQLite để thay chức năng chưa expose.
- Skill `sol-lean-codex` yêu cầu không mutation trên authoritative source nếu chưa có lane/write authority hợp lệ. Vì vậy A0/A1 source write đang dừng ở authority boundary, không phải vì cần chạy lại toàn bộ test hoặc chưa tìm được vị trí lỗi.

### 16.2. X0: đã tìm lại historical canonical proof — không còn UNLOCATED

**Kết quả mới được kiểm chứng:** blob ledger trong commit `a9fcb9974b5ca43266ec2feea1dc64c1a95d406e` chứa đủ ba RUN accepted, ba checkpoint và events cần tìm.

| Identity | Giá trị |
| --- | --- |
| Historical Git ledger blob | `bed5b266a83e4cbc3947f5dd15854d80f58f6264` |
| Original blob SHA-256 | `e7700489c3ecd85afcd2c21c36967741793fef73f36aad47a47da8f9887de9b6` |
| Bytes | 97,824,768 |
| Event tail | seq 59822, `2026-09-15T11:37:00.517Z` |
| Integrity/FK | `ok` / 0 rows |
| Problem boot trong bản lịch sử | OPEN@1, 66 RUN = 47 accepted + 16 aborted + 3 active |
| Problem continuation trong bản lịch sử | OPEN@2, 39 RUN = 16 accepted + 10 aborted + 13 active |

Phương pháp chỉ đọc: `git cat-file blob` lấy original bytes; SHA tính trên original blob. Để query không tạo file/WAL, SQLite `deserialize()` vào memory; chỉ hai byte header journal mode của **bản trong memory** đổi sang rollback-journal phù hợp in-memory SQLite, rồi `query_only=ON`. Không sửa Git object, canonical DB, index, WAL/SHM hay file snapshot trên đĩa. Vì đây là view trong memory, integrity kết quả được hiểu trong đúng phương pháp này; không khẳng định đã chạy restore acceptance trên hệ thống thật.

| RUN | Checkpoint lịch sử | Hash chain kiểm lại theo `verify_chain` source |
| --- | --- | --- |
| `dcb539e0e1694bc1bb29eed2b2e07f8b` | `8d10f27638e2498cba80edf0bcbe77ce` | 32 events PASS; head `aa9ced88aedb23cd72228b8470355a048e8f863ff3e49570b934c5a682977148` |
| `d01a5dce50c846fc8e13673cdfc8b3b3` | `6fb3de41a26349f5995a6a2bd92d82f2` | 32 events PASS; head `562bbc4b4063ea9790f0ae6b5f3d0174c273df84db579d13fbb7ca6e781f5808` |
| `b194ab1e311e42efa1dd0614ca245037` | `c8f32a66c7714204bcdd64162dc20ee1` | 62 events PASS; head `9ecba1536c9c53a57d9f7349078e2cbf4f6f8e41e899879ca211e54099897b0b` |

Hash chain là **per RUN**, không phải một chain toàn bộ events theo global seq. Một check adjacency toàn bảng ban đầu cho nhiều chỗ không khớp vì trộn các RUN; đã loại bỏ check sai abstraction này. Phép kiểm cuối tái tính SHA-256 trên canonical JSON đúng `orchestration_ledger.py::verify_chain`, theo từng RUN; không có failed sequence trong 126 events của ba RUN. Không gọi kiểm adjacency global ban đầu là corruption.

So sánh snapshot hiện tại E02 với historical blob theo exact primary identity và toàn bộ column values ở sáu bảng:

| Bảng | Historical / current rows | Chỉ historical | Chỉ current | Row chung bị thay đổi |
| --- | ---: | ---: | ---: | ---: |
| events | 25,822 / 25,694 | 128 | 0 | 0 |
| problem_events | 307 / 304 | 3 | 0 | 0 |
| runs | 557 / 554 | 3 | 0 | 0 |
| waves | 892 / 888 | 4 | 0 | 0 |
| checkpoints | 273 / 270 | 3 | 0 | 0 |
| proofs | 947 / 942 | 5 | 0 | 0 |

Kết luận chỉ áp dụng **sáu bảng đã so**. Chưa so toàn bộ DB, leases, journals, archives, schema/migration compatibility, hiện trạng effects và file attestations để quyết định restore. Không suy bảng lịch sử là replacement an toàn cho toàn canonical live.

### 16.3. X0: đã xác lập divergence ở Git merge

1. `a9fcb99` và `3f1bd8a` là hai commit sibling, cùng parent `cffd2ac`.
2. `a9fcb99` chứa ledger blob `bed5b266…`, đủ tail tới seq 59822; `3f1bd8a` chứa `ab3ebf3f…`, tail chỉ tới 59694.
3. Merge `000938f401b6d6605b0b94474cbc87b5171c2909` ngày 15/09 18:56:40 có parent thứ nhất `7958f5c…` và parent thứ hai `a9fcb99`. Tree của merge giữ ledger `ab3ebf3f…`, trùng parent thứ nhất, không giữ tail của parent `a9fcb99`.
4. HEAD hiện tại chứa ledger `be178d84…` có cùng tail cũ; các later commits đổi giữa các blob chứa tail cũ. Cả hai nhánh sibling đều là ancestor của HEAD, nên lịch sử có thể truy hồi bằng exact Git object mà không rewrite history.

**Proven cause ở lớp Git:** merged tree không bảo toàn phần tail canonical có trên parent `a9fcb99`. Chưa biết hành động/command/actor cụ thể đã chọn binary conflict resolution nào; không quy trách nhiệm hoặc kết luận thao tác thủ công/automation nào khi chưa có log.

`scripts/stage-coding-tools-delivery.py::verify_index` hiện kiểm receipt↔staged blob, size, schema và SQLite integrity. Các kiểm tra đó không tự chứng minh event history là superset của mọi merge parent. Vì vậy một receipt mới có thể nhất quán với một ledger thiếu tail; việc sửa cần **guard semantic history continuity** tại delivery/merge workflow hiện có, không chỉ thêm checksum khác.

Gói bổ sung X0-G (đề xuất sau khi có write authority): kiểm required RUN/event/checkpoint ancestry theo exact IDs/hashes và archive/maintenance provenance; không chỉ so max seq hoặc file size, không bác nhầm archival hợp lệ; có fixture hai sibling DB/merge chọn tail cũ phải fail, append hợp lệ pass, divergent common event hash fail, archive đầy đủ có receipt được xử lý đúng. Không thêm DB competing writer và không tự merge rows để guard xanh.

### 16.4. Bảng tiến độ sau lượt đầu

| Packet | Trạng thái thực tế | Proof mới / còn thiếu | Exact next action |
| --- | --- | --- | --- |
| X0 discovery | **LOCATED + VERIFIED_RUN_CHAINS** | Đủ ba historical RUN/checkpoint, sáu bảng so sánh, merge ancestry | Chuẩn bị supported isolated reconciliation/restore plan, kiểm các bảng/receipts/effects còn lại |
| X0 canonical recovery | **NOT_RUN / AUTHORITY REQUIRED** | Canonical live vẫn 63 RUN boot; chưa restore/reconcile | Owner/lane recovery hợp lệ + fresh quiescence/effect gate trước mutation |
| X0-G continuity guard | **PROPOSED** | Existing receipt guard không chứng minh merge-parent history completeness | Sau write authority: focused failing fixture rồi guard nhỏ trong existing delivery path |
| X1 contract | **BASELINE VERIFIED / NO REVISION CHANGE** | Giữ 12 và 18 criteria; central role/matrix mapping trong kế hoạch | Không tự đổi canonical criterion hoặc grant |
| X2 measurement | **BASELINE RECORDED** | Window/hash/census và nguồn historical đã ghi | Triển khai instrumentation chỉ khi có lane/source authority |
| A0/A1 | **BLOCKED_AUTHORITY, SOURCE UNCHANGED** | Chưa có EOCL write lease/public control path trong phiên; lỗi source vẫn còn | Cấp lane/lease qua connector phù hợp, hoặc explicit override cho local Desktop candidate lane với EOCL acceptance riêng |
| A2, B0–B4 | **NOT_STARTED** | Chưa dùng prose plan như proof thực thi | Theo dependencies sau source/lane gate; không provider dispatch chưa consent |
| A3–A5, K, R0 | **NOT_RUN / DEPENDENCY GATED** | Không install/activation/reboot/natural experiment/release | Authority/target/consent riêng và prerequisite proof |

**Operator checkpoint:** hoàn thành phần discovery và chứng minh nguyên nhân X0 ở Git tree; chỉ Markdown thay đổi. Main/HEAD không đổi; không tạo RUN, không active job từ các lệnh audit còn chạy. Source implementation chưa thực hiện, không giả là đã sửa P1/P2. Điểm cần người dùng quyết định để tiếp tục: cho phép lane Codex Desktop sửa candidate source/test cục bộ cho A0/A1 với local proof, giữ EOCL acceptance/activation chờ controller; hoặc cung cấp public Coding Tools path có write lease cho exact packet. Không tự cấp một trong hai phương án bằng câu ghi trong tài liệu.

### 16.5. A0/A1 — local authority và RED→GREEN bước đầu, 22/09 khoảng 17:21–17:26 +07

- Người dùng đã cho phép tiếp tục lane Codex Desktop để sửa source/test cục bộ, giữ EOCL acceptance và activation riêng. Không xin lại cùng quyền, không tạo giả RUN/lease/receipt.
- Thêm regression trước sửa: bốn semantic-refusal cases và năm off/unknown/partial/manual-stop/epoch-change rollback cases đều FAIL trên code cũ; Node báo 11 fail gồm hai parent tests và chín subtests. Refusal đi tới terminate; các rollback cases gọi start=1 thay vì 0.
- Sửa local candidate `recoveryBootstrap.js`: chỉ xử lý các mã transport-loss cụ thể; semantic/unknown refusal giữ error gốc và không đánh dấu stop có effect để tự rollback. Mất response cần authenticated forced snapshot chứng minh runtime/native/Tunnel đã dừng, không busy/manual-stop và đúng workspace; thiếu proof trả `RECOVERY_BOOTSTRAP_STOP_UNCONFIRMED`, không terminate/spawn.
- Sửa `recoveryIpc.js` đánh dấu `recoveryResponseReceived=true` trên lỗi response, để semantic handler dùng code giống OS (ví dụ ECONNRESET) không bị hiểu nhầm là socket error. Không thay public MCP surface hoặc quyền IPC.
- Compensation chỉ khi fresh pre-stop snapshot chứng minh runtime đã chạy đủ theo role; sau failure phải exact old descriptor/PID/start-token, snapshot stopped, cùng role/workspace/epoch và không manual-stop. Ban đầu idle/off/unknown/partial không tự start. Failed receipt giữ nguyên.
- Lượt focused bootstrap sau sửa đầu tiên: **34/34 PASS**. Tiếp tục bổ sung transport-unconfirmed negatives và real-loopback IPC response-provenance assertion; chưa dùng kết quả này như final integrated proof.
- Không restore ledger, không kill/restart/install/package/deploy; mọi process/IPC trong tests là fixture tạm, không runtime sản phẩm. Next: chạy affected bootstrap + Recovery Host tests, review diff/adjacent identity guards rồi ghi final local checkpoint.

### 16.6. A0/A1 — checkpoint local source proof, 22/09 khoảng 17:30 +07

**Đã hoàn thành gói source/test A0/A1 trong lane Desktop được người dùng cấp; không claim EOCL accepted hoặc runtime fixed.**

Files thuộc packet:

| File | SHA-256 final local bytes |
| --- | --- |
| `electron/services/recoveryBootstrap.js` | `d3c2b63ccf67ebc8f89cf5a0cdea7a2dac6b850ef8a53d56f4869152a1e52e0f` |
| `electron/services/recoveryIpc.js` | `b418f619c4a2c65f05734865f4ecb4ff42de33ae087a9557c026cc2f8f7df897` |
| `tests/recovery-bootstrap.test.js` | `a5f48d4049fbb6b01d9a79f2f706bf30a868af5a37b15efa996008402fce3490` |
| `tests/recovery-host.test.js` | `7f85e734ce7fc13a83bfc86dd4ec5a8760529e7b4138a504acfaf5ff113e367f` |

**Validation thực tế:**

1. RED trước patch: chín discriminating subcases của P1/P2 fail như 16.5; không che failure này.
2. Bootstrap sau patch đầu: 34/34 PASS.
3. Sau bổ sung transport-unconfirmed và central rollback/IPC provenance: `node --test tests/recovery-bootstrap.test.js tests/recovery-host.test.js` **82/82 PASS**, exit 0, khoảng 19.16s. Có real-loopback IPC assertion cho semantic handler trả code ECONNRESET nhưng `recoveryResponseReceived=true`; đây là isolated test server, không primary runtime.
4. Review liền kề siết `recovering` phải **explicit false**; missing/true không cho compensation. Bổ sung hai negative subcases và chạy lại **chỉ affected bootstrap file**: **41/41 PASS**, exit 0, khoảng 9.40s. Không cộng hai lượt thành 123 tests độc lập hoặc gọi 82/82 là rerun trên final bootstrap hash; IPC source/test không đổi sau lượt 82.
5. Diff review + scoped `git diff --check` PASS; chỉ cảnh báo LF→CRLF theo Git môi trường. Existing changed-descriptor negative vẫn kiểm hai descriptor reads với baseline running, không vô hiệu hóa đường rollback để làm test xanh.

**Hành vi đã chứng minh trong local tests:**

- Semantic refusal (generic/busy/authority/OS-like code) giữ nguyên error, zero terminate/spawn/start; receipt failed giữ code gốc.
- Transport loss chỉ tiếp tục khi forced authenticated runtime snapshot chứng minh primary/native/Tunnel đã dừng đúng workspace; running/unknown/native-alive trả STOP_UNCONFIRMED với zero lifecycle effect tiếp theo.
- Initial off/unknown/partial, manual-stop xuất hiện, epoch changed, recovery active/unknown: không auto start.
- Runtime trước đó đầy đủ running được compensation khi exact owner còn nguyên và fresh stopped snapshot cùng role/workspace/epoch; central mode không đòi local direct Tunnel phải được bật để nhận biết baseline running.
- Existing idle-packaged handoff, bounded snapshot waits, trusted-source checks, changed-owner/PID identity, immutable failed receipts và activation guards vẫn qua regression.

**Giới hạn/điều chỉnh có chủ đích:** rollback API `runtime.start` khởi động cả runtime, không restore từng service theo mask. Vì vậy partial hoặc unknown baseline **không auto compensate**, giữ failure để operator/controller reconcile; không thêm API restore tổng quát trong packet này. Snapshot là observation, không phải durable idle lease; chưa chứng minh toàn bộ concurrent lifecycle/installed reboot matrix hoặc source–runtime activation. A2/A3 vẫn phải xử lý oracle/end-to-end và exact loaded identity trước khi claim boot/recovery closure. Chưa đổi revision contract, cấp continuation consent, gọi paid provider hoặc sửa các guard acceptance khác.

**Trạng thái packet mới nhất:**

| Packet | Trạng thái | Còn thiếu / next action |
| --- | --- | --- |
| X0 discovery | LOCATED + VERIFIED_RUN_CHAINS | Canonical recovery và X0-G guard chưa thực hiện |
| A0 | LOCAL_SOURCE_PROVED | Exact EOCL acceptance và loaded-runtime/package proof riêng |
| A1 | LOCAL_SOURCE_PROVED trong scope trên | Full lifecycle race/installed matrix chưa được phép suy từ test fixtures |
| A2 | NEXT — chưa bắt đầu | Role-aware end-to-end receipt/verifier và false-green negative cases |
| A3–A5 / B / K / R | Chưa thay đổi trạng thái | Theo dependencies/quyền riêng trong kế hoạch |

**Operator-visible checkpoint:** đã sửa bốn source/test files và cập nhật file Markdown này; `main@77d7347` không đổi, không staged/unmerged, giữ toàn bộ dirty work khác. Tests đã terminal, không còn test process từ packet được quan sát đang chạy. Không tạo/cấp giả RUN/lease/EOCL checkpoint; không restore ledger, restart/kill/reboot, package/install, commit/push/release/deploy. **Exact next action:** review/adopt exact A0/A1 bytes qua controller khi public path sẵn sàng; bước source kế tiếp là A2, không activation mù và không coi hai Problem OPEN đã đóng.

### 16.7. A2 — offline consistency oracle, 22/09 khoảng 17:33–17:40 +07

**Đã triển khai phần oracle source của A2**, không sửa nghĩa của packaged smoke hiện có và không chạy smoke executable/installer. Scope mới đúng hai file:

| File | SHA-256 final bytes |
| --- | --- |
| [scripts/verify-boot-acceptance.js](../../scripts/verify-boot-acceptance.js) | `b094d3220bb31d2fb704424d7d12aeabdcba76350246aa898e6b11d2e0a4253e` |
| [tests/boot-acceptance.test.js](../../tests/boot-acceptance.test.js) | `fb265f896fa60ed079b4e8a50fbfe3d922ab525d3369a3b4709f2ab55369ee2f` |

#### Contract và ranh giới authority

Verifier chỉ đọc hai JSON packet normalized schema v2: expected manifest do owner freeze và observed receipt do reader/collector cung cấp. Nó không tự thu bằng chứng, không gọi IPC/network/connector, không khởi tạo canonical writer và không cấp quyền lifecycle. Những normalized fields mới dưới đây **không phải public MCP response schema**; adapter ở bước tiếp phải map từ actual authenticated response, không yêu cầu server giả các field đó.

Verdict chỉ gồm `INVALID_INPUT`, `NOT_PROVEN`, `EVIDENCE_CONSISTENT`. Luôn có:

```json
{
  "authority_granted": false,
  "live_accepted": false,
  "receipt_authenticity_verified": false
}
```

Ngay cả JSON tự viết với các boolean true cũng **không thành live proof**: consistency check không xác thực provenance/chữ ký/receipt authority. Controller phải đối chiếu original authenticated reader/client evidence và exact criterion coverage. Không đưa fixture test vào `.coding-tools` như receipt live.

#### Các gate đã implement

- Exact problem ID/revision/criteria fingerprint; expected role và connector policy phải explicit.
- Before→after boot ordering, boot mode, host packaged PID/instance/start-token mới, host-start sau boot, cùng activation epoch; PID được tái sử dụng không tự fail nếu instance/start-token mới có bằng chứng.
- Package/executable/Supervisor-script SHA, Supervisor healthy/fresh/installed trỏ đúng host PID, startup intent enabled. Intent OFF trả chưa chứng minh **auto-start acceptance**, không bị đổi thành ON và không được diễn giải bản thân OFF là product defect.
- Host/MCP running revision = disk revision = expected manifest, no update pending; READY/open epoch/operation và primary/native/components/fullyReady true.
- Client read phải ok/completed/workspace_accessed, đúng device/endpoint/workspace generation/process/server/epoch/contract, có request ID và nằm sau boot. Pending handshake không thay actual workspace read.
- Direct role cần Tunnel ready và connector proof strict hoặc exact/reviewed-compatible theo explicit expected policy; compatible không được coi strict rediscovery.
- Central role không đòi local Tunnel. Cần localReady/centralConnected/authorityReady, fresh route, policy chưa hết hạn, đúng principal/binding/device/endpoint/workspace generation, post-boot client discovery.
- Observations không ở tương lai; after/client/Supervisor/route/discovery phải đạt freshness window **30 giây của verifier v2**, không thay đổi token TTL hay runtime connector policy. Timestamp milliseconds được normalized từ nguồn thật; historical receipt cũ không được cập nhật timestamp để pass CLI.
- Attempt history có nội dung, final succeeded operation khớp activation, manual repair count=0 cho sample đang chứng minh không cần repair. Verifier không tự xác minh tính đầy đủ của history do collector cung cấp; giữ authority gate riêng.
- CLI chỉ nhận regular JSON file tối đa 256 KiB mỗi input; bounded read không đọc vô hạn nếu file lớn lên sau stat; reject symlink theo preflight/OS support, luôn đóng fd. Không echo path/payload/parser excerpts; output chứa hash exact input và failure codes.

#### Sử dụng ở giai đoạn có actual observations

Lệnh dưới đây là **cú pháp**, chưa chạy trên receipt live:

```powershell
node scripts/verify-boot-acceptance.js <expected-manifest.json> <observed-receipt-v2.json>
```

Exit 0 = evidence internally consistent, **không đồng nghĩa LIVE_ACCEPTED**; exit 1 = thiếu/mismatch proof; exit 2 = input không hợp lệ. Không thêm `--force`/bypass hoặc chức năng sửa receipt.

Các nhóm field normalized bắt buộc để collector implement tiếp:

| Input | Nội dung |
| --- | --- |
| expected | schema_version=2; problem_id/revision/criteria_fingerprint; execution_role; device/endpoint/workspace/generation; package/executable/Supervisor-script SHA; revisions.recovery_host/coding_mcp; contract SHA; startup_intent; connector_policy; central principal/binding hoặc reviewed_ack_sha256 cho compatibility |
| receipt root | schema_version=2; exact Problem fields; before; after; client; attempts; manual_repair_count |
| before | boot_time_ms, observed_at_ms, host.instance_id/process_start_token |
| after | boot_time/mode/observed_at; target + role + package/startup; host identity/start/epoch/executable SHA; Supervisor identity/script/host pointer; revisions; runtime; central_route nếu central |
| runtime | Existing readiness concepts + process/server identity + toolContract + activationEpoch; direct connector proof hoặc central readiness, không lấy từ cached client schema |
| client | Original-request correlation, actual successful workspace read và exact target/runtime/contract; central principal/binding/discovery observation nếu central |

Schema fixture đầy đủ nằm trong `fixture()` của test file và chỉ có ý nghĩa **synthetic unit input**. Collector phải giữ original receipts/content-free references riêng để controller verify, không copy fixture làm sample thực.

#### RED→GREEN, QA và trạng thái

1. First oracle + negatives: 34/34 PASS.
2. Review phát hiện bộ kiểm đầu chưa ràng buộc host-start, host epoch, Supervisor target/script và final attempt. Thêm negatives trước correction: sáu subtests + parent FAIL, trong đó parent cũng kiểm expired central policy. Đây là lỗi **candidate oracle mới**, không khẳng định runtime sản phẩm đã gây các false-green này.
3. Bổ sung các gate đó: 43/43 PASS cùng packaged-smoke unit tests.
4. Bổ sung fresh-but-pre-reboot discovery và bounded CLI input tests. Final `node --test tests/boot-acceptance.test.js tests/packaged-recovery-smoke.test.js`: **45/45 PASS**, exit 0, khoảng 0.37s. Bộ packaged smoke unit test không launch packaged app.
5. Scoped whitespace check hai file mới đạt; các A0/A1 source và existing smoke script không bị sửa trong A2. Không cần rerun suite A0/A1 trên cùng relevant bytes.

| Gate | Trạng thái sau lượt này |
| --- | --- |
| A2 offline oracle + false-green unit regression | **LOCAL_SOURCE_PROVED** |
| A2 reader/collector mapping từ official runtime + actual client evidence | **NOT_IMPLEMENTED / NEXT** |
| A2 provenance và real post-reboot receipt | **NOT_RUN**, cần actual observations và controller verification |
| A3 controlled activation / A4 reboot / closure | Chưa mở; không chuyển source proof thành quyền thao tác |

**Checkpoint:** chỉ thêm verifier/test và cập nhật Markdown trong lượt này; `main@77d7347`, không stage/commit, giữ dirty work khác và A0/A1 candidate. Test jobs đã terminal. Không cập nhật receipt ngày 15/09, không ghi canonical DB/EOCL acceptance, không collector probe/live client call, restart/reboot/install/deploy/push. **Exact next action:** nối adapter chỉ đọc vào các authenticated readers hiện có và xác minh origin/correlation của client receipt; chỉ sau đó thu một sample thật khi A3/A4 được phép. A2 toàn phần chưa được đánh dấu hoàn tất.

### 16.8. A2 — official IPC reader và live observation, 22/09 khoảng 17:43–17:48 +07

Lượt trước được phân loại **PROGRESS** vì đã thêm oracle source/test thực; mục tiêu không thu hẹp thành hoàn thành oracle. Lượt này tiếp tục local Desktop lane, bảo toàn các concurrent files mới ở `deploy/prepare-control-plane-activation.py` và `control-plane/tests/test_activation_config.py`; không đưa chúng vào packet A2 hoặc nhận proof của tác vụ khác làm proof của lượt này.

Files mới:

| File | SHA-256 |
| --- | --- |
| [collect-boot-runtime-observation.js](../../scripts/collect-boot-runtime-observation.js) | `dc722ec666e4b87d2468505025cdd9d0d46f4f6dba0f6ef53ef8ace5667e56c9` |
| [boot-runtime-observation.test.js](../../tests/boot-runtime-observation.test.js) | `5299273f04e8733e916a072303f8177c8e44e56ff332be5444fcdc21bdf30113` |

Adapter dùng `RecoveryIpcClient` hiện có; bắt buộc exact workspace absolute, descriptor PID/instance/start-token. Chỉ gọi `recovery.status`, `runtime.lightweight_snapshot`, `runtime.identity_observation`, đều kèm expected identity; kiểm descriptor sau đọc, host/epoch agreement và đúng workspace. Không dựng raw HTTP, không gửi discovery hoặc workspace_context giả.

Projection chỉ whitelist fields content-free; không xuất token/descriptor/raw settings/path/exception message. Missing boolean giữ null, không đổi false/true ngầm. Timestamp host/cache/identity giữ nguyên từ nguồn, `collected_at_ms` là clock riêng; timestamp thiếu/future/cache quá 30s trả `STALE_OR_INCOMPLETE`, không “refresh” observation bằng giờ collector. `OBSERVED` chỉ nghĩa đọc được snapshot, **không có nghĩa READY hoặc accepted**.

Validation: `node --test tests/boot-runtime-observation.test.js tests/boot-acceptance.test.js` **49/49 PASS**. Bao gồm stale timestamp không được làm mới, unknown không thành false, wrong workspace dừng trước identity query, descriptor/epoch replacement không trộn snapshot, secret redaction và chỉ có ba read actions đúng identity. Không chạy lại toàn bộ bootstrap suite vì relevant A0/A1 bytes không đổi.

Đã chạy thật, chỉ đọc:

```powershell
node scripts/collect-boot-runtime-observation.js --workspace E:\DEV\Codex-web
```

Observation `collected_at_ms=1790073953799` (22/09 17:45:53.799 +07), runtime source timestamp `1790073952265`, identity source `1790073953798`:

- `status=OBSERVED`, workspace match; Host PID 14300, instance `f5ed03009310a9e4a25d80a7b20301bb`, **development**.
- Host running `80f71aa1…`, disk `961519d4…`, update_pending=true; MCP running=disk `396e1692…`, update_pending=false.
- MCP/native true, Tunnel false; role central_executor; localReady/componentsReady/centralConnected/authorityReady/fullyReady đều false.
- Epoch `activation-mucbq2r3-51dffc08603d42b6c30e1413ec68862f`, projection UPDATE_INCOMPLETE, admission đóng; `identity_current=false`.
- Process `wo7dJSwX_m-JDV1j`, server `ta0GlVny6oNE9w_w`; identity/runtime contract cùng `bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0`.
- Connector CHANGED_NEEDS_DISCOVERY; client=null; authority_granted/live_accepted=false. Không export raw credentials hoặc endpoint URL.

**Còn thiếu, không tự điền từ expected manifest:** actual client workspace read/discovery provenance; boot before/after; package/executable/Supervisor hashes; central binding/policy receipt; startup/attempt history. Output reader schema v1 là partial observation, **không** giả thành reboot receipt v2 hoàn chỉnh. Chưa nối tự động collector với verifier để PASS bằng cách lấy expected values làm observed values. Fresh current-process client proof vẫn cần real client có authority; source có thể tiếp tục hoàn thiện passive evidence correlation, nhưng không đóng live gate khi thiếu nó.

### 16.9. B1 — focused continuation safety proof, 22/09 khoảng 17:46–17:48 +07

Không viết lại parent grant/driver đã có. Đọc package AGENTS và test fixture isolation trước khi chạy:

```powershell
# cwd: E:\DEV\Codex-web\resources\coding-tools-mcp
python -B -m pytest tests/test_run_continuation.py -q -k 'goal_episode or restart_with_pending_dispatch or patch_budget_is_atomic or execution_rebind or lost_bridge_ownership'
```

Kết quả **11 passed, 39 deselected in 20.27s**, exit 0. Tập chọn có exact goal/controller-fenced contract, materialized child, parent revoke/shared budget/no-progress, matching child binding, atomic patch exhaustion, lost bridge ownership, pending dispatch sau restart và cross-endpoint/successor-epoch rebind. Tests dùng temp ledgers/mocks; không provider dispatch/real grant và không sửa canonical workspace ledger.

Fingerprint source kiểm chứng:

| Input | SHA-256 |
| --- | --- |
| continuation_contract.py | `d932257853817b16c8683641d3e99341d1c3fecad60d3c3cfc69f068f5ea92da` |
| run_continuation.py | `dbcbaef2173ff7ef1430f352d5faa93268bb568f471e7e8a43c0d0055e2bca54` |
| continuation_driver.py | `f8016eff3c82d4c4251fbbee400e926df49ad2432cf3af1e03f59561e168d780` |
| test_run_continuation.py | `d594fd6e01ea86f18122b95bdbbdd2b6f89854c91b392c5e7b8c90f90f4926bb` |

B1 ở mức **FOCUSED_SOURCE_PROOF cho tập nêu trên**, chưa toàn bộ process fault matrix, source acceptance, actual background inference hoặc BG10/BG14 natural outcome. Không coi 11 tests như bao phủ đủ 18 criterion.

**Completion audit cuối lượt:** X0 historical proof tìm được nhưng canonical recovery chưa chạy; A0/A1 local proved chưa loaded; A2 oracle/IPC reader proved nhưng client/reboot/package/provenance chưa đầy đủ; B1 focused green, B2/B3/B4 live còn mở; K/experiment/release còn gate. Do đó mục tiêu **ACTIVE, chưa COMPLETE**. Blocker chưa qua ba goal turns liên tiếp và vẫn còn source/evidence work an toàn, không đánh dấu BLOCKED.

**Checkpoint:** chỉ thêm reader/test và cập nhật Markdown; HEAD main@77d7347, không stage/commit hoặc source conflict. Node/Python test handles đều exit 0 và đã terminal. Không restore DB, acceptance giả, runtime restart, reboot, package/install/deploy/push hoặc paid inference. Next: tiếp tục exact client-receipt correlation/normalization và các B1 effect-journal guards còn lại; duy trì missing-evidence gate trước A3/A4 và actual natural Goal.

### 16.10. A2 client-contact evidence + B1 journal proof — 22/09 khoảng 17:50–17:56 +07

Lượt trước là PROGRESS; phiên hiện tại vẫn không expose public Coding Tools `workspace_context`/`task_control`/`agent_workflow`. Không dùng raw HTTP hoặc attestation tự dựng để tạo actual client receipt. Thay vào đó hoàn thiện source path để **lời gọi thật sau activation** tự mang evidence đúng tầng.

**Thay đổi:** `runtime_activity.py::_record_successful_rpc_contact` bổ sung `workspace_read` content-free vào existing attested contact receipt. Chỉ ghi khi response structured `workspace_context` completed=true/workspace_accessed=true, activation admission mở, exact process/server/epoch/workspace/endpoint/generation khớp; transport vẫn phải qua existing attested ChatWeb guard trong `_record_client_contact`. Request ID arbitrary text được hash thành `rpc-<sha256>`; không lưu raw path/entries/source/request text. Không tạo table/DB/writer mới và không đổi tám public tools.

`connector_client_contact()` chỉ expose phần read khi contact còn current; epoch đổi thì read không còn current. Receipt vẫn là observation trong process, không phải durable acceptance hoặc bằng chứng client đã nhận response. Không biến `workspace_read` thành discovery; existing discovery semantics giữ riêng. Later contact không có completed read trong cùng record slot không được re-date read cũ. Slots của execution-context khác vẫn riêng; downstream reader phải chọn/correlate đúng target/request, không tự lấy latest rồi cấp quyền.

**Proof:**

- `python -B -m pytest tests/test_stateless_http_2026.py -q -k 'completed_workspace_read or unattested_workspace_response or tools_call_records_current_contact or activation_pending_tool_error'`: **4 passed, 34 deselected, 7.73s**, final exit 0. Bao gồm actual isolated HTTP call với fixture attestation, content-free request correlation, epoch invalidation, pending/false completed, endpoint process/server/epoch/workspace mismatch, untrusted caller và no fabricated discovery.
- Một lượt intermediate 1 failed/3 passed do negative fixture tạo contact dưới execution-context khác trong khi slot cũ vẫn còn; đã sửa fixture để kiểm từng negative sample độc lập, không thay product guard để test xanh. Không gọi lỗi fixture này là runtime data loss.
- `python -B -m pytest tests/test_run_continuation.py -q -k 'reserved_action_release or effect_journal_is_written or effect_observation_is_idempotent or effect_backups or patch_context_drift or controller_reconciliation_terminalizes'`: **8 passed, 42 deselected, 10.47s**. Kiểm refund chỉ trước dispatch/no effect, immutable pre-effect journal, conflicting terminal rejection, backup/reobserve, drift không ghi effect và classified reconciliation. Không đổi continuation source; không có real provider/live canonical mutation.
- `check_module_size.py` **FAIL pre-existing**: controller_continuity 1612, coordination 1836, run_continuation 2452, workflow_tools 1640 lines; từng file có đúng số dòng đó ở HEAD trước packet. Module thay đổi runtime_activity 618→662 lines, trong budget 1600. Không tăng allowlist hoặc refactor bốn module ngoài scope. Repository-wide size gate chưa PASS.
- Scoped diff whitespace PASS, không staged/unmerged. SHA runtime_activity.py `b11e3c32549f407faf78765d70bd92829dcddf1e8da84045f18b34b3e954b424`; test_stateless_http_2026.py `c6621e3868ea9dfc9bb236e718758b354d565d71972060b654ab75d5713bab22`.

**Còn thiếu:** expose sanitized completed-contact qua official Recovery identity observation/collector và map target/request tới oracle; nguồn central OAuth/binding khác attested ChatWeb direct cần contract riêng, không giả central discovery từ local contact. Chưa activated source MCP mới, chưa real-client receipt, chưa reboot/installed/natural sample, chưa X0 canonical recovery hoặc EOCL acceptance. Một local HTTP fixture không đóng C09/C12/BG10/BG14.

**Operator checkpoint:** thay đổi đúng runtime_activity.py + focused test + Markdown trong lượt này; main@77d7347, giữ dirty work khác. Test sessions đều terminal; không restart/kill/install/deploy/restore/commit/push hoặc paid inference. Mục tiêu ACTIVE, chưa complete và chưa ở impasse: next là nối read-only Host/collector projection có exact target filtering; sau đó mới đánh giá live receipt gate và authority vận hành cần bổ sung.

### 16.11. A2 Host→collector completed-contact projection — 22/09 khoảng 17:57–17:59 +07

Previous turn=PROGRESS; đã kiểm lại HEAD/status và cuối file trước khi sửa. Không suy từ số token/ý định rằng có process đang chạy. Goal vẫn active và các test của lượt trước đã terminal.

`recoveryHost.js::buildMcpIdentityObservation` nay expose `workspace_read` bằng whitelist content-free, chỉ khi MCP identity/epoch/admission current, contact attested và current, completed read đúng process/server/epoch/contract, target IDs/generation hợp lệ, request hash đúng format, timestamp không future/quá 30s. Không đưa raw health/contact extras hoặc credential/path lên IPC. Missing/untrusted/stale/malformed trả null; observation vẫn không cấp authority.

`collectBootRuntimeObservation` nhận optional `expectedClient` từ caller của API JavaScript, bắt buộc exact device/endpoint/workspace/generation/request hash trước khi đưa read vào `client`. Không chọn latest contact làm target mặc định. `delivery_confirmed=false` luôn giữ vì server observation không chứng minh client nhận response. CLI hiện chỉ đọc runtime, chưa nhận correlation packet, do đó CLI mặc định vẫn client=null; không giả đây là full collector end-to-end. Central principal/binding và discovery provenance vẫn có gate riêng, không suy từ direct ChatWeb contact.

Validation:

- `node --test tests/boot-runtime-observation.test.js tests/boot-acceptance.test.js`: **50/50 PASS** (0.36s), gồm Host sanitizer→collector API fixture, omitted/wrong request correlation, invalid generation/epoch/completion/stale/attestation, redaction và no delivery claim.
- `node --test --test-name-pattern='identity observation|read-only context|central bridge admission' tests/recovery-host.test.js`: **3/3 PASS** (0.26s) ở affected consumers. Không launch runtime sản phẩm.
- Scoped whitespace checks PASS (chỉ cảnh báo LF→CRLF). Không rerun unchanged Python tests từ 16.10.

Exact local SHA-256:

| File | Hash |
| --- | --- |
| electron/services/recoveryHost.js | `3d8f6d9f7d0e5403962acdfdfc87081c38d0252f3fba2269d621ecac322ad585` |
| scripts/collect-boot-runtime-observation.js | `b11d781cde1f56ffc4699a392dba9b5e0d9600dd3990a1d11070091f132ee889` |
| tests/boot-runtime-observation.test.js | `c725bcbefba3b32100b95353b96cb04fb58eb585b61a9adc61036a94bd3dacf6` |

**Outcome audit:** A2 source pipeline từ MCP attested contact→Host whitelist→collector exact filter có focused proof, chưa loaded/life-cycle proof. Không có current client call thật trong phiên (public Coding Tools connector chưa expose), không before/after reboot, source acceptance/activation, central binding receipt hoặc natural 48h. X0 vẫn chưa restore. Không đóng hai Problem hoặc đánh dấu goal complete.

**Checkpoint/next:** thay đổi ba file trên và Markdown; main@77d7347, bảo toàn WIP khác, test handles terminal. Không restart/reboot/install/deploy/restore/commit/push/paid dispatch. Tiếp theo hoàn thiện explicit correlation input/operator receipt path và đối chiếu lại scopes cần owner cấp trước A3; tránh tiếp tục thêm synthetic tests chỉ để tăng tổng PASS khi blocker còn là actual client và operational authority.

### 16.12. A2 explicit CLI correlation — 22/09 khoảng 18:00–18:01 +07

Previous turn=PROGRESS. HEAD main@77d7347 và relevant worktree được kiểm lại; không thay các concurrent Control Plane/deploy files.

Collector CLI đã nối tới expectedClient API của 16.11. Chấp nhận một bộ non-secret target IDs + generation + request hash đầy đủ, không nhận partial/duplicate/unknown flags, generation fractional/overflow, hoặc arbitrary raw request text. Validation diễn ra **trước IPC**. Nếu có correlation request mà client=null, exit 1 kể cả runtime `OBSERVED`; không dùng runtime-read success thay client proof.

```powershell
# Cú pháp vận hành, chưa chạy với client evidence thật:
node scripts/collect-boot-runtime-observation.js --workspace E:\DEV\Codex-web `
  --device-id <device-id> --endpoint-id <endpoint-id> --workspace-id <workspace-id> `
  --workspace-generation <positive-integer> --request-hash <64-lowercase-hex>
```

Hash là phần digest của `rpc-<sha256>` do source contact ghi cho JSON-RPC request ID của **đúng request được theo dõi**; không tự lấy latest receipt/request từ health rồi gọi đó là independent client correlation. Caller/operator cần nguồn request correlation từ client/transport được phép. Các ID không phải bearer token; tuyệt đối không truyền credential hoặc header qua flags. Không có mode force/auto-discovery/retry/read-mutating trong collector.

CLI chỉ `--workspace` vẫn hỗ trợ read-only runtime diagnosis, không client claim. Invalid args trả exit 2 với code bounded, không echo dữ liệu; matched partial observation không tự thành schema-v2 reboot packet hoặc controller acceptance.

**Validation:** `node --test tests/boot-runtime-observation.test.js tests/boot-acceptance.test.js` **51/51 PASS**, khoảng 0.49s, final exit 0. Test mới chứng minh all-or-nothing validation, duplicate/unknown flags, unsafe numeric generation, no IPC on invalid input, missing client returns nonzero. Scoped whitespace PASS; chỉ LF→CRLF warning.

Final SHA-256: collector `d6c2094d124a448127155ee4486889bc627c33b5608f9f3eb505a8924864c334`; test `8bfc42cefa3b2e9b3f66e31191a0648f107d640689b33ab73fd504d3f10fae82`.

**Authority/next-gate audit:** local source/test quyền đã được cấp; chưa có quyền cụ thể để restore live canonical, install frozen Windows artifact, restart/activation với exact target, sửa/deploy Ubuntu service hoặc reboot hai máy. Public Coding Tools client và natural user outcome không thể giả bằng loopback fixture. Vì vậy A3/A4/B3/B4 còn gate, không tự nâng quyền từ goal “hoàn thiện”. Vẫn có source work hữu ích ở X0-G delivery-history regression/guard cần làm trước delivery; không để active goal chỉ lặp runtime poll hoặc đếm test xanh. Next safe packet là X0-G kiểm tra history continuity dựa trên failure đã chứng minh ở merge, giữ supported archival semantics và không sửa ledger.

**Checkpoint:** chỉ collector/test/Markdown đổi trong lượt, no staged/unmerged, tests terminal; không EOCL acceptance giả, lifecycle/DB mutation, commit/push/deploy/paid inference. Mục tiêu ACTIVE, chưa complete; full criteria/matrix/live/natural requirements được giữ nguyên.

### 16.13. X0-G — semantic delivery-history guard, 22/09 khoảng 18:03–18:10 +07

**Concurrent Git advance:** đầu lượt HEAD=`5aae18eddb8dae52bc852cbf35ab71e9e58b95fc`, commit `Update execution workflows and delivery evidence` lúc 18:02:07 +07, parent `77d7347`. Luồng khác đã commit candidate trước; lượt này không commit/push/rewrite. Chỉ Markdown dirty trước khi X0-G bắt đầu. Proof trước giữ fingerprint riêng, không tự coi đã rerun trên HEAD mới.

**Implement:** [ledger-delivery-history.py](../../scripts/ledger-delivery-history.py) đọc Git index/blobs và query SQLite trong memory. `stage-coding-tools-delivery.py::verify_index` gọi semantic retention check sau receipt/hash/size/schema/integrity checks; existing stage_delivery đã gọi verify_index, nên guard nằm trên delivery path hiện hữu. Không repair/merge DB hoặc staging riêng để guard PASS.

Semantics:

- Baselines mặc định: HEAD, mọi MERGE_HEAD khi merge đang diễn ra, các parent khi HEAD là merge commit; de-duplicate refs.
- Candidate là **Git index**, không live working bytes. Canonical + archives có trong indexed manifest được kiểm integrity, exact SHA/size, safe shard filename và manifest run IDs có mặt. Unlisted archive không tự bù history.
- `events`/`problem_events`: giữ identity và toàn bộ row values; mất/sửa immutable event đều fail. `runs`/`waves`/`checkpoints`/`proofs`: giữ identity, cho phép projection state tiến triển. Không dùng max seq/file size/accepted count thay exact identity.
- Whole-run archival có manifest/hash/retained evidence hợp lệ được chấp nhận; missing shard hoặc wrong hash/run manifest fail. Optional path không tồn tại khác lỗi đọc existing Git blob.
- Git snapshots deserialize trong memory, normalize journal-header bytes chỉ trong memory; không thay Git blob/canonical/WAL/SHM/index. Đây không phải tool restore.
- Giới hạn: không scan toàn ancestry, không chứng minh mọi bảng/state hoặc authority signature. Schema migration sửa immutable event cần review/handling riêng; không force bypass. PASS không tự là restore/closure acceptance.

CLI audit chỉ đọc:

```powershell
python -B scripts/stage-coding-tools-delivery.py --verify-history
python -B scripts/stage-coding-tools-delivery.py --verify-history --baseline a9fcb9974b5ca43266ec2feea1dc64c1a95d406e
```

`--baseline` chỉ dùng cùng `--verify-history`. Default guard ngăn regression so HEAD/merge boundary; history thiếu từ lâu phải dùng explicit baseline. Không dùng default PASS để nói X0 cũ đã phục hồi.

**Proof:**

1. `python -B -m unittest discover -s tests -p test_stage_coding_tools_delivery.py`: final **7 tests OK, 24.80s**, exit 0. Repositories tạm kiểm consistent snapshot/live drift, corrupt ledger, unrelated unstaged evidence, deleted/rewritten event, dropped merge-parent tail và valid archival rồi manifest hash bị sửa.
2. Intermediate failures phân loại/sửa: SQLite context manager chưa close gây Windows cleanup lock; fixture thiếu actual `run-python.js`; snapshot header khác closed-WAL file làm temp checkout dirty. Sửa fixture bằng explicit close/commit, copy launcher, align **chỉ temp repository** với chính committed blob trước branch switch. Không bypass production guard.
3. Audit explicit baseline trên **index dự án thật**, không stage: exit 1 expected, `LEDGER_HISTORY_NOT_PRESERVED baseline=a9fcb9974b5ca43266ec2feea1dc64c1a95d406e table=events missing=128 changed=0`. Khớp finding X0, không phải recovery PASS.
4. Không chạy `npm run stage:coding-tools-delivery` hoặc `check:coding-tools-delivery` ở repo chính vì chúng có staging side effects. Index không staged changes, no unmerged, scoped whitespace PASS (LF→CRLF warning).

Final SHA-256:

| File | Hash |
| --- | --- |
| scripts/ledger-delivery-history.py | `795306245defda0a0e80764772e7cc4201aa9abfad5d4a9f5ac1fb8da68b340b` |
| scripts/stage-coding-tools-delivery.py | `c7a232159839fea64ffb65b825f51dbfb17f4f386b6aaa2184df6900f464946d` |
| tests/test_stage_coding_tools_delivery.py | `8ee5afc9869c92bee1cc72a836ebfa69990eab680946cc8a5bc7e80460eadef7` |

**Checkpoint/completion audit:** X0-G local source/proof đạt trong scope; X0 canonical recovery vẫn NOT_RUN, real guard vẫn xác nhận gap. A0/A1/A2/B1 có các lớp proof đã ghi, chưa loaded/client/reboot/natural closure. Main@5aae18e; chỉ guard/stage-script/test/Markdown thay đổi lượt này, test handles terminal. Không production restore/restart/reboot/install/deploy/commit/push/paid inference. Goal ACTIVE, chưa complete. Next safe action: isolated recovery applicability audit cho toàn state trước recovery proposal có authority; không copy đè live canonical từ historical blob chỉ vì sáu bảng là superset.

### 16.14. X0 full-state applicability audit — 22/09 khoảng 18:13–18:15 +07

Previous turn=PROGRESS (guard đã implement và bắt actual gap). Lượt này chỉ compare read-only để chọn recovery đúng nghĩa, không thay goal bằng thêm tests.

**Phương pháp:** nguồn current đọc URI mode=ro rồi SQLite Backup API vào memory; historical Git blob `bed5b266…` normalize journal header chỉ trong memory như 16.2. Cả hai query_only, integrity ok/FK0. So schema và rows của **36 user tables**, dùng primary key từng bảng (fallback full row nếu không có PK); không in JSON payload/raw source/credentials. Schema 36 bảng giống nhau, không table mới/mất. 19 bảng giống toàn bộ rows; 17 bảng có khác biệt. Phép so không bao gồm internal SQLite bookkeeping như sqlite_sequence, không phải restore dry-run/permission.

| Table | Chỉ historical | Chỉ current | Common rows khác values |
| --- | ---: | ---: | ---: |
| background_operations | 6 | 0 | 0 |
| checkpoints | 3 | 0 | 0 |
| continuity_telemetry | 12 | 0 | 0 |
| controller_goal_attachments | 0 | 0 | 1 |
| controller_knowledge_acks | 1 | 0 | 0 |
| controller_leases | 3 | 0 | 3 |
| controller_reattach_receipts | 1 | 0 | 0 |
| events | 128 | 0 | 0 |
| hub_clients | 3 | 0 | 4 |
| idempotency_records | 18 | 0 | 0 |
| managed_process_jobs | 7 | 0 | 0 |
| problem_events | 3 | 0 | 0 |
| problem_threads | 0 | 0 | 1 |
| proofs | 5 | 0 | 0 |
| runs | 3 | 0 | 0 |
| waves | 4 | 0 | 0 |
| write_fences | 0 | 0 | 1 |

**Finding quyết định recovery:** historical causal tables là superset nhưng **toàn DB không phải replacement an toàn**:

- Controller attachment generation historical=29/current=28, owner/endpoint/reattach khác; ba controller leases có fencing_token/lease/owner/expiry khác.
- Write-fence historical token=1681/current=1677, RUN/WAVE/lease khác. Không tự resurrect authority từ token lớn hơn hoặc timestamp cũ.
- Problem-thread latest event projection historical=320/current=317 phải đi cùng event lineage được xác minh, không chỉnh counters riêng.
- Hai common hub-client rows có current observations ngày **22/09** mới hơn historical ngày 09/09 hoặc 13/09. Copy đè toàn DB sẽ đánh mất observed state mới, dù không có current-only primary key.
- Historical-only background_operations: 5 completed + **1 running**; managed jobs: 7 exited; idempotency: 15 completed + **1 unknown + 1 failed + 1 in_progress**. Đây là trạng thái lưu lịch sử, **không phải proof process đang sống**. Không replay các effect từ missing/in_progress/unknown record hoặc coi missing ở current là permission execute lại.
- Các bảng continuation grants/effects, P5 epochs/assignments/outcomes và nhiều domain khác giống nhau trong audit; không được hiểu là chúng đã đạt natural outcome.

Census current mới `snapshot_at=2026-09-22T11:14:29.096Z` vẫn physical/logical hashes E02, integrity ok/FK0, canonical_mutated=false; 17 stale candidates, 6 P5 anchors, managed jobs rỗng, unbound live/stale background residue0. Census này không thay việc classify historical-only effects trước recovery.

**Quyết định:** loại phương án `git show historical ledger > live ledger` hoặc copy đè/INSERT thủ công. Existing archive/query/compact tools được kiểm tra không phải divergence-recovery importer; không dùng compact/post-restart smoke để giả restore. Recovery cần packet được duyệt với:

1. Exact source baseline/current SHA + effect inventory trước mutation, quiesce qua supported runtime khi có quyền.
2. Chọn cơ chế supported restore/reconciliation/import preserves original IDs/hash-chain/acceptance provenance; không tạo acceptance mới từ report text. Nếu cần triển khai importer, thiết kế domain contract và dry-run trước; không generic arbitrary-SQL escape hatch.
3. Giữ newer observed hub state, xác định authority/lease/reattach/fence post-recovery qua runtime-owned rules; không nhận historical owner là current owner.
4. Giữ unknown/in_progress effects và terminal evidence; exact reconciliation trước bất kỳ replay nào, không sửa thành completed cho đẹp.
5. Diễn tập isolated, all-table consistency + append-after-recovery + duplicate-effect/authority negatives; freeze receipt/artifact/fingerprint, owner review trước actual canonical switch.
6. Backup/rollback có bảo toàn evidence sau switch; không downgrade đè mất event mới. Sau đó fresh runtime/client readback và canonical coverage, không chỉ integrity check.

**Completion/authority checkpoint:** audit này thay đổi lựa chọn next action nên là PROGRESS, không phải no-progress poll. Chưa có actual recovery authority hoặc supported applied reconciliation; A3 live activation/reboot/central rollout cũng vẫn chưa được cấp target-specific authority. Lượt này chỉ Markdown cập nhật, main@5aae18e, các source X0-G còn dirty như lượt trước; census/query handles terminal. Kiểm tra cuối 18:16 thấy `.coding-tools/delivery-snapshot.json` được staged bởi hoạt động concurrent (6 dòng diff); lượt này không chạy stage và không unstage/ghi đè receipt đó. Không unmerged. Không restore/SQL mutation/runtime restart/install/deploy/commit/push/paid inference. Goal ACTIVE, không COMPLETE/BLOCKED trong lượt có progress. Cần owner cấp phạm vi cho recovery có kiểm soát trên exact canonical `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3` (backup + isolated rehearsal trước, actual switch chỉ sau review) và quyết định operational target trước khi tiến sang live gates. Không mặc định yêu cầu “hoàn thiện” cho phép bỏ các chốt này.

### 16.15. Authority gate revalidation — 22/09 khoảng 18:18 +07

Lượt 16.14 là PROGRESS vì full-state audit thay đổi quyết định recovery. Lượt hiện tại **NO PROGRESS đối với implementation/outcome**, không phải verified wait: không có job handle đang chạy để chờ; cập nhật báo cáo không được tính như đã xử lý thêm criterion.

Đã kiểm HEAD/status và available tool inventory: HEAD vẫn 5aae18e, public Coding Tools workspace_context/agent_workflow/task_control vẫn không expose; chưa có user response cấp quyền cho recovery được hỏi ở lượt trước. Internal automatic goal continuation không phải consent mới. Không rerun tests đã có exact proof, không thử synthetic canary thay client thật, không gọi repeated runtime poll vì không có expectation external state đã đổi.

Hoạt động concurrent đã staged delivery receipt, Markdown và ba files X0-G. Lượt này không stage/unstage hoặc commit các files đó. Bản cập nhật 16.15 chỉ sửa working-copy Markdown sau staged snapshot; khi delivery thật cần owner recapture/review, không âm thầm ghi đè index. No unmerged.

Các gate ngăn hoàn tất giữ nguyên: recovery/applicability approval và live canonical reconciliation; exact source acceptance + target-specific activation/installed/reboot/central operations; real client correlation/discovery; actual bounded continuation consent/provider authority; hai máy và independent natural outcome/window. Không có phép kiểm local nào thay thế những điều kiện này. Đây là lần revalidation thứ hai của authority boundary nêu ở 16.14; goal còn ACTIVE cho tới blocked audit threshold, không claim COMPLETE. Next action cần user: duyệt scope recovery backup/isolated rehearsal cho exact ledger, giữ actual canonical switch chờ review; sau đó chốt operational target/quyền riêng cho live gates.

### 16.16. Blocked audit terminal checkpoint — 22/09 khoảng 18:19 +07

Lượt trước=NO PROGRESS. Recheck hiện tại HEAD/status/tool inventory không đổi authority: chưa có câu trả lời cho scope recovery, public Coding Tools control path vẫn không expose. Không có live job handle để chờ; repeated goal prompt không tạo consent. Cùng boundary đã ghi ở 16.14, 16.15 và nay 16.16; đạt ba consecutive goal-turn observations. Dừng vòng automatic continuation bằng status **BLOCKED**, không COMPLETE hoặc PAUSED.

Đã làm và có proof: A0/A1 safety fixes; A2 offline oracle + attested contact/Host/collector/exact CLI correlation; B1 các nhóm source guards; X0 historical chain + all-table audit; X0-G delivery continuity guard. Chưa được chứng minh: applied canonical recovery, exact loaded package/runtime acceptance, client/central/reboot/two-machine samples, actual bounded background inference và independent natural outcome/48h. Không có authority để tự thay các missing gates bằng local fixtures hoặc broad operational action.

**Điều kiện gỡ blocker trước mắt:** người dùng chấp thuận triển khai gói recovery cho `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3`, giới hạn backup và isolated rehearsal trước; actual canonical switch chỉ sau review riêng. Tiếp đó cần target-specific activation/installed/central/reboot scope và real-client/consent/outcome actors. Chấp thuận local source trước đây không được mở rộng ngầm sang live DB/lifecycle.

Git cuối main@5aae18e; receipt/X0-G/report được staged bởi hoạt động concurrent, working-copy Markdown có cập nhật mới chưa staged. Không unstage/reset/overwrite index; delivery owner phải review/recapture khi commit. Lượt này chỉ checkpoint Markdown, không test rerun/source mutation/restore/restart/reboot/install/deploy/commit/push/paid inference; các query terminal. Toàn bộ remaining objective được giữ nguyên để resume, không hạ Definition of Done.

### 16.17. Controlled recovery backup + isolated rehearsal — 22/09 khoảng 18:20–18:28 +07

**Quyền mới:** user cho phép controlled recovery cho exact `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3`, trong ngữ cảnh backup/diễn tập cô lập trước và chuyển canonical thật sau review riêng. Goal đã trở lại ACTIVE; blocked-audit counter được reset cho resumed run. Không coi consent này là quyền restart/reboot/deploy hoặc bỏ unknown-effect gates.

Thêm [rehearse-ledger-recovery.py](../../scripts/rehearse-ledger-recovery.py) và [tests](../../tests/test_ledger_recovery_rehearsal.py). Tool **không có apply/switch/restart mode**, chỉ tạo artifact mới trong temp directory riêng; live ledger mở mode=ro và copy bằng Online Backup API. Historical Git blob phải match expected SHA; current snapshot phải match expected SHA; missing RUN set phải đúng ba exact IDs được truyền. Không ghi live DB/index hoặc tái tạo accepted event từ report text.

Strategy rehearsal:

- Candidate bắt đầu từ current snapshot, không bắt đầu từ historical replacement.
- Schema phải bằng nhau, immutable-row conflicts bị từ chối. Nhập historical-only rows trên bản cô lập; giữ nguyên toàn bộ existing row values hiện tại, kể cả hub observations mới.
- Không nhập historical authority tables: controller attachments/leases/reattach, write fences, hub clients/cursors, active lanes/resource claims, continuation grants. Current authority không được thay bằng historical owner.
- Không đổi historical unknown/in_progress/running effects thành completed; giữ nguyên fact và đánh dấu required reconciliation. Problem-thread projection chưa tự promote theo event mới; candidate không thể activation chỉ vì integrity đạt.
- FK deferred trong transaction và kiểm trước commit candidate; conflict rollback. Output luôn `QUARANTINED_REHEARSAL`, `activation_eligible=false`; backup/source/candidate được đặt file read-only sau diễn tập. Read-only file flag là guard thao tác, không thay authority review.

**Artifacts thực tế** tại `E:\Caches\Temp\codex-ledger-recovery-rehearsal-ho9mu2yt` (giữ nguyên để review, không Git-stage/publish raw DB):

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| current-backup.sqlite3 | 97,509,376 | `c894f57ebdb0c1c7995cb5dc315edbc39a317d6143afe2d1cda1184b9034f39a` |
| historical-original.sqlite3 | 97,824,768 | `e7700489c3ecd85afcd2c21c36967741793fef73f36aad47a47da8f9887de9b6` |
| QUARANTINED-candidate.sqlite3 | 97,837,056 | `5f003d4cb80a3b6bfa4aca28e0ead57ca011b613a39fb0888ce63f8b700657d3` |
| rehearsal-report.json | Content-free result | Chụp `2026-09-22T11:25:56.266243Z`; không phải EOCL receipt |

Directory này là artifact diễn tập ở temp, **không** là backup-retention policy production. Trước actual switch phải chọn durable backup location/ACL/retention và fresh snapshot. Không xóa các artifact trong lượt này. Read-only attribute được xác minh 18:27 cho ba SQLite files; original report giữ nguyên, không backfill timestamp/acceptance.

**Kết quả candidate:** thêm events128, problem_events3, runs3, waves4, checkpoints3, proofs5, continuity_telemetry12, knowledge_acks1, background_operations6, idempotency_records18, managed_jobs7. Withheld historical leases3, reattach receipts1, hub_clients3. Giữ nguyên mọi existing row, gồm attachment/lease/hub/problem-thread/fence conflicts đã nêu 16.14. Integrity `ok`, FK0.

Historical-only effect labels còn nguyên: background 5 completed/1 running; idempotency 15 completed/1 failed/1 unknown/1 in_progress; jobs7 exited. Không có attempt replay hoặc process execution; các nhãn này không phải current-live liveness.

**Validation đã làm:**

1. Focused recovery unit suite **4 tests OK, 9.10s**, gồm evidence merge/current hub preservation/authority withheld/unknown giữ nguyên; immutable conflict rollback; wrong allowlist và overwrite refusal; FK dependency không được kéo authority cũ vào bằng đường vòng.
2. Tool rehearsal chạy thật trên backup cô lập, exit0 và report như trên. Canonical source chỉ đọc. `activation_eligible=false` không phải thất bại SQLite, mà là gate bảo vệ chưa đóng.
3. Recompute per-RUN event hash chain trên candidate: 32/32/62 events PASS, head hashes đúng historical 16.2, không failed sequence.
4. SQLite allocator/rollback probe chỉ trên candidate trước khi write-protect: next seq59823 >59822, rollback toàn transaction; candidate bytes/SHA không đổi. Đây **không** là committed causal event hoặc canonical append/authority acceptance. Không giữ synthetic probe row trong artifact.
5. Postflight official read-only census `snapshot_at=2026-09-22T11:26:59.821Z`: canonical physical/logical hashes vẫn E02, integrity ok/FK0; 17 stale candidates, no managed job/unbound live residue. Chứng minh live canonical chưa đổi, không suy candidate runtime safety từ census của canonical.
6. File write-protection xác minh trực tiếp trên đúng ba artifact paths; scoped source/test whitespace checks PASS. CLI được bổ sung write-protect sau rehearsal core test; không claim core suite đã test một live restore path.

Local source fingerprints: rehearsal script `27bee60f52e6dd8db852de5b5a446583bb3fa52546940c80baa2a5a958042217`; test `331c51a7c82b795a6bc7672c7d9b2a2066b86a98c49adbbb1ac52ba272792080`.

**Các gate còn thiếu trước đề nghị switch:** problem projection reconciliation; monotonic authority generation/fencing với lịch sử đã phục hồi nhưng không hồi sinh owner cũ; unknown/in-progress effect reconciliation; full startup/duplicate-effect dry-run và operator review. Candidate hiện **KHÔNG ĐƯỢC dùng làm live DB**. Source rehearsal generic table copy chỉ phục vụ isolated diagnosis, không phải sanctioned canonical importer/apply API.

**Checkpoint:** consent blocker backup/rehearsal đã được gỡ và có concrete progress. Luồng khác tạo commit `ee11ec2e0177b69e37438420dca7ef08aebb9d5f` (chore: guard coding-tools delivery history), đã recheck; lượt này không commit/push. Chỉ thêm rehearsal script/test, artifact tạm có kiểm soát và cập nhật Markdown; không thay canonical/index, không restart/install/deploy/reboot/paid dispatch. Test/rehearsal/census handles terminal. Goal ACTIVE, chưa COMPLETE; tiếp tục xử lý các gate candidate nêu trên trước khi xin duyệt actual canonical switch, không hỏi lại quyền backup đã được cấp.

### 16.18. Chạy lại controlled recovery rehearsal và startup-guard probe — 22/09 khoảng 18:55–18:57 +07

Đây là wave **PROGRESS** sau khi user cấp phạm vi controlled recovery. Tôi không switch/copy/INSERT vào canonical; `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3` chỉ được mở `mode=ro`, sau đó Online Backup API tạo artifact mới ngoài repository.

**Input và identity đã kiểm:**

| Input | Giá trị |
| --- | --- |
| Branch/HEAD | `main@ee11ec2e0177b69e37438420dca7ef08aebb9d5f` |
| Live backup | `E:\Caches\Temp\codex-ledger-recovery-rehearsal-udbg894e\current-backup.sqlite3` |
| Live backup SHA-256 | `c894f57ebdb0c1c7995cb5dc315edbc39a317d6143afe2d1cda1184b9034f39a` |
| Historical Git blob | `bed5b266a83e4cbc3947f5dd15854d80f58f6264` |
| Historical SHA-256 | `e7700489c3ecd85afcd2c21c36967741793fef73f36aad47a47da8f9887de9b6` |
| Exact historical RUN allowlist | `dcb539e0e1694bc1bb29eed2b2e07f8b`, `d01a5dce50c846fc8e13673cdfc8b3b3`, `b194ab1e311e42efa1dd0614ca245037` |

Rehearsal report: `E:\Caches\Temp\codex-ledger-recovery-rehearsal-udbg894e\rehearsal-report.json`; candidate `QUARANTINED-candidate.sqlite3` SHA `651f6c40c633974f0f2668f3b18ccfdb751e946f5ce6b8bd7bb96f7dc97d1be5`; all three artifacts write-protected. Result là `QUARANTINED_REHEARSAL`, `canonical_mutated=false`, `activation_eligible=false`, `integrity=ok`, FK `0`, current rows preserved. Candidate thêm đúng 3 RUN, 4 WAVE, 3 checkpoint, 5 proof, 128 `events`, 3 `problem_events`, 12 continuity telemetry, 6 background operations, 18 idempotency records và 7 managed jobs. Các historical authority rows vẫn bị giữ lại: 3 controller leases, 1 reattach receipt, 3 hub clients.

Đối soát sâu trên candidate:

- Ba event hash-chain theo RUN lịch sử hợp lệ; candidate có `events=25,822`, seq `26897..59822`, không trùng seq/hash-chain error. `problem_events=307` cũng giữ chain liên tục; không tạo event acceptance mới.
- Tất cả row hiện tại của 36 bảng được bảo toàn; không current-only row bị mất và không common row bị overwrite. `integrity_check=ok`, FK `0` trên current/candidate/historical.
- Projection Problem `prl-22e…` **chưa thể coi là reconciled**: event mới nhất là seq `320`, trong khi `problem_threads.latest_problem_event_seq` vẫn `317` vì rehearsal cố ý giữ current projection khi gặp conflict. `prl-e918…` không có drift mới. Đây là blocker có chủ đích, không sửa bằng cách copy historical thread row.
- Historical write-fence/reattach generation đạt `1681/29`, current/candidate giữ `1677/28`; candidate không resurrect authority high-water mark cũ. Historical `background_operations` có 1 `running`, idempotency có `unknown`/`in_progress`; đây là unknown-effect inventory, không phải quyền replay.

**Startup guard probe** trên một workspace temp mới, input candidate SHA đúng, cho `ISOLATED_STARTUP_GUARDS_PROVED`: source unchanged; integrity/FK `ok/0`; events count unchanged; `background_marked_orphaned=1`; `idempotency_marked_unknown=1`; **663** unknown/in-progress claims bị từ chối; `controller_leases_expired=0`; `real_runtime_started=false`; probe artifact `E:\Caches\Temp\codex-ledger-startup-probe-0e1p3vj4\startup-probe-report.json`. Probe SHA của target sau guard là `b312aba43f1acd8b1e5987c4d4d85f8cb165bc01de73bd4f235f793909649963`; input candidate không đổi.

**Đã đạt trong wave:** backup nhất quán, allowlist exact, isolated merge, all-table preservation, integrity/FK, event lineage, authority withholding và unknown-effect refusal. **Chưa đạt:** supported problem-projection reconciliation cho seq `318–320`, authority high-water review/owner sign-off, exact runtime activation/loaded package, client strict discovery/MCP-Tunnel/workspace read, reboot/two-machine, natural continuation và independent outcome. Vì vậy không được copy candidate lên live ledger, không restart/reboot/install/deploy/push, và không đánh dấu hai Problem đã đóng.

**Next action chính:** bổ sung verifier append-after-recovery và negative duplicate/authority checks trên clone writable của candidate; sau đó owner review một receipt bất biến. Chỉ khi có supported reconciliation contract + quiesced runtime + target-specific approval mới xem xét canonical switch; mọi switch vẫn phải có rollback backup, postflight integrity/projection/readback và acceptance riêng.

### 16.19. Verifier candidate: append-after-recovery và negative duplicate/authority — 22/09 khoảng 19:02–19:08 +07

Đã triển khai [audit-ledger-recovery-candidate.py](../../scripts/audit-ledger-recovery-candidate.py) và test [test_ledger_recovery_candidate_audit.py](../../tests/test_ledger_recovery_candidate_audit.py). Verifier nhận ba file đã hash-check, mở chúng read-only, rồi chỉ tạo một clone tạm của candidate để chạy các probe có ghi. Không có đường lệnh apply/switch canonical.

Kết quả trên candidate SHA `651f6c40c633974f0f2668f3b18ccfdb751e946f5ce6b8bd7bb96f7dc97d1be5`:

| Gate | Kết quả | Ý nghĩa |
| --- | --- | --- |
| Current rows preserved / authority current-only | PASS | Candidate không đổi row hiện tại; authority tables bằng current; historical leases/reattach/hub vẫn withheld |
| SQLite integrity/FK | PASS | candidate/current/historical đều `integrity=ok`, FK `0` |
| Event sequence + hash chain | PASS | 25,822 events, 555 RUN chains, seq monotonic, link/digest errors `0` |
| Append-after-recovery | PASS trên clone | Tạo RUN/WAVE/event mới bằng `OrchestrationLedger`; event persist đúng, hash đầu chain rỗng là đúng với RUN mới; clone integrity/FK `ok/0` |
| Unknown-effect replay refusal | PASS trên clone | `663` unknown/in-progress claim bị từ chối; `1` running background được đánh dấu orphaned; sau probe không còn running/in-progress |
| Completed duplicate refusal | PASS trên clone | claim lại một idempotency record `completed` trả `reason=completed`, không claim effect lần hai |
| Problem projection | **BLOCKED** | `prl-22e…` thread seq `317`, event seq `320`; cần supported projection reconciliation, không copy thread historical |
| Unknown-effect reconciliation | **BLOCKED** | Candidate còn `1 running` background + `662 unknown` + `1 in_progress` idempotency trước probe; đó là evidence cần owner phân loại, không được tự mark completed |
| Operator/support switch authority | **MISSING** | Không có receipt quiesce/owner review/supported importer cho canonical switch |

Focused suite hiện tại: **5 tests PASS, 11.58s** (`test_ledger_recovery_rehearsal.py` + `test_ledger_recovery_candidate_audit.py`); verifier `py_compile` PASS. Đây là proof cho safety behavior của rehearsal và clone, không phải source acceptance của toàn app, không phải live runtime/client proof.

**Phân loại checkpoint:** PROGRESS. Hai probe mới đã đóng phần “candidate có thể mở/append/không replay duplicate” trong môi trường cô lập, nhưng không làm thay đổi verdict `activation_eligible=false`. Không thực hiện canonical write, runtime restart, reboot, package/install, deploy, push hoặc tạo outcome tự nhiên. Next action vẫn là owner review + contract reconciliation cho `prl-22e…` và unknown effects; nếu không có supported API/authority, phải giữ candidate quarantine và không gọi đây là recovery đã áp dụng.

### 16.20. Direct `main` push bị chặn bởi GitHub large-file gate — 22/09 khoảng 19:17–19:20 +07

Đã commit trực tiếp trên `main` và chạy lại delivery guard trước push:

- `5413dc7` — `feat: audit controlled ledger recovery candidate` (verifier, test, checkpoint 16.19).
- `25e7cfd` — `chore: refresh delivery snapshot before push` (receipt snapshot mới nhất).
- `npm run check:coding-tools-delivery`: **PASS**; `ledger_blob=131f76e2582c2e0b73e53338296d40f450deb2a9`, `size_bytes=97509376`, `user_version=12`, history **PASS (4876 files)**; `git diff --cached --check` sạch.

Lệnh `git push origin HEAD:main` đã chạy nhưng server từ chối ở pre-receive với `GH001`: ba binary generated đã có trong **lịch sử local chưa có trên remote**, mỗi file khoảng 215 MB:

| Path bị GitHub nêu | Kích thước theo remote |
| --- | ---: |
| `output/packaged-candidate-final/win-unpacked/Coding Tools MCP.exe` | 215.21 MB |
| `output/packaged-candidate-revalidated-20260922-135500/win-unpacked/Coding Tools MCP.exe` | 215.21 MB |
| `output/packaged-candidate-revalidated-20260922-140500/win-unpacked/Coding Tools MCP.exe` | 215.16 MB |

`origin/main` **không đổi**, vẫn `044dd96178faacc92a049a528eb05baa60b8816a`; local `main` vẫn sạch ở `25e7cfd0ce5ef17b7fb927fb8561ef54f03c3c24`, ahead `6`, behind `0`. Các thư mục này nằm dưới `output/` vốn bị ignore nhưng đã bị track trong các commit local trước đó; không được đánh đồng với retention bắt buộc của `.coding-tools`, và không được tự xóa/rollback chỉ để vượt gate. Canonical `.coding-tools/orchestration/ledger.sqlite3` không bị đổi.

`25e7cfd` là HEAD tại thời điểm lệnh push bị reject; checkpoint 16.20 sau đó được ghi vào local history. Các con số HEAD/divergence ở trên là snapshot tại thời điểm checkpoint; trước mỗi delivery tiếp theo phải recapture. Remote ref vẫn không đổi.

**Phân loại:** `EXTERNAL_DELIVERY_BLOCKED_LARGE_FILE`, không phải test/source failure. Không dùng `--force`, không rewrite history, không xóa artifact hay đổi `.coding-tools` khi chưa có lựa chọn rõ ràng. Để push `main`, owner phải chọn và cấp quyền cụ thể cho một trong các đường sau:

1. Rewrite có backup các commit local chưa publish để bỏ generated `output/**/win-unpacked` khỏi Git history, giữ manifest/hash và artifact ngoài Git, rồi `git push --force-with-lease origin main`.
2. Di chuyển đúng binary lớn sang Git LFS, kiểm tra LFS quota/remote policy, vẫn phải history migration và force-with-lease cho phần local chưa publish.
3. Giữ `main` local như hiện tại và phát hành binary qua artifact store/release channel được chỉ định; chỉ push source/evidence history sau khi path contract được chốt.

**Next action an toàn:** chờ owner xác nhận chính xác phương án history/artifact. Khi được cấp, tạo backup ref/receipt trước rewrite, dry-run lọc đúng các path nêu trên, kiểm tra `.coding-tools` retention, chạy lại `stage:coding-tools-delivery` + `check:coding-tools-delivery`, rồi chỉ force-with-lease nếu remote vẫn đúng `044dd961…`. Cho tới lúc đó không gọi lần push này là thành công và không coi hai Problem đã đóng.

### 16.21. Đối soát kích thước lịch sử và khả năng LFS — 22/09 khoảng 19:30 +07

Đã kiểm read-only toàn bộ objects trong `origin/main..HEAD` bằng `git rev-list --objects` + `git cat-file --batch-check`:

- Có đúng **3 blob** lớn hơn giới hạn GitHub 100 MB; cả ba đều là ba executable đã được remote nêu ở 16.20.
- Không có blob khác vượt 100 MB trong 9 commit local chưa publish.
- `git lfs version`: **3.6.1** đã cài, nhưng `.gitattributes` hiện chỉ có `* text=auto`, chưa track executable/package nào bằng LFS.
- `git ls-files output` hiện có **1031 path**; `output/` vốn bị `.gitignore`, nhưng các path này đã bị track trong commit `5aae18e` và các commit kế tiếp.

Đây là bằng chứng đủ để khoanh phạm vi migration, không phải quyền tự thực hiện migration. Không sửa `.gitattributes`, không chạy `git lfs migrate`, không reset/rebase/force-push và không xóa các output vật lý. Canonical ledger, `.coding-tools` retention và local `main` không đổi trong probe này.

**Kết luận cập nhật:** nếu owner chọn loại generated output khỏi lịch sử, dry-run có thể giới hạn chính xác ở `output/**` (giữ artifact ngoài Git, giữ manifest/hash trong docs). Nếu owner chọn LFS, migration tối thiểu phải bao phủ ba executable và kiểm quota/remote policy trước khi rewrite. Cả hai đều là history mutation; vẫn chờ xác nhận phương án và target `main`.

### 16.22. Concurrent authority-status fix đã được commit trên `main` — 22/09 khoảng 19:30–19:32 +07

Trong lúc đối soát large-file blocker, một tiến trình concurrent đã hoàn tất commit trực tiếp trên cùng `main`:

```text
b0b6505 fix: accept enriched authority status targets
```

Commit này thay đổi `control-plane/control_plane/node_agent.py` để nhận đúng hai shape target legacy/enriched bằng một `target_keys` đã kiểm tra kiểu, đồng thời thêm [test_node_agent_authority_status.py](../../control-plane/tests/test_node_agent_authority_status.py). Focused proof chạy sau commit:

```text
python -B -m unittest -v control-plane/tests/test_node_agent_authority_status.py
Ran 1 test ... OK
```

Tôi không sửa, stage, revert hoặc gộp nội dung source/test của commit này. Commit có cập nhật `delivery-snapshot.json`; tiến trình concurrent đã chạy delivery verification trước đó, nhưng lane hiện tại chưa claim full repository/release acceptance từ một focused test. `origin/main` vẫn chưa đổi vì push trước đó đã bị `GH001`; commit này cũng chưa được publish.

**Current-state note:** sau commit này local `main` đã tiến thêm một commit so với snapshot 16.21. Trước mọi delivery/rewrite tiếp theo phải recapture HEAD/divergence và kiểm tra lại các file ngoài scope; không staging `control-plane/control_plane/node_agent.py` hoặc test khác nếu chưa có owner packet tương ứng.

### 16.23. Backup bundle trước history migration — 22/09 khoảng 19:34 +07

Để chuẩn bị cho lựa chọn publish nhưng chưa thực hiện rewrite, đã tạo một Git bundle ngoài repository:

```text
Path: E:\Caches\Temp\codex-web-main-before-history-migration-20260922.bundle
Size: 159,829,396 bytes
SHA-256: 192cf5810e901d4a451cfd1b6f1412b64957a7dea860f30a502c693e594788f9
Ref: a23c45dd06e49fc48a494df2963eab7c0884263a refs/heads/main
Prerequisites: 77d73471dc896a1f1ac189b2df46529276481552, 044dd96178faacc92a049a528eb05baa60b8816a
git bundle verify: OK
```

Bundle này chứa phần lịch sử local `origin/main..HEAD`, đủ để khôi phục ref hiện tại sau một migration có kiểm soát; nó không phải worktree và không làm thay đổi `main`, `origin/main`, canonical ledger hoặc artifact vật lý. Trước migration hiện có **1031 tracked path dưới `output/`**, nhưng chỉ **3 blob >100 MB**; dry-run được phép giới hạn vào generated output nếu owner chọn phương án loại khỏi lịch sử.

Sau khi ghi checkpoint 16.23, đã tạo thêm bundle bao phủ đúng current HEAD để không dùng nhầm snapshot cũ:

```text
Path: E:\Caches\Temp\codex-web-main-before-history-migration-20260922-current.bundle
Size: 159,829,859 bytes
SHA-256: 132f2ec48d023c858065e49baef6ddd2f798a20e5b01edeaf5ffc409d08884e5
Ref: abab565e471530541f67095c23d7ff7b8d722eb3 refs/heads/main
git bundle verify: OK
```

Bundle đầu tiên vẫn được giữ làm checkpoint lịch sử tại `a23c45d`; bundle `current` là snapshot chính xác tại thời điểm HEAD `abab565`. Vì các checkpoint tiếp theo có thể làm HEAD tiến thêm, phải recapture hoặc tạo bundle mới ngay trước history migration; không dùng tên `current` như một tuyên bố freshness vô thời hạn.

**Trạng thái:** backup đã có, nhưng chưa có lệnh `git filter-repo`, `git lfs migrate`, `git update-ref`, `git reset`, `git rebase`, `git push --force-with-lease` hoặc canonical recovery switch. Tiếp theo vẫn cần owner xác nhận phương án và target history; sau đó mới chạy dry-run trên bản sao kiểm soát, đối chiếu `.coding-tools` retention, và publish.

### 16.24. Pointer-only projection plan và clone apply probe — 22/09 khoảng 19:40–19:46 +07

Đã mở rộng [audit-ledger-recovery-candidate.py](../../scripts/audit-ledger-recovery-candidate.py) với hai lớp read-only/clone-only:

1. `problem_projection_reconciliation` chỉ phân loại tail event là `POINTER_ONLY_SAFE` khi cùng current revision/state, state không chuyển, relation là non-transition, link `EXACT`, primary binding hợp lệ và `prev_hash` nối đúng pointer hiện tại. Nó trả `can_apply=false` và yêu cầu authority `RUNTIME_RECONCILIATION`.
2. `isolated_projection_reconciliation_probe` copy candidate sang thư mục tạm rồi mô phỏng compare-and-swap pointer update trên clone; kiểm tra event bytes, state/revision, integrity/FK và projection sau update. Không có đường mở canonical ledger.

Kết quả trên candidate SHA `651f6c40c633974f0f2668f3b18ccfdb751e946f5ce6b8bd7bb96f7dc97d1be5`:

| Gate | Kết quả | Bằng chứng |
| --- | --- | --- |
| Pointer plan | **POINTER_ONLY_SAFE** | `prl-22e…`, revision `1`, state `OPEN`, tail seq `318,319,320`, đều `ENGINEERING_ATTEMPT_BOUND/EXACT/PRIMARY`, `OPEN→OPEN` |
| Proposed pointer | **317 → 320** | Current hash `380a108…`; proposed hash `1ee18f7…` |
| Clone-only apply probe | **PASS** | `applied_pointer_count=1`, `projection_valid_after=true`, `remaining_plan_count=0` |
| State/revision preservation | **PASS** | `state_and_revision_preserved=true`; current revision/state không đổi |
| Immutable event preservation | **PASS** | `events_preserved=true`; không đổi event/hash/chain |
| SQLite post-probe | **PASS** | `integrity=ok`, FK `0` |
| Apply authority | **MISSING** | `can_apply=false`; chưa có supported runtime reconciliation API, quiesced receipt hoặc owner sign-off |

Test bổ sung [test_ledger_recovery_candidate_audit.py](../../tests/test_ledger_recovery_candidate_audit.py) kiểm cả plan invariant và clone-only compare-and-swap. Focused recovery suite hiện tại: **7 tests PASS, 15.217s**; `py_compile` PASS. Đây là bằng chứng semantics trên quarantine/clone, **không** phải canonical projection reconciliation, live activation, Problem closure hoặc quyền replay unknown effects. `activation_eligible` vẫn `false`; unknown-effect và authority gates vẫn mở.

**Next action:** dùng receipt này cho owner review; nếu được cấp supported `RUNTIME_RECONCILIATION` target-specific authority thì mới chạy importer chính thức với rollback backup/postflight. Nếu không, giữ candidate quarantine; không sửa trực tiếp `problem_threads` trên canonical chỉ vì clone probe PASS.

### 16.25. Windows packaged refresh và delivery revalidation — 22/09 khoảng 19:40–20:00 +07

Wave này hoàn tất phần source → package → installation → packaged runtime trên Windows, nhưng không tự mở rộng sang canonical recovery hoặc history rewrite.

**Package/installation:**

- Local source trước wave build là `main@abab565`; từ commit này đến `HEAD=ac24f18` chỉ có thay đổi audit/test/docs/evidence, không thay đổi các đường dẫn được đóng gói (`electron/**`, `renderer/**`, `resources/**`, `control-plane/control_plane/**`, `package.json`).
- Build `electron-builder --win dir` và NSIS chạy PASS ở thư mục ngoài repository. Exact byte/SHA-256 comparison PASS cho `node_agent.py`, bốn Recovery adapter và `runtime_activity.py`; installer NSIS mới có SHA-256 `7D242FD9EA3350A57EA14FE746395428D36BEF2705242B2930E5BEBE2D362281`.
- Installer đã chạy silent exit `0`. Sau cài, các payload critical trong `C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP` trùng source từng byte; package cũ không còn là payload đang được kiểm tra.
- Supervisor được cài lại bằng flow chính thức với `-Packaged -Executable ... -AppRoot ...`; scheduled task `WebMCP Recovery Supervisor` ở `Running`, status `healthy`, host PID/instance mới, không sửa manifest bằng tay.

**Runtime/authority:**

- Packaged `reconcile-authority-status` exit `0`, target count `1`, `workspace_id=workspace_f93b5bac9dc74fae9cea66f44c4ebc94`, `workspace_generation=generation_a91d1829c5bf4c7093a30cec14105c76`, `dispatch_state=dispatchable`, capability chỉ `read=true` (`write=false`, `exec=false`).
- Sau `runtime.restart` chính thức với `full_clean_refresh`, packaged observer đọc `strict_ready=true` trên installation/instance mới. Route evidence là heartbeat authenticated fresh, đúng `device_id`, `endpoint_id`, server origin và `policy_state=enabled`.
- Supervisor vẫn `control_plane_agent_state=started_heartbeat_only`; đây là fail-closed đúng thiết kế khi chưa có standing file-read/patch/exec policy hợp lệ. Không tự cấp thêm C3, write hoặc exec.
- `connector_rediscovered`/natural task outcome chưa được tuyên bố từ heartbeat hoặc strict runtime; đây vẫn là các gate riêng.

**Ubuntu/server boundary:**

- Lượt trước đã có bằng chứng deploy package control-plane `b0b6505` với schema 24, SQLite integrity `ok`, admission vẫn `recovery` và unresolved action chưa được mở. Wave này gọi lại `/healthz` nhưng Windows không resolve được `svhome.tail0e403.ts.net`, nên không ghi đè bằng chứng cũ và không tuyên bố fresh remote readback.
- Không canonical SQLite write, không quarantine/reconcile unknown action, không mở admission và không restart Ubuntu trong wave này.

**Git delivery:**

- Delivery guard PASS (`4876` files); runtime snapshot mới đã được commit cùng source verifier/test. Current local `HEAD=ac24f18`, `origin/main=044dd961`, local ahead `19`, worktree sạch sau commit.
- `git push origin main` đã bị GitHub pre-receive từ chối với `GH001` vì đúng ba executable generated trong lịch sử local chưa publish, mỗi file khoảng `215 MB`, vượt giới hạn `100 MB`. Remote ref không đổi.
- Không dùng `reset`, `rebase`, `filter-repo`, `git lfs migrate` hoặc `push --force-with-lease`. Muốn publish `main` cần owner chọn rõ: loại `output/**` khỏi lịch sử có backup và force-with-lease, chuyển đúng binary sang LFS sau khi xác nhận quota/policy, hoặc chỉ định artifact/release channel khác. Đây là blocker delivery ngoài code, không phải test/source failure.

### 16.26. Phân loại unknown-effect trên candidate và hiệu chỉnh checkpoint live — 22/09 khoảng 20:00–20:08 +07

Checkpoint này bổ sung inventory read-only cho [audit-ledger-recovery-candidate.py](../../scripts/audit-ledger-recovery-candidate.py); không sửa lại các snapshot lịch sử 16.19–16.25. Vì runtime Windows tiếp tục ghi evidence trong lúc làm việc, số hash/live-state dưới đây là một observation window mới, không thay thế hash của candidate quarantine.

**Thay đổi đã triển khai trực tiếp trên `main`:**

- Tách hai trục phân loại: `liveness_classification` (`STALE_CANDIDATE`, `UNRESOLVED_ACTIVE_PARENT`, `TERMINAL_UNKNOWN`) và `effect_safety_classification` (`ORPHAN_SAFE_CANDIDATE`, `OWNER_MANUAL_EVIDENCE`). Không dùng một nhãn stale để suy ra process đã chết hoặc effect chưa xảy ra.
- Inventory theo table/status, process hoặc server instance, `run_id`, `wave_id`, operation/tool và `error_code`; trả thêm cardinality, top aggregates và stale-candidate sample. Output được giới hạn sample 25 dòng/table để không biến verifier thành một kho sao chép payload.
- Chỉ gắn `ORPHAN_SAFE_CANDIDATE` khi summary có field typed chứng minh no-effect (`outcome_unknown=false`, `effect_applied=false`, `effect_state=not_applied/never_sent/...`, hoặc dispatch/admission bị reject trước effect). Category `validation/security/permission` tự nó **không** đủ bằng chứng. `replay_allowed` luôn bằng `0` và `reconciled=false` khi còn bất kỳ unresolved row nào.
- Thêm test regression cho running/in-progress stale candidate, terminal unknown cần owner evidence và typed no-effect candidate. Đây là code/test proof; chưa có importer hỗ trợ để đổi trạng thái canonical.

**Kết quả chạy lại verifier trên candidate quarantine:**

| Hạng mục | Kết quả quan sát | Diễn giải đúng |
| --- | ---: | --- |
| Candidate SHA-256 | `651f6c40c633974f0f2668f3b18ccfdb751e946f5ce6b8bd7bb96f7dc97d1be5` | Candidate không đổi; chỉ đọc + clone probe |
| Snapshot frontier | `2026-09-15T11:37:30.275Z` | Mốc cuối của snapshot candidate, không phải live clock hiện tại |
| `background_operations` | `1309 completed`, `37 orphaned`, `1 running`, `2 timed_out` | `1 running` là stale candidate vì parent RUN/WAVE đã `accepted`; không được mark completed/orphaned trên canonical |
| `idempotency_records` | `8347 completed`, `832 failed`, `662 unknown`, `1 in_progress` | `1 in_progress` không bind RUN/WAVE và cùng process/server lineage với operation reboot; phải giữ unknown/reconcile-required |
| `managed_process_jobs` | `8433 exited`, `155 quiesced`, `40 timeout`, `8 closed`, `2 spawn_failed` | Không còn active/unknown/in-progress managed job trong candidate |
| Tổng unresolved effect | **664** | `1 running background + 662 unknown + 1 in_progress`; con số 663 trước đây chỉ đếm idempotency, chưa cộng background |
| Liveness | `2 STALE_CANDIDATE`, `662 TERMINAL_UNKNOWN` | Stale chỉ là phân loại theo parent/status trong snapshot, không phải live PID proof |
| Effect safety | `0 ORPHAN_SAFE_CANDIDATE`, `664 OWNER_MANUAL_EVIDENCE` | Không có typed no-effect receipt đủ mạnh để tự terminalize |
| Replay | `0 allowed` | Không retry/replay effect unknown hoặc stale |

Cardinality unresolved: **157** process/server instance IDs, **121** `run_id` buckets (trong đó **403/664** rows không bind RUN), và **177** `wave_id` buckets (cùng **403** rows không bind WAVE). Top operation: `agent_workflow=351`, `task_control=162`, `exec_command=144`, `document_workflow=3`, `workspace_context=3`, `command_control=1`. Top error categories: `EXECUTION_OWNER_INVALID=88`, `PREPARED_RUN_BINDING_MISMATCH=83`, `OPERATOR_REPORT_ACK_REQUIRED=60`, `FINAL_ACCEPTANCE_NOT_READY=52`, `SOLUTION_SHADOW_REQUIRED=51`, `REPLAN_REASON_REQUIRED=41`, empty=`32`, `RUNTIME_BUSY=32`, `TASK_STOPPED=31`, `PERMISSION_REQUIRED=30`.

**Đối soát canonical live tại observation mới:**

- `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3` tại `2026-09-22T13:00:19Z` có SHA-256 `10671e3ea80ef459b32badf25f80b3d1b59b5465d94fdca2b0513664ec470076`, kích thước `97,509,376` bytes, `user_version=12`, `integrity_check=ok`, foreign-key violations `0`, `events=25,694`, `problem_events=304`.
- Hash live khác backup rehearsal `c894f57e…` vì runtime tiếp tục tạo evidence; đây là drift/volatility cần snapshot delivery mới, **không** phải bằng chứng candidate đã được switch hoặc canonical đã được recovery.
- `activation_eligible=false`, `problem_projection_reconciled=false`, `problem_projection_pointer_plan_safe=true`, `unknown_effects_reconciled=false`. Pointer `317→320` vẫn chỉ được mô phỏng trên clone; không có canonical write, runtime restart, reboot, package/install, deploy hoặc history rewrite trong checkpoint này.
- Khi capture, `main@ac24f18` là HEAD; sau đó working tree có thay đổi verifier sample/output và report này, cùng các artifact runtime dirty. Không dùng claim “worktree sạch” của checkpoint 16.25 làm current state.

**Quyết định xử lý:** giữ nguyên fail-closed. Owner/support phải cung cấp (1) receipt quiesce + logical SHA mới, (2) supported `RUNTIME_RECONCILIATION` API cho pointer `problem_threads`, (3) per-record classification/evidence cho 664 effect rows, và (4) rollback/postflight receipt trước mọi canonical switch. Chỉ những row có typed no-effect proof mới có thể được xem xét `orphan-safe`; mọi row còn lại vẫn `UNKNOWN/RECONCILE_REQUIRED`, không được đổi thành `completed`, không được replay và không được dùng để đóng hai Problem.

**Validation:** `python -B -m unittest -v tests/test_ledger_recovery_rehearsal.py tests/test_ledger_recovery_candidate_audit.py` — **8 tests PASS, 11.320s**; `python -B -m py_compile scripts/audit-ledger-recovery-candidate.py` — PASS. Đây là proof verifier/rehearsal/clone, chưa phải runtime activation, client strict discovery, reboot, natural-use hay outcome proof.

**Next action exact:** stage snapshot mới theo `npm run stage:coding-tools-delivery`, chạy `npm run check:coding-tools-delivery`, review diff và commit trực tiếp trên `main`; sau đó chỉ thử `git push origin main` một lần. Nếu vẫn gặp `GH001`, dừng ở external delivery blocker và chờ owner chọn history/artifact strategy; không tự filter/LFS/force-push.

### 16.27. Push trực tiếp `main` bị chặn lại bởi generated executable — 22/09 khoảng 20:20–20:27 +07

Đã thực hiện đúng một lần `git push origin main` sau khi `stage:coding-tools-delivery` và `check:coding-tools-delivery` cùng PASS (`4876 files`, ledger blob tại snapshot `e01b447d…`, `user_version=12`). Kết quả pre-receive:

- Remote `origin/main` **không đổi**, vẫn `044dd96178faacc92a049a528eb05baa60b8816a`.
- Local `main` ở `d8efaeb1126a27498f55f8a384a82b75e008e27e`, ahead `24`, behind `0`.
- GitHub cảnh báo canonical `.coding-tools/orchestration/ledger.sqlite3` khoảng `92.99 MB` vượt khuyến nghị `50 MB` nhưng chưa vượt hard limit `100 MB`.
- GitHub từ chối đúng ba generated executable lịch sử: `output/packaged-candidate-final/win-unpacked/Coding Tools MCP.exe`, `output/packaged-candidate-revalidated-20260922-135500/win-unpacked/Coding Tools MCP.exe`, và `output/packaged-candidate-revalidated-20260922-140500/win-unpacked/Coding Tools MCP.exe` (khoảng `215 MB` mỗi file), với `GH001`.

Đây là **external delivery blocker**, không phải lỗi verifier/test hay canonical recovery. Không được coi push thành công, không được tự `filter-repo`, `git lfs migrate`, reset/rebase hoặc `push --force-with-lease`. Owner cần chọn rõ một đường history/artifact: loại generated `output/**/win-unpacked` khỏi lịch sử local chưa publish và giữ manifest/hash ngoài Git; chuyển đúng executable sang LFS sau khi xác nhận quota/policy; hoặc chỉ định artifact/release channel khác. Mọi history mutation phải có bundle backup mới, dry-run path allowlist, kiểm tra `.coding-tools` retention và force-with-lease theo remote guard.

Sau push, runtime tiếp tục tạo dirty evidence (`ledger.sqlite3`, `task-context-workspaces.json`, `performance.json`); hash live ledger đã là `e8cd1aa2dac11f2fca0a4b71a1e32d6b37ed49e4499b867c9d17ffa0d428866b`, không dùng hash này để thay receipt delivery snapshot đã commit. Hai Problem vẫn OPEN; candidate recovery vẫn quarantine, `activation_eligible=false`, và không có canonical switch.

### 16.28. Fresh rehearsal sau live drift: candidate vẫn quarantine — 22/09 lúc 20:12–20:14 +07

Không dùng candidate rehearsal cũ sau khi runtime đã thay đổi canonical. Đã tạo lại một snapshot bằng SQLite Online Backup API từ live ledger hiện tại với exact historical allowlist gồm `dcb539e0e1694bc1bb29eed2b2e07f8b`, `d01a5dce50c846fc8e13673cdfc8b3b3`, `b194ab1e311e42efa1dd0614ca245037`.

| Artifact | Giá trị |
| --- | --- |
| Capture UTC | `2026-09-22T13:12:58.981897+00:00` |
| Fresh current backup SHA | `2caabf5c1a0a21bdcca3e5ec530cfe53e2d70dbef4381e4ff78ba532f5e33957` |
| Fresh candidate SHA | `54d184807dd9af667fda67d2e7735578d4b7d03d845477d3b626328db62ee8e9` |
| Artifact directory | `E:\Caches\Temp\codex-ledger-recovery-rehearsal-9ncd608f` |
| Historical SHA | `e7700489c3ecd85afcd2c21c36967741793fef73f36aad47a47da8f9887de9b6` |
| Artifact protection | current backup, historical blob và candidate đều write-protected |

Fresh rehearsal giữ nguyên current rows, integrity `ok`, FK `0`, và thêm đúng 3 RUN / 4 WAVE / 3 checkpoint / 5 proof / 128 event / 3 problem-event cùng các row telemetry/evidence nêu ở checkpoint trước. Historical authority (`3 controller_leases`, `1 reattach receipt`, `3 hub clients`) vẫn withheld. Kết quả verifier không đổi về bản chất: pointer plan `POINTER_ONLY_SAFE` nhưng `can_apply=false`; `problem_projection_reconciled=false`; `unknown_effects_reconciled=false`; 664 effect rows vẫn cần owner/manual evidence; `activation_eligible=false`.

**Lý do không apply live:** canonical hiện tại đã không còn `running`/`in_progress` effect rows của candidate cũ, trong khi candidate historical bắt buộc phải mang chúng để bảo toàn exact evidence. Copy candidate hoặc mark các row đó completed sẽ làm hồi sinh stale effect/authority và vi phạm fail-closed. Source hiện chỉ có `problem_reconcile_provisional_from_checkpoint` cho một accepted checkpoint hợp lệ; không có supported importer để nhập lại exact historical immutable rows và compare-and-swap projection `problem_threads` mà không trực tiếp SQL-copy. Vì vậy fresh rehearsal là bằng chứng recovery plan, không phải quyền canonical switch.

**Trạng thái wave:** `REPLAN_REQUIRED / OPERATOR_REVIEW_PENDING`, không phải `COMPLETE` và chưa phải `BLOCKED` vĩnh viễn. Next action duy nhất để tiến tới live recovery là cung cấp supported importer/`RUNTIME_RECONCILIATION` contract với quiesce receipt, exact logical-SHA guard, per-row unknown disposition, rollback backup và postflight integrity/projection/authority readback. Cho tới khi có contract đó, giữ candidate ngoài repository ở quarantine, không sửa trực tiếp `ledger.sqlite3`, không replay unknown effect và không đóng hai Problem.

### 16.29. Regression A0/A1/A2 và fresh rehearsal sau khi được phép tiếp tục — 22/09/2026 khoảng 20:05–20:26 +07

Lượt này tiếp tục **trực tiếp trên `main`, không tạo worktree**. Trong khi chạy, một tiến trình delivery khác đã tạo commit snapshot `23f86f0` (`chore: refresh delivery snapshot before publish`); tôi giữ nguyên commit đó và không sửa/revert các file evidence concurrent. Tại checkpoint:

```text
HEAD         = 23f86f0d81d1bf03a66ad8c104805db29baca595
origin/main  = 044dd96178faacc92a049a528eb05baa60b8816a
remote change= none observed
dirty        = .coding-tools/orchestration/ledger.sqlite3
               .coding-tools/orchestration/task-context-workspaces.json
               .coding-tools/performance.json
```

#### A0/A1 — source safety và rollback intent

Không thêm một đường kill/restart mới. Source hiện hành đã giữ các guard của `recoveryBootstrap` và `recoveryIpc`, sau đó tôi chạy lại proof trên đúng checkout hiện tại:

| Oracle | Kết quả |
| --- | ---: |
| `node --test tests/recovery-bootstrap.test.js` | **41/41 PASS**, 9.787 s |
| `node --test tests/recovery-bootstrap.test.js tests/recovery-host.test.js` | **84/84 PASS**, 22.641 s |
| `node --test tests/boot-acceptance.test.js tests/boot-runtime-observation.test.js` | **51/51 PASS**, 0.356 s |

Các negative phân biệt được đúng ba lớp:

1. **Semantic refusal có response provenance** (`busy`, `authority denied`, handler refusal, kể cả mã giống `ECONNRESET`) dừng handoff; `terminate=0`, `spawn=0`, `start rollback=0`.
2. **Transport loss** chỉ được đi tiếp nếu forced authenticated snapshot chứng minh runtime/native/Tunnel đã dừng, đúng workspace và không busy/recovering; thiếu proof trả typed `RECOVERY_BOOTSTRAP_STOP_UNCONFIRMED`, không terminate.
3. **Rollback** chỉ có thể gọi `runtime.start` khi baseline thật sự đang ON, owner/PID/start-token/descriptor vẫn exact, epoch/workspace/role còn nguyên và sau stop đã chứng minh stopped. Baseline OFF, UNKNOWN, partial, manual-stop, recovering hoặc epoch đổi đều không tự bật lại. Central executor không bị biến thành direct Tunnel.

Điều này đóng **local source/test proof** cho P1/P2; nó chưa phải installed runtime, reboot, package hoặc live client acceptance. Snapshot observation là evidence để quyết định, không phải giấy phép bỏ qua lifecycle authority.

#### A2 — role-aware oracle và false-green

Oracle v2 và collector hiện hành cũng qua toàn bộ **51/51** test: receipt chỉ được nhất quán khi có reboot sequence, fresh packaged host/start-token, Supervisor target đúng, revision/epoch/contract đồng nhất, `fullyReady=true`, primary MCP/native sống, role-specific Tunnel/central binding, connector discovery và một `workspace_context` đã hoàn tất đúng target/request. Các biến thể chỉ có PID/hash/health, workspace sai, generation sai, epoch cũ, MCP/Tunnel chết, stale/future client, policy hết hạn hoặc compatible ACK bị ghi nhầm là strict đều **NOT_PROVEN**.

#### Fresh controlled rehearsal — vẫn quarantine, không switch canonical

Để không dùng candidate cũ sau live drift, đã tạo lại Online Backup snapshot và rehearsal mới bên ngoài repository:

```text
artifact directory = E:\Caches\Temp\codex-ledger-recovery-rehearsal-live-y7r_wey2
historical blob    = bed5b266a83e4cbc3947f5dd15854d80f58f6264
historical SHA     = e7700489c3ecd85afcd2c21c36967741793fef73f36aad47a47da8f9887de9b6
current backup SHA = a318f2330fc7d391d3189332ce395fb8d810c6c745972c65d606e399cde2dc33
candidate SHA      = 02f184cb62288fb82c8dc8724081050a0fc42bc880d683365605180b1f418ae5
```

Rehearsal/audit mới nhất giữ nguyên current rows, integrity `ok`, FK `0` và thêm đúng các historical rows đã allowlist:

```text
3 RUN / 4 WAVE / 3 checkpoint / 5 proof / 128 events / 3 problem_events
12 continuity_telemetry / 1 controller_knowledge_ack
6 background_operations / 18 idempotency_records / 7 managed_process_jobs
```

Các gate không đổi về bản chất:

| Gate | Kết quả |
| --- | --- |
| Append/duplicate probe trên clone | **PASS** |
| Pointer-only plan `problem_threads` | **SAFE TO PROPOSE**, clone CAS **PASS** |
| `problem_projection_reconciled` | **false** |
| Unknown effects | **664**, gồm `2 STALE_CANDIDATE` + `662 TERMINAL_UNKNOWN`; effect safety `OWNER_MANUAL_EVIDENCE=664` |
| Replay unknown/stale effect | **0 allowed** |
| `activation_eligible` | **false** |
| Canonical mutation | **false** |

Historical authority (`controller_leases`, `controller_reattach_receipts`, `hub_clients`) tiếp tục được withheld. Candidate vì thế **không được copy vào live**: làm vậy sẽ hồi sinh historical `running/in_progress` residue mà live canonical hiện không còn, đồng thời có thể trộn authority cũ vào workspace hiện tại. Không mark các row đó completed, không replay, không sửa SQL trực tiếp.

#### Operator checkpoint

- **Đã hoàn thành:** regression proof A0/A1, role-aware A2 oracle proof, fresh candidate rehearsal và audit trên clone.
- **Trạng thái hiện tại:** hai Problem vẫn `OPEN`; candidate vẫn `QUARANTINED_REHEARSAL`, `activation_eligible=false`; canonical ledger chưa bị thay đổi, không restart/kill/reboot/install/deploy/push trong wave này.
- **Blocker phân loại:** thiếu supported canonical importer/`RUNTIME_RECONCILIATION` cho historical immutable rows + pointer CAS; thiếu disposition có typed evidence cho 664 effect rows; thiếu quiesce/rollback/postflight receipt. Đây là blocker authority/evidence, không phải test failure.
- **Còn lại:** chốt importer contract và operator approval; sau đó mới có thể quiesce đúng owner, snapshot/hash exact, apply transactional target-specific, postflight integrity/projection/authority readback và fresh MCP/Tunnel/client oracle. C09/C12/BG natural outcome/48-hour gate vẫn mở.
- **Exact next action:** giữ candidate ngoài repository và chờ supported importer/receipt contract; không retry `git push` (GH001 large-file history blocker chưa đổi), không tự filter/LFS/force-push.

### 16.30. Evidence-only recovery importer và clone proof — 22/09/2026 lúc 20:54 +07

Đã triển khai trực tiếp trên `main`, không tạo worktree, một primitive hỗ trợ recovery có kiểm soát:

- [ledger_evidence_recovery.py](../../resources/coding-tools-mcp/coding_tools_mcp/ledger_evidence_recovery.py) tách rõ `preflight_evidence_recovery`, `capture_quiesce_receipt` và `apply_evidence_recovery`.
- [recover_ledger_evidence.py](../../resources/coding-tools-mcp/scripts/recover_ledger_evidence.py) cung cấp CLI `preflight`, `capture-quiesce`, `apply` với exact hash/allowlist/receipt guards.
- [test_ledger_evidence_recovery.py](../../resources/coding-tools-mcp/tests/test_ledger_evidence_recovery.py) chứng minh importer không phải đường SQL copy tự do: append evidence trong transaction, compare-and-swap pointer, withheld effect/authority, source drift refusal và stopped-runtime refusal.

Boundary của importer được đóng như sau:

1. Chỉ cho phép append các bảng immutable evidence (`runs`, `waves`, `checkpoints`, `proofs`, `events`, `problem_events`, `continuity_telemetry`, `controller_knowledge_acks`) từ candidate có cùng schema và không được thay đổi row hiện tại.
2. `controller_leases`, `hub_clients`, reattach/continuation/claim/cursor authority và các bảng effect (`background_operations`, `idempotency_records`, `managed_process_jobs`) không bao giờ được nhập. Các row historical này chỉ được đếm, phân loại và trả lại trong receipt `withheld_*`; `replay_allowed` cố định bằng `0`.
3. `problem_threads` chỉ được cập nhật pointer sau khi event tail đã tồn tại và qua CAS exact `problem_id + revision + state + old seq/hash`; tail phải cùng revision/state, `EXACT`, quan hệ non-transition và hash-chain nối đúng. Không đổi resolution state, closed time, revision hoặc outcome.
4. Apply yêu cầu exact current/candidate physical + logical SHA, quiesce receipt có `runtime_stopped=true`, ownership live bằng `0`, exclusive `ledger_access_gate`, rollback backup mới, transaction `BEGIN IMMEDIATE`, foreign-key/integrity/event-chain postflight và expected logical SHA từ clone.

Focused proof:

```text
python -B -m py_compile resources/coding-tools-mcp/coding_tools_mcp/ledger_evidence_recovery.py resources/coding-tools-mcp/scripts/recover_ledger_evidence.py resources/coding-tools-mcp/tests/test_ledger_evidence_recovery.py  PASS
python -B -m unittest -v tests/test_ledger_evidence_recovery.py                 3/3 PASS
python -B -m unittest -v tests/test_ledger_recovery_candidate_audit.py tests/test_ledger_recovery_rehearsal.py  8/8 PASS
```

Trong cùng observation window, canonical live ledger vẫn sạch về SQLite nhưng đang volatile:

```text
HEAD = 5b5c775d668fa3ac4f564de0d018bd6933243bad
ledger physical SHA = 8cdb5cc817c120f907fa1dd99342c23149b90697641450d43b1790785ec0dece
ledger logical SHA  = 5cad9211f9c80724eba44d6a3e9c1b44e06586641ca6223639255f2f36a7ab0d
integrity = ok; foreign-key rows = 0; schema = 12
dirty runtime evidence = ledger.sqlite3, task-context-workspaces.json, performance.json
```

Candidate `E:\Caches\Temp\codex-ledger-recovery-rehearsal-live-y7r_wey2\QUARANTINED-candidate.sqlite3` vẫn là candidate của snapshot cũ (`physical SHA 02f184...`, `logical SHA 2b9d...`), nên **chưa được phép dùng apply**: importer phải từ chối source/candidate mismatch thay vì ghép candidate cũ vào canonical mới. Chưa có canonical mutation, restart, reboot, replay effect, Problem closure hay natural-outcome proof trong checkpoint này.

**Operator checkpoint:** phần còn thiếu để chạy live là (a) quiesce runtime qua owner hợp lệ, (b) tạo fresh candidate từ cùng snapshot current và historical allowlist, (c) capture quiesce receipt mới, (d) chạy preflight CLI rồi review receipt, và chỉ sau đó (e) apply một lần với rollback backup. Exact next action là dừng writer có kiểm soát và tạo fresh rehearsal; nếu live snapshot drift hoặc ownership không-zero, giữ `REPLAN_REQUIRED`, không cưỡng ép importer.

### 16.31. Fresh preflight bị từ chối vì runtime-ledger drift — 22/09/2026 lúc 20:56 +07

Đã tạo một fresh rehearsal bên ngoài repository với historical blob exact `bed5b266...` và allowlist ba RUN (`dcb539e0...`, `d01a5dce...`, `b194ab1...`):

```text
artifact directory = E:\Caches\Temp\codex-ledger-recovery-xhveo95j
candidate SHA      = ecc7a08c7815f574e058e9006d22166b56073950b062c321e2582d2be48c0215
candidate logical  = 26fb496aab7505df50c6d67f335c2ba9d5e89f3e040c5610da0216e3e0fee374
```

Lần gọi CLI `preflight` đầu tiên **không được phép chạy tiếp** với receipt đã chuẩn bị: guard trả `RECOVERY_CURRENT_SHA256_MISMATCH`. Khi đọc lại ngay sau đó, canonical đã chuyển từ physical/logical `86d6d29e... / ad161247...` sang `ed196da8... / 663d6f63...` trong cùng cửa sổ. SQLite vẫn `integrity=ok`, FK `0`, nhưng causal ledger là volatile do các writer/evidence events khác; đây là drift thật, không phải lỗi candidate.

**Operator checkpoint:** importer đã chứng minh guard drift hoạt động; không canonical mutation, không pointer update, không effect replay và không Problem closure xảy ra trong wave này. Exact next action là chạy một bounded sequence duy nhất trong cửa sổ đã quiesce: snapshot live → tạo candidate từ đúng snapshot → preflight → capture stopped receipt → apply transaction + rollback backup. Nếu sequence đó còn thấy drift dưới exclusive gate, dừng ở `REPLAN_REQUIRED` và giữ candidate quarantine.

### 16.32. Publish và triển khai Ubuntu đã xác minh; admission vẫn đóng — 22/09/2026

Wave này hoàn tất việc đưa bản source đã publish lên control plane Ubuntu theo release identity cố định, đồng thời ghi nhận rõ các gate chưa được phép đóng. Đây là deployment evidence, không phải bằng chứng rằng execution/admission đã sẵn sàng.

**Git và release identity:**

- Lịch sử local đã được làm sạch các blob `output/**` vượt giới hạn GitHub; backup refs/bundle vẫn được giữ riêng. Push `--force-with-lease` đã thành công trước wave này.
- `main` và `origin/main` cùng ở `5b5c775d668fa3ac4f564de0d018bd6933243bad` tại thời điểm triển khai.
- Package source fingerprint: `sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2`.
- Release archive SHA-256: `bb5f8ebcfe6b2de0b48e05488637c03b00bed6cb1d57a934db80aa648790b48f`.

**Ubuntu readback sau activation:**

- Release hiện tại: `/home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-5b5c775d668fa3ac4f564de0d018bd6933243bad`.
- Schema `24`; package fingerprint và declared source revision khớp release trên.
- `codex-control-plane.service` ở trạng thái `active` và `enabled`; service instance `cp_73a8a26bbc4f4504b341abe6f3619ee0`, `MainPID=984081`.
- Backup trước deploy có SHA-256 `f5a3160676054e64f5d09bc589f9e236dd97b8b829f97a0b6acedcebfb5ddf3c`, SQLite integrity `ok`, schema `24`.
- HTTPS root/admin trả HTTP `200`; `/healthz` trả `ok=true`, SQLite integrity `ok`, schema `24`, đúng package/source revision.

Healthcheck tự động vẫn **fail-closed** với `control-plane automatic backup is stale or not restorable`. Nguyên nhân cụ thể đã đọc lại là `unquarantined_unresolved_action_count=1`, không phải kết luận backup hỏng. Action còn mở là `act_0f0a49c6424d42d3bc7bc49ad46e4ffa` (`workspace_context`, `dispatch_unconfirmed`, không có receipt), gắn với canary cũ `canary-fixture-daochienthang` đang stale/unavailable. Không mark completed/cancelled, không replay, không sửa trực tiếp SQLite và không mở admission; `admission_mode=recovery`, unresolved count `11`, trong đó `10` historical unknown đã quarantine và `1` vẫn cần node-side reconciliation hoặc operator decision có evidence.

**Windows boundary:** profile `DESKTOP-63643J4` đã `approved`, route evidence báo `runtime_readiness=ready`, `policy_state=enabled`, origin `https://svhome.tail0e4032.ts.net`, và Supervisor packaged đang `healthy`. Tuy nhiên `npm start` không được handoff sang checkout dev vì guard trả `RECOVERY_HOST_IDLE_HANDOFF_REFUSED`; packaged Recovery Host chưa chứng minh idle. `npm run dev:status` vì vậy chỉ phản ánh development UI `MISSING`/`connector_state=UNAVAILABLE`, không phủ nhận packaged node đang sống. Không kill theo tên process, không restart để bypass guard, không lặp `dev:refresh`.

**Importer/evidence:** ba file importer evidence-only và focused tests đã được thêm ở section 16.30–16.31; chúng chưa được chạy `apply` trên canonical ledger. Các thay đổi source/document/evidence ở wave này sẽ được commit và push, nhưng không cần redeploy package Ubuntu vì không chạm `control-plane/**` hoặc package fingerprint đã deploy. Natural task/canary outcome, strict client discovery và điều kiện mở admission vẫn chưa được chứng minh.

**Operator checkpoint:** Git publish và Ubuntu package/service update đã hoàn tất, admin page đã tồn tại và node Windows đã có route/approval evidence. Blocker còn lại là một `dispatch_unconfirmed` thiếu receipt, development handoff thiếu idle proof, và thiếu natural-work outcome. Exact next action là giữ `recovery`, thu thập reconciliation evidence cho action trên hoặc quyết định operator có target-bound receipt; chỉ sau đó mới chạy canary có kiểm soát. Không gọi goal là `COMPLETE` chỉ từ HTTP `200`, `/healthz`, package fingerprint hay test importer.

### 16.33. Đóng contract gap allowlist cho evidence thuộc RUN hiện hữu — 22/09/2026 lúc 21:11 +07

Rehearsal trước đã chỉ ra đúng một gap của importer: hai row `continuity_telemetry` mới có `run_id` thuộc RUN đã tồn tại (`076dbebd4f1a464092905c388398709f`), trong khi guard chỉ cho phép `allowed_run_ids` là các RUN mới. Không sửa bằng cách cho phép mọi RUN hiện hữu.

Đã cập nhật trực tiếp trên `main`, không tạo worktree:

- [ledger_evidence_recovery.py](../../resources/coding-tools-mcp/coding_tools_mcp/ledger_evidence_recovery.py) tách bốn tập kiểm soát: `allowed_run_ids` (RUN mới), `allowed_existing_run_ids` (RUN hiện hữu nhận evidence), `allowed_evidence_ids` (identity của `controller_knowledge_acks` như trước), và `allowed_existing_evidence_ids` (identity chính xác của từng row bổ sung vào RUN hiện hữu).
- Identity ưu tiên khóa semantic ổn định của từng bảng (`logical_id`, `event_id`, `ack_id`, `checkpoint_id`, `proof_id`, `wave_id`), fallback về primary key/composite key đúng schema; với `continuity_telemetry` là đúng `logical_id`, do đó không thể mở rộng quyền chỉ bằng tên RUN. Allowlist RUN/evidence phải khớp **exact set**, không nhận identity thừa hoặc thiếu.
- Preflight receipt ghi rõ `run_ids`, `existing_run_ids`, `evidence_ids`, `existing_evidence_ids`; apply đọc lại chính receipt đó và chạy lại guard dưới exclusive gate.
- `apply_eligible` trong receipt chỉ có nghĩa là append evidence-only có thể tiếp tục sau khi đủ quiesce/rollback/owner gates; `activation_eligible` vẫn `false` khi còn authority/effect bị withheld, nên không được hiểu là admission hay execution đã mở.
- [recover_ledger_evidence.py](../../resources/coding-tools-mcp/scripts/recover_ledger_evidence.py) thêm `--allow-existing-run-id` và `--allow-existing-evidence-id`; flag cũ `--allow-evidence-id` vẫn giữ riêng cho knowledge-ack evidence.
- [test_ledger_evidence_recovery.py](../../resources/coding-tools-mcp/tests/test_ledger_evidence_recovery.py) thêm negative/positive proof: thiếu existing RUN bị từ chối; có RUN nhưng thiếu/wrong logical ID bị từ chối; đúng RUN + đúng identity được preflight; current rows/pointer/effect boundary không bị nới.

Validation sau patch:

```text
python -B -m py_compile coding_tools_mcp/ledger_evidence_recovery.py scripts/recover_ledger_evidence.py tests/test_ledger_evidence_recovery.py  PASS
python -B -m unittest -v tests/test_ledger_evidence_recovery.py                                      5/5 PASS
python -B -m unittest -v tests.test_ledger_recovery_candidate_audit tests.test_ledger_recovery_rehearsal 8/8 PASS
```

Tại observation gần nhất, canonical ledger vẫn `integrity_check=ok`, foreign-key `0`, `compact_allowed=true`, active controller/write-fence/managed-job/background-operation ownership đều `0`; native primary MCP đã được dừng bằng authenticated Recovery Host trước wave này. Recovery Supervisor/Recovery Host/recovery plane vẫn resident để giữ quyền điều khiển an toàn, nhưng không có bằng chứng chúng đang ghi ledger. Chưa có canonical mutation, pointer CAS, effect replay, restart, reboot, Problem closure hoặc natural-outcome proof.

**Exact next action:** trong một cửa sổ bounded duy nhất, tạo Online Backup mới từ canonical hiện tại → merge historical blob với ba RUN allowlist và hai `continuity_telemetry` identity hiện hữu → preflight với exact current/candidate physical+logical hash → capture quiesce receipt → apply atomic dưới `ledger_access_gate` với rollback backup mới → postflight integrity/FK/event-chain/pointer/authority/effect readback. Nếu bất kỳ hash hoặc mtime nào drift trước commit, dừng và giữ candidate quarantine; không dùng candidate cũ.

### 16.34. Controlled recovery evidence-only đã apply và postflight đạt — 22/09/2026 lúc 21:24 +07

Đã thực hiện đúng một bounded sequence mới trên canonical `E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3`, sau khi native primary MCP được dừng qua authenticated Recovery Host. Không dùng candidate cũ, không copy file đè, không replay effect và không restart/reboot.

**Artifact/receipt ngoài repository:**

- Candidate mới: `E:\Caches\Temp\codex-ledger-recovery-rehearsal-7ogq2l4i\QUARANTINED-candidate.sqlite3`, physical SHA `2657fc2b6388b6c632e4ea9aee3adda9015c404e9bab287c653c70ddfd45d301`, logical SHA `012c2542270e48267acf2f9a443f0648b073430c24ee1986341ada4feffba5c5`.
- Preflight: `E:\Caches\Temp\codex-ledger-controlled-t8c1u72\preflight-receipt.json`; quiesce: `quiesce-receipt.json`; apply: `apply-receipt.json`; rollback: `rollback-before-apply.sqlite3`.
- Pre-apply canonical SHA/logical SHA: `07e39583d46a21f5b01602ba4cb0a88de0eaa335fbd9e2723e4be181458eed75` / `b7d3fb6138b6b9cc2e4b21fa8a3215d6d2436ca156b927d425d744ddcc410eba`.
- Post-apply canonical SHA/logical SHA: `07d76b2fd37e3872f278b4835ea29b49cb39b751642df0f247fcb4113f837663` / `988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d`.
- Rollback backup giữ đúng pre-apply physical/logical SHA và `integrity=ok`, FK `0`; artifact được đặt read-only.

**Import và projection:**

```text
runs                       +3
waves                      +4
checkpoints                +3
proofs                     +5
events                    +128
problem_events             +3
continuity_telemetry       +12
controller_knowledge_acks  +1
```

- `prl-22e670302757c9b7663170e226ed7c26`: exact CAS pointer `317 → 320`, revision `1`, `OPEN → OPEN`, `closed_at=null`.
- `prl-e918c7d33e70c2d304d0797e11b05fcb`: revision `2`, `OPEN`, `closed_at=null`, pointer `316` và hash không đổi.
- Không import authority table; effect additions bị withheld: `background_operations=6`, `idempotency_records=18`, `managed_process_jobs=7`. `replay_allowed=0`; các trạng thái `running/in_progress/unknown` vẫn là unknown-effect evidence, không bị mark completed/orphaned bằng recovery này.

**Postflight độc lập:**

- `PRAGMA integrity_check=ok`, foreign-key violations `0`.
- Event hash-chain kiểm tra lại `25,822/25,822` event hợp lệ.
- So sánh toàn bộ authority/effect tables với rollback backup cho kết quả **không table nào thay đổi**; không resurrect lease, fence, hub client, continuation, job hay effect.
- Ba RUN historical hiện có status `accepted` đúng theo source evidence, nhưng đây chỉ là nối lại causal evidence; không phải Problem resolution hoặc natural outcome.
- Sau apply, native primary MCP PID `50956` vẫn absent; Recovery Supervisor `47772`, Recovery Host `42556`, recovery MCP `38200` và control-plane agent `37104` vẫn resident. Ledger mtime ổn định trong 4 giây; không có post-apply writer drift quan sát được.

**Phân loại kết quả:** recovery **đã hoàn tất ở tầng evidence continuity + safe pointer CAS**. Đây không phải activation/admission, không phải reboot acceptance, không chứng minh MCP/Tunnel/client discovery, không tạo authority continuation grant và không đóng Problem. Hai Problem vẫn `OPEN`; C09/C12, 18-criterion durable continuation, natural-use/independent outcome, strict workspace-context read và release gates vẫn mở.

**Exact next action:** review diff/runtime evidence, chạy `npm run stage:coding-tools-delivery` và `npm run check:coding-tools-delivery`, rồi commit/push evidence trực tiếp trên `main`. Không redeploy/restart control plane trong wave này; GH001 generated-executable history warning và các gate runtime/natural outcome phải được báo riêng, không trộn vào acceptance của recovery ledger.

### 16.35. Recheck sau controlled recovery và checkpoint trước delivery trực tiếp trên `main` — 22/09/2026 khoảng 21:37–21:45 +07

Wave này không tạo worktree và không thực hiện restart/reboot/deploy. Mục tiêu là đối chiếu lại đúng canonical state sau apply, phân biệt runtime recovery với runtime usability, rồi chuẩn bị delivery snapshot theo chính sách giữ toàn bộ `.coding-tools` evidence.

**Git và phạm vi thay đổi**

- Checkout hiện tại là `main`; `HEAD = origin/main = 02e2a6b5dfa8d138be403b64617c2a3e6f3489aa`.
- Trước khi stage, chỉ canonical `.coding-tools/orchestration/ledger.sqlite3` dirty do byte-level live evidence sau controlled recovery; không có source/test file ngoài các commit đã ghi ở 16.30–16.34.
- Không dùng `reset`, `restore`, `clean`, worktree hoặc copy đè SQLite. Việc user yêu cầu “up thẳng lên main” được thực hiện theo nghĩa commit/push trực tiếp trên checkout `main`, nhưng chỉ sau khi delivery guard xác nhận snapshot ledger và receipt cùng một index.

**Canonical ledger read-only recheck**

`report_lifecycle_census.py --summary` dùng SQLite Online Backup API, `mode=ro` và `query_only`; capture `2026-09-22T14:37:07.425Z` (`21:37:07.425 +07`). Kết quả:

| Chỉ số | Giá trị hiện thấy | Ý nghĩa không được suy rộng |
| --- | ---: | --- |
| SQLite schema / integrity / FK | `12` / `ok` / `0` | Ledger đọc được và không có FK violation; không phải proof runtime/client |
| Backup snapshot physical SHA | `b65bf7e066b2929987f43fa2feefae14090dfbdb63c06741c2f8d372792e5b1` | Hash của bản Backup API; phải bind lại khi stage, không trộn với candidate cũ |
| Logical SHA | `988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d` | Khớp logical state sau apply |
| `events` / max seq | `25,822` / `59,822` | Causal tail hiện thấy trong canonical |
| `runs` | `557` | Bao gồm ba RUN historical vừa được nối lại; không phải 557 natural tasks |
| `problem_events` / max seq | `307` / `320` | Pointer `prl-22e…` đã CAS tới 320 |
| ordinary active RUN / P5 anchor | `17` / `6` | Đều là projection/candidate classification; không chứng minh process sống |
| stale background residue / unbound live resource | `0` / `0` | Không có residue được census nhận diện; unknown effects vẫn không được replay |
| projection mode | `CONTEXTUAL_PROJECTIONS`, `1079` contexts | Projection không có binding current RUN cho hai Problem; không thay canonical causal history |

Truy vấn exact revision sau apply cho kết quả không đổi về authority:

- `prl-22e670302757c9b7663170e226ed7c26` revision 1: `OPEN`, pointer `320`, `66 RUN = 47 accepted + 16 aborted + 3 active`, `closed_at=null`.
- `prl-e918c7d33e70c2d304d0797e11b05fcb` revision 2: `OPEN`, pointer `316`, `39 RUN = 16 accepted + 10 aborted + 13 active`, `closed_at=null`.
- Cả hai revision vẫn có `coverage_manifest/criterion_dispositions = 0`, `problem_outcome_claim = 0`, và `continuation_success = 0` trong tập exact binding. Accepted RUN và `REPORT_ACKNOWLEDGED` không được nâng thành resolution/natural outcome.
- Đính chính cách đếm: event-distinct `run_id` từng cho 64/40 vì có event `OPEN`/`REVISION`/`USER_FEEDBACK` với `run_id=''`; khi lọc `ENGINEERING_ATTEMPT_BOUND` và join `runs`, không có non-empty dangling RUN ID. Khoảng thiếu còn lại là ba report/checkpoint lịch sử đã được nối lại bằng importer; đó là lineage gap đã xử lý ở tầng evidence, không phải bằng chứng Problem đã đóng.

**Runtime/process recheck — strongest state remains fail-closed**

- Recovery Supervisor script PID `47772` đang `healthy`; packaged Recovery Host PID `42556` có executable `C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP\Coding Tools MCP.exe` và `--recovery-host`; Recovery MCP PID `38200` đang resident; connected control-plane agent PID `37104` ở `started_heartbeat_only`.
- Exact persisted final census trong `activation-epoch.json` ghi `workspace_matches=true`, `process_identity_verified=true`, `authority_ready=true`, Coding MCP running revision = disk revision `57531dd62073778b223bed695728221b0f1fa522bb6d7c40d56f3a955802c747`, `mcpRunning=true`, `nativeAlive=true`, nhưng `tunnelRunning=false`, `componentsReady=false`, `fullyReady=false`, `updateIncomplete=true`.
- Cùng receipt ghi `connectorContractState=CHANGED_NEEDS_DISCOVERY`, `connectorRediscovered=false`, `connectorRefreshRequired=true`, không có connector ACK/freshness. `runtime-state.json` cũng không có native/tunnel PID hiện hành. `node scripts/dev-ui-lifecycle.js status` trả `state=MISSING`, `installation=mismatch`, `connector_state=UNAVAILABLE` cho development UI.
- Outer epoch envelope có `state=READY/admission_state=OPEN`, nhưng final census của cùng epoch lại là `UPDATE_INCOMPLETE/admission_open=false`. Vì vậy phải chọn nhánh fail-closed chặt hơn: biết host/process và authority, nhưng chưa có primary MCP/Tunnel/connector usable. Không dùng trường outer stale để gọi hệ thống `fullyReady` hoặc mở canary.

**Proof source và boundary**

- P1/P2 handoff safety, A2 role-aware oracle và evidence-only importer đã có focused source proof; continuation suite gần nhất là `140 passed, 10 subtests passed` trên cùng source HEAD.
- Đây vẫn chưa phải process-level fault injection qua restart/lost ACK/effect boundary, strict `tools/list`/`server/discover`, real `workspace_context`, provider/App Server dispatch, reboot/logon, Machine B, 48-hour natural-use hoặc independent user outcome.
- Không restart/kill/reboot để “lấy thêm xanh”, không tự tạo natural task, không auto-ACK knowledge thiếu và không mark unknown effect completed. B0–B4, C09/C12 và bốn continuity/BG natural gates vẫn mở.

**Operator checkpoint**

- **Đã hoàn thành:** canonical evidence continuity và pointer CAS đã apply có rollback/postflight; current ledger/runtime/process được recapture; các denominator và lineage correction được ghi rõ.
- **Trạng thái hiện tại:** hai Problem vẫn `OPEN`; recovery plane resident; primary MCP process-level census có nhưng tunnel/connector chưa usable; Git chưa có commit mới sau 02e2a6b5.
- **Phân loại blocker:** không còn là thiếu chứng minh Supervisor spawn; blocker hiện tại là `UPDATE_INCOMPLETE`/connector discovery, authority cho live activation, process-level fault proof và natural outcome. Đây là blocker evidence/authority, không phải test failure.
- **Exact next action:** chạy `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery`, review index/delivery receipt, commit trực tiếp trên `main` và push `main` nếu guard PASS. Sau delivery chỉ tiếp tục bằng một activation epoch mới có receipt exact; không dùng epoch outer `READY/OPEN`, không reboot và không đóng Problem trước khi có strict discovery + workspace outcome.

### 16.36. Ubuntu đã nạp revision hiện hành từ Git bằng release LF sạch — 22/09/2026 lúc 21:41 +07

Sau checkpoint 16.35, đã triển khai lại control plane từ đúng `origin/main`/`HEAD=02e2a6b5dfa8d138be403b64617c2a3e6f3489aa`. Build trực tiếp từ Windows working tree bị loại trước activation vì CRLF làm fingerprint khác; release chính thức được build từ detached worktree sạch của đúng commit để giữ byte LF ổn định.

**Artifact và preflight:**

- Release archive SHA-256: `07ded62a44b79a9e7c2bc84198ac7ebd5aa58ba96b59851e2c1b304564a58eb8`.
- Remote manifest verification: `34` files, schema `24`, source revision `02e2a6b5...`, package fingerprint `sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2`.
- Bản CRLF fingerprint `sha256:3e13c165...` không được cài; không có artifact không xác định nào được trỏ vào `current`.
- Backup ngay trước activation: snapshot SHA-256 `9c51f92589602811fb0a64a331153b28dd849adf7ef31c381c9b39292029502b`, schema `24`, SQLite integrity `ok`, FK `0`, admission `recovery`.
- Protected env/drop-in đã được prepare atomic; cả revision và expected package fingerprint cùng khớp manifest.

**Remote readback sau switch/restart:**

```text
current = /home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-02e2a6b5dfa8d138be403b64617c2a3e6f3489aa
service = active, enabled
MainPID = 991827
NRestarts = 0
service_instance_id = cp_3efb2ef516884f0aa1e857318bcb9735
schema_version = 24
declared_source_revision = 02e2a6b5dfa8d138be403b64617c2a3e6f3489aa
package_source_sha256 = expected sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2
```

`/healthz` trả HTTP `200`, `ok=true`, `sqlite_integrity=ok`; đây là bằng chứng package/service identity hiện hành đã được nạp. `control-plane-healthcheck.sh` vẫn fail-closed đúng thiết kế với `control-plane automatic backup is stale or not restorable` vì inspection backup ghi `unquarantined_unresolved_action_count=1`, không phải vì SQLite hay package hỏng.

Action còn mở vẫn là `act_0f0a49c6424d42d3bc7bc49ad46e4ffa`: node `3c7378b3-ecc4-4466-9a87-25d4d53ffdcf`/`DaoChienThang` stale, `policy_state=unavailable`, `delivery_state=dispatch_unconfirmed`, có một attempt nhưng không có receipt hoặc reconciliation. Không tự ghi receipt, không đổi thành completed/cancelled, không retry và không mở admission. Current server revision đã cập nhật; blocker còn lại là node-side evidence/operator decision cho action cũ, strict Windows runtime/discovery và natural-work outcome.

**Operator checkpoint:** yêu cầu “push lên để server cập nhật” hiện đã có bằng chứng mạnh hơn Git push: Ubuntu đang chạy đúng revision `02e2a6b5` từ release sạch và package fingerprint được đối chiếu độc lập. Không thực hiện deploy/restart thêm trong wave này; bước tiếp theo phải là thu thập evidence đúng node cũ hoặc giữ `recovery` theo runbook, không làm xanh healthcheck bằng cách sửa ledger trực tiếp.

### 16.37. Remote readback sau push `a2eb0eb4`: package Ubuntu còn lag Git hiện hành — 22/09/2026 khoảng 21:46 +07

Đã kiểm tra lại bằng một GET read-only tới `https://svhome.tail0e4032.ts.net/healthz`; không gửi credential, không gọi mutation, không thay đổi node hoặc admission.

```text
HTTP = 200
service = coding-tools-control-plane
service_instance_id = cp_3efb2ef516884f0aa1e857318bcb9735
schema_version = 24
package_source_sha256 = sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2
expected_package_source_sha256 = sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2
declared_source_revision = 02e2a6b5dfa8d138be403b64617c2a3e6f3489aa
admission_mode = recovery
unresolved_action_count = 11
unquarantined_unresolved_action_count = 1
```

Readback này xác nhận section 16.36 có remote service/package identity thực, nhưng **không xác nhận Ubuntu đã chạy commit mới `a2eb0eb44376294e5c327f43c07e40d923ddedd6`**. Hiện trạng phải ghi là:

- Git `main`, `origin/main` và GitHub `refs/heads/main` đã ở `a2eb0eb4`.
- Ubuntu control plane vẫn nạp release từ `02e2a6b5`, tức chậm hơn một commit docs/delivery.
- `admission_mode=recovery`; không mở execution chỉ vì `/healthz=200`.
- Một action `dispatch_unconfirmed` vẫn chưa có receipt/reconciliation; không mark completed, cancelled hoặc replay.
- Windows vẫn còn `tunnelRunning=false`, `fullyReady=false`, `UPDATE_INCOMPLETE`, `CHANGED_NEEDS_DISCOVERY`; vì vậy remote package readback không thay thế strict Windows client discovery.

**Operator checkpoint:** đã thêm bằng chứng endpoint hiện tại và sửa cách diễn đạt package/server thành “đã xác minh release 02e2” thay vì “đã nạp HEAD hiện hành”. Không triển khai/restart Ubuntu từ wave này, không tạo worktree, không sửa ledger và không đóng Problem. Exact next action là chỉ deploy package `a2eb0eb4` nếu có deployment authority riêng; sau đó phải đọc lại exact service/package identity và giữ admission `recovery` cho tới khi unresolved action, Windows strict discovery và natural outcome được xử lý.

### 16.38. Git-export provenance: package code khớp fingerprint, revision metadata trên Ubuntu còn cũ — 22/09/2026 khoảng 21:52 +07

Để tách ảnh hưởng line-ending của Windows checkout khỏi provenance package, đã tạo một source export tạm bằng `git archive HEAD` ngoài repository và chạy release builder ở chế độ artifact-only. Đây không phải Git worktree, không ghi vào checkout, không đọc credential/SQLite và không deploy.

```text
source HEAD = 541c4c314c572b95896352b2b9a9a3c2679a5db7
package_source_sha256 = sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2
archive_sha256 = 3e7655099a3bbcb7a404347c500e3b52c346e343148d333116888231906496f6
schema = 24
```

Kết quả đối chiếu:

- Fingerprint package từ Git-export `HEAD` **trùng chính xác** fingerprint `/healthz` của Ubuntu và artifact release `02e2` (`8fc57c65...`).
- `git diff 02e2a6b5...HEAD -- control-plane deploy` không có file thay đổi; các commit sau `02e2` chỉ cập nhật docs/delivery snapshot. Vì vậy package code đang chạy có thể được coi là cùng package-source fingerprint với source hiện hành, dù server khai báo revision cũ.
- Build trực tiếp từ Windows working tree cho fingerprint `3e13c165...` vì `control-plane/control_plane/node_agent.py` đang có line-ending mixed/CRLF; đây là lý do không dùng fingerprint đó để đối chiếu release. Git-export là phép build canonical đáng tin cậy hơn cho release provenance.
- Archive `02e2` đã kiểm tra có payload CRLF ở checkout Windows; nhãn “LF sạch” trong section 16.36 là không chính xác về byte line-ending và đã được điều chỉnh bằng finding này. Không dùng nhãn đó làm proof riêng.

Ranh giới còn lại không đổi: remote service vẫn `declared_source_revision=02e2a6b5...`, `admission_mode=recovery`, `unquarantined_unresolved_action_count=1`; package fingerprint khớp không tự nâng service thành current-HEAD deployment, không mở admission, không chứng minh Windows connector/discovery hoặc natural outcome.

**Operator checkpoint:** package code provenance đã được thu hẹp từ “chưa xác minh” thành **fingerprint khớp Git-export HEAD**, còn release identity vẫn lệch revision metadata. Không deploy/restart/reconcile thêm trong wave này. Exact next action nếu có deployment authority là build/install release canonical từ Git-export của HEAD hiện tại, đọc lại cả `declared_source_revision` và fingerprint, rồi vẫn giữ `recovery` cho đến khi action unresolved và các gate Windows/natural-use được xử lý.

### 16.39a. Đã bổ sung disposition fail-closed cho dispatch cũ không có receipt — 22/09/2026

Source hiện nâng schema control-plane lên `25` và thêm `action_dispatch_dispositions` riêng cho đúng blocker còn lại: action `workspace_context` đã hết hạn, `dispatch_unconfirmed`, có đúng một attempt, không có receipt, trong khi node stale/unavailable hoặc thiếu runtime/policy observation hợp lệ. Operator route mới là:

```text
POST /v1/action-dispositions/quarantine-historical-unobserved-dispatch
POST /v1/ui/action-dispositions/quarantine-historical-unobserved-dispatch
```

Route yêu cầu declaration chính xác `HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH` và rationale bounded. Transaction kiểm tra owner/device/action/attempt/expiry/zero-receipt/node state, ghi evidence digest + audit event, nhưng **không** tạo receipt, không đổi `actions.delivery_state`, không retry/cancel/replay và không mở admission. Health/backup inspection có thể coi disposition là một unresolved item đã được operator cách ly để healthcheck không còn đếm là `unquarantined`, song action vẫn giữ `dispatch_unconfirmed` và không phải completed, local read, acceptance hay natural outcome.

Focused proof: store + HTTP/UI tests cho route/auth/no-receipt và các điều kiện expiry/dispatchability đều pass; các boundary suite deployment/permission đạt `14 passed`. Lần chạy có thêm `test_mcp_oauth.py` có `5` failure fixture trên Windows (POSIX owner-private mode và symlink privilege), không phải failure của disposition mới. Chưa invoke route trên Ubuntu, chưa deploy schema 25, chưa mở admission và chưa có strict Windows discovery/natural-work outcome.

**Operator checkpoint:** blocker nay có một đường xử lý được audit mà không cần giả receipt. Exact next action sau source commit là chỉ khi có maintenance authority mới build Git-export canonical, backup/migrate/restart Ubuntu lên schema 25, đọc lại service/package identity và invoke route với exact action/device/rationale. Giữ `recovery` cho tới khi owner chấp nhận reconciliation packet; không tuyên bố hoàn tất từ health `200` hoặc disposition.

### 16.39. Hardening release builder và đính chính fingerprint canonical — 22/09/2026 khoảng 22:00 +07

Đã sửa release builder để clean build (`require_clean_source=true`) đọc trực tiếp bytes của `git show HEAD:<path>` thay vì bytes đã qua Windows checkout/EOL conversion; package fingerprint được tính lại trên đúng staging bytes sẽ đưa vào archive. Đây là source fix nhằm loại bỏ sai lệch reproducibility, không phải deploy.

Thay đổi và proof:

- [build-control-plane-release.py](../../scripts/build-control-plane-release.py) dùng canonical Git blob cho `control-plane/` và `deploy/` trong clean build; `require_clean_source=false` vẫn giữ hành vi fixture/test cũ.
- [test_release_artifact.py](../../control-plane/tests/test_release_artifact.py) thêm regression chứng minh `node_agent.py` trong clean artifact khớp chính xác `git show HEAD`, và receipt fingerprint khớp staging package.
- Release artifact canonical từ `HEAD=b4698a611280d2ce9c2840cd2bf3f06bf8fdd288`:

```text
package_source_sha256 = sha256:77d6441e3e4f79da238d017683974da26dd18caee61ca8e20ba74f60ac09e0af
archive_sha256 = 74d5516b7ce337da36ba5263d177ec57b09e837c0d1989c431fbf2805eca8f71
package Python files checked = 10
byte mismatches against git show HEAD = 0
```

- `control-plane.tests.test_release_artifact`: **4 tests PASS, 1 POSIX-launcher test skipped trên Windows**.
- `py_compile` của builder/test và `git diff --check`: PASS.
- Remote `/healthz` hiện vẫn báo package `8fc57c65...` và revision `02e2a6b5...`; vì vậy remote không phải exact canonical Git-blob artifact `77d6441e...` của HEAD hiện hành.
- Section 16.38 ghi fingerprint `8fc` từ một `git archive` export trên Windows; phép export đó giữ CRLF, nên không phải canonical Git-blob proof. Section 16.39 này là correction có authority cao hơn vì kiểm trực tiếp `git show` và staging output.

**Operator checkpoint:** đã loại bỏ một nguồn fingerprint churn có thể làm package/revision continuity sai lệch giữa Windows và Ubuntu. Chưa deploy/restart, chưa đổi admission và chưa mở canary. Exact next action nếu được cấp deployment authority là dùng builder canonical này để tạo release từ HEAD, verify manifest, deploy package đã chọn và đọc lại `/healthz`; nếu chưa có authority, giữ remote `recovery` và các Problem OPEN.

### 16.40. Recovery ledger đã nối lại canonical lineage; kiểm tra live mới nhất — 22/09/2026 lúc 22:16 +07

Wave này tiếp tục theo đúng quyền recovery có kiểm soát đã được cấp cho
`.coding-tools/orchestration/ledger.sqlite3`. Không mở một writer mới, không sửa
SQLite bằng câu lệnh thủ công, không replay effect và không thay đổi admission.
Các truy vấn canonical được mở `mode=ro`; kết quả dưới đây là snapshot mới, không
dùng lại số liệu của các report cũ.

**Canonical ledger sau recovery:**

```text
physical file SHA-256 = 07d76b2fd37e3872f278b4835ea29b49cb39b751642df0f247fcb4113f837663
PRAGMA user_version   = 12
PRAGMA integrity_check = ok
foreign_key_check      = 0
runs                   = 557
waves                  = 892
checkpoints            = 273
proofs                 = 947
events                 = 25,822
problem_events         = 307
continuity_telemetry   = 396
controller_knowledge_acks = 68
```

Ba RUN từng có report/receipt nhưng vắng trong snapshot canonical trước đó đã
được nối lại với đầy đủ identity và checkpoint:

| RUN | trạng thái | checkpoint | Problem binding |
|---|---|---|---|
| `dcb539e0e1694bc1bb29eed2b2e07f8b` | `accepted` | `8d10f27638e2498cba80edf0bcbe77ce` | `prl-22e…` rev1 |
| `d01a5dce50c846fc8e13673cdfc8b3b3` | `accepted` | `6fb3de41a26349f5995a6a2bd92d82f2` | `prl-22e…` rev1 |
| `b194ab1e311e42efa1dd0614ca245037` | `accepted` | `c8f32a66c7714204bcdd64162dc20ee1` | `prl-22e…` rev1 |

Denominator hiện tại đã đối chiếu lại theo `ENGINEERING_ATTEMPT_BOUND` và bảng
`runs`, không tính các event có `run_id=''`:

| Problem/revision | accepted | aborted | active | tổng RUN hợp lệ | coverage manifest | outcome claim | resolution |
|---|---:|---:|---:|---:|---:|---:|---:|
| `prl-22e670302757c9b7663170e226ed7c26` / 1 | 47 | 16 | 3 | 66 | 0 | 0 | 0 |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / 2 | 16 | 10 | 13 | 39 | 0 | 0 | 0 |

`active` ở đây là trạng thái durable chưa terminal; lifecycle census không có
live-owned RUN hay resource residue tương ứng. Vì vậy recovery đã sửa tính liên
tục của evidence, nhưng **không** làm Problem nào thành `CLOSED`, không tạo
criterion PASS và không tạo natural outcome.

**Live Windows readback (authenticated Recovery IPC, read-only):**

Observation lúc `2026-09-22T15:16:21.185Z` (`22:16:21 +07`) khớp workspace
`E:\\DEV\\Codex-web`, Recovery Host PID `42556`, instance
`3d2a072b655e55995ff15ad2db94dda`, packaged revision
`baf32237ab3bbf38ca80f3b696575c5922f6a73ac60c0353e90630ea651749ce`:

```text
mcpRunning=false
nativeAlive=false
tunnelRunning=false
componentsReady=false
fullyReady=false
updateIncomplete=true
centralConnected=true
authorityReady=true
connectorContractState=UNAVAILABLE
connectorRediscovered=false
connectorRefreshRequired=false
live_accepted=false
authority_granted=false
```

Supervisor process `47772` vẫn báo `healthy`, packaged Recovery Host `42556` còn
sống và Recovery MCP `38200` còn sống; nhưng đó chỉ chứng minh recovery plane
resident. Nó không chứng minh primary MCP/Tunnel hay client connector usable.
`node scripts/dev-ui-lifecycle.js status` vẫn trả
`state=MISSING`, `installation=mismatch`, `connector_state=UNAVAILABLE`.
Envelope activation đang ghi `state=READY/admission_state=OPEN`, trong khi live
runtime readback ghi `UPDATE_INCOMPLETE` và mọi primary component là `false`;
theo fail-closed phải dùng nhánh runtime thực tế chặt hơn, không dùng outer
envelope để gọi `fullyReady`.

**Ubuntu readback cùng thời kỳ:**

```text
HTTP /healthz = 200
declared_source_revision = 02e2a6b5dfa8d138be403b64617c2a3e6f3489aa
package_source_sha256 = sha256:8fc57c65d1218444a3ff4661b3cc6c16186ed352e3ec72a74f6665f2be2ab6d2
admission_mode = recovery
unresolved_action_count = 11
unquarantined_unresolved_action_count = 1
```

Remote service đang sống, nhưng chưa exact-current với `main@cbe7de18` và
`/healthz=200` không phải execution/admission proof. Không deploy, restart,
reconcile action hoặc mở admission trong wave này.

**Source proof bổ sung:**

- `python -m pytest -q control-plane/tests/test_store.py control-plane/tests/test_http_api.py`
  đạt `129 passed, 50 subtests passed` trên source hiện tại.
- Selector focused cho disposition mới (`-k 'unobserved_dispatch or
  historical_unobserved or no_receipt'`) đạt `3 passed, 129 deselected`.
- Đây là proof source/store/HTTP của predicate và route mới trên fixture test; nó
  chưa phải migration proof trên database Ubuntu schema 24, chưa phải operator
  invocation, deployment/restart, strict Windows discovery hay natural outcome.
- `control-plane/control_plane/store.py` và `http_api.py` vẫn là dirty concurrent
  source lane. Chưa stage, commit hoặc nhận ownership thay lane đó; cần bổ sung
  migration review và package identity readback trước khi release schema 25.

**Operator checkpoint:**

- **Đã hoàn thành:** controlled ledger recovery; canonical lineage của ba RUN đã
  được kiểm tra lại; live Windows/remote readback mới đã được ghi; focused store
  và HTTP suite đã xanh.
- **Trạng thái:** Git `main@cbe7de18`; `.coding-tools` live ledger dirty do
  evidence runtime; source `store.py`/`http_api.py` dirty concurrent; hai Problem
  vẫn `OPEN`.
- **Blocker:** primary MCP/Tunnel/connector chưa usable; remote package metadata
  còn lag; action `dispatch_unconfirmed` chưa có receipt/reconciliation; schema-25
  chưa có focused acceptance; natural outcome và criterion coverage vẫn thiếu.
- **Exact next action:** quiesce/snapshot bằng `npm run stage:coding-tools-delivery`,
  chạy delivery/history guards, commit trực tiếp trên `main` chỉ phần report và
  evidence được sở hữu; sau đó review/test lane schema-25. Chỉ khi có deployment
  authority mới build/deploy canonical package, đọc lại revision + fingerprint,
  giữ `admission=recovery` cho tới khi unresolved action được xử lý bằng evidence
  thật. Tiếp theo mới tạo activation epoch mới để chứng minh strict discovery,
  real `workspace_context`, fault/reattach, reboot/logon và natural-use.

### 16.41. Tách validation schema-25 khỏi lỗi fixture OAuth phụ thuộc POSIX — 22/09/2026 sau 22:20 +07

Đã chạy thêm boundary validation cho các module chịu ảnh hưởng schema/version:

```text
test_deployment_verifier.py + test_mcp_permission_requests.py
14 passed in 17.35s

test_store.py + test_http_api.py
129 passed, 50 subtests passed

focused historical-dispatch selector
3 passed, 129 deselected
```

Lần chạy gộp `test_deployment_verifier.py + test_mcp_permission_requests.py +
test_mcp_oauth.py` có `40 passed, 5 failed, 35 subtests passed`. Cả 5 failure
đều nằm trong `test_mcp_oauth.py`, tại fixture kiểm tra file credential
owner-private và symlink. Trên Windows hiện tại, `chmod(0o600)` không tạo mode
POSIX tương ứng nên file bị từ chối như thiết kế; việc tạo symlink cũng trả
`WinError 1314` vì process không có privilege symlink. Không có failure nào ở
store, HTTP disposition, deployment verifier hay permission-request migration.

Phân loại đúng là **test-environment portability gap**, không phải lý do để nới
policy credential hoặc bỏ kiểm tra symlink. Cần chạy OAuth suite trên POSIX/CI
được cấp symlink privilege (hoặc bổ sung fixture Windows riêng ở một change lane
được sở hữu) trước khi gọi toàn bộ control-plane suite xanh.

**Checkpoint bổ sung:** source lane schema-25 hiện có focused implementation,
UI/runbook và tests xanh trong working tree, nhưng vẫn chưa được nhận ownership
để commit; remote Ubuntu chưa được migrate/deploy schema 25. Vì vậy trạng thái
strongest vẫn là `SOURCE_PRESENT + FOCUSED_PROOF`, chưa phải
`PACKAGED_RELEASED`, `LIVE_ACCEPTED` hay natural outcome.

### 16.42. Sửa boundary two-phase activation để không mở READY từ runtime hỏng — 22/09/2026

Wave này xử lý lỗi do invariant mới đặt nhầm ở tầng `ActivationEpochStore`:
`commitReady()` được gọi khi activation còn `READY_COMMITTED/admission=CLOSED`,
nhưng `componentsReady` và `fullyReady` của central executor có thể vẫn là
`false` vì hai cờ này bao gồm chính admission bit. Nếu bắt buộc chúng `true` ở
`commitReady()`, store tạo circular dependency và từ chối một central route đã
được xác thực trước khi có cơ hội chạy `revalidateBeforeAdmission()`.

Đã sửa [electron/services/activationEpoch.js](../../electron/services/activationEpoch.js)
theo nguyên tắc hai pha:

- `validateReadyVerification()` vẫn fail-closed nếu runtime snapshot **ghi rõ**
  `mcpRunning=false`, `nativeAlive=false`, `tunnelRunning=false` ở direct mode,
  hoặc `updateIncomplete=true` (hỗ trợ cả tên snake_case tương ứng).
- Không bắt buộc `componentsReady`/`fullyReady` tại `READY_COMMITTED`, vì chúng
  có thể phụ thuộc admission; producer `fullCleanActivation.finalCensus()` và
  `revalidateBeforeAdmission()` vẫn là nơi quyết định `pass=true` và mở admission.
- Central execution không bị buộc có local Tunnel; direct legacy vẫn bị chặn
  nếu census hiện rõ Tunnel đã tắt.

Đã thêm regression trong
[tests/activation-epoch.test.js](../../tests/activation-epoch.test.js):

1. primary runtime `mcpRunning=false/nativeAlive=false/updateIncomplete=true`
   bị từ chối và epoch vẫn `VERIFYING/CLOSED`;
2. central `READY_COMMITTED` với `mcpRunning=true/nativeAlive=true`, route/policy
   hợp lệ nhưng `componentsReady=false/fullyReady=false` vẫn được commit an toàn
   ở trạng thái `CLOSED`, để bước revalidation độc lập xử lý admission sau đó.

**Focused proof:**

```text
node --test tests/activation-epoch.test.js tests/full-clean-activation.test.js tests/recovery-host.test.js
129 passed, 0 failed
duration_ms = 34,371.8122
```

Bộ proof bao phủ store two-phase commit, central route/policy, direct connector,
full-clean census, pre-admission identity revalidation, Recovery Host adoption,
handoff và các guard `UPDATE_INCOMPLETE`. Đây là source/focused proof; chưa phải
runtime activation proof. Không restart/reboot, không deploy Ubuntu, không gọi
route quarantine và không mở admission trong wave này.

**Operator checkpoint:** invariant đã được đặt đúng boundary: runtime hỏng không
thể trở thành READY proof, nhưng central pre-admission không còn bị circular
dependency. Git vẫn làm trực tiếp trên `main`; cần chạy diff/syntax và toàn bộ
delivery/history/secret guards trước commit. Exact next action là snapshot
`.coding-tools`, commit/push source + research lên `origin/main`, sau đó recapture
Windows/Ubuntu readback; nếu runtime vẫn `UPDATE_INCOMPLETE`, tiếp tục giữ
`admission=recovery` và không tuyên bố Problem nào đã đóng.

### 16.43. Checkpoint sau commit/push và recapture runtime — 22/09/2026 lúc 22:49 +07

Patch two-phase đã được giao trực tiếp trên `main`, không tạo worktree:

```text
506c415a fix: preserve two-phase activation readiness boundary
9ed732a9 chore: refresh coding-tools delivery receipt
HEAD = origin/main = 9ed732a9ed7b0a471d6e4f2b1a9f7cc42278de5a
git rev-list --left-right --count HEAD...origin/main = 0 0
```

Delivery/history/secret guards đã chạy lại trước push; snapshot receipt lúc đó
bind ledger blob `e574c83cfa1f24eb377e576199e38aac05f77127`, schema 12,
`integrity_check=ok`, FK violations `0`. Sau push, ledger live tiếp tục có
runtime evidence mới nên phải tạo snapshot mới cho delivery attempt kế tiếp;
không reset hoặc bỏ dirty `ledger.sqlite3`.

**Windows authenticated Recovery IPC, read-only observation:**

```text
collected_at_ms = 1790092088273 (2026-09-22T15:48:08Z)
Recovery Host PID = 42556
host instance = 3d2a072b655e55995ff15ad2db94dda3
runtime_mode = packaged
Recovery Host running_revision = disk_revision = baf32237ab3bbf38ca80f3b696575c5922f6a73ac60c0353e90630ea651749ce
Coding MCP running_revision = null
Coding MCP disk_revision = 57531dd62073778b223bed695728221b0f1fa522bb6d7c40d56f3a955802c747
mcpRunning/nativeAlive/tunnelRunning/componentsReady/fullyReady = false/false/false/false/false
updateIncomplete = true
centralConnected/authorityReady = true/true
connectorContractState = UNAVAILABLE
connectorRediscovered = false
identity_current = false
workspace_context client read = absent
activation envelope = READY, admission_open=true
```

Observation status là `STALE_OR_INCOMPLETE`, `authority_granted=false`,
`live_accepted=false`; nó xác nhận đúng mâu thuẫn cần fail-closed (outer
envelope xanh nhưng primary runtime chết), không phải reboot receipt, strict
connector discovery hay natural outcome. Source fix mới chỉ tác động các epoch
được commit/revalidate sau này; không tự động rewrite epoch/runtime đang chạy.

**Ubuntu `/healthz`, GET read-only sau push:**

```text
HTTP = 200
schema_version = 25
admission_mode = recovery
declared_source_revision = be16a0b1bb6536643c4894e37c9adaffd76bc905
package_source_sha256 = sha256:4cbb2b37b4c2ce84ba8aaaa5564ebed83b376dd2d8e5d7af62c98adc3ea6a18c
expected_package_source_sha256 = same as package_source_sha256
unresolved_action_count = 11
quarantined_unknown_action_count = 10
quarantined_unresolved_action_count = 10
unquarantined_unresolved_action_count = 1
action_dispatch_dispositions = 0
```

Remote package/revision chưa theo `main@9ed732a9`; fingerprint equality giữa
package và expected chỉ là process self-consistency, không phải current-HEAD
deployment proof. Không SSH, không deploy/restart/reboot, không invoke
quarantine route và không mở admission.

**Canonical lifecycle census mới, Backup API/query-only:**

```text
snapshot_at = 2026-09-22T15:48:54.554Z
backup_api_snapshot_sha256 = b65bf7e066b2929987f43fa2feefae14090dfbdb63c06741c2f8d372792e5b1e
logical_sha256 = 988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d
size_bytes = 97742848
schema_version = 12
integrity_check = ok
foreign_key_check_rows = 0
ordinary_active_runs = 17 (all THRESHOLD_SENSITIVE_STALE_CANDIDATE)
stale_background_operation_residues = 0
unbound_live_resource_residues = 0
```

Đếm exact revision từ connection `mode=ro` vẫn là:

| Problem/revision | accepted | aborted | active | tổng RUN hợp lệ |
|---|---:|---:|---:|---:|
| `prl-22e670302757c9b7663170e226ed7c26` / 1 | 47 | 16 | 3 | 66 |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / 2 | 16 | 10 | 13 | 39 |

Coverage manifest, outcome claim và resolution của hai revision vẫn `0`; không
được lấy accepted RUN, outer READY, package health hay `/healthz=200` làm
criterion/natural outcome. `report_lifecycle_census.py` xác nhận
`mutated_canonical_ledger=false`, projection `CONTEXTUAL_PROJECTIONS`, không có
live-owned RUN/resource residue.

**Operator checkpoint:** source/focused repair đã lên `origin/main`; ledger và
runtime evidence vẫn được giữ nguyên để điều tra. Các Problem vẫn `OPEN`,
Windows primary MCP/Tunnel/strict discovery/workspace read chưa đạt, Ubuntu còn
recovery + một unresolved action và remote chưa theo HEAD. Exact next action là
stage một snapshot mới của ledger hiện tại cùng receipt, kiểm tra lại guards và
chỉ commit/push nếu muốn bảo toàn snapshot evidence; sau đó cần activation epoch
mới có source/package/epoch đồng nhất trước mọi reboot/admission test.

### 16.44. Xác nhận P1/P2 handoff đã có trên main và proof hồi quy — 22/09/2026

Đã đối chiếu lại source thay vì tạo patch trùng. Hai gap handoff từng nêu trong
đánh giá trước đã có implementation trên ancestor `e6626062` của `main`:

- `electron/services/recoveryBootstrap.js` gọi `observeHandoffRuntime()` trước
  `stop`, coi `recoveryResponseReceived=true` là semantic refusal và **không**
  chuyển nó thành quyền terminate/spawn; transport loss chỉ được tiếp tục khi
  một snapshot exact workspace chứng minh runtime đã stopped.
- Rollback chỉ gọi `client.start()` nếu snapshot trước stop chứng minh runtime
  thật sự `running`, có epoch/workspace/role rõ; `off`, `unknown`, partial,
  manual-stop, recovering hoặc epoch drift đều không được tự bật service. Snapshot
  sau stop phải khớp role/epoch/workspace trước khi compensation chạy.

Focused proof mới:

```text
node --test tests/recovery-bootstrap.test.js
41 passed, 0 failed
```

Các regression trực tiếp đã xanh: semantic refusal cho
`RECOVERY_REQUEST_FAILED/RUNTIME_BUSY/AUTHORITY_DENIED/ECONNRESET`, transport loss
không terminate runtime chưa xác nhận, rollback giữ nguyên off/unknown/partial/
manual-stop và central rollback không bật direct Tunnel. Vì vậy P1/P2 là
`SOURCE_PRESENT + FOCUSED_PROOF` trên `main`, không còn là source gap cần sửa
thêm trong wave này; chúng vẫn chưa có live packaged handoff/reboot proof.

**Operator checkpoint:** không thêm writer/store hay thay đổi runtime. Exact next
action chuyển sang activation packet mới: freeze package/source/epoch đồng nhất,
revalidate primary MCP/Tunnel/connector/workspace trước admission, rồi mới chạy
reboot matrix. Giữ các gate Machine B, 48-hour natural-use, independent outcome
và Problem closure ở `NOT_RUN/OPEN` cho tới khi có receipt thật.

### 16.45. Oracle reboot hiện hành đã đủ chặt; receipt cũ vẫn không đạt — 22/09/2026

Để phân biệt “oracle source đã sửa” với “artifact acceptance đã có”, đã chạy lại
`scripts/verify-boot-acceptance.js` qua bộ fixture hiện hành:

```text
node --test tests/boot-acceptance.test.js
43 passed, 0 failed
```

Oracle hiện tại không còn chỉ kiểm PID/hash/Supervisor. Nó bắt buộc schema-v2,
Problem/revision/criteria fingerprint, boot sequence trước/sau, packaged host mới
với process-start token, Supervisor healthy + startup intent enabled, exact
Recovery Host/Coding MCP revisions, activation `READY/admission_open`,
`updateIncomplete=false`, `mcpRunning/nativeAlive/componentsReady/fullyReady=true`,
client binding cùng epoch/process/contract, một `workspace_context` thật với
`completed=true/workspace_accessed=true`, và role-specific central route hoặc
direct Tunnel + connector freshness. Các negative fixture (`mcpDead`, `tunnelDead`,
source drift, old epoch, closed admission, no reboot, no client read, manual
repair...) đều fail-closed.

Vì vậy nhận định đúng ở thời điểm này là: **source oracle đã đạt
`FOCUSED_PROOF`**, còn file pre-reboot lịch sử chỉ chứa Supervisor/packaged-host
evidence và không thể vượt oracle hiện hành; chưa có post-reboot receipt đủ trường,
strict discovery, workspace read hoặc natural outcome. Không nới oracle để làm
receipt cũ xanh.

**Operator checkpoint:** giữ nguyên oracle và acceptance policy. Exact next action
là tạo receipt v2 mới từ một activation/reboot được phép, bind đúng package/epoch/
client và chạy oracle này; nếu thiếu một trường thì kết quả phải là `NOT_PROVEN`,
không thay bằng `/healthz`, PID hoặc accepted RUN.

### 16.46. Deployment Ubuntu schema-25 và quarantine action lịch sử — 22/09/2026 sau 22:45 +07

Wave này đã thực hiện bằng SSH target-bound tới `svhome@100.116.112.22`, giữ
admission đóng ở `recovery`. Control-plane package đã được build/verify từ
commit `be16a0b1bb6536643c4894e37c9adaffd76bc905`; các commit sau đó trên
`main` chỉ thay đổi Electron/docs/delivery evidence, không thay đổi bytes dưới
`control-plane/` hoặc `deploy/`. Artifact receipt:

```text
control_plane_schema_version = 25
package_source_sha256 = sha256:4cbb2b37b4c2ce84ba8aaaa5564ebed83b376dd2d8e5d7af62c98adc3ea6a18c
archive_sha256 = 2d7af7229d14dcba39e712cda039946a2d5a6dd348d325048bda42526e46ee74
release_file_count = 34
```

Trước migration đã tạo verified SQLite snapshot bằng Backup API, không copy
file đang chạy:

```text
pre_migration_snapshot_sha256 = fc8bd08aed13532660787555299ef07df926a8de7bb491f191a94cc558aa7f59
pre_migration_schema = 24
pre_migration_integrity = ok
pre_migration_admission = recovery
```

Sau khi bind revision/fingerprint vào protected env + systemd drop-in, đổi
`current` bằng symlink atomic, `daemon-reload` và restart đúng user unit một
lần. Readback exact sau restart:

```text
service = active + enabled
current = codex-control-plane-be16a0b1bb6536643c4894e37c9adaffd76bc905
service_instance_id = cp_d8f080f6d0eb44409ce1e5015c9c58a7
main_pid_at_readback = 1002684
schema_version = 25
sqlite_integrity = ok
declared_source_revision = be16a0b1bb6536643c4894e37c9adaffd76bc905
package_source_sha256 = sha256:4cbb2b37b4c2ce84ba8aaaa5564ebed83b376dd2d8e5d7af62c98adc3ea6a18c
expected_package_source_sha256 = same
admission_mode = recovery
```

Deployment verifier và healthcheck remote đều PASS. Sau khi đối chiếu exact
action `act_0f0a49c6424d42d3bc7bc49ad46e4ffa` / device
`3c7378b3-ecc4-4466-9a87-25d4d53ffdcf`, operator đã ghi disposition
`HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH` với bounded rationale. Action vẫn
giữ nguyên `dispatch_unconfirmed`, đúng một attempt, **0 receipts**, không có
reconciliation/completed/cancelled giả và không retry. Health sau đó:

```text
unresolved_action_count = 11
quarantined_unknown_action_count = 10
historical_unobserved_dispatch_count = 1
quarantined_unresolved_action_count = 11
unquarantined_unresolved_action_count = 0
```

Một automatic backup + healthcheck mới cũng PASS, snapshot hash
`8b30b03cbf5aef3744d616d99ad716616e012d583a9fbb2d84a78a628ae1e6ef`, nhưng
đây chỉ là bằng chứng integrity/package/recovery-state. Không mở admission,
không approve enrollment, không cấp workspace/policy/binding, không chạy
Windows canary, strict client discovery hay natural-work outcome. Các gate
Windows primary MCP/Tunnel/connector và Problem closure vẫn `OPEN/NOT_RUN`.

**Operator checkpoint:** Ubuntu đã chạy đúng backend schema 25 của source
đã push, database migration có backup và identity readback đầy đủ; action cũ
được quarantine minh bạch chứ chưa được coi là đã thực thi. Exact next action
là hoàn thiện packaged Windows activation/strict discovery theo owner-authorized
packet; chỉ sau node-side proof và independent outcome mới cân nhắc mở admission.

**Provenance note:** commit `0e562f0b` của concurrent delivery wave xuất hiện
trên `main` trong lúc controller này đang chạy source/oracle work; controller này
không tự gọi SSH/deploy/quarantine trong wave đó. Các trạng thái remote ở trên đã
được kiểm tra độc lập bằng GET `/healthz` read-only sau khi commit xuất hiện;
không coi mệnh đề “đã deploy” là bằng chứng Windows runtime hoặc Problem closure.

### 16.47. Projection admission fail-closed khi durable READY đã lỗi thời — 22/09/2026

Wave này sửa đúng lớp read-model đang cho phép một snapshot biểu diễn đồng thời
`activation=READY/admission_open=true` và runtime hiện tại
`mcpRunning=false/nativeAlive=false/tunnelRunning=false/fullyReady=false`.
Trong `RecoveryHost.decorate()`, khi aggregate runtime readiness không đạt hoặc
`UPDATE_INCOMPLETE` đang hiện hữu, projection mới:

- giữ nguyên durable `READY` trong activation-epoch store để bảo toàn lịch sử,
  không sửa tay và không rewrite SQLite;
- đóng `admission_open` ở snapshot hiệu dụng và đặt
  `update_incomplete=true/error_code=RUNTIME_READINESS_INCOMPLETE` nếu trước đó
  envelope đang mở;
- chiếu cùng một giá trị fail-closed vào top-level `activationEpoch`,
  `status.activationEpoch` và `recoveryHost.activation_epoch`, để caller không
  lấy một nhánh xanh cũ làm authority grant;
- không tự restart, không tạo activation epoch mới và không biến projection thành
  bằng chứng đã phục hồi MCP/Tunnel.

Regression proof:

```text
node --test tests/recovery-host.test.js
44 passed, 0 failed

node --test tests/activation-epoch.test.js tests/full-clean-activation.test.js tests/recovery-host.test.js tests/boot-runtime-observation.test.js
138 passed, 0 failed

node --check electron/services/recoveryHost.js
node --check tests/recovery-host.test.js
git diff --check
```

Trong lần chạy đầu, patch đã lộ một lỗi integration do dùng shorthand
`projectedRecoveryHost`, làm mất key contract `recoveryHost` và khiến 4 test cũ
fail. Key đã được khôi phục thành `recoveryHost: projectedRecoveryHost`; lần
chạy lại toàn bộ suite đạt `44/44` và boundary đạt `138/138`. Đây là lỗi của
patch trong cùng wave, đã được sửa và không phải bằng chứng runtime Windows.

Ý nghĩa acceptance cần giữ tách lớp:

| Lớp | Trạng thái hiện tại |
|---|---|
| Durable epoch history | Có thể vẫn đọc `READY/OPEN` như lịch sử immutable |
| Effective IPC admission projection | Đã đóng khi runtime hiện tại incomplete |
| Packaged primary MCP/Tunnel | Chưa chứng minh sống lại |
| Strict connector discovery | Chưa chạy/không có receipt mới |
| Real `workspace_context` | Chưa có trong observation hiện tại |
| Reboot/logon matrix | Chưa chạy |
| Natural-use / independent Problem outcome | Chưa có |

Current branch tại lúc ghi nhận là `main@6551b34e`, đồng bộ với
`origin/main`; `.coding-tools/orchestration/ledger.sqlite3` vẫn là live evidence
dirty và không bị reset/revert. Không restart/reboot/deploy/remote route trong
wave này. Exact next action là tạo snapshot delivery mới cho ledger hiện tại,
chạy đủ delivery/history/secrets guards, rồi commit trực tiếp trên `main`; sau
đó chỉ khi có authority riêng mới thực hiện controlled activation epoch để
đồng nhất source/package/runtime trước strict discovery và reboot acceptance.

### 16.48. Recheck sau commit: ledger recovery đã idempotent, không lặp apply — 22/09/2026 lúc 23:18–23:22 +07

User đã cho phép tiếp tục recovery có kiểm soát cho
`E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3`. Quyền này đã
được thực thi ở section 16.34 bằng đúng importer evidence-only, rollback backup,
quiesce receipt và pointer CAS. Wave hiện tại chỉ recheck an toàn sau commit
`ba9875b7`; không coi candidate cũ là một lý do để nhập lại.

**Census canonical mới, read-only Backup API:**

```text
snapshot_at = 2026-09-22T16:17:57.973Z
backup_api_physical_sha256 = b65bf7e066b2929987f43fa2feefae14090dfbdb63c06741c2f8d372792e5b1e
logical_sha256 = 988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d
schema_version = 12
integrity_check = ok
foreign_key_check_rows = 0
ordinary_active_runs = 17 (all THRESHOLD_SENSITIVE_STALE_CANDIDATE)
unexplained_active_runs = 0
stale_background_operation_residues = 0
unbound_live_resource_residues = 0
mutated_canonical_ledger = false
```

Logical SHA khớp postflight của controlled recovery trước đó; physical SHA
khác do file SQLite tiếp tục là live evidence và có thể thay đổi byte-level
giữa các snapshot. Không dùng physical churn để suy ra recovery thất bại.

**Readback lineage/effect hiện tại:**

- Ba RUN historical được nối ở section 16.34 vẫn tồn tại và đều `accepted`:
  `dcb539e0e1694bc1bb29eed2b2e07f8b`, `d01a5dce50c846fc8e13673cdfc8b3b3`,
  `b194ab1e311e42efa1dd0614ca245037`.
- `prl-22e670302757c9b7663170e226ed7c26` vẫn `OPEN`, revision `1`, pointer
  seq `320`; `prl-e918c7d33e70c2d304d0797e11b05fcb` vẫn `OPEN`, revision `2`,
  pointer seq `316`. Không có resolution/outcome/criterion closure mới.
- Read-only effect census hiện tại là `background_operations` completed `1304`,
  orphaned `37`, timed_out `2`; `idempotency_records` completed `8332`, failed
  `831`, unknown `661`; `managed_process_jobs` closed `8`, exited `8426`,
  quiesced `155`, spawn_failed `2`, timeout `40`. `unknown=661` vẫn là evidence
  cần phân loại, không được gọi là replay-safe hay đã reconcile chỉ vì không
  còn row `running` tại lát cắt này.

**Negative idempotence proof:**

Đã gọi `recover_ledger_evidence.py preflight` read-only với candidate cũ của
section 16.34, exact candidate physical/logical SHA và cùng allowlist. Guard từ
chối trước mutation với:

```text
RECOVERY_CURRENT_ROWS_CHANGED:problem_threads:1
```

Điều này là kết quả đúng: candidate cũ đã được apply, còn canonical hiện tại đã
có row/pointer state khác nên không được ghép lại. Không tạo receipt apply mới,
không mở `ledger_access_gate` ghi, không copy/replace SQLite, không pointer CAS,
không replay effect và không thay đổi canonical ledger trong probe này.

**Runtime boundary sau commit (read-only):**

```text
npm run dev:status
DEV_UI state=MISSING, host=unavailable, connector_state=UNAVAILABLE,
error_code=RECOVERY_DESCRIPTOR_STALE

node scripts/collect-boot-runtime-observation.js --workspace E:/DEV/Codex-web
status=NOT_PROVEN, failure_code=RECOVERY_DESCRIPTOR_STALE

recovery:supervisor:status
task_state=Running, state=spawn_failed, consecutive_failures=82,
last_error_code=SPAWN_FAILED, last_error_message="Recovery Supervisor executable missing",
last_host_pid=42556, last_healthy_at=2026-09-22T16:11:21.6495570Z
```

Recovery plane/ledger continuity vì thế đang có bằng chứng, nhưng primary
MCP/Tunnel, development UI, strict connector discovery và reboot oracle vẫn
chưa usable. Patch `ba9875b7` chỉ làm read-model admission fail-closed khi gặp
runtime incomplete; nó không tự spawn executable thiếu, không restart host và
không tự mở admission.

**Checkpoint và quyết định:** controlled ledger recovery được giữ ở trạng thái
`APPLIED_EVIDENCE_ONLY + IDEMPOTENCE_GUARDED`; không cần và không được apply lại
candidate cũ. Hai Problem vẫn `OPEN`, natural-use/independent outcome và các
criterion coverage vẫn thiếu. Exact next action không còn là thêm một ledger
import, mà là owner-authorized runtime activation mới với source/package/epoch
đồng nhất, sau đó strict connector discovery và real `workspace_context`; mọi
reboot/admission chỉ sau khi các receipt đó có thật.

### 16.49. Xác định đúng nguyên nhân activation store và hoàn tất source repair fail-closed — 22/09/2026 lúc 23:37 +07

Wave này tiếp tục theo quyền xử lý recovery có kiểm soát nhưng **không ghi
thêm vào canonical ledger** và không khởi động lại runtime. Mục tiêu là phân
biệt lỗi cũ được hiển thị là “executable missing” với nguyên nhân hiện tại của
Recovery Host, sau đó làm cho packaged host có thể đi tới một full-clean
activation mới mà không thừa nhận READY cũ.

**Reproduction live, chỉ đọc:** executable packaged thực tế tồn tại tại
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP\Coding Tools MCP.exe`.
Đọc log/store mới cho thấy lỗi khởi động là:

```text
ACTIVATION_EPOCH_STORE_INVALID
details.code = ACTIVATION_EPOCH_READY_PROOF_REQUIRED
```

Hai snapshot persisted đều có READY proof cũ nhưng proof đó chứa
`updateIncomplete=true`, `tunnelRunning=false`, `componentsReady=false`,
`fullyReady=false`, vì vậy validator readiness hiện hành phải từ chối. Đây là
**semantic incompatibility của persisted proof sau khi guard được siết**, không
phải bằng chứng thiếu file executable và cũng không được xử lý bằng cách hạ
guard hoặc lấy `.bak` làm authority.

**Source repair đã áp dụng trên `main` (chưa được packaged runtime load):**

1. `normalizeRecord()`/`normalizeSnapshot()` có một nhánh nội bộ chỉ dùng khi
   `_read()` bắt đúng `ACTIVATION_EPOCH_READY_PROOF_REQUIRED` (kể cả mã lỗi nằm
   trong `details.code` do lớp snapshot wrap). Mọi lỗi khác vẫn fail-closed.
2. Khi primary/backup chứa READY proof stale, `_read()` chỉ tạo **projection
   trong bộ nhớ** thành `FAILED`, `admission_state=CLOSED`, xoá digest READY và
   gắn `ACTIVATION_EPOCH_STALE_READY_PROOF` cùng hành động bắt buộc
   `controlled_full_clean_activation_required`. Không rewrite primary/backup,
   không fallback sang backup và không mở authority.
3. Bổ sung đường quarantine operator-confirmed cho trường hợp snapshot thực sự
   invalid: bắt buộc `--confirm`, tùy chọn hash SHA-256 primary để chống nhầm
   target, sao lưu nguyên byte primary/backup vào file quarantine có receipt và
   chỉ thay bằng store rỗng hợp lệ với admission đóng. Đường này không được gọi
   tự động khi host khởi động. CLI được expose qua
   `npm run recovery:epoch:quarantine` và đã ghi hướng dẫn trong
   `docs/RECOVERY_HOST.md`.

**Proof đã chạy:**

```text
node --test tests/activation-epoch.test.js
26 passed, 0 failed

node --test tests/activation-epoch.test.js tests/full-clean-activation.test.js tests/recovery-host.test.js tests/boot-runtime-observation.test.js
141 passed, 0 failed

node --check electron/services/activationEpoch.js
node --check tests/activation-epoch.test.js
node --check scripts/quarantine-invalid-activation-epoch.js
git diff --check
npm run check:repository-secrets
```

Regression test mới đã sửa đúng failure mode: khi cả primary và backup bị
đánh dấu `updateIncomplete=true` rồi recompute digest, reader trả
`FAILED/CLOSED + ACTIVATION_EPOCH_STALE_READY_PROOF`, đồng thời byte của cả hai
file không đổi. Các test quarantine chứng minh thiếu `--confirm` bị từ chối,
hash mismatch không được thay target, snapshot hợp lệ không bị quarantine, và
receipt giữ nguyên evidence trước khi tạo store rỗng.

**Live readback sau source patch (không mutation):**

```text
file = C:\Users\Admin\AppData\Roaming\web-mcp-assistant\activation-epoch.json
primary_sha256_before = 1c6f31af546f44369ac785f3d41af6145ccdfc3614fa6694665fbfda16849e1c
backup_sha256_before  = cf84fa8015fad7a5df61feb39445d187e0a4335717c4195f7b48e97a5495dc7a
projection = FAILED / CLOSED / ACTIVATION_EPOCH_STALE_READY_PROOF
update_incomplete = true
primary_sha256_after  = 1c6f31af546f44369ac785f3d41af6145ccdfc3614fa6694665fbfda16849e1c
backup_sha256_after   = cf84fa8015fad7a5df61feb39445d187e0a4335717c4195f7b48e97a5495dc7a
unchanged = true
```

Đây là bằng chứng source/focused và read-only projection, chưa phải
`PACKAGED_RELEASED`, `LIVE_ACCEPTED`, strict connector discovery hay
`workspace_context` thật. Bản runtime cài đặt hiện tại chưa được restart để
nạp patch; do đó không được dùng kết quả trên để tuyên bố MCP/Tunnel đã phục
hồi.

**Checkpoint wave:** source repair và regression proof đã đạt; ledger recovery
vẫn giữ `APPLIED_EVIDENCE_ONLY + IDEMPOTENCE_GUARDED`; không có restart,
reboot, deploy, admission grant, effect replay hay ledger import mới. Hai
Problem vẫn `OPEN` và các gate natural-use/independent outcome/criterion
coverage vẫn thiếu.

**Exact next action:** tạo delivery snapshot mới cho live ledger rồi chạy
`check:coding-tools-delivery`, `check:coding-tools-history`,
`check:repository-secrets` và `--verify-index`; commit trực tiếp trên `main`
và push `origin/main`. Chỉ sau khi packaged runtime được cập nhật đúng source
identity mới cân nhắc controlled full-clean activation, strict discovery,
real `workspace_context`, reboot/logon oracle và natural-use. Không được gọi
CLI quarantine cho snapshot hiện tại nếu chưa có một receipt operator xác nhận
riêng; stale READY đang được xử lý an toàn bằng projection fail-closed.

### 16.50. Post-push runtime boundary và ledger census mới — 22/09/2026 lúc 23:44 +07

Sau khi commit `6f507fda` đã được push, controller chỉ thực hiện các lệnh
quan sát. Kết quả hiện tại:

```text
DEV_UI state=MISSING
host=unavailable
connector_state=UNAVAILABLE
error_code=RECOVERY_DESCRIPTOR_STALE

boot_runtime_observation = NOT_PROVEN
failure_code = RECOVERY_DESCRIPTOR_STALE
authority_granted = false
live_accepted = false

Supervisor task_state=Running
supervisor state=suppressed
last_error_code=OWNER_DEAD
last_host_pid=42556
last_spawned_pid=null
consecutive_failures=63
suppressed_until=2026-09-22T16:48:12.9353536Z
last_healthy_at=2026-09-22T16:11:21.6495570Z
```

`Running` của Scheduled Task chỉ chứng minh task tồn tại; không phải
Recovery Host healthy. `OWNER_DEAD` và `last_spawned_pid=null` cho thấy
packaged host chưa nạp source repair và chưa có activation mới. Không gọi
`recovery:supervisor:once`, `dev:refresh`, reboot, deploy, admission grant hay
quarantine trong bước này.

**Canonical census read-only mới:**

```text
snapshot_at = 2026-09-22T16:44:04.753Z
physical_sha256 = b65bf7e066b2929987f43fa2feefae14090dfbdb63c06741c2f8d372792e5b1e
logical_sha256 = 988e557c1ad10954f32e71927684e36cb527ab297942cee57fcdc771cd38964d
schema_version = 12
size_bytes = 97742848
integrity_check = ok
foreign_key_check_rows = 0
ordinary_active_runs = 17
p5_epochs = 6
run_classification = 17 THRESHOLD_SENSITIVE_STALE_CANDIDATE + 6 P5_EXPERIMENT_ANCHOR
unexplained_active_runs = 0
stale_background_operation_residues = 0
unbound_live_resource_residues = 0
mutated_canonical_ledger = false
```

Logical/physical hash và số census khớp snapshot 16.48; Backup API vẫn
`query_only + immutable`, không khởi tạo writer/runtime. Điều này củng cố rằng
controlled ledger recovery vẫn ở trạng thái
`APPLIED_EVIDENCE_ONLY + IDEMPOTENCE_GUARDED`; không cần và không được replay
candidate cũ.

**Checkpoint:** source repair đã được commit/push, nhưng packaged runtime,
primary MCP/Tunnel, strict discovery và real `workspace_context` vẫn chưa
được chứng minh. Hai Problem vẫn `OPEN`; các gate reboot/logon, natural-use,
independent outcome và criterion coverage vẫn chưa đạt. Bước tiếp theo có thể
thực hiện chỉ khi có owner-authorized controlled packaged activation; khi được
cấp, phải dùng đúng source/package/epoch identity rồi mới kiểm tra
`fullyReady`, connector freshness, `tools/list`/`server/discover` và một
`workspace_context` thật.
