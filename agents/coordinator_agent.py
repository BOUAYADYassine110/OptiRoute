from .base_agent import BaseAgent
import requests

class CoordinatorAgent(BaseAgent):
    def __init__(self, agent_id="coordinator_001"):
        super().__init__(
            agent_id=agent_id,
            role="System Coordinator",
            goal="Maintain system balance and resolve conflicts between agents",
            backstory="Strategic overseer ensuring optimal system performance and conflict resolution"
        )
        self.active_agents = {}
        self.system_metrics = {}
    
    def register_agent(self, agent_id, agent_type, capabilities):
        """Register new agent in the system"""
        self.active_agents[agent_id] = {
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "last_seen": self.last_update.isoformat()
        }
    
    def redistribute_tasks(self, failed_agent_id):
        """Redistribute tasks when an agent fails"""
        # Get failed agent's assignments
        response = requests.get(f"http://localhost:5000/api/agent/{failed_agent_id}/assignments")
        
        if response.status_code == 200:
            assignments = response.json()["assignments"]
            
            for assignment in assignments:
                # Find best alternative agent
                best_agent = self.find_best_agent_for_task(assignment)
                if best_agent:
                    self.send_message(best_agent, "emergency_assignment", {
                        "order": assignment,
                        "reason": "agent_failure",
                        "original_agent": failed_agent_id
                    })
    
    def find_best_agent_for_task(self, task):
        """Find the most suitable agent for a task"""
        delivery_agents = [aid for aid, info in self.active_agents.items() 
                          if info["type"] == "delivery" and info["status"] == "active"]
        
        if not delivery_agents:
            return None
        
        # Simple selection based on proximity (in real implementation, use more sophisticated logic)
        return delivery_agents[0]
    
    def resolve_conflict(self, conflict_data):
        """Resolve conflicts between agents"""
        conflict_type = conflict_data["type"]
        
        if conflict_type == "assignment_dispute":
            # Arbitrate between competing agents
            agents = conflict_data["agents"]
            costs = conflict_data["costs"]
            
            # Select agent with lowest cost
            best_agent = min(agents, key=lambda a: costs[a])
            
            # Notify winner and losers
            for agent in agents:
                if agent == best_agent:
                    self.send_message(agent, "assignment_awarded", conflict_data["order"])
                else:
                    self.send_message(agent, "assignment_denied", {"reason": "higher_cost"})
    
    def monitor_system_health(self):
        """Monitor overall system performance"""
        # Collect metrics from all agents
        for agent_id in self.active_agents:
            try:
                response = requests.get(f"http://localhost:5000/api/agent/{agent_id}/metrics")
                if response.status_code == 200:
                    metrics = response.json()
                    self.system_metrics[agent_id] = metrics
            except:
                # Mark agent as potentially failed
                self.active_agents[agent_id]["status"] = "unresponsive"
    
    def process_message(self, message):
        """Handle incoming messages"""
        if message["message_type"] == "reassignment_request":
            order_id = message["data"]["order_id"]
            # Find new agent for the order
            best_agent = self.find_best_agent_for_task(message["data"])
            if best_agent:
                self.send_message(best_agent, "emergency_assignment", message["data"])
        
        elif message["message_type"] == "conflict_report":
            self.resolve_conflict(message["data"])
        
        elif message["message_type"] == "agent_registration":
            agent_data = message["data"]
            self.register_agent(agent_data["agent_id"], agent_data["type"], agent_data["capabilities"])