const PANEL_WIDTH = 510;
const PANEL_WIDTH_RATIO = 0.45;
const PANEL_MIN_WIDTH = PANEL_WIDTH;
const PANEL_MAX_WIDTH = 880;
const MIN_CHAT_WIDTH = 560;

function targetPanelWidth(width, options = {}) {
  const explicitWidth = Number(options.panelWidth);
  if (explicitWidth > 0) return Math.floor(explicitWidth);
  const viewportWidth = Math.max(0, Math.floor(width));
  return Math.min(PANEL_MAX_WIDTH, Math.max(PANEL_MIN_WIDTH, Math.round(viewportWidth * PANEL_WIDTH_RATIO)));
}

function panelInset(width, visible, options = {}) {
  const panelWidth = targetPanelWidth(width, options);
  const minChatWidth = Number(options.minChatWidth) || MIN_CHAT_WIDTH;
  if (!visible) return 0;
  return Math.min(panelWidth, Math.max(0, Math.floor(width) - minChatWidth));
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

function chatBounds(width, height, toolbarHeight, visible, options = {}) {
  const inset = panelInset(width, visible, options);
  return {
    x: 0,
    y: toolbarHeight,
    width: Math.max(0, Math.floor(width) - inset),
    height: Math.max(0, Math.floor(height) - toolbarHeight)
  };
}

module.exports = {
  PANEL_WIDTH,
  PANEL_WIDTH_RATIO,
  PANEL_MIN_WIDTH,
  PANEL_MAX_WIDTH,
  MIN_CHAT_WIDTH,
  targetPanelWidth,
  panelInset,
  panelBounds,
  chatBounds
};
