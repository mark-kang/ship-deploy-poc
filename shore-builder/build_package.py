"""
Shore Builder - 오프라인 패키징 도구
육상에서 Django 앱과 의존성을 wheel 파일로 패키징
"""
import subprocess
import hashlib
import zipfile
import argparse
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build offline deployment package")
    parser.add_argument("--version", required=True, help="Package version (e.g., 1.0.0)")
    parser.add_argument("--source", required=True, help="Source directory path")
    
    args = parser.parse_args()
    
    build_offline_package(args.version, args.source)
