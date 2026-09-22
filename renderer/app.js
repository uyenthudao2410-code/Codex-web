const api = window.mcpAssistant || createPreviewApi();

function createPreviewApi() {
  const previewSettings = {
    workspace: 'C:\\Users\\ExampleUser\\Desktop\\my-project', permissionMode: 'safe', toolMode: 'smart',
    mcpPort: 18766, healthPort: 18082, proxyMode: 'auto', proxyUrl: '', tunnelId: 'tunnel_demo',
    recoveryMcpPort: 18767, recoveryHealthPort: 18083, recoveryTunnelId: '',
    controlPlaneServerUrl: '',
    theme: 'light', startWithWindows: false, progressReportSeconds: 90, keepRunningOnClose: true, autoStartServices: false, firstRunCompleted: true, guideProgress: {}, authorizedRoots: []
  };
  const snapshot = {
    settings: previewSettings,
    secrets: { runtimeApiKey: true, mcpAuthToken: true },
    environment: {
      python: { installed: true, version: 'Python 3.12.10' },
      proxy: { mode: 'auto', configured: false, reachable: true, source: 'auto-direct', url: '' }, tunnelClient: { installed: true },
      workspace: { configured: true, exists: true }, ports: { mcpListening: true, tunnelListening: true }
    },
    status: { busy: false, runtimeRunning: true, tunnelRunning: true, fullyReady: true, localMcpUrl: 'http://127.0.0.1:18766/mcp', tunnelUiUrl: 'http://127.0.0.1:18082/ui', connectorContractState: 'UNCHANGED_ACKNOWLEDGED', connectorRefreshRequired: false, codeRevision: { codingMcp: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false } } },
    device: { scope: 'current_device_only', registry: 'local', device_id: '12345678-1234-4123-8123-123456789abc', device_instance_id: 'preview-device-instance-0001', display_name: 'Máy bàn', online: true, workspace: previewSettings.workspace, coding: { mcp_running: true, native_alive: true, tunnel_running: true, tunnel_id: 'tunnel_demo', ownership: 'device_id' }, recovery: { host_running: true, mcp_running: true, tunnel_running: false, tunnel_state: 'not_configured', tunnel_id: null }, git: { available: true, branch: 'main', head: 'cf6cb6ddbf29d90515d003ce72490ffda985c37f', head_short: 'cf6cb6dd', dirty: true } },
    recoveryHost: { state: 'healthy', device_id: '12345678-1234-4123-8123-123456789abc', device_instance_id: 'preview-device-instance-0001', device_display_name: 'Máy bàn', code_revision: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }, electron_ui_revision: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }, electron_ui_recovery: { state: 'healthy', alive: true, pid: 42001, instance_id: 'preview-electron-ui-0001', runtime_mode: 'development' }, recovery_plane: { tunnel: { state: 'not_configured', configured: false, pid: null } } }
  };
  const ok = (data) => Promise.resolve({ ok: true, data });
  return {
    snapshot: () => ok(snapshot), chooseWorkspace: () => ok(snapshot.settings.workspace), switchWorkspace: (workspace) => { snapshot.settings.workspace=workspace; return ok(snapshot); }, updateAuthorizedRoots: (roots) => { snapshot.settings.authorizedRoots=roots; return ok(snapshot); }, closeManager: () => ok(true),
    saveSettings: (patch) => { Object.assign(snapshot.settings, patch); return ok(snapshot.settings); },
    saveRuntimeKey: () => ok(snapshot.secrets), removeRuntimeKey: () => ok(snapshot.secrets), regenerateMcpToken: () => ok(snapshot.secrets),
    requestControlPlaneEnrollment: (serverUrl) => ok({ enrollment_id: 'enroll_preview_0001', device_id: snapshot.device.device_id, state: 'pending_operator_approval', server_origin: serverUrl || '' }),
    reconcileControlPlaneEnrollment: () => ok({ device_id: snapshot.device.device_id, enrollment_id: 'enroll_preview_0001', state: 'pending_operator_approval', credential_generation: null, fresh: true, observed_at_ms: Date.now(), error_code: null, server_origin: snapshot.settings.controlPlaneServerUrl || null }),
    reconcileControlPlaneAuthorityStatus: () => ok({ device_id: snapshot.device.device_id, state: 'no_binding', node_display_name: 'Máy bàn', workspace_count: 1, target_count: 0, dispatchable_target_count: 0, targets: [], fresh: true, observed_at_ms: Date.now(), error_code: null }),
    rotateControlPlaneCredential: () => ok({ device_id: snapshot.device.device_id, rotation_id: 'rotate_' + 'a'.repeat(32), state: 'completed', current_generation: 1, next_generation: 2, fresh: true, error_code: null }),
    registerControlPlaneWorkspace: ({ capabilities } = {}) => ok({ workspace_id: 'workspace_0123456789abcdef0123456789abcdef', workspace_generation: 'generation_abcdef0123456789abcdef0123456789', display_name: 'my-project', capabilities: { read: true, write: capabilities?.write === true, exec: capabilities?.exec === true }, replayed: false, state: 'registered' }),
    replaceControlPlaneWorkspace: ({ capabilities } = {}) => ok({ workspace_id: 'workspace_0123456789abcdef0123456789abcdef', old_workspace_generation: 'generation_abcdef0123456789abcdef0123456789', workspace_generation: 'generation_fedcba9876543210fedcba9876543210', display_name: 'my-project', capabilities: { read: true, write: capabilities?.write === true, exec: capabilities?.exec === true }, replayed: false, state: 'replaced' }),
    listControlPlaneWorkspaces: () => ok([]),
    installControlPlaneReadOnlyPolicyAssignment: () => ok({ enabled: true, expires_at_ms: Date.now() + 60 * 60 * 1000, policy_sha256: 'b'.repeat(64), runtime_mode: 'packaged', windows_acl_verified: false }),
    retireControlPlaneWorkspace: ({ workspaceId, workspaceGeneration } = {}) => ok({ workspace_id: workspaceId, workspace_generation: workspaceGeneration, display_name: 'my-project', capabilities: { read: true, write: false, exec: false }, replayed: false, state: 'retired' }),
    handoffCentralExecutor: () => { snapshot.settings.executionRole = 'central_executor'; snapshot.status.executionRole = 'central_executor'; snapshot.status.tunnelRunning = false; snapshot.status.fullyReady = false; return ok(snapshot); },
    start: () => ok(snapshot), stop: () => ok(snapshot), restart: () => ok(snapshot), acknowledgeConnectorContract: () => ok(snapshot),
    logs: () => ok([{ time: new Date().toISOString(), level: 'info', message: 'Chế độ xem trước giao diện tĩnh' }]), clearLogs: () => ok(true),
    taskState: () => ok({ exists: false, state: null }), clearTaskState: () => ok(true), pauseTask: () => ok({}), resumeTask: () => ok({}), stopTask: () => ok({}), taskHistory: () => ok([]), performanceTrace: () => ok(null), clearPerformanceTrace: () => ok(true), recordUiPerformance: () => ok({ accepted: false }), uiPerformance: () => ok(null),
    inspectBuild: () => ok({ type: 'electron', name: 'demo', version: '0.1.0', testCommand: 'npm test', buildCommand: 'npm run dist', artifacts: ['dist'] }), runBuild: () => ok({ overallStatus: 'passed', project: { type: 'electron', name: 'demo', version: '0.1.0' }, testResult: { status: 'passed' }, buildResult: { status: 'passed' }, artifacts: [] }), inspectHealth: () => ok({ healthy: true, checks: [] }), repairHealth: () => ok({ healthy: true, checks: [], actions: [], unresolved: [] }),
    openControlPlaneConsole: () => ok(true), openExternal: () => ok(true), installPython: () => ok(true), detectProxy: () => ok(snapshot.environment.proxy), onProgress: () => () => {}, onLog: () => () => {}, onStatus: () => () => {}, onHeartbeat: () => () => {}, onBuildProgress: () => () => {}
  };
}

const pageMeta = {
  overview: ['EXECUTION CONTROL', 'Command Center', 'Runtime, clients, routing, authority and proof in one operational view.'],
  device: ['DEVICE CONTROL', 'Thiết bị hiện tại', 'Định danh thiết bị, ownership, Coding/Recovery, Tunnel và Git của máy đang chạy Recovery Host.'],
  deploy: ['KẾT NỐI', 'Kết nối máy chủ', 'Kết nối Ubuntu hoặc cấu hình direct legacy trong phần nâng cao.'],
  workspace: ['THƯ MỤC & QUYỀN', 'Thư mục & quyền', 'Chọn đường dẫn local và xem rõ quyền đọc, ghi, chạy đang được áp dụng.'],
  task: ['TASKS & PROOF', 'Tasks & Proof', 'Theo dõi durable task state, kiểm thử, proof, lịch sử và hiệu năng.'],
  system: ['THIẾT LẬP HỆ THỐNG', 'Thiết lập hệ thống', 'Máy chủ, tài khoản, thư mục và tùy chọn ứng dụng trong cùng một nơi.'],
  build: ['BUILD & XÁC MINH', 'Xác minh & Build', 'Tự động nhận diện dự án, thực thi kiểm thử và build, đồng thời kiểm tra sản phẩm đầu ra.'],
  health: ['CHẨN ĐOÁN & SỬA CHỮA', 'Chẩn đoán & Sửa chữa', 'Kiểm tra môi trường vận hành và tự động sửa chữa các sự cố an toàn.'],
  guide: ['HƯỚNG DẪN CẤU HÌNH', 'Hướng dẫn Kết nối', 'Hoàn thành các bước kết nối OpenAI Tunnel và ChatGPT Web.'],
  logs: ['CHẨN ĐOÁN', 'Nhật ký Vận hành', 'Xem thông tin chẩn đoán của môi trường portable, MCP và Tunnel.'],
  settings: ['CẤU HÌNH TÙY CHỌN', 'Cài đặt Trợ lý', 'Quản lý giao diện, hành vi khởi động, phản hồi nhiệm vụ và chứng thư cục bộ.']
};

