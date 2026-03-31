# ========================================
# stop.ps1
# Stop backend + frontend
# ========================================

Write-Host "Stopping backend and frontend..."

# Stop uvicorn / FastAPI backend
Get-CimInstance Win32_Process |
Where-Object {
    $_.CommandLine -match "uvicorn app.main:app"
} |
ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    Write-Host "Stopped backend process ID:" $_.ProcessId
}

# Stop Next.js frontend
Get-CimInstance Win32_Process |
Where-Object {
    $_.CommandLine -match "next dev"
} |
ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    Write-Host "Stopped frontend process ID:" $_.ProcessId
}

Write-Host "All services stopped."