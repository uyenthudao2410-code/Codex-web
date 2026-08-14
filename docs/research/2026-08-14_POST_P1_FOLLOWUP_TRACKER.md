# Post-P1 Follow-up Tracker — 2026-08-14

## 0. Authority và evidence rules

File này theo dõi các follow-up sau activation/telemetry, P1 proof-cache và control-plane hardening. Nó bổ sung cho `docs/research/2026-08-14_RUNTIME_ACTIVATION_AND_PRODUCTION_TELEMETRY_LOG.md`; chronology lịch sử trong file đó không bị viết lại.

Current authoritative checkout:

- Workspace: `E:\DEV\Tools-Codex-web`
- Branch: `main`
- HEAD quan sát xuyên suốt follow-up: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Public MCP profile: `smart-v3`
- Public tool count: `8`
- Current public tool-contract SHA-256: `4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754`

Evidence classes:

1. **Live runtime / durable-ledger measurement** — đọc trực tiếp từ runtime/ledger/benchmark trên checkout hiện tại.
2. **Deterministic focused proof** — test/oracle chứng minh semantics trong phạm vi thay đổi; không tự động suy ra production economics.
3. **Real-model microbenchmark** — model thật, credits/cache/TTA thật cho packet cụ thể; sample nhỏ không đủ để tune production policy.
4. **Scenario simulation** — regression/economic model; không được gọi là production billing A/B.
5. **Blocked candidate sample** — model call thật nhưng không đạt accepted candidate do packet/scope/runtime blocker; không tính vào accepted route cohort.

---

## 1. Status board

| Priority | Hạng mục | Trạng thái | Kết luận hiện tại |
|---|---|---|---|
| P0 | Connector/tool schema refresh | **FULL LIVE PASS** | Fresh ChatWeb contract expose đủ 8 tools, EOCL fields, `restart_runtime` và `confirm_restart`. |
| P0 | Universal idempotency live three-case canary | **PASS** | Exact replay dedup; conflicting reuse reject; new key intentional repeat executes. |
| P0 | Compact `workspace_context` payload tax | **PASS** | Compact không trả runtime block; full giữ diagnostics. |
| P1 | Proof-cache live reuse | **PASS** | Exact repeat hit; relevant source drift miss; volatile `.coding-tools` không invalidation; false reuse 0. |
| P1 | Handoff capsule durability/resume | **PASS** | Capsule bounded, round-trip stable, fresh resume không mất state. |
| P1 | Handoff same-thread vs fresh-window A/B | **SEED COMPLETE / AUTO-HANDOFF OFF** | Seed nghiêng về same-thread continuation khi thread healthy; còn thiếu representative real-task A/B samples. |
| P1 | Accepted-run cohort observability | **PASS** | Latest direct snapshot: `31/31` accepted runs có complete cohort dimensions. |
| P1.5 | Contract fingerprint + stale connector detection | **FULL LIVE PASS** | `smart-v3`, 8 tools, deterministic SHA live; connector mới đã nhận schema. |
| P1.5 | Permission unsupported status fallback | **FULL LIVE PASS** | `ELICITATION_UNSUPPORTED` là successful status report nhưng permission vẫn `granted=false`, `fail_closed=true`; task không bị `tool_failed`. |
| P1.5 | Electron-supervised restart from MCP | **FULL LIVE PASS** | One-shot restart ticket, expected disconnect, reconnect với new instance IDs đã chứng minh live nhiều lần. |
| P1.5 | Bounded candidate deep-symbol localization | **FULL LIVE PASS** | Deep query snippets nằm trong cùng 14k source budget, tối đa 4 deep reads; source đã được nạp vào runtime qua controlled restart. |
| P1.5 | Task/EOCL lifecycle terminalization | **FULL LIVE PASS** | `stop/clear/replacement` terminalize đúng exact linked nonterminal run thành `ABORTED`; `pause` giữ resumable; unrelated run không bị đụng. Live `PREFLIGHT → ABORTED` canary pass. |
| P1.6 | Execution Hub durable multi-client state | **SOURCE PASS / ACTIVATION PENDING** | Durable client registry, independent cursors, controller lease/fencing, online-only transfer; accepted backend proof `10 passed`. |
| P1.6 | Single-runtime Codex Desktop thin proxy | **SOURCE PASS / ACTIVATION PENDING** | Electron gateway giữ real bearer; Desktop stdio proxy không mở Runtime/ledger/workspace; session/protocol + descriptor rotation + idle heartbeat focused-proven. |
| P1.6 | Execution Control Center | **SOURCE PASS / ACTIVATION PENDING** | Panel hiển thị clients/cursors/controller/write authority/continuity/resume, task controls đi qua MCP EOCL, manual transfer + safe-rotate fail-closed. |
| P1.6 | Hub reconnect/fault gates | **PASS** | Same shared Runtime truth, cursor independence/controller fencing, durable task/run/capsule across Runtime recreation và old authenticated session alias reconnect; real `Server not initialized` defect đã được sửa. Final Hub Python fault set `18 passed`. |
| P2 | Routing calibration | **OBSERVABILITY READY / ACCEPTED EVIDENCE PENDING** | Latest accepted cohorts vẫn toàn `deterministic`; 2 Mini observations là blocked pre-fix attempts, không phải accepted Mini cohort. Thresholds giữ nguyên. |
| P2 | Auto-handoff policy | **EVIDENCE PENDING** | Cơ chế đã pass; auto-trigger chưa đủ representative A/B evidence. |