const state = {
  snapshot: null,
  currentPage: 'overview',
  selectedWorkspace: '',
  logFilter: 'all',
  logs: [],
  busy: false,
  centralEnrollmentBusy: false,
  centralEnrollmentReceipt: null,
  centralEnrollmentStatus: null,
  centralEnrollmentStatusChecked: false,
  centralAuthorityBusy: false,
  centralAuthorityStatus: null,
  centralCredentialRotationBusy: false,
  centralCredentialRotationStatus: null,
  centralWorkspaceBusy: false,
  // This is deliberately an in-memory picker result, not settings.workspace.
  // Registering another root must never retarget the local runtime or an
  // already-bound remote task.
  centralWorkspaceCandidate: '',
  centralWorkspacePreset: 'read',
  centralWorkspaceCapabilities: { read: true, write: false, exec: false },
  centralWorkspaceReceipt: null,
  centralPolicyReceipt: null,
  centralPolicyBusy: false,
  centralWorkspaceListBusy: false,
  centralWorkspaces: null,
  centralWorkspaceInventoryStatus: 'not_loaded',
  centralWorkspaceInventoryError: null,
  centralWorkspaceRetirementReceipt: null,
  initializedForms: false
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function unwrap(result) {
  if (!result?.ok) throw new Error(result?.error || 'Thao tác thất bại');
  return result.data;
}

function toast(title, message = '', type = 'success') {
  const element = document.createElement('div');
  element.className = `toast ${type}`;
  const heading = document.createElement('b');
  heading.textContent = title;
  const detail = document.createElement('span');
  detail.textContent = message;
  element.append(heading, detail);
  $('#toastStack').appendChild(element);
  setTimeout(() => element.remove(), 4200);
}

function setBusy(value, overlay = false) {
  state.busy = value;
  $('#busyOverlay').classList.toggle('visible', value && overlay);
  ['#topStartButton', '#heroStartButton', '#deployNow', '#overviewRestart', '#overviewStop', '#deviceStart', '#deviceRestart', '#deviceStop', '#deviceRepair', '#handoffCentralExecutor', '#retryCentralExecutorHandoff', '#requestControlPlaneEnrollment', '#rotateControlPlaneCredential', '#chooseControlPlaneWorkspace', '#registerControlPlaneWorkspace', '#refreshControlPlaneWorkspaces', '#refreshControlPlaneAuthorityStatus'].forEach((selector) => {
    const element = $(selector);
    if (element) element.disabled = value;
  });
}

function setDot(element, status) {
  if (!element) return;
  element.classList.remove('ready', 'warn', 'error');
  if (status) element.classList.add(status);
}

function isCentralExecutor(settings = {}) {
  return settings?.executionRole === 'central_executor';
}

const CENTRAL_WORKSPACE_PRESETS = Object.freeze({
  read: Object.freeze({
    label: 'Chỉ xem',
    detail: 'Đọc danh sách và kết quả; không sửa file hoặc chạy lệnh.',
    capabilities: Object.freeze({ read: true, write: false, exec: false })
  }),
  code: Object.freeze({
    label: 'Làm việc với mã nguồn',
    detail: 'Đọc, sửa file và chạy công cụ trong policy đã được cấp.',
    capabilities: Object.freeze({ read: true, write: true, exec: true })
  }),
  custom: Object.freeze({
    label: 'Tùy chỉnh',
    detail: 'Chọn từng quyền trong phần nâng cao.',
    capabilities: null
  })
});

function centralWorkspacePresetFor(capabilities = {}) {
  if (capabilities.write === true && capabilities.exec === true) return 'code';
  if (capabilities.write !== true && capabilities.exec !== true) return 'read';
  return 'custom';
}

function centralWorkspaceCapabilityLabel(capabilities = {}) {
  const preset = centralWorkspacePresetFor(capabilities);
  if (preset !== 'custom') return CENTRAL_WORKSPACE_PRESETS[preset].label;
  const labels = { read: 'đọc', write: 'ghi', exec: 'chạy' };
  const selected = ['read', 'write', 'exec']
    .filter((name) => capabilities[name] === true)
    .map((name) => labels[name]);
  return selected.length ? `Tùy chỉnh · ${selected.join(', ')}` : 'Chưa chọn quyền';
}

// Central workspaces are deliberately separate from the legacy direct-mode
// settings.workspace field.  The latter is retained only for an explicit
// rollback and must never decide whether the Ubuntu setup wizard is complete.
function centralWorkspaceEntries() {
  if (Array.isArray(state.centralWorkspaces)) return state.centralWorkspaces;
  if (state.centralWorkspaceReceipt?.workspace_id && state.centralWorkspaceReceipt?.workspace_generation) {
    return [state.centralWorkspaceReceipt];
  }
  return [];
}

function centralWorkspaceSummary() {
  const entries = centralWorkspaceEntries();
  if (!entries.length) return 'Chưa chọn thư mục';
  const labels = entries.map((entry) => String(entry.display_name || '').trim()).filter(Boolean);
  if (labels.length === 1) return labels[0];
  return `${labels.length} thư mục đã thêm`;
}

function centralDispatchableTargetForLocalWorkspace() {
  const entries = centralWorkspaceEntries();
  const targets = Array.isArray(state.centralAuthorityStatus?.targets)
    ? state.centralAuthorityStatus.targets
    : [];
  const dispatchable = targets.filter((target) => target?.dispatch_state === 'dispatchable');
  const matches = dispatchable.filter((target) => entries.some((entry) => {
    if (target.workspace_id && target.workspace_generation) {
      return entry.workspace_id === target.workspace_id
        && entry.workspace_generation === target.workspace_generation;
    }
    return entry.display_name === target.workspace_display_name;
  }));
  // Prefer opaque identity/generation when the server supplies it. Legacy
  // receipts may contain only a display name; still refuse ambiguity rather
  // than guessing a target behind the user's back.
  if (matches.length !== 1) return null;
  const matchingEntries = entries.filter((entry) => {
    if (matches[0].workspace_id && matches[0].workspace_generation) {
      return entry.workspace_id === matches[0].workspace_id
        && entry.workspace_generation === matches[0].workspace_generation;
    }
    return entry.display_name === matches[0].workspace_display_name;
  });
  return matchingEntries.length === 1 ? matches[0] : null;
}

function centralWorkspaceCapabilitiesFromUi() {
  const preset = state.centralWorkspacePreset || 'read';
  if (preset !== 'custom') return { ...CENTRAL_WORKSPACE_PRESETS[preset].capabilities };
  return {
    read: true,
    write: $('#controlPlaneCapabilityWrite')?.checked === true,
    exec: $('#controlPlaneCapabilityExec')?.checked === true
  };
}

function chooseCentralWorkspacePreset(preset) {
  if (!Object.hasOwn(CENTRAL_WORKSPACE_PRESETS, preset)) return;
  state.centralWorkspacePreset = preset;
  if (preset !== 'custom') {
    state.centralWorkspaceCapabilities = { ...CENTRAL_WORKSPACE_PRESETS[preset].capabilities };
  }
  if (state.snapshot) renderCentralExecutorMode(state.snapshot);
}

function centralRoutePresentation(status = {}) {
  const reason = String(status.centralStatusReason || '').trim() || null;
  if (status.centralConnected === true && status.authorityReady === true && !reason) {
    return {
      state: 'connected',
      label: 'Đã sẵn sàng qua Ubuntu',
      detail: 'Route trung tâm và policy action cục bộ đã được xác minh.'
    };
  }
  if (status.runtimeRunning !== true) {
    return {
      state: 'waiting',
      label: 'MCP nội bộ chưa sẵn sàng',
      detail: 'Có thể gửi pairing và cài policy Ubuntu ngay; thực thi vẫn bị khóa cho tới khi MCP và kiểm tra chuyển đổi hoàn tất.'
    };
  }
  if (status.centralConnected !== true) {
    return {
      state: 'waiting',
      label: 'Chờ pairing Ubuntu',
      detail: reason
        ? `Ubuntu chưa xác minh route cho máy này (${reason}).`
        : 'Ubuntu chưa xác minh route cho máy này.'
    };
  }
  return {
    state: 'waiting',
    label: 'Đã nối Ubuntu · chờ quyền',
    detail: reason
      ? `Máy chủ đã phản hồi nhưng chưa có đủ quyền cho target này (${reason}).`
      : 'Máy chủ đã phản hồi; cần target/policy được cấp trước khi nhận việc.'
  };
}

function centralSetupGuidance(snapshot = {}, enrollment = null, authority = null) {
  const mode = snapshot.recoveryHost?.electron_ui_recovery?.runtime_mode;
  const status = snapshot?.status || {};
  const centralStatusReason = String(status.centralStatusReason || '').trim();
  const packagedRequired = [enrollment?.error_code, authority?.error_code]
    .some((code) => /PACKAGED_REQUIRED|candidate packaged/.test(String(code || '')));
  const packagedRuntimeMissing = [enrollment?.error_code, authority?.error_code]
    .some((code) => /RUNTIME_MISSING/.test(String(code || '')));
  if (mode === 'development' || packagedRequired) return {
    key: 'development', owner: 'TRÊN WINDOWS', title: 'Cần bản cài đặt để hoàn tất kết nối',
    detail: 'Bạn đang chạy npm start. Mở bản Coding Tools MCP đã cài và được xác minh để duyệt máy, thêm thư mục và kiểm tra quyền. Bật Ubuntu hoặc bấm kiểm tra lại không gỡ giới hạn của bản dev.',
    action: 'details', actionLabel: 'Xem hướng dẫn kết nối'
  };
  if (packagedRuntimeMissing) return {
    key: 'runtime-missing', owner: 'TRÊN WINDOWS', title: 'Bản cài đặt thiếu thành phần kết nối',
    detail: 'Candidate packaged không có đủ Python hoặc node-agent để kiểm tra/enrollment. Cài lại đúng gói đã xác minh; không gửi lại yêu cầu và không duyệt máy mới để né lỗi.',
    action: 'check', actionLabel: 'Kiểm tra lại bản cài'
  };
  if (mode !== 'packaged') return {
    key: 'runtime-unverified', owner: 'TRÊN WINDOWS', title: 'Chưa xác minh bản chạy của máy này',
    detail: 'Không thể xác nhận cửa sổ đang dùng bản cài packaged đã được xác minh. Giữ pairing, workspace và policy ở trạng thái đóng; mở bản cài đặt đúng hoặc kiểm tra lại runtime trước khi tiếp tục.',
    action: 'details', actionLabel: 'Xem chi tiết runtime'
  };
  if (enrollment?.fresh === false && enrollment?.state !== 'unconfigured') return {
    key: 'unverified', owner: 'KIỂM TRA KẾT NỐI', title: 'Chưa xác minh được trạng thái máy',
    detail: 'Kiểm tra địa chỉ Ubuntu và kết nối mạng chung, rồi kiểm tra trạng thái máy. Giữ nguyên yêu cầu đã lưu; không gửi đăng ký mới chỉ vì lần kiểm tra này chưa thành công.',
    action: 'check', actionLabel: 'Kiểm tra trạng thái máy'
  };
  if (enrollment?.state === 'revoked' || authority?.state === 'revoked') return {
    key: 'revoked', owner: 'QUẢN TRỊ VIÊN UBUNTU', title: 'Máy đã bị thu hồi quyền',
    detail: 'Nhờ quản trị viên kiểm tra máy trên Ubuntu. Không tự đăng ký lại hoặc chuyển công việc sang máy khác.',
    action: 'details', actionLabel: 'Xem hướng xử lý'
  };
  if (['request_sent', 'pending_operator_approval'].includes(enrollment?.state)) return {
    key: 'pending', owner: 'QUẢN TRỊ VIÊN UBUNTU', title: 'Đã gửi yêu cầu · chờ duyệt máy',
    detail: 'Quản trị viên cần duyệt yêu cầu của máy này trên Ubuntu. Sau khi được duyệt, bấm “Kiểm tra trạng thái máy”, rồi thêm thư mục. Không cần gửi lại yêu cầu.',
    action: 'check', actionLabel: 'Kiểm tra trạng thái máy'
  };
  const supportedEnrollmentState = new Set(['unconfigured', 'request_sent', 'pending_operator_approval', 'approved', 'revoked', 'unknown']);
  if (enrollment?.state && !supportedEnrollmentState.has(enrollment.state)) return {
    key: 'unverified', owner: 'KIỂM TRA KẾT NỐI', title: 'Trạng thái máy chưa được xác minh',
    detail: 'Ubuntu trả về một trạng thái chưa có trong contract hiện tại. Không tự đăng ký lại hoặc suy ra máy đã được duyệt; cần kiểm tra phiên bản và receipt.',
    action: 'check', actionLabel: 'Kiểm tra trạng thái máy'
  };
  const approved = enrollment?.fresh === true && enrollment?.state === 'approved';
  if (!approved && enrollment?.state === 'approved') return {
    key: 'unverified', owner: 'KIỂM TRA KẾT NỐI', title: 'Yêu cầu đã lưu nhưng chưa có receipt mới',
    detail: 'Máy từng được báo approved nhưng lần đọc hiện tại chưa fresh. Giữ cấu hình và kiểm tra lại; không gửi enrollment mới.',
    action: 'check', actionLabel: 'Kiểm tra trạng thái máy'
  };
  if (!approved && status.centralConnected !== true) return {
    key: 'connect', owner: 'TRÊN WINDOWS', title: 'Nhập địa chỉ và gửi yêu cầu kết nối',
    detail: 'Dùng địa chỉ HTTPS của máy chủ Ubuntu mà máy này truy cập được. Gửi một yêu cầu, sau đó nhờ quản trị viên Ubuntu duyệt máy. Không cần nhập API key, Tunnel hay token.',
    action: 'details', actionLabel: 'Nhập địa chỉ Ubuntu'
  };
  if (!approved) return {
    key: 'unverified', owner: 'KIỂM TRA KẾT NỐI', title: 'Chưa xác minh được trạng thái máy',
    detail: 'Runtime đang phản hồi nhưng chưa có receipt enrollment fresh ở client. Giữ nguyên cấu hình và kiểm tra lại; không coi heartbeat là approve.',
    action: 'check', actionLabel: 'Kiểm tra trạng thái máy'
  };
  if (authority?.fresh === false) return {
    key: 'authority-stale', owner: 'KIỂM TRA QUYỀN UBUNTU', title: 'Máy đã duyệt nhưng quyền hiện tại chưa xác minh',
    detail: 'Lần đọc account/target từ Ubuntu đang stale hoặc lỗi. Không giữ nhãn xanh từ receipt cũ, không gửi lại enrollment và không chạy task cho tới khi có receipt mới.',
    action: 'check', actionLabel: 'Kiểm tra lại quyền'
  };
  if (centralStatusReason === 'LOCAL_EXECUTOR_NOT_READY') return {
    key: 'local-executor', owner: 'TRÊN WINDOWS', title: 'Máy đã duyệt nhưng runtime local chưa sẵn sàng',
    detail: 'Enrollment không có vấn đề. Kiểm tra activation/runtime local theo hướng dẫn; không duyệt lại máy và không đăng ký workspace mới để né blocker.',
    action: 'details', actionLabel: 'Xem chi tiết runtime'
  };
  if (centralStatusReason === 'CENTRAL_LOCAL_POLICY_NOT_READY') return {
    key: 'policy', owner: 'WINDOWS → UBUNTU', title: 'Đã nối Ubuntu nhưng chưa đủ policy thực thi',
    detail: 'Route trung tâm đã được nhìn thấy nhưng policy local hoặc target chưa hợp lệ. Kiểm tra binding, workspace generation và policy; không tự cấp quyền mới.',
    action: 'details', actionLabel: 'Xem liên kết & quyền'
  };
  if (status.centralConnected !== true) return {
    key: 'route', owner: 'WINDOWS → UBUNTU', title: 'Máy đã duyệt nhưng route Ubuntu chưa sẵn sàng',
    detail: 'Giữ enrollment hiện tại và kiểm tra route trung tâm. Không gửi lại enrollment hoặc chuyển task sang máy khác.',
    action: 'check', actionLabel: 'Kiểm tra route'
  };
  return {
    key: 'approved', owner: 'WINDOWS → UBUNTU', title: 'Máy đã được xác nhận · tiếp tục thư mục và quyền',
    detail: 'Thêm thư mục ở phần “Thư mục & quyền”. Quản trị viên cấp thư mục cho tài khoản; sau đó kiểm tra liên kết ở dưới. Duyệt máy không đồng nghĩa đã sẵn sàng chạy nhiệm vụ.',
    action: 'workspace', actionLabel: 'Mở thư mục & quyền'
  };
}

function centralSetupRuntimeBlocked(guidance = centralSetupGuidance(state.snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus)) {
  return ['development', 'runtime-unverified', 'runtime-missing'].includes(guidance?.key);
}

function centralSetupDevelopmentBlocked() {
  return isCentralExecutor(state.snapshot?.settings)
    && centralSetupRuntimeBlocked();
}

function assertPackagedCentralSetup(action) {
  if (centralSetupDevelopmentBlocked()) {
    const guidance = centralSetupGuidance(state.snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus);
    const detail = guidance?.key === 'runtime-missing'
      ? 'Bản cài đặt đang thiếu Python hoặc node-agent đóng gói; cài lại candidate đã xác minh.'
      : 'npm start chỉ hỗ trợ preview và chẩn đoán; hãy mở bản cài đặt packaged đã được xác minh.';
    throw new Error(`${action} cần runtime packaged hợp lệ. ${detail}`);
  }
}

function renderConnectionGuidance(snapshot) {
  const guidance = centralSetupGuidance(snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus);
  const devNotice = $('#setupDevelopmentNotice');
  const runtimeBlocked = centralSetupRuntimeBlocked(guidance);
  if (devNotice) {
    devNotice.hidden = !runtimeBlocked;
    const title = devNotice.querySelector('b');
    const detail = devNotice.querySelector('p');
    if (guidance.key === 'development') {
      if (title) title.textContent = 'Bạn đang dùng bản phát triển · npm start';
      if (detail) detail.textContent = 'Bản này dùng để phát triển giao diện. Các bước xác minh máy, thư mục và quyền Ubuntu cần bản cài đặt đã được xác minh. Máy chủ đang bật không đồng nghĩa máy Windows đã được cấp quyền.';
    } else if (guidance.key === 'runtime-unverified') {
      if (title) title.textContent = 'Chưa xác minh bản packaged';
      if (detail) detail.textContent = 'Không thể xác nhận runtime hiện tại là bản cài đặt packaged đã được xác minh. Không gửi pairing hoặc cấp policy từ cửa sổ này; kiểm tra lại runtime trước.';
    } else if (guidance.key === 'runtime-missing') {
      if (title) title.textContent = 'Bản cài đặt thiếu thành phần kết nối';
      if (detail) detail.textContent = 'Python hoặc node-agent packaged không có/không hợp lệ. Cài lại candidate đã xác minh trước khi gửi pairing, đăng ký workspace hoặc cài policy.';
    }
  }
  for (const [id, text] of [['connectionNextOwner', guidance.owner], ['connectionNextTitle', guidance.title], ['connectionNextText', guidance.detail]]) {
    const element = $(`#${id}`);
    if (element) element.textContent = text;
  }
  const check = $('#refreshControlPlaneEnrollment');
  if (check) check.disabled = state.busy || state.centralEnrollmentBusy || runtimeBlocked;
  const technical = $('#controlPlaneTechnicalStatus');
  if (technical) technical.textContent = [
    `Máy: ${snapshot?.device?.display_name || 'chưa xác định'}`,
    `Yêu cầu: ${state.centralEnrollmentStatus?.enrollment_id || state.centralEnrollmentReceipt?.enrollment_id || 'chưa đọc được'}`,
    `Kiểm tra máy: ${state.centralEnrollmentStatus?.error_code || state.centralEnrollmentStatus?.state || 'chưa kiểm tra'}`,
    `Kiểm tra tài khoản: ${state.centralAuthorityStatus?.error_code || state.centralAuthorityStatus?.state || 'chưa kiểm tra'}`
  ].join('\n');
  renderControlPlaneConsoleLink();
  return guidance;
}

function renderControlPlaneConsoleLink() {
  const origin = String($('#controlPlaneServerUrl')?.value || state.snapshot?.settings?.controlPlaneServerUrl || '').trim();
  const button = $('#openControlPlaneConsole');
  if (button) button.disabled = !origin || typeof api.openControlPlaneConsole !== 'function';
  const hint = $('#controlPlaneConsoleHint');
  if (hint) hint.textContent = origin
    ? 'Mở địa chỉ đã nhập trong trình duyệt. Chỉ nhập operator token trên trang quản trị đúng máy chủ; ứng dụng không chuyển token hoặc tự đăng nhập.'
    : 'Nhập địa chỉ Ubuntu ở trên để mở trang quản trị. Mở trang không đăng ký máy hoặc cấp quyền.';
}

async function openControlPlaneConsole() {
  const origin = String($('#controlPlaneServerUrl')?.value || state.snapshot?.settings?.controlPlaneServerUrl || '').trim();
  try { unwrap(await api.openControlPlaneConsole(origin)); }
  catch (error) { toast('Không thể mở trang quản trị Ubuntu', error.message, 'error'); }
}

function renderCentralWorkspaceRegistrations(central) {
  const container = $('#controlPlaneWorkspaceRegistrations');
  if (!container) return;
  container.replaceChildren();
  if (!central) return;
  const development = centralSetupDevelopmentBlocked();
  if (state.centralWorkspaceListBusy) {
    const loading = document.createElement('span');
    loading.className = 'task-muted';
    loading.textContent = 'Đang tải inventory workspace local…';
    container.append(loading);
    return;
  }
  if (state.centralWorkspaceInventoryStatus === 'unknown') {
    const pending = document.createElement('span');
    pending.className = 'task-muted';
    pending.textContent = `Không đọc được inventory workspace local (${state.centralWorkspaceInventoryError || 'lỗi chưa rõ'}). Bấm “Tải workspace đã đăng ký” để thử lại.`;
    container.append(pending);
    return;
  }
  if (state.centralWorkspaceInventoryStatus !== 'loaded' || state.centralWorkspaces === null) {
    const pending = document.createElement('span');
    pending.className = 'task-muted';
    pending.textContent = 'Chưa tải inventory workspace local';
    container.append(pending);
    return;
  }
  if (state.centralWorkspaces.length === 0) {
    const empty = document.createElement('span');
    empty.className = 'task-muted';
    empty.textContent = 'Chưa có workspace local nào được đăng ký.';
    container.append(empty);
    return;
  }
  for (const workspace of state.centralWorkspaces) {
    const row = document.createElement('div');
    row.className = 'authorized-root-row central-workspace-row';
    const label = document.createElement('span');
    const title = document.createElement('b');
    title.textContent = workspace.display_name;
    const detail = document.createElement('small');
    const capabilities = workspace.capabilities || {};
    const targetMatches = (state.centralAuthorityStatus?.targets || [])
      .filter((item) => (item.workspace_id && item.workspace_generation
        ? item.workspace_id === workspace.workspace_id && item.workspace_generation === workspace.workspace_generation
        : item.workspace_display_name === workspace.display_name));
    const target = targetMatches.length === 1 ? targetMatches[0] : null;
    const targetLabel = targetMatches.length > 1
      ? 'Nhiều target trùng tên · cần xác định'
      : target?.dispatch_state === 'dispatchable'
      ? 'Đã liên kết'
      : target
        ? 'Đã đăng ký · đang chờ quyền'
        : 'Chưa liên kết tài khoản';
    detail.textContent = `${targetLabel} · ${centralWorkspaceCapabilityLabel(capabilities)}`;
    label.append(title, detail);
    const advanced = document.createElement('details');
    advanced.className = 'workspace-advanced-actions';
    const advancedSummary = document.createElement('summary');
    advancedSummary.textContent = 'Quản lý nâng cao';
    advanced.append(advancedSummary);
    const advancedActions = document.createElement('div');
    advancedActions.className = 'authorized-root-actions';
    const retire = document.createElement('button');
    retire.type = 'button';
    retire.className = 'secondary-button';
    retire.textContent = 'Thu hồi thư mục';
    retire.disabled = development || state.busy || state.centralWorkspaceBusy || state.centralWorkspaceListBusy;
    retire.addEventListener('click', () => {
      retireControlPlaneWorkspace(workspace).catch((error) => {
        toast('Không thể thu hồi workspace Ubuntu', error.message, 'error');
      });
    });
    const replace = document.createElement('button');
    replace.type = 'button';
    replace.className = 'secondary-button';
    replace.textContent = 'Đổi mức quyền';
    replace.title = 'Đóng generation cũ, tạo generation mới và yêu cầu liên kết lại target.';
    replace.disabled = development || state.busy || state.centralWorkspaceBusy || state.centralWorkspaceListBusy;
    replace.addEventListener('click', () => {
      replaceControlPlaneWorkspace(workspace).catch((error) => {
        toast('Không thể đổi mức quyền workspace Ubuntu', error.message, 'error');
      });
    });
    const policy = document.createElement('button');
    policy.type = 'button';
    policy.className = 'secondary-button';
    policy.textContent = 'Đồng bộ quyền chỉ xem';
    policy.title = 'Chỉ dùng khi quản trị viên yêu cầu; không phải thủ tục cấp quyền hằng ngày.';
    policy.disabled = development || state.busy || state.centralWorkspaceBusy || state.centralWorkspaceListBusy || state.centralPolicyBusy;
    policy.addEventListener('click', () => {
      installControlPlaneReadOnlyPolicyAssignment(workspace).catch((error) => {
        toast('Không thể đồng bộ read-only policy', error.message, 'error');
      });
    });
    advancedActions.append(replace, retire, policy);
    advanced.append(advancedActions);
    row.append(label, advanced);
    container.append(row);
  }
}

function renderCentralExecutorMode(snapshot) {
  const settings = snapshot?.settings || {};
  const central = isCentralExecutor(settings);
  const development = central && centralSetupRuntimeBlocked(centralSetupGuidance(snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus));
  const route = centralRoutePresentation(snapshot?.status || {});
  document.body.dataset.executionRole = central ? 'central-executor' : 'direct-legacy';
  $$('[data-direct-only]').forEach((element) => { element.hidden = central; });
  const notice = $('#centralExecutorNotice');
  const noticeText = $('#centralExecutorNoticeText');
  const deployTitle = $('#deploySectionTitle');
  const deploySubtitle = $('#deploySectionSubtitle');
  const guide = $('#centralExecutorGuide');
  const pairingInput = $('#controlPlaneServerUrl');
  const pairingButton = $('#requestControlPlaneEnrollment');
  const pairingStatus = $('#controlPlaneEnrollmentStatus');
  const credentialRotation = $('#controlPlaneCredentialRotation');
  const credentialRotationButton = $('#rotateControlPlaneCredential');
  const credentialRotationStatus = $('#controlPlaneCredentialRotationStatus');
  const workspaceRegistration = $('#centralExecutorWorkspaceRegistration');
  const workspaceChoose = $('#chooseControlPlaneWorkspace');
  const workspaceCandidate = $('#controlPlaneWorkspaceCandidate');
  const workspaceDevice = $('#controlPlaneWorkspaceDevice');
  const capabilityRead = $('#controlPlaneCapabilityRead');
  const capabilityWrite = $('#controlPlaneCapabilityWrite');
  const capabilityExec = $('#controlPlaneCapabilityExec');
  const capabilityPresets = $$('input[name="centralWorkspacePreset"]');
  const customCapabilities = $('#centralWorkspaceCustomCapabilities');
  const capabilitySummary = $('#controlPlaneCapabilitySummary');
  const workspaceButton = $('#registerControlPlaneWorkspace');
  const workspaceRefresh = $('#refreshControlPlaneWorkspaces');
  const workspaceStatus = $('#controlPlaneWorkspaceRegistrationStatus');
  const activationStatus = $('#centralExecutorActivationStatus');
  const retryHandoff = $('#retryCentralExecutorHandoff');
  const epoch = snapshot?.recoveryHost?.activation_epoch || snapshot?.status?.activationEpoch || {};
  const epochState = epoch.epoch_state || epoch.state;
  const expired = epoch.stale === true || (!['READY', 'FAILED'].includes(epochState)
    && Number(epoch.expires_at_unix_ms) > 0 && Number(epoch.expires_at_unix_ms) <= Date.now());
  const retryable = expired || ['FAILED', 'UPDATE_INCOMPLETE', 'NONE'].includes(epochState);
  if (notice) notice.hidden = !central;
  if (guide) guide.hidden = !central;
  if (workspaceRegistration) workspaceRegistration.hidden = !central;
  if (deployTitle) deployTitle.textContent = central ? 'Kết nối máy chủ Ubuntu' : 'Cấu hình triển khai nhanh';
  if (deploySubtitle) deploySubtitle.textContent = central
    ? 'Chỉ nhập địa chỉ Ubuntu và theo dõi trạng thái pairing. Máy này không cần API key hoặc Tunnel.'
    : 'Chỉ cần điền một lần, các thao tác khởi động, khởi động lại và kiểm tra sức khỏe sau đó sẽ do trợ lý tự động thực hiện.';
  if (!central) {
    state.centralWorkspaceCandidate = '';
    state.centralPolicyReceipt = null;
  }
  if (retryHandoff) {
    retryHandoff.hidden = !central || !retryable;
    retryHandoff.disabled = state.busy;
  }
  if (activationStatus && central) {
    activationStatus.textContent = retryable
      ? 'Chuyển vai trò đã được lưu nhưng activation chưa hoàn tất hoặc đã hết hạn. Hoàn thành pairing và liên kết tài khoản bên dưới, rồi bấm thử lại. Quyền thực thi vẫn đóng.'
      : snapshot?.status?.fullyReady === true && state.centralAuthorityStatus?.fresh === true && state.centralAuthorityStatus?.state === 'active'
        ? 'Runtime local và target được Ubuntu cấp đã sẵn sàng trong phạm vi quyền hiện tại.'
        : snapshot?.status?.fullyReady === true
          ? 'Runtime local đã sẵn sàng; tài khoản vẫn chưa có target dispatchable trên máy này.'
        : 'Đang xác minh executor; hãy hoàn thành pairing và liên kết tài khoản bên dưới. Đã chuyển vai trò không đồng nghĩa đã có kết nối hoặc quyền chạy.';
  }
  if (noticeText && central) {
    noticeText.textContent = `Runtime API Key và OpenAI Tunnel chính chỉ thuộc Ubuntu. ${route.label}: ${route.detail}`;
  }
  if (central) renderConnectionGuidance(snapshot);
  const enrollmentState = String(
    state.centralEnrollmentStatus?.state || state.centralEnrollmentReceipt?.state || ''
  ).toLowerCase();
  const enrollmentSubmitted = ['request_sent', 'pending_operator_approval', 'approved'].includes(enrollmentState);
  if (pairingInput) pairingInput.disabled = !central || state.centralEnrollmentBusy === true;
  if (pairingButton) {
    pairingButton.disabled = !central || development || state.busy || state.centralEnrollmentBusy === true
      || !state.centralEnrollmentStatusChecked || enrollmentSubmitted;
    pairingButton.title = development
      ? 'Mở bản cài đặt đã được xác minh để gửi yêu cầu kết nối.'
      : enrollmentSubmitted
        ? 'Yêu cầu pairing đã tồn tại; mở quản trị Ubuntu hoặc kiểm tra trạng thái máy.'
        : !state.centralEnrollmentStatusChecked
          ? 'Kiểm tra trạng thái máy trước khi gửi yêu cầu mới.'
          : '';
  }
  const enrollmentApproved = state.centralEnrollmentStatus?.state === 'approved';
  if (credentialRotation) credentialRotation.hidden = !central || !enrollmentApproved;
  if (credentialRotationButton) {
    credentialRotationButton.disabled = !central || development || state.busy || state.centralCredentialRotationBusy === true;
  }
  if (credentialRotationStatus && central && enrollmentApproved) {
    const rotation = state.centralCredentialRotationStatus;
    if (!rotation) {
      credentialRotationStatus.textContent = 'Credential được giữ lâu dài; chỉ đổi khi chủ máy xác nhận. Raw secret không rời node-agent.';
    } else if (rotation.fresh !== true) {
      credentialRotationStatus.textContent = 'Chưa nhận được receipt rotation (' + (rotation.error_code || 'trạng thái cũ') + '). Có thể thử lại; không tạo credential thủ công.';
    } else if (rotation.error_code) {
      credentialRotationStatus.textContent = 'Rotation chưa hoàn tất (' + rotation.error_code + '); node-agent sẽ tiếp tục từ phase durable khi thử lại.';
    } else {
      credentialRotationStatus.textContent = 'Rotation ' + rotation.state + '; generation ' + (rotation.next_generation || rotation.current_generation || 'hiện hành') + '. Raw secret chỉ nằm trong storage bảo vệ của node.';
    }
  }
  if (workspaceChoose) workspaceChoose.disabled = !central || development || state.busy || state.centralWorkspaceBusy === true;
  if (workspaceButton) workspaceButton.disabled = !central || development || state.busy || state.centralWorkspaceBusy === true
    || !String(state.centralWorkspaceCandidate || '').trim();
  if (workspaceRefresh) workspaceRefresh.disabled = !central || development || state.busy || state.centralWorkspaceListBusy === true;
  if (capabilityRead) {
    capabilityRead.checked = true;
    capabilityRead.disabled = true;
  }
  const selectedPreset = state.centralWorkspacePreset || centralWorkspacePresetFor(state.centralWorkspaceCapabilities);
  state.centralWorkspacePreset = selectedPreset;
  for (const input of capabilityPresets) {
    input.checked = input.value === selectedPreset;
    input.disabled = !central || development || state.busy || state.centralWorkspaceBusy === true;
  }
  if (customCapabilities) customCapabilities.open = selectedPreset === 'custom';
  if (capabilitySummary) {
    const preset = CENTRAL_WORKSPACE_PRESETS[selectedPreset] || CENTRAL_WORKSPACE_PRESETS.custom;
    capabilitySummary.textContent = preset.detail;
  }
  if (capabilityWrite) {
    capabilityWrite.checked = state.centralWorkspaceCapabilities.write === true;
    capabilityWrite.disabled = !central || development || selectedPreset !== 'custom' || state.busy || state.centralWorkspaceBusy === true;
  }
  if (capabilityExec) {
    capabilityExec.checked = state.centralWorkspaceCapabilities.exec === true;
    capabilityExec.disabled = !central || development || selectedPreset !== 'custom' || state.busy || state.centralWorkspaceBusy === true;
  }
  if (workspaceCandidate) {
    const candidate = String(state.centralWorkspaceCandidate || '').trim();
    workspaceCandidate.textContent = !central
      ? ''
      : candidate
        ? `Thư mục: ${candidate}`
        : 'Chưa chọn thư mục cục bộ để đăng ký.';
    workspaceCandidate.title = central ? candidate : '';
  }
  if (workspaceDevice) {
    const deviceName = String(snapshot?.device?.display_name || snapshot?.device?.device_id || 'thiết bị này');
    workspaceDevice.textContent = central ? `Máy: ${deviceName}` : '';
  }
  if (pairingStatus && central) {
    const enrollment = state.centralEnrollmentStatus;
    if (!enrollment && !state.centralEnrollmentReceipt) {
      pairingStatus.textContent = 'Chỉ gửi định danh máy tới Ubuntu. Không gửi API key, Tunnel ID hoặc thông tin đăng nhập OpenAI.';
    } else if (enrollment?.fresh !== true) {
      pairingStatus.textContent = 'Chưa có kết quả kiểm tra mới. Cấu hình đã lưu được giữ nguyên; chưa thể xác nhận kết nối Ubuntu.';
    } else if (enrollment?.state === 'approved') {
      pairingStatus.textContent = 'Ubuntu đã duyệt máy. Tiếp tục thêm thư mục và liên kết tài khoản.';
    } else if (enrollment?.state === 'revoked') {
      pairingStatus.textContent = 'Ubuntu đã thu hồi quyền của máy. Cần quản trị viên kiểm tra trước khi kết nối lại.';
    } else {
      pairingStatus.textContent = enrollment?.state === 'pending_operator_approval'
        ? 'Đã gửi yêu cầu. Đang chờ quản trị viên Ubuntu duyệt máy.'
        : 'Chưa xác nhận máy được duyệt. Xem bước xử lý bên dưới.';
    }
  }
  if (workspaceStatus && central && !state.centralWorkspaceReceipt) {
    workspaceStatus.textContent = 'Chọn thư mục và mức quyền; thao tác này không đổi workspace chính hoặc task đang có. Ubuntu không nhận path và đăng ký chưa tạo quyền chạy.';
  }
  if (workspaceStatus && central && state.centralWorkspaceReceipt) {
    const receipt = state.centralWorkspaceReceipt;
    const capabilities = receipt.capabilities || {};
    const capabilityLabel = centralWorkspaceCapabilityLabel(capabilities);
    workspaceStatus.textContent = `${receipt.replayed ? 'Đã xác nhận lại' : 'Đã thêm'} ${receipt.display_name} với mức quyền “${capabilityLabel}”. Chờ liên kết tài khoản chọn target riêng trước khi có action.`;
  }
  if (workspaceStatus && central && state.centralPolicyReceipt) {
    const receipt = state.centralPolicyReceipt;
    const expiry = new Date(receipt.expires_at_ms).toLocaleString();
    workspaceStatus.textContent = `Đã cài policy read-only cục bộ, hết hạn ${expiry}. Policy này không cấp ghi, shell hoặc quyền task mới.`;
  }
  renderCentralAuthorityStatus(central);
  renderCentralWorkspaceRegistrations(central);
  for (const selector of ['#runtimeKeyInput', '#saveRuntimeKey', '#removeRuntimeKey', '#tunnelIdInput', '#recoveryTunnelIdInput', '#saveRecoveryTunnel']) {
    const control = $(selector);
    if (control) control.disabled = central;
  }
  return { central, route };
}

function recoveryTunnelPresentation(source) {
  if (isCentralExecutor(source?.settings)) {
    return { state: 'not_configured', label: 'Do Ubuntu quản lý', detail: 'Central executor không dùng Recovery OpenAI Tunnel tại Windows.' };
  }
  if (source?.status?.signalStale === true || source?.signalStale === true) {
    return { state: 'connecting', label: 'Telemetry gián đoạn', detail: 'Đang giữ receipt gần nhất và chờ heartbeat mới từ Recovery Host.' };
  }
  const tunnel = source?.recoveryHost?.recovery_plane?.tunnel || null;
  const raw = String(tunnel?.state || '').toLowerCase();
  if (raw === 'healthy') return { state: 'connected', label: 'Đã kết nối', detail: 'Recovery Tunnel đã qua health check cục bộ.' };
  if (raw === 'starting') return { state: 'connecting', label: 'Đang kết nối', detail: 'Recovery Tunnel đang khởi tạo và chờ health check.' };
  if (raw === 'not_configured') return { state: 'not_configured', label: 'Chưa cấu hình', detail: 'Chưa có Recovery Tunnel ID riêng.' };
  if (raw === 'blocked_shared_tunnel_id') return { state: 'error', label: 'Bị chặn', detail: 'Recovery Tunnel ID đang trùng với Coding Tunnel ID chính.' };
  if (raw === 'blocked_missing_runtime_key') return { state: 'error', label: 'Thiếu Runtime Key', detail: 'Đã có Recovery Tunnel ID nhưng chưa có Runtime API Key khả dụng.' };
  if (raw.startsWith('blocked_')) return { state: 'error', label: 'Bị chặn', detail: `Recovery Tunnel báo trạng thái: ${raw}.` };
  if (raw) return { state: 'connecting', label: 'Đang xác minh lại', detail: `Recovery Tunnel tạm báo trạng thái: ${raw}.` };
  return { state: 'not_configured', label: 'Đang kiểm tra', detail: 'Chưa nhận được telemetry Recovery Tunnel từ Recovery Host.' };
}

function renderRecoveryTunnelSettings(source) {
  const presentation = recoveryTunnelPresentation(source);
  const badge = $('#recoveryTunnelSettingsBadge');
  const stateChip = $('#recoveryTunnelSettingsState');
  if (badge) {
    badge.textContent = presentation.label;
    badge.dataset.state = presentation.state;
  }
  if (stateChip) {
    stateChip.textContent = presentation.label;
    stateChip.dataset.state = presentation.state;
  }
  const detail = $('#recoveryTunnelSettingsStatus');
  if (detail) detail.textContent = presentation.detail;
}

function renderDevice(source) {
  const device = source?.device || {};
  const settings = source?.settings || state.snapshot?.settings || {};
  const recoveryHost = source?.recoveryHost || {};
  const displayName = String(device.display_name || recoveryHost.device_display_name || 'Thiết bị hiện tại');
  const deviceId = String(device.device_id || recoveryHost.device_id || '');
  const instanceId = String(device.device_instance_id || recoveryHost.device_instance_id || '');
  const online = device.online !== false && Boolean(deviceId);
  const git = device.git || {};
  const gitLabel = git.available ? `${git.branch || 'detached'} @ ${git.head_short || 'no-head'}${git.dirty ? ' · dirty' : ' · clean'}` : 'Không phải Git repo / chưa có dữ liệu';
  const coding = device.coding || {};
  const recovery = device.recovery || {};
  const central = isCentralExecutor(settings);
  const top = $('#topDeviceButton');
  if (top) { top.classList.remove('ready', 'warn'); top.classList.add(online ? (coding.mcp_running ? 'ready' : 'warn') : 'warn'); top.title = deviceId ? `Current device: ${deviceId}` : 'Device identity unavailable'; }
  if ($('#topDeviceName')) $('#topDeviceName').textContent = displayName;
  if ($('#topDeviceMeta')) $('#topDeviceMeta').textContent = `${device.registry || 'local'} · ${deviceId ? deviceId.slice(0, 8) : 'unknown'} · ${git.available ? `${git.branch || 'detached'} @ ${git.head_short || 'no-head'}` : 'Git n/a'}`;
  if ($('#deviceDisplayName')) $('#deviceDisplayName').textContent = displayName;
  if ($('#deviceOnline')) { $('#deviceOnline').textContent = online ? 'Online' : 'Unknown'; $('#deviceOnline').classList.toggle('neutral', !online); }
  if ($('#deviceId')) { $('#deviceId').textContent = deviceId || '—'; $('#deviceId').title = deviceId; }
  if ($('#deviceInstanceId')) { $('#deviceInstanceId').textContent = instanceId || '—'; $('#deviceInstanceId').title = instanceId; }
  if ($('#deviceWorkspace')) { $('#deviceWorkspace').textContent = device.workspace || settings.workspace || '—'; $('#deviceWorkspace').title = device.workspace || settings.workspace || ''; }
  if ($('#deviceGitState')) $('#deviceGitState').textContent = gitLabel;
  if ($('#deviceCodingState')) $('#deviceCodingState').textContent = central
    ? (coding.mcp_running ? 'Local executor ready · Ubuntu managed' : 'Local executor stopped')
    : (coding.mcp_running && coding.tunnel_running ? 'Coding ready' : coding.mcp_running ? 'MCP ready · Tunnel down' : 'Coding stopped');
  if ($('#deviceRecoveryState')) $('#deviceRecoveryState').textContent = central
    ? (recovery.mcp_running ? 'Recovery MCP local · no OpenAI Tunnel' : 'Recovery unavailable')
    : (recovery.mcp_running && recovery.tunnel_running ? 'Recovery ready' : recovery.mcp_running ? `Recovery MCP ready · ${recovery.tunnel_state || 'Tunnel down'}` : 'Recovery unavailable');
  if ($('#deviceCodingTunnelId')) $('#deviceCodingTunnelId').textContent = central
    ? 'OpenAI Tunnel: Ubuntu quản lý'
    : `Tunnel: ${coding.tunnel_id || settings.tunnelId || 'chưa cấu hình'}`;
  if ($('#deviceRecoveryTunnelId')) $('#deviceRecoveryTunnelId').textContent = central
    ? 'Recovery Tunnel: không dùng tại executor'
    : `Tunnel: ${recovery.tunnel_id || settings.recoveryTunnelId || 'chưa cấu hình'}`;
}

function renderSetupState(snapshot) {
  const settings = snapshot?.settings || {};
  const status = snapshot?.status || {};
  const environment = snapshot?.environment || {};
  const central = isCentralExecutor(settings);
  const inventoryKnown = !central || state.centralWorkspaceInventoryStatus === 'loaded';
  const inventoryUnknown = central && state.centralWorkspaceInventoryStatus !== 'loaded';
  const workspaceReady = central
    ? inventoryKnown && centralWorkspaceEntries().length > 0
    : environment.workspace?.exists === true && Boolean(settings.workspace);
  const directConnectionReady = Boolean(snapshot?.secrets?.runtimeApiKey) && Boolean(settings.tunnelId);
  // Enrollment is the first step; a verified execution route also depends on
  // workspace/policy. Waiting for that route here used to trap setup at step 1.
  const enrollmentReady = state.centralEnrollmentStatus?.fresh === true
    && state.centralEnrollmentStatus?.state === 'approved';
  const connectionReady = central ? enrollmentReady || status.centralConnected === true : directConnectionReady;
  const guidance = central ? centralSetupGuidance(snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus) : null;
  const authorityStatus = state.centralAuthorityStatus;
  const accountTargetReady = authorityStatus?.fresh === true
    && authorityStatus?.state === 'active'
    && Number(authorityStatus?.dispatchable_target_count || 0) > 0
    && Boolean(centralDispatchableTargetForLocalWorkspace());
  const authorityReady = central
    ? status.authorityReady === true && accountTargetReady
    : status.tunnelRunning === true;
  // The local runtime can be healthy before an account has selected a
  // binding. Settings must not call that state “ready to receive work”.
  const fullyReady = central
    ? workspaceReady && status.fullyReady === true && accountTargetReady
    : workspaceReady && status.fullyReady === true;
  const accessStepTitle = $('#setupStepAccount b');
  if (accessStepTitle) accessStepTitle.textContent = central ? 'Liên kết & quyền' : 'Kiểm tra kết nối';
  const steps = [
    ['setupStepConnection', connectionReady, central
      ? (connectionReady ? 'Máy đã được xác nhận' : guidance.title)
      : (directConnectionReady ? 'Tunnel và khóa đã lưu' : 'Cần cấu hình kết nối')],
    ['setupStepFolder', workspaceReady, workspaceReady
      ? 'Đã chọn thư mục local'
      : inventoryUnknown
        ? 'Chưa đọc được inventory · cần tải lại'
        : 'Chưa chọn thư mục'],
    ['setupStepAccount', authorityReady, central
      ? (accountTargetReady ? 'Đã có target được cấp' : authorityStatus?.state === 'no_binding' ? 'Chưa có liên kết tài khoản' : 'Chờ Ubuntu xác nhận target')
      : (status.tunnelRunning === true ? 'Tunnel đã phản hồi' : 'Chờ Tunnel phản hồi')],
    ['setupStepVerify', fullyReady, fullyReady ? 'Sẵn sàng nhận việc' : 'Chưa có receipt sẵn sàng']
  ];
  steps.forEach(([id, done, detail]) => {
    const item = $(`#${id}`);
    if (!item) return;
    const current = !done && ((id === 'setupStepConnection' && !connectionReady)
      || (id === 'setupStepFolder' && connectionReady && !workspaceReady)
      || (id === 'setupStepAccount' && connectionReady && workspaceReady && !authorityReady)
      || (id === 'setupStepVerify' && workspaceReady && authorityReady && !fullyReady));
    item.classList.toggle('done', done);
    item.classList.toggle('current', current);
    item.classList.toggle('blocked', !done && !current);
    const small = item.querySelector('small');
    if (small) small.textContent = detail;
    item.setAttribute('aria-label', `${item.querySelector('b')?.textContent || 'Bước'}: ${detail}`);
  });

  const summary = $('#setupSummaryTitle');
  const summaryText = $('#setupSummaryText');
  const badge = $('#setupSummaryBadge');
  const nextDetail = $('#setupNextDetail');
  const action = $('#setupPrimaryAction');
  const connectionSummary = $('#settingsConnectionSummary');
  const workspaceSummary = $('#settingsWorkspaceSummary');
  if (connectionSummary) connectionSummary.textContent = central
    ? (connectionReady ? 'Máy đã được xác nhận' : guidance.title)
    : (directConnectionReady ? 'Đã cấu hình direct' : 'Cần cấu hình kết nối');
  if (workspaceSummary) workspaceSummary.textContent = central
    ? inventoryUnknown
      ? 'Chưa xác minh inventory workspace · tải lại để phân biệt lỗi đọc với danh sách trống'
      : centralWorkspaceSummary()
    : workspaceReady ? settings.workspace : 'Chưa chọn thư mục';
  if (summary) summary.textContent = fullyReady
    ? 'Máy này đã sẵn sàng trong phạm vi quyền được cấp'
    : central && !connectionReady
      ? guidance.title
      : inventoryUnknown
        ? 'Chưa xác minh được inventory workspace'
        : !workspaceReady
          ? 'Chưa chọn thư mục làm việc'
        : 'Cần hoàn tất một bước thiết lập';
  if (summaryText) summaryText.textContent = fullyReady
    ? 'Sẵn sàng không có nghĩa đã nghiệm thu bản phát hành; bằng chứng ChatGPT vẫn được hiển thị riêng.'
    : central
      ? 'Cấu hình đã lưu. Không cần nhập context ID, token hoặc JSON để tiếp tục.'
      : 'Bạn có thể đóng cửa sổ; dữ liệu đã lưu sẽ xuất hiện lại khi mở Cài đặt.';
  if (badge) {
    badge.textContent = fullyReady ? 'SẴN SÀNG' : 'ĐANG CHỜ';
    badge.className = `soft-badge ${fullyReady ? 'positive' : 'neutral'}`;
  }
  if (nextDetail) {
    nextDetail.textContent = fullyReady
      ? 'Có thể mở Command Center để xem bằng chứng runtime.'
      : central && !connectionReady
        ? guidance.detail
      : inventoryUnknown
        ? `Không đọc được inventory workspace (${state.centralWorkspaceInventoryError || 'lỗi chưa rõ'}). Bấm tải lại; không đăng ký lại chỉ vì lỗi đọc.`
        : !workspaceReady
          ? 'Chọn một thư mục trước khi cấp quyền.'
        : !authorityReady
            ? (central ? 'Chờ target được liên kết và local policy hợp lệ; không tự tạo quyền.' : 'Chờ route/policy hợp lệ; không tự tạo quyền.')
            : 'Kiểm tra lại snapshot runtime hiện tại.';
  }
  if (action) {
    action.textContent = fullyReady
      ? 'Mở Command Center'
      : central && !connectionReady
        ? guidance.actionLabel
      : inventoryUnknown
        ? 'Tải lại inventory'
        : !workspaceReady
          ? 'Chọn thư mục'
          : central && !authorityReady
            ? 'Mở quản trị & liên kết tài khoản'
            : 'Kiểm tra lại';
    action.dataset.setupAction = fullyReady
      ? 'overview'
      : central && !connectionReady
        ? (guidance.action === 'check' ? 'check-connection' : 'deploy')
        : inventoryUnknown
          ? 'workspace-refresh'
          : !workspaceReady
            ? 'workspace'
          : central && !authorityReady
            ? 'account'
            : 'refresh';
  }
}

async function handleSetupPrimaryAction() {
  const action = $('#setupPrimaryAction')?.dataset.setupAction;
  if (action === 'check-connection') {
    await refreshSystemSetup();
    return;
  }
  if (action === 'workspace-refresh') {
    await refreshControlPlaneWorkspaces({ quiet: false });
    return;
  }
  if (action === 'overview' || action === 'deploy' || action === 'workspace' || action === 'account') {
    if (action === 'account') {
      navigate('deploy');
      // This is an explicit operator action: open the shared Ubuntu console
      // so the user can bind the account/target, while keeping the local card
      // read-only and truthful about what the client can observe.
      await openControlPlaneConsole();
      const card = $('#controlPlaneAuthorityStatusCard');
      if (card) requestAnimationFrame(() => card.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      return;
    }
    navigate(action);
    if (action === 'workspace') {
      if (isCentralExecutor(state.snapshot?.settings)) await chooseControlPlaneWorkspace();
      else await chooseWorkspace();
    }
    return;
  }
  await refreshSnapshot({ forceForms: false });
}

function navigate(page) {
  if (!pageMeta[page]) return;
  const setupPages = ['system', 'deploy', 'workspace', 'settings'];
  const inSetup = setupPages.includes(page);
  state.currentPage = page;
  document.body.dataset.setupView = inSetup ? page : '';
  if (location.hash !== `#${page}`) history.replaceState(null, '', `#${page}`);
  const primaryPage = inSetup || ['build', 'health', 'guide', 'logs'].includes(page) ? 'system' : page;
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.page === primaryPage));
  $$('.page').forEach((item) => item.classList.toggle('active', item.dataset.pageView === page
    || (inSetup && item.dataset.pageView === 'system')));
  $$('.setup-section-link').forEach((item) => {
    const selected = item.dataset.nav === page;
    item.classList.toggle('active', selected);
    if (selected) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
  let [eyebrow, title, subtitle] = pageMeta[inSetup ? 'system' : page];
  if (isCentralExecutor(state.snapshot?.settings)) {
    if (page === 'guide') {
      eyebrow = 'CENTRAL EXECUTOR';
      title = 'Hướng dẫn pairing với Ubuntu';
      subtitle = 'Theo dõi route evidence và policy action; connector OpenAI chỉ được quản lý tại server Ubuntu.';
    }
  }
  $('#pageEyebrow').textContent = eyebrow;
  $('#pageTitle').textContent = title;
  $('#pageSubtitle').textContent = subtitle;
  $('.content-viewport').scrollTop = 0;
  if (page === 'logs') loadLogs();
  if (page === 'task') loadTaskState();
  if (page === 'build') inspectBuild();
  if (page === 'health') inspectHealth();
}

function textOr(value, fallback = '—') { return String(value ?? '').trim() || fallback; }

function renderTaskList(container, items, render) {
  container.replaceChildren();
  if (!items?.length) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Chưa có bản ghi'; container.appendChild(empty); return;
  }
  items.forEach((item) => container.appendChild(render(item)));
}

function renderTaskState(payload) {
  const task = payload?.state;
  const hasTask = Boolean(task && (
    textOr(task.objective, '') ||
    textOr(task.current_step, '') ||
    textOr(task.next_step, '') ||
    (Array.isArray(task.steps) && task.steps.length) ||
    (task.status && task.status !== 'idle')
  ));
  $('#taskStateEmpty').hidden = hasTask;
  $('#taskStateContent').hidden = !hasTask;
  if (!hasTask) return;
  $('#taskObjective').textContent = textOr(task.objective, 'Chưa điền mục tiêu hiện tại');
  $('#taskId').textContent = textOr(task.task_id);
  $('#taskStatus').textContent = textOr(task.status, 'idle');
  $('#taskCurrentStep').textContent = textOr(task.current_step);
  $('#taskNextStep').textContent = textOr(task.next_step);
  $('#taskFailureRow').hidden = !task.failure;
  $('#taskFailure').textContent = textOr(task.failure);
  const steps = Array.isArray(task.steps) ? task.steps : [];
  const done = steps.filter((item) => item.status === 'completed').length;
  $('#taskStepCount').textContent = `${done} / ${steps.length}`;
  renderTaskList($('#taskSteps'), steps, (item) => { const row=document.createElement('div'); row.className=`task-step ${item.status || 'pending'}`; const mark=document.createElement('i'); mark.textContent=item.status==='completed'?'✓':item.status==='in_progress'?'→':item.status==='failed'?'!':'•'; const label=document.createElement('span'); label.textContent=textOr(item.text); row.append(mark,label); return row; });
  const command = task.current_command;
  $('#taskCommand').textContent = command ? `${textOr(command.command)}\n${textOr(command.status)} · ${textOr(command.workdir, '.')}` : 'Hiện không có lệnh nào đang chạy';
  const tests = Array.isArray(task.test_results) ? task.test_results.slice(-5).reverse() : [];
  renderTaskList($('#taskTests'), tests, (item) => { const row=document.createElement('div'); row.className=`task-result ${item.status}`; row.textContent=`${item.status === 'passed' ? 'Thành công' : 'Thất bại'} · ${textOr(item.command, 'Kiểm thử')} · ${item.duration_ms ?? 0} ms`; return row; });
  const files = Array.isArray(task.modified_files) ? task.modified_files.slice().reverse() : [];
  $('#taskFileCount').textContent = String(files.length);
  renderTaskList($('#taskFiles'), files, (item) => { const row=document.createElement('div'); row.className='task-file'; const op=document.createElement('b'); op.textContent=textOr(item.operation, 'update').slice(0,1).toUpperCase(); const file=document.createElement('span'); file.textContent=textOr(item.path); row.append(op,file); return row; });
  const report = task.last_build_report;
  const build = $('#taskBuild'); build.replaceChildren();
  if (!report) { build.textContent='Chưa chạy verify_build.'; }
  else {
    const summary=document.createElement('div'); summary.className=`build-summary ${report.overall_status}`; summary.textContent=`${report.overall_status === 'passed' ? 'Xác minh thành công' : 'Xác minh thất bại'} · ${textOr(report.project?.type)} · v${textOr(report.project?.version)}`; build.appendChild(summary);
    (report.artifacts || []).slice(0,8).forEach((item) => { const row=document.createElement('div'); row.className='task-artifact'; const path=document.createElement('span'); path.textContent=textOr(item.path); const hash=document.createElement('code'); hash.textContent=textOr(item.sha256 || item.sha384 || item.sha512).slice(0,16); row.append(path,hash); build.appendChild(row); });
    if (!(report.artifacts || []).length) { const empty=document.createElement('span'); empty.className='task-muted'; empty.textContent=textOr(report.failure, 'Không tìm thấy sản phẩm build'); build.appendChild(empty); }
  }
}

async function loadTaskState() {
  try {
    const [taskPayload] = await Promise.all([api.taskState(), loadTaskHistory(), loadPerformanceTrace()]);
    renderTaskState(unwrap(taskPayload));
  }
  catch (error) { toast('Đọc trạng thái nhiệm vụ thất bại', error.message, 'error'); }
}

function formatDuration(ms) {
  const value = Number(ms || 0);
  if (value < 1000) return `${value} ms`;
  if (value < 60000) return `${(value / 1000).toFixed(1)} giây`;
  return `${Math.floor(value / 60000)} phút ${Math.round((value % 60000) / 1000)} giây`;
}

function renderPerformanceTrace(trace) {
  const metrics = $('#performanceMetrics');
  const timeline = $('#performanceTimeline');
  metrics.replaceChildren(); timeline.replaceChildren();
  if (!trace || !trace.tool_calls) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Chưa có bản ghi hiệu năng'; metrics.append(empty); return;
  }
  const items = [
    ['Gọi công cụ', trace.tool_calls], ['Thực thi trên máy', formatDuration(trace.local_execution_ms)],
    ['Thời gian chờ ước tính', formatDuration(trace.estimated_wait_ms)], ['Trùng bộ nhớ đệm', trace.cache_hits || 0],
    ['Chắn lặp lại', trace.deduplicated_calls || 0], ['Thất bại', trace.errors || 0]
  ];
  items.forEach(([label, value]) => { const card=document.createElement('div'); card.className='performance-metric'; const b=document.createElement('b'); b.textContent=String(value); const span=document.createElement('span'); span.textContent=label; card.append(b,span); metrics.append(card); });
  (trace.recent || []).slice(-30).reverse().forEach((event) => {
    const row=document.createElement('div'); row.className='performance-event';
    const tool=document.createElement('b'); tool.textContent=textOr(event.tool);
    const local=document.createElement('span'); local.textContent=`Trên máy ${formatDuration(event.duration_ms)}`;
    const wait=document.createElement('span'); wait.textContent=`Thời gian chờ ${formatDuration(event.wait_before_ms)}`;
    const flag=document.createElement('span'); flag.textContent=event.deduplicated ? 'Đã lọc trùng' : event.cache_hit ? 'Bộ nhớ đệm' : event.ok ? 'Hoàn thành' : 'Thất bại'; if (event.cache_hit || event.deduplicated) flag.className='cache-hit';
    row.append(tool,local,wait,flag); timeline.append(row);
  });
}

