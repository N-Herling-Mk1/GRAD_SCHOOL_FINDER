# export.ps1 -- validate, freeze to site/, and serve it locally the way Pages will.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
if (Test-Path ".\.venv") { & .\.venv\Scripts\Activate.ps1 }
Write-Host "[export] validating data packs..." -ForegroundColor DarkCyan
python .\tools\check_data.py
if ($LASTEXITCODE -ne 0) { Write-Host "[export] data check failed." -ForegroundColor Red; exit 1 }
python .\tools\export_static.py --out site
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "[export] previewing on http://127.0.0.1:8080/  (Ctrl+C to stop)" -ForegroundColor Green
python -m http.server 8080 -d site
