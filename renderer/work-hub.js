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

  let persistenceError = '';
  const adapter = {
    load() {
      try { const raw = localStorage.getItem('coding-tools-work-hub-v1'); return raw ? JSON.parse(raw) : null; }
      catch { return null; }
    },
    save(data) {
      try { localStorage.setItem('coding-tools-work-hub-v1', JSON.stringify(data)); persistenceError = ''; }
      catch { persistenceError = 'Không lưu được trên máy. Hãy sao chép yêu cầu trước khi đóng ứng dụng.'; setStatus(persistenceError, 'error'); }
    },
  };
  const store = S.createStore(adapter);
  const ui = { snapshot: null, taskPayload: null, selectedPromptId: '', selectedType: 'bugfix', dirRel: '', viewerRel: '', viewerHash: '', viewerContent: null, viewerEditable: false, gen: 0, job: null, pendingImports: [], boundProject: null, refreshRequest: 0, requests: {}, activeTab: 'context', commitSelection: new Set(), commitBusy: false, gitHead: '', diffHead: '', diffFingerprint: '', gitReview: null, gitReviewHead: '' };

  function setStatus(message, kind = 'info') {
    const box = $('#whStatus');
    if (!box) return;
    box.textContent = message;
    box.dataset.kind = kind;
    box.hidden = !message;
  }

  function activateTab(name, { focus = false } = {}) {
    const tabs = Array.from(document.querySelectorAll('[data-wh-tab]'));
    if (!tabs.some((tab) => tab.dataset.whTab === name)) return;
    ui.activeTab = name;
    for (const tab of tabs) {
      const selected = tab.dataset.whTab === name;
      tab.setAttribute('aria-selected', String(selected));
      tab.setAttribute('tabindex', selected ? '0' : '-1');
      if (selected && focus) tab.focus();
    }
    for (const panel of document.querySelectorAll('[data-wh-panel]')) panel.hidden = panel.dataset.whPanel !== name;
  }

  function requestScope(name) {
    const id = (ui.requests[name] || 0) + 1;
    ui.requests[name] = id;
    const gen = ui.gen;
    const workspace = currentProject();
    return { workspace, current: () => gen === ui.gen && workspace === currentProject() && id === ui.requests[name] };
  }

  function saveCurrentDraft(workspace = currentProject()) {
    if (!workspace) { renderDraftState(); return; }
    try { store.saveDraft(workspace, { text: $('#whPreview')?.value || '', type: ui.selectedType, fields: fieldValues(), promptId: ui.selectedPromptId }); }
    catch (error) { persistenceError = error.message || 'Không lưu được nháp.'; setStatus(persistenceError, 'error'); }
    renderDraftState();
  }

  const fileDrafts = new Map();
  function fileDraftKey(workspace, rel) { return `${S.workspaceKeyOf(workspace)}\n${rel}`; }
  function rememberFileEdit(workspace = currentProject()) {
    const editor = $('#whEditor');
    if (!editor || editor.hidden || !ui.viewerRel || editor.value === ui.viewerContent) return;
    fileDrafts.set(fileDraftKey(workspace, ui.viewerRel), { content: editor.value, hash: ui.viewerHash });
  }
  function canLeaveFileEdit() {
    if (ui.savingFile) { setStatus('Đang lưu tệp. Chờ xác nhận trước khi đổi tệp hoặc dự án.'); return false; }
    const editor = $('#whEditor');
    if (editor && !editor.hidden && editor.value !== ui.viewerContent) {
      if (document.body.dataset.page !== 'workhub') window.navigate?.('workhub');
      setStatus('Tệp có thay đổi chưa lưu. Chọn Lưu tệp hoặc Hủy sửa trước khi mở tệp hay chuyển dự án.', 'error');
      editor.focus();
      return false;
    }
    return true;
  }

  function resetProjectView() {
    ui.gen += 1;
    ui.dirRel = '';
    ui.viewerRel = '';
    ui.viewerHash = '';
    ui.viewerContent = null;
    ui.viewerEditable = false;
    ui.diffRel = '';
    ui.diffText = '';
    ui.diffHead = '';
    ui.diffFingerprint = '';
    ui.diffStale = false;
    ui.gitReview = null;
    ui.gitReviewHead = '';
    ui.taskPayload = null;
    ui.pendingImports = [];
    ui.importResults = [];
    for (const id of ['whCodeResults', 'whGitList', 'whGitLog', 'whTaskFiles', 'whArtifactImage', 'whCapsuleView', 'whImportList', 'whPatchApproval', 'whCosSessions', 'whCodexChatLog', 'whCodexChatEvents', 'whCodexChatThreads', 'whGitReview']) $(`#${id}`)?.replaceChildren();
    for (const id of ['whCodeQuery', 'whEditor', 'whPreview', 'whFilePath', 'whFileSize', 'whImportDest', 'whSnippetName', 'whSnippetBody', 'whFeedbackText', 'whQueueTitle', 'whNoteTitle', 'whNoteBody', 'whChatLabel', 'whChatUrl', 'whCodexChatInput', 'whGitReviewFrom', 'whGitReviewTo']) { const input = $(`#${id}`); if (input) input.value = ''; }
    if ($('#whGitReviewMeta')) $('#whGitReviewMeta').textContent = '';
    stopCodexChatPolling();
    if ($('#whCodexChatState')) $('#whCodexChatState').textContent = 'Chưa kiểm tra Codex App Server.';
    if ($('#whCodexChatLink')) $('#whCodexChatLink').textContent = 'Chưa liên kết RUN.';
    if ($('#whCodexChatHandoffInfo')) $('#whCodexChatHandoffInfo').textContent = 'Chưa chuyển phiên chat này thành việc điều hành.';
    for (const id of ['whViewerAddBasket', 'whEditFile', 'whSaveFile', 'whBlame']) { const button = $(`#${id}`); if (button) button.disabled = true; }
    if ($('#whEditor')) $('#whEditor').hidden = true;
    if ($('#whCancelEditFile')) $('#whCancelEditFile').hidden = true;
    if ($('#whViewer')) { $('#whViewer').hidden = false; $('#whViewer').textContent = 'Chọn một tệp để xem nội dung.'; }
    if ($('#whViewerTitle')) $('#whViewerTitle').textContent = 'Chưa chọn tệp';
    if ($('#whDiff')) $('#whDiff').textContent = 'Chọn một tệp để xem thay đổi.';
    if ($('#whDiffMeta')) $('#whDiffMeta').textContent = '';
    if ($('#whCosEvents')) $('#whCosEvents').textContent = 'Chọn một phiên CoS để xem sự kiện (chỉ đọc).';
    setStatus('');
  }

  function renderWorkspace() {
    const project = currentProject();
    if ($('#whWorkspaceName')) $('#whWorkspaceName').textContent = project ? store.projectLabel(project) : 'Chưa chọn dự án';
    if ($('#whWorkspacePath')) $('#whWorkspacePath').textContent = project || 'Chọn thư mục để bắt đầu.';
  }

  async function switchProject(project) {
    if (S.workspaceKeyOf(project) === S.workspaceKeyOf(currentProject())) return true;
    if (ui.switchingProject) return false;
    if (!canLeaveFileEdit()) return false;
    saveCurrentDraft();
    const main = document.querySelector('.main-area');
    ui.switchingProject = true;
    if (main) main.inert = true;
    try {
      const source = window.mcpAssistant || (typeof api === 'undefined' ? null : api);
      if (!source?.switchWorkspace) throw new Error('Chuyển dự án cần ứng dụng Desktop.');
      const result = await source.switchWorkspace(project);
      if (result?.ok === false) throw new Error(result.error?.message || result.error || 'Không chuyển được dự án.');
      if (typeof refreshSnapshot === 'function') await refreshSnapshot();
      window.navigate?.('workhub');
      await refresh();
      const menu = document.querySelector('.wh-project-menu');
      if (menu) menu.open = false;
      return true;
    } catch (error) { if (document.body.dataset.page !== 'workhub') window.navigate?.('workhub'); setStatus(error.message || 'Không chuyển được dự án. Cấu hình cũ vẫn đang được dùng.', 'error'); return false; }
    finally { ui.switchingProject = false; if (main) main.inert = false; }
  }

  function currentProject() {
    const settings = ui.snapshot?.settings || {};
    return String(settings.workspace || '').trim();
  }
  // P2: one canonical workspace key. Main publishes the canonical
  // spelling in snapshot.settings.canonicalWorkspace (it realpaths; the
  // renderer cannot). currentProject() keeps the raw spelling because
  // IPC scope arguments must stay lexical (scopedWorkHubRoot is a
  // fail-closed lexical fence). Only store keys use the canonical key.
  function canonicalProjectKey() {
    const settings = ui.snapshot?.settings || {};
    const canonical = String(settings.canonicalWorkspace || '').trim();
    return S.workspaceKeyOf(canonical || currentProject());
  }
  function syncCanonicalWorkspaceKey() {
    // Map the current raw spelling to the snapshot's canonical key so
    // store getters/writers unify aliases (8.3, junction, subst) under
    // one bucket, and migrate any legacy bucket that exists.
    const raw = currentProject();
    const settings = ui.snapshot?.settings || {};
    const canonical = String(settings.canonicalWorkspace || '').trim();
    if (typeof store.setCanonicalKeyResolver === 'function') {
      store.setCanonicalKeyResolver((workspace) => {
        if (raw && S.workspaceKeyOf(workspace) === S.workspaceKeyOf(raw) && canonical) return canonical;
        return null;
      });
    }
    if (raw && canonical) {
      const fromKey = S.workspaceKeyOf(raw);
      const toKey = canonicalProjectKey();
      if (fromKey && toKey && fromKey !== toKey && typeof store.migrateWorkspaceKey === 'function') {
        store.migrateWorkspaceKey(fromKey, toKey);
      }
    }
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
      const isCurrent = S.workspaceKeyOf(project) === S.workspaceKeyOf(current);
      if (isCurrent) row.appendChild(el('span', 'soft-badge', 'Đang dùng'));
      else {
        const useBtn = el('button', 'secondary-button wh-small', 'Chuyển đến');
        useBtn.addEventListener('click', () => switchProject(project));
        row.appendChild(useBtn);
      }
      const pinBtn = el('button', 'secondary-button wh-small', pin.pinned ? 'Bỏ ghim' : 'Ghim');
      pinBtn.addEventListener('click', () => { store.setPin(project, { pinned: !pin.pinned }); renderProjects(); });
      const aliasBtn = el('button', 'secondary-button wh-small', 'Đặt tên');
      aliasBtn.addEventListener('click', () => {
        const alias = window.prompt('Tên dễ nhớ cho dự án:', pin.alias || store.projectLabel(project));
        if (alias !== null) { store.setPin(project, { alias }); renderProjects(); renderWorkspace(); }
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
  function renderTypeFields(values = {}) {
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
      input.value = values[field.key] || '';
      input.required = Boolean(field.required);
      input.maxLength = 4000;
      input.addEventListener('input', () => saveCurrentDraft());
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
  function showRequestDraft() {
    activateTab('context');
    const preparation = $('#whTypeFields')?.closest('details');
    if (preparation) preparation.open = false;
    $('#whPreview')?.focus();
    $('#whPreview')?.scrollIntoView({ block: 'nearest' });
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
      saveCurrentDraft();
      showRequestDraft();
      setStatus('Yêu cầu đã sẵn sàng. Bạn có thể chỉnh sửa rồi sao chép.');
    } catch (error) { setStatus(`Chưa đủ thông tin: ${error.message}`, 'error'); }
  }
  function buildFromPrompt() {
    const prompt = store.listPrompts().find((p) => p.id === ui.selectedPromptId);
    if (!prompt) return;
    $('#whPreview').value = S.fillTemplate(prompt.body, {
      project: currentProject(),
      request: firstFieldValue(),
      files: store.contextPackageText(currentProject()) || '(chưa chọn tệp)',
    });
    saveCurrentDraft();
    showRequestDraft();
    setStatus('Đã tạo yêu cầu từ mẫu đã chọn.');
  }

  // ---------- F05 basket ----------
  function renderBasket() {
    const label = $('#whBasketProject');
    if (label) label.textContent = currentProject() || 'Chưa chọn dự án';
    const box = $('#whBasketList');
    if (!box) return;
    box.replaceChildren();
    const files = store.basketFor(currentProject());
    if ($('#whBasketCount')) $('#whBasketCount').textContent = String(files.length);
    const selected = new Set(files.map((file) => String(file.path).replace(/\\/g, '/')));
    for (const input of document.querySelectorAll('[data-wh-file]')) input.checked = selected.has(input.dataset.whFile);
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
    const recipes = store.listRecipes(currentProject());
    if (!recipes.length) { box.appendChild(el('span', 'task-muted', 'Chưa có lệnh nào được lưu.')); return; }
    const scoped = recipes;
    const others = [];
    const renderOne = (recipe, inProject) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.appendChild(el('b', '', recipe.name + (inProject ? '' : ' · dự án khác')));
      main.appendChild(el('small', '', recipe.command + (recipe.cwd ? `  ·  ${recipe.cwd}` : '')));
      row.appendChild(main);
      const run = el('button', 'secondary-button wh-small', 'Chạy lệnh');
      run.addEventListener('click', () => { activateTab('verify'); return runRecipeAsJob(recipe); });
      const copy = el('button', 'secondary-button wh-small', 'Sao chép lệnh');
      copy.addEventListener('click', () => copyText(recipe.command, copy));
      row.append(run, copy);
      if (recipe.url) {
        const open = el('button', 'secondary-button wh-small', 'Mở URL');
        open.addEventListener('click', () => window.mcpAssistant?.openExternal?.(recipe.url));
        const check = el('button', 'secondary-button wh-small', 'Kiểm tra URL');
        check.addEventListener('click', async () => {
          const result = unwrap(await window.mcpAssistant.workhubCheckUrl(recipe.url).catch(() => null));
          window.alert(result ? `${recipe.url}\nHTTP ${result.status} · ${result.ms} ms${result.title ? ` · ${result.title}` : ''}` : 'Không truy cập được URL (server chưa chạy?).');
        });
        row.append(open, check);
      }
      const remove = el('button', 'secondary-button wh-small', 'Xóa');
      remove.addEventListener('click', () => { store.removeRecipe(recipe.id); renderRecipes(); });
      row.append(remove);
      box.appendChild(row);
    };
    if (!scoped.length && !others.length) { box.appendChild(el('span', 'task-muted', 'Chưa có lệnh nào được lưu.')); return; }
    scoped.forEach((r) => renderOne(r, true));
    others.forEach((r) => renderOne(r, false));
  }

  // ---------- F09/F12 task summary + F29 handoff + F22 notify ----------
  function renderTaskSummary() {
    const box = $('#whTaskSummary');
    if (!box) return;
    box.replaceChildren();
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if ($('#whCurrentTaskTitle')) $('#whCurrentTaskTitle').textContent = task?.objective || 'Chưa có công việc hiện tại';
    const statusLabels = { running: 'Đang chạy', in_progress: 'Đang thực hiện', completed: 'Hoàn tất', done: 'Hoàn tất', failed: 'Có lỗi', paused: 'Tạm dừng', waiting_approval: 'Chờ bạn duyệt', blocked: 'Đang bị chặn' };
    if ($('#whCurrentTaskState')) $('#whCurrentTaskState').textContent = task ? (statusLabels[task.status] || task.status || 'Chưa rõ trạng thái') : 'Bắt đầu bằng một yêu cầu bên dưới.';
    if ($('#whCurrentTask')) $('#whCurrentTask').dataset.state = task?.status || '';
    if (!task) { box.appendChild(el('span', 'task-muted', 'Chưa có trạng thái tác vụ. Mở trang Tác vụ & kết quả để xem chi tiết.')); return; }
    if (task.details_available === false) { box.appendChild(el('span', 'task-muted', 'Chưa lấy được chi tiết của công việc này. Hãy làm mới khi runtime kết nối lại.')); return; }
    const preview = S.handoffPreview(task);
    const files = preview?.files || [];
    box.appendChild(el('p', '', `Tệp đã sửa đổi (${files.length}): ${files.length ? files.join(', ') : 'chưa ghi nhận'}`));
    const tests = S.taskTests(task);
    const passed = tests.filter((t) => ['passed', 'pass', 'success', 'completed'].includes(String(t.status).toLowerCase())).length;
    box.appendChild(el('p', '', `Kiểm chứng gần đây: ${tests.length ? `${passed}/${tests.length} lần kiểm tra đạt` : 'chưa có kết quả'}. Xem sản phẩm đầu ra tại tab Kết quả.`));
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
    // Bind the event to the exact task/run. Only record "notified" once a
    // notification is actually shown: if permission is missing, a later
    // state change can still notify instead of being silently swallowed.
    const runId = task.orchestration?.run_id || task.run_id || '';
    const id = `${task.task_id || task.id || 'task'}:${runId}:${status}`;
    if (store.hasNotified(id)) return;
    if (Notification.permission !== 'granted') return;
    try {
      const notice = new Notification('Codex Hub — tác vụ cần chú ý', { body: `${task.objective || 'Tác vụ'} ${attention}.` });
      store.claimNotification(id);
      notice.onclick = () => { window.focus?.(); window.navigate?.('workhub'); refresh(); };
    } catch { /* notifications unavailable in this context */ }
  }

  let attentionTimer = null;
  function startAttentionPolling() {
    if (attentionTimer) return;
    // Background attention check while the app runs (any page): the poll is
    // read-only and cheap, and notifications are deduped per task/run/status.
    attentionTimer = setInterval(async () => {
      try {
        const result = await window.mcpAssistant?.taskState?.();
        const payload = result?.data || result || null;
        const task = payload?.state || payload?.data?.state || null;
        maybeNotify(task);
      } catch { /* runtime not ready */ }
    }, 30000);
  }
  // ---------- F06/F09/F12 increment 2: files, git diff, artifacts ----------
  const unwrap = (result) => (result && typeof result === 'object' && 'ok' in result)
    ? (result.ok ? result.data : null) : result;
  const smallButton = (label) => el('button', 'secondary-button wh-small', label);
  const PREVIEWABLE = new Set(['.md', '.txt', '.log', '.json', '.csv', '.html', '.xml', '.yml', '.yaml']);

  async function renderFiles() {
    const box = $('#whFileList');
    if (!box) return;
    if (!window.mcpAssistant?.workhubList) { box.textContent = 'Mở ứng dụng Desktop và chọn dự án để duyệt tệp.'; return; }
    const scope = requestScope('files');
    box.setAttribute('aria-busy', 'true');
    const data = unwrap(await window.mcpAssistant.workhubList(ui.dirRel, scope.workspace).catch(() => null));
    if (!scope.current()) return;
    box.setAttribute('aria-busy', 'false');
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
        const label = el('label', 'wh-file-check');
        const add = document.createElement('input');
        add.type = 'checkbox';
        add.dataset.whFile = entry.rel;
        add.setAttribute('data-wh-file', entry.rel);
        add.setAttribute('aria-label', `Chọn tệp ${entry.rel} làm ngữ cảnh`);
        add.checked = store.basketFor(scope.workspace).some((file) => String(file.path).replace(/\\/g, '/') === entry.rel);
        add.addEventListener('change', () => {
          if (!scope.current()) return;
          try {
            if (add.checked) store.addToBasket(scope.workspace, { path: entry.rel, size: entry.size });
            else store.removeFromBasket(scope.workspace, entry.rel);
            renderBasket();
          }
          catch (error) { window.alert(error.message); }
        });
        label.append(add, el('span', '', 'Chọn'));
        row.append(label);
      }
      return row;
    }));
    if (data.truncated) box.append(el('span', 'task-muted', 'Danh sách đã rút gọn ở 300 mục đầu.'));
  }

  async function openFile(rel, line) {
    const viewer = $('#whViewer');
    if (!viewer || !window.mcpAssistant?.workhubRead) return;
    if (!canLeaveFileEdit()) return;
    const scope = requestScope('viewer');
    ui.viewerRel = rel;
    ui.viewerHash = '';
    ui.viewerContent = null;
    ui.viewerEditable = false;
    viewer.hidden = false;
    viewer.textContent = 'Đang đọc tệp…';
    viewer.setAttribute('aria-busy', 'true');
    if ($('#whEditor')) $('#whEditor').hidden = true;
    if ($('#whCancelEditFile')) $('#whCancelEditFile').hidden = true;
    if ($('#whSaveFile')) $('#whSaveFile').disabled = true;
    $('#whViewerTitle').textContent = rel;
    const addBtn = $('#whViewerAddBasket');
    if (addBtn) addBtn.disabled = true;
    const editBtn = $('#whEditFile');
    if (editBtn) editBtn.disabled = true;
    if ($('#whBlame')) $('#whBlame').disabled = true;
    const data = unwrap(await window.mcpAssistant.workhubRead(rel, scope.workspace).catch(() => null));
    if (!scope.current()) return;
    viewer.setAttribute('aria-busy', 'false');
    if (!data) { viewer.textContent = 'Không đọc được tệp.'; return; }
    ui.viewerHash = data.hash || '';
    if (addBtn) addBtn.disabled = false;
    if (data.binary) { viewer.textContent = `Tệp nhị phân (${data.size} bytes) — không xem trước nội dung.`; return; }
    ui.viewerContent = String(data.content || '');
    ui.viewerEditable = Boolean(data.hash) && !data.truncated;
    if (editBtn) editBtn.disabled = !ui.viewerEditable;
    if ($('#whBlame')) $('#whBlame').disabled = false;
    const suffix = data.truncated ? '\n… (đã rút gọn 256KB đầu)' : '';
    if (line && line > 0) {
      // Render per-line so the requested line is highlighted and scrolled to.
      const lines = String(data.content).split('\n');
      viewer.replaceChildren(...lines.map((text, index) => {
        const row = el('span', index + 1 === line ? 'wh-line wh-line-hit' : 'wh-line', `${index + 1}  ${text}\n`);
        return row;
      }));
      if (suffix) viewer.append(document.createTextNode(suffix));
      viewer.querySelector('.wh-line-hit')?.scrollIntoView({ block: 'center' });
    } else {
      viewer.textContent = data.content + suffix;
    }
    const draft = fileDrafts.get(fileDraftKey(scope.workspace, rel));
    if (draft && ui.viewerEditable) {
      ui.viewerHash = draft.hash;
      $('#whEditor').value = draft.content;
      $('#whEditor').hidden = false;
      viewer.hidden = true;
      $('#whSaveFile').disabled = false;
      if ($('#whCancelEditFile')) $('#whCancelEditFile').hidden = false;
      setStatus('Đã khôi phục phần sửa tệp chưa lưu. Nếu tệp đã đổi trên đĩa, thao tác lưu sẽ yêu cầu đối chiếu lại.');
    }
  }

  async function renderCodeSearch() {
    const box = $('#whCodeResults');
    const query = String($('#whCodeQuery')?.value || '').trim();
    if (!box || !query) return;
    const scope = requestScope('search');
    box.textContent = 'Đang tìm trong dự án…';
    const data = unwrap(await window.mcpAssistant.workhubSearch(query, scope.workspace).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Tìm kiếm thất bại (từ khóa tối thiểu 2 ký tự).')); return; }
    if (!data.results.length) { box.replaceChildren(el('span', 'task-muted', `Không thấy "${query}" trong ${data.scannedFiles} tệp đã quét.`)); return; }
    const rows = data.results.map((hit) => {
      const row = el('button', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(el('b', '', `${hit.rel}:${hit.line}`), el('small', '', hit.text));
      row.append(main);
      row.addEventListener('click', () => openFile(hit.rel, hit.line));
      return row;
    });
    if (data.budgetExhausted) rows.push(el('span', 'task-muted', 'Đã hết ngân sách quét (giới hạn số tệp) — kết quả có thể chưa đầy đủ.'));
    if (data.truncated) rows.push(el('span', 'task-muted', 'Đã đạt giới hạn số kết quả hiển thị.'));
    box.replaceChildren(...rows);
  }

  async function renderGit() {
    const box = $('#whGitList');
    if (!box || !window.mcpAssistant?.workhubGitStatus) return;
    const scope = requestScope('git');
    const data = unwrap(await window.mcpAssistant.workhubGitStatus(scope.workspace).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Không lấy được trạng thái Git (dự án chưa phải git repo?).')); return; }
    // Remember the HEAD this change list was reviewed against; the commit
    // sends it as expectedHead so a concurrent commit aborts instead of
    // silently stacking on an unseen tree.
    if (window.mcpAssistant.workhubGitHead) {
      const head = unwrap(await window.mcpAssistant.workhubGitHead(scope.workspace).catch(() => ''));
      if (scope.current() && typeof head === 'string') ui.gitHead = head;
    }
    // A refreshed HEAD may prove the currently displayed diff stale.
    if (scope.current() && ui.diffRel) renderDiffMeta();
    if (scope.current() && ui.diffRel) renderPatchApproval();
    // Same re-check for a range review already on screen (W5): its STALE
    // label is recomputed against the freshly observed HEAD.
    if (scope.current() && ui.gitReview) renderGitReviewMeta();
    if (!data.length) { ui.commitSelection.clear(); renderCommitBar(); box.replaceChildren(el('span', 'task-muted', 'Không có thay đổi nào trong cây làm việc.')); return; }
    const present = new Set(data.map((item) => item.path));
    for (const path of [...ui.commitSelection]) if (!present.has(path)) ui.commitSelection.delete(path);
    box.replaceChildren(...data.map((item) => {
      const row = el('div', 'wh-row');
      const check = document.createElement('input');
      check.type = 'checkbox';
      check.className = 'wh-commit-check';
      check.dataset.path = item.path;
      check.checked = ui.commitSelection.has(item.path);
      check.setAttribute('aria-label', `Chọn commit: ${item.path}`);
      check.addEventListener('change', () => {
        if (check.checked) ui.commitSelection.add(item.path); else ui.commitSelection.delete(item.path);
        renderCommitBar();
      });
      row.append(check);
      const main = el('div', 'wh-row-main');
      const label = item.origPath ? `${item.origPath} → ${item.path}` : item.path;
      const untracked = item.status === '??';
      main.append(el('b', '', label), el('small', '', untracked ? 'Tệp mới (chưa track)' : `Trạng thái: ${item.status.trim() || 'đã sửa'}`));
      row.append(main);
      const view = smallButton(untracked ? 'Xem nội dung' : 'Xem diff');
      view.addEventListener('click', () => { if (untracked) openFile(item.path); else renderDiff(item.path); });
      row.append(view);
      return row;
    }));
    renderCommitBar();
    renderTaskFileChanges();
  }

  function renderCommitBar() {
    const all = $('#whCommitAll');
    const button = $('#whCommitSelected');
    const boxes = [...document.querySelectorAll('.wh-commit-check')];
    if (all) {
      all.checked = boxes.length > 0 && boxes.every((box) => box.checked);
      all.indeterminate = boxes.some((box) => box.checked) && !all.checked;
    }
    if (button) {
      button.disabled = ui.commitBusy || ui.commitSelection.size === 0;
      button.textContent = ui.commitSelection.size
        ? `Commit ${ui.commitSelection.size} tệp đã chọn`
        : 'Commit tệp đã chọn';
    }
  }

  async function commitSelectedFiles() {
    if (ui.commitBusy) return;
    const message = $('#whCommitMessage')?.value.trim() || '';
    const result = $('#whCommitResult');
    if (!message) { if (result) result.textContent = 'Nhập nội dung commit trước.'; return; }
    if (!ui.commitSelection.size) { if (result) result.textContent = 'Chưa chọn tệp nào.'; return; }
    // The expected_head guard is only meaningful with the HEAD this list was
    // rendered against. If it could not be loaded, refuse loudly instead of
    // silently committing through the legacy unguarded path.
    if (!ui.gitHead) { if (result) result.textContent = 'Chưa lấy được HEAD hiện tại — hãy tải lại danh sách thay đổi trước khi commit.'; return; }
    const scope = requestScope('gitcommit');
    ui.commitBusy = true;
    renderCommitBar();
    try {
      const data = unwrap(await window.mcpAssistant.workhubGitCommit({
        files: [...ui.commitSelection], message, expectedWorkspace: scope.workspace,
        expectedHead: ui.gitHead || undefined,
      }));
      if (!scope.current()) return;
      ui.commitSelection.clear();
      const input = $('#whCommitMessage');
      if (input) input.value = '';
      if (result) result.textContent = data?.hash
        ? `Đã commit ${data.files} tệp: ${String(data.hash).slice(0, 10)}${data.deliverySnapshot ? ` + snapshot dữ liệu ${String(data.deliverySnapshot).slice(0, 10)}` : ''}`
        : 'Đã commit.';
      await Promise.allSettled([renderGit(), renderGitLog()]);
    } catch (error) {
      if (result) result.textContent = `Commit thất bại: ${error.message}`;
    } finally {
      ui.commitBusy = false;
      renderCommitBar();
    }
  }

  async function renderGitLog() {
    const box = $('#whGitLog');
    if (!box || !window.mcpAssistant?.workhubGitLog) return;
    const scope = requestScope('gitlog');
    const data = unwrap(await window.mcpAssistant.workhubGitLog(15, scope.workspace).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Không lấy được lịch sử Git.')); return; }
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có commit nào.')); return; }
    box.replaceChildren(...data.map((commit) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', `${commit.short} · ${commit.subject}`), el('small', '', `${commit.author} · ${commit.date}`));
      row.append(main);
      const view = smallButton('Xem');
      view.addEventListener('click', async () => {
        const diffBox = $('#whDiff');
        const request = requestScope('diff');
        const shown = unwrap(await window.mcpAssistant.workhubGitShow(commit.hash, request.workspace).catch(() => null));
        if (!request.current()) return;
        ui.diffRel = '';
        ui.diffText = '';
        ui.diffHead = '';
        ui.diffFingerprint = '';
        renderPatchApproval();
        if (diffBox) diffBox.textContent = shown ? shown.text + (shown.truncated ? '\n… (đã rút gọn)' : '') : 'Không đọc được commit.';
        renderDiffMeta(shown ? `Đang xem commit ${commit.hash.slice(0, 10)} — không phải diff cây làm việc` : '');
      });
      row.append(view);
      return row;
    }));
  }

  async function renderWorktrees() {
    const box = $('#whWorktreeList');
    if (!box || !window.mcpAssistant?.workhubWorktreeList) return;
    const scope = requestScope('worktrees');
    const data = unwrap(await window.mcpAssistant.workhubWorktreeList(scope.workspace).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Không lấy được danh sách worktree.')); return; }
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có worktree nào.')); return; }
    box.replaceChildren(...data.map((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(
        el('b', '', item.path),
        el('small', '', `${item.branch || '(detached)'}${item.managed ? ' · được quản lý' : ''}`),
      );
      row.append(main);
      if (item.managed) {
        const remove = smallButton('Gỡ');
        remove.addEventListener('click', async () => {
          if (!window.confirm(`Gỡ worktree ${item.path}? Worktree còn thay đổi chưa commit sẽ không gỡ được.`)) return;
          const resultBox = $('#whWorktreeResult');
          try {
            unwrap(await window.mcpAssistant.workhubWorktreeRemove({ path: item.path, expectedWorkspace: scope.workspace }));
            if (resultBox) resultBox.textContent = `Đã gỡ ${item.path}`;
          } catch (error) {
            if (resultBox) resultBox.textContent = `Không gỡ được: ${error.message}`;
          }
          renderWorktrees();
        });
        row.append(remove);
      }
      return row;
    }));
  }

  async function addWorktree() {
    const resultBox = $('#whWorktreeResult');
    const name = $('#whWorktreeName')?.value.trim() || '';
    const branch = $('#whWorktreeBranch')?.value.trim() || '';
    const scope = requestScope('worktrees');
    try {
      const data = unwrap(await window.mcpAssistant.workhubWorktreeAdd({ name, branch, expectedWorkspace: scope.workspace }));
      if (resultBox) resultBox.textContent = data?.path ? `Đã tạo: ${data.path} (nhánh ${data.branch})` : 'Đã tạo worktree.';
      const nameInput = $('#whWorktreeName');
      if (nameInput) nameInput.value = '';
    } catch (error) {
      if (resultBox) resultBox.textContent = `Không tạo được: ${error.message}`;
    }
    renderWorktrees();
  }

  function renderTaskFileChanges() {
    const box = $('#whTaskFiles');
    if (!box) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const files = S.taskFiles(task || {});
    if (!task || !files.length) { box.replaceChildren(el('span', 'task-muted', 'Task hiện tại chưa ghi nhận tệp thay đổi.')); return; }
    box.replaceChildren(...files.map((path) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', path), el('small', '', 'Được task ghi nhận — diff hiển thị thay đổi chưa commit trong cây làm việc'));
      row.append(main);
      const view = smallButton('Xem diff');
      view.addEventListener('click', () => renderDiff(path));
      row.append(view);
      return row;
    }));
  }

  // W2 (§5.1): the diff carries the HEAD it was read at plus a sha256
  // fingerprint of its exact text (electron/services/workHubFiles.js).
  // ui.diffStale is true when the workspace HEAD observed since (ui.gitHead,
  // refreshed by renderGit) no longer matches the diff's HEAD.
  function diffIsStale() {
    return Boolean(ui.diffHead && ui.gitHead && ui.diffHead !== ui.gitHead);
  }

  function renderDiffMeta(extra = '') {
    const meta = $('#whDiffMeta');
    if (!meta) return;
    if (!ui.diffRel) { meta.textContent = extra; return; }
    const parts = [];
    if (ui.diffHead) parts.push(`HEAD khi đọc diff: ${ui.diffHead.slice(0, 10)}`);
    if (ui.diffFingerprint) parts.push(`sha256 diff: ${ui.diffFingerprint.slice(0, 12)}…`);
    ui.diffStale = diffIsStale();
    if (ui.diffStale) parts.push(`STALE — HEAD hiện tại ${String(ui.gitHead).slice(0, 10)} đã khác; tải lại thay đổi trước khi duyệt/commit`);
    if (extra) parts.push(extra);
    meta.textContent = parts.join(' · ');
  }

  function renderDiffLines(box, text) {
    // Structured rendering (native port of the CoS unified-diff line
    // model): dual gutters, per-kind rows, bounded line count. Every line
    // is a text node — diff content is never injected as HTML. Falls back
    // to the previous plain-text <pre> when the parser is unavailable.
    const Diff = window.WorkHubDiff;
    if (!Diff) { box.textContent = text; return null; }
    const parsed = Diff.parseUnifiedDiff(text);
    if (!parsed.lines.length) { box.textContent = text; return parsed; }
    const rows = parsed.lines.map((line) => {
      const row = el('span', `wh-diff-line is-${line.kind}`);
      row.append(
        el('span', 'wh-diff-gutter', line.old === null ? '' : String(line.old)),
        el('span', 'wh-diff-gutter', line.next === null ? '' : String(line.next)),
        el('span', 'wh-diff-sign', line.kind === 'added' ? '+' : line.kind === 'removed' ? '−' : ' '),
        el('span', 'wh-diff-code', line.text),
      );
      return row;
    });
    if (parsed.truncated) rows.push(el('span', 'wh-diff-line is-meta', `… hiển thị tối đa ${Diff.DEFAULT_LIMIT} dòng diff — tệp thay đổi rất lớn; xem đầy đủ bằng git diff ngoài ứng dụng`));
    box.replaceChildren(...rows);
    return parsed;
  }

  async function renderDiff(rel) {
    const box = $('#whDiff');
    if (!box) return;
    const scope = requestScope('diff');
    activateTab('changes');
    box.textContent = 'Đang đọc thay đổi…';
    ui.diffRel = '';
    ui.diffText = '';
    ui.diffHead = '';
    ui.diffFingerprint = '';
    renderDiffMeta();
    renderPatchApproval();
    const data = unwrap(await window.mcpAssistant.workhubGitDiff(rel, scope.workspace).catch(() => null));
    if (!scope.current()) return;
    ui.diffRel = rel;
    ui.diffText = data?.diff || '';
    ui.diffHead = data?.head || '';
    ui.diffFingerprint = data?.fingerprint || '';
    if (!data) {
      box.textContent = 'Không lấy được diff.';
      renderDiffMeta();
    } else if (!data.diff) {
      box.textContent = 'Tệp chưa có diff (tệp mới chưa track sẽ không có diff — xem ở trang Tác vụ).';
      renderDiffMeta();
    } else {
      const parsed = renderDiffLines(box, data.diff);
      const counts = parsed ? `+${parsed.added} / −${parsed.removed} dòng` : '';
      renderDiffMeta([counts, data.truncated ? 'diff đã rút gọn ở 200KB' : ''].filter(Boolean).join(' · '));
    }
    renderPatchApproval();
  }

  // W5: git range review (workhub:git-review -> workHubGitReview).
  // ui.gitReviewHead is the workspace HEAD captured when the review ran
  // (for the default HEAD~1..HEAD range it equals the review's toHash);
  // the review is STALE once a later render/refresh observes a different
  // HEAD — the same pattern as the W2 diff STALE label above.
  function gitReviewIsStale() {
    return Boolean(ui.gitReview && ui.gitReviewHead && ui.gitHead && ui.gitReviewHead !== ui.gitHead);
  }

  function renderGitReviewMeta(extra = '') {
    const meta = $('#whGitReviewMeta');
    if (!meta) return;
    if (!ui.gitReview) { meta.textContent = extra; return; }
    const review = ui.gitReview;
    const totals = review.totals || {};
    const parts = [];
    parts.push(`${review.from}..${review.to} · ${totals.commits ?? 0} commit · ${totals.files ?? 0} tệp · +${totals.additions ?? 0} / −${totals.deletions ?? 0}${totals.renames ? ` · ${totals.renames} rename` : ''}`);
    if (review.fingerprint) parts.push(`fingerprint ${String(review.fingerprint).slice(0, 12)}…`);
    if (ui.gitReviewHead) parts.push(`HEAD khi rà soát: ${String(ui.gitReviewHead).slice(0, 10)}`);
    if (gitReviewIsStale()) parts.push(`STALE — HEAD hiện tại ${String(ui.gitHead).slice(0, 10)} đã khác đầu đã rà soát; chạy lại rà soát để xem range mới`);
    if (review.truncated) parts.push('kết quả đã rút gọn ở giới hạn commit/tệp của service');
    if (extra) parts.push(extra);
    meta.textContent = parts.join(' · ');
  }

  function renderGitReviewResults(review) {
    const box = $('#whGitReview');
    if (!box) return;
    const rows = [];
    const commits = Array.isArray(review.commits) ? review.commits : [];
    if (commits.length) {
      rows.push(el('div', 'wh-row', `Commit trong range (${commits.length})`));
      for (const commit of commits.slice(0, 20)) {
        const row = el('div', 'wh-row');
        const main = el('div', 'wh-row-main');
        main.append(el('b', '', `${String(commit.hash || '').slice(0, 10)} · ${commit.subject || ''}`),
          el('small', '', `${commit.author || ''} · ${commit.date || ''}`));
        row.append(main);
        rows.push(row);
      }
      if (commits.length > 20) rows.push(el('span', 'task-muted', `… còn ${commits.length - 20} commit nữa trong range (service giới hạn 200).`));
    }
    const files = Array.isArray(review.files) ? review.files : [];
    if (!files.length) {
      rows.push(el('span', 'task-muted', 'Range không có tệp thay đổi.'));
    } else {
      for (const group of (Array.isArray(review.subsystems) ? review.subsystems : [])) {
        rows.push(el('div', 'wh-row', `${group.subsystem} · ${group.files} tệp · +${group.additions} / −${group.deletions}${group.renames ? ` · ${group.renames} rename` : ''}`));
        for (const file of files.filter((item) => item.subsystem === group.subsystem)) {
          const row = el('div', 'wh-row');
          const main = el('div', 'wh-row-main');
          const label = file.renamed && file.origPath ? `${file.origPath} → ${file.path}` : file.path;
          const stats = file.binary
            ? 'binary (không tính dòng)'
            : `+${file.additions ?? '—'} / −${file.deletions ?? '—'} dòng`;
          main.append(el('b', '', label), el('small', '', `${file.status} · ${stats}`));
          row.append(main);
          rows.push(row);
        }
      }
    }
    box.replaceChildren(...rows);
  }

  async function renderGitReview() {
    const box = $('#whGitReview');
    if (!box) return;
    if (typeof window.mcpAssistant?.workhubGitReview !== 'function') {
      renderGitReviewMeta('Rà soát range cần ứng dụng Desktop.');
      return;
    }
    const scope = requestScope('gitreview');
    const from = String($('#whGitReviewFrom')?.value || '').trim();
    const to = String($('#whGitReviewTo')?.value || '').trim();
    box.replaceChildren(el('span', 'task-muted', 'Đang rà soát range…'));
    renderGitReviewMeta('Đang rà soát…');
    let raw = null;
    let thrown = '';
    try {
      raw = await window.mcpAssistant.workhubGitReview({ from: from || undefined, to: to || undefined, expectedWorkspace: scope.workspace });
    } catch (error) { thrown = error?.message || String(error || ''); }
    if (!scope.current()) return;
    if (raw && raw.ok === false) {
      // Service validation errors (e.g. an invalid rev) are shown verbatim.
      ui.gitReview = null;
      ui.gitReviewHead = '';
      box.replaceChildren(el('span', 'task-muted', 'Rà soát thất bại.'));
      renderGitReviewMeta(typeof raw.error === 'string' ? raw.error : (raw.error?.message || thrown || 'Rà soát thất bại.'));
      return;
    }
    const data = unwrap(raw);
    if (!data) {
      ui.gitReview = null;
      ui.gitReviewHead = '';
      box.replaceChildren(el('span', 'task-muted', 'Không lấy được kết quả rà soát.'));
      renderGitReviewMeta(thrown || 'Không lấy được kết quả rà soát.');
      return;
    }
    ui.gitReview = data;
    // Capture the workspace HEAD at review time for the STALE check; for
    // the default range this is the review's own `to` head (toHash).
    ui.gitReviewHead = data.toHash || '';
    if (typeof window.mcpAssistant.workhubGitHead === 'function') {
      const head = unwrap(await window.mcpAssistant.workhubGitHead(scope.workspace).catch(() => ''));
      if (!scope.current()) return;
      if (typeof head === 'string' && head) { ui.gitReviewHead = head; ui.gitHead = head; }
    }
    renderGitReviewResults(data);
    renderGitReviewMeta();
  }

  function renderPatchApproval() {
    const box = $('#whPatchApproval');
    if (!box) return;
    box.replaceChildren();
    if (!ui.diffRel || !ui.diffText) { box.append(el('span', 'task-muted', 'Chọn một tệp đã thay đổi để xem diff và duyệt.')); return; }
    const hash = S.hashText(ui.diffText);
    const approved = store.isPatchApproved(ui.diffRel, hash);
    const previous = store.patchApproval(ui.diffRel);
    box.append(el('span', 'task-muted', approved
      ? `Đã duyệt đúng bản vá này (${hash}).`
      : previous ? 'Bản vá đã thay đổi kể từ lần duyệt trước — cần duyệt lại.' : 'Chưa duyệt bản vá này.'));
    if (diffIsStale()) {
      box.append(el('span', 'task-muted', `Lưu ý STALE: diff này đọc ở HEAD ${ui.diffHead.slice(0, 10)}, HEAD hiện tại là ${String(ui.gitHead).slice(0, 10)} — duyệt ở đây chỉ gắn với đúng nội dung diff đã hiển thị, không tự áp cho cây mới.`));
    }
    const btn = smallButton(approved ? 'Đã duyệt' : 'Duyệt đúng bản vá này');
    btn.disabled = approved;
    btn.addEventListener('click', () => { store.approvePatch(ui.diffRel, hash); renderPatchApproval(); });
    box.append(btn);
    if (previous && !approved) {
      const revoke = smallButton('Xóa duyệt cũ');
      revoke.addEventListener('click', () => { store.revokePatchApproval(ui.diffRel); renderPatchApproval(); });
      box.append(revoke);
    }
  }

  function renderArtifacts() {
    const box = $('#whArtifacts');
    if (!box) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const workspace = currentProject();
    const report = task?.last_build_report || null;
    if (task?.details_available === false) { box.replaceChildren(el('span', 'task-muted', 'Chưa lấy được chi tiết công việc. Hãy kết nối runtime rồi làm mới để đọc báo cáo.')); return; }
    if (!report) { box.replaceChildren(el('span', 'task-muted', 'Công việc hiện tại chưa ghi nhận báo cáo build.')); return; }
    const head = el('div', 'wh-row');
    const headMain = el('div', 'wh-row-main');
    const reportLabels = { passed: 'Kiểm chứng đạt', failed: 'Kiểm chứng có lỗi', skipped: 'Chưa chạy kiểm chứng', unknown: 'Chưa xác định kết quả', running: 'Đang kiểm chứng' };
    headMain.append(el('b', '', reportLabels[report.overall_status] || 'Chưa xác định kết quả'),
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
      if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'].includes(ext)) {
        const viewImage = smallButton('Xem ảnh');
        viewImage.addEventListener('click', async () => {
          const scope = requestScope('artifactImage');
          const data = unwrap(await window.mcpAssistant.workhubReadImage(item.path, workspace).catch(() => null));
          if (!scope.current() || workspace !== currentProject()) return;
          const imgBox = $('#whArtifactImage');
          if (!imgBox) return;
          if (!data) { imgBox.replaceChildren(el('span', 'task-muted', 'Không xem trước được ảnh (quá lớn hoặc đã đổi).')); return; }
          const img = document.createElement('img');
          img.className = 'wh-artifact-img';
          img.alt = item.path;
          img.src = `data:${data.mime};base64,${data.base64}`;
          imgBox.replaceChildren(img);
        });
        row.append(viewImage);
      }
      const open = smallButton('Mở');
      open.addEventListener('click', async () => {
        const result = unwrap(await window.mcpAssistant.workhubOpenPath(item.path, false, workspace).catch(() => null));
        if (workspace !== currentProject()) return;
        if (!result) window.alert('Không mở được tệp — có thể tệp đã bị di chuyển hoặc đổi sau khi build.');
      });
      row.append(open);
      const reveal = smallButton('Mở thư mục');
      reveal.addEventListener('click', () => window.mcpAssistant.workhubOpenPath(item.path, true, workspace).catch(() => {}));
      row.append(reveal);
      const copy = smallButton('Sao chép đường dẫn');
      copy.addEventListener('click', (e) => copyText(item.path || '', e.currentTarget));
      row.append(copy);
      rows.push(row);
    });
    if (report.failure) rows.push(el('span', 'task-muted', `Lỗi: ${report.failure}`));
    box.replaceChildren(...rows);
  }

  async function loadTask() {
    const scope = requestScope('task');
    try {
      const source = window.mcpAssistant || (typeof api === 'undefined' ? null : api);
      const result = await source?.taskState?.();
      if (!scope.current()) return;
      ui.taskPayload = result?.data || result || null;
    } catch { if (!scope.current()) return; ui.taskPayload = null; }
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
      entries.push({ kind: 'Lời nhắc', title: p.name, detail: 'mẫu yêu cầu thư viện lời nhắc', run: () => { ui.selectedPromptId = p.id; renderPromptOptions(); saveCurrentDraft(); window.navigate?.('workhub'); activateTab('context'); const select = $('#whPromptSelect'); const preparation = select?.closest('details'); if (preparation) preparation.open = true; select?.focus(); } });
    }
    for (const r of store.listRecipes(currentProject())) {
      entries.push({ kind: 'Lệnh đã lưu', title: r.name, detail: r.command, run: () => { window.navigate?.('workhub'); activateTab('verify'); $('#whRecipeList')?.scrollIntoView({ block: 'start' }); setStatus(`Lệnh đã lưu: ${r.name} · ${r.command}. Chọn Chạy lệnh để thực thi.`); } });
    }
    for (const project of recentProjects()) {
      entries.push({
        kind: 'Dự án', title: store.projectLabel(project), detail: project,
        run: async () => {
          if (!await switchProject(project)) return;
          window.navigate?.('workhub');
        },
      });
    }
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if (task?.objective) {
      entries.push({ kind: 'Tác vụ', title: task.objective, detail: `task hiện tại · ${task.status || ''}`, run: () => window.navigate?.('task') });
      entries.push({ kind: 'Báo cáo', title: `Báo cáo: ${task.objective}`, detail: 'kết quả và xuất báo cáo', run: () => { window.navigate?.('workhub'); activateTab('results'); } });
    }
    for (const note of store.listNotes(currentProject())) {
      entries.push({ kind: 'Ghi chú', title: note.title, detail: note.body.slice(0, 80), run: () => { window.navigate?.('workhub'); const box = $('#whNotes'); for (let parent = box?.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true; box?.scrollIntoView({ block: 'start' }); } });
    }
    for (const chat of store.listChats(currentProject())) {
      entries.push({ kind: 'Hội thoại', title: chat.label, detail: chat.note || chat.url || '', run: () => { if (chat.url) window.mcpAssistant?.openExternal?.(chat.url); } });
    }
    for (const file of store.basketFor(currentProject())) {
      entries.push({ kind: 'Tệp ngữ cảnh', title: file.path, detail: 'trong giỏ ngữ cảnh của dự án hiện tại', run: () => { window.navigate?.('workhub'); return openFile(String(file.path).replace(/\\/g, '/')); } });
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
    if (overlay.hidden) ui.searchReturnFocus = document.activeElement;
    overlay.hidden = false;
    renderSearchResults();
    setTimeout(() => $('#whSearchInput')?.focus(), 0);
  }
  function closeSearch() {
    const overlay = $('#whSearchOverlay');
    if (overlay && !overlay.hidden) { overlay.hidden = true; ui.searchReturnFocus?.focus?.(); }
  }

  // ---------- M1.5: LSP code navigation ----------
  async function renderLspProviders() {
    const badge = $('#whLspProvider');
    if (!badge || !window.mcpAssistant?.workhubLspProviders) return;
    const scope = requestScope('lsp');
    const data = unwrap(await window.mcpAssistant.workhubLspProviders(scope.workspace).catch(() => null));
    if (!scope.current() || !data) return;
    const ready = data.filter((p) => p.status === 'ready').map((p) => p.id);
    badge.textContent = ready.length ? ready.join(' + ') : 'fallback';
    const status = $('#whLspStatus');
    if (status) status.textContent = data.map((p) => `${p.id}: ${p.status === 'ready' ? 'sẵn sàng' : p.status} — ${p.detail}`).join(' · ');
  }
  function lspPayload() {
    const rel = String($('#whLspFile')?.value || ui.viewerRel || '').trim();
    return {
      rel,
      line: Math.max(1, Number($('#whLspLine')?.value || 1)),
      character: Math.max(1, Number($('#whLspCol')?.value || 1)),
    };
  }
  async function renderLspNavigate(kind) {
    const box = $('#whLspResults');
    if (!box || !window.mcpAssistant?.workhubLspDefinition) return;
    const payload = lspPayload();
    if (!payload.rel) { box.replaceChildren(el('span', 'task-muted', 'Hãy mở một tệp hoặc nhập đường dẫn tệp.')); return; }
    const scope = requestScope('lsp');
    box.textContent = 'Đang định vị…';
    const call = kind === 'definition' ? window.mcpAssistant.workhubLspDefinition : window.mcpAssistant.workhubLspReferences;
    const data = unwrap(await call({ ...payload, expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Định vị thất bại.')); return; }
    const rows = [];
    rows.push(el('span', 'task-muted', data.fallback
      ? `Fallback tìm văn bản cho "${data.word || ''}" — KHÔNG phải định vị ngữ nghĩa.`
      : `Provider: ${data.provider}`));
    if (!data.results.length) rows.push(el('span', 'task-muted', 'Không có kết quả.'));
    for (const hit of data.results) {
      const row = el('button', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(el('b', '', `${hit.path}:${hit.line}:${hit.character}`), el('small', '', hit.kind || hit.text || ''));
      row.append(main);
      row.addEventListener('click', () => openFile(hit.path, hit.line));
      rows.push(row);
    }
    box.replaceChildren(...rows);
  }
  async function renderLspSymbols() {
    const box = $('#whLspResults');
    if (!box || !window.mcpAssistant?.workhubLspSymbols) return;
    const { rel } = lspPayload();
    if (!rel) { box.replaceChildren(el('span', 'task-muted', 'Hãy mở một tệp hoặc nhập đường dẫn tệp.')); return; }
    const scope = requestScope('lsp');
    box.textContent = 'Đang đọc ký hiệu…';
    const data = unwrap(await window.mcpAssistant.workhubLspSymbols({ rel, expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Đọc ký hiệu thất bại.')); return; }
    if (data.fallback) { box.replaceChildren(el('span', 'task-muted', 'Tệp này không có language server — không liệt kê ký hiệu theo fallback.')); return; }
    const rows = [el('span', 'task-muted', `Provider: ${data.provider} — ${data.symbols.length} ký hiệu`)];
    for (const symbol of data.symbols) {
      const row = el('button', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(el('b', '', `${'  '.repeat(Math.min(symbol.depth || 0, 6))}${symbol.name}`), el('small', '', `${symbol.kind} · dòng ${symbol.line}`));
      row.append(main);
      row.addEventListener('click', () => openFile(rel, symbol.line));
      rows.push(row);
    }
    box.replaceChildren(...rows);
  }

  // ---------- M2: coordination (runs / workers / steering) ----------
  // ---------- W1: CoS companion (read-only, OBSERVED) ----------
  // Sessions come from the CoS Control API through the main-process adapter.
  // They are external observations: no project binding exists for them, the
  // panel says so, and nothing here renders CoS text as HTML or offers any
  // send/stop/resume action.
  const COS_STATE_LABELS = {
    DISCONNECTED: 'Chưa kết nối CoS',
    CONNECTED_READ_ONLY: 'Đã kết nối CoS · chỉ đọc',
    ACTIONS_AUTHORIZED: 'Đã kết nối CoS · CoS đang bật hành động (adapter vẫn chỉ đọc)',
    STALE: 'Mất kết nối CoS · dữ liệu cũ (stale)',
    UNKNOWN: 'Trạng thái CoS không xác định',
  };
  async function renderCosCompanion() {
    const stateBox = $('#whCosState');
    const listBox = $('#whCosSessions');
    if (!stateBox || !listBox || typeof window.mcpAssistant?.workhubCosStatus !== 'function') return;
    const scope = requestScope('cos');
    const view = unwrap(await window.mcpAssistant.workhubCosStatus().catch(() => null));
    if (!scope.current()) return;
    if (!view) { stateBox.textContent = 'Không đọc được trạng thái companion.'; return; }
    if (view.enabled === false) {
      stateBox.textContent = 'Companion đang tắt (cosCompanionEnabled=false). Khi tắt, Work Hub không thay đổi gì.';
      listBox.replaceChildren();
      return;
    }
    const label = COS_STATE_LABELS[view.state] || String(view.state || 'Không xác định');
    stateBox.textContent = view.error
      ? `${label} — ${view.error.message || view.error.code || ''}`
      : `${label}${view.appVersion ? ` · CoS ${view.appVersion}` : ''}. Phiên dưới đây là quan sát OBSERVED, chưa liên kết với dự án/RUN hiện tại. Worker CoS không đọc được ở chế độ chỉ đọc — worker trong Work Hub là worker EOCL.`;
    if (view.state !== 'CONNECTED_READ_ONLY' && view.state !== 'ACTIONS_AUTHORIZED') {
      listBox.replaceChildren(el('span', 'task-muted', 'Chưa có dữ liệu phiên.'));
      return;
    }
    const result = unwrap(await window.mcpAssistant.workhubCosSessions({ limit: 20 }).catch(() => null));
    if (!scope.current()) return;
    const data = result && result.ok ? result.data : null;
    if (!data) {
      listBox.replaceChildren(el('span', 'task-muted', (result && result.error && result.error.message) || 'Không đọc được danh sách phiên CoS.'));
      return;
    }
    if (!data.sessions.length) {
      listBox.replaceChildren(el('span', 'task-muted', 'CoS chưa ghi phiên nào.'));
      return;
    }
    listBox.replaceChildren(...data.sessions.map((session) => {
      const row = el('div', 'wh-row');
      const title = el('span', '', `${session.title || '(không tiêu đề)'} · OBSERVED`);
      const meta = el('span', 'task-muted', ` ${session.updatedAt ? new Date(session.updatedAt).toLocaleString('vi-VN') : ''}${session.conversationId ? ` · conv ${String(session.conversationId).slice(0, 8)}` : ''}`);
      const open = el('button', 'secondary-button wh-small', 'Xem sự kiện');
      open.type = 'button';
      open.addEventListener('click', () => openCosSession(session.sessionId));
      row.appendChild(title);
      row.appendChild(meta);
      row.appendChild(open);
      return row;
    }));
  }

  async function openCosSession(sessionId) {
    const box = $('#whCosEvents');
    if (!box || !sessionId || typeof window.mcpAssistant?.workhubCosSessionEvents !== 'function') return;
    const scope = requestScope('cos-events');
    box.textContent = 'Đang tải sự kiện…';
    const result = unwrap(await window.mcpAssistant.workhubCosSessionEvents({ sessionId, limit: 50 }).catch(() => null));
    if (!scope.current()) return;
    const data = result && result.ok ? result.data : null;
    if (!data) {
      box.textContent = (result && result.error && result.error.message) || 'Không đọc được sự kiện của phiên.';
      return;
    }
    const lines = data.events.map((event) => {
      const when = event.time ? new Date(event.time).toLocaleTimeString('vi-VN') : '';
      const head = `[${when}] ${event.kind}${event.toolName ? ` · ${event.toolName}` : ''}`;
      const body = event.text || event.detail || '';
      return body ? `${head}\n${body}` : head;
    });
    box.textContent = lines.length ? lines.join('\n\n') : 'Phiên chưa có sự kiện nào được ghi.';
  }

  // ---------- W3: native Codex chat (Codex App Server via codex_bridge) ----------
  // The chat lives in Codex-web itself — no CoS app is involved. Session
  // state is held by the main-process service (workhub:codex-chat-*); this
  // panel only renders what the bridge reports. A thread is shown as linked
  // to a RUN only when the service recorded a real run_id captured from the
  // current task state at creation time — never inferred from chat content.
  const CODEX_CHAT_STATE_LABELS = {
    UNKNOWN: 'Chưa kiểm tra Codex App Server',
    READY: 'Codex App Server sẵn sàng',
    RUNNING: 'Đang chạy lượt chat…',
    COMPLETED: 'Lượt chat hoàn tất',
    FAILED: 'Lượt chat lỗi',
    INTERRUPTED: 'Đã dừng lượt chat',
    PROVIDER_UNAVAILABLE: 'Chưa có Codex provider trên máy này',
    MCP_UNAVAILABLE: 'MCP chưa sẵn sàng',
    OWNERSHIP_LOST: 'Phiên chat thuộc tiến trình bridge trước (MCP/App Server đã khởi động lại) — không tiếp tục được, hãy tạo chat mới',
  };
  const codexChatUi = { timer: null, modelsLoaded: false };
  function stopCodexChatPolling() {
    if (codexChatUi.timer) { clearInterval(codexChatUi.timer); codexChatUi.timer = null; }
  }
  function paintCodexChat(view) {
    const stateBox = $('#whCodexChatState');
    if (!stateBox || !view) return;
    const label = CODEX_CHAT_STATE_LABELS[view.state] || String(view.state || '');
    const version = view.availability?.codexVersion ? ` · Codex ${view.availability.codexVersion}` : '';
    const route = view.route ? ` · ${view.route.model || ''}${view.route.effort ? `/${view.route.effort}` : ''}` : '';
    stateBox.textContent = view.error
      ? `${label} — ${view.error.message || view.error.code || ''}`
      : `${label}${version}${route}${view.threadId ? ` · thread ${String(view.threadId).slice(0, 8)}` : ''}.`;
    const log = $('#whCodexChatLog');
    if (log) {
      log.replaceChildren(...view.messages.map((message) => {
        const row = el('div', `wh-chat-msg ${message.role === 'user' ? 'is-user' : 'is-assistant'}`);
        const head = el('div', 'wh-chat-head', message.role === 'user'
          ? 'Bạn'
          : `Codex${message.status === 'running' ? ' · đang trả lời…' : message.status === 'interrupted' ? ' · đã dừng' : message.status === 'failed' ? ' · lỗi' : ''}`);
        const body = el('div', 'wh-chat-body', message.text || (message.status === 'running' ? '…' : ''));
        row.append(head, body);
        return row;
      }));
    }
    const eventsBox = $('#whCodexChatEvents');
    if (eventsBox) {
      const events = (view.events || []).slice(-8);
      eventsBox.replaceChildren(...events.map((event) => el('div', 'wh-row',
        `${event.method || ''}${event.itemType ? ` · ${event.itemType}` : ''}${event.status ? ` · ${event.status}` : ''}`)));
    }
    const linkBox = $('#whCodexChatLink');
    if (linkBox) {
      const forkNote = view.forkedFrom ? ` · fork từ thread Desktop ${String(view.forkedFrom).slice(0, 8)} (kế thừa bối cảnh qua App Server; panel không đọc được lượt cũ)` : '';
      linkBox.textContent = (view.link?.runId
        ? `Liên kết RUN ${view.link.runId}${view.link.taskId ? ` · task ${view.link.taskId}` : ''} (id thật từ trạng thái tác vụ lúc tạo chat hoặc từ handoff).`
        : 'Chưa liên kết RUN — liên kết chỉ được ghi khi chat được tạo trong lúc tác vụ hiện tại có RUN thật, hoặc qua "Chuyển thành việc điều hành".') + forkNote;
    }
    // P0 handoff mismatch: the chat link and the panel's current task
    // disagree, so the service refused to guess. Offer the three
    // choices explicitly instead of a dead error line.
    const handoffBox = $('#whCodexChatHandoffInfo');
    if (handoffBox && view.mismatch) {
      const m = view.mismatch;
      handoffBox.replaceChildren();
      handoffBox.append(el('div', 'wh-row',
        `Handoff đang lệch: phiên chat liên kết RUN ${m.linkRunId}${m.linkTaskId ? ` · task ${m.linkTaskId}` : ''}, nhưng tác vụ hiện tại của panel là RUN ${m.currentRunId}${m.currentTaskId ? ` · task ${m.currentTaskId}` : ''}${m.hasPendingCapsule ? ' · có capsule chờ ghi từ lần handoff trước.' : '.'} Chọn nơi ghi capsule:`));
      for (const [choice, label] of [['current', 'Ghi vào RUN hiện tại'], ['link', 'Giữ link cũ'], ['new', 'Tạo task mới']]) {
        const button = smallButton(label);
        button.addEventListener('click', () => handoffCodexChatChoice(choice));
        handoffBox.append(button);
      }
    } else if (handoffBox && view.handoff) {
      // W3-C handoff receipt: directive + recommended action are shown
      // verbatim; a blocked directive is a stop sign, not a suggestion.
      const h = view.handoff;
      if (h.status === 'blocked') {
        handoffBox.textContent = `Handoff BỊ CHẶN bởi directive ${h.directive || ''}. ${h.recommendedNextAction || 'Hãy reconcile trước khi tiếp tục.'} Không tạo task mới, không ghi capsule mới, không tiếp tục mù.`;
      } else {
        handoffBox.textContent = `Đã chuyển thành việc điều hành: task ${h.taskId || '—'}${h.runId ? ` · RUN ${h.runId}` : ''}${h.capsuleId ? ` · capsule ${String(h.capsuleId).slice(0, 8)}` : ''}${h.lease ? ` · lease ${h.lease.status || ''} · owner ${h.lease.owner || ''} · hết hạn ${h.lease.expiresAt || ''}` : ''}${h.capsuleNote ? ` · ${h.capsuleNote}` : ''}${h.leaseNote ? ` · ${h.leaseNote}` : ''}`;
      }
    }
    const sendBtn = $('#whCodexChatSend');
    if (sendBtn) sendBtn.disabled = view.state === 'RUNNING' || view.state === 'PROVIDER_UNAVAILABLE' || view.state === 'MCP_UNAVAILABLE' || view.state === 'OWNERSHIP_LOST';
    const stopBtn = $('#whCodexChatStop');
    if (stopBtn) stopBtn.disabled = view.state !== 'RUNNING';
    const handoffBtn = $('#whCodexChatHandoff');
    if (handoffBtn) handoffBtn.disabled = !(view.messages || []).length || view.state === 'RUNNING';
  }
  async function pollCodexChatTurn(scope) {
    if (typeof window.mcpAssistant?.workhubCodexChatPoll !== 'function') return;
    const result = unwrap(await window.mcpAssistant.workhubCodexChatPoll({ expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) { stopCodexChatPolling(); return; }
    const view = result?.data;
    if (view) paintCodexChat(view);
    if (!view || view.state !== 'RUNNING') stopCodexChatPolling();
  }
  function startCodexChatPolling(scope) {
    stopCodexChatPolling();
    codexChatUi.timer = setInterval(() => { pollCodexChatTurn(scope).catch(() => {}); }, 1500);
  }
  async function renderCodexChat() {
    const stateBox = $('#whCodexChatState');
    if (!stateBox || typeof window.mcpAssistant?.workhubCodexChatProbe !== 'function') return;
    const scope = requestScope('codex-chat');
    const result = unwrap(await window.mcpAssistant.workhubCodexChatProbe({ expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    const view = result?.data;
    if (!view) { stateBox.textContent = 'Không đọc được trạng thái Codex App Server.'; return; }
    paintCodexChat(view);
    if (view.state === 'RUNNING') startCodexChatPolling(scope);
    loadCodexChatModels(scope);
    const threadsBox = $('#whCodexChatThreads');
    if (threadsBox && result.ok) {
      const history = unwrap(await window.mcpAssistant.workhubCodexChatHistory({ expectedWorkspace: scope.workspace }).catch(() => null));
      if (!scope.current()) return;
      const threads = history?.data?.threads || [];
      if (!threads.length) {
        threadsBox.replaceChildren(el('span', 'task-muted', 'Chưa có lịch sử Codex nào trong dự án này.'));
        return;
      }
      const rows = [el('span', 'task-muted', 'Lịch sử Codex của dự án này (chỉ xem summary — panel không đọc được nội dung lượt cũ của thread Desktop; fork kế thừa bối cảnh qua App Server bằng thread/fork, không qua việc panel đọc turns):')];
      for (const t of threads) {
        const row = el('div', 'wh-row');
        const main = el('span', 'wh-row-main', `${t.name || t.preview || t.id.slice(0, 8)}${t.updatedAt ? ` · ${new Date(t.updatedAt).toLocaleString('vi-VN')}` : ''}`);
        row.append(main);
        if (typeof window.mcpAssistant?.workhubCodexChatFork === 'function') {
          const forkBtn = el('button', 'secondary-button', 'Fork thành chat mới');
          forkBtn.addEventListener('click', () => forkCodexChatFromHistory(t.id));
          row.append(forkBtn);
        }
        rows.push(row);
      }
      threadsBox.replaceChildren(...rows);
    }
  }
  async function loadCodexChatModels(scope) {
    const select = $('#whCodexChatModel');
    if (!select || codexChatUi.modelsLoaded || typeof window.mcpAssistant?.workhubCodexChatModels !== 'function') return;
    codexChatUi.modelsLoaded = true;
    const result = unwrap(await window.mcpAssistant.workhubCodexChatModels({ expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    const models = result?.data?.models || [];
    const current = select.value;
    const makeOption = (value, label) => { const opt = el('option', '', label); opt.value = value; return opt; };
    select.replaceChildren(...[
      makeOption('', 'Mặc định của profile chat'),
      ...models.map((m) => makeOption(m.id, m.displayName || m.id)),
    ]);
    select.value = current || '';
  }
  function codexChatRouteSelection() {
    const model = String($('#whCodexChatModel')?.value || '').trim();
    const effort = String($('#whCodexChatEffort')?.value || '').trim();
    return { ...(model ? { model } : {}), ...(effort ? { effort } : {}) };
  }
  async function forkCodexChatFromHistory(sourceThreadId) {
    const input = $('#whCodexChatInput');
    const text = String(input?.value || '').trim();
    if (!text) {
      setStatus('Nhập nội dung lượt đầu vào ô chat trước khi fork — fork tạo thread mới bằng chính lượt đó (bridge không tạo thread rỗng).', 'error');
      input?.focus();
      return;
    }
    if (typeof window.mcpAssistant?.workhubCodexChatFork !== 'function') return;
    const scope = requestScope('codex-chat');
    const result = unwrap(await window.mcpAssistant.workhubCodexChatFork({
      expectedWorkspace: scope.workspace, sourceThreadId, text, ...codexChatRouteSelection(),
    }).catch(() => null));
    if (!scope.current()) return;
    const view = result?.data;
    if (view) paintCodexChat(view);
    if (result?.ok) {
      if (input) input.value = '';
      setStatus('Đã fork thành chat mới (bridge-owned, tiếp tục được). Nội dung lượt cũ của thread Desktop không hiển thị ở panel — chỉ summary; bối cảnh được kế thừa qua App Server.');
      startCodexChatPolling(scope);
    }
  }
  async function handoffCodexChatRequest(extra = {}) {
    if (typeof window.mcpAssistant?.workhubCodexChatHandoff !== 'function') return null;
    const scope = requestScope('codex-chat');
    // P0 (L1/L5): pass the CURRENT panel task link, exactly like send
    // does — the service blocks on a stale link instead of guessing.
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const runId = task?.orchestration?.run_id || task?.run_id || '';
    const link = runId ? { runId, taskId: task?.task_id || '' } : null;
    const result = unwrap(await window.mcpAssistant.workhubCodexChatHandoff({ expectedWorkspace: scope.workspace, link, runId: runId || undefined, ...extra }).catch(() => null));
    if (!scope.current()) return null;
    const view = result?.data;
    if (view) paintCodexChat(view);
    if (!result?.ok) setStatus(result?.error?.message || 'Handoff thất bại.', 'error');
    return result;
  }
  async function handoffCodexChat() {
    const result = await handoffCodexChatRequest();
    if (result?.error?.code === 'HANDOFF_RUN_ENDED' && result.error.runId) {
      // Ended RUN, default refuse: only an explicit confirmation
      // proceeds, and it re-invokes with the confirmation flag.
      if (window.confirm(`RUN ${result.error.runId} đã kết thúc (trạng thái ${result.error.runStatus || ''}). Ghi capsule vào RUN đã kết thúc?`)) {
        await handoffCodexChatRequest({ confirmEnded: true });
      } else {
        setStatus('Đã hủy handoff vào RUN đã kết thúc.', 'info');
      }
    }
  }
  async function handoffCodexChatChoice(choice) {
    await handoffCodexChatRequest({ choice });
  }
  async function sendCodexChat() {
    const input = $('#whCodexChatInput');
    const text = String(input?.value || '').trim();
    if (!text || typeof window.mcpAssistant?.workhubCodexChatSend !== 'function') return;
    const scope = requestScope('codex-chat');
    // Capture the link from the CURRENT task state only: a real run_id the
    // runtime already recorded. No run -> no link, by design.
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const runId = task?.orchestration?.run_id || task?.run_id || '';
    const link = runId ? { runId, taskId: task?.task_id || '' } : null;
    const result = unwrap(await window.mcpAssistant.workhubCodexChatSend({ expectedWorkspace: scope.workspace, text, link, ...codexChatRouteSelection() }).catch(() => null));
    if (!scope.current()) return;
    const view = result?.data;
    if (view) paintCodexChat(view);
    if (result?.ok) {
      if (input) input.value = '';
      startCodexChatPolling(scope);
    }
  }

  async function renderCoordRuns() {
    const box = $('#whCoordRuns');
    if (!box || !window.mcpAssistant?.workhubCoordRuns) return;
    const scope = requestScope('coord');
    const data = unwrap(await window.mcpAssistant.workhubCoordRuns({ limit: 15, expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    if (!data?.available) { box.replaceChildren(el('span', 'task-muted', 'Chưa có ledger orchestration trong dự án này.')); return; }
    if (!data.runs.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có RUN nào.')); return; }
    const rows = data.runs.map((run) => {
      const row = el('button', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(
        el('b', '', `${run.status} · ${run.runId.slice(0, 8)} · ${run.waveCount} wave · ${run.laneCount} lane`),
        el('small', '', `${run.startedAt || ''} — ${run.objective || '(không có mô tả)'}`)
      );
      row.append(main);
      row.addEventListener('click', () => renderCoordDetail(run.runId));
      return row;
    });
    box.replaceChildren(...rows);
  }
  async function renderCoordDetail(runId) {
    const box = $('#whCoordDetail');
    if (!box || !window.mcpAssistant?.workhubCoordRun) return;
    const scope = requestScope('coord');
    box.textContent = 'Đang đọc ledger…';
    const data = unwrap(await window.mcpAssistant.workhubCoordRun({ runId, expectedWorkspace: scope.workspace }).catch(() => null));
    if (!scope.current()) return;
    if (!data?.found) { box.replaceChildren(el('span', 'task-muted', 'Không tìm thấy RUN.')); return; }
    if ($('#whSteerRun')) $('#whSteerRun').value = runId;
    const parts = [];
    const head = el('p', 'wh-help', `RUN ${data.run.runId} · ${data.run.status} · task ${data.run.taskId}`);
    parts.push(head);
    const lines = [];
    // W2 (§5.2): every row carries its source. Workers below are EOCL
    // delegations from the ledger and lanes are agent lanes of the same
    // run — neither is a CoS worker (CoS workers are not readable in
    // read-only mode, W0 S1, and are never mixed into this board).
    lines.push(`Nguồn: ledger EOCL · dự án ${scope.workspace}`);
    for (const wave of data.waves) lines.push(`Wave ${wave.ordinal}: ${wave.status} · ${wave.mode || ''} · head ${(wave.baseHead || '').slice(0, 8)}`);
    for (const worker of data.workers) lines.push(`Worker EOCL · ${worker.owner || ''} · ${worker.model || ''} · effort ${worker.effort || ''} · ${worker.status} · scope ${(worker.scope || []).length} đường dẫn${worker.finishedAt ? '' : ' · chưa kết thúc (đang chạy hoặc đang chờ)'}`);
    for (const lane of data.lanes) lines.push(`Lane (agent lane) · ${lane.role} · ${lane.provider || ''} · ${lane.model || ''} · ${lane.lifecycle}`);
    if (data.lease) lines.push(`Lease: ${data.lease.status} · owner ${data.lease.owner} · hết hạn ${data.lease.expiresAt}`);
    for (const proof of data.proofs.slice(0, 8)) lines.push(`Proof ${proof.stage}: ${proof.status} · exit ${proof.exitCode ?? '—'} · ${proof.durationMs ?? '—'}ms${proof.cacheHit ? ' · cache' : ''}`);
    for (const msg of data.messages) lines.push(`Coord msg ${msg.kind} (${msg.direction}): ${msg.status}${msg.acknowledgedAt ? ` · ack ${msg.acknowledgedAt}` : ' · chưa ack'}`);
    for (const event of data.activity.slice(-10)) lines.push(`${event.at} · ${event.type}: ${event.from || ''} → ${event.to || ''}`);
    const pre = el('pre', 'task-command wh-viewer');
    pre.textContent = lines.join('\n') || 'Không có dữ liệu chi tiết.';
    parts.push(pre);
    box.replaceChildren(...parts);
  }
  async function renderSteering() {
    const box = $('#whSteerList');
    if (!box || !window.mcpAssistant?.workhubSteerList) return;
    const scope = requestScope('coord');
    const data = unwrap(await window.mcpAssistant.workhubSteerList(scope.workspace).catch(() => null));
    if (!scope.current() || !Array.isArray(data)) return;
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có điều chỉnh nào.')); return; }
    const stateLabel = { draft: 'Bản nháp', saved: 'Đã lưu', dispatched: 'Đã dispatch', acknowledged: 'Đã xác nhận', consumed: 'Đã tiêu thụ' };
    const rows = data.map((record) => {
      const row = el('div', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(
        el('b', '', `${stateLabel[record.state] || record.state} · RUN ${String(record.runId).slice(0, 8)} → ${record.recipient}`),
        el('small', '', `${record.text}${record.capsuleSha256 ? ` · capsule ${record.capsuleSha256.slice(0, 12)}…` : ''}${record.state === 'dispatched' ? ' · chưa có bằng chứng tiếp nhận' : ''}`)
      );
      row.append(main);
      if (record.state === 'saved' || record.state === 'draft') {
        const btn = el('button', 'secondary-button', 'Dispatch');
        btn.addEventListener('click', async () => {
          await window.mcpAssistant.workhubSteerDispatch({ id: record.id, expectedWorkspace: scope.workspace }).catch(() => null);
          renderSteering();
        });
        row.append(btn);
      }
      return row;
    });
    box.replaceChildren(...rows);
  }
  async function saveSteeringFromForm() {
    if (!window.mcpAssistant?.workhubSteerSave) return;
    const scope = requestScope('coord');
    const payload = {
      runId: String($('#whSteerRun')?.value || '').trim(),
      text: String($('#whSteerText')?.value || '').trim(),
      recipient: 'controller',
      expectedWorkspace: scope.workspace,
    };
    const saved = unwrap(await window.mcpAssistant.workhubSteerSave(payload).catch(() => null));
    if (!scope.current()) return;
    if (saved && $('#whSteerText')) $('#whSteerText').value = '';
    renderSteering();
  }

  // ---------- M3.1: browser QA captures ----------
  function qaSummary(record) {
    if (!record) return 'Không có dữ liệu.';
    const verdict = record.verdict ? ` · kỳ vọng "${record.verdict.expectedText}": ${record.verdict.pass ? 'ĐẠT' : 'KHÔNG ĐẠT'}` : '';
    const shot = record.screenshot ? ` · ảnh ${record.screenshot.path} sha256 ${record.screenshot.sha256.slice(0, 12)}…` : ' · không có ảnh';
    return `${record.at} · ${record.status}${record.loadError ? ` (${record.loadError})` : ''} · ${record.finalUrl} · "${record.title}" · console lỗi: ${record.consoleErrors} · request lỗi: ${record.networkErrors.length} · DOM ${record.domChars} ký tự${shot}${verdict}${record.jobId ? ` · Job ${record.jobId}` : ''}`;
  }
  async function renderQaList() {
    const box = $('#whQaList');
    if (!box || !window.mcpAssistant?.workhubQaList) return;
    const scope = requestScope('qa');
    const data = unwrap(await window.mcpAssistant.workhubQaList(scope.workspace).catch(() => null));
    if (!scope.current() || !Array.isArray(data)) return;
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có bản chụp nào.')); return; }
    box.replaceChildren(...data.map((record) => {
      const row = el('div', 'wh-search-row');
      const main = el('span', 'wh-row-main');
      main.append(el('b', '', `${record.status} · ${record.title || record.finalUrl}`), el('small', '', qaSummary(record)));
      row.append(main);
      return row;
    }));
  }
  async function runQaCapture() {
    const out = $('#whQaResult');
    if (!window.mcpAssistant?.workhubQaCapture) return;
    const scope = requestScope('qa');
    const payload = {
      url: String($('#whQaUrl')?.value || '').trim(),
      expectedText: String($('#whQaExpected')?.value || '').trim(),
      expectedWorkspace: scope.workspace,
    };
    if (out) out.textContent = 'Đang mở trang trong cửa sổ ẩn và chụp bằng chứng…';
    const data = unwrap(await window.mcpAssistant.workhubQaCapture(payload).catch((error) => ({ error: String(error?.message || error) })));
    if (!scope.current() || !out) return;
    if (!data || data.error) { out.textContent = `Chụp thất bại: ${data?.error || 'không có phản hồi'}`; return; }
    out.textContent = `${qaSummary(data)}\n\n--- Trích DOM ---\n${data.domExcerpt || '(trống)'}`;
    renderQaList();
  }

  // ---------- wiring ----------
  function bind() {
    const tabs = Array.from(document.querySelectorAll('[data-wh-tab]'));
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => activateTab(tab.dataset.whTab));
      tab.addEventListener('keydown', (event) => {
        const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1;
        if (next < 0) return;
        event.preventDefault();
        activateTab(tabs[next].dataset.whTab, { focus: true });
      });
    });
    $('#whOpenSearch')?.addEventListener('click', openSearch);
    $('#whRefresh')?.addEventListener('click', async () => {
      const button = $('#whRefresh');
      button.disabled = true;
      try { await refresh(); } finally { button.disabled = false; }
    });
    $('#whBrowseFiles')?.addEventListener('click', () => { $('#whFileBrowser')?.scrollIntoView({ block: 'start', behavior: 'smooth' }); $('#whCodeQuery')?.focus(); });
    $('#whPromptSelect')?.addEventListener('change', (e) => { ui.selectedPromptId = e.target.value; renderPromptOptions(); saveCurrentDraft(); });
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
    $('#whTaskType')?.addEventListener('change', (e) => { ui.selectedType = e.target.value; renderTypeFields(); saveCurrentDraft(); });
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
        store.upsertRecipe({ name: $('#whRecipeName').value, command: $('#whRecipeCommand').value, cwd: $('#whRecipeCwd').value || currentProject(), url: $('#whRecipeUrl')?.value || '' });
        $('#whRecipeName').value = ''; $('#whRecipeCommand').value = ''; $('#whRecipeCwd').value = ''; if ($('#whRecipeUrl')) $('#whRecipeUrl').value = '';
        renderRecipes();
        setStatus('Đã lưu lệnh cho dự án này.');
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
    $('#whQaCapture')?.addEventListener('click', runQaCapture);
    $('#whQaReload')?.addEventListener('click', renderQaList);
    $('#whCoordReload')?.addEventListener('click', () => { renderCoordRuns(); renderSteering(); });
    $('#whSteerSave')?.addEventListener('click', saveSteeringFromForm);
    $('#whLspDefinition')?.addEventListener('click', () => renderLspNavigate('definition'));
    $('#whLspReferences')?.addEventListener('click', () => renderLspNavigate('references'));
    $('#whLspSymbols')?.addEventListener('click', renderLspSymbols);
    $('#whCodeQuery')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') renderCodeSearch(); });
    $('#whGitRefresh')?.addEventListener('click', renderGit);
    $('#whCommitAll')?.addEventListener('change', (event) => {
      document.querySelectorAll('.wh-commit-check').forEach((box) => {
        box.checked = event.target.checked;
        if (box.dataset.path) {
          if (event.target.checked) ui.commitSelection.add(box.dataset.path);
          else ui.commitSelection.delete(box.dataset.path);
        }
      });
      renderCommitBar();
    });
    $('#whCommitSelected')?.addEventListener('click', commitSelectedFiles);
    $('#whCommitMessage')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') commitSelectedFiles(); });
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
      const overlay = $('#whSearchOverlay');
      if (!overlay || overlay.hidden) return;
      const buttons = Array.from(overlay.querySelectorAll('button'));
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const rows = Array.from($('#whSearchResults')?.querySelectorAll('button') || []);
        if (!rows.length) return;
        const current = rows.indexOf(document.activeElement);
        const next = e.key === 'ArrowDown' ? (current + 1) % rows.length : (current - 1 + rows.length) % rows.length;
        e.preventDefault(); rows[next].focus();
      }
      if (e.key === 'Tab') {
        const controls = [$('#whSearchInput'), ...buttons].filter(Boolean);
        const index = controls.indexOf(document.activeElement);
        if ((e.shiftKey && index <= 0) || (!e.shiftKey && index === controls.length - 1)) {
          e.preventDefault(); controls[e.shiftKey ? controls.length - 1 : 0]?.focus();
        }
      }
    });
  }

  async function refresh() {
    const request = ++ui.refreshRequest;
    try {
      const source = window.mcpAssistant || (typeof api === 'undefined' ? null : api);
      const result = await source?.snapshot?.();
      if (request !== ui.refreshRequest) return;
      const snapshot = unwrap(result);
      if (snapshot?.settings) {
        const project = String(snapshot.settings.workspace || '').trim();
        const changed = ui.boundProject === null || S.workspaceKeyOf(ui.boundProject) !== S.workspaceKeyOf(project);
        if (changed && ui.boundProject) { saveCurrentDraft(ui.boundProject); rememberFileEdit(ui.boundProject); }
        ui.snapshot = snapshot;
        syncCanonicalWorkspaceKey();
        if (changed) {
          ui.boundProject = project;
          resetProjectView();
          restoreDraft({ force: true });
        }
      }
    } catch { setStatus('Chưa lấy được trạng thái mới. Dữ liệu đang hiển thị chưa được cập nhật.', 'error'); }
    if (request !== ui.refreshRequest) return;
    renderWorkspace();
    renderProjects();
    renderBasket();
    renderRecipes();
    await Promise.allSettled([loadTask(), renderFiles(), renderGit(), renderGitLog(), renderWorktrees(), renderLspProviders(), renderCoordRuns(), renderSteering(), renderQaList(), renderCosCompanion(), renderCodexChat()]);
    if (request !== ui.refreshRequest) return;
    renderExtended();
    renderGoal();
  }

  // ================= Extended waves (adoption decisions 261022) =================

  // ---- A3/F19/F20: run a saved recipe through the runtime Job lifecycle ----
  const JOB_OUTPUT_LIMIT = 12000;
  const JOB_TERMINAL_STATUSES = new Set(['exited', 'completed', 'complete', 'done', 'failed', 'error', 'terminated', 'killed', 'stopped', 'timeout', 'cancelled', 'canceled']);
  let jobUiUnloaded = false;
  let jobWakeQueue = Promise.resolve();

  function jobOutputText(result) {
    if (!result || typeof result !== 'object') return '';
    if (typeof result.output === 'string') return result.output;
    const parts = [];
    if (typeof result.stdout === 'string' && result.stdout) parts.push(result.stdout);
    if (typeof result.stderr === 'string' && result.stderr) parts.push(result.stderr);
    if (!parts.length && Array.isArray(result.content)) {
      for (const item of result.content) if (item?.type === 'text') parts.push(item.text);
    }
    return parts.join('\n');
  }
  function jobStatusOf(result) {
    const status = String(result?.status || result?.state || '').toLowerCase();
    if (status) return status;
    if (result?.running === true) return 'running';
    if (result?.exit_code != null || result?.exitCode != null) return 'exited';
    return 'unknown';
  }
  function jobIsTerminal(job) {
    return Boolean(job && JOB_TERMINAL_STATUSES.has(job.status));
  }
  function setJobAwake(on) {
    // Keep the order of start/stop IPC calls even when their replies arrive late.
    jobWakeQueue = jobWakeQueue.catch(() => {}).then(async () => {
      if (typeof window.mcpAssistant?.workhubKeepAwake === 'function') {
        await window.mcpAssistant.workhubKeepAwake(Boolean(on) && !jobUiUnloaded);
      }
    }).catch(() => {});
    return jobWakeQueue;
  }
  function jobResult(response) {
    if (response?.ok === false) throw new Error(String(response.error || 'Bộ thực thi không xác nhận thao tác.'));
    const result = unwrap(response);
    if (!result || typeof result !== 'object') throw new Error('Không nhận được trạng thái lệnh từ bộ thực thi.');
    return result;
  }
  function appendJobOutput(job, result) {
    const parts = [];
    let hasStreams = false;
    job.streamEnds ||= {};
    for (const stream of ['stdout', 'stderr']) {
      if (typeof result[stream] !== 'string') continue;
      hasStreams = true;
      let text = result[stream];
      const end = result.output_retention?.[stream]?.total_stream_bytes;
      const previous = job.streamEnds[stream];
      if (Number.isFinite(end)) {
        // The first named consumer can replay the initial exec output. Its
        // stream byte totals let us remove that overlap without dropping later
        // cursor deltas (or repeated lines that the command actually emitted).
        if (Number.isFinite(previous)) {
          if (end <= previous) text = '';
          else if (text && typeof TextEncoder !== 'undefined' && typeof TextDecoder !== 'undefined') {
            const bytes = new TextEncoder().encode(text);
            const overlap = previous - (end - bytes.length);
            if (overlap > 0) text = new TextDecoder().decode(bytes.subarray(Math.min(overlap, bytes.length)));
          }
        }
        job.streamEnds[stream] = Math.max(previous || 0, end);
      }
      if (text) parts.push(text);
    }
    const delta = hasStreams ? parts.join('\n') : jobOutputText(result);
    if (delta) {
      const combined = `${job.output || ''}${delta}`;
      job.outputClipped ||= combined.length > JOB_OUTPUT_LIMIT;
      job.output = combined.slice(-JOB_OUTPUT_LIMIT);
    }
    job.outputIncomplete ||= Boolean(result.output_truncated || result.truncated || result.stdout_truncated || result.stderr_truncated);
  }
  function applyJobResult(job, result) {
    const commandId = String(result.command_id || result.session_id || result.commandId || '');
    if (job.commandId && commandId && commandId !== job.commandId) throw new Error('Bộ thực thi trả về một lần chạy khác; đã dừng cập nhật để tránh nhầm lần chạy.');
    if (commandId) job.commandId = commandId;
    appendJobOutput(job, result);
    job.status = jobStatusOf(result);
    job.exitCode = result.exit_code ?? result.exitCode ?? job.exitCode;
    job.observationError = '';
    if (jobIsTerminal(job)) job.stopRequested = false;
  }
  async function observeJob(job, action, extra = {}) {
    // All actions share the runtime cursor. Serializing also prevents a late
    // poll from overwriting a terminal reply or consuming a write's output.
    const queued = (job.observationQueue || Promise.resolve()).catch(() => {}).then(async () => {
      if (ui.job !== job || jobUiUnloaded || !job.commandId) return false;
      if (action === 'write' && jobIsTerminal(job)) return false;
      if (action === 'kill' && jobIsTerminal(job)) return true;
      try {
        const result = jobResult(await window.mcpAssistant.workhubJobControl({ action, commandId: job.commandId, ...extra }));
        if (ui.job !== job || jobUiUnloaded) return false;
        applyJobResult(job, result);
        renderJob();
        if (jobIsTerminal(job)) setJobAwake(false);
        return true;
      } catch (error) {
        if (ui.job === job) {
          job.status = 'unknown';
          job.observationError = String(error?.message || error).slice(0, 400);
          renderJob();
        }
        setJobAwake(false);
        return false;
      }
    });
    job.observationQueue = queued;
    return queued;
  }
  function renderJob() {
    const box = $('#whJobView');
    const meta = $('#whJobMeta');
    if (!box || !meta) return;
    if (!ui.job) {
      meta.textContent = 'Chưa chạy lệnh nào trong phiên này.';
      box.textContent = 'Chọn “Chạy lệnh” ở một lệnh đã lưu.';
      for (const selector of ['#whJobKill', '#whJobPoll', '#whJobWrite']) { const button = $(selector); if (button) button.disabled = true; }
      return;
    }
    const job = ui.job;
    const labels = { starting: 'Đang gửi lệnh', running: 'Đang chạy', unknown: 'Chưa xác định trạng thái', exited: 'Đã kết thúc', terminated: 'Đã dừng', stopped: 'Đã dừng', timeout: 'Hết thời gian', error: 'Không chạy được' };
    const status = job.stopRequested && !jobIsTerminal(job) ? 'Đã yêu cầu dừng · chờ xác nhận' : (labels[job.status] || job.status);
    meta.textContent = `${job.name} · ${status}${job.workspace ? ` · Dự án: ${job.workspace}` : ''}${job.commandId ? ` · Mã lần chạy: ${job.commandId}` : ''}${job.exitCode != null ? ` · Mã thoát: ${job.exitCode}` : ''}${job.boundRunId ? ` · gắn RUN ${job.boundRunId}` : (job.commandId ? ' · không gắn task' : '')}`;
    const notices = [];
    if (job.observationError) notices.push(job.status === 'error'
      ? `Lệnh chưa được gửi: ${job.observationError}\nBạn có thể chạy lại sau khi khắc phục lỗi.`
      : `Không xác nhận được trạng thái: ${job.observationError}\nLệnh có thể vẫn chạy. Dùng “Lấy kết quả mới” để kiểm tra; không tự chạy lại.`);
    if (job.inputDeliveryError) notices.push(job.inputDeliveryError);
    if (job.outputClipped) notices.push('Đang hiển thị 12.000 ký tự kết quả cuối.');
    if (job.outputIncomplete) notices.push('Bộ thực thi đã rút gọn hoặc không còn giữ một phần kết quả.');
    box.textContent = [job.output || '(chưa có kết quả)', ...notices].join('\n\n');
    const kill = $('#whJobKill');
    const poll = $('#whJobPoll');
    const write = $('#whJobWrite');
    if (kill) kill.disabled = !job.commandId || jobIsTerminal(job) || (job.stopRequested && !job.observationError);
    if (poll) poll.disabled = !job.commandId || job.status === 'starting';
    if (write) write.disabled = !job.commandId || job.status !== 'running' || job.stopRequested || job.inputPending;
  }
  async function runRecipeAsJob(recipe) {
    if (ui.job && !jobIsTerminal(ui.job)) { window.alert('Lần chạy trước đang được gửi, đang chạy hoặc chưa xác định trạng thái. Hãy kiểm tra lần chạy đó trước khi chạy lệnh khác.'); return; }
    const workspace = currentProject();
    const job = { name: recipe.name, workspace, commandId: '', status: 'starting', output: '', exitCode: null, boundRunId: '' };
    ui.job = job;
    renderJob();
    try {
      // P1 (L2): bind the job to the panel's current task RUN when one
      // exists, exactly like send binds the chat link — so the runtime's
      // owner-mismatch guard can refuse a stale scope instead of running
      // silently unbound. No RUN means no binding, shown as such below.
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const runId = task?.orchestration?.run_id || task?.run_id || '';
      const request = { command: recipe.command, cwd: recipe.cwd || workspace, expectedWorkspace: workspace };
      if (runId) request.runId = runId;
      const response = await window.mcpAssistant.workhubJobRun(request);
      if (ui.job !== job || jobUiUnloaded) return;
      if (response?.ok === false) {
        // IPC errors can include a timeout after the runtime admitted a
        // command. Without an explicit pre-dispatch rejection, execution is
        // unknown and must not be silently retried.
        job.status = /MCP chưa sẵn sàng|Lệnh không được trống|Dự án đã thay đổi|OWNER_MISMATCH|không khớp với task/.test(String(response.error || '')) ? 'error' : 'unknown';
        job.observationError = String(response.error || 'Bộ thực thi từ chối lệnh.').slice(0, 400);
      } else {
        const result = jobResult(response);
        job.boundRunId = result && typeof result === 'object' && result.workhubRunBinding && typeof result.workhubRunBinding === 'object'
          ? String(result.workhubRunBinding.runId || '')
          : '';
        applyJobResult(job, result);
      }
    } catch (error) {
      if (ui.job !== job || jobUiUnloaded) return;
      job.status = 'unknown';
      job.observationError = String(error?.message || error).slice(0, 400);
    }
    renderJob();
    if (job.status === 'running' && job.commandId) { setJobAwake(true); pollJobLoop(job); }
  }
  async function pollJobLoop(job = ui.job) {
    if (!job || job.polling || jobUiUnloaded) return;
    job.polling = true;
    try {
      while (ui.job === job && !jobUiUnloaded && job.status === 'running' && job.commandId) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        if (ui.job !== job || jobUiUnloaded || job.status !== 'running') break;
        if (!await observeJob(job, 'poll')) break;
      }
    } finally {
      job.polling = false;
      if (ui.job === job && job.status !== 'running') setJobAwake(false);
    }
  }
  window.addEventListener('pagehide', () => { jobUiUnloaded = true; setJobAwake(false); });

  // ---- A1: context package with real content + versions ----
  async function buildContextPackage() {
    const scope = requestScope('contextPackage');
    const files = store.basketFor(scope.workspace);
    if (!files.length) { setStatus('Giỏ ngữ cảnh đang trống. Hãy chọn tệp trước.'); return; }
    if (!window.mcpAssistant?.workhubRead) { setStatus('Đọc nội dung tệp cần ứng dụng Desktop.', 'error'); return; }
    const preview = $('#whPreview');
    const request = preview?.value || '';
    const parts = [request, `${request ? '\n\n' : ''}Ngữ cảnh dự án: ${scope.workspace}`];
    const limit = 20000;
    let used = parts.join('\n\n').length;
    let included = 0;
    let skipped = 0;
    let shortened = 0;
    const button = $('#whBuildContextBtn');
    if (button) button.disabled = true;
    try {
    for (const file of files) {
      const rel = String(file.path).replace(/\\/g, '/');
      const data = unwrap(await window.mcpAssistant.workhubRead(rel, scope.workspace).catch(() => null));
      if (!scope.current()) return;
      if (!data || data.binary) { skipped += 1; continue; }
      const head = `\n\n--- ${rel} · sha ${String(data.hash || '').slice(0, 12) || 'chưa có'} ---\n`;
      const available = limit - used - head.length - 40;
      if (available <= 0) { skipped += 1; continue; }
      const source = String(data.content || '');
      const content = source.slice(0, available);
      const cut = Boolean(data.truncated) || content.length < source.length;
      const section = `${head}${content}${cut ? '\n… (nội dung đã rút gọn)' : ''}`;
      parts.push(section);
      used += section.length;
      included += 1;
      if (cut) shortened += 1;
    }
    if (!scope.current()) return;
    if (preview?.value !== request) { setStatus('Yêu cầu đã được sửa trong lúc đọc tệp. Bấm tạo gói lần nữa để dùng nội dung mới.'); return; }
    if (!included) { setStatus('Chưa thêm được nội dung: tệp không đọc được, là tệp nhị phân hoặc yêu cầu đã hết chỗ.', 'error'); return; }
    if (preview) { preview.value = parts.join(''); saveCurrentDraft(); showRequestDraft(); }
    setStatus(`Đã thêm ${included} tệp vào yêu cầu · ${shortened} tệp rút gọn · ${skipped} tệp bỏ qua. Tối đa 20.000 ký tự.`);
    } finally { if (button) button.disabled = false; }
  }

  // ---- F17 plan + F18 steering ----
  function renderPlan() {
    const box = $('#whPlan');
    if (!box) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const plan = S.planView(task);
    if (!plan) { box.replaceChildren(el('span', 'task-muted', 'Chưa có task để trình bày kế hoạch.')); return; }
    box.replaceChildren();
    box.append(el('p', '', `${plan.doneCount}/${plan.steps.length} bước xong · ${plan.testsRun} lần kiểm tra đã ghi nhận, ${plan.testsFailed} lần có lỗi${plan.detailsAvailable ? '' : ' · Chưa lấy được đầy đủ chi tiết'}`));
    for (const step of plan.steps) box.append(el('div', 'wh-row', `${step.done ? '✓' : '•'} ${step.text} (${step.status})`));
    for (const blocker of plan.blockers) box.append(el('div', 'wh-row', `⛔ ${blocker}`));
  }
  function renderFeedback() {
    const box = $('#whFeedbackList');
    if (!box) return;
    const items = store.listFeedback(currentProject());
    if (!items.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có điều chỉnh nào.')); return; }
    box.replaceChildren(...items.slice().reverse().map((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      const stateLabel = { saved: 'Đã lưu (chỉ ở máy này)', copied: 'Đã sao chép để chuyển', acknowledged: 'Đã đánh dấu controller xác nhận' }[item.state];
      main.append(el('b', '', item.text), el('small', '', stateLabel));
      row.append(main);
      if (item.state === 'saved') {
        const copy = smallButton('Sao chép');
        copy.addEventListener('click', (e) => { copyText(item.text, e.currentTarget); store.setFeedbackState(currentProject(), item.id, 'copied'); renderFeedback(); });
        row.append(copy);
      }
      if (item.state === 'copied') {
        const ack = smallButton('Đánh dấu đã xác nhận');
        ack.addEventListener('click', () => { store.setFeedbackState(currentProject(), item.id, 'acknowledged'); renderFeedback(); });
        row.append(ack);
      }
      return row;
    }));
  }

  // ---- F02 drafts ----
  function renderDraftState() {
    const box = $('#whDraftState');
    if (!box) return;
    const draft = store.getDraft(currentProject());
    box.textContent = persistenceError || (!currentProject() ? 'Chọn dự án để bật tự lưu nháp.' : draft ? `Đã lưu nháp lúc ${new Date(draft.updatedAt).toLocaleTimeString('vi-VN')} · chỉ trong dự án này.` : 'Yêu cầu đang soạn được tự lưu theo dự án.');
  }
  function restoreDraft({ force = false } = {}) {
    const draft = store.getDraft(currentProject());
    const preview = $('#whPreview');
    if (force) {
      ui.selectedType = S.TASK_TYPES[draft?.type] ? draft.type : 'bugfix';
      ui.selectedPromptId = draft?.promptId || '';
      if ($('#whTaskType')) $('#whTaskType').value = ui.selectedType;
      renderTypeFields(draft?.fields || {});
      renderPromptOptions();
      if (preview) preview.value = draft?.text || '';
    }
    renderDraftState();
  }

  // ---- F15 queue + F24 schedules ----
  function renderQueue() {
    const box = $('#whQueueList');
    if (!box) return;
    const queue = store.queueFor(currentProject());
    const toggle = $('#whQueuePaused');
    if (toggle) toggle.checked = queue.paused;
    if (!queue.items.length) { box.replaceChildren(el('span', 'task-muted', 'Hàng đợi trống.')); return; }
    box.replaceChildren(...queue.items.map((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', item.title), el('small', '', item.status));
      row.append(main);
      const up = smallButton('↑');
      up.addEventListener('click', () => { store.moveQueueItem(currentProject(), item.id, -1); renderQueue(); });
      const down = smallButton('↓');
      down.addEventListener('click', () => { store.moveQueueItem(currentProject(), item.id, 1); renderQueue(); });
      row.append(up, down);
      if (item.status === 'queued') {
        const start = smallButton('Bắt đầu');
        start.addEventListener('click', () => {
          store.setQueueItemStatus(currentProject(), item.id, 'running');
          const preview = $('#whPreview');
          if (preview) preview.value = item.text || item.title;
          renderQueue();
        });
        row.append(start);
      }
      if (item.status === 'running') {
        const done = smallButton('Xong');
        done.addEventListener('click', () => { store.setQueueItemStatus(currentProject(), item.id, 'done'); renderQueue(); });
        row.append(done);
      }
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeQueueItem(currentProject(), item.id); renderQueue(); });
      row.append(remove);
      return row;
    }));
  }
  function renderSchedules() {
    const box = $('#whScheduleList');
    if (!box) return;
    const select = $('#whScheduleRecipe');
    if (select) {
      const currentValue = select.value;
      select.replaceChildren(...store.listRecipes().map((r) => { const opt = document.createElement('option'); opt.value = r.id; opt.textContent = r.name; return opt; }));
      if (currentValue) select.value = currentValue;
    }
    const schedules = store.listSchedules();
    if (!schedules.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có lịch nào. Lịch chỉ được xét khi ứng dụng đang mở.')); return; }
    box.replaceChildren(...schedules.map((schedule) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      const recipe = store.listRecipes().find((r) => r.id === schedule.recipeId);
      main.append(el('b', '', schedule.name), el('small', '', `${recipe?.name || 'lệnh đã xóa'} · mỗi ${schedule.intervalHours}h · lần kế: ${new Date(store.nextRunAt(schedule)).toLocaleString('vi-VN')}${schedule.enabled ? '' : ' · đang tắt'}`));
      row.append(main);
      const run = smallButton('Chạy ngay');
      run.addEventListener('click', () => { if (recipe) { store.markScheduleRun(schedule.id); runRecipeAsJob(recipe); renderSchedules(); } });
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeSchedule(schedule.id); renderSchedules(); });
      row.append(run, remove);
      return row;
    }));
    const due = store.dueSchedules();
    if (due.length) box.append(el('span', 'task-muted', `${due.length} lịch đã đến hạn — bấm "Chạy ngay" ở lịch tương ứng để chạy qua Job.`));
  }

  // ---- F32 notes / F34 skills / F39 chats / F40 ssh ----
  function simpleList(box, items, renderItem) {
    if (!box) return;
    if (!items.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có mục nào.')); return; }
    box.replaceChildren(...items.map(renderItem));
  }
  function renderNotes() {
    simpleList($('#whNoteList'), store.listNotes(currentProject()), (note) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', `${note.pinned ? '📌 ' : ''}${note.title}`), el('small', '', note.body.slice(0, 120)));
      row.append(main);
      const add = smallButton('Đưa vào yêu cầu');
      add.addEventListener('click', () => {
        const preview = $('#whPreview');
        if (preview) preview.value = `${preview.value ? `${preview.value}\n` : ''}[Ghi chú dự án] ${note.title}: ${note.body}`;
      });
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeNote(currentProject(), note.id); renderNotes(); });
      row.append(add, remove);
      return row;
    });
  }
  function renderSkills() {
    simpleList($('#whSkillList'), store.listSkills(), (skill) => {
      const active = store.skillsForProject(currentProject()).some((s) => s.id === skill.id);
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      const shaLabel = skill.sha256 ? `sha256 ${skill.sha256.slice(0, 12)}…` : 'sha256: đang tính…';
      const usedLabel = skill.lastUsedAt ? ` · đã dùng ${new Date(skill.lastUsedAt).toLocaleString()} tại ${skill.lastUsedProject || 'dự án'}` : ' · chưa có consumer dùng';
      main.append(el('b', '', skill.name), el('small', '', `${skill.source} · rev ${skill.revision || 1} · ${shaLabel} · ${active ? 'đang bật cho dự án này' : 'chưa bật cho dự án này'}${usedLabel}`));
      row.append(main);
      if (!skill.sha256 && window.mcpAssistant?.workhubSha256) {
        window.mcpAssistant.workhubSha256(skill.content).then((sha) => {
          const value = unwrap(sha);
          if (value) { store.setSkillSha(skill.id, value); renderSkills(); }
        }).catch(() => null);
      }
      const toggle = smallButton(active ? 'Tắt' : 'Bật cho dự án');
      toggle.addEventListener('click', () => { store.setSkillForProject(skill.id, currentProject(), !active); renderSkills(); });
      const add = smallButton('Đưa vào yêu cầu');
      add.addEventListener('click', () => {
        const preview = $('#whPreview');
        if (preview) preview.value = `${preview.value ? `${preview.value}\n` : ''}[Skill: ${skill.name}]\n${skill.content}`;
        store.markSkillUsed(skill.id, currentProject());
        renderSkills();
      });
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeSkill(skill.id); renderSkills(); });
      row.append(toggle, add, remove);
      return row;
    });
  }
  function renderChats() {
    simpleList($('#whChatList'), store.listChats(currentProject()), (chat) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', `${chat.pinned ? '📌 ' : ''}${chat.label}`), el('small', '', chat.note || chat.url || ''));
      row.append(main);
      if (chat.url) {
        const open = smallButton('Mở');
        open.addEventListener('click', () => window.mcpAssistant?.openExternal?.(chat.url));
        row.append(open);
      }
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeChat(currentProject(), chat.id); renderChats(); });
      row.append(remove);
      return row;
    });
  }
  function renderSshTargets() {
    simpleList($('#whSshList'), store.listSshTargets(), (target) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      const fpLabel = target.fingerprint ? ` · ${target.fingerprint}` : ' · chưa ghim vân tay host';
      main.append(el('b', '', target.name), el('small', '', `${target.user ? `${target.user}@` : ''}${target.host}:${target.port}${target.remoteDir ? ` · ${target.remoteDir}` : ''}${fpLabel}`));
      row.append(main);
      const scan = smallButton('Quét & ghim vân tay');
      scan.addEventListener('click', async () => {
        const out = $('#whSshOutput');
        if (out) out.textContent = `Đang quét host key của ${target.host}…`;
        const data = unwrap(await window.mcpAssistant?.workhubSshScan?.({ host: target.host, port: target.port }).catch(() => null));
        if (!data) { if (out) out.textContent = 'Quét vân tay thất bại.'; return; }
        store.upsertSshTarget({ id: target.id, name: target.name, host: target.host, user: target.user, port: target.port, remoteDir: target.remoteDir, fingerprint: data.fingerprint });
        if (out) out.textContent = `Đã ghim ${data.fingerprint} (${data.keyType}).`;
        renderSshTargets();
      });
      const check = smallButton('Chạy kiểm tra');
      check.addEventListener('click', async () => {
        const out = $('#whSshOutput');
        if (out) out.textContent = 'Đang kiểm tra SSH (ghim vân tay, StrictHostKeyChecking)…';
        const scope = requestScope('ssh');
        const data = unwrap(await window.mcpAssistant?.workhubSshTest?.({
          host: target.host, port: target.port, user: target.user, remoteDir: target.remoteDir,
          expectedFingerprint: target.fingerprint || '', expectedWorkspace: scope.workspace,
        }).catch((error) => ({ error: String(error?.message || error) })));
        if (!scope.current()) return;
        if (!out) return;
        if (!data) { out.textContent = 'Kiểm tra thất bại (không có phản hồi).'; return; }
        if (data.error) { out.textContent = `Từ chối: ${data.error}`; return; }
        out.textContent = `${data.ok ? 'OK' : `exit ${data.exitCode}`} · ${data.fingerprint}${data.pinned ? ' · khớp vân tay đã ghim' : ' · CHƯA ghim vân tay'}\n${data.stdout || ''}${data.stderr ? `\n[stderr] ${data.stderr}` : ''}`;
      });
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeSshTarget(target.id); renderSshTargets(); });
      row.append(scan, check, remove);
      return row;
    });
  }

  // ---- F16 task board + F21 lanes ----
  async function renderTaskBoard() {
    const box = $('#whTaskBoard');
    if (!box) return;
    const scope = requestScope('taskboard');
    const rows = [];
    const current = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if (current) rows.push({ title: current.objective || 'Task hiện tại', status: current.status || '', current: true });
    const history = unwrap(await window.mcpAssistant?.taskHistory?.().catch(() => null));
    if (!scope.current()) return;
    for (const item of Array.isArray(history) ? history.slice(-12).reverse() : []) {
      rows.push({ title: item.objective || item.task_id || 'Task', status: item.status || '', current: false });
    }
    if (!rows.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có task nào trong ledger.')); return; }
    box.replaceChildren(...rows.map((item) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.append(el('b', '', `${item.current ? '▶ ' : ''}${item.title}`), el('small', '', item.status));
      row.append(main);
      if (item.current) {
        const open = smallButton('Mở Tác vụ');
        open.addEventListener('click', () => window.navigate?.('task'));
        row.append(open);
      }
      return row;
    }));
  }
  async function renderWorkers() {
    const box = $('#whWorkerList');
    if (!box) return;
    const scope = requestScope('workers');
    const data = unwrap(await window.mcpAssistant?.orchestration?.().catch(() => null));
    if (!scope.current()) return;
    const payload = data?.data || data || {};
    const clients = Array.isArray(payload.clients) ? payload.clients : [];
    const delegations = Array.isArray(payload.delegations) ? payload.delegations : [];
    if (!clients.length && !delegations.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có dữ liệu điều phối (delegation/client) từ runtime.')); return; }
    const rows = [];
    // W2 (§5.2): label the source explicitly — everything here comes from
    // the EOCL orchestration runtime of this workspace. CoS-observed
    // sessions live in the companion panel and are never listed as workers.
    for (const client of clients) rows.push(`EOCL · Client ${client.client_id || client.client_type || ''} · ${client.online ? 'online' : 'offline'}`);
    for (const lane of delegations) rows.push(`EOCL · Delegation ${lane.lane || lane.id || ''} · ${lane.status || ''} · ${lane.objective || lane.summary || ''}`);
    box.replaceChildren(...rows.map((text) => el('div', 'wh-row', text)));
  }

  // ---- F33 targets + F36 integration inventory ----
  async function renderTargets() {
    const box = $('#whTargetList');
    if (!box) return;
    const scope = requestScope('targets');
    const rows = [];
    const local = scope.workspace;
    if (local) rows.push({ label: `Máy này · ${local}`, action: null });
    const workspaces = unwrap(await window.mcpAssistant?.listControlPlaneWorkspaces?.().catch(() => null));
    if (!scope.current()) return;
    const list = workspaces?.workspaces || workspaces?.items || (Array.isArray(workspaces) ? workspaces : []);
    for (const ws of list) {
      rows.push({ label: `${ws.name || ws.id || 'workspace'} · ${ws.path || ws.workspace || ''} · ${ws.status || ws.state || ''}`, action: null });
    }
    if (!rows.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có máy/dự án nào được đăng ký.')); return; }
    box.replaceChildren(...rows.map((item) => el('div', 'wh-row', item.label)));
  }
  function renderIntegrations() {
    const box = $('#whIntegrationList');
    if (!box) return;
    const settings = ui.snapshot?.settings || {};
    const status = ui.snapshot?.status || {};
    const rows = [
      `MCP runtime · ${status.runtimeRunning ? 'đang chạy' : 'chưa rõ trạng thái'}`,
      `Chế độ thực thi · ${settings.executionMode || 'local'} (cấu hình đã lưu)`,
      `Control Plane · ${settings.controlPlaneServerUrl || 'chưa cấu hình'}`,
      `Work Hub Job · qua exec_command/command_control của runtime (không phải executor riêng)`,
    ];
    box.replaceChildren(...rows.map((text) => el('div', 'wh-row', text)));
  }

  function renderExtended() {
    renderPlan();
    renderFeedback();
    renderDraftState();
    restoreDraft();
    renderQueue();
    renderSchedules();
    renderNotes();
    renderSkills();
    renderChats();
    renderSshTargets();
    renderIntegrations();
    renderTaskBoard();
    renderWorkers();
    renderTargets();
    renderPatchApproval();
    renderJob();
    // F24: surface due schedules via the deduped notification gate.
    for (const schedule of store.dueSchedules()) {
      if (typeof Notification !== 'undefined' && Notification.permission === 'granted' && store.claimNotification(`schedule:${schedule.id}:${Math.floor(Date.now() / 3600000)}`)) {
        try { new Notification('Codex Hub — lịch kiểm tra đến hạn', { body: schedule.name }); } catch { /* ignore */ }
      }
    }
  }

  function bindExtended() {
    $('#whBuildContextBtn')?.addEventListener('click', buildContextPackage);
    $('#whPreview')?.addEventListener('input', () => saveCurrentDraft());
    $('#whClearDraft')?.addEventListener('click', () => { store.clearDraft(currentProject()); $('#whPreview').value = ''; renderTypeFields(); renderDraftState(); setStatus('Đã xóa nháp của dự án này.'); });
    $('#whRecipeUrl')?.closest('form')?.addEventListener('submit', (e) => e.preventDefault());
    $('#whJobKill')?.addEventListener('click', async () => {
      const job = ui.job;
      if (!job?.commandId || jobIsTerminal(job) || (job.stopRequested && !job.observationError)) return;
      job.stopRequested = true;
      job.observationError = '';
      renderJob();
      const observed = await observeJob(job, 'kill');
      if (observed && ui.job === job && job.status === 'running') { setJobAwake(true); pollJobLoop(job); }
    });
    $('#whJobPoll')?.addEventListener('click', async () => {
      const job = ui.job;
      if (!job?.commandId || job.status === 'starting') return;
      const observed = await observeJob(job, 'poll');
      if (observed && ui.job === job && job.status === 'running') { setJobAwake(true); pollJobLoop(job); }
    });
    $('#whJobWrite')?.addEventListener('click', async () => {
      const input = $('#whJobInput');
      const chars = input?.value || '';
      const job = ui.job;
      if (!job?.commandId || !chars || job.inputPending || job.status !== 'running' || job.stopRequested) return;
      // Local command_control has no input_id: if the ACK is lost we do NOT
      // auto-resend. Preserve the draft so the user can inspect output first.
      job.inputPending = true;
      renderJob();
      const observed = await observeJob(job, 'write', { chars });
      job.inputPending = false;
      if (ui.job !== job) return;
      if (observed) {
        job.inputDeliveryError = '';
        if (input.value === chars) input.value = '';
      } else {
        job.inputDeliveryError = jobIsTerminal(job)
          ? 'Lệnh đã kết thúc trước khi gửi nội dung. Nội dung vẫn được giữ.'
          : 'Chưa xác nhận được nội dung đã tới lệnh. Nội dung vẫn được giữ; hãy lấy kết quả mới trước khi quyết định gửi lại.';
      }
      renderJob();
    });
    $('#whEditFile')?.addEventListener('click', () => {
      const viewer = $('#whViewer');
      const editor = $('#whEditor');
      if (!viewer || !editor || !ui.viewerRel || !ui.viewerEditable || ui.viewerContent === null) return;
      editor.value = ui.viewerContent;
      editor.hidden = false;
      viewer.hidden = true;
      $('#whSaveFile').disabled = false;
      if ($('#whCancelEditFile')) $('#whCancelEditFile').hidden = false;
      editor.focus();
    });
    $('#whCancelEditFile')?.addEventListener('click', () => {
      if (ui.savingFile) { setStatus('Đang lưu tệp. Chờ xác nhận trước khi hủy sửa.'); return; }
      fileDrafts.delete(fileDraftKey(currentProject(), ui.viewerRel));
      $('#whEditor').hidden = true;
      $('#whViewer').hidden = false;
      $('#whSaveFile').disabled = true;
      $('#whCancelEditFile').hidden = true;
      setStatus('Đã hủy phần sửa tệp.');
    });
    $('#whSaveFile')?.addEventListener('click', async () => {
      const editor = $('#whEditor');
      if (!editor || editor.hidden || !ui.viewerRel || !ui.viewerEditable || ui.savingFile) return;
      const scope = requestScope('viewer');
      const rel = ui.viewerRel;
      const content = editor.value;
      const hash = ui.viewerHash;
      const save = $('#whSaveFile');
      ui.savingFile = true;
      save.disabled = true;
      let message = '';
      const result = await window.mcpAssistant.workhubWrite(rel, content, hash, scope.workspace).catch((error) => { message = error.message; return null; });
      const data = unwrap(result);
      ui.savingFile = false;
      if (data) fileDrafts.delete(fileDraftKey(scope.workspace, rel));
      if (!scope.current()) return;
      save.disabled = false;
      if (!data) { setStatus(message || 'Không lưu được — tệp có thể đã đổi trên đĩa. Phần sửa vẫn được giữ; sao chép nội dung trước khi tải lại tệp.', 'error'); return; }
      ui.viewerHash = data.hash;
      ui.viewerContent = content;
      if (editor.value !== content) { setStatus('Đã lưu. Bạn có phần sửa mới sau lúc bấm lưu; hãy lưu thêm lần nữa.'); return; }
      editor.hidden = true;
      await openFile(rel);
      if (scope.workspace === currentProject()) setStatus('Đã lưu tệp.');
    });
    $('#whBlame')?.addEventListener('click', async () => {
      if (!ui.viewerRel || !canLeaveFileEdit()) return;
      const scope = requestScope('viewer');
      const data = unwrap(await window.mcpAssistant.workhubGitBlame(ui.viewerRel, scope.workspace).catch(() => null));
      if (!scope.current()) return;
      const viewer = $('#whViewer');
      if (viewer) viewer.textContent = data ? data.lines.map((l) => `${l.line} · ${l.author} · ${l.text}`).join('\n') : 'Không lấy được blame.';
    });
    $('#whGitLogRefresh')?.addEventListener('click', renderGitLog);
    $('#whGitReviewRun')?.addEventListener('click', renderGitReview);
    for (const id of ['whGitReviewFrom', 'whGitReviewTo']) $(`#${id}`)?.addEventListener('keydown', (event) => { if (event.key === 'Enter') renderGitReview(); });
    $('#whWorktreeRefresh')?.addEventListener('click', renderWorktrees);
    $('#whWorktreeAdd')?.addEventListener('click', addWorktree);
    $('#whChooseImport')?.addEventListener('click', async () => {
      const scope = requestScope('importChooser');
      const files = unwrap(await window.mcpAssistant.chooseFiles().catch(() => null)) || [];
      if (!scope.current()) return;
      ui.pendingImports = files;
      renderImports();
    });
    $('#whRunImports')?.addEventListener('click', async () => {
      if (ui.importing) return;
      const scope = requestScope('import');
      const sources = ui.pendingImports.slice();
      const dest = $('#whImportDest')?.value || '';
      const results = [];
      ui.importing = true;
      $('#whRunImports').disabled = true;
      try {
      for (const source of sources) {
        if (!scope.current()) return;
        try {
          const copied = unwrap(await window.mcpAssistant.workhubCopyIn(source, dest, scope.workspace));
          if (!copied) throw new Error('Không nhận được xác nhận nhập tệp.');
          results.push({ source, ok: true, dest: copied?.rel || '' });
        } catch (error) {
          results.push({ source, ok: false, error: error?.message || 'không rõ lỗi' });
        }
      }
      if (!scope.current()) return;
      // Keep only the failures queued so the user can retry them; report
      // every file's outcome instead of clearing the list silently.
      ui.pendingImports = results.filter((r) => !r.ok).map((r) => r.source);
      ui.importResults = results;
      renderImports();
      renderFiles();
      } finally { ui.importing = false; $('#whRunImports').disabled = false; }
    });
    $('#whSaveSnippet')?.addEventListener('click', async () => {
      if (ui.savingSnippet) return;
      const scope = requestScope('snippet');
      const name = String($('#whSnippetName')?.value || '').trim();
      const content = $('#whSnippetBody')?.value || '';
      if (!name) { window.alert('Nhập tên tệp cho đoạn code.'); return; }
      const rel = ui.dirRel ? `${ui.dirRel}/${name}` : name;
      ui.savingSnippet = true;
      const result = await window.mcpAssistant.workhubWrite(rel, content, null, scope.workspace).catch(() => null);
      ui.savingSnippet = false;
      if (!scope.current()) return;
      if (!unwrap(result)) { window.alert('Không tạo được tệp — có thể tệp đã tồn tại (ghi đè cần mở tệp và dùng Sửa nhanh).'); return; }
      renderFiles();
    });
    $('#whFeedbackAdd')?.addEventListener('click', () => {
      try { store.addFeedback(currentProject(), $('#whFeedbackText').value); $('#whFeedbackText').value = ''; renderFeedback(); }
      catch (error) { window.alert(error.message); }
    });
    $('#whQueueAdd')?.addEventListener('click', () => {
      try {
        store.enqueue(currentProject(), { title: $('#whQueueTitle').value, text: $('#whPreview').value || $('#whQueueTitle').value });
        $('#whQueueTitle').value = '';
        renderQueue();
      } catch (error) { window.alert(error.message); }
    });
    $('#whQueuePaused')?.addEventListener('change', (e) => { store.setQueuePaused(currentProject(), e.target.checked); renderQueue(); });
    $('#whQueueStartNext')?.addEventListener('click', () => {
      const next = store.nextQueuedItem(currentProject());
      if (!next) { window.alert('Không có việc đang chờ (hoặc hàng đợi đang tạm dừng).'); return; }
      store.setQueueItemStatus(currentProject(), next.id, 'running');
      const preview = $('#whPreview');
      if (preview) { preview.value = next.text || next.title; saveCurrentDraft(); activateTab('context'); }
      renderQueue();
    });
    $('#whScheduleAdd')?.addEventListener('click', () => {
      try {
        store.upsertSchedule({ name: $('#whScheduleName').value, recipeId: $('#whScheduleRecipe').value, intervalHours: Number($('#whScheduleHours').value) || 24 });
        renderSchedules();
      } catch (error) { window.alert(error.message); }
    });
    $('#whGoalSave')?.addEventListener('click', () => {
      try {
        store.setGoalPrep(currentProject(), { criteria: $('#whGoalCriteria').value, maxTurns: Number($('#whGoalTurns').value) || 5, maxMinutes: Number($('#whGoalMinutes').value) || 60 });
        renderGoal();
      } catch (error) { window.alert(error.message); }
    });
    $('#whGoalBuild')?.addEventListener('click', () => {
      const prep = store.goalPrepFor(currentProject());
      const preview = $('#whPreview');
      if (prep && preview) { preview.value = S.goalRequestText(currentProject(), prep); saveCurrentDraft(); activateTab('context'); }
    });
    $('#whGoalClear')?.addEventListener('click', () => { store.clearGoalPrep(currentProject()); renderGoal(); });
    $('#whNoteAdd')?.addEventListener('click', () => {
      try { store.upsertNote(currentProject(), { title: $('#whNoteTitle').value, body: $('#whNoteBody').value }); $('#whNoteTitle').value = ''; $('#whNoteBody').value = ''; renderNotes(); }
      catch (error) { window.alert(error.message); }
    });
    $('#whSkillAdd')?.addEventListener('click', () => {
      try { store.upsertSkill({ name: $('#whSkillName').value, content: $('#whSkillBody').value, source: 'local' }); $('#whSkillName').value = ''; $('#whSkillBody').value = ''; renderSkills(); }
      catch (error) { window.alert(error.message); }
    });
    $('#whChatAdd')?.addEventListener('click', () => {
      try { store.upsertChat(currentProject(), { label: $('#whChatLabel').value, url: $('#whChatUrl').value }); $('#whChatLabel').value = ''; $('#whChatUrl').value = ''; renderChats(); }
      catch (error) { window.alert(error.message); }
    });
    $('#whSshAdd')?.addEventListener('click', () => {
      try {
        store.upsertSshTarget({ name: $('#whSshName').value, host: $('#whSshHost').value, user: $('#whSshUser').value, port: Number($('#whSshPort').value) || 22, remoteDir: $('#whSshDir').value });
        renderSshTargets();
      } catch (error) { window.alert(error.message); }
    });
    $('#whExportReport')?.addEventListener('click', () => {
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const text = S.buildReportText(task);
      if (!text) { window.alert('Chưa có task để xuất báo cáo.'); return; }
      const blob = new Blob([text], { type: 'text/markdown' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'bao-cao-tac-vu.md';
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 5000);
    });
    $('#whReadCapsule')?.addEventListener('click', async () => {
      const scope = requestScope('capsule');
      const box = $('#whCapsuleView');
      if (!box) return;
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const runId = S.taskRunId(task);
      box.replaceChildren();
      // Never query without an exact run id: the runtime falls back to the
      // latest capsule overall, which could belong to another task.
      if (!runId) {
        box.appendChild(el('p', 'task-muted', 'Chưa xác định được lần chạy của công việc hiện tại. Hãy mở trang Tác vụ để lấy trạng thái trước khi đọc bản bàn giao.'));
        return;
      }
      box.appendChild(el('span', 'task-muted', 'Đang đọc bản bàn giao…'));
      const result = unwrap(await window.mcpAssistant.workhubHandoffGet({ runId }).catch((error) => ({ error: error.message })));
      if (!scope.current()) return;
      const view = S.capsuleView(result?.capsule || null);
      box.replaceChildren();
      if (!view) {
        box.appendChild(el('p', 'task-muted', result?.recommended_next_action || 'Chưa có bản bàn giao cho lần chạy này. Hãy tạo từ trang Tác vụ trước khi chuyển hội thoại.'));
        return;
      }
      if (view.runId && view.runId !== runId) {
        box.appendChild(el('p', 'task-muted', 'Bản bàn giao trả về thuộc lần chạy khác. Hãy làm mới công việc trước khi tiếp tục.'));
        return;
      }
      const head = el('div', 'wh-row');
      head.appendChild(el('b', '', `Bản bàn giao ${view.capsuleId.slice(0, 12)} · v${view.version ?? '?'}`));
      head.appendChild(el('span', 'soft-badge', view.status));
      box.appendChild(head);
      box.appendChild(el('p', '', `Mục tiêu khi ghi: ${view.objective || '—'}`));
      if (view.panelSummary) box.appendChild(el('p', 'task-muted', `Tóm tắt panel: ${view.panelSummary}`));
      box.appendChild(el('p', 'task-muted', `Ghi lúc ${view.createdAt || '—'} · run ${view.runId || '—'} · sha256 ${view.sha256.slice(0, 12)}…`));
      // Revalidate the capsule against the CURRENT workspace state.
      // workhubGitLog takes a numeric limit and returns the commit array.
      const checks = [];
      if (view.baseHead) {
        const log = unwrap(await window.mcpAssistant.workhubGitLog(1, scope.workspace).catch(() => null));
        if (!scope.current()) return;
        const currentHead = Array.isArray(log) ? String(log[0]?.hash || '') : '';
        const matched = S.headMatches(view.baseHead, currentHead);
        checks.push(matched === null
          ? `HEAD: capsule ${view.baseHead.slice(0, 8)} — không đọc được HEAD hiện tại để đối chiếu.`
          : `HEAD: capsule ${view.baseHead.slice(0, 8)} vs hiện tại ${currentHead.slice(0, 8)} — ${matched ? 'KHỚP' : 'ĐÃ ĐỔI (cần xem lại diff kể từ base)'}`);
      }
      checks.push(`Trạng thái task khi ghi: ${view.taskStatus || '—'}; hiện tại: ${task?.status || '—'}.`);
      for (const line of checks) box.appendChild(el('p', 'task-muted', line));
      if (result?.recommended_next_action) box.appendChild(el('p', 'task-muted', result.recommended_next_action));
      const useBtn = el('button', 'secondary-button wh-small', 'Soạn yêu cầu tiếp tục');
      useBtn.addEventListener('click', () => {
        const text = [
          `Tiếp tục từ capsule ${view.capsuleId} (run ${view.runId}).`,
          view.objective ? `Mục tiêu: ${view.objective}` : '',
          view.panelSummary ? `Tóm tắt: ${view.panelSummary}` : '',
          checks.map((line) => `- ${line}`).join('\n'),
          'Không phát lại transcript cũ; tiếp tục từ trạng thái đã kiểm tra ở trên.',
        ].filter(Boolean).join('\n');
        const preview = $('#whPreview');
        if (preview) preview.value = text;
        saveCurrentDraft();
        activateTab('context');
      });
      box.appendChild(useBtn);
    });
    $('#whRevalidate')?.addEventListener('click', async () => {
      const scope = requestScope('revalidate');
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const files = S.taskFiles(task || {});
      const lines = [];
      for (const path of files) {
        const data = unwrap(await window.mcpAssistant.workhubRead(path.replace(/\\/g, '/'), scope.workspace).catch(() => null));
        if (!scope.current()) return;
        lines.push(data ? `Còn trên đĩa: ${path} (${data.size} bytes)` : `KHÔNG còn đọc được: ${path}`);
      }
      const git = unwrap(await window.mcpAssistant.workhubGitStatus(scope.workspace).catch(() => null));
      if (!scope.current()) return;
      lines.push(git ? `Git hiện có ${git.length} thay đổi chưa commit.` : 'Không đọc được trạng thái Git.');
      const viewer = $('#whHandoffView');
      if (viewer) viewer.textContent = `${viewer.textContent}\n\n[Kiểm tra lại ${new Date().toLocaleTimeString('vi-VN')}]\n${lines.join('\n')}`;
    });
    $('#whVoiceBtn')?.addEventListener('click', () => {
      const scope = requestScope('voice');
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const status = $('#whVoiceStatus');
      if (!Recognition) { if (status) status.textContent = 'Engine giọng nói không có trong môi trường này — nhập bằng bàn phím.'; return; }
      const recognition = new Recognition();
      recognition.lang = 'vi-VN';
      recognition.onresult = (event) => {
        if (!scope.current()) return;
        const text = event.results?.[0]?.[0]?.transcript || '';
        const preview = $('#whPreview');
        if (preview && text) { preview.value = `${preview.value ? `${preview.value} ` : ''}${text}`; saveCurrentDraft(); }
        if (status) status.textContent = 'Đã chuyển thành chữ — kiểm tra và sửa trước khi dùng.';
      };
      recognition.onerror = () => { if (status && scope.current()) status.textContent = 'Không ghi âm được (engine từ chối hoặc không có micro).'; };
      if (status) status.textContent = 'Đang nghe…';
      recognition.start();
    });
    $('#whCosRefresh')?.addEventListener('click', () => renderCosCompanion());
    $('#whCodexChatSend')?.addEventListener('click', () => sendCodexChat());
    $('#whCodexChatPoll')?.addEventListener('click', () => { const scope = requestScope('codex-chat'); pollCodexChatTurn(scope); });
    $('#whCodexChatStop')?.addEventListener('click', async () => {
      stopCodexChatPolling();
      const scope = requestScope('codex-chat');
      const result = unwrap(await window.mcpAssistant.workhubCodexChatInterrupt({ expectedWorkspace: scope.workspace }).catch(() => null));
      if (scope.current() && result?.data) paintCodexChat(result.data);
    });
    $('#whCodexChatNew')?.addEventListener('click', async () => {
      stopCodexChatPolling();
      const scope = requestScope('codex-chat');
      const result = unwrap(await window.mcpAssistant.workhubCodexChatReset({ expectedWorkspace: scope.workspace }).catch(() => null));
      if (scope.current() && result?.data) paintCodexChat(result.data);
      renderCodexChat();
    });
    $('#whCodexChatHandoff')?.addEventListener('click', () => handoffCodexChat());
    $('#whWindowsBtn')?.addEventListener('click', async () => {
      const data = unwrap(await window.mcpAssistant.workhubListWindows().catch(() => null));
      const box = $('#whWindowsList');
      if (!box) return;
      if (!data?.supported) { box.replaceChildren(el('span', 'task-muted', 'Chỉ hỗ trợ liệt kê cửa sổ trên Windows; tự động thao tác GUI cần adapter riêng — chưa bật.')); return; }
      box.replaceChildren(...data.windows.map((w) => el('div', 'wh-row', `${w.process} · ${w.title}`)));
    });
  }

  function renderGoal() {
    const box = $('#whGoalState');
    if (!box) return;
    const prep = store.goalPrepFor(currentProject());
    box.textContent = prep
      ? `Đã chuẩn bị: "${prep.criteria}" · tối đa ${prep.maxTurns} lượt / ${prep.maxMinutes} phút. Đây là bản chuẩn bị yêu cầu — vòng lặp chỉ chạy khi controller/grant của runtime cho phép.`
      : 'Chưa chuẩn bị mục tiêu nào cho dự án này.';
  }

  function renderImports() {
    const box = $('#whImportList');
    if (!box) return;
    box.replaceChildren();
    if (Array.isArray(ui.importResults) && ui.importResults.length) {
      const okCount = ui.importResults.filter((r) => r.ok).length;
      box.appendChild(el('p', '', `Kết quả nhập: ${okCount}/${ui.importResults.length} tệp thành công.`));
      for (const r of ui.importResults) {
        box.appendChild(el('div', 'wh-row', r.ok ? `✓ ${r.source}${r.dest ? ` → ${r.dest}` : ''}` : `✗ ${r.source} — ${r.error}`));
      }
      if (ui.pendingImports.length) box.appendChild(el('p', 'task-muted', 'Các tệp thất bại vẫn ở hàng chờ bên dưới — sửa nguyên nhân rồi bấm Nhập lại.'));
    }
    if (!ui.pendingImports.length) {
      if (!box.childNodes.length) box.appendChild(el('span', 'task-muted', 'Chưa chọn tệp nào để nhập.'));
      return;
    }
    for (const file of ui.pendingImports) box.appendChild(el('div', 'wh-row', file));
  }

  window.WorkHubUI = { refresh, store };
  document.addEventListener('coding-tools:workspace-changed', () => { refresh(); });
  window.addEventListener('beforeunload', (event) => {
    const editor = $('#whEditor');
    const editing = editor && !editor.hidden && editor.value !== ui.viewerContent;
    if (!editing && !fileDrafts.size && !ui.savingFile) return;
    event.preventDefault();
    event.returnValue = '';
  });
  document.addEventListener('DOMContentLoaded', () => {
    bind();
    bindExtended();
    renderTypeFields();
    renderPromptOptions();
    renderProjects();
    renderBasket();
    renderRecipes();
    renderJob();
    refresh();
    startAttentionPolling();
  });
})();
