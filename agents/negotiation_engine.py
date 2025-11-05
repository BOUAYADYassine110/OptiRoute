"""
Simple negotiation engine for agent communication
Replaces CrewAI functionality with lightweight implementation
"""

class NegotiationEngine:
    def __init__(self):
        self.active_negotiations = {}
        self.agent_registry = {}
    
    def register_agent(self, agent_id, agent_instance):
        """Register agent for negotiations"""
        self.agent_registry[agent_id] = agent_instance
    
    def start_negotiation(self, negotiation_id, participants, task_data):
        """Start negotiation between agents"""
        self.active_negotiations[negotiation_id] = {
            'participants': participants,
            'task_data': task_data,
            'bids': {},
            'status': 'active'
        }
        
        # Request bids from all participants
        for agent_id in participants:
            if agent_id in self.agent_registry:
                agent = self.agent_registry[agent_id]
                if hasattr(agent, 'calculate_delivery_cost'):
                    cost = agent.calculate_delivery_cost(task_data)
                    self.submit_bid(negotiation_id, agent_id, cost)
    
    def submit_bid(self, negotiation_id, agent_id, bid_value):
        """Submit bid for negotiation"""
        if negotiation_id in self.active_negotiations:
            self.active_negotiations[negotiation_id]['bids'][agent_id] = bid_value
    
    def resolve_negotiation(self, negotiation_id):
        """Resolve negotiation and select winner"""
        if negotiation_id not in self.active_negotiations:
            return None
        
        negotiation = self.active_negotiations[negotiation_id]
        bids = negotiation['bids']
        
        if not bids:
            return None
        
        # Select agent with lowest cost
        winner = min(bids.keys(), key=lambda x: bids[x])
        
        negotiation['status'] = 'resolved'
        negotiation['winner'] = winner
        
        return {
            'winner': winner,
            'winning_bid': bids[winner],
            'all_bids': bids
        }

# Global negotiation engine
negotiation_engine = NegotiationEngine()