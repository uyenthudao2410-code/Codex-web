[CmdletBinding()]
param(
    [string]$CandidatePath,
    [string]$ParityProofPath,
    [string]$SmokeProofPath,
    [string]$ReadyReceiptPath,
    [string]$ExpectedEpoch,
    [string]$IntentPath,
    [switch]$Apply
)

# Additive r3 -> r4 shortcut handoff.  The default path only prepares a
# one-shot intent and writes repository evidence.  Production shortcuts are
# changed only with -Apply after every guard is rechecked immediately before
# the first Save call.
$ErrorActionPreference = 'Stop'
$TransitionRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $TransitionRoot '..\..\..\..'))
$ExpectedCandidate = [IO.Path]::GetFullPath((Join-Path $RepoRoot 'dist\windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4\win-unpacked'))
$R3EvidencePath = [IO.Path]::GetFullPath((Join-Path $RepoRoot '.coding-tools\reports\native-first-20261012\parallel-r3-transition\shortcuts-r3.json'))
$BeforeReceiptPath = Join-Path $TransitionRoot 'shortcut-update-before-r4.json'
$AfterReceiptPath = Join-Path $TransitionRoot 'shortcut-update-after-r4.json'

if (-not $CandidatePath) { $CandidatePath = Join-Path $ExpectedCandidate 'Coding Tools MCP.exe' }
if (-not $ParityProofPath) { $ParityProofPath = Join-Path $RepoRoot '.coding-tools\reports\native-first-20261012\parallel-r4-candidate-parity.json' }
if (-not $SmokeProofPath) { $SmokeProofPath = Join-Path $RepoRoot '.coding-tools\reports\native-first-20261012\parallel-r4-packaged-smoke.json' }
if (-not $ReadyReceiptPath) { $ReadyReceiptPath = Join-Path $TransitionRoot 'status-1791815928643-e7d3c41b.json' }
if (-not $ExpectedEpoch) { $ExpectedEpoch = 'activation-mv5cvpnu-2ddc4f6edfe0487ec46a1594cb87218d' }
if (-not $IntentPath) { $IntentPath = Join-Path $TransitionRoot 'shortcut-update-intent-r4.json' }

function FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path)
}

function SamePath([string]$Left, [string]$Right) {
    return [string]::Equals((FullPath $Left), (FullPath $Right), [StringComparison]::OrdinalIgnoreCase)
}

function Require([bool]$Condition, [string]$Code) {
    if (-not $Condition) { throw $Code }
}

