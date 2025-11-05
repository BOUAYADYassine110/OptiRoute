from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Import and register blueprints
from api.chat_api import chat_bp
from api.route_api import route_api_bp
from api.auth_api import auth_api_bp
app.register_blueprint(chat_bp)
app.register_blueprint(route_api_bp)
app.register_blueprint(auth_api_bp)

jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# MongoDB connection (optional)
try:
    from pymongo import MongoClient
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/optiroute'), serverSelectionTimeoutMS=2000)
    client.server_info()  # Test connection
    db = client.optiroute
    print("MongoDB connected")
except:
    db = None
    print("MongoDB not available - using in-memory storage")

# Agent registry
active_agents = {}

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Multi-Agent Delivery System',
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({'status': 'Backend is working', 'endpoints': ['chat', 'route', 'auth']})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple auth (implement proper authentication in production)
    if username and password:
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/orders/create', methods=['POST'])
def create_order_simple():
    try:
        order_data = request.get_json()
        order_data['created_at'] = datetime.now().isoformat()
        order_data['status'] = 'pending'
        
        if db:
            try:
                result = db.orders.insert_one(order_data.copy())
                order_id = str(result.inserted_id)
            except Exception as e:
                print(f'DB insert error: {e}')
                order_id = order_data.get('order_id', 'ORD_' + str(int(datetime.now().timestamp())))
        else:
            order_id = order_data.get('order_id', 'ORD_' + str(int(datetime.now().timestamp())))
        
        if 'warehouse_001' in active_agents:
            try:
                active_agents['warehouse_001'].receive_order(order_data)
            except Exception as e:
                print(f'Warehouse agent error: {e}')
        
        # Emit real-time update
        socketio.emit('order_update', {
            'order_id': order_id,
            'status': 'pending',
            'message': 'Order created successfully'
        })
        
        return jsonify({'order_id': order_id, 'status': 'created'})
    except Exception as e:
        print(f'Order creation error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    if db:
        try:
            order = db.orders.find_one({'_id': order_id})
            if order:
                order['_id'] = str(order['_id'])
                return jsonify(order)
        except:
            pass
    return jsonify({'error': 'Order not found'}), 404

@app.route('/api/agent/<agent_id>/message', methods=['POST'])
def send_agent_message(agent_id):
    try:
        message_data = request.get_json()
        
        if agent_id in active_agents:
            try:
                active_agents[agent_id].process_message(message_data)
                return jsonify({'status': 'delivered'})
            except Exception as e:
                print(f'Agent message error: {e}')
                return jsonify({'status': 'error', 'message': str(e)})
        
        return jsonify({'error': 'Agent not found'}), 404
    except Exception as e:
        print(f'Send agent message error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/register', methods=['POST'])
def register_agent():
    agent_data = request.get_json()
    agent_id = agent_data['agent_id']
    
    # Store agent reference (in real implementation, this would be more sophisticated)
    active_agents[agent_id] = agent_data
    
    return jsonify({'status': 'registered'})

@app.route('/api/agents/delivery', methods=['GET'])
def get_delivery_agents():
    try:
        delivery_agents = [aid for aid in active_agents.keys() 
                          if 'delivery' in aid]
        return jsonify({'agents': delivery_agents})
    except Exception as e:
        print(f'Get delivery agents error: {e}')
        return jsonify({'agents': []})

@app.route('/api/optimize-assignment', methods=['POST'])
def optimize_assignment():
    try:
        data = request.get_json()
        order_data = data.get('order', {})
        
        # Simple assignment logic
        delivery_agents = [aid for aid in active_agents.keys() 
                          if 'delivery' in aid]
        
        if delivery_agents:
            # For now, assign to first available agent
            assigned_agent = delivery_agents[0]
            return jsonify({'delivery_agent_id': assigned_agent})
        
        return jsonify({'error': 'No available agents'}), 404
    except Exception as e:
        print(f'Optimize assignment error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    route_data = request.get_json()
    
    # Simple route optimization (OR-Tools optional)
    try:
        from optimization.route_optimizer import optimize_delivery_route
        optimized_route = optimize_delivery_route(
            route_data['current_location'],
            route_data['orders']
        )
    except:
        # Fallback: simple sequential route
        optimized_route = []
        for order in route_data.get('orders', []):
            optimized_route.append({
                'location': order.get('pickup_location'),
                'type': 'pickup',
                'order_id': order.get('order_id')
            })
            optimized_route.append({
                'location': order.get('delivery_location'),
                'type': 'delivery',
                'order_id': order.get('order_id')
            })
    
    return jsonify({'route': optimized_route})

@app.route('/api/traffic/update', methods=['POST'])
def update_traffic():
    traffic_data = request.get_json()
    traffic_data['timestamp'] = datetime.now()
    
    if db:
        try:
            db.traffic_updates.insert_one(traffic_data)
        except:
            pass
    
    if 'traffic_001' in active_agents:
        active_agents['traffic_001'].process_message({
            'message_type': 'traffic_update',
            'data': traffic_data
        })
    
    return jsonify({'status': 'updated'})

@app.route('/api/traffic/status', methods=['GET'])
def get_traffic_status():
    if db:
        try:
            traffic_data = list(db.traffic_updates.find().sort('timestamp', -1).limit(10))
            for item in traffic_data:
                item['_id'] = str(item['_id'])
                if 'timestamp' in item and hasattr(item['timestamp'], 'isoformat'):
                    item['timestamp'] = item['timestamp'].isoformat()
            return jsonify({'traffic_data': traffic_data})
        except Exception as e:
            print(f'Traffic DB error: {e}')
    return jsonify({'traffic_data': []})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'msg': 'Connected to OptiroRoute system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('agent_update')
def handle_agent_update(data):
    # Broadcast agent updates to connected clients
    emit('agent_status', data, broadcast=True)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)