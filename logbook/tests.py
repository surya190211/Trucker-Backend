from django.test import TestCase
from logbook.services.trip_planner import generate_schedule, split_days
from logbook.services.hos import check_hos_compliance
from datetime import datetime

class HOSTests(TestCase):
    def test_short_trip_generation(self):
        start_dt = datetime.now()
        schedule = generate_schedule(distance_miles=200, duration_hours=3.5, start_time=start_dt, current_cycle_hours=10)
        
        # Pickup + Driving + Dropoff = 3 segments (without fuel or break)
        self.assertTrue(len(schedule) >= 3)
        self.assertEqual(schedule[0]['status'], 'ON DUTY')
        self.assertEqual(schedule[0]['reason'], 'Pickup')

    def test_split_days_totals_24(self):
        start_dt = datetime.fromisoformat('2026-09-28T10:00:00')
        schedule = generate_schedule(distance_miles=1500, duration_hours=25.0, start_time=start_dt, current_cycle_hours=0)
        days = split_days(schedule)
        
        for day in days:
            total_hours = sum([seg['duration'] for seg in day['segments']])
            self.assertAlmostEqual(total_hours, 24.0, places=2)
            
    def test_11_hour_driving_limit(self):
        start_dt = datetime.fromisoformat('2026-09-28T08:00:00')
        # A 12-hour drive should force a rest stop
        schedule = generate_schedule(distance_miles=720, duration_hours=12.0, start_time=start_dt, current_cycle_hours=0)
        
        driving_chunks = [s for s in schedule if s['status'] == 'DRIVING']
        rests = [s for s in schedule if s['status'] == 'SLEEPER BERTH']
        
        self.assertTrue(len(rests) >= 1)
        
    def test_30_minute_break(self):
        start_dt = datetime.fromisoformat('2026-09-28T08:00:00')
        schedule = generate_schedule(distance_miles=550, duration_hours=9.0, start_time=start_dt, current_cycle_hours=0)
        
        breaks = [s for s in schedule if s['reason'] == '30-Minute Break']
        self.assertTrue(len(breaks) >= 1)
