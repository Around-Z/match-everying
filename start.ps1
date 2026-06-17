# Matching Platform Launcher (PowerShell)
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Multi-Scenario Matching Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check .env
$envFile = Join-Path $ROOT "backend\.env"
$hasZhipu = Select-String -Path $envFile -Pattern "your_zhipuai_api_key_here" -Quiet
$hasDeep = Select-String -Path $envFile -Pattern "your_deepseek_api_key_here" -Quiet
if ($hasZhipu -or $hasDeep) {
    Write-Host "[WARN] Configure API keys in backend\.env:" -ForegroundColor Yellow
    if ($hasZhipu) { Write-Host "  - ZHIPUAI_API_KEY" -ForegroundColor Yellow }
    if ($hasDeep)  { Write-Host "  - DEEPSEEK_API_KEY" -ForegroundColor Yellow }
    Write-Host ""
}

# Find Python (prefer conda)
$python = "python"
$condaPy = "$env:USERPROFILE\anaconda3\python.exe"
if (Test-Path $condaPy) { $python = $condaPy }

# Kill old instances
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -match "uvicorn|Matching" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

# Start backend
Write-Host "[1/2] Starting backend..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k title Matching-Backend && cd /d `"$ROOT\backend`" && `"$python`" run.py"

Start-Sleep -Seconds 3

# Start frontend
Write-Host "[2/2] Starting frontend..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k title Matching-Frontend && cd /d `"$ROOT\frontend`" && npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close the two CMD windows to stop services." -ForegroundColor Gray
