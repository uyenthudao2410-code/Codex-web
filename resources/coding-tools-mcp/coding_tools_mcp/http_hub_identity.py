from __future__ import annotations

import hashlib
import os
import re
from typing import Any

from .connector_attestation import (
    CONNECTOR_ATTESTATION_ENV,
    CONNECTOR_ATTESTATION_HEADER,
    verify_connector_attestation,
)


_HUB_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


class HTTPHubIdentityMixin:
    """Execution Hub client identity parsing shared by control and RPC paths."""

    def _hub_identity_from_values(
        self,
        *,
        client_id: str,
        client_type: str,
        client_name: str = "",
        client_version: str = "",
        session_instance: str = "",
        execution_context_id: str = "",
    ) -> dict[str, Any]:
        client_id = client_id.strip()
        client_type = client_type.strip().lower().replace("-", "_") or "client"
        if not _HUB_CLIENT_ID_RE.fullmatch(client_id):
            raise ValueError("Execution Hub client id must match [A-Za-z0-9][A-Za-z0-9._:-]{0,63}")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", client_type):
            raise ValueError("invalid Execution Hub client type")
        role = "controller" if client_type == "chatweb" else "worker" if client_type in {"codex_desktop", "opencode"} else "supervisor" if client_type == "electron" else "client"
        return {
            "client_id": client_id,
            "client_type": client_type,
            "role": role,
            "session_instance": session_instance,
            "execution_context_id": str(execution_context_id or "")[:64],
            "capabilities": {"client_name": client_name[:100], "client_version": client_version[:50]},
        }

    def _hub_identity_from_request(self, request: dict[str, Any]) -> dict[str, Any]:
        raw_client_id = str(self.headers.get("X-Coding-Tools-Client-Id") or "").strip()
        raw_client_type = str(self.headers.get("X-Coding-Tools-Client-Type") or "").strip()
        client_id = raw_client_id or "chatweb"
        normalized_client_id = raw_client_id.lower()
        implicit_chatweb_id = (
            not normalized_client_id
            or normalized_client_id == "chatweb"
            or normalized_client_id.startswith(("chatweb-", "chatweb_", "chatweb:", "chatweb."))
        )
        client_type = raw_client_type or ("chatweb" if implicit_chatweb_id else "client")
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        meta = params.get("_meta") if isinstance(params.get("_meta"), dict) else {}
        client_info = meta.get("io.modelcontextprotocol/clientInfo") if isinstance(meta.get("io.modelcontextprotocol/clientInfo"), dict) else {}
        if request.get("method") == "initialize" and isinstance(params.get("clientInfo"), dict):
            client_info = params.get("clientInfo")
        raw_session = str(self.headers.get("Mcp-Session-Id") or "")
        logical_session = raw_session or str(getattr(self.runtime, "http_session_id", "") or "")
        session_instance = hashlib.sha256(logical_session.encode("utf-8")).hexdigest()[:16] if logical_session else ""
        identity = self._hub_identity_from_values(
            client_id=client_id,
            client_type=client_type,
            client_name=str(client_info.get("name") or ""),
            client_version=str(client_info.get("version") or ""),
            session_instance=session_instance,
            execution_context_id=str(getattr(self.runtime, "execution_context_id", "") or ""),
        )
        # The legacy defaults keep ordinary unauthenticated/legacy HTTP calls
        # usable, but they are not caller provenance.  Discovery acceptance
        # must therefore distinguish a managed transport that explicitly
        # supplied both identity headers from an implicit or partial label.
        identity["identity_source"] = (
            "explicit_headers"
            if raw_client_id and raw_client_type
            else "partial_headers"
            if raw_client_id or raw_client_type
            else "implicit_default"
        )
        attestation = str(self.headers.get(CONNECTOR_ATTESTATION_HEADER) or "").strip()
        attestation_secret = str(
            getattr(self.runtime, "connector_attestation_secret", None)
            or os.environ.get(CONNECTOR_ATTESTATION_ENV, "")
        ).strip()
        verified, reason = verify_connector_attestation(
            attestation,
            attestation_secret,
            client_id=client_id,
            client_type=client_type,
            activation_epoch_id=getattr(self.runtime, "activation_epoch_id", ""),
            process_instance_id=getattr(self.runtime, "process_instance_id", ""),
            server_instance_id=getattr(self.runtime, "server_instance_id", ""),
            contract_sha256=(getattr(self.runtime, "tool_contract", {}) or {}).get("sha256", ""),
        )
        identity["attestation_verified"] = verified
        identity["attestation_source"] = "managed_tunnel" if verified else reason
        if verified and identity["identity_source"] == "explicit_headers":
            identity["identity_source"] = "attested_transport"
        return identity
