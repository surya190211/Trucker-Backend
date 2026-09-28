from rest_framework import viewsets
from .models import DailyLog
from .serializers import DailyLogSerializer

class DailyLogViewSet(viewsets.ModelViewSet):
    queryset = DailyLog.objects.all().prefetch_related('entries')
    serializer_class = DailyLogSerializer

from .models import Driver, Truck, Trip, MaintenanceRecord, Notification
from .serializers import DriverSerializer, TruckSerializer, TripSerializer, MaintenanceRecordSerializer, NotificationSerializer
from rest_framework import viewsets

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from .services.hos import check_hos_compliance
from .models import DailyLog

class HOSComplianceView(APIView):
    def get(self, request, *args, **kwargs):
        latest_log = DailyLog.objects.order_by('-date').first()
        if not latest_log:
            return Response({"error": "No logs found to calculate compliance."}, status=404)
        
        compliance = check_hos_compliance(latest_log.entries.all())
        return Response({
            "data": {
                "driver": latest_log.driver_name,
                "date": latest_log.date,
                **compliance
            }
        })
