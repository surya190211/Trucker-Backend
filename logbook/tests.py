from django.test import TestCase
from rest_framework.test import APIClient
from logbook.services.trip_planner import generate_schedule, split_days
from datetime import datetime
from unittest.mock import patch

class TripPlannerTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('logbook.views.geocode')
    @patch('logbook.views.get_trip_route')
    def test_current_pickup_dropoff_both_legs(self, mock_get_route, mock_geocode):
        mock_geocode.side_effect = [(1,1), (2,2), (3,3)]
        mock_get_route.return_value = {
            "total_distance_miles": 100,
            "total_duration_hours": 2,
            "geometry": {},
            "legs": [
                {"name": "current_to_pickup", "distance_miles": 50, "duration_hours": 1},
                {"name": "pickup_to_dropoff", "distance_miles": 50, "duration_hours": 1}
            ]
        }
        
        response = self.client.post('/api/trips/plan/', {
            'current_location': 'A',
            'pickup_location': 'B',
            'dropoff_location': 'C',
            'current_cycle_hours': 0
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['route']['legs']), 2)
        stops = data['stops']
        self.assertTrue(any(s['type'] == 'PICKUP' for s in stops))
        self.assertTrue(any(s['type'] == 'DROPOFF' for s in stops))

    def test_8_hours_driving_break(self):
        legs = [{"name": "current_to_pickup", "distance_miles": 550, "duration_hours": 9.0}]
        schedule = generate_schedule(legs, datetime.now(), 0)
        breaks = [s for s in schedule if s.get('stop_type') == 'BREAK']
        self.assertEqual(len(breaks), 1)

    def test_11_hours_driving_rest(self):
        legs = [{"name": "current_to_pickup", "distance_miles": 720, "duration_hours": 12.0}]
        schedule = generate_schedule(legs, datetime.now(), 0)
        rests = [s for s in schedule if s.get('stop_type') == 'REST']
        self.assertTrue(len(rests) >= 1)

    def test_14_hour_window_exhaustion(self):
        legs = [
            {"name": "current_to_pickup", "distance_miles": 500, "duration_hours": 10.0},
            {"name": "pickup_to_dropoff", "distance_miles": 200, "duration_hours": 3.0}
        ]
        schedule = generate_schedule(legs, datetime.now(), 0)
        rests = [s for s in schedule if s.get('stop_type') == 'REST']
        self.assertTrue(len(rests) >= 1)

    def test_cycle_near_70(self):
        legs = [{"name": "current_to_pickup", "distance_miles": 100, "duration_hours": 2.0}]
        schedule = generate_schedule(legs, datetime.now(), 68.0)
        rests = [s for s in schedule if s.get('stop_type') == 'REST' and s['duration'] == 34.0]
        self.assertTrue(len(rests) >= 1)

    def test_1000_miles_fuel(self):
        legs = [{"name": "current_to_pickup", "distance_miles": 1100, "duration_hours": 17.0}]
        schedule = generate_schedule(legs, datetime.now(), 0)
        fuels = [s for s in schedule if s.get('stop_type') == 'FUEL']
        self.assertTrue(len(fuels) >= 1)

    def test_long_trip_multiple_days(self):
        legs = [{"name": "current_to_pickup", "distance_miles": 2000, "duration_hours": 30.0}]
        schedule = generate_schedule(legs, datetime.fromisoformat('2026-09-28T10:00:00'), 0)
        days = split_days(schedule)
        self.assertTrue(len(days) > 2)
        for day in days:
            total_hrs = sum(s['duration'] for s in day['segments'])
            self.assertAlmostEqual(total_hrs, 24.0, places=2)

    def test_invalid_input(self):
        response1 = self.client.post('/api/trips/plan/', {
            'current_location': 'A',
            'pickup_location': 'B',
            'dropoff_location': 'C',
            'current_cycle_hours': -5
        }, format='json')
        self.assertEqual(response1.status_code, 400)

        response2 = self.client.post('/api/trips/plan/', {
            'current_location': 'A',
            'pickup_location': 'B',
            'dropoff_location': 'C',
            'current_cycle_hours': 71
        }, format='json')
        self.assertEqual(response2.status_code, 400)

        response3 = self.client.post('/api/trips/plan/', {
            'current_location': 'A',
            'dropoff_location': 'C',
            'current_cycle_hours': 0
        }, format='json')
        self.assertEqual(response3.status_code, 400)
