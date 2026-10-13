param([ValidateSet('retire','status','refresh','stop','observe','stopped-observation')][string]$Operation,[string]$Epoch)
$ErrorActionPreference='Stop'
$tag=if($Operation -eq 'retire'){'r7'}else{'r8'}
$candidate='E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-'+$tag+'\win-unpacked'
$script=Join-Path $PSScriptRoot $(if($Operation -eq 'observe'){'observe-r8-machine.cjs'}else{'packaged-operations.cjs'})
$id=[guid]::NewGuid().ToString('N')
$stdout=Join-Path $PSScriptRoot ($Operation+'-'+$id+'.stdout.json')
$stderr=Join-Path $PSScriptRoot ($Operation+'-'+$id+'.stderr.txt')
$args=if($Operation -eq 'observe'){@(('"'+$script+'"'),('"'+$candidate+'"'),$Epoch)}else{@(('"'+$script+'"'),$Operation,('"'+$candidate+'"'))}
$previous=$env:ELECTRON_RUN_AS_NODE
try {
 $env:ELECTRON_RUN_AS_NODE='1'
 $p=Start-Process -FilePath (Join-Path $candidate 'Coding Tools MCP.exe') -ArgumentList $args -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
 Get-Content -LiteralPath $stdout
 Get-Content -LiteralPath $stderr
 Write-Output ('PROCESS_EXIT='+$p.ExitCode)
 exit $p.ExitCode
} finally {$env:ELECTRON_RUN_AS_NODE=$previous}
