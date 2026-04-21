# Build a single-file Windows GUI executable (run in PowerShell on Windows).
# Prerequisite: Python 3.10+ on PATH, game monitor deps installed:
#   pip install -r requirements-windows-gui.txt

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $root

if (-not $IsWindows -and $env:OS -notmatch "Windows") {
    Write-Error "This build script must run on Windows."
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "LastWarAllianceMonitor" `
    --hidden-import "psutil._psutil_windows" `
    lw_monitor_gui.py

Write-Host "Done. Output: $root\dist\LastWarAllianceMonitor.exe"
