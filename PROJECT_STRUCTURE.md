# Ship Deploy PoC - 프로젝트 구조

## 📂 디렉터리 구조

```
ship-deploy-poc/
├── 📂 .github/workflows/
│   └── build-and-package.yml      # CI/CD 자동화 워크플로우
│
├── 📂 shore-builder/              # [육상] 빌드 및 패키징 도구
│   ├── build_package.py           # Django 앱 + wheel 패키징 스크립트
│   ├── sign_artifact.ps1          # SHA-256 해시 생성
│   └── requirements.txt           # 빌드 도구 의존성
│
├── 📂 ship-deployer/              # [선박] 배포 및 운영 도구
│   ├── deploy.ps1                 # 핵심 배포 스크립트
│   ├── rollback.ps1               # 즉시 롤백 스크립트
│   ├── health_check.ps1           # 헬스 체크
│   └── config.json                # 배포 설정
│
├── 📂 vms-dummy-app/              # 테스트용 Django VMS 앱
│   ├── manage.py                  # Django 관리 스크립트
│   ├── requirements.txt           # Django 의존성
│   ├── vms/                       # Django 프로젝트
│   │   ├── __init__.py
│   │   ├── settings.py            # Django 설정
│   │   ├── urls.py                # URL 라우팅
│   │   ├── wsgi.py                # WSGI 설정
│   │   └── asgi.py                # ASGI 설정
│   └── vessel/                    # 선박 관리 앱
│       ├── models.py              # Vessel, DeploymentLog 모델
│       ├── views.py               # 대시보드, API 뷰
│       ├── admin.py               # Django Admin 설정
│       ├── urls.py                # URL 패턴
│       ├── templates/vessel/
│       │   └── index.html         # 메인 대시보드 UI
│       └── migrations/
│
├── 📂 docs/
│   └── README.md                  # 문서 디렉터리
│
├── 📄 README.md                   # 프로젝트 설명서
├── 📄 LICENSE
└── 📄 .gitignore
```

## 🎯 주요 파일 설명

### Shore Builder (육상 빌드)
- **build_package.py**: Python wheel 다운로드 + Django 소스 압축 + SHA-256 생성
- **sign_artifact.ps1**: 패키지 무결성 검증을 위한 체크섬 생성

### Ship Deployer (선박 배포)
- **deploy.ps1**: 5단계 배포 프로세스 (검증 → 스냅샷 → 배포 → 헬스체크 → 롤백)
- **rollback.ps1**: Junction 포인터 전환으로 1초 이내 복구
- **health_check.ps1**: HTTP 엔드포인트 상태 확인
- **config.json**: 배포 경로, IIS 사이트명 등 설정

### VMS Django App
- **vessel/models.py**: 선박 정보 및 배포 이력 모델
- **vessel/views.py**: 대시보드, 헬스체크, API 엔드포인트
- **vessel/templates/vessel/index.html**: 그라디언트 배경의 모던 UI

## 🚀 빠른 시작

### 1. Django 앱 실행 (로컬 테스트)
```bash
cd vms-dummy-app
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2. 패키지 빌드 (육상)
```bash
cd shore-builder
python build_package.py --version 1.0.0 --source ../vms-dummy-app
```

### 3. 배포 시뮬레이션 (선박)
```powershell
cd ship-deployer
.\deploy.ps1 -PackagePath "C:\path\to\vms-app-1.0.0.zip" -DryRun
```

## 📝 다음 단계

1. ✅ 프로젝트 구조 생성 완료
2. ⏭️ Django 마이그레이션 실행
3. ⏭️ 샘플 데이터 추가
4. ⏭️ 실제 배포 테스트
