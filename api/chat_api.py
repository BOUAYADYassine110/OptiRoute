"""
Chat API - Natural language order processing
"""

from flask import Blueprint, request, jsonify

try:
    from services.geocoding_service import geocoding_service
except ImportError as e:
    print(f'Geocoding service import error: {e}')
    geocoding_service = None

try:
    from services.llm_service import llm_service
except ImportError as e:
    print(f'LLM service import error: {e}')
    llm_service = None

chat_bp = Blueprint('chat', __name__)

def parse_order_from_text(text):
    """Extract order details from natural language using LLM"""
    if llm_service:
        return llm_service.extract_order_details(text)
    else:
        # Fallback regex parsing
        import re
        pattern = r'from\s+(.+?)\s+to\s+(.+?)(?:\s*\d+\s*kg|\s*,|\.|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return {
                'pickup_address': match.group(1).strip(),
                'delivery_address': match.group(2).strip(),
                'weight': 1.0,
                'success': True
            }
        return {'success': False, 'message': 'Could not parse order'}

def calculate_cost_and_time(distance_km, weight):
    """Calculate delivery cost and estimated time"""
    # Base cost: $5
    # Distance cost: $2 per km
    # Weight cost: $1 per kg
    base_cost = 5.0
    distance_cost = distance_km * 2.0
    weight_cost = weight * 1.0
    total_cost = base_cost + distance_cost + weight_cost
    
    # Estimated time: 3 minutes per km (20 km/h average)
    estimated_minutes = distance_km * 3
    
    return {
        'cost': round(total_cost, 2),
        'estimated_time': round(estimated_minutes, 0),
        'breakdown': {
            'base': base_cost,
            'distance': round(distance_cost, 2),
            'weight': round(weight_cost, 2)
        }
    }

def calculate_distance(loc1, loc2):
    """Calculate distance between two coordinates (Haversine)"""
    import math
    
    lat1, lon1 = math.radians(loc1['lat']), math.radians(loc1['lng'])
    lat2, lon2 = math.radians(loc2['lat']), math.radians(loc2['lng'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c
    
    return distance_km

@chat_bp.route('/api/chat/process', methods=['POST'])
def process_chat_message():
    """Process natural language order request"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        print(f"Chat: {message}")
        
        # Parse the message
        parsed = parse_order_from_text(message)
        
        print(f"Parsed: {parsed}")
        
        if not parsed.get('success') or not parsed.get('pickup_address') or not parsed.get('delivery_address'):
            return jsonify({
                'success': False,
                'message': parsed.get('message', 'I need both pickup and delivery locations. Try: "Send a package from [address] to [address]"')
            })
        
        print(f"Geocoding...")
        
        # Geocode addresses
        if geocoding_service:
            pickup_geo = geocoding_service.geocode_address(parsed['pickup_address'])
            delivery_geo = geocoding_service.geocode_address(parsed['delivery_address'])
        else:
            # Fallback coordinates
            pickup_geo = {'lat': 40.7128, 'lng': -74.0060, 'address': parsed['pickup_address'], 'success': True}
            delivery_geo = {'lat': 40.7589, 'lng': -73.9851, 'address': parsed['delivery_address'], 'success': True}
        
        print(f"Pickup: {pickup_geo.get('address', 'Not found')}")
        print(f"Delivery: {delivery_geo.get('address', 'Not found')}")
        
        if not pickup_geo['success'] or not delivery_geo['success']:
            return jsonify({
                'success': False,
                'message': 'Could not find one or both addresses. Please be more specific.'
            })
        
        # Calculate distance, cost, and time
        distance = calculate_distance(pickup_geo, delivery_geo)
        pricing = calculate_cost_and_time(distance, parsed.get('weight', 1.0))
        
        # Create order preview
        order_preview = {
            'pickup_location': pickup_geo,
            'delivery_location': delivery_geo,
            'weight': parsed.get('weight', 1.0),
            'notes': parsed.get('notes', ''),
            'distance_km': round(distance, 2),
            'cost': pricing['cost'],
            'estimated_time': pricing['estimated_time'],
            'cost_breakdown': pricing['breakdown']
        }
        
        print(f"Preview: ${pricing['cost']}, {pricing['estimated_time']} min")
        
        msg = f"Order Summary:\\n\\n"
        msg += f"From: {pickup_geo['address']}\\n"
        msg += f"To: {delivery_geo['address']}\\n"
        msg += f"Distance: {order_preview['distance_km']} km\\n"
        msg += f"Weight: {parsed.get('weight', 1.0)} kg\\n\\n"
        msg += f"Cost: ${pricing['cost']}\\n"
        msg += f"Time: {pricing['estimated_time']} min\\n\\n"
        msg += f"Confirm to place order?"
        
        return jsonify({
            'success': True,
            'message': msg,
            'order_preview': order_preview
        })
    except Exception as e:
        print(f"Chat processing error: {e}")
        return jsonify({
            'success': False,
            'message': 'Sorry, I had trouble processing that. Please try again.'
        }), 500

@chat_bp.route('/api/chat/confirm', methods=['POST'])
def confirm_order():
    """Confirm and create order from preview"""
    try:
        data = request.get_json()
        order_preview = data.get('order_preview')
        
        if not order_preview:
            return jsonify({'success': False, 'message': 'No order to confirm'})
        
        # Create order
        import time
        order_data = {
            'order_id': f"ORD_{int(time.time())}",
            'pickup_location': order_preview['pickup_location'],
            'delivery_location': order_preview['delivery_location'],
            'weight': order_preview['weight'],
            'estimated_cost': order_preview['cost'],
            'estimated_time': order_preview['estimated_time'],
            'status': 'pending'
        }
        
        # Send to warehouse agent
        from api.app import active_agents, socketio
        if 'warehouse_001' in active_agents:
            try:
                active_agents['warehouse_001'].receive_order(order_data)
            except Exception as e:
                print(f"Warehouse agent error: {e}")
        
        # Emit WebSocket update
        socketio.emit('order_update', {
            'order_id': order_data['order_id'],
            'status': 'pending',
            'message': 'Order created successfully'
        })
        
        return jsonify({
            'success': True,
            'order_id': order_data['order_id'],
            'message': f"Order {order_data['order_id']} created! Track it in real-time."
        })
    except Exception as e:
        print(f"Order confirmation error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create order. Please try again.'
        }), 500