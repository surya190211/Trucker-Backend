from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from .models import DailyLog, Driver, Truck, Trip, MaintenanceRecord, Notification
from .serializers import DailyLogSerializer, DriverSerializer, TruckSerializer, TripSerializer, MaintenanceRecordSerializer, NotificationSerializer
from .services.hos import check_hos_compliance
from .services.routing import geocode, get_trip_route
from .services.trip_planner import generate_schedule, split_days

class DailyLogViewSet(viewsets.ModelViewSet):
    queryset = DailyLog.objects.all().prefetch_related('entries')
    serializer_class = DailyLogSerializer

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


class HOSComplianceView(APIView):
    def get(self, request, *args, **kwargs):
        latest_log = DailyLog.objects.order_by('-date').first()
        if not latest_log:
            return Response({
                "has_data": False,
                "message": "No daily logs available yet.",
                "data": None
            }, status=200)
        
        compliance = check_hos_compliance(latest_log.entries.all())
        return Response({
            "has_data": True,
            "data": {
                "driver": latest_log.driver_name,
                "date": latest_log.date,
                **compliance
            }
        })


class TripPlanView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        curr_loc = data.get('current_location')
        pickup = data.get('pickup_location')
        dropoff = data.get('dropoff_location')
        cycle = data.get('current_cycle_hours')
        
        if not curr_loc or not pickup or not dropoff or cycle is None:
            return Response({"error": "Missing required fields (current_location, pickup_location, dropoff_location, current_cycle_hours)."}, status=400)
            
        try:
            cycle = float(cycle)
            if cycle < 0 or cycle > 70:
                return Response({"error": "Cycle hours must be between 0 and 70."}, status=400)
        except ValueError:
            return Response({"error": "Invalid cycle hours."}, status=400)
        
        try:
            c_coords = geocode(curr_loc)
            p_coords = geocode(pickup)
            d_coords = geocode(dropoff)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        try:
            route_data = get_trip_route(c_coords, p_coords, d_coords)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
            
        schedule = generate_schedule(route_data["legs"], datetime.now(), cycle)
        days = split_days(schedule)
        
        # Build stops and calculate totals
        stops = []
        driving_hours = 0
        on_duty_hours = 0
        off_duty_hours = 0
        sleeper_hours = 0
        cycle_hours_used = cycle
        fuel_stops = 0
        break_stops = 0
        rest_stops = 0
        
        for seg in schedule:
            if "stop_type" in seg:
                stops.append({
                    "type": seg["stop_type"],
                    "location": seg["location"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "reason": seg["reason"],
                    "mileage": seg["miles"]
                })
                if seg["stop_type"] == "FUEL":
                    fuel_stops += 1
                elif seg["stop_type"] == "BREAK":
                    break_stops += 1
                elif seg["stop_type"] == "REST" or seg["stop_type"] == "RESTART":
                    rest_stops += 1
            
            dur = seg["duration"]
            if seg["status"] == "DRIVING":
                driving_hours += dur
                on_duty_hours += dur
                cycle_hours_used += dur
            elif seg["status"] == "ON DUTY":
                on_duty_hours += dur
                cycle_hours_used += dur
            elif seg["status"] == "OFF DUTY":
                off_duty_hours += dur
                if seg.get("stop_type") == "RESTART" or (seg.get("stop_type") == "REST" and dur >= 34.0):
                    cycle_hours_used = 0
            elif seg["status"] == "SLEEPER BERTH":
                sleeper_hours += dur
        
        cycle_hours_remaining = max(0, 70.0 - cycle_hours_used)
        
        # Add summary data to days
        for day in days:
            d_dr = sum(s["duration"] for s in day["segments"] if s["status"] == "DRIVING")
            d_od = sum(s["duration"] for s in day["segments"] if s["status"] == "ON DUTY")
            d_sb = sum(s["duration"] for s in day["segments"] if s["status"] == "SLEEPER BERTH")
            d_off = sum(s["duration"] for s in day["segments"] if s["status"] == "OFF DUTY")
            day["totals"] = {
                "driving": d_dr,
                "on_duty": d_od,
                "sleeper": d_sb,
                "off_duty": d_off,
                "total": d_dr + d_od + d_sb + d_off
            }

        return Response({
            "trip": {
                "distance_miles": route_data["total_distance_miles"],
                "estimated_duration_hours": route_data["total_duration_hours"]
            },
            "summary": {
                "driving_hours": driving_hours,
                "on_duty_hours": on_duty_hours,
                "off_duty_hours": off_duty_hours,
                "sleeper_hours": sleeper_hours,
                "cycle_hours_used": cycle_hours_used,
                "cycle_hours_remaining": cycle_hours_remaining,
                "fuel_stops": fuel_stops,
                "break_stops": break_stops,
                "rest_stops": rest_stops,
                "days": len(days)
            },
            "route": {
                "geometry": route_data["geometry"],
                "waypoints": {
                    "current": c_coords,
                    "pickup": p_coords,
                    "dropoff": d_coords
                },
                "legs": route_data["legs"]
            },
            "stops": stops,
            "days": days
        })
