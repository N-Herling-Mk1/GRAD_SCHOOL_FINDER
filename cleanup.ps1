# cleanup.ps1 -- flatten and verify 0_grad_site, then start the server.
#
#   Unblock-File .\cleanup.ps1 ; .\cleanup.ps1
#
# Nothing is deleted until the flat copy has been verified file by file.
# Switches:  -NoRun    verify and clean, do not start the server
#            -DryRun   report only, touch nothing

param(
    [switch]$NoRun,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$nested  = Join-Path $PSScriptRoot "gradfinder_mk1"
$attic   = Join-Path $PSScriptRoot "_drops"

# ------------------------------------------------------------------ manifest
# path -> a marker string that must appear in the file. Length and timestamp are
# not trusted here: files under OneDrive have silently reverted to older deltas
# before, and only content proves which version is on disk.
$manifest = [ordered]@{
    ".gitignore"                            = "__pycache__"
    "README.md"                             = "GRADFINDER mk1"
    "app.py"                                = "create_app"
    "config.py"                             = "GRADFINDER_PORT"
    "requirements.txt"                      = "Flask"
    "run.ps1"                               = "validating data packs"
    "run.sh"                                = "check_data.py"
    "data\derived\projection.json"          = "gradfinder.projection/1"
    "data\institutions\AZ.json"             = "gradfinder.state_pack/1"
    "docs\NEXT.md"                          = "Open decisions"
    "docs\map_snapshot.png"                 = $null
    "gradfinder\__init__.py"                = "def create_app"
    "gradfinder\routes\__init__.py"         = $null
    "gradfinder\routes\api.py"              = "states/<code>"
    "gradfinder\routes\views.py"            = "def method"
    "gradfinder\services\__init__.py"       = $null
    "gradfinder\services\albers.py"         = "def solve_fit"
    "gradfinder\services\geo.py"            = "def load_geo"
    "gradfinder\services\store.py"          = "def rollup"
    "gradfinder\static\css\tokens.css"      = "--cyan: #35e0ff"
    "gradfinder\static\css\layout.css"      = ".status"
    "gradfinder\static\css\map.css"         = ".smallchips"
    "gradfinder\static\css\panel.css"       = ".fambar"
    "gradfinder\static\geo\us_states.json"  = "gradfinder.geo/1"
    "gradfinder\static\js\api.js"           = "GF.api"
    "gradfinder\static\js\app.js"           = "wireFilters"
    "gradfinder\static\js\map.js"           = "function tweenTo"
    "gradfinder\static\js\panel.js"         = "function famBars"
    "gradfinder\templates\base.html"        = "GRADFINDER"
    "gradfinder\templates\index.html"       = "layer-markers"
    "gradfinder\templates\method.html"      = "Counting rule"
    "tools\build_geo.py"                    = "douglas_peucker"
    "tools\check_data.py"                   = "outside the state bbox"
    "tools\us-states.raw.json"              = "FeatureCollection"
}

function Say($msg, $color = "Gray") { Write-Host "  $msg" -ForegroundColor $color }
function Head($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }

Write-Host "GRADFINDER mk1 -- directory cleanup" -ForegroundColor Cyan
Say ("root      " + $PSScriptRoot)
Say ("mode      " + $(if ($DryRun) { "dry run" } else { "apply" })) $(if ($DryRun) { "Yellow" } else { "Gray" })

if ($PSScriptRoot -match "OneDrive") {
    Say "root is under OneDrive -- known hazard: files can revert to older deltas mid-session" "Yellow"
}

# ---------------------------------------------- 1. backfill from the nested copy
Head "1/5  reconcile against .\gradfinder_mk1"
$restored = 0
if (Test-Path $nested) {
    $files = @($manifest.Keys)
    for ($i = 0; $i -lt $files.Count; $i++) {
        $rel = $files[$i]
        Write-Progress -Activity "Reconciling" -Status $rel -PercentComplete (100 * ($i + 1) / $files.Count)
        $flat = Join-Path $PSScriptRoot $rel
        $deep = Join-Path $nested $rel
        if ((Test-Path $deep) -and -not (Test-Path $flat)) {
            Say "restoring $rel from the nested copy" "Yellow"
            if (-not $DryRun) {
                New-Item -ItemType Directory -Force -Path (Split-Path $flat) | Out-Null
                Copy-Item $deep $flat
            }
            $restored++
        }
    }
    Write-Progress -Activity "Reconciling" -Completed
    Say "$restored file(s) restored from .\gradfinder_mk1"
} else {
    Say "no nested copy present, nothing to reconcile"
}

# ------------------------------------------------------- 2. verify the flat tree
Head "2/5  verify the flat tree"
$missing = @()
$stale   = @()
$files = @($manifest.Keys)
for ($i = 0; $i -lt $files.Count; $i++) {
    $rel = $files[$i]
    Write-Progress -Activity "Verifying" -Status $rel -PercentComplete (100 * ($i + 1) / $files.Count)
    $path = Join-Path $PSScriptRoot $rel
    if (-not (Test-Path $path)) { $missing += $rel; continue }
    $marker = $manifest[$rel]
    if ($marker) {
        if (-not (Select-String -Path $path -SimpleMatch -Pattern $marker -Quiet)) {
            $stale += $rel
        }
    }
}
Write-Progress -Activity "Verifying" -Completed

Say ("present   {0}/{1}" -f ($files.Count - $missing.Count), $files.Count) $(if ($missing) { "Red" } else { "Green" })
foreach ($m in $missing) { Say "MISSING  $m" "Red" }
foreach ($s in $stale)   { Say "MARKER FAILED  $s  (wrong version on disk)" "Red" }

if ($missing.Count -or $stale.Count) {
    Write-Host "`nVerification failed. Nothing deleted. Re-extract the drop before continuing." -ForegroundColor Red
    exit 1
}
Say "all markers matched" "Green"

# ------------------------------------------------------ 3. retire the duplicates
Head "3/5  retire duplicates and drop artifacts"
if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $attic | Out-Null }

