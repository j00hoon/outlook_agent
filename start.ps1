# ========================================
# start.ps1 - Start backend + frontend
# ========================================

$rootPath    = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $rootPath "backend"
$frontendPath= Join-Path $rootPath "frontend"
$venvActivate= Join-Path $rootPath "venv\Scripts\Activate.ps1"
$logDir      = Join-Path $rootPath "logs"

# 로그 폴더 생성
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Outlook Agent Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Backend ──────────────────────────────
Write-Host "[1/2] Starting Backend (FastAPI)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "
    cd '$rootPath'
    & '$venvActivate'
    Write-Host 'Backend running at http://localhost:8000' -ForegroundColor Green
    cd '$backendPath'
    uvicorn app.main:app --reload 2>&1 | Tee-Object -FilePath '$logDir\backend.log'
    "
)

# Backend 뜰 때까지 대기
Write-Host "   Waiting for backend..." -ForegroundColor Gray
$backendReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        $backendReady = $true
        break
    } catch {}
}

if ($backendReady) {
    Write-Host "   Backend is ready!" -ForegroundColor Green
} else {
    Write-Host "   Backend might still be loading, check logs\backend.log" -ForegroundColor Red
}

# ── Frontend ─────────────────────────────
Write-Host ""
Write-Host "[2/2] Starting Frontend (Next.js)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "
    cd '$frontendPath'
    Write-Host 'Frontend running at http://localhost:3000' -ForegroundColor Green
    npm run dev 2>&1 | Tee-Object -FilePath '$logDir\frontend.log'
    "
)

Start-Sleep -Seconds 3

# ── 브라우저 자동 오픈 ───────────────────
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Logs     : $logDir" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""