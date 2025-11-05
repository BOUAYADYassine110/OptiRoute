#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import re
import random
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ORS_API_KEY = os.getenv('OPENROUTE_API_KEY', '').strip('"')
OWM_API_KEY = os.getenv('OPENWEATHER_API_KEY', '').strip('"')

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def root():
    return jsonify({'service': 'OptiroRoute', 'status': 'online'})

@app.route('/api/test')
def test():
    return jsonify({'status': 'working'})

@app.route('/api/agents/delivery')
def agents():
    return jsonify({'agents': ['delivery_001', 'delivery_002', 'delivery_003']})

@app.route('/api/traffic/status')
def traffic():
    return jsonify({'traffic_data': []})

@app.route('/api/chat/process', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('message', '')
    
    match = re.search(r'from\s+(.+?)\s+to\s+(.+)', msg, re.IGNORECASE)
    if match:
        pickup = match.group(1).strip()
        delivery = match.group(2).strip()
        
        return jsonify({
            'success': True,
            'message': f'Order from {pickup} to {delivery}\\n\\nCost: $15.50\\nTime: 25 min\\n\\nConfirm?',
            'order_preview': {
                'pickup_location': {'lat': 40.7128, 'lng': -74.0060, 'address': pickup},
                'delivery_location': {'lat': 40.7589, 'lng': -73.9851, 'address': delivery},
                'weight': 1.0,
                'cost': 15.50,
                'estimated_time': 25
            }
        })
    
    return jsonify({'success': False, 'message': 'Use: from [pickup] to [delivery]'})

@app.route('/api/chat/confirm', methods=['POST'])
def confirm():
    order_id = f"ORD_{int(time.time())}"
    socketio.emit('order_update', {'order_id': order_id, 'status': 'pending'})
    return jsonify({'success': True, 'order_id': order_id, 'message': f'Order {order_id} created!'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({'access_token': 'demo_token', 'user': {'username': 'demo'}})

@app.route('/api/route/get', methods=['POST'])
def route():
    data = request.get_json()
    start = data.get('start', {})
    end = data.get('end', {})
    
    start_coords = [start.get('lng', -74.0060), start.get('lat', 40.7128)]
    end_coords = [end.get('lng', -73.9851), end.get('lat', 40.7589)]
    
    # Try OpenRouteService API
    route_coords = []
    distance = 5000
    duration = 1500
    
    if ORS_API_KEY and ORS_API_KEY != 'your-openroute-api-key':
        try:
            ors_url = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'
            headers = {'Authorization': ORS_API_KEY}
            ors_data = {
                'coordinates': [start_coords, end_coords],
                'format': 'geojson'
            }
            
            response = requests.post(ors_url, json=ors_data, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'features' in result and result['features']:
                    feature = result['features'][0]
                    route_coords = feature['geometry']['coordinates']
                    props = feature['properties']
                    distance = props.get('summary', {}).get('distance', 5000)
                    duration = props.get('summary', {}).get('duration', 1500)
                    print(f'ORS route: {len(route_coords)} points, {distance}m, {duration}s')
        except Exception as e:
            print(f'ORS error: {e}')
    
    # Fallback route if API failed
    if not route_coords:
        steps = 20
        route_coords = []
        for i in range(steps + 1):
            ratio = i / steps
            lng = start_coords[0] + (end_coords[0] - start_coords[0]) * ratio
            lat = start_coords[1] + (end_coords[1] - start_coords[1]) * ratio
            route_coords.append([lng, lat])
    
    # Get weather data
    weather_impact = random.randint(0, 100)
    start_weather = {'temp': 20, 'condition': 'clear'}
    end_weather = {'temp': 22, 'condition': 'clear'}
    
    if OWM_API_KEY and OWM_API_KEY != 'your-openweather-api-key':
        try:
            # Get weather for start location
            weather_url = f'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'lat': start.get('lat', 40.7128),
                'lon': start.get('lng', -74.0060),
                'appid': OWM_API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(weather_url, params=params, timeout=10)
            if response.status_code == 200:
                weather_data = response.json()
                start_weather = {
                    'temp': weather_data['main']['temp'],
                    'condition': weather_data['weather'][0]['description'],
                    'humidity': weather_data['main']['humidity'],
                    'wind_speed': weather_data.get('wind', {}).get('speed', 0)
                }
                
                # Calculate weather impact
                if 'rain' in weather_data or 'snow' in weather_data:
                    weather_impact = 70
                elif weather_data['main']['humidity'] > 80:
                    weather_impact = 40
                else:
                    weather_impact = 10
                    
                print(f'Weather: {start_weather["temp"]}°C, {start_weather["condition"]}')
        except Exception as e:
            print(f'Weather API error: {e}')
    
    # Traffic simulation
    traffic_level = random.randint(20, 80)
    traffic_status = 'clear' if traffic_level < 30 else 'moderate' if traffic_level < 70 else 'heavy'
    
    return jsonify({
        'route': {
            'coordinates': route_coords,
            'distance': distance,
            'duration': duration,
            'adjusted_duration': duration * (1.2 if weather_impact > 50 else 1.0)
        },
        'weather': {
            'start': start_weather,
            'end': end_weather,
            'impact_score': weather_impact
        },
        'traffic': {
            'level': traffic_level,
            'status': traffic_status,
            'delay': max(0, (traffic_level - 50) * 10)
        }
    })

@app.route('/api/conditions/live', methods=['POST'])
def conditions():
    data = request.get_json()
    lat = data.get('lat', 40.7128)
    lng = data.get('lng', -74.0060)
    
    # Default values
    weather_data = {
        'temp': 20,
        'condition': 'clear',
        'humidity': 60,
        'wind_speed': 5
    }
    weather_impact = 20
    
    # Try to get real weather data
    if OWM_API_KEY and OWM_API_KEY != 'your-openweather-api-key':
        try:
            weather_url = f'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'lat': lat,
                'lon': lng,
                'appid': OWM_API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(weather_url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                weather_data = {
                    'temp': result['main']['temp'],
                    'condition': result['weather'][0]['description'],
                    'humidity': result['main']['humidity'],
                    'wind_speed': result.get('wind', {}).get('speed', 0)
                }
                
                # Calculate impact
                if 'rain' in result['weather'][0]['description'] or 'snow' in result['weather'][0]['description']:
                    weather_impact = 75
                elif result['main']['humidity'] > 80:
                    weather_impact = 45
                else:
                    weather_impact = 15
        except Exception as e:
            print(f'Live weather error: {e}')
    
    # Simulate traffic
    traffic_level = random.randint(0, 100)
    traffic_status = 'clear' if traffic_level < 30 else 'moderate' if traffic_level < 70 else 'heavy'
    
    return jsonify({
        'weather': weather_data,
        'weather_impact': weather_impact,
        'traffic_level': traffic_level,
        'traffic_status': traffic_status,
        'timestamp': time.time()
    })

@app.route('/api/route/start-monitoring', methods=['POST'])
def start_monitor():
    return jsonify({'status': 'started'})

@app.route('/api/route/check-reroute/<order_id>')
def check_reroute(order_id):
    return jsonify({'reroute_needed': False})

@app.route('/api/route/stop-monitoring/<order_id>', methods=['POST'])
def stop_monitor(order_id):
    return jsonify({'status': 'stopped'})

@socketio.on('connect')
def on_connect():
    emit('status', {'msg': 'Connected'})

if __name__ == '__main__':
    print('Starting on port 5001...')
    socketio.run(app, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)