#!/usr/bin/env bash
# Start the control-plane code from the immutable release containing this
# launcher. Runtime state and the protected environment file are intentionally
# outside that release tree.
set -euo pipefail

readonly RELEASE_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly PACKAGE_ROOT="$RELEASE_ROOT/control-plane"

if [[ ! -f "$PACKAGE_ROOT/control_plane/__main__.py" ]]; then
  printf 'control-plane release package is incomplete\n' >&2
  exit 2
fi

export PYTHONPATH="$PACKAGE_ROOT"
exec /usr/bin/python3 -B -m control_plane
