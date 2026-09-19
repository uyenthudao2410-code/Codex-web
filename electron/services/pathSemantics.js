const path = require('node:path');

function isWindowsAbsolutePath(value) {
  const text = String(value || '').trim();
  return /^[A-Za-z]:[\\/]/.test(text) || /^\\\\[^\\/]+[\\/][^\\/]+(?:[\\/]|$)/.test(text);
}

function pathApiFor(value) {
  return isWindowsAbsolutePath(value) ? path.win32 : path;
}

function normalizeAbsolutePath(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  const pathApi = pathApiFor(text);
  if (!pathApi.isAbsolute(text)) return '';
  return pathApi.normalize(text);
}

function sameAbsolutePath(left, right) {
  const leftWindows = isWindowsAbsolutePath(left);
  const rightWindows = isWindowsAbsolutePath(right);
  if (leftWindows !== rightWindows) return false;
  const normalizedLeft = normalizeAbsolutePath(left);
  const normalizedRight = normalizeAbsolutePath(right);
  if (!normalizedLeft || !normalizedRight) return false;
  return leftWindows
    ? normalizedLeft.toLowerCase() === normalizedRight.toLowerCase()
    : normalizedLeft === normalizedRight;
}

function joinUnderRoot(root, ...segments) {
  const text = String(root || '').trim();
  if (!normalizeAbsolutePath(text)) return '';
  return pathApiFor(text).join(text, ...segments);
}

module.exports = {
  isWindowsAbsolutePath,
  normalizeAbsolutePath,
  sameAbsolutePath,
  joinUnderRoot
};
