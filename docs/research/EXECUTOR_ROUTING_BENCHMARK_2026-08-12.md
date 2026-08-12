# Executor Routing Benchmark — ChatWeb Sol vs Codex Luna vs Codex Terra

**Ngày nghiên cứu:** 2026-08-12  
**Repository:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**HEAD:** `1df45d48a661f336703f8b1c95fb3df74359dc60`  
**Codex runtime:** `codex-cli 0.147.0-alpha.6.6`  
**Grading Python:** `Python 3.11.7`  
**Mục tiêu:** quyết định có nên bật automatic Luna/Terra implementation routing trong `sol-lean-codex` / Coding Tools MCP hay không.

---

## 1. Executive decision

### Quyết định hiện tại

**KHÔNG bật Luna hoặc Terra thành autonomous executor mặc định.**

Giữ topology production hiện tại:

```text
ChatWeb GPT-5.6 Sol
    -> localize / settle semantics / choose proof
    -> deterministic Coding Tools MCP apply + verify
    -> optional independent packet review
    -> Sol final acceptance
```

Đối với implementation routing:

- **Luna autonomous executor: REJECT cho auto-routing hiện tại.** First-pass acceptance chỉ `2/10 = 20%`; ngay cả khi loại capacity failures chỉ còn `2/6 = 33.3%`.
- **Terra autonomous executor: REJECT làm global/default auto-route.** First-pass acceptance `6/10 = 60%`; khi loại capacity failures đạt `6/8 = 75%`, vẫn thấp hơn quality floor của Sol trên suite này.
- **ChatWeb Sol -> MCP patch: KEEP DEFAULT cho localized strong-oracle work.** Đạt `10/10 = 100%` accepted và không có focused-green/full-red integration defect.
- **Terra: giữ làm gated experimental executor** cho cross-file/reasoning-bearing work khi lợi ích giảm context hoặc chạy độc lập có khả năng bù được startup/tool-loop latency.
- **Luna: giữ reviewer / narrow leaf; nghiên cứu tiếp topology `patch-only/no-tools`** thay vì autonomous shell/test loop.
- **Không dùng cascade `Luna -> Terra -> Sol` hoặc `Terra -> Sol` làm mặc định.** Trên dữ liệu này, cascade tuần tự làm time-to-accepted-result tệ hơn Sol-only.

Điểm quan trọng nhất: **rate card rẻ không đồng nghĩa expected accepted result rẻ.** Luna rẻ hơn trên mỗi successful call, nhưng failure/capacity/deadline làm lower-bound observed credits per accepted outcome cao hơn Terra trong suite này.

---

## 2. Research question

Benchmark trả lời câu hỏi triển khai cụ thể:

> Với cùng một regression thật trên source hiện tại, cùng focused oracle và cùng full package gate, route nào có xác suất đạt accepted result cao nhất với latency/cost hợp lý: ChatWeb Sol điều phối MCP patch, Codex Luna autonomous executor, hay Codex Terra autonomous executor?

Đây là **system/topology benchmark**, không phải pure model intelligence benchmark. Nó đo đúng đường chạy có thể triển khai trong hệ thống hiện tại, bao gồm tool loops, App Server capacity, hard deadline và MCP round trips.

---

## 3. Snapshot / provenance

Benchmark base là **working-tree snapshot hiện tại**, không chỉ HEAD commit, vì Codex bridge đang là change-set chưa commit. Các file quyết định và SHA-256 tại thời điểm benchmark:

| File | SHA-256 |
|---|---|
| `resources/coding-tools-mcp/coding_tools_mcp/server.py` | `D19D2566F1DC97A6ADE4B7400E4FD137D0BBBD6C7625B4241D65E18F03527054` |
| `resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py` | `C592E36D2E7282A2668953D49715C6A5EF2D4FD952203A7DB5CB88ECCE54668F` |
| `resources/coding-tools-mcp/tests/test_codex_bridge.py` | `9C892DD14C5ACB3909E8471D2ADBDE03637090A84CC16EA7E125F3EFD69C7E7F` |
| `resources/coding-tools-mcp/tests/test_task_state_and_build.py` | `478EE429D6E78A4B2EFAA18ED412F416AF50EE4AEDE836D9C63D793D290C3771` |
| `tests/stability-source.test.js` | `D4C7764C72104A7F12B2C37AFCB8C2730D82E3EB9028329ED214A221B16B62CF` |

