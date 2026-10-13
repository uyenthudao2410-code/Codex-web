const PANEL_WIDTH = 420;
const PANEL_WIDTH_RATIO = 0.35;
const PANEL_MIN_WIDTH = 360;
const PANEL_MAX_WIDTH = 750;
const MIN_EXECUTOR_WIDTH = 560;

function targetPanelWidth(width, options = {}) {
  const explicitWidth = Number(options.panelWidth);
  if (explicitWidth > 0) return Math.floor(explicitWidth);
  const viewportWidth = Math.max(0, Math.floor(width));
  return Math.min(PANEL_MAX_WIDTH, Math.max(PANEL_MIN_WIDTH, Math.round(viewportWidth * PANEL_WIDTH_RATIO)));
}

function panelInset(width, visible, options = {}) {
  const panelWidth = targetPanelWidth(width, options);
  const minExecutorWidth = Number(options.minExecutorWidth) || MIN_EXECUTOR_WIDTH;
  if (!visible) return 0;
  return Math.min(panelWidth, Math.max(0, Math.floor(width) - minExecutorWidth));
}

function panelBounds(width, height, toolbarHeight, visible, options = {}) {
  const inset = panelInset(width, visible, options);
  if (!visible || inset <= 0) return null;
  return {
    x: Math.max(0, Math.floor(width) - inset),
    y: toolbarHeight,
    width: inset,
    height: Math.max(0, Math.floor(height) - toolbarHeight)
  };
}

module.exports = {
  PANEL_WIDTH,
  PANEL_WIDTH_RATIO,
  PANEL_MIN_WIDTH,
  PANEL_MAX_WIDTH,
  MIN_EXECUTOR_WIDTH,
  targetPanelWidth,
  panelInset,
  panelBounds
};
