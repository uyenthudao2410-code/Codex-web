# Explicit Windows Sandbox setup — 12-10-2026

Repository `E:\DEV\Codex-web`, branch `main`, source HEAD
`7999c4151cb501db86f2e4d0a2275d33fc248324`. Previous local machine repairs and
runtime evidence are preserved. This wave changes source only; root owns the
subsequent r5 package/activation and shared write/exec proof.

## Cause and change

- Folder picker and workspace-registration service did not start a Sandbox.
  The UI registration/complete button entered `continueSetup`, which called
  exec-policy setup after general folder consent. That wrapper's initial
  inspection always ran the real Python Windows Sandbox probe.
- Default exec-policy inspection now reads installed policy, authenticated
  current authority, and any current diagnostic receipt. It never starts a
  Sandbox. Missing/expired receipt reports `not_checked / SANDBOX_PROBE_REQUIRED`.
- Ordinary folder setup verifies file permissions and observes exec permission.
  The separate button **Kiểm tra Sandbox và bật lệnh** obtains consent that
  explicitly states Windows Sandbox will open before the actual probe.
- Actual probe remains mandatory before installing exec. The same selected
  root and validated candidate hashes share a single in-flight probe and the
  successful five-minute receipt; failure releases ownership for an explicit
  retry and cannot grant readiness.
- A standing exec policy with fresh matching server authority remains enabled
  when diagnostic cache expires. UI describes permission separately from a
  running Sandbox or actual Job result.
- Probe creates and closes its own VM. No fabricated session reuse, headless
  claim, window hiding, backend change, or sandbox/security weakening occurred.

Source: `renderer/app.js`, `renderer/index.html`, `electron/main.js`,
`electron/services/controlPlaneEnrollment.js`.
Tests: `tests/folder-permission-editor.test.js`,
`tests/control-plane-exec-sandbox.test.js`, `tests/control-center-manager.test.js`.

## Validation and next action

Focused Node tests: **70 passed, 0 failed**. Coverage includes default folder
registration, inventory refresh and automatic owner-authority continuation
with zero probe launch; explicit consent and one probe; cancellation before
install; status reads after cache expiry; root/candidate hash scoping;
concurrent single-flight; failed explicit retry; advanced probe confirmation;
fresh policy authority after
cache expiry. [Log](focused-tests.txt).

JavaScript syntax checks and scoped `git diff --check` passed.
`observe-status-only.cjs` is a prepared packaged observer with a runner guard
allowing only `inspect-exec-policy` and `inspect-policy-authority`; it has not
yet been run against r5. Root should build and smoke r5, then run that observer
on the actual candidate before its shared MCP write/exec canary.

No runtime activation, service operation, commit, push, release, or deployment
was performed by this wave. Git remains dirty with intended existing changes
and this source/evidence. Windows Sandbox still can appear on an explicitly
requested probe or real command; a truly background backend is outside this
focused repair.
