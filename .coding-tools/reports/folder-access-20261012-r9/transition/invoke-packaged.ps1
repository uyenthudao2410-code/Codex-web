param([ValidateSet('retire','status','refresh','complete','activate','metadata','files','exec','observe')][string]$Operation,[string]$Epoch)
$ErrorActionPreference='Stop'
$candidate = if ($Operation -eq 'retire') {
 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r8\win-unpacked'
} else { 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9\win-unpacked' }
$script = Join-Path $PSScriptRoot $(if($Operation -eq 'observe'){'observe-r9-machine.cjs'}else{'packaged-operations.cjs'})
$id=[guid]::NewGuid().ToString('N')
$stdout=Join-Path $PSScriptRoot ($Operation+'-'+$id+'.stdout.json')
$stderr=Join-Path $PSScriptRoot ($Operation+'-'+$id+'.stderr.txt')
$generation='generation_03f9c04f1b14414fa4bfa7d91cc8ea7a'
$arguments=if($Operation -eq 'observe'){@(('"'+$script+'"'),('"'+$candidate+'"'),$Epoch)}else{
 @(('"'+$script+'"'),$Operation,('"'+$candidate+'"')) + $(if($Operation -eq 'complete'){@($Epoch)}elseif($Operation -in @('metadata','files','exec')){@($generation)}else{@()})
}
$previous=$env:ELECTRON_RUN_AS_NODE
try {
 $env:ELECTRON_RUN_AS_NODE='1'
 $process=Start-Process -FilePath (Join-Path $candidate 'Coding Tools MCP.exe') -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
 $raw=Get-Content -LiteralPath $(if($process.ExitCode -eq 0){$stdout}else{$stderr}) -Raw
 if ($raw.Trim()) { $result=$raw | ConvertFrom-Json; $result | Select-Object operation,ok,code,stage,report_path,@{n='activation';e={$_.receipt.activation}},@{n='target';e={$_.receipt | Select-Object workspace_id,workspace_generation,binding_id,pilot_decision_id,workspace_path,expires_at_ms}},@{n='runtime';e={$_.receipt.runtime | Select-Object mcpRunning,fullyReady,centralConnected,authorityReady,activationState,activationEpochId}} | ConvertTo-Json -Depth 8 -Compress }
 Write-Output ('PROCESS_EXIT='+$process.ExitCode)
 exit $process.ExitCode
} finally { $env:ELECTRON_RUN_AS_NODE=$previous }