async function loadPerformanceTrace() {
  try { renderPerformanceTrace(unwrap(await api.performanceTrace())); }
  catch (error) { renderPerformanceTrace(null); }
}

async function loadTaskHistory() {
  const container = $('#taskHistory');
  try {
    const items = unwrap(await api.taskHistory());
    renderTaskList(container, items, (task) => {
      const row = document.createElement('div'); row.className = 'task-history-item';
      const copy = document.createElement('div');
      const title = document.createElement('b'); title.textContent = textOr(task.objective, 'Nhiệm vụ chưa đặt tên');
      const meta = document.createElement('small'); meta.textContent = `${textOr(task.status, 'unknown')} · ${textOr(task.task_id)} · ${new Date(task.archived_at || task.updated_at || Date.now()).toLocaleString('vi-VN')}`;
      copy.append(title, meta); row.append(copy); return row;
    });
  } catch (error) { container.textContent = `Đọc thất bại: ${error.message}`; }
}

function applyTheme(theme) {
  document.body.dataset.theme = theme === 'light' ? 'light' : 'dark';
  $('#themeSelect').value = theme === 'light' ? 'light' : 'dark';
}

function applyFormValues(snapshot, force = false) {
  if (state.initializedForms && !force) return;
  const settings = snapshot.settings;
  state.selectedWorkspace = settings.workspace;
  $('#tunnelIdInput').value = settings.tunnelId || '';
  $('#recoveryTunnelIdInput').value = settings.recoveryTunnelId || '';
  if ($('#controlPlaneServerUrl')) $('#controlPlaneServerUrl').value = settings.controlPlaneServerUrl || '';
  $('#recoveryMcpEndpoint').textContent = `http://127.0.0.1:${settings.recoveryMcpPort || 18767}/mcp`;
  $('#proxyModeSelect').value = settings.proxyMode || 'auto';
  $('#proxyUrlInput').value = settings.proxyUrl || '';
  $('#mcpPortInput').value = settings.mcpPort;
  $('#healthPortInput').value = settings.healthPort;
  $('#startWithWindowsToggle').checked = Boolean(settings.startWithWindows);
  $('#keepRunningToggle').checked = settings.keepRunningOnClose;
  $('#autoStartToggle').checked = settings.autoStartServices;
  $('#progressReportSelect').value = String(settings.progressReportSeconds || 90);
  if ($('#toolModeSelect')) $('#toolModeSelect').value = 'smart';
  $$('input[name="permission"]').forEach((input) => {
    input.checked = input.value === settings.permissionMode;
    input.closest('.choice').classList.toggle('selected', input.checked);
  });
  applyTheme(settings.theme);
  restoreGuideProgress(settings.guideProgress || {});
  renderProxyControls();
  state.initializedForms = true;
}

