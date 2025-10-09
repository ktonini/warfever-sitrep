# Auto-organize screenshots by game location
param(
    [string]$SourceFolder = ".\extracted-screenshots",
    [string]$DestFolder = ".\organized-assets"
)

Write-Host "=== The Last War Screenshot Organizer ===" -ForegroundColor Cyan
Write-Host ""

# Create folder structure
$folders = @(
    "alliance-logos",
    "resources\gold",
    "resources\gems",
    "resources\materials",
    "chests",
    "buildings",
    "heroes",
    "ui"
)

Write-Host "Creating folder structure..." -ForegroundColor Yellow
foreach ($folder in $folders) {
    $path = Join-Path $DestFolder $folder
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    Write-Host "  ✓ Created: $folder" -ForegroundColor Green
}

# Check if source folder exists
if (-not (Test-Path $SourceFolder)) {
    Write-Host ""
    Write-Host "Source folder not found: $SourceFolder" -ForegroundColor Red
    Write-Host "Creating it for you..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $SourceFolder | Out-Null
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Take screenshots using Win+Shift+S" -ForegroundColor White
    Write-Host "2. Save them to: $SourceFolder" -ForegroundColor White
    Write-Host "3. Run this script again to organize them" -ForegroundColor White
    exit
}

# Get all PNG files
$screenshots = Get-ChildItem "$SourceFolder\*.png" -ErrorAction SilentlyContinue

if ($screenshots.Count -eq 0) {
    Write-Host ""
    Write-Host "No screenshots found in: $SourceFolder" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Take screenshots using Win+Shift+S" -ForegroundColor White
    Write-Host "2. Save them to: $SourceFolder" -ForegroundColor White
    Write-Host "3. Run this script again to organize them" -ForegroundColor White
    exit
}

Write-Host ""
Write-Host "Found $($screenshots.Count) screenshots to organize..." -ForegroundColor Cyan
Write-Host ""

# Statistics
$stats = @{
    "alliance-logos" = 0
    "resources" = 0
    "chests" = 0
    "buildings" = 0
    "heroes" = 0
    "ui" = 0
}

# Move files based on naming pattern
foreach ($file in $screenshots) {
    $name = $file.Name.ToLower()
    $moved = $false

    if ($name -match "alliance|logo") {
        Copy-Item $file.FullName "$DestFolder\alliance-logos\" -Force
        $stats["alliance-logos"]++
        Write-Host "  → alliance-logos: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "gold|coin") {
        Copy-Item $file.FullName "$DestFolder\resources\gold\" -Force
        $stats["resources"]++
        Write-Host "  → resources/gold: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "gem|diamond") {
        Copy-Item $file.FullName "$DestFolder\resources\gems\" -Force
        $stats["resources"]++
        Write-Host "  → resources/gems: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "resource|material|item") {
        Copy-Item $file.FullName "$DestFolder\resources\materials\" -Force
        $stats["resources"]++
        Write-Host "  → resources/materials: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "chest|box|crate") {
        Copy-Item $file.FullName "$DestFolder\chests\" -Force
        $stats["chests"]++
        Write-Host "  → chests: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "building") {
        Copy-Item $file.FullName "$DestFolder\buildings\" -Force
        $stats["buildings"]++
        Write-Host "  → buildings: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    elseif ($name -match "hero|character") {
        Copy-Item $file.FullName "$DestFolder\heroes\" -Force
        $stats["heroes"]++
        Write-Host "  → heroes: $($file.Name)" -ForegroundColor Green
        $moved = $true
    }
    else {
        Copy-Item $file.FullName "$DestFolder\ui\" -Force
        $stats["ui"]++
        Write-Host "  → ui: $($file.Name)" -ForegroundColor Gray
        $moved = $true
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Alliance Logos: $($stats['alliance-logos'])" -ForegroundColor White
Write-Host "Resources: $($stats['resources'])" -ForegroundColor White
Write-Host "Chests: $($stats['chests'])" -ForegroundColor White
Write-Host "Buildings: $($stats['buildings'])" -ForegroundColor White
Write-Host "Heroes: $($stats['heroes'])" -ForegroundColor White
Write-Host "UI Elements: $($stats['ui'])" -ForegroundColor White
Write-Host ""
Write-Host "Screenshots organized successfully!" -ForegroundColor Green
Write-Host "Output location: $DestFolder" -ForegroundColor Cyan
