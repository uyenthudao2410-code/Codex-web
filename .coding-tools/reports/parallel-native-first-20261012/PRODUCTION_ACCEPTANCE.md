# Native-First và hai workspace — checkpoint nghiệm thu production

> **Cập nhật hiện hành — 13-10-2026 (UTC+07).** Phần này supersede trạng thái
> đầu tài liệu ngày 12-10-2026; các đoạn dated bên dưới vẫn được giữ làm
> chronology và không được dùng để phủ nhận receipt mới hơn.

## Kết luận checkpoint hiện hành

- Candidate Windows đang phục vụ là
  `dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked`;
  parity và packaged smoke đều pass. Production activation hiện hành đang
  `READY/OPEN`, MCP/native sống, Ubuntu service PID `970133`, MCP instance
  `7GYqt3ZdkU47_HIr`, Windows process instance `-s21-KH6ldxHjCSO`.
- Hai scope `Codex-web` và `Autocad` đều đã được khôi phục và kiểm tra với
  `execution_mode=native_first`; Autocad giữ nguyên ba action `UNKNOWN` và
  không replay/settle.
- Semantic acceptance độc lập đạt **20/20**, mỗi proof có run/wave/proof
  riêng, verifier pass, exit 0, không cache reuse và không patch replay.
- Live overlap đạt **2.078 ms** với hai native Job khác nhau; client reconnect
  chỉ ở transport và không redispatch. Task/writer của cả hai root đã đóng.
- Isolated idle proof đạt `ok=true`: Job terminal, record/daemon/host thuộc
  sandbox biến mất tự động; `vmmemWindowsSandbox` cuối kỳ bằng 0 sau 390.240 ms
  kể từ terminal. Không có lifecycle mutation hoặc generic process kill.
- Readiness Ubuntu sau restore đạt `ok=true`, node `ready`, service ổn định,
  SQLite integrity pass, Codex-web scope idle và AutoCAD chỉ còn ba
  `reconcile_required` UNKNOWN lịch sử. Aggregate đầy đủ nằm tại
  `canary/r4/production-evidence-aggregate-20261013-final3.json`.
- Checkpoint offline nối các lane, policy roundtrip, overlap, idle, readiness
  và quarantine hiện hành nằm tại
  `canary/r5/production-final-evidence-20261013-v3.json`; aggregate chi tiết
  nằm tại `canary/r5/production-completion-evidence-20261013.json`.
- Live post-activation verification confirms the Recovery Supervisor plus the
  Desktop and Start Menu shortcuts target the r4-timefix candidate; the named
  Sandbox process census is zero. Receipt:
  `production-post-shortcut-verification-20261013.json`.
- Packaged Phase A token canary completed one exact read-only native approval
  with exit 0, `process_container` isolation, no VM adapter calls, AppContainer,
  low-integrity RID 4096, non-elevated token, Administrator deny-only and zero
  enabled sensitive privileges. The exact Codex-web policy was restored to
  empty native prefixes and independently read back; Codex baseline hash is
  `f10114ea42142a48134e6432089b2af4c60be425e027848551b3e22ed4de2d58`,
  AutoCAD baseline hash is
  `0d42309ae640f768ba2c5e114822e3cd0d536a2dbab93d381850faf120c10782`.
  Receipts: `canary/r5/packaged-token-canary-694a79bfeef446559b3897cc052e723a.ndjson`,
  `canary/r5/packaged-token-packaged-token-restore-1791850043345-d884cf29.json`,
  and `canary/r5/packaged-token-restore-verify-20261013.json`.
- Phase B completed one real source Problem. Retained `.coding-tools` evidence
  had caused `AUTO_ACTIVATION_GIT_TOO_LARGE` before source identity evaluation;
  the rooted pathspec fix passed `node --test tests/accepted-code-activation.test.js`
  38/38 and behavior confirmation returned a source fingerprint. Receipt:
  `phase-b-real-problem-git-evidence-20261013.json`. This source patch is not
  packaged or loaded into the serving candidate. The tracked-sensitive guard
  `maxBuffer` change in `scripts/check-sensitive-tracked.js` has focused 4/4
  evidence. Phase C delivery staging and guard results remain pending.

