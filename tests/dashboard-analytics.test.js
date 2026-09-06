const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('manager overview embeds accepted-result KPIs plus secondary token/cost diagnostics', () => {
  const html = read('renderer/index.html');
  assert.match(html, /dashboard\.css/);
  assert.match(html, /dashboard\.js/);
  for (const id of ['daTokensTotal', 'daTokensSplit', 'daCostTotal', 'daCallsTotal', 'daEfficiencyTotal', 'daOperationsTableBody', 'daOperationsCoverage', 'daCoveragePolicy', 'daCoverageController', 'daCoverageControllerMeta', 'daCoverageProvider', 'daCoverageProviderMeta', 'daCoverageInvocation', 'daCoverageInvocationMeta', 'daCoverageToolCard', 'daCoverageToolCardMeta', 'daCoverageCost', 'daCoverageCostMeta', 'daCoverageRunAttribution', 'daCoverageRunAttributionMeta', 'daTurnTokenStatus', 'daChart', 'daChartEmpty', 'daDonut', 'daDonutTotal', 'daLegend', 'daToolBars', 'daSpark', 'daPreset', 'daRateIn', 'daRateOut', 'daCurrency', 'daFx', 'daApply', 'daRefreshButton', 'daLastSync', 'daModelTable', 'daModelSummary', 'daTicker', 'daTickerTrack', 'daLaneChatIn', 'daLaneFastIn', 'daLaneDeepIn', 'daLaneTerraIn', 'daLaneSolIn', 'daRealtimeTpm', 'daRealtimeTpmMeta', 'daRealtimeLatency', 'daRealtimeLatencyMeta']) {
    assert.match(html, new RegExp(`id="${id}"`), `missing analytics id ${id}`);
  }
  assert.doesNotMatch(html, /id="daBytesPerToken"/);
  for (const label of ['ACCEPTED', 'TIME / ACCEPT', 'FIRST PASS', 'OBSERVED COST', 'TOOLS / ACCEPT', 'REWORK / REPLAN']) assert.match(html, new RegExp(label.replace('/', '\\/')));
});

