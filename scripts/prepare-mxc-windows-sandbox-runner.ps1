param(
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$SourceRepository = 'https://github.com/microsoft/mxc.git'
$SourceCommit = 'cbe1774364ea2ec846f56ab744e43a416f751420'
$LocalPatchPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'patches\mxc-windows-sandbox-c-drive-share.patch'))
$LocalPatchFile = 'scripts/patches/mxc-windows-sandbox-c-drive-share.patch'
$LocalPatchSha256 = '85a0991dd4473b31574ad6c71d2c489389e6719a3e6ef9116f5f9156a7b7c8df'
$SchemaVersion = '0.10.0-alpha'
$ExpectedBinaries = @(
    'wxc-exec.exe',
    'wxc-windows-sandbox-daemon.exe',
    'wxc-windows-sandbox-guest.exe'
)
$PreviousCandidateBinaries = [ordered]@{
    'wxc-exec.exe' = @{ sha256 = 'a186e44c5f6b00658231e99d16438576d5f6405db95aebbbd3c095be71aa0fa6'; size_bytes = 5947392 }
    'wxc-windows-sandbox-daemon.exe' = @{ sha256 = 'a62711836156af10f1a369feb4ac28049eef05d69765c390625433e195096c1c'; size_bytes = 1538560 }
    'wxc-windows-sandbox-guest.exe' = @{ sha256 = '47d446e833160d1fba89b3f68216612b3e139bcc8f48bf392cdfe4ed6d7212b0'; size_bytes = 1422848 }
}
$ResourcesRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\resources'))
$ToolsRoot = [IO.Path]::GetFullPath((Join-Path $ResourcesRoot 'tools'))
$TargetRoot = [IO.Path]::GetFullPath((Join-Path $ToolsRoot 'mxc-windows-sandbox'))

function Assert-Candidate([string]$Directory) {
    $ProvenancePath = Join-Path $Directory 'mxc-windows-sandbox.provenance.json'
    if (-not (Test-Path -LiteralPath $ProvenancePath -PathType Leaf)) {
        throw 'MXC Windows Sandbox provenance is missing.'
    }
    $Provenance = Get-Content -LiteralPath $ProvenancePath -Raw | ConvertFrom-Json
    if ($Provenance.source_commit -ne $SourceCommit -or $Provenance.schema_version -ne $SchemaVersion -or
        $Provenance.local_patch_file -ne $LocalPatchFile -or
        $Provenance.local_patch_sha256 -ne $LocalPatchSha256 -or
        $Provenance.source_commit_signature -ne 'unsigned' -or
        $Provenance.authenticode -ne 'unsigned-local-source-build' -or
        $Provenance.distribution -ne 'development-candidate-only') {
        throw 'MXC Windows Sandbox provenance does not match the pinned development source.'
    }
    $ExpectedBinaryNames = @($ExpectedBinaries | Sort-Object)
    $ObservedBinaryNames = @($Provenance.binaries.PSObject.Properties.Name | Sort-Object)
    if ((ConvertTo-Json -Compress $ObservedBinaryNames) -ne (ConvertTo-Json -Compress $ExpectedBinaryNames)) {
        throw 'MXC Windows Sandbox provenance has an unexpected binary set.'
    }
    foreach ($Name in $ExpectedBinaries) {
        $Path = Join-Path $Directory $Name
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "MXC Windows Sandbox binary is missing: $Name" }
        $Metadata = Get-Item -LiteralPath $Path
        $Hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        $Receipt = $Provenance.binaries.$Name
        if ($Receipt.sha256 -notmatch '^[a-f0-9]{64}$' -or
            [int64]$Receipt.size_bytes -le 0 -or
            $Hash -ne $Receipt.sha256 -or
            $Metadata.Length -ne [int64]$Receipt.size_bytes) {
            throw "MXC Windows Sandbox binary failed its per-build provenance hash/size check: $Name"
        }
    }
    [pscustomobject]@{
        operation = 'mxc_windows_sandbox_candidate_verification'
        source_commit = $SourceCommit
        local_patch_sha256 = $LocalPatchSha256
        schema_version = $SchemaVersion
        development_candidate_only = $true
        files = $ExpectedBinaries
    } | ConvertTo-Json -Compress
}

