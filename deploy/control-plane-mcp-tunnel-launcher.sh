#!/usr/bin/env bash
# Run one OpenAI Secure MCP Tunnel profile that was initialized for the
# dedicated Ubuntu root-MCP loopback listener.  The profile is created by an
# operator with `tunnel-client init`; this launcher never receives, prints, or
# synthesizes a Runtime API Key.
set -euo pipefail

readonly RELEASE_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly PACKAGE_ROOT="$RELEASE_ROOT/control-plane"

if [[ ! -f "$PACKAGE_ROOT/control_plane/__main__.py" ]]; then
  printf 'control-plane release package is incomplete\n' >&2
  exit 2
fi

: "${CONTROL_PLANE_TUNNEL_CLIENT:?CONTROL_PLANE_TUNNEL_CLIENT is required}"
: "${CONTROL_PLANE_TUNNEL_PROFILE:?CONTROL_PLANE_TUNNEL_PROFILE is required}"
: "${CONTROL_PLANE_TUNNEL_ID:?CONTROL_PLANE_TUNNEL_ID is required}"
: "${CONTROL_PLANE_MCP_AUTH_HEADER_FILE:?CONTROL_PLANE_MCP_AUTH_HEADER_FILE is required}"
: "${CONTROL_PLANE_MCP_BIND:=127.0.0.1}"
: "${CONTROL_PLANE_MCP_PORT:=8766}"

if [[ "$CONTROL_PLANE_MCP_BIND" != "127.0.0.1" ]]; then
  printf 'CONTROL_PLANE_MCP_BIND must be 127.0.0.1 for the root MCP tunnel\n' >&2
  exit 2
fi
if [[ ! "$CONTROL_PLANE_MCP_PORT" =~ ^[1-9][0-9]{3,4}$ ]] || (( CONTROL_PLANE_MCP_PORT < 1024 || CONTROL_PLANE_MCP_PORT > 65535 )); then
  printf 'CONTROL_PLANE_MCP_PORT is invalid\n' >&2
  exit 2
fi
if [[ ! "$CONTROL_PLANE_TUNNEL_ID" =~ ^tunnel_[A-Za-z0-9_-]{4,}$ ]]; then
  printf 'CONTROL_PLANE_TUNNEL_ID is invalid\n' >&2
  exit 2
fi
if [[ "$CONTROL_PLANE_TUNNEL_CLIENT" != /* || ! -f "$CONTROL_PLANE_TUNNEL_CLIENT" || ! -x "$CONTROL_PLANE_TUNNEL_CLIENT" ]]; then
  printf 'CONTROL_PLANE_TUNNEL_CLIENT is not an executable regular file\n' >&2
  exit 2
fi

# This file contains the complete MCP Authorization header value, not the
# OpenAI Runtime API Key or the control-plane operator credential.  Inspect
# only metadata here: tunnel-client reads the file reference itself.
if [[ "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" != /* ||
      "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" == *$'\n'* ||
      "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" == *$'\r'* ||
      ! -f "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" ||
      -L "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" ||
      ! -r "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" ||
      ! -s "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE" ]] ||
   [[ "$(stat -c '%u' -- "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE")" != "$EUID" ]]; then
  printf 'CONTROL_PLANE_MCP_AUTH_HEADER_FILE must be a readable, nonempty, owner-owned regular file, not a symlink\n' >&2
  exit 2
fi
case "$(stat -c '%a' -- "$CONTROL_PLANE_MCP_AUTH_HEADER_FILE")" in
  400|600) ;;
  *) printf 'CONTROL_PLANE_MCP_AUTH_HEADER_FILE must have mode 0400 or 0600\n' >&2; exit 2 ;;
esac

# Do not pass the privileged operator token even if a manual invocation
# accidentally inherited it. The service uses a separate, nonsecret env file.
unset CONTROL_PLANE_OPERATOR_TOKEN

# Pin both identity and the sole main upstream at execution time so a stale
# profile cannot forward this Tunnel to a Windows listener or the operator UI.
# Only file references appear in argv; the profile also stores its Runtime API
# Key as a file reference. No fallback URL or second Tunnel is permitted here.
exec "$CONTROL_PLANE_TUNNEL_CLIENT" run \
  --profile "$CONTROL_PLANE_TUNNEL_PROFILE" \
  --control-plane.tunnel-id "$CONTROL_PLANE_TUNNEL_ID" \
  --mcp.server-url "url=http://127.0.0.1:${CONTROL_PLANE_MCP_PORT}/mcp,channel=main" \
  --mcp.extra-headers "Authorization: file:${CONTROL_PLANE_MCP_AUTH_HEADER_FILE}" \
  --mcp.discovery-extra-headers "Authorization: file:${CONTROL_PLANE_MCP_AUTH_HEADER_FILE}"
