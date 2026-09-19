"""Fail-closed OAuth introspection support for the root MCP resource server.

The control plane deliberately supports a small, configuration-driven OAuth
mode instead of treating a Tunnel header or a decoded token payload as a user
identity.  A real identity provider remains an operator decision: this module
only validates the resource-server side once an issuer, resource identifier,
introspection endpoint, and owner-private client credential file are supplied.

OAuth metadata and access tokens can travel through the Secure MCP Tunnel, but
the authorization server itself is external to that private transport.  The
configuration therefore names HTTPS endpoints explicitly and rejects partial
or ambiguous modes at startup.
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


MCP_AUTH_MODE_LEGACY_CONTEXT_GRANT = "legacy_context_grant"
MCP_AUTH_MODE_OAUTH_INTROSPECTION = "oauth_introspection"
MCP_AUTH_MODES = frozenset({MCP_AUTH_MODE_LEGACY_CONTEXT_GRANT, MCP_AUTH_MODE_OAUTH_INTROSPECTION})

MAX_ACCESS_TOKEN_BYTES = 8192
MAX_INTROSPECTION_RESPONSE_BYTES = 16 * 1024
INTROSPECTION_TIMEOUT_SECONDS = 5
_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{3,128}$")


class OAuthConfigurationError(ValueError):
    """The protected resource cannot safely enter OAuth mode."""


class OAuthAuthenticationError(RuntimeError):
    """An access token is absent, malformed, or not valid for this resource."""


def _finite_numeric_claim(value: Any) -> bool:
    """Accept one finite JSON number while rejecting bool/NaN/infinity.

    Python's JSON decoder accepts non-standard ``NaN``/``Infinity`` spellings
    and a malformed IdP response must not make an expiry comparison evaluate
    false by accident.  An arbitrarily large integer can also overflow a
    conversion inside ``math.isfinite``, so treat it as invalid rather than
    relying on an implicit numeric coercion.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _required_environment(value: Mapping[str, str], name: str) -> str:
    candidate = value.get(name)
    text = candidate if isinstance(candidate, str) else ""
    if not text or text != text.strip():
        raise OAuthConfigurationError(f"{name} is required for OAuth MCP authentication.")
    return text


