"""Small same-origin operator UI assets for the private control plane.

The assets are Python constants deliberately served only by the authenticated
control-plane process.  Keeping the small UI in the package means the existing
package fingerprint covers the exact HTML, CSS, and JavaScript bytes.  This is
not a replacement for the artifact manifest required at the packaging gate.
"""

from __future__ import annotations


WEB_UI_HTML = """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Control Plane</title>
  <link rel="stylesheet" href="/assets/control-plane-ui.css">
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <p class="eyebrow">PRIVATE TAILNET OPERATOR CONSOLE</p>
        <h1>Control Plane</h1>
        <p id="connection-status" aria-live="polite">Đang kiểm tra phiên vận hành.</p>
      </div>
      <div class="header-actions">
        <button id="refresh" type="button" disabled>Làm mới</button>
        <button id="logout" type="button" class="secondary" hidden>Đăng xuất</button>
      </div>
    </header>

    <section id="login-panel" class="panel" hidden aria-labelledby="login-title">
      <h2 id="login-title">Đăng nhập operator</h2>
      <p>Nhập operator token một lần để tạo phiên ngắn hạn. Token không được lưu trong trình duyệt.</p>
      <form id="login-form">
        <label for="operator-token">Operator token</label>
        <input id="operator-token" name="operator-token" type="password" autocomplete="off" spellcheck="false" required>
        <button type="submit">Tạo phiên riêng tư</button>
      </form>
      <p id="login-error" class="error" role="alert"></p>
    </section>

    <section id="dashboard" hidden>
      <p class="notice">Bảng này chỉ quan sát dữ liệu central và điều khiển admission. Nó không mở shell, không chọn path Windows, không xác nhận job đã dừng và không tự suy diễn Windows đã sẵn sàng.</p>

      <div class="grid cards" aria-live="polite">
        <article class="card">
          <h2>Ubuntu / cơ sở dữ liệu</h2>
          <dl>
            <dt>Service</dt><dd id="service-state">—</dd>
            <dt>SQLite</dt><dd id="sqlite-state">—</dd>
            <dt>Schema</dt><dd id="schema-version">—</dd>
            <dt>Xác thực MCP</dt><dd id="mcp-authentication-mode">—</dd>
            <dt>Build source</dt><dd id="source-revision">—</dd>
            <dt>Gói đã nạp</dt><dd id="package-fingerprint">—</dd>
            <dt>Quan sát lúc</dt><dd id="observed-at">—</dd>
          </dl>
        </article>
        <article class="card">
          <h2>Admission an toàn</h2>
          <p id="admission-state" class="state">—</p>
          <p id="admission-explanation">—</p>
          <div class="actions">
            <button id="close-admission" type="button" disabled>Đóng admission / bảo trì</button>
          </div>
          <p class="muted">Đóng admission chỉ chặn intake/dispatch mới; không khẳng định mọi job đã dừng. Mở lại theo runbook sau khi đối soát, không có nút browser ở giai đoạn này.</p>
        </article>
        <article class="card">
          <h2>Đường điều khiển</h2>
          <p>Console đang quan sát Control Plane. Trạng thái Tunnel/ChatGPT transport không được suy ra từ heartbeat Windows và chỉ được coi là có khi có receipt transport riêng.</p>
          <p class="muted">Read-only control surface: heartbeat node, executor cục bộ, workspace đã chọn và quyền task là các trạng thái tách biệt. “ready” cũ không chứng minh máy còn sẵn sàng hôm nay.</p>
        </article>
      </div>

      <section class="panel">
        <h2>Kết nối một lần (wizard)</h2>
        <p class="muted">Một luồng duy nhất, không chép token/context mỗi lần làm việc: duyệt enrollment → chọn root local tại máy → tạo binding → mở task ghim đích → cài policy local tại máy (owner xác nhận) → giao việc từ ChatGPT/Console. Wizard không tự approve máy lạ, không nhận path Windows và không biến đổi UI thành quyền remote.</p>
        <div class="table-wrap"><table><thead><tr><th>Bước</th><th>Trạng thái hiện tại</th><th>Đi tới</th></tr></thead><tbody id="onboarding-wizard-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Windows nodes</h2>
        <p class="muted">Ngưỡng stale heartbeat: 60 giây. Policy là quan sát do node báo, không phải quyền do browser cấp. Timestamp thiếu hoặc stale không được hiển thị là executor sẵn sàng.</p>
        <div class="table-wrap"><table><thead><tr><th>Tên</th><th>Readiness</th><th>Heartbeat</th><th>Runtime / epoch</th><th>Contract</th><th>Local policy</th></tr></thead><tbody id="nodes-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Workspace đã đăng ký, bindings và contexts</h2>
        <p class="muted">Chỉ chọn workspace generation do Windows node đăng ký. Console không nhận path Windows, nội dung file hoặc secret. Registration không cấp policy/quyền chạy; binding và context vẫn là hai bước riêng.</p>
        <div class="operator-forms">
          <form id="binding-form" class="operator-form">
            <h3>Tạo workspace binding</h3>
            <label>Workspace node đã đăng ký <select id="binding-workspace-registration" required></select></label>
            <button type="submit">Tạo binding</button>
          </form>
          <form id="context-form" class="operator-form">
            <h3>Cấp context tạm thời</h3>
            <label>Binding <select id="context-binding-id" required></select></label>
            <label>Thời lượng <select id="context-duration-minutes"><option value="15">15 phút</option><option value="60" selected>1 giờ</option><option value="240">4 giờ</option><option value="1440">24 giờ</option></select></label>
            <button type="submit">Cấp context</button>
          </form>
        </div>
        <div class="table-wrap"><table><thead><tr><th>Node</th><th>Workspace</th><th>Generation</th><th>Capability</th><th>Trạng thái</th></tr></thead><tbody id="workspace-registrations-body"></tbody></table></div>
        <div class="table-wrap"><table><thead><tr><th>Binding / workspace</th><th>Node</th><th>Generation</th><th>Context / expiry</th><th>Canary</th><th>Control</th></tr></thead><tbody id="bindings-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Yêu cầu và enrollment</h2>
        <p class="muted">Duyệt enrollment chỉ tạo identity cho request đang chờ; không cài policy, binding, context hay thực thi trên node.</p>
        <div class="table-wrap"><table><thead><tr><th>Loại</th><th>ID</th><th>Target</th><th>Trạng thái</th><th>Thời gian</th><th>Thao tác</th></tr></thead><tbody id="requests-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Liên kết tài khoản OAuth</h2>
        <p class="muted">Yêu cầu chỉ xuất hiện sau khi IdP đã xác thực tài khoản tại MCP. Console chỉ thấy ID opaque và thời gian; không hiện subject, email, issuer, token hoặc workspace. Duyệt chỉ cho tài khoản xem inventory được cấp, không tạo context, policy, action hay quyền ghi.</p>
        <div class="table-wrap"><table><thead><tr><th>Yêu cầu</th><th>Trạng thái</th><th>Yêu cầu lúc</th><th>Quyết định lúc</th><th>Thao tác</th></tr></thead><tbody id="oauth-link-requests-body"></tbody></table></div>
        <h3>Tài khoản đã liên kết</h3>
        <div class="table-wrap"><table><thead><tr><th>Principal opaque</th><th>Trạng thái</th><th>Liên kết lúc</th><th>Thu hồi lúc</th><th>Thao tác</th></tr></thead><tbody id="oauth-principals-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Yêu cầu quyền patch</h2>
        <p class="muted">Đây là bản ghi duyệt scope cho một patch tương lai: node/workspace, đường dẫn tương đối, preimage, patch digest, profile kiểm tra và hạn dùng. Duyệt không queue action, không đổi policy Windows, không ghi file, không chạy lệnh và không cấp local authority. Bridge mutation sau này phải kiểm lại toàn bộ scope/policy trước effect.</p>
        <div class="table-wrap"><table><thead><tr><th>Yêu cầu / principal</th><th>Target / scope</th><th>Trạng thái / hết hạn</th><th>Digest</th><th>Thao tác</th></tr></thead><tbody id="permission-requests-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Phiên công việc đa đích (task)</h2>
        <p class="muted">Mỗi task ghim một máy/workspace/generation bất biến cho nhiều lần đọc, xin quyền, patch và quan sát. Hai chat dùng hai task không đổi đích của nhau. Đóng task chỉ chặn action mới; action đã gửi vẫn quan sát/dừng được. ChatGPT không được chọn đích bằng tên hiển thị hay chat_id.</p>
        <form id="task-session-form" class="operator-form">
          <h3>Mở task mới</h3>
          <label>Tài khoản (principal opaque) <select id="task-principal-id" required></select></label>
          <label>Binding đích <select id="task-binding-id" required></select></label>
          <label>Nhãn task <input id="task-label" maxlength="120" autocomplete="off" spellcheck="false" required></label>
          <button type="submit">Mở task ghim đích</button>
        </form>
        <div class="table-wrap"><table><thead><tr><th>Task / nhãn</th><th>Target bất biến</th><th>Hạn / trạng thái</th><th>Thao tác</th></tr></thead><tbody id="task-sessions-body"></tbody></table></div>
        <h3>Nghiệm thu patch local</h3>
        <p class="muted">Receipt completed mới chứng minh file đã đổi ở Windows; nghiệm thu mới đóng vòng task. Từ chối không hoàn tác file — phải mở patch sửa mới.</p>
        <div class="table-wrap"><table><thead><tr><th>Action</th><th>Quyết định</th><th>Lúc / bởi</th><th>Thao tác</th></tr></thead><tbody id="patch-acceptances-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Action và receipt</h2>
        <p class="muted">“Đã gửi” không phải là “đã thực thi”. Payload, local handle và nội dung workspace không được hiển thị ở đây. Một action lịch sử có receipt <code>unknown</code> chỉ được cách ly sau khi operator gõ xác nhận; cách ly không nói rằng Windows chưa đọc hoặc đã hoàn tất.</p>
        <form id="action-reconciliation-form" class="operator-form reconciliation-form">
          <h3>Cách ly action lịch sử chưa xác định</h3>
          <label>Node <select id="reconciliation-device-id" required></select></label>
          <label>Action IDs (mỗi ID một dòng)<textarea id="reconciliation-action-ids" rows="4" maxlength="7000" autocomplete="off" spellcheck="false" required></textarea></label>
          <label>Gõ chính xác <code>HISTORICAL_READ_ONLY_UNKNOWN_EFFECT</code> để chấp nhận rủi ro kiểm toán <input id="reconciliation-declaration" maxlength="128" autocomplete="off" spellcheck="false" required></label>
          <button type="submit">Cách ly, không retry</button>
        </form>
        <form id="dispatch-disposition-form" class="operator-form reconciliation-form">
          <h3>Cách ly dispatch cũ không có receipt</h3>
          <p class="muted">Chỉ dùng cho <code>workspace_context</code> đã hết hạn, đúng một attempt, không có receipt và node stale/unavailable. Action vẫn là <code>dispatch_unconfirmed</code>; thao tác này không tạo receipt, không retry và không mở admission.</p>
          <label>Node <select id="dispatch-disposition-device-id" required></select></label>
          <label>Action IDs (mỗi ID một dòng)<textarea id="dispatch-disposition-action-ids" rows="4" maxlength="7000" autocomplete="off" spellcheck="false" required></textarea></label>
          <label>Gõ chính xác <code>HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH</code> <input id="dispatch-disposition-declaration" maxlength="128" autocomplete="off" spellcheck="false" required></label>
          <label>Lý do vận hành (không ghi secret/path)<textarea id="dispatch-disposition-rationale" rows="2" maxlength="500" autocomplete="off" spellcheck="false" required></textarea></label>
          <button type="submit">Cách ly dispatch, không retry</button>
        </form>
        <div class="table-wrap"><table><thead><tr><th>Action / tool</th><th>Context / node</th><th>Delivery</th><th>Receipt mới nhất</th><th>Thời gian</th><th>Nghiệm thu</th></tr></thead><tbody id="actions-body"></tbody></table></div>
      </section>
    </section>
  </main>
  <script src="/assets/control-plane-ui.js" defer></script>
</body>
</html>
""".encode("utf-8")


