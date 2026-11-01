# Local preview with the author's notes shown, plus NOTES.md (the to-do list). Nothing here is published.
#   powershell -File scripts\preview.ps1          serve at http://localhost:4000
#   powershell -File scripts\preview.ps1 -NotesOnly   only regenerate NOTES.md
param([switch]$NotesOnly, [int]$Port = 4000)

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')

python scripts\notes_report.py
if ($NotesOnly) { return }

Write-Host "Preview with notes: http://localhost:$Port/  (Ctrl+C to stop)"
bundle exec jekyll serve --config "_config.yml,_config_local.yml" --port $Port --destination _site_local
