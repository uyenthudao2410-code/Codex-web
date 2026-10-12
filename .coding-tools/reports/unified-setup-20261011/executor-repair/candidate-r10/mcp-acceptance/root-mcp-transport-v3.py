"""Additive transport for the explicitly approved same-expiry pilot replacement.

Root executes; import only loads immutable transport definitions. Frozen canary
and transport bytes remain unchanged. No authority operation is implemented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

BASE = Path(__file__).resolve().parent
ORIGINAL = BASE / "root-mcp-transport.py"
ORIGINAL_SHA = "a081b293cd1e33fbc4c53f86ed52fe2c9c2ce53cb6b6797c4fee1b615eaf5d19"
RENEWAL = BASE.parent / "activation/server-authority-renewal.json"
RENEWAL_SHA = "54d83471ed13e919fe035a037427931906bac87b1334698094b563c5454fa83b"
REOPEN = BASE.parent / "activation/server-recovery-reopened.json"
REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
PACKAGE = "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"


def need(value, code):
    if not value:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


raw = ORIGINAL.read_bytes()
need(sha(raw) == ORIGINAL_SHA, "FROZEN_TRANSPORT_CHANGED")
scope = {"__name__": "root_mcp_transport_v3_frozen_definitions", "__file__": str(ORIGINAL)}
exec(compile(raw, str(ORIGINAL), "exec"), scope)
old_pins_bytes = scope["pins_bytes"]


def replacement_guard(file: Path, expected: str):
    need(file.resolve(strict=True) == REOPEN.resolve(strict=True) and not file.is_symlink(), "EXACT_RECOVERY_RECEIPT_PATH_REQUIRED")
    raw = file.read_bytes()
    need(0 < len(raw) <= 131072 and re.fullmatch(r"[a-f0-9]{64}", expected or "") and sha(raw) == expected,
         "EXPLICIT_RECOVERY_RECEIPT_HASH_REQUIRED")
    receipt = json.loads(raw)
    renewal_raw = RENEWAL.read_bytes()
    need(sha(renewal_raw) == RENEWAL_SHA, "ORIGINAL_RENEWAL_CHANGED")
    renewal = json.loads(renewal_raw)
    need(renewal["source_revision"] == REVISION and renewal["service_grant_preserved"] == GRANT
         and renewal["service_grant_changed"] is False and renewal["service_instance_id"] == scope["SERVICE"]
         and renewal["context_id"] == scope["CONTEXT"] and renewal["pilot_id"] == scope["PILOT"]
         and renewal["requested_at_ms"] == scope["REQUESTED"] and renewal["expires_at_ms"] == scope["EXPIRES"], "EXACT_ORIGINAL_AUTHORITY_REQUIRED")
    now = int(time.time() * 1000)
    need(receipt["phase"] == "r10_same_window_intake_reopened" and receipt["ok"] is True
         and receipt["remote_mutation"] is True and receipt["admission"] == "scoped_pilot"
         and receipt["binding_id"] == scope["BINDING"] and receipt["service_instance_id"] == scope["SERVICE"]
         and receipt["source_revision"] == REVISION and receipt["package_source_sha256"] == PACKAGE
         and receipt["service_grant_preserved"] == GRANT
         and receipt["context_id"] == scope["CONTEXT"] and receipt["pilot_id"] == scope["PILOT"]
         and receipt["original_pilot_id"] == scope["PILOT"] and receipt["newpilot_id"] != scope["PILOT"]
         and re.fullmatch(r"pilot_[a-f0-9]{32}", receipt["newpilot_id"])
         and receipt["requested_at_ms"] == scope["REQUESTED"] and receipt["expires_at_ms"] == scope["EXPIRES"]
         and type(receipt["observed_at_ms"]) is int and 0 <= now - receipt["observed_at_ms"] < 600000
         and now + 600000 < scope["EXPIRES"]
         and all(receipt[name] is False for name in ("authority_renewed", "original_marker_modified", "service_grant_changed", "command_replayed", "pending_acceptance_changed")),
         "FRESH_SAME_EXPIRY_REPLACEMENT_RECEIPT_REQUIRED")
    need(re.fullmatch(r"activation-[A-Za-z0-9_-]{8,128}", receipt["activation_epoch"])
         and receipt["activation_epoch"] not in {"activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7", "activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba"}, "NEW_RECOVERY_EPOCH_REQUIRED")
    state = receipt["state"]
    need(sha(json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()) == receipt["state_sha256"], "RECOVERY_STATE_DIGEST_MISMATCH")
    # Frozen canary inspect()/authority_guard performs the live exact source,
    # package, binding, service grant, context, pilot and ready-node validation.
    # The receipt declares preservation; no changed grant is accepted here.
    return receipt


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reopen-receipt-file", type=Path, required=True)
    parser.add_argument("--reopen-receipt-sha256", required=True)
    args, remaining = parser.parse_known_args()
    receipt = replacement_guard(args.reopen_receipt_file, args.reopen_receipt_sha256)
    need(remaining and remaining[0] in {"preflight", "execute"}, "V3_PREFLIGHT_OR_EXECUTE_ONLY")
    scope["PILOT"] = receipt["newpilot_id"]

    def pins_bytes(file):
        raw, pins = old_pins_bytes(file)
        need(pins["activation_epoch_id"] == receipt["activation_epoch"]
             and pins["rollout_receipt_sha256"] == args.reopen_receipt_sha256, "PINS_NOT_BOUND_TO_RECOVERY_RECEIPT")
        return raw, pins

    scope["pins_bytes"] = pins_bytes
    sys.argv = [str(Path(__file__).resolve())] + remaining
    # Original main retains exact argv, no-replay marker, public output guards,
    # SSH transport, immutable canary hash and one-attempt failure semantics.
    scope["main"]()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "root_mcp_transport_v3_failed", "ok": False,
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__,
                          "no_automatic_retry": True, "root_reconciliation_required": True}, separators=(",", ":")), flush=True)
        raise SystemExit(2) from None
