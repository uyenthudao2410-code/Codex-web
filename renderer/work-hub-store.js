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
  const LIMITS = { prompts: 100, recipes: 100, basketPerProject: 200, notified: 500, pins: 100, drafts: 50, notesPerProject: 200, skills: 100, chatsPerProject: 100, sshTargets: 50, queuePerProject: 100, feedbackPerProject: 100, schedules: 50 };

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
      drafts: {},
      patchApprovals: {},
      queues: {},
      feedback: {},
      goalPreps: {},
      schedules: [],
      notes: {},
      skills: [],
      chats: {},
      sshTargets: [],
    };
  }

  const KNOWN_DRAFT_FIELDS = new Set(Object.values(TASK_TYPES).flatMap((type) => type.fields.map((field) => field.key)));
  function sanitizeDraft(value) {
    // Drafts carry the whole request-builder state per project: the composed
    // text plus the task type, form fields and selected prompt, so switching
    // projects restores exactly where the user left off. A plain string is
    // accepted for older callers and normalized to the object shape. Only
    // known form fields survive a reload; unknown keys are dropped.
    if (typeof value === 'string') value = { text: value };
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const fields = {};
    if (value.fields && typeof value.fields === 'object') {
      for (const [name, fieldValue] of Object.entries(value.fields)) {
        if (KNOWN_DRAFT_FIELDS.has(name) && typeof fieldValue === 'string') fields[name] = fieldValue.slice(0, 4000);
      }
    }
    return {
      text: typeof value.text === 'string' ? value.text.slice(0, 20000) : '',
      type: typeof value.type === 'string' && TASK_TYPES[value.type] ? value.type : 'bugfix',
      fields,
      promptId: typeof value.promptId === 'string' ? value.promptId.slice(0, 200) : '',
      updatedAt: Number(value.updatedAt) || 0,
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
        .map((r) => ({ id: String(r.id || ''), name: r.name.slice(0, 120), command: r.command.slice(0, 2000), cwd: String(r.cwd || '').slice(0, 500), url: String(r.url || '').slice(0, 500) }));
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
    if (raw.drafts && typeof raw.drafts === 'object') {
      for (const [key, value] of Object.entries(raw.drafts).slice(0, LIMITS.drafts)) {
        const draft = sanitizeDraft(value);
        if (draft) data.drafts[key] = draft;
      }
    }
    if (raw.patchApprovals && typeof raw.patchApprovals === 'object') {
      for (const [key, value] of Object.entries(raw.patchApprovals).slice(0, 500)) {
        if (value && typeof value.hash === 'string') data.patchApprovals[key] = { hash: value.hash.slice(0, 64), at: Number(value.at) || 0 };
      }
    }
    if (raw.queues && typeof raw.queues === 'object') {
      for (const [key, value] of Object.entries(raw.queues)) {
        if (!value || !Array.isArray(value.items)) continue;
        data.queues[key] = {
          paused: Boolean(value.paused),
          items: value.items.filter((i) => i && typeof i.title === 'string').slice(0, LIMITS.queuePerProject)
            .map((i) => ({ id: String(i.id || ''), title: i.title.slice(0, 200), text: String(i.text || '').slice(0, 20000), status: ['queued', 'running', 'done', 'skipped'].includes(i.status) ? i.status : 'queued', createdAt: Number(i.createdAt) || 0 })),
        };
      }
    }
    if (raw.feedback && typeof raw.feedback === 'object') {
      for (const [key, items] of Object.entries(raw.feedback)) {
        if (!Array.isArray(items)) continue;
        data.feedback[key] = items.filter((i) => i && typeof i.text === 'string').slice(-LIMITS.feedbackPerProject)
          .map((i) => ({ id: String(i.id || ''), text: i.text.slice(0, 4000), state: ['saved', 'copied', 'acknowledged'].includes(i.state) ? i.state : 'saved', at: Number(i.at) || 0 }));
      }
    }
    if (raw.goalPreps && typeof raw.goalPreps === 'object') {
      for (const [key, value] of Object.entries(raw.goalPreps)) {
        if (value && typeof value.criteria === 'string') {
          data.goalPreps[key] = { criteria: value.criteria.slice(0, 4000), maxTurns: Math.max(1, Math.min(50, Number(value.maxTurns) || 5)), maxMinutes: Math.max(1, Math.min(1440, Number(value.maxMinutes) || 60)), updatedAt: Number(value.updatedAt) || 0 };
        }
      }
    }
    if (Array.isArray(raw.schedules)) {
      data.schedules = raw.schedules.filter((s) => s && typeof s.name === 'string' && typeof s.recipeId === 'string').slice(0, LIMITS.schedules)
        .map((s) => ({ id: String(s.id || ''), name: s.name.slice(0, 120), recipeId: s.recipeId, intervalHours: Math.max(0.25, Math.min(24 * 30, Number(s.intervalHours) || 24)), enabled: s.enabled !== false, lastRunAt: Number(s.lastRunAt) || 0, createdAt: Number(s.createdAt) || 0 }));
    }
    if (raw.notes && typeof raw.notes === 'object') {
      for (const [key, items] of Object.entries(raw.notes)) {
        if (!Array.isArray(items)) continue;
        data.notes[key] = items.filter((n) => n && typeof n.title === 'string').slice(0, LIMITS.notesPerProject)
          .map((n) => ({ id: String(n.id || ''), title: n.title.slice(0, 200), body: String(n.body || '').slice(0, 8000), pinned: Boolean(n.pinned), updatedAt: Number(n.updatedAt) || 0 }));
      }
    }
    if (Array.isArray(raw.skills)) {
      data.skills = raw.skills.filter((s) => s && typeof s.name === 'string' && typeof s.content === 'string').slice(0, LIMITS.skills)
        .map((s) => ({ id: String(s.id || ''), name: s.name.slice(0, 120), content: s.content.slice(0, 20000), source: String(s.source || 'local').slice(0, 500), projects: Array.isArray(s.projects) ? s.projects.filter((p) => typeof p === 'string').slice(0, 100) : [], updatedAt: Number(s.updatedAt) || 0 }));
    }
    if (raw.chats && typeof raw.chats === 'object') {
      for (const [key, items] of Object.entries(raw.chats)) {
        if (!Array.isArray(items)) continue;
        data.chats[key] = items.filter((c) => c && typeof c.label === 'string').slice(0, LIMITS.chatsPerProject)
          .map((c) => ({ id: String(c.id || ''), label: c.label.slice(0, 200), url: String(c.url || '').slice(0, 1000), note: String(c.note || '').slice(0, 1000), pinned: Boolean(c.pinned), updatedAt: Number(c.updatedAt) || 0 }));
      }
    }
    if (Array.isArray(raw.sshTargets)) {
      data.sshTargets = raw.sshTargets.filter((t) => t && typeof t.name === 'string' && typeof t.host === 'string').slice(0, LIMITS.sshTargets)
        .map((t) => ({ id: String(t.id || ''), name: t.name.slice(0, 120), host: t.host.slice(0, 255), user: String(t.user || '').slice(0, 80), port: Math.max(1, Math.min(65535, Number(t.port) || 22)), remoteDir: String(t.remoteDir || '').slice(0, 500) }));
    }
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
      listRecipes(workspace) {
        // F20: a project's command list = recipes pinned to the project or
        // one of its subdirectories, plus shared recipes (no cwd). Sibling
        // folders that merely share a name prefix do not leak in. No
        // argument lists everything; an explicitly empty project lists none.
        if (workspace === undefined) return data.recipes.slice();
        if (!String(workspace).trim()) return [];
        const project = String(workspace).replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
        return data.recipes.filter((recipe) => {
          const cwd = String(recipe.cwd || '').replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
          return !cwd || cwd === project || cwd.startsWith(`${project}/`);
        });
      },
      upsertRecipe({ id, name, command, cwd, url }) {
        const cleanName = String(name || '').trim();
        const cleanCommand = String(command || '').trim();
        if (!cleanName) throw new Error('Tên lệnh không được trống.');
        if (!cleanCommand) throw new Error('Lệnh không được trống.');
        const cleanUrl = String(url || '').trim().slice(0, 500);
        const existing = id ? data.recipes.find((r) => r.id === id) : null;
        if (existing) { existing.name = cleanName.slice(0, 120); existing.command = cleanCommand.slice(0, 2000); existing.cwd = String(cwd || '').slice(0, 500); existing.url = cleanUrl; }
        else {
          if (data.recipes.length >= LIMITS.recipes) throw new Error('Danh sách lệnh đã lưu đã đầy.');
          data.recipes.push({ id: nextId('recipe'), name: cleanName.slice(0, 120), command: cleanCommand.slice(0, 2000), cwd: String(cwd || '').slice(0, 500), url: cleanUrl });
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
      hasNotified(eventId) { return data.notified.includes(String(eventId || '').trim()); },

      // ---- F02 per-project drafts ----
      getDraft(workspace) {
        const draft = data.drafts[workspaceKeyOf(workspace)];
        return draft ? { ...draft, fields: { ...draft.fields } } : null;
      },
      saveDraft(workspace, draft) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        // A plain empty string clears the draft; any other save MERGES into
        // the stored draft, so updating just the preview text never loses
        // the task type, form fields or selected prompt (and vice versa).
        if (typeof draft === 'string' && !draft.trim()) { delete data.drafts[key]; persist(); return null; }
        const incoming = sanitizeDraft(draft);
        if (!incoming) return null;
        const existing = data.drafts[key];
        const merged = existing ? {
          text: typeof draft === 'string' || typeof draft?.text === 'string' ? incoming.text : existing.text,
          type: draft && typeof draft === 'object' && typeof draft.type === 'string' ? incoming.type : existing.type,
          fields: draft && typeof draft === 'object' && draft.fields && typeof draft.fields === 'object' ? { ...existing.fields, ...incoming.fields } : existing.fields,
          promptId: draft && typeof draft === 'object' && typeof draft.promptId === 'string' ? incoming.promptId : existing.promptId,
        } : incoming;
        const hasContent = merged.text.trim() || merged.promptId || Object.values(merged.fields).some((value) => value.trim());
        if (!hasContent) { delete data.drafts[key]; persist(); return null; }
        if (!existing && Object.keys(data.drafts).length >= LIMITS.drafts) throw new Error('Kho nháp đã đầy.');
        merged.updatedAt = Date.now();
        data.drafts[key] = merged;
        persist();
        return this.getDraft(workspace);
      },
      clearDraft(workspace) { delete data.drafts[workspaceKeyOf(workspace)]; persist(); },

      // ---- F10 patch approvals bound to the exact diff content ----
      approvePatch(rel, diffHash) {
        const key = String(rel || '').replace(/\\/g, '/');
        if (!key || !diffHash) throw new Error('Thiếu tệp hoặc phiên bản diff để duyệt.');
        data.patchApprovals[key] = { hash: String(diffHash), at: Date.now() };
        persist();
        return data.patchApprovals[key];
      },
      patchApproval(rel) { return data.patchApprovals[String(rel || '').replace(/\\/g, '/')] || null; },
      isPatchApproved(rel, diffHash) {
        const approval = this.patchApproval(rel);
        return Boolean(approval && diffHash && approval.hash === diffHash);
      },
      revokePatchApproval(rel) { delete data.patchApprovals[String(rel || '').replace(/\\/g, '/')]; persist(); },

      // ---- F15 bounded work queue per project ----
      queueFor(workspace) {
        const queue = data.queues[workspaceKeyOf(workspace)];
        return queue ? { paused: queue.paused, items: queue.items.slice() } : { paused: false, items: [] };
      },
      enqueue(workspace, { title, text }) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const cleanTitle = String(title || '').trim();
        if (!cleanTitle) throw new Error('Tên việc trong hàng đợi không được trống.');
        const queue = data.queues[key] || (data.queues[key] = { paused: false, items: [] });
        if (queue.items.length >= LIMITS.queuePerProject) throw new Error('Hàng đợi đã đầy.');
        const item = { id: nextId('queue'), title: cleanTitle.slice(0, 200), text: String(text || '').slice(0, 20000), status: 'queued', createdAt: Date.now() };
        queue.items.push(item);
        persist();
        return item;
      },
      moveQueueItem(workspace, id, direction) {
        const queue = data.queues[workspaceKeyOf(workspace)];
        if (!queue) return;
        const index = queue.items.findIndex((i) => i.id === id);
        const target = index + (direction < 0 ? -1 : 1);
        if (index < 0 || target < 0 || target >= queue.items.length) return;
        [queue.items[index], queue.items[target]] = [queue.items[target], queue.items[index]];
        persist();
      },
      setQueueItemStatus(workspace, id, status) {
        const queue = data.queues[workspaceKeyOf(workspace)];
        const item = queue?.items.find((i) => i.id === id);
        if (item && ['queued', 'running', 'done', 'skipped'].includes(status)) { item.status = status; persist(); }
      },
      removeQueueItem(workspace, id) {
        const queue = data.queues[workspaceKeyOf(workspace)];
        if (queue) { queue.items = queue.items.filter((i) => i.id !== id); persist(); }
      },
      setQueuePaused(workspace, paused) {
        const key = workspaceKeyOf(workspace);
        const queue = data.queues[key] || (data.queues[key] = { paused: false, items: [] });
        queue.paused = Boolean(paused);
        persist();
      },
      nextQueuedItem(workspace) {
        const queue = data.queues[workspaceKeyOf(workspace)];
        if (!queue || queue.paused) return null;
        return queue.items.find((i) => i.status === 'queued') || null;
      },

      // ---- F18 steering notes with saved/copied/acknowledged states ----
      listFeedback(workspace) { return (data.feedback[workspaceKeyOf(workspace)] || []).slice(); },
      addFeedback(workspace, text) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const clean = String(text || '').trim();
        if (!clean) throw new Error('Nội dung điều chỉnh không được trống.');
        const items = data.feedback[key] || (data.feedback[key] = []);
        const item = { id: nextId('feedback'), text: clean.slice(0, 4000), state: 'saved', at: Date.now() };
        items.push(item);
        if (items.length > LIMITS.feedbackPerProject) data.feedback[key] = items.slice(-LIMITS.feedbackPerProject);
        persist();
        return item;
      },
      setFeedbackState(workspace, id, state) {
        const item = (data.feedback[workspaceKeyOf(workspace)] || []).find((i) => i.id === id);
        if (item && ['saved', 'copied', 'acknowledged'].includes(state)) { item.state = state; persist(); }
      },

      // ---- F23 bounded goal preparation (preparation only, no loop) ----
      goalPrepFor(workspace) { return data.goalPreps[workspaceKeyOf(workspace)] || null; },
      setGoalPrep(workspace, { criteria, maxTurns, maxMinutes }) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const clean = String(criteria || '').trim();
        if (!clean) throw new Error('Tiêu chí mục tiêu không được trống.');
        data.goalPreps[key] = {
          criteria: clean.slice(0, 4000),
          maxTurns: Math.max(1, Math.min(50, Number(maxTurns) || 5)),
          maxMinutes: Math.max(1, Math.min(1440, Number(maxMinutes) || 60)),
          updatedAt: Date.now(),
        };
        persist();
        return data.goalPreps[key];
      },
      clearGoalPrep(workspace) { delete data.goalPreps[workspaceKeyOf(workspace)]; persist(); },

      // ---- F24 schedules for saved recipes (evaluated while the app runs) ----
      listSchedules() { return data.schedules.slice(); },
      upsertSchedule({ id, name, recipeId, intervalHours, enabled }) {
        const cleanName = String(name || '').trim();
        if (!cleanName) throw new Error('Tên lịch không được trống.');
        if (!data.recipes.some((r) => r.id === recipeId)) throw new Error('Lịch phải gắn với một lệnh đã lưu.');
        const existing = id ? data.schedules.find((s) => s.id === id) : null;
        if (existing) {
          existing.name = cleanName.slice(0, 120); existing.recipeId = recipeId;
          existing.intervalHours = Math.max(0.25, Math.min(24 * 30, Number(intervalHours) || 24));
          existing.enabled = enabled !== false;
        } else {
          if (data.schedules.length >= LIMITS.schedules) throw new Error('Danh sách lịch đã đầy.');
          data.schedules.push({ id: nextId('schedule'), name: cleanName.slice(0, 120), recipeId, intervalHours: Math.max(0.25, Math.min(24 * 30, Number(intervalHours) || 24)), enabled: enabled !== false, lastRunAt: 0, createdAt: Date.now() });
        }
        persist();
        return existing || data.schedules[data.schedules.length - 1];
      },
      removeSchedule(id) { data.schedules = data.schedules.filter((s) => s.id !== id); persist(); },
      markScheduleRun(id, at = Date.now()) {
        const schedule = data.schedules.find((s) => s.id === id);
        if (schedule) { schedule.lastRunAt = at; persist(); }
      },
      dueSchedules(now = Date.now()) {
        return data.schedules.filter((s) => s.enabled && now - (s.lastRunAt || s.createdAt || 0) >= s.intervalHours * 3600 * 1000);
      },
      nextRunAt(schedule) {
        if (!schedule) return null;
        return (schedule.lastRunAt || schedule.createdAt || 0) + schedule.intervalHours * 3600 * 1000;
      },

      // ---- F32 project notes ----
      listNotes(workspace) {
        return (data.notes[workspaceKeyOf(workspace)] || []).slice()
          .sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.updatedAt - a.updatedAt);
      },
      upsertNote(workspace, { id, title, body, pinned }) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const cleanTitle = String(title || '').trim();
        if (!cleanTitle) throw new Error('Tiêu đề ghi chú không được trống.');
        const items = data.notes[key] || (data.notes[key] = []);
        const existing = id ? items.find((n) => n.id === id) : null;
        if (existing) {
          existing.title = cleanTitle.slice(0, 200); existing.body = String(body || '').slice(0, 8000);
          existing.pinned = Boolean(pinned); existing.updatedAt = Date.now();
        } else {
          if (items.length >= LIMITS.notesPerProject) throw new Error('Ghi chú dự án đã đầy.');
          items.push({ id: nextId('note'), title: cleanTitle.slice(0, 200), body: String(body || '').slice(0, 8000), pinned: Boolean(pinned), updatedAt: Date.now() });
        }
        persist();
        return existing || items[items.length - 1];
      },
      removeNote(workspace, id) {
        const key = workspaceKeyOf(workspace);
        if (data.notes[key]) { data.notes[key] = data.notes[key].filter((n) => n.id !== id); persist(); }
      },

      // ---- F34 skills library (instructions only, per-project enable) ----
      listSkills() { return data.skills.slice(); },
      upsertSkill({ id, name, content, source }) {
        const cleanName = String(name || '').trim();
        const cleanContent = String(content || '');
        if (!cleanName) throw new Error('Tên skill không được trống.');
        if (!cleanContent.trim()) throw new Error('Nội dung hướng dẫn skill không được trống.');
        const existing = id ? data.skills.find((s) => s.id === id) : null;
        if (existing) {
          existing.name = cleanName.slice(0, 120); existing.content = cleanContent.slice(0, 20000);
          existing.source = String(source || 'local').slice(0, 500); existing.updatedAt = Date.now();
        } else {
          if (data.skills.length >= LIMITS.skills) throw new Error('Thư viện skills đã đầy.');
          data.skills.push({ id: nextId('skill'), name: cleanName.slice(0, 120), content: cleanContent.slice(0, 20000), source: String(source || 'local').slice(0, 500), projects: [], updatedAt: Date.now() });
        }
        persist();
        return existing || data.skills[data.skills.length - 1];
      },
      removeSkill(id) { data.skills = data.skills.filter((s) => s.id !== id); persist(); },
      setSkillForProject(id, workspace, enabled) {
        const skill = data.skills.find((s) => s.id === id);
        if (!skill) return;
        const key = workspaceKeyOf(workspace);
        skill.projects = enabled ? [...new Set([...skill.projects, key])] : skill.projects.filter((p) => p !== key);
        persist();
      },
      skillsForProject(workspace) {
        const key = workspaceKeyOf(workspace);
        return data.skills.filter((s) => s.projects.includes(key));
      },

      // ---- F39 conversation registry (user-supplied labels/URLs only) ----
      listChats(workspace) {
        return (data.chats[workspaceKeyOf(workspace)] || []).slice()
          .sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.updatedAt - a.updatedAt);
      },
      upsertChat(workspace, { id, label, url, note, pinned }) {
        const key = workspaceKeyOf(workspace);
        if (!key) throw new Error('Chưa chọn dự án.');
        const cleanLabel = String(label || '').trim();
        if (!cleanLabel) throw new Error('Nhãn hội thoại không được trống.');
        const items = data.chats[key] || (data.chats[key] = []);
        const existing = id ? items.find((c) => c.id === id) : null;
        if (existing) {
          existing.label = cleanLabel.slice(0, 200); existing.url = String(url || '').slice(0, 1000);
          existing.note = String(note || '').slice(0, 1000); existing.pinned = Boolean(pinned); existing.updatedAt = Date.now();
        } else {
          if (items.length >= LIMITS.chatsPerProject) throw new Error('Danh sách hội thoại đã đầy.');
          items.push({ id: nextId('chat'), label: cleanLabel.slice(0, 200), url: String(url || '').slice(0, 1000), note: String(note || '').slice(0, 1000), pinned: Boolean(pinned), updatedAt: Date.now() });
        }
        persist();
        return existing || items[items.length - 1];
      },
      removeChat(workspace, id) {
        const key = workspaceKeyOf(workspace);
        if (data.chats[key]) { data.chats[key] = data.chats[key].filter((c) => c.id !== id); persist(); }
      },

      // ---- F40 named SSH targets ----
      listSshTargets() { return data.sshTargets.slice(); },
      upsertSshTarget({ id, name, host, user, port, remoteDir }) {
        const cleanName = String(name || '').trim();
        const cleanHost = String(host || '').trim();
        if (!cleanName) throw new Error('Tên máy SSH không được trống.');
        if (!cleanHost) throw new Error('Host SSH không được trống.');
        const existing = id ? data.sshTargets.find((t) => t.id === id) : null;
        const value = {
          name: cleanName.slice(0, 120), host: cleanHost.slice(0, 255),
          user: String(user || '').trim().slice(0, 80),
          port: Math.max(1, Math.min(65535, Number(port) || 22)),
          remoteDir: String(remoteDir || '').trim().slice(0, 500),
        };
        if (existing) Object.assign(existing, value);
        else {
          if (data.sshTargets.length >= LIMITS.sshTargets) throw new Error('Danh sách máy SSH đã đầy.');
          data.sshTargets.push({ id: nextId('ssh'), ...value });
        }
        persist();
        return existing || data.sshTargets[data.sshTargets.length - 1];
      },
      removeSshTarget(id) { data.sshTargets = data.sshTargets.filter((t) => t.id !== id); persist(); },
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
  // Canonical task projection (task_snapshot_projection.py + main.js
  // canonicalTaskStateFromControl): steps[].text, test_results[],
  // modified_files[]. Legacy names are accepted as fallback only.
  const DONE_STEP_STATUSES = ['done', 'completed', 'complete', 'passed', 'success'];
  function taskSteps(task) { return Array.isArray(task?.steps) ? task.steps : []; }
  function stepText(step) { return String(step?.text || step?.title || step?.name || step?.step || ''); }
  function taskTests(task) {
    if (Array.isArray(task?.test_results)) return task.test_results;
    return Array.isArray(task?.tests) ? task.tests : [];
  }
  function testFailed(test) {
    const status = String(test?.status || '').toLowerCase();
    if (['failed', 'fail', 'error'].includes(status)) return true;
    return typeof test?.exit_code === 'number' && test.exit_code !== 0 && status !== 'passed';
  }
  function testLabel(test) { return String(test?.command || test?.name || test?.title || 'kiểm thử'); }
  function taskFiles(task) {
    const raw = Array.isArray(task?.modified_files) ? task.modified_files
      : (Array.isArray(task?.files) ? task.files : (Array.isArray(task?.changed_files) ? task.changed_files : []));
    return raw.map((f) => (typeof f === 'string' ? f : String(f?.path || f?.file || ''))).filter(Boolean);
  }

  function taskRunId(task) {
    // Canonical run-id path (same precedence as handoffPreview): the panel
    // task state carries the run under orchestration first.
    return String(task?.orchestration?.run_id || task?.run_id || '');
  }

  function capsuleView(capsule) {
    if (!capsule || typeof capsule !== 'object') return null;
    const payload = capsule.payload && typeof capsule.payload === 'object' ? capsule.payload : {};
    const runtime = payload.runtime && typeof payload.runtime === 'object' ? payload.runtime : {};
    return {
      capsuleId: String(capsule.capsule_id || ''),
      version: capsule.version ?? null,
      status: String(capsule.status || ''),
      createdAt: String(capsule.created_at || ''),
      runId: String(capsule.run_id || ''),
      sha256: String(capsule.sha256 || ''),
      objective: String(runtime.objective || payload.objective || ''),
      panelSummary: String(payload.panel_summary || ''),
      baseHead: String(runtime.base_head || ''),
      taskStatus: String(runtime.task_status || ''),
    };
  }

  function headMatches(baseHead, currentHead) {
    const base = String(baseHead || '').trim().toLowerCase();
    const current = String(currentHead || '').trim().toLowerCase();
    if (!base || !current || Math.min(base.length, current.length) < 7) return null;
    return base.startsWith(current) || current.startsWith(base);
  }

  function handoffPreview(task) {
    if (!task || typeof task !== 'object') return null;
    const steps = taskSteps(task);
    const done = steps.filter((s) => DONE_STEP_STATUSES.includes(String(s?.status || '').toLowerCase()));
    const pending = steps.filter((s) => !DONE_STEP_STATUSES.includes(String(s?.status || '').toLowerCase()));
    const tests = taskTests(task);
    const failedTests = tests.filter(testFailed);
    const detailsAvailable = task.details_available !== false;
    return {
      taskId: String(task.task_id || task.id || ''),
      runId: String(task.orchestration?.run_id || task.run_id || ''),
      detailsAvailable,
      objective: String(task.objective || task.title || ''),
      status: String(task.status || ''),
      doneSteps: done.map(stepText).filter(Boolean),
      unverified: [
        ...pending.map((s) => `Bước chưa xong: ${stepText(s)}`),
        ...failedTests.map((t) => `Test lỗi: ${testLabel(t)}`),
        ...(detailsAvailable && tests.length === 0 ? ['Chưa có kết quả kiểm thử nào được ghi nhận.'] : []),
      ].filter(Boolean),
      nextStep: String(task.next_step || task.nextStep || ''),
      currentStep: String(task.current_step || task.currentStep || ''),
      files: taskFiles(task),
    };
  }

  function formatHandoffText(preview) {
    if (!preview) return '';
    const lines = [];
    if (!preview.detailsAvailable) {
      lines.push('Chưa lấy được chi tiết task (details_available=false) — dưới đây chỉ có mục tiêu và trạng thái tổng, không suy ra test/tệp.');
    }
    lines.push(`Mục tiêu: ${preview.objective || '—'}`);
    lines.push(`Đã làm: ${preview.doneSteps.length ? preview.doneSteps.join('; ') : 'chưa ghi nhận bước hoàn thành'}`);
    lines.push(`Chưa kiểm chứng: ${preview.unverified.length ? preview.unverified.join('; ') : 'không có'}`);
    lines.push(`Bước tiếp theo: ${preview.nextStep || preview.currentStep || '—'}`);
    if (preview.files.length) lines.push(`Tệp liên quan: ${preview.files.join(', ')}`);
    return lines.join('\n');
  }

  // ---- small content hash (binds a local record to exact text, e.g. a diff) ----
  function hashText(text) {
    const source = String(text || '');
    let h1 = 0x811c9dc5;
    for (let i = 0; i < source.length; i += 1) {
      h1 ^= source.charCodeAt(i);
      h1 = Math.imul(h1, 0x01000193) >>> 0;
    }
    return `fnv1a-${h1.toString(16).padStart(8, '0')}-${source.length}`;
  }

  // ---- A1 context package with real content + version labels ----
  // parts: [{ path, size, content|null, truncated, hash }]
  function contextContentText(workspace, parts) {
    const lines = [`Ngữ cảnh cho dự án ${workspace}:`];
    for (const part of Array.isArray(parts) ? parts : []) {
      lines.push('');
      lines.push(`### ${part.path}${part.size != null ? ` (${part.size} bytes)` : ''}${part.hash ? ` · rev ${part.hash}` : ''}`);
      if (part.content == null) lines.push('[Không đọc được nội dung — chỉ có đường dẫn]');
      else {
        lines.push(part.content);
        if (part.truncated) lines.push('[Nội dung đã bị cắt theo hạn mức đọc]');
      }
    }
    return lines.join('\n');
  }

  // ---- F17 plan view over the canonical task projection ----
  function planView(task) {
    if (!task || typeof task !== 'object') return null;
    const steps = taskSteps(task).map((s) => ({
      text: stepText(s),
      status: String(s?.status || 'pending'),
      done: DONE_STEP_STATUSES.includes(String(s?.status || '').toLowerCase()),
    }));
    const tests = taskTests(task);
    const blockers = [
      ...(task.failure ? [`Lỗi: ${String(task.failure)}`] : []),
      ...tests.filter(testFailed).map((t) => `Test lỗi: ${testLabel(t)}`),
      ...steps.filter((s) => s.status === 'blocked' || s.status === 'failed').map((s) => `Bước ${s.status}: ${s.text}`),
    ];
    return {
      objective: String(task.objective || ''),
      status: String(task.status || ''),
      steps,
      doneCount: steps.filter((s) => s.done).length,
      testsRun: tests.length,
      testsFailed: tests.filter(testFailed).length,
      blockers,
      detailsAvailable: task.details_available !== false,
    };
  }

  // ---- F23 bounded goal continuation request (text preparation only) ----
  function goalRequestText(workspace, prep) {
    if (!prep) return '';
    return [
      `Tiếp tục theo mục tiêu cho dự án ${workspace}.`,
      `Tiêu chí hoàn thành: ${prep.criteria}`,
      `Giới hạn: tối đa ${prep.maxTurns} lượt và ${prep.maxMinutes} phút; dừng ngay khi đạt tiêu chí, khi gặp blocker cần người dùng quyết định, hoặc khi hết giới hạn.`,
      'Báo cáo rõ phần đã kiểm chứng và phần chưa kiểm chứng trước khi dừng.',
    ].join('\n');
  }

  // ---- F30 task report export (Markdown/plain text from real task data) ----
  function buildReportText(task, { generatedAt } = {}) {
    const preview = handoffPreview(task);
    if (!preview) return '';
    const plan = planView(task);
    const report = task?.last_build_report || null;
    const lines = [
      '# Báo cáo tác vụ',
      '',
      `- Mục tiêu: ${preview.objective || '—'}`,
      `- Trạng thái: ${preview.status || '—'}`,
      `- Task: ${preview.taskId || '—'}${preview.runId ? ` · Run: ${preview.runId}` : ''}`,
      `- Thời điểm xuất: ${generatedAt || new Date().toISOString()}`,
      '',
      '## Đã làm',
      ...(plan?.steps.length ? plan.steps.map((s) => `- [${s.done ? 'x' : ' '}] ${s.text} (${s.status})`) : ['- Chưa ghi nhận bước nào.']),
      '',
      '## Kiểm chứng',
      ...(taskTests(task).length
        ? taskTests(task).map((t) => `- ${testFailed(t) ? 'LỖI' : 'ĐẠT'} · ${testLabel(t)}${t.duration_ms != null ? ` · ${t.duration_ms} ms` : ''}`)
        : ['- Chưa có kết quả kiểm thử được ghi nhận.']),
      '',
      '## Tệp đã thay đổi',
      ...(preview.files.length ? preview.files.map((f) => `- ${f}`) : ['- Chưa ghi nhận tệp thay đổi.']),
      '',
      '## Sản phẩm build',
      ...(report
        ? [`- Trạng thái: ${report.overall_status || '—'} · ${report.project?.type || ''} v${report.project?.version || '?'}`,
          ...(report.artifacts || []).map((a) => `- ${a.path}${a.sha256 ? ` · sha256 ${String(a.sha256).slice(0, 16)}…` : ''}`)]
        : ['- Chưa có báo cáo build.']),
      '',
      '## Chưa kiểm chứng / còn lại',
      ...(preview.unverified.length ? preview.unverified.map((u) => `- ${u}`) : ['- Không có mục chưa kiểm chứng được ghi nhận.']),
      '',
      `Bước tiếp theo: ${preview.nextStep || preview.currentStep || '—'}`,
    ];
    return lines.join('\n');
  }

  // ---- F40 ssh argv builder (no shell string interpolation) ----
  function sshArgs(target, remoteCommand) {
    if (!target || !target.host) throw new Error('Thiếu máy SSH đích.');
    const destination = target.user ? `${target.user}@${target.host}` : String(target.host);
    const args = ['-p', String(target.port || 22), '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', destination];
    const dir = String(target.remoteDir || '').trim();
    const command = String(remoteCommand || '').trim();
    const remote = dir ? `cd ${dir} && ${command}` : command;
    if (remote) args.push(remote);
    return args;
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
    taskSteps, stepText, taskTests, testFailed, testLabel, taskFiles,
    taskRunId, capsuleView, headMatches,
    hashText, contextContentText, planView, goalRequestText, buildReportText, sshArgs,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.WorkHubStore = api;
})(typeof window !== 'undefined' ? window : globalThis);