**Engineering conclusion:** P0/P1/P1.5 vẫn giữ trạng thái đã chứng minh. P1.6 Execution Hub đã qua source/fault proofs nhưng còn **live activation** vì Electron/runtime hiện đang chạy code trước Hub; cần full Electron restart, paste thin-proxy Codex config và real ChatWeb ⇄ Desktop canary. P2 routing và auto-handoff vẫn là evidence gates, không được ép đóng bằng synthetic workload.

---

## 2. P1 proof-cache live reuse — accepted evidence

### Exact miss → exact hit

First oracle miss:

- Run `16066fc1213f4547b3a9c8c45cd1239c`
- `pytest tests/test_proof_ledger.py` -> `1 passed`
- `cache_hit=false`
- duration `999 ms`
- input fp `3406a7d27b77c54c2570fcb2b59a123b68a449d0cf9d7209d2d782460ee97e90`
- proof `5c8ce2e19b804607871c9bb127d57bd0`

Exact reuse:

- Run `b609d40619fd4907847de66edfeb1396`
- `cache_hit=true`
- same input fp / same proof
- duration `0`
- `cache_saved_ms=999`
- durable `proof_cache_hit`

Relevant source canary changed source fp and forced real re-run:

- Run `6496bfac04de471087ad596fd8f47197`
- `cache_hit=false`
- duration `950 ms`
- input fp `1088256b6fa75e57aa5489fdc82eee45ac6d130a71bda0045715fab1bca77d70`
- proof `40e0dc1133ea45929132a87016f67c8f`
- false reuse `0`

Volatile `.coding-tools` state did not change source worktree fingerprint. Cleanup restored the source fingerprint exactly.

Current cumulative proof telemetry in latest snapshot:

```text
proof_cache_hits:     1
proof_cache_saved_ms: 999
```

Verdict: **PASS end-to-end**.

---

## 3. P1 handoff evidence

### Durable capsule

- Baseline run `b2bca65d7d454fae8e84c2fa63183fd1`
- Capsule `c4741192276b46ebbc31eaf324d43cd3`
- payload `2336 B`
- SHA-256 `67cab4ec4c4b0d06f8090a473f41bc88252302c0a738f8f4ae587809aa068ebd`
- record/get round-trip exact.

### Fresh isolated resume

- lane `UZMgLIaopTfPd8tt`
- model `gpt-5.4-mini`, low
- resume PASS, missing state none
- cache `14.54%`
- credits `0.191715`
- wall `7358 ms`

### Same-thread continuation control

- lane `QAIS85DBRk-x5k5L`
- continuation resume PASS, missing state none
- cache `87.95%`
- credits `0.072915`
- wall `6030 ms`

Incremental continuation vs fresh resume:

- khoảng `62%` lower credits;
- khoảng `18%` lower wall;
- `+73.41` percentage points cache.

Decision giữ nguyên:

```text
healthy thread -> continue same thread
rollover/recovery -> durable capsule
auto handoff -> OFF
```

Cần thêm representative real-task A/B samples trước khi auto-trigger.

---

## 4. Cohort observability v2

Accepted implementation:

