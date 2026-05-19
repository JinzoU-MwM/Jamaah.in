# =============================================================================
# Auto Deploy Script - Push ke GitHub + Deploy ke VPS
# Usage: .\deploy\auto-deploy.ps1 [-SkipPush] [-SkipBuild] [-Message "custom commit msg"]
# =============================================================================

param(
    [switch]$SkipPush,
    [switch]$SkipBuild,
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$VpsHost = "jni-server"
$VpsProjectDir = "/data/docker/jamaah.in"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Auto Deploy - Jamaah.in" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1: Git commit & push
# ---------------------------------------------------------------------------
if (-not $SkipPush) {
    Write-Host "[1/4] Git commit & push..." -ForegroundColor Yellow

    $status = git status --porcelain
    if ($status) {
        if (-not $Message) {
            $branch = git rev-parse --abbrev-ref HEAD
            $Message = "deploy: auto-deploy from $branch"
        }

        git add -A
        git commit -m $Message
        Write-Host "  Commit: $Message" -ForegroundColor Green
    }
    else {
        Write-Host "  No changes to commit" -ForegroundColor Gray
    }

    Write-Host "  Pushing to origin..." -ForegroundColor Gray
    git push origin main
    Write-Host "  Push OK" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "[1/4] Skipping git push (--SkipPush)" -ForegroundColor Gray
}

# ---------------------------------------------------------------------------
# Step 2: SSH pull latest code on VPS
# ---------------------------------------------------------------------------
Write-Host "[2/4] Pulling latest code on VPS..." -ForegroundColor Yellow
ssh $VpsHost "cd $VpsProjectDir && git pull --ff-only origin main"
Write-Host "  Pull OK" -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------------------------------
# Step 3: Build & restart Docker containers
# ---------------------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "[3/4] Rebuilding Docker images..." -ForegroundColor Yellow

    Write-Host "  Building backend..." -ForegroundColor Gray
    ssh $VpsHost "cd $VpsProjectDir && docker compose build backend 2>&1 | tail -1"
    Write-Host "  Backend build OK" -ForegroundColor Green

    Write-Host "  Building frontend..." -ForegroundColor Gray
    ssh $VpsHost "cd $VpsProjectDir && docker compose build frontend 2>&1 | tail -1"
    Write-Host "  Frontend build OK" -ForegroundColor Green

    Write-Host "  Restarting containers..." -ForegroundColor Gray
    ssh $VpsHost "cd $VpsProjectDir && docker compose up -d --force-recreate backend frontend 2>&1 | Select-String -Pattern 'Container|Started|Healthy'" 2>$null
    # Fallback if Select-String doesn't work over SSH
    ssh $VpsHost "cd $VpsProjectDir && docker compose up -d --force-recreate backend frontend"
    Write-Host "  Containers restarted" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "[3/4] Skipping build (--SkipBuild)" -ForegroundColor Gray
}

# ---------------------------------------------------------------------------
# Step 4: Health checks
# ---------------------------------------------------------------------------
Write-Host "[4/4] Health checks..." -ForegroundColor Yellow

# Wait for containers to be ready
Start-Sleep -Seconds 5

# Backend health
$health = ssh $VpsHost "curl -s http://127.0.0.1:8006/health"
if ($health -match "healthy") {
    Write-Host "  Backend:  OK ($health)" -ForegroundColor Green
}
else {
    Write-Host "  Backend:  FAIL" -ForegroundColor Red
}

# Frontend
$frontendStatus = ssh $VpsHost "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8005/"
if ($frontendStatus -eq "200") {
    Write-Host "  Frontend: OK (HTTP $frontendStatus)" -ForegroundColor Green
}
else {
    Write-Host "  Frontend: FAIL (HTTP $frontendStatus)" -ForegroundColor Red
}

# Docker container status
Write-Host ""
Write-Host "  Container status:" -ForegroundColor Gray
ssh $VpsHost "docker ps --format 'table {{.Names}}\t{{.Status}}' --filter 'name=jamaah'"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Deploy Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
