# Native-First Hybrid Agent — triển khai Windows / Ubuntu Control Plane

## Checkpoint vận hành hiện hành — 13-10-2026

Candidate r4-timefix đang phục vụ production với activation epoch
`activation-mv5gbzeq-7ac98611bf3a96aa444fcf8e14d3ea1c`, Ubuntu node `ready` và
MCP/native runtime sống. Hai workspace `Codex-web` và `Autocad` đều dùng
`native_first` sau restore policy. Bằng chứng mới nhất nằm trong
`.coding-tools/reports/parallel-native-first-20261012/canary/r4/` và `r5/`:
checkpoint liên kết đầy đủ là
`canary/r5/production-final-evidence-20261013-v3.json`; aggregate chi tiết là
`canary/r5/production-completion-evidence-20261013.json`:

- linked continuation acceptance: 100 reads, 20 exact patches, 20 readbacks,
  10 distinct native Node Jobs, 3 Git Jobs, approved build and artifact
  readback, all bound to one workspace/generation/runtime identity chain;
- semantic acceptance: 20/20 proof wave độc lập, verifier pass, không replay;
- parallel overlap: 2.078 ms, hai native Job khác nhau, reconnect không
  redispatch, task/writer đã terminal;
- isolated idle: sandbox record/daemon/host và sandbox-named RAM aggregate tự
  biến mất, MCP/epoch không đổi;
- fresh Ubuntu readiness: service ổn định, Codex-web idle, ba AutoCAD
  `UNKNOWN` vẫn được bảo toàn.

Đây là bằng chứng activation/runtime của candidate. Receipt cha
`native_first_shared_mcp_canary` vẫn giữ lỗi harness ban đầu; báo cáo r5
`native-first-continuation-evidence-join-20261013-v3.json` nối receipt cha với
continuation/resume/finalizer bằng hash nguồn, Job/command/
handle riêng và cùng runtime identity, nên các lane nghiệp vụ đã đủ mà không
đổi lỗi lịch sử thành `ok=true`. Bounded source Runtime native-only token fixture
đã pass WinAPI queries (low integrity, non-elevated, administrator deny-only,
zero sensitive enabled privileges). Một probe read-only qua đúng packaged
r4-timefix policy cũng đã pass: Job native/process-container, exit 0, VM calls
0, AppContainer, low integrity RID 4096, không elevated và Administrator
deny-only. Exact Codex-web policy sau đó được restore về `native_first` với
`native_argv_prefixes=[]`; readback độc lập xác nhận Codex hash
`f10114...de2d58` và AutoCAD hash `0d4230...10782`, không có prefix. Hai lần
restore trước trả `TOKEN_POLICY_RESTORE_NOT_EXACT` do helper so sánh policy SHA
với raw scope hash; được giữ nguyên lịch sử và không tạo Job trùng. Network/path
và Job-limit dimensions không được token probe trực tiếp kiểm tra nên vẫn khóa
theo boundary isolated/deny hiện tại; không cấp broad script/toolchain approval.
.NET/AutoCAD build thật, connector direct discovery và publish/commit/release
vẫn là gate riêng.

Infrastructure closure Phase B đã hoàn tất một Coding Problem thật. Khối lượng
`.coding-tools` retained evidence từng khiến automatic activation dừng ở
`AUTO_ACTIVATION_GIT_TOO_LARGE` trước khi đọc source identity. Patch có guard
pathspec rooted loại `.coding-tools` trước bounded output/source-entry checks;
focused `node --test tests/accepted-code-activation.test.js` pass 38/38 và
behavior confirmation trả source fingerprint. Receipt:
`phase-b-real-problem-git-evidence-20261013.json`. Đây là source-only patch;
chưa rebuild hoặc nạp vào packaged production candidate. `scripts/check-sensitive-tracked.js`
cũng nâng `spawnSync` `maxBuffer` cho tracked evidence và focused guard đạt
4/4; baseline delivery guard vẫn là Phase C.

Live post-activation verification `production-post-shortcut-verification-20261013.json`
confirms the Recovery Supervisor, Desktop shortcut and Start Menu shortcut all
target the r4-timefix executable and working directory. The repair was guarded
against the previously observed r3 target and preserved shortcut metadata; the
named Sandbox process census is zero.

## Phạm vi

Đường thực thi có cấu trúc từ Ubuntu Control Plane giữ nguyên MCP facade
schema 32 và tám tool smart-v3. File API, writer lease, task/action/attempt,
Job và receipt hiện hữu tiếp tục là nguồn trạng thái. Không tạo patch engine
hoặc bộ quản lý Job thứ hai.