- Run `88c37ce342e94f409db1d4c926ac0ca4`
- Wave `420d4d2c647a408284a453a227b325d1`
- Proof `249b9be5b7e14ece9739f36e432cd471`
- proof fp `239a81ae04d0546100985a2a6a9cfbc387065166c9d2531c60dfdff8f03f7002`
- focused oracle `3 passed in 0.58s`

Schema v2 derives only durable dimensions:

- entry surface;
- resolved route;
- task class;
- acceptance status;
- repair status;
- missing values stay `unknown`.

Historical validation report:

`resources/coding-tools-mcp/benchmarks/reports/runtime-activation-snapshot-20260814-092724.json`

At that point:

```text
accepted n:       25
coverage:         25/25 = 1.0
p50 TTA:          49.32 s
p90 TTA:          339.099 s
```

---

## 5. P1.5 contract, permission và restart — FULL LIVE PASS

### Contract fingerprint

Live contract:

```text
profile:        smart-v3
schema_version: 1
tool_count:     8
sha256:         4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
```

Fresh ChatWeb tool schema now includes `task_control.restart_runtime` and `confirm_restart`. Connector stale-schema blocker from the earlier session is closed.

### Source implementation acceptance

Main control-plane run:

- Run `c33493add833469a9517515f2c76833d`
- accepted wave `6e4a0b71d79547939911a3169927dbfe`
- proof fp `b3543b0ab1d9b16a7bb9fa6fe3610a9f02bd7283e93aac0e9cde5f885bb4f94a`
- EOCL `CHECKPOINTED`

Critical final review explicitly rejected an earlier green wave until:

- concurrent restart enqueue was serialized;
- Electron stopped using `.bak` recovery for one-shot restart tickets;
- regression tests covered both conditions.

### Permission unsupported-as-status

Follow-up semantics fix:

```text
ok=true
status=unsupported
grant_id=null
error.code=ELICITATION_UNSUPPORTED
fallback.mode=server_policy
fallback.granted=false
fallback.fail_closed=true
```

Accepted:

- Run `c6147b01947149559b918646975540e1`
- Wave `4ef17154c82d4f3eaa77519fb196c268`
- Proof `f12a432728df496daddccdcef775cc0c`
- proof fp `8add10e9c06502744ff8681f1e4c00a98e8adf39d24880d75d75dbef11e1536c`
- focused oracle `1 passed, 35 deselected in 0.49s`
- EOCL `CHECKPOINTED`

Live post-restart canary returned the same fail-closed status and `task_control get` showed `failure=null`; no `tool_failed` event was produced.

### Production restart canary

First full production canary:

- ticket `6HBpZeooJnG_SqxY`
- pre `s8PAY7Cu8wc0ED5N / ZHExCrNYoKQKbBiR`
- expected disconnect observed
- post `Mt7wkXwz8H9N3aUR / wKwXo5gzP8QLjNtZ`
- contract unchanged; stale/orphan counters 0.

This proves restart ownership is Electron supervisor, not MCP self-`taskkill`.

---

## 6. Candidate packet deep-symbol hardening — FULL LIVE PASS

### Real blocker

A useful permission-status bugfix attempted Mini twice. The second attempt had correct file path but `server.py` was too large: candidate source packet contained file head while target implementation was near line ~7840. Search knew the symbol but candidate did not receive enough local code.

One blocked real-model observation:

```text
model:          gpt-5.4-mini / low
wall:           ~5157 ms
input:          9281
cached:         1920
uncached:       7361
output:         174
reasoning:      92
credits:        0.161281
cache ratio:    ~20.69%
```

This is **blocked packet evidence**, not an accepted Mini failure.

### Fix

Current bounded constants:

```text
AGENT_CANDIDATE_PACKET_MAX_CHARS      = 14_000
AGENT_CANDIDATE_SNIPPET_BUDGET_CHARS = 6_000
AGENT_CANDIDATE_SNIPPET_MAX_CHARS    = 1_500
AGENT_CANDIDATE_SNIPPET_MAX_COUNT    = 4
AGENT_CANDIDATE_SNIPPET_RADIUS_LINES = 12
```

Rules:

- query-centered snippets are read only from normalized allowed paths;
- unique `(path,line)` matches only;
- max 4 deep reads;
- snippet bytes count against the same 14k source evidence budget;
- remaining budget is used for existing head-of-file slices;
- MCP remains the only writer/oracle owner;
- production routing thresholds unchanged.

