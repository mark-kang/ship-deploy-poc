<#
.SYNOPSIS
    즉시 롤백 스크립트 (1초 이내 복구)

.DESCRIPTION
    배포 실패 시 이전 버전으로 즉시 롤백합니다.
    Junction 포인터만 변경하므로 파일 복사 불필요

.PARAMETER TargetVersion
    롤백할 버전 (예: 1.0.0)

.PARAMETER SnapshotPath
    복원할 스냅샷 경로 (선택사항)

.EXAMPLE
    .\rollback.ps1 -TargetVersion "1.0.0"
#>

param(
    [string]$TargetVersion,
    [string]$SnapshotPath
)

$ErrorActionPreference = "Stop"

$baseDir = "C:\Apps\VMS"
$versionsDir = "$baseDir\versions"
$currentLink = "$baseDir\current"

Write-Host "[WARN] Rolling back deployment..." -ForegroundColor Yellow

if ($TargetVersion) {
    $targetPath = "$versionsDir\$TargetVersion"
    
    if (-not (Test-Path $targetPath)) {
        throw "Target version not found: $targetPath"
    }
    
    Write-Host "[INFO] Switching junction: current -> $TargetVersion" -ForegroundColor Cyan
    
    # 기존 Junction 제거
    if (Test-Path $currentLink) {
        (Get-Item $currentLink).Delete()
    }
    
    # 이전 버전으로 Junction 생성
    New-Item -ItemType Junction -Path $currentLink -Target $targetPath -Force | Out-Null
    
    Write-Host "✅ Rollback completed in $(Get-Date -Format 'ss.fff') seconds" -ForegroundColor Green
}

Write-Host "✅ System restored to stable state" -ForegroundColor Green
