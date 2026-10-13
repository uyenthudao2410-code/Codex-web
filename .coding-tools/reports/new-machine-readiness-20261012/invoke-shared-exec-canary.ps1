# One reviewed operator canary, using the existing pinned SSH host key.
# Credential bytes remain on svhome and are never arguments or local output.
param(
    [Parameter(Mandatory = $true)]
    [switch]$ExecuteConfirmedReadyPilot
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedReadyPilot) { throw 'EXPLICIT_CANARY_EXECUTION_REQUIRED' }
$reportDirectory = 'E:\DEV\Codex-web\.coding-tools\reports\new-machine-readiness-20261012'
$scriptPath = Join-Path $reportDirectory 'run-shared-exec-canary.py'
$receiptPath = Join-Path $reportDirectory 'shared-exec-canary-receipt.ndjson'
$attemptId = '3517e4afc0344b3ea64902f492784795'
if (Test-Path -LiteralPath $receiptPath) { throw 'LOCAL_CANARY_RECEIPT_ALREADY_EXISTS_DO_NOT_REDISPATCH' }
$sshArguments = @(
    '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes',
    'svhome@100.116.112.22', 'python3', '-B', '-',
    '--binding-id', 'bind_71661b1046884174b01c99af5f8546aa',
    '--new-generation', 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097',
    '--pilot-decision-id', 'pilot_dfb3174078d842299c41c6638830e505',
    '--activation-epoch', 'activation-mv4od6fe-c45648f5d945ceeb7f3640048b0e91b7',
    '--process-instance-id', 'Mmrm0HVhHUpvj9sz',
    '--server-instance-id', 'oOu_kV3jhDH_x822',
    '--local-tool-contract-sha256', '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4',
    '--attempt-id', $attemptId,
    '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization',
    '--execute-confirmed-ready-pilot'
)
Get-Content -LiteralPath $scriptPath -Raw | & ssh.exe @sshArguments | Tee-Object -FilePath $receiptPath
$sshExitCode = $LASTEXITCODE
Write-Output (ConvertTo-Json -Compress @{ operation = 'shared_exec_canary_ssh'; exit_code = $sshExitCode; attempt_id = $attemptId })
exit $sshExitCode
