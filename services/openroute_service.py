"""
OpenRouteService API Integration
Get API key from: https://openrouteservice.org/dev/#/signup
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class OpenRouteService:
    def __init__(self):
        api_key = os.getenv('OPENROUTE_API_KEY', '')
        # Remove quotes if present
        self.api_key = api_key.strip('"').strip()
        self.base_url = 'https://api.openrouteservice.org'
    
    def get_route(self, start_coords, end_coords, profile='driving-car'):
        """Get optimized route between two points"""
        url = f'{self.base_url}/v2/directions/{profile}/geojson'
        
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        body = {
            'coordinates': [
                [start_coords['lng'], start_coords['lat']],
                [end_coords['lng'], end_coords['lat']]
            ],
            'format': 'geojson'
        }
        
        try:
            response = requests.post(url, json=body, headers=headers)
            if response.status_code == 200:
                data = response.json()
                feature = data['features'][0]
                coords = feature['geometry']['coordinates']
                props = feature['properties']
                print(f"✓ ORS API: Got {len(coords)} route points")
                return {
                    'distance': props['summary']['distance'],
                    'duration': props['summary']['duration'],
                    'geometry': feature['geometry'],
                    'coordinates': coords
                }
            else:
                print(f"✗ ORS API Error {response.status_code}: {response.text}")
                print("  → Using fallback (straight line)")
        except Exception as e:
            print(f"✗ ORS Exception: {e}")
            print("  → Using fallback (straight line)")
        
        return self._fallback_route(start_coords, end_coords)
    
    def _fallback_route(self, start, end):
        """Simple fallback when API unavailable"""
        import math
        
        lat1, lon1 = math.radians(start['lat']), math.radians(start['lng'])
        lat2, lon2 = math.radians(end['lat']), math.radians(end['lng'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = 6371000 * c
        
        duration = distance / (50000 / 3600)
        
        return {
            'distance': distance,
            'duration': duration,
            'coordinates': [[start['lng'], start['lat']], [end['lng'], end['lat']]]
        }

openroute_service = OpenRouteService()