foreach ($f in @("gradfinder_mk1.zip", "map_snapshot.png")) {
    $p = Join-Path $PSScriptRoot $f
    if (Test-Path $p) {
        Say "moving $f -> _drops\"
        if (-not $DryRun) { Move-Item $p (Join-Path $attic $f) -Force }
    }
}

if (Test-Path $nested) {
    Say "removing the nested .\gradfinder_mk1 copy" "Yellow"
    if (-not $DryRun) { Remove-Item $nested -Recurse -Force }
}

# --------------------------------------------------------------- 4. scratch dirs
Head "4/5  clear build scratch"
$pyc = Get-ChildItem -Path $PSScriptRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($pyc) {
    Say ("removing {0} __pycache__ dir(s)" -f $pyc.Count)
    if (-not $DryRun) { $pyc | Remove-Item -Recurse -Force }
} else {
    Say "no __pycache__ to clear"
}

# -------------------------------------------------------------------- 5. report
Head "5/5  final layout"
Get-ChildItem -Path $PSScriptRoot -Force |
    Where-Object { $_.Name -notin @(".git", ".venv") } |
    Sort-Object { -not $_.PSIsContainer }, Name |
    ForEach-Object {
        $tag = if ($_.PSIsContainer) { "dir " } else { "file" }
        Say ("{0}  {1}" -f $tag, $_.Name)
    }

if ($DryRun) { Write-Host "`nDry run complete. Nothing was changed." -ForegroundColor Yellow; exit 0 }
Write-Host "`nDirectory clean." -ForegroundColor Green

if ($NoRun) { Write-Host "Start it with:  .\run.ps1" -ForegroundColor DarkCyan; exit 0 }

Write-Host "`nStarting the server..." -ForegroundColor Cyan
Unblock-File .\run.ps1 -ErrorAction SilentlyContinue
& .\run.ps1
