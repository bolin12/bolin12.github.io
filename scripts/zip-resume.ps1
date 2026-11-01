# 把 resume/ 打成 zip,直接在 Overleaf: New Project -> Upload Project 导入
$root = Split-Path $PSScriptRoot -Parent
$out  = Join-Path $root "resume.zip"
Remove-Item $out -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $root "resume\*") -DestinationPath $out
Write-Host "已生成 $out"