Accepted source proof:

- Run `01f754053c014a5eac93dd7db29b8c9c`
- Wave `5ca5392b1ce44462a8a1a1d93043c579`
- Proof `163eb619f9954524aa7aa560f25f0fdb`
- proof fp `150056487a182ec9e1e70c32dab82df5b1283b69f469f0148baa14123893face`
- focused `2 passed, 35 deselected in 2.59s`
- EOCL `CHECKPOINTED`

Activation:

- restart ticket `4DyZDSywbwmlu2ve`
- expected disconnect observed;
- runtime reconnected with new instances;
- `smart-v3`, 8-tool count and contract SHA `4283e098…` stayed unchanged;
- no ChatGPT connector refresh was required because public schema did not change.

Verdict: **source + runtime activation PASS**.

---

## 7. Task/EOCL lifecycle leak — fixed and live-proven

### Finding

A fresh cohort snapshot showed many historical ledger rows with `status=active` while runtime reported `stale_orchestration_runs=0`.

This was not “46 stale runs”: stale reconciliation intentionally handles sufficiently old runs without live ownership. However, a bookkeeping gap was real:

- `task_control stop` changed only task projection;
- `clear` and `start` replacement could similarly leave the linked nonterminal EOCL run active;
- `pause` correctly needed to stay resumable.

### Safety invariant

The fix may terminalize **only** the exact `orchestration.run_id` stored in the current task projection. It must never use `current_active_run()` fallback and must never abort an unrelated run.

New behavior:

```text
stop        -> exact linked nonterminal run -> ABORTED
clear       -> exact linked nonterminal run -> ABORTED
start(new)  -> prior exact linked nonterminal run -> ABORTED
pause       -> run remains active/resumable
missing projected run -> no invented fallback
illegal transition -> typed ORCHESTRATION_ABORT_FAILED, fail closed
```

Accepted source implementation:

- Run `6898afecdcd24b2999d3fed05151f579`
- Wave `950cecefa99d49629bc73d6057a3fe57`
- Proof `85902dc7b8a04dcabe38ed829af0669d`
- proof fp `20a8af65700c9e70f9eb71988f75e88ad4ea05b65c4fd666e526ca3ce09ad56d`
- focused oracle `2 passed, 36 deselected in 1.62s`
- EOCL `CHECKPOINTED`

Adjacent review confirmed `TaskStateStore(new_task=True)` archives old state then resets `_default_state()`, so a new task cannot inherit an old ABORTED projection.

### Runtime activation

- restart ticket `LpsLTXHuu9HuGCj4`
- expected disconnect observed
- post-restart runtime:
  - process `xjxDaKSHw5ee5MqM`
  - server `snkgOI10Qm1wLy2W`
  - `smart-v3`
  - contract SHA unchanged `4283e098…`
  - stale/orphan/waiting counters `0`

### Live lifecycle canary

Read-only PREPARE run:

- Run `ed8b976f8ac747759306e7f6ebe42369`
- Wave `58eff3d677804773bf8120e19dae769a`
- initial state `PREFLIGHT`

Then `task_control stop` intentionally stopped it.

Live evidence:

```text
state transition: PREFLIGHT -> ABORTED
reason:           task_stopped
run status:       aborted
wave status:      aborted
run finished_at:  2026-08-14T04:21:21.726Z
wave finished_at: 2026-08-14T04:21:21.582Z
integrity:        green
```

Task projection emitted `task_orchestration_aborted` before `task_stopped` and showed `orchestration_state=ABORTED`.

Verdict: **future stop leak closed live**.

### Historical active backlog

The fix deliberately does **not** mass-rewrite historical active ledger rows. That would risk terminalizing legitimate historical state without provenance.

Latest direct snapshot shows:

```text
run_status_counts:
  aborted:  1
  accepted: 31
  active:   46
```

The active count was already `46` before this live canary; creating and then stopping the canary left it at `46` while adding `aborted=1`. This is strong evidence that new `stop` operations no longer grow the active-run leak.

Historical rows remain subject to normal stale reconciliation / explicit evidence-based maintenance, not bulk cleanup.

---

## 8. Latest direct production telemetry snapshot

