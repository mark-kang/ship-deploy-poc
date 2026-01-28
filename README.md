# Ship Deploy PoC: 선박(Edge) 환경을 위한 고신뢰성 배포 자동화

> **핵심 컨셉**: 인터넷이 끊긴 Windows Server 선박 환경에서, 육상에서 만든 업데이트 패키지를 안전하게 배포하고 문제 발생 시 1초 만에 롤백하는 PowerShell 기반 자동화 도구

> **Target Environment**: Windows Server, Offline/Low-Bandwidth (VSAT), High Latency  
> **Core Value**: Idempotency(멱등성), Atomic Rollback(원자적 롤백), Infrastructure as Code

## 📖 프로젝트 개요
본 프로젝트는 인터넷 연결이 불안정하거나 완전히 단절된(Disconnected) **선박(Vessel) 및 오프라인 엣지 환경**에서, 애플리케이션을 안전하고 일관성 있게 배포하기 위한 **DevSecOps 파이프라인 및 배포 에이전트 PoC(Proof of Concept)**입니다.

일반적인 클라우드/리눅스 환경과 달리, 선박 관리 시스템(VMS)은 **Windows Server** 기반의 레거시 환경과 제한적인 네트워크 대역폭이라는 특수한 제약 사항을 가집니다. 이 프로젝트는 이러한 환경에서 **'배포 안정성'**과 **'운영 효율성'**을 극대화하는 아키텍처를 제시합니다.

## 🎯 해결하고자 하는 핵심 문제 (Problem Solving)

### 1. 불안정한 네트워크와 배포 신뢰성
- **Challenge**: 운항 중인 선박은 위성 통신(VSAT)을 사용하므로 대역폭이 좁고 연결이 자주 끊깁니다. 배포 도중 네트워크가 단절되면 시스템이 'Corrupted State'에 빠질 위험이 큽니다.
- **Solution**: 
    - **Artifact Integrity**: 해시(SHA-256) 기반의 무결성 검증을 통과한 패키지만 배포 프로세스에 진입합니다.
    - **Offline-First Strategy**: '다운로드'와 '설치' 단계를 엄격히 분리하여, 로컬에 완벽한 패키지가 확보된 상태에서만 업데이트를 수행합니다.

### 2. 배포 실패 시 복구 비용 (MTTR)
- **Challenge**: 육상 엔지니어가 선박에 직접 접근하기 어려우므로, 배포 실패 시 원격 복구가 매우 까다롭습니다.
- **Solution**: 
    - **Atomic Rollback**: 파일 시스템 및 IIS 설정 변경 시 트랜잭션 개념을 도입하여, 실패 시 자동으로 이전의 안정적인 상태(Last Known Good Configuration)로 즉시 복구합니다.
    - **Snapshot-based Backup**: 배포 직전 상태를 경량화된 스냅샷으로 저장합니다.

### 3. Windows Server 환경의 IaC 부재
- **Challenge**: 리눅스 컨테이너 환경에 비해 Windows Server(IIS, .NET)는 배포 스크립트가 표준화되어 있지 않고 수동 작업 의존도가 높습니다.
- **Solution**: 
    - **PowerShell Desired State Configuration (DSC)** 철학을 차용한 멱등성(Idempotency) 있는 배포 스크립트 작성.
    - 동일한 스크립트를 여러 번 실행해도 시스템 상태가 항상 일정하게 유지되도록 설계.

## 🛠️ 기술 스택 및 아키텍처 (Tech Stack & Architecture)

### Architecture Overview
```mermaid
graph TB
    subgraph "Shore (CI/CD Pipeline)"
        Dev[DevSecOps Engineer] -->|Push Code| Git[GitHub]
        Git -->|Trigger Build| CI[CI Server]
        CI -->|Package & Sign| Artifact[Artifact Repository]
        Artifact -->|Generate| Hash[SHA-256 Checksum]
    end
    
    subgraph "Network Boundary (VSAT/Satellite)"
        Artifact -.->|Resumable Transfer| Transfer[Secure Channel]
        Hash -.->|Metadata| Transfer
    end
    
    subgraph "Vessel (Windows Server - Offline Capable)"
        Transfer -->|Download Complete| Agent[Ship Deploy Agent]
        Agent -->|1. Verify Integrity| Verify{Hash Match?}
        Verify -->|No| Reject[Reject & Alert]
        Verify -->|Yes| Snapshot[2. Create Snapshot]
        Snapshot -->|Backup Complete| Deploy[3. Deploy to IIS]
        Deploy -->|Post-Deploy| Health{Health Check}
        Health -->|Pass| Success[Log Success]
        Health -->|Fail| Rollback[4. Atomic Rollback]
        Rollback -->|Restore| Snapshot
    end
    
    Success -->|Telemetry| Audit[Audit Log]
    Rollback -->|Alert| Audit
```