function Test-PreviousCandidate([string]$Directory) {
    try {
        $ExpectedNames = @(
            'mxc-windows-sandbox.provenance.json',
            'wxc-exec.exe',
            'wxc-windows-sandbox-daemon.exe',
            'wxc-windows-sandbox-guest.exe'
        ) | Sort-Object
        $ObservedNames = @(Get-ChildItem -LiteralPath $Directory -Force | Select-Object -ExpandProperty Name | Sort-Object)
        if ((ConvertTo-Json -Compress $ObservedNames) -ne (ConvertTo-Json -Compress $ExpectedNames)) { return $false }
        $OldProvenance = Get-Content -LiteralPath (Join-Path $Directory 'mxc-windows-sandbox.provenance.json') -Raw | ConvertFrom-Json
        if ($OldProvenance.source_commit -ne $SourceCommit -or
            $OldProvenance.schema_version -ne $SchemaVersion -or
            $OldProvenance.authenticode -ne 'unsigned-local-source-build' -or
            $OldProvenance.distribution -ne 'development-candidate-only') { return $false }
        foreach ($Name in $PreviousCandidateBinaries.Keys) {
            $Path = Join-Path $Directory $Name
            if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
            $Metadata = Get-Item -LiteralPath $Path
            $Hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($Hash -ne $PreviousCandidateBinaries[$Name].sha256 -or
                $Metadata.Length -ne $PreviousCandidateBinaries[$Name].size_bytes) { return $false }
        }
        return $true
    } catch { return $false }
}

if (Test-Path -LiteralPath $TargetRoot) {
    try {
        Assert-Candidate $TargetRoot | Out-Null
        Assert-Candidate $TargetRoot
        exit 0
    } catch {
        if ($VerifyOnly -or -not (Test-PreviousCandidate $TargetRoot)) {
            throw 'Existing MXC candidate is neither the current C: mapping build nor the exact prior pinned build; refusing to replace it.'
        }
    }
}
if ($VerifyOnly) { throw 'MXC Windows Sandbox development candidate is missing.' }
if (-not (Test-Path -LiteralPath $LocalPatchPath -PathType Leaf)) { throw 'The pinned MXC C-drive mapping patch is missing.' }
$ObservedPatchHash = (Get-FileHash -LiteralPath $LocalPatchPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ObservedPatchHash -ne $LocalPatchSha256) { throw 'The pinned MXC C-drive mapping patch hash does not match.' }

$Rustup = Get-Command rustup.exe -ErrorAction SilentlyContinue
$Git = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $Rustup -or -not $Git) { throw 'The pinned MXC source build requires rustup and Git on PATH.' }
if (-not ((& rustup toolchain list) -match '^1\.93(?:\.|-)')) {
    throw 'Install the upstream-pinned Rust 1.93 toolchain before building this candidate.'
}
$VsWhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $VsWhere -PathType Leaf)) { throw 'Visual Studio Build Tools locator is missing.' }
$VsInstall = (& $VsWhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1).Trim()
if (-not $VsInstall) { throw 'Visual Studio C++ Build Tools for x64 were not found.' }
$VsDevCmd = Join-Path $VsInstall 'Common7\Tools\VsDevCmd.bat'
if (-not (Test-Path -LiteralPath $VsDevCmd -PathType Leaf)) { throw 'VsDevCmd.bat is missing from the selected Build Tools installation.' }

$BuildRoot = Join-Path ([IO.Path]::GetTempPath()) ('codex-mxc-source-' + [guid]::NewGuid().ToString('N'))
$StageRoot = Join-Path $ToolsRoot ('.mxc-wsb-stage-' + [guid]::NewGuid().ToString('N'))
if ((Test-Path -LiteralPath $BuildRoot) -or (Test-Path -LiteralPath $StageRoot)) { throw 'A unique source/build staging directory unexpectedly exists.' }
New-Item -ItemType Directory -Path $ToolsRoot -Force | Out-Null

