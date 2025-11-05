"""
Geocoding Service - Convert addresses to coordinates
Uses Nominatim (OpenStreetMap) - Free, no API key needed
"""

import requests
import time

class GeocodingService:
    def __init__(self):
        self.base_url = 'https://nominatim.openstreetmap.org'
        self.headers = {
            'User-Agent': 'OptiroRoute/1.0'
        }
    
    def geocode_address(self, address):
        """Convert address to coordinates"""
        url = f'{self.base_url}/search'
        
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        try:
            time.sleep(1)  # Rate limiting - be nice to free service
            response = requests.get(url, params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    return {
                        'address': result.get('display_name'),
                        'lat': float(result.get('lat')),
                        'lng': float(result.get('lon')),
                        'success': True
                    }
        except Exception as e:
            print(f"Geocoding error: {e}")
        
        return {
            'address': address,
            'lat': 40.7128,
            'lng': -74.0060,
            'success': False,
            'error': 'Could not geocode address'
        }

geocoding_service = GeocodingService()