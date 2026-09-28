from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyLogViewSet, HOSComplianceView, DriverViewSet, TruckViewSet, TripViewSet, MaintenanceRecordViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'logs', DailyLogViewSet, basename='dailylog')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'trucks', TruckViewSet, basename='truck')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'maintenance', MaintenanceRecordViewSet, basename='maintenance')
router.register(r'notifications', NotificationViewSet, basename='notification')

from django.urls import path
urlpatterns = [
    path('hos/', HOSComplianceView.as_view(), name='hos-compliance'),
    path('', include(router.urls)),
]
