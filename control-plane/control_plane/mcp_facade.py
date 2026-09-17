"""Fail-closed, context-scoped root MCP facade.

This module gives one authenticated, time-bounded, context-scoped MCP
principal a way to discover the exact eight tool public surface, inspect that
context's central state, and atomically record exactly one fixed read-only
intent. After the separately admitted node action completes, it can expose one
allowlisted compact receipt projection. It never calls a node, forwards a
client credential, polls, or turns a central record into local authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .node_agent import safe_workspace_summary
from .store import ControlPlaneError, ControlPlaneStore, PermissionError, ValidationError


MCP_PROTOCOL_VERSION = "2025-11-25"
STATELESS_MCP_PROTOCOL_VERSION = "2026-07-28"
# The initialize handshake only negotiates legacy revisions. The modern
# revision uses per-request metadata and server/discover instead.
# Do not advertise 2025-03-26: its batching and older result contract are not
# implemented here. Unsupported offers negotiate our latest supported revision.
LEGACY_MCP_PROTOCOL_VERSIONS = (MCP_PROTOCOL_VERSION, "2025-06-18")
SUPPORTED_MCP_PROTOCOL_VERSIONS = (STATELESS_MCP_PROTOCOL_VERSION, *LEGACY_MCP_PROTOCOL_VERSIONS)
FACADE_SCHEMA_VERSION = 5
FACADE_PROFILE = "control-plane-scoped-read-only-relay-v4"
PUBLIC_TOOL_NAMES = (
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _rpc_error(request_id: str | int | None, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _response_id(request: dict[str, Any]) -> str | int | None:
    value = request.get("id")
    return value if isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool)) else None


def _tool_input_schema() -> dict[str, Any]:
    """Use one explicit envelope; it is not the local tool's byte schema.

    The only central mutation represented here is an authenticated, idempotent
    request for the exact fixed read-only operation under the caller's one
    server-issued context grant. It creates a central intent/action but cannot
    dispatch it or grant local authority.
    """
    return {
        "type": "object",
        "required": ["context_id"],
        "additionalProperties": False,
        "properties": {
            "context_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Immutable control-plane context selected by the authenticated owner.",
            },
            "action_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Optional existing action under this context; observation only.",
            },
            "operation": {
                "type": "string",
                "enum": ["status", "request_read_only"],
                "description": "Defaults to status. request_read_only queues only the fixed local workspace_context operation.",
            },
            "idempotency_key": {
                "type": "string",
                "minLength": 8,
                "maxLength": 256,
                "description": "Required for request_read_only; replays only an immutable matching central intent.",
            },
            "expires_at_ms": {
                "type": "integer",
                "minimum": 1,
                "description": "Required for request_read_only; must be within the selected context's live expiry.",
            },
            "expected_facade_contract": {
                "type": "object",
                "required": ["schema_version", "profile", "sha256"],
                "additionalProperties": False,
                "properties": {
                    "schema_version": {"type": "integer", "minimum": 1},
                    "profile": {"type": "string", "minLength": 3, "maxLength": 128},
                    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                },
                "description": "Required for request_read_only; pin the exact façade contract from initialize or tools/list.",
            },
        },
    }


def _tool_description(name: str) -> str:
    if name == "workspace_context":
        return "Return central status, queue only the fixed read-only workspace_context action, or show its verified compact completed receipt; this facade never directly accesses a local workspace."
    return "Declared public tool name. Relay is unavailable until a separate local admission bridge is accepted."


def _central_lifecycle_state(action: dict[str, Any]) -> str:
    """Name only a state directly supported by central durable records.

    This intentionally does not infer a local job state, a workspace result,
    acceptance, or an outcome. ``dispatch_unconfirmed`` is evidence that the
    central store emitted an attempt, not evidence that the node executed it.
    A settled action without a receipt can result from central expiry/revoke or
    cancellation, so it must remain distinguishable from terminal receipts.
    """
    delivery_state = action.get("delivery_state")
    if delivery_state in {"queued", "dispatch_unconfirmed", "accepted", "reconcile_required"}:
        return str(delivery_state)
    if delivery_state != "settled":
        return "unrecognized_central_lifecycle_state"
    receipts = action.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        return "settled_without_receipt"
    latest = receipts[-1]
    receipt_state = latest.get("receipt_state") if isinstance(latest, dict) else None
    if receipt_state in {"completed", "rejected", "failed"}:
        return str(receipt_state)
    return "settled_with_nonterminal_receipt"


def _completed_workspace_relay(action: dict[str, Any], contract: dict[str, int | str]) -> dict[str, Any] | None:
    """Return only the exact, bounded local summary from a completed receipt.

    Receipts are untrusted network input even after they are durable.  The
    node agent performs the first allowlist, but this final client-facing
    boundary validates it again and never returns the raw receipt payload,
    absolute Windows workspace, local handle, or a summary from a stale
    facade contract.
    """

    if action.get("tool_name") != "workspace_context":
        return None
    receipts = action.get("receipts")
    if not isinstance(receipts, list):
        return None
    for receipt in reversed(receipts):
        if not isinstance(receipt, dict) or receipt.get("receipt_state") != "completed":
            continue
        raw_payload = receipt.get("payload_json")
        if not isinstance(raw_payload, str) or len(raw_payload.encode("utf-8")) > 16 * 1024:
            continue
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError):
            continue
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != 1
            or payload.get("operation_kind") != "control_plane_read_only_workspace_context"
            or payload.get("workspace_accessed") is not True
            or payload.get("actor") != {"client_id": "electron-control-plane-bridge", "client_type": "electron"}
            or payload.get("facade_contract") != contract
            or not isinstance(payload.get("workspace_summary_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["workspace_summary_sha256"].lower()) is None
            or not isinstance(payload.get("response_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["response_sha256"].lower()) is None
        ):
            continue
        try:
            summary = safe_workspace_summary(payload.get("workspace_summary"))
        except RuntimeError:
            continue
        summary_sha256 = payload["workspace_summary_sha256"].lower()
        expected_summary_sha256 = hashlib.sha256(
            _canonical_json(summary).encode("utf-8")
        ).hexdigest()
        if summary_sha256 != expected_summary_sha256:
            continue
        return {
            "receipt_id": receipt.get("receipt_id"),
            "received_at_ms": receipt.get("received_at_ms"),
            "workspace_summary": summary,
            "workspace_summary_sha256": summary_sha256,
            "response_sha256": payload["response_sha256"].lower(),
        }
    return None


def tool_contract() -> dict[str, Any]:
    tools = [
        {
            "name": name,
            "description": _tool_description(name),
            "inputSchema": _tool_input_schema(),
            "annotations": {"readOnlyHint": name == "workspace_context"},
        }
        for name in PUBLIC_TOOL_NAMES
    ]
    digest_input = {
        "schema_version": FACADE_SCHEMA_VERSION,
        "profile": FACADE_PROFILE,
        "tools": tools,
    }
    return {
        "schema_version": FACADE_SCHEMA_VERSION,
        "profile": FACADE_PROFILE,
        "sha256": hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest(),
        "tools": tools,
    }


def _contract_metadata(contract: dict[str, Any]) -> dict[str, int | str]:
    return {key: contract[key] for key in ("schema_version", "profile", "sha256")}


def _expected_contract(value: Any) -> dict[str, int | str]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "profile", "sha256"}:
        raise ValidationError("expected_facade_contract is invalid.")
    schema_version = value.get("schema_version")
    profile = value.get("profile")
    sha256 = value.get("sha256")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or not 1 <= schema_version <= 1_000_000
        or not isinstance(profile, str)
        or not 3 <= len(profile.strip()) <= 128
        or not isinstance(sha256, str)
        or re.fullmatch(r"[a-f0-9]{64}", sha256.strip().lower()) is None
    ):
        raise ValidationError("expected_facade_contract is invalid.")
    return {"schema_version": schema_version, "profile": profile.strip(), "sha256": sha256.strip().lower()}


class ContractMismatchError(ControlPlaneError):
    code = "CONTRACT_MISMATCH"


class ControlPlaneMcpFacade:
    """Stateless JSON-RPC boundary for one authenticated control-plane owner."""

    def __init__(self, store: ControlPlaneStore) -> None:
        self.store = store
        self.contract = tool_contract()

    def _result(self, request: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
        if "id" not in request or request.get("id") is None:
            return None
        return {"jsonrpc": "2.0", "id": _response_id(request), "result": value}

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        requested = params.get("protocolVersion", MCP_PROTOCOL_VERSION)
        if not isinstance(requested, str) or not requested.strip():
            raise ValidationError("MCP protocol version must be a non-empty string.")
        negotiated = requested if requested in LEGACY_MCP_PROTOCOL_VERSIONS else MCP_PROTOCOL_VERSION
        return {
            "protocolVersion": negotiated,
            "serverInfo": {"name": "coding-tools-control-plane", "version": "0.1.0"},
            "capabilities": {"tools": {"listChanged": False}},
            "instructions": (
                "This facade is context-scoped central status plus a queued fixed read-only intent and a verified compact completed "
                "receipt projection. It never directly accesses a local workspace, calls a node, or grants local admission; a separate "
                "local bridge must accept and complete the action."
            ),
            "_meta": {
                "control_plane": {
                    "execution": "local_admission_required",
                    "access_scope": "server_issued_context_grant",
                    "tool_contract": {
                        key: self.contract[key] for key in ("schema_version", "profile", "sha256")
                    },
                }
            },
        }

    def _tools_list(self) -> dict[str, Any]:
        return {
            "tools": self.contract["tools"],
            "_meta": {
                "control_plane": {
                    "execution": "local_admission_required",
                    "access_scope": "server_issued_context_grant",
                    "tool_contract": {
                        key: self.contract[key] for key in ("schema_version", "profile", "sha256")
                    },
                }
            },
        }

    @staticmethod
    def _validate_stateless_params(params: dict[str, Any]) -> None:
        meta = params.get("_meta")
        if not isinstance(meta, dict) or meta.get("io.modelcontextprotocol/protocolVersion") != STATELESS_MCP_PROTOCOL_VERSION:
            raise ValidationError("MCP 2026-07-28 requires matching params._meta protocolVersion.")
        if not isinstance(meta.get("io.modelcontextprotocol/clientCapabilities"), dict):
            raise ValidationError("MCP 2026-07-28 requires params._meta clientCapabilities.")
        if "io.modelcontextprotocol/clientInfo" in meta:
            info = meta["io.modelcontextprotocol/clientInfo"]
            if not isinstance(info, dict) or not all(isinstance(info.get(key), str) for key in ("name", "version")):
                raise ValidationError("MCP clientInfo must contain string name and version fields when present.")

    @staticmethod
    def _stateless_result(result: dict[str, Any], *, cacheable: bool) -> dict[str, Any]:
        # Decorate the response, not the tool contract or any durable record.
        # Legacy and modern clients therefore observe the same authority and
        # exact eight-tool schema hash.
        decorated = {**result, "resultType": "complete"}
        decorated["_meta"] = {
            **result.get("_meta", {}),
            "io.modelcontextprotocol/serverInfo": {"name": "coding-tools-control-plane", "version": "0.1.0"},
        }
        if cacheable:
            decorated.update({"ttlMs": 0, "cacheScope": "private"})
        return decorated

    @staticmethod
    def _call_error(*, code: str, message: str, tool_name: str) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {"code": code, "tool_name": tool_name, "execution": "not_implemented"},
            "isError": True,
        }

    @staticmethod
    def _arguments(params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        name = params.get("name")
        if not isinstance(name, str) or name not in PUBLIC_TOOL_NAMES:
            raise ValidationError("tools/call name is unsupported.")
        arguments = params.get("arguments")
        if not isinstance(arguments, dict):
            raise ValidationError("tools/call arguments must be an object.")
        context_id = arguments.get("context_id")
        if not isinstance(context_id, str) or not 3 <= len(context_id.strip()) <= 128:
            raise ValidationError("context_id is invalid.")
        operation = arguments.get("operation", "status")
        if operation not in {"status", "request_read_only"}:
            raise ValidationError("operation is unsupported.")
        result = {"context_id": context_id.strip(), "operation": operation}
        if operation == "status":
            if not set(arguments) <= {"context_id", "action_id", "operation"}:
                raise ValidationError("status operation accepts context_id and optional action_id only.")
            if "action_id" not in arguments:
                return name, result
            action_id = arguments.get("action_id")
            if not isinstance(action_id, str) or not 3 <= len(action_id.strip()) <= 128:
                raise ValidationError("action_id is invalid.")
            result["action_id"] = action_id.strip()
            return name, result
        if set(arguments) != {"context_id", "operation", "idempotency_key", "expires_at_ms", "expected_facade_contract"}:
            raise ValidationError("request_read_only requires exact context, idempotency, expiry and expected facade contract.")
        key = arguments.get("idempotency_key")
        if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
            raise ValidationError("idempotency_key is invalid.")
        expiry = arguments.get("expires_at_ms")
        if not isinstance(expiry, int) or isinstance(expiry, bool) or expiry <= 0:
            raise ValidationError("expires_at_ms is invalid.")
        result["idempotency_key"] = key.strip()
        result["expires_at_ms"] = expiry
        result["expected_facade_contract"] = _expected_contract(arguments.get("expected_facade_contract"))
        return name, result

    def _action_status(self, *, owner_id: str, context_id: str, action_id: str) -> dict[str, Any]:
        """Return an allowlisted lifecycle projection for this exact context.

        Receipt payloads may be implementation-specific and action arguments
        belong to the sealed authority record, so neither is a facade status
        field. A caller can learn that a receipt exists, not its raw content.
        """
        action = self.store.action_observation(owner_id=owner_id, action_id=action_id)
        if action.get("context_id") != context_id:
            raise ValidationError("action_id does not belong to context_id.")
        return {
            "action_id": action["action_id"],
            "action_digest": action["action_digest"],
            "tool_name": action["tool_name"],
            "created_at_ms": action["created_at_ms"],
            "expires_at_ms": action["expires_at_ms"],
            "delivery_state": action["delivery_state"],
            "central_lifecycle_state": _central_lifecycle_state(action),
            "settled_at_ms": action["settled_at_ms"],
            "attempts": [
                {
                    "attempt_id": attempt["attempt_id"],
                    "attempt_number": attempt["attempt_number"],
                    "dispatched_at_ms": attempt["dispatched_at_ms"],
                }
                for attempt in action["attempts"]
            ],
            "receipts": [
                {
                    "receipt_id": receipt["receipt_id"],
                    "receipt_state": receipt["receipt_state"],
                    "received_at_ms": receipt["received_at_ms"],
                    "receipt_digest": receipt["receipt_digest"],
                }
                for receipt in action["receipts"]
            ],
        }

    def _workspace_context(self, *, owner_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
        context = self.store.context(owner_id=owner_id, context_id=arguments["context_id"])
        node = self.store.node_observation(owner_id=owner_id, device_id=str(context["device_id"]))
        now = self.store.clock()
        if context["closed_at_ms"] is not None:
            context_state = "closed"
        elif int(context["expires_at_ms"]) <= now:
            context_state = "expired"
        else:
            context_state = "active"
        observation = {
            "schema_version": FACADE_SCHEMA_VERSION,
            "observation_kind": "control_plane_workspace_status",
            "workspace_accessed": False,
            "execution": "not_implemented",
            "local_admission": "unverified",
            "context": {
                key: context[key]
                for key in (
                    "context_id",
                    "binding_id",
                    "device_id",
                    "endpoint_id",
                    "workspace_id",
                    "workspace_generation",
                    "created_at_ms",
                    "expires_at_ms",
                    "closed_at_ms",
                )
            },
            "context_state": context_state,
            "node": {
                key: node[key]
                for key in (
                    "device_id",
                    "endpoint_id",
                    "revoked_at_ms",
                    "last_seen_at_ms",
                    "runtime_instance_id",
                    "mcp_server_instance_id",
                    "activation_epoch",
                    "contract_version",
                    "readiness",
                )
            },
        }
        content = "Central status only; no local workspace was accessed."
        if "action_id" in arguments:
            observation["action"] = self._action_status(
                owner_id=owner_id,
                context_id=context["context_id"],
                action_id=arguments["action_id"],
            )
            action = self.store.action_observation(owner_id=owner_id, action_id=arguments["action_id"])
            relay = _completed_workspace_relay(action, _contract_metadata(self.contract))
            if relay is not None:
                observation.update({
                    "workspace_accessed": True,
                    "execution": "completed_read_relay",
                    "local_admission": "completed",
                    "workspace_read": relay,
                })
                content = "Compact workspace metadata was read by the selected local node and relayed through its completed receipt."
        return {
            "content": [{"type": "text", "text": content}],
            "structuredContent": observation,
            "isError": False,
        }

    def _request_read_only_workspace_context(
        self,
        *,
        owner_id: str,
        principal_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        current_contract = _contract_metadata(self.contract)
        if arguments["expected_facade_contract"] != current_contract:
            raise ContractMismatchError("expected facade contract does not match this control-plane surface.")
        intent = self.store.request_mcp_read_only_workspace_context(
            owner_id=owner_id,
            context_id=arguments["context_id"],
            idempotency_key=arguments["idempotency_key"],
            expires_at_ms=arguments["expires_at_ms"],
            facade_contract=current_contract,
            principal_id=principal_id,
        )
        action = self._action_status(
            owner_id=owner_id,
            context_id=arguments["context_id"],
            action_id=intent["action_id"],
        )
        return {
            "content": [{"type": "text", "text": "Read-only intent is queued for local admission; no local workspace was accessed by the facade."}],
            "structuredContent": {
                "schema_version": FACADE_SCHEMA_VERSION,
                "observation_kind": "control_plane_read_only_intent",
                "workspace_accessed": False,
                "execution": "queued_for_local_admission",
                "local_admission": "required",
                "request_id": intent["request_id"],
                "action_id": intent["action_id"],
                "intent_digest": intent["intent_digest"],
                "facade_contract": intent["facade_contract"],
                "replayed": intent["replayed"],
                "action": action,
            },
            "isError": False,
        }

    @staticmethod
    def _require_granted_context(*, requested_context_id: str, granted_context_id: str) -> None:
        if requested_context_id != granted_context_id:
            raise PermissionError("MCP client access grant does not cover context_id.")

    def _call_tool(
        self,
        *,
        owner_id: str,
        principal_id: str,
        granted_context_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        name, arguments = self._arguments(params)
        self._require_granted_context(
            requested_context_id=arguments["context_id"],
            granted_context_id=granted_context_id,
        )
        if name != "workspace_context":
            return self._call_error(
                code="LOCAL_ADMISSION_BRIDGE_REQUIRED",
                message="This tool cannot be relayed until the local admission bridge is accepted.",
                tool_name=name,
            )
        if arguments["operation"] == "request_read_only":
            return self._request_read_only_workspace_context(
                owner_id=owner_id,
                principal_id=principal_id,
                arguments=arguments,
            )
        return self._workspace_context(owner_id=owner_id, arguments=arguments)

    def handle(
        self,
        request: dict[str, Any],
        *,
        owner_id: str,
        principal_id: str,
        granted_context_id: str,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        """Handle one authenticated JSON-RPC request without persistent session state."""
        request_id = _response_id(request)
        if "id" not in request:
            # This stateless facade has no client notifications to persist or
            # dispatch. Accept initialized (and ignore unknown notifications)
            # without a JSON-RPC response. Invalid notifications are rejected
            # by the HTTP boundary, never interpreted as tool requests.
            if (
                request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)
                or not request["method"].startswith("notifications/")
                or not request["method"][len("notifications/"):]
                or not isinstance(request.get("params", {}), dict)
            ):
                raise ValidationError("MCP notification is invalid or a request id is missing.")
            return None
        try:
            if (
                request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)
                or not request["method"]
                or request_id is None
            ):
                return _rpc_error(request_id, -32600, "Invalid Request")
            params = request.get("params", {})
            if params is None:
                params = {}
            if not isinstance(params, dict):
                raise ValidationError("MCP method params must be an object.")
            method = request["method"]
            if stateless_2026:
                self._validate_stateless_params(params)
            if stateless_2026 and method in {"initialize", "ping"}:
                return _rpc_error(request_id, -32601, "Method not found")
            if method == "initialize":
                if request_id is None:
                    return _rpc_error(None, -32600, "Invalid Request: initialize requires a non-null request id")
                result = self._initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = self._tools_list()
            elif method == "server/discover":
                if stateless_2026:
                    initialized = self._initialize({})
                    result = {
                        "supportedVersions": list(SUPPORTED_MCP_PROTOCOL_VERSIONS),
                        "capabilities": initialized["capabilities"],
                        "instructions": initialized["instructions"],
                        "_meta": initialized["_meta"],
                    }
                else:
                    result = {**self._initialize({}), **self._tools_list()}
            elif method == "tools/call":
                result = self._call_tool(
                    owner_id=owner_id,
                    principal_id=principal_id,
                    granted_context_id=granted_context_id,
                    params=params,
                )
            else:
                return _rpc_error(request_id, -32601, f"Unknown method: {method}")
            if stateless_2026:
                result = self._stateless_result(result, cacheable=method in {"server/discover", "tools/list"})
            return self._result(request, result)
        except ControlPlaneError as error:
            return _rpc_error(request_id, -32602, "Invalid params", {"code": error.code, "message": str(error)})
