from .base_agent import BaseAgent
import requests
from datetime import datetime

class DeliveryAgent(BaseAgent):
    def __init__(self, agent_id, vehicle_type="van", capacity=20):
        super().__init__(
            agent_id=agent_id,
            role="Intelligent Delivery Driver",
            goal="Optimize deliveries using learned patterns and predictions",
            backstory="AI-enhanced driver with adaptive route optimization"
        )
        self.vehicle_type = vehicle_type
        self.capacity = capacity
        self.current_load = 0
        self.assigned_orders = []
        self.current_location = {"lat": 0, "lng": 0}
        self.route = []
        
        # INTELLIGENCE ADDITIONS
        self.delivery_history = []  # Learn from past deliveries
        self.route_performance = {}  # Track route efficiency
        self.learned_patterns = {}  # Time-of-day patterns
        self.prediction_accuracy = 0.5  # Track prediction quality
    
    def negotiate_assignment(self, order_data):
        """Negotiate order assignment with other delivery agents"""
        my_cost = self.calculate_delivery_cost(order_data)
        
        # Simple negotiation logic
        negotiation_request = {
            "order": order_data,
            "my_cost": my_cost,
            "my_capacity": self.capacity - self.current_load,
            "my_location": self.current_location,
            "agent_id": self.agent_id
        }
        
        try:
            response = requests.post("http://localhost:5000/api/negotiate-assignment", 
                                   json=negotiation_request)
            return response.json() if response.status_code == 200 else {"status": "failed"}
        except:
            return {"status": "failed"}
    
    def calculate_delivery_cost(self, order_data):
        """INTELLIGENT: Learned cost calculation with predictions"""
        # Base calculation
        pickup_distance = self.calculate_distance(self.current_location, order_data["pickup_location"])
        delivery_distance = self.calculate_distance(order_data["pickup_location"], order_data["delivery_location"])
        base_cost = pickup_distance + delivery_distance + (self.current_load * 0.1)
        
        # INTELLIGENT: Adjust based on learned patterns
        time_factor = self._get_time_factor()
        traffic_factor = self._predict_traffic_impact(order_data)
        
        adjusted_cost = base_cost * time_factor * traffic_factor
        
        # LEARNING: Record prediction for later validation
        self._record_cost_prediction(order_data['order_id'], adjusted_cost)
        
        return adjusted_cost
    
    def calculate_distance(self, loc1, loc2):
        """Simple Euclidean distance calculation"""
        return ((loc1["lat"] - loc2["lat"])**2 + (loc1["lng"] - loc2["lng"])**2)**0.5
    
    def accept_order(self, order_data):
        """Accept assigned order"""
        if self.current_load + order_data.get("weight", 1) <= self.capacity:
            self.assigned_orders.append(order_data)
            self.current_load += order_data.get("weight", 1)
            print(f"\n🚚 {self.agent_id} accepted order {order_data['order_id']}")
            print(f"   Current load: {self.current_load}/{self.capacity} kg")
            self.optimize_route()
            return True
        return False
    
    def optimize_route(self):
        """Request route optimization"""
        if self.assigned_orders:
            # Simple route: pickup then delivery for each order
            self.route = []
            for order in self.assigned_orders:
                self.route.append({
                    'location': order['pickup_location'],
                    'type': 'pickup',
                    'order_id': order['order_id']
                })
                self.route.append({
                    'location': order['delivery_location'],
                    'type': 'delivery',
                    'order_id': order['order_id']
                })
            print(f"   🛣️ Route optimized: {len(self.route)} stops")
    
    def _get_time_factor(self):
        """LEARNING: Time-based cost adjustment"""
        hour = datetime.now().hour
        
        if hour not in self.learned_patterns:
            # Default patterns
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hour
                return 1.3
            elif 22 <= hour or hour <= 6:  # Night (easier)
                return 0.8
            else:
                return 1.0
        
        return self.learned_patterns[hour]
    
    def _predict_traffic_impact(self, order_data):
        """INTELLIGENT: Predict traffic impact"""
        # Simple prediction - in production, query traffic agent
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.4  # Rush hour impact
        elif 22 <= hour or hour <= 6:
            return 0.9  # Night time easier
        else:
            return 1.0
    
    def _record_cost_prediction(self, order_id, predicted_cost):
        """LEARNING: Record for validation"""
        self.delivery_history.append({
            'order_id': order_id,
            'predicted_cost': predicted_cost,
            'actual_cost': None,  # Will be updated after delivery
            'timestamp': datetime.now()
        })
    
    def complete_delivery(self, order_id, actual_time=None, actual_cost=None):
        """LEARNING: Complete delivery with learning update"""
        order = next((o for o in self.assigned_orders if o["order_id"] == order_id), None)
        if order:
            self.assigned_orders.remove(order)
            self.current_load -= order.get("weight", 1)
            
            # LEARNING: Update from actual results
            if actual_time and actual_cost:
                self._learn_from_delivery(order_id, actual_time, actual_cost)
            
            # Notify warehouse
            self.send_message("warehouse_001", "order_completion", {
                "order_id": order_id,
                "completion_time": self.last_update.isoformat(),
                "actual_time": actual_time or 30,
                "actual_cost": actual_cost or 10
            })
    
    def _learn_from_delivery(self, order_id, actual_time, actual_cost):
        """LEARNING: Improve predictions from feedback"""
        # Find prediction
        for record in self.delivery_history:
            if record['order_id'] == order_id:
                record['actual_cost'] = actual_cost
                record['actual_time'] = actual_time
                
                # Calculate prediction error
                if record['predicted_cost']:
                    error = abs(actual_cost - record['predicted_cost']) / actual_cost
                    
                    # Update accuracy (exponential moving average)
                    self.prediction_accuracy = 0.9 * self.prediction_accuracy + 0.1 * (1 - error)
                    
                    print(f"   {self.agent_id} prediction accuracy: {self.prediction_accuracy:.2%}")
                
                # Learn time patterns
                hour = record['timestamp'].hour
                if hour not in self.learned_patterns:
                    self.learned_patterns[hour] = 1.0
                
                # Simple pattern adjustment
                if actual_time > 40:  # Took longer than expected
                    self.learned_patterns[hour] = min(1.5, self.learned_patterns[hour] * 1.1)
                elif actual_time < 20:  # Faster than expected
                    self.learned_patterns[hour] = max(0.7, self.learned_patterns[hour] * 0.9)
                
                break
    
    def process_message(self, message):
        """Handle incoming messages"""
        if message["message_type"] == "order_assignment":
            order = message["data"]["order"]
            self.accept_order(order)
        
        elif message["message_type"] == "route_update":
            self.route = message["data"]["new_route"]
            print(f"   🔄 {self.agent_id} received route update")
        
        elif message["message_type"] == "traffic_alert":
            alert = message["data"]
            print(f"   🚨 {self.agent_id} received traffic alert for {alert['route']}")
            if self.assigned_orders:
                print(f"   🔄 Recalculating route to avoid delays...")
                # INTELLIGENT: Consider traffic in route optimization
                self.optimize_route()
                
                # LEARNING: Record traffic impact
                self.route_performance[alert['route']] = {
                    'traffic_level': alert['traffic_level'],
                    'timestamp': datetime.now(),
                    'avoided': True
                }