from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, MutableMapping


SECRET_BROKER_ENV = "CODING_TOOLS_MCP_SECRET_BROKER"
AUTH_HANDLE_ENV = "CODING_TOOLS_MCP_AUTH_HANDLE"
MCP_AUTH_HANDLE = "secret://mcp/auth"
OPENAI_API_KEY_HANDLE = "secret://provider/openai/api-key"
SECRET_BROKER_SCHEMA_VERSION = 1
MAX_SECRET_HANDLES = 16
MAX_SECRET_BYTES = 16 * 1024
MAX_SECRET_BROKER_ENVELOPE_BYTES = 64 * 1024

_HANDLE_RE = re.compile(r"^secret://[a-z0-9][a-z0-9._/-]{0,190}$")
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


class SecretBrokerError(ValueError):
    """Fail-closed secret broker error whose message never contains secret material."""


def _validated_handle(value: object) -> str:
    handle = str(value or "").strip()
    suffix = handle[len("secret://") :] if handle.startswith("secret://") else ""
    if (
        not _HANDLE_RE.fullmatch(handle)
        or not suffix
        or ".." in suffix.split("/")
        or "?" in handle
        or "#" in handle
    ):
        raise SecretBrokerError("Secret broker handle is invalid.")
    return handle


def _validated_secret(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SecretBrokerError("Secret broker value is invalid.")
    if len(value.encode("utf-8")) > MAX_SECRET_BYTES:
        raise SecretBrokerError("Secret broker value exceeds the configured bound.")
    return value


class SecretBroker:
    """Process-local trusted secret store addressed only by opaque secret:// handles."""

    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values: dict[str, str] = {}
        for handle, secret in dict(values or {}).items():
            self._put(handle, secret)

    def __repr__(self) -> str:
        return f"SecretBroker(handle_count={len(self._values)})"

    def _put(self, handle: object, secret: object) -> None:
        normalized_handle = _validated_handle(handle)
        normalized_secret = _validated_secret(secret)
        if normalized_handle in self._values:
            if self._values[normalized_handle] != normalized_secret:
                raise SecretBrokerError("Secret broker contains a conflicting handle assignment.")
            return
        if len(self._values) >= MAX_SECRET_HANDLES:
            raise SecretBrokerError("Secret broker handle capacity exceeded.")
        self._values[normalized_handle] = normalized_secret

    @classmethod
    def from_environment(
        cls,
        env: MutableMapping[str, str] | None = None,
        *,
        consume: bool = True,
    ) -> "SecretBroker":
        source = os.environ if env is None else env
        broker = cls()
        raw_envelope = source.pop(SECRET_BROKER_ENV, "") if consume else source.get(SECRET_BROKER_ENV, "")
        if raw_envelope:
            if len(raw_envelope.encode("utf-8")) > MAX_SECRET_BROKER_ENVELOPE_BYTES:
                raise SecretBrokerError("Secret broker envelope exceeds the configured bound.")
            try:
                parsed = json.loads(raw_envelope)
            except json.JSONDecodeError as exc:
                raise SecretBrokerError("Secret broker envelope is invalid JSON.") from exc
            if not isinstance(parsed, dict):
                raise SecretBrokerError("Secret broker envelope must be a JSON object.")
            for handle, secret in parsed.items():
                broker._put(handle, secret)

        for env_name, handle in (
            ("CODING_TOOLS_MCP_AUTH_TOKEN", MCP_AUTH_HANDLE),
            ("MCP_AUTH_TOKEN", MCP_AUTH_HANDLE),
            ("OPENAI_API_KEY", OPENAI_API_KEY_HANDLE),
        ):
            value = source.pop(env_name, "") if consume else source.get(env_name, "")
            if value:
                broker._put(handle, value)
        return broker

    def resolve(self, handle: str) -> str | None:
        return self._values.get(_validated_handle(handle))

    def inject_env(
        self,
        base: Mapping[str, str],
        bindings: Mapping[str, str],
    ) -> dict[str, str]:
        env = {str(key): str(value) for key, value in base.items()}
        for env_name, handle in bindings.items():
            normalized_name = str(env_name or "").strip().upper()
            if not _ENV_NAME_RE.fullmatch(normalized_name):
                raise SecretBrokerError("Secret broker environment binding is invalid.")
            secret = self.resolve(handle)
            if secret is not None:
                env[normalized_name] = secret
        return env

    def status(self) -> dict[str, object]:
        return {
            "schema_version": SECRET_BROKER_SCHEMA_VERSION,
            "enabled": bool(self._values),
            "handle_count": len(self._values),
            "content_free": True,
        }
