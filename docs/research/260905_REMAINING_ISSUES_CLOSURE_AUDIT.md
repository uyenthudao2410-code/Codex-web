# Kiểm tra tồn đọng và kế hoạch đóng hoàn thiện — 05/09/2026

> Phạm vi: `E:\DEV\Codex-web`, chương trình G0–G10. Cửa sổ quan sát chính: 2026-09-05 03:21–03:33 UTC (10:21–10:33 giờ Việt Nam).
> Git: `main @ 8697ace8204e7e3da55d250d4a52d9b2b930116c`, `origin/main` cùng HEAD; worktree có nhiều WIP đồng thời.
> Kết luận: **chưa hoàn thiện toàn bộ**. Nhiều lỗi source đã có focused proof, nhưng source mới chưa được final-accept và chưa có live closure. Activation hiện FAILED/CLOSED; dữ liệu Problem tự nhiên và usage/outcome chưa đủ.

> **Bổ sung tiếp trong ngày:** Mục 9 ghi nhận sáu font đã được xác minh trùng byte với artifact chính thức, license/notice đã bổ sung, hai lỗi tích hợp token-window đã sửa và hướng dẫn startup đã đồng bộ. Nhận định `UNPROVEN_ORIGIN` ở snapshot ban đầu được thay thế riêng cho sáu byte/hash đó; G0 và acceptance/live/package vẫn chưa đóng.

> **Đính chính đường phục hồi G0:** Mục 10 phân biệt accepted-checkpoint activation với explicit process refresh. `npm run dev:refresh` được triển khai là checkpoint-free; không cần chờ G2 acceptance hoặc dọn hết stale RUN để bắt đầu đường này. Các guard runtime và quyền thực hiện thao tác dịch vụ vẫn bắt buộc. Không dùng thứ tự ở mục 7 như một prerequisite bổ sung cho process refresh.

> **Refresh thành công nhưng sau đó mất runtime:** Mục 11 ghi nhận epoch READY/OPEN và Coding-VP đọc workspace thành công lúc 04:12 UTC. Đến lần kiểm tra khoảng 04:22 UTC, Recovery Host/UI/MCP/Tunnel của epoch đó đều không còn PID sống và client trả `tunnel_client_not_connected`. Receipt READY còn lưu là lịch sử, không phải bằng chứng liveness hiện tại. Mục 12 theo dõi phục hồi tiếp theo; chưa có strict rediscovery hoặc source acceptance.

> **Checkpoint mới nhất 04:47 UTC:** Mục 12.3–12.4 ghi nhận epoch thay thế READY/OPEN, UI/MCP current và supervisor healthy, đã duy trì qua hơn 13 phút kiểm tra sau READY. Mục 13 ghi nhận một test endpoint đã được thêm nhưng proof/REPLAN bị nền tảng chặn; chưa accept. G1 bulk inventory cũng bị chặn trước execution. Không yêu cầu người dùng xác nhận lại Send và không dùng đường khác để vượt kiểm tra an toàn.

> **Checkpoint tiếp nối 05:06 UTC (12:06 Việt Nam):** Mục 14 xác minh cùng host/UI/supervisor vẫn healthy sau hơn 32 phút và qua lượt goal mới, không restart thêm. Official event replay đã tìm thấy durable `patch_surface_observed` của test endpoint; lịch sử apply không bị mất, nhưng báo cáo partial failure thiếu danh sách file. Proof/acceptance vẫn chưa có. Đây là chẩn đoán mới, không phải retry hai payload đã bị nền tảng từ chối.

Đây là báo cáo quan sát có thời điểm, không phải canonical ledger, completion ACK, release receipt hoặc giấy phép bỏ qua activation gate. Mọi trạng thái runtime bên dưới phải được đọc đúng cửa sổ quan sát; không dùng lại identity/hash của census khi thực hiện thao tác mới.

## 1. Kết quả quan trọng nhất

1. Đã sửa các lỗi có oracle rõ ràng: line-budget, hợp đồng tools/list, measurement interim/final và bounded journal tail, revision ownership của token dashboard/font, cùng truthfulness/freshness của Dashboard và Control Center.
2. G0 không còn là chẩn đoán chung chung “tool chưa bật”. Coding-VP đã trả bootstrap tương thích; Recovery Host chuyển sang `UNCHANGED_COMPATIBLE_NEEDS_ACK`. Tuy nhiên final census có `ui_verified=false`, ACK chưa được thử, và epoch đã hết hạn thành `FAILED/CLOSED`.
3. Ledger census chỉ đọc ghi nhận integrity tốt, không có managed job/unbound resource/projection drift; vẫn có 12 ordinary RUN active nhưng không có ownership sống. Chỉ hai RUN đủ ngưỡng stale 24 giờ. Chưa reconcile RUN nào.
4. Có đúng một Problem Revision trong báo cáo PRL hiện tại, nhưng **không có mẫu nào có typed natural provenance**, chưa có independent outcome, và chưa chứng minh continuity thật qua hai ChatGPT product sessions.
5. G5 còn giới hạn transport thực: nguồn hiện hành khai báo chưa hỗ trợ post-turn controller usage transport. Ba chỉ số G8 cũng chưa có instrumentation/receipt. Chỉ tăng số Problem hoặc test không tự lấp được những khoảng trống này.

## 2. Các lỗi đã sửa và giới hạn bằng chứng

Tất cả các gói mới dưới đây vẫn là **dirty source / focused proof**, chưa phải EOCL accepted, loaded Electron, installer, release hoặc production. Không nhận toàn bộ diff hiện tại là do đợt này tạo: main/preload/CSS/HTML và các nguồn khác có WIP đồng thời đã được giữ nguyên ngoài phần sửa có giới hạn.

| Gói | Hành vi đã sửa | Oracle đã đạt |
|---|---|---|
| Context line-budget | Mặc định 2.000 dòng; opt-in tối đa 5.000; yêu cầu 2.500 materialize được 2.076 dòng; giữ byte cap và continuation accounting | Checkpoint trước: `test_task_state_and_build.py` 77 pass + 20 subtests; không chạy lại khi không có delta liên quan |
| Smart-v3 contract identity | Sửa current SHA mapping/expectation bị cũ; nguồn có đúng 8 public tools, SHA payload `6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf` | Hai test identity/bootstrap đích đều pass; đây không phải receipt rediscovery |
| Measurement + bounded live tail | Một measurement hiệu lực cho mỗi `(turn_id, trace_id)`; final thay interim, exact ưu tiên; thứ tự append xác định latest; đọc tối đa 256 KiB/400 dòng thay vì toàn file; bỏ fragment đang ghi; final record invalid trở thành unknown | `test_token_measurements.py`: 26 pass; journal JS checkpoint trước: 22 pass |
| Electron revision ownership | Token dashboard HTML thực sự được load nay thuộc `electron_ui`; `.woff2` thay đổi cũng đổi revision | `component-revision.test.js`: 11 pass |
| Dashboard numeric/freshness | Từ chối bool/blank/array/object/negative/nonfinite; giữ measured zero; thiếu cache/reasoning/cost là unknown; clear latest cũ khi receipt lỗi; animation không ghi đè unknown; rolling stale không hiện throughput current | Dashboard integration + VM behavior: 35 pass |
| Control Center runtime truthfulness | Thiếu/stale/invalid heartbeat là UNKNOWN/WARN; chỉ fresh explicit false mới hiện Stopped/OFF; timestamp/age lấy từ receipt; bound freshness tối đa 30 giây theo Recovery Host; failed snapshot/projection phát null thay vì dữ liệu cũ | Truthfulness + manager + signal failsafe: 25 pass |
| HTML/affordances | Bỏ số liệu demo, nhãn Production/ngày/thiết bị/live giả và các nút lọc/export/navigation chưa có hành vi; workspace ban đầu unknown; standalone tiêu thụ theme query | `token-dashboard.test.js`: 4 pass |

Đã kiểm tra syntax hai renderer JS và `git diff --check` theo phạm vi. Không chạy full workspace/Cargo/release suite: thay đổi đợt này không cần những oracle đó. Không dùng tổng số test làm phần trăm hoàn thành hệ thống.

Các file chính:

- [Dashboard](../../renderer/dashboard.js), [Control Center](../../renderer/control-center.js), [manager HTML](../../renderer/index.html), [token HTML](../../renderer/token-dashboard.html).
- [Component revision](../../electron/services/componentRevision.js), [measurement projector](../../resources/coding-tools-mcp/coding_tools_mcp/token_measurements.py), [tool contract](../../resources/coding-tools-mcp/coding_tools_mcp/tool_contract.py).
- [Dashboard behavioral proof](../../tests/dashboard-measurement-behavior.test.js), [Control Center behavioral proof](../../tests/control-center-truthfulness.test.js), [token page checks](../../tests/token-dashboard.test.js).

## 3. G0: nguyên nhân activation chưa đóng

### 3.1 Đường ChatGPT thường → Coding-VP Live

