const fs = require('node:fs');
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

// One canonical spelling for path identity, shared by every workspace,
// registry and launch-authority comparison in the product.
//
// A directory can be spelled several ways on one machine — an 8.3 short
// name (RUNNER~1), a OneDrive junction, a subst drive, a symlink — while
// still being the same directory. Comparing raw spellings therefore refuses
// legitimate workspaces (the r21 CI gate failed 84 desktop-integration tests
// this way: the runner TEMP used RUNNER~1 while git and the product returned
// runneradmin). realpath collapses every alias to the same key. Paths that
// do not exist yet (registry lookups, pending workspaces) keep their
// resolved spelling instead of failing closed as mismatches. A path grammar
// that does not match the host OS (a Windows payload inspected on POSIX, or
// the reverse) cannot be resolved by this host's filesystem, so it keeps its
// resolved spelling as well.
function canonicalPathKey(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  const isWindows = /^[A-Za-z]:[\\/]/.test(text) || /^\\\\[^\\/]+[\\/][^\\/]+/.test(text);
  const pathApi = isWindows ? path.win32 : path;
  let absolute;
  try {
    absolute = pathApi.resolve(text);
  } catch {
    return '';
  }
  if (!pathApi.isAbsolute(absolute)) return '';
  const hostMatches = isWindows ? process.platform === 'win32' : process.platform !== 'win32';
  if (hostMatches) {
    try {
      absolute = typeof fs.realpathSync.native === 'function'
        ? fs.realpathSync.native(absolute)
        : fs.realpathSync(absolute);
    } catch {
      // Not-yet-created: keep the resolved spelling.
    }
  }
  const normalized = pathApi.normalize(absolute);
  return isWindows ? normalized.toLowerCase() : normalized;
}

// Lexical spelling key: resolve + normalize + case-fold, WITHOUT realpath.
// Use it only for containment prefix checks that run BEFORE a component-wise
// reparse walk. Realpathing the target there would collapse a symlink that
// points outside the root into an outside path, turning the walk's precise
// REPARSE_DENIED into a coarse "escapes" denial (and hiding the reparse
// itself). Identity comparisons must use canonicalPathKey instead.
function lexicalPathKey(value) {
  const normalized = path.normalize(path.resolve(String(value || '')));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

// True when any component of an absolute path is a symlink/junction.
// lstat does not follow the final component, so walking level by level is
// what exposes an intermediate reparse point. 8.3 short names are NOT
// reparse points, so this passes them. Use it to tell "same directory under
// an alias spelling" apart from "directory replaced through a reparse point"
// (drift): realpath alone collapses both cases, so a guard that compares a
// stored spelling against a live realpath must consult this walk before
// accepting a spelling difference as a harmless alias.
function pathTraversesReparsePoint(value) {
  const text = String(value || '').trim();
  if (!text) return true;
  const pathApi = pathApiFor(text);
  const root = pathApi.parse(text).root;
  if (!root) return true;
  // A Windows path may be displayed with forward slashes; split on both.
  const parts = text.slice(root.length).split(/[\\/]/).filter(Boolean);
  let cursor = root;
  for (const part of parts) {
    cursor = pathApi.join(cursor, part);
    let stat;
    try {
      stat = fs.lstatSync(cursor);
    } catch {
      return true;
    }
    if (stat.isSymbolicLink()) return true;
  }
  return false;
}

module.exports = {
  isWindowsAbsolutePath,
  normalizeAbsolutePath,
  sameAbsolutePath,
  joinUnderRoot,
  canonicalPathKey,
  lexicalPathKey,
  pathTraversesReparsePoint
};