Pristine package gate trước mutation: **38/38 Python tests pass**.

---

## 4. Methodology

### 4.1 Controlled mutation design

Không dùng toy repository. Benchmark tạo 10 regressions có chủ đích trên source production của `resources/coding-tools-mcp`, mỗi regression phá đúng một invariant đã có existing test oracle.

Mỗi task được chạy trên isolated fixture riêng:

1. copy cùng pristine source snapshot;
2. inject đúng một production regression;
3. `git init` + commit mutated baseline;
4. xác nhận focused oracle **đỏ**;
5. giao cùng objective + focused oracle cho executor;
6. executor không được sửa tests;
7. grading lại focused oracle;
8. chạy full **38-test Python package gate**;
9. accepted chỉ khi focused pass + full pass + tests không bị sửa.

Preflight xác nhận **10/10 mutations đều làm focused oracle fail**, nên không có task oracle giả-green.

### 4.2 Routes

#### ChatWeb Sol

- Model/control plane: GPT-5.6 Sol trong ChatWeb.
- Flow: failure evidence -> focused source inspection -> minimal MCP patch -> external grading.
- Không có token/credit telemetry từ ChatWeb; báo cáo **không suy đoán** token/cost.
- Sol coordinator đã có repository/conversation context; đây là topology production thực tế nhưng tạo lợi thế context so với một pure blind model benchmark.

#### Luna executor

- Model: `gpt-5.6-luna`.
- Effort: `low`.
- Independent App Server thread.
- Isolated `workspaceWrite` fixture.
- Network off, approval `never`, no delegation/multi-agent/apps/browser/plugins/memories.
- Shell enabled vì đây là autonomous implementation executor.
- Hard executor deadline: 45 seconds.
- Một attempt duy nhất; không retry unchanged capacity/deadline failure.

#### Terra executor

- Model: `gpt-5.6-terra`.
- Effort: `medium`.
- Cùng sandbox, isolation, oracle và 45-second deadline như Luna.

### 4.3 Why App Server, not `codex exec`

Pilot `codex exec --ignore-user-config` rơi khỏi Desktop provider/auth route và gặp `401` từ stale environment API key. Benchmark chuyển sang cùng App Server transport mà bridge production đang dùng thành công. Writable sandbox được preflight riêng: Luna tạo file trong isolated fixture đúng nội dung, chứng minh workspace-write path hoạt động.

### 4.4 Metrics

- **First-pass acceptance:** route đạt focused + full gate trong một outer attempt.
- **Availability-adjusted acceptance:** acceptance sau khi loại `serverOverloaded` khỏi denominator; dùng để tách capability khỏi service capacity.
- **Executor wall:** thời gian model/tool loop, không tính fixture setup.
- **TTA (time-to-accepted-result observation):** `executor wall + independent focused grading + full 38-test gate`.
- **Capacity failure:** App Server `serverOverloaded` / “Selected model is at capacity”.
- **Deadline failure:** 45-second turn bị interrupt và grading vẫn đỏ.
- **Accepted-at-deadline:** turn bị interrupt nhưng source đã đủ đúng để external grading xanh.
- **Integration defect:** focused gate xanh nhưng full package gate đỏ.
- **Credits:** bridge-estimated credits theo `codex_rate_card_observed_2026-08-12`; chỉ là estimate có pricing-basis date.

Lưu ý: TTA ở đây là **time-to-accepted under current orchestration**, không phải timestamp chính xác của “first byte when patch became green”. Current telemetry chưa timestamp được thời điểm focused oracle đầu tiên bên trong agent loop. Với accepted-at-deadline runs, patch có thể đã đúng trước giây 45 nhưng agent chưa kết thúc turn.

---

## 5. Task suite