function shortRevision(value) {
  const revision = String(value || '');
  return revision ? `${revision.slice(0, 12)}${revision.length > 12 ? '…' : ''}` : 'unknown';
}

function componentSourcePresentation(revision, { running = true, label = 'component' } = {}) {
  if (!running) return { state: 'STOPPED', detail: `${label} hiện không chạy.` };
  const runningRevision = String(revision?.running_revision || '');
  const diskRevision = String(revision?.disk_revision || '');
  if (runningRevision && diskRevision && runningRevision === diskRevision && revision?.update_pending !== true) {
    return { state: 'CURRENT', detail: `${shortRevision(runningRevision)} · running = disk` };
  }
  if (diskRevision) {
    return { state: 'STALE', detail: `${shortRevision(runningRevision)} → ${shortRevision(diskRevision)}` };
  }
  return { state: 'UNKNOWN', detail: `${label} chưa có revision receipt.` };
}

function connectorContractPresentation(status = {}) {
  const reported = String(status.connectorContractState || '').toUpperCase();
  const explicit = reported === 'COMPATIBLE_ACKNOWLEDGED' ? 'UNAVAILABLE' : reported;
  if (status.connectorAcknowledgementPending === true
    && ['UNCHANGED_ACKNOWLEDGED', 'CURRENT_ACKNOWLEDGED', 'CURRENT_COMPATIBLE_ACKNOWLEDGED'].includes(explicit)) {
    return {
      state: 'UNAVAILABLE',
      notice: true,
      message: 'Connector receipt đang mâu thuẫn: state đã acknowledged nhưng acknowledgement vẫn pending. Chờ runtime hội tụ trước khi hiển thị xanh.',
      toast: 'Connector acknowledgement chưa hội tụ; không dùng trạng thái xanh cũ.'
    };
  }
  if (explicit === 'UNCHANGED_ACKNOWLEDGED') {
    const activationClosed = status?.activationEpoch?.admission_open === false;
    return {
      state: explicit,
      notice: activationClosed,
      message: activationClosed
        ? 'SHA contract đã acknowledge, nhưng activation mới vẫn chờ discovery hoặc compatibility bootstrap bound với process hiện tại.'
        : 'Tool contract không đổi và SHA hiện tại đã được acknowledge.',
      toast: activationClosed
        ? 'Activation mới vẫn chờ connector freshness bound với process hiện tại.'
        : 'Tool contract không đổi và SHA hiện tại đã được acknowledge.'
    };
  }
  if (explicit === 'CURRENT_ACKNOWLEDGED') {
    return {
      state: explicit,
      notice: false,
      message: 'Tool contract hiện tại đã được discovery và acknowledge.',
      toast: 'Tool contract hiện tại đã được discovery và acknowledge.'
    };
  }
  if (explicit === 'CURRENT_COMPATIBLE_ACKNOWLEDGED') {
    return {
      state: explicit,
      notice: false,
      message: 'No-workspace compatibility bootstrap của đúng process/server/epoch đã được xác minh và Recovery Host ACK; connector hiện tại đã sẵn sàng theo contract tương thích.',
      toast: 'Compatibility bootstrap hiện tại đã được xác minh và acknowledge.'
    };
  }
  if (explicit === 'CHANGED_DISCOVERED_NEEDS_ACK') {
    return {
      state: explicit,
      notice: true,
      message: 'ChatGPT đã discovery contract SHA mới; acknowledgement chính thức vẫn đang chờ Recovery Host hoàn tất.',
      toast: 'Contract SHA mới đã được discovery; acknowledgement chính thức vẫn đang chờ.'
    };
  }
  if (explicit === 'CHANGED_NEEDS_DISCOVERY') {
    return {
      state: explicit,
      notice: true,
      message: 'Tool contract SHA đã đổi. ChatGPT cần discovery contract hiện tại hoặc thực hiện compatibility bootstrap an toàn khi gọi lại workspace_context.',
      toast: 'Connector chưa có discovery hoặc compatibility bootstrap cho activation hiện tại.'
    };
  }
  if (explicit === 'CHANGED_COMPATIBLE_NEEDS_ACK' || explicit === 'UNCHANGED_COMPATIBLE_NEEDS_ACK') {
    return {
      state: explicit,
      notice: true,
      message: 'Đã có no-workspace compatibility bootstrap bound đúng process/epoch; Recovery Host đang hoàn tất ACK chính thức.',
      toast: 'Compatibility bootstrap hợp lệ; đang chờ Recovery Host ACK.'
    };
  }
  if (explicit === 'UNAVAILABLE') {
    return {
      state: explicit,
      notice: false,
      message: 'Chưa có tool contract runtime để đánh giá connector freshness.',
      toast: 'Tool contract runtime hiện chưa khả dụng.'
    };
  }
  if (explicit || typeof status.connectorRefreshRequired !== 'boolean') {
    return {
      state: 'UNAVAILABLE',
      notice: false,
      message: explicit
        ? `Connector contract state không được nhận diện: ${explicit}.`
        : 'Chưa có connector contract state hoặc refresh receipt để đánh giá freshness.',
      toast: 'Connector contract freshness hiện chưa khả dụng.'
    };
  }
  // A legacy boolean can tell us that no refresh is requested, but cannot
  // prove the authenticated acknowledgement/discovery state required by the
  // current closure contract. Keep it visibly unavailable until the enum is
  // present.
  return {
    state: 'UNAVAILABLE',
    notice: false,
    message: 'Runtime chỉ cung cấp cờ tương thích cũ; chưa có connectorContractState để chứng minh freshness/acknowledgement.',
    toast: 'Connector contract freshness hiện chưa có receipt đủ mạnh.'
  };
}

