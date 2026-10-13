$ErrorActionPreference='Stop'
$r4='E:\DEV\Codex-web\.coding-tools\reports\parallel-native-first-20261012\canary\r4'
$electron='E:\DEV\Codex-web\node_modules\electron\dist\electron.exe'
$script=Join-Path $r4 'semantic-replan-one.cjs'
$rows=@()
foreach($n in 3..20){$lane=('patch_{0:d3}' -f $n);$out=Join-Path $r4 ("semantic-lane-{0:d3}.stdout" -f $n);$err=Join-Path $r4 ("semantic-lane-{0:d3}.stderr" -f $n);Remove-Item $out,$err -ErrorAction SilentlyContinue;$profile=Join-Path $r4 ("semantic-lane-profile-{0:d3}" -f $n);$p=Start-Process -FilePath $electron -ArgumentList @('--user-data-dir='+$profile,$script,'--lane',$lane) -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -Wait -WindowStyle Hidden;$text=(Get-Content $out -Raw -ErrorAction SilentlyContinue);$rows += [pscustomobject]@{lane=$lane;exit=$p.ExitCode;stdout=$text};if($p.ExitCode -ne 0){break}}
$rows | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $r4 'semantic-lanes-summary.json') -Encoding UTF8
