from __future__ import annotations

import json
import shutil
import subprocess
import unittest

from control_plane.web_ui import WEB_UI_HTML, WEB_UI_JAVASCRIPT


@unittest.skipUnless(shutil.which("node"), "Console behavior tests require Node.js")
class FolderSetupConsoleTests(unittest.TestCase):
    def run_browser_check(self, check: str) -> None:
        # Execute the production closure with a tiny DOM and fetch fixture.
        # Replace its initial session request only; no production behavior is
        # reimplemented in the tests.
        javascript = WEB_UI_JAVASCRIPT.decode("utf-8").replace(
            "  establishSession();\n})();",
            """  globalThis.setup = {
    folderSetupPlan, folderSetupContextBlocker, renderFolderSetup, submitFolderSetup,
    ready(data, selection) {
      csrfToken = 'test-csrf'; folderSetupOverview = data;
      byId('folder-setup-workspace').value = selection;
      byId('folder-setup-duration').value = '60';
    }
  };
})();""",
        )
        harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor() { this.children = []; this.value = ''; this.listeners = {}; this.disabled = false; this.textContent = ''; }
  get firstChild() { return this.children[0]; }
  get childNodes() { return this.children; }
  appendChild(child) { this.children.push(child); }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  querySelector() { return this.button ||= new Element(); }
  reset() {}
}
const elements = new Map();
const element = (id) => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
element('folder-setup-duration').value = '60';
const fixture = () => ({
  nodes: [{ device_id: 'device-a', endpoint_id: 'endpoint-a', display_name: 'Máy A', revoked_at_ms: null }],
  workspace_registrations: [{ device_id: 'device-a', workspace_id: 'workspace-a', workspace_generation: 'generation-a', display_name: 'Dự án A', retired_at_ms: null, capabilities: { read: true, write: true, exec: false } }],
  bindings: [], contexts: [], actions: [], enrollment_requests: []
});
const binding = () => ({ binding_id: 'binding-a', device_id: 'device-a', endpoint_id: 'endpoint-a', workspace_id: 'workspace-a', workspace_generation: 'generation-a', revoked_at_ms: null });
const context = () => ({ context_id: 'context-a', ...binding(), closed_at_ms: null, expires_at_ms: Date.now() + 600000 });
const selection = JSON.stringify(['device-a', 'workspace-a', 'generation-a']);
let state = fixture();
let requests = [];
let confirmations = [];
let confirmResult = true;
let failContext = false;
let loseBindingResponse = false;
let afterRead = null;
const browser = {
  document: { hidden: true, getElementById: element, createElement: () => new Element(), addEventListener() {} },
  console, Date, setTimeout, clearTimeout,
  confirm(message) { confirmations.push(message); return confirmResult; },
  async fetch(path, options = {}) {
    requests.push({ path, ...options });
    if (!options.method || options.method === 'GET') {
      const result = structuredClone(state);
      if (afterRead) afterRead();
      return { ok: true, json: async () => result };
    }
    assert.equal(options.headers['X-Control-Plane-CSRF'], 'test-csrf');
    assert.equal(options.credentials, 'same-origin');
    if (path === '/v1/ui/bindings') {
      assert.deepEqual(Object.keys(JSON.parse(options.body)).sort(), ['device_id', 'display_name', 'workspace_generation', 'workspace_id']);
      state.bindings.push(binding());
      if (loseBindingResponse) throw new Error('connection lost');
      return { ok: true, json: async () => binding() };
    }
    assert.equal(path, '/v1/ui/contexts');
    assert.deepEqual(JSON.parse(options.body), { binding_id: 'binding-a', duration_minutes: 60 });
    if (failContext) return { ok: false, status: 503, json: async () => ({ error: { message: 'context rejected' } }) };
    state.contexts.push(context());
    return { ok: true, json: async () => context() };
  }
};
vm.createContext(browser);
"""
        # Normalize cross-realm values only for assertions that need deep equality.
        harness += f"\nvm.runInContext({json.dumps(javascript)}, browser);\n"
        harness += "const setup = browser.setup;\n(async () => {\n" + check + "\n})().catch((error) => { console.error(error); process.exitCode = 1; });\n"
        result = subprocess.run(
            [shutil.which("node") or "node", "-"],
            input=harness,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_target_selector_uses_registered_scope_and_fails_closed(self) -> None:
        self.run_browser_check(r"""
setup.ready(state, selection);
setup.renderFolderSetup(state);
assert.equal(element('folder-setup-workspace').value, selection);
assert.equal(element('folder-setup-workspace').children[1].textContent, 'Máy A · Dự án A');
assert.match(element('folder-setup-summary').textContent, /generation-a/);
assert.equal(element('folder-setup-submit').disabled, false);
assert.throws(() => setup.folderSetupPlan(state, '[]', 60), /không hợp lệ/);
assert.throws(() => setup.folderSetupPlan(state, selection, 0), /thời lượng/);
state.workspace_registrations[0].workspace_generation = 'generation-b';
assert.throws(() => setup.folderSetupPlan(state, selection, 60), /Generation đã đổi/);
state = fixture(); state.workspace_registrations.push({ ...state.workspace_registrations[0] });
assert.throws(() => setup.folderSetupPlan(state, selection, 60), /mơ hồ/);
state = fixture(); state.nodes[0].revoked_at_ms = 1;
assert.throws(() => setup.folderSetupPlan(state, selection, 60), /Máy chưa được duyệt/);
""")

    def test_reuses_only_unique_current_binding(self) -> None:
        self.run_browser_check(r"""
