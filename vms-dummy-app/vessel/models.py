from django.db import models
from django.utils import timezone


class Vessel(models.Model):
    """선박 정보 모델"""
    
    name = models.CharField('선박명', max_length=100)
    imo_number = models.CharField('IMO 번호', max_length=20, unique=True)
    vessel_type = models.CharField('선박 유형', max_length=50)
    flag = models.CharField('선적국', max_length=50)
    built_year = models.IntegerField('건조년도')
    gross_tonnage = models.DecimalField('총톤수', max_digits=10, decimal_places=2)
    
    # 운항 정보
    current_location = models.CharField('현재 위치', max_length=200, blank=True)
    last_updated = models.DateTimeField('최종 업데이트', default=timezone.now)
    
    # 시스템 정보
    vms_version = models.CharField('VMS 버전', max_length=20, default='1.0.0')
    is_online = models.BooleanField('온라인 상태', default=False)
    
    class Meta:
        verbose_name = '선박'
        verbose_name_plural = '선박 목록'
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.name} ({self.imo_number})"


class DeploymentLog(models.Model):
    """배포 이력 모델"""
    
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='deployments')
    version = models.CharField('배포 버전', max_length=20)
    deployed_at = models.DateTimeField('배포 시각', default=timezone.now)
    status = models.CharField('상태', max_length=20, choices=[
        ('success', '성공'),
        ('failed', '실패'),
        ('rollback', '롤백'),
    ])
    duration_seconds = models.FloatField('소요 시간(초)', null=True, blank=True)
    notes = models.TextField('비고', blank=True)
    
    class Meta:
        verbose_name = '배포 이력'
        verbose_name_plural = '배포 이력'
        ordering = ['-deployed_at']
    
    def __str__(self):
        return f"{self.vessel.name} - v{self.version} ({self.status})"
