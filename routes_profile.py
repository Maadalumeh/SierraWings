"""
Profile Management Routes
Handles user profile updates and management
"""

from flask import jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from models import User
from werkzeug.security import check_password_hash, generate_password_hash
import re

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Username and email are required'
            }), 400
        
        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Check if username or email already exists (for other users)
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email']),
            User.id != current_user.id
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username or email already exists'
            }), 400
        
        # Handle password change
        if data.get('current_password') and data.get('new_password'):
            if not current_user.check_password(data['current_password']):
                return jsonify({
                    'success': False,
                    'message': 'Current password is incorrect'
                }), 400
            
            if len(data['new_password']) < 6:
                return jsonify({
                    'success': False,
                    'message': 'New password must be at least 6 characters long'
                }), 400
            
            current_user.set_password(data['new_password'])
        
        # Update profile fields
        current_user.first_name = data.get('first_name', '').strip()
        current_user.last_name = data.get('last_name', '').strip()
        current_user.username = data['username'].strip()
        current_user.email = data['email'].strip()
        current_user.phone = data.get('phone', '').strip()
        current_user.address = data.get('address', '').strip()
        
        # Update role-specific fields
        if current_user.role == 'patient':
            current_user.emergency_contact = data.get('emergency_contact', '').strip()
            current_user.allergies = data.get('allergies', '').strip()
        elif current_user.role == 'clinic':
            current_user.clinic_name = data.get('clinic_name', '').strip()
            current_user.clinic_license = data.get('clinic_license', '').strip()
            current_user.specialization = data.get('specialization', '').strip()
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }), 500

@app.route('/get_profile')
@login_required
def get_profile():
    """Get current user profile data"""
    try:
        profile_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'phone': current_user.phone,
            'address': current_user.address,
            'role': current_user.role,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'email_verified': current_user.email_verified
        }
        
        # Add role-specific fields
        if current_user.role == 'patient':
            profile_data.update({
                'emergency_contact': current_user.emergency_contact,
                'allergies': current_user.allergies,
                'medical_id': current_user.medical_id
            })
        elif current_user.role == 'clinic':
            profile_data.update({
                'clinic_name': current_user.clinic_name,
                'clinic_license': current_user.clinic_license,
                'specialization': current_user.specialization
            })
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting profile: {str(e)}'
        }), 500