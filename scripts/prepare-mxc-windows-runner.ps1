param(
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$ArchiveUrl = "https://github.com/microsoft/mxc/releases/download/v0.8.0/mxc-release-binaries.zip"
$ArchiveSha256 = "5c3a27073ba18eddf97efb4caad0f8b201c40a18d17b70f3a1e3847fb6232e3c"
$BinarySha256 = "6049c64723af1173c3739dc6cd6b2f33f6c021bb2832c4216233cba7f71aee9a"
$ExpectedSigner = "CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US"
$Target = Join-Path $PSScriptRoot "..\resources\tools\wxc-exec.exe"
$Target = [IO.Path]::GetFullPath($Target)

function Assert-SignedBinary([string]$Path) {
    $Hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Hash -ne $BinarySha256) { throw "MXC Windows executor SHA-256 mismatch." }
    $Signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($Signature.Status.ToString() -ne "Valid" -or $Signature.SignerCertificate.Subject -ne $ExpectedSigner) {
        throw "MXC Windows executor Authenticode signature is not the pinned Microsoft signer."
    }
    [pscustomobject]@{
        operation = "mxc_windows_executor_verification"
        sha256 = $Hash
        authenticode = "valid"
        signer = $ExpectedSigner
        path = $Path
    } | ConvertTo-Json -Compress
}

if (Test-Path -LiteralPath $Target) {
    Assert-SignedBinary $Target
    exit 0
}
if ($VerifyOnly) { throw "Bundled MXC Windows executor is missing." }

$TempRoot = Join-Path ([IO.Path]::GetTempPath()) ("codex-mxc-fetch-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempRoot | Out-Null
try {
    $Archive = Join-Path $TempRoot "mxc-release-binaries.zip"
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $Archive
    $ObservedArchiveHash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ObservedArchiveHash -ne $ArchiveSha256) { throw "MXC release archive SHA-256 mismatch." }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        $Entry = $Zip.GetEntry("x64/wxc-exec.exe")
        if ($null -eq $Entry) { throw "Pinned MXC release is missing x64/wxc-exec.exe." }
        $Extracted = Join-Path $TempRoot "wxc-exec.exe"
        [IO.Compression.ZipFileExtensions]::ExtractToFile($Entry, $Extracted, $false)
    } finally {
        $Zip.Dispose()
    }

    Assert-SignedBinary $Extracted
    if (Test-Path -LiteralPath $Target) { throw "Refusing to overwrite the existing bundled executor." }
    Move-Item -LiteralPath $Extracted -Destination $Target
    Assert-SignedBinary $Target
} finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}
