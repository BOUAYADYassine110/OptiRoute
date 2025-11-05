"""
OpenWeather API Integration
Get API key from: https://openweathermap.org/api
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class OpenWeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.base_url = 'https://api.openweathermap.org/data/2.5'
    
    def get_current_weather(self, lat, lng):
        """Get current weather for location"""
        url = f'{self.base_url}/weather'
        
        params = {
            'lat': lat,
            'lon': lng,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'weather': data['weather'][0]['main'],
                    'description': data['weather'][0]['description'],
                    'wind_speed': data['wind']['speed'],
                    'visibility': data.get('visibility', 10000),
                    'rain': data.get('rain', {}).get('1h', 0)
                }
        except Exception as e:
            print(f"OpenWeather error: {e}")
        
        return self._fallback_weather()
    
    def get_weather_impact_score(self, lat, lng):
        """Calculate weather impact on delivery (0-100, higher = worse)"""
        weather = self.get_current_weather(lat, lng)
        
        score = 0
        
        # Rain impact
        if weather['rain'] > 0:
            score += min(weather['rain'] * 10, 30)
        
        # Wind impact
        if weather['wind_speed'] > 10:
            score += min((weather['wind_speed'] - 10) * 2, 20)
        
        # Visibility impact
        if weather['visibility'] < 5000:
            score += 20
        
        # Temperature extremes
        if weather['temperature'] < 0 or weather['temperature'] > 35:
            score += 15
        
        # Weather condition
        bad_conditions = ['Rain', 'Snow', 'Thunderstorm', 'Fog']
        if weather['weather'] in bad_conditions:
            score += 15
        
        return min(score, 100)
    
    def _fallback_weather(self):
        """Default weather when API unavailable"""
        return {
            'temperature': 20,
            'feels_like': 20,
            'humidity': 50,
            'weather': 'Clear',
            'description': 'clear sky',
            'wind_speed': 5,
            'visibility': 10000,
            'rain': 0
        }

openweather_service = OpenWeatherService()