| ID | Class | Mutated invariant | Integration width |
|---|---|---|---|
| T01 | `security_env_isolation` | Child env không còn loại `WEBCODEX_*` secret prefix | Low |
| T02 | `routing_effort_control` | PACKET review bị đổi `low -> ultra` | Low |
| T03 | `tool_surface_isolation` | PACKET reviewer bị bật shell tool | Low |
| T04 | `app_server_protocol` | Ephemeral fork gửi lại invalid `deferGoalContinuation` | Medium |
| T05 | `cost_accounting` | Cached tokens bị tính lại như uncached | Low |
| T06 | `capacity_resilience` | Capacity error không mở cooldown/circuit breaker | Medium |
| T07 | `session_ownership` | Continuation bỏ bridge-owned-thread guard | Medium |
| T08 | `api_validation` | Public error code `INVALID_ACTION` bị đổi sai | Low |
| T09 | `client_tool_compatibility` | Smart surface tăng 8 -> 9 model-facing tools | Medium |
| T10 | `dirty_worktree_isolation` | Reviewer diff lấy whole dirty path thay vì affected paths | Medium |

---

## 6. Aggregate results

| Metric | ChatWeb Sol -> MCP | Luna autonomous | Terra autonomous |
|---|---:|---:|---:|
| First-pass accepted | **10/10 (100%)** | **2/10 (20%)** | **6/10 (60%)** |
| Accepted given model available | **100%** | **33.3% (2/6)** | **75% (6/8)** |
| Capacity failures | 0 | 4 | 2 |
| Deadline failures | 0 | 4 | 2 |
| Accepted despite deadline interrupt | 0 | 1 | 5 |
| Focused-green / full-red integration defects | **0** | **0** | **0** |
| Tests modified | 0 | 0 | 0 |
| Median executor wall | 39.2s | 43.4s | 45.8s |
| Median observed TTA, all attempts | **42.5s** | 47.3s | 48.9s |
| Median observed TTA, accepted only | **42.5s** | 48.1s | 49.2s |
| p90 observed TTA, accepted only | 104.9s | 51.1s* | 49.9s |
| Median model/tool command events | **2** | 3 | 4 |

`*` Luna accepted-only n=2 nên p90 không có ý nghĩa thống kê mạnh.

### Interpretation

1. **Quality floor disqualifies both lower-tier autonomous routes before cost optimization.** Sol đạt 100%; Luna 20%; Terra 60%.
2. Terra tốt hơn Luna rõ rệt về autonomous implementation competence, nhưng chưa đủ ổn định để làm default executor.
3. Lower-tier agent loops không tạo typical latency advantage trên suite localized/strong-oracle này. Median TTA của cả Luna và Terra đều cao hơn Sol.
4. Sol có tail latency lớn hơn do ChatWeb/tool-roundtrip orchestration outliers; vì thế phải nhìn median và per-task pairing, không dùng mean đơn độc.

---

## 7. Per-task results

Status: `PASS` = accepted; `CAP` = capacity failure; `DL` = deadline with red grading.

| Task | Class | Sol result / TTA | Luna result / TTA / credits | Terra result / TTA / credits |
|---|---|---:|---:|---:|
| T01 | security_env_isolation | PASS / 30.2s | CAP / 33.9s / 0.183 cr | CAP / 8.6s / n/a cr |
| T02 | routing_effort_control | PASS / 146.7s | DL / 54.4s / 0.144 cr | DL / 50.3s / 0.371 cr |
| T03 | tool_surface_isolation | PASS / 30.0s | CAP / 10.3s / n/a cr | PASS / 49.7s / 0.200 cr |
| T04 | app_server_protocol | PASS / 45.8s | PASS / 44.3s / 0.065 cr | PASS / 49.1s / 0.199 cr |
| T05 | cost_accounting | PASS / 40.7s | CAP / 15.9s / 0.257 cr | PASS / 48.6s / 0.264 cr |
| T06 | capacity_resilience | PASS / 100.3s | PASS / 51.9s / 0.091 cr | PASS / 43.6s / 0.208 cr |
| T07 | session_ownership | PASS / 38.3s | DL / 51.8s / 0.103 cr | DL / 48.6s / 0.433 cr |
| T08 | api_validation | PASS / 44.3s | DL / 50.3s / 0.285 cr | CAP / 21.5s / 0.206 cr |
| T09 | client_tool_compatibility | PASS / 58.4s | CAP / 9.0s / n/a cr | PASS / 50.0s / 0.317 cr |
| T10 | dirty_worktree_isolation | PASS / 37.3s | DL / 52.6s / 0.077 cr | PASS / 49.2s / 0.199 cr |