To avoid creating another EOCL run merely to measure ledger counts, the latest benchmark was executed directly under a plain task rather than inside `agent_workflow`.

Report:

`resources/coding-tools-mcp/benchmarks/reports/runtime-activation-snapshot-20260814-112152.json`

Captured at `2026-08-14T04:21:52.465Z`.

### Performance

```text
schema_version:                    2
performance version:               3
tool_calls:                        341
errors:                            29
local_execution_ms:                465498
estimated_wait_ms:                 7006972
idempotency eligible:              203
idempotency keyed:                 83
idempotency coverage:              0.408867
proof_cache_hits:                  1
proof_cache_saved_ms:              999
route_resolved deterministic:      101
route_resolved mini:               2
```

`estimated_wait_ms` remains a runtime gap proxy, not pure model/network latency.

### Ledger / cohort coverage

```text
accepted runs:                     31
aborted runs:                      1
active historical rows:            46
accepted TTA n:                    31
accepted TTA p50:                  49.32 s
accepted TTA p90:                  339.099 s
cohort coverage:                   31/31 = 1.0
proof records:                     63
handoff capsules:                  1
```

Accepted cohorts in this snapshot:

| Task class | Repair | n | p50 s | p90 s |
|---|---|---:|---:|---:|
| bugfix | first_pass | 5 | 90.694 | 212.636 |
| bugfix | repaired | 2 | 141.959 | 143.154 |
| build_release | first_pass | 2 | 53.053 | 74.157 |
| custom | repaired | 1 | 57.870 | 57.870 |
| diagnose | first_pass | 7 | 31.799 | 339.099 |
| feature | first_pass | 9 | 31.105 | 580.301 |
| feature | repaired | 1 | 340.871 | 340.871 |
| refactor | first_pass | 3 | 49.320 | 15959.737 |
| test_failure | repaired | 1 | 265.667 | 265.667 |

**All accepted cohorts still resolve to `deterministic`.**

The two telemetry observations with route `mini` are the blocked pre-fix candidate attempts described in Section 6. They are not accepted Mini samples and must not be used to lower routing thresholds.

---

## 9. P2 routing calibration gate

Current gate:

```text
accepted cohort dimensions complete: YES (31/31)
accepted deterministic samples:      YES
real Mini calls observed:             YES, 2 blocked pre-fix attempts
accepted Mini representative:         NO
accepted Luna representative:         NO
accepted Sol representative:          NO
automatic threshold change:           BLOCKED
```

Interpretation:

- tooling blocker that prevented deep Mini localization is fixed and live;
- there is now no need for synthetic no-op tasks merely to increase `n`;
- future real bounded tasks that naturally match Mini/Luna should be allowed to produce evidence;
- compare only homogeneous accepted cohorts by task class, route, first-pass/repair status and oracle quality;
- track credits/accepted, first-pass accepted, repairs/accepted, critical defects and TTA with sample size;
- scenario harness remains `scenario_simulation_not_production_ab`.

**No production routing threshold was changed in this follow-up.**

---

## 10. Handoff evidence gate

Mechanism is healthy and one A/B seed exists. Remaining work is representative operational evidence only.

Required future sample fields:

- same-thread continuation credits/cache/TTA;
- fresh capsule-resume credits/cache/TTA;
- resume success;
- missing state;
- duplicate work;
- capsule/model-visible bytes when observable.

Current policy remains:

```text
healthy thread -> continue same thread
rollover/recovery -> durable capsule
auto handoff -> OFF
```

This is a deliberate evidence gate, not an unfinished implementation defect.

---

## 11. Documentation and test ergonomics

### README

`README.md` was synchronized with:

- smart-v3 8-tool contract/fingerprint;
- stale connector detection;
- EOCL/coordination/handoff/restart groups;
- Electron-supervised restart semantics;
- fail-closed permission unsupported status;
- deep candidate snippets;
- routing evidence policy;
- canonical root commands.

Document workflow result at that update:

- SHA-256 `32ae246c8efdabd9eb902ae9179067e98b89a052910a8e8dc23375f87451db52`
- 746 lines
- 29158 bytes.

### Root-level Python test command

Already present in `package.json`:

```text
npm run test:mcp
npm run test:all
```

`test:mcp` executes:

```text
cd resources/coding-tools-mcp && python -m pytest tests
```

No duplicate script was added.

---

## 12. Current delivery state

