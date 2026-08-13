const PANEL_WIDTH = 340;
const MIN_CHAT_WIDTH = 560;

function panelInset(width, visible, options = {}) {
  const panelWidth = Number(options.panelWidth) || PANEL_WIDTH;
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

module.exports = { PANEL_WIDTH, MIN_CHAT_WIDTH, panelInset, panelBounds, chatBounds };