test('operations dashboard consumes a coverage-qualified accepted-result projection', () => {
  const js = read('renderer/dashboard.js');
  const handler = read('resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py');
  assert.match(js, /function canonicalOperationsAnalytics/);
  assert.match(js, /accepted_result_operations_v1/);
  assert.match(js, /analytics\.missing_measurement_policy !== 'unknown_not_zero'/);
  assert.match(js, /function renderOperationsTiles/);
  assert.match(js, /function renderOperationsTable/);
  assert.match(js, /function observedNumber\(value\)/);
  assert.match(js, /typeof value !== 'number' && typeof value !== 'string'/);
  assert.match(js, /value\.trim\(\) === ''/);
  assert.match(js, /observedNumber\(outcomes\.acceptance_rate\)/);
  assert.match(js, /observedNumber\(providerCost\.total_usd\)/);
  assert.match(js, /mean_per_observed_accepted/);
  assert.match(js, /Tool calls unobserved; unknown, not zero/);
  assert.match(handler, /"operations_analytics": operations_analytics\(/);
  assert.match(handler, /performance=runtime\.performance_trace\.get\(\)/);
  assert.match(handler, /"snapshot_scope": "dashboard_analytics"/);
  assert.match(handler, /normalized == "\/__control\/orchestration\/analytics"/);
});

test('realtime performance uses exact rolling five-minute evidence without stale aggregate fallbacks', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /REALTIME_WINDOW_MS = 5 \* 60 \* 1000/);
  assert.match(js, /analytics\.rolling_5m/);
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

test('dashboard visible token path uses canonical UsageEvents and never byte-derived fallback', () => {
  const js = read('renderer/dashboard.js');
  const controlCenter = read('renderer/control-center.js');
  assert.match(controlCenter, /api\.performanceTrace\(\)/);
  assert.match(controlCenter, /detail: \{ snapshot, orchestration, performance, force:/);
  assert.match(js, /function canonicalMeasuredUsage/);
  assert.match(js, /const hourly = canonicalHourBuckets\(measured, DASHBOARD_WINDOW_HOURS\) \|\| \[\]/);
  assert.match(js, /const entries = measured\?\.byModel\?\.length \? measured\.byModel : \[\]/);
  assert.match(js, /const models = new Map\(\)/);
  assert.match(js, /Canonical token trend unavailable/);
  assert.doesNotMatch(js, /chartTrendBuckets\(measured, records/);
  assert.doesNotMatch(js, /const estimatedEntries = toolBreakdown\(today\)/);
  assert.doesNotMatch(js, /const models = modelBreakdown\(today\)/);
  assert.doesNotMatch(js, /byId\('daBytesPerToken'\)/);
  assert.doesNotMatch(js, /costBytesPerToken:/);
  assert.match(js, /perf\?\.recent/);
  assert.match(js, /model_visible_bytes/);
  assert.match(js, /request_bytes/);
  assert.match(js, /response_bytes/);
  assert.match(js, /Transport request\/response\/model-visible bytes are payload telemetry, not token truth/);
  assert.doesNotMatch(js, /function tokensFromBytes/);
  assert.doesNotMatch(js, /tokensFromBytes\(/);
  assert.doesNotMatch(js, /bytesPerToken/);
  assert.doesNotMatch(js, /tokensFromBytes\(record\.requestBytes\)/);
  assert.doesNotMatch(js, /tokensFromBytes\(record\.responseBytes\)/);
  assert.match(js, /DASHBOARD_ANALYTICS_REFRESH_MS = 30000/);
  assert.match(js, /api\.dashboardAnalytics\(\)/);
  assert.match(js, /coding-tools:overview-pulse/);
  assert.match(js, /coding-tools:overview-refresh-request/);
  assert.doesNotMatch(js, /function pollDashboard\(/);
  assert.doesNotMatch(js, /api\.liveOrchestration\(\)/);
  assert.doesNotMatch(js, /api\.orchestration\(\)/);
  assert.doesNotMatch(js, /api\.lightweightSnapshot\(\)/);
  assert.doesNotMatch(js, /setInterval\(\(\) => refresh\(false\), 3000\)/);
  assert.doesNotMatch(js, /fetch\(/);
  assert.doesNotMatch(js, /localStorage/);
});

test('dashboard reads snapshot and live state only from the shared overview pulse', () => {
  const js = read('renderer/dashboard.js');
  assert.doesNotMatch(js, /api\.snapshot\(\)/);
  assert.match(js, /Object\.prototype\.hasOwnProperty\.call\(detail, 'snapshot'\)/);
  assert.match(js, /Object\.prototype\.hasOwnProperty\.call\(detail, 'orchestration'\)/);
  assert.match(js, /coding-tools:overview-pulse/);
  assert.match(js, /void refreshAnalytics\(detail\.force === true\)\.then\(\(\) => renderAll\(\)\)/);
});

test('dashboard animation cancels the previous frame chain before scheduling a new one', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /element\.__dashboardAnimationFrame/);
  assert.match(js, /cancelAnimationFrame\(element\.__dashboardAnimationFrame\)/);
});
test('dashboard per-turn log lists newest turns without identity leakage', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  const css = read('renderer/dashboard.css');
  assert.match(html, /id="daTurnLog"/);
  assert.match(html, /Nhật ký lượt chat/);
  assert.match(js, /function renderTurnLog\(operations\)/);
  assert.match(js, /renderTurnLog\(operations\)/);
  assert.match(js, /recent_turns/);
  assert.match(js, /da-turn-row/);
  assert.match(css, /\.da-turn-log/);
  assert.match(css, /\.da-turn-row/);
  assert.match(css, /\.da-turn-kind\.is-exact/);
  const start = js.indexOf('function renderTurnLog(operations)');
  assert.ok(start >= 0);
  const block = js.slice(start, start + 2600);
  assert.doesNotMatch(block, /turn_id|trace_id/);
  assert.match(block, /toLocaleTimeString\('vi-VN'/);
});

test('dashboard preserves unknown for malformed turn-measurement numerics', () => {
  const js = read('renderer/dashboard.js');
  const logStart = js.indexOf('function renderTurnLog(operations)');
  const liveStart = js.indexOf('function renderLiveTurnCard(orchestration)');
  const cardStart = js.indexOf('function renderChatTurnCard(operations)');
  assert.ok(logStart >= 0 && liveStart > logStart && cardStart > liveStart);
  const log = js.slice(logStart, liveStart);
  const live = js.slice(liveStart, cardStart);
  assert.match(log, /const point = observedNumber\(row\?\.point\);/);
  assert.match(log, /const lower = observedNumber\(row\?\.lower\);/);
  assert.match(log, /const upper = observedNumber\(row\?\.upper\);/);
  assert.match(log, /if \(point === null \|\| kindName === 'unknown'\)/);
  assert.doesNotMatch(log, /Number\(row\.point\) \|\| 0/);
  assert.match(live, /const point = observedNumber\(latest\?\.point\);/);
  assert.match(live, /const lower = observedNumber\(latest\.lower\);/);
  assert.match(live, /const upper = observedNumber\(latest\.upper\);/);
  assert.doesNotMatch(live, /Number\(latest\.point\) \|\| 0/);
});

test('dashboard does not claim a synchronized workspace before a snapshot', () => {
  const js = read('renderer/dashboard.js');
  const controlCenter = read('renderer/control-center.js');
  const start = js.indexOf('function updateHeaderContext()');
  const end = js.indexOf('function renderFleetTable', start);
  assert.ok(start >= 0 && end > start);
  const block = js.slice(start, end);
  assert.match(block, /if \(!snapshot \|\| typeof snapshot !== 'object'\) return;/);
  assert.match(block, /setText\('daProjectText', name\);/);
  assert.match(js, /setText\('daLastSync', snapshotFreshnessLabel\(\)\)/);
  assert.match(js, /Freshness snapshot chưa xác nhận/);
  assert.match(controlCenter, /setText\('ccLastSync', snapshotSyncText\(snapshot\?\.status\)\)/);
});

test('dashboard per-turn tile shows effective turn measurement without double count', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(html, /TOKEN CHATWEB/);
  assert.match(html, /TOKEN PROVIDER/);
  assert.ok(html.indexOf('TOKEN CHATWEB') < html.indexOf('TOKEN PROVIDER'));
  assert.match(html, /id="daTurnTokenStatus"/);
  assert.match(html, /id="daChatTurnValue"/);
  assert.match(html, /id="daChatTurnDelta"/);
  assert.match(html, /id="daChatTurnMeta"/);
  assert.match(js, /function renderChatTurnCard\(operations\)/);
  assert.match(js, /renderChatTurnCard\(operations\)/);
  assert.match(js, /STRUCTURAL ESTIMATE · confidence none/);
  assert.match(js, /Chưa đo lượt chat nào/);
  const chatCardStart = js.indexOf('function renderChatTurnCard(operations)');
  const providerCardStart = js.indexOf('function renderTokenOverviewTiles', chatCardStart);
  assert.ok(chatCardStart >= 0 && providerCardStart > chatCardStart);
  const chatCardSource = js.slice(chatCardStart, providerCardStart);
  assert.doesNotMatch(chatCardSource, /\bmeasured\b|daTokensTotal|daProviderTokenStatus/);
  assert.doesNotMatch(js, /measured\.total \+/);
  assert.match(html, /Token lượt chat/);
  assert.match(js, /function turnTokenState\(operations\)/);
  assert.match(js, /function renderTurnTokens\(operations\)/);
  assert.match(js, /turn_token_measurements/);
  assert.match(js, /chat_turn_measurements_v1/);
  assert.match(js, /renderTurnTokens\(operations\)/);
  assert.match(js, /Chưa đo lượt nào/);
  assert.match(js, /Lượt mới nhất chưa đo/);
  assert.match(js, /phiên ≈/);
  assert.doesNotMatch(js, /tokensFromBytes|bytesPerToken/);
});

test('dashboard analytics never fabricate provider billing data', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /not provider billing/);
  assert.match(html, /Phân tích Context & Chi phí/);
  assert.match(html, /Tool call của ChatGPT\/Coding-VP/);
  assert.match(html, /Không quy đổi byte→token/);
  assert.doesNotMatch(js, /tokensFromBytes\(/);
  assert.doesNotMatch(html, /Byte \/ context token/);
  assert.doesNotMatch(js, /api\.openai\.com|platform\.openai\.com\/usage/);
});

test('dashboard token trend uses canonical hourly UsageEvent evidence only', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /function canonicalHourBuckets/);
  assert.match(js, /const hourly = canonicalHourBuckets\(measured, DASHBOARD_WINDOW_HOURS\) \|\| \[\]/);
  assert.doesNotMatch(js, /performanceBuckets\(records, DASHBOARD_WINDOW_HOURS\)/);
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
  assert.doesNotMatch(js, /const models = modelBreakdown\(today\)/);
  assert.match(js, /const models = new Map\(\)/);
  assert.match(js, /controller_transferred/);
  assert.match(js, /coding-tools:overview-pulse/);
});

