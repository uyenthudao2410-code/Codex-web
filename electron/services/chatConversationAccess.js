'use strict';

// Content-free ChatGPT conversation access monitor.
//
// Detects page-level ACL failures ("You don't have access to this
// conversation") without reading any page content, body, DOM, cookie or
// token: the verdict uses only the response URL and the HTTP status code of
// ChatGPT backend conversation endpoints, observed via
// session.webRequest.onCompleted in the main process.
//
// Two layers:
//
// 1. createConversationAccessTracker() - stateful same-target correlation.
//    A denial is keyed by the exact endpoint pathname (in-memory closure
//    only, never logged, never persisted, never exposed in results). A 2xx
//    clears the denial ONLY for that same pathname: a 200 from
//    /backend-api/conversations (list) or from another conversation never
//    clears another target's denial. reset() is called on top-level
//    navigation because the error state belongs to one navigation target.
// 2. ensure/releaseConversationAccessMonitor() - single webRequest
//    dispatcher per session. Electron honors only the last attached
//    webRequest listener, so modules must not each attach their own.
//    The dispatcher is attached once and forwards to a mutable subscriber,
//    which fixes both listener clobbering and stale-controller capture
//    across ChatViewController dispose/recreate cycles.
//
// Error/user-facing copies never embed the request URL because conversation
// endpoints carry conversation IDs.

const CHAT_HOSTS = new Set(['chatgpt.com', 'www.chatgpt.com']);

const CONVERSATION_ACCESS_FILTER = [
  '*://chatgpt.com/backend-api/conversation*',
  '*://www.chatgpt.com/backend-api/conversation*'
];

const SESSION_MONITOR_KEY = '__mcpConversationAccessMonitor';

function isConversationApiRequest(url) {
  let parsed;
  try {
    parsed = new URL(String(url || ''));
  } catch {
    return false;
  }
  if (parsed.protocol !== 'https:') return false;
  if (!CHAT_HOSTS.has(parsed.hostname.toLowerCase())) return false;
  // Exact-segment match: /backend-api/conversation and
  // /backend-api/conversation/<id>/... only. The list endpoint
  // /backend-api/conversations must never match.
  return parsed.pathname === '/backend-api/conversation'
    || parsed.pathname.startsWith('/backend-api/conversation/');
}

function conversationPathKey(url) {
  let parsed;
  try {
    parsed = new URL(String(url || ''));
  } catch {
    return null;
  }
  if (parsed.protocol !== 'https:') return null;
  if (!CHAT_HOSTS.has(parsed.hostname.toLowerCase())) return null;
  return parsed.pathname;
}

function classifyConversationAccess(url, statusCode) {
  if (!isConversationApiRequest(url)) return null;
  const status = Number(statusCode);
  if (!Number.isFinite(status)) return null;
  if (status === 401 || status === 403) return 'denied';
  if (status >= 200 && status < 300) return 'recovered';
  return null;
}

function accessDeniedMessage(statusCode) {
  const status = Number(statusCode) === 401 ? '401' : '403';
  return `ChatGPT từ chối truy cập conversation (HTTP ${status}). `
    + 'Có thể session đăng nhập riêng của app đã cũ hoặc thuộc workspace khác, '
    + 'hoặc lỗi phía ChatGPT. Dùng nút "Đăng nhập lại" trên thanh công cụ để làm mới session của app.';
}

function createConversationAccessTracker() {
  let deniedPath = null;
  return {
    observe(url, statusCode) {
      const verdict = classifyConversationAccess(url, statusCode);
      if (verdict === 'denied') {
        const path = conversationPathKey(url);
        if (path && path === deniedPath) return { changed: false, denied: true, message: null };
        deniedPath = path;
        return { changed: true, denied: true, message: accessDeniedMessage(statusCode) };
      }
      if (verdict === 'recovered') {
        const path = conversationPathKey(url);
        if (deniedPath && path && path === deniedPath) {
          deniedPath = null;
          return { changed: true, denied: false, message: null };
        }
        return { changed: false, denied: deniedPath !== null, message: null };
      }
      return { changed: false, denied: deniedPath !== null, message: null };
    },
    reset() {
      const wasDenied = deniedPath !== null;
      deniedPath = null;
      return wasDenied;
    },
    snapshot() {
      return { denied: deniedPath !== null };
    }
  };
}

function ensureConversationAccessMonitor(chatSession, onResponse) {
  if (!chatSession || !chatSession.webRequest
    || typeof chatSession.webRequest.onCompleted !== 'function') return false;
  if (typeof onResponse !== 'function') return false;
  const existing = chatSession[SESSION_MONITOR_KEY];
  if (existing && existing.dispatch === true) {
    existing.subscriber = onResponse;
    return true;
  }
  const record = { dispatch: true, subscriber: onResponse };
  chatSession[SESSION_MONITOR_KEY] = record;
  chatSession.webRequest.onCompleted({ urls: CONVERSATION_ACCESS_FILTER }, (details) => {
    const target = record.subscriber;
    if (typeof target !== 'function') return;
    try {
      target(details?.url, details?.statusCode);
    } catch {
      // Best-effort observation must never break page traffic.
    }
  });
  return true;
}

function releaseConversationAccessMonitor(chatSession, onResponse) {
  const record = chatSession?.[SESSION_MONITOR_KEY];
  if (!record || record.dispatch !== true) return false;
  if (record.subscriber === onResponse) record.subscriber = null;
  return true;
}

module.exports = {
  CHAT_HOSTS,
  CONVERSATION_ACCESS_FILTER,
  SESSION_MONITOR_KEY,
  isConversationApiRequest,
  conversationPathKey,
  classifyConversationAccess,
  accessDeniedMessage,
  createConversationAccessTracker,
  ensureConversationAccessMonitor,
  releaseConversationAccessMonitor
};
