from django.shortcuts import render
from django.http import JsonResponse
from .models import Vessel, DeploymentLog
import os


def index(request):
    """메인 대시보드"""
    vessels = Vessel.objects.all()
    recent_deployments = DeploymentLog.objects.select_related('vessel')[:10]
    
    # 현재 VMS 버전 (환경변수 또는 기본값)
    current_version = os.getenv('VMS_VERSION', '1.0.0')
    
    context = {
        'vessels': vessels,
        'recent_deployments': recent_deployments,
        'current_version': current_version,
        'total_vessels': vessels.count(),
        'online_vessels': vessels.filter(is_online=True).count(),
    }
    
    return render(request, 'vessel/index.html', context)


def health(request):
    """헬스 체크 엔드포인트"""
    return JsonResponse({
        'status': 'healthy',
        'version': os.getenv('VMS_VERSION', '1.0.0'),
        'database': 'connected',
    })


def vessel_list(request):
    """선박 목록 API"""
    vessels = Vessel.objects.all()
    data = {
        'count': vessels.count(),
        'vessels': [
            {
                'name': v.name,
                'imo_number': v.imo_number,
                'type': v.vessel_type,
                'version': v.vms_version,
                'online': v.is_online,
            }
            for v in vessels
        ]
    }
    return JsonResponse(data)
