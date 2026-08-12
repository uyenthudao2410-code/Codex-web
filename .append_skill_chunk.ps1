$dest='C:\Users\Admin\.codex\skill-staging\sol-lean-codex-v4\delta.b64'
$text=[Console]::In.ReadToEnd()
[IO.File]::AppendAllText($dest,$text,[Text.Encoding]::ASCII)

