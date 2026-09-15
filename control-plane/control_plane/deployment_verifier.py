"""Read-only, fail-closed verification of a selected control-plane deployment.

The verifier requests only the unauthenticated ``/healthz`` endpoint.  It
never opens SQLite, starts a server, reads credentials, or changes a remote
service.  A successful receipt proves only that one health response had the
operator-supplied package fingerprint and expected startup gate at that time;
it is not systemd, service-account, checkout, TLS, write-admission, or canary
attestation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Sequence
from urllib.parse import urlsplit

from .store import SCHEMA_VERSION


FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SERVICE_INSTANCE_PATTERN = re.compile(r"^cp_[a-f0-9]{32}$")
ADMISSION_MODES = frozenset({"open", "recovery"})
MAX_HEALTH_BYTES = 128 * 1024


class DeploymentVerificationError(RuntimeError):
    """A typed, content-free deployment-health verification failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so verification makes exactly one explicit GET."""

    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def _health_url(value: str) -> str:
    """Accept only a credential-free absolute HTTP(S) URL ending in /healthz."""

    candidate = str(value or "").strip()
    parsed = urlsplit(candidate)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/healthz"
        or parsed.query
        or parsed.fragment
    ):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_URL_INVALID")
    return candidate


def _fingerprint(value: str) -> str:
    candidate = str(value or "").strip()
    if not FINGERPRINT_PATTERN.fullmatch(candidate):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_FINGERPRINT_INVALID")
    return candidate


def _admission(value: str) -> str:
    candidate = str(value or "").strip()
    if candidate not in ADMISSION_MODES:
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_ADMISSION_INVALID")
    return candidate


def _read_health(health_url: str, timeout_seconds: float) -> dict[str, Any]:
    try:
        request = urllib.request.Request(health_url, headers={"Accept": "application/json"}, method="GET")
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_UNAVAILABLE")
            body = response.read(MAX_HEALTH_BYTES + 1)
    except DeploymentVerificationError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_UNAVAILABLE") from None

    if len(body) > MAX_HEALTH_BYTES:
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_INVALID")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_INVALID") from None
    if not isinstance(payload, dict):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_INVALID")
    return payload


def verify_health(
    *,
    health_url: str,
    expected_package_source_sha256: str,
    expected_admission: str,
    timeout_seconds: float = 5,
) -> dict[str, Any]:
    """Verify the exact health fields required for a selected package.

    Values that are absent/null are classified separately from a contradictory
    value so an older deployment cannot be mistaken for the selected package.
    No endpoint, response body, exception text, or credentials appear in the
    returned receipt or typed error.
    """

    if not 0 < timeout_seconds <= 30:
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_TIMEOUT_INVALID")
    checked_url = _health_url(health_url)
    expected_fingerprint = _fingerprint(expected_package_source_sha256)
    admission = _admission(expected_admission)
    payload = _read_health(checked_url, timeout_seconds)

    required_fields = (
        "service",
        "ok",
        "sqlite_integrity",
        "schema_version",
        "admission_mode",
        "service_instance_id",
        "package_source_sha256",
        "expected_package_source_sha256",
    )
    if any(name not in payload or payload[name] is None for name in required_fields):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE")

    if (
        payload["service"] != "coding-tools-control-plane"
        or payload["ok"] is not True
        or payload["sqlite_integrity"] != "ok"
        or payload["schema_version"] != SCHEMA_VERSION
        or payload["admission_mode"] != admission
        or not isinstance(payload["service_instance_id"], str)
        or SERVICE_INSTANCE_PATTERN.fullmatch(payload["service_instance_id"]) is None
        or payload["package_source_sha256"] != expected_fingerprint
        or payload["expected_package_source_sha256"] != expected_fingerprint
    ):
        raise DeploymentVerificationError("CONTROL_PLANE_DEPLOYMENT_HEALTH_MISMATCH")

    return {
        "operation": "control_plane_deployment_health_verification",
        "service": "coding-tools-control-plane",
        "service_instance_id": payload["service_instance_id"],
        "schema_version": SCHEMA_VERSION,
        "admission_mode": admission,
        "package_source_sha256": expected_fingerprint,
        "expected_package_source_sha256": expected_fingerprint,
        "sqlite_integrity": "ok",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health-url", required=True, help="credential-free absolute HTTP(S) /healthz URL")
    parser.add_argument(
        "--expected-package-source-sha256",
        required=True,
        help="exact sha256:<64 lowercase hex> fingerprint from the selected package receipt",
    )
    parser.add_argument("--expected-admission", required=True, choices=sorted(ADMISSION_MODES))
    parser.add_argument("--timeout-seconds", type=float, default=5, help="read-only request timeout (0, 30] seconds")
    args = parser.parse_args(argv)
    try:
        receipt = verify_health(
            health_url=args.health_url,
            expected_package_source_sha256=args.expected_package_source_sha256,
            expected_admission=args.expected_admission,
            timeout_seconds=args.timeout_seconds,
        )
    except DeploymentVerificationError as error:
        print(json.dumps({"error": {"code": error.code}}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(receipt, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