T02 là Sol outlier do MCP permission/patch primitive phải đổi strategy giữa chừng; đây là orchestration friction thật của observed path, không phải semantic difficulty. T06 cũng có ChatWeb round-trip latency outlier. Hai outliers này làm mean Sol xấu hơn đáng kể, trong khi median vẫn thấp hơn lower-tier routes.

---

## 8. Pairwise comparison on tasks both routes accepted

### Luna vs Sol

Chỉ có 2 common accepted tasks:

| Task | Sol TTA | Luna TTA | Luna delta |
|---|---:|---:|---:|
| T04 | 45.8s | 44.3s | **-1.6s** |
| T06 | 100.3s | 51.9s | **-48.4s** |

Luna có thể thắng mạnh khi Sol gặp orchestration tail, nhưng first-pass acceptance 20% khiến không thể dùng kết quả này để justify auto-routing.

### Terra vs Sol

Có 6 common accepted tasks:

| Task | Sol TTA | Terra TTA | Terra delta |
|---|---:|---:|---:|
| T03 | 30.0s | 49.7s | **+19.8s slower** |
| T04 | 45.8s | 49.1s | **+3.3s slower** |
| T05 | 40.7s | 48.6s | **+7.9s slower** |
| T06 | 100.3s | 43.6s | **-56.7s faster** |
| T09 | 58.4s | 50.0s | **-8.4s faster** |
| T10 | 37.3s | 49.2s | **+11.9s slower** |

Terra nhanh hơn trên 2/6 common accepted tasks và chậm hơn trên 4/6. Không thấy feature classifier đơn giản như `integration_width=medium` đủ để dự báo thắng/thua: T04/T06/T09/T10 đều medium nhưng kết quả latency khác nhau.

---

## 9. Cost economics

### Accepted-call cost

Trong những run đã accepted và có telemetry:

- Luna: total accepted credits `0.155620`, mean `0.077810` / accepted call.
- Terra: total accepted credits `1.386789`, mean `0.231132` / accepted call.

Nếu chỉ nhìn bảng này, Luna có vẻ cực rẻ. Nhưng đó không phải policy cost.

### Cost including failed attempts

Observed credits trên toàn route:

- Luna: `1.204870` credits trên 8/10 rows có token accounting; 2 capacity rows thiếu accounting.
- Terra: `2.396638` credits trên 9/10 rows có accounting; 1 capacity row thiếu accounting.

Lower-bound observed credits per accepted outcome, **tính cả credits đã tiêu ở failed attempts**:

- Luna: ít nhất `1.204870 / 2 = 0.602435` credits / accepted outcome.
- Terra: ít nhất `2.396638 / 6 = 0.399440` credits / accepted outcome.

Đây là lower bound vì rows thiếu telemetry không được giả định là zero-cost.

**Kết luận:** model rẻ hơn theo rate card có thể trở thành policy đắt hơn theo accepted-result economics nếu failure rate cao.

ChatWeb Sol token/credit telemetry không được expose, nên benchmark **không kết luận monetary cost của Sol thấp hơn Luna/Terra**. Kết luận monetary chỉ áp dụng cho so sánh internal Codex routes và wasted-call economics.

---

## 10. Cascade policy analysis

Dùng chính paired observations để mô phỏng serial fallback:

### Sol-only

- Mean observed TTA: **57.20s/task**.
- Median: **42.52s/task**.

### Luna first, Sol on Luna failure

- Mean: **80.02s/task**.
- Median: **65.75s/task**.
- Mean penalty so với Sol-only: **+22.82s/task (~+39.9%)**.

### Terra first, Sol on Terra failure

- Mean: **67.86s/task**.
- Median: **49.47s/task**.
- Mean penalty so với Sol-only: **+10.66s/task (~+18.6%)**.

### Impossible oracle-perfect router

Nếu có oracle biết trước route nào sẽ accepted và nhanh nhất, lựa chọn observed tối ưu sẽ là:

- T04 -> Luna;
- T06 -> Terra;
- T09 -> Terra;
- 7 task còn lại -> Sol.

Khi đó:

- Mean TTA: `50.53s` thay vì `57.20s`, save `~6.67s/task` (~11.7%).
- Median TTA: `42.16s` thay vì `42.52s`, save chỉ `~0.36s` (~0.85%).

Điều này rất quan trọng: phần lớn mean gain lý tưởng đến từ vài Sol tail outliers. **Typical-task median hầu như không cải thiện ngay cả với perfect routing knowledge.** Thực tế router không có perfect foresight, nên auto cascade hiện chưa có economic case.

---

## 11. Rework / loop behavior

Benchmark cố ý dùng **một outer attempt per route** và không retry unchanged failure. Vì vậy metric chính cho rework là first-pass acceptance, không phải “retry until green”.

- Sol: median 2 problem-solving MCP tool turns.
- Luna: median 3 command events.
- Terra: median 4 command events.

Lower-tier autonomous routes thường cần nhiều tool-loop steps hơn, nhưng nhiều run vẫn chạm 45s deadline. Điều này cho thấy phần chi phí lớn nằm ở **agentic localization/test loop**, không chỉ model reasoning token.

Không có task nào sửa tests. Không có case focused oracle xanh nhưng full Python package gate đỏ. Trong phạm vi suite này, khi lower-tier thực sự tìm được causal fix thì existing strong oracle khá tốt trong việc bảo vệ integration boundary.

---

## 12. Deadline behavior and a useful executor primitive

Một finding đáng giữ lại dù không promote auto executor:

- Luna có 1 accepted run bị interrupt ở deadline.
- Terra có **5 accepted runs** bị interrupt ở deadline.

Tức là model turn chưa kết thúc nhưng patch trên disk đã đủ đúng để external grading pass.

Nếu sau này triển khai writable Codex executor production, cần primitive:

```text
deadline reached
    -> interrupt model turn
    -> freeze candidate diff
    -> run external focused oracle
    -> if green: run affected integration gate and accept candidate
    -> if red: reject/revert candidate
```

Không nên coi `turn interrupted` tự động đồng nghĩa `implementation failed`.

Đồng thời cần thêm telemetry `time_to_first_write` và `time_to_first_oracle_green`; current benchmark chỉ có turn/deadline-level wall time nên có thể overestimate time mà correct patch đã thực sự tồn tại.

---

## 13. Capacity is operational, not intrinsic capability

Observed `serverOverloaded`:

- Luna: **4/10 = 40%**.
- Terra: **2/10 = 20%**.

Capacity-adjusted acceptance:

- Luna: **33.3%**.
- Terra: **75%**.

Vì vậy một phần failure là runtime availability chứ không phải reasoning failure. Tuy nhiên router production phải tối ưu **accepted result trong môi trường thật**, nên capacity vẫn là routing input hợp lệ.

Policy giữ nguyên:

1. không retry cùng unchanged call;
2. mở model-specific cooldown;
3. không cascade nhiều tier chỉ vì capacity;
4. return quyền quyết định về Sol;
5. chỉ dùng một fallback nếu expected value dương và quality floor vẫn giữ được.

---

## 14. Production routing recommendation

### 14.1 Localized + strong oracle

**Default:** `ChatWeb Sol -> deterministic MCP patch/verify`.

```text
if localized and strong_oracle:
    EXECUTOR_ROUTE = SOL_LOCAL + MCP
    external_autonomous_executor = NONE
```

Lý do: 100% acceptance trong suite, median TTA thấp hơn lower-tier autonomous routes, và không cần trả startup/tool-loop cost của một agent thứ hai.

### 14.2 Luna

Không bật `LUNA_AUTONOMOUS_EXECUTOR`.

Giữ Luna cho:

- packet reviewer;
- leaf reasoning cực hẹp;
- candidate generation khi exact scope/contract đã settled.

**Nghiên cứu tiếp topology đáng giá hơn:**

```text
Sol localizes + builds compact implementation packet
    -> Luna PATCH-ONLY / NO-TOOLS / short deadline
    -> deterministic MCP applies patch
    -> oracle
    -> Sol accepts
```

