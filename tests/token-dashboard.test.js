const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { componentOwnsPath } = require('../electron/services/componentRevision');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

// The token dashboard is hosted directly in renderer/index.html, so the KPI
// typography/narrow-breakpoint contracts live in the shared dashboard stylesheet.
function dashboardStyleSources() {
  return [['shared', read('renderer/dashboard.css')]];
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

async function publishHeartbeat() {
  const managerMessages = [];
  const chatMessages = [];
  const status = { fullyReady: true, telemetryAvailable: true };
  const context = {
    runtimeHeartbeatInFlight: null,
    orchestrator: { lightweightSnapshot: async () => status },
    decorateUiRuntimeSnapshot: (value) => value,
    lastRecoveryProgressTime: null,
    sendManager: (channel, payload) => managerMessages.push({ channel, payload }),
    chatWindow: makeWindow(chatMessages),
    registerUiRevision: () => Promise.resolve(),
    Promise
  };
  vm.runInNewContext(`${heartbeatPublisherSource()}\nglobalThis.publishRuntimeHeartbeat = publishRuntimeHeartbeat;`, context, {
    filename: 'electron/main.js#publishRuntimeHeartbeat'
  });
  await context.publishRuntimeHeartbeat();
  return { status, managerMessages, chatMessages };
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

test('overview donut has no measured segments before the first snapshot', () => {
  const html = read('renderer/index.html');
  const donut = html.match(/<svg id="daDonut"[\s\S]*?<\/svg>/)?.[0];
  assert.ok(donut, 'donut missing');
  assert.doesNotMatch(donut, /<circle\b/, 'overview has unobserved initial segments');
  assert.match(donut, /id="daDonutTotal"[^>]*>—<\/text>/);
});

test('token overview shows no fabricated numbers before the live snapshot', () => {
  const html = read('renderer/index.html');
  assert.match(html, /<meta http-equiv="Content-Security-Policy" content="default-src 'self';/);
  assert.doesNotMatch(html, /fonts\.googleapis\.com|fonts\.gstatic\.com/);
  assert.doesNotMatch(html, /Math\.random\(\)/);
  for (const id of ['daChatTurnValue', 'daTokensTotal', 'daCostTotal', 'daDonutTotal', 'daToolCostTotal', 'daRealtimeTpm', 'daCoveragePolicy']) {
    const tag = html.match(new RegExp(`<[^>]+id="${id}"[^>]*>[\\s\\S]*?(</[a-z]+>|/>)`));
    assert.ok(tag, `token overview thiếu id ${id}`);
    assert.doesNotMatch(tag[0], /216\.8M|18\.4K|\$48\.25|43\.2K|đạt chuẩn 100%|142 lần|Đã đo 142/);
  }
  assert.match(html, /id="daTurnLog"/);
  assert.match(html, /Nhật ký lượt chat/);
  assert.match(html, /<script src="control-center\.js"><\/script>/);
  assert.match(html, /<script src="dashboard\.js"><\/script>/);
  assert.match(html, /id="themeToggle"/);
  assert.match(html, /Chưa có dữ liệu — đang chờ snapshot\./);
  assert.match(html, /Chưa có accepted-result evidence\./);
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
});

test('token overview is hosted directly in the Control Center without a standalone window', () => {
  assert.equal(fs.existsSync(path.join(root, 'renderer', 'token-dashboard.html')), false);
  const html = read('renderer/index.html');
  assert.doesNotMatch(html, /daTokenBoardButton/);
  assert.doesNotMatch(html, /overviewTokenFrame/);
  const main = read('electron/main.js');
  assert.doesNotMatch(main, /tokenWindow/);
  assert.doesNotMatch(main, /token-dashboard/);
  const preload = read('electron/preload.js');
  assert.doesNotMatch(preload, /openTokenDashboard|closeTokenDashboard|token-dashboard/);
  const js = read('renderer/dashboard.js');
  assert.doesNotMatch(js, /daTokenBoardButton|openTokenDashboard|overviewTokenFrame/);
});

test('runtime heartbeat reaches manager and chat windows only', async () => {
  const live = await publishHeartbeat();
  assert.deepEqual(live.managerMessages, [{ channel: 'runtime:heartbeat', payload: live.status }]);
  assert.deepEqual(live.chatMessages, [{ channel: 'runtime:heartbeat', payload: live.status }]);
});

test('token overview waits for real workspace data', () => {
  const html = read('renderer/index.html');
  assert.match(html, /id="daProjectText">Chưa xác nhận</);
  assert.match(html, /id="daEnvText">Chưa xác nhận</);
  assert.doesNotMatch(html, /id="daProjectSelect"|Nền tảng AI Doanh nghiệp|Multi-Agent Workspace/);
  assert.doesNotMatch(html, /Bộ lọc nâng cao|Xuất báo cáo dữ liệu|Tự động ▾/);
  for (const id of ['ccRefreshButton', 'daRefreshButton', 'themeToggle', 'closeManager']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
});

test('token overview self-hosts its display fonts (offline-safe)', () => {
  const css = read('renderer/fonts.css');
  assert.match(css, /font-family: 'Plus Jakarta Sans'/);
  assert.match(css, /font-family: 'JetBrains Mono'/);
  assert.match(css, /font-display: swap/);
  assert.doesNotMatch(css, /https?:\/\//);
  const html = read('renderer/index.html');
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