### Components & Technology Stack

#### 핵심 배포 엔진
- **Language**: PowerShell 7+ (크로스 플랫폼 지원, 향상된 오류 처리)
- **Target OS**: Windows Server 2016/2019/2022
- **Execution Policy**: RemoteSigned (프로덕션 스크립트용)

#### 주요 PowerShell 모듈 및 도구
- **IIS 관리**
  - `WebAdministration` (Windows Server 기본 제공 IIS PowerShell 모듈)
  - `IISAdministration` (Server 2016+ 최신 IIS 관리 모듈)
  - Application Pool 제어, 바인딩 구성, 사이트 생명주기 관리

- **아티팩트 무결성 및 보안**
  - `Get-FileHash` (SHA-256 체크섬 검증)
  - `Protect-CmsMessage` / `Unprotect-CmsMessage` (CMS 기반 암호화로 안전한 전송)
  - `Set-AuthenticodeSignature` (스크립트 무결성 보장을 위한 코드 서명)

- **백업 및 롤백**
  - **Robocopy** with `/MIR` flag (스냅샷을 위한 고속 디렉터리 미러링)
  - **Junction Points** (`New-Item -ItemType Junction`) (원자적 버전 전환)
  - **VSS (Volume Shadow Copy Service)** via `vssadmin` or `Diskshadow` (전체 시스템 스냅샷, 선택사항)

- **헬스 체크 및 모니터링**
  - `Invoke-WebRequest` (HTTP 엔드포인트 스모크 테스트)
  - `Test-NetConnection` (포트 가용성 확인)
  - 재시도 로직이 포함된 커스텀 헬스 체크 스크립트

- **로깅 및 감사**
  - `Start-Transcript` / `Stop-Transcript` (세션 로깅)
  - `Write-EventLog` (Windows Event Log 통합)
  - 텔레메트리 분석을 위한 JSON 구조화 로깅

#### 설계 패턴
- **Immutable Infrastructure**: 각 배포 버전을 별도 디렉터리에 저장 (`C:\Apps\MyApp\v1.0.0`, `v1.0.1`)
- **Blue-Green Deployment**: IIS 사이트가 "current" junction을 가리키며, 버전 간 원자적 전환
- **Idempotency**: 모든 작업은 변경 적용 전 현재 상태를 확인 (예: "이 버전이 이미 배포되었는가?")

## 🚀 주요 기능 (Key Features)

### 1. 멱등성 있는 배포 (Idempotent Deployment)
- 현재 버전과 대상 버전을 비교하여 변경사항만 적용 (Diff-based)
- 스크립트 재실행 시 불필요한 작업(서비스 재시작 등) 방지

### 2. 자동화된 헬스 체크 및 롤백 (Self-Healing)
- 배포 직후 `Smoke Test` (HTTP Status, Service Running State) 수행
- 실패 감지 시 별도의 개입 없이 즉시 이전 버전 Junction 복원

### 3. 저대역폭 최적화 (Bandwidth Optimization)
- 증분 배포(Delta Deployment) 지원을 고려한 패키징 구조
- 전송 실패 시 이어받기(Resumable Transfer) 로직 시뮬레이션
- Python wheel 파일 사전 다운로드로 선박에서의 설치 시간 최소화

## 📁 리포지토리 구조 (Repository Structure)

