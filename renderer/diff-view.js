'use strict';
/*
 * Work Hub diff view — pure parser from git unified-diff text to a bounded,
 * structured line model the renderer can draw with text nodes only.
 *
 * W2 selective port (§5.1 of the CoS integration plan): the line model
 * ({ kind, old, next, text }), the bounded-line limit with an explicit
 * `truncated` flag, and the dual-gutter presentation follow
 * Chat On Steroids `src/renderer/unified-diff.ts` (MIT — see
 * THIRD_PARTY_NOTICES.md). The CoS original computes chunks from two exact
 * snapshots with CodeMirror Chunk/Text; Codex-web's Changes tab instead
 * receives unified-diff text from `git diff` (electron/services/
 * workHubFiles.js), so the parsing below is original to Codex-web and no
 * CodeMirror/lezer dependency is introduced. This module is native to
 * Codex-web: it needs no CoS app, adapter, or runtime to work.
 *
 * Line kinds:
 *   context  — unchanged line inside a hunk (has both numbers)
 *   added    — '+' line (next number only)
 *   removed  — '-' line (old number only)
 *   hunk     — '@@ -a,b +c,d @@' header (no numbers)
 *   meta     — file headers, section labels ('# Đã stage'…), '\ No newline…'
 */
(function (global) {
  const DEFAULT_LIMIT = 600;

  function parseUnifiedDiff(text, options = {}) {
    const limit = Math.max(1, Number(options.limit) || DEFAULT_LIMIT);
    const lines = [];
    let truncated = false;
    let added = 0;
    let removed = 0;
    let oldLine = null;
    let nextLine = null;
    const push = (line) => {
      if (lines.length < limit) lines.push(line);
      else truncated = true;
    };
    for (const raw of String(text || '').split('\n')) {
      const hunk = raw.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (hunk) {
        oldLine = Number(hunk[1]);
        nextLine = Number(hunk[2]);
        push({ kind: 'hunk', old: null, next: null, text: raw });
        continue;
      }
      if (raw.startsWith('diff --git ')
        || raw.startsWith('--- ') || raw.startsWith('+++ ')
        || raw.startsWith('# ')
        || raw.startsWith('\\ ')
        || /^(index|new file mode|deleted file mode|old mode|new mode|similarity index|rename (from|to)|Binary files) /.test(raw)
        || raw === 'GIT binary patch') {
        push({ kind: 'meta', old: null, next: null, text: raw });
        continue;
      }
      if (oldLine === null) {
        // Text before the first hunk (should not happen for git output,
        // but never drop it silently or misnumber it).
        if (raw) push({ kind: 'meta', old: null, next: null, text: raw });
        continue;
      }
      // Git never emits a bare empty line inside a hunk (an empty context
      // line is a single space). Bare '' lines only come from the trailing
      // newline or the staged/unstaged section join in gitFileDiff — skip
      // them without touching the line counters.
      if (raw === '') continue;
      if (raw.startsWith('+')) {
        added += 1;
        push({ kind: 'added', old: null, next: nextLine, text: raw.slice(1) });
        nextLine += 1;
      } else if (raw.startsWith('-')) {
        removed += 1;
        push({ kind: 'removed', old: oldLine, next: null, text: raw.slice(1) });
        oldLine += 1;
      } else if (raw.startsWith(' ')) {
        push({ kind: 'context', old: oldLine, next: nextLine, text: raw.slice(1) });
        oldLine += 1;
        nextLine += 1;
      } else {
        push({ kind: 'meta', old: null, next: null, text: raw });
      }
    }
    return { lines, truncated, added, removed };
  }

  const api = { DEFAULT_LIMIT, parseUnifiedDiff };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.WorkHubDiff = api;
})(typeof window !== 'undefined' ? window : globalThis);
