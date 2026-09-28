import requests

def geocode(location_str):
    url = f"https://nominatim.openstreetmap.org/search?q={location_str}&format=json&limit=1"
    headers = {"User-Agent": "Trucker-HOS-App/1.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            return float(data['lon']), float(data['lat'])
    except:
        pass
    return None, None

def get_route(start_lon, start_lat, end_lon, end_lat):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok':
                route = data['routes'][0]
                distance_miles = route['distance'] * 0.000621371
                duration_hours = route['duration'] / 3600.0
                geometry = route['geometry']
                return distance_miles, duration_hours, geometry
    except:
        pass
    return 0, 0, None
