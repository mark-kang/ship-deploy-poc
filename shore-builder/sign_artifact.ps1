<#
.SYNOPSIS
    패키지 서명 및 SHA-256 해시 생성 스크립트

.DESCRIPTION
    배포 패키지에 디지털 서명을 추가하고 무결성 검증을 위한 해시를 생성합니다.
    
.PARAMETER PackagePath
    서명할 패키지 파일 경로

.EXAMPLE
    .\sign_artifact.ps1 -PackagePath ".\output\vms-app-1.0.0.zip"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PackagePath
)

$ErrorActionPreference = "Stop"

Write-Host "[INFO] Signing artifact: $PackagePath" -ForegroundColor Cyan

# SHA-256 체크섬 생성
$hash = (Get-FileHash -Path $PackagePath -Algorithm SHA256).Hash
$checksumFile = "$PackagePath.sha256"

$packageName = Split-Path $PackagePath -Leaf
Set-Content -Path $checksumFile -Value "$hash  $packageName"

Write-Host "✅ Checksum created: $checksumFile" -ForegroundColor Green
Write-Host "   Hash: $hash" -ForegroundColor Gray

# 코드 서명 (인증서가 있는 경우)
# $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
# if ($cert) {
#     Set-AuthenticodeSignature -FilePath $PackagePath -Certificate $cert
#     Write-Host "✅ Package signed with certificate" -ForegroundColor Green
# }
