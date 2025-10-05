param (
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"

Write-Host "[bootstrap] Initialising converter workspace" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

function Assert-Command {
    param (
        [string]$Name,
        [string]$InstallHint
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. $InstallHint"
    }
}

Assert-Command -Name "python" -InstallHint "Install Python 3.11 and ensure it is on PATH."
Assert-Command -Name "node" -InstallHint "Install Node.js 20+ from https://nodejs.org/."
Assert-Command -Name "docker" -InstallHint "Install Docker Desktop and enable Docker Compose."

# Ensure Poetry is available in a local bootstrap venv
if (-not (Test-Path ".bootstrap")) {
    python -m venv .bootstrap
}
$bootstrapPython = if ($IsWindows) { Join-Path (Resolve-Path ".bootstrap").Path "Scripts\python.exe" } else { Join-Path (Resolve-Path ".bootstrap").Path "bin/python" }
& $bootstrapPython -m pip install --upgrade pip setuptools wheel
& $bootstrapPython -m pip install "poetry==1.8.2"

function Install-PoetryProject {
    param (
        [string]$ProjectPath
    )
    Push-Location $ProjectPath
    try {
        & $bootstrapPython -m poetry install --no-root
        $envPath = (& $bootstrapPython -m poetry env info --path).Trim()
        if (-not $envPath) {
            throw "Failed to resolve poetry environment for $ProjectPath"
        }
        if ($IsWindows) {
            return Join-Path $envPath "Scripts\python.exe"
        } else {
            return Join-Path $envPath "bin/python"
        }
    } finally {
        Pop-Location
    }
}

Write-Host "[bootstrap] Installing API dependencies" -ForegroundColor Yellow
$apiPython = Install-PoetryProject -ProjectPath (Join-Path $repoRoot "apps/api")

Write-Host "[bootstrap] Installing worker dependencies" -ForegroundColor Yellow
$workerPython = Install-PoetryProject -ProjectPath (Join-Path $repoRoot "workers")

# Frontend bootstrap
Write-Host "[bootstrap] Ensuring pnpm is available" -ForegroundColor Yellow
$pnpmRoot = Join-Path $repoRoot '.pnpm'
if (-not (Test-Path $pnpmRoot)) {
    New-Item -ItemType Directory -Force -Path $pnpmRoot | Out-Null
}
$pnpmBin = if ($IsWindows) { Join-Path $pnpmRoot 'node_modules\.bin\pnpm.cmd' } else { Join-Path $pnpmRoot 'node_modules/.bin/pnpm' }
if (-not (Test-Path $pnpmBin)) {
    Write-Host "[bootstrap] Installing pnpm locally" -ForegroundColor Yellow
    npm install pnpm@9.1.2 --prefix $pnpmRoot --no-save | Out-Null
} else {
    Write-Host "[bootstrap] Reusing pnpm from $pnpmBin" -ForegroundColor Yellow
}

Write-Host "[bootstrap] Installing web dependencies" -ForegroundColor Yellow
Push-Location (Join-Path $repoRoot 'apps/web')
try {
    & $pnpmBin install
} finally {
    Pop-Location
}

if (-not $SkipDocker) {
    Write-Host "[bootstrap] Pulling containers" -ForegroundColor Yellow
    docker compose pull postgres redis ollama 2>$null

    Write-Host "[bootstrap] Starting infrastructure containers" -ForegroundColor Yellow
    docker compose up -d postgres redis ollama
}

Write-Host "[bootstrap] Launching dev servers" -ForegroundColor Yellow
Start-Job -ScriptBlock {
    Set-Location $using:repoRoot
    & $using:apiPython -m uvicorn app.main:app --reload --app-dir apps/api --host 0.0.0.0 --port 8000
} | Out-Null

Start-Job -ScriptBlock {
    Set-Location $using:repoRoot
    & $using:workerPython -m celery -A workers.worker worker --loglevel=INFO
} | Out-Null

Start-Job -ScriptBlock {
    Set-Location (Join-Path $using:repoRoot 'apps/web')
    & $using:pnpmBin dev --host 0.0.0.0 --port 5173
} | Out-Null

Write-Host "[bootstrap] Jobs started. Use 'Get-Job' to inspect and 'Stop-Job' to terminate." -ForegroundColor Green
Write-Host "[bootstrap] Visit http://localhost:5173 for the dashboard." -ForegroundColor Green
