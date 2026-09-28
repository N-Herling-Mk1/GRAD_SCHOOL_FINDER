# run.ps1 -- start the gradfinder dev server on Windows.
# Unblock-File .\run.ps1   before the first run if it came out of a zip.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "[run] checking python..." -ForegroundColor DarkCyan
python --version

if (-not (Test-Path ".\.venv")) {
    Write-Host "[run] creating .venv..." -ForegroundColor DarkCyan
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1

Write-Host "[run] installing requirements..." -ForegroundColor DarkCyan
pip install -q -r requirements.txt

if (-not (Test-Path ".\gradfinder\static\geo\us_states.json")) {
    Write-Host "[run] geometry missing, building..." -ForegroundColor Yellow
    python .\tools\build_geo.py
}

Write-Host "[run] validating data packs..." -ForegroundColor DarkCyan
python .\tools\check_data.py
if ($LASTEXITCODE -ne 0) { Write-Host "[run] data check failed. Fix the pack before serving." -ForegroundColor Red; exit 1 }

Write-Host "[run] starting server on http://127.0.0.1:5057/" -ForegroundColor Green
python .\app.py