Source and evidence touched across this follow-up include:

- `README.md`
- `resources/coding-tools-mcp/benchmarks/runtime_activation.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/tests/test_efficiency_runtime.py`
- `resources/coding-tools-mcp/tests/test_runtime_activation.py`
- `resources/coding-tools-mcp/tests/test_task_state_and_build.py`
- `electron/paths.js`
- `electron/services/nativeService.js`
- `electron/services/runtimeOrchestrator.js`
- `electron/main.js`
- `electron/preload.js`
- `renderer/index.html`
- `renderer/app.js`
- `tests/runtime-lifecycle.test.js`
- this tracker
- generated orchestration reports / activation snapshots.

Unrelated and historical working-tree changes were preserved; no reset/restore/clean/rebase was performed.

Operations:

```text
commit:                         no
push:                           no
release:                        no
external deployment:            no
controlled service restarts:    yes, explicit P1.5/lifecycle activation canaries
ChatGPT connector refresh:      yes, earlier contract activation; verified live
additional connector refresh:   not needed for later internal fixes; contract SHA unchanged
production route threshold edit:no
auto-handoff enablement:        no
```

---

## 13. Exit criteria and next evidence phase

### Known implementation/activation blockers

**Closed.**

Current live runtime after latest lifecycle activation:

```text
process_instance_id = xjxDaKSHw5ee5MqM
server_instance_id  = snkgOI10Qm1wLy2W
profile             = smart-v3
tool_count          = 8
contract_sha256     = 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
stale_runs          = 0
orphaned_operations = 0
orphaned_idempotency= 0
waiting_after_restart = 0
```

### Remaining evidence-only gates

P2 routing decision becomes ready only when:

- representative **accepted** non-deterministic route samples exist;
- cohort dimensions are complete for samples used;
- cost/accepted + first-pass + repair + critical-defect + TTA agree without safety/quality regression;
- uncertainty from small `n` is explicit;
- scenario harness remains only a regression guard.

Auto-handoff becomes ready only when additional real-task A/B samples show stable benefit without state loss or duplicate work.

Until then:

```text
production routing thresholds -> unchanged
auto-handoff                  -> OFF
```

That remaining state is intentional scientific/evidence discipline rather than incomplete tool implementation.

---

## 14. Post-audit Traffic & Observability closure addendum

This addendum supersedes older statements in this tracker that imply the post-P1.6 operator surface or provider traffic-control source work is still absent. Historical chronology above remains unchanged.

Post-audit source closure completed on the current dirty worktree without changing the `smart-v3` 8-tool public contract:

- added runtime-scoped provider traffic admission for explicitly configured RPM/TPM/concurrency limits;
- unconfigured provider quota stays unknown/`observe_only`; invalid explicit configuration fails closed;
- manual OpenCode provider dispatch is governor-gated while automatic provider routing remains `OFF` / evidence-gated;
- OpenCode active/retained capacity and Codex model cooldown evidence are exposed through the authenticated Hub projection;
- existing EOCL ledger now provides bounded recent-run history, stable-cursor flight-recorder/delta projection and timestamp-derived phase timing without a second store;
- Hub run-history projection excludes objective/metadata/transcript and exposes only run id, status and lifecycle timestamps;
- Electron supervisor exposes typed local recovery counters/state already known to the process;
- Control Center / Live Routing renders provider traffic/capacity, automatic-routing gate, phase timing, flight-recorder evidence, sanitized run history, local recovery state and explicit `context_pressure=unknown / host_not_exposed`;
- no context percentage, provider quota, billing or model streaming state is fabricated;
- no remote unauthenticated status endpoint was introduced.

Configuration seam for provider limits:

```text
CODING_TOOLS_MCP_PROVIDER_LIMITS_JSON
```

Example shape (illustrative configuration syntax only, not a claim about real provider limits):

```json
{
  "opencode-go/deepseek-v4-flash": {
    "rpm": 10,
    "tpm": 50000,
    "concurrency": 2
  }
}
```

The numbers above are examples only. Production limits must come from real operator/provider configuration; leaving a field/provider unconfigured intentionally keeps it unknown.

Final current-worktree boundary verification:

```text
Node:             61/61 PASS
Python MCP:      228/228 PASS
Total:           289/289 PASS
git diff --check: PASS
```

