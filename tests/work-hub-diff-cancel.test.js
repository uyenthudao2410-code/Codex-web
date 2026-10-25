'use strict';

// GUI round 4 residual (a): a diff load cancelled by resetProjectView must
// show a cancelled state, never silently fall back to the pristine
// placeholder — and an old load resolving after a newer one started must
// not clobber the new load's view. Slices the real requestScope,
// resetProjectView, renderDiffMeta and renderDiff out of
// renderer/work-hub.js and runs them in vm with stubbed DOM/IPC — same
// pattern as tests/work-hub-p4-display.test.js. No Electron.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer/work-hub.js'), 'utf8');
function section(start, end) {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing UI fragment: ${start}`);
  return source.slice(from, to);
}

const PRISTINE = 'Chọn một tệp để xem thay đổi.';
const CANCELLED = 'Tải diff bị hủy do dữ liệu làm việc thay đổi — bấm lại để xem.';

function node(text = '') {
  return {
    text, children: [], value: '', disabled: false, hidden: false,
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; this.text = ''; },
    addEventListener() {},
    get textContent() { return this.text + this.children.map((child) => child.textContent).join(''); },
    set textContent(value) { this.text = String(value ?? ''); this.children = []; },
  };
}

function fixture() {
  const boxes = new Map();
  for (const id of ['whDiff', 'whDiffMeta', 'whCodeResults', 'whGitList', 'whGitLog',
    'whTaskFiles', 'whArtifactImage', 'whCapsuleView', 'whImportList', 'whPatchApproval',
    'whCosSessions', 'whCodexChatLog', 'whCodexChatEvents', 'whCodexChatThreads', 'whGitReview',
    'whCodeQuery', 'whEditor', 'whPreview', 'whFilePath', 'whFileSize', 'whImportDest',
    'whSnippetName', 'whSnippetBody', 'whFeedbackText', 'whQueueTitle', 'whNoteTitle',
    'whNoteBody', 'whChatLabel', 'whChatUrl', 'whCodexChatInput', 'whGitReviewFrom',
    'whGitReviewTo', 'whGitReviewMeta', 'whCodexChatState', 'whCodexChatLink',
    'whCodexChatHandoffInfo', 'whViewerAddBasket', 'whEditFile', 'whSaveFile', 'whBlame',
    'whCancelEditFile', 'whViewer', 'whViewerTitle', 'whCosEvents']) boxes.set(id, node());
  const pending = [];
  const context = vm.createContext({
    ui: {
      requests: {}, gen: 0, diffRel: '', diffText: '', diffHead: '', diffFingerprint: '',
      diffStale: false, gitHead: '', diffLoading: false, viewerRel: '', viewerHash: '',
      viewerContent: null, viewerEditable: false, dirRel: '', gitReview: null,
      gitReviewHead: '', gitReviewBinding: null, taskPayload: null, pendingImports: [],
      importResults: [],
    },
    currentProject: () => 'E:/Projects/alpha',
    $: (selector) => boxes.get(selector.slice(1)) || null,
    activateTab: () => {},
    renderPatchApproval: () => {},
    renderDiffLines: (box, text) => { box.textContent = text; return { added: 1, removed: 0 }; },
    unwrap: (result) => (result && typeof result === 'object' && 'ok' in result)
      ? (result.ok ? result.data : null) : result,
    stopCodexChatPolling: () => {},
    setStatus: () => {},
    window: {
      mcpAssistant: { workhubGitDiff: () => new Promise((resolve) => pending.push(resolve)) },
    },
  });
  vm.runInContext(section('  function requestScope(', '  function saveCurrentDraft('), context);
  vm.runInContext(section('  function resetProjectView(', '  function renderWorkspace('), context);
  vm.runInContext(section('  function diffIsStale(', '  function renderDiffLines('), context);
  vm.runInContext(section('  async function renderDiff(', '  function panelTaskLink('), context);
  return {
    context, boxes, pending,
    diffText: () => boxes.get('whDiff').textContent,
    renderDiff: (rel) => context.renderDiff(rel),
    reset: () => context.resetProjectView(),
    resolveNext: (data) => pending.shift()(data),
  };
}

test('(a) reset mid-load: viewer shows the cancelled notice, not the pristine placeholder', async () => {
  const fx = fixture();
  const load = fx.renderDiff('a.txt');
  assert.equal(fx.diffText(), 'Đang đọc thay đổi…');
  fx.reset();
  assert.equal(fx.diffText(), CANCELLED);
  assert.notEqual(fx.diffText(), PRISTINE);
  fx.resolveNext({ diff: '--- a\n+++ b\n', head: 'abc', fingerprint: 'def' });
  await load;
  assert.equal(fx.diffText(), CANCELLED);
});

test('(a) fresh reset with no load in flight keeps the pristine placeholder', () => {
  const fx = fixture();
  fx.reset();
  assert.equal(fx.diffText(), PRISTINE);
});

test('(a) an old load resolving after a newer one started does not clobber the new load', async () => {
  const fx = fixture();
  const oldLoad = fx.renderDiff('a.txt');
  fx.reset();
  assert.equal(fx.diffText(), CANCELLED);
  const newLoad = fx.renderDiff('b.txt');
  assert.equal(fx.diffText(), 'Đang đọc thay đổi…');
  fx.resolveNext({ diff: 'OLD-DIFF', head: 'abc', fingerprint: 'def' });
  await oldLoad;
  assert.equal(fx.diffText(), 'Đang đọc thay đổi…');
  fx.resolveNext({ diff: 'NEW-DIFF', head: 'abc', fingerprint: 'def' });
  await newLoad;
  assert.equal(fx.diffText(), 'NEW-DIFF');
});
