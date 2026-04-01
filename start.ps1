$ErrorActionPreference = "Stop"

$redisContainerName = "redis-stack-server"
$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $rootPath "backend"
$frontendPath = Join-Path $rootPath "frontend"
$venvActivate = Join-Path $rootPath "venv\Scripts\Activate.ps1"
$logDir = Join-Path $rootPath "logs"
$backendPidFile = Join-Path $logDir "backend.pid"
$frontendPidFile = Join-Path $logDir "frontend.pid"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

function Write-Section([string]$Message) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Test-DockerAvailable {
    try {
        $null = docker version 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds = 20) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}

function Wait-ForTcpPort([string]$TargetHost, [int]$Port, [int]$TimeoutSeconds = 20) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $client.BeginConnect($TargetHost, $Port, $null, $null)
            if ($async.AsyncWaitHandle.WaitOne(1000, $false) -and $client.Connected) {
                $client.EndConnect($async)
                return $true
            }
        } catch {
        } finally {
            $client.Close()
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Ensure-RedisContainer {
    Write-Host "[0/2] Checking Redis container..." -ForegroundColor Yellow

    if (-not (Test-DockerAvailable)) {
        Write-Host "   Docker Desktop is not running. Start Docker Desktop, then rerun start.ps1." -ForegroundColor Red
        return $false
    }

    $containerExists = docker ps -a -q -f name="^/${redisContainerName}$"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Failed to query Docker for Redis container state." -ForegroundColor Red
        return $false
    }

    if ($containerExists) {
        $isRunning = docker ps -q -f name="^/${redisContainerName}$"
        if (-not $isRunning) {
            Write-Host "   Starting existing Redis container..." -ForegroundColor Yellow
            docker start $redisContainerName | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   Failed to start Redis container." -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "   Redis container is already running." -ForegroundColor Green
        }
    } else {
        Write-Host "   Creating Redis container..." -ForegroundColor Yellow
        docker run -d --name $redisContainerName -p 6379:6379 redis/redis-stack-server:latest | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   Failed to create Redis container." -ForegroundColor Red
            return $false
        }
    }

    Write-Host "   Waiting for Redis on localhost:6379..." -ForegroundColor Gray
    if (Wait-ForTcpPort -TargetHost "127.0.0.1" -Port 6379 -TimeoutSeconds 20) {
        Write-Host "   Redis is ready." -ForegroundColor Green
        return $true
    }

    Write-Host "   Redis container started but port 6379 did not become ready in time." -ForegroundColor Red
    return $false
}

function Start-ServiceWindow(
    [string]$Name,
    [string]$WorkingDirectory,
    [string]$Command,
    [string]$PidFile
) {
    $process = Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        $Command
    ) -WorkingDirectory $WorkingDirectory -PassThru

    Set-Content -Path $PidFile -Value $process.Id
    Write-Host "   $Name window started (PID $($process.Id))." -ForegroundColor Green
}

Write-Section "Outlook Agent Starting"

$redisReady = Ensure-RedisContainer
if (-not $redisReady) {
    Write-Host ""
    Write-Host "Start aborted because Redis is required for this app." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/2] Starting Backend (FastAPI)..." -ForegroundColor Yellow

$backendCommand = @"
cd '$rootPath'
& '$venvActivate'
`$env:HF_HUB_OFFLINE = '1'
`$env:TRANSFORMERS_OFFLINE = '1'
`$env:EMBEDDING_MODEL_PATH = '$backendPath\models\paraphrase-multilingual-MiniLM-L12-v2'
Write-Host 'Backend running at http://localhost:8000' -ForegroundColor Green
cd '$backendPath'
uvicorn app.main:app --reload 2>&1 | Tee-Object -FilePath '$logDir\backend.log'
"@

Start-ServiceWindow -Name "Backend" -WorkingDirectory $backendPath -Command $backendCommand -PidFile $backendPidFile

Write-Host "   Waiting for backend..." -ForegroundColor Gray
if (Wait-ForHttp -Url "http://localhost:8000/docs" -TimeoutSeconds 60) {
    Write-Host "   Backend is ready." -ForegroundColor Green
} else {
    Write-Host "   Backend did not become ready. Check logs\backend.log." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/2] Starting Frontend (Next.js)..." -ForegroundColor Yellow

$frontendCommand = @"
cd '$frontendPath'
Write-Host 'Frontend running at http://localhost:3000' -ForegroundColor Green
npm run dev 2>&1 | Tee-Object -FilePath '$logDir\frontend.log'
"@

Start-ServiceWindow -Name "Frontend" -WorkingDirectory $frontendPath -Command $frontendCommand -PidFile $frontendPidFile

Write-Host "   Waiting for frontend..." -ForegroundColor Gray
if (Wait-ForHttp -Url "http://localhost:3000" -TimeoutSeconds 60) {
    Write-Host "   Frontend is ready." -ForegroundColor Green
} else {
    Write-Host "   Frontend did not become ready. Check logs\frontend.log." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services started" -ForegroundColor Green
Write-Host "  Redis    : localhost:6379" -ForegroundColor White
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Logs     : $logDir" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
