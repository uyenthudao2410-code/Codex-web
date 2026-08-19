const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('manager overview embeds the token/cost analytics dashboard', () => {
  const html = read('renderer/index.html');
  assert.match(html, /dashboard\.css/);
  assert.match(html, /dashboard\.js/);
  for (const id of ['daTokensTotal', 'daTokensSplit', 'daCostTotal', 'daCallsTotal', 'daEfficiencyTotal', 'daChart', 'daChartEmpty', 'daDonut', 'daDonutTotal', 'daLegend', 'daToolBars', 'daSpark', 'daPreset', 'daRateIn', 'daRateOut', 'daBytesPerToken', 'daCurrency', 'daFx', 'daApply', 'daRefreshButton', 'daLastSync', 'daModelTable', 'daModelSummary', 'daTicker', 'daTickerTrack', 'daLaneChatIn', 'daLaneFastIn', 'daLaneDeepIn', 'daLaneTerraIn', 'daLaneSolIn', 'daRealtimeTpm', 'daRealtimeTpmMeta', 'daRealtimeLatency', 'daRealtimeLatencyMeta']) {
    assert.match(html, new RegExp(`id="${id}"`), `missing analytics id ${id}`);
  }
});

test('realtime performance uses exact rolling five-minute evidence without stale aggregate fallbacks', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /REALTIME_WINDOW_MS = 5 \* 60 \* 1000/);
  assert.match(js, /samples: \[\]/);
  assert.match(js, /function rollingProviderUsage/);
  assert.match(js, /function rollingLatency/);
  assert.match(js, /updateRealtimeMetrics\(records, measured\)/);
  assert.match(js, /Không có phép đo provider trong 5 phút gần nhất/);
  assert.match(js, /Không có lệnh trong 5 phút gần nhất/);
  assert.match(html, /id="daRealtimeTpmMeta"/);
  assert.match(html, /id="daRealtimeLatencyMeta"/);
  assert.doesNotMatch(js, /lastHour\[1\]\.in \+ lastHour\[1\]\.out\) \/ 60/);
  assert.doesNotMatch(js, /measuredTokens \/ 1440/);
  assert.doesNotMatch(js, /allSummary\?\.calls/);
  assert.doesNotMatch(js, /compactNumber/);
});

test('dashboard analytics derive context estimates from measured model-visible bytes', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /api\.performanceTrace\(\)/);
  assert.match(js, /NON_TOKEN_TOOLS = new Set\(\['view_image'\]\)/);
  assert.match(js, /function tokensFromBytes/);
  assert.match(js, /function hourBuckets/);
  assert.match(js, /function toolBreakdown/);
  assert.match(js, /function costOf/);
  assert.match(js, /perf\?\.recent/);
  assert.match(js, /model_visible_bytes/);
  assert.match(js, /request_bytes/);
  assert.match(js, /response_bytes/);
  assert.match(js, /Transport request\/response bytes are payload telemetry, not token truth/);
  assert.doesNotMatch(js, /tokensFromBytes\(record\.requestBytes\)/);
  assert.doesNotMatch(js, /tokensFromBytes\(record\.responseBytes\)/);
  assert.match(js, /setInterval\(\(\) => refresh\(false\), 3000\)/);
  assert.doesNotMatch(js, /fetch\(/);
  assert.doesNotMatch(js, /localStorage/);
});

test('dashboard analytics never fabricate provider billing data', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /SCENARIO/);
  assert.match(js, /not provider billing/);
  assert.match(html, /Phân tích Context & Chi phí/);
  assert.match(html, /recent trace/);
  assert.match(html, /MEASURED/);
  assert.match(html, /ESTIMATED/);
  assert.match(html, /SCENARIO/);
  assert.match(html, /Request\/response transport bytes không được coi là token/);
  assert.doesNotMatch(js, /api\.openai\.com|platform\.openai\.com\/usage/);
});

test('dashboard analytics measure traffic over time from persisted hourly buckets, not one fixed snapshot', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /hourly_metrics/);
  assert.match(js, /function hourlyFromStore/);
  assert.match(js, /function performanceBuckets/);
  assert.match(js, /return hourlyFromStore\(count\) \|\| hourBuckets\(records, count\);/);
  assert.match(js, /model_visible_bytes/);
  assert.match(js, /Giờ gần nhất ≈/);
  assert.match(html, /id="daTokensRate"/);
  assert.doesNotMatch(js, /fetch\(/);
});