// The backend is the authority for computing activation closure, but the
// renderer must not hide the warning merely because an untrusted/stale
// snapshot happens to contain closure_state="LIVE_CLOSED".  Keep this check
// deliberately redundant and fail-closed: every gate that is rendered green
// must be present, true, and agree with the current runtime status.
function activationClosureDisplayState(closure, status = {}) {
  const value = closure && typeof closure === 'object' ? closure : {};
  const requiredTrue = [
    'closure_input_schema_supported',
    'checkpoint_identity_valid',
    'source_accepted',
    'accepted_receipts_complete',
    'activation_eligible',
    'affected_components_valid',
    'component_receipts_valid',
    'postflight_receipts_valid',
    'lifecycle_clean',
    'components_current',
    'connector_contract_current',
    'runtime_fully_ready'
  ];
  const missingGate = requiredTrue.find((key) => value[key] !== true);
  if (missingGate) return { liveClosed: false, reason: missingGate };
  if (String(value.closure_state || '') !== 'LIVE_CLOSED') return { liveClosed: false, reason: 'closure_state' };
  if (Number(value.schema_version) !== 1) return { liveClosed: false, reason: 'schema_version' };
  if (!String(value.source_checkpoint_id || '').trim()
    || !String(value.run_id || '').trim()
    || !String(value.wave_id || '').trim()
    || !String(value.proof_fingerprint || '').trim()
    || !String(value.accepted_head || '').trim()) {
    return { liveClosed: false, reason: 'checkpoint_identity' };
  }
  if (value.release_state !== 'NOT_RELEASED' || value.production_state !== 'NOT_CLAIMED') {
    return { liveClosed: false, reason: 'release_claim_separation' };
  }
  // If the closure projection carries these fields, they are authenticated
  // runtime facts and must not contradict the point-in-time status.
  if (Object.hasOwn(value, 'connector_refresh_required') && value.connector_refresh_required !== false) {
    return { liveClosed: false, reason: 'connector_refresh_required' };
  }
  if (Object.hasOwn(value, 'runtime_running') && value.runtime_running !== true) {
    return { liveClosed: false, reason: 'runtime_running' };
  }
  const centralExecutor = status.executionRole === 'central_executor';
  if (!centralExecutor && Object.hasOwn(value, 'tunnel_running') && value.tunnel_running !== true) {
    return { liveClosed: false, reason: 'tunnel_running' };
  }
  if (centralExecutor && (
    (Object.hasOwn(value, 'central_connected') && value.central_connected !== true)
    || (Object.hasOwn(value, 'authority_ready') && value.authority_ready !== true)
  )) {
    return { liveClosed: false, reason: 'central_route_evidence' };
  }
  if (status.runtimeRunning !== true || status.fullyReady !== true || (!centralExecutor && status.tunnelRunning !== true)
    || (centralExecutor && (status.centralConnected !== true || status.authorityReady !== true || status.centralStatusReason != null))) {
    return { liveClosed: false, reason: 'runtime_status_disagreement' };
  }
  return { liveClosed: true, reason: null };
}

function renderRuntimeSourceStatus(snapshot) {
  const status = snapshot?.status || {};
  const central = isCentralExecutor(snapshot?.settings);
  const route = centralRoutePresentation(status);
  const recoveryHost = snapshot?.recoveryHost || {};
  const uiRecovery = recoveryHost.electron_ui_recovery || {};
  const electron = componentSourcePresentation(recoveryHost.electron_ui_revision, {
    running: uiRecovery.alive === true,
    label: 'Electron UI'
  });
  const recovery = componentSourcePresentation(recoveryHost.code_revision, {
    running: recoveryHost.state === 'healthy',
    label: 'Recovery Host'
  });
  const coding = componentSourcePresentation(status.codeRevision?.codingMcp, {
    running: status.runtimeRunning === true,
    label: 'Coding MCP'
  });
  const tunnel = central
    ? { state: route.state === 'connected' ? 'CENTRAL' : 'WAITING', detail: `${route.label} · ${route.detail}` }
    : (status.tunnelRunning === true
      ? { state: 'READY', detail: 'Tunnel READY · health receipt present' }
      : { state: 'STOPPED', detail: 'Tunnel hiện chưa kết nối.' });
  const sourcePresentations = [electron, recovery, coding];
  const bindings = [
    ['#runtimeElectronState', '#runtimeElectronMeta', electron, uiRecovery.pid ? `PID ${uiRecovery.pid} · ${uiRecovery.runtime_mode || 'unknown'} · ${electron.detail}` : electron.detail],
    ['#runtimeRecoveryState', '#runtimeRecoveryMeta', recovery, recovery.detail],
    ['#runtimeMcpSourceState', '#runtimeMcpSourceMeta', coding, coding.detail],
    ['#runtimeTunnelSourceState', '#runtimeTunnelSourceMeta', tunnel, tunnel.detail]
  ];
  bindings.forEach(([stateSelector, metaSelector, presentation, detail]) => {
    const stateElement = $(stateSelector);
    const metaElement = $(metaSelector);
    if (stateElement) {
      stateElement.textContent = presentation.state;
      stateElement.dataset.state = presentation.state.toLowerCase();
    }
    if (metaElement) metaElement.textContent = detail;
  });
  const stale = sourcePresentations.filter((item) => item.state === 'STALE').length;
  const current = sourcePresentations.filter((item) => item.state === 'CURRENT').length;
  const tunnelReady = central ? route.state === 'connected' : tunnel.state === 'READY';
  const summary = $('#runtimeSourceSummary');
  if (summary) {
    summary.textContent = stale
      ? `SOURCE STALE · ${stale}/3 pending · ${central ? 'CENTRAL' : 'TUNNEL'} ${tunnel.state}`
      : `SOURCE ${current}/3 CURRENT · ${central ? 'CENTRAL' : 'TUNNEL'} ${tunnel.state}`;
    summary.className = `cc-pill ${stale ? 'is-blocked' : current === 3 && tunnelReady ? 'is-active' : 'is-waiting'}`;
  }
  const notice = $('#sourceUpdateNotice');
  if (notice) notice.hidden = stale === 0;
  const message = $('#sourceUpdateMessage');
  if (message && stale) {
    message.textContent = `${stale} component đang chạy revision khác disk. Dùng controlled activation hoặc npm run dev; service health không thay thế loaded-source proof.`;
  }
  const closure = recoveryHost.activation_closure || snapshot?.activationClosure || status.activationClosure || {};
  const closureState = String(closure.closure_state || 'UNAVAILABLE');
  const closureDisplay = activationClosureDisplayState(closure, status);
  const liveClosed = closureDisplay.liveClosed;
  const closureElement = $('#runtimeClosureState');
  if (closureElement) {
    closureElement.textContent = closureState;
    closureElement.dataset.state = liveClosed ? 'current' : 'stale';
  }
  const closureMeta = $('#runtimeClosureMeta');
  if (closureMeta) {
    const checkpoint = shortRevision(closure.source_checkpoint_id);
    closureMeta.textContent = `${checkpoint} · release ${closure.release_state || 'NOT_RELEASED'} · production ${closure.production_state || 'NOT_CLAIMED'}`;
  }
  const closureNotice = $('#activationClosureNotice');
  if (closureNotice) closureNotice.hidden = liveClosed;
  const closureMessage = $('#activationClosureMessage');
  if (closureMessage && !liveClosed) {
    closureMessage.textContent = `${closureState}: source acceptance, exact postflight, connector freshness và runtime readiness phải cùng thuộc checkpoint hiện tại (${closureDisplay.reason}).`;
  }
}

function renderSnapshot(snapshot, options = {}) {
  state.snapshot = snapshot;
  applyFormValues(snapshot, options.forceForms);
  const { settings, secrets, environment, status } = snapshot;
  state.selectedWorkspace = settings.workspace;
  const { central, route: centralRoute } = renderCentralExecutorMode(snapshot);
  const localRuntimeReady = status.fullyReady === true;
  const accountTargetReady = central
    && state.centralAuthorityStatus?.fresh === true
    && state.centralAuthorityStatus?.state === 'active'
    && Number(state.centralAuthorityStatus?.dispatchable_target_count || 0) > 0
    && Boolean(centralDispatchableTargetForLocalWorkspace());
  const ready = central ? localRuntimeReady && accountTargetReady : localRuntimeReady;
  renderRecoveryTunnelSettings(snapshot);
  renderDevice(snapshot);
  renderRuntimeSourceStatus(snapshot);

  const activationIncomplete = status.updateIncomplete === true
    || status.activationEpoch?.update_incomplete === true
    || status.activationEpoch?.state === 'UPDATE_INCOMPLETE';
  $('#sideRuntimeText').textContent = central
    ? (ready ? 'Executor Ubuntu đã sẵn sàng nhận việc' : localRuntimeReady ? 'Runtime local sẵn sàng · chờ target' : `${centralRoute.label}`)
    : (ready
      ? 'Dịch vụ sẵn sàng'
      : activationIncomplete
        ? 'Đang hoàn tất activation epoch'
        : status.runtimeRunning ? 'Đang chờ Tunnel' : 'Dịch vụ chưa chạy');
  setDot($('#sideRuntimeDot'), ready ? 'ready' : status.runtimeRunning ? 'warn' : 'error');
  $('#sideWorkspace').textContent = settings.workspace || 'Chưa chọn thư mục làm việc';
  $('#sideMcp').textContent = status.runtimeRunning ? 'ON' : 'OFF';
  $('#sideTunnel').textContent = central ? 'UBUNTU' : (status.tunnelRunning ? 'ON' : 'OFF');

  $('#runtimeStatus').textContent = environment.python.installed ? 'Môi trường bình thường' : 'Thiếu môi trường runtime';
  $('#runtimeMeta').textContent = environment.python.version || 'Không tìm thấy Python tích hợp';
  setDot($('#runtimeDot'), environment.python.installed ? 'ready' : 'error');

  $('#mcpStatus').textContent = status.runtimeRunning ? 'Đang chạy bình thường' : 'Chưa khởi động';
  $('#mcpMeta').textContent = status.localMcpUrl;
  setDot($('#mcpDot'), status.runtimeRunning ? 'ready' : 'error');
  $('#tunnelStatus').textContent = central
    ? 'Do Ubuntu quản lý'
    : (status.tunnelRunning ? 'Đã kết nối' : 'Chưa kết nối');
  $('#tunnelMeta').textContent = central
    ? `${centralRoute.label} · ${centralRoute.detail}`
    : (settings.tunnelId || 'Chưa điền Tunnel ID');
  setDot($('#tunnelDot'), central ? (centralRoute.state === 'connected' ? 'ready' : 'warn') : (status.tunnelRunning ? 'ready' : settings.tunnelId ? 'warn' : 'error'));
  $('#workspaceStatus').textContent = environment.workspace.exists ? 'Đã ủy quyền' : 'Chưa chọn';
  $('#workspaceMeta').textContent = settings.workspace || 'Chỉ thư mục được chọn mới có thể được MCP truy cập';
  setDot($('#workspaceDot'), environment.workspace.exists ? 'ready' : 'error');
  $('#selectedWorkspace').textContent = settings.workspace || 'Chưa chọn thư mục';
  renderAuthorizedRoots(settings.authorizedRoots || []);

  $('#heroBadge').textContent = central
    ? (ready ? 'Executor central sẵn sàng nhận việc' : localRuntimeReady ? 'CENTRAL EXECUTOR · chờ liên kết target' : `CENTRAL EXECUTOR · ${centralRoute.label}`)
    : (ready ? 'Tất cả dịch vụ đang hoạt động bình thường' : activationIncomplete ? 'UPDATE_INCOMPLETE · đang đồng bộ runtime' : 'Chưa hoàn tất triển khai');
  $('#heroTitle').textContent = central
    ? (ready ? 'Máy thực thi được Ubuntu quản lý' : localRuntimeReady ? 'Runtime local đã sẵn sàng, còn chờ target' : 'Máy thực thi được Ubuntu quản lý')
    : (ready ? 'Workspace lập trình web đã sẵn sàng' : 'Cho phép Web Chat truy cập an toàn thư mục mã nguồn của bạn');
  $('#heroText').textContent = central
    ? `Không cần Runtime API Key hoặc OpenAI Tunnel tại máy này. ${centralRoute.detail}${localRuntimeReady && !accountTargetReady ? ' Runtime local có thể sống nhưng chưa có binding/target được cấp cho tài khoản.' : ''}`
    : (ready
      ? 'Hiện đang chạy qua môi trường portable tích hợp, trang web chỉ có thể truy cập thư mục làm việc đã chọn.'
      : 'Chọn một thư mục làm việc, cấu hình OpenAI Tunnel, sau đó trợ lý sẽ hoàn tất việc khởi động MCP, xác thực, kiểm tra sức khỏe và chẩn đoán sự cố.');
  $('#heroStartButton').textContent = ready ? 'Triển khai lại' : (central ? 'Mở kết nối Ubuntu' : 'Bắt đầu triển khai');
  $('#topStartButton').textContent = central ? 'Thiết lập hệ thống' : ready ? 'Triển khai lại' : 'Khởi động nhanh';
  renderSetupState(snapshot);

  $('#runtimeKeyHint').textContent = central ? 'Không dùng tại central executor; Ubuntu giữ credential.' : (secrets.runtimeApiKey ? 'Đã lưu bằng kho lưu trữ an toàn Windows' : 'Chưa lưu');
  $('#runtimeKeyHint').style.color = central || secrets.runtimeApiKey ? 'var(--green)' : '';
  $('#settingsKeyState').textContent = central ? 'Ubuntu quản lý credential' : (secrets.runtimeApiKey ? 'Đã mã hóa và lưu' : 'Chưa lưu');
  $('#guideLocalUrl').textContent = central ? 'MCP nội bộ executor · không public' : status.localMcpUrl;
  $('#guideTunnelId').textContent = central ? 'Ubuntu quản lý' : (settings.tunnelId || 'Chưa điền');
  const connector = connectorContractPresentation(status);
  const connectorContractNotice = $('#connectorContractNotice');
  if (connectorContractNotice) {
    connectorContractNotice.hidden = !connector.notice;
    if (connector.notice) {
      const shortHash = status.toolContract?.sha256 ? `${status.toolContract.sha256.slice(0, 12)}…` : 'không xác định';
      $('#connectorContractMessage').textContent = `${connector.message} SHA hiện tại: ${shortHash}.`;
    }
  }
  renderEnvironment(environment);
  renderDeploySummary();
}

function renderAuthorizedRoots(roots) {
  const container = $('#authorizedRootsList');
  if (!container) return;
  container.replaceChildren();
  if (!roots.length) {
    const empty = document.createElement('span');
    empty.className = 'task-muted';
    empty.textContent = 'Chưa thêm thư mục ủy quyền bổ sung';
    container.appendChild(empty);
    return;
  }
  roots.forEach((root) => {
    const row = document.createElement('div');
    row.className = 'authorized-root-row';
    const code = document.createElement('code');
    code.textContent = root;
    code.title = root;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'danger-button';
    remove.textContent = 'Xóa';
    remove.addEventListener('click', () => removeAuthorizedRoot(root));
    row.append(code, remove);
    container.appendChild(row);
  });
}

async function addAuthorizedRoot() {
  try {
    const selected = unwrap(await api.chooseWorkspace());
    if (!selected) return;
    const current = state.snapshot?.settings?.authorizedRoots || [];
    if (current.some((item) => item.toLowerCase() === selected.toLowerCase())) {
      toast('Thư mục đã được ủy quyền', selected);
      return;
    }
    const snapshot = unwrap(await api.updateAuthorizedRoots([...current, selected]));
    renderSnapshot(snapshot, { forceForms: true });
    toast('Đã thêm thư mục ủy quyền', selected);
  } catch (error) { toast('Ủy quyền thư mục thất bại', error.message, 'error'); }
}

async function removeAuthorizedRoot(root) {
  try {
    const current = state.snapshot?.settings?.authorizedRoots || [];
    const snapshot = unwrap(await api.updateAuthorizedRoots(current.filter((item) => item !== root)));
    renderSnapshot(snapshot, { forceForms: true });
    toast('Đã xóa thư mục ủy quyền', root);
  } catch (error) { toast('Xóa ủy quyền thất bại', error.message, 'error'); }
}

function renderEnvironment(environment) {
  setDot($('#envPythonDot'), environment.python.installed ? 'ready' : 'error');
  $('#envPythonText').textContent = environment.python.installed ? environment.python.version : 'Không tìm thấy Python 3.11+';
  const proxy = environment.proxy;
  const sourceLabels = {
    'auto-direct': 'Tự động phát hiện · Kết nối trực tiếp', 'auto-system': 'Tự động phát hiện · Proxy hệ thống Windows', 'auto-local': 'Tự động phát hiện · Proxy cục bộ',
    'system': 'Proxy hệ thống Windows', 'system-direct': 'Hệ thống không đặt Proxy · Kết nối trực tiếp', manual: 'Proxy thủ công', direct: 'Bắt buộc kết nối trực tiếp',
    'auto-unavailable': 'Không tìm thấy tuyến đường mạng khả dụng', error: 'Kiểm tra proxy thất bại'
  };
  setDot($('#envProxyDot'), proxy.reachable ? 'ready' : 'error');
  $('#envProxyText').textContent = `${sourceLabels[proxy.source] || 'Kiểm tra mạng'}${proxy.url ? ` · ${proxy.url}` : ''}`;
  $('#proxyHint').textContent = proxy.reachable ? 'Tuyến đường mạng hiện tại đã qua xác minh kết nối thực tế.' : 'Tuyến đường hiện tại chưa qua xác minh, có thể kiểm tra lại hoặc chọn proxy thủ công.';
}

function renderProxyControls() {
  const manual = $('#proxyModeSelect').value === 'manual';
  $('#manualProxyField').classList.toggle('disabled', !manual);
  $('#proxyUrlInput').disabled = !manual;
}

