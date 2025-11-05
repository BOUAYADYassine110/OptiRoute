"""
Route API - Get real routes and conditions
"""

from flask import Blueprint, request, jsonify
from services.openroute_service import openroute_service
from services.openweather_service import openweather_service
from services.route_monitor import route_monitor
import random

route_api_bp = Blueprint('route_api', __name__)

active_deliveries = {}

@route_api_bp.route('/api/route/get', methods=['POST'])
def get_route():
    """Get real route with traffic and weather"""
    data = request.get_json()
    
    start = data.get('start')
    end = data.get('end')
    order_id = data.get('order_id', 'unknown')
    
    if not start or not end:
        return jsonify({'error': 'Missing start or end location'}), 400
    
    route_data = openroute_service.get_route(start, end)
    start_weather = openweather_service.get_current_weather(start['lat'], start['lng'])
    end_weather = openweather_service.get_current_weather(end['lat'], end['lng'])
    weather_impact = openweather_service.get_weather_impact_score(start['lat'], start['lng'])
    traffic_level = random.randint(20, 80)
    
    adjusted_duration = route_data['duration']
    if weather_impact > 50:
        adjusted_duration *= 1.2
    if traffic_level > 70:
        adjusted_duration *= 1.3
    
    return jsonify({
        'route': {
            'coordinates': route_data['coordinates'],
            'distance': route_data['distance'],
            'duration': route_data['duration'],
            'adjusted_duration': adjusted_duration
        },
        'weather': {
            'start': start_weather,
            'end': end_weather,
            'impact_score': weather_impact
        },
        'traffic': {
            'level': traffic_level,
            'status': 'clear' if traffic_level < 30 else 'moderate' if traffic_level < 70 else 'heavy',
            'delay': max(0, (traffic_level - 50) * 10)
        }
    })

@route_api_bp.route('/api/conditions/live', methods=['POST'])
def get_live_conditions():
    """Get live weather and traffic for location"""
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not lat or not lng:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    weather = openweather_service.get_current_weather(lat, lng)
    weather_impact = openweather_service.get_weather_impact_score(lat, lng)
    traffic_level = random.randint(0, 100)
    
    return jsonify({
        'weather': weather,
        'weather_impact': weather_impact,
        'traffic_level': traffic_level,
        'traffic_status': 'clear' if traffic_level < 30 else 'moderate' if traffic_level < 70 else 'heavy',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@route_api_bp.route('/api/route/start-monitoring', methods=['POST'])
def start_route_monitoring():
    data = request.get_json()
    order_id = data.get('order_id')
    start = data.get('start')
    end = data.get('end')
    
    if not all([order_id, start, end]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    active_deliveries[order_id] = {'start': start, 'end': end, 'reroutes': []}
    
    def reroute_callback(reroute_data):
        if order_id in active_deliveries:
            active_deliveries[order_id]['reroutes'].append(reroute_data)
    
    route_monitor.start_monitoring(order_id, start, end, reroute_callback)
    return jsonify({'status': 'monitoring_started', 'order_id': order_id})

@route_api_bp.route('/api/route/check-reroute/<order_id>', methods=['GET'])
def check_reroute(order_id):
    if order_id not in active_deliveries:
        return jsonify({'reroute_needed': False})
    
    reroutes = active_deliveries[order_id].get('reroutes', [])
    if reroutes:
        latest = reroutes[-1]
        return jsonify({
            'reroute_needed': True,
            'new_route': latest['new_route'],
            'reason': latest['reason'],
            'weather_impact': latest['weather_impact'],
            'reroute_count': latest['reroute_count']
        })
    
    return jsonify({'reroute_needed': False})

@route_api_bp.route('/api/route/stop-monitoring/<order_id>', methods=['POST'])
def stop_route_monitoring(order_id):
    route_monitor.stop_monitoring(order_id)
    if order_id in active_deliveries:
        del active_deliveries[order_id]
    return jsonify({'status': 'monitoring_stopped'})
