"""
Route Monitor - Dynamic rerouting based on conditions
"""

import time
import threading
from services.openroute_service import openroute_service
from services.openweather_service import openweather_service

class RouteMonitor:
    def __init__(self):
        self.active_routes = {}  # order_id -> route_data
        self.monitoring = False
        self.check_interval = 30  # Check every 30 seconds
        
    def start_monitoring(self, order_id, start, end, callback):
        """Start monitoring route for changes"""
        self.active_routes[order_id] = {
            'start': start,
            'end': end,
            'callback': callback,
            'last_route': None,
            'last_check': 0,
            'reroute_count': 0
        }
        
        if not self.monitoring:
            self.monitoring = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop_monitoring(self, order_id):
        """Stop monitoring a route"""
        if order_id in self.active_routes:
            del self.active_routes[order_id]
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            current_time = time.time()
            
            for order_id, route_data in list(self.active_routes.items()):
                if current_time - route_data['last_check'] >= self.check_interval:
                    self._check_route(order_id, route_data)
                    route_data['last_check'] = current_time
            
            time.sleep(5)
    
    def _check_route(self, order_id, route_data):
        """Check if route needs updating"""
        start = route_data['start']
        end = route_data['end']
        
        # Get current conditions
        weather_impact = openweather_service.get_weather_impact_score(start['lat'], start['lng'])
        
        # Get fresh route
        new_route = openroute_service.get_route(start, end)
        
        # Check if reroute needed
        should_reroute = False
        reason = None
        
        if route_data['last_route']:
            old_duration = route_data['last_route']['duration']
            new_duration = new_route['duration']
            
            # Reroute if new route is 15% faster
            if new_duration < old_duration * 0.85:
                should_reroute = True
                reason = 'faster_route'
            
            # Reroute if weather impact is high
            if weather_impact > 70:
                should_reroute = True
                reason = 'weather_alert'
        
        if should_reroute:
            route_data['reroute_count'] += 1
            route_data['last_route'] = new_route
            
            # Notify via callback
            if route_data['callback']:
                route_data['callback']({
                    'order_id': order_id,
                    'new_route': new_route,
                    'reason': reason,
                    'weather_impact': weather_impact,
                    'reroute_count': route_data['reroute_count']
                })
        else:
            route_data['last_route'] = new_route

route_monitor = RouteMonitor()