### Bfix production gate — 13-10-2026

The rebuilt bfix candidate was rechecked with packaged parity and isolated
recovery smoke; both passed. It remains **not installed or activated**. A fresh
trusted bootstrap preflight returned `TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE`
because the current HEAD has no accepted `recovery_host` checkpoint. The
development full-clean preflight also returned
`RECOVERY_HOST_INSTALLATION_MISMATCH` because the authenticated owner is the
serving packaged r4-timefix installation. The exact read-only gate is recorded
in [bfix-production-activation-gate-20261013.json](bfix-production-activation-gate-20261013.json).
The r4-timefix process remains the only production-loaded candidate; no
supervisor, shortcut, process, epoch, policy, Ubuntu service, or AutoCAD
UNKNOWN action was changed in this wave.

### Giới hạn còn mở

- Receipt cha `native_first_shared_mcp_canary` giữ nguyên lỗi
  `ORIGINAL_JOB_IDENTITY_NOT_VERIFIED`. Báo cáo r5
  `native-first-continuation-evidence-join-20261013-v3.json` xác minh chuỗi
  cha → continuation → resume → readback bằng hash nguồn và cùng runtime,
  hoàn tất các lane 100/20/20 + 10 Node + 3 Git + build/readback mà không
  redispatch hay sửa receipt cũ.
- `connectorContractState=CHANGED_NEEDS_DISCOVERY` được phân loại
  `not_applicable_central_executor` trong receipt discovery r5; direct connector
  riêng vẫn cần discovery attested.
- .NET/AutoCAD build thực tế và toolchain dự án chưa được nghiệm thu; không
  cấp thêm native prefix hoặc chạy build AutoCAD khi ba UNKNOWN còn tồn tại.
- Network/path and required Job-limit dimensions not directly exercised by the
  token child remain locked to the existing isolated/deny boundary; no broad
  script/toolchain approval follows from this probe. CPython production loader
  compatibility cũng chưa đóng.
- Chưa commit, push, tag, publish installer/release hoặc deploy thêm trong
  checkpoint này. Production activation ở đây là candidate/runtime đang phục
  vụ, không phải phát hành artifact công khai. Source-only Phase B changes are
  not loaded in this candidate; the current operational runtime remains the
  r4-timefix package.

## Trạng thái của checkpoint

Ghi nhận activation hiện hành ngày **13-10-2026**, Git `main @
7999c4151cb501db86f2e4d0a2275d33fc248324`, worktree dirty có thay đổi đã tồn
tại. R5 đã nối các receipt parent/continuation/resume/finalizer và xác nhận
các lane chính của kế hoạch trên đúng binding Codex-web; semantic 20/20,
overlap hai root, idle teardown và readiness cũng đã có bằng chứng. Các phần
chưa đóng là giới hạn toolchain .NET/AutoCAD, child-token probe và ba UNKNOWN
AutoCAD được giữ nguyên. Native-first production cho File API/Git/Node đang
hoạt động. Không có commit, push hay published installer/release trong đợt này.

## Đối chiếu hai tài liệu người dùng cung cấp

Kế hoạch đầu tiên yêu cầu công việc coding thường ngày không mở VM: File API
cho đọc/ghi/patch; Git metadata và CLI được phép dùng native; build/script phải
được duyệt; mã chưa tin cậy dùng isolation; Job, writer lease, receipt và lịch
sử vẫn được giữ. Kế hoạch đó còn yêu cầu nghiệm thu toolchain, idle Sandbox,
reconnect, đổi workspace và rollback.

Tài liệu tham khảo tiếp theo nêu vấn đề chỉ một binding hiện ra và một vòng
điều phối có thể giữ các root khác chờ. Trên source hiện tại, giới hạn được
xử lý ở pilot authority, policy selector/store và node poll: authority thêm
theo exact scope; policy của nhiều root được giữ; poll luân phiên root, command
trả Job sớm và quan sát handle gốc. Thư mục chọn trong UI chỉ định task mới;
task đang chạy vẫn giữ root/generation ban đầu.