Hypothesis: loại shell/test-agent loop có thể giữ cost thấp của Luna mà tránh 40–50s autonomous executor overhead.

### 14.3 Terra

Không bật Terra làm default/global executor.

Cho phép **gated experiment** khi:

- task thật sự reasoning-bearing/cross-file;
- scope và write ownership bounded;
- isolated worktree;
- strong external proof;
- expected Sol control-plane work lớn hơn startup cost;
- recent class-specific telemetry cho thấy first-pass acceptance đủ cao;
- one attempt, bounded deadline;
- capacity failure -> Sol, không retry unchanged.

Terra vẫn là candidate hợp lý hơn Luna cho autonomous implementation vì capability-adjusted acceptance 75%, nhưng sample này chưa đạt quality floor để auto promote.

### 14.4 No serial model ladder

Không triển khai:

```text
Luna fails -> Terra -> Sol
```

hoặc mặc định:

```text
Terra -> Sol fallback
```

Dữ liệu paired đã chứng minh serial fallback làm mean latency tăng mạnh trên suite hiện tại.

---

## 15. Proposed router state after this study

```text
EXECUTION PLANE

TOOL
  deterministic transform / tests / compiler / exact operations

CHATWEB_SOL_MCP   <- DEFAULT for localized strong-oracle repair
  semantic localization + minimal deterministic patch + proof

LUNA_PATCH_ONLY   <- EXPERIMENTAL, not autonomous
  compact settled packet, no repository shell loop

TERRA_SCOPED_EXECUTOR <- GATED EXPERIMENT
  cross-file reasoning-bearing implementation, isolated worktree

SOL_LOCAL
  unsettled semantics / critical invariants / integration / final acceptance
```

External verification plane remains independent:

```text
NONE -> PACKET(Mini) -> SCOPED(Luna) -> CRITICAL(Terra) -> SOL_LOCAL -> HISTORY
```

Implementation tier và review tier không được trộn thành một mandatory cascade.

---

## 16. Promotion gates before enabling automatic implementation routing

Một lower-tier implementation route chỉ được promote theo task class sau khi paired evaluation đạt đồng thời:

1. **Quality:** không thấp hơn accepted quality floor của Sol trên protected invariants.
2. **First-pass acceptance:** đủ cao để serial failure cost không nuốt latency/cost savings.
3. **Capacity:** low enough cho production use; capacity failures không bị che bằng retry loops.
4. **Latency:** accepted-result median và p90 có material improvement, không chỉ một vài mean outliers.
5. **Integration:** không có focused-green/full-red regression trên representative boundary tests.
6. **Cost:** expected credits per accepted outcome, tính cả failed attempts, tốt hơn route hiện tại.
7. **Rework:** không tăng review/repair burden của Sol.

Suite hiện tại không đạt gate 1/2 cho Luna và Terra autonomous execution, nên promotion bị từ chối trước khi tối ưu sâu về price.

---

## 17. Limitations

### 17.1 ChatWeb context advantage / experimenter contamination

ChatWeb Sol coordinator đã có conversation/repository context và cũng là bên thiết kế benchmark mutations. Codex Luna/Terra chỉ nhận objective + focused oracle. Vì vậy đây **không phải blind pure-model leaderboard**.

Điều này không làm benchmark vô giá trị: production topology cũng có Sol giữ accumulated semantic context. Nhưng kết luận nên đọc là “route nào tốt trong hệ thống này”, không phải “model nào thông minh hơn tuyệt đối”.

### 17.2 Single run per task/model

Mỗi route/task có một official observation. Capacity variance chưa được estimate bằng repeated trials. Vì kết luận hiện tại là **không promote** (conservative), thiếu replicates không làm phát sinh false-positive promotion; nhưng cần replicates trước khi sau này promote Terra.

### 17.3 Suite concentrates on localized strong-oracle regressions

10 tasks chủ yếu là one-invariant fixes trong Coding Tools MCP bridge/runtime. Đây chính là class cần quyết định có nên route xuống Luna/Terra vì “trông có vẻ dễ”. Kết luận **không nên extrapolate** sang feature development lớn, UI, migration hoặc cross-system architecture.

