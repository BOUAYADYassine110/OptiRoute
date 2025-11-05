from .base_agent import BaseAgent
from datetime import datetime
import requests

class ClientAgent(BaseAgent):
    def __init__(self, agent_id, client_name, preferences=None):
        super().__init__(
            agent_id=agent_id,
            role="Intelligent Client",
            goal="Express needs and constraints while optimizing delivery experience",
            backstory="AI-powered client agent that learns preferences and negotiates optimal delivery terms"
        )
        self.client_name = client_name
        self.preferences = preferences or {
            'preferred_time': 'morning',
            'max_cost': 100,
            'urgency': 'normal',
            'delivery_instructions': ''
        }
        self.order_history = []
        self.satisfaction_scores = []
        self.learned_patterns = {}
    
    def create_order_request(self, pickup_address, delivery_address, weight, notes=""):
        """INTELLIGENT: Create optimized order request"""
        order_request = {
            'client_id': self.agent_id,
            'client_name': self.client_name,
            'pickup_address': pickup_address,
            'delivery_address': delivery_address,
            'weight': weight,
            'notes': notes,
            'preferences': self._get_optimized_preferences(),
            'timestamp': datetime.now().isoformat()
        }
        
        # LEARNING: Apply learned patterns
        if self.learned_patterns:
            order_request['preferred_time'] = self._predict_optimal_time()
            order_request['max_acceptable_cost'] = self._calculate_acceptable_cost(weight)
        
        print(f"Client {self.client_name} created order request:")
        print(f"  From: {pickup_address}")
        print(f"  To: {delivery_address}")
        print(f"  Preferences: {order_request['preferences']}")
        
        return order_request
    
    def _get_optimized_preferences(self):
        """INTELLIGENT: Get preferences based on learning"""
        current_hour = datetime.now().hour
        
        # Adapt preferences based on time
        if 7 <= current_hour <= 9:
            urgency = 'high'  # Morning rush
        elif 17 <= current_hour <= 19:
            urgency = 'medium'  # Evening
        else:
            urgency = 'normal'
        
        return {
            'preferred_time': self._get_preferred_time(),
            'max_cost': self.preferences['max_cost'],
            'urgency': urgency,
            'delivery_instructions': self.preferences['delivery_instructions']
        }
    
    def _get_preferred_time(self):
        """LEARNING: Learn optimal delivery times"""
        if 'optimal_time' in self.learned_patterns:
            return self.learned_patterns['optimal_time']
        return self.preferences['preferred_time']
    
    def _predict_optimal_time(self):
        """INTELLIGENT: Predict best delivery time"""
        # Analyze historical satisfaction by time
        if len(self.satisfaction_scores) < 3:
            return self.preferences['preferred_time']
        
        # Simple learning: prefer times with higher satisfaction
        time_satisfaction = {}
        for i, score in enumerate(self.satisfaction_scores[-10:]):
            order = self.order_history[-(10-i)]
            time_slot = order.get('actual_delivery_time', 'morning')
            if time_slot not in time_satisfaction:
                time_satisfaction[time_slot] = []
            time_satisfaction[time_slot].append(score)
        
        # Find time with highest average satisfaction
        best_time = 'morning'
        best_score = 0
        for time_slot, scores in time_satisfaction.items():
            avg_score = sum(scores) / len(scores)
            if avg_score > best_score:
                best_score = avg_score
                best_time = time_slot
        
        return best_time
    
    def _calculate_acceptable_cost(self, weight):
        """LEARNING: Calculate acceptable cost based on experience"""
        if not self.order_history:
            return self.preferences['max_cost']
        
        # Learn from past orders
        recent_orders = self.order_history[-5:]
        avg_cost_per_kg = sum(o.get('actual_cost', 0) / max(1, o.get('weight', 1)) for o in recent_orders) / len(recent_orders)
        
        # Add 20% buffer for negotiation
        acceptable_cost = avg_cost_per_kg * weight * 1.2
        return min(acceptable_cost, self.preferences['max_cost'])
    
    def negotiate_terms(self, initial_quote):
        """INTELLIGENT: Negotiate delivery terms"""
        print(f"Client {self.client_name} negotiating quote: ${initial_quote['cost']}")
        
        acceptable_cost = self._calculate_acceptable_cost(initial_quote.get('weight', 1))
        
        if initial_quote['cost'] <= acceptable_cost:
            print(f"  Accepted quote: ${initial_quote['cost']}")
            return {'accepted': True, 'counter_offer': None}
        
        # Counter-offer
        counter_cost = acceptable_cost * 0.9  # Negotiate down
        counter_offer = {
            'cost': counter_cost,
            'delivery_time': self._get_preferred_time(),
            'special_instructions': self.preferences['delivery_instructions']
        }
        
        print(f"  Counter-offer: ${counter_cost}")
        return {'accepted': False, 'counter_offer': counter_offer}
    
    def provide_feedback(self, order_id, delivery_time, actual_cost, service_quality):
        """LEARNING: Provide feedback and learn"""
        satisfaction_score = self._calculate_satisfaction(delivery_time, actual_cost, service_quality)
        
        self.satisfaction_scores.append(satisfaction_score)
        
        # Update order history
        for order in self.order_history:
            if order.get('order_id') == order_id:
                order.update({
                    'actual_delivery_time': delivery_time,
                    'actual_cost': actual_cost,
                    'service_quality': service_quality,
                    'satisfaction': satisfaction_score
                })
                break
        
        # LEARNING: Update patterns
        self._update_learned_patterns(delivery_time, satisfaction_score)
        
        print(f"Client {self.client_name} feedback:")
        print(f"  Satisfaction: {satisfaction_score:.1f}/5.0")
        print(f"  Learning updated: {len(self.learned_patterns)} patterns")
        
        return satisfaction_score
    
    def _calculate_satisfaction(self, delivery_time, actual_cost, service_quality):
        """Calculate satisfaction score (1-5)"""
        score = 3.0  # Base satisfaction
        
        # Time satisfaction
        if delivery_time == self.preferences['preferred_time']:
            score += 0.5
        
        # Cost satisfaction
        if actual_cost <= self.preferences['max_cost'] * 0.8:
            score += 0.5
        elif actual_cost > self.preferences['max_cost']:
            score -= 1.0
        
        # Service quality (1-5 scale)
        score += (service_quality - 3) * 0.5
        
        return max(1.0, min(5.0, score))
    
    def _update_learned_patterns(self, delivery_time, satisfaction_score):
        """LEARNING: Update learned patterns"""
        if satisfaction_score >= 4.0:
            self.learned_patterns['optimal_time'] = delivery_time
        
        # Update cost expectations
        if len(self.satisfaction_scores) >= 5:
            avg_satisfaction = sum(self.satisfaction_scores[-5:]) / 5
            if avg_satisfaction >= 4.0:
                # Satisfied with recent service, can be more flexible on cost
                self.preferences['max_cost'] *= 1.05
            elif avg_satisfaction <= 2.5:
                # Not satisfied, reduce max cost
                self.preferences['max_cost'] *= 0.95
    
    def process_message(self, message):
        """Handle incoming messages"""
        if message["message_type"] == "quote_offer":
            quote = message["data"]
            response = self.negotiate_terms(quote)
            
            # Send response back
            self.send_message(message["sender_id"], "quote_response", response)
        
        elif message["message_type"] == "delivery_update":
            update = message["data"]
            print(f"Client {self.client_name} received update: {update['status']}")
        
        elif message["message_type"] == "delivery_completed":
            completion = message["data"]
            # Automatically provide feedback
            self.provide_feedback(
                completion["order_id"],
                completion.get("delivery_time", "unknown"),
                completion.get("cost", 0),
                completion.get("service_quality", 3)
            )
    
    def get_client_profile(self):
        """Get client profile for system optimization"""
        return {
            'client_id': self.agent_id,
            'name': self.client_name,
            'preferences': self.preferences,
            'order_count': len(self.order_history),
            'avg_satisfaction': sum(self.satisfaction_scores) / max(1, len(self.satisfaction_scores)),
            'learned_patterns': self.learned_patterns,
            'loyalty_score': self._calculate_loyalty_score()
        }
    
    def _calculate_loyalty_score(self):
        """Calculate client loyalty score (0-100)"""
        if len(self.satisfaction_scores) < 3:
            return 50  # Neutral for new clients
        
        recent_satisfaction = sum(self.satisfaction_scores[-5:]) / min(5, len(self.satisfaction_scores))
        order_frequency = min(len(self.order_history) / 10, 1.0)  # Max 1.0 for 10+ orders
        
        loyalty = (recent_satisfaction / 5.0) * 70 + order_frequency * 30
        return min(100, max(0, loyalty))