# ========================================
# stop.ps1 - Stop backend + frontend
# ========================================

Write-Host ""
Write-Host "Stopping all services..." -ForegroundColor Yellow

# FastAPI (uvicorn) 종료
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "  Backend stopped" -ForegroundColor Green

# Next.js (node) 종료
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "  Frontend stopped" -ForegroundColor Green

Write-Host "All services stopped." -ForegroundColor Cyan
Write-Host ""