'use strict';
/*
 * Work Hub store — pure logic for the Đợt A usability features
 * (catalog docs/research/261022_FEATURE_EXPANSION_CATALOG.md):
 *   F01 prompt library, F03 project pin/alias, F04 task-type request builder,
 *   F05 per-project @file context basket, F20 saved project recipes,
 *   F22 attention-notification dedupe gate, F29 handoff preview,
 *   F31 unified search (Vietnamese, diacritics-insensitive).
 * No DOM access here: persistence is injected as an adapter {load(), save(data)}
 * so the module is testable under node:test and reusable from the renderer.
 */
(function (global) {
  const VERSION = 1;
  const LIMITS = { prompts: 100, recipes: 100, basketPerProject: 200, notified: 500, pins: 100 };

  const TASK_TYPES = {
    bugfix: {
      label: 'Sửa lỗi',
      fields: [
        { key: 'symptom', label: 'Hiện tượng lỗi', required: true },
        { key: 'expected', label: 'Kết quả mong đợi', required: false },
        { key: 'repro', label: 'Cách tái hiện', required: false },
      ],
      completion: 'Lỗi được sửa, có kiểm chứng bằng test hoặc thao tác tái hiện không còn lỗi.',
    },
    feature: {
      label: 'Thêm tính năng',
      fields: [
        { key: 'goal', label: 'Tính năng cần làm', required: true },
        { key: 'behavior', label: 'Hành vi mong đợi', required: false },
        { key: 'constraints', label: 'Ràng buộc / không được làm', required: false },
      ],
      completion: 'Tính năng hoạt động theo hành vi mong đợi, phạm vi thay đổi đúng phần đã nêu.',
    },
    review: {
      label: 'Review',
      fields: [
        { key: 'scope', label: 'Phạm vi review', required: true },
        { key: 'focus', label: 'Điểm cần chú ý', required: false },
      ],
      completion: 'Liệt kê vấn đề theo mức độ, kèm tệp/dòng liên quan; không tự sửa khi chưa được duyệt.',
    },
    test: {
      label: 'Kiểm thử / chạy test',
      fields: [
        { key: 'scope', label: 'Phần cần kiểm thử', required: true },
        { key: 'known', label: 'Điều đã biết / nghi ngờ', required: false },
      ],
      completion: 'Chạy đúng test liên quan, báo số test đạt/lỗi kèm bằng chứng, không suy đoán.',
    },
    docs: {
      label: 'Viết tài liệu',
      fields: [
        { key: 'topic', label: 'Chủ đề tài liệu', required: true },
        { key: 'audience', label: 'Người đọc', required: false },
      ],
      completion: 'Tài liệu khớp mã nguồn hiện tại, ví dụ kiểm chứng được.',
    },
  };

  const DEFAULT_PROMPTS = [
    {
      id: 'seed-bugfix', name: 'Sửa lỗi', builtin: true,
      body: 'Hãy sửa lỗi sau trong dự án {{project}}.\nHiện tượng: {{request}}\nTệp liên quan:\n{{files}}\nYêu cầu: tìm nguyên nhân gốc trước khi sửa, giữ phạm vi thay đổi nhỏ nhất, chạy test liên quan và báo bằng chứng.',
    },
    {
      id: 'seed-review', name: 'Review trước commit', builtin: true,
      body: 'Hãy review các thay đổi hiện tại của dự án {{project}} trước khi commit.\nTrọng tâm: {{request}}\nTệp đã đổi:\n{{files}}\nLiệt kê vấn đề theo mức độ nghiêm trọng kèm tệp/dòng; chưa tự sửa khi tôi chưa duyệt.',
    },
    {
      id: 'seed-docs', name: 'Viết tài liệu', builtin: true,
      body: 'Hãy viết/cập nhật tài liệu cho {{request}} trong dự án {{project}}.\nNgữ cảnh:\n{{files}}\nTài liệu phải khớp mã nguồn hiện tại; ví dụ phải kiểm chứng được.',
    },
  ];

  function normalizeText(value) {
    return String(value ?? '')
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/đ/g, 'd')
      .replace(/Đ/g, 'D')
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim();
  }

  function workspaceKeyOf(value) {
    return String(value ?? '').trim().replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
  }

  function fillTemplate(body, vars) {
    const source = String(body ?? '');
    return source.replace(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g, (match, key) => {
      const v = vars ? vars[key] : undefined;
      return v === undefined || v === null || v === '' ? match : String(v);
    });
  }

  function emptyData() {
    return {
      version: VERSION,
      prompts: DEFAULT_PROMPTS.map((p) => ({ ...p })),
      pins: {},
      recipes: [],
      baskets: {},
      notified: [],
      notificationsEnabled: true,
    };
  }

  function sanitizeData(raw) {
    const data = emptyData();
    if (!raw || typeof raw !== 'object') return data;
    if (Array.isArray(raw.prompts)) {
      data.prompts = raw.prompts
        .filter((p) => p && typeof p.name === 'string' && typeof p.body === 'string')
        .slice(0, LIMITS.prompts)
        .map((p) => ({ id: String(p.id || ''), name: p.name.slice(0, 120), body: p.body.slice(0, 20000), builtin: Boolean(p.builtin) }));
      if (!data.prompts.length) data.prompts = emptyData().prompts;
    }
    if (raw.pins && typeof raw.pins === 'object') {
      for (const [key, value] of Object.entries(raw.pins).slice(0, LIMITS.pins)) {
        if (value && typeof value === 'object') {
          data.pins[key] = { pinned: Boolean(value.pinned), alias: String(value.alias || '').slice(0, 80) };
        }
      }
    }
    if (Array.isArray(raw.recipes)) {
      data.recipes = raw.recipes
        .filter((r) => r && typeof r.name === 'string' && typeof r.command === 'string')
        .slice(0, LIMITS.recipes)
        .map((r) => ({ id: String(r.id || ''), name: r.name.slice(0, 120), command: r.command.slice(0, 2000), cwd: String(r.cwd || '').slice(0, 500) }));
    }
    if (raw.baskets && typeof raw.baskets === 'object') {
      for (const [key, items] of Object.entries(raw.baskets)) {
        if (!Array.isArray(items)) continue;
        const seen = new Set();
        data.baskets[key] = items
          .filter((f) => f && typeof f.path === 'string' && f.path.trim())
          .filter((f) => { const k = workspaceKeyOf(f.path); if (seen.has(k)) return false; seen.add(k); return true; })
          .slice(0, LIMITS.basketPerProject)
          .map((f) => ({ path: f.path.slice(0, 1000), size: Number.isFinite(Number(f.size)) && Number(f.size) >= 0 ? Number(f.size) : null }));
      }
    }
    if (Array.isArray(raw.notified)) data.notified = raw.notified.filter((x) => typeof x === 'string').slice(-LIMITS.notified);
    data.notificationsEnabled = raw.notificationsEnabled !== false;
    return data;
  }

  let idCounter = 0;
  function nextId(prefix) {
    idCounter += 1;
    return `${prefix}-${Date.now().toString(36)}-${idCounter.toString(36)}`;
  }

  function createStore(adapter) {
    const persistence = adapter && typeof adapter.load === 'function' && typeof adapter.save === 'function'
      ? adapter
      : { load: () => null, save: () => {} };
    let data = sanitizeData(safeLoad());
    function safeLoad() { try { return persistence.load(); } catch { return null; } }
    function persist() { try { persistence.save(JSON.parse(JSON.stringify(data))); } catch { /* storage full/blocked: keep in-memory state */ } }

    return {
      get data() { return data; },

      // ---- F01 prompt library ----
      listPrompts() { return data.prompts.slice(); },
      upsertPrompt({ id, name, body }) {
        const cleanName = String(name || '').trim();
        const cleanBody = String(body || '');
        if (!cleanName) throw new Error('Tên mẫu không được trống.');
        if (!cleanBody.trim()) throw new Error('Nội dung mẫu không được trống.');
        const existing = id ? data.prompts.find((p) => p.id === id) : null;
        if (existing) { existing.name = cleanName.slice(0, 120); existing.body = cleanBody.slice(0, 20000); }
        else {
          if (data.prompts.length >= LIMITS.prompts) throw new Error('Thư viện lời nhắc đã đầy.');
          data.prompts.push({ id: nextId('prompt'), name: cleanName.slice(0, 120), body: cleanBody.slice(0, 20000), builtin: false });
        }
        persist();
        return existing || data.prompts[data.prompts.length - 1];
      },
      removePrompt(id) {
        data.prompts = data.prompts.filter((p) => p.id !== id);
        persist();
      },

      // ---- F03 project pins / aliases ----
      setPin(workspace, { pinned, alias } = {}) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Đường dẫn dự án không hợp lệ.');
        const current = data.pins[key] || { pinned: false, alias: '' };
        if (pinned !== undefined) current.pinned = Boolean(pinned);
        if (alias !== undefined) current.alias = String(alias).trim().slice(0, 80);
        if (!current.pinned && !current.alias) delete data.pins[key];
        else data.pins[key] = current;
        persist();
        return current;
      },
      pinOf(workspace) { return data.pins[workspaceKeyOf(workspace)] || { pinned: false, alias: '' }; },
      projectLabel(workspace) {
        const pin = this.pinOf(workspace);
        if (pin.alias) return pin.alias;
        const parts = String(workspace || '').replace(/\\/g, '/').split('/').filter(Boolean);
        return parts.length ? parts[parts.length - 1] : String(workspace || '');
      },
      sortProjects(workspaces) {
        return (Array.isArray(workspaces) ? workspaces.slice() : []).sort((a, b) => {
          const pa = this.pinOf(a).pinned ? 0 : 1;
          const pb = this.pinOf(b).pinned ? 0 : 1;
          return pa - pb;
        });
      },

      // ---- F05 context basket (isolated per project) ----
      basketFor(workspace) { return (data.baskets[workspaceKeyOf(workspace)] || []).slice(); },
      addToBasket(workspace, file) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const path = String(file?.path || '').trim();
        if (!path) throw new Error('Đường dẫn tệp không được trống.');
        const list = data.baskets[key] || (data.baskets[key] = []);
        if (list.some((f) => workspaceKeyOf(f.path) === workspaceKeyOf(path))) return list.slice();
        if (list.length >= LIMITS.basketPerProject) throw new Error('Giỏ ngữ cảnh đã đầy.');
        list.push({ path: path.slice(0, 1000), size: Number.isFinite(Number(file?.size)) && Number(file.size) >= 0 ? Number(file.size) : null });
        persist();
        return list.slice();
      },
      removeFromBasket(workspace, path) {
        const key = workspaceKeyOf(workspace);
        if (data.baskets[key]) data.baskets[key] = data.baskets[key].filter((f) => workspaceKeyOf(f.path) !== workspaceKeyOf(path));
        persist();
      },
      clearBasket(workspace) {
        delete data.baskets[workspaceKeyOf(workspace)];
        persist();
      },
      contextPackageText(workspace) {
        const files = this.basketFor(workspace);
        if (!files.length) return '';
        const lines = files.map((f) => `- ${f.path}${f.size !== null ? ` (${f.size} bytes)` : ''}`);
        return `Ngữ cảnh tệp cho dự án ${workspace}:\n${lines.join('\n')}`;
      },

      // ---- F20 saved recipes ----
      listRecipes() { return data.recipes.slice(); },
      upsertRecipe({ id, name, command, cwd }) {
        const cleanName = String(name || '').trim();
        const cleanCommand = String(command || '').trim();
        if (!cleanName) throw new Error('Tên lệnh không được trống.');
        if (!cleanCommand) throw new Error('Lệnh không được trống.');
        const existing = id ? data.recipes.find((r) => r.id === id) : null;
        if (existing) { existing.name = cleanName.slice(0, 120); existing.command = cleanCommand.slice(0, 2000); existing.cwd = String(cwd || '').slice(0, 500); }
        else {
          if (data.recipes.length >= LIMITS.recipes) throw new Error('Danh sách lệnh đã lưu đã đầy.');
          data.recipes.push({ id: nextId('recipe'), name: cleanName.slice(0, 120), command: cleanCommand.slice(0, 2000), cwd: String(cwd || '').slice(0, 500) });
        }
        persist();
        return existing || data.recipes[data.recipes.length - 1];
      },
      removeRecipe(id) { data.recipes = data.recipes.filter((r) => r.id !== id); persist(); },

      // ---- F22 notification dedupe gate ----
      setNotificationsEnabled(enabled) { data.notificationsEnabled = Boolean(enabled); persist(); },
      notificationsEnabled() { return data.notificationsEnabled; },
      claimNotification(eventId) {
        if (!data.notificationsEnabled) return false;
        const id = String(eventId || '').trim();
        if (!id || data.notified.includes(id)) return false;
        data.notified.push(id);
        if (data.notified.length > LIMITS.notified) data.notified = data.notified.slice(-LIMITS.notified);
        persist();
        return true;
      },
    };
  }

  // ---- F04 task-type request builder ----
  function buildRequest({ type, fields, project, filesText }) {
    const def = TASK_TYPES[type];
    if (!def) throw new Error('Loại công việc không hợp lệ.');
    const values = fields && typeof fields === 'object' ? fields : {};
    for (const field of def.fields) {
      if (field.required && !String(values[field.key] || '').trim()) {
        throw new Error(`Thiếu trường bắt buộc: ${field.label}.`);
      }
    }
    const lines = [`[${def.label}] ${project ? `Dự án: ${project}` : ''}`.trim()];
    for (const field of def.fields) {
      const v = String(values[field.key] || '').trim();
      if (v) lines.push(`${field.label}: ${v}`);
    }
    if (filesText && String(filesText).trim()) lines.push(String(filesText).trim());
    lines.push(`Tiêu chí hoàn thành: ${def.completion}`);
    return lines.join('\n');
  }

  // ---- F29 handoff preview ----
  function handoffPreview(task) {
    if (!task || typeof task !== 'object') return null;
    const steps = Array.isArray(task.steps) ? task.steps : [];
    const done = steps.filter((s) => ['done', 'completed', 'complete', 'passed', 'success'].includes(String(s?.status || '').toLowerCase()));
    const pending = steps.filter((s) => !['done', 'completed', 'complete', 'passed', 'success'].includes(String(s?.status || '').toLowerCase()));
    const tests = Array.isArray(task.tests) ? task.tests : [];
    const failedTests = tests.filter((t) => ['failed', 'fail', 'error'].includes(String(t?.status || '').toLowerCase()));
    const files = Array.isArray(task.files) ? task.files : (Array.isArray(task.changed_files) ? task.changed_files : []);
    return {
      objective: String(task.objective || task.title || ''),
      status: String(task.status || ''),
      doneSteps: done.map((s) => String(s?.title || s?.name || s?.step || '')).filter(Boolean),
      unverified: [
        ...pending.map((s) => `Bước chưa xong: ${String(s?.title || s?.name || s?.step || '')}`),
        ...failedTests.map((t) => `Test lỗi: ${String(t?.name || t?.title || '')}`),
        ...(tests.length === 0 ? ['Chưa có kết quả kiểm thử nào được ghi nhận.'] : []),
      ].filter(Boolean),
      nextStep: String(task.next_step || task.nextStep || ''),
      currentStep: String(task.current_step || task.currentStep || ''),
      files: files.map((f) => (typeof f === 'string' ? f : String(f?.path || f?.file || ''))).filter(Boolean),
    };
  }

  function formatHandoffText(preview) {
    if (!preview) return '';
    const lines = [`Mục tiêu: ${preview.objective || '—'}`];
    lines.push(`Đã làm: ${preview.doneSteps.length ? preview.doneSteps.join('; ') : 'chưa ghi nhận bước hoàn thành'}`);
    lines.push(`Chưa kiểm chứng: ${preview.unverified.length ? preview.unverified.join('; ') : 'không có'}`);
    lines.push(`Bước tiếp theo: ${preview.nextStep || preview.currentStep || '—'}`);
    if (preview.files.length) lines.push(`Tệp liên quan: ${preview.files.join(', ')}`);
    return lines.join('\n');
  }

  // ---- F31 unified search ----
  function searchAll(entries, query, limit = 12) {
    const q = normalizeText(query);
    if (!q || !Array.isArray(entries)) return [];
    const scored = [];
    for (const entry of entries) {
      if (!entry || typeof entry.title !== 'string') continue;
      const title = normalizeText(entry.title);
      const detail = normalizeText(entry.detail || '');
      let score = -1;
      if (title.startsWith(q)) score = 3;
      else if (title.includes(q)) score = 2;
      else if (detail.includes(q)) score = 1;
      else if (q.split(' ').every((part) => title.includes(part) || detail.includes(part))) score = 0;
      if (score >= 0) scored.push({ entry, score });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.entry);
  }

  const api = {
    VERSION, LIMITS, TASK_TYPES, DEFAULT_PROMPTS,
    normalizeText, workspaceKeyOf, fillTemplate,
    emptyData, sanitizeData, createStore,
    buildRequest, handoffPreview, formatHandoffText, searchAll,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.WorkHubStore = api;
})(typeof window !== 'undefined' ? window : globalThis);
