const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { componentOwnsPath } = require('../electron/services/componentRevision');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

function dashboardStyleSources() {
  const inlineStyles = [...read('renderer/token-dashboard.html').matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g)].map((match) => match[1]);
  assert.ok(inlineStyles.length, 'standalone dashboard styles missing');
  return [['shared', read('renderer/dashboard.css')], ['standalone', inlineStyles.join('\n')]];
}

function loadTokenDashboardBootstrap(closeTokenDashboard) {
  const html = read('renderer/token-dashboard.html');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  const source = scripts.at(-1)?.[1];
  assert.ok(source, 'token dashboard inline bootstrap missing');

  const controls = new Map();
  const createControl = () => {
    const listeners = new Map();
    return {
      addEventListener(type, listener) { listeners.set(type, listener); },
      listener(type) { return listeners.get(type); }
    };
  };
  controls.set('themeToggleBtn', createControl());
  controls.set('closeManager', createControl());
  let fallbackCloseCalls = 0;
  const context = {
    window: {
      location: { search: '?theme=dark' },
      mcpAssistant: closeTokenDashboard ? { closeTokenDashboard } : undefined,
      close: () => { fallbackCloseCalls += 1; }
    },
    document: {
      documentElement: { setAttribute() {}, getAttribute() { return 'dark'; } },
      body: { dataset: {}, setAttribute() {} },
      getElementById(id) { return controls.get(id) || null; }
    },
    URLSearchParams,
    Promise
  };
  vm.runInNewContext(source, context, { filename: 'renderer/token-dashboard.html' });
  const close = controls.get('closeManager').listener('click');
  assert.equal(typeof close, 'function', 'token dashboard close handler missing');
  return {
    close,
    fallbackCloseCalls: () => fallbackCloseCalls
  };
}

function heartbeatPublisherSource() {
  const main = read('electron/main.js');
  const start = main.indexOf('    const publishRuntimeHeartbeat = () => {');
  const end = main.indexOf('\n    setInterval(() => { void publishRuntimeHeartbeat(); }, 5000).unref();', start);
  assert.ok(start >= 0 && end > start, 'runtime heartbeat publisher missing');
  return main.slice(start, end);
}

function makeWindow(messages, destroyed = false) {
  return {
    isDestroyed: () => destroyed,
    webContents: {
      send: (channel, payload) => messages.push({ channel, payload })
    }
  };
}

async function publishHeartbeat({ tokenDestroyed = false } = {}) {
  const managerMessages = [];
  const chatMessages = [];
  const tokenMessages = [];
  const status = { fullyReady: true, telemetryAvailable: true };
  const context = {
    runtimeHeartbeatInFlight: null,
    orchestrator: { lightweightSnapshot: async () => status },
    lastRecoveryProgressTime: null,
    sendManager: (channel, payload) => managerMessages.push({ channel, payload }),
    chatWindow: makeWindow(chatMessages),
    tokenWindow: makeWindow(tokenMessages, tokenDestroyed),
    registerUiRevision: () => Promise.resolve(),
    Promise
  };
  vm.runInNewContext(`${heartbeatPublisherSource()}\nglobalThis.publishRuntimeHeartbeat = publishRuntimeHeartbeat;`, context, {
    filename: 'electron/main.js#publishRuntimeHeartbeat'
  });
  await context.publishRuntimeHeartbeat();
  return { status, managerMessages, chatMessages, tokenMessages };
}

test('KPI metadata keeps typography without outer tile geometry', () => {
  for (const [label, source] of dashboardStyleSources()) {
    let metadataRules = 0;
    for (const match of source.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      if (!match[1].split(',').some((selector) => selector.trim() === '.da-tile-sub')) continue;
      metadataRules += 1;
      assert.doesNotMatch(match[2], /(?:^|;)\s*(?:height|min-height|max-height|grid-column)\s*:/i, label + ' metadata has tile geometry');
    }
    assert.ok(metadataRules > 0, label + ' metadata typography was removed');
  }
});
test('final narrow rules retain readable KPI tracks and populated analytics', () => {
  for (const [label, source] of dashboardStyleSources()) {
    const start = source.lastIndexOf('@media (max-width: 1080px)');
    assert.ok(start >= 0, label + ' narrow breakpoint missing');
    const rules = [...source.slice(start).matchAll(/([^{}]+)\{([^{}]*)\}/g)];
    const declarations = (selector) => {
      const matches = rules.filter((match) => match[1].trim() === selector);
      assert.equal(matches.length, 1, label + ' narrow rule missing or overridden: ' + selector);
      return matches[0][2];
    };
    assert.match(declarations('.da-grid-tiles'), /grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)\s*!important/);
    assert.match(declarations('.da-grid-tiles > article.da-tile'), /grid-column:\s*span 2\s*!important/);
    assert.match(declarations('.da-split-view-row'), /grid-template-columns:\s*minmax\(0,\s*1fr\)\s*!important/);
    const bars = declarations('.da-split-left .da-tools-card .da-bars');
    assert.match(bars, /max-height:\s*none\s*!important/);
    assert.match(bars, /overflow:\s*visible\s*!important/);
  }
});