test('dashboard reuses Control Center pulse and never accumulates chart listeners or fabricates fleet latency/trend', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /document\.addEventListener\('coding-tools:overview-pulse', applyOverviewPulse\)/);
  assert.match(js, /svg\.onmouseleave = clearGuide/);
  assert.match(js, /svg\.onmousemove = \(event\) =>/);
  assert.doesNotMatch(js, /svg\.addEventListener\('mousemove'/);
  assert.doesNotMatch(js, /1\.1 \+ \(rows % 4\) \* 0\.15/);
  assert.doesNotMatch(js, /M0 12 Q15/);
  assert.match(js, /Observed execution \+ estimated wait per attributed trace call/);
  assert.match(js, /Chưa có per-model time-series evidence; không nội suy trend 24h/);
  assert.match(js, /percent\(Math\.max\(0, Number\(entry\?\.ok\) \|\| 0\), calls\)/);
});

test('dashboard honors real evidence: delegations drive lanes, controller lease drives ChatWeb', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /route_resolved/);
  assert.match(js, /authority\?\.controller\?\.owner_client_id/);
  assert.match(js, /function modelState/);
  assert.match(js, /delegationLane\(delegation\)/);
  assert.doesNotMatch(js, /const measuredByLane = new Map/);
  assert.doesNotMatch(js, /const models = modelBreakdown\(today\)/);
  assert.match(js, /không suy diễn từ bytes/);
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

