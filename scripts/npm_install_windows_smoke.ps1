# Windows-native packaging + npm-install smoke for WebCodex.
#
# Exercises the full Windows distribution chain on one Windows machine,
# without Git Bash, WSL, or the npm registry:
#
#   cargo build -> Windows artifact -> canonical npm manifest + local manifest
#     -> npm installer (postinstall) -> temporary npm prefix
#     -> vendor/bin/*.exe -> npm wrapper
#
# Verifies:
#   - the artifact is created and contains exactly the three .exe binaries
#   - the installer verifies the checksum and unpacks the tar.gz
#   - version and build identity are consistent
#   - the npm wrapper finds webcodex.exe
#   - webcodex.exe --version / --help and webcodex-runner.exe --version work
#   - an install failure does not break the previous binary set
#   - staging/temporary files are cleaned up
#
# Never touches the real npm registry (the registry URL is pinned to a
# non-routable address so any accidental network access fails loudly) and
# never publishes anything.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\npm_install_windows_smoke.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\npm_install_windows_smoke.ps1 -BinDir E:\webcodex\target\release
[CmdletBinding()]
param(
    # Directory containing webcodex.exe / webcodex-server.exe / webcodex-runner.exe.
    # Defaults to the debug build, which this script builds first.
    [string]$BinDir,
    [switch]$RequireExactSource,
    [string]$ProvenanceOut
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Version = (Get-Content -LiteralPath (Join-Path $Root "npm\webcodex\package.json") -Raw | ConvertFrom-Json).version
$DesktopVersion = (Get-Content -LiteralPath (Join-Path $Root "package.json") -Raw | ConvertFrom-Json).version
$McpPyproject = Get-Content -LiteralPath (Join-Path $Root "resources\coding-tools-mcp\pyproject.toml") -Raw
$McpVersionMatch = [regex]::Match($McpPyproject, '(?ms)^\[project\]\s*.*?^version\s*=\s*"([^"]+)"')
if (-not $McpVersionMatch.Success) {
    throw "cannot read Coding Tools MCP version from pyproject.toml"
}
$McpVersion = $McpVersionMatch.Groups[1].Value
if ($ProvenanceOut) {
    $ProvenanceOut = [System.IO.Path]::GetFullPath($ProvenanceOut)
}

$InitialHead = @(& git -C $Root rev-parse HEAD)[0].Trim().ToLowerInvariant()
$InitialTree = @(& git -C $Root rev-parse "HEAD^{tree}")[0].Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $InitialHead -notmatch '^[a-f0-9]{40}$' -or $InitialTree -notmatch '^[a-f0-9]{40}$') {
    throw "cannot resolve exact Git commit/tree identity for Windows smoke"
}
if ($RequireExactSource) {
    $initialStatus = @(& git -C $Root status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $initialStatus.Count -ne 0) {
        # Name the dirt before failing: a bare "clean worktree required"
        # error leaves the next investigation guessing which entry broke it
        # (see the step-21 gate failure on run 40089338352, whose log named
        # no file). Logging does not weaken the check — it still throws.
        foreach ($entry in $initialStatus) { Write-Host "exact-source dirty entry: $entry" }
        throw "-RequireExactSource requires a clean Git worktree before building the Windows candidate"
    }
}

# ---------------------------------------------------------------------------
# 0. Build the three Windows binaries unless an explicit BIN_DIR was given.
# ---------------------------------------------------------------------------
if (-not $BinDir) {
    $BinDir = Join-Path $Root "target\debug"
    Write-Host "building Windows binaries (debug)..."
    # Pin the build timestamp so every binary built in this invocation reports
    # the identical `built_at` in its revision identity (webcodex-core's
    # build.rs reads WEBCODEX_BUILT_AT when set). This mirrors what a release
    # build on the release host must do.
    #
    # The three binaries live in three packages: webcodex.exe is the
    # webcodex-cli package's bin, webcodex-server.exe is the root webcodex
    # package's bin, and webcodex-runner.exe is its own package.
    $env:WEBCODEX_BUILT_AT = [string][long](Get-Date -UFormat %s)
    try {
        & cargo build --locked -p webcodex -p webcodex-cli -p webcodex-runner
    } finally {
        Remove-Item Env:WEBCODEX_BUILT_AT -ErrorAction SilentlyContinue
    }
    if ($LASTEXITCODE -ne 0) {
        throw "cargo build failed with exit code $LASTEXITCODE"
    }
}
$BinDir = [System.IO.Path]::GetFullPath($BinDir)