state.bindings = [binding()];
setup.ready(state, selection);
await setup.submitFolderSetup({ preventDefault() {} });
assert.deepEqual(requests.filter((item) => item.method === 'POST').map((item) => item.path), ['/v1/ui/contexts']);
assert.equal(confirmations.length, 1);
for (const part of ['device-a', 'workspace-a', 'generation-a', '60 phút', 'Sửa có', 'Chạy không']) assert.ok(confirmations[0].includes(part));
assert.match(element('folder-setup-result').textContent, /dùng lại/);
state = fixture(); state.bindings = [binding(), { ...binding(), binding_id: 'binding-b' }];
assert.throws(() => setup.folderSetupPlan(state, selection, 60), /Liên kết thư mục bị mơ hồ/);
state.bindings = [{ ...binding(), endpoint_id: 'old-endpoint' }];
assert.throws(() => setup.folderSetupPlan(state, selection, 60), /khác identity/);
""")

    def test_create_binding_and_context_only_after_explicit_confirmation(self) -> None:
        self.run_browser_check(r"""
setup.ready(state, selection);
setup.renderFolderSetup(state);
assert.equal(requests.length, 0);
confirmResult = false;
await setup.submitFolderSetup({ preventDefault() {} });
assert.equal(requests.filter((item) => item.method === 'POST').length, 0);
confirmResult = true;
await setup.submitFolderSetup({ preventDefault() {} });
assert.deepEqual(requests.filter((item) => item.method === 'POST').map((item) => item.path), ['/v1/ui/bindings', '/v1/ui/contexts']);
assert.match(element('folder-setup-result').textContent, /Đã tạo liên kết và cấp context/);
assert.equal(element('folder-setup-workspace').value, selection);
""")

    def test_never_reuses_action_context_or_adds_live_authority_window(self) -> None:
        self.run_browser_check(r"""
state.bindings = [binding()]; state.contexts = [context()];
setup.ready(state, selection); setup.renderFolderSetup(state);
assert.equal(element('folder-setup-submit').disabled, true);
assert.match(element('folder-setup-summary').textContent, /Đã có cửa sổ context/);
state.actions = [{ action_id: 'action-a', context_id: 'context-a', authority_mode: 'standing' }];
setup.renderFolderSetup(state);
assert.match(element('folder-setup-summary').textContent, /Không dùng context tác vụ làm quyền duy trì/);
await setup.submitFolderSetup({ preventDefault() {} });
assert.equal(confirmations.length, 0);
assert.equal(requests.filter((item) => item.method === 'POST').length, 0);
state.contexts.push({ ...context(), context_id: 'context-b' });
const plan = setup.folderSetupPlan(state, selection, 60);
assert.match(setup.folderSetupContextBlocker(plan, state), /nhiều context/);
""")

    def test_partial_failure_keeps_scope_and_does_not_retry_or_rollback(self) -> None:
        self.run_browser_check(r"""
setup.ready(state, selection); failContext = true;
await setup.submitFolderSetup({ preventDefault() {} });
assert.deepEqual(requests.filter((item) => item.method === 'POST').map((item) => item.path), ['/v1/ui/bindings', '/v1/ui/contexts']);
assert.equal(state.bindings.length, 1); assert.equal(state.contexts.length, 0);
assert.match(element('folder-setup-result').textContent, /Đã tạo liên kết binding-a; chưa xác nhận cấp context/);
assert.match(element('folder-setup-result').textContent, /không tự gửi lại hoặc hoàn tác/);
assert.equal(element('folder-setup-workspace').value, selection);
failContext = false;
await setup.submitFolderSetup({ preventDefault() {} });
assert.deepEqual(requests.filter((item) => item.method === 'POST').map((item) => item.path), ['/v1/ui/bindings', '/v1/ui/contexts', '/v1/ui/contexts']);
""")

    def test_lost_binding_response_is_observed_without_mutation_replay(self) -> None:
        self.run_browser_check(r"""
setup.ready(state, selection); loseBindingResponse = true;
await setup.submitFolderSetup({ preventDefault() {} });
assert.deepEqual(requests.filter((item) => item.method === 'POST').map((item) => item.path), ['/v1/ui/bindings']);
assert.match(element('folder-setup-result').textContent, /server có thể đã nhận yêu cầu/);
assert.equal(state.bindings.length, 1); assert.equal(state.contexts.length, 0);
assert.equal(element('folder-setup-workspace').value, selection);
""")

    def test_change_after_confirmation_stops_before_first_mutation(self) -> None:
        self.run_browser_check(r"""
setup.ready(state, selection);
let reads = 0;
afterRead = () => { if (++reads === 1) state.workspace_registrations[0].workspace_generation = 'generation-b'; };
await setup.submitFolderSetup({ preventDefault() {} });
assert.equal(confirmations.length, 1);
assert.equal(requests.filter((item) => item.method === 'POST').length, 0);
assert.match(element('folder-setup-result').textContent, /Generation đã đổi/);
assert.equal(element('folder-setup-workspace').value, selection);
assert.equal(element('folder-setup-submit').disabled, true);
""")

    def test_advanced_forms_and_authority_boundaries_remain_explicit(self) -> None:
        html = WEB_UI_HTML.decode("utf-8")
        javascript = WEB_UI_JAVASCRIPT.decode("utf-8")
        for element_id in ("folder-setup-form", "folder-setup-workspace", "folder-setup-duration", "advanced-folder-setup", "binding-form", "context-form"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("không tự gia hạn", html)
        self.assertIn("Không dùng context tác vụ làm quyền duy trì", javascript)
        self.assertIn("'X-Control-Plane-CSRF': csrfToken", javascript)
        self.assertNotIn("/v1/ui/mcp-service-grants',", javascript)
        self.assertNotIn("/v1/ui/scoped-pilot-decisions',", javascript)
        self.assertNotIn("localStorage", javascript)
        self.assertNotIn("access_token", javascript)


if __name__ == "__main__":
    unittest.main()