WEB_UI_CSS = """* { box-sizing: border-box; }
:root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #0b1220; color: #e5edf9; }
body { margin: 0; min-width: 320px; }
button, input, select, textarea { font: inherit; }
button { background: #1d70f7; border: 1px solid #478cff; border-radius: .45rem; color: white; cursor: pointer; padding: .65rem .9rem; }
button.secondary { background: transparent; border-color: #71829d; }
button:disabled { cursor: not-allowed; opacity: .55; }
input, select, textarea { background: #111c2e; border: 1px solid #71829d; border-radius: .4rem; color: #fff; padding: .65rem; width: min(100%, 34rem); }
.shell { margin: 0 auto; max-width: 1280px; padding: 1.4rem; }
header { align-items: start; border-bottom: 1px solid #2a3b56; display: flex; gap: 1rem; justify-content: space-between; margin-bottom: 1.25rem; padding-bottom: 1rem; }
h1, h2, p { margin-top: 0; }
h1 { margin-bottom: .35rem; }
h2 { font-size: 1.05rem; }
.eyebrow { color: #8fb4ff; font-size: .75rem; font-weight: 700; letter-spacing: .09em; }
.header-actions, .actions { display: flex; flex-wrap: wrap; gap: .6rem; }
.panel, .card { background: #111c2e; border: 1px solid #2a3b56; border-radius: .65rem; margin: 1rem 0; padding: 1rem; }
.grid { display: grid; gap: 1rem; }
.cards { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.operator-forms { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); margin: 1rem 0; }
.operator-form { border: 1px solid #2a3b56; border-radius: .5rem; display: grid; gap: .7rem; padding: .9rem; }
.operator-form h3 { font-size: .95rem; margin: 0; }
.operator-form label { display: grid; gap: .35rem; color: #aebed5; font-size: .9rem; }
.reconciliation-form { margin: 1rem 0; }
.card { margin: 0; }
dl { display: grid; gap: .45rem .8rem; grid-template-columns: minmax(7rem, auto) 1fr; margin: 0; }
dt, .muted { color: #aebed5; }
dd { margin: 0; overflow-wrap: anywhere; }
.state { font-size: 1.25rem; font-weight: 700; }
.notice { background: #172b4d; border-left: 4px solid #478cff; border-radius: .3rem; padding: .8rem; }
.error { color: #ff9b9b; min-height: 1.2rem; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; min-width: 720px; width: 100%; }
th, td { border-bottom: 1px solid #2a3b56; padding: .65rem; text-align: left; vertical-align: top; }
th { color: #aebed5; font-size: .85rem; }
td { overflow-wrap: anywhere; }
@media (max-width: 620px) { .shell { padding: 1rem; } header { display: block; } .header-actions { margin-top: 1rem; } }
""".encode("utf-8")