test('model control table attributes traffic to every running lane including ChatWeb', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /id: 'chatweb', name: 'ChatWeb'/);
  assert.match(js, /id: 'fast', name: 'Codex Fast'/);
  assert.match(js, /id: 'deepseek', name: 'OpenCode Go'/);
  assert.match(js, /id: 'terra', name: 'Codex Deep'/);
  assert.match(js, /id: 'sol', name: 'Codex Critical'/);
  assert.match(js, /function laneWindows/);
  assert.match(js, /function controllerWindows/);
  assert.match(js, /function modelOf/);
  assert.match(js, /function modelBreakdown/);
  assert.match(js, /controller_transferred/);
  assert.match(js, /api\.orchestration\(\)/);
});

test('dashboard honors real evidence: delegations drive lanes, controller lease drives ChatWeb', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /route_resolved/);
  assert.match(js, /authority\?\.controller\?\.owner_client_id/);
  assert.match(js, /metadata\?\.economics/);
  assert.match(js, /usageEvidence = 'MEASURED'/);
  assert.match(js, /usageEvidence = 'ESTIMATED'/);
  assert.match(js, /Chưa phân bổ/);
  assert.match(js, /không có bằng chứng delegation\/controller/);
});

test('cost model settings are allowlisted, normalized and persisted', () => {
  const main = read('electron/main.js');
  for (const key of ['costPreset', 'costRateInUsd', 'costRateOutUsd', 'costCurrency', 'costFxRate', 'costBytesPerToken', 'costLaneRates']) {
    assert.match(main, new RegExp(`'${key}'`), `settings:save must allow ${key}`);
  }
  const { normalize } = require('../electron/services/config');
  const settings = normalize({ costRateInUsd: 'x', costBytesPerToken: 0, costCurrency: 'EUR' });
  assert.equal(settings.costRateInUsd, 0.15);
  assert.equal(settings.costBytesPerToken, 4);
  assert.equal(settings.costCurrency, 'USD');
  assert.equal(normalize({ costRateOutUsd: 8.5 }).costRateOutUsd, 8.5);
  const laneRates = JSON.parse(settings.costLaneRates);
  assert.equal(laneRates.deepseek.in, 0.28);
  assert.equal(laneRates.sol.out, 40);
  const repaired = JSON.parse(normalize({ costLaneRates: '{"deepseek":{"in":-1,"out":"x"}}' }).costLaneRates);
  assert.equal(repaired.deepseek.in, 0.28);
  assert.equal(repaired.terra.out, 10);
});

test('dashboard prices measured tokens per canonical model and prefers provider-reported cost', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /MODEL_PRICING = \{/);
  assert.match(js, /'deepseek-v4-flash': \{ in: 0\.28, out: 0\.42, cached: 0\.028 \}/);
  assert.match(js, /'gpt-5\.6-sol': \{ in: 10, out: 40 \}/);
  assert.match(js, /function modelPriceOf/);
  assert.match(js, /economics\.provider_cost/);
  assert.match(js, /costSource = 'provider_reported'/);
  assert.match(js, /\? 'pricing_derived' : 'settings_estimate'/);
  assert.match(js, /cachedTokens = Number\(summary\.cachedTokens\) \|\| 0/);
  assert.match(js, /uncached = Math\.max\(0, Number\(summary\.inTokens\) - cachedTokens\)/);
  assert.match(js, /derived from \$\/1M pricing/);
});

test('dashboard styling is themed, animated and honors reduced motion', () => {
  const css = read('renderer/dashboard.css');
  assert.match(css, /\.da-grid-tiles/);
  assert.match(css, /\.da-chart/);
  assert.match(css, /\.da-donut/);
  assert.match(css, /\.da-bar-row/);
  assert.match(css, /var\(--cc-surface\)/);
  assert.match(css, /@keyframes daTickerScroll/);
  assert.match(css, /@keyframes daRowFlow/);
  assert.match(css, /@keyframes daPulse/);
  assert.match(css, /@keyframes daAreaIn/);
  assert.match(css, /\.da-model-row\.is-active/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(max-width: 1080px\)/);
});