### 17.4 Full gate boundary

Per-task integration gate là 38-test Python package suite, không phải toàn monorepo/npm/Electron/release matrix. `integration_defect=0` chỉ có nghĩa không có focused-green/full-red trong boundary này.

### 17.5 TTA instrumentation

Current App Server harness chưa ghi timestamp chính xác của first successful internal oracle. Accepted-at-deadline runs cho thấy patch có thể green trước khi turn kết thúc. Production executor nên thêm first-write/first-green telemetry trước benchmark vòng sau.

### 17.6 ChatWeb cost is unknown

Không có token/credit accounting cho ChatWeb route. Không được suy ra monetary superiority của Sol từ dữ liệu này.

### 17.7 Generated bytecode

Python grading tạo `__pycache__/*.pyc` trong fixtures. Các file này bị bỏ qua khi đánh giá implementation overreach; production source/test writes mới là material changes.

---

## 18. Next study with highest value

Không cần thêm bridge research trước. Vòng tiếp theo nên tập trung vào topology nơi lower-tier model có cơ hội thắng thật:

### Study A — Luna patch-only

10–12 localized tasks, so sánh:

1. ChatWeb Sol -> MCP patch;
2. Luna autonomous executor;
3. **Luna packet/no-tools -> patch candidate -> MCP oracle**.

Đo `time_to_candidate`, `time_to_green`, tokens/credits, accepted rate và Sol repair burden.

### Study B — Terra cross-file executor

6–10 medium-context/cross-file tasks thật, mỗi task 2–3 repetitions để đo capacity variance:

- adapters;
- environment/CI diagnosis;
- multi-file behavior fixes;
- bounded UI/data-flow changes;
- repository slices nơi Sol context growth có cost rõ.

So `Sol/MCP` với `Terra scoped executor`, không dùng Luna làm mandatory first hop.

### Instrumentation cần thêm

- `time_to_first_write`;
- `time_to_first_focused_green`;
- exact tool/command timestamps;
- candidate diff fingerprint;
- cache ratio by turn;
- capacity/cooldown state;
- Sol repair-after-worker count;
- accepted/rejected reason taxonomy.

---

## 19. Final conclusion

Dữ liệu hiện tại **không ủng hộ bật automatic Luna/Terra autonomous implementation routing**.

### What is proven enough to act on now

- Sol/MCP: **10/10 accepted** trên targeted strong-oracle suite.
- Luna autonomous: **2/10 accepted**, 40% capacity failures, nhiều deadline failures.
- Terra autonomous: **6/10 accepted**, tốt hơn Luna nhưng vẫn không đạt quality floor; 5/6 accepted tasks gần/chạm hard deadline.
- Naive Luna-first cascade làm mean TTA tệ hơn Sol-only khoảng **22.8s/task**.
- Naive Terra-first cascade làm mean TTA tệ hơn Sol-only khoảng **10.7s/task**.
- Ngay cả impossible perfect router chỉ cải thiện median khoảng **0.36s** trên suite này; mean gain chủ yếu đến từ vài Sol tail outliers.
- Không có focused-green/full-red integration defect trong 30 official observations.
- Cheap per-call không đồng nghĩa cheap per-accepted-result: Luna lower-bound observed credits/accepted outcome cao hơn Terra vì failure waste.

### Deployment decision

```text
KEEP:
  ChatWeb Sol as semantic/control plane and final acceptance
  deterministic MCP execution/proof
  Mini/Luna/Terra as optional review plane according to existing router

DO NOT ENABLE:
  Luna autonomous executor by default
  Terra autonomous executor globally
  Luna -> Terra -> Sol serial cascade

ALLOW EXPERIMENTALLY:
  Luna patch-only/no-tools candidate generation
  Terra scoped executor for cross-file reasoning work with isolated write lane,
  one attempt, hard deadline, external grading, and class-specific telemetry
```

**Promotion status: REJECT automatic Luna/Terra executor routing for the tested task class.**

The next optimization target is not “use more agents”; it is **reduce autonomous agent-loop overhead and route only when class-specific evidence predicts a real accepted-result advantage**.
