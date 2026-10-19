param (
    [switch]$NoBrowser
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Lifeline Triage Cyclone Response System     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot

# 1. Start Backend
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru

# 2. Start Frontend
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\frontend'; npm run dev" -PassThru

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Lifeline Triage is running!                           " -ForegroundColor Green
Write-Host "  - Frontend UI:      http://localhost:5173            " -ForegroundColor Green
Write-Host "  - Backend API:      http://127.0.0.1:8000            " -ForegroundColor Green
Write-Host "  - Interactive Docs: http://127.0.0.1:8000/docs       " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

if (-not $NoBrowser) {
    Start-Process "http://localhost:5173"
}
