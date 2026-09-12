from __future__ import annotations

"""Loopback-only user approval for an attested ChatWeb continuation grant.

The MCP tool call creates an in-memory, exact-descriptor challenge.  A local
browser renders those terms and an explicit button press finalizes the grant.
The token stays in the URL fragment, so it is never sent in a request target or
written by the HTTP access logger.  Challenges are process-local by design: a
restart changes runtime authority and invalidates every outstanding approval.
"""

import copy
import hashlib
import ipaddress
import json
import secrets
import threading
import time
import urllib.parse
from typing import Any


CONTINUATION_CONSENT_HTTP_PATH = "/__control/continuation-consent"
CONTINUATION_CONSENT_CHALLENGE_TTL_MS = 120_000
MAX_CONTINUATION_CONSENT_CHALLENGES = 32
_MAX_HTTP_BODY_BYTES = 4096


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _now_ms() -> int:
    return int(time.time() * 1000)


def _token_digest(token: object) -> str:
    normalized = str(token or "").strip()
    if not normalized or len(normalized) > 256:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ContinuationConsentChallengeStore:
    """Bounded process-local challenges with one processing owner at a time."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, dict[str, Any]] = {}

    def _prune_locked(self, now_ms: int) -> None:
        expired = [key for key, record in self._records.items() if int(record["expires_at_unix_ms"]) <= now_ms]
        for key in expired:
            self._records.pop(key, None)
        if len(self._records) <= MAX_CONTINUATION_CONSENT_CHALLENGES:
            return
        oldest = sorted(self._records, key=lambda key: int(self._records[key]["issued_at_unix_ms"]))
        for key in oldest[: len(self._records) - MAX_CONTINUATION_CONSENT_CHALLENGES]:
            self._records.pop(key, None)

    def issue(
        self,
        *,
        descriptor: dict[str, Any],
        policy: dict[str, Any],
        controller: dict[str, Any],
        host_turn: dict[str, Any],
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        now = int(_now_ms() if now_ms is None else now_ms)
        descriptor_copy = copy.deepcopy(descriptor)
        policy_copy = copy.deepcopy(policy)
        descriptor_sha256 = hashlib.sha256(_canonical_json(descriptor_copy).encode("utf-8")).hexdigest()
        trace_id = str(host_turn.get("trace_id") or "").strip()
        turn_id = str(host_turn.get("turn_id") or "").strip()
        issuer_client_id = str(descriptor_copy.get("issuer_client_id") or "").strip()
        with self._lock:
            self._prune_locked(now)
            for digest, record in self._records.items():
                if (
                    record["state"] == "pending"
                    and record["descriptor_sha256"] == descriptor_sha256
                    and record["trace_id"] == trace_id
                    and record["issuer_client_id"] == issuer_client_id
                ):
                    return {
                        "token": record["token"],
                        "challenge_id": record["challenge_id"],
                        "expires_at_unix_ms": record["expires_at_unix_ms"],
                        "descriptor_sha256": descriptor_sha256,
                    }
            token = secrets.token_urlsafe(32)
            digest = _token_digest(token)
            challenge_id = "run-continuation-consent:" + secrets.token_hex(16)
            self._records[digest] = {
                "token": token,
                "challenge_id": challenge_id,
                "descriptor": descriptor_copy,
                "descriptor_sha256": descriptor_sha256,
                "policy": policy_copy,
                "controller": copy.deepcopy(controller),
                "trace_id": trace_id,
                "turn_id": turn_id,
                "issuer_client_id": issuer_client_id,
                "issued_at_unix_ms": now,
                "expires_at_unix_ms": now + CONTINUATION_CONSENT_CHALLENGE_TTL_MS,
                "state": "pending",
            }
            self._prune_locked(now)
            return {
                "token": token,
                "challenge_id": challenge_id,
                "expires_at_unix_ms": now + CONTINUATION_CONSENT_CHALLENGE_TTL_MS,
                "descriptor_sha256": descriptor_sha256,
            }

    def preview(self, token: object, *, now_ms: int | None = None) -> dict[str, Any] | None:
        now = int(_now_ms() if now_ms is None else now_ms)
        digest = _token_digest(token)
        with self._lock:
            self._prune_locked(now)
            record = self._records.get(digest)
            if record is None or record["state"] not in {"pending", "approved"}:
                return None
            return {
                "challenge_id": record["challenge_id"],
                "descriptor": copy.deepcopy(record["descriptor"]),
                "descriptor_sha256": record["descriptor_sha256"],
                "expires_at_unix_ms": record["expires_at_unix_ms"],
            }

    def begin_approval(self, token: object, *, now_ms: int | None = None) -> dict[str, Any] | None:
        now = int(_now_ms() if now_ms is None else now_ms)
        digest = _token_digest(token)
        with self._lock:
            self._prune_locked(now)
            record = self._records.get(digest)
            if record is None or record["state"] not in {"pending", "approved"}:
                return None
            record["state"] = "processing"
            receipt = {
                "receipt_id": "chatweb-continuation-consent-web:" + secrets.token_hex(16),
                "turn_id": record["turn_id"],
                "trace_id": record["trace_id"],
                "staged_at_unix_ms": now,
                "descriptor": copy.deepcopy(record["descriptor"]),
            }
            return {
                "_challenge_token_digest": digest,
                "challenge_id": record["challenge_id"],
                "policy": copy.deepcopy(record["policy"]),
                "controller": copy.deepcopy(record["controller"]),
                "receipt": receipt,
            }

    def release(self, approved: dict[str, Any]) -> None:
        digest = str(approved.get("_challenge_token_digest") or "")
        with self._lock:
            record = self._records.get(digest)
            if record is not None and record["state"] == "processing":
                record["state"] = "approved"

    def consume(self, approved: dict[str, Any]) -> None:
        digest = str(approved.get("_challenge_token_digest") or "")
        with self._lock:
            self._records.pop(digest, None)


def local_continuation_consent_origin(server_address: tuple[Any, ...]) -> str:
    host = str(server_address[0] or "").strip("[]")
    port = int(server_address[1])
    if host in {"", "0.0.0.0"}:
        host = "127.0.0.1"
    elif host == "::":
        host = "::1"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host.lower() != "localhost":
            return ""
    else:
        mapped = getattr(address, "ipv4_mapped", None)
        if not address.is_loopback and not (mapped and mapped.is_loopback):
            return ""
    display = f"[{host}]" if ":" in host else host
    return f"http://{display}:{port}"


class ContinuationConsentHTTPMixin:
    """Small HTTP adapter; the Runtime owns all grant and start semantics."""

    def _local_continuation_consent_request(self) -> bool:
        peer = str(self.client_address[0] or "").strip("[]")
        try:
            address = ipaddress.ip_address(peer)
        except ValueError:
            return False
        mapped = getattr(address, "ipv4_mapped", None)
        if not address.is_loopback and not (mapped and mapped.is_loopback):
            return False
        if any(self.headers.get(name) for name in ("Forwarded", "X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto", "CF-Connecting-IP")):
            return False
        host = str(self.headers.get("Host") or "")
        try:
            hostname = urllib.parse.urlsplit(f"//{host}").hostname or ""
            host_address = ipaddress.ip_address(hostname)
        except ValueError:
            return hostname.lower() == "localhost"
        mapped_host = getattr(host_address, "ipv4_mapped", None)
        return host_address.is_loopback or bool(mapped_host and mapped_host.is_loopback)

    def _send_consent_headers(self, content_type: str, length: int, *, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()

    def _send_consent_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = _canonical_json(payload).encode("utf-8")
        self._send_consent_headers("application/json; charset=utf-8", len(body), status=status)
        self.wfile.write(body)

    def handle_continuation_consent_get(self) -> None:
        if not self._local_continuation_consent_request():
            self._send_consent_json({"ok": False, "code": "LOCAL_APPROVAL_REQUIRED"}, status=403)
            return
        body = _CONSENT_PAGE.encode("utf-8")
        self._send_consent_headers("text/html; charset=utf-8", len(body))
        self.wfile.write(body)

    def handle_continuation_consent_post(self) -> None:
        if not self._local_continuation_consent_request():
            self._send_consent_json({"ok": False, "code": "LOCAL_APPROVAL_REQUIRED"}, status=403)
            return
        content_type = str(self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        try:
            length = int(self.headers.get("Content-Length") or "-1")
        except ValueError:
            length = -1
        if content_type != "application/json" or not (0 <= length <= _MAX_HTTP_BODY_BYTES):
            self._send_consent_json({"ok": False, "code": "INVALID_APPROVAL_REQUEST"}, status=400)
            return
        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_consent_json({"ok": False, "code": "INVALID_APPROVAL_REQUEST"}, status=400)
            return
        action = str(request.get("action") or "").strip().lower() if isinstance(request, dict) else ""
        token = request.get("token") if isinstance(request, dict) else None
        runtime = self.server.control_runtime
        store = runtime.run_continuation_consent_challenges
        if action == "preview":
            preview = store.preview(token)
            self._send_consent_json({"ok": preview is not None, **(preview or {"code": "CHALLENGE_MISSING_OR_EXPIRED"})}, status=200 if preview else 404)
            return
        if action != "approve":
            self._send_consent_json({"ok": False, "code": "INVALID_APPROVAL_ACTION"}, status=400)
            return
        approved = store.begin_approval(token)
        if approved is None:
            self._send_consent_json({"ok": False, "code": "CHALLENGE_MISSING_EXPIRED_OR_CONSUMED"}, status=409)
            return
        try:
            result = runtime._run_continuation_approve_http_challenge(approved)
        except Exception as exc:  # Runtime converts known failures below; never expose internals.
            store.release(approved)
            code = str(getattr(exc, "code", "RUN_CONTINUATION_APPROVAL_FAILED"))
            message = str(getattr(exc, "message", "The continuation approval could not be finalized."))
            self._send_consent_json({"ok": False, "code": code, "message": message}, status=409)
            return
        store.consume(approved)
        self._send_consent_json({"ok": True, **result})


_CONSENT_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Authorize bounded continuation</title><style>
body{font:15px/1.5 system-ui,sans-serif;max-width:760px;margin:48px auto;padding:0 20px;color:#18202a;background:#f5f7fa}
main{background:white;border:1px solid #d9e0e8;border-radius:12px;padding:24px;box-shadow:0 8px 24px #10203012}
h1{font-size:22px;margin-top:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f3f7;padding:14px;border-radius:8px;max-height:420px;overflow:auto}
button{font:inherit;font-weight:650;padding:10px 16px;border:0;border-radius:8px;background:#1769e0;color:white;cursor:pointer}button:disabled{opacity:.45;cursor:not-allowed}
#status{margin-top:14px}.error{color:#a10f20}.success{color:#08753c}
</style></head><body><main><h1>Authorize bounded continuation</h1>
<p>Review the exact RUN, workspace, scope, checks, epoch, and budget below. Approval is one-shot and starts only this bounded continuation.</p>
<pre id="terms">Loading exact terms…</pre><button id="approve" disabled>Authorize and start</button><p id="status"></p>
</main><script>
let token=location.hash.slice(1);history.replaceState(null,'',location.pathname);const terms=document.getElementById('terms');const button=document.getElementById('approve');const status=document.getElementById('status');
async function call(action){const response=await fetch(location.pathname,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,token}),cache:'no-store'});const data=await response.json();if(!response.ok||!data.ok)throw new Error(data.message||data.code||'Approval failed');return data}
(async()=>{try{if(!token)throw new Error('Missing one-shot approval token');const data=await call('preview');terms.textContent=JSON.stringify(data.descriptor,null,2);button.disabled=false}catch(error){terms.textContent='';status.className='error';status.textContent=error.message}})();
button.addEventListener('click',async()=>{button.disabled=true;status.textContent='Finalizing exact grant and starting the MCP-owned driver…';try{const data=await call('approve');token='';status.className='success';status.textContent=data.status==='PROPOSING'?'Authorized and started. You may close this page and the chat; final acceptance will still require the controller.':'Authorized. '+(data.message||data.status||'');}catch(error){button.disabled=false;status.className='error';status.textContent=error.message}});
</script></body></html>"""
