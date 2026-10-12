"""Preserve the verified candidate archive and its code-only review packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


OUTPUT = Path(__file__).resolve().parent
receipt_path = OUTPUT / "artifact-receipt.json"
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
release = Path(receipt["release_directory"])
archive = Path(receipt["archive"])
if hashlib.sha256(archive.read_bytes()).hexdigest() != receipt["archive_sha256"]:
    raise RuntimeError("candidate archive changed since artifact verification")
delivery = OUTPUT / archive.name
if delivery.exists():
    raise RuntimeError("review archive already exists")
shutil.copyfile(archive, delivery)
shutil.copyfile(release / "release-manifest.json", OUTPUT / "candidate-release-manifest.json")
shutil.copyfile(release / "DEPLOYMENT.md", OUTPUT / "CANDIDATE-DEPLOYMENT.md")
receipt["review_archive"] = str(delivery)
receipt["review_archive_sha256"] = hashlib.sha256(delivery.read_bytes()).hexdigest()
receipt["review_manifest"] = str(OUTPUT / "candidate-release-manifest.json")
receipt["isolated_preparation_recovery"] = {
    "initial_checkout": "Windows path length failure; partial checkout preserved under dist",
    "resolution": "fresh isolated clone configured core.longpaths=true before checkout",
    "post_commit_status": "canonical ledger working bytes differ from transactional Git snapshot; release source clean",
    "clean_source_guard": "unchanged CLI require_clean_source=True; canonical Git blobs used",
}
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
readme = f"""# Owner Console standing-patch acceptance fix

## Prepared outcome

This packet is an artifact preparation receipt. No Ubuntu file, configuration,
database, current symlink, admission state, or service was changed.

- Base/deployed revision: `{receipt['base_revision']}`.
- Isolated candidate revision: `{receipt['source_revision']}`.
- Isolated branch: `codex/owner-standing-acceptance`.
- Archive: `{delivery.name}`.
- Archive SHA-256: `{receipt['archive_sha256']}`.
- Package fingerprint: `{receipt['package_source_sha256']}`.

The owner Console resolves the exact sealed principal from either owner-review
or standing patch intents, filtered by owner and action. It still delegates to
the existing principal, action, completed-receipt and UNKNOWN acceptance gates.
No schema migration or authority expansion is included.

## Provenance and complete release delta

The code-only SSH inspection verified all currently deployed files against the
existing manifest. All 36 canonical Git runtime/deploy/documentation inputs at
the base revision matched that deployed manifest. The deployed `store.py` was
byte-equal to the base revision. The isolated checkout contains only the fix,
its regression test, and mandatory delivery evidence updates.

Compared with the complete deployed release manifest:

1. `control-plane/control_plane/store.py` changes from
   `96db42eda0f332d707341d877e51a4ba178347e17149e019dc57b2abed8b20a4`
   to `99d3eba656a269886a842bc357a14222eb811bbb7dea8d0538c210d5f3edcf40`.
2. Generated `DEPLOYMENT.md` embeds the candidate revision.
3. `release-manifest.json` records the candidate revision, package/component
   fingerprints and changed store digest.

The remaining 35 manifest-listed files are unchanged. No other runtime or
deployment script changes are included. Detailed per-file observations are in
`preflight.json`; the full candidate comparison is in `artifact-receipt.json`.

## Verification

- The standing regression reproduced the original `NotFoundError` before the
  fix. The focused acceptance lane passed all four tests after the fix.
- Test coverage includes no completed receipt, UNKNOWN, cross-owner denial,
  exact sealed principal, acceptance after task closure, idempotent replay,
  conflicting verdict and revoked principal; owner-review acceptance passes.
- Passed unchanged test proof was reused for identical isolated source bytes.
- `npm run stage:coding-tools-delivery` and
  `npm run check:coding-tools-delivery` passed before the isolated commit.
- The release builder ran through its strict CLI with a real clean source
  revision; its clean-source guard was unchanged. Release-local integrity
  verification passed.
- Main HEAD, branch and index remained unchanged. The main worktree retains
  its existing edits plus this evidence packet.

The isolated canonical ledger working bytes differ from the transactionally
consistent committed snapshot; this documented runtime-evidence drift is
permitted by the unchanged release guard and does not enter the artifact.
A failed initial Windows checkout remains under `dist`; a fresh checkout with
Git long-path support completed the preparation. No reset or deletion occurred.

## Exact next step after operator approval

Use the release-local procedure in `CANDIDATE-DEPLOYMENT.md`: verify/extract
this immutable archive, close intake and inspect in-flight work, make a verified
backup, review activation identity with `prepare-control-plane-activation.py
--check-only`, update the declared release identity, select the verified current
release and restart only `codex-control-plane.service`. Confirm the new package
fingerprint/process health before reopening the approved admission mode.
Preserve the existing protected configuration and external SQLite database.

Then submit owner acceptance for the existing verified standing-patch action.
Do not replay the patch. Actual Ubuntu deployment and owner acceptance remain
unperformed and are owned by the parent controller.
"""
(OUTPUT / "README.md").write_text(readme, encoding="utf-8")
print(json.dumps({"review_archive": str(delivery), "archive_sha256": receipt["review_archive_sha256"]}, sort_keys=True))
