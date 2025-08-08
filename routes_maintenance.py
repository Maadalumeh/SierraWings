"""
Maintenance Mode Routes for SierraWings
Handles maintenance mode toggle and system status
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from models_extensions import SystemAlert
from datetime import datetime
import logging

# Create maintenance blueprint
maintenance_bp = Blueprint('maintenance', __name__)

# Global maintenance state
maintenance_mode = False
maintenance_message = ""
maintenance_start_time = None

@app.route('/admin/maintenance/toggle', methods=['POST'])
@login_required
def toggle_maintenance():
    """Toggle maintenance mode on/off"""
    global maintenance_mode, maintenance_message, maintenance_start_time
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        message = data.get('message', 'System is undergoing maintenance. Please check back later.')
        
        maintenance_mode = enabled
        maintenance_message = message
        
        if enabled:
            maintenance_start_time = datetime.utcnow()
            # Create maintenance alert
            alert = SystemAlert(
                alert_type='maintenance',
                title='System Maintenance',
                message=message,
                severity='warning',
                created_by=current_user.id
            )
            db.session.add(alert)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Maintenance mode enabled',
                'maintenance_mode': True
            })
        else:
            maintenance_start_time = None
            return jsonify({
                'success': True,
                'message': 'Maintenance mode disabled',
                'maintenance_mode': False
            })
            
    except Exception as e:
        logging.error(f"Error toggling maintenance mode: {str(e)}")
        return jsonify({'error': 'Failed to toggle maintenance mode'}), 500

@app.route('/admin/maintenance/status')
@login_required
def maintenance_status():
    """Get current maintenance status"""
    global maintenance_mode, maintenance_message, maintenance_start_time
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'maintenance_mode': maintenance_mode,
        'message': maintenance_message,
        'start_time': maintenance_start_time.isoformat() if maintenance_start_time else None
    })

@app.route('/api/maintenance/check')
def check_maintenance():
    """Check if system is in maintenance mode (public endpoint)"""
    global maintenance_mode, maintenance_message
    
    return jsonify({
        'maintenance_mode': maintenance_mode,
        'message': maintenance_message if maintenance_mode else None
    })

def is_maintenance_mode():
    """Check if system is currently in maintenance mode"""
    global maintenance_mode
    return maintenance_mode

def get_maintenance_message():
    """Get current maintenance message"""
    global maintenance_message
    return maintenance_message