function renderDeploySummary() {
  const snapshot = state.snapshot;
  if (!snapshot) return;
  const missing = [];
  const workspace = state.selectedWorkspace || snapshot.settings.workspace;
  if (isCentralExecutor(snapshot.settings)) {
    const route = centralRoutePresentation(snapshot.status || {});
    if (!workspace) missing.push('Thư mục làm việc');
    const authority = authorityStatusPresentation(state.centralAuthorityStatus);
    $('#deploySummary').textContent = missing.length
      ? `Central executor còn cần: ${missing.join('、')}. Không cần Runtime API Key hay Tunnel ID tại Windows.`
      : `${route.label}. ${route.detail} ${authority.label}. Không cần Runtime API Key hay Tunnel ID tại Windows.`;
    return;
  }
  const tunnelId = $('#tunnelIdInput').value.trim();
  if (!workspace) missing.push('Thư mục làm việc');
  if (!tunnelId) missing.push('Tunnel ID');
  if (!snapshot.secrets.runtimeApiKey && !$('#runtimeKeyInput').value.trim()) missing.push('Runtime API Key');
  $('#deploySummary').textContent = missing.length ? `Còn cần điền: ${missing.join('、')}` : 'Cấu hình cần thiết cho chế độ portable đã hoàn tất.';
}

async function reconcileControlPlaneEnrollment({ quiet = true } = {}) {
  if (!isCentralExecutor(state.snapshot?.settings) || typeof api.reconcileControlPlaneEnrollment !== 'function') return null;
  if (centralSetupDevelopmentBlocked()) return null;
  try {
    const status = unwrap(await api.reconcileControlPlaneEnrollment());
    state.centralEnrollmentStatusChecked = true;
    state.centralEnrollmentStatus = status;
    if (status?.enrollment_id) {
      state.centralEnrollmentReceipt = {
        enrollment_id: status.enrollment_id,
        device_id: status.device_id,
        state: status.state,
        server_origin: status.server_origin || null
      };
    }
    // The server origin is credential-free resume metadata owned by the
    // node-agent.  Keep the current snapshot/input in sync immediately; the
    // main process persists it only when the ordinary setting is empty.
    if (status?.server_origin && state.snapshot?.settings
      && !String(state.snapshot.settings.controlPlaneServerUrl || '').trim()) {
      state.snapshot.settings.controlPlaneServerUrl = status.server_origin;
      const field = $('#controlPlaneServerUrl');
      if (field) field.value = status.server_origin;
    }
    return status;
  } catch (error) {
    state.centralEnrollmentStatusChecked = false;
    state.centralEnrollmentStatus = {
      ...(state.centralEnrollmentStatus || {}), fresh: false,
      error_code: error?.code || error?.message || 'CONTROL_PLANE_ENROLLMENT_STATUS_FAILED'
    };
    if (!quiet) toast('Không thể đồng bộ trạng thái pairing', error.message, 'warning');
    return null;
  } finally {
    if (state.snapshot) {
      renderCentralExecutorMode(state.snapshot);
      renderSetupState(state.snapshot);
    }
  }
}

async function refreshSystemSetup() {
  const button = $('#refreshSystemSetup');
  if (button?.disabled) return;
  if (button) button.disabled = true;
  try {
    await refreshSnapshot({ forceForms: false });
    if (isCentralExecutor(state.snapshot?.settings)
      && !centralSetupRuntimeBlocked(centralSetupGuidance(state.snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus))) {
      await reconcileControlPlaneEnrollment({ quiet: false });
      await reconcileControlPlaneAuthorityStatus({ quiet: false });
      await refreshControlPlaneWorkspaces({ quiet: true });
    }
  } catch (error) {
    toast('Chưa kiểm tra được thiết lập', error.message, 'warning');
  } finally {
    if (button) button.disabled = false;
    if (state.snapshot) renderSetupState(state.snapshot);
  }
}

function authorityStatusPresentation(status) {
  if (!status) return { state: 'unknown', label: 'Chưa kiểm tra', detail: 'Kiểm tra này chỉ đọc trạng thái Ubuntu; không tạo binding hoặc cấp quyền.' };
  if (status.fresh !== true) return { state: 'unknown', label: 'Chưa kiểm tra được', detail: `Giữ nguyên cấu hình hiện tại; lần kiểm tra gần nhất chưa có receipt (${status.error_code || 'trạng thái cũ'}).` };
  const count = Number(status.dispatchable_target_count || 0);
  switch (status.state) {
    case 'pending_operator_approval': return { state: 'waiting', label: 'Chờ Ubuntu duyệt máy', detail: 'Enrollment mới chỉ xác minh identity; chưa có liên kết tài khoản hoặc quyền chạy.' };
    case 'no_binding': return { state: 'waiting', label: 'Chưa có liên kết tài khoản', detail: status.workspace_count ? 'Workspace local đã đăng ký, nhưng tài khoản chưa chọn target cho máy này.' : 'Hãy đăng ký workspace local trước, sau đó chọn target từ tài khoản ChatGPT.' };
    case 'active': return { state: 'connected', label: 'Đã có target được cấp', detail: `${count} target có thể được chọn theo binding và generation hiện tại.` };
    case 'binding_revoked': return { state: 'error', label: 'Binding đã bị thu hồi', detail: 'Ubuntu vẫn giữ lịch sử để tránh failover âm thầm; cần liên kết target mới.' };
    case 'workspace_missing': return { state: 'error', label: 'Workspace chưa được đăng ký', detail: 'Binding còn tồn tại nhưng workspace hiện tại chưa có registration hợp lệ trên máy này.' };
    case 'workspace_retired': return { state: 'error', label: 'Workspace đã ngừng dùng', detail: 'Generation cũ đã bị fence; không tự đổi sang thư mục khác.' };
    case 'revoked': return { state: 'error', label: 'Máy đã bị Ubuntu thu hồi', detail: 'Không tự đăng ký lại hoặc cấp credential mới từ màn hình này.' };
    case 'blocked': return { state: 'warning', label: 'Target đã có nhưng đang bị chặn', detail: 'Xem chi tiết target và blocker; trạng thái này không chứng minh có thể chạy task.' };
    default: return { state: 'unknown', label: 'Chưa xác định', detail: 'Ubuntu trả về trạng thái chưa được UI diễn giải.' };
  }
}

function renderCentralAuthorityStatus(central) {
  const card = $('#controlPlaneAuthorityStatusCard');
  const badge = $('#controlPlaneAuthorityStatusBadge');
  const detail = $('#controlPlaneAuthorityStatusText');
  const targets = $('#controlPlaneAuthorityTargets');
  const refresh = $('#refreshControlPlaneAuthorityStatus');
  if (!card || !badge || !detail || !targets) return;
  card.hidden = !central;
  if (!central) return;
  const presentation = authorityStatusPresentation(state.centralAuthorityStatus);
  badge.textContent = presentation.label;
  badge.dataset.state = presentation.state;
  detail.textContent = presentation.detail;
  targets.replaceChildren();
  if (state.centralAuthorityBusy) {
    const loading = document.createElement('span');
    loading.className = 'task-muted';
    loading.textContent = 'Đang đọc liên kết tài khoản từ Ubuntu…';
    targets.append(loading);
  } else if (state.centralAuthorityStatus?.fresh === true && state.centralAuthorityStatus.targets?.length) {
    for (const target of state.centralAuthorityStatus.targets) {
      const row = document.createElement('div');
      row.className = 'authority-target-row';
      const label = document.createElement('b');
      label.textContent = `${target.node_display_name} · ${target.workspace_display_name}`;
      const meta = document.createElement('small');
      const capabilities = ['read', 'write', 'exec'].filter((name) => target.capabilities?.[name] === true).join('/') || 'none';
      meta.textContent = `${capabilities} · ${target.dispatch_state === 'dispatchable' ? 'được cấp' : 'bị chặn'} · ${target.presence_state}`;
      row.append(label, meta);
      targets.append(row);
    }
  } else {
    const empty = document.createElement('span');
    empty.className = 'task-muted';
    empty.textContent = 'Không có target nào được hiển thị ở máy này.';
    targets.append(empty);
  }
  if (refresh) refresh.disabled = !central || state.busy || state.centralAuthorityBusy
    || centralSetupRuntimeBlocked(centralSetupGuidance(state.snapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus));
}

async function reconcileControlPlaneAuthorityStatus({ quiet = true } = {}) {
  if (!isCentralExecutor(state.snapshot?.settings) || typeof api.reconcileControlPlaneAuthorityStatus !== 'function') return null;
  if (centralSetupDevelopmentBlocked()) return null;
  state.centralAuthorityBusy = true;
  if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  try {
    const status = unwrap(await api.reconcileControlPlaneAuthorityStatus());
    state.centralAuthorityStatus = status;
    if (state.snapshot) {
      renderCentralExecutorMode(state.snapshot);
      renderSetupState(state.snapshot);
    }
    return status;
  } catch (error) {
    if (!quiet) toast('Không thể kiểm tra liên kết tài khoản', error.message, 'warning');
    state.centralAuthorityStatus = {
      ...(state.centralAuthorityStatus || {}),
      fresh: false,
      error_code: error?.code || error?.message || 'CONTROL_PLANE_AUTHORITY_STATUS_FAILED'
    };
    return null;
  } finally {
    state.centralAuthorityBusy = false;
    if (state.snapshot) {
      renderCentralExecutorMode(state.snapshot);
      renderSetupState(state.snapshot);
    }
  }
}