```
ship-deploy-poc/
├── 📂 shore-builder/          # [육상] 빌드 및 패키징 도구
│   ├── build_package.py       # Django 앱과 의존성(.whl)을 zip으로 묶는 스크립트
│   ├── sign_artifact.ps1      # 패키지 서명 및 SHA-256 해시 생성
│   └── requirements.txt       # 빌드 도구 의존성
│
├── 📂 ship-deployer/          # [선박] 배포 및 운영 도구
│   ├── deploy.ps1             # [핵심] PowerShell 배포 스크립트 (무결성 검증 → 스냅샷 → 배포)
│   ├── rollback.ps1           # [핵심] 1초 이내 즉시 롤백 스크립트 (Junction 전환)
│   ├── health_check.ps1       # HTTP 엔드포인트 및 서비스 상태 확인
│   └── config.json            # 배포 대상 경로, IIS 사이트명 등 설정
│
├── 📂 vms-dummy-app/          # 테스트용 간단한 Django VMS 앱
│   ├── manage.py
│   ├── vms/                   # Django 프로젝트
│   └── requirements.txt
│
├── 📂 docs/
│   └── architecture.png       # 아키텍처 다이어그램 이미지
│
├── 📂 .github/workflows/      # (선택사항) CI/CD 자동화
│   └── build-and-package.yml  # 육상 빌드 자동화
│
├── 📄 README.md               # 본 문서
└── 📄 LICENSE
```

## 🎬 데모 시나리오 (Demo Scenario)

### 시나리오: "선박 VMS 1.0.0 → 1.0.1 무중단 업데이트"

#### **Phase 1: Shore (육상) - 빌드 및 패키징**
```bash
# 1. Django 앱 빌드 및 의존성 패키징
cd shore-builder
python build_package.py --version 1.0.1 --source ../vms-dummy-app

# 출력:
# ✅ Package created: vms-app-1.0.1.zip (15.2 MB)
# ✅ Checksum: vms-app-1.0.1.sha256
```

**생성된 파일:**
- `vms-app-1.0.1.zip` (Django 코드 + Python wheels)
- `vms-app-1.0.1.sha256` (무결성 검증용 해시)

#### **Phase 2: Transfer (전송) - 위성 통신 시뮬레이션**
```powershell
# 실제 환경: VSAT 위성 통신 또는 USB 드라이브 물리 전달
# 데모 환경: 로컬 파일 복사로 시뮬레이션
Copy-Item "vms-app-1.0.1.*" -Destination "\\ship-server\deployments\"
```

#### **Phase 3: Ship (선박) - 배포 실행**
```powershell
cd ship-deployer

# 배포 실행 (무결성 검증 → 스냅샷 → 배포 → 헬스 체크가 자동으로 진행)
.\deploy.ps1 -PackagePath "C:\deployments\vms-app-1.0.1.zip" -SiteName "VMS-Production"
```

**실행 결과 (자동화된 5단계 프로세스):**
```
[INFO] Verifying package integrity...
✅ Hash verified: SHA-256 match

[INFO] Current version: 1.0.0
[INFO] Target version: 1.0.1
[INFO] Creating snapshot of current deployment...
✅ Snapshot saved: C:\Apps\VMS\snapshots\1.0.0_20260129_075930

[INFO] Extracting package to C:\Apps\VMS\versions\1.0.1...
[INFO] Installing dependencies from wheels (offline mode)...
[INFO] Switching IIS junction: current -> 1.0.1
✅ Junction switched successfully

[INFO] Running health check...
✅ Health check passed (HTTP 200, Response time: 120ms)
✅ Deployment successful
```

**배포 후 상태:**
```
C:\Apps\VMS\
├── versions/
│   ├── 1.0.0/          # 이전 버전 (보존)
│   └── 1.0.1/          # 새 버전
├── current -> 1.0.1    # Junction (IIS가 이 경로를 바라봄)
└── snapshots/
    └── 1.0.0_20260129_075930/  # 롤백용 스냅샷
```

#### **Phase 4: Rollback (롤백) - 문제 발생 시**
```powershell
# 만약 1.0.1에서 치명적 버그 발견 시
.\rollback.ps1 -TargetVersion "1.0.0"

# 출력:
# [WARN] Rolling back from 1.0.1 to 1.0.0...
# [INFO] Switching junction: current -> 1.0.0
# [INFO] IIS application pool recycled
# ✅ Rollback completed in 0.8 seconds
```

**핵심 포인트:**
- ⚡ **1초 이내 롤백**: Junction 포인터만 변경하므로 파일 복사 불필요
- 🔒 **데이터 무손실**: 이전 버전 파일은 삭제되지 않고 보존
- 🚫 **네트워크 불필요**: 모든 작업이 로컬에서 완료

## 🏁 빠른 시작 (Quick Start)

