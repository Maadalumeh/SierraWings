"""
Update Message Panel Routes for SierraWings
Handles admin update messages and user message viewing
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from models_extensions import SystemAlert, UpdateMessage
from datetime import datetime
from mail_service import send_email
import logging

# Create updates blueprint
updates_bp = Blueprint('updates', __name__)

# Routes defined in this file use the updates_bp blueprint

@app.route('/api/maintenance/check')
def api_maintenance_check():
    """Check maintenance status for maintenance checker"""
    return jsonify({
        'maintenance_mode': False,
        'message': 'System is operational'
    })

@app.route('/admin/updates')
@login_required
def admin_updates():
    """Admin update messages management"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all update messages
    updates = UpdateMessage.query.order_by(UpdateMessage.created_at.desc()).all()
    
    return render_template('admin_updates.html', updates=updates)

@app.route('/admin/updates/send', methods=['POST'])
@login_required
def send_update_message():
    """Send update message to all users"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        message_type = data.get('type', 'info')  # info, warning, success, danger
        
        if not title or not message:
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Create update message
        update_message = UpdateMessage(
            title=title,
            message=message,
            message_type=message_type,
            created_by=current_user.id,
            is_active=True
        )
        
        db.session.add(update_message)
        db.session.commit()
        
        # Send email notifications to all users
        from models import User
        users = User.query.filter_by(email_verified=True).all()
        
        for user in users:
            try:
                send_email(
                    user.email,
                    f"SierraWings Update: {title}",
                    f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background: #1A252F; color: white; padding: 20px; text-align: center;">
                            <h2>SierraWings Update</h2>
                        </div>
                        <div style="padding: 20px; background: #f8f9fa;">
                            <h3 style="color: #1A252F;">{title}</h3>
                            <p style="color: #2C3E50; line-height: 1.6;">{message}</p>
                            <hr style="border: 1px solid #ddd; margin: 20px 0;">
                            <p style="color: #6c757d; font-size: 0.9rem;">
                                This is an automated message from SierraWings. 
                                For support, contact: sierrawingsofficial@gmail.com
                            </p>
                        </div>
                    </div>
                    """,
                    f"SierraWings Update: {title}\n\n{message}\n\nFor support, contact: sierrawingsofficial@gmail.com"
                )
            except Exception as e:
                logging.error(f"Failed to send update email to {user.email}: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Update message sent successfully',
            'update_id': update_message.id
        })
        
    except Exception as e:
        logging.error(f"Error sending update message: {str(e)}")
        return jsonify({'error': 'Failed to send update message'}), 500

@app.route('/admin/updates/<int:update_id>/edit', methods=['POST'])
@login_required
def edit_update_message(update_id):
    """Edit existing update message"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        update_message = UpdateMessage.query.get_or_404(update_id)
        data = request.get_json()
        
        update_message.title = data.get('title', update_message.title).strip()
        update_message.message = data.get('message', update_message.message).strip()
        update_message.message_type = data.get('type', update_message.message_type)
        update_message.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Update message edited successfully'
        })
        
    except Exception as e:
        logging.error(f"Error editing update message: {str(e)}")
        return jsonify({'error': 'Failed to edit update message'}), 500

@app.route('/admin/updates/<int:update_id>/delete', methods=['POST'])
@login_required
def delete_update_message(update_id):
    """Delete update message"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        update_message = UpdateMessage.query.get_or_404(update_id)
        db.session.delete(update_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Update message deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting update message: {str(e)}")
        return jsonify({'error': 'Failed to delete update message'}), 500

@app.route('/api/updates/active')
@login_required
def get_active_updates():
    """Get active update messages for current user"""
    # Get messages not dismissed by current user
    active_updates = UpdateMessage.query.filter_by(is_active=True).order_by(UpdateMessage.created_at.desc()).all()
    
    # Filter out dismissed messages
    from models_extensions import DismissedMessage
    dismissed = DismissedMessage.query.filter_by(user_id=current_user.id).all()
    dismissed_ids = [d.message_id for d in dismissed]
    
    active_updates = [u for u in active_updates if u.id not in dismissed_ids]
    
    updates_data = []
    for update in active_updates:
        updates_data.append({
            'id': update.id,
            'title': update.title,
            'message': update.message,
            'type': update.message_type,
            'created_at': update.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(updates_data)

@app.route('/api/updates/<int:update_id>/dismiss', methods=['POST'])
@login_required
def dismiss_update_message(update_id):
    """Dismiss update message for current user"""
    try:
        from models_extensions import DismissedMessage
        
        # Check if already dismissed
        existing = DismissedMessage.query.filter_by(
            user_id=current_user.id,
            message_id=update_id
        ).first()
        
        if not existing:
            dismissed = DismissedMessage(
                user_id=current_user.id,
                message_id=update_id
            )
            db.session.add(dismissed)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Update message dismissed'
        })
        
    except Exception as e:
        logging.error(f"Error dismissing update message: {str(e)}")
        return jsonify({'error': 'Failed to dismiss message'}), 500

@app.route('/updates')
@login_required
def view_updates():
    """View all update messages"""
    # Get all active updates
    updates = UpdateMessage.query.filter_by(is_active=True).order_by(UpdateMessage.created_at.desc()).all()
    
    # Get dismissed messages for current user
    from models_extensions import DismissedMessage
    dismissed = DismissedMessage.query.filter_by(user_id=current_user.id).all()
    dismissed_ids = [d.message_id for d in dismissed]
    
    return render_template('updates.html', updates=updates, dismissed_ids=dismissed_ids)