Backend native tái sử dụng **Microsoft MXC ProcessContainer đã pin**, yêu cầu
tier BaseContainer có deny-path và không dùng DACL fallback. Đây là tiến trình
Windows không mở VM. Máy không đáp ứng capability bị chặn; không chạy lại bằng
quyền host để né lỗi. ProcessContainer không tương đương ranh giới hypervisor
của [Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/).
[Tài liệu Microsoft MXC](https://github.com/microsoft/mxc/blob/v0.8.0/docs/process-container/os-version-support.md)
mô tả capability phụ thuộc bản Windows; runtime probe là căn cứ chọn backend.

## Hành vi được triển khai

| Thao tác | Đường mặc định |
|---|---|
| Read, write, exact PATCH, hash | File API hiện hữu; không VM |
| Git status/diff/log theo grammar metadata | Native ProcessContainer; không pager/fsmonitor/external diff/textconv/signature helper |
| Lệnh kiểm tra phiên bản được router chấp nhận | Native ProcessContainer |
| Build/test/script đã được chủ máy cấp native prefix riêng | Native ProcessContainer trong giới hạn quyền |
| Build/test/script chưa có native approval | Windows Sandbox trong `native_first`; từ chối trong `native_only` |
| Mọi lệnh ở `isolated` | Windows Sandbox |
| Backend không đủ capability hoặc giới hạn Job thất bại | Fail closed; không đổi sang quyền cao hơn |

Quyền đọc/ghi thư mục và `allowed_argv_prefixes` chỉ cho phép yêu cầu tới exec;
chúng không tự cấp quyền native cho mã dự án. Router kiểm tra độc lập grammar
metadata. Native prefix mặc định là `[]`. Prefix được cấp là quyền thực thi
thực sự cho toàn bộ phần argv tiếp theo; dùng prefix hẹp và workspace/generation
đúng. Shell không được dùng làm native prefix. Tham số route nội bộ chỉ do
bridge Electron đã attestation cung cấp; model không được tự chọn mức bảo vệ.

Phiên bản Git/Node/CPython có grammar tự động. `dotnet --version` cần native
approval riêng hoặc isolation: `global.json` có thể chọn SDK trong repository.
Đây là lựa chọn bảo thủ từ cơ chế
[SDK resolution của .NET](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json).

## Nhiều workspace trên cùng node

Codex-web và Autocad có thể giữ authority đồng thời. Mỗi pilot bind đúng
principal, binding, device, workspace và generation; thêm một root giữ quyền
của root khác. Thư mục được chọn trong UI là đích của task mới. Task, writer
lease, policy và command đang chạy tiếp tục dùng scope ban đầu.

Node poll lọc cặp workspace/generation trước LIMIT và luân phiên các scope
đủ quyền. Command bắt đầu với thời gian yield ngắn, các lượt quan sát dùng
Job/handle gốc và không chờ toàn bộ lệnh kết thúc. Nhờ đó một command dài ở
root này không giữ vòng poll của root kia. Focused tests đã kiểm tra hai
request cùng bắt đầu, approvals riêng và Jobs khác nhau. Receipt r4-timefix đã
chứng minh live overlap hai root với hai native Job riêng, đúng task/writer
scope và không redispatch khi client reconnect.

UNKNOWN chặn phạm vi liên quan, giữ kiểm tra generation và lịch sử root đã
retired. Quarantine hợp lệ thêm disposition có audit; không biến UNKNOWN
thành kết quả thành công, không xóa receipt và không chạy lại tác vụ chưa rõ
hiệu ứng. Approval native của một root không dùng được ở root còn lại.

## Cấu hình và rollback

Giao diện thư mục có ba lựa chọn: **Tự động có kiểm soát · Native trước**,
**Chỉ native có kiểm soát · Không mở VM**, **Ưu tiên cách ly · Windows Sandbox**.
Việc cài/thay policy vẫn cần xác nhận chủ máy và bind đúng workspace generation.
Đọc metadata/quyền và chuyển workspace không chạy lệnh kiểm tra trong VM.
Kiểm tra capability native chỉ chạy `wxc-exec --experimental --probe`.
Chẩn đoán Windows Sandbox là thao tác riêng, rõ ràng.

Policy local schema 2 thêm hai trường tùy chọn:

```json
{
  "execution_mode": "native_first",
  "native_argv_prefixes": []
}
```

Node agent `install-exec-policy` hỗ trợ `--execution-mode` và lặp lại
`--native-argv-prefix` với mỗi giá trị là JSON argv array. Các trường identity,
authority, facade hash, allowlist, giới hạn và cờ xác nhận hiện hữu vẫn bắt buộc.
Policy cũ giữ fingerprint cũ khi không có trường mới; mode hiệu lực mặc định
là `native_first`. Prefix native không chuyển giữa workspace/generation.

Khi chỉ có một scope, file policy giữ object gốc. Nhiều scope dùng envelope
`{"schema_version":1,"policies":[...]}`; mỗi phần tử giữ schema của lane đó.
Reader phải chọn đúng workspace/generation, không đoán phần tử đầu tiên.
Cài policy dùng merge atomic có lock để giữ các scope đã tồn tại.

Rollback lựa chọn runner: cài lại policy cho **chính workspace/generation** với
`execution_mode=isolated`, giữ backend Sandbox và lịch sử hiện hữu. Rollback
binary: giữ package trước đó, chỉ đổi candidate theo quy trình activation
hiện hữu sau khi census Job/task/receipt xác nhận quiescence. Không reset ledger,
không xóa UNKNOWN hoặc awaiting-acceptance để đạt trạng thái xanh.

## Giới hạn và audit

Native runner dùng argv, môi trường tối thiểu, workspace write grant và toolchain
read grant đã kiểm tra. Mạng/loopback bị chặn, không truyền credential của host.
Host có token elevated hoặc integrity cao hơn medium bị từ chối; không đọc được
token posture cũng fail closed. Fixture CPython riêng vẫn thoát ở loader exit
126 trước khi truy vấn token, nhưng probe Node qua đúng packaged r4-timefix đã
quan sát child AppContainer, low-integrity, non-elevated và Administrator
deny-only. Bằng chứng packaged đó chỉ áp dụng cho một argv read-only cụ thể;
không mở rộng thành quyền native cho toolchain khác. Không bật thuộc tính LPAC
không tương thích để gán nhãn bảo mật mà runtime không thực thi.
Job Object được cài trước khi tiến trình suspended được resume: tổng RAM 2 GiB,
tối đa 64 tiến trình, CPU hard cap 50%, CPU time theo timeout. Không cài được
đủ giới hạn thì tiến trình không được resume. Thời hạn wall-clock và process-tree
cleanup dùng cơ chế Job/session hiện hữu.

Receipt thêm ba trường cùng hash: `execution_backend`, `isolation_level`,
`policy_decision`. Native có `native/process_container`; isolated có
`isolated/hypervisor`. Metadata thiếu một phần, sai tổ hợp, đổi hoặc mất trong
recovery bị từ chối/UNKNOWN; không tự spawn lại. Receipt cũ không có metadata
vẫn dùng hash cũ. Public schema/descriptions/input không đổi.

Sandbox chỉ giữ một VM cho đúng root/toolchain. Sau khi lệnh kết thúc, scratch
đã cleanup và Job terminal đã ghi, timer rảnh 30 giây đóng **sandbox ID do manager
sở hữu**. Acquire mới hủy timer; generation bảo vệ trước callback/receipt cũ.
Không đóng VM của ứng dụng khác. Teardown không xác minh được sẽ chặn execution
tiếp theo. Giao diện không suy diễn RAM VM từ trạng thái policy; khi chưa có số
đo trực tiếp, hiển thị chưa có dữ liệu.

## Kiểm chứng và nghiệm thu

Bằng chứng của đợt này nằm trong
[`native-first-20261012`](../.coding-tools/reports/native-first-20261012/).
Baseline đọc canonical ledger trong transaction read-only, ghi HEAD, thời điểm,
aggregate performance và census tiến trình. Không sửa projection runtime hay
coi credit estimate là hóa đơn provider.

Source tests, Job thực tế trong workspace tạm, package parity và canary hệ thống
đang vận hành là các mức chứng minh riêng. `node --version` chạy 10 lần không
chứng minh đủ Node/Python/.NET/AutoCAD build compatibility. File fixture không
chứng minh canary thật từ ChatGPT tới Ubuntu và Windows. Cần nghiệm thu live
đúng binding `Codex-web` trước, sau đó nghiệm thu chồng thời gian trên hai root.
Giữ task/writer lease của mỗi root theo đúng scope; không chuyển authority
của root đầu tiên để kiểm tra root thứ hai.

Fixture CPython native hiện có trả loader exit 126 trước khi truy vấn token;
capability ProcessContainer không chứng minh mọi bản Python chạy được. Bằng chứng
source Runtime native-only nằm ở `canary/r5/token-child-native-fixture-20261013.json`;
nó không phải live packaged receipt và không cấp thêm native prefix. Node và
Git có bằng chứng tiến trình thực tế; .NET/AutoCAD toolchain cần nghiệm thu riêng
trước khi cấp prefix build/test native.

### Ma trận nghiệm thu của đợt triển khai

| Tiêu chí | Bằng chứng hiện hành | Giới hạn |
|---|---|---|
| Đọc 100 / exact PATCH 20 file, không VM | R4 receipts + r5 immutable chain: 100 đọc, 20 patch/readback; semantic 20/20 | Failed parent harness vẫn là chronology; không redispatch |
| Git metadata, không VM/global config mutation | Git status/diff/log có 3 native Jobs; grammar không cho config mutation; hostile helper tests đạt | Chỉ các shape metadata đã cấp quyền |
| 10 CLI có đủ receipt | 10 Node Jobs/command/handle khác nhau, cùng task/action/attempt/runtime chain | Không suy diễn sang mọi CLI |
| Build/test được duyệt | Approved native Node build có artifact/readback hash đúng; chưa duyệt bị chặn trước spawn | Toolchain .NET/AutoCAD chưa chuyển sang native |
| Cách ly mã chưa tin cậy | Router/path/network tests và isolated terminal Job trên package đang phục vụ | Native ProcessContainer không tương đương hypervisor |
| VM rảnh dừng an toàn | Owned record/daemon/host tự biến mất; sandbox-named RAM cuối 0 | 390.240 ms sau terminal; không có teardown receipt riêng |
| Reconnect/recovery | Client transport reconnect trong overlap, không redispatch | Chưa đo host restart giữa Job |
| Chuyển workspace/rollback | Exact task/writer scopes và native_first → isolated → native_first roundtrip; other scope unchanged | Binary service rollback không được thực hiện |
| Hai root chạy đồng thời | Hai task/writer lease riêng, File API đúng root, 2.078 ms native Job overlap | UNKNOWN AutoCAD vẫn quarantine, không settle/replay |

Không cộng các lượt chạy test trùng nhau thành tổng số kiểm thử độc lập.
Baseline chưa đo VM cold-start hoặc peak RAM; census không có VM tại thời điểm
quan sát chỉ chứng minh trạng thái rảnh của thời điểm đó.

### Trạng thái rollout ngày 12-10-2026

Ubuntu `svhome@100.116.112.22` đã chuyển sang release
`codex-control-plane-parallel-native-1012-f7acd9ec4ba1`; health sau restart
xác nhận package source
`sha256:eb8c83abf44aca6c73ae5760813cda91d76187605cc53bbf1ae92cf6bb85f22d`.
Hai pilot Codex-web/Autocad đã được cấp lại sau recovery fence, Codex-web trước,
admission `scoped_pilot`. Schema database 29, MCP facade 32 và contract hash
không đổi. Deploy giữ lịch sử và backup; không restore database.

Ba Autocad UNKNOWN đã có quarantine disposition qua API được hỗ trợ; action,
attempt và receipt gốc vẫn UNKNOWN, không settle/replay. Diagnostic generic
`CONTROL_PLANE_FILE_READ_TARGET_MISSING` vẫn có thể phát sinh cả trước lẫn sau
đọc. Chỉ `CONTROL_PLANE_FILE_READ_TARGET_MISSING_BEFORE_DISPATCH` từ validation
ban đầu được phân loại từ chối trước đọc.

Candidate Windows `parallel-native-1012-r3` khớp 90 application files,
299 resources, 10 adapters và đạt smoke Recovery với profile tạm. Launch thực
tế phát hiện import sibling của node-agent không chạy dưới Python `-I`, nên
connected heartbeat không đạt. Source đã sửa direct-file loader dùng exact
sibling và chặn bytecode cache; real `-I` CLI/policy tests đạt. Production r3
đã READY/OPEN, `fullyReady=true`, MCP/native running và central connected lúc
**19:44:12 +07**; epoch
`activation-mv58t4he-c162dd8a1c513c77581c5adee2ae6762`.
Ubuntu inventory mới xác nhận hai root active/ready/online/dispatchable, gắn
heartbeat r3. Production đã kích hoạt theo scope cho hai root; canary Codex-web
đầu tiên, hai root chạy chồng thời gian và semantic acceptance vẫn chưa
nghiệm thu ở checkpoint này. Không có
commit/push/published installer/release.

Ubuntu giữ release đã deploy: loader fix chỉ đổi nhánh chạy file trực tiếp,
nhánh package import và các AST statement khác không đổi. HTTP/renewal hiện
không chạy nhánh đó. Không restart Ubuntu để alignment; pins canary ghi hash
source đang phục vụ riêng với hash loader Windows r3, không tuyên bố byte parity.
Xem [delta receipt](../.coding-tools/reports/parallel-native-first-20261012/r3-server/windows-r3-source-delta-receipt.json).

Evidence: [server deployment](../.coding-tools/reports/parallel-native-first-20261012/server-deployment-receipt.json),
[authority reissue](../.coding-tools/reports/parallel-native-first-20261012/authority-reissue-receipt.json),
[quarantine](../.coding-tools/reports/parallel-native-first-20261012/quarantine-receipt.json),
[Windows r3 parity](../.coding-tools/reports/native-first-20261012/parallel-r3-candidate-parity.json),
[Windows r3 smoke](../.coding-tools/reports/native-first-20261012/parallel-r3-packaged-smoke.json),
[r3 READY](../.coding-tools/reports/native-first-20261012/parallel-r3-transition/status-1791809052309-179002f3.json),
[hai root dispatchable](../.coding-tools/reports/parallel-native-first-20261012/server-readiness-r3-initial.json)
và [ma trận nghiệm thu production](../.coding-tools/reports/parallel-native-first-20261012/PRODUCTION_ACCEPTANCE.md).

### Canary r3 và sửa nhịp heartbeat

Canary `6bba02a734db47988da6042572f69497` xác minh 66 lần đọc rồi dừng ở
read067 với `CONTROL_PLANE_FILE_READ_TIMEOUT`. Kết quả gốc được giữ UNKNOWN;
đối soát sau đó chỉ ghi thêm receipt `rejected`, không tuyên bố đọc thành công
và không replay. Canary mới `bf3876b82a8a4eafbc83fec7c6e9b244` xác minh 57
lần đọc rồi bị từ chối admission vì heartbeat cũ 62,102 giây, vượt TTL 60 giây.
Task và writer của lần thứ hai đã đóng; không có action UNKNOWN mới, PATCH
hoặc Job trong lần này. Năm UNKNOWN trong census gồm ba Autocad và hai Codex
thuộc generation đã nghỉ từ tháng 9; cả năm đã tồn tại trước lần thứ hai.

Nguồn lỗi được tái hiện bằng kiểm tra tập trung: sau heartbeat thành công,
poll gặp khóa lane bận vẫn làm tăng backoff chung tới 300 giây. Source hiện
ghi lane `busy` chỉ cho đúng mã khóa của lane đó, tiếp tục các scope/lane khác,
và giữ khoảng lặp bình thường khi capability lỗi nhưng heartbeat thành công.
Lỗi heartbeat thực sự vẫn dùng backoff có giới hạn. Đây là bằng chứng source
và test; bản sửa cần package/activation mới trước khi tuyên bố production đã
được sửa. Vòng tuần tự vẫn có thể trì hoãn heartbeat khi công việc thực sự
chạy lâu; test này xác minh đường lỗi khóa/backoff.

Xem [audit lần thứ hai](../.coding-tools/reports/parallel-native-first-20261012/attempt2-heartbeat-policy-audit.json).
Status worker bị ghi đè mỗi vòng, nên mã busy của đúng vòng lịch sử chưa được
giữ lại; liên hệ giữa trigger đó và lần thất bại thực tế là suy luận từ timing,
worker không đổi và đường lỗi source đã tái hiện. Nhãn supervisor
`running_heartbeat_only` không chứng minh Python ngừng capability polling;
worker thực tế vẫn chạy `run-connected-agent` với policy theo scope.

Đo lại baseline bằng output mới, không ghi đè bằng chứng:

```powershell
python scripts/report-native-first-baseline.py --output .coding-tools/reports/native-first-20261012/after-activation-observation.json
```

Các bài test tập trung gồm router, required Job limits, MXC path/network boundary,
idle ownership, bridge metadata/hash/recovery, schema 32 và UI/policy authority.
Direct MCP shell-text escape hatch và Linux execution không được thay đổi bởi
router Windows structured argv này.