async function rotateControlPlaneCredential() {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Đổi credential Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Đổi credential Ubuntu');
  if (state.centralEnrollmentStatus?.state !== 'approved') {
    throw new Error('Ubuntu phải duyệt máy trước khi đổi credential.');
  }
  if (typeof api.rotateControlPlaneCredential !== 'function') {
    throw new Error('Build hiện tại chưa hỗ trợ rotation credential.');
  }
  const accepted = window.confirm(
    'Đổi credential riêng của máy với Ubuntu? Node-agent sẽ lưu candidate bảo vệ, giữ credential cũ trong cửa sổ chuyển tiếp và chỉ thu hồi key cũ sau ACK. Raw credential không hiển thị trong giao diện.'
  );
  if (!accepted) return null;
  state.centralCredentialRotationBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    const status = unwrap(await api.rotateControlPlaneCredential({ confirmRotation: true }));
    state.centralCredentialRotationStatus = status;
    if (status?.error_code) {
      toast('Rotation credential chưa hoàn tất', status.error_code, 'warning');
    } else {
      toast('Đã xử lý rotation credential', 'Generation ' + (status?.next_generation || status?.current_generation || 'hiện hành') + ' đã được ghi nhận.', 'success');
    }
    await refreshSnapshot({ forceForms: false });
    await reconcileControlPlaneEnrollment({ quiet: true });
    return status;
  } finally {
    state.centralCredentialRotationBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function refreshSnapshot(options = {}) {
  try {
    const snapshot = unwrap(await api.snapshot(options));
    renderSnapshot(snapshot, options);
    return snapshot;
  } catch (error) {
    toast('Kiểm tra trạng thái thất bại', error.message, 'error');
    return null;
  }
}

function collectSettings() {
  const existing = state.snapshot?.settings || {};
  const central = isCentralExecutor(existing);
  const controlPlaneField = $('#controlPlaneServerUrl');
  return {
    workspace: state.selectedWorkspace,
    permissionMode: $('input[name="permission"]:checked')?.value || 'safe',
    toolMode: 'smart',
    mcpPort: Number($('#mcpPortInput').value),
    healthPort: Number($('#healthPortInput').value),
    proxyMode: $('#proxyModeSelect').value,
    proxyUrl: $('#proxyUrlInput').value.trim(),
    // Central handoff preserves any legacy direct profile for explicit
    // rollback. The renderer must never clear tunnel fields merely because it
    // hides them from an executor that is no longer allowed to use them.
    tunnelId: central ? String(existing.tunnelId || '') : $('#tunnelIdInput').value.trim(),
    recoveryTunnelId: central ? String(existing.recoveryTunnelId || '') : $('#recoveryTunnelIdInput').value.trim(),
    // A central user may intentionally clear the saved origin.  In direct
    // mode the field is hidden, so preserve the last central origin rather
    // than clearing it during an unrelated legacy save.
    controlPlaneServerUrl: central && controlPlaneField
      ? String(controlPlaneField.value || '').trim()
      : String(existing.controlPlaneServerUrl || '').trim(),
    theme: $('#themeSelect').value,
    startWithWindows: $('#startWithWindowsToggle').checked,
    keepRunningOnClose: $('#keepRunningToggle').checked,
    autoStartServices: $('#autoStartToggle').checked,
    progressReportSeconds: Number($('#progressReportSelect').value || 90),
    guideProgress: collectGuideProgress()
  };
}

async function saveSettings(showToast = true) {
  const saved = unwrap(await api.saveSettings(collectSettings()));
  if (showToast) toast('Cài đặt đã được lưu', 'Cấu hình mới sẽ có hiệu lực ở lần triển khai tiếp theo.');
  if (state.snapshot) state.snapshot.settings = saved;
  return saved;
}

async function savePreference(field, value) {
  const stateElement = $(`[data-setting-state="${field}"]`);
  const hint = $('#settingsPreferenceHint');
  if (stateElement) {
    stateElement.textContent = 'Đang lưu…';
    stateElement.dataset.state = 'saving';
  }
  if (hint) hint.textContent = 'Đang lưu thay đổi…';
  try {
    const saved = unwrap(await api.saveSettings({ [field]: value }));
    if (state.snapshot) state.snapshot.settings = { ...state.snapshot.settings, ...saved };
    const control = {
      theme: $('#themeSelect'),
      startWithWindows: $('#startWithWindowsToggle'),
      autoStartServices: $('#autoStartToggle'),
      keepRunningOnClose: $('#keepRunningToggle'),
      progressReportSeconds: $('#progressReportSelect')
    }[field];
    if (control && Object.hasOwn(saved, field)) {
      if (control.type === 'checkbox') control.checked = Boolean(saved[field]);
      else control.value = String(saved[field]);
    }
    if (stateElement) {
      stateElement.textContent = 'Đã lưu';
      stateElement.dataset.state = 'saved';
    }
    if (hint) hint.textContent = 'Đã lưu thay đổi';
    return saved;
  } catch (error) {
    if (stateElement) {
      stateElement.textContent = 'Chưa lưu được';
      stateElement.dataset.state = 'error';
    }
    if (hint) hint.textContent = 'Chưa lưu được — kiểm tra lại và thử lại';
    toast('Không thể lưu tùy chọn', error.message, 'error');
    return null;
  }
}

async function saveKeyIfPresent() {
  if (isCentralExecutor(state.snapshot?.settings)) return false;
  const key = $('#runtimeKeyInput').value.trim();
  if (!key) return false;
  unwrap(await api.saveRuntimeKey(key));
  $('#runtimeKeyInput').value = '';
  return true;
}

async function requestControlPlaneEnrollment() {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Pairing Ubuntu chỉ khả dụng cho central executor.');
  }
  const existingState = String(
    state.centralEnrollmentStatus?.state || state.centralEnrollmentReceipt?.state || ''
  ).toLowerCase();
  if (!state.centralEnrollmentStatusChecked) {
    throw new Error('Hãy kiểm tra trạng thái yêu cầu hiện có trước khi gửi pairing mới.');
  }
  if (['request_sent', 'pending_operator_approval', 'approved'].includes(existingState)) {
    throw new Error('Máy đã có yêu cầu pairing đang lưu. Không cần gửi lại; hãy mở quản trị Ubuntu hoặc kiểm tra trạng thái máy.');
  }
  assertPackagedCentralSetup('Pairing Ubuntu');
  const field = $('#controlPlaneServerUrl');
  const serverUrl = String(field?.value || '').trim();
  if (!serverUrl) throw new Error('Nhập HTTPS origin của Ubuntu Control Plane trước.');
  state.centralEnrollmentBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    const receipt = unwrap(await api.requestControlPlaneEnrollment(serverUrl));
    state.centralEnrollmentReceipt = receipt;
    state.centralEnrollmentStatusChecked = true;
    state.centralEnrollmentStatus = { ...receipt, credential_generation: null, fresh: true, observed_at_ms: Date.now(), error_code: null, server_origin: receipt.server_origin || null };
    if (receipt?.server_origin && state.snapshot?.settings) {
      state.snapshot.settings.controlPlaneServerUrl = receipt.server_origin;
      if (field) field.value = receipt.server_origin;
    }
    toast('Đã gửi yêu cầu pairing', 'Ubuntu phải duyệt identity; sau đó account OAuth chọn target và tạo authority riêng trước khi máy này được chạy.', 'success');
    await refreshSnapshot({ forceForms: false });
    await reconcileControlPlaneEnrollment({ quiet: true });
    await reconcileControlPlaneAuthorityStatus({ quiet: true });
    return receipt;
  } finally {
    state.centralEnrollmentBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function chooseControlPlaneWorkspace() {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Chọn root đăng ký Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Chọn workspace Ubuntu');
  state.centralWorkspaceBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    // The directory dialog only returns a local candidate.  In particular it
    // must not call switchWorkspace or mutate settings.workspace: existing
    // local work and remote task bindings keep their original target.
    const candidate = String(unwrap(await api.chooseWorkspace()) || '').trim();
    if (!candidate) return null;
    state.centralWorkspaceCandidate = candidate;
    toast('Đã chọn thư mục', 'Chưa thay đổi workspace chính, policy hay quyền task. Bấm “Thêm thư mục này” để gửi inventory ẩn danh tới Ubuntu.', 'success');
    return candidate;
  } finally {
    state.centralWorkspaceBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function registerControlPlaneWorkspace() {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Đăng ký workspace Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Đăng ký workspace Ubuntu');
  const workspacePath = String(state.centralWorkspaceCandidate || '').trim();
  if (!workspacePath) throw new Error('Chọn thư mục local trước.');
  state.centralWorkspaceBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    // This is inventory only.  Do not call switchWorkspace,
    // updateAuthorizedRoots, install a policy, or infer any task authority
    // from the registration receipt.
    const capabilities = centralWorkspaceCapabilitiesFromUi();
    const receipt = unwrap(await api.registerControlPlaneWorkspace({ workspacePath, capabilities }));
    state.centralWorkspaceReceipt = receipt;
    state.centralWorkspaceCapabilities = {
      read: true,
      write: receipt.capabilities?.write === true,
      exec: receipt.capabilities?.exec === true
    };
    state.centralWorkspacePreset = centralWorkspacePresetFor(state.centralWorkspaceCapabilities);
    toast('Đã thêm thư mục', 'Ubuntu chỉ nhận inventory ẩn danh; tài khoản vẫn phải chọn target và quyền thực thi vẫn theo policy local.', 'success');
    await refreshCentralWorkspaceUiAfterCommit();
    await reconcileControlPlaneAuthorityStatus({ quiet: true });
    return receipt;
  } finally {
    state.centralWorkspaceBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function replaceControlPlaneWorkspace(workspace) {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Đổi mức quyền thư mục Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Đổi mức quyền workspace Ubuntu');
  if (!workspace?.workspace_id || !workspace?.workspace_generation || !workspace?.display_name) {
    throw new Error('Thư mục local được chọn không hợp lệ.');
  }
  let workspacePath = String(state.centralWorkspaceCandidate || '').trim();
  if (!workspacePath) {
    workspacePath = await chooseControlPlaneWorkspace();
  }
  if (!workspacePath) return null;
  const capabilities = centralWorkspaceCapabilitiesFromUi();
  const oldLabel = centralWorkspaceCapabilityLabel(workspace.capabilities);
  const newLabel = centralWorkspaceCapabilityLabel(capabilities);
  const accepted = window.confirm(
    `Đổi mức quyền cho “${workspace.display_name}” (${oldLabel} → ${newLabel})? `
      + 'Ubuntu sẽ retire generation cũ, đóng binding/task cũ, vô hiệu policy local cũ và tạo generation mới. '
      + 'Bạn phải bind lại workspace mới trên tài khoản ChatGPT; không ghi đè âm thầm.'
  );
  if (!accepted) return null;
  state.centralWorkspaceBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    const receipt = unwrap(await api.replaceControlPlaneWorkspace({
      workspacePath,
      capabilities,
      confirmReplace: true
    }));
    state.centralWorkspaceReceipt = receipt;
    state.centralWorkspaceCapabilities = {
      read: true,
      write: receipt.capabilities?.write === true,
      exec: receipt.capabilities?.exec === true
    };
    state.centralWorkspacePreset = centralWorkspacePresetFor(state.centralWorkspaceCapabilities);
    toast('Đã tạo generation workspace mới', 'Binding/task generation cũ đã bị fence; hãy bind lại ID mới trước khi giao việc.', 'success');
    await refreshCentralWorkspaceUiAfterCommit();
    await reconcileControlPlaneAuthorityStatus({ quiet: true });
    return receipt;
  } finally {
    state.centralWorkspaceBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function refreshControlPlaneWorkspaces({ quiet = false } = {}) {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Danh sách workspace Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Đọc inventory workspace Ubuntu');
  state.centralWorkspaceListBusy = true;
  state.centralWorkspaceInventoryStatus = 'loading';
  state.centralWorkspaceInventoryError = null;
  renderCentralExecutorMode(state.snapshot);
  try {
    const workspaces = unwrap(await api.listControlPlaneWorkspaces());
    state.centralWorkspaces = Array.isArray(workspaces) ? workspaces : [];
    state.centralWorkspaceInventoryStatus = 'loaded';
    state.centralWorkspaceInventoryError = null;
    if (!quiet) toast('Đã tải workspace local', `${state.centralWorkspaces.length} workspace đang đăng ký.`, 'success');
    return state.centralWorkspaces;
  } catch (error) {
    state.centralWorkspaces = null;
    state.centralWorkspaceInventoryStatus = 'unknown';
    state.centralWorkspaceInventoryError = error?.code || error?.message || 'CONTROL_PLANE_WORKSPACE_LIST_FAILED';
    throw error;
  } finally {
    state.centralWorkspaceListBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function installControlPlaneReadOnlyPolicyAssignment(workspace) {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Đồng bộ policy read-only chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Đồng bộ policy read-only');
  if (!workspace?.workspace_id || !workspace?.workspace_generation || !workspace?.display_name) {
    throw new Error('Workspace local được chọn không hợp lệ.');
  }
  const accepted = window.confirm(
    `Cài policy read-only do Ubuntu đã cấp cho “${workspace.display_name}”? `
      + 'Thao tác chỉ mở đọc trong root này; không cấp ghi, shell hoặc quyền task mới. '
      + 'Nếu đang có policy read-only khác, policy đó sẽ bị thay thế.'
  );
  if (!accepted) return null;
  state.centralPolicyBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    const receipt = unwrap(await api.installControlPlaneReadOnlyPolicyAssignment({
      workspaceId: workspace.workspace_id,
      workspaceGeneration: workspace.workspace_generation,
      confirmInstall: true,
      replaceExisting: true
    }));
    state.centralPolicyReceipt = {
      ...receipt,
      workspace_id: workspace.workspace_id,
      workspace_generation: workspace.workspace_generation
    };
    toast('Đã đồng bộ read-only policy', 'Ubuntu chỉ trả policy đã gắn nội bộ với workspace này. Không có context ID, token hoặc quyền ghi/chạy nào vào Windows.', 'success');
    await refreshSnapshot({ forceForms: false });
    return receipt;
  } finally {
    state.centralPolicyBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function refreshCentralWorkspaceUiAfterCommit() {
  // Registration/retirement receipts are durable state transitions. A
  // subsequent local inventory or snapshot refresh is only a UI observation;
  // it must not make a committed workspace change look like it failed.
  let stale = false;
  try {
    await refreshControlPlaneWorkspaces({ quiet: true });
  } catch {
    stale = true;
    state.centralWorkspaces = null;
    state.centralWorkspaceInventoryStatus = 'unknown';
    state.centralWorkspaceInventoryError = 'CONTROL_PLANE_WORKSPACE_REFRESH_FAILED';
  }
  try {
    await refreshSnapshot({ forceForms: false });
  } catch {
    stale = true;
  }
  if (stale) {
    toast('Thay đổi đã được ghi nhận', 'Không thể làm mới inventory ngay lúc này; dùng “Tải workspace đã đăng ký” để kiểm tra lại. Không có binding hay quyền mới được suy ra.', 'warning');
  }
}

async function retireControlPlaneWorkspace(workspace) {
  if (!isCentralExecutor(state.snapshot?.settings)) {
    throw new Error('Thu hồi workspace Ubuntu chỉ khả dụng cho central executor.');
  }
  assertPackagedCentralSetup('Thu hồi workspace Ubuntu');
  if (!workspace?.workspace_id || !workspace?.workspace_generation || !workspace?.display_name) {
    throw new Error('Workspace local được chọn không hợp lệ.');
  }
  const accepted = window.confirm(
    `Thu hồi ${workspace.display_name} khỏi Ubuntu? Context còn sống sẽ bị đóng và action chưa gửi cho workspace này sẽ bị từ chối.`
  );
  if (!accepted) return null;
  state.centralWorkspaceBusy = true;
  renderCentralExecutorMode(state.snapshot);
  try {
    const receipt = unwrap(await api.retireControlPlaneWorkspace({
      workspaceId: workspace.workspace_id,
      workspaceGeneration: workspace.workspace_generation
    }));
    state.centralWorkspaceRetirementReceipt = receipt;
    if (state.centralWorkspaceReceipt?.workspace_id === receipt.workspace_id
      && state.centralWorkspaceReceipt?.workspace_generation === receipt.workspace_generation) {
      state.centralWorkspaceReceipt = null;
    }
    if (state.centralPolicyReceipt?.workspace_id === receipt.workspace_id
      && state.centralPolicyReceipt?.workspace_generation === receipt.workspace_generation) {
      state.centralPolicyReceipt = null;
    }
    toast('Đã thu hồi workspace', 'Ubuntu đã xác nhận retirement; registry local chỉ được xóa sau receipt này.', 'success');
    await refreshCentralWorkspaceUiAfterCommit();
    return receipt;
  } finally {
    state.centralWorkspaceBusy = false;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  }
}

async function handoffCentralExecutor() {
  setBusy(true, true);
  try {
    // This requests an operator migration, not a code acceptance checkpoint.
    // No Windows Tunnel/key/profile input crosses this IPC. A HANDOFF receipt
    // is not a runtime snapshot or proof of a completed/connected executor.
    const result = unwrap(await api.handoffCentralExecutor());
    if (result?.settings && result?.status) renderSnapshot(result, { forceForms: true });
    toast('Đã nhận yêu cầu chuyển sang executor Ubuntu', 'Ứng dụng có thể khởi động lại. Chờ vai trò central xuất hiện rồi hoàn thành pairing/liên kết tài khoản; chưa xác nhận kết nối Ubuntu.', 'success');
    return result;
  } catch (error) {
    toast('Không thể chuyển sang executor Ubuntu', error.message, 'error');
    throw error;
  } finally {
    setBusy(false);
    await refreshSnapshot({ forceForms: true });
  }
}

function updateProgress(payload) {
  const percent = Math.max(0, Math.min(100, Number(payload.percent || 0)));
  $('#progressPercent').textContent = `${percent}%`;
  $('#progressBar').style.width = `${percent}%`;
  $('#progressRing').style.setProperty('--value', `${percent * 3.6}deg`);
  $('#progressTitle').textContent = payload.step === 'failed' ? 'Triển khai thất bại' : payload.step === 'complete' ? 'Triển khai hoàn tất' : 'Đang thực thi nhiệm vụ triển khai';
  $('#progressMessage').textContent = payload.message;
  $('#progressBadge').textContent = payload.step === 'failed' ? 'Cần xử lý' : payload.step === 'complete' ? 'Đã hoàn thành' : 'Đang chạy';
  if (payload.step === 'failed') toast('Triển khai thất bại', payload.message, 'error');
}

async function runRuntime(action) {
  setBusy(true, false);
  navigate('overview');
  try {
    const result = unwrap(await api[action]());
    renderSnapshot(result, { forceForms: true });
    const central = isCentralExecutor(result?.settings || state.snapshot?.settings);
    toast(action === 'stop' ? 'Dịch vụ đã dừng' : 'Thao tác hoàn tất', action === 'stop'
      ? (central ? 'Executor cục bộ đã dừng; Tunnel Ubuntu không bị thay đổi.' : 'MCP và Tunnel đã dừng an toàn.')
      : (central ? 'Đã kiểm tra MCP executor và route evidence tới Ubuntu.' : 'MCP và Tunnel đã qua kiểm tra sức khỏe cục bộ.'));
  } catch (error) {
    toast('Thao tác thất bại', error.message, 'error');
    if (/工作目录|Thư mục làm việc|Runtime API Key|Tunnel ID|Python/.test(error.message)) navigate('deploy');
  } finally {
    setBusy(false);
    await refreshSnapshot();
  }
}

async function deployNow() {
  setBusy(true, false);
  try {
    await saveKeyIfPresent();
    await saveSettings(false);
    navigate('overview');
    const result = unwrap(await api.start());
    renderSnapshot(result, { forceForms: true });
    const central = isCentralExecutor(result?.settings || state.snapshot?.settings);
    toast('Triển khai hoàn tất', central
      ? 'Executor cục bộ đã được kiểm tra. Pairing/policy Ubuntu vẫn là authority để chạy action.'
      : 'Bây giờ bạn có thể làm theo trang hướng dẫn để tạo hoặc kiểm tra MCP trong ChatGPT.');
  } catch (error) {
    toast('Triển khai thất bại', error.message, 'error');
  } finally {
    setBusy(false);
    await refreshSnapshot();
  }
}

async function chooseWorkspace() {
  try {
    const selected = unwrap(await api.chooseWorkspace());
    if (!selected) return;
    state.selectedWorkspace = selected;
    $('#selectedWorkspace').textContent = selected;
    renderDeploySummary();
    toast('Đang chuyển thư mục làm việc', 'MCP sẽ âm thầm tạo lại ở chế độ nền, ChatGPT và Tunnel sẽ không bị đóng.');
    const switched = unwrap(await api.switchWorkspace(selected));
    renderSnapshot(switched, { forceForms: true });
    toast('Đã chuyển thư mục làm việc', selected);
  } catch (error) { toast('Không thể chọn thư mục', error.message, 'error'); }
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); toast('Đã sao chép', text.length > 70 ? 'Nội dung đã được sao chép vào bộ nhớ tạm.' : text); }
  catch { toast('Sao chép thất bại', 'Vui lòng chọn và sao chép thủ công.', 'error'); }
}

function collectGuideProgress() {
  return Object.fromEntries($$('[data-guide-check]').map((input) => [input.dataset.guideCheck, input.checked]));
}

function restoreGuideProgress(progress) {
  $$('[data-guide-check]').forEach((input) => { input.checked = Boolean(progress[input.dataset.guideCheck]); });
  renderGuideProgress();
}

function renderGuideProgress() {
  const checks = $$('[data-guide-check]');
  const done = checks.filter((input) => input.checked).length;
  const percent = Math.round((done / checks.length) * 100);
  $('#guideProgressPercent').textContent = `${percent}%`;
  $('#guideProgressBar').style.width = `${percent}%`;
  checks.forEach((input, index) => {
    input.closest('.guide-step').classList.toggle('done', input.checked);
    $$('#guideChecklist li')[index]?.classList.toggle('done', input.checked);
  });
}

function appendBuildOutput(text) {
  const consoleElement = $('#buildConsole');
  const next = `${consoleElement.textContent === 'Chưa thực hiện xác minh build.' ? '' : consoleElement.textContent}${text}`;
  consoleElement.textContent = next.slice(-60000);
  consoleElement.scrollTop = consoleElement.scrollHeight;
}

function applyBuildProject(project) {
  $('#buildProjectType').textContent = `${textOr(project.type, 'unknown')} · ${textOr(project.name)}`;
  $('#buildTestCommand').value = project.testCommand || '';
  $('#buildCommand').value = project.buildCommand || '';
  $('#buildArtifacts').value = (project.artifacts || []).join(', ');
}

async function inspectBuild() {
  try { applyBuildProject(unwrap(await api.inspectBuild())); }
  catch (error) { toast('Nhận diện dự án thất bại', error.message, 'error'); }
}

function renderBuildReport(report) {
  $('#buildReportStatus').textContent = report.overallStatus === 'passed' ? 'Xác minh thành công' : 'Xác minh thất bại';
  const container = $('#buildReport'); container.replaceChildren();
  const summary = document.createElement('div'); summary.className = `build-report-summary ${report.overallStatus}`;
  summary.textContent = `${textOr(report.project?.name)} · ${textOr(report.project?.type)} · v${textOr(report.project?.version)} · Kiểm thử ${textOr(report.testResult?.status)} · Build ${textOr(report.buildResult?.status)}`;
  container.append(summary);
  (report.artifacts || []).forEach((artifact) => {
    const row = document.createElement('div'); row.className = 'build-report-artifact';
    const name = document.createElement('b'); name.textContent = textOr(artifact.path);
    const size = document.createElement('span'); size.textContent = `${Number(artifact.size || 0).toLocaleString()} bytes`;
    const hash = document.createElement('code'); hash.textContent = textOr(artifact.sha256);
    row.append(name, size, hash); container.append(row);
  });
  if (!(report.artifacts || []).length) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Không tìm thấy sản phẩm build.'; container.append(empty);
  }
}

async function runBuildVerification() {
  $('#buildConsole').textContent = '';
  $('#buildStatus').textContent = 'Đang thực thi';
  $('#runBuild').disabled = true;
  try {
    const options = {
      testCommand: $('#buildTestCommand').value.trim(),
      buildCommand: $('#buildCommand').value.trim(),
      artifacts: $('#buildArtifacts').value.split(',').map((item) => item.trim()).filter(Boolean),
      runTests: $('#buildRunTests').checked,
      runBuild: $('#buildRunBuild').checked
    };
    const report = unwrap(await api.runBuild(options));
    renderBuildReport(report);
    $('#buildStatus').textContent = report.overallStatus === 'passed' ? 'Đã vượt qua' : 'Chưa vượt qua';
    toast(report.overallStatus === 'passed' ? 'Xác minh build thành công' : 'Xác minh build không thành công', `${report.artifacts?.length || 0} sản phẩm đã được kiểm tra`, report.overallStatus === 'passed' ? 'success' : 'error');
  } catch (error) {
    $('#buildStatus').textContent = 'Thực thi thất bại'; appendBuildOutput(`\n${error.message}\n`); toast('Xác minh build thất bại', error.message, 'error');
  } finally { $('#runBuild').disabled = false; }
}

function renderHealth(report) {
  $('#healthSummary').textContent = report.healthy ? 'Tất cả bình thường' : 'Cần xử lý';
  const container = $('#healthList'); container.replaceChildren();
  (report.checks || []).forEach((check) => {
    const row = document.createElement('div'); row.className = `health-item ${check.ok ? 'passed' : 'failed'}`;
    const mark = document.createElement('i'); mark.textContent = check.ok ? '✓' : '!';
    const copy = document.createElement('div'); const title = document.createElement('b'); title.textContent = check.label; const detail = document.createElement('small'); detail.textContent = check.detail; copy.append(title, detail);
    const status = document.createElement('span'); status.textContent = check.ok ? 'Bình thường' : 'Chờ xử lý'; row.append(mark, copy, status); container.append(row);
  });
  (report.actions || []).forEach((action) => {
    const row = document.createElement('div'); row.className = 'health-item passed';
    const mark = document.createElement('i'); mark.textContent = '↻';
    const copy = document.createElement('div'); const title = document.createElement('b'); title.textContent = 'Đã thực thi sửa chữa'; const detail = document.createElement('small'); detail.textContent = action; copy.append(title, detail);
    const status = document.createElement('span'); status.textContent = 'Hoàn thành'; row.append(mark, copy, status); container.append(row);
  });
}

async function inspectHealth() {
  try { renderHealth(unwrap(await api.inspectHealth())); }
  catch (error) { toast('Kiểm tra sức khỏe hệ thống thất bại', error.message, 'error'); }
}

async function repairHealth() {
  $('#repairHealth').disabled = true;
  try {
    const report = unwrap(await api.repairHealth()); renderHealth(report);
    toast(report.healthy ? 'Sửa chữa nhanh hoàn tất' : 'Đã hoàn thành các mục có thể xử lý tự động', report.unresolved?.length ? `Vẫn cần xử lý thủ công: ${report.unresolved.join('、')}` : 'Môi trường hiện tại đã qua kiểm tra sức khỏe.', report.healthy ? 'success' : 'error');
  } catch (error) { toast('Sửa chữa nhanh thất bại', error.message, 'error'); }
  finally { $('#repairHealth').disabled = false; }
}

function applyHeartbeat(status) {
  if (!state.snapshot || !status) return;
  if (status.signalStale === true || status.telemetryAvailable === false) {
    state.snapshot.status.signalStale = true;
    renderRecoveryTunnelSettings({ ...state.snapshot, signalStale: true });
    $('#sideRuntimeText').textContent = 'Telemetry tạm gián đoạn';
    $('#mcpStatus').textContent = 'Đang chờ heartbeat mới';
    $('#tunnelStatus').textContent = 'Đang chờ heartbeat mới';
    setDot($('#sideRuntimeDot'), 'warn');
    setDot($('#mcpDot'), 'warn');
    setDot($('#tunnelDot'), 'warn');
    return;
  }
  delete state.snapshot.status.signalStale;
  // Heartbeats are authoritative point-in-time projections. Never retain a
  // previous green closure/connector receipt when the current host omits it.
  for (const key of ['codeRevision', 'toolContract', 'connectorContractState', 'connectorRefreshRequired', 'connectorAcknowledgementPending', 'connectorRediscovered', 'connectorRediscoveredAt', 'activationClosure', 'activationEpoch', 'updateIncomplete']) {
    if (!Object.hasOwn(status, key)) delete state.snapshot.status[key];
  }
  state.snapshot.status.runtimeRunning = Boolean(status.mcpRunning);
  state.snapshot.status.tunnelRunning = Boolean(status.tunnelRunning);
  state.snapshot.status.fullyReady = Boolean(status.fullyReady);
  ['codeRevision', 'toolContract', 'connectorContractState', 'connectorRefreshRequired', 'connectorAcknowledgementPending', 'connectorRediscovered', 'connectorRediscoveredAt', 'activationClosure', 'activationEpoch', 'updateIncomplete'].forEach((key) => {
    if (Object.hasOwn(status, key)) state.snapshot.status[key] = status[key];
  });
  if (status.recoveryHost) state.snapshot.recoveryHost = status.recoveryHost;
  else delete state.snapshot.recoveryHost;
  if (status.device) state.snapshot.device = status.device;
  renderRecoveryTunnelSettings(state.snapshot);
  renderDevice(state.snapshot);
  renderRuntimeSourceStatus(state.snapshot);
  const ready = state.snapshot.status.fullyReady;
  $('#sideMcp').textContent = status.mcpRunning ? 'ON' : 'OFF';
  $('#sideTunnel').textContent = status.tunnelRunning ? 'ON' : 'OFF';
  $('#mcpStatus').textContent = status.mcpRunning ? 'Đang chạy bình thường' : 'Chưa khởi động';
  $('#tunnelStatus').textContent = status.tunnelRunning ? 'Đã kết nối' : 'Chưa kết nối';
  setDot($('#mcpDot'), status.mcpRunning ? 'ready' : 'error');
  setDot($('#tunnelDot'), status.tunnelRunning ? 'ready' : 'error');
  const activationIncomplete = status.updateIncomplete === true
    || status.activationEpoch?.update_incomplete === true
    || status.activationEpoch?.state === 'UPDATE_INCOMPLETE';
  $('#sideRuntimeText').textContent = ready
    ? 'Dịch vụ sẵn sàng'
    : activationIncomplete
      ? 'Đang hoàn tất activation epoch'
      : status.mcpRunning ? 'Đang chờ Tunnel' : 'Dịch vụ chưa chạy';
  setDot($('#sideRuntimeDot'), ready ? 'ready' : status.mcpRunning ? 'warn' : 'error');
}

async function loadLogs() {
  try {
    state.logs = unwrap(await api.logs());
    renderLogs();
  } catch (error) { toast('Đọc nhật ký thất bại', error.message, 'error'); }
}

function renderLogs() {
  const output = $('#logOutput');
  const list = state.logFilter === 'all' ? state.logs : state.logs.filter((item) => item.level === state.logFilter);
  output.replaceChildren();
  if (!list.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = '<b>Chưa có nhật ký phù hợp</b><span>Thực hiện triển khai hoặc chuyển điều kiện lọc để xem.</span>';
    output.appendChild(empty);
    return;
  }
  list.forEach((item) => {
    const row = document.createElement('div');
    row.className = `log-line ${item.level}`;
    const time = document.createElement('time');
    time.textContent = new Date(item.time).toLocaleString('vi-VN', { hour12: false });
    const level = document.createElement('em');
    level.textContent = item.level;
    const message = document.createElement('span');
    message.textContent = item.message;
    row.append(time, level, message);
    output.appendChild(row);
  });
  output.scrollTop = output.scrollHeight;
}

function bindEvents() {
  $('#closeManager')?.addEventListener('click', () => api.closeManager());
  $$('.nav-item').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.page)));
  $$('[data-nav]').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.nav)));
  $$('[data-open]').forEach((button) => button.addEventListener('click', async () => {
    try { unwrap(await api.openExternal(button.dataset.open)); }
    catch (error) { toast('Không thể mở trang', error.message, 'error'); }
  }));
  $$('input[name="permission"]').forEach((input) => input.addEventListener('change', () => {
    $$('.choice').forEach((choice) => choice.classList.toggle('selected', choice.contains(input) && input.checked));
  }));

  $('#refreshSystemSetup')?.addEventListener('click', () => refreshSystemSetup());
  $('#openControlPlaneConsole')?.addEventListener('click', () => openControlPlaneConsole());
  $('#controlPlaneServerUrl')?.addEventListener('input', () => renderControlPlaneConsoleLink());
  $('#refreshControlPlaneEnrollment')?.addEventListener('click', () => refreshSystemSetup());
  $('#refreshButton').addEventListener('click', () => {
  if (['system', 'deploy', 'workspace', 'settings'].includes(state.currentPage)) {
      refreshSystemSetup();
      return;
    }
    // Overview refreshes have one owner: Control Center.  Keep this top-bar
    // affordance on the same lightweightSnapshot + liveOrchestration path.
    document.dispatchEvent(new CustomEvent('coding-tools:overview-refresh-request'));
  });
  $('#deviceRefresh')?.addEventListener('click', () => refreshSnapshot());
  $('#deviceStart')?.addEventListener('click', () => runRuntime('start'));
  $('#deviceRestart')?.addEventListener('click', () => runRuntime('restart'));
  $('#deviceStop')?.addEventListener('click', () => runRuntime('stop'));
  $('#deviceRepair')?.addEventListener('click', async () => { await repairHealth(); await refreshSnapshot(); });
  $('#topStartButton').addEventListener('click', () => isCentralExecutor(state.snapshot?.settings)
    ? navigate('system')
    : runRuntime(state.snapshot?.status.fullyReady ? 'restart' : 'start'));
  $('#heroStartButton').addEventListener('click', () => isCentralExecutor(state.snapshot?.settings)
    ? navigate('system')
    : state.snapshot?.status.fullyReady ? runRuntime('restart') : navigate('deploy'));
  $('#setupPrimaryAction')?.addEventListener('click', () => handleSetupPrimaryAction());
  $('#overviewRestart').addEventListener('click', () => runRuntime('restart'));
  $('#overviewStop').addEventListener('click', () => runRuntime('stop'));
  $('#deployNow').addEventListener('click', deployNow);
  $('#handoffCentralExecutor')?.addEventListener('click', async () => {
    try { await handoffCentralExecutor(); }
    catch (_) { /* The handoff function has already shown a redacted error. */ }
  });
  $('#retryCentralExecutorHandoff')?.addEventListener('click', async () => {
    try { await handoffCentralExecutor(); }
    catch (_) { /* The handoff function has already shown a redacted error. */ }
  });
  $('#requestControlPlaneEnrollment')?.addEventListener('click', async () => {
    try { await requestControlPlaneEnrollment(); }
    catch (error) { toast('Không thể gửi pairing Ubuntu', error.message, 'error'); }
  });
  $('#refreshControlPlaneAuthorityStatus')?.addEventListener('click', async () => {
    try { await reconcileControlPlaneAuthorityStatus({ quiet: false }); }
    catch (error) { toast('Không thể kiểm tra liên kết tài khoản', error.message, 'error'); }
  });
  $('#rotateControlPlaneCredential')?.addEventListener('click', async () => {
    try { await rotateControlPlaneCredential(); }
    catch (error) { toast('Không thể đổi credential Ubuntu', error.message, 'error'); }
  });
  $('#chooseControlPlaneWorkspace')?.addEventListener('click', async () => {
    try { await chooseControlPlaneWorkspace(); }
    catch (error) { toast('Không thể chọn root đăng ký Ubuntu', error.message, 'error'); }
  });
  $$('input[name="centralWorkspacePreset"]').forEach((input) => input.addEventListener('change', (event) => {
    if (event.currentTarget.checked) chooseCentralWorkspacePreset(event.currentTarget.value);
  }));
  $('#controlPlaneCapabilityWrite')?.addEventListener('change', (event) => {
    state.centralWorkspacePreset = 'custom';
    state.centralWorkspaceCapabilities.write = event.currentTarget.checked === true;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  });
  $('#controlPlaneCapabilityExec')?.addEventListener('change', (event) => {
    state.centralWorkspacePreset = 'custom';
    state.centralWorkspaceCapabilities.exec = event.currentTarget.checked === true;
    if (state.snapshot) renderCentralExecutorMode(state.snapshot);
  });
  $('#registerControlPlaneWorkspace')?.addEventListener('click', async () => {
    try { await registerControlPlaneWorkspace(); }
    catch (error) { toast('Không thể đăng ký workspace Ubuntu', error.message, 'error'); }
  });
  $('#refreshControlPlaneWorkspaces')?.addEventListener('click', async () => {
    try { await refreshControlPlaneWorkspaces(); }
    catch (error) { toast('Không thể tải workspace Ubuntu', error.message, 'error'); }
  });
  $('#chooseWorkspace').addEventListener('click', chooseWorkspace);
  $('#addAuthorizedRoot').addEventListener('click', addAuthorizedRoot);
  $('#saveDeploySettings').addEventListener('click', async () => {
    try { await saveKeyIfPresent(); await saveSettings(); await refreshSnapshot({ forceForms: true }); }
    catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#saveWorkspace').addEventListener('click', async () => {
    try { await saveSettings(); await refreshSnapshot({ forceForms: true }); }
    catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#saveWorkspaceRestart').addEventListener('click', async () => {
    try { await saveSettings(false); await runRuntime('restart'); }
    catch (error) { toast('Triển khai lại thất bại', error.message, 'error'); }
  });
  $('#saveRuntimeKey').addEventListener('click', async () => {
    try {
      if (!(await saveKeyIfPresent())) throw new Error('Vui lòng dán Runtime API Key trước.');
      toast('Khóa mật mã đã được lưu an toàn', 'Khóa mật mã đã được mã hóa bằng kho lưu trữ an toàn Windows.');
      await refreshSnapshot();
    } catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#removeRuntimeKey').addEventListener('click', async () => {
    try { unwrap(await api.removeRuntimeKey()); toast('Đã xóa khóa mật mã'); await refreshSnapshot(); }
    catch (error) { toast('Xóa thất bại', error.message, 'error'); }
  });
  $('#saveRecoveryTunnel').addEventListener('click', async () => {
    try {
      const recoveryId = $('#recoveryTunnelIdInput').value.trim();
      const primaryId = $('#tunnelIdInput').value.trim() || String(state.snapshot?.settings?.tunnelId || '').trim();
      if (recoveryId && primaryId && recoveryId === primaryId) throw new Error('Tunnel cứu hộ phải dùng Tunnel ID riêng, khác Tunnel chính.');
      await saveSettings(false);
      toast('Đã lưu Tunnel cứu hộ', recoveryId ? 'Recovery Host sẽ tự thử kết nối trong vài giây.' : 'Tunnel cứu hộ đang để ở trạng thái chưa cấu hình.');
      await refreshSnapshot({ forceForms: true });
    } catch (error) { toast('Lưu Tunnel cứu hộ thất bại', error.message, 'error'); }
  });
  $('#regenerateToken').addEventListener('click', async () => {
    try { unwrap(await api.regenerateMcpToken()); toast('Token xác thực đã được tạo lại', 'Có hiệu lực sau khi triển khai lại.'); }
    catch (error) { toast('Tạo thất bại', error.message, 'error'); }
  });
  $('#clearChatSession').addEventListener('click', async () => {
    if (!confirm('Thao tác này sẽ đăng xuất ChatGPT tích hợp và xóa Cookie cũng như bộ nhớ đệm web do trợ lý này lưu. Bạn có muốn tiếp tục?')) return;
    try {
      unwrap(await api.clearChatSession());
      toast('Dữ liệu đăng nhập ChatGPT đã được xóa', 'Bạn có thể đăng nhập lại sau khi quay lại cửa sổ chat chính.');
    } catch (error) { toast('Xóa thất bại', error.message, 'error'); }
  });
  $('#pythonInstall').addEventListener('click', async () => {
    setBusy(true, true);
    try { unwrap(await api.installPython()); toast('Cài đặt Python hoàn tất', 'Vui lòng kiểm tra lại môi trường.'); await refreshSnapshot(); }
    catch (error) { toast('Cài đặt thất bại', error.message, 'error'); }
    finally { setBusy(false); }
  });
  $('#proxyModeSelect').addEventListener('change', () => { renderProxyControls(); renderDeploySummary(); });
  $('#proxyDetect').addEventListener('click', async () => {
    try {
      await saveSettings(false);
      const result = unwrap(await api.detectProxy());
      toast(result.reachable ? 'Tuyến đường mạng khả dụng' : 'Không phát hiện thấy tuyến đường khả dụng', result.resolvedUrl || (result.reachable ? 'Hiện đang sử dụng kết nối trực tiếp.' : 'Vui lòng kiểm tra cài đặt mạng hoặc proxy thủ công.'), result.reachable ? 'success' : 'error');
      await refreshSnapshot({ forceForms: true });
    } catch (error) { toast('Kiểm tra proxy thất bại', error.message, 'error'); }
  });
  ['#tunnelIdInput', '#proxyUrlInput', '#runtimeKeyInput'].forEach((selector) => $(selector).addEventListener('input', renderDeploySummary));

  $('#themeToggle').addEventListener('click', async () => {
    const next = document.body.dataset.theme === 'light' ? 'dark' : 'light';
    applyTheme(next);
    await savePreference('theme', next);
  });
  $('#themeSelect').addEventListener('change', async () => {
    const next = $('#themeSelect').value;
    applyTheme(next);
    await savePreference('theme', next);
  });
  $('#startWithWindowsToggle').addEventListener('change', () => savePreference('startWithWindows', $('#startWithWindowsToggle').checked));
  $('#keepRunningToggle').addEventListener('change', () => savePreference('keepRunningOnClose', $('#keepRunningToggle').checked));
  $('#autoStartToggle').addEventListener('change', () => savePreference('autoStartServices', $('#autoStartToggle').checked));
  $('#progressReportSelect').addEventListener('change', () => savePreference('progressReportSeconds', Number($('#progressReportSelect').value || 90)));

  $$('[data-guide-check]').forEach((input) => input.addEventListener('change', async () => {
    renderGuideProgress();
    try { await saveSettings(false); } catch { /* non-critical */ }
  }));
  $$('[data-copy]').forEach((button) => button.addEventListener('click', () => copyText(button.dataset.copy)));
  $('#copyLocalUrl').addEventListener('click', () => copyText($('#guideLocalUrl').textContent));
  $('#copyTunnelId').addEventListener('click', () => copyText($('#guideTunnelId').textContent));

  $('#refreshLogs').addEventListener('click', loadLogs);
  $('#refreshTaskState').addEventListener('click', loadTaskState);
  $('#refreshTaskHistory').addEventListener('click', loadTaskHistory);
  $('#pauseTask').addEventListener('click', async () => { try { unwrap(await api.pauseTask()); await loadTaskState(); toast('Nhiệm vụ đã tạm dừng', 'Tiến độ hiện tại đã được lưu trong workspace.'); } catch (error) { toast('Tạm dừng thất bại', error.message, 'error'); } });
  $('#resumeTask').addEventListener('click', async () => { try { unwrap(await api.resumeTask()); await loadTaskState(); toast('Nhiệm vụ đã tiếp tục', 'Mô hình web có thể khôi phục từ bước tiếp theo được ghi lại.'); } catch (error) { toast('Tiếp tục thất bại', error.message, 'error'); } });
  $('#stopTask').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn dừng nhiệm vụ hiện tại không? Các lệnh đang chạy sẽ bị chấm dứt.')) return; try { unwrap(await api.stopTask()); await loadTaskState(); toast('Nhiệm vụ đã dừng', 'Trạng thái và lịch sử vẫn được giữ lại, có thể tiếp tục sau.'); } catch (error) { toast('Dừng thất bại', error.message, 'error'); } });
  $('#clearTaskState').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn xóa trạng thái nhiệm vụ của workspace hiện tại không?')) return; unwrap(await api.clearTaskState()); renderTaskState(null); toast('Đã xóa trạng thái nhiệm vụ'); });
  $('#refreshPerformance').addEventListener('click', loadPerformanceTrace);
  $('#clearPerformance').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn xóa sạch các bản ghi hiệu năng của workspace hiện tại không?')) return; try { unwrap(await api.clearPerformanceTrace()); renderPerformanceTrace(null); toast('Đã xóa sạch bản ghi hiệu năng'); } catch (error) { toast('Xóa sạch thất bại', error.message, 'error'); } });
  $('#inspectBuild').addEventListener('click', inspectBuild);
  $('#runBuild').addEventListener('click', runBuildVerification);
  $('#inspectHealth').addEventListener('click', inspectHealth);
  $('#repairHealth').addEventListener('click', repairHealth);
  $('#ackConnectorContract')?.addEventListener('click', async () => {
    try {
      const snapshot = unwrap(await api.snapshot());
      renderSnapshot(snapshot, { forceForms: false });
      toast(
        'Đã kiểm tra lại tool contract',
        connectorContractPresentation(snapshot.status).toast
      );
    } catch (error) { toast('Không thể kiểm tra tool contract', error.message, 'error'); }
  });
  $('#toolModeSelect')?.addEventListener('change', async () => {
    try {
      const wasRunning = Boolean(state.snapshot?.status.runtimeRunning);
      await saveSettings(false);
      toast('Chế độ công cụ đã được lưu', wasRunning ? 'Đang âm thầm tạo lại MCP để áp dụng phạm vi công cụ mới.' : 'Có hiệu lực ở lần khởi động MCP tiếp theo.');
      if (wasRunning) await runRuntime('restart');
    } catch (error) { toast('Chuyển đổi chế độ công cụ thất bại', error.message, 'error'); }
  });
  $('#clearLogs').addEventListener('click', async () => { unwrap(await api.clearLogs()); state.logs = []; renderLogs(); toast('Đã xóa nhật ký'); });
  $$('.log-filter').forEach((button) => button.addEventListener('click', () => {
    state.logFilter = button.dataset.logFilter;
    $$('.log-filter').forEach((item) => item.classList.toggle('active', item === button));
    renderLogs();
  }));
}