Đích hiện hành: [Kiểm tra kích hoạt runtime](https://chatgpt.com/c/6a9b602e-2d30-83ec-84bf-5a832cb38924).

Đã gửi một yêu cầu `workspace_context` và một lần retry đúng yêu cầu bootstrap của server, cùng `path=E:\DEV\Codex-web`, `detail=full`, `max_entries=40`. Không gửi command, ACK completion, workflow/control mutation hoặc thay đổi connector.

Cả hai trả:

```text
ok=true
workspace_accessed=false
completed=false
retryable=true
activation_bootstrap.accepted=true
activation_bootstrap.kind=connector_compatibility_bootstrap
activation_bootstrap.retry_required=true
activation_epoch_id=activation-mtntdmx3-9f6066997b3b91cc178bf6912aa6a8ce
```

Lần retry trả `task_context_id=ctx_8b499dba4cec34ab0a722fda7425a0fd`. Các trường workspace/branch/HEAD/worktree fingerprint, process/server, tool contract, semantic và quiescence không có trong envelope này. Không điền chúng từ snapshot khác rồi gọi là kết quả `workspace_context(full)`.

Bootstrap đã tới server, nhưng **workspace chưa được truy cập**. Các lần gọi có thể ghi transport/task-context/bootstrap observations theo cơ chế runtime; “read-only workspace” không đồng nghĩa không phát sinh bất kỳ transport state nào.

### 3.2 Receipt cục bộ sau bootstrap

`npm run dev:status`, runtime revision check tại `2026-09-05T03:29:59.932Z`:

| Trường | Giá trị |
|---|---|
| Electron UI | `STALE`, `update_pending=true`, PID `36000`, instance `5047488924923176f75afaef763a91d7` |
| UI running revision | `f37bb366df937188f5a0b0ca1bb24e02be49c5a62493ccd4b9915c2308b1f5dc` |
| UI disk revision tại receipt | `d2b70419a2a05f867fec434d595c76c5d73b1ed1a80fa7d97b0714168f6832d6` |
| MCP | `current`, running/disk `27d452a5fd6f34b5e710aed0016d4a9c549cf82dad44fe0308ab74742e085ef7` |
| Readiness | `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true` |
| Connector | `UNCHANGED_COMPATIBLE_NEEDS_ACK`, `connector_ack_pending=true` |
| Freshness | rediscovered `false`, rediscovered_at `none`, refresh_required `false`, compatibility_acknowledged_at `none` |
| Contract | current/acknowledged SHA đều `6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf` |
| Telemetry | available `true`, signal_stale `false`, source `recovery_host_supervision_cache` |

Source thay đổi sau receipt có thể tiếp tục thay disk revision; không dùng giá trị trên làm manifest cuối của gói sửa.

Đọc đúng `ActivationEpochStore.current()` với development paths của repository tại `2026-09-05T03:32:44.603Z`, không gọi mutate/enforce-expiry/finalize:

```text
epoch=activation-mtntdmx3-9f6066997b3b91cc178bf6912aa6a8ce
state=FAILED
admission_state=CLOSED
expired=true
last_final_census.pass=false
last_final_census.ui_verified=false
last_final_census.connector_acknowledgement.attempted=false
last_final_census.connector_acknowledgement.completed=false
last_final_census.connector_acknowledgement.error=null
connector_validation.reasons=[CONNECTOR_ACKNOWLEDGEMENT_PENDING, CONNECTOR_CONTRACT_STATE_INVALID]
process_instance_id=KPCoADkL97DX68Da
server_instance_id=jDxKEabE3KFL8OCS
host_instance_id=e1ed426c86f7f358be1d273d83329112
```

Trong census được lưu, workspace/device/MCP revision/Recovery Host revision/process identity/epoch/recovery plane/projection đều verified; projection validation `READY`, classification `ABORTED`. Đây là **last persisted activation census**, không thay thế một fresh live call hoặc lifecycle census mới.

Mã nguồn tại [fullCleanActivation.js](../../electron/services/fullCleanActivation.js) chỉ thử ACK sau khi toàn bộ component gates, bao gồm UI, đạt. [recoveryHost.js](../../electron/services/recoveryHost.js) giao việc final census → guarded ACK → finalize cho Recovery Host coordinator. Vì vậy UI gate không đạt giải thích được `attempted=false`; sau hết hạn, retry ChatGPT không thể tự mở admission. Không có bằng chứng rằng cần bật/tắt plugin lặp lại.

**Bước đóng G0:** ổn định source và exact acceptance packet; sau đó dùng supported controlled activation của Recovery Host cho đúng installation, lấy postflight mới và gọi lại Coding-VP. Epoch FAILED không được revive bằng một ACK mù hoặc thay identity thủ công. Compatible activation có thể hợp lệ với `connector_rediscovered=false` nếu receipt tương thích được guarded ACK; yêu cầu `STRICT_REDISCOVERED` vẫn là một gate riêng cần official current-process `tools/list`/`server/discover`.

## 4. G1/G2: source acceptance, font provenance và tracker

G2 Rust trước đó vẫn đóng đúng ba file Cargo/LSP, không mở rộng sang Electron/MCP/UI:

```text
RUN=03a0d2161bd8423c8368580706c2744c
WAVE=5cdb075e119f45aabdbb024bea78f513
CHECKPOINT=978f66e9c5c946b3a39df2d93e6201e5
proof_fingerprint=cad3b2a2f634a1b022fe9476ec57c2db6ac93b5f6655bdcec8203c787d0b8adb
state=accepted
```

Đã đối chiếu [generated run summary](../../.coding-tools/orchestration/reports/run-03a0d2161bd8423c8368580706c2744c/run-summary.md); không sửa report/ledger, không ACK lại gói này.

Các packet mới phải có exact preimage/current-byte manifest, focused proof và acceptance riêng. Đặc biệt gói Electron phải bao phủ main/preload/revision/HTML/JS/assets/tests có liên quan; không lấy acceptance ba file Rust để hợp thức hóa cả worktree dirty.

**Font còn mở:** sáu WOFF2 local vẫn `UNPROVEN_ORIGIN`. Font CSS tồn tại và package glob `renderer/**/*` sẽ phân phối chúng, nhưng chưa có acquisition receipt gắn immutable URL/version/build-subset parameters/SHA, chưa có mapping thông báo bản quyền và license phù hợp cho đúng local bytes. Test offline/existence/revision ownership không chứng minh provenance hoặc quyền phân phối. Không tự gán license từ tên font, không package/release trước khi có bằng chứng hoặc một phương án thay thế được kiểm chứng.

`tasks/todo.md` có các checkpoint UI lịch sử như “40/40”, “100%”, số token/cost và nhãn Production. Không dùng chúng làm hiện trạng hệ thống. Đợt này thêm chú thích phạm vi bằng chứng ở đầu tracker và giữ phần lịch sử/concurrent WIP bên dưới.

## 5. G3: census hiện tại và phần chưa reconcile

Official `report_lifecycle_census.py --workspace E:\DEV\Codex-web --stale-after-seconds 86400`, snapshot `2026-09-05T03:22:13.611Z`:

```text
physical_sha256=213f52ee734d70d6102eaa64f9598e3ac43a72857eabab7ba4d22fbb7c3b1e26
logical_sha256=34c850942532ca58803a9719de2c9a748ef9b8a1d1f1cf1666c2bfe74492cb1d
schema=12
backup_api_copy=true; immutable=true; query_only=true
integrity_check=[ok]; foreign_key_violations=0
mutated_canonical_ledger=false; canonical_writer_instantiated=false
ordinary_active_runs=12; retained_terminal_P5_anchors=6
projection_drift=false; managed_jobs=[]; unbound_live_resources=[]
unexplained_active_runs=0; stale_background_operation_residues=0
```

Hai exact RUN đủ ngưỡng 24 giờ và không có live ownership:

- `9fc19ad0412447d2b502acc347d8108f` — age khoảng 91.758 giây.
- `f33db8cd682741549704ad704f139284` — age khoảng 95.488 giây.

Mười RUN còn lại dưới ngưỡng; không bulk-clean hoặc terminalize trước hạn. Chưa reconcile trong đợt này. Muốn đóng G3 cần Recovery Host-owned stopped-writer receipt nếu primitive yêu cầu, immutable census **sau** stop, supported one-ID reconciliation, rồi postflight chain/integrity/FK/residue census. Không tái sử dụng hai hash trên cho một mutation sau này.

## 6. G4–G10: bảng tồn đọng và điều kiện đóng

| Gate | Hiện trạng đã xác minh | Điều kiện đóng / hành động kế tiếp |
|---|---|---|
| G4 semantic | Source hỗ trợ machine binding/provider; chưa có fresh live workspace result cho epoch hiện tại | Sau G0, xác minh provider đã load; chỉ dùng `agent_workflow(prepare)` trên task tự nhiên thực sự cần localization. Không semantic canary hoặc hidden native call |
| G5 host-turn/usage | `live_control.py` khai báo `post_turn_sideband.supported=false`, reason `no_supported_post_turn_controller_usage_transport`; ingress hiện hữu không chứng minh host đã gửi | Cần trusted host post-turn transport/receipt với server-owned turn/trace, exact RUN/Wave. Nếu ordinary ChatGPT không cung cấp, giữ unknown hoặc thu hẹp tiêu chí sản phẩm; không ước lượng thành billing |
| G6 một Problem qua hai session | Reporter: `INCOMPLETE`, 7 PASS / 3 INCOMPLETE / 9 UNAVAILABLE | Cần typed session A/B, intentional rotation, legal exact reattach, no duplicate start, reconstructed criteria/proof, closure falsifier và independent outcome/truthful reopen |
| G7 cohort tự nhiên | `COLLECTING`: 1 selected row nhưng 0 typed-natural rows, 0 real-cross-session pass rows | Thu thập 5–10 Problem tự nhiên từ start identity cố định; giữ cả failure; không backfill provenance từ objective/keyword |
| G8 economics | `DESCRIPTIVE_ONLY`; controller usage 0/3, complete money unavailable; 3 metric chưa có producer/receipt | Báo coverage/missingness, chỉ bổ sung instrumentation thật sự phục vụ quyết định; không suy chi phí hoặc nhân quả từ timing/bytes |
| G9 A/A → A/B | Chưa đủ natural evidence/readiness; study preparation không được mở | Preregister và A/A healthy trên baseline đúng identity trước khi cân nhắc A/B; không paid routing hoặc experiment để lấp checklist |
| G10 simplification | `tg10_manual_continuity_safety_gate=HOLD`; chưa chứng minh 5 safe real-cross-session rows | KEEP authority/evidence có vai trò riêng; MODIFY lỗi đã chứng minh; REMOVE affordance giả đã thực hiện. Quyết định policy rộng hơn chờ evidence, không xóa durable history |

### 6.1 PRL hiện tại, không lấy số lịch sử làm current

Reporter economics, cross-session và natural cohort đều chạy qua immutable SQLite Backup API; canonical writer không được khởi tạo. Exact identity đọc được từ PRL:

```text
problem_id=prl-b1fed3cdfd5203d9d9202643265865c3
revision=1
state=OPEN
exact_linked_runs=3; exact_linked_waves=7
accepted_runs=2; aborted_runs=1
independent_outcome_confirmations=0
controller_usage_observed_runs=0/3
natural_cohort.target_n=10
natural_cohort.selected_rows=1
natural_cohort.typed_natural_rows=0
natural_cohort.real_cross_session_pass_rows=0
natural_cohort.rows_skipped_after_start=0
```

Provider plane là `OBSERVED_ZERO` vì ba exact RUN không có provider delegation/usage event. Đây không chứng minh tổng ChatGPT token hoặc tổng tiền bằng 0. Controller plane và complete monetary cost vẫn unavailable.

Ba RUN có event chain/prewrite binding nhưng thiếu `typed_representative_natural_provenance_missing`; không tự đổi chúng thành mẫu tự nhiên. Ba reattach receipts/two opaque controller endpoints cũng không chứng minh hai ChatGPT product sessions.

G6 còn thiếu các gate: TG6-02, 05, 07, 08, 09, 10, 13, 14, 15, 16, 17, 18. Bảy gate đạt là 01, 03, 04, 06, 11, 12, 19. Fact-window không truncated. Hai reporter G6/G7 dùng 32 fact queries, một live Backup connection; không xuất physical/logical SHA, integrity/FK hoặc snapshot timestamp. Không gắn hash của lifecycle census sang các báo cáo đó.

### 6.2 Khoảng trống instrumentation phải phân loại riêng

- `problem_resolution_economics.py`: Framing Regret luôn `UNAVAILABLE` — chưa có availability clock của counterevidence và attribution của avoidable work.
- Cùng module: true sibling recurrence luôn `UNAVAILABLE` — chưa có explicit semantic sibling linkage; multiple RUN là proxy, không phải sibling proof.
- `natural_problem_cohort.py`: large-result continuation theo Problem luôn `UNAVAILABLE` — chưa có Problem-attributed receipt.

Không mở framework mới chỉ để đủ metric. Cần quyết định metric nào thực sự làm thay đổi KEEP/MODIFY/REMOVE rồi mới thêm producer nhỏ tại authority hiện hữu.

## 7. Thứ tự đóng tiếp và điều kiện dừng

1. Giữ source packet ổn định; review/accept đúng phạm vi, giải quyết font provenance trước Electron package acceptance. Không sửa source tiếp trong lúc một activation đang cố hội tụ revision.
2. Chọn supported Recovery Host activation cho installation development hiện tại sau khi source/authority đủ điều kiện. Epoch hiện FAILED nên không tiếp tục bằng `completeActivationEpoch` trên identity cũ. Cần receipt replacement/postflight mới; không kill/adopt process thủ công, không sửa admission/epoch file.
3. Lấy lại official Coding-VP workspace context. Nếu compatible bootstrap đóng hợp lệ, ghi `LIVE_COMPATIBLE`; chỉ ghi strict rediscovery khi có receipt strict thực.
4. Recapture G3 ownership/census; reconcile duy nhất exact candidate còn hợp lệ qua supported maintenance path.
5. Dùng một công việc tự nhiên cho semantic và cross-session; giữ source/test/acceptance tách khỏi independent user outcome. Không tạo synthetic Problem/cohort hoặc outcome.
6. Với giới hạn G5/G8, công khai unknown và thu hẹp feature/metric chưa thể chứng minh; chưa mở experiment/policy tự động.

Không có commit, stage, push, tag, package, publish, release, deploy, restart/stop service hoặc external-system mutation chủ động trong checkpoint này. Các thao tác ChatGPT giới hạn ở hai lời gọi workspace_context; các diagnostics/source tests cục bộ không được mô tả là Coding-VP execution proof. Không ACK completion report `cf5cefca8d2f505e507929f1c8e44143c4a94c2e744c39efa1141bc448eae70c`.

Git vẫn dirty trên HEAD đã nêu; không có unmerged path trong kiểm tra cuối đợt. Các worker source đã hoàn thành, không để lại test/job cục bộ chạy nền. Job canonical được báo theo thời điểm census, không suy từ trạng thái worker. Mục tiêu G0–G10 vẫn mở; báo cáo này không tự tạo acceptance trong ledger.

## 8. Current-byte inventory hỗ trợ review

SHA-256 đọc tại khoảng `2026-09-05T03:32:44Z`, sau khi các worker kết thúc. Đây là byte inventory, không phải accepted manifest. Cần chụp lại khi source thay đổi hoặc trước acceptance.

| File | SHA-256 |
|---|---|
| `electron/services/componentRevision.js` | `91464481561DAED4630AA004451E2B6C9BA00F09AEF526AB55BA38FEC9A85CD9` |
| `renderer/control-center.js` | `3570AA6E65F544030F9FC17A3D621E5BF3C6BF408ADFCFB8DA03F022D0BCDCD2` |
| `renderer/dashboard.js` | `93F1C68556FFFD3024AD8D67C7685C2893FD7DA1733B4AF3886834253393C4E1` |
| `renderer/index.html` | `984FBD06A68D47CAD1596E5DB2C7857B92E29FA0500D1644FC10C587A6C50FBA` |
| `renderer/token-dashboard.html` | `6BBCDCA0D70B50A60583C9C32BFB710E0A3894B7C1EE5AA0619289D1B5C85841` |
| `tests/control-center-truthfulness.test.js` | `65FA685FE4F6647B45B8F338EAD2428D8728E68E6C29D1B24C1453D182F1B42D` |
| `tests/dashboard-measurement-behavior.test.js` | `30E94DBF28473C551153CD19302426C5BA1C4681EFBA637F7775E137CB9FFF4E` |
| `tests/dashboard-analytics.test.js` | `E28441D3FFC06A4710DCCF8DF23E282B7891F8B0B4B1406440B3FA58511F4A27` |
| `tests/token-dashboard.test.js` | `FEE2F28F3B360637AE894E97BEBA00400724F1F7682AE7F6A029DD0F1435BE46` |
| `tests/component-revision.test.js` | `965FC32E72AB9283A0E1F99F891F7C9B09AC22B3953A5C0B1C4EEA95DA598FFF` |
| `resources/coding-tools-mcp/coding_tools_mcp/token_measurements.py` | `BA13589488B77A8D9F899E63F727C5703BE0A6BC0E8023603D36C575DF57F5D5` |
| `resources/coding-tools-mcp/tests/test_token_measurements.py` | `1DC3536F05CDAF2F4868E9AD0F7908E2DF73796BA863B4F44F512F2F83A1648A` |
| `resources/coding-tools-mcp/coding_tools_mcp/tool_contract.py` | `514AF3F68B9A725F13051F6549B46D18610512F203DE6DD4BF96AB18064E21BA` |
| `resources/coding-tools-mcp/tests/test_efficiency_runtime.py` | `B545E9491D82CD91B9F34DD7F973979894FF7EF03F295C59A9E22F8D633F6486` |

## 9. Bổ sung: đóng source provenance font và hai lỗi token-window

### 9.1 Font: đã có exact distributor receipt, không thay binary

Tại `2026-09-05T03:40:37.368Z`, cả sáu WOFF2 local được so byte trực tiếp và SHA-256 với các artifact HTTPS do CSS API chính thức của Google Fonts chọn: JetBrains Mono distributor path `v24`, Plus Jakarta Sans `v12`. Cả sáu `exact_byte_match=true`. Không ghi đè, chuyển đổi hoặc subset lại file font.

Metadata OpenType đọc tại local bằng FontTools 4.60.1 xác nhận JetBrains Mono version 2.211, weight axis 100–800; Plus Jakarta Sans version 2.071/gftools 0.9.30, axis 200–800. Name table chứa copyright của đúng upstream và URL OFL. Metadata upstream tương ứng tại [JetBrains Mono](https://github.com/google/fonts/blob/main/ofl/jetbrainsmono/METADATA.pb) và [Plus Jakarta Sans](https://github.com/google/fonts/blob/main/ofl/plusjakartasans/METADATA.pb) hỗ trợ attribution; **byte match với artifact thực**, không tên family, là bằng chứng nguồn phân phối của local bytes.

Đã bổ sung:

- [provenance.json](../../renderer/fonts/provenance.json): exact URL/size/hash từng file, verification time, font version/axis, immutable upstream license URLs/hashes.
- [JetBrainsMono-OFL.txt](../../renderer/fonts/JetBrainsMono-OFL.txt) và [PlusJakartaSans-OFL.txt](../../renderer/fonts/PlusJakartaSans-OFL.txt): full copyright, license, conditions/disclaimer; chỉ chuẩn hóa LF/trailing whitespace, có hash trước/sau chuẩn hóa.
- [font README](../../renderer/fonts/README.md) và [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md): attribution từng filename, phạm vi phân phối và giới hạn của receipt.
- `.gitattributes` trong thư mục font giữ hai license text ở LF để hash ổn định trên Windows checkout.
- [fonts.css](../../renderer/fonts.css): chỉ sửa ba declaration Plus Jakarta từ 100–800 thành 200–800 đúng axis thật. JetBrains giữ 100–800.
- [font-provenance.test.js](../../tests/font-provenance.test.js): kiểm tra đủ sáu file, magic WOFF2, size/hash, URL distributor, CSS weight/source, license/notice và package input coverage.

Original acquisition timestamp vẫn `null`; pipeline nội bộ của Google Fonts vẫn không được tái dựng. Receipt này chứng minh **exact distributed artifacts**, không giả vờ khôi phục lịch sử tải ban đầu hoặc reproducible upstream build. Hai OFL được lấy từ immutable upstream commits, không gán license chỉ từ family name. Font binaries vẫn nguyên hash khi kiểm tra lại sau sửa.

Vì vậy source provenance/notice gap của sáu font này đã được xử lý; acceptance gói Electron, built-package/installer và live activation vẫn cần bằng chứng riêng.

### 9.2 Token window: sửa lỗi tích hợp mà test cũ bỏ sót

1. Nút đóng gọi `window.api` không tồn tại, trong khi preload expose `window.mcpAssistant`. Đã sửa sang `mcpAssistant.closeTokenDashboard()` và fallback khi bridge thiếu, reject hoặc trả envelope lỗi `ok=false`.
2. Token page đăng ký heartbeat/watchdog nhưng main chỉ gửi event cho manager/chat. Đã thêm token window còn sống vào broadcast `runtime:heartbeat`, tránh watchdog của token page tự báo stale vì không được cấp heartbeat.

Behavioral VM tests nay thực thi inline handler và publisher thực, kiểm tra đúng bridge, fallback và live/destroyed token recipients. Không đổi preload/capability/security policy, không chạy Electron thật.

| File | Preimage SHA-256 | Postimage SHA-256 |
|---|---|---|
| `electron/main.js` | `D59CB01A1239981E4FF7AA82C317834FC8C6F12C36D7D7E8F05DE6F3DCB97BDA` | `ED2F76ACCEB3DC3D064EA7BB45DB70608D67A60DE6B79D2505F386D3D20E3125` |
| `renderer/token-dashboard.html` | `6BBCDCA0D70B50A60583C9C32BFB710E0A3894B7C1EE5AA0619289D1B5C85841` | `73433C5361FB588AA9A086A003200B9784C412DDFE99F3D588F3B3951E2DA955` |
| `tests/token-dashboard.test.js` | `FEE2F28F3B360637AE894E97BEBA00400724F1F7682AE7F6A029DD0F1435BE46` | `D91F6A73E9B296038C6A47A2667FEC643ABAD3B411FCB2D4AB2ACC2D16B34306` |

### 9.3 Hướng dẫn startup được sửa theo HEAD thực tế

Commit hiện tại đã chủ ý đổi package script `start` sang stable start/focus và có test guard tương ứng. Không đổi package/control flow để chạy theo tài liệu cũ.

| Lệnh hiện tại | Contract |
|---|---|
| `npm start` / `npm run dev` | Cùng start/focus lifecycle; UI stale chỉ activate qua authority hợp lệ |
| `npm run dev:refresh` | Explicit full-system refresh transaction |
| `npm run dev:status` | Đọc status |

Đã đồng bộ README, CURRENT_STATE, RECOVERY_HOST; sửa comment/error text trong nhánh refresh và tên ba mock tests. Giữ nguyên dated historical receipts. README cũng nêu đúng hai nhánh connector hợp lệ: strict discovery hoặc exact managed-attested admission-closed compatible bootstrap với guarded Recovery Host ACK. Compatible không được đổi tên thành strict rediscovery.

### 9.4 Proof và trạng thái sau bổ sung

```text
node --test tests/font-provenance.test.js tests/token-dashboard.test.js
10 passed, 0 failed

node --test --test-name-pattern='package start contract|dev focuses an exact current UI|dev:refresh refreshes the whole owned runtime' tests/dev-ui-lifecycle.test.js
3 passed, 0 failed (mock dependencies; không chạy startup/refresh thật)
```

Syntax checks và scoped diff checks đạt. Token HTML có một dòng whitespace-only cũ ngoài phần chỉnh sửa, được giữ nguyên cùng WIP đồng thời. Mục 8 là byte inventory trước bổ sung, không phải hash mới của main/token HTML/test.

Đọc lại ActivationEpochStore vào `2026-09-05T03:49:30.400Z` vẫn cho cùng epoch `activation-mtntdmx3-9f6066997b3b91cc178bf6912aa6a8ce`, `FAILED/CLOSED`, expired. Chưa gửi thêm retry ChatGPT không đổi điều kiện; chưa chạy restart/refresh, ACK, commit, package, push, release hoặc deployment. Không đổi canonical ledger để tạo acceptance. Công việc tiếp theo vẫn là exact source acceptance và supported controlled activation, rồi fresh Coding-VP/runtime/semantic/continuity evidence.

## 10. Đính chính G0: process refresh không cần source checkpoint

### 10.1 Bằng chứng làm thay đổi hành động kế tiếp

Đọc lại implementation và focused tests cho thấy hai authority khác nhau:

| Đường | Source checkpoint | Ý nghĩa |
|---|---|---|
| Code/revision activation | Bắt buộc exact accepted checkpoint | Kích hoạt source đã được chấp nhận theo receipt |
| Explicit `npm run dev:refresh` | Bắt buộc `null`; truyền checkpoint vào sẽ bị từ chối | Thay thế process của đúng installation qua Recovery Host, không tự accept source |

[dev-ui-lifecycle.js](../../scripts/dev-ui-lifecycle.js) gọi supported bootstrap với `sourceCheckpoint:null`, `refresh:true`, `forceRefresh:true`. [recoveryBootstrap.js](../../electron/services/recoveryBootstrap.js) từ chối checkpoint trên request refresh. [fullCleanActivation.js](../../electron/services/fullCleanActivation.js) chỉ áp dụng `requireCanonicalSourceCheckpoint` cho nhánh không phải refresh.

Vì vậy nhận định trước đó rằng phải hoàn tất exact source acceptance rồi mới có thể phục hồi epoch FAILED là **quá chặt đối với process refresh**. Không sửa implementation để lách gate; implementation hiện có đã phân biệt đúng hai thao tác. Việc load dirty bytes sau refresh, nếu thành công, vẫn không chứng minh EOCL acceptance, package/release hoặc outcome.

Epoch predecessor `FAILED` là terminal. Helper tạo operation ID mới; replay operation đã FAILED vẫn bị từ chối. Số `THRESHOLD_SENSITIVE_STALE_CANDIDATE` riêng lẻ cũng không phải blocker của explicit refresh. Live ownership, managed jobs, unbound/unexplained residue, projection drift và nonterminal P5 mới là các cổng phải kiểm tra. Không bulk-reconcile chỉ để giảm số RUN.

Focused proof mới trong lượt này:

```text
node --test --test-name-pattern='refresh bootstrap is checkpoint-free|explicit process refresh starts a full-clean epoch without inventing a source checkpoint|refresh ignores a predecessor FAILED epoch while locating the replacement operation|refresh still throws a FAILED epoch belonging to the requested replacement operation' tests/recovery-bootstrap.test.js tests/full-clean-activation.test.js tests/dev-ui-lifecycle.test.js
4 passed, 0 failed; duration_ms=285.5547
```

Các test dùng mock/temp fixtures, không chạy dịch vụ thật. Chúng chứng minh checkpoint-free refresh, từ chối checkpoint gắn vào refresh, chấp nhận predecessor FAILED khi đang tìm operation mới và không che lỗi của chính requested operation. Guard từ chối replay cùng operation FAILED được đọc trực tiếp tại `_restart`; không nói bốn test này đã exercise riêng nhánh replay đó.

Đường refresh sẽ kiểm tra lại authenticated descriptor/installation, exact process identity và start token, disk revision, canonical immutable census, quiescence và thay đổi epoch trước handoff. Pending acceptance chỉ được bảo toàn qua envelope refresh đã được validate, không được accept ngầm. Đây là **thao tác dịch vụ có ghi bootstrap/activation receipts và thay thế process**, không phải read-only workspace audit.

### 10.2 Hiện trạng được làm mới trước khi đề nghị vận hành

`ActivationEpochStore.current()` tại `2026-09-05T03:59:29.534Z`: cùng epoch `activation-mtntdmx3-9f6066997b3b91cc178bf6912aa6a8ce`, `FAILED/CLOSED`, expired.

`npm run dev:status`, MCP revision check tại `2026-09-05T04:01:12.868Z`:

```text
host=available; installation=current; mode=development
electron_ui=STALE; pid=36000
ui_instance=5047488924923176f75afaef763a91d7
ui_running_revision=f37bb366df937188f5a0b0ca1bb24e02be49c5a62493ccd4b9915c2308b1f5dc
ui_disk_revision=7ac5358c7704d9f3ad45e2d425c1f364ecae891a7f97769f9e5c22fa127ee7f8
coding_mcp=current; update_pending=false
mcp_running_and_disk_revision=27d452a5fd6f34b5e710aed0016d4a9c549cf82dad44fe0308ab74742e085ef7
components_ready=false; fully_ready=false; runtime_update_incomplete=true
telemetry_available=true; signal_stale=false; snapshot_age_ms=4474
connector=UNCHANGED_COMPATIBLE_NEEDS_ACK
connector_ack_pending=true; rediscovered=false; refresh_required=false
connector_current_and_ack_sha=6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf
```

Official read-only lifecycle census, snapshot `2026-09-05T04:02:31.071Z`:

```text
physical_sha256=2c58674fd562a2fe9143ae78b3f22addef71ddaf9df95348aa6fc0cb74360135
logical_sha256=4280dc9966d2c0b1b5585580ee18aafede766a387dcf241cf04aafe23498d693
schema=12; backup_api_copy=true; immutable=true; query_only=true
integrity_check=[ok]; foreign_key_check_rows=0
mutated_canonical_ledger=false; canonical_writer_instantiated=false
ordinary_active_runs=12; terminal_P5_anchors=6
all_observed_active_controller_leases=0; all_observed_active_write_fences=0
managed_jobs=[]; unbound_live_resources=[]; unexplained_active_runs=0
projection_drift=false; stale_background_operation_residues=0
```

Vẫn chỉ hai RUN `9fc19ad0412447d2b502acc347d8108f` và `f33db8cd682741549704ad704f139284` đủ ngưỡng 86.400 giây. Census này không phải stopped-writer receipt và không chứng minh toàn bộ live process quiescence; Recovery Host phải tự kiểm tra lại các guard tại action time. Không dùng hash trên để bỏ qua census mới sau stop.

### 10.3 Khoảng trống proof endpoint được khoanh đúng phạm vi

Read-only review đường `live_control` → HTTP → Electron IPC/preload không phát hiện việc đổi `null` thành zero hay drop projection. Reader lấy đúng ledger workspace và fail closed khi journal lỗi; nhánh admission-closed không đọc journal.

Tuy nhiên test live HTTP hiện tại trong [test_execution_hub.py](../../resources/coding-tools-mcp/tests/test_execution_hub.py) chưa assert `latest_turn_measurement`. Các test parser trước đây không thay thế proof của endpoint này. Gói test kế tiếp cần kiểm tra envelope exact-zero/unknown được giữ nguyên, exception thành unknown, và admission-closed không gọi reader; chưa thêm hoặc chạy test đó trong lượt audit này.

`latest_turn` hiện cũng không cung cấp observation timestamp hoặc exact `turn_id`/`trace_id`; không lấy schema identity hay snapshot timestamp làm G5 host-turn binding/freshness proof. Chưa có bằng chứng mới để đóng transport usage hoặc natural outcome.

### 10.4 Ranh giới tiếp tục

Hành động vận hành kế tiếp là một lần `npm run dev:refresh` trong `E:\DEV\Codex-web`, dùng official Recovery Host của development installation này. Nó có thể thay Recovery Host, Coding MCP/Tunnel và Electron UI đang được quản lý. Không phải quyền gửi ChatGPT; repository yêu cầu service operation được chỉ định rõ. Chưa thực hiện thao tác này trong lượt audit.

Sau khi có quyền cho đúng service operation: giữ source ổn định, để helper kiểm tra guard và tạo operation mới; theo dõi đúng operation/epoch đến postflight hoặc lỗi cụ thể; chỉ gửi lại official Coding-VP `workspace_context(full)` khi có trạng thái mới. Không ACK report cấm, không sửa epoch/ledger/projection bằng tay, không suy refresh thành source acceptance.

Lượt này không sửa product source, không tạo RUN/Wave/Problem/usage/outcome, không stage/commit/push/package/release/deploy hoặc restart/stop dịch vụ. Git vẫn `main @ 8697ace8204e7e3da55d250d4a52d9b2b930116c`, dirty WIP được giữ nguyên. Tiến bộ của lượt là sửa prerequisite G0 sai bằng implementation evidence và thu census/status mới; không tuyên bố G0–G10 đã đóng.

## 11. Official refresh đã hoàn tất; Coding-VP đã đọc lại workspace

### 11.1 Thao tác dịch vụ được người dùng cho phép

Người dùng xác nhận tiếp sau yêu cầu cụ thể cho một lần `npm run dev:refresh` tại `E:\DEV\Codex-web`. Đã chạy đúng lệnh này, không kill/adopt PID thủ công, không sửa bootstrap/epoch/ledger/projection. Source giữ ổn định trong suốt activation. Command session hoàn tất với exit code 0:

```text
operation_id=full-clean-refresh-mtnv7z3s-de6959b198228b7fec6efcba
activation_epoch_id=activation-mtnv8aer-521bd93de375bf1e6aae322f69cf3f5d
previous_host=e1ed426c86f7f358be1d273d83329112
replacement_host=e69ec6d39f4992dbb9c8b78b5cd466d1
replacement_ui=a3b2848b841b3b4f5448924bd706dcd4
replacement_mcp_pid=35844
replacement_tunnel_pid=31592
CLI postflight=REFRESHED; activation=VERIFYING; admission=closed
```

CLI postflight là process replacement, chưa được gọi là fully ready. Sau đó đã gửi một official Coding-VP `workspace_context` qua hội thoại ChatGPT hiện có. Lần đầu trả bootstrap tương thích của **epoch mới**, `workspace_accessed=false`, `retry_required=true`, task context `ctx_9d071deee5857ed40b92b662e5105429`.

Recovery Host tiếp tục hoàn tất việc xác minh/ACK theo đường hỗ trợ. Không trực tiếp gọi ACK. Persisted final receipt:

```text
state=READY; admission_state=OPEN
verification.verified=true
verification.verified_at=2026-09-05T04:12:39.840Z
final_census.pass=true; ui_verified=true
source_checkpoint=null
process_instance_id=q8QtIMKgna8Ou3PE
server_instance_id=9Z-Zpd1KwdUdTrLW
connector_validation.valid=true; code=READY; reasons=[]
freshness_mode=compatible_activation_bootstrap
compatibility_acknowledged_at=2026-09-05T04:12:34.233936+00:00
rediscovered_at=null
```

Final census cuối có `connector_acknowledgement.attempted=false/completed=false`: đó là trạng thái của lần census cuối khi contract đã được ACK, không được dùng để phủ nhận timestamp/validation hợp lệ trước đó hoặc nói controller đã trực tiếp ACK.

`npm run dev:status`, revision check `2026-09-05T04:12:42.003Z`, xác nhận:

| Thành phần | Bằng chứng hiện tại |
|---|---|
| Electron UI | CURRENT; PID 3824; instance `a3b2848b841b3b4f5448924bd706dcd4`; running=disk `7ac5358c7704d9f3ad45e2d425c1f364ecae891a7f97769f9e5c22fa127ee7f8`; update_pending=false |
| Coding MCP | current; running=disk `27d452a5fd6f34b5e710aed0016d4a9c549cf82dad44fe0308ab74742e085ef7`; update_pending=false |
| Aggregate | components_ready=true; fully_ready=true; runtime_update_incomplete=false |
| Connector | CURRENT_COMPATIBLE_ACKNOWLEDGED; ack_pending=false; refresh_required=false; rediscovered=false |
| Telemetry | available=true; signal_stale=false; supervision-cache age 3332 ms |

### 11.2 Official client result sau khi admission OPEN

Chỉ sau khi có READY/OPEN mới gửi một lần retry được server yêu cầu. Đã mở tool card gốc, không chỉ tin phần diễn giải của ChatGPT. Result `workspace_context(detail=full)` có:

```text
ok=true
workspace=E:\DEV\Codex-web
workspace_id=368dc8d57af2cd4d14bd248fa3488279d297cc0f6eacd8e76a8cf28617e0f251
workspace_generation=1
cache.hit=false; cache.age_ms=0
entries.count=32; entries_truncated=false
git.branch=main
git.head=8697ace8204e7e3da55d250d4a52d9b2b930116c
git.upstream=origin/main; ahead=0; behind=0; clean=false
git.entries.count=100; git.truncated=true
runtime.source.worktree_fp=88dab4a04cd7ec513c5daa34f3204f33b1cc0fa9a414a59aa027ddb780e87fbf
endpoint.activation_epoch_id=activation-mtnv8aer-521bd93de375bf1e6aae322f69cf3f5d
process_instance_id=q8QtIMKgna8Ou3PE
server_instance_id=9Z-Zpd1KwdUdTrLW
tool_contract.profile=smart-v3; tool_count=8
tool_contract.sha256=6420537a2150a7d8e0152eabde4b298c3c689645a4515ba17fd254d60fc43cdf
semantic_localization.available=true
semantic_localization.provider=webcodex_native_lsp
semantic_localization.read_only=true
agent_lanes_waiting_after_restart=0
orphaned_background_operations=0; orphaned_idempotency_records=0
stale_run_threshold_seconds=86400
stale_orchestration_runs=2; reconciled=0; unresolved=2
task=null; task_orchestration_projection_reconciled=false
```

Success envelope bình thường **không expose literal `workspace_accessed`**, cũng không expose admission hay connector freshness tuple. Vì vậy không ghi giả `workspace_accessed=true` như một field trả về. Khả năng đọc workspace được chứng minh trực tiếp bằng `ok=true`, entries/Git/project/current-process result không lấy từ cache; READY/OPEN và compatible freshness lấy từ **Recovery Host receipt riêng**, cùng epoch/process/server. Đây không phải result bootstrap còn đóng.

Git entries bị truncate ở 100: không dùng workspace_context để kết luận đã inventory đủ dirty paths cho G1. Semantic `available=true` chứng minh binding/provider được runtime công bố, chưa thay cho query tự nhiên thực sự qua prepare.

### 11.3 Phạm vi đã đóng và còn mở sau refresh

Đã gỡ blocker vận hành G0: process replacement được hỗ trợ, UI/MCP revision hội tụ, admission OPEN, official Coding-VP đọc workspace trở lại. Nhánh chứng minh là **LIVE_COMPATIBLE**, không phải STRICT_REDISCOVERED. Không bật/tắt lại tool hay sửa quyền connector.

G1/G2 vẫn cần full current-byte provenance và exact acceptance của các source packet mới; refresh checkpoint-free không cấp acceptance. G3 còn hai stale RUN chưa reconcile. G4 cần query tự nhiên; G5 cần host transport/evidence và endpoint proof; G6–G10 vẫn cần natural continuity/usage/outcome/cohort. Candidate endpoint test đã được chuẩn bị read-only, chưa áp dụng hoặc chạy.

Thao tác dịch vụ trong mục này **đã xảy ra** và tạo receipts theo cơ chế runtime; khác với các mục chỉ đọc trước. Không stage/commit/push/package/publish/release/deploy, không ACK completion report cấm, không tạo Problem hoặc usage/outcome giả. Product-source hashes được kiểm tra vẫn giữ nguyên so với trước refresh; báo cáo này không phải canonical acceptance.

## 12. Regression vận hành sau receipt READY

### 12.1 Hai lỗi phải phân biệt

Lệnh census đầu qua official Coding-VP dùng cú pháp đặt biến môi trường PowerShell trong command chạy bằng shell mặc định khác. Command `z1dXAdvYWHqdIaShTg_rznPx` kết thúc exit 1 với `The filename, directory name, or volume label syntax is incorrect.` Đây là lỗi định dạng command của controller; chưa chạy được census.

Một lần retry đã sửa thành `python -B resources/coding-tools-mcp/scripts/report_lifecycle_census.py --workspace E:\DEV\Codex-web --stale-after-seconds 86400`, kèm transport `workdir` và scoped context. Lần này kết thúc với HTTP 404, `tunnel_client_not_connected`: client không nhận được lần poll tiếp theo từ tunnel. Không có snapshot/hash/command-result để suy thành census thành công.

`npm run dev:status` sau đó trả `MISSING`, `RECOVERY_DESCRIPTOR_STALE`. Các PID Recovery Host 40420, UI 3824, MCP 35844 và Tunnel 31592 đều không tồn tại khi kiểm tra. Persisted epoch vẫn READY/OPEN, updated `2026-09-05T04:12:41.089Z`; không dùng trạng thái lưu này để phủ nhận kiểm tra liveness mới. Chưa có log exit/crash xác lập nguyên nhân gốc hoặc thời điểm chết chính xác. Windows parent-job lifetime mới là giả thuyết; riêng Job Object của Coding MCP không giải thích được lần refresh đã chạy qua local Codex exec.

### 12.2 Supervisor bị giữ suppression sau refresh

Read-only inspection xác minh Scheduled Task có sẵn `WebMCP Recovery Supervisor` ở cùng user, non-elevated; manifest khóa đúng development app root `E:\DEV\Codex-web`, executable Electron và SHA hợp lệ. Installed script/launcher trùng byte source. `stop.request` tồn tại với timestamp `2026-09-05T04:11:00.0912767Z`, trùng cửa sổ refresh; các lần scheduled Run thấy sentinel rồi ghi `stopping`, không kiểm tra/resurrect host. `recovery:supervisor:status` chỉ đọc, không phải nguyên nhân ghi trạng thái đó.

Đường hỗ trợ trong [RECOVERY_HOST.md](../RECOVERY_HOST.md) yêu cầu chạy `npm run recovery:supervisor:install` từ đúng checkout sau mutation/handoff để làm mới manifest/script và bỏ suppression. Đây là khôi phục supervisor đã cài cho cùng target, không phải sửa ledger, giả receipt, tắt job cleanup hay kill/adopt PID. Chưa coi việc tìm thấy đường này là bằng chứng runtime đã phục hồi; postflight phải xác minh host hiện tại và official client lại.

### 12.3 Phục hồi có postflight supervisor

Đã thực hiện supported `npm run recovery:supervisor:install`: exit 0, same-user Limited task Running; supervisor PID 45436 khởi động lúc `2026-09-05T04:30:06.5319921Z`. Sau đủ mẫu owner-dead, supervisor tạo Recovery Host PID 18732 / instance `d916494b8b0be5f7f8b54f5cda5c4688` và xác nhận authenticated healthy. Host phục hồi UI, nhưng MCP/Tunnel vẫn bị guard từ chối thay trong terminal activation epoch. Đây là trạng thái mới cụ thể yêu cầu một full-clean epoch mới, không phải lý do để sửa READY cũ bằng tay.

Đã chạy một `npm run dev:refresh` mới, exit 0, rồi **ngay sau postflight** chạy supported supervisor install để khôi phục suppression. Không chỉnh product source giữa hai bước:

```text
operation_id=full-clean-refresh-mtnvz3jg-1d0d177aae4ca366c592a82f
activation_epoch_id=activation-mtnvzch4-58f6924c524e8df372fec14615d09ec7
host_pid=16780; host_instance_id=f9129335d45a4c967789658815811a2e
ui_pid=3604; ui_instance_id=27ce6a9eaa49aa34e879c4ee529638d3
mcp_pid=47560; tunnel_pid=45380
process_instance_id=OFwZEdK7Z4525mgA
server_instance_id=o8_n8OoSNHVqeGPU
state=READY; admission_state=OPEN
verification.verified_at=2026-09-05T04:34:01.378Z
final_census.pass=true; ui_verified=true; recovery_plane_verified=true
connector_freshness_mode=compatible_activation_bootstrap
connector_compatibility_acknowledged_at=2026-09-05T04:33:56.297155+00:00
connector_rediscovered_at=null
```

Supervisor sau postflight: PID 38232, task Running, `healthy` qua authenticated ping lúc `2026-09-05T04:34:28.7763074Z`, exact host PID/instance như trên, không có error. Install là mutation có chủ đích: cập nhật installed script/VBS/manifest, đăng ký lại cùng task, bỏ marker và start; không phải status-only operation. Các thao tác không đổi account/destination/privilege, không cài phần mềm tải mới.

Official Coding-VP đã nhận đúng bootstrap của epoch mới và yêu cầu một retry; client cũng xác nhận public schema hiện có `agent_workflow.adopt_existing_files`. Chưa suy điều này thành adoption hay acceptance. Read-only workspace retry và census được gửi có điều kiện; chỉ coi census hoàn thành khi có tool result thật.

Khoảng trống source được khoanh lại: full refresh tạm suppress supervisor trước bootstrap nhưng không tự re-arm sau thành công. Không sửa bằng cách đơn thuần bỏ suppression hoặc truyền matching paths, vì cần giữ guard chống resurrection race trong handoff. Operational workaround ở trên theo tài liệu đã được thực hiện; source lifecycle fix/test còn là gói riêng. Nguyên nhân bốn PID ban đầu biến mất vẫn chưa được xác lập.

### 12.4 Official workspace/census thành công; inventory G1 bị chặn trước execution

Đã đối chiếu tool card gốc của official `exec_command`, không chỉ phần diễn giải. Workspace retry trả đúng epoch/process/server ở mục 12.3, cache miss/age 0, HEAD không đổi; source/worktree fingerprint của lần đọc `1edec83cbf13508cad446af0273ff0e44fe04e6c9717fecfb07bc6fe1702c9d6`.

```text
census_command_id=YrOljkirtsiqrNZXO4HLjgs3
status=exited; exit_code=0; elapsed_ms=5121; timed_out=false
stdout_output_bytes=19003; stdout_truncated=false; stderr=""
snapshot_at=2026-09-05T04:35:18.297Z
physical_sha256=a6b9684e7a364a9bf5c25941954862ae8897e9ed77b080507d5235f75f75b2ca
logical_sha256=155bea6432d6046785b07cdcecc189ec61b554b4feb06dee09da5a04f260c47a
schema=12; backup_api_copy=true; immutable=true; query_only=true
integrity_check=[ok]; foreign_key_check_rows=0
canonical_writer_instantiated=false; runtime_instantiated=false
ordinary_active_runs=12; P5_anchors=6; projection_drift=false
unexplained_active_runs=0; unbound_live_resource_residues=1
```

Không gọi snapshot này là quiescent: nó chứa một managed job đang chạy, ID `3fc0acfda2814b2db62d045c68434ca7`, root PID 44672, current checkout/exact identity, không có canonical RUN parent, tạo lúc `04:35:15.261Z` trong cửa sổ census. Điều này phù hợp tác động quan sát từ command transport, nhưng chưa có direct binding receipt trong output để xác lập riêng nó là census job. Sau command exit, kiểm tra OS lúc khoảng 04:39 UTC không còn PID 44672; không sửa/xóa resource để làm census sạch và không suy đó thành canonical terminal receipt của mọi job.

Hai RUN đủ stale threshold vẫn là `9fc19ad0412447d2b502acc347d8108f` và `f33db8cd682741549704ad704f139284`, mỗi RUN không có live controller lease/write fence/agent lane/job/background operation. Chưa có stopped-writer receipt hay exact reconcile; chưa terminalize RUN nào.

Đã gửi inventory G1 chỉ đọc qua official Coding-VP `exec_command(cmd="python -B -", stdin=...)`. Client báo `The tool call was blocked by OpenAI safety checks before execution. No command handle was created.` Không có command ID, exit code, JSONL hay trailer inventory; **G1 inventory không chạy và chưa hoàn tất**. Không đổi mã, shell, công cụ hoặc đường local để vượt chặn. Không dùng hash cũ/truncated workspace entries để giả lập output bị thiếu, không adopt/accept gói source trên cơ sở này.

Read-only postflight `2026-09-05T04:39:23.803Z` tiếp tục xác minh Electron và MCP running=disk, `components_ready=true`, `fully_ready=true`, `runtime_update_incomplete=false`. Supervisor authenticated healthy lúc `04:39:36.8369227Z`, vẫn exact host PID 16780/instance `f9129335d45a4c967789658815811a2e`, không có error. Đây là bằng chứng kéo dài qua nhiều lệnh đã kết thúc, chưa phải soak test dài hoặc chứng minh nguyên nhân death cũ đã được sửa.

Lượt phục hồi này chỉ chỉnh báo cáo nghiên cứu, không chỉnh product source; thao tác vận hành chính thức đã nêu rõ ở mục 12.3. Git vẫn dirty `main @ 8697ace8204e7e3da55d250d4a52d9b2b930116c`, không có unmerged path; không stage/commit/push/tag/package/publish/release/deploy, không ACK report cấm, không tạo RUN/Wave/Problem/adoption/acceptance/usage/outcome mới. Official command transport và activation vẫn ghi trace/receipt/projection theo cơ chế runtime của chúng; không tuyên bố toàn workspace không có runtime writes.

## 13. Gói test endpoint độc lập: patch có thật, proof chưa chạy

### 13.1 Phạm vi và lỗi sau apply

Sau khi G1 bulk inventory bị chặn, đã giữ nguyên blocker đó và thực hiện một task test-maintenance độc lập qua official Coding-VP `agent_workflow`, `mcp_only`/`deterministic`. Gói chỉ sửa [test_execution_hub.py](../../resources/coding-tools-mcp/tests/test_execution_hub.py), thêm 60 dòng cho `test_live_snapshot_transports_latest_turn_evidence_and_fails_closed`; fixture dùng temporary workspace, không phải usage/Problem/outcome tự nhiên.

```text
test_file_preimage_sha256=da91ef93172431ade406d98fb2fb22e3eebcabb22262aee297d7a5ec9f47f253
test_file_current_sha256=8e95f3b4463973dc940ccded798c674c69ab41f199f166eb1d2009d6375ca63f
diff=60 insertions, 0 deletions
RUN=4135fb1a2afd49c787a8fa7f0dd87cb0
WAVE=73b0f849954e4660beee87e99919650d
state=REPLAN
```

Test mô tả bốn trường hợp: exact-zero giữ nguyên; thiếu measurement giữ null/unknown; reader exception thành `chat_journal_unavailable`; admission-closed không gọi journal reader. Chưa được gọi các trường hợp này là passed.

Workflow đã apply patch rồi mới lỗi validation khi kiểm tra command `pytest ...py::ExecutionHubHTTPTests::...`. `_check_command_path_candidate` cố inspect toàn node selector như một Windows filename, trả `INVALID_ARGUMENT`, errno 22. Không có test process/proof chạy. Local current-byte và diff xác nhận source đã thay đổi; response thiếu patch result không được suy thành không có mutation.

### 13.2 Changed-strategy REPLAN bị nền tảng từ chối

Đã báo checkpoint REPLAN cho operator, đọc official scoped task state, giữ nguyên patch và gửi một continuation trên cùng RUN: no patch/files/directories, chỉ public existing-byte adoption đúng một test file và focused pytest `-k` trên filename hợp lệ. Đây không phải bulk inventory hoặc một đường thay thế cho request G1 bị chặn.

Client trả `agent_workflow=REFUSED_BY_OPENAI_SAFETY`, không có RUN/Wave continuation, adoption, proof hoặc completion report trả về cho lần gọi đó. Không chạy lại bằng terminal cục bộ, không đổi route để vượt chặn, không biến test chưa chạy thành PASS. Không có final acceptance.

Official `task_control(get)` cuối được đối chiếu tool card gốc, state updated `2026-09-05T04:47:25.843Z`:

```text
RUN=4135fb1a2afd49c787a8fa7f0dd87cb0
current_WAVE=73b0f849954e4660beee87e99919650d
orchestration_state=REPLAN; run_status=active; wave_status=active
task_status=waiting; current_command=null
write_lease_id=""; write_owner=""
active_command_count=0; active_claim_count=0; orphaned_count=0
quiescent=true
quiescence_scope=managed_processes_and_scheduling_claims
proof_count=0; proofs=[]; all_recorded_proofs_passed=false
completion_report_id=c527b311309f81cad72954a2568ecaf5d162babf3c434aaa53f4d0105f46b6b9
completion_report_acknowledged_at=null
accepted_or_not=NOT_ACCEPTED_REPLAN_REQUIRED
integrity.ok=true; integrity.checked=18
integrity.head_hash=7a96b505c47c390f647d207041212445d3af5c97b604dcf61837d8ffa15b1c22
```

Completion report `what_changed.files=[]`, source `no_durable_file_receipts`: đây là khoảng trống receipt sau partial workflow failure, không phủ nhận 60 dòng/hashes đã thấy trên disk. Không dùng Markdown này thay durable patch/adoption receipt. Report yêu cầu trình bày failure rồi REPLAN với evidence/scope/strategy thay đổi; hiện chưa thể thực thi continuation bị platform từ chối. Report mới này và report lịch sử bị cấm đều chưa được ACK.

### 13.3 Tình trạng bàn giao và bước tiếp theo

Postflight runtime lúc `2026-09-05T04:47:29.547Z`: UI/MCP running=disk, `fully_ready=true`, `update_incomplete=false`, connector `CURRENT_COMPATIBLE_ACKNOWLEDGED`. Supervisor healthy lúc `04:47:46.8991156Z`, exact host 16780 / `f9129335d45a4c967789658815811a2e`, không error. Đây là operational proof hiện tại, không phải strict tools/list rediscovery, acceptance, package hoặc soak test dài.

Git giữ nguyên `main @ 8697ace8204e7e3da55d250d4a52d9b2b930116c`; test diff không có whitespace errors. Toàn bộ WIP khác được giữ nguyên. Không có command/claim đang chạy ở scoped managed-resource checkpoint. Không stage/commit/push/tag/package/publish/release/deploy; không tạo natural Problem/cohort/usage/outcome. Một RUN/Wave test-maintenance đã được tạo như ghi ở mục này; khác với cửa sổ chỉ đọc ở mục 12.4.

Next action hợp lệ: xử lý platform refusal bằng cơ chế phê duyệt/hỗ trợ chính thức của client nếu được cung cấp; không cần thêm lời cấp toàn quyền Send, không tắt/bật connector hoặc đổi đường thực thi để né từ chối. Sau khi rào cản này thực sự thay đổi, recapture exact current task/report/file hash và tiếp tục đúng RUN bằng changed-strategy proof, không replay patch. G1 inventory vẫn phải hoàn thành riêng trước khi nhận các packet dirty khác; G3 cần stopped-writer receipt + census mới; G4–G10 giữ nguyên natural-evidence gates.

Candidate auto re-arm supervisor chưa được áp dụng: ngoài exact manifest, còn phải chứng minh sentinel thuộc đúng operation và không xóa một yêu cầu stop/uninstall mới hơn của operator. Vì chưa có proof cho race/ownership đó, không chấp nhận proposal chỉ match manifest rồi unlink marker. Workaround supported supervisor-install có postflight ở mục 12.3 là thao tác đã thực hiện; source lifecycle remediation vẫn mở.

## 14. Tiếp nối: runtime ổn định và xác lập nguyên nhân báo cáo partial failure

### 14.1 Không tái diễn mất runtime trong cửa sổ kiểm tra mới

`dev:status` lúc `2026-09-05T04:54:15.130Z` và `2026-09-05T05:06:36.242Z` tiếp tục trả UI/MCP `CURRENT`, running=disk, `fully_ready=true`, `runtime_update_incomplete=false`, telemetry fresh. UI giữ PID 3604 / instance `27ce6a9eaa49aa34e879c4ee529638d3`; component revisions giữ nguyên các giá trị ở mục 12.3–13.3. Supervisor lúc `05:06:56.9396522Z` vẫn PID 38232, authenticated healthy, exact host PID 16780 / instance `f9129335d45a4c967789658815811a2e`, zero consecutive failures, không có restart attempt hoặc suppression mới.

Đây là hơn 32 phút kể từ postflight READY, có kiểm tra sau khi lượt trước đã kết thúc và goal mới tiếp tục. Không thể kết luận runtime luôn chết khi một lượt Codex kết thúc; giả thuyết đó chưa có causal proof. Cũng chưa gọi khoảng quan sát này là long-duration soak/SLO hoặc bằng chứng nguyên nhân death cũ đã được sửa. Không thực hiện service operation nào trong lượt tiếp nối này.

Connector vẫn `CURRENT_COMPATIBLE_ACKNOWLEDGED`, `connector_rediscovered=false`, timestamp rediscovery thiếu, compatible ACK lúc `2026-09-05T04:33:56.297155+00:00`, `connector_refresh_required=false`. Giữ đúng phân biệt: operational access qua compatible activation đang hoạt động; strict discovery là claim riêng chưa có bằng chứng. Không tự thêm yêu cầu strict discovery vào đường compatible mà implementation và tài liệu hiện hành cho phép, cũng không gắn nhãn compatible thành strict.

### 14.2 Official replay xác nhận patch có durable observation

Đã gửi qua cuộc chat Coding-VP hiện có đúng một `task_control(action="events")`, scoped RUN `4135fb1a2afd49c787a8fa7f0dd87cb0`, context `ctx_9d071deee5857ed40b92b662e5105429`, `after_seq=0`, `limit=50`. Tool card gốc trả `ok=true`, 18 events, `has_more=false`, `next_after_seq=40342`. Client cursor cập nhật lúc `2026-09-05T05:03:36.911Z`; event read có cursor bookkeeping bình thường, không phải zero-state-write audit.

Tất cả sự kiện bên dưới thuộc WAVE `73b0f849954e4660beee87e99919650d`:

| Seq | Sự kiện / thời điểm UTC | Điều thực sự chứng minh |
|---|---|---|
| 40332 | `write_lease_acquired`, 04:43:16.903 | MCP có lease đúng một path `resources/coding-tools-mcp/tests/test_execution_hub.py` |
| 40334 | `patch_surface_observed`, 04:43:17.693 | Có applied-patch observation, 1 file, complete/content-free, additions 61, removals 1 |
| 40336 | `write_lease_revoked`, 04:43:18.263 | Lease `aef44cfdd3eb437b87f99bdfd04f877c` đã released trước proof |
| 40337–40338 | `PROVING` rồi `proof_cache_miss` | Bắt đầu đường proof, không phải proof thành công |
| 40340–40341 | `INVALID_ARGUMENT` rồi `REPLAN`, 04:43:19.390–19.625 | Execution cần changed-strategy recovery; không có test PASS |
| 40342 | `wave_processes_quiesced`, 04:43:19.896 | Có canonical quiescence event của wave; không suy thành census toàn bộ RUN |

Event 40334 có ID `554e610607884a5e884f12b3a1d82374`, event hash `5c6bf547fd0f4ddaec2a0cd5c4f3fd6a4e3be56b9bfd30389ac48ec1b66382fb`. `file_ids[0]=e7777b970c63aafb65c5e9128b59c339351d45c80ec47e5980a43e6bb6339bd5` khớp SHA-256 của **chuỗi path** đã nêu, được đối chiếu bằng đúng thuật toán `_path_identity` trong [solution_economics.py](../../resources/coding-tools-mcp/coding_tools_mcp/solution_economics.py). Đây không phải SHA của nội dung file hay accepted receipt. Số dòng trong patch operation là +61/-1; Git net diff hiện vẫn +60/-0. Hai đại lượng khác nhau, không được đổi một cái thành cái còn lại.

Kết luận được cập nhật hẹp: **không mất toàn bộ causal history của apply**. `what_changed.files=[]`/`no_durable_file_receipts` trong completion report là thiếu thông tin path ở projection/report, không phủ nhận applied patch. Event này không mang exact content-byte attestation, không tạo proof và không thay final acceptance/G1 inventory.

### 14.3 Nguyên nhân trong implementation và oracle cần bổ sung

Đối chiếu source hiện tại cho thấy chuỗi lỗi cụ thể:

1. [context_tools.py](../../resources/coding-tools-mcp/coding_tools_mcp/context_tools.py), `apply_changes_and_verify`, gọi `self.apply_patch` trực tiếp và ghi `record_patch_surface` ngay sau apply; chưa đưa `affected_files` vào task-state ở biên này.
2. Command được kiểm tra sau apply. [exec_tools.py](../../resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py), `_check_command_path_candidate`, inspect nguyên pytest node selector như filename và phát `INVALID_ARGUMENT` trên Windows.
3. Exception đi qua [workflow_tools.py](../../resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py) rồi structured error boundary của [server.py](../../resources/coding-tools-mcp/coding_tools_mcp/server.py). Response lỗi không còn chứa local `affected_files` của apply.
4. [task_state.py](../../resources/coding-tools-mcp/coding_tools_mcp/task_state.py), `record_tool_result`, chỉ ghi file từ workflow payload khi outer result `ok != false`. [operator_report.py](../../resources/coding-tools-mcp/coding_tools_mcp/operator_report.py), `_changed_files`, dùng accepted receipts hoặc aligned task `modified_files`, không dùng patch-surface observations để cảnh báo partial mutation.

Do đó có hai vấn đề khác nhau: parser path không hiểu selector pytest hợp lệ; và metadata file sau partial apply bị thiếu ở task/report. Không được sửa bằng cách bỏ path/security guard, giả receipt, suy accepted bytes từ hashed path, hoặc sửa task-state/ledger bằng tay.

Gói corrective tối thiểu cho lần thực thi hợp lệ tiếp theo phải giữ thông tin apply ngay khi apply thành công, phân biệt attempted/actually-applied/verified/accepted, và có focused fault-injection oracle: first patch succeeded rồi command validation raises; first patch succeeded rồi later patch fails; dry-run hoặc lỗi trước mutation không tạo changed-file claim. Phần này mới đạt **SOURCE_DIAGNOSED**, chưa có patch hay test chạy trong lượt này. Test nested-success hiện tại ở [test_task_state_and_build.py](../../resources/coding-tools-mcp/tests/test_task_state_and_build.py) không tự chứng minh đường exception sau apply.

### 14.4 Ranh giới đóng việc và bước kế tiếp

- Runtime resurrection đã được phục hồi bằng supported supervisor install và giữ healthy trong cửa sổ trên. Theo [RECOVERY_HOST.md](../RECOVERY_HOST.md), re-install sau development mutation/handoff là thao tác vận hành có chủ đích. Automatic re-arm là cải tiến riêng chưa triển khai, không phải prerequisite mới để công nhận runtime hiện tại đang sống. Không xây thêm machinery chỉ để làm thao tác này tự động; proposal xóa marker chỉ theo manifest vẫn không an toàn với yêu cầu stop mới hơn.
- Review đọc mã độc lập đã liệt kê marker writers/readers/deleters: Node suppression và PowerShell Uninstall cùng ghi marker timestamp-only; Install xóa marker; supervisor Run chỉ kiểm tra tồn tại và dừng. Mutex hiện có chỉ serialize các Run instance, không serialize Install/Uninstall/Node. Controller đối chiếu thêm [dev-ui-lifecycle.js](../../scripts/dev-ui-lifecycle.js): `refresh` gọi suppression không truyền expected app-root/executable, trong khi `ensureRecoveryHost` có truyền chúng. Vì vậy câu trong maintained docs nói chỉ suppress khi manifest mismatch không mô tả đầy đủ đường explicit full refresh. Cần làm rõ ngoại lệ này trong gói documentation kế tiếp; không tự sửa bằng cách truyền matching paths vì refresh hiện yêu cầu suppression thành công để chống resurrection race. Nhánh review không chỉnh source, chạy test hoặc thao tác service.
- Test endpoint giữ nguyên patch hiện có, chưa chạy proof, chưa accept. Hai platform refusals vẫn giữ nguyên; không retry hoặc đổi kênh để thực thi chúng. RUN còn `REPLAN` với last-verified zero active managed command/claim và không có write lease; không abort chỉ để làm sạch số đếm, không mở wave mới chỉ để chờ.
- G1/G2 cần inventory/proof/exact acceptance hợp lệ; G3 cần supported stopped-writer receipt rồi fresh census/reconcile đúng ID; G5–G10 cần trusted host usage và natural Problem/outcome thật. Bằng chứng mới ở mục 14 không đóng thay các gate đó.
- Nếu client vẫn từ chối inventory hoặc workflow continuation trước execution, bước tiếp theo phải là cơ chế phê duyệt/hỗ trợ chính thức của client. Không cần xin lại quyền Send của người dùng, không toggle connector và không dùng terminal thay thế để vượt chặn. Chỉ sau thay đổi thực của blocker mới recapture current RUN/report/source identity để tiếp tục, không replay patch.

Trong lượt này chỉ cập nhật báo cáo này; không sửa product source, không chạy lại test đã bị chặn, không sửa canonical evidence bằng tay, không ACK report, không stage/commit/push/tag/package/publish/release/deploy hoặc restart. Git vẫn dirty `main @ 8697ace8204e7e3da55d250d4a52d9b2b930116c`, không unmerged path. Không có natural Problem/cohort/usage/outcome được tạo.

### 14.5 Checkpoint cuối qua official Coding-VP

Sau khi gửi chẩn đoán cho controller trong cuộc chat, đã đọc `task_control(get)` đúng RUN một lần nữa và đối chiếu raw tool card: `state.updated_at=2026-09-05T05:03:36.506Z`, vẫn đúng RUN/WAVE ở mục 14.2, `REPLAN`, task waiting, write lease/owner rỗng và `current_command=null`. Resource snapshot có `active_command_count=0`, `active_claim_count=0`, `orphaned_count=0`, `quiescent=true` trong scope `managed_processes_and_scheduling_claims`; recovery có `orphaned_background_operations=0` và hai unresolved stale candidates. Không suy những số này thành G3 đã reconcile.

Proof count vẫn 0. Completion report vẫn `c527b311309f81cad72954a2568ecaf5d162babf3c434aaa53f4d0105f46b6b9`, `NOT_ACCEPTED_REPLAN_REQUIRED`, ACK timestamp null. Không có thêm execution/adoption/proof/ACK từ lượt này. Report Markdown đã kiểm tra 36 relative links, không broken link, không trailing whitespace; scoped test diff không có whitespace error. Mục tiêu toàn dự án tiếp tục **chưa hoàn thành**, không được đổi thành COMPLETE vì đã hết phần kiểm tra an toàn trong lượt này.
