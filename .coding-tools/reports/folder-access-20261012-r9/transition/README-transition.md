# r9 guarded local transition

These scripts are additive copies of the reviewed r8 scripts. Preparing and
parsing them did not install a supervisor, launch an app or change shortcuts.

## Bound identities

- Prior candidate: `machine-exec-lifecycle-1012-r8/win-unpacked`.
- Prior Host: PID `11364`, instance `83634bc8f513cc453f74f94751efb819`,
  installation `6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228`,
  Windows process start token `134362637018564480`.
- New candidate: `machine-folder-access-1012-r9/win-unpacked`.
- EXE SHA-256: `4d7bb476ae8ebc8e15af8ebdb8081d0cb56c524443bbfe3f36cf07b66a14a268`.
- app.asar SHA-256: `445b0e4e24d3f7cd39e487d257545025d63ca7ca02e8a425f904bc1787f489d0`.
- Adapter SHA-256: `3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9`.

The actual r9 proof and candidate hashes were verified during preparation.
The current Desktop and Start Menu shortcut hashes match the r8 completion
receipt. Both PowerShell scripts parse with zero errors.

## Root-controlled sequence

1. Use the supported Stop observation and exact retirement receipt. The
   original Stop failure remains separate from later confirmed stopped state.
2. Run `launch-r9.ps1 -Operation InstallSupervisor` with `-Apply` and the absolute
   retirement receipt path inside this transition directory. It requires
   exact prior ownership, a quiescent census, an absent prior Host, the stopped
   prior supervisor installation and a receipt at most 900 seconds old.
3. Run `launch-r9.ps1 -Operation LaunchUi` with `-Apply`, the same retirement
   receipt and the fresh install receipt. This verifies the installed manifest
   before launching the new exact candidate. Launching does not imply READY.
4. Perform the supported full-clean refresh and produce a fresh r9 observer
   receipt with a new READY/OPEN activation epoch.
5. Run `update-coding-tools-shortcuts-r9.ps1 -Apply` with the exact r9 EXE,
   new epoch and its observer receipt. The observer must be at most 120 seconds
   old. Both old shortcut bytes are rechecked and backed up before each Save;
   unrelated shortcut properties remain preserved.

The scripts access descriptor credentials only through existing services or
local JSON parsing. They never print token fields. Keep the r9 candidate
directory in place while its supervisor and shortcuts use it.

See `launch-and-shortcuts-preparation.json` and
`transition-scripts-validation.json` for source hashes and preparation evidence.
