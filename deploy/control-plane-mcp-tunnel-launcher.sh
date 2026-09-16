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
: "${CONTROL_PLANE_MCP_BIND:=127.0.0.1}"
: "${CONTROL_PLANE_MCP_PORT:=8766}"

if [[ "$CONTROL_PLANE_MCP_BIND" != "127.0.0.1" ]]; then
  printf 'CONTROL_PLANE_MCP_BIND must be 127.0.0.1 for the root MCP tunnel\n' >&2
  exit 2
fi
if [[ ! "$CONTROL_PLANE_MCP_PORT" =~ ^[0-9]+$ ]] || (( CONTROL_PLANE_MCP_PORT < 1024 || CONTROL_PLANE_MCP_PORT > 65535 )); then
  printf 'CONTROL_PLANE_MCP_PORT is invalid\n' >&2
  exit 2
fi
if [[ ! "$CONTROL_PLANE_TUNNEL_ID" =~ ^tunnel_[A-Za-z0-9_-]{4,}$ ]]; then
  printf 'CONTROL_PLANE_TUNNEL_ID is invalid\n' >&2
  exit 2
fi
if [[ ! -x "$CONTROL_PLANE_TUNNEL_CLIENT" ]]; then
  printf 'CONTROL_PLANE_TUNNEL_CLIENT is not an executable regular file\n' >&2
  exit 2
fi

# The OpenAI-supported profile flow keeps the chosen tunnel identity and exact
# local MCP URL in tunnel-client's protected profile configuration.  It must
# have been initialized with http://127.0.0.1:${CONTROL_PLANE_MCP_PORT}/mcp and
# checked with `tunnel-client doctor --profile ... --explain` before this
# service is started.  No fallback URL or second Tunnel is permitted here.
exec "$CONTROL_PLANE_TUNNEL_CLIENT" run --profile "$CONTROL_PLANE_TUNNEL_PROFILE"
