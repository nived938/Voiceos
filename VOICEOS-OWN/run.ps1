# PowerShell launcher for VoiceOS-Own
$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     Launching VoiceOS-Own Desktop App    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Verify Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python was not found in PATH." -ForegroundColor Red
    exit 1
}

# Run Application
python main.py