try {
    & $Git.Source clone --filter=blob:none --no-checkout --depth 1 $SourceRepository $BuildRoot
    if ($LASTEXITCODE -ne 0) { throw 'MXC shallow clone failed.' }
    & $Git.Source -C $BuildRoot fetch --depth 1 origin $SourceCommit
    if ($LASTEXITCODE -ne 0) { throw 'Pinned MXC source commit could not be fetched.' }
    & $Git.Source -C $BuildRoot checkout --detach $SourceCommit
    if ($LASTEXITCODE -ne 0) { throw 'Pinned MXC source checkout failed.' }
    $ObservedCommit = (& $Git.Source -C $BuildRoot rev-parse HEAD).Trim()
    if ($ObservedCommit -ne $SourceCommit) { throw 'MXC source checkout did not match the pinned commit.' }

    & $Git.Source -C $BuildRoot apply --recount --check $LocalPatchPath
    if ($LASTEXITCODE -ne 0) { throw 'Pinned MXC C-drive mapping patch does not apply cleanly.' }
    & $Git.Source -C $BuildRoot apply --recount $LocalPatchPath
    if ($LASTEXITCODE -ne 0) { throw 'Pinned MXC C-drive mapping patch could not be applied.' }
    & $Git.Source -C $BuildRoot diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Patched MXC source has whitespace errors.' }

    $BuildDir = Join-Path $BuildRoot 'src'
    $BuildCommand = "`"$VsDevCmd`" -no_logo -arch=x64 && cd /d `"$BuildDir`" && cargo build --locked --release --target x86_64-pc-windows-msvc -p wxc -p wxc_windows_sandbox_daemon -p wxc_windows_sandbox_guest"
    & cmd.exe /d /s /c $BuildCommand
    if ($LASTEXITCODE -ne 0) { throw 'Pinned MXC Windows Sandbox source build failed.' }

    $OutputDir = Join-Path $BuildDir 'target\x86_64-pc-windows-msvc\release'
    New-Item -ItemType Directory -Path $StageRoot | Out-Null
    $ProvenanceBinaries = [ordered]@{}
    foreach ($Name in $ExpectedBinaries) {
        $Built = Join-Path $OutputDir $Name
        if (-not (Test-Path -LiteralPath $Built -PathType Leaf)) { throw "MXC build output is missing: $Name" }
        $ObservedHash = (Get-FileHash -LiteralPath $Built -Algorithm SHA256).Hash.ToLowerInvariant()
        $ObservedSize = (Get-Item -LiteralPath $Built).Length
        if ($ObservedSize -le 0) { throw "MXC build output is empty: $Name" }
        Copy-Item -LiteralPath $Built -Destination (Join-Path $StageRoot $Name)
        $ProvenanceBinaries[$Name] = [ordered]@{
            sha256 = $ObservedHash
            size_bytes = $ObservedSize
        }
    }
    $Provenance = [ordered]@{
        component = 'Microsoft MXC Windows Sandbox state-aware candidate'
        source_repository = 'https://github.com/microsoft/mxc'
        source_commit = $SourceCommit
        local_patch_file = $LocalPatchFile
        local_patch_sha256 = $LocalPatchSha256
        source_commit_signature = 'unsigned'
        mxc_crate_version = '0.8.0'
        schema_version = $SchemaVersion
        backend = 'windows_sandbox'
        lifecycle = 'state-aware'
        experimental = $true
        build_profile = 'release'
        target = 'x86_64-pc-windows-msvc'
        rustc = (& rustup run 1.93 rustc --version).Trim().Replace('rustc ', '')
        authenticode = 'unsigned-local-source-build'
        distribution = 'development-candidate-only'
        license = 'MIT'
        binaries = $ProvenanceBinaries
    }
    $Json = $Provenance | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText((Join-Path $StageRoot 'mxc-windows-sandbox.provenance.json'), $Json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    Assert-Candidate $StageRoot | Out-Null
    $BackupRoot = $null
    if (Test-Path -LiteralPath $TargetRoot) {
        $BackupRoot = Join-Path ([IO.Path]::GetTempPath()) ('codex-mxc-wsb-unmapped-' + [guid]::NewGuid().ToString('N'))
        if (Test-Path -LiteralPath $BackupRoot) { throw 'Unique previous-candidate backup path unexpectedly exists.' }
        [IO.Directory]::Move($TargetRoot, $BackupRoot)
    }
    try {
        [IO.Directory]::Move($StageRoot, $TargetRoot)
    } catch {
        if ($BackupRoot -and (Test-Path -LiteralPath $BackupRoot) -and -not (Test-Path -LiteralPath $TargetRoot)) {
            [IO.Directory]::Move($BackupRoot, $TargetRoot)
        }
        throw
    }
    if ($BackupRoot) { Write-Output ('previous_unmapped_candidate_preserved=' + $BackupRoot) }
    Assert-Candidate $TargetRoot
} finally {
    $TempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (Test-Path -LiteralPath $BuildRoot) {
        $ResolvedBuildRoot = [IO.Path]::GetFullPath($BuildRoot)
        if (-not $ResolvedBuildRoot.StartsWith($TempRoot, [StringComparison]::OrdinalIgnoreCase) -or
            -not ([IO.Path]::GetFileName($ResolvedBuildRoot).StartsWith('codex-mxc-source-', [StringComparison]::Ordinal))) {
            throw 'Refusing to remove a build directory outside the exact temporary prefix.'
        }
        Remove-Item -LiteralPath $ResolvedBuildRoot -Recurse -Force
    }
    if (Test-Path -LiteralPath $StageRoot) {
        $ResolvedStageRoot = [IO.Path]::GetFullPath($StageRoot)
        if (-not $ResolvedStageRoot.StartsWith($ToolsRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
            -not ([IO.Path]::GetFileName($ResolvedStageRoot).StartsWith('.mxc-wsb-stage-', [StringComparison]::Ordinal))) {
            throw 'Refusing to remove a stage directory outside resources/tools.'
        }
        Remove-Item -LiteralPath $ResolvedStageRoot -Recurse -Force
    }
}