function Read-BoundedJson([string]$Path) {
    $Resolved = FullPath $Path
    Require ([IO.Path]::IsPathFullyQualified($Resolved)) 'ABSOLUTE_RECEIPT_REQUIRED'
    Require (Test-Path -LiteralPath $Resolved -PathType Leaf) 'RECEIPT_NOT_FOUND'
    $Info = Get-Item -LiteralPath $Resolved
    Require ($Info.Length -le 4MB) 'RECEIPT_TOO_LARGE'
    return (Get-Content -LiteralPath $Resolved -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Sha256([string]$Path) {
    Require (Test-Path -LiteralPath $Path -PathType Leaf) 'FILE_NOT_FOUND_FOR_HASH'
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-Utf8Json([string]$Path, $Value) {
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((FullPath $Path), ((ConvertTo-Json -InputObject $Value -Depth 12) + [Environment]::NewLine), $Encoding)
}

function Get-ShortcutObservation([string]$Path, $Shell, $ShellApplication) {
    $Resolved = FullPath $Path
    Require (Test-Path -LiteralPath $Resolved -PathType Leaf) 'SHORTCUT_NOT_FOUND'
    $Shortcut = $Shell.CreateShortcut($Resolved)
    $AppUserModelId = $null
    try {
        $Folder = $ShellApplication.NameSpace([IO.Path]::GetDirectoryName($Resolved))
        if ($null -ne $Folder) {
            $Item = $Folder.ParseName([IO.Path]::GetFileName($Resolved))
            if ($null -ne $Item) { $AppUserModelId = $Item.ExtendedProperty('System.AppUserModel.ID') }
        }
    } catch { $AppUserModelId = $null }
    return [ordered]@{
        path = $Resolved
        sha256 = Sha256 $Resolved
        target = $Shortcut.TargetPath
        working_directory = $Shortcut.WorkingDirectory
        arguments = $Shortcut.Arguments
        description = $Shortcut.Description
        icon_location = $Shortcut.IconLocation
        window_style = $Shortcut.WindowStyle
        hotkey = $Shortcut.Hotkey
        app_user_model_id = $AppUserModelId
        target_exists = Test-Path -LiteralPath $Shortcut.TargetPath -PathType Leaf
    }
}

function Compare-PreservedShortcutProperties($Before, $After) {
    foreach ($Property in @('arguments', 'description', 'icon_location', 'window_style', 'hotkey', 'app_user_model_id')) {
        Require ($After[$Property] -eq $Before[$Property]) ("SHORTCUT_PROPERTY_CHANGED:$Property")
    }
}

function Validate-PackageAndProofs {
    $Candidate = FullPath $CandidatePath
    Require (SamePath $Candidate (Join-Path $ExpectedCandidate 'Coding Tools MCP.exe')) 'EXACT_R4_EXECUTABLE_REQUIRED'
    $CandidateRoot = [IO.Path]::GetDirectoryName($Candidate)
    $AppAsar = Join-Path $CandidateRoot 'resources\app.asar'
    Require (Test-Path -LiteralPath $Candidate -PathType Leaf) 'R4_EXECUTABLE_NOT_FOUND'
    Require (Test-Path -LiteralPath $AppAsar -PathType Leaf) 'R4_APP_ASAR_NOT_FOUND'
    $ParityPath = FullPath $ParityProofPath
    $SmokePath = FullPath $SmokeProofPath
    Require (SamePath $ParityPath (Join-Path $RepoRoot '.coding-tools\reports\native-first-20261012\parallel-r4-candidate-parity.json')) 'EXACT_R4_PARITY_RECEIPT_REQUIRED'
    Require (SamePath $SmokePath (Join-Path $RepoRoot '.coding-tools\reports\native-first-20261012\parallel-r4-packaged-smoke.json')) 'EXACT_R4_SMOKE_RECEIPT_REQUIRED'
    $Parity = Read-BoundedJson $ParityPath
    $Smoke = Read-BoundedJson $SmokePath
    $ExeSha = Sha256 $Candidate
    $AsarSha = Sha256 $AppAsar
    Require ($Parity.ok -eq $true -and $Parity.proof_kind -eq 'exact_source_package_parity') 'R4_PARITY_PROOF_INVALID'
    Require (SamePath $Parity.candidate $ExpectedCandidate) 'R4_PARITY_CANDIDATE_MISMATCH'
    Require ($ExeSha -eq [string]$Parity.executable_sha256 -and $AsarSha -eq [string]$Parity.app_asar_sha256) 'R4_PACKAGE_HASH_CHANGED'
    Require ($Smoke.ok -eq $true -and (SamePath $Smoke.candidate $ExpectedCandidate)) 'R4_SMOKE_PROOF_INVALID'
    Require ($Smoke.sha256.executable -eq $ExeSha -and $Smoke.sha256.app_asar -eq $AsarSha) 'R4_SMOKE_PACKAGE_HASH_MISMATCH'
    Require ($Smoke.sha256.source_package_parity_receipt -eq (Sha256 $ParityPath)) 'R4_SMOKE_PARITY_CHAIN_BROKEN'
    $FixtureCount = @($Smoke.fixture_generations_alive_after).Count
    $CandidateProcessCount = @($Smoke.candidate_process_census_after).Count
    $ProfileCount = @($Smoke.profiles_remaining_after).Count
    $SmokeCleanupOk = ($Smoke.production_descriptor_stable -eq $true -and $FixtureCount -eq 0 -and $CandidateProcessCount -eq 0 -and $ProfileCount -eq 0)
    Require $SmokeCleanupOk 'R4_ISOLATED_SMOKE_CLEANUP_REQUIRED'
    return [ordered]@{ candidate = $ExpectedCandidate; executable_sha256 = $ExeSha; app_asar_sha256 = $AsarSha
        parity_proof = $ParityPath; parity_proof_sha256 = Sha256 $ParityPath
        smoke_proof = $SmokePath; smoke_proof_sha256 = Sha256 $SmokePath }
}

function Validate-Ready {
    $ReadyPath = FullPath $ReadyReceiptPath
    Require (SamePath $ReadyPath (Join-Path $TransitionRoot ([IO.Path]::GetFileName($ReadyPath)))) 'READY_RECEIPT_MUST_BE_IN_TRANSITION_DIR'
    $Ready = Read-BoundedJson $ReadyPath
    Require ($Ready.ok -eq $true -and (SamePath $Ready.candidate $ExpectedCandidate)) 'R4_READY_RECEIPT_INVALID'
    $Runtime = $Ready.receipt.runtime
    $Activation = $Ready.receipt.activation
    Require ($Runtime.fullyReady -eq $true -and $Runtime.mcpRunning -eq $true -and $Runtime.nativeAlive -eq $true) 'R4_RUNTIME_NOT_FULLY_READY'
    $ReadyEpochOk = ($Activation.activation_epoch_id -eq $ExpectedEpoch -and $Activation.state -eq 'READY' -and $Activation.epoch_state -eq 'READY' -and $Activation.admission_open -eq $true -and $Activation.update_incomplete -eq $false)
    Require $ReadyEpochOk 'R4_READY_EPOCH_INVALID'
    $ObservedMs = [int64]$Ready.observed_at_ms
    $AgeMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() - $ObservedMs
    Require ($AgeMs -ge 0 -and $AgeMs -le 120000) 'R4_READY_RECEIPT_STALE'
    return [ordered]@{ path = $ReadyPath; sha256 = Sha256 $ReadyPath; observed_at_ms = $ObservedMs
        age_ms = $AgeMs; activation_epoch_id = $Activation.activation_epoch_id }
}

function Load-ShortcutSpecs {
    $Evidence = Read-BoundedJson $R3EvidencePath
    Require ($Evidence.ok -eq $true -and @($Evidence.changes).Count -eq 2) 'R3_SHORTCUT_EVIDENCE_INVALID'
    $Specs = @()
    foreach ($Change in @($Evidence.changes)) {
        $Backup = FullPath $Change.backup
        $Path = FullPath $Change.path
        Require (Test-Path -LiteralPath $Backup -PathType Leaf) 'R3_SHORTCUT_BACKUP_MISSING'
        $BackupHash = Sha256 $Backup
        $Specs += [ordered]@{ path = $Path; old_target = [string]$Change.target; old_sha256 = $BackupHash
            backup = $Backup; backup_sha256 = $BackupHash }
    }
    return $Specs
}

function New-Intent($Proof, $Ready, $Before, $Specs) {
    return [ordered]@{
        schema_version = 1
        operation = 'update_coding_tools_shortcuts_r4'
        state = 'prepared'
        intent_id = [guid]::NewGuid().ToString('N')
        prepared_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        repo_root = $RepoRoot
        candidate = $Proof.candidate
        executable_sha256 = $Proof.executable_sha256
        app_asar_sha256 = $Proof.app_asar_sha256
        parity_proof = $Proof.parity_proof
        parity_proof_sha256 = $Proof.parity_proof_sha256
        smoke_proof = $Proof.smoke_proof
        smoke_proof_sha256 = $Proof.smoke_proof_sha256
        ready_receipt = $Ready.path
        ready_receipt_sha256 = $Ready.sha256
        expected_epoch = $Ready.activation_epoch_id
        shortcuts = @($Specs | ForEach-Object { [ordered]@{ path = $_.path; old_target = $_.old_target; old_sha256 = $_.old_sha256; backup = $_.backup; backup_sha256 = $_.backup_sha256 } })
        before = @($Before)
        apply_required = $true
        no_replay_after_uncertain = $true
    }
}

$Shell = New-Object -ComObject WScript.Shell
$ShellApplication = New-Object -ComObject Shell.Application
$Proof = Validate-PackageAndProofs
$Ready = Validate-Ready
$Specs = Load-ShortcutSpecs
$Before = @()
for ($Index = 0; $Index -lt $Specs.Count; $Index++) {
    $Observation = Get-ShortcutObservation $Specs[$Index].path $Shell $ShellApplication
    Require ($Observation.sha256 -eq $Specs[$Index].old_sha256 -and $Observation.target -eq $Specs[$Index].old_target -and [string]::IsNullOrEmpty([string]$Observation.arguments)) 'R3_SHORTCUT_SOURCE_CHANGED'
    $Before += $Observation
}

if (-not $Apply) {
    if (Test-Path -LiteralPath $IntentPath -PathType Leaf) {
        $Existing = Read-BoundedJson $IntentPath
        Require ($Existing.operation -eq 'update_coding_tools_shortcuts_r4' -and $Existing.state -eq 'prepared') 'ONE_SHOT_INTENT_ALREADY_CONSUMED'
        Write-Output (ConvertTo-Json ([ordered]@{ operation = 'coding_tools_shortcuts_prepared'; intent = (FullPath $IntentPath); reused = $true; originals_verified = $Before.Count; changed_shortcuts = 0 }) -Compress)
        exit 0
    }
    Write-Utf8Json $BeforeReceiptPath ([ordered]@{ schema_version = 1; operation = 'coding_tools_shortcuts_before_r4'; observed_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); proof = $Proof; ready = $Ready; shortcuts = $Before; production_shortcuts_mutated = $false })
    $Intent = New-Intent $Proof $Ready $Before $Specs
    Write-Utf8Json $IntentPath $Intent
    Write-Output (ConvertTo-Json ([ordered]@{ operation = 'coding_tools_shortcuts_prepared'; intent = (FullPath $IntentPath); originals_verified = $Before.Count; backups_verified = $Specs.Count; changed_shortcuts = 0; production_shortcuts_mutated = $false }) -Compress)
    exit 0
}

$IntentResolved = FullPath $IntentPath
Require (Test-Path -LiteralPath $IntentResolved -PathType Leaf) 'ONE_SHOT_INTENT_REQUIRED'
$Intent = Read-BoundedJson $IntentResolved
Require ($Intent.operation -eq 'update_coding_tools_shortcuts_r4' -and $Intent.state -eq 'prepared') 'ONE_SHOT_INTENT_ALREADY_CONSUMED'
Require ($Intent.candidate -eq $Proof.candidate -and $Intent.executable_sha256 -eq $Proof.executable_sha256 -and $Intent.app_asar_sha256 -eq $Proof.app_asar_sha256 -and $Intent.parity_proof_sha256 -eq $Proof.parity_proof_sha256 -and $Intent.smoke_proof_sha256 -eq $Proof.smoke_proof_sha256 -and $Intent.ready_receipt_sha256 -eq $Ready.sha256 -and $Intent.expected_epoch -eq $Ready.activation_epoch_id) 'ONE_SHOT_INTENT_PROOF_CHANGED'
Require ((@($Intent.shortcuts)).Count -eq $Specs.Count) 'ONE_SHOT_INTENT_SHORTCUT_COUNT_CHANGED'
for ($Index = 0; $Index -lt $Specs.Count; $Index++) {
    $IntentSpec = $Intent.shortcuts[$Index]
    Require ($IntentSpec.path -eq $Specs[$Index].path -and $IntentSpec.old_target -eq $Specs[$Index].old_target -and $IntentSpec.old_sha256 -eq $Specs[$Index].old_sha256 -and $IntentSpec.backup -eq $Specs[$Index].backup -and $IntentSpec.backup_sha256 -eq $Specs[$Index].backup_sha256) 'ONE_SHOT_INTENT_SHORTCUT_CHANGED'
}

# Re-read the source hashes immediately before the first mutation.  If any
# Save call fails after the marker below, the state becomes uncertain and a
# later invocation is rejected rather than replaying the operation.
for ($Index = 0; $Index -lt $Specs.Count; $Index++) {
    $Observation = Get-ShortcutObservation $Specs[$Index].path $Shell $ShellApplication
    Require ($Observation.sha256 -eq $Specs[$Index].old_sha256 -and $Observation.target -eq $Specs[$Index].old_target -and [string]::IsNullOrEmpty([string]$Observation.arguments)) 'R3_SHORTCUT_CHANGED_BEFORE_APPLY'
    Compare-PreservedShortcutProperties $Before[$Index] $Observation
}
$Intent.state = 'mutation_started'
$Intent.mutation_started_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
Write-Utf8Json $IntentResolved $Intent

$After = @()
try {
    for ($Index = 0; $Index -lt $Specs.Count; $Index++) {
        $Spec = $Specs[$Index]
        $Observation = Get-ShortcutObservation $Spec.path $Shell $ShellApplication
        Require ($Observation.sha256 -eq $Spec.old_sha256 -and $Observation.target -eq $Spec.old_target -and [string]::IsNullOrEmpty([string]$Observation.arguments)) 'R3_SHORTCUT_CHANGED_DURING_APPLY'
        $Shortcut = $Shell.CreateShortcut($Spec.path)
        $Shortcut.TargetPath = $Proof.candidate + '\Coding Tools MCP.exe'
        $Shortcut.WorkingDirectory = $Proof.candidate
        $Shortcut.Save()
        $Saved = Get-ShortcutObservation $Spec.path $Shell $ShellApplication
        Require ($Saved.target -eq ($Proof.candidate + '\Coding Tools MCP.exe') -and $Saved.working_directory -eq $Proof.candidate -and $Saved.target_exists) 'R4_SHORTCUT_TARGET_VERIFICATION_FAILED'
        Compare-PreservedShortcutProperties $Before[$Index] $Saved
        $After += $Saved
    }
    Write-Utf8Json $AfterReceiptPath ([ordered]@{ schema_version = 1; operation = 'coding_tools_shortcuts_after_r4'; observed_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); intent_id = $Intent.intent_id; candidate = $Proof.candidate; executable_sha256 = $Proof.executable_sha256; app_asar_sha256 = $Proof.app_asar_sha256; shortcuts = $After; backups_preserved = $true; production_shortcuts_mutated = $true })
    $Intent.state = 'applied'
    $Intent.applied_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $Intent.after_receipt = $AfterReceiptPath
    $Intent.after_receipt_sha256 = Sha256 $AfterReceiptPath
    Write-Utf8Json $IntentResolved $Intent
    Write-Output (ConvertTo-Json ([ordered]@{ operation = 'coding_tools_shortcuts_updated'; changed_shortcuts = $After.Count; target = $Proof.candidate + '\Coding Tools MCP.exe'; exe_sha256 = $Proof.executable_sha256; asar_sha256 = $Proof.app_asar_sha256; preserved_r3_backups = $true; no_replay_state = 'applied' }) -Compress)
} catch {
    $Intent.state = 'uncertain'
    $Intent.uncertain_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $Intent.failure_code = 'SHORTCUT_MUTATION_UNCERTAIN'
    try { Write-Utf8Json $IntentResolved $Intent } catch { }
    throw
}