test('standalone donut has no measured segments before the first snapshot', () => {
  for (const relative of ['renderer/token-dashboard.html']) {
    const html = read(relative);
    const donut = html.match(/<svg id="daDonut"[\s\S]*?<\/svg>/)?.[0];
    assert.ok(donut, relative + ' donut missing');
    assert.doesNotMatch(donut, /<circle\b/, relative + ' has unobserved initial segments');
    assert.match(donut, /id="daDonutTotal"[^>]*>—<\/text>/);
  }
});

test('token dashboard shows no fabricated numbers before the live snapshot', () => {
  const html = read('renderer/token-dashboard.html');
  assert.match(html, /<meta http-equiv="Content-Security-Policy" content="default-src 'self';/);
  assert.doesNotMatch(html, /fonts\.googleapis\.com|fonts\.gstatic\.com/);
  assert.doesNotMatch(html, /Math\.random\(\)/);
  for (const id of ['daChatTurnValue', 'daTokensTotal', 'daCostTotal', 'daDonutTotal', 'daToolCostTotal', 'daRealtimeTpm', 'daCoveragePolicy']) {
    const tag = html.match(new RegExp(`<[^>]+id="${id}"[^>]*>[\\s\\S]*?(</[a-z]+>|/>)`));
    assert.ok(tag, `token dashboard thiếu id ${id}`);
    assert.doesNotMatch(tag[0], /216\.8M|18\.4K|\$48\.25|43\.2K|đạt chuẩn 100%|142 lần|Đã đo 142/);
  }
  assert.match(html, /id="daTurnLog"/);
  assert.match(html, /Nhật ký lượt chat/);
  assert.match(html, /<script src="control-center\.js"><\/script>/);
  assert.match(html, /<script src="dashboard\.js"><\/script>/);
  assert.match(html, /themeToggleBtn/);
  assert.match(html, /Chưa có dữ liệu — đang chờ snapshot\./);
  assert.match(html, /Chưa có accepted-result evidence\./);
  assert.match(html, /Chưa có snapshot runtime/);
  assert.match(html, /Chờ snapshot overview; không có dữ liệu được tự tạo/);
  assert.match(html, /Chưa có lượt chat nào được đo/);
  assert.match(html, /Chưa có ước lượng controller/);
  for (const fabricatedValue of [
    'DESKTOP-6J643J4',
    'ac2514f',
    'main @ 2687ac8',
    'Last sync 09:41:02',
    'Production',
    '05/09/2026',
    '229 - 688',
    '110 reasoning',
    '89 kết quả',
    '420K token',
    '284K-852K',
    '00:29:49',
    '25 Triệu',
    '15 Triệu',
    '5 Triệu',
    '≈ 344',
    '16.2K',
    '4.8K'
  ]) {
    assert.doesNotMatch(html, new RegExp(fabricatedValue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  assert.doesNotMatch(html, /Standalone Preview Fallback/);
  assert.doesNotMatch(html, /Bộ lọc nâng cao|Xuất báo cáo dữ liệu/);
  assert.match(html, /const initialTheme = params\.get\('theme'\) \|\| 'light';/);
});

test('token dashboard opens in its own window with the shared manager preload', () => {
  const main = read('electron/main.js');
  assert.match(main, /let tokenWindow;/);
  assert.match(main, /function openTokenWindow\(\)/);
  assert.match(main, /token-dashboard\.html/);
  assert.match(main, /preload: path\.join\(__dirname, 'preload\.js'\)/);
  assert.match(main, /secureHandle\('token-dashboard:open'/);
  assert.match(main, /secureHandle\('token-dashboard:close'/);
  assert.match(main, /openTokenWindow\(\); return true/);
  assert.match(main, /tokenWindow\.on\('closed', \(\) => \{ tokenWindow = null; \}\)/);
  assert.doesNotMatch(main, /tokenWindow\.hide\(\)/);
  const preload = read('electron/preload.js');
  assert.match(preload, /openTokenDashboard: \(\) => ipcRenderer\.invoke\('token-dashboard:open'\)/);
  assert.match(preload, /closeTokenDashboard: \(\) => ipcRenderer\.invoke\('token-dashboard:close'\)/);
  const html = read('renderer/index.html');
  assert.match(html, /id="daTokenBoardButton"/);
  assert.match(html, /Bảng token/);
  const js = read('renderer/dashboard.js');
  assert.match(js, /byId\('daTokenBoardButton'\)\?\.addEventListener\('click'/);
  assert.match(js, /api\.openTokenDashboard\(\)/);
});

test('token dashboard close control invokes the exposed preload bridge', async () => {
  let bridgeCalls = 0;
  const harness = loadTokenDashboardBootstrap(async () => {
    bridgeCalls += 1;
    return { ok: true, data: true };
  });

  await harness.close();

  assert.equal(bridgeCalls, 1);
  assert.equal(harness.fallbackCloseCalls(), 0);
});

test('token dashboard falls back to window close if its close bridge fails', async () => {
  const rejected = loadTokenDashboardBootstrap(async () => { throw new Error('IPC unavailable'); });
  await rejected.close();
  assert.equal(rejected.fallbackCloseCalls(), 1);

  const failed = loadTokenDashboardBootstrap(async () => ({ ok: false, error: 'IPC unavailable' }));
  await failed.close();

  assert.equal(failed.fallbackCloseCalls(), 1);
});

test('runtime heartbeat reaches a live token window and skips a destroyed one', async () => {
  const live = await publishHeartbeat();
  assert.deepEqual(live.managerMessages, [{ channel: 'runtime:heartbeat', payload: live.status }]);
  assert.deepEqual(live.chatMessages, [{ channel: 'runtime:heartbeat', payload: live.status }]);
  assert.deepEqual(live.tokenMessages, [{ channel: 'runtime:heartbeat', payload: live.status }]);

  const destroyed = await publishHeartbeat({ tokenDestroyed: true });
  assert.equal(destroyed.tokenMessages.length, 0);
});

test('standalone token header waits for real workspace data', () => {
  for (const relative of ['renderer/token-dashboard.html']) {
    const html = read(relative);
    assert.match(html, /id="daProjectText">Chưa xác nhận</);
    assert.match(html, /id="daEnvText">Chưa xác nhận</);
    assert.doesNotMatch(html, /id="daProjectSelect"|Nền tảng AI Doanh nghiệp|Multi-Agent Workspace/);
    assert.doesNotMatch(html, /Bộ lọc nâng cao|Xuất báo cáo dữ liệu|Tự động ▾/);
  }
  const standalone = read('renderer/token-dashboard.html');
  assert.doesNotMatch(standalone, /<button[^>]*(?:data-page=|data-nav=|data-open=)/);
  assert.doesNotMatch(standalone, /id="(?:topStartButton|refreshButton|daTokenBoardButton)"/);
  for (const id of ['ccRefreshButton', 'daRefreshButton', 'themeToggleBtn', 'closeManager']) {
    assert.match(standalone, new RegExp(`id="${id}"`));
  }
});

test('token dashboard self-hosts its display fonts (offline-safe)', () => {
  const css = read('renderer/fonts.css');
  assert.match(css, /font-family: 'Plus Jakarta Sans'/);
  assert.match(css, /font-family: 'JetBrains Mono'/);
  assert.match(css, /font-display: swap/);
  assert.doesNotMatch(css, /https?:\/\//);
  const html = read('renderer/token-dashboard.html');
  assert.match(html, /<link rel="stylesheet" href="fonts\.css">/);
  for (const file of [
    'PlusJakartaSans-vietnamese.woff2',
    'PlusJakartaSans-latin.woff2',
    'PlusJakartaSans-latin-ext.woff2',
    'JetBrainsMono-vietnamese.woff2',
    'JetBrainsMono-latin.woff2',
    'JetBrainsMono-latin-ext.woff2'
  ]) {
    const target = path.join(root, 'renderer', 'fonts', file);
    assert.ok(fs.existsSync(target), `missing font ${file}`);
    assert.ok(fs.statSync(target).size > 4000, `font too small ${file}`);
    assert.equal(componentOwnsPath('electron_ui', `renderer/fonts/${file}`), true);
  }
  assert.ok(JSON.parse(read('package.json')).build.files.includes('renderer/**/*'));
});
