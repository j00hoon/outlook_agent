# ========================================
# start.ps1
# Start backend + frontend
# ========================================

# Project paths
$backendPath = "C:\Users\SDSA\OneDrive\Desktop\Work\Operation service part\2025_2026\99. outlook_summarization\backend"
$frontendPath = "C:\Users\SDSA\OneDrive\Desktop\Work\Operation service part\2025_2026\99. outlook_summarization\frontend"

Write-Host "Starting backend (FastAPI)..."

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendPath'; uvicorn app.main:app --reload"
)

Write-Host "Backend started."

Write-Host "Starting frontend (Next.js)..."

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendPath'; npm run dev"
)

Write-Host "Frontend started."

Write-Host "All services started."