from abc import ABC, abstractmethod
import requests
import json
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, agent_id, role, goal, backstory):
        self.agent_id = agent_id
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.status = "active"
        self.last_update = datetime.now()
    
    def send_message(self, recipient_id, message_type, data):
        """Send message to another agent via API"""
        payload = {
            "sender_id": self.agent_id,
            "recipient_id": recipient_id,
            "message_type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        try:
            response = requests.post(f"http://localhost:5000/api/agent/{recipient_id}/message", 
                                   json=payload)
            return response.json()
        except Exception as e:
            print(f"Message send failed: {e}")
            return None
    
    @abstractmethod
    def process_message(self, message):
        """Process incoming message"""
        pass
    
    def update_status(self, status):
        self.status = status
        self.last_update = datetime.now()