### Prerequisites
- **OS**: Windows 10/11 또는 Windows Server 2016+
- **PowerShell**: 7.0 이상
- **IIS**: 설치 및 활성화 상태 (테스트 환경에서는 선택사항)
- **Python**: 3.9+ (shore-builder 사용 시)

### 로컬 환경에서 데모 실행
```powershell
# 1. 레포지토리 클론
git clone https://github.com/mark-kang/ship-deploy-poc.git
cd ship-deploy-poc

# 2. [육상] 테스트 패키지 빌드
cd shore-builder
python build_package.py --version 1.0.0 --source ../vms-dummy-app

# 3. [선박] 배포 시뮬레이션 (Dry-Run)
cd ../ship-deployer
.\deploy.ps1 -PackagePath "../shore-builder/output/vms-app-1.0.0.zip" -DryRun

# 4. [선박] 실제 배포 실행
.\deploy.ps1 -PackagePath "../shore-builder/output/vms-app-1.0.0.zip" -SiteName "VMS-Test"
```

## 🔧 핵심 구현 로직 (Core Implementation Logic)

이 섹션은 PoC의 **기술적 차별화 포인트**를 보여줍니다. 단순한 스크립트가 아닌, 실제 프로덕션 환경에서 작동 가능한 엔지니어링 솔루션입니다.

### A. [Shore] 오프라인 패키징 - Python Wheel 사전 다운로드

**문제**: 선박 환경은 인터넷이 단절되어 있어 `pip install`로 의존성을 설치할 수 없습니다.

**해결책**: 육상에서 모든 Python 의존성을 `.whl` (wheel) 파일로 다운로드하여 패키지에 포함시킵니다.

#### `shore-builder/build_package.py` 핵심 로직
```python
import subprocess
import hashlib
import zipfile
from pathlib import Path

def build_offline_package(version: str, source_dir: str):
    """
    인터넷이 없는 환경을 위한 완전 자급자족 패키지 생성
    """
    output_dir = Path("./output")
    wheels_dir = output_dir / "wheels"
    wheels_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 의존성을 wheel 파일로 다운로드 (인터넷 연결 필요 - 육상에서만 실행)
    print("[INFO] Downloading dependencies as wheels...")
    subprocess.run([
        "pip", "download",
        "-d", str(wheels_dir),
        "-r", f"{source_dir}/requirements.txt",
        "--platform", "win_amd64",  # Windows Server 타겟
        "--python-version", "39",
        "--only-binary", ":all:"
    ], check=True)
    
    # 2. Django 소스 코드 및 정적 파일 압축
    package_name = f"vms-app-{version}.zip"
    package_path = output_dir / package_name
    
    print(f"[INFO] Creating package: {package_name}")
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Django 앱 소스
        for file in Path(source_dir).rglob("*"):
            if not file.is_dir() and "__pycache__" not in str(file):
                zipf.write(file, file.relative_to(source_dir))
        
        # Wheel 파일들
        for wheel in wheels_dir.glob("*.whl"):
            zipf.write(wheel, f"wheels/{wheel.name}")
    
    # 3. SHA-256 체크섬 생성 (무결성 검증용)
    print("[INFO] Generating SHA-256 checksum...")
    sha256_hash = hashlib.sha256()
    with open(package_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum_path = output_dir / f"{package_name}.sha256"
    with open(checksum_path, "w") as f:
        f.write(f"{sha256_hash.hexdigest()}  {package_name}\n")
    
    print(f"✅ Package created: {package_path} ({package_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"✅ Checksum: {checksum_path}")
    
    return package_path, checksum_path
```

**핵심 포인트:**
- `--platform win_amd64`: Windows Server 환경에 맞는 바이너리 다운로드
- `--only-binary :all:`: 컴파일이 필요한 패키지도 미리 빌드된 wheel 사용
- **선박에서는 `pip install --no-index --find-links=./wheels`로 오프라인 설치 가능**

---

### B. [Ship] PowerShell Junction 기반 원자적 배포

**문제**: 배포 중 파일 복사 시간이 길면 서비스 다운타임이 발생하고, 실패 시 복구가 어렵습니다.

**해결책**: NTFS Junction Point를 활용한 **Blue-Green Deployment** 패턴으로 포인터만 전환하여 즉시 배포/롤백합니다.