async function initialize() {
  try {
    bindEvents();
    api.onProgress(updateProgress);
    api.onLog((entry) => {
      state.logs.push(entry);
      if (state.logs.length > 1000) state.logs.shift();
      if (state.currentPage === 'logs') renderLogs();
    });
    api.onStatus((payload) => {
      if (payload?.snapshot) renderSnapshot(payload.snapshot, { forceForms: false });
    });
    api.onHeartbeat(applyHeartbeat);
    api.onBuildProgress((payload) => {
      if (payload.status === 'output') appendBuildOutput(payload.text || '');
      else if (payload.status === 'running') { $('#buildStatus').textContent = payload.stage === 'test' ? 'Đang kiểm thử' : 'Đang build'; appendBuildOutput(`\n> ${payload.command}\n`); }
      else if (payload.stage === 'complete') $('#buildStatus').textContent = payload.status === 'passed' ? 'Đã vượt qua' : 'Chưa vượt qua';
    });
    const requestedPage = location.hash.slice(1);
    if (pageMeta[requestedPage]) navigate(requestedPage);

    // Show the settings shell immediately. Runtime/network inspection continues
    // in the background so opening Preferences never feels like a diagnostic run.
    document.body.classList.remove('booting');
    document.body.classList.add('booted');
    $('#bootScreen')?.setAttribute('aria-hidden', 'true');

    const firstSnapshot = await refreshSnapshot({ forceForms: true });
    if (firstSnapshot && isCentralExecutor(firstSnapshot.settings)
      && !centralSetupRuntimeBlocked(centralSetupGuidance(firstSnapshot, state.centralEnrollmentStatus, state.centralAuthorityStatus))) {
      // The receipt is reconstructed from the node's durable config/central
      // status, so a renderer reload does not look like a new enrollment.
      await reconcileControlPlaneEnrollment({ quiet: true });
      await reconcileControlPlaneAuthorityStatus({ quiet: true });
      // Central workspace registration is local durable state, not the
      // legacy settings.workspace field.  Rehydrate it once so the wizard
      // resumes at the correct step after the window is reopened.
      if (typeof api.listControlPlaneWorkspaces === 'function') {
        try { await refreshControlPlaneWorkspaces({ quiet: true }); }
        catch (_) {
          state.centralWorkspaceInventoryStatus = 'unknown';
          state.centralWorkspaceInventoryError ||= 'CONTROL_PLANE_WORKSPACE_LIST_FAILED';
          /* The setup card keeps an explicit unknown state. */
        }
      }
    }
    if (firstSnapshot && !firstSnapshot.settings.firstRunCompleted) {
      try {
        navigate('health');
        await inspectHealth();
        unwrap(await api.saveSettings({ firstRunCompleted: true }));
        toast('Kiểm tra sức khỏe lần chạy đầu tiên', 'Đã kiểm tra môi trường hiện tại; có thể nhấp "Sửa chữa nhanh" để xử lý các vấn đề tự động.');
      } catch (error) { toast('Chưa hoàn tất kiểm tra sức khỏe lần chạy đầu tiên', error.message, 'error'); }
    }
  } finally {
    document.body.classList.remove('booting');
    document.body.classList.add('booted');
    $('#bootScreen')?.setAttribute('aria-hidden', 'true');
  }
}

initialize();
