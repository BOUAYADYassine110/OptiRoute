"""
Authentication API - JWT-based user authentication
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta

auth_api_bp = Blueprint('auth_api', __name__)

# In-memory user store (in production, use database)
users_db = {
    'client1': {
        'password': generate_password_hash('password'),
        'role': 'client',
        'name': 'John Doe',
        'email': 'client1@example.com'
    },
    'delivery1': {
        'password': generate_password_hash('password'),
        'role': 'delivery',
        'name': 'Mike Driver',
        'email': 'delivery1@example.com'
    },
    'manager1': {
        'password': generate_password_hash('password'),
        'role': 'manager',
        'name': 'Sarah Manager',
        'email': 'manager1@example.com'
    }
}

@auth_api_bp.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = users_db.get(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create JWT token
    access_token = create_access_token(
        identity=username,
        expires_delta=timedelta(hours=24),
        additional_claims={
            'role': user['role'],
            'name': user['name']
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'username': username,
            'role': user['role'],
            'name': user['name'],
            'email': user['email']
        }
    })

@auth_api_bp.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'client')
    name = data.get('name')
    email = data.get('email')
    
    if not all([username, password, name, email]):
        return jsonify({'error': 'All fields required'}), 400
    
    if username in users_db:
        return jsonify({'error': 'Username already exists'}), 409
    
    # Create new user
    users_db[username] = {
        'password': generate_password_hash(password),
        'role': role,
        'name': name,
        'email': email
    }
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_api_bp.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    username = get_jwt_identity()
    user = users_db.get(username)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'username': username,
        'role': user['role'],
        'name': user['name'],
        'email': user['email']
    })

@auth_api_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout (client-side token removal)"""
    return jsonify({'message': 'Logged out successfully'})

@auth_api_bp.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token validity"""
    username = get_jwt_identity()
    user = users_db.get(username)
    
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    
    return jsonify({
        'valid': True,
        'user': {
            'username': username,
            'role': user['role'],
            'name': user['name']
        }
    })