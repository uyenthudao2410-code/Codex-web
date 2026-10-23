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
  const ui = { snapshot: null, taskPayload: null, selectedPromptId: '', selectedType: 'bugfix', dirRel: '', viewerRel: '', viewerHash: '', gen: 0, job: null, pendingImports: [] };

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
      const isCurrent = S.workspaceKeyOf(project) === S.workspaceKeyOf(current);
      if (isCurrent) row.appendChild(el('span', 'soft-badge', 'Đang dùng'));
      else {
        const useBtn = el('button', 'secondary-button wh-small', 'Chuyển đến');
        useBtn.addEventListener('click', async () => {
          const switched = unwrap(await window.mcpAssistant.switchWorkspace(project).catch(() => null));
          if (switched) { ui.snapshot = switched?.data || switched; ui.dirRel = ''; refresh(); }
        });
        row.appendChild(useBtn);
      }
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
    const project = currentProject();
    const keyOf = (p) => S.workspaceKeyOf(p || '');
    const scoped = recipes.filter((r) => !r.cwd || keyOf(r.cwd) === keyOf(project));
    const others = recipes.filter((r) => r.cwd && keyOf(r.cwd) !== keyOf(project));
    const renderOne = (recipe, inProject) => {
      const row = el('div', 'wh-row');
      const main = el('div', 'wh-row-main');
      main.appendChild(el('b', '', recipe.name + (inProject ? '' : ' · dự án khác')));
      main.appendChild(el('small', '', recipe.command + (recipe.cwd ? `  ·  ${recipe.cwd}` : '')));
      row.appendChild(main);
      const run = el('button', 'secondary-button wh-small', 'Chạy (Job)');
      run.addEventListener('click', () => runRecipeAsJob(recipe));
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
    if (!task) { box.appendChild(el('span', 'task-muted', 'Chưa có trạng thái tác vụ. Mở trang Tác vụ & kết quả để xem chi tiết.')); return; }
    const preview = S.handoffPreview(task);
    const files = preview?.files || [];
    box.appendChild(el('p', '', `Tệp đã sửa đổi (${files.length}): ${files.length ? files.join(', ') : 'chưa ghi nhận'}`));
    const tests = S.taskTests(task);
    box.appendChild(el('p', '', `Kiểm thử gần đây: ${tests.length ? `${tests.filter((t) => !S.testFailed(t)).length}/${tests.length} đạt` : 'chưa có'}. Xem diff đầy đủ và sản phẩm đầu ra ở trang Tác vụ & kết quả.`));
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
    if (!box || !window.mcpAssistant?.workhubList) return;
    const gen = ui.gen;
    const project = currentProject();
    const data = unwrap(await window.mcpAssistant.workhubList(ui.dirRel).catch(() => null));
    if (gen !== ui.gen || project !== currentProject()) return; // stale response for an old project/generation
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

  async function openFile(rel, line) {
    const viewer = $('#whViewer');
    if (!viewer || !window.mcpAssistant?.workhubRead) return;
    const gen = ui.gen;
    ui.viewerRel = rel;
    ui.viewerHash = '';
    $('#whViewerTitle').textContent = rel;
    const addBtn = $('#whViewerAddBasket');
    if (addBtn) addBtn.disabled = false;
    const editBtn = $('#whEditFile');
    if (editBtn) editBtn.disabled = false;
    const data = unwrap(await window.mcpAssistant.workhubRead(rel).catch(() => null));
    if (gen !== ui.gen) return; // a newer navigation superseded this read
    if (!data) { viewer.textContent = 'Không đọc được tệp.'; return; }
    ui.viewerHash = data.hash || '';
    if (data.binary) { viewer.textContent = `Tệp nhị phân (${data.size} bytes) — không xem trước nội dung.`; return; }
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
  }

  async function renderCodeSearch() {
    const box = $('#whCodeResults');
    const query = String($('#whCodeQuery')?.value || '').trim();
    if (!box || !query) return;
    const gen = ui.gen;
    const data = unwrap(await window.mcpAssistant.workhubSearch(query).catch(() => null));
    if (gen !== ui.gen) return;
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
    const data = unwrap(await window.mcpAssistant.workhubGitStatus().catch(() => null));
    if (!data) { box.replaceChildren(el('span', 'task-muted', 'Không lấy được trạng thái Git (dự án chưa phải git repo?).')); return; }
    if (!data.length) { box.replaceChildren(el('span', 'task-muted', 'Không có thay đổi nào trong cây làm việc.')); return; }
    box.replaceChildren(...data.map((item) => {
      const row = el('div', 'wh-row');
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
    renderTaskFileChanges();
  }

  async function renderGitLog() {
    const box = $('#whGitLog');
    if (!box || !window.mcpAssistant?.workhubGitLog) return;
    const data = unwrap(await window.mcpAssistant.workhubGitLog(15).catch(() => null));
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
        const shown = unwrap(await window.mcpAssistant.workhubGitShow(commit.hash).catch(() => null));
        if (diffBox) diffBox.textContent = shown ? shown.text + (shown.truncated ? '\n… (đã rút gọn)' : '') : 'Không đọc được commit.';
      });
      row.append(view);
      return row;
    }));
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

  async function renderDiff(rel) {
    const box = $('#whDiff');
    if (!box) return;
    const gen = ui.gen;
    const data = unwrap(await window.mcpAssistant.workhubGitDiff(rel).catch(() => null));
    if (gen !== ui.gen) return;
    ui.diffRel = rel;
    ui.diffText = data?.diff || '';
    box.textContent = !data ? 'Không lấy được diff.'
      : (data.diff || 'Tệp chưa có diff (tệp mới chưa track sẽ không có diff — xem ở trang Tác vụ).')
        + (data.truncated ? '\n… (diff đã rút gọn)' : '');
    renderPatchApproval();
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
      if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'].includes(ext)) {
        const viewImage = smallButton('Xem ảnh');
        viewImage.addEventListener('click', async () => {
          const data = unwrap(await window.mcpAssistant.workhubReadImage(item.path).catch(() => null));
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
        const result = unwrap(await window.mcpAssistant.workhubOpenPath(item.path, false).catch(() => null));
        if (!result) window.alert('Không mở được tệp — có thể tệp đã bị di chuyển hoặc đổi sau khi build.');
      });
      row.append(open);
      const reveal = smallButton('Mở thư mục');
      reveal.addEventListener('click', () => window.mcpAssistant.workhubOpenPath(item.path, true).catch(() => {}));
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
      entries.push({
        kind: 'Dự án', title: store.projectLabel(project), detail: project,
        run: async () => {
          if (S.workspaceKeyOf(project) !== S.workspaceKeyOf(currentProject())) {
            const switched = unwrap(await window.mcpAssistant.switchWorkspace(project).catch(() => null));
            if (switched) { ui.snapshot = switched?.data || switched; ui.dirRel = ''; }
          }
          window.navigate?.('workhub');
          refresh();
        },
      });
    }
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if (task?.objective) {
      entries.push({ kind: 'Tác vụ', title: task.objective, detail: `task hiện tại · ${task.status || ''}`, run: () => window.navigate?.('task') });
      entries.push({ kind: 'Báo cáo', title: `Báo cáo: ${task.objective}`, detail: 'xuất báo cáo tác vụ md', run: () => { window.navigate?.('workhub'); $('#whExportReport')?.click(); } });
    }
    for (const note of store.listNotes(currentProject())) {
      entries.push({ kind: 'Ghi chú', title: note.title, detail: note.body.slice(0, 80), run: () => window.navigate?.('workhub') });
    }
    for (const chat of store.listChats(currentProject())) {
      entries.push({ kind: 'Hội thoại', title: chat.label, detail: chat.note || chat.url || '', run: () => { if (chat.url) window.mcpAssistant?.openExternal?.(chat.url); } });
    }
    for (const file of store.basketFor(currentProject())) {
      entries.push({ kind: 'Tệp ngữ cảnh', title: file.path, detail: 'trong giỏ ngữ cảnh của dự án hiện tại', run: () => openFile(String(file.path).replace(/\\/g, '/')) });
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
    ui.gen += 1;
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
    renderGitLog();
    renderExtended();
    renderGoal();
  }

  // ================= Extended waves (adoption decisions 261022) =================

  // ---- A3/F19/F20: run a saved recipe through the runtime Job lifecycle ----
  function jobOutputText(result) {
    if (!result || typeof result !== 'object') return '';
    const parts = [];
    if (typeof result.output === 'string') parts.push(result.output);
    if (typeof result.stdout === 'string') parts.push(result.stdout);
    if (typeof result.stderr === 'string') parts.push(result.stderr);
    if (!parts.length && Array.isArray(result.content)) {
      for (const item of result.content) if (item?.type === 'text') parts.push(item.text);
    }
    return parts.join('\n').slice(-12000);
  }
  function jobStatusOf(result) {
    return String(result?.status || result?.state || (result?.running ? 'running' : 'exited'));
  }
  function renderJob() {
    const box = $('#whJobView');
    const meta = $('#whJobMeta');
    if (!box || !meta) return;
    if (!ui.job) { meta.textContent = 'Chưa chạy lệnh nào trong phiên này.'; box.textContent = 'Chọn "Chạy (Job)" ở một lệnh đã lưu.'; return; }
    meta.textContent = `${ui.job.name} · ${ui.job.status}${ui.job.commandId ? ` · Job ${ui.job.commandId}` : ''}${ui.job.exitCode != null ? ` · exit ${ui.job.exitCode}` : ''}`;
    box.textContent = ui.job.output || '(chưa có output)';
    const kill = $('#whJobKill');
    const poll = $('#whJobPoll');
    if (kill) kill.disabled = ui.job.status !== 'running';
    if (poll) poll.disabled = ui.job.status !== 'running';
  }
  async function runRecipeAsJob(recipe) {
    if (ui.job?.status === 'running') { window.alert('Đang có Job chạy — dừng hoặc chờ xong trước khi chạy lệnh khác.'); return; }
    ui.job = { name: recipe.name, commandId: '', status: 'starting', output: '', exitCode: null };
    renderJob();
    const result = unwrap(await window.mcpAssistant.workhubJobRun({ command: recipe.command, cwd: recipe.cwd || currentProject() }).catch(() => null));
    if (!result) { ui.job.status = 'error'; ui.job.output = 'Không chạy được lệnh qua runtime (MCP chưa sẵn sàng?).'; renderJob(); return; }
    ui.job.commandId = result.command_id || result.session_id || result.commandId || '';
    ui.job.status = jobStatusOf(result);
    ui.job.output = jobOutputText(result);
    ui.job.exitCode = result.exit_code ?? result.exitCode ?? null;
    renderJob();
    if (ui.job.status === 'running') {
      window.mcpAssistant.workhubKeepAwake(true).catch(() => {});
      pollJobLoop();
    }
  }
  async function pollJobLoop() {
    while (ui.job && ui.job.status === 'running' && ui.job.commandId) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      if (!ui.job || ui.job.status !== 'running') break;
      const result = unwrap(await window.mcpAssistant.workhubJobControl({ action: 'poll', commandId: ui.job.commandId }).catch(() => null));
      if (!result) break;
      const text = jobOutputText(result);
      if (text) ui.job.output = text;
      ui.job.status = jobStatusOf(result);
      ui.job.exitCode = result.exit_code ?? result.exitCode ?? ui.job.exitCode;
      renderJob();
    }
    if (ui.job && ui.job.status !== 'running') window.mcpAssistant.workhubKeepAwake(false).catch(() => {});
  }

  // ---- A1: context package with real content + versions ----
  async function buildContextPackage() {
    const files = store.basketFor(currentProject());
    if (!files.length) { window.alert('Giỏ ngữ cảnh đang trống.'); return; }
    const parts = [];
    let budget = 120 * 1024;
    for (const file of files) {
      const rel = String(file.path).replace(/\\/g, '/');
      const data = unwrap(await window.mcpAssistant.workhubRead(rel).catch(() => null));
      if (!data || data.binary) { parts.push({ path: rel, size: file.size, content: null }); continue; }
      let content = data.content || '';
      if (content.length > budget) content = content.slice(0, Math.max(0, budget));
      budget -= content.length;
      parts.push({ path: rel, size: data.size, content, truncated: Boolean(data.truncated) || content.length < (data.content || '').length, hash: String(data.hash || '').slice(0, 12) });
      if (budget <= 0) break;
    }
    const text = S.contextContentText(currentProject(), parts);
    const preview = $('#whPreview');
    if (preview) { preview.value = text; store.saveDraft(currentProject(), text); renderDraftState(); }
  }

  // ---- F17 plan + F18 steering ----
  function renderPlan() {
    const box = $('#whPlan');
    if (!box) return;
    const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    const plan = S.planView(task);
    if (!plan) { box.replaceChildren(el('span', 'task-muted', 'Chưa có task để trình bày kế hoạch.')); return; }
    box.replaceChildren();
    box.append(el('p', '', `${plan.doneCount}/${plan.steps.length} bước xong · ${plan.testsRun} test đã chạy, ${plan.testsFailed} lỗi${plan.detailsAvailable ? '' : ' · CHƯA lấy được chi tiết (details_available=false)'}`));
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
    box.textContent = draft ? `Có nháp đã lưu lúc ${new Date(draft.updatedAt).toLocaleTimeString('vi-VN')} cho dự án này.` : 'Chưa có nháp cho dự án này.';
  }
  function restoreDraft() {
    const draft = store.getDraft(currentProject());
    const preview = $('#whPreview');
    if (draft && preview && !preview.value) preview.value = draft.text;
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
      main.append(el('b', '', skill.name), el('small', '', `${skill.source} · ${active ? 'đang bật cho dự án này' : 'chưa bật cho dự án này'}`));
      row.append(main);
      const toggle = smallButton(active ? 'Tắt' : 'Bật cho dự án');
      toggle.addEventListener('click', () => { store.setSkillForProject(skill.id, currentProject(), !active); renderSkills(); });
      const add = smallButton('Đưa vào yêu cầu');
      add.addEventListener('click', () => {
        const preview = $('#whPreview');
        if (preview) preview.value = `${preview.value ? `${preview.value}\n` : ''}[Skill: ${skill.name}]\n${skill.content}`;
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
      main.append(el('b', '', target.name), el('small', '', `${target.user ? `${target.user}@` : ''}${target.host}:${target.port}${target.remoteDir ? ` · ${target.remoteDir}` : ''}`));
      row.append(main);
      const check = smallButton('Chạy kiểm tra');
      check.addEventListener('click', async () => {
        const out = $('#whSshOutput');
        if (out) out.textContent = 'Đang chạy qua Job (ssh)...';
        const command = `ssh ${S.sshArgs(target, 'pwd && git status --short | head -20').map((a) => (/\s/.test(a) ? `"${a.replace(/"/g, '\\"')}"` : a)).join(' ')}`;
        await runRecipeAsJob({ name: `SSH ${target.name}`, command, cwd: currentProject() });
        if (out) out.textContent = 'Kết quả ở bảng Job phía trên.';
      });
      const remove = smallButton('Xóa');
      remove.addEventListener('click', () => { store.removeSshTarget(target.id); renderSshTargets(); });
      row.append(check, remove);
      return row;
    });
  }

  // ---- F16 task board + F21 lanes ----
  async function renderTaskBoard() {
    const box = $('#whTaskBoard');
    if (!box) return;
    const rows = [];
    const current = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
    if (current) rows.push({ title: current.objective || 'Task hiện tại', status: current.status || '', current: true });
    const history = unwrap(await window.mcpAssistant?.taskHistory?.().catch(() => null));
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
    const data = unwrap(await window.mcpAssistant?.orchestration?.().catch(() => null));
    const payload = data?.data || data || {};
    const clients = Array.isArray(payload.clients) ? payload.clients : [];
    const delegations = Array.isArray(payload.delegations) ? payload.delegations : [];
    if (!clients.length && !delegations.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa có dữ liệu điều phối (delegation/client) từ runtime.')); return; }
    const rows = [];
    for (const client of clients) rows.push(`Client ${client.client_id || client.client_type || ''} · ${client.online ? 'online' : 'offline'}`);
    for (const lane of delegations) rows.push(`Lane ${lane.lane || lane.id || ''} · ${lane.status || ''} · ${lane.objective || lane.summary || ''}`);
    box.replaceChildren(...rows.map((text) => el('div', 'wh-row', text)));
  }

  // ---- F33 targets + F36 integration inventory ----
  async function renderTargets() {
    const box = $('#whTargetList');
    if (!box) return;
    const rows = [];
    const local = currentProject();
    if (local) rows.push({ label: `Máy này · ${local}`, action: null });
    const workspaces = unwrap(await window.mcpAssistant?.listControlPlaneWorkspaces?.().catch(() => null));
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
    $('#whPreview')?.addEventListener('input', (e) => { try { store.saveDraft(currentProject(), e.target.value); } catch { /* draft store full */ } renderDraftState(); });
    $('#whClearDraft')?.addEventListener('click', () => { store.clearDraft(currentProject()); renderDraftState(); });
    $('#whRecipeUrl')?.closest('form')?.addEventListener('submit', (e) => e.preventDefault());
    const recipeSave = $('#whAddRecipe');
    if (recipeSave) recipeSave.addEventListener('click', () => {
      const url = $('#whRecipeUrl')?.value || '';
      if (url) {
        const name = $('#whRecipeName').value;
        const existing = store.listRecipes().find((r) => r.name === name);
        if (existing) store.upsertRecipe({ id: existing.id, name, command: $('#whRecipeCommand').value, cwd: $('#whRecipeCwd').value || currentProject(), url });
      }
    }, true);
    $('#whJobKill')?.addEventListener('click', async () => {
      if (!ui.job?.commandId) return;
      await window.mcpAssistant.workhubJobControl({ action: 'kill', commandId: ui.job.commandId }).catch(() => null);
      ui.job.status = 'killed (đã gửi yêu cầu dừng)';
      renderJob();
    });
    $('#whJobPoll')?.addEventListener('click', async () => {
      if (!ui.job?.commandId) return;
      const result = unwrap(await window.mcpAssistant.workhubJobControl({ action: 'poll', commandId: ui.job.commandId }).catch(() => null));
      if (result) { ui.job.output = jobOutputText(result) || ui.job.output; ui.job.status = jobStatusOf(result); renderJob(); }
    });
    $('#whJobWrite')?.addEventListener('click', async () => {
      const chars = $('#whJobInput')?.value || '';
      if (!ui.job?.commandId || !chars) return;
      // Local command_control has no input_id: if the ACK is lost we do NOT
      // auto-resend — the user decides after polling (adoption decision A3).
      await window.mcpAssistant.workhubJobControl({ action: 'write', commandId: ui.job.commandId, chars }).catch(() => null);
      $('#whJobInput').value = '';
    });
    $('#whEditFile')?.addEventListener('click', () => {
      const viewer = $('#whViewer');
      const editor = $('#whEditor');
      if (!viewer || !editor || !ui.viewerRel) return;
      editor.value = viewer.textContent || '';
      editor.hidden = false;
      $('#whSaveFile').disabled = false;
    });
    $('#whSaveFile')?.addEventListener('click', async () => {
      const editor = $('#whEditor');
      if (!editor || !ui.viewerRel) return;
      const result = await window.mcpAssistant.workhubWrite(ui.viewerRel, editor.value, ui.viewerHash).catch(() => null);
      const data = unwrap(result);
      if (!data) { window.alert('Không lưu được — tệp có thể đã thay đổi bên ngoài. Tải lại tệp trước khi sửa tiếp.'); return; }
      ui.viewerHash = data.hash;
      editor.hidden = true;
      openFile(ui.viewerRel);
    });
    $('#whBlame')?.addEventListener('click', async () => {
      if (!ui.viewerRel) return;
      const data = unwrap(await window.mcpAssistant.workhubGitBlame(ui.viewerRel).catch(() => null));
      const viewer = $('#whViewer');
      if (viewer) viewer.textContent = data ? data.lines.map((l) => `${l.line} · ${l.author} · ${l.text}`).join('\n') : 'Không lấy được blame.';
    });
    $('#whGitLogRefresh')?.addEventListener('click', renderGitLog);
    $('#whChooseImport')?.addEventListener('click', async () => {
      const files = unwrap(await window.mcpAssistant.chooseFiles().catch(() => null)) || [];
      ui.pendingImports = files;
      renderImports();
    });
    $('#whRunImports')?.addEventListener('click', async () => {
      const dest = $('#whImportDest')?.value || '';
      for (const source of ui.pendingImports) {
        await window.mcpAssistant.workhubCopyIn(source, dest).catch(() => null);
      }
      ui.pendingImports = [];
      renderImports();
      renderFiles();
    });
    $('#whSaveSnippet')?.addEventListener('click', async () => {
      const name = String($('#whSnippetName')?.value || '').trim();
      const content = $('#whSnippetBody')?.value || '';
      if (!name) { window.alert('Nhập tên tệp cho đoạn code.'); return; }
      const rel = ui.dirRel ? `${ui.dirRel}/${name}` : name;
      const result = await window.mcpAssistant.workhubWrite(rel, content, null).catch(() => null);
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
      if (preview) preview.value = next.text || next.title;
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
      if (prep && preview) preview.value = S.goalRequestText(currentProject(), prep);
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
      const preview = $('#whPreview');
      if (preview) preview.value = text;
      const blob = new Blob([text], { type: 'text/markdown' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'bao-cao-tac-vu.md';
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 5000);
    });
    $('#whReadCapsule')?.addEventListener('click', async () => {
      const box = $('#whCapsuleView');
      if (!box) return;
      box.replaceChildren(el('span', 'task-muted', 'Đang đọc capsule từ ledger…'));
      const preview = ui.handoffPreview;
      const runId = String(preview?.runId || ui.taskPayload?.run_id || ui.taskPayload?.state?.run_id || '');
      const result = unwrap(await window.mcpAssistant.workhubHandoffGet({ runId }).catch((error) => ({ error: error.message })));
      const capsule = result?.capsule || null;
      box.replaceChildren();
      if (!capsule) {
        box.appendChild(el('p', 'task-muted', result?.recommended_next_action || 'Chưa có capsule nào được ghi cho run này. Hãy ghi capsule từ trang Tác vụ trước khi chuyển hội thoại.'));
        return;
      }
      const payload = capsule.payload || {};
      const runtime = payload.runtime || {};
      const head = el('div', 'wh-row');
      head.appendChild(el('b', '', `Capsule ${String(capsule.capsule_id || '').slice(0, 12)} · v${capsule.version ?? '?'}`));
      head.appendChild(el('span', 'soft-badge', capsule.status || ''));
      box.appendChild(head);
      box.appendChild(el('p', '', `Mục tiêu khi ghi: ${runtime.objective || payload.objective || '—'}`));
      if (payload.panel_summary) box.appendChild(el('p', 'task-muted', `Tóm tắt panel: ${payload.panel_summary}`));
      box.appendChild(el('p', 'task-muted', `Ghi lúc ${capsule.created_at || '—'} · run ${capsule.run_id || '—'} · sha256 ${String(capsule.sha256 || '').slice(0, 12)}…`));
      // Revalidate the capsule against the CURRENT workspace state.
      const checks = [];
      if (runtime.base_head) {
        const log = unwrap(await window.mcpAssistant.workhubGitLog({ root: currentProject(), limit: 1 }).catch(() => null));
        const currentHead = log?.commits?.[0]?.hash || '';
        checks.push(`HEAD: capsule ${String(runtime.base_head).slice(0, 8)} vs hiện tại ${currentHead.slice(0, 8)} — ${currentHead && String(runtime.base_head).startsWith(currentHead.slice(0, 8)) || currentHead.startsWith(String(runtime.base_head).slice(0, 8)) ? 'KHỚP' : 'ĐÃ ĐỔI (cần xem lại diff kể từ base)'}`);
      }
      checks.push(`Trạng thái task khi ghi: ${runtime.task_status || '—'}; hiện tại: ${currentTaskState()?.status || '—'}.`);
      for (const line of checks) box.appendChild(el('p', 'task-muted', line));
      if (result?.recommended_next_action) box.appendChild(el('p', 'task-muted', result.recommended_next_action));
      const useBtn = el('button', 'secondary-button wh-small', 'Tạo yêu cầu tiếp tục từ capsule');
      useBtn.addEventListener('click', () => {
        const text = [
          `Tiếp tục từ capsule ${capsule.capsule_id} (run ${capsule.run_id}).`,
          runtime.objective ? `Mục tiêu: ${runtime.objective}` : '',
          payload.panel_summary ? `Tóm tắt: ${payload.panel_summary}` : '',
          checks.map((line) => `- ${line}`).join('\n'),
          'Không phát lại transcript cũ; tiếp tục từ trạng thái đã kiểm tra ở trên.',
        ].filter(Boolean).join('\n');
        const preview = $('#whPreview');
        if (preview) preview.value = text;
        try { store.saveDraft(currentProject(), text); } catch { /* draft store full */ }
        renderDraftState();
      });
      box.appendChild(useBtn);
    });
    $('#whRevalidate')?.addEventListener('click', async () => {
      const task = ui.taskPayload?.state || ui.taskPayload?.data?.state || null;
      const files = S.taskFiles(task || {});
      const lines = [];
      for (const path of files) {
        const data = unwrap(await window.mcpAssistant.workhubRead(path.replace(/\\/g, '/')).catch(() => null));
        lines.push(data ? `Còn trên đĩa: ${path} (${data.size} bytes)` : `KHÔNG còn đọc được: ${path}`);
      }
      const git = unwrap(await window.mcpAssistant.workhubGitStatus().catch(() => null));
      lines.push(git ? `Git hiện có ${git.length} thay đổi chưa commit.` : 'Không đọc được trạng thái Git.');
      const viewer = $('#whHandoffView');
      if (viewer) viewer.textContent = `${viewer.textContent}\n\n[Kiểm tra lại ${new Date().toLocaleTimeString('vi-VN')}]\n${lines.join('\n')}`;
    });
    $('#whVoiceBtn')?.addEventListener('click', () => {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const status = $('#whVoiceStatus');
      if (!Recognition) { if (status) status.textContent = 'Engine giọng nói không có trong môi trường này — nhập bằng bàn phím.'; return; }
      const recognition = new Recognition();
      recognition.lang = 'vi-VN';
      recognition.onresult = (event) => {
        const text = event.results?.[0]?.[0]?.transcript || '';
        const preview = $('#whPreview');
        if (preview && text) { preview.value = `${preview.value ? `${preview.value} ` : ''}${text}`; store.saveDraft(currentProject(), preview.value); }
        if (status) status.textContent = 'Đã chuyển thành chữ — kiểm tra và sửa trước khi dùng.';
      };
      recognition.onerror = () => { if (status) status.textContent = 'Không ghi âm được (engine từ chối hoặc không có micro).'; };
      if (status) status.textContent = 'Đang nghe…';
      recognition.start();
    });
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
    if (!ui.pendingImports.length) { box.replaceChildren(el('span', 'task-muted', 'Chưa chọn tệp nào để nhập.')); return; }
    box.replaceChildren(...ui.pendingImports.map((file) => el('div', 'wh-row', file)));
  }

  window.WorkHubUI = { refresh, store };
  document.addEventListener('DOMContentLoaded', () => {
    bind();
    bindExtended();
    renderTypeFields();
    renderPromptOptions();
    renderProjects();
    renderBasket();
    renderRecipes();
    startAttentionPolling();
  });
})();
