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
: "${CONTROL_PLANE_MCP_AUTH_MODE:=legacy_context_grant}"
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

header_args=()
case "$CONTROL_PLANE_MCP_AUTH_MODE" in
  legacy_context_grant|private_tunnel_service)
    : "${CONTROL_PLANE_MCP_AUTH_HEADER_FILE:?CONTROL_PLANE_MCP_AUTH_HEADER_FILE is required in grant modes}"
    # This file contains the complete MCP Authorization header for the
    # selected mode, never the OpenAI Runtime API Key or operator credential.
    # In private_tunnel_service mode it authenticates a shared connector,
    # not an individual ChatGPT member. Inspect metadata only; tunnel-client
    # reads the protected file reference itself.
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
    header_args=(
      --mcp.extra-headers "Authorization: file:${CONTROL_PLANE_MCP_AUTH_HEADER_FILE}"
      --mcp.discovery-extra-headers "Authorization: file:${CONTROL_PLANE_MCP_AUTH_HEADER_FILE}"
    )
    ;;
  oauth_introspection)
    # In OAuth mode ChatGPT supplies the account access token on each request.
    # A static pilot header would overwrite it or turn every account into the
    # old shared principal, so reject even an empty accidental setting rather
    # than silently ignoring it.
    if [[ -n "${CONTROL_PLANE_MCP_AUTH_HEADER_FILE+x}" ]]; then
      printf 'CONTROL_PLANE_MCP_AUTH_HEADER_FILE must be unset in oauth_introspection mode\n' >&2
      exit 2
    fi
    ;;
  *)
    printf 'CONTROL_PLANE_MCP_AUTH_MODE must be legacy_context_grant, private_tunnel_service or oauth_introspection\n' >&2
    exit 2
    ;;
esac

# Do not pass the privileged operator token even if a manual invocation
# accidentally inherited it. The service uses a separate, nonsecret env file.
unset CONTROL_PLANE_OPERATOR_TOKEN

# Pin both identity and the sole main upstream at execution time so a stale
# profile cannot forward this Tunnel to a Windows listener or the operator UI.
# Only file references appear in legacy argv; OAuth account tokens are never
# stored in the profile or supplied as launcher arguments. The profile itself
# stores its Runtime API Key as a file reference. No fallback URL or second
# Tunnel is permitted here. This launcher never switches accounts or profiles
# on its own: exactly one profile and one Tunnel ID run per invocation.

# Permanent credential handling: tunnel-client retries poll failures with
# backoff. A 401 account_deactivated response is terminal, so stop this tunnel
# after a short consecutive-failure run instead of retrying forever. The marker
# is keyed to the exact Tunnel ID; changing to a separately provisioned Tunnel
# ID is the operator's explicit recovery action.
readonly DEAD_CREDENTIAL_MARK_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/codex-control-plane"
readonly DEAD_CREDENTIAL_MARK_FILE="$DEAD_CREDENTIAL_MARK_DIR/tunnel-credential-dead"
readonly DEAD_CREDENTIAL_THRESHOLD=3

dead_marker_matches_current_tunnel() {
  [[ -f "$DEAD_CREDENTIAL_MARK_FILE" ]] &&
    grep -qxF "tunnel_id=${CONTROL_PLANE_TUNNEL_ID}" "$DEAD_CREDENTIAL_MARK_FILE"
}

refuse_dead_credential() {
  cat >&2 <<EOF
FATAL: tunnel ${CONTROL_PLANE_TUNNEL_ID} is marked with a dead OpenAI credential (account_deactivated).
Refusing to start: no retries, no account switching.
Operator action required:
  1. Restore the OpenAI account access, or provision an allowed tunnel
     (Tunnel ID + platform organization/ChatGPT workspace + Runtime API key).
  2. Create/select the tunnel-client profile for the allowed tunnel and set
     CONTROL_PLANE_TUNNEL_PROFILE / CONTROL_PLANE_TUNNEL_ID in mcp-tunnel.env.
     A new Tunnel ID automatically lifts this stop.
  3. If the same account was restored, clear the marker manually:
     rm -- ${DEAD_CREDENTIAL_MARK_FILE}
Marker: ${DEAD_CREDENTIAL_MARK_FILE}
EOF
}

if dead_marker_matches_current_tunnel; then
  refuse_dead_credential
  exit 0
fi

mkdir -p -- "$DEAD_CREDENTIAL_MARK_DIR"
chmod 0700 -- "$DEAD_CREDENTIAL_MARK_DIR"

credential_watchdog() {
  # This process-substitution subshell cannot see the client PID assigned
  # later. It records the exact-tunnel marker; the main shell owns the PID and
  # terminates the client after observing that marker.
  local line consecutive=0
  while IFS= read -r line; do
    printf '%s\n' "$line" >&2
    if [[ "$line" == *account_deactivated* ]]; then
      consecutive=$((consecutive + 1))
    else
      consecutive=0
    fi
    if (( consecutive >= DEAD_CREDENTIAL_THRESHOLD )); then
      {
        printf 'FATAL: OpenAI control plane reports account_deactivated for tunnel %s (%d consecutive poll failures).\n' "$CONTROL_PLANE_TUNNEL_ID" "$consecutive"
        printf 'Stopping this tunnel branch permanently: no further retries, no account switching.\n'
        printf 'Operator action required: restore account access or configure an allowed tunnel\n'
        printf '(new Tunnel ID + profile in mcp-tunnel.env), then start the service again.\n'
        printf 'Marker: %s\n' "$DEAD_CREDENTIAL_MARK_FILE"
      } >&2
      cat > "$DEAD_CREDENTIAL_MARK_FILE" <<EOF
tunnel_id=${CONTROL_PLANE_TUNNEL_ID}
first_seen=$(date -u +%Y-%m-%dT%H:%M:%SZ)
source=launcher-credential-watchdog
EOF
      chmod 0600 -- "$DEAD_CREDENTIAL_MARK_FILE"
      return 0
    fi
  done
  return 0
}

client_pid=0
forward_stop_to_client() {
  if (( client_pid > 0 )) && kill -0 "$client_pid" 2>/dev/null; then
    kill -TERM "$client_pid" 2>/dev/null || true
  fi
}
trap forward_stop_to_client TERM INT

"$CONTROL_PLANE_TUNNEL_CLIENT" run \
  --profile "$CONTROL_PLANE_TUNNEL_PROFILE" \
  --control-plane.tunnel-id "$CONTROL_PLANE_TUNNEL_ID" \
  --mcp.server-url "url=http://127.0.0.1:${CONTROL_PLANE_MCP_PORT}/mcp,channel=main" \
  "${header_args[@]}" 2> >(credential_watchdog) &
client_pid=$!
if (( client_pid <= 0 )); then
  printf 'failed to start tunnel-client\n' >&2
  exit 2
fi

client_rc=0
# Poll so the main shell — the only process that owns the client PID — can
# stop the client as soon as the watchdog records the dead-credential marker.
# Under systemd the whole service cgroup also receives SIGTERM on stop.
while kill -0 "$client_pid" 2>/dev/null; do
  if dead_marker_matches_current_tunnel; then
    kill -TERM "$client_pid" 2>/dev/null || true
    break
  fi
  sleep 1 || break
done
wait "$client_pid" || client_rc=$?
client_pid=0
trap - TERM INT
if dead_marker_matches_current_tunnel; then
  exit 0
fi
exit "$client_rc"