test('dashboard keeps canonical measured token economics while byte telemetry stays non-token', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /costSource = 'provider_reported'/);
  assert.match(js, /entry\.costSource = 'pricing_derived'/);
  assert.doesNotMatch(js, /const models = modelBreakdown\(today\)/);
  assert.doesNotMatch(js, /settings_estimate/);
  assert.doesNotMatch(js, /tokensFromBytes\(/);
  assert.doesNotMatch(js, /bytesPerToken/);
  assert.match(js, /Canonical UsageEvent token total/);
});

test('measurement coverage panel exposes six evidence-qualified planes and preserves unknown-not-zero', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /function renderMeasurementCoverage/);
  assert.match(js, /analytics\?\.measurement_coverage/);
  assert.match(js, /coverage\.missing_measurement_policy === 'unknown_not_zero'/);
  assert.match(js, /renderMeasurementCoverage\(operations\)/);
  assert.match(html, /Measurement coverage/);
  for (const id of ['daCoverageController', 'daCoverageProvider', 'daCoverageInvocation', 'daCoverageToolCard', 'daCoverageCost', 'daCoverageRunAttribution']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(html, /Tool-card tokens/);
  assert.match(html, /Exact RUN attribution/);
  assert.match(html, /UNOBSERVED/);
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
  assert.match(css, /\.da-tile-hero/);
  assert.match(css, /@keyframes daTileIn/);
  assert.match(css, /@keyframes daHeroSheen/);
  const html = read('renderer/index.html');
  assert.match(html, /da-tile-hero/);
  assert.doesNotMatch(html, /da-live-dot/);
});

