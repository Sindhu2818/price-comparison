from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import User, db
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            pincode=data.get('pincode'),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/api/guest-access', methods=['POST'])
def guest_access():
    try:
        # Create temporary guest user
        guest_id = str(uuid.uuid4())
        guest_user = User(
            username=f'guest_{guest_id[:8]}',
            email=f'guest_{guest_id[:8]}@temp.com',
            is_guest=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        guest_user.set_password(guest_id)  # Random password
        
        db.session.add(guest_user)
        db.session.commit()
        
        # Generate tokens with shorter expiry for guests
        access_token = create_access_token(
            identity=str(guest_user.id),
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Guest access granted',
            'access_token': access_token,
            'user': guest_user.to_dict(),
            'is_guest': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({'access_token': new_token}), 200

@auth_bp.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    # In production, implement email sending with reset link
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    if user:
        # Generate reset token (simplified - use proper token generation in production)
        reset_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1)
        )
        # Send email with reset link (implement email service)
        return jsonify({
            'message': 'Reset link sent to email',
            'reset_token': reset_token  # In production, don't return token
        }), 200
    
    return jsonify({'error': 'Email not found'}), 404

@auth_bp.route('/api/reset-password', methods=['POST'])
@jwt_required()
def reset_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/api/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Admin endpoint to view all registered users"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.email != 'admin@example.com':
            return jsonify({'error': 'Admin access required'}), 403

        users = User.query.all()
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'pincode': user.pincode,
            'is_guest': user.is_guest,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        } for user in users]
        
        return jsonify({'users': users_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/api/user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a specific user account"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        # Allow admin OR the user deleting their own account
        if not current_user or (current_user.email != 'admin@example.com' and current_user_id != user_id):
            return jsonify({'error': 'Access denied'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400