The full-suite run also caught and closed two stale test-environment issues without weakening production behavior: the Node-only live-supervisor harness now isolates the one-shot supervisor restart-ticket path, and the runtime-activation oracle now expects the canonical PerformanceTrace v4 rather than historical v3.

Operations in this post-audit closure:

```text
paid provider call:     no
runtime restart:        no
connector refresh:      no
commit/push/release:    no
deployment:             no
route threshold change: no
auto-handoff enablement:no
```

Remaining gates are unchanged in kind: the post-fix paid Flash terminal repro requires explicit external-cost authorization; P-MP4 needs representative accepted cohorts before automatic route promotion; auto-handoff needs more real A/B evidence; ChatGPT context pressure remains unavailable until the host exposes it. Generic Composite Read / ArtifactRef / full ToolSpec convergence and a dedicated push transport remain optional benchmark-driven follow-ups rather than current source blockers.

---

## 15. PerformanceTrace v5 and accepted-result measurement follow-up

This addendum supersedes the current-state portions of Sections 13-14 that still identify PerformanceTrace v4 or the older `61 Node + 228 Python` boundary count. Earlier records remain historical evidence.

### Source status

- PerformanceTrace source schema advanced to `v5` with clean required/optional idempotency semantics, key provenance, structured error attribution and broader measured phase timing.
- The broad v4 eligible denominator remains historical. v5 decision coverage uses required replay-protection calls; optional side effects are reported separately rather than forced into automatic deduplication.
- Durable auto-keys are limited to `agent_workflow execute` and `task_control accept/reject`; accept/reject keys are scoped by caller client id and controller fencing epoch.
- EOCL accepted-result evidence now reports terminal TTA, observed/unattributed time and 90%/95% coverage gates. Provider queue/provider/total timing is overlapping evidence and is not double-counted.
- Electron Hub proxy source now records bounded resident loopback gateway `p50/p90/p99/max` by MCP/heartbeat/telemetry without persisting content or credentials.
- Python/Rust tool metadata now share a narrow risk-vocabulary/ownership seam while Smart-v3 remains 8 public tools and authority remains EOCL/permission/write-lease controlled.
- Runtime activation snapshot schema advanced to v3 and distinguishes v5 required coverage from legacy-v4 coverage.

### Regression and final proof

The first full Python boundary after introducing auto-derived accept/reject keys exposed one controller-transfer regression (`1 failed, 239 passed`). A denied stale ChatWeb caller had claimed the key later needed by Codex Desktop. Scoping the derived key by `client_id + fencing_token` closed the defect without weakening fencing or idempotency fail-closed semantics.

```text
focused regression: 10 / 10 PASS
Python MCP:         240 / 240 PASS (+3 subtests)
Node / Electron:     93 / 93 PASS
top-level total:    333 / 333 PASS
git diff --check:   PASS
source-root check:  PASS
```

### Activation/evidence boundary

No Runtime/Electron restart was performed for this source closure. Existing live telemetry is therefore still pre-v5/legacy until controlled activation. In particular, the historical `304 / 1291 = 23.5476%` value is the old broad denominator and must not be used to claim success or failure of the new required-v5 gate.

A clean post-activation PerformanceTrace-v5 epoch is required before claiming the methodology `>=95%` required-idempotency target or a live resident Hub percentile baseline. No historical data is synthetically reclassified into v5.

```text
post-fix paid Flash terminal repro -> PENDING explicit external-cost authorization
P-MP4 representative cohorts      -> PENDING real accepted work
Routing-v2 automatic dispatch      -> OFF / evidence-gated
deep automatic escalation          -> OFF / evidence-gated
auto-handoff                       -> OFF / evidence-gated
OpenCode authoritative direct write-> OFF by authority design
context pressure percentage        -> UNKNOWN / host_not_exposed
```

Operations in this follow-up:

```text
paid provider call:      no
runtime/Electron restart:no
connector refresh:       no
commit/push/release:     no
deployment:              no
route threshold change:  no
auto-handoff enablement: no
```

Remaining work is now primarily **controlled live activation plus representative evidence collection**, not missing source implementation for the performance/measurement issues closed here. Generic ArtifactRef/Composite Read expansion, semantic parallel proof scheduling, authenticated remote-phone status and a dedicated push transport remain benchmark/product-driven optional follow-ups unless future evidence promotes them.
