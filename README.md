# Ship Deploy PoC: 선박(Edge) 환경을 위한 고신뢰성 배포 자동화

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
graph LR
    User[DevSecOps Engineer] -->|Push Code| Git[GitHub Enterprise]
    Git -->|CI Build| Artifact[Build Server]
    
    subgraph "High Latency Network (Satellite)"
    Artifact -->|Secure Transfer| ShipAgent[Ship Deploy Agent]
    end
    
    subgraph "Vessel (Windows Server)"
    ShipAgent -->|Verify & Backup| Backup[Snapshot]
    ShipAgent -->|Deploy| IIS[IIS / App Service]
    IIS -- Fail -->|Auto Rollback| Backup
    IIS -- Success -->|Log| Audit[Deployment Log]
    end
```

### Components
- **Language**: PowerShell 7+ (Core logic), Python (Optional for cross-platform agent logic)
- **Target OS**: Windows Server 2016/2019/2022
- **Key Libraries**: 
    - WinDeployment (Proprietary/Custom Module for IIS Control)
    - FileSystemWatcher (Monitoring)
- **Concept**: Immutable Infrastructure (Simulated via folder versioning)

## 🚀 주요 기능 (Key Features)

### 1. 멱등성 있는 배포 (Idempotent Deployment)
- 현재 버전과 대상 버전을 비교하여 변경사항만 적용 (Diff-based).
- 스크립트 재실행 시 불필요한 작업(서비스 재시작 등) 방지.

### 2. 자동화된 헬스 체크 및 롤백 (Self-Healing)
- 배포 직후 `Smoke Test` (HTTP Status, Service Running State) 수행.
- 실패 감지 시 별도의 개입 없이 즉시 이전 버전 심볼릭 링크(Junction) 복원.

### 3. 저대역폭 최적화 (Bandwidth Optimization)
- 증분 배포(Delta Deployment) 지원을 고려한 패키징 구조.
- 전송 실패 시 이어받기(Resumable Transfer) 로직 시뮬레이션.

## 🏁 시작하기 (Getting Started)

### Prerequisites
- Windows 10/11 or Windows Server
- PowerShell 7.0 or higher

### Installation & Run
```powershell
# 레포지토리 클론
git clone https://github.com/mark-kang/ship-deploy-poc.git

# 배포 시뮬레이션 실행 (Dry-Run 모드)
./deploy.ps1 -ArtifactPath "./builds/v1.0.1.zip" -Target "IIS_App_01" -DryRun

# 실제 배포 진행
./deploy.ps1 -ArtifactPath "./builds/v1.0.1.zip" -Target "IIS_App_01"
```

## � 설계 철학 및 핵심 가치 (Design Philosophy)
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
