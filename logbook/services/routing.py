import requests

def geocode(location_str):
    url = f"https://nominatim.openstreetmap.org/search?q={location_str}&format=json&limit=1"
    headers = {"User-Agent": "Trucker-HOS-App/1.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            return float(data['lon']), float(data['lat'])
    except Exception:
        pass
    raise ValueError(f"Could not geocode location: {location_str}")

def get_route(start_lon, start_lat, end_lon, end_lat):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok':
                route = data['routes'][0]
                distance_miles = route['distance'] * 0.000621371
                duration_hours = route['duration'] / 3600.0
                geometry = route['geometry']
                return distance_miles, duration_hours, geometry
    except Exception:
        pass
    raise ValueError(f"Routing API failed for coordinates ({start_lon}, {start_lat}) to ({end_lon}, {end_lat})")

def get_trip_route(current_coords, pickup_coords, dropoff_coords):
    # Leg 1: Current -> Pickup
    leg1_dist, leg1_dur, leg1_geom = get_route(current_coords[0], current_coords[1], pickup_coords[0], pickup_coords[1])
    
    # Leg 2: Pickup -> Dropoff
    leg2_dist, leg2_dur, leg2_geom = get_route(pickup_coords[0], pickup_coords[1], dropoff_coords[0], dropoff_coords[1])
    
    total_dist = leg1_dist + leg2_dist
    total_dur = leg1_dur + leg2_dur
    
    combined_coords = leg1_geom['coordinates'] + leg2_geom['coordinates'][1:]
    combined_geom = {
        "type": "LineString",
        "coordinates": combined_coords
    }
    
    return {
        "total_distance_miles": total_dist,
        "total_duration_hours": total_dur,
        "geometry": combined_geom,
        "legs": [
            {
                "name": "current_to_pickup",
                "distance_miles": leg1_dist,
                "duration_hours": leg1_dur,
                "start_location": current_coords,
                "end_location": pickup_coords
            },
            {
                "name": "pickup_to_dropoff",
                "distance_miles": leg2_dist,
                "duration_hours": leg2_dur,
                "start_location": pickup_coords,
                "end_location": dropoff_coords
            }
        ]
    }
