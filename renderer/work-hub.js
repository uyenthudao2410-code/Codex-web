'use strict';
/*
 * Work Hub UI — Đợt A of docs/research/261022_FEATURE_EXPANSION_CATALOG.md.
 * One daily-work page: F03 projects, F01/F04 request preparation, F05 context
 * basket, F20 saved recipes, F29 handoff preview, F22 attention notifications,
 * F31 Ctrl+K unified search. Logic lives in work-hub-store.js (tested);
 * this file is DOM wiring only. Task file changes / build artifacts (F09/F12)
 * are summarized here from task state and opened in full on the Tasks page.
 */
(function () {
  const S = window.WorkHubStore;
  if (!S) return;
  const $ = (sel) => document.querySelector(sel);

  const adapter = {
    load() {
      try { const raw = localStorage.getItem('coding-tools-work-hub-v1'); return raw ? JSON.parse(raw) : null; }
      catch { return null; }
    },
    save(data) {
      try { localStorage.setItem('coding-tools-work-hub-v1', JSON.stringify(data)); } catch { /* keep in-memory */ }
    },
  };
  const store = S.createStore(adapter);
  const ui = { snapshot: null, taskPayload: null, selectedPromptId: '', selectedType: 'bugfix', dirRel: '', viewerRel: '' };

  function currentProject() {
    const settings = ui.snapshot?.settings || {};
    return String(settings.workspace || '').trim();
  }
  function recentProjects() {
    const settings = ui.snapshot?.settings || {};
    const list = Array.isArray(settings.recentWorkspaces) ? settings.recentWorkspaces.slice() : [];
    const current = currentProject();
    if (current && !list.some((p) => S.workspaceKeyOf(p) === S.workspaceKeyOf(current))) list.unshift(current);
    return store.sortProjects(list.filter(Boolean));
  }
  async function copyText(text, button) {
    const value = String(text || '');
    if (!value) return;
    try { await navigator.clipboard.writeText(value); }
    catch {
      const ta = document.createElement('textarea');
      ta.value = value; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch { /* clipboard unavailable */ }
      ta.remove();
    }
    if (button) { const old = button.textContent; button.textContent = 'Đã sao chép'; setTimeout(() => { button.textContent = old; }, 1200); }
  }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // ---------- F03 projects ----------
  function renderProjects() {
    const box = $('#whProjects');
    if (!box) return;
    box.replaceChildren();
    const projects = recentProjects();
    if (!projects.length) { box.appendChild(el('span', 'task-muted', 'Chưa có dự án nào. Hãy chọn thư mục làm việc trước.')); return; }
    const current = currentProject();
    for (const project of projects) {
      const row = el('div', 'wh-row');
      const pin = store.pinOf(project);
      const main = el('div', 'wh-row-main');
      main.appendChild(el('b', '', store.projectLabel(project)));
      main.appendChild(el('small', '', project));
      row.appendChild(main);
      if (S.workspaceKeyOf(project) === S.workspaceKeyOf(current)) row.appendChild(el('span', 'soft-badge', 'Đang dùng'));
      const pinBtn = el('button', 'secondary-button wh-small', pin.pinned ? 'Bỏ ghim' : 'Ghim');
      pinBtn.addEventListener('click', () => { store.setPin(project, { pinned: !pin.pinned }); renderProjects(); });
      const aliasBtn = el('button', 'secondary-button wh-small', 'Đặt tên');
      aliasBtn.addEventListener('click', () => {
        const alias = window.prompt('Tên dễ nhớ cho dự án:', pin.alias || store.projectLabel(project));
        if (alias !== null) { store.setPin(project, { alias }); renderProjects(); }
      });
      row.append(pinBtn, aliasBtn);
      box.appendChild(row);
    }
  }

  // ---------- F01 + F04 request preparation ----------
  function renderPromptOptions() {
    const select = $('#whPromptSelect');
    if (!select) return;
    const prompts = store.listPrompts();
    select.replaceChildren();
    for (const p of prompts) {
      const opt = document.createElement('option');
      opt.value = p.id; opt.textContent = p.name;
      select.appendChild(opt);
    }
    if (!prompts.some((p) => p.id === ui.selectedPromptId)) ui.selectedPromptId = prompts[0]?.id || '';
    select.value = ui.selectedPromptId;
    const selected = prompts.find((p) => p.id === ui.selectedPromptId);
    if (selected) { $('#whPromptName').value = selected.name; $('#whPromptBody').value = selected.body; }
  }
  function renderTypeFields() {
    const box = $('#whTypeFields');
    if (!box) return;
    box.replaceChildren();
    const def = S.TASK_TYPES[ui.selectedType];
    for (const field of def.fields) {
      const label = el('label', 'field');
      label.appendChild(el('span', '', field.label + (field.required ? ' *' : '')));
      const input = document.createElement('input');
      input.id = `whField-${field.key}`;
      input.placeholder = field.label;
      label.appendChild(input);
      box.appendChild(label);
    }
  }
  function fieldValues() {
    const def = S.TASK_TYPES[ui.selectedType];
    const values = {};
    for (const field of def.fields) values[field.key] = $(`#whField-${field.key}`)?.value || '';
    return values;
  }
  function firstFieldValue() {
    const def = S.TASK_TYPES[ui.selectedType];
    return String(fieldValues()[def.fields[0].key] || '').trim();
  }
  function buildFromType() {
    const preview = $('#whPreview');
    try {
      preview.value = S.buildRequest({
        type: ui.selectedType,
        fields: fieldValues(),
        project: currentProject(),
        filesText: store.contextPackageText(currentProject()),
      });
    } catch (error) { preview.value = `Chưa đủ thông tin: ${error.message}`; }
  }
  function buildFromPrompt() {
    const prompt = store.listPrompts().find((p) => p.id === ui.selectedPromptId);
    if (!prompt) return;
    $('#whPreview').value = S.fillTemplate(prompt.body, {
      project: currentProject(),
      request: firstFieldValue(),
      files: store.contextPackageText(currentProject()) || '(chưa chọn tệp)',
    });
  }

  // ---------- F05 basket ----------
  function renderBasket() {
    const label = $('#whBasketProject');
    if (label) label.textContent = currentProject() || 'Chưa chọn dự án';
    const box = $('#whBasketList');
    if (!box) return;
    box.replaceChildren();
    const files = store.basketFor(currentProject());
    if (!files.length) { box.appendChild(el('span', 'task-muted', 'Giỏ trống. Thêm đường dẫn tệp hoặc nhập từ tác vụ hiện tại.')); return; }
    for (const file of files) {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.appendChild(el('span', '', file.path));
      if (file.size !== null) main.appendChild(el('small', '', `${file.size} bytes`));
      row.appendChild(main);
      const remove = el('button', 'secondary-button wh-small', 'Bỏ');
      remove.addEventListener('click', () => { store.removeFromBasket(currentProject(), file.path); renderBasket(); });
      row.appendChild(remove);
      box.appendChild(row);
    }
  }

  // ---------- F20 recipes ----------
  function renderRecipes() {
    const box = $('#whRecipeList');
    if (!box) return;
    box.replaceChildren();
    const recipes = store.listRecipes();
    if (!recipes.length) { box.appendChild(el('span', 'task-muted', 'Chưa có lệnh nào được lưu.')); return; }
    for (const recipe of recipes) {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.appendChild(el('b', '', recipe.name));
      main.appendChild(el('small', '', recipe.command + (recipe.cwd ? `  ·  ${recipe.cwd}` : '')));
      row.appendChild(main);
      const copy = el('button', 'secondary-button wh-small', 'Sao chép lệnh');
      copy.addEventListener('click', () => copyText(recipe.command, copy));
      const remove = el('button', 'secondary-button wh-small', 'Xóa');
      remove.addEventListener('click', () => { store.removeRecipe(recipe.id); renderRecipes(); });
      row.append(copy, remove);
      box.appendChild(row);
    }
  }

  // ---------- F09/F12 task summary + F29 handoff + F22 notify ----------
  function renderTaskSummary() {
    const box = $('#whTaskSummary');
    if (!box) return;
    box.replaceChildren();
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if (!task) { box.appendChild(el('span', 'task-muted', 'Chưa có trạng thái tác vụ. Mở trang Tác vụ & kết quả để xem chi tiết.')); return; }
    const preview = S.handoffPreview(task);
    const files = preview?.files || [];
    box.appendChild(el('p', '', `Tệp đã sửa đổi (${files.length}): ${files.length ? files.join(', ') : 'chưa ghi nhận'}`));
    const tests = Array.isArray(task.tests) ? task.tests : [];
    box.appendChild(el('p', '', `Kiểm thử gần đây: ${tests.length ? `${tests.filter((t) => String(t.status).toLowerCase() === 'passed').length}/${tests.length} đạt` : 'chưa có'}. Xem diff đầy đủ và sản phẩm đầu ra ở trang Tác vụ & kết quả.`));
    const open = el('button', 'secondary-button wh-small', 'Mở Tác vụ & kết quả');
    open.addEventListener('click', () => window.navigate?.('task'));
    box.appendChild(open);
  }
  function renderHandoff() {
    const view = $('#whHandoffView');
    if (!view) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const preview = S.handoffPreview(task);
    view.textContent = preview
      ? S.formatHandoffText(preview)
      : 'Chưa có trạng thái tác vụ để tạo bản xem trước. Bản xem trước không tạo Job và không chạy lại lệnh nào.';
  }
  function maybeNotify(task) {
    if (!task || typeof Notification === 'undefined') return;
    const status = String(task.status || '').toLowerCase();
    const attention = { completed: 'đã hoàn thành', complete: 'đã hoàn thành', done: 'đã hoàn thành', failed: 'bị lỗi', error: 'bị lỗi', waiting_approval: 'đang chờ duyệt', needs_approval: 'đang chờ duyệt', paused: 'đã tạm dừng' }[status];
    if (!attention) return;
    const id = `${task.id || task.task_id || task.objective || 'task'}:${status}`;
    if (!store.claimNotification(id)) return;
    try {
      if (Notification.permission === 'granted') {
        new Notification('Codex Hub — tác vụ cần chú ý', { body: `${task.objective || 'Tác vụ'} ${attention}.` });
      }
    } catch { /* notifications unavailable in this context */ }
  }
  // ---------- F06/F09/F12 increment 2: files, git diff, artifacts ----------
  const unwrap = (result) => (result && typeof result === 'object' && 'ok' in result)
    ? (result.ok ? result.data : null) : result;
  const smallButton = (label) => el('button', 'secondary-button wh-small', label);
  const PREVIEWABLE = new Set(['.md', '.txt', '.log', '.json', '.csv', '.html', '.xml', '.yml', '.yaml']);

  async function renderFiles() {
    const box = $('#whFileList');
    if (!box || !window.mcpAssistant?.workhubList) return;
    const data = unwrap(await window.mcpAssistant.workhubList(ui.dirRel).catch(() => null));
    $('#whCrumb').textContent = `/${ui.dirRel || ''}`;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Chưa chọn thư mục làm việc hoặc không đọc được.')); return; }
    ui.dirRel = data.rel || '';
    $('#whCrumb').textContent = `/${ui.dirRel}`;
    box.replaceChildren(...data.entries.map((entry) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', entry.type === 'dir' ? `📁 ${entry.name}` : entry.name),
        el('small', '', entry.type === 'dir' ? 'Thư mục' : `${entry.size ?? 0} bytes`));
      row.append(main);
      const action = smallButton(entry.type === 'dir' ? 'Mở' : 'Xem');
      action.addEventListener('click', () => {
        if (entry.type === 'dir') { ui.dirRel = entry.rel; renderFiles(); }
        else openFile(entry.rel);
      });
      row.append(action);
      if (entry.type === 'file') {
        const add = smallButton('Giỏ');
        add.addEventListener('click', () => {
          try { store.addToBasket(currentProject(), { path: entry.rel, size: entry.size }); renderBasket(); }
          catch (error) { window.alert(error.message); }
        });
        row.append(add);
      }
      return row;
    }));
    if (data.truncated) box.append(el('span', 'task-muted', 'Danh sách đã rút gọn ở 300 mục đầu.'));
  }

  async function openFile(rel) {
    const viewer = $('#whViewer');
    if (!viewer || !window.mcpAssistant?.workhubRead) return;
    ui.viewerRel = rel;
    $('#whViewerTitle').textContent = rel;
    const addBtn = $('#whViewerAddBasket');
    if (addBtn) addBtn.disabled = false;
    const data = unwrap(await window.mcpAssistant.workhubRead(rel).catch(() => null));
    if (!data) { viewer.textContent = 'Không đọc được tệp.'; return; }
    viewer.textContent = data.binary
      ? `Tệp nhị phân (${data.size} bytes) — không xem trước nội dung.`
      : data.content + (data.truncated ? '\n… (đã rút gọn 256KB đầu)' : '');
  }

  async function renderCodeSearch() {
    const box = $('#whCodeResults');
    const query = String($('#whCodeQuery')?.value || '').trim();
    if (!box || !query) return;
    const data = unwrap(await window.mcpAssistant.workhubSearch(query).catch(() => null));
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Tìm kiếm thất bại (từ khóa tối thiểu 2 ký tự).')); return; }
    if (!data.results.length) { box.replaceChildren(el('span', 'task-muted', `Không thấy "${query}" trong ${data.scannedFiles} tệp đã quét.`)); return; }
    box.replaceChildren(...data.results.map((hit) => {
      const row = el('button', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(el('b', '', `${hit.rel}:${hit.line}`), el('small', '', hit.text));
      row.append(main);
      row.addEventListener('click', () => openFile(hit.rel));
      return row;
    }));
  }

  async function renderGit() {
    const box = $('#whGitList');
    if (!box || !window.mcpAssistant?.workhubGitStatus) return;
    const data = unwrap(await window.mcpAssistant.workhubGitStatus().catch(() => null));
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Không lấy được trạng thái Git (dự án chưa phải git repo?).')); return; }
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Không có thay đổi nào trong cây làm việc.')); return; }
    box.replaceChildren(...data.map((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', item.path), el('small', '', `Trạng thái: ${item.status.trim() || 'đã sửa'}`));
      row.append(main);
      const view = smallButton('Xem diff');
      view.addEventListener('click', () => renderDiff(item.path));
      row.append(view);
      return row;
    }));
  }

  async function renderDiff(rel) {
    const box = $('#whDiff');
    if (!box) return;
    const data = unwrap(await window.mcpAssistant.workhubGitDiff(rel).catch(() => null));
    box.textContent = !data ? 'Không lấy được diff.'
      : (data.diff || 'Tệp chưa có diff (tệp mới chưa track sẽ không có diff — xem ở trang Tác vụ).')
        + (data.truncated ? '\n… (diff đã rút gọn)' : '');
  }

  function renderArtifacts() {
    const box = $('#whArtifacts');
    if (!box) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const report = task?.last_build_report || null;
    if (!report) { box.replaceChildren(el('span', 'task-muted', 'Chưa có báo cáo build (verify_build) trong tác vụ hiện tại.')); return; }
    const head = el('div', 'wh-row');
    const headMain = el('div', 'wh-row-main');
    headMain.append(el('b', '', report.overall_status === 'passed' ? 'Xác minh thành công' : 'Xác minh thất bại'),
      el('small', '', `${report.project?.type || ''} · v${report.project?.version || '?'}`));
    head.append(headMain);
    const rows = [head];
    (report.artifacts || []).slice(0, 12).forEach((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      const hash = String(item.sha256 || item.sha384 || item.sha512 || '').slice(0, 16);
      main.append(el('b', '', item.path || 'sản phẩm'), el('small', '', hash ? `sha ${hash}…` : 'Không có hash'));
      row.append(main);
      const ext = String(item.path || '').toLowerCase().match(/\.[a-z0-9]+$/)?.[0] || '';
      if (PREVIEWABLE.has(ext)) {
        const view = smallButton('Xem trước');
        view.addEventListener('click', () => openFile(item.path));
        row.append(view);
      }
      const copy = smallButton('Sao chép đường dẫn');
      copy.addEventListener('click', (e) => copyText(item.path || '', e.currentTarget));
      row.append(copy);
      rows.push(row);
    });
    if (report.failure) rows.push(el('span', 'task-muted', `Lỗi: ${report.failure}`));
    box.replaceChildren(...rows);
  }

  async function loadTask() {
    try {
      const result = await window.mcpAssistant?.taskState?.();
      ui.taskPayload = result?.data || result || null;
    } catch { ui.taskPayload = null; }
    renderTaskSummary();
    renderHandoff();
    renderArtifacts();
    maybeNotify(ui.taskPayload?.state || ui.taskPayload?.data?.state || null);
  }

  // ---------- F31 unified search ----------
  function searchEntries() {
    const entries = [
      { kind: 'Trang', title: 'Thực thi mã', detail: 'command center tổng quan', run: () => window.navigate?.('overview') },
      { kind: 'Trang', title: 'Tác vụ & kết quả', detail: 'task diff tệp đã sửa báo cáo', run: () => window.navigate?.('task') },
      { kind: 'Trang', title: 'Cài đặt', detail: 'thư mục quyền chế độ thực thi', run: () => window.navigate?.('system') },
      { kind: 'Trang', title: 'Sử dụng', detail: 'token chi phí usage', run: () => window.navigate?.('usage') },
      { kind: 'Trang', title: 'Xác minh & Build', detail: 'chạy test build sản phẩm', run: () => window.navigate?.('build') },
    ];
    for (const p of store.listPrompts()) {
      entries.push({ kind: 'Lời nhắc', title: p.name, detail: 'mẫu yêu cầu thư viện lời nhắc', run: () => { ui.selectedPromptId = p.id; renderPromptOptions(); window.navigate?.('workhub'); } });
    }
    for (const r of store.listRecipes()) {
      entries.push({ kind: 'Lệnh đã lưu', title: r.name, detail: r.command, run: () => copyText(r.command) });
    }
    for (const project of recentProjects()) {
      entries.push({ kind: 'Dự án', title: store.projectLabel(project), detail: project, run: () => window.navigate?.('workspace') });
    }
    return entries;
  }
  function renderSearchResults() {
    const box = $('#whSearchResults');
    const input = $('#whSearchInput');
    if (!box || !input) return;
    box.replaceChildren();
    const results = S.searchAll(searchEntries(), input.value, 10);
    if (!results.length) { box.appendChild(el('span', 'task-muted', 'Không có kết quả.')); return; }
    for (const entry of results) {
      const row = el('button', 'wh-search-row');
      row.appendChild(el('span', 'soft-badge neutral', entry.kind));
      const main = el('span', 'wh-row-main');
      main.appendChild(el('b', '', entry.title));
      main.appendChild(el('small', '', entry.detail || ''));
      row.appendChild(main);
      row.addEventListener('click', () => { closeSearch(); entry.run?.(); });
      box.appendChild(row);
    }
  }
  function openSearch() {
    const overlay = $('#whSearchOverlay');
    if (!overlay) return;
    overlay.hidden = false;
    renderSearchResults();
    setTimeout(() => $('#whSearchInput')?.focus(), 0);
  }
  function closeSearch() {
    const overlay = $('#whSearchOverlay');
    if (overlay) overlay.hidden = true;
  }

  // ---------- wiring ----------
  function bind() {
    $('#whPromptSelect')?.addEventListener('change', (e) => { ui.selectedPromptId = e.target.value; renderPromptOptions(); });
    $('#whPromptSave')?.addEventListener('click', () => {
      try {
        const saved = store.upsertPrompt({ id: ui.selectedPromptId, name: $('#whPromptName').value, body: $('#whPromptBody').value });
        ui.selectedPromptId = saved.id; renderPromptOptions();
      } catch (error) { window.alert(error.message); }
    });
    $('#whPromptNew')?.addEventListener('click', () => {
      try {
        const saved = store.upsertPrompt({ name: 'Mẫu mới', body: 'Yêu cầu: {{request}}\nDự án: {{project}}\nTệp:\n{{files}}' });
        ui.selectedPromptId = saved.id; renderPromptOptions();
      } catch (error) { window.alert(error.message); }
    });
    $('#whPromptDelete')?.addEventListener('click', () => { store.removePrompt(ui.selectedPromptId); ui.selectedPromptId = ''; renderPromptOptions(); });
    $('#whTaskType')?.addEventListener('change', (e) => { ui.selectedType = e.target.value; renderTypeFields(); });
    $('#whBuildBtn')?.addEventListener('click', buildFromType);
    $('#whUsePromptBtn')?.addEventListener('click', buildFromPrompt);
    $('#whCopyBtn')?.addEventListener('click', (e) => copyText($('#whPreview').value, e.currentTarget));
    $('#whAddFile')?.addEventListener('click', () => {
      const path = $('#whFilePath').value.trim();
      if (!path) return;
      try {
        store.addToBasket(currentProject(), { path, size: $('#whFileSize').value === '' ? null : Number($('#whFileSize').value) });
        $('#whFilePath').value = ''; $('#whFileSize').value = '';
        renderBasket();
      } catch (error) { window.alert(error.message); }
    });
    $('#whClearBasket')?.addEventListener('click', () => { store.clearBasket(currentProject()); renderBasket(); });
    $('#whImportTaskFiles')?.addEventListener('click', async () => {
      await loadTask();
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const preview = S.handoffPreview(task);
      for (const path of preview?.files || []) {
        try { store.addToBasket(currentProject(), { path }); } catch { /* basket full */ }
      }
      renderBasket();
    });
    $('#whAddRecipe')?.addEventListener('click', () => {
      try {
        store.upsertRecipe({ name: $('#whRecipeName').value, command: $('#whRecipeCommand').value, cwd: $('#whRecipeCwd').value || currentProject() });
        $('#whRecipeName').value = ''; $('#whRecipeCommand').value = ''; $('#whRecipeCwd').value = '';
        renderRecipes();
      } catch (error) { window.alert(error.message); }
    });
    $('#whLoadHandoff')?.addEventListener('click', loadTask);
    $('#whCopyHandoff')?.addEventListener('click', (e) => copyText($('#whHandoffView').textContent, e.currentTarget));
    const toggle = $('#whNotifyToggle');
    if (toggle) {
      toggle.checked = store.notificationsEnabled();
      toggle.addEventListener('change', () => {
        store.setNotificationsEnabled(toggle.checked);
        if (toggle.checked && typeof Notification !== 'undefined' && Notification.permission === 'default') Notification.requestPermission().catch(() => {});
      });
    }
    $('#whNotifyTest')?.addEventListener('click', async () => {
      if (typeof Notification === 'undefined') { window.alert('Môi trường này không hỗ trợ Notification.'); return; }
      if (Notification.permission === 'default') await Notification.requestPermission().catch(() => {});
      if (Notification.permission === 'granted') new Notification('Codex Hub', { body: 'Thông báo thử: kênh thông báo đang hoạt động.' });
      else window.alert('Quyền thông báo chưa được cấp.');
    });
    $('#whDirUp')?.addEventListener('click', () => {
      ui.dirRel = ui.dirRel.split('/').slice(0, -1).join('/');
      renderFiles();
    });
    $('#whDirReload')?.addEventListener('click', renderFiles);
    $('#whCodeSearch')?.addEventListener('click', renderCodeSearch);
    $('#whCodeQuery')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') renderCodeSearch(); });
    $('#whGitRefresh')?.addEventListener('click', renderGit);
    $('#whViewerAddBasket')?.addEventListener('click', () => {
      if (!ui.viewerRel) return;
      try { store.addToBasket(currentProject(), { path: ui.viewerRel }); renderBasket(); }
      catch (error) { window.alert(error.message); }
    });
    $('#whSearchInput')?.addEventListener('input', renderSearchResults);
    $('#whSearchClose')?.addEventListener('click', closeSearch);
    $('#whSearchOverlay')?.addEventListener('click', (e) => { if (e.target.id === 'whSearchOverlay') closeSearch(); });
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && String(e.key).toLowerCase() === 'k') { e.preventDefault(); openSearch(); }
      if (e.key === 'Escape') closeSearch();
    });
  }

  async function refresh() {
    try {
      const result = await window.mcpAssistant?.snapshot?.();
      ui.snapshot = result?.data || result || null;
    } catch { /* keep last snapshot */ }
    renderProjects();
    renderPromptOptions();
    renderBasket();
    renderRecipes();
    await loadTask();
    renderFiles();
    renderGit();
  }

  window.WorkHubUI = { refresh, store };
  document.addEventListener('DOMContentLoaded', () => {
    bind();
    renderTypeFields();
    renderPromptOptions();
    renderProjects();
    renderBasket();
    renderRecipes();
  });
})();
