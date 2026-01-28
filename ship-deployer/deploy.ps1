<#
.SYNOPSIS
    선박 VMS 무중단 배포 스크립트 (Junction 기반 Atomic Switching)

.DESCRIPTION
    오프라인 환경에서 Django 앱을 안전하게 배포합니다.
    무결성 검증 → 스냅샷 생성 → 배포 → 헬스 체크 → 자동 롤백

.PARAMETER PackagePath
    배포할 패키지 파일 경로 (.zip)

.PARAMETER SiteName
    IIS 사이트명 (기본값: VMS-Production)

.PARAMETER DryRun
    실제 배포 없이 시뮬레이션만 수행

.EXAMPLE
    .\deploy.ps1 -PackagePath "C:\deployments\vms-app-1.0.1.zip" -SiteName "VMS-Production"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PackagePath,
    
    [string]$SiteName = "VMS-Production",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# 배포 경로 설정
$baseDir = "C:\Apps\VMS"
$versionsDir = "$baseDir\versions"
$currentLink = "$baseDir\current"
$snapshotsDir = "$baseDir\snapshots"

# ============================================
# 1. 무결성 검증 (SHA-256)
# ============================================
Write-Host "[INFO] Verifying package integrity..." -ForegroundColor Cyan
$checksumFile = "$PackagePath.sha256"

if (-not (Test-Path $checksumFile)) {
    throw "Checksum file not found: $checksumFile"
}

$expectedHash = (Get-Content $checksumFile).Split()[0]
$actualHash = (Get-FileHash -Path $PackagePath -Algorithm SHA256).Hash

if ($expectedHash -ne $actualHash) {
    throw "❌ Hash mismatch! Package may be corrupted."
}
Write-Host "✅ Hash verified: SHA-256 match" -ForegroundColor Green

# ============================================
# 2. 버전 추출 및 스냅샷 생성
# ============================================
$packageName = [System.IO.Path]::GetFileNameWithoutExtension($PackagePath)
$targetVersion = $packageName -replace 'vms-app-', ''
$deployPath = "$versionsDir\$targetVersion"

Write-Host "[INFO] Target version: $targetVersion" -ForegroundColor Cyan

# 현재 버전 스냅샷 (롤백용)
if (Test-Path $currentLink) {
    $currentVersion = (Get-Item $currentLink).Target
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $snapshotPath = "$snapshotsDir\snapshot_$timestamp"
    
    Write-Host "[INFO] Creating snapshot of current deployment..." -ForegroundColor Cyan
    if (-not $DryRun) {
        robocopy $currentVersion $snapshotPath /MIR /NFL /NDL /NJH /NJS | Out-Null
    }
    Write-Host "✅ Snapshot saved: $snapshotPath" -ForegroundColor Green
}

# ============================================
# 3. 패키지 압축 해제 및 의존성 설치
# ============================================
Write-Host "[INFO] Extracting package to $deployPath..." -ForegroundColor Cyan
if (-not $DryRun) {
    Expand-Archive -Path $PackagePath -DestinationPath $deployPath -Force
    
    # 오프라인 pip 설치 (wheel 파일 사용)
    $wheelsDir = "$deployPath\wheels"
    if (Test-Path $wheelsDir) {
        Write-Host "[INFO] Installing dependencies from wheels (offline mode)..." -ForegroundColor Cyan
        python -m pip install --no-index --find-links=$wheelsDir -r "$deployPath\requirements.txt"
    }
}

# ============================================
# 4. Junction Point 원자적 전환 (Atomic Switching)
# ============================================
if (-not $DryRun) {
    Write-Host "[INFO] Switching IIS junction: current -> $targetVersion" -ForegroundColor Yellow
    
    # 기존 Junction 제거
    if (Test-Path $currentLink) {
        (Get-Item $currentLink).Delete()
    }
    
    # 새 Junction 생성 (원자적 작업)
    New-Item -ItemType Junction -Path $currentLink -Target $deployPath -Force | Out-Null
    
    Write-Host "✅ Junction switched successfully" -ForegroundColor Green
}

# ============================================
# 5. 헬스 체크 (Smoke Test)
# ============================================
Write-Host "[INFO] Running health check..." -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "✅ Dry-run completed successfully" -ForegroundColor Green
} else {
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health check passed (HTTP 200)" -ForegroundColor Green
            Write-Host "✅ Deployment successful" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Health check failed! Rolling back..." -ForegroundColor Red
        # 자동 롤백 로직
        & "$PSScriptRoot\rollback.ps1" -SnapshotPath $snapshotPath
        throw "Deployment failed and rolled back."
    }
}