# ---------------------------------------------------------------------------
# Isolate everything under one smoke root; the registry is pinned to a
# non-routable address so the smoke provably never contacts npmjs.org.
# ---------------------------------------------------------------------------
$TempRoot = Join-Path $env:TEMP ("webcodex-smoke-" + [guid]::NewGuid().ToString("N"))
$ArtifactOut = Join-Path $TempRoot "artifact-out"
$Prefix = Join-Path $TempRoot "install-prefix"
$ManifestPath = Join-Path $TempRoot "local-manifest.json"
$PackageStage = Join-Path $TempRoot "npm-package"
$PackageSourceArchive = Join-Path $TempRoot "npm-package-source.zip"
$NativeProvenancePath = Join-Path $TempRoot "native-provenance.json"
New-Item -ItemType Directory -Force -Path $ArtifactOut | Out-Null
$env:npm_config_registry = "http://127.0.0.1:9"
try {
    # -----------------------------------------------------------------------
    # 1. Windows release artifact.
    # -----------------------------------------------------------------------
    Write-Host "creating Windows release artifact..."
    $artifactOutput = & (Join-Path $PSScriptRoot "package_release_artifact.ps1") `
        -BinDir $BinDir -OutDir $ArtifactOut -AllowDevelopmentBuild -ProvenanceOut $NativeProvenancePath
    if ($LASTEXITCODE -ne 0) {
        throw "package_release_artifact.ps1 failed with exit code $LASTEXITCODE"
    }
    $shaLine = @($artifactOutput)[0]
    $Archive = @($artifactOutput)[1]
    if (-not $Archive -or -not (Test-Path -LiteralPath $Archive)) {
        throw "packaging did not report a produced archive: $artifactOutput"
    }
    $sha256 = ($shaLine -split "\s+", 2)[0]
    if ($sha256 -notmatch '^[a-f0-9]{64}$') {
        throw "packaging did not report a SHA-256: $shaLine"
    }
    $ExpectedArchiveName = "webcodex-v$Version-win32-x64.tar.gz"
    if ((Split-Path -Leaf $Archive) -ne $ExpectedArchiveName) {
        throw "unexpected artifact name: $(Split-Path -Leaf $Archive) (expected $ExpectedArchiveName)"
    }
    if (-not (Test-Path -LiteralPath $NativeProvenancePath -PathType Leaf)) {
        throw "native packager did not produce provenance"
    }
    $NativeProvenance = Get-Content -LiteralPath $NativeProvenancePath -Raw | ConvertFrom-Json
    if ($NativeProvenance.archive.sha256 -ne $sha256) {
        throw "native provenance archive digest does not match the packaged artifact"
    }
    if ($NativeProvenance.source.git_sha -ne $InitialHead -or $NativeProvenance.source.git_tree -ne $InitialTree) {
        throw "native artifact source identity drifted during the Windows smoke"
    }
    if ($RequireExactSource -and -not $NativeProvenance.source.exact_source) {
        throw "native artifact does not prove exact clean source identity"
    }

    # -----------------------------------------------------------------------
    # 2. The archive must contain exactly the three .exe binaries. The
    #    Windows System32 tar is used explicitly (Git Bash tar is not
    #    supported and mangles Windows paths).
    # -----------------------------------------------------------------------
    $systemTar = Join-Path $env:SystemRoot "System32\tar.exe"
    if (-not (Test-Path -LiteralPath $systemTar -PathType Leaf)) {
        throw "tar.exe was not found at $systemTar; required to inspect the artifact"
    }
    $entries = @(& $systemTar -tf $Archive)
    $expectedEntries = @("webcodex.exe", "webcodex-server.exe", "webcodex-runner.exe")
    $diff = @($entries | Where-Object { $_ -notin $expectedEntries }) + `
        @($expectedEntries | Where-Object { $_ -notin $entries })
    if ($diff.Count -ne 0) {
        throw "artifact does not contain exactly the three binaries; entries: $($entries -join ', ')"
    }

    # -----------------------------------------------------------------------
    # 3. Produce two manifests from the same real artifact digest. The npm
    #    tarball must contain a publish-ready canonical GitHub release URL,
    #    while the installer smoke uses a local file:// URL so it remains
    #    fully offline. Keeping these distinct preserves the strict prepack
    #    release contract instead of bypassing it for CI.
    # -----------------------------------------------------------------------
    $localManifest = [ordered]@{
        version = $Version
        binaries = @("webcodex", "webcodex-server", "webcodex-runner")
        artifacts = [ordered]@{
            "win32-x64" = [ordered]@{
                url = [System.Uri]::new($Archive).AbsoluteUri
                sha256 = $sha256
            }
        }
    }
    $releaseManifest = [ordered]@{
        version = $Version
        binaries = @("webcodex", "webcodex-server", "webcodex-runner")
        artifacts = [ordered]@{
            "win32-x64" = [ordered]@{
                url = "https://github.com/yyjeqhc/webcodex/releases/download/v$Version/$ExpectedArchiveName"
                sha256 = $sha256
            }
        }
    }
    # BOM-less UTF-8: install.js parses the manifest with JSON.parse, which
    # rejects a leading byte-order mark.
    $Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText(
        $ManifestPath,
        ($localManifest | ConvertTo-Json -Depth 6),
        $Utf8NoBom
    )

    # -----------------------------------------------------------------------
    # 4. Stage only tracked npm package sources from this exact commit, add
    #    the canonical manifest, then pack from the staging tree. This mirrors
    #    release staging and cannot accidentally include local credentials,
    #    node_modules, vendor binaries, or other untracked workstation files.
    # -----------------------------------------------------------------------
    & git -C $Root archive --format=zip --output=$PackageSourceArchive "HEAD:npm/webcodex"
    if ($LASTEXITCODE -ne 0) {
        throw "git archive failed with exit code $LASTEXITCODE"
    }
    Expand-Archive -LiteralPath $PackageSourceArchive -DestinationPath $PackageStage
    $PackageSourceArchiveHash = (Get-FileHash -LiteralPath $PackageSourceArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    $PackageSourceArchiveInfo = Get-Item -LiteralPath $PackageSourceArchive
    $PackageManifestPath = Join-Path $PackageStage "manifest.json"
    [System.IO.File]::WriteAllText(
        $PackageManifestPath,
        ($releaseManifest | ConvertTo-Json -Depth 6),
        $Utf8NoBom
    )
    & node (Join-Path $PackageStage "test\release-manifest-check.js") $PackageManifestPath
    if ($LASTEXITCODE -ne 0) {
        throw "release manifest validation failed with exit code $LASTEXITCODE"
    }

    Push-Location $PackageStage
    try {
        & npm pack --pack-destination $TempRoot --silent
        if ($LASTEXITCODE -ne 0) {
            throw "npm pack failed with exit code $LASTEXITCODE"
        }
    } finally {
        Pop-Location
    }
    $Tarball = Get-ChildItem -LiteralPath $TempRoot -Filter "yyjeqhc-webcodex-*.tgz" |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $Tarball) {
        throw "npm pack produced no tarball"
    }
    $TarballHashBefore = (Get-FileHash -LiteralPath $Tarball -Algorithm SHA256).Hash.ToLowerInvariant()
    $TarballInfo = Get-Item -LiteralPath $Tarball

    Write-Host "installing from local artifact via npm installer..."
    $env:WEBCODEX_MANIFEST = $ManifestPath
    try {
        & npm install --prefix $Prefix --no-audit --no-fund $Tarball
        if ($LASTEXITCODE -ne 0) {
            throw "npm install failed with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item Env:WEBCODEX_MANIFEST -ErrorAction SilentlyContinue
    }

    # -----------------------------------------------------------------------
    # 5. vendor/bin/*.exe, version/identity, wrapper, --help.
    # -----------------------------------------------------------------------
    $Installed = Join-Path $Prefix "node_modules\@yyjeqhc\webcodex"
    $VendorBin = Join-Path $Installed "vendor\bin"
    foreach ($name in @("webcodex", "webcodex-server", "webcodex-runner")) {
        if (-not (Test-Path -LiteralPath (Join-Path $VendorBin "$name.exe") -PathType Leaf)) {
            throw "installed package is missing $name.exe in vendor\bin"
        }
    }

    $cli = Join-Path $VendorBin "webcodex.exe"
    $versionOut = & $cli --version
    if ($LASTEXITCODE -ne 0 -or -not $versionOut -or -not $versionOut.StartsWith("webcodex $Version ")) {
        throw "webcodex.exe --version produced unexpected output: $versionOut"
    }
    $helpOut = & $cli --help
    if ($LASTEXITCODE -ne 0 -or -not $helpOut) {
        throw "webcodex.exe --help failed"
    }
    $runnerOut = & (Join-Path $VendorBin "webcodex-runner.exe") --version
    if ($LASTEXITCODE -ne 0 -or -not $runnerOut -or -not $runnerOut.StartsWith("webcodex-runner $Version ")) {
        throw "webcodex-runner.exe --version produced unexpected output: $runnerOut"
    }

    # The npm wrapper (vendor/bin resolution + spawn) through the .bin shim.
    $wrapperShim = Join-Path $Prefix "node_modules\.bin\webcodex.cmd"
    if (-not (Test-Path -LiteralPath $wrapperShim)) {
        throw "npm did not create the .bin\webcodex wrapper shim"
    }
    $wrapperOut = & $wrapperShim --version
    if ($LASTEXITCODE -ne 0 -or -not $wrapperOut -or -not $wrapperOut.StartsWith("webcodex $Version ")) {
        throw "npm wrapper --version produced unexpected output: $wrapperOut"
    }

    # -----------------------------------------------------------------------
    # 6. An install failure must not break the previous binary set.
    # -----------------------------------------------------------------------
    $badManifest = [ordered]@{
        version = $Version
        binaries = @("webcodex", "webcodex-server", "webcodex-runner")
        artifacts = [ordered]@{
            "win32-x64" = [ordered]@{
                url = [System.Uri]::new($Archive).AbsoluteUri
                sha256 = "0" * 64
            }
        }
    }
    $BadManifestPath = Join-Path $TempRoot "bad-manifest.json"
    [System.IO.File]::WriteAllText(
        $BadManifestPath,
        ($badManifest | ConvertTo-Json -Depth 6),
        $Utf8NoBom
    )
    $env:WEBCODEX_MANIFEST = $BadManifestPath
    try {
        & node (Join-Path $Installed "install.js")
        if ($LASTEXITCODE -eq 0) {
            throw "install.js must fail against a manifest with a wrong checksum"
        }
    } finally {
        Remove-Item Env:WEBCODEX_MANIFEST -ErrorAction SilentlyContinue
    }
    $afterFailure = & $cli --version
    if ($LASTEXITCODE -ne 0 -or $afterFailure -ne $versionOut) {
        throw "the previous binary set was damaged by the failed install"
    }

    # -----------------------------------------------------------------------
    # 7. Staging/temporary cleanup.
    # -----------------------------------------------------------------------
    $leftovers = Get-ChildItem -LiteralPath $env:TEMP -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "webcodex-artifact-*" -or $_.Name -like "webcodex-manifest-*" -or $_.Name -like "webcodex-npm-test-*" } |
        Select-Object -ExpandProperty FullName
    $stagingLeftovers = Get-ChildItem -LiteralPath (Split-Path $Installed) -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like ".bin-staging-*" -or $_.Name -like ".bin-backup-*" } |
        Select-Object -ExpandProperty FullName
    if ($leftovers -or $stagingLeftovers) {
        throw "installer left staging/temp files behind: $($leftovers + $stagingLeftovers -join '; ')"
    }

    $ArtifactHashAfter = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    $TarballHashAfter = (Get-FileHash -LiteralPath $Tarball -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ArtifactHashAfter -ne $sha256) {
        throw "Windows artifact bytes changed during the npm install smoke"
    }
    if ($TarballHashAfter -ne $TarballHashBefore) {
        throw "npm tarball bytes changed during the npm install smoke"
    }
    $FinalHead = @(& git -C $Root rev-parse HEAD)[0].Trim().ToLowerInvariant()
    $FinalTree = @(& git -C $Root rev-parse "HEAD^{tree}")[0].Trim().ToLowerInvariant()
    if ($FinalHead -ne $InitialHead -or $FinalTree -ne $InitialTree) {
        throw "Git source identity changed during the Windows smoke"
    }
    if ($RequireExactSource) {
        $finalStatus = @(& git -C $Root status --porcelain --untracked-files=all)
        if ($LASTEXITCODE -ne 0 -or $finalStatus.Count -ne 0) {
            throw "exact-source Windows smoke ended with a dirty Git worktree"
        }
    }

    if ($ProvenanceOut) {
        $provenance = [ordered]@{
            schema_version = 1
            kind = "tools-codex-web.windows_release_candidate_provenance"
            generated_at_utc = [DateTime]::UtcNow.ToString("o")
            source = [ordered]@{
                git_sha = $InitialHead
                git_tree = $InitialTree
                worktree_clean = [bool]$NativeProvenance.source.worktree_clean
                exact_source = [bool]$NativeProvenance.source.exact_source
            }
            versions = [ordered]@{
                desktop_app = $DesktopVersion
                coding_tools_mcp = $McpVersion
                webcodex_npm = $Version
            }
            native = [ordered]@{
                platform = "win32-x64"
                build_identity = [string]$NativeProvenance.build_identity
                archive = $NativeProvenance.archive
                binaries = $NativeProvenance.binaries
            }
            package = [ordered]@{
                source_archive = [ordered]@{
                    name = (Split-Path -Leaf $PackageSourceArchive)
                    size_bytes = [long]$PackageSourceArchiveInfo.Length
                    sha256 = $PackageSourceArchiveHash
                }
                npm_tarball = [ordered]@{
                    name = (Split-Path -Leaf $Tarball)
                    size_bytes = [long]$TarballInfo.Length
                    sha256 = $TarballHashBefore
                }
            }
            release = [ordered]@{
                native_packaging_mode = [string]$NativeProvenance.release.mode
                publishable = [bool]$NativeProvenance.release.publishable
            }
            proof = [ordered]@{
                name = "windows_artifact_to_npm_install_smoke"
                status = "passed"
                artifact_rehash_sha256 = $ArtifactHashAfter
                npm_tarball_rehash_sha256 = $TarballHashAfter
            }
        }
        $provenanceParent = Split-Path -Parent $ProvenanceOut
        if ($provenanceParent) {
            New-Item -ItemType Directory -Force -Path $provenanceParent | Out-Null
        }
        [System.IO.File]::WriteAllText($ProvenanceOut, ($provenance | ConvertTo-Json -Depth 10), $Utf8NoBom)
        $finalizeArgs = @((Join-Path $PSScriptRoot "windows-release-provenance.js"), "finalize", $ProvenanceOut)
        if ($RequireExactSource) {
            $finalizeArgs += "--require-exact-source"
        }
        & node @finalizeArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Windows provenance finalization failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "Windows artifact -> npm install smoke passed"
    Write-Host "  artifact:  $Archive"
    Write-Host "  sha256:    $sha256"
    Write-Host "  installed: $VendorBin"
    if ($ProvenanceOut) {
        Write-Host "  provenance: $ProvenanceOut"
    }
} finally {
    Remove-Item Env:npm_config_registry -ErrorAction SilentlyContinue
    Remove-Item Env:WEBCODEX_MANIFEST -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}