test('operations overview renders measured token KPIs from canonical non-overlapping usage analytics', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /function canonicalControllerUsageState/);
  assert.match(js, /function canonicalMeasuredUsage/);
  assert.match(js, /const analytics = analyticsSnapshot\?\.usage_analytics;/);
  assert.match(js, /const analytics = analyticsSnapshot\?\.operations_analytics;/);
  assert.doesNotMatch(js, /orchestration\?\.usage_analytics/);
  assert.doesNotMatch(js, /orchestration\?\.operations_analytics/);
  assert.match(js, /analytics\.measurement !== 'canonical_non_overlapping'/);
  assert.match(js, /missing_measurement_policy !== 'unknown_not_zero'/);
  assert.match(js, /analytics\.controller_usage/);
  assert.match(js, /controller\.missing_measurement_policy !== 'unknown_not_zero'/);
  assert.match(js, /CONTROLLER \$\{controllerUsage\.status\.toUpperCase\(\)\}/);
  assert.match(js, /token controller là unknown, không phải 0/);
  assert.match(js, /controller UNOBSERVED \(unknown, not zero\)/);
  assert.match(js, /renderModelTable\(models, controllerUsage\)/);
  assert.match(js, /usage\.input_total_tokens/);
  assert.match(js, /usage\.input_cached_tokens/);
  assert.match(js, /usage\.output_total_tokens/);
  assert.match(js, /usage\.output_reasoning_tokens/);
  assert.match(js, /usage\.total_tokens/);
  assert.match(js, /Array\.isArray\(analytics\.by_model\)/);
  assert.match(js, /const measuredTokens = measured \? measured\.total : 0/);
  assert.match(js, /const measuredOut = measured \? measured\.output : 0/);
  assert.doesNotMatch(js, /measured\.input \+ measured\.cached \+ measured\.output \+ measured\.reasoning/);
  assert.doesNotMatch(js, /measured\.output \+ measured\.reasoning/);
});

test('operations overview uses canonical hourly and rolling evidence without byte-derived fallback', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /const DASHBOARD_WINDOW_HOURS = 7 \* 24/);
  assert.match(js, /function canonicalHourBuckets/);
  assert.match(js, /function aggregateHourBuckets/);
  assert.match(js, /function chartTrendBuckets/);
  assert.match(js, /Array\.isArray\(analytics\.hourly\)/);
  assert.match(js, /analytics\.rolling_5m/);
  assert.match(js, /canonicalHourBuckets\(measured, DASHBOARD_WINDOW_HOURS\)/);
  assert.match(js, /const hourly = canonicalHourBuckets\(measured, DASHBOARD_WINDOW_HOURS\) \|\| \[\]/);
  assert.doesNotMatch(js, /performanceBuckets\(records, DASHBOARD_WINDOW_HOURS\)/);
  assert.match(js, /aggregateHourBuckets\(hourly, 24\)/);
  assert.doesNotMatch(js, /canonicalHourBuckets\(measured, 24\)/);
  assert.match(js, /TOKEN MEASURED/);
  assert.match(js, /Canonical token trend unavailable/);
});

