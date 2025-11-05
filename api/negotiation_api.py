"""
API endpoints for agent negotiation
"""

from flask import Blueprint, request, jsonify
from agents.negotiation_engine import negotiation_engine
import uuid

negotiation_bp = Blueprint('negotiation', __name__)

@negotiation_bp.route('/api/negotiate-assignment', methods=['POST'])
def negotiate_assignment():
    """Handle assignment negotiation between agents"""
    data = request.get_json()
    
    # Create negotiation ID
    negotiation_id = str(uuid.uuid4())
    
    # Get all available delivery agents (mock for now)
    available_agents = ['delivery_001', 'delivery_002', 'delivery_003']
    
    # Start negotiation
    negotiation_engine.start_negotiation(
        negotiation_id, 
        available_agents, 
        data['order']
    )
    
    # Resolve immediately (in real system, this would be async)
    result = negotiation_engine.resolve_negotiation(negotiation_id)
    
    if result:
        return jsonify({
            'status': 'success',
            'assigned_agent': result['winner'],
            'cost': result['winning_bid']
        })
    else:
        return jsonify({
            'status': 'failed',
            'message': 'No agents available'
        }), 404