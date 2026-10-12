# Unified setup static visual QA — 2026-10-11

## Scope and evidence

Rendered copied source in an isolated hidden Electron window with `preview=1` and the renderer's built-in fake API. Synthetic data: approved device, one registered Tools-Codex-web workspace, no binding, file policies unavailable, continuation waiting for owner approval. HTTP(S) requests were blocked. No shared profile, preload, Recovery Host, server, activation or authority was used.

This is static UI evidence only. It does not prove server integration, policy installation, execution, acceptance or a live runtime.

`preview-inputs-02.json` records capture time and SHA-256 of the copied renderer source. `preview-source-02/` preserves the exact rendered files. `layout-result-02.json` records geometry, theme states and console messages. `system-02-*` contains top, folder and execution captures at 1360, 1100 and 760 pixels for light and dark themes (18 captures).

## Completed checks

- All six viewport/theme combinations had zero controls outside the content viewport and no horizontal overflow.
- Connection, folder and execution sections remained visible on the same setup page.
- Folder controls, permission presets and pending owner approval remained operable and readable.
- The execution checklist remained explicitly unverified; read/small/exec were not marked successful based on capabilities.
- Legacy settings remained collapsed.
- Light/dark captures at the observed initial light document state were readable.
- `system-02-1360-light-top.png`, `system-02-1100-dark-setupFolderSection.png`, `system-02-760-light-top.png`, and `system-02-760-dark-setupExecutionSection.png` were inspected visually with `view_image`.

## Issues reported to root for repair

1. Theme switching changes body but leaves documentElement at its initial theme. The earlier dark-initial preview (`01`) then switched to light and showed white branding/header text over a light background because dashboard selectors also match `html[data-theme="dark"]`. Update both theme datasets and the theme test fixture.
2. The setup summary says “Hãy đăng ký workspace local trước” when a workspace is already registered and only owner binding is missing. Use the observed workspace state and pending owner step instead.
3. At 760 pixels, the four stacked progress items and three stacked navigation buttons consume nearly the entire first viewport. Use a compact two-column progress grid and three-column section navigation or remove duplicate progress emphasis while keeping the controls and IDs.
4. The third navigation button is highlighted whenever page is system because it also has `data-nav="system"`. Active state should reflect its section anchor, not only the page alias.
5. Folder and summary instructions still mention going away and returning to enable policy when continuation is already waiting for approval. Keep the waiting state and automatic continuation visible in the same page.

## Existing console diagnostics

The static source emits CSP warnings for an external font stylesheet import and dashboard style mutations. The helper preserves these warnings and does not relax CSP. Local bundled fonts are available. The first run `01` omitted the explicit preview opt-in and correctly exercised the missing-preload fail-closed path; it was superseded by the valid static `02` run for layout conclusions.

## State and next action

No renderer or runtime edits were made in this QA wave. Git remained dirty main; no commit/push/release/deployment/service operation occurred. The isolated preview exited successfully. Root owns source repairs and final focused tests. Rerender copied source once those concrete issues are repaired.

## Final repaired-source acceptance — stamp 08

Root repaired theme synchronization, the registered-workspace owner guidance, folder continuation text, compact 760-pixel progress/navigation, setup primary continuation action and anchor active state. Final artifacts are `preview-inputs-08.json`, `preview-source-08/`, `layout-result-08.json`, `preview-08.stdout.log`, and 22 `system-08-*` captures. Earlier artifacts remain historical QA evidence.

- All six width/theme combinations remain free of horizontal overflow and out-of-viewport controls.
- Both html and body theme values match in every final capture.
- At 760 pixels, the first viewport now shows the server input, with progress in two columns and section navigation in three columns.
- The registered folder summary directs the user to continue and wait for owner approval. The primary action is “Kiểm tra & tiếp tục” while the synthetic continuation waits.
- The third section is no longer falsely active at the top of the system page.
- Synthetic sandbox-unavailable observations leave read/small policy checks verified and exec pending, with a clear message about enabling Windows Sandbox or rebooting.
- Synthetic exec-ready observations show matching policy and sandbox and explicitly refer command results to Tasks. They do not claim a test was run or passed.
- `system-08-760-light-top.png`, `system-08-1360-light-sandbox-unavailable.png`, and `system-08-1360-dark-exec-ready.png` were inspected with `view_image`; controls are readable and usable.

The intermediate hidden-window captures initially showed secondary button colors midway through a theme transition. Two compositor frames after finishing animations corrected that artifact in stamps 07 and 08. No source change was needed for that capture timing issue. Stamp 03 also stopped during its second synthetic scenario due to a helper const redeclaration; an IIFE fixed the helper, and all final scenarios complete with exit 0.

Existing CSP diagnostics are still recorded, without relaxing CSP. No unresolved layout blocker was found for the changed setup surface. No further optional rerenders are needed. Root owns packaged/live acceptance; static observations remain synthetic.
