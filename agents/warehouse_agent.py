from .base_agent import BaseAgent
from datetime import datetime

class WarehouseAgent(BaseAgent):
    def __init__(self, agent_id="warehouse_001"):
        super().__init__(
            agent_id=agent_id,
            role="Intelligent Warehouse Manager",
            goal="Optimize order distribution using multi-factor analysis and learning",
            backstory="AI-powered logistics optimizer with learning capabilities"
        )
        self.pending_orders = []
        self.assigned_orders = {}
        
        # INTELLIGENCE ADDITIONS
        self.agent_performance = {}  # Track agent success rates
        self.assignment_history = []  # Learn from past assignments
        self.optimization_weights = {
            'distance': 0.4,
            'capacity': 0.3,
            'performance': 0.2,
            'current_load': 0.1
        }
    
    def receive_order(self, order_data):
        """INTELLIGENT: Optimal agent selection with multi-factor analysis"""
        self.pending_orders.append(order_data)
        print(f"📦 Warehouse received order: {order_data['order_id']}")
        print(f"   From: {order_data['pickup_location']['address']}")
        print(f"   To: {order_data['delivery_location']['address']}")
        
        from api.app import active_agents
        delivery_agents = [aid for aid in active_agents.keys() if 'delivery' in aid]
        
        if delivery_agents:
            # INTELLIGENT: Score each agent
            agent_scores = {}
            for agent_id in delivery_agents:
                agent = active_agents[agent_id]
                score = self._calculate_agent_score(agent, order_data)
                agent_scores[agent_id] = score
            
            # Select best agent
            best_agent = max(agent_scores, key=agent_scores.get)
            
            print(f"   🧠 Agent scores: {agent_scores}")
            print(f"   ✅ Selected {best_agent} (score: {agent_scores[best_agent]:.2f})")
            
            self.assign_order(order_data["order_id"], best_agent)
            
            # LEARNING: Record assignment
            self._record_assignment(order_data["order_id"], best_agent, agent_scores[best_agent])
            
            return {"delivery_agent_id": best_agent, "status": "assigned", "score": agent_scores[best_agent]}
        
        return {"status": "pending", "message": "No agents available"}
    
    def assign_order(self, order_id, delivery_agent_id):
        """Assign order to specific delivery agent"""
        order = next((o for o in self.pending_orders if o["order_id"] == order_id), None)
        if order:
            self.assigned_orders[order_id] = delivery_agent_id
            self.pending_orders.remove(order)
            print(f"   ✅ Assigned to {delivery_agent_id}")
            
            # Notify delivery agent directly
            from api.app import active_agents
            if delivery_agent_id in active_agents:
                agent = active_agents[delivery_agent_id]
                if hasattr(agent, 'accept_order'):
                    agent.accept_order(order)
            
            self.send_message(delivery_agent_id, "order_assignment", {
                "order": order,
                "assignment_time": self.last_update.isoformat()
            })
    
    def _calculate_agent_score(self, agent, order_data):
        """INTELLIGENT: Multi-factor scoring system"""
        try:
            score = 0
            
            # Factor 1: Distance (closer is better)
            if hasattr(agent, 'current_location') and hasattr(agent, 'calculate_distance'):
                distance = agent.calculate_distance(agent.current_location, order_data['pickup_location'])
                distance_score = max(0, 100 - distance * 10)
            else:
                distance_score = 50  # Default score
            score += distance_score * self.optimization_weights['distance']
            
            # Factor 2: Capacity (more available capacity is better)
            if hasattr(agent, 'capacity') and hasattr(agent, 'current_load'):
                capacity_available = agent.capacity - agent.current_load
                capacity_score = (capacity_available / agent.capacity) * 100
            else:
                capacity_score = 75  # Default good score
            score += capacity_score * self.optimization_weights['capacity']
            
            # Factor 3: Performance history (better performers get priority)
            performance_score = self._get_agent_performance(agent.agent_id)
            score += performance_score * self.optimization_weights['performance']
            
            # Factor 4: Current load (less loaded agents preferred)
            if hasattr(agent, 'capacity') and hasattr(agent, 'current_load'):
                load_score = (1 - agent.current_load / agent.capacity) * 100
            else:
                load_score = 75  # Default good score
            score += load_score * self.optimization_weights['current_load']
            
            return score
        except Exception as e:
            print(f"Agent scoring error: {e}")
            return 50  # Default neutral score
    
    def _get_agent_performance(self, agent_id):
        """LEARNING: Get agent's historical performance"""
        if agent_id not in self.agent_performance:
            return 50  # Neutral score for new agents
        
        perf = self.agent_performance[agent_id]
        success_rate = perf['successful'] / max(1, perf['total'])
        avg_time = perf.get('avg_delivery_time', 30)
        
        # Score based on success rate and speed
        return (success_rate * 70) + (30 if avg_time < 30 else 15)
    
    def _record_assignment(self, order_id, agent_id, score):
        """LEARNING: Record for future optimization"""
        self.assignment_history.append({
            'order_id': order_id,
            'agent_id': agent_id,
            'score': score,
            'timestamp': datetime.now()
        })
        
        # Keep last 500 assignments
        if len(self.assignment_history) > 500:
            self.assignment_history = self.assignment_history[-500:]
    
    def update_agent_performance(self, agent_id, order_id, success, delivery_time):
        """LEARNING: Update performance metrics"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {
                'total': 0,
                'successful': 0,
                'avg_delivery_time': 0,
                'total_time': 0
            }
        
        perf = self.agent_performance[agent_id]
        perf['total'] += 1
        if success:
            perf['successful'] += 1
        perf['total_time'] += delivery_time
        perf['avg_delivery_time'] = perf['total_time'] / perf['total']
        
        print(f"   Updated {agent_id} performance: {perf['successful']}/{perf['total']} success rate")
    
    def process_message(self, message):
        """Handle incoming messages with learning"""
        if message["message_type"] == "order_completion":
            order_id = message["data"]["order_id"]
            agent_id = self.assigned_orders.get(order_id)
            
            if agent_id:
                # LEARNING: Update performance
                delivery_time = message["data"].get("actual_time", 30)
                self.update_agent_performance(agent_id, order_id, True, delivery_time)
                del self.assigned_orders[order_id]
        
        elif message["message_type"] == "order_failure":
            order_id = message["data"]["order_id"]
            agent_id = self.assigned_orders.get(order_id)
            
            if agent_id:
                # LEARNING: Update performance (failure)
                self.update_agent_performance(agent_id, order_id, False, 60)
            
            # Reassign failed order
            self.send_message("coordinator_001", "reassignment_request", {
                "order_id": order_id,
                "reason": message["data"]["reason"]
            })