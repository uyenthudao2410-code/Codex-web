# Ubuntu Console delta prepared for review

Captured on 11 October 2026 at 16:57:19 +07. Repository HEAD observed:
`2c554f59cb7b8ffc86ce5e0e28076c792777642f`. This directory is local evidence,
not a new release or a record that the server has been updated.

## Exact scope and artifacts

The candidate delta replaces **only**
`control-plane/control_plane/web_ui.py` from the previously deployed
`beaa9d5ade4926ef231e3ec9d0a517fe93830e90` archive. Other dirty repository
files are not included in this review delta.

- `receipt.json`: archive, base-file, current-file and patch SHA-256 values,
  target expectations, and explicit deployment/authority-operation flags.
- `web_ui.base-073bde8624c5d6ff76ddfae8633acb7c1c4118b05aa458b4be1b21b3ae8181aa.py`:
  untouched base bytes read directly from the one regular archive member.
- `web_ui.current-03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b.py`:
  frozen current bytes; later source edits cannot change this snapshot.
- `web_ui.review-lf.patch`: compact textual review; CRLF in the Windows
  candidate is normalized to LF for this patch only.
- `web_ui.exact.patch`: byte-exact patch preserving the candidate's CRLF.
  Consequently its whole-file newline delta is larger than the review patch.
- `prepare-review.py`: local-only reproducibility helper. It inspects all
  archive paths and member types, checks the trusted archive digest and base
  manifest entry, reads the selected member without extracting archive paths,
  and checks/replays both patches in a temporary directory. Existing frozen
  artifacts are never overwritten with different contents.

Both patches were replayed successfully in a temporary directory. Exact
replay produced current-file SHA-256
`03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b`.
The LF review replay produced
`437e9f9910f615ebfe422b2a610eec90d15916be8b80ead7d2c78bf00eef68d3`.
Verification sets `git -c core.autocrlf=false` so host configuration cannot
silently alter the result.

## Behavior being reviewed

The Console exposes a single **Cấp quyền cho thư mục** form. It resolves the
registered machine/workspace/generation, confirms the capability inventory and
bounded duration, reuses one current binding or creates it, and then creates
one context through the existing owner-session/CSRF endpoints.

Unknown enrollment remains a separate owner decision. Ambiguous bindings,
retired generation, revoked node and live/action contexts block this flow.
Existing manual forms remain under **Nâng cao**. Partial failures preserve the
selection and show the completed/uncertain boundary; observation refreshes do
not replay or undo mutations. The delta does not add any server endpoint,
change authentication/dispatch validation, approve enrollment automatically,
create service grants or pilot decisions, reopen admission, or install a
Windows policy. Simultaneous submissions from independent Console tabs still
require reconciliation because the existing binding/context endpoints are
separate non-idempotent calls.

## Destination for a later approved rollout

- SSH target: `svhome@100.116.112.22`.
- Named service: **user** `codex-control-plane.service`.
- Prior release expectation to reverify:
  `/home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-beaa9d5ade4926ef231e3ec9d0a517fe93830e90`.
- Prior package fingerprint recorded by that archive:
  `sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835`.

The destination and service are documented for review; no SSH connection,
transfer, service operation, runtime activation or authority mutation occurred
in this preparation.

Before rollout, approval must name this destination and the prepared delta.
Then reverify the live baseline and job/authority state, preserve the prior
release, and build/verify a **new** immutable package with a genuine release
identity and regenerated manifest. Do not replace a file inside the published
`beaa9d5a` release or keep its old package fingerprint after changing source.
Only after that package verifies should the approved service switch/restart
and fresh health/UI acceptance checks occur. This directory does not assign a
new Git revision, create deployment state, or claim full-package validation.
