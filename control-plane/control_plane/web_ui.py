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
          <h2>Giới hạn pilot</h2>
          <p>Read-only control surface. Trạng thái “ready” của node là heartbeat do node báo, không phải bằng chứng job đang chạy hoặc quyền ghi.</p>
          <p class="muted">Browser chỉ có thể queue một canary `workspace_context` cố định trên context còn hiệu lực. Thao tác hủy/stop, binding wizard và remote execution chỉ xuất hiện sau các gate riêng.</p>
        </article>
      </div>

      <section class="panel">
        <h2>Windows nodes</h2>
        <p class="muted">Ngưỡng stale heartbeat: 60 giây. Policy là quan sát do node báo, không phải quyền do browser cấp. Timestamp thiếu được hiển thị là chưa có quan sát.</p>
        <div class="table-wrap"><table><thead><tr><th>Tên</th><th>Readiness</th><th>Heartbeat</th><th>Runtime / epoch</th><th>Contract</th><th>Local policy</th></tr></thead><tbody id="nodes-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Workspace bindings và contexts</h2>
        <div class="table-wrap"><table><thead><tr><th>Binding / workspace</th><th>Node</th><th>Generation</th><th>Context / expiry</th><th>Canary</th></tr></thead><tbody id="bindings-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Yêu cầu và enrollment</h2>
        <p class="muted">Duyệt enrollment chỉ tạo identity cho request đang chờ; không cài policy, binding, context hay thực thi trên node.</p>
        <div class="table-wrap"><table><thead><tr><th>Loại</th><th>ID</th><th>Target</th><th>Trạng thái</th><th>Thời gian</th><th>Thao tác</th></tr></thead><tbody id="requests-body"></tbody></table></div>
      </section>
      <section class="panel">
        <h2>Action và receipt</h2>
        <p class="muted">“Đã gửi” không phải là “đã thực thi”. Payload, local handle và nội dung workspace không được hiển thị ở đây.</p>
        <div class="table-wrap"><table><thead><tr><th>Action / tool</th><th>Context / node</th><th>Delivery</th><th>Receipt mới nhất</th><th>Thời gian</th></tr></thead><tbody id="actions-body"></tbody></table></div>
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
button, input { font: inherit; }
button { background: #1d70f7; border: 1px solid #478cff; border-radius: .45rem; color: white; cursor: pointer; padding: .65rem .9rem; }
button.secondary { background: transparent; border-color: #71829d; }
button:disabled { cursor: not-allowed; opacity: .55; }
input { background: #111c2e; border: 1px solid #71829d; border-radius: .4rem; color: #fff; padding: .65rem; width: min(100%, 34rem); }
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
  function policyState(node) {
    const state = node.policy_state || 'unobserved';
    if (state === 'enabled') return `enabled / hết hạn ${formatTime(node.policy_expires_at_ms)}`;
    if (state === 'expired_or_disabled') return `expired_or_disabled / ${formatTime(node.policy_expires_at_ms)}`;
    if (state === 'unavailable') return `unavailable / ${node.policy_reason || 'không có lý do an toàn'}`;
    return 'chưa có quan sát policy từ node';
  }
  function appendCell(row, value) { const cell = document.createElement('td'); cell.textContent = value === null || value === undefined || value === '' ? '—' : String(value); row.appendChild(cell); }
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
    for (const node of data.nodes || []) { const row = document.createElement('tr'); appendCell(row, node.display_name || node.device_id); appendCell(row, node.readiness); appendCell(row, heartbeat(node.last_seen_at_ms)); appendCell(row, `${node.runtime_instance_id || '—'} / ${node.activation_epoch || '—'}`); appendCell(row, node.contract_version); appendCell(row, policyState(node)); nodes.appendChild(row); }

    const contextsByBinding = new Map();
    for (const context of data.contexts || []) { const entries = contextsByBinding.get(context.binding_id) || []; entries.push(`${context.context_id} / ${formatTime(context.expires_at_ms)}`); contextsByBinding.set(context.binding_id, entries); }
    const bindings = clearBody('bindings-body');
    if (!data.bindings?.length) emptyRow(bindings, 5, 'Chưa có workspace binding.');
    for (const binding of data.bindings || []) { const row = document.createElement('tr'); const matchingContexts = (data.contexts || []).filter((context) => context.binding_id === binding.binding_id); appendCell(row, `${binding.display_name || binding.binding_id} / ${binding.workspace_id || '—'}`); appendCell(row, binding.device_id); appendCell(row, binding.workspace_generation); appendCell(row, (contextsByBinding.get(binding.binding_id) || []).join('\\n') || 'chưa có context'); appendReadOnlyButton(row, matchingContexts.find((context) => !context.closed_at_ms && Number.isFinite(context.expires_at_ms) && context.expires_at_ms > Date.now()) || null); bindings.appendChild(row); }

    const requests = clearBody('requests-body');
    const work = data.work_requests || [];
    const enrollments = data.enrollment_requests || [];
    if (!work.length && !enrollments.length) emptyRow(requests, 6, 'Chưa có yêu cầu hoặc enrollment.');
    for (const item of work) { const row = document.createElement('tr'); appendCell(row, 'Work request'); appendCell(row, item.request_id); appendCell(row, item.context_id); appendCell(row, item.canceled_at_ms ? 'đã hủy' : 'đã lưu; không suy ra đã thực thi'); appendCell(row, formatTime(item.created_at_ms)); appendCell(row, '—'); requests.appendChild(row); }
    for (const item of enrollments) { const row = document.createElement('tr'); appendCell(row, 'Enrollment'); appendCell(row, item.enrollment_id); appendCell(row, item.display_name || item.device_id); appendCell(row, item.approved_at_ms ? 'đã phê duyệt' : 'đợi phê duyệt'); appendCell(row, formatTime(item.requested_at_ms)); appendEnrollmentApproval(row, item); requests.appendChild(row); }

    const actions = clearBody('actions-body');
    if (!data.actions?.length) emptyRow(actions, 5, 'Chưa có action được niêm phong.');
    for (const action of data.actions || []) {
      const row = document.createElement('tr');
      appendCell(row, `${action.action_id} / ${action.tool_name || '—'}`);
      appendCell(row, `${action.context_id || '—'} / ${action.device_id || '—'}`);
      const delivery = action.delivery_state === 'queued' ? 'queued — chưa gửi node'
        : action.delivery_state === 'dispatch_unconfirmed' ? 'dispatch_unconfirmed — chưa rõ node đã nhận'
        : action.delivery_state === 'accepted' ? 'accepted — chờ receipt kết thúc'
        : action.delivery_state === 'reconcile_required' ? 'reconcile_required — không tự retry'
        : `${action.delivery_state || 'unknown'} — xem receipt`;
      appendCell(row, delivery);
      appendCell(row, action.latest_receipt_state ? `${action.latest_receipt_state} (${action.receipt_count || 0}) / ${formatTime(action.latest_receipt_at_ms)}` : 'chưa có receipt');
      appendCell(row, formatTime(action.created_at_ms));
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
  byId('login-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const input = byId('operator-token'); const error = byId('login-error'); error.textContent = '';
    try { const result = await api('/v1/ui/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ operator_token: input.value }) }); input.value = ''; csrfToken = result.csrf_token; setSessionVisible(true); await loadOverview(); }
    catch (failure) { input.value = ''; error.textContent = failure.message; }
  });
  refresh.addEventListener('click', loadOverview);
  logout.addEventListener('click', async () => { try { await api('/v1/ui/logout', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Control-Plane-CSRF': csrfToken }, body: JSON.stringify({}) }); } finally { csrfToken = null; stopPolling(); setSessionVisible(false); connectionStatus.textContent = 'Đã đăng xuất; phiên server đã bị hủy.'; } });
  byId('close-admission').addEventListener('click', () => changeAdmission('recovery'));
  document.addEventListener('visibilitychange', () => { if (document.hidden) stopPolling(); else loadOverview(); });
  establishSession();
})();
""".encode("utf-8")


WEB_UI_CSP = "default-src 'self'; base-uri 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; img-src 'self'; object-src 'none'; script-src 'self'; style-src 'self'"