Root đã đối chiếu PR upstream chính thức: [PR 862](https://github.com/yyjeqhc/webcodex/pull/862)
về runtime performance/đường đọc có giới hạn,
[PR 863](https://github.com/yyjeqhc/webcodex/pull/863) về Windows recovery và
thêm folder qua kết nối hiện hữu, [PR 866](https://github.com/yyjeqhc/webcodex/pull/866)
về resource lifecycle/Windows Job Objects. Ba PR merged ngày 03-10-2026;
chúng hỗ trợ hướng sửa trực tiếp runtime và giữ contracts. Không xác minh
tuyên bố v0.4.6 là release mới nhất và không merge toàn bộ upstream main.
Bằng chứng nghiệm thu là implementation, focused tests, package và receipt của
chính Codex-web hiện tại. Không hợp nhất framework hoặc Job manager mới.

## Kết quả đã chứng minh

| Hạng mục | Mức bằng chứng hiện có | Phần còn lại |
|---|---|---|
| Đọc 100, exact PATCH 20 file | Receipt cha + r5 continuation chain: 100/20/20, task/writer terminal, hash nguồn liên kết | Parent harness vẫn giữ lỗi identity; không replay actions cũ |
| Git status/diff/log | 3 native Jobs riêng, bounded stderr policy, task/action/Job lineage | Không mở rộng sang global config mutation |
| 10 CLI native | 10 Node Jobs khác nhau, terminal và đủ metadata trong continuation | Không suy diễn sang .NET/AutoCAD toolchain |
| Build/script được duyệt | Node fixture tạo artifact đúng; chưa duyệt bị chặn trước spawn trong native-only | Toolchain dự án thực tế chưa nghiệm thu |
| Không mở VM cho metadata/quyền | Source router/bridge/UI và focused tests | Quan sát package đang phục vụ với canary |
| Hai root đồng thời | Pilot/policy exact scope; polling công bằng; hai live task/writer lease, File API đúng root, 2.078 ms Job overlap | Ba UNKNOWN AutoCAD vẫn giữ nguyên |
| Job/resource/boundary | Deny-path, network/loopback deny, host non-elevated, required limits trước resume, cancel/cleanup tests | Native child token inspection chưa chứng minh |
| Idle VM | Live VM tự đóng sau 390.240 ms, exact owner/generation, RAM cuối bằng 0 | Timer 30s còn chờ callback/lock; không coi đó là 30s end-to-end SLA |
| Reconnect | Client transport reconnect, không redispatch, hai Job distinct, task/writer terminal | Không suy diễn thành reconnect sau restart toàn host |
| Rollback/lịch sử | Isolate → native_first policy roundtrip theo exact Codex-web generation; package backup/source rollback và immutable history giữ nguyên | Binary service rollback vẫn là thao tác vận hành riêng nếu cần |

ProcessContainer là tiến trình hạn chế quyền, không phải hypervisor isolation.
Prefix mặc định là `[]`; quyền exec thư mục không tự cho phép script native.
Approval phải đúng workspace/generation và được giữ độc lập ở mỗi root.

Node/Git có process proof. CPython fixture hiện trả loader exit 126;
`.NET` và AutoCAD build chưa được chứng minh. `dotnet --version` cần approval
riêng vì SDK resolution có thể đọc `global.json` trong repository. Không cấp
prefix hay chạy build AutoCAD trong acceptance này. Không suy diễn khả năng
toolchain từ `node --version` hoặc probe MXC.

## Trạng thái triển khai ngoài repo

### Ubuntu đã deploy

- Đích: `svhome@100.116.112.22`, service `codex-control-plane.service`.
- Release: `codex-control-plane-parallel-native-1012-f7acd9ec4ba1`.
- Package source: `sha256:eb8c83abf44aca6c73ae5760813cda91d76187605cc53bbf1ae92cf6bb85f22d`.
- Health sau start: PID `970133`, service instance
  `cp_49af2c4d087147dfa64fecc067f97c19`.
- Database schema 29; facade schema 32/hash
  `3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66`;
  tám public tools giữ nguyên.
- Recovery fence đã revoke pilot cũ theo API hiện hữu; hai pilot mới được
  reissue với Codex-web trước, admission `scoped_pilot`, grant không đổi.
- Census sau deploy: không có live task/writer hay active action tại thời điểm
  quan sát. History rows được giữ, không restore database.

Xem [deployment receipt](server-deployment-receipt.json) và
[authority reissue receipt](authority-reissue-receipt.json). Ba Autocad UNKNOWN
đã có [quarantine disposition](quarantine-receipt.json) qua API được hỗ trợ.
Action/attempt/receipt gốc không đổi, không settle/replay. Hash lịch sử:
`b9ab0423d195427636b0c408dbb20fb9705283681f461b045db84c6bd2c3cea5`.

### Historical Windows r3 activation baseline — 12-10-2026

Candidate `parallel-native-1012-r3` có
[exact parity](../native-first-20261012/parallel-r3-candidate-parity.json):
90 application files, 299 resources, 10 adapters; ASAR
`3a7ad69df796379812463b19ba928c41fd8ad2f32d8fa142c656b0135d421cd6`.
[Isolated packaged Recovery smoke](../native-first-20261012/parallel-r3-packaged-smoke.json)
đạt với profile tạm. [Production status](../native-first-20261012/parallel-r3-transition/status-1791809052309-179002f3.json)
lúc **19:44:12 +07** xác nhận fullyReady/nativeAlive/mcpRunning/centralConnected
đều true, READY/OPEN epoch
`activation-mv58t4he-c162dd8a1c513c77581c5adee2ae6762`, ready commit
`fbd0fd5195b69788d847d2cb7ea06d91e57f2cc44eb17d924cca98193331f6f4`.
[Ubuntu readiness](server-readiness-r3-initial.json) xác nhận cả hai exact
roots active/ready/online/dispatchable, heartbeat mang epoch r3. Đây là
production activation; canary, semantic acceptance và strict rediscovery
là bằng chứng riêng. Readiness có `connectorContractState=CHANGED_NEEDS_DISCOVERY`;
không suy diễn rằng đã có current-process discovery receipt.

Live launch r2 phát hiện standalone `node_agent.py` không import được sibling
dưới Python `-I`, nên connected heartbeat không đạt. Execution lane đã sửa
direct-file branch bằng exact sibling loader, chặn bytecode trước import và
đạt real `-I --help`/policy-inspection tests. Windows r3 đã nạp fix này.
Source loader r3 SHA-256:
`bee27651ef1fba03f6f6c52dd1a93fe671f07d7b73b0402118ead88c97f9dffe`.

Ubuntu vẫn giữ package đã deploy; không cần alignment restart cho fix chỉ
dùng bởi Windows standalone launcher. [Source delta receipt](r3-server/windows-r3-source-delta-receipt.json)
đã kiểm tra bằng AST: package branch và mọi statement ngoài direct-file else
đều không đổi. HTTP launcher chạy `-B -m control_plane`; HTTP/renewal không
import node-agent. Actual serving node-agent hash vẫn là
`e368fd239446c8313c871dd41e4b35356e40bef83fff0bff80debff528f92f96`.
Canary phải pin serving hash riêng với Windows loader hash, không claim byte
parity hoặc deploy Ubuntu mới.

### Historical first canary failure — original receipt retained

[Original attempt `6bba02a734db47988da6042572f69497`](canary/shared-mcp-receipt-6bba02a734db47988da6042572f69497.ndjson)
kết thúc harness sau 923,682 giây: **66 File API reads có receipt**, chưa chạy
PATCH/readback, Node/Git Job hay build. `read_067`, action
`act_1de2cef3dc304d6e8b3f90237d7c136a`, có trạng thái
`reconcile_required`, execution `local_admission_pending_or_unverified`, chưa
settle. Task `task_cd3ea31140794fbcb5c598eb29cb9c90` chưa có bằng chứng
closure/writer release trong final receipt; cleanup được defer để giữ evidence.
Đây là failure tại boundary admission/settlement, không phải canary pass.
Root đang audit action và lease gốc; chưa xác nhận nguyên nhân hoặc replay.

Helper semantic acceptance đã chuẩn bị với sáu offline tests, nhưng không có
patch wave để nghiệm thu trong attempt này. Helper verifier chỉ được chuẩn bị
sau một full canary thành công, đúng 20 postimage/readback và task/writer đã
terminal. Idle pins constructor có ba offline tests, dùng actual policy/
readiness/current supervisor projection; đây chưa phải live idle proof. Xem
[semantic operator sequence](canary/SEMANTIC_OPERATOR_COMMANDS.md).

Ordinary stop r9e đã thực hiện một lần và owner cũ đã được retire qua census.
Receipt gốc và lỗi helper xác nhận stop vẫn giữ. Chuyển r1 gặp sanitation
blocker do bytecode cache trong package; không bỏ exact-resource guard để
cho qua. Candidate r2 đã được tạo để tiếp tục activation. Root controller
chịu trách nhiệm postflight và mọi production mutations.

## Bằng chứng kiểm tra source

- [Control Plane focused proof](../native-first-20261012/parallel-control-plane-validation.json):
  52 tests, facade hash/schema không đổi.
- [Execution workspace proof](execution-workspace-source-proof.json): 59 Python
  tests; corrected simultaneous-context suite 12/12. Một fixture ban đầu dùng
  cwd `.` bị existing contract từ chối, đã sửa cwd rỗng; giữ original failure.
- [Lifecycle source checkpoint](../native-first-20261012/parallel-lifecycle-source-checkpoint-1791806539525.json):
  142 JS tests và 3 deployment-boundary tests.
- [Exact server candidate validation](server-candidate-validation.json): 48
  tests với actual imports từ immutable candidate, không dùng nhầm source repo.
- Native-first source/process proof trước đó giữ ở
  [native-first evidence](../native-first-20261012/). Không cộng các lượt test
  trùng nhau thành tổng kiểm thử độc lập.

Baseline [read-only observation](../native-first-20261012/baseline-observation.json)
có cửa sổ **10:42:59 UTC**, cùng HEAD trên. Nó đọc canonical ledger qua
transaction, gồm 564 runs/899 waves, và ghi timestamp/hash của performance,
task-history, task-state. Canonical ledger là nguồn causal history; projections
là snapshot. Không đo VM cold-start hay peak RAM; census không VM chỉ chứng
minh tại thời điểm quan sát. Không dùng credit estimate làm hóa đơn provider
hay tuyên bố phần trăm RAM/latency giảm khi chưa có phép đo tương ứng.

## Bước tiếp theo tại checkpoint r3 — lịch sử

Danh sách này ghi kế hoạch tại checkpoint r3 ngày 12-10-2026. Các receipt r4/r5
và kết luận hiện hành ở đầu tài liệu supersede các bước đã hoàn thành; không
chạy lại canary hoặc settle UNKNOWN chỉ vì danh sách lịch sử này.

1. Giữ exact Windows r3 READY/OPEN và hai-root heartbeat đang phục vụ; pins
   canary bind đúng identities hiện hữu.
2. Kiểm tra policy native-first theo supported API cho hai exact root/generation;
   chỉ thêm native fixture approval hẹp phục vụ acceptance.
3. Audit/settle original `read_067` bằng supported evidence và terminalize task/
   writer gốc; sửa nguyên nhân đã xác minh, rồi chạy full canary mới đúng scope.
4. Chạy hai-root overlap canary, xác minh original Jobs có khoảng chạy giao
   nhau và File API/receipts giữ đúng root; giữ Autocad UNKNOWN lịch sử.
5. Thu live idle/reconnect evidence nếu cần để đóng đầy đủ các tiêu chí của
   kế hoạch đầu tiên; không gán các focused tests thành kết quả live.
6. Dọn fixture approval về mặc định hẹp sau proof, giữ hai root delegated;
   cập nhật shortcut và maintained docs bằng receipt mới.

Trạng thái tại checkpoint r3: **triển khai tiếp tục, full production acceptance
chưa được tuyên bố**. Trạng thái hiện hành ngày 13-10-2026 nằm ở đầu tài liệu;
receipt và các dated report cũ giữ vai trò chronology, không đổi observation
cũ thành kết quả mới.
