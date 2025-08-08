from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import User, Drone, Mission
from models_extensions import SystemAlert, MaintenanceRecord, Feedback
from app import db

bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Get system statistics
    total_users = User.query.count()
    total_drones = Drone.query.count()
    total_missions = Mission.query.count()
    active_missions = Mission.query.filter(Mission.status.in_(['accepted', 'assigned', 'in_progress'])).count()
    
    # Get recent activities
    recent_missions = Mission.query.order_by(Mission.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get drone status
    available_drones = Drone.query.filter_by(status='available').count()
    in_flight_drones = Drone.query.filter_by(status='in_flight').count()
    maintenance_drones = Drone.query.filter_by(status='maintenance').count()
    
    # Get feedback data
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    # Get current time for system status
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get all drones for wireless connection
    all_drones = Drone.query.all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_drones=total_drones,
                         total_missions=total_missions,
                         active_missions=active_missions,
                         recent_missions=recent_missions,
                         recent_users=recent_users,
                         available_drones=all_drones,
                         in_flight_drones=in_flight_drones,
                         maintenance_drones=maintenance_drones,
                         total_feedback=total_feedback,
                         pending_feedback=pending_feedback,
                         recent_feedback=recent_feedback,
                         current_time=current_time)