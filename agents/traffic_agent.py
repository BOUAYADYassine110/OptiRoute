from .base_agent import BaseAgent
import requests
import time
from threading import Thread
from collections import deque
from datetime import datetime, timedelta

class TrafficAgent(BaseAgent):
    def __init__(self, agent_id="traffic_001"):
        super().__init__(
            agent_id=agent_id,
            role="Intelligent Traffic Analyst",
            goal="Predict traffic patterns and proactively optimize routes",
            backstory="AI-powered traffic analyst with predictive capabilities and learning"
        )
        self.traffic_data = {}
        self.monitoring = False
        
        # INTELLIGENCE ADDITIONS
        self.traffic_history = {}  # Store historical patterns
        self.prediction_model = {}  # Simple prediction model
        self.learning_rate = 0.1
        self.pattern_memory = deque(maxlen=100)
    
    def start_monitoring(self):
        """Start continuous traffic monitoring"""
        self.monitoring = True
        monitor_thread = Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring:
            self.update_traffic_data()
            self.check_for_alerts()
            time.sleep(10)  # Update every 10 seconds for more visibility
    
    def update_traffic_data(self):
        """INTELLIGENT: Enhanced with learning and prediction"""
        import random
        
        major_routes = ["route_1", "route_2", "route_3", "highway_a", "highway_b"]
        current_time = datetime.now()
        hour = current_time.hour
        day_of_week = current_time.weekday()
        
        for route in major_routes:
            # INTELLIGENT: Use historical patterns
            base_traffic = self._predict_traffic(route, hour, day_of_week)
            
            # Add some randomness
            traffic_level = max(0, min(100, base_traffic + random.randint(-15, 15)))
            
            # LEARNING: Store for future predictions
            self._learn_from_observation(route, hour, day_of_week, traffic_level)
            
            self.traffic_data[route] = {
                "traffic_level": traffic_level,
                "predicted_level": base_traffic,
                "confidence": self._calculate_confidence(route),
                "estimated_delay": traffic_level * 0.5,
                "last_updated": time.time(),
                "status": self._get_traffic_status(traffic_level)
            }
    
    def _get_traffic_status(self, level):
        """Convert traffic level to status"""
        if level < 30:
            return "clear"
        elif level < 60:
            return "moderate"
        elif level < 80:
            return "heavy"
        else:
            return "severe"
    
    def check_for_alerts(self):
        """INTELLIGENT: Check for alerts with predictions"""
        alerts_sent = False
        predictions_made = False
        
        for route, data in self.traffic_data.items():
            # Current alerts
            if data["status"] in ["heavy", "severe"]:
                self.broadcast_traffic_alert(route, data)
                alerts_sent = True
            
            # INTELLIGENT: Predictive alerts
            future_prediction = self.predict_future_traffic(route, 1)
            if future_prediction['predicted_level'] > 70 and data["traffic_level"] < 50:
                print(f"\n🔮 Predictive Alert: {route} will have heavy traffic in 1 hour")
                print(f"   Current: {data['traffic_level']}% → Predicted: {future_prediction['predicted_level']}%")
                print(f"   Confidence: {future_prediction['confidence']:.0%}")
                predictions_made = True
        
        if not alerts_sent and not predictions_made:
            clear_routes = [r for r, d in self.traffic_data.items() if d["status"] == "clear"]
            if clear_routes:
                print(f"\n✅ Traffic Status: All routes clear ({len(clear_routes)} routes monitored)")
    
    def broadcast_traffic_alert(self, route, traffic_data):
        """Send traffic alert to all delivery agents"""
        alert_data = {
            "route": route,
            "traffic_level": traffic_data["traffic_level"],
            "estimated_delay": traffic_data["estimated_delay"],
            "status": traffic_data["status"],
            "recommendation": self._get_recommendation(traffic_data["status"])
        }
        
        print(f"\n🚦 Traffic Alert: {traffic_data['status'].upper()} traffic on {route}")
        print(f"   Level: {traffic_data['traffic_level']}/100")
        print(f"   Estimated delay: {traffic_data['estimated_delay']:.1f} minutes")
        print(f"   Recommendation: {alert_data['recommendation']}")
        
        # Notify delivery agents directly
        from api.app import active_agents
        delivery_agents = [aid for aid in active_agents.keys() if 'delivery' in aid]
        
        for agent_id in delivery_agents:
            if agent_id in active_agents:
                agent = active_agents[agent_id]
                if hasattr(agent, 'process_message'):
                    agent.process_message({
                        'sender_id': self.agent_id,
                        'message_type': 'traffic_alert',
                        'data': alert_data
                    })
            self.send_message(agent_id, "traffic_alert", alert_data)
    
    def _get_recommendation(self, status):
        """Get recommendation based on traffic status"""
        recommendations = {
            "heavy": "Consider alternative routes",
            "severe": "Avoid this route, seek alternatives immediately"
        }
        return recommendations.get(status, "Monitor conditions")
    
    def get_route_conditions(self, route_id):
        """Get current conditions for specific route"""
        return self.traffic_data.get(route_id, {
            "traffic_level": 0,
            "estimated_delay": 0,
            "status": "unknown"
        })
    
    def process_message(self, message):
        """Handle incoming messages"""
        if message["message_type"] == "route_query":
            route_id = message["data"]["route_id"]
            conditions = self.get_route_conditions(route_id)
            
            # Send response back to requesting agent
            self.send_message(message["sender_id"], "route_conditions", {
                "route_id": route_id,
                "conditions": conditions
            })
        
        elif message["message_type"] == "incident_report":
            # Update traffic data based on reported incident
            incident_data = message["data"]
            affected_route = incident_data["route"]
            
            if affected_route in self.traffic_data:
                # Increase traffic level due to incident
                self.traffic_data[affected_route]["traffic_level"] = min(100, 
                    self.traffic_data[affected_route]["traffic_level"] + 30)
                self.traffic_data[affected_route]["status"] = self._get_traffic_status(
                    self.traffic_data[affected_route]["traffic_level"])
    
    def _predict_traffic(self, route, hour, day_of_week):
        """INTELLIGENT: Predict traffic based on patterns"""
        key = f"{route}_{hour}_{day_of_week}"
        
        if key not in self.prediction_model:
            # Initialize with reasonable defaults
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                return 70
            elif 22 <= hour or hour <= 6:  # Night
                return 20
            else:
                return 40
        
        return self.prediction_model[key]
    
    def _learn_from_observation(self, route, hour, day_of_week, observed_traffic):
        """LEARNING: Update predictions based on observations"""
        key = f"{route}_{hour}_{day_of_week}"
        
        if key not in self.prediction_model:
            self.prediction_model[key] = observed_traffic
        else:
            # Exponential moving average (simple learning)
            old_prediction = self.prediction_model[key]
            self.prediction_model[key] = (
                (1 - self.learning_rate) * old_prediction + 
                self.learning_rate * observed_traffic
            )
        
        # Store in history
        if route not in self.traffic_history:
            self.traffic_history[route] = []
        
        self.traffic_history[route].append({
            'timestamp': datetime.now(),
            'hour': hour,
            'day': day_of_week,
            'level': observed_traffic
        })
        
        # Keep only last 500 observations per route
        if len(self.traffic_history[route]) > 500:
            self.traffic_history[route] = self.traffic_history[route][-500:]
    
    def _calculate_confidence(self, route):
        """INTELLIGENT: Calculate prediction confidence"""
        if route not in self.traffic_history:
            return 0.3  # Low confidence without history
        
        history_length = len(self.traffic_history[route])
        
        if history_length < 10:
            return 0.4
        elif history_length < 50:
            return 0.6
        elif history_length < 100:
            return 0.8
        else:
            return 0.95
    
    def predict_future_traffic(self, route, hours_ahead=1):
        """INTELLIGENT: Predict traffic N hours in the future"""
        future_time = datetime.now() + timedelta(hours=hours_ahead)
        future_hour = future_time.hour
        future_day = future_time.weekday()
        
        predicted_level = self._predict_traffic(route, future_hour, future_day)
        confidence = self._calculate_confidence(route)
        
        return {
            'route': route,
            'predicted_time': future_time.isoformat(),
            'predicted_level': predicted_level,
            'confidence': confidence,
            'recommendation': self._get_recommendation_for_level(predicted_level)
        }
    
    def _get_recommendation_for_level(self, level):
        """INTELLIGENT: Provide smart recommendations"""
        if level < 30:
            return "Optimal time for delivery"
        elif level < 50:
            return "Good conditions, proceed as planned"
        elif level < 70:
            return "Moderate traffic, consider alternative routes"
        else:
            return "Heavy traffic predicted, strongly recommend rescheduling"
    
    def suggest_optimal_departure_time(self, route):
        """INTELLIGENT: Suggest best departure time"""
        best_time = None
        lowest_traffic = 100
        
        # Check next 6 hours
        for hours_ahead in range(0, 7):
            prediction = self.predict_future_traffic(route, hours_ahead)
            if prediction['predicted_level'] < lowest_traffic:
                lowest_traffic = prediction['predicted_level']
                best_time = prediction['predicted_time']
        
        return {
            'recommended_departure': best_time,
            'expected_traffic': lowest_traffic,
            'reason': f"Optimal window with {lowest_traffic}% traffic level"
        }
    
    def stop_monitoring(self):
        """Stop traffic monitoring"""
        self.monitoring = False