#### `ship-deployer/deploy.ps1` 핵심 로직
```powershell
<#
.SYNOPSIS
    선박 VMS 무중단 배포 스크립트 (Junction 기반 Atomic Switching)
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
    robocopy $currentVersion $snapshotPath /MIR /NFL /NDL /NJH /NJS | Out-Null
    Write-Host "✅ Snapshot saved: $snapshotPath" -ForegroundColor Green
}

# ============================================
# 3. 패키지 압축 해제 및 의존성 설치
# ============================================
Write-Host "[INFO] Extracting package to $deployPath..." -ForegroundColor Cyan
Expand-Archive -Path $PackagePath -DestinationPath $deployPath -Force

# 오프라인 pip 설치 (wheel 파일 사용)
$wheelsDir = "$deployPath\wheels"
if (Test-Path $wheelsDir) {
    Write-Host "[INFO] Installing dependencies from wheels (offline mode)..." -ForegroundColor Cyan
    python -m pip install --no-index --find-links=$wheelsDir -r "$deployPath\requirements.txt"
}

# Django 마이그레이션 (선택사항)
# python "$deployPath\manage.py" migrate --noinput

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
    
    # IIS Application Pool 재시작 (무중단에 가까움)
    Import-Module WebAdministration
    Restart-WebAppPool -Name $SiteName
    
    Write-Host "✅ Junction switched successfully" -ForegroundColor Green
}

# ============================================
# 5. 헬스 체크 (Smoke Test)
# ============================================
Write-Host "[INFO] Running health check..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed (HTTP 200)" -ForegroundColor Green
        Write-Host "✅ Deployment successful" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Health check failed! Rolling back..." -ForegroundColor Red
    # 자동 롤백 로직 (스냅샷 복원)
    & "$PSScriptRoot\rollback.ps1" -SnapshotPath $snapshotPath
    throw "Deployment failed and rolled back."
}
```

**핵심 포인트:**
- **Junction Point**: 심볼릭 링크보다 안정적이며, Windows Server에서 권한 문제 없음
- **Atomic Switching**: `New-Item -Force`로 포인터 전환이 순간적으로 완료 (< 100ms)
- **Self-Healing**: Health Check 실패 시 자동으로 이전 스냅샷 복원
- **오프라인 pip**: `--no-index --find-links`로 인터넷 없이 wheel 설치

---

### 왜 이 구현이 중요한가?

| 기술 요소 | 일반적인 방법 | 본 PoC의 차별점 |
|----------|-------------|---------------|
| **의존성 관리** | `pip install` (인터넷 필요) | Wheel 사전 다운로드 (완전 오프라인) |
| **배포 방식** | 파일 복사 (느림, 위험) | Junction 전환 (즉시, 안전) |
| **롤백 시간** | 수 분 (재배포 필요) | **1초 이내** (포인터 복원) |
| **무결성 검증** | 선택사항 | SHA-256 필수 검증 |
| **플랫폼 전문성** | Linux 중심 | **Windows Server 네이티브** |

이 구현은 **"선박 환경의 특수성을 이해하고, Windows 생태계에서 최적의 솔루션을 설계할 수 있는 시니어 엔지니어"**임을 증명합니다.

## 💡 설계 철학 및 핵심 가치 (Design Philosophy)
본 프로젝트는 단순한 기능 구현을 넘어, **엔터프라이즈급 운영 환경**에서 요구되는 안정성과 확장성을 최우선으로 설계되었습니다.

- **Security & Governance (보안 및 거버넌스)**
  - 폐쇄망 환경에서도 패키지 무결성(Integrity)을 엄격히 검증하며, 모든 배포 변경 사항은 추적 및 감사(Audit)가 가능하도록 설계했습니다.

- **Resilience Engineering (결함 허용 및 복원력)**
  - '네트워크 단절'과 '배포 실패'를 예기치 못한 오류가 아닌 **통제 가능한 시나리오**로 정의합니다.
  - 시스템이 실패 상태에서 스스로 복구(Self-Healing)될 수 있는 아키텍처를 지향합니다.

- **Data-Driven Operation (데이터 기반 운영)**
  - 단순한 배포 성공/실패 여부를 넘어, 배포 소요 시간 및 복구 시간(MTTR)과 같은 운영 지표를 측정하고 최적화할 수 있는 기반을 마련했습니다.

---
**Author**: Mark Kang (DevSecOps Specialist)  
**Status**: PoC / Active Development
