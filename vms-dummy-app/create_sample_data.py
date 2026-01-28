"""
샘플 데이터 생성 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vms.settings')
django.setup()

from vessel.models import Vessel, DeploymentLog
from django.utils import timezone
from datetime import timedelta

# 기존 데이터 삭제
Vessel.objects.all().delete()
DeploymentLog.objects.all().delete()

# 샘플 선박 생성
vessels_data = [
    {
        'name': 'PACIFIC STAR',
        'imo_number': 'IMO9876543',
        'vessel_type': 'Container Ship',
        'flag': 'South Korea',
        'built_year': 2018,
        'gross_tonnage': 50000.00,
        'current_location': 'Busan Port',
        'vms_version': '1.0.0',
        'is_online': True,
    },
    {
        'name': 'OCEAN VOYAGER',
        'imo_number': 'IMO9876544',
        'vessel_type': 'Bulk Carrier',
        'flag': 'Panama',
        'built_year': 2020,
        'gross_tonnage': 75000.00,
        'current_location': 'Singapore',
        'vms_version': '1.0.0',
        'is_online': True,
    },
    {
        'name': 'ATLANTIC PRIDE',
        'imo_number': 'IMO9876545',
        'vessel_type': 'Tanker',
        'flag': 'Liberia',
        'built_year': 2015,
        'gross_tonnage': 100000.00,
        'current_location': 'Rotterdam',
        'vms_version': '0.9.5',
        'is_online': False,
    },
]

vessels = []
for data in vessels_data:
    vessel = Vessel.objects.create(**data)
    vessels.append(vessel)
    print(f"✅ Created vessel: {vessel.name}")

# 샘플 배포 이력 생성
deployments_data = [
    {
        'vessel': vessels[0],
        'version': '1.0.0',
        'status': 'success',
        'duration_seconds': 45.2,
        'deployed_at': timezone.now() - timedelta(hours=2),
        'notes': 'Initial deployment successful',
    },
    {
        'vessel': vessels[1],
        'version': '1.0.0',
        'status': 'success',
        'duration_seconds': 38.7,
        'deployed_at': timezone.now() - timedelta(hours=5),
        'notes': 'Upgraded from 0.9.5',
    },
    {
        'vessel': vessels[1],
        'version': '0.9.5',
        'status': 'success',
        'duration_seconds': 42.1,
        'deployed_at': timezone.now() - timedelta(days=7),
        'notes': 'Previous stable version',
    },
    {
        'vessel': vessels[2],
        'version': '1.0.0',
        'status': 'failed',
        'duration_seconds': 12.3,
        'deployed_at': timezone.now() - timedelta(hours=1),
        'notes': 'Network timeout during deployment',
    },
    {
        'vessel': vessels[2],
        'version': '1.0.0',
        'status': 'rollback',
        'duration_seconds': 0.8,
        'deployed_at': timezone.now() - timedelta(minutes=55),
        'notes': 'Automatic rollback to 0.9.5',
    },
]

for data in deployments_data:
    deployment = DeploymentLog.objects.create(**data)
    print(f"✅ Created deployment: {deployment}")

print("\n🎉 Sample data created successfully!")
print(f"Total vessels: {Vessel.objects.count()}")
print(f"Total deployments: {DeploymentLog.objects.count()}")