def _https_url(value: str, field: str, *, origin_only: bool = False) -> str:
    """Accept one explicit HTTPS URL without silently normalizing identity."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise OAuthConfigurationError(f"{field} must be a canonical HTTPS URL.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise OAuthConfigurationError(f"{field} must be a canonical HTTPS URL.") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port is not None and not 1 <= port <= 65535
        or origin_only and parsed.path not in {"", "/"}
    ):
        raise OAuthConfigurationError(f"{field} must be a canonical HTTPS URL.")
    # The issuer and resource values are compared exactly with provider/token
    # values.  Do not add or remove a slash, path, port, or case here.
    return value


def _opaque_text(value: Any, field: str, *, maximum_bytes: int = 1024) -> str:
    """Keep opaque IdP identifiers out of logs and SQLite as raw values."""

    if not isinstance(value, str):
        raise OAuthAuthenticationError("OAuth access token is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise OAuthAuthenticationError("OAuth access token is invalid.") from error
    if not encoded or len(encoded) > maximum_bytes or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise OAuthAuthenticationError("OAuth access token is invalid.")
    return value


@dataclass(frozen=True)
class OAuthClientCredentials:
    """One owner-private introspection client, never rendered or logged."""

    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)


def _read_client_credentials(path_value: str) -> OAuthClientCredentials:
    """Read a small JSON credential file with the same ownership guarantees as secrets.

    The service environment supplies only a file reference.  The credential is
    never accepted from a Tunnel request, node, browser, or process argv.
    """

    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute() or "\n" in path_value or "\r" in path_value:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE must be an absolute regular file.")
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE is unavailable.") from error
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_size <= 0
        or metadata.st_size > 4096
        or hasattr(os, "geteuid") and metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) not in {0o400, 0o600}
    ):
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE is not owner-private.")
    try:
        document = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE is invalid.") from error
    if not isinstance(document, dict) or set(document) != {"client_id", "client_secret"}:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE is invalid.")
    try:
        client_id = _opaque_text(document["client_id"], "client_id", maximum_bytes=512)
        client_secret = _opaque_text(document["client_secret"], "client_secret", maximum_bytes=1024)
    except OAuthAuthenticationError as error:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE is invalid.") from error
    return OAuthClientCredentials(client_id=client_id, client_secret=client_secret)


@dataclass(frozen=True)
class OAuthIntrospectionConfiguration:
    """The fixed identity-provider contract for this root MCP resource."""

    issuer: str
    resource: str
    introspection_url: str
    required_scope: str
    credentials: OAuthClientCredentials = field(repr=False)
    # Inventory is intentionally the default OAuth capability.  Bounded file
    # reads are a separate, candidate-only relay and must be made explicit in
    # the server's protected profile before any client can discover it.
    file_read_enabled: bool = False
    # C4 starts with a review-only patch permission request.  This flag is
    # separate from file reads and does not enable a mutation relay, local
    # policy, action dispatch, shell, or process launch.
    permission_requests_enabled: bool = False
    # A central permission record and a Windows write are both mutations.  Do
    # not reuse the inventory scope for either one; the candidate must name an
    # additional exact scope so the IdP consent and tool descriptor remain
    # truthful.
    patch_write_scope: str | None = None
    # This remains off until the independent Windows patch policy/bridge is
    # packaged and intentionally enabled for a canary.
    approved_patch_enabled: bool = False
    # Bounded exec reuses the patch write scope but needs its own explicit
    # flag: argv execution is a new authority even after patch relay exists.
    exec_enabled: bool = False

    @property
    def resource_metadata_url(self) -> str:
        return f"{self.resource.rstrip('/')}/.well-known/oauth-protected-resource"

    @property
    def security_schemes(self) -> list[dict[str, Any]]:
        return [{"type": "oauth2", "scopes": [self.required_scope]}]

    @property
    def supported_scopes(self) -> tuple[str, ...]:
        return (
            (self.required_scope, self.patch_write_scope)
            if self.patch_write_scope is not None
            else (self.required_scope,)
        )

    def protected_resource_metadata(self) -> dict[str, Any]:
        return {
            "resource": self.resource,
            "authorization_servers": [self.issuer],
            "scopes_supported": list(self.supported_scopes),
        }

    def www_authenticate(
        self,
        *,
        error: str = "invalid_token",
        required_scopes: Iterable[str] | None = None,
    ) -> str:
        # All fields are startup-validated HTTPS URLs / scope tokens.  This is
        # intentionally constant-content with respect to any presented token.
        requested = tuple(required_scopes) if required_scopes is not None else (self.required_scope,)
        if (
            not requested
            or any(not isinstance(scope, str) or scope not in self.supported_scopes for scope in requested)
        ):
            raise OAuthConfigurationError("OAuth challenge scopes are invalid.")
        return (
            f'Bearer resource_metadata="{self.resource_metadata_url}", '
            f'scope="{" ".join(requested)}", error="{error}", '
            'error_description="OAuth access token is required"'
        )


def oauth_configuration_from_environment(
    environment: Mapping[str, str] | None = None,
) -> OAuthIntrospectionConfiguration | None:
    """Load an all-or-nothing resource-server OAuth configuration.

    ``None`` means the historical, explicitly named pilot grant mode.  OAuth
    mode is opt-in and fails during service startup on a missing credential or
    partial provider configuration; it never falls back to the shared bearer.
    """

    source = os.environ if environment is None else environment
    raw_mode = source.get("CONTROL_PLANE_MCP_AUTH_MODE", MCP_AUTH_MODE_LEGACY_CONTEXT_GRANT)
    mode = raw_mode.strip() if isinstance(raw_mode, str) else ""
    if not mode:
        mode = MCP_AUTH_MODE_LEGACY_CONTEXT_GRANT
    if mode not in MCP_AUTH_MODES:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_AUTH_MODE is invalid.")
    oauth_names = (
        "CONTROL_PLANE_MCP_OAUTH_RESOURCE",
        "CONTROL_PLANE_MCP_OAUTH_ISSUER",
        "CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL",
        "CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE",
        "CONTROL_PLANE_MCP_OAUTH_SCOPE",
        "CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED",
        "CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED",
        "CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE",
        "CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED",
        "CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED",
    )
    if mode == MCP_AUTH_MODE_LEGACY_CONTEXT_GRANT:
        if any(str(source.get(name, "") or "").strip() for name in oauth_names):
            raise OAuthConfigurationError("OAuth MCP settings require CONTROL_PLANE_MCP_AUTH_MODE=oauth_introspection.")
        return None
    resource = _https_url(_required_environment(source, "CONTROL_PLANE_MCP_OAUTH_RESOURCE"), "CONTROL_PLANE_MCP_OAUTH_RESOURCE", origin_only=True)
    issuer = _https_url(_required_environment(source, "CONTROL_PLANE_MCP_OAUTH_ISSUER"), "CONTROL_PLANE_MCP_OAUTH_ISSUER")
    introspection_url = _https_url(
        _required_environment(source, "CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL"),
        "CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL",
    )
    required_scope = _required_environment(source, "CONTROL_PLANE_MCP_OAUTH_SCOPE")
    if _SCOPE_PATTERN.fullmatch(required_scope) is None:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_SCOPE is invalid.")
    raw_file_read = source.get("CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED", "")
    if not isinstance(raw_file_read, str) or raw_file_read not in {"", "false", "true"}:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED must be true or false.")
    raw_permission_requests = source.get("CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED", "")
    if not isinstance(raw_permission_requests, str) or raw_permission_requests not in {"", "false", "true"}:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED must be true or false.")
    if raw_permission_requests == "true" and raw_file_read != "true":
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED requires CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED=true.")
    raw_patch_write_scope = source.get("CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE", "")
    if not isinstance(raw_patch_write_scope, str) or raw_patch_write_scope != raw_patch_write_scope.strip():
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE is invalid.")
    patch_write_scope = raw_patch_write_scope or None
    if patch_write_scope is not None and _SCOPE_PATTERN.fullmatch(patch_write_scope) is None:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE is invalid.")
    if raw_permission_requests == "true":
        if patch_write_scope is None or patch_write_scope == required_scope:
            raise OAuthConfigurationError("OAuth patch permission requests require a distinct CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE.")
    elif patch_write_scope is not None:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE requires CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED=true.")
    raw_approved_patch = source.get("CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED", "")
    if not isinstance(raw_approved_patch, str) or raw_approved_patch not in {"", "false", "true"}:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED must be true or false.")
    if raw_approved_patch == "true" and raw_permission_requests != "true":
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED requires CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED=true.")
    raw_exec = source.get("CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED", "")
    if not isinstance(raw_exec, str) or raw_exec not in {"", "false", "true"}:
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED must be true or false.")
    if raw_exec == "true" and raw_approved_patch != "true":
        raise OAuthConfigurationError("CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED requires CONTROL_PLANE_MCP_OAUTH_APPROVED_PATCH_ENABLED=true.")
    credentials = _read_client_credentials(_required_environment(source, "CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE"))
    return OAuthIntrospectionConfiguration(
        issuer=issuer,
        resource=resource,
        introspection_url=introspection_url,
        required_scope=required_scope,
        credentials=credentials,
        file_read_enabled=raw_file_read == "true",
        permission_requests_enabled=raw_permission_requests == "true",
        patch_write_scope=patch_write_scope,
        approved_patch_enabled=raw_approved_patch == "true",
        exec_enabled=raw_exec == "true",
    )


@dataclass(frozen=True)
class OAuthAccessIdentity:
    """Validated provider claims retained only for the immediate DB lookup."""

    issuer: str
    subject: str = field(repr=False)
    scopes: frozenset[str]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, _request: Request, _fp: Any, _code: int, _message: str, _headers: Any, _newurl: str) -> Request | None:
        return None


class OAuthIntrospectionVerifier:
    """Verify one OAuth access token through an authenticated IdP endpoint.

    Introspection is allowed for opaque or signed access tokens, but the
    response is still untrusted until this resource checks ``active``, issuer,
    audience/resource, expiry, and the required scope.  There is intentionally
    no JWT payload decoder here, so an ID token or forged JWT can never be
    accepted merely because it has plausible claims.
    """

    def __init__(
        self,
        configuration: OAuthIntrospectionConfiguration,
        *,
        clock_seconds: Callable[[], float] = time.time,
        transport: Callable[[Request], Any] | None = None,
    ) -> None:
        self.configuration = configuration
        self._clock_seconds = clock_seconds
        self._transport = transport

    def _open(self, request: Request) -> Any:
        if self._transport is not None:
            return self._transport(request)
        opener = build_opener(_NoRedirect())
        return opener.open(request, timeout=INTROSPECTION_TIMEOUT_SECONDS)

    @staticmethod
    def _access_token(value: Any) -> str:
        if not isinstance(value, str) or not value or value != value.strip():
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        try:
            encoded = value.encode("ascii")
        except UnicodeEncodeError as error:
            raise OAuthAuthenticationError("OAuth access token is invalid.") from error
        if len(encoded) > MAX_ACCESS_TOKEN_BYTES or any(byte < 33 or byte > 126 for byte in encoded):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return value

    def _request(self, token: str) -> Request:
        credentials = self.configuration.credentials
        basic = base64.b64encode(f"{credentials.client_id}:{credentials.client_secret}".encode("utf-8")).decode("ascii")
        return Request(
            self.configuration.introspection_url,
            data=urlencode({"token": token, "token_type_hint": "access_token"}).encode("ascii"),
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

    def _introspection_response(self, token: str) -> dict[str, Any]:
        response: Any = None
        try:
            response = self._open(self._request(token))
            # ``getattr(..., response.getcode())`` evaluates the fallback
            # before checking ``status``.  That makes an otherwise valid
            # test/dedicated transport response fail merely because it does
            # not also implement urllib's ``getcode`` method.  Accept either
            # documented response shape, but never invent a status when both
            # are absent.
            if hasattr(response, "status"):
                status = int(response.status)
            else:
                status = int(response.getcode())
            content_type = str(getattr(response, "headers", {}).get("Content-Type", "")).lower()
            raw = response.read(MAX_INTROSPECTION_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, OSError, ValueError, TypeError):
            raise OAuthAuthenticationError("OAuth access token is invalid.") from None
        finally:
            if response is not None:
                try:
                    response.close()
                except OSError:
                    pass
        if status != 200 or "application/json" not in content_type or not isinstance(raw, bytes) or len(raw) > MAX_INTROSPECTION_RESPONSE_BYTES:
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OAuthAuthenticationError("OAuth access token is invalid.") from error
        if not isinstance(parsed, dict):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return parsed

    @staticmethod
    def _audiences(value: Any) -> frozenset[str]:
        if isinstance(value, str):
            return frozenset({value})
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return frozenset(value)
        return frozenset()

    @staticmethod
    def _scopes(value: Any) -> frozenset[str]:
        if not isinstance(value, str) or value != value.strip():
            return frozenset()
        scopes = value.split(" ")
        if not scopes or any(_SCOPE_PATTERN.fullmatch(scope) is None for scope in scopes):
            return frozenset()
        return frozenset(scopes)

    def authenticate(
        self,
        access_token: Any,
        *,
        required_scopes: Iterable[str] | None = None,
    ) -> OAuthAccessIdentity:
        token = self._access_token(access_token)
        payload = self._introspection_response(token)
        configuration = self.configuration
        if payload.get("active") is not True or payload.get("iss") != configuration.issuer:
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        subject = _opaque_text(payload.get("sub"), "sub")
        audiences = self._audiences(payload.get("aud"))
        scopes = self._scopes(payload.get("scope"))
        expiration = payload.get("exp")
        # This resource accepts only Bearer *access* tokens.  RFC 7662 does
        # not force every provider to distinguish every token class for us,
        # so an active response alone is insufficient: a provider that also
        # introspects an ID token or another credential type must not turn it
        # into MCP authority.  OAuth bearer token types are case-insensitive.
        token_type = payload.get("token_type")
        not_before = payload.get("nbf")
        required = frozenset(required_scopes) if required_scopes is not None else frozenset({configuration.required_scope})
        if (
            not required
            or not required <= set(configuration.supported_scopes)
            or any(not isinstance(scope, str) for scope in required)
            or
            not isinstance(token_type, str)
            or token_type.casefold() != "bearer"
            or configuration.resource not in audiences
            or not required <= scopes
            or not _finite_numeric_claim(expiration)
            or expiration <= self._clock_seconds()
            or ("nbf" in payload and (not _finite_numeric_claim(not_before) or not_before > self._clock_seconds()))
        ):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return OAuthAccessIdentity(issuer=configuration.issuer, subject=subject, scopes=scopes)