test('token trend time selector switches between full-window hourly and daily rendering', () => {
  const html = read('renderer/index.html');
  const js = read('renderer/dashboard.js');
  assert.match(html, /id="daChartTimeMode"/);
  assert.match(html, /<option value="hour" selected>Theo giờ<\/option>/);
  assert.match(html, /<option value="day">Theo ngày<\/option>/);
  assert.match(js, /byId\('daChartTimeMode'\)\?\.addEventListener\('change'/);
  assert.match(js, /chartTimeMode = event\.currentTarget\?\.value === 'day' \? 'day' : 'hour'/);
  assert.match(js, /const buckets = chartTrendBuckets\(measured, chartTimeMode\)/);
  assert.match(js, /renderChart\(buckets, chartTimeMode\)/);
  assert.match(js, /const tickEvery = timeMode === 'day'/);
});

test('operations overview heatmap is built from real canonical hourly evidence', () => {
  const js = read('renderer/dashboard.js');
  assert.match(js, /function renderHeatmap\(measured\)/);
  assert.match(js, /measured\?\.hours instanceof Map/);
  assert.doesNotMatch(js, /day >= 5 \? 0\.35 : 0\.85/);
  assert.doesNotMatch(js, /buckets\[hour % buckets\.length\]/);
});

test('basic overview keeps token quantification primary while technical telemetry stays retained but hidden', () => {
  const html = read('renderer/index.html');
  const css = read('renderer/dashboard.css');
  const js = read('renderer/dashboard.js');
  assert.match(html, /TOKEN PROVIDER/);
  assert.match(html, /INPUT TOKEN/);
  assert.match(html, /OUTPUT TOKEN/);
  assert.match(html, /CACHED TOKEN/);
  assert.match(html, /TOKEN \/ KẾT QUẢ/);
  assert.match(html, /id="daProviderTokenStatus"/);
  assert.match(html, /id="daControllerTokenStatus"/);
  assert.match(html, /id="daEstimateConfidence"/);
  assert.match(css, /#runtimeSourceStatusCard/);
  assert.match(css, /article\[aria-labelledby="daOperationsTitle"\]/);
  assert.match(css, /article\[aria-labelledby="daCoverageTitle"\]/);
  assert.match(css, /#ccRestartButton/);
  assert.match(css, /\.cc-bottom-grid/);
  assert.match(css, /\.da-model-card \.da-fleet-table th:nth-child\(n \+ 5\)/);
  assert.match(js, /function renderTokenOverviewTiles\(measured, operations, controllerUsage\)/);
  assert.match(js, /renderTokenOverviewTiles\(measured, operations, controllerUsage\)/);
  assert.match(js, /function controllerTokenEstimateState\(operations\)/);
  assert.match(js, /operations\?\.controller_token_estimate/);
  assert.match(js, /CALIBRATED_ESTIMATE/);
  assert.match(js, /CONTEXT_ESTIMATE/);
  assert.match(js, /p50_total_tokens \?\? estimate\.p50_context_tokens/);
  assert.match(js, /không phải controller total/);
  assert.match(js, /Math\.round\(measured\.total \/ accepted\)/);
  assert.match(js, /measured\.cached \/ measured\.input/);
  assert.match(js, /token bổ sung/);
  assert.match(js, /Context ≈/);
  assert.match(js, /Quy đổi bảng giá · không phải ChatGPT billing/);
  assert.match(js, /renderOperationsTable\(operations\)/);
  assert.match(js, /const providerUsd = observedNumber\(providerCost\.total_usd\)/);
  assert.match(js, /const toolMean = observedNumber\(tools\.mean_per_observed_accepted\)/);
  assert.match(js, /const replanRate = observedNumber\(efficiency\.replan_rate\)/);
  assert.match(js, /measured\.costSource !== 'unobserved'/);
  assert.match(js, /entry\.costSource === 'pricing_derived'/);
});

test('secondary model and fleet token economics fail closed without canonical lane mapping', () => {
  const js = read('renderer/dashboard.js');
  const html = read('renderer/index.html');
  assert.match(js, /Chưa có UsageEvent canonical đủ để gán token\/chi phí theo lane; không suy diễn từ bytes/);
  assert.match(js, /Token\/chi phí theo model chưa có mapping UsageEvent canonical; giữ unknown, không quy đổi từ bytes/);
  assert.doesNotMatch(js, /const models = modelBreakdown\(today\)/);
  assert.doesNotMatch(html, /TOKEN \(EST\.\)/);
  assert.doesNotMatch(html, /CHI PHÍ \(SCENARIO\)/);
  assert.doesNotMatch(html, /SCENARIO \/ 1K EST\. TOKEN/);
  assert.match(html, /TOKEN \(USAGE EVENT\)/);
  assert.match(html, /PROVENANCE/);
});

test('dead legacy measuredUsage helper is absent and dashboard rendering stays canonical', () => {
  const js = read('renderer/dashboard.js');
  assert.doesNotMatch(js, /\bmeasuredUsage\(/);
  assert.doesNotMatch(js, /function measuredUsage/);
  assert.match(js, /const measured = canonicalMeasuredUsage\(\)/);
});
