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

from .services.routing import geocode, get_route
from .services.trip_planner import generate_schedule, split_days

class TripPlanView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        curr_loc = data.get('current_location', '')
        pickup = data.get('pickup_location', '')
        dropoff = data.get('dropoff_location', '')
        cycle = float(data.get('current_cycle_hours', 0))
        
        # Geocode
        c_lon, c_lat = geocode(curr_loc)
        p_lon, p_lat = geocode(pickup)
        d_lon, d_lat = geocode(dropoff)
        
        dist, dur, geom = get_route(p_lon, p_lat, d_lon, d_lat)
        
        from datetime import datetime
        schedule = generate_schedule(dist, dur, datetime.now(), cycle)
        days = split_days(schedule)
        
        return Response({
            "trip": {"distance_miles": dist, "estimated_duration_hours": dur},
            "summary": {"driving_hours": dur},
            "route": {"geometry": geom},
            "stops": [],
            "days": days
        })
