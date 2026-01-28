<#
.SYNOPSIS
    HTTP 헬스 체크 스크립트

.DESCRIPTION
    배포된 애플리케이션의 HTTP 엔드포인트 상태를 확인합니다.

.PARAMETER Url
    체크할 URL (기본값: http://localhost)

.PARAMETER TimeoutSec
    타임아웃 시간 (기본값: 10초)

.EXAMPLE
    .\health_check.ps1 -Url "http://localhost:8000/health"
#>

param(
    [string]$Url = "http://localhost",
    [int]$TimeoutSec = 10
)

$ErrorActionPreference = "Stop"

Write-Host "[INFO] Health check: $Url" -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed (HTTP $($response.StatusCode))" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "❌ Health check failed (HTTP $($response.StatusCode))" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
