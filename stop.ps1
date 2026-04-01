$ErrorActionPreference = "Stop"

$redisContainerName = "redis-stack-server"
$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $rootPath "logs"
$backendPidFile = Join-Path $logDir "backend.pid"
$frontendPidFile = Join-Path $logDir "frontend.pid"

function Test-DockerAvailable {
    try {
        $null = docker version 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Stop-ServiceFromPidFile([string]$Name, [string]$PidFile) {
    if (-not (Test-Path $PidFile)) {
        Write-Host "  $Name PID file not found. Skipping." -ForegroundColor Yellow
        return
    }

    $pidValue = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pidValue) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "  $Name PID file was empty. Skipping." -ForegroundColor Yellow
        return
    }

    $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force
        Write-Host "  $Name stopped (PID $pidValue)." -ForegroundColor Green
    } else {
        Write-Host "  $Name process was already stopped." -ForegroundColor Yellow
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ProcessByPort([string]$Name, [int]$Port) {
    $lines = netstat -ano -p tcp | Select-String ":$Port "
    $pids = @()

    foreach ($line in $lines) {
        $parts = ($line.ToString() -split "\s+") | Where-Object { $_ }
        if ($parts.Length -ge 5 -and $parts[3] -eq "LISTENING") {
            $parsedPid = 0
            if ([int]::TryParse($parts[4], [ref]$parsedPid)) {
                $pids += $parsedPid
            }
        }
    }

    $pids = $pids | Sort-Object -Unique
    if (-not $pids) {
        Write-Host "  No listener found on port $Port." -ForegroundColor Yellow
        return
    }

    foreach ($targetPid in $pids) {
        $process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $targetPid -Force
            Write-Host "  $Name stopped via port $Port (PID $targetPid)." -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stopping Outlook Agent" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Stopping backend..." -ForegroundColor Yellow
Stop-ServiceFromPidFile -Name "Backend" -PidFile $backendPidFile
Stop-ProcessByPort -Name "Backend" -Port 8000

Write-Host "[2/3] Stopping frontend..." -ForegroundColor Yellow
Stop-ServiceFromPidFile -Name "Frontend" -PidFile $frontendPidFile
Stop-ProcessByPort -Name "Frontend" -Port 3000

Write-Host "[3/3] Stopping Redis..." -ForegroundColor Yellow
if (-not (Test-DockerAvailable)) {
    Write-Host "  Docker Desktop is not running. Redis stop skipped." -ForegroundColor Yellow
} else {
    $isRunning = docker ps -q -f name="^/${redisContainerName}$"
    if ($isRunning) {
        docker stop $redisContainerName | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Redis container stopped." -ForegroundColor Green
        } else {
            Write-Host "  Failed to stop Redis container." -ForegroundColor Red
        }
    } else {
        Write-Host "  Redis container is already stopped." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "All stop tasks completed." -ForegroundColor Cyan
