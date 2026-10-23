# 第三方软件声明

本程序集成并管理 **Coding Tools MCP**。

- Project: Coding Tools MCP
- Author: Coding Tools MCP Contributors
- Source: https://github.com/xyTom/coding-tools-mcp
- License: Apache License 2.0

发行包内 `resources/coding-tools-mcp/LICENSE` 与 `NOTICE` 保留了上游许可和声明。

本程序可能调用用户电脑中已经安装的 Python、Git 与其他开发工具；这些外部工具不随本程序分发，其许可由各自项目提供。

## Microsoft MXC Windows process sandbox

The application bundles the unmodified, Authenticode-signed `wxc-exec.exe`
from Microsoft MXC release `v0.8.0` for Windows structured Control Plane
execution. MXC is a pre-release and is distributed under the MIT License; the
full notice is in [MXC-LICENSE-MIT.txt](resources/tools/MXC-LICENSE-MIT.txt).
The pinned release archive and binary hashes, signer and selected sandbox
policy are recorded in
[mxc-wxc-exec.provenance.json](resources/tools/mxc-wxc-exec.provenance.json).
Recreate or verify the binary with
[`prepare-mxc-windows-runner.ps1`](scripts/prepare-mxc-windows-runner.ps1).
Microsoft's MXC trademarks remain Microsoft property; this application is not
Microsoft-endorsed.

The unpacked Windows dev candidate also contains an **unsigned, experimental**
state-aware Windows Sandbox build from MXC source commit
`cbe1774364ea2ec846f56ab744e43a416f751420` (schema `0.10.0-alpha`) with a
local host-to-guest C-drive share/working-directory adapter in
[`mxc-windows-sandbox-c-drive-share.patch`](scripts/patches/mxc-windows-sandbox-c-drive-share.patch).
Host paths remain the authorization keys; each share is mounted at a
deterministic guest `C:\` path. The patch hash, individual binary hashes and
toolchain provenance are recorded in
[mxc-windows-sandbox.provenance.json](resources/tools/mxc-windows-sandbox/mxc-windows-sandbox.provenance.json).
The build is reproducible with
[`prepare-mxc-windows-sandbox-runner.ps1`](scripts/prepare-mxc-windows-sandbox-runner.ps1).
It is distributed under the same MIT License above; no Microsoft Authenticode
signature or production-security certification is claimed for this local build.

## Chat On Steroids — unified-diff line model (selective port)

The Work Hub structured diff view (`renderer/diff-view.js`) adapts the line
model, bounded-line limit and dual-gutter presentation of
`src/renderer/unified-diff.ts` from Chat On Steroids 2.1.45
(commit `366404c1002038f055d61311f137d9701ff83b96`,
https://github.com/totec448-spec/chat-on-steroids), used under the MIT License:

MIT License — Copyright (c) 2026 Chat On Steroids contributors. Permission is
hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the
Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, subject to the condition that the above copyright notice and
this permission notice be included in all copies or substantial portions of
the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED.

Only the presentation model was ported; the parsing of `git diff` output is
original to this project, no CoS code or dependency (CodeMirror/lezer) is
bundled, and the feature runs natively in this application without the CoS
app. The full upstream license text ships in the research snapshot and in the
upstream repository.

## Bundled display fonts

The application bundles the following unmodified Google Fonts webfont
distribution artifacts. Font software remains under SIL Open Font License 1.1;
the application license does not replace the font licenses.

| Family | Files under `renderer/fonts/` | Copyright / upstream | Full license |
|---|---|---|---|
| JetBrains Mono | `JetBrainsMono-latin.woff2`, `JetBrainsMono-latin-ext.woff2`, `JetBrainsMono-vietnamese.woff2` | Copyright 2020 The JetBrains Mono Project Authors ([upstream](https://github.com/JetBrains/JetBrainsMono)) | [JetBrainsMono-OFL.txt](renderer/fonts/JetBrainsMono-OFL.txt) |
| Plus Jakarta Sans | `PlusJakartaSans-latin.woff2`, `PlusJakartaSans-latin-ext.woff2`, `PlusJakartaSans-vietnamese.woff2` | Copyright 2020 The Plus Jakarta Sans Project Authors ([upstream](https://github.com/tokotype/PlusJakartaSans)) | [PlusJakartaSans-OFL.txt](renderer/fonts/PlusJakartaSans-OFL.txt) |

Exact versioned artifact URLs, local SHA-256 values, verification time, metadata
and license-source receipts are in [renderer/fonts/provenance.json](renderer/fonts/provenance.json).
The [font provenance notes](renderer/fonts/README.md) distinguish this exact-byte
revalidation from the unknown original acquisition date. No font binaries were
modified by this notice/provenance repair.