WEB_UI_JAVASCRIPT = """(() => {
  'use strict';
  const POLL_MS = 5000;
  const STALE_HEARTBEAT_MS = 60000;
  let csrfToken = null;
  let admissionMode = null;
  let pollTimer = null;
  let requestInFlight = false;

  const byId = (id) => document.getElementById(id);
  const dashboard = byId('dashboard');
  const loginPanel = byId('login-panel');
  const connectionStatus = byId('connection-status');
  const refresh = byId('refresh');
  const logout = byId('logout');
  const bindingForm = byId('binding-form');
  const contextForm = byId('context-form');
  const actionReconciliationForm = byId('action-reconciliation-form');
  const dispatchDispositionForm = byId('dispatch-disposition-form');

  function text(id, value) { byId(id).textContent = value === null || value === undefined || value === '' ? 'chưa có quan sát' : String(value); }
  function formatTime(value) {
    if (!Number.isFinite(value)) return 'chưa có quan sát';
    return new Date(value).toLocaleString('vi-VN');
  }
  function heartbeat(value) {
    if (!Number.isFinite(value)) return 'chưa có quan sát';
    const age = Date.now() - value;
    return `${formatTime(value)} (${age > STALE_HEARTBEAT_MS ? 'stale' : 'fresh'})`;
  }
  function nodeReadiness(node) {
    if (node.revoked_at_ms) return 'revoked — không được dispatch';
    if (!Number.isFinite(node.last_seen_at_ms)) return 'unobserved — chưa có heartbeat';
    const age = Date.now() - node.last_seen_at_ms;
    if (age > STALE_HEARTBEAT_MS) return `stale — node từng báo ${node.readiness || 'unknown'}; không coi executor sẵn sàng`;
    return node.readiness || 'unknown';
  }
  function policyState(node) {
    const state = node.policy_state || 'unobserved';
    const observedAt = node.policy_observed_at_ms;
    if (!Number.isFinite(observedAt)) return 'unobserved — chưa có policy observation';
    if (Date.now() - observedAt > STALE_HEARTBEAT_MS) return `stale — policy từng báo ${state}; không cấp quyền task`;
    if (state === 'enabled' && Number.isFinite(node.policy_expires_at_ms) && node.policy_expires_at_ms <= Date.now()) return `expired — ${formatTime(node.policy_expires_at_ms)}`;
    if (state === 'enabled') return `enabled / hết hạn ${formatTime(node.policy_expires_at_ms)}`;
    if (state === 'expired_or_disabled') return `expired_or_disabled / ${formatTime(node.policy_expires_at_ms)}`;
    if (state === 'unavailable') return `unavailable / ${node.policy_reason || 'không có lý do an toàn'}`;
    return 'chưa có quan sát policy từ node';
  }
  function appendCell(row, value) { const cell = document.createElement('td'); cell.textContent = value === null || value === undefined || value === '' ? '—' : String(value); row.appendChild(cell); }
  function setSelectOptions(id, entries, placeholder, label) {
    const select = byId(id); const previous = select.value;
    while (select.firstChild) select.removeChild(select.firstChild);
    const initial = document.createElement('option'); initial.value = ''; initial.textContent = placeholder; select.appendChild(initial);
    for (const entry of entries) { const option = document.createElement('option'); option.value = entry.value; option.textContent = entry.label; select.appendChild(option); }
    if (entries.some((entry) => entry.value === previous)) select.value = previous;
    else if (entries.length === 1) select.value = entries[0].value;
  }
  function appendBindingControls(row, binding, activeContext) {
    const cell = document.createElement('td');
    if (activeContext) { const close = document.createElement('button'); close.type = 'button'; close.className = 'secondary'; close.textContent = 'Đóng context'; close.disabled = !csrfToken; close.addEventListener('click', () => closeContext(activeContext.context_id, close)); cell.appendChild(close); }
    const revoke = document.createElement('button'); revoke.type = 'button'; revoke.className = 'secondary'; revoke.textContent = 'Thu hồi binding'; revoke.disabled = !csrfToken; revoke.addEventListener('click', () => revokeBinding(binding.binding_id, revoke)); cell.appendChild(revoke); row.appendChild(cell);
  }
  function appendReadOnlyButton(row, context) {
    const cell = document.createElement('td');
    const active = context && !context.closed_at_ms && Number.isFinite(context.expires_at_ms) && context.expires_at_ms > Date.now();
    if (!active) { cell.textContent = 'context không còn hiệu lực'; row.appendChild(cell); return; }
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Queue read-only'; button.disabled = !csrfToken;
    button.addEventListener('click', () => queueReadOnly(context.context_id, button)); cell.appendChild(button); row.appendChild(cell);
  }
  function appendEnrollmentApproval(row, enrollment) {
    const cell = document.createElement('td');
    if (enrollment.approved_at_ms) { cell.textContent = '—'; row.appendChild(cell); return; }
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Duyệt enrollment'; button.disabled = !csrfToken;
    button.addEventListener('click', () => approveEnrollment(enrollment.enrollment_id, button)); cell.appendChild(button); row.appendChild(cell);
  }
  function appendOAuthLinkRequestControls(row, request) {
    const cell = document.createElement('td');
    if (request.state !== 'pending') { cell.textContent = '—'; row.appendChild(cell); return; }
    const approve = document.createElement('button'); approve.type = 'button'; approve.textContent = 'Duyệt liên kết'; approve.disabled = !csrfToken;
    approve.addEventListener('click', () => approveOAuthLinkRequest(request.link_request_id, approve)); cell.appendChild(approve);
    const reject = document.createElement('button'); reject.type = 'button'; reject.className = 'secondary'; reject.textContent = 'Từ chối'; reject.disabled = !csrfToken;
    reject.addEventListener('click', () => rejectOAuthLinkRequest(request.link_request_id, reject)); cell.appendChild(reject);
    row.appendChild(cell);
  }
  function appendOAuthPrincipalControls(row, principal) {
    const cell = document.createElement('td');
    if (principal.state !== 'enabled') { cell.textContent = '—'; row.appendChild(cell); return; }
    const revoke = document.createElement('button'); revoke.type = 'button'; revoke.className = 'secondary'; revoke.textContent = 'Thu hồi liên kết'; revoke.disabled = !csrfToken;
    revoke.addEventListener('click', () => revokeOAuthPrincipal(principal.principal_id, revoke)); cell.appendChild(revoke);
    row.appendChild(cell);
  }
  function appendPermissionRequestControls(row, request) {
    const cell = document.createElement('td');
    if (request.state !== 'pending') { cell.textContent = '—'; row.appendChild(cell); return; }
    const approve = document.createElement('button'); approve.type = 'button'; approve.textContent = 'Duyệt scope'; approve.disabled = !csrfToken;
    approve.addEventListener('click', () => approvePermissionRequest(request.permission_request_id, approve)); cell.appendChild(approve);
    const reject = document.createElement('button'); reject.type = 'button'; reject.className = 'secondary'; reject.textContent = 'Từ chối'; reject.disabled = !csrfToken;
    reject.addEventListener('click', () => rejectPermissionRequest(request.permission_request_id, reject)); cell.appendChild(reject);
    row.appendChild(cell);
  }
  function selectedBindingWorkspaceRegistration() {
    const value = byId('binding-workspace-registration').value;
    let registration;
    try { registration = JSON.parse(value); }
    catch { throw new Error('Chọn workspace registration còn hiệu lực trước.'); }
    if (!Array.isArray(registration) || registration.length !== 4 || registration.some((entry) => typeof entry !== 'string' || !entry)) {
      throw new Error('Workspace registration đã chọn không hợp lệ.');
    }
    const [device_id, workspace_id, workspace_generation, display_name] = registration;
    return { device_id, workspace_id, workspace_generation, display_name };
  }
  function clearBody(id) { const body = byId(id); while (body.firstChild) body.removeChild(body.firstChild); return body; }
  function emptyRow(body, columns, value) { const row = document.createElement('tr'); const cell = document.createElement('td'); cell.colSpan = columns; cell.textContent = value; row.appendChild(cell); body.appendChild(row); }
  async function api(path, options = {}) {
    const response = await fetch(path, { ...options, credentials: 'same-origin', headers: { ...(options.headers || {}) } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { const error = new Error(data?.error?.message || 'Yêu cầu không thành công.'); error.status = response.status; throw error; }
    return data;
  }
  function setSessionVisible(active) {
    if (!active) admissionMode = null;
    dashboard.hidden = !active; loginPanel.hidden = active; logout.hidden = !active; refresh.disabled = !active; byId('close-admission').disabled = !active || !csrfToken || admissionMode === 'recovery';
  }
  function stopPolling() { if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null; } }
  function schedulePolling() { stopPolling(); if (!document.hidden) pollTimer = setTimeout(loadOverview, POLL_MS); }
  function renderOverview(data) {
    const health = data.health || {};
    text('service-state', health.ok ? 'healthy (central only)' : 'unhealthy');
    text('sqlite-state', health.sqlite_integrity || null);
    text('schema-version', health.schema_version);
    const mcpAuthenticationMode = health.mcp_authentication_mode;
    text('mcp-authentication-mode', mcpAuthenticationMode === 'oauth_introspection'
      ? 'OAuth account introspection'
      : mcpAuthenticationMode === 'legacy_context_grant'
        ? 'legacy context grant — không phải đăng nhập tài khoản'
        : 'không xác định');
    text('source-revision', health.declared_source_revision || 'không khai báo');
    text('package-fingerprint', health.package_source_sha256 || null);
    text('observed-at', formatTime(data.observed_at_ms));
    const admission = data.admission || {};
    admissionMode = admission.admission_mode || null;
    text('admission-state', admission.admission_mode || null);
    text('admission-explanation', admission.admission_mode === 'recovery' ? 'Intake/dispatch mới đang bị chặn; late receipt hợp lệ vẫn được ghi. Mở lại theo runbook sau khi đối soát.' : 'Admission đang mở. Nút browser chỉ cho phép đóng về recovery; mở lại cần runbook và xác minh độc lập.');
    byId('close-admission').disabled = !csrfToken || admissionMode === 'recovery';

    const nodes = clearBody('nodes-body');
    if (!data.nodes?.length) emptyRow(nodes, 6, 'Chưa có node được enrollment.');
    for (const node of data.nodes || []) { const row = document.createElement('tr'); appendCell(row, node.display_name || node.device_id); appendCell(row, nodeReadiness(node)); appendCell(row, heartbeat(node.last_seen_at_ms)); appendCell(row, `${node.runtime_instance_id || '—'} / ${node.activation_epoch || '—'}`); appendCell(row, node.contract_version); appendCell(row, policyState(node)); nodes.appendChild(row); }
    const nodeById = new Map((data.nodes || []).map((node) => [node.device_id, node]));
    const wizard = clearBody('onboarding-wizard-body');
    {
      const pendingEnrollments = (data.enrollment_requests || []).filter((item) => item.enrollment_id && !item.approved_at_ms);
      const currentRegistrations = (data.workspace_registrations || []).filter((registration) => !registration.retired_at_ms);
      const openTasks = (data.task_sessions || []).filter((task) => !task.closed_at_ms && !(Number.isFinite(task.expires_at_ms) && task.expires_at_ms <= Date.now()));
      const steps = [
        { name: '1. Duyệt enrollment máy', state: (data.nodes || []).length ? 'đã có node' : pendingEnrollments.length ? `đợi duyệt (${pendingEnrollments.length})` : 'chưa có yêu cầu', target: 'Yêu cầu và enrollment' },
        { name: '2. Node đăng ký root local', state: currentRegistrations.length ? `${currentRegistrations.length} root current` : 'chưa có root', target: 'Workspace đã đăng ký' },
        { name: '3. Tạo binding (chọn root)', state: (data.bindings || []).length ? `${data.bindings.length} binding` : 'chưa có binding', target: 'Workspace đã đăng ký' },
        { name: '4. Mở task ghim đích', state: openTasks.length ? `${openTasks.length} task mở` : 'chưa có task mở', target: 'Phiên công việc đa đích' },
        { name: '5. Cài policy tại máy + giao việc', state: 'policy cài bằng CLI tại máy sau khi owner xác nhận; ChatGPT/Console giao việc theo task', target: 'Action và receipt' },
      ];
      for (const step of steps) {
        const row = document.createElement('tr');
        appendCell(row, step.name);
        appendCell(row, step.state);
        appendCell(row, step.target);
        wizard.appendChild(row);
      }
      if (!wizard.childNodes.length) emptyRow(wizard, 3, 'Chưa có dữ liệu onboarding.');
    }
    const registrations = data.workspace_registrations || [];
    const registrationRows = clearBody('workspace-registrations-body');
    if (!registrations.length) emptyRow(registrationRows, 5, 'Chưa có workspace local nào được node đăng ký.');
    for (const registration of registrations) {
      const row = document.createElement('tr');
      const node = nodeById.get(registration.device_id);
      const capabilities = registration.capabilities || {};
      const capabilityLabel = `read=${capabilities.read === true}; write=${capabilities.write === true}; exec=${capabilities.exec === true}`;
      const registrationState = registration.retired_at_ms ? `retired / ${formatTime(registration.retired_at_ms)}` : 'current — inventory only';
      appendCell(row, node?.display_name || registration.device_id);
      appendCell(row, registration.display_name || registration.workspace_id);
      appendCell(row, registration.workspace_generation);
      appendCell(row, capabilityLabel);
      appendCell(row, registrationState);
      registrationRows.appendChild(row);
    }
    const selectableRegistrations = registrations.filter((registration) => !registration.retired_at_ms && !nodeById.get(registration.device_id)?.revoked_at_ms);
    setSelectOptions('binding-workspace-registration', selectableRegistrations.map((registration) => ({
      value: JSON.stringify([registration.device_id, registration.workspace_id, registration.workspace_generation, registration.display_name]),
      label: `${registration.display_name} · ${registration.device_id} · ${registration.workspace_generation}`,
    })), 'Chọn workspace node đã đăng ký', 'workspace registration');
    setSelectOptions('reconciliation-device-id', (data.nodes || []).filter((node) => !node.revoked_at_ms).map((node) => ({ value: node.device_id, label: `${node.display_name || node.device_id} (${node.device_id})` })), 'Chọn node đã duyệt', 'node');
    setSelectOptions('dispatch-disposition-device-id', (data.nodes || []).filter((node) => !node.revoked_at_ms).map((node) => ({ value: node.device_id, label: `${node.display_name || node.device_id} (${node.device_id})` })), 'Chọn node đã duyệt', 'node');

    const contextsByBinding = new Map();
    for (const context of data.contexts || []) { const entries = contextsByBinding.get(context.binding_id) || []; entries.push(`${context.context_id} / ${formatTime(context.expires_at_ms)}`); contextsByBinding.set(context.binding_id, entries); }
    const bindings = clearBody('bindings-body');
    if (!data.bindings?.length) emptyRow(bindings, 5, 'Chưa có workspace binding.');
    for (const binding of data.bindings || []) { const row = document.createElement('tr'); const matchingContexts = (data.contexts || []).filter((context) => context.binding_id === binding.binding_id); const activeContext = matchingContexts.find((context) => !context.closed_at_ms && Number.isFinite(context.expires_at_ms) && context.expires_at_ms > Date.now()) || null; appendCell(row, `${binding.display_name || binding.binding_id} / ${binding.workspace_id || '—'}`); appendCell(row, binding.device_id); appendCell(row, binding.workspace_generation); appendCell(row, (contextsByBinding.get(binding.binding_id) || []).join('\\n') || 'chưa có context'); appendReadOnlyButton(row, activeContext); appendBindingControls(row, binding, activeContext); bindings.appendChild(row); }
    setSelectOptions('context-binding-id', (data.bindings || []).map((binding) => ({ value: binding.binding_id, label: `${binding.display_name || binding.binding_id} (${binding.workspace_id})` })), 'Chọn binding', 'binding');
    setSelectOptions('task-binding-id', (data.bindings || []).filter((binding) => !binding.revoked_at_ms).map((binding) => ({ value: binding.binding_id, label: `${binding.display_name || binding.binding_id} · ${binding.device_id} · ${binding.workspace_generation}` })), 'Chọn binding đích', 'binding');
    setSelectOptions('task-principal-id', (data.oauth_principals || []).map((principal) => ({ value: principal.principal_id, label: principal.principal_id })), 'Chọn principal', 'principal');

    const requests = clearBody('requests-body');
    const work = data.work_requests || [];
    const enrollments = data.enrollment_requests || [];
    if (!work.length && !enrollments.length) emptyRow(requests, 6, 'Chưa có yêu cầu hoặc enrollment.');
    for (const item of work) { const row = document.createElement('tr'); appendCell(row, 'Work request'); appendCell(row, item.request_id); appendCell(row, item.context_id); appendCell(row, item.canceled_at_ms ? 'đã hủy' : 'đã lưu; không suy ra đã thực thi'); appendCell(row, formatTime(item.created_at_ms)); appendCell(row, '—'); requests.appendChild(row); }
    for (const item of enrollments) { const row = document.createElement('tr'); appendCell(row, 'Enrollment'); appendCell(row, item.enrollment_id); appendCell(row, item.display_name || item.device_id); appendCell(row, item.approved_at_ms ? 'đã phê duyệt' : 'đợi phê duyệt'); appendCell(row, formatTime(item.requested_at_ms)); appendEnrollmentApproval(row, item); requests.appendChild(row); }

    const oauthLinkRequests = clearBody('oauth-link-requests-body');
    if (!data.oauth_link_requests?.length) emptyRow(oauthLinkRequests, 5, 'Chưa có yêu cầu liên kết OAuth.');
    for (const request of data.oauth_link_requests || []) {
      const row = document.createElement('tr');
      appendCell(row, request.link_request_id);
      appendCell(row, request.state === 'pending' ? 'đợi owner phê duyệt' : request.state === 'approved' ? 'đã liên kết' : request.state === 'rejected' ? 'đã từ chối' : 'trạng thái không xác định');
      appendCell(row, formatTime(request.requested_at_ms));
      appendCell(row, formatTime(request.decided_at_ms));
      appendOAuthLinkRequestControls(row, request);
      oauthLinkRequests.appendChild(row);
    }
    const oauthPrincipals = clearBody('oauth-principals-body');
    if (!data.oauth_principals?.length) emptyRow(oauthPrincipals, 5, 'Chưa có tài khoản OAuth được liên kết.');
    for (const principal of data.oauth_principals || []) {
      const row = document.createElement('tr');
      appendCell(row, principal.principal_id);
      appendCell(row, principal.state === 'enabled' ? 'đang được cấp inventory' : principal.state === 'revoked' ? 'đã thu hồi' : 'trạng thái không xác định');
      appendCell(row, formatTime(principal.created_at_ms));
      appendCell(row, formatTime(principal.revoked_at_ms));
      appendOAuthPrincipalControls(row, principal);
      oauthPrincipals.appendChild(row);
    }

    const permissionRequests = clearBody('permission-requests-body');
    if (!data.permission_requests?.length) emptyRow(permissionRequests, 5, 'Chưa có yêu cầu quyền patch.');
    for (const request of data.permission_requests || []) {
      const row = document.createElement('tr');
      appendCell(row, `${request.permission_request_id} / ${request.principal_id || '—'}`);
      appendCell(row, `${request.device_id || '—'} / ${request.workspace_id || '—'}\n${request.operation || '—'} ${request.path || '—'}\npreimage=${request.preimage_sha256 || '—'}\npatch=${request.patch_sha256 || '—'}\nvalidation=${request.validation_profile || '—'}`);
      appendCell(row, `${request.state === 'pending' ? 'đợi owner duyệt' : request.state === 'approved' ? 'đã duyệt — chưa tạo effect' : request.state === 'rejected' ? 'đã từ chối' : 'trạng thái không xác định'} / hết hạn ${formatTime(request.expires_at_ms)}`);
      appendCell(row, request.permission_digest || '—');
      appendPermissionRequestControls(row, request);
      permissionRequests.appendChild(row);
    }

    const actions = clearBody('actions-body');
    if (!data.actions?.length) emptyRow(actions, 6, 'Chưa có action được niêm phong.');
    const acceptancesByAction = new Map((data.patch_acceptances || []).map((entry) => [entry.action_id, entry]));
    const taskSessions = clearBody('task-sessions-body');
    if (!data.task_sessions?.length) emptyRow(taskSessions, 4, 'Chưa có task bền vững.');
    for (const task of data.task_sessions || []) {
      const row = document.createElement('tr');
      appendCell(row, `${task.task_id}\n${task.label || '—'} / principal ${task.principal_id || '—'}`);
      appendCell(row, `${task.device_id || '—'} / ${task.workspace_id || '—'}\ngen ${task.workspace_generation || '—'}\nbinding ${task.binding_id || '—'}`);
      const state = task.closed_at_ms ? `đã đóng (${task.close_reason || 'closed'}) / ${formatTime(task.closed_at_ms)}` : Number.isFinite(task.expires_at_ms) && task.expires_at_ms <= Date.now() ? `hết hạn / ${formatTime(task.expires_at_ms)}` : `mở / hết hạn ${formatTime(task.expires_at_ms)}`;
      appendCell(row, state);
      appendTaskControls(row, task);
      taskSessions.appendChild(row);
    }
    const patchAcceptances = clearBody('patch-acceptances-body');
    if (!data.patch_acceptances?.length) emptyRow(patchAcceptances, 4, 'Chưa có nghiệm thu patch local.');
    for (const entry of data.patch_acceptances || []) {
      const row = document.createElement('tr');
      appendCell(row, entry.action_id);
      appendCell(row, entry.decision === 'accepted' ? 'đã nghiệm thu' : 'đã từ chối — cần patch sửa mới, không tự hoàn tác');
      appendCell(row, `${formatTime(entry.decided_at_ms)} / ${entry.decided_by || '—'}`);
      const cell = document.createElement('td'); cell.textContent = '—'; row.appendChild(cell);
      patchAcceptances.appendChild(row);
    }
    for (const action of data.actions || []) {
      const row = document.createElement('tr');
      appendCell(row, `${action.action_id} / ${action.tool_name || '—'}`);
      appendCell(row, `${action.context_id || '—'} / ${action.device_id || '—'}`);
      const delivery = action.dispatch_disposition === 'historical_read_only_unobserved_dispatch' ? 'historical_read_only_unobserved_dispatch — đã cách ly dispatch cũ, không receipt/không retry'
        : action.delivery_state === 'queued' ? 'queued — chưa gửi node'
        : action.delivery_state === 'dispatch_unconfirmed' ? 'dispatch_unconfirmed — chưa rõ node đã nhận'
        : action.delivery_state === 'accepted' ? 'accepted — chờ receipt kết thúc'
        : action.approved_patch_candidate === true && action.delivery_state === 'reconcile_required' ? 'unknown/reconcile_required — patch có thể đã áp tại Windows; phải đối soát local, không retry'
        : action.delivery_state === 'reconcile_required' && action.reconciliation_disposition === 'quarantined_unknown' ? 'quarantined_unknown — rủi ro unknown đã được operator cách ly; không retry'
        : action.delivery_state === 'reconcile_required' ? 'reconcile_required — không tự retry'
        : action.approved_patch_candidate === true && action.delivery_state === 'settled' && action.latest_receipt_state === 'completed' ? 'effect đã áp — chờ proof/semantic acceptance local'
        : `${action.delivery_state || 'unknown'} — xem receipt`;
      appendCell(row, delivery);
      appendCell(row, action.latest_receipt_state ? `${action.latest_receipt_state} (${action.receipt_count || 0}) / ${formatTime(action.latest_receipt_at_ms)}` : 'chưa có receipt');
      appendCell(row, formatTime(action.created_at_ms));
      const control = document.createElement('td');
      const needsAcceptance = action.tool_name === 'agent_workflow' && action.latest_receipt_state === 'completed' && !acceptancesByAction.has(action.action_id);
      const needsExecStop = action.tool_name === 'exec_command' && (!action.latest_receipt_state || !['completed', 'failed', 'stopped'].includes(action.latest_receipt_state));
      if (needsAcceptance) {
        const accept = document.createElement('button'); accept.type = 'button'; accept.textContent = 'Nghiệm thu';
        accept.addEventListener('click', () => recordPatchAcceptance(action.action_id, 'accepted', accept));
        const reject = document.createElement('button'); reject.type = 'button'; reject.className = 'secondary'; reject.textContent = 'Từ chối';
        reject.addEventListener('click', () => recordPatchAcceptance(action.action_id, 'rejected', reject));
        control.appendChild(accept); control.appendChild(reject);
      } else if (needsExecStop) {
        const stop = document.createElement('button'); stop.type = 'button'; stop.textContent = 'Stop';
        stop.addEventListener('click', () => requestExecStop(action.action_id, stop));
        control.appendChild(stop);
      } else { control.textContent = acceptancesByAction.has(action.action_id) ? acceptancesByAction.get(action.action_id).decision : '—'; }
      row.appendChild(control);
      actions.appendChild(row);
    }
  }
  async function loadOverview() {
    if (requestInFlight || document.hidden) return;
    requestInFlight = true; refresh.disabled = true; connectionStatus.textContent = 'Đang đọc quan sát central…';
    try { const data = await api('/v1/ui/overview'); renderOverview(data); connectionStatus.textContent = 'Đã cập nhật dữ liệu central; không suy diễn local execution.'; }
    catch (error) { if (error.status === 403) { csrfToken = null; setSessionVisible(false); connectionStatus.textContent = 'Phiên hết hạn hoặc chưa đăng nhập.'; } else { connectionStatus.textContent = `Không thể tải overview: ${error.message}`; } }
    finally { requestInFlight = false; refresh.disabled = dashboard.hidden; schedulePolling(); }
  }
  async function establishSession() {
    try { const session = await api('/v1/ui/session'); csrfToken = session.csrf_token; setSessionVisible(true); await loadOverview(); }
    catch (error) { csrfToken = null; setSessionVisible(false); connectionStatus.textContent = 'Hãy đăng nhập bằng operator token.'; }
  }
  async function changeAdmission(mode) {
    if (!csrfToken) return;
    byId('close-admission').disabled = true;
    try { await api('/v1/maintenance/admission', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({ mode }) }); await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không đổi admission: ${error.message}`; }
    finally { byId('close-admission').disabled = !csrfToken || admissionMode === 'recovery'; }
  }
  async function queueReadOnly(contextId, button) {
    if (!csrfToken || !contextId) return;
    button.disabled = true; connectionStatus.textContent = 'Đang queue fixed read-only canary…';
    try {
      const result = await api('/v1/ui/read-only-requests', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({ context_id: contextId }) });
      connectionStatus.textContent = `Đã ${result.replayed ? 'tái dùng' : 'queue'} action ${result.action_id}; trạng thái effect vẫn chờ receipt.`;
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không queue canary: ${error.message}`; button.disabled = false; }
  }
  async function approveEnrollment(enrollmentId, button) {
    if (!csrfToken || !enrollmentId) return;
    button.disabled = true; connectionStatus.textContent = 'Đang duyệt identity enrollment…';
    try {
      const result = await api(`/v1/ui/enrollment-requests/${encodeURIComponent(enrollmentId)}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = `Đã duyệt node ${result.display_name || result.device_id}; policy, binding và execution vẫn chưa được tạo.`;
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không duyệt enrollment: ${error.message}`; button.disabled = false; }
  }
  async function approveOAuthLinkRequest(linkRequestId, button) {
    if (!csrfToken || !linkRequestId || !confirm('Duyệt liên kết sẽ cho tài khoản OAuth này xem inventory thuộc owner hiện tại. Không cấp quyền task hoặc quyền ghi. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang duyệt liên kết OAuth…';
    try {
      await api(`/v1/ui/oauth-link-requests/${encodeURIComponent(linkRequestId)}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = 'Đã liên kết tài khoản OAuth; context, policy và action vẫn chưa được tạo.';
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không duyệt liên kết OAuth: ${error.message}`; button.disabled = false; }
  }
  async function rejectOAuthLinkRequest(linkRequestId, button) {
    if (!csrfToken || !linkRequestId || !confirm('Từ chối yêu cầu liên kết OAuth này? Tài khoản đó sẽ không thể tự gửi lại yêu cầu.')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang từ chối liên kết OAuth…';
    try {
      await api(`/v1/ui/oauth-link-requests/${encodeURIComponent(linkRequestId)}/reject`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = 'Đã từ chối yêu cầu liên kết OAuth; không tạo account authority.';
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không từ chối liên kết OAuth: ${error.message}`; button.disabled = false; }
  }
  async function approvePermissionRequest(permissionRequestId, button) {
    if (!csrfToken || !permissionRequestId || !confirm('Duyệt scope này chỉ tạo decision central. Nó không ghi file, chạy lệnh, queue action hoặc đổi policy Windows. Bridge mutation tương lai vẫn phải kiểm lại target, preimage, digest và policy local. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang duyệt scope patch…';
    try {
      await api(`/v1/ui/permission-requests/${encodeURIComponent(permissionRequestId)}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = 'Đã duyệt scope central; chưa có action hay local effect.';
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không duyệt scope: ${error.message}`; button.disabled = false; }
  }
  async function rejectPermissionRequest(permissionRequestId, button) {
    if (!csrfToken || !permissionRequestId || !confirm('Từ chối scope patch này? Không có local effect nào cần dừng vì request chưa tạo action.')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang từ chối scope patch…';
    try {
      await api(`/v1/ui/permission-requests/${encodeURIComponent(permissionRequestId)}/reject`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = 'Đã từ chối scope central; không có action hay local effect.';
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không từ chối scope: ${error.message}`; button.disabled = false; }
  }
  async function revokeOAuthPrincipal(principalId, button) {
    if (!csrfToken || !principalId || !confirm('Thu hồi sẽ chặn yêu cầu OAuth mới của principal này. Nó không dừng Job đã gửi; hãy dùng control Job riêng nếu có. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang thu hồi liên kết OAuth…';
    try {
      await api(`/v1/ui/oauth-principals/${encodeURIComponent(principalId)}/revoke`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) });
      connectionStatus.textContent = 'Đã thu hồi liên kết OAuth; yêu cầu task mới của principal này sẽ bị chặn.';
      await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không thu hồi liên kết OAuth: ${error.message}`; button.disabled = false; }
  }
  async function revokeBinding(bindingId, button) {
    if (!csrfToken || !bindingId || !confirm('Thu hồi binding sẽ từ chối action chưa gửi của binding này. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang thu hồi binding…';
    try { await api(`/v1/ui/bindings/${encodeURIComponent(bindingId)}/revoke`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); connectionStatus.textContent = 'Binding đã bị thu hồi; policy local phải được xử lý riêng.'; await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không thu hồi binding: ${error.message}`; button.disabled = false; }
  }
  async function closeContext(contextId, button) {
    if (!csrfToken || !contextId || !confirm('Đóng context sẽ chặn intake mới trong context này. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang đóng context…';
    try { await api(`/v1/ui/contexts/${encodeURIComponent(contextId)}/close`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); connectionStatus.textContent = 'Context đã đóng; action đã gửi vẫn cần reconciliation riêng.'; await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không đóng context: ${error.message}`; button.disabled = false; }
  }
  function appendTaskControls(row, task) {
    const cell = document.createElement('td');
    if (!task.closed_at_ms) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'secondary'; button.textContent = 'Đóng task';
      button.addEventListener('click', () => closeTaskSession(task.task_id, button));
      cell.appendChild(button);
    } else { cell.textContent = '—'; }
    row.appendChild(cell);
  }
  async function closeTaskSession(taskId, button) {
    if (!csrfToken || !taskId || !confirm('Đóng task sẽ chặn action mới của task này. Action đã gửi vẫn quan sát/dừng được. Tiếp tục?')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang đóng task…';
    try { await api(`/v1/ui/task-sessions/${encodeURIComponent(taskId)}/close`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); connectionStatus.textContent = 'Task đã đóng cho intake mới.'; await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không đóng task: ${error.message}`; button.disabled = false; }
  }
  async function recordPatchAcceptance(actionId, decision, button) {
    if (!csrfToken || !actionId || !confirm(decision === 'accepted' ? 'Nghiệm thu kết quả patch này? Chỉ xác nhận khi đã đối chiếu diff/test độc lập.' : 'Từ chối kết quả patch này? File sẽ không tự hoàn tác; cần patch sửa mới.')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang ghi nghiệm thu patch…';
    try { await api(`/v1/ui/patch-acceptances/${encodeURIComponent(actionId)}`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({ decision }) }); connectionStatus.textContent = decision === 'accepted' ? 'Đã nghiệm thu patch.' : 'Đã từ chối patch; file giữ nguyên.'; await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không ghi nghiệm thu: ${error.message}`; button.disabled = false; }
  }
  async function requestExecStop(actionId, button) {
    if (!csrfToken || !actionId || !confirm('Yêu cầu dừng Job này? Sẽ báo pending cho tới khi node chứng minh cây process đã quiescent. Node offline không báo success.')) return;
    button.disabled = true; connectionStatus.textContent = 'Đang yêu cầu dừng exec…';
    try { await api(`/v1/ui/exec-stops/${encodeURIComponent(actionId)}`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); connectionStatus.textContent = 'Đã gửi yêu cầu dừng; chờ node xác minh.'; await loadOverview(); }
    catch (error) { connectionStatus.textContent = `Không gửi stop: ${error.message}`; button.disabled = false; }
  }
  byId('login-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const input = byId('operator-token'); const error = byId('login-error'); error.textContent = '';
    try { const result = await api('/v1/ui/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ operator_token: input.value }) }); input.value = ''; csrfToken = result.csrf_token; setSessionVisible(true); await loadOverview(); }
    catch (failure) { input.value = ''; error.textContent = failure.message; }
  });
  bindingForm.addEventListener('submit', async (event) => {
    event.preventDefault(); const button = bindingForm.querySelector('button[type="submit"]'); button.disabled = true; connectionStatus.textContent = 'Đang tạo workspace binding…';
    try {
      const registration = selectedBindingWorkspaceRegistration();
      const binding = await api('/v1/ui/bindings', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify(registration) });
      connectionStatus.textContent = `Đã tạo ${binding.binding_id}; cấp context riêng khi cần.`; bindingForm.reset(); await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không tạo binding: ${error.message}`; } finally { button.disabled = !csrfToken; }
  });
  contextForm.addEventListener('submit', async (event) => {
    event.preventDefault(); const button = contextForm.querySelector('button[type="submit"]'); button.disabled = true; connectionStatus.textContent = 'Đang cấp context tạm thời…';
    try {
      const context = await api('/v1/ui/contexts', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({ binding_id: byId('context-binding-id').value, duration_minutes: Number(byId('context-duration-minutes').value) }) });
      connectionStatus.textContent = `Đã cấp ${context.context_id} đến ${formatTime(context.expires_at_ms)}.`; await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không cấp context: ${error.message}`; } finally { button.disabled = !csrfToken; }
  });
  byId('task-session-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const form = byId('task-session-form'); const button = form.querySelector('button[type="submit"]'); button.disabled = true; connectionStatus.textContent = 'Đang mở task ghim đích…';
    try {
      const task = await api('/v1/ui/task-sessions', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({ principal_id: byId('task-principal-id').value, binding_id: byId('task-binding-id').value, label: byId('task-label').value }) });
      connectionStatus.textContent = `Đã mở task ${task.task_id} ghim ${task.device_id}/${task.workspace_id}.`; form.reset(); await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không mở task: ${error.message}`; } finally { button.disabled = !csrfToken; }
  });
  actionReconciliationForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = actionReconciliationForm.querySelector('button[type="submit"]');
    const actionIds = byId('reconciliation-action-ids').value.split(/\\s+/).filter(Boolean);
    const declaration = byId('reconciliation-declaration').value.trim();
    if (!confirm(`Cách ly ${actionIds.length} action lịch sử với receipt unknown? Thao tác này không retry và không xác nhận effect.`)) return;
    button.disabled = true; connectionStatus.textContent = 'Đang ghi nhận cách ly lịch sử có kiểm toán…';
    try {
      const result = await api('/v1/ui/action-reconciliations/quarantine-historical-unknown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken },
        body: JSON.stringify({ device_id: byId('reconciliation-device-id').value, action_ids: actionIds, declaration }),
      });
      connectionStatus.textContent = `Đã cách ly ${result.actions.length} action historical unknown. Receipt gốc vẫn giữ nguyên; không action nào được retry.`;
      actionReconciliationForm.reset(); await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không cách ly action: ${error.message}`; }
    finally { button.disabled = !csrfToken; }
  });
  dispatchDispositionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = dispatchDispositionForm.querySelector('button[type="submit"]');
    const actionIds = byId('dispatch-disposition-action-ids').value.split(/\\s+/).filter(Boolean);
    const declaration = byId('dispatch-disposition-declaration').value.trim();
    const rationale = byId('dispatch-disposition-rationale').value.trim();
    if (!confirm(`Cách ly ${actionIds.length} dispatch cũ không có receipt? Action vẫn unconfirmed, không retry và không tạo receipt.`)) return;
    button.disabled = true; connectionStatus.textContent = 'Đang ghi nhận disposition dispatch lịch sử…';
    try {
      const result = await api('/v1/ui/action-dispositions/quarantine-historical-unobserved-dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken },
        body: JSON.stringify({
          device_id: byId('dispatch-disposition-device-id').value,
          action_ids: actionIds,
          declaration,
          rationale,
        }),
      });
      connectionStatus.textContent = `Đã cách ly ${result.actions.length} dispatch lịch sử; không tạo receipt và không retry.`;
      dispatchDispositionForm.reset(); await loadOverview();
    } catch (error) { connectionStatus.textContent = `Không cách ly dispatch: ${error.message}`; }
    finally { button.disabled = !csrfToken; }
  });
  refresh.addEventListener('click', loadOverview);
  logout.addEventListener('click', async () => { try { await api('/v1/ui/logout', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); } finally { csrfToken = null; stopPolling(); setSessionVisible(false); connectionStatus.textContent = 'Đã đăng xuất; phiên server đã bị hủy.'; } });
  byId('close-admission').addEventListener('click', () => changeAdmission('recovery'));
  document.addEventListener('visibilitychange', () => { if (document.hidden) stopPolling(); else loadOverview(); });
  establishSession();
})();
""".encode("utf-8")


WEB_UI_CSP = "default-src 'self'; base-uri 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; img-src 'self'; object-src 'none'; script-src 'self'; style-src 'self'"
