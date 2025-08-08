"""
SierraWings Feedback Routes
API endpoints for feedback submission and email delivery
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from feedback_service import send_feedback_email
import logging

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback via API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        if not all([name, email, message]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Get user role
        user_role = current_user.role if current_user.is_authenticated else 'Unknown'
        
        # Send feedback email
        success = send_feedback_email(name, email, message, user_role)
        
        if success:
            return jsonify({'success': True, 'message': 'Feedback sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send feedback'}), 500
            
    except Exception as e:
        logging.error(f"Feedback submission error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback_form():
    """Feedback form page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not all([name, email, message]):
            return render_template('feedback_form.html', 
                                 error='All fields are required',
                                 name=name, email=email, message=message)
        
        # Get user role
        user_role = current_user.role if current_user.is_authenticated else 'Unknown'
        
        # Send feedback email
        success = send_feedback_email(name, email, message, user_role)
        
        if success:
            return render_template('feedback_form.html', 
                                 success='Thank you for your feedback! We will review it soon.')
        else:
            return render_template('feedback_form.html', 
                                 error='Failed to send feedback. Please try again.',
                                 name=name, email=email, message=message)
    
    # Pre-fill form with user data
    user_name = f"{current_user.first_name} {current_user.last_name}".strip() if current_user.first_name or current_user.last_name else current_user.username
    user_email = current_user.email if current_user.email else ''
    
    return render_template('feedback_form.html', 
                         name=user_name, email=user_email)