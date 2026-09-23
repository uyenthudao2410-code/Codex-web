# Trạng thái hiện tại sau commit `00c9c855` — hai Problem vẫn OPEN

**Quan sát:** `2026-09-23 16:28:31 +07` (`2026-09-23T09:28:31Z`)

**Workspace:** `E:\DEV\Codex-web`
**Branch:** `main` (không dùng worktree)
**Phạm vi:** recapture read-only và cập nhật kế hoạch; không kill process, không
restart/reboot, không tunnel CRUD, không connector ACK, không sửa descriptor,
không quarantine epoch, không ghi trực tiếp `ledger.sqlite3`, không tạo RUN hay
outcome nhân tạo.

Tài liệu này là snapshot mới. Các tài liệu ngày 23/09 trước đó vẫn là chronology
và bằng chứng của thời điểm tương ứng; không dùng snapshot cũ để tuyên bố trạng
thái live hiện tại.

## 1. Git và delivery

```text
branch                  = main
HEAD                    = 00c9c85549345a9ae33fcbb63c3ebc57c6ed637c
origin/main             = 00c9c85549345a9ae33fcbb63c3ebc57c6ed637c
divergence              = 0/0
source/test worktree    = clean
runtime evidence dirty  = .coding-tools/orchestration/ledger.sqlite3
                          .coding-tools/orchestration/task-context-workspaces.json
                          .coding-tools/performance.json
```

Commit hiện hành là:

```text
fix: drain HTTP handlers before runtime shutdown
```

Các delivery guard trước commit đã pass (`check:coding-tools-delivery`,
`check:coding-tools-history`, `check:repository-secrets`, `git diff --cached
--check`) và commit đã được push lên `origin/main`. Ba file dirty hiện tại là
runtime evidence biến động; không được reset hoặc sửa tay để làm worktree xanh.

## 2. Runtime live hiện tại

Lệnh đọc `npm run dev:status` tại snapshot này trả:

```text
state=MISSING
host=available
installation=mismatch
pid=none
instance=none
mode=none
running_revision=none
disk_revision=none
components_ready=unknown
fully_ready=unknown
runtime_update_incomplete=unknown
runtime_telemetry_available=unknown
connector_state=UNAVAILABLE
connector_rediscovered=unknown
connector_refresh_required=unknown
error_code=DEV_UI_INSTALLATION_MISMATCH
```

Diễn giải đúng mức bằng chứng:

- Không có process/instance current nào được `dev:status` chứng minh là đã nạp
  source `00c9c855`.
- `host=available` không đồng nghĩa MCP/Tunnel đang chạy; `state=MISSING` là
  trạng thái fail-closed của primary dev UI/runtime.
- `installation=mismatch` là blocker handoff/activation hiện tại. Không được
  dùng `taskkill`, sửa `recovery-host.json`, sửa `runtime-state.json` hoặc sửa
  ledger để vượt guard.
- Lần `dev:refresh` trước đã bị từ chối với
  `RECOVERY_HOST_IDLE_HANDOFF_REFUSED`; đây là guard đúng khi chưa có bằng chứng
  packaged host idle. Cần lifecycle authority và process identity authenticated
  cho lần xử lý kế tiếp.

Vì connector được hỗ trợ hiện không khả dụng, chưa có receipt current-process
cho `tools/list`, `server/discover`, client delivery/compatibility attestation
hoặc `workspace_context` thật.

## 3. Ledger census và dữ liệu tri thức

Đã mở canonical ledger bằng read-only/backup API. Snapshot vật lý được tạo lúc
`2026-09-23T09:27:21.576Z` có:

```text
schema_version                 = 12
integrity_check                = ok
foreign_key_check_rows         = 0
physical_snapshot_sha256       = b9381dec0dea3b13e695352b4fa8ec41793f080d916e7209981966c53a7a8aea
logical_snapshot_sha256        = 782f1e87fd2062ce2ec3009101bf17d2bc9763cb56b6fa3b40b6b9db7b148108
mutated_canonical_ledger       = false
projection                    = CONTEXTUAL_PROJECTIONS; drift=false
context_count                 = 1079
ordinary_active_runs          = 17 (THRESHOLD_SENSITIVE_STALE_CANDIDATE)
p5_epochs                     = 6
unexplained/unbound/stale-bg  = 0/0/0
```

Đếm trực tiếp chế độ read-only sau census xác nhận:

```text
goal_continuations             = 0
goal_continuation_observations = 0
run_continuations              = 1
```

`run_continuations` duy nhất thuộc Problem khác
`prl-6ac55390f353c5743406eb8d0a823d8e` revision 1, không thuộc
`prl-e918c7d33e70c2d304d0797e11b05fcb` revision 2. Do đó chưa có durable Goal
canary/outcome cho Goal đang theo đuổi.

## 4. Hai Problem — phải giữ tách biệt

Truy vấn theo đúng `problem_id` và `revision` cho kết quả:

| Problem | Revision / tiêu chí | RUN theo status | Latest event | Outcome receipt | Authority |
|---|---:|---|---:|---:|---|
| `prl-22e670302757c9b7663170e226ed7c26` | rev1 / 12 | 47 accepted, 16 aborted, 3 active = 66 | 320 | 0 | `OPEN` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` | rev2 / 18 | 16 accepted, 10 aborted, 13 active = 39 | 316 | 0 | `OPEN` |

Các RUN accepted ở đây chỉ là lịch sử engineering attempt. Chúng không phải
criterion coverage, natural outcome hay closure authority. Cả hai Problem đều
chưa có `outcome_receipt_id`.

### 4.1. `prl-22e…` rev1 — packaged/recovery/reboot acceptance

Đã đạt ở tầng source/focused: P1 semantic stop refusal, P2 rollback startup
intent, role-aware lifecycle readiness, installation/process identity guard,
mutex isolation, foreign-installation refusal, fallback read-only, packaged
Recovery Host smoke và HTTP/SQLite shutdown-drain repair.

Chưa đạt ở tầng live/acceptance:

- controlled activation bound vào installation và activation epoch hiện tại;
- current-process `tools/list` và `server/discover`;
- real `workspace_context` trên `E:\DEV\Codex-web`;
- receipt bind PID/process instance/MCP server instance/epoch/contract SHA;
- cold-start/logon/reboot và startup-intent matrix;
- Machine B/right endpoint và host-only/central-route/Tunnel fault matrix;
- rollback/partial-effect proof ở runtime thật;
- natural-use window, independent user outcome và coverage chính xác C01–C12.

### 4.2. `prl-e918…` rev2 — durable Goal continuation

Đã có source/focused proof cho provider bridge bền vững, persistent App Server
session, response-end worker observation, parent/child continuation và budget,
effect journal/backup, unknown-effect reconciliation, reconnect/restart/rebind,
controller/Problem/revision/epoch/source binding và fail-closed unknown dispatch.

Chưa đạt:

- natural Goal thật có provider/worker dispatch sau response end, không manual
  relay;
- reconnect/restart/rebind trong cùng Goal và unknown-effect reconciliation
  thật;
- parent-budget continuity;
- controller delivery/ACK, review/progress semantics;
- independent Goal outcome và coverage chính xác BG01–BG14;
- closure authority.

## 5. Proof ladder hiện hành

```text
SOURCE_PRESENT             = PASS
FOCUSED_PROOF              = PASS
DELIVERED_MAIN             = PASS (HEAD == origin/main)
PACKAGED_SMOKE             = PASS ở snapshot cô lập/lịch sử; chưa phải live current
CONTROLLED_ACTIVATION      = CHƯA CHỨNG MINH
STRICT_REDISCOVERED        = CHƯA CHỨNG MINH
REAL_WORKSPACE_CONTEXT     = CHƯA CHỨNG MINH
REBOOT / MACHINE B         = CHƯA CHỨNG MINH
NATURAL C01–C12 OUTCOME    = CHƯA CÓ
DURABLE BG01–BG14 OUTCOME  = CHƯA CÓ
P4/P5 PROMOTION/ECONOMICS  = CHƯA ĐẠT
Problem closure             = OPEN / không có closure authority
```

Các proof source đã ghi nhận:

```text
python -m py_compile mcp_http_handler.py                    PASS
provider/telemetry focused tests                             3 passed
execution_hub + fault tests                                  22 passed + 4 subtests
npm run test:mcp                                             1162 passed, 5 skipped
npm test                                                      1033 passed
npm run test:recovery:e2e                                    3 passed
packaged/isolated NSIS recovery smoke                        PASS
```

Đây là bằng chứng source/focused/package; không được nâng thành installed live
acceptance khi `dev:status` còn `MISSING/mismatch` và connector còn
`UNAVAILABLE`.

## 6. P4/P5 và chỉ số economics

Report read-only ở cùng HEAD cho:

```text
P4 state / empirically complete       = COLLECTING / false
representative shadow tasks           = 100
raw repaired tasks                    = 20
causal-solution repair tasks          = 0
causal-solution unknown tasks         = 29
predictive targeting                  = false
P5 baseline ready                     = true
P5 lifecycle                          = EPOCH_HARD_STOPPED
P5 experiment start                   = false
```

Không được diễn giải `20 raw repaired` thành 20 causal fixes; nhãn causal
solution hiện không có variation đủ để đánh giá predictive signal.

Economics report quan sát cửa sổ `2026-09-01`–`2026-09-15`:

```text
proof-cache hits/misses               = 6/977 trên 983 mẫu
hit rate                              = 0.6104%
known saved time                     = 25,335 ms
misses                                = 517 cold + 460 input_fingerprint_changed
accepted runs in resource summary    = 262
provider usage observed runs         = 0
provider cost complete runs          = 0
total monetary cost coverage         = 0.0%
current-head DRE accepted runs       = 0 (insufficient_head_window_volume)
```

Chi phí thiếu là `unknown`, không phải zero. Estimated wait/local execution và
response bytes chỉ là resource evidence mô tả; chưa phải provider billing hay
economic promotion.

## 7. Việc đã xử lý và việc còn tồn tại

### Đã xử lý

1. Sửa race shutdown: request handler threads được drain trước khi đóng shared
   runtime/SQLite; giữ daemon-thread semantics của MCP server.
2. Hoàn tất các packet P1/P2, identity/handoff guard và regression proof.
3. Đưa source/doc/evidence snapshot lên `main`, push thành công.
4. Giữ nguyên fail-closed khi chưa có identity/epoch/connector proof thay vì
   kill process hoặc tạo receipt giả.

### Còn tồn tại — thứ tự bắt buộc

1. **Handoff/activation:** qua lifecycle authority chứng minh packaged host idle
   hoặc một owner-authorized packaged handoff; đồng nhất installation, package,
   source revision và activation epoch. Nếu không chứng minh được idle thì giữ
   `RECOVERY_HOST_IDLE_HANDOFF_REFUSED`.
2. **Strict discovery:** chỉ qua supported connector, thu `tools/list`,
   `server/discover`, client delivery/compatibility receipt bind PID/process
   instance/MCP server/epoch/contract SHA.
3. **Workspace admission:** gọi `workspace_context` thật trên đúng workspace;
   không dùng raw HTTP, internal Recovery IPC, local health, synthetic context
   hoặc manual ACK thay thế.
4. **Problem 22e:** sau admission mới chạy reboot/logon, startup-intent,
   Machine B, right endpoint, host-only/central-route/Tunnel fault matrix và
   một natural C01–C12 có independent outcome.
5. **Problem e918:** chạy một natural Goal qua response-end dispatch,
   reconnect/restart/rebind, unknown-effect reconciliation, budget continuity,
   controller delivery/ACK và independent outcome.
6. **Closure:** tạo exact coverage manifest C01–C12 và BG01–BG14, đối chiếu
   receipt lineage, rồi mới xin closure authority. Không terminalize 17 active
   stale-candidate RUNs hàng loạt và không tạo RUN/outcome nhân tạo.
7. **P4/P5/economics:** chỉ mở promotion/treatment khi có causal repair outcome
   variation, holdout validation, complete resource/cost coverage và release
   acceptance độc lập.

## 8. Quyết định vận hành hiện tại

Blocker hiện tại là:

```text
WAITING_FOR_SUPPORTED_CONNECTOR + DEV_UI_INSTALLATION_MISMATCH
```

Không có bằng chứng cho thấy P1/P2 đã regress và cũng không có căn cứ sửa
`control-plane` để giả lập local success. Bước tiếp theo duy nhất an toàn là
activation/handoff có kiểm soát khi lifecycle authority và supported connector
đủ điều kiện; nếu chưa đủ, giữ nguyên fail-closed và cập nhật snapshot mới.

**Kết luận:** phần sửa mã cốt lõi đã ở `main` và test xanh, nhưng mục tiêu sản
phẩm của hai Problem chưa hoàn tất. Hiện mới đạt source + focused proof +
delivered main; còn thiếu runtime identity/activation, strict discovery,
workspace admission, reboot/fault matrices, natural outcomes